"""Integration Test Suite for Unified 5-Benchmark Model & Dataset Switcher API.

Tests adhere strictly to Section 5.1 of the SemanticDFL research paper:
1. Benchmark Catalog: GET /api/v1/toppaper/benchmarks returns metadata for all 5 pairs.
2. Parameter counts, paper optimal P/M ratios, topologies, and canonical layer orders match Paper §5.1.
3. Training Dispatcher: POST /api/v1/toppaper/train-cnn dispatches dynamically to each benchmark pipeline.
4. Downstream Top-P Endpoints: cnn-weights, round-importance, energy-distribution, and binary-search-pmin
   properly filter by benchmark and respect benchmark subdirectory artifact scoping.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import torch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.flattening import save_flat_parameters_artifact
import backend.top_p_router as router_mod


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


def _make_mock_round_artifact(flat_tensor: torch.Tensor, path: Path, layer_name: str = "conv1.weight") -> None:
    """Create a minimal synthetic flat-parameter artifact on disk."""
    metadata = {
        "layer_slices": {
            layer_name: {
                "start_idx": 0,
                "end_idx": flat_tensor.numel(),
                "shape": [flat_tensor.numel()],
                "numel": flat_tensor.numel(),
            },
        },
        "l2_norm": float(torch.linalg.norm(flat_tensor).item()),
        "num_parameters": flat_tensor.numel(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    save_flat_parameters_artifact(flat_tensor=flat_tensor, metadata=metadata, output_path=path)


# ---------------------------------------------------------------------------
# Test Suite 1: Benchmark Catalog Endpoint & Schema Validation
# ---------------------------------------------------------------------------

class TestBenchmarksCatalogApi:
    """Tests for GET /api/v1/toppaper/benchmarks."""

    def test_catalog_endpoint_returns_200_and_expected_keys(self, client: TestClient):
        """Verify endpoint returns all 5 benchmarks with valid contract schema."""
        res = client.get("/api/v1/toppaper/benchmarks")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert "benchmarks" in data
        assert "count" in data
        assert data["count"] == 5
        assert data["default"] == "cifar10"

        benchmarks = data["benchmarks"]
        expected_benchmarks = ["cifar10", "fmnist", "tiny_imagenet", "speech", "20news"]
        for b_id in expected_benchmarks:
            assert b_id in benchmarks, f"Missing benchmark {b_id} in catalog"

    def test_paper_constants_and_optimal_ratios(self, client: TestClient):
        """Verify paper optimal P* target ratios and parameter scales match Paper §5.1."""
        res = client.get("/api/v1/toppaper/benchmarks")
        assert res.status_code == 200
        benchmarks = res.json()["benchmarks"]

        # CIFAR-10: ~2.15M params, P* = 12.3%
        cifar = benchmarks["cifar10"]
        assert cifar["model_name"] == "CIFAR10CNN"
        assert cifar["total_parameters"] == 2156490
        assert cifar["paper_optimal_p_ratio"] == 0.123
        assert cifar["num_classes"] == 10
        assert len(cifar["canonical_layers"]) == 8

        # Fashion-MNIST: ~1.65M params, P* = 12.3%
        fmnist = benchmarks["fmnist"]
        assert fmnist["model_name"] == "FMNISTCNN"
        assert fmnist["total_parameters"] == 1663370
        assert fmnist["paper_optimal_p_ratio"] == 0.123
        assert fmnist["num_classes"] == 10
        assert len(fmnist["canonical_layers"]) == 8

        # Tiny-ImageNet: ~11.27M params, P* = 9.6%
        tiny = benchmarks["tiny_imagenet"]
        assert tiny["model_name"] == "TinyImageNetResNet18"
        assert tiny["total_parameters"] == 11271432
        assert tiny["paper_optimal_p_ratio"] == 0.096
        assert tiny["num_classes"] == 200

        # Google Speech: ~11.17M params, P* = 11.2%
        speech = benchmarks["speech"]
        assert speech["model_name"] == "SpeechResNet18"
        assert speech["total_parameters"] == 11172810
        assert speech["paper_optimal_p_ratio"] == 0.112
        assert speech["num_classes"] == 10

        # 20Newsgroups: ~11.68M params, P* = 12.8%
        news = benchmarks["20news"]
        assert news["model_name"] == "NewsAlbert"
        assert news["total_parameters"] == 11698964
        assert news["paper_optimal_p_ratio"] == 0.128
        assert news["num_classes"] == 20

    def test_canonical_layer_orders_non_empty(self, client: TestClient):
        """Verify each benchmark defines deterministic, non-empty canonical layer orders."""
        res = client.get("/api/v1/toppaper/benchmarks")
        benchmarks = res.json()["benchmarks"]

        for b_id, b_meta in benchmarks.items():
            assert "canonical_layers" in b_meta
            assert isinstance(b_meta["canonical_layers"], list)
            assert len(b_meta["canonical_layers"]) > 0, f"{b_id} has empty canonical_layers"


# ---------------------------------------------------------------------------
# Test Suite 2: Multi-Benchmark Training Dispatcher
# ---------------------------------------------------------------------------

class TestBenchmarkTrainingDispatcher:
    """Tests for POST /api/v1/toppaper/train-cnn with dynamic benchmark selection."""

    def test_train_fmnist_synthetic(self, client: TestClient):
        """Verify training endpoint dispatches to Fashion-MNIST CNN pipeline."""
        payload = {
            "benchmark": "fmnist",
            "rounds": 1,
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.01,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 32,
        }
        res = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["benchmark"] == "fmnist"
        assert "final_train_loss" in data
        assert "final_train_accuracy" in data
        assert Path("output/models/fmnist_flat_parameters.pt").exists()
        assert Path("output/models/fmnist_cnn_checkpoint.pt").exists()

    def test_train_tiny_imagenet_synthetic(self, client: TestClient):
        """Verify training endpoint dispatches to Tiny-ImageNet ResNet-18 pipeline."""
        payload = {
            "benchmark": "tiny_imagenet",
            "rounds": 1,
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.05,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 32,
        }
        res = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["benchmark"] == "tiny_imagenet"
        assert Path("output/models/tiny_imagenet_flat_parameters.pt").exists()

    def test_train_speech_synthetic(self, client: TestClient):
        """Verify training endpoint dispatches to Google Speech SpeechResNet18 pipeline."""
        payload = {
            "benchmark": "speech",
            "rounds": 1,
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.05,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 32,
        }
        res = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["benchmark"] == "speech"
        assert Path("output/models/speech_flat_parameters.pt").exists()

    def test_train_20news_synthetic(self, client: TestClient):
        """Verify training endpoint dispatches to 20Newsgroups ALBERT pipeline."""
        payload = {
            "benchmark": "20news",
            "rounds": 1,
            "epochs": 1,
            "batch_size": 8,
            "learning_rate": 2e-5,
            "weight_decay": 0.01,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 16,
        }
        res = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert data["benchmark"] == "20news"
        assert Path("output/models/albert_flat_parameters.pt").exists()

    def test_invalid_benchmark_rejected_with_422(self, client: TestClient):
        """Verify unsupported benchmark identifiers are rejected with HTTP 422."""
        res = client.post("/api/v1/toppaper/train-cnn", json={"benchmark": "invalid_dataset"})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Test Suite 3: Benchmark-Scoped Downstream Endpoints
# ---------------------------------------------------------------------------

class TestBenchmarkScopedEndpoints:
    """Tests verifying benchmark scoping on weights, importance, energy, and P_min endpoints."""

    def test_cnn_weights_benchmark_scoping(self, client: TestClient):
        """Verify /cnn-weights returns correct architecture parameter count per benchmark."""
        # Fashion-MNIST weights
        res_fmnist = client.get("/api/v1/toppaper/cnn-weights?benchmark=fmnist")
        assert res_fmnist.status_code == 200
        data_fmnist = res_fmnist.json()
        assert data_fmnist["total_parameters"] == 1663370
        assert data_fmnist["checkpoint_info"]["benchmark"] == "fmnist"

        # CIFAR-10 default
        res_cifar = client.get("/api/v1/toppaper/cnn-weights")
        assert res_cifar.status_code == 200
        assert res_cifar.json()["total_parameters"] == 2156490

    def test_round_importance_benchmark_subdirectory_scoping(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify /round-importance discovers artifacts in benchmark subdirectory."""
        rounds_dir = tmp_path / "rounds"
        fmnist_sub = rounds_dir / "fmnist"
        fmnist_sub.mkdir(parents=True)

        w1 = torch.tensor([0.1, 0.4, 0.3], dtype=torch.float32)
        _make_mock_round_artifact(w1, fmnist_sub / "fmnist_flat_round_1.pt")

        monkeypatch.setattr(router_mod, "ROUNDS_DIR", rounds_dir)

        # Scoped query for fmnist must find the round
        res = client.get("/api/v1/toppaper/round-importance?benchmark=fmnist")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is True
        assert data["benchmark"] == "fmnist"
        assert data["total_rounds"] == 1
        assert data["total_parameters"] == 3

        # Scoped query for cifar10 must find no rounds in the fmnist folder
        res_cifar = client.get("/api/v1/toppaper/round-importance?benchmark=cifar10")
        assert res_cifar.status_code == 200
        assert res_cifar.json()["has_data"] is False

    def test_energy_distribution_benchmark_scoping(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify /energy-distribution filters by benchmark parameter."""
        rounds_dir = tmp_path / "rounds"
        tiny_sub = rounds_dir / "tiny_imagenet"
        tiny_sub.mkdir(parents=True)

        w1 = torch.tensor([3.0, 4.0], dtype=torch.float32)
        _make_mock_round_artifact(w1, tiny_sub / "tiny_imagenet_flat_round_1.pt")

        monkeypatch.setattr(router_mod, "ROUNDS_DIR", rounds_dir)

        res = client.get("/api/v1/toppaper/energy-distribution?benchmark=tiny_imagenet")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is True
        assert data["benchmark"] == "tiny_imagenet"
        assert data["total_rounds"] == 1
        assert abs(data["rounds"][0]["nu"] - 5.0) < 1e-4

    def test_binary_search_pmin_benchmark_scoping(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Verify /binary-search-pmin calculates minimal coordinates scoped to benchmark."""
        rounds_dir = tmp_path / "rounds"
        speech_sub = rounds_dir / "speech"
        speech_sub.mkdir(parents=True)

        w1 = torch.tensor([1.0, 2.0, 3.0, 4.0], dtype=torch.float32)
        _make_mock_round_artifact(w1, speech_sub / "speech_flat_round_1.pt")

        monkeypatch.setattr(router_mod, "ROUNDS_DIR", rounds_dir)

        res = client.get("/api/v1/toppaper/binary-search-pmin?benchmark=speech&theta=0.8")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is True
        assert data["benchmark"] == "speech"
        assert data["p_min"] >= 1
        assert data["achieved_cosine"] >= 0.8


# ---------------------------------------------------------------------------
# Test Suite 4: Benchmark Switcher UI Elements & Event Handlers
# ---------------------------------------------------------------------------

class TestBenchmarkSwitcherUIIntegration:
    """Tests verifying the 5-benchmark switcher pill bar and dynamic bindings in top_p_lab.html."""

    def test_benchmark_pills_present_in_tab2(self):
        """Verify all 5 benchmark pills exist with exact identifiers and click handlers."""
        html_path = Path("frontend/static/top_p_lab.html")
        content = html_path.read_text(encoding="utf-8")

        expected_benchmarks = ["cifar10", "fmnist", "tiny_imagenet", "speech", "20news"]
        for b_id in expected_benchmarks:
            pill_id = f'id="benchmark-pill-{b_id}"'
            onclick = f'onclick="switchBenchmark(\'{b_id}\')"'
            assert pill_id in content, f"Missing benchmark pill ID: {pill_id}"
            assert onclick in content, f"Missing onclick handler: {onclick}"

    def test_dynamic_hud_elements_present(self):
        """Verify dynamic HUD elements exist for real-time benchmark telemetry."""
        html_path = Path("frontend/static/top_p_lab.html")
        content = html_path.read_text(encoding="utf-8")

        expected_elements = [
            'id="benchmark-active-name"',
            'id="benchmark-active-model"',
            'id="benchmark-badge-modality"',
            'id="benchmark-badge-optimal-p"',
            'id="benchmark-active-desc"',
            'id="train-controller-title"',
            'id="train-controller-algo"',
            'id="cnn-kpi-optimal-p"',
            'id="cnn-slice-map-title"',
        ]
        for el_id in expected_elements:
            assert el_id in content, f"Missing HUD element: {el_id}"

    def test_js_benchmark_switcher_functions(self):
        """Verify JS functions for switching benchmark and propagating parameters."""
        html_path = Path("frontend/static/top_p_lab.html")
        content = html_path.read_text(encoding="utf-8")

        assert "function switchBenchmark(benchmarkId)" in content
        assert "let currentBenchmark = 'cifar10';" in content
        assert "LOCAL_BENCHMARKS" in content
        assert "benchmark: currentBenchmark" in content
        assert "benchmark=${encodeURIComponent(currentBenchmark)}" in content

