"""Integration tests for GET /api/v1/toppaper/round-importance endpoint.

Seam: the public HTTP interface of the multi-round importance-score pipeline.
All expected values are computed from the spec (§5 EMA formula) independently —
never derived from the production code itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
import torch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.flattening import save_flat_parameters_artifact


# ---------------------------------------------------------------------------
# Helpers — build synthetic flat-parameter artifacts on disk
# ---------------------------------------------------------------------------

def _make_flat_artifact(flat_tensor: torch.Tensor, path: Path) -> None:
    """Persist a synthetic 1-D float32 tensor as a flat-parameter artifact."""
    metadata = {
        "layer_slices": {
            "conv1.weight": {
                "start_idx": 0,
                "end_idx": flat_tensor.numel(),
                "shape": [flat_tensor.numel()],
                "numel": flat_tensor.numel(),
            },
        },
        "l2_norm": float(torch.linalg.norm(flat_tensor).item()),
        "num_parameters": flat_tensor.numel(),
    }
    save_flat_parameters_artifact(flat_tensor=flat_tensor, metadata=metadata, output_path=path)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests: empty-state (no round artifacts on disk)
# ---------------------------------------------------------------------------

class TestRoundImportanceEmptyState:
    """Endpoint must degrade gracefully when no round artifacts exist."""

    def test_empty_state_returns_200_with_has_data_false(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GET /round-importance returns HTTP 200 and has_data=false when rounds dir is empty."""
        monkeypatch.setattr("backend.top_p_router.ROUNDS_DIR", tmp_path / "rounds_empty")
        res = client.get("/api/v1/toppaper/round-importance")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["has_data"] is False
        assert data["rounds"] == []
        assert data["total_rounds"] == 0

    def test_empty_state_schema_keys_present(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty-state response must include all required top-level keys."""
        monkeypatch.setattr("backend.top_p_router.ROUNDS_DIR", tmp_path / "rounds_empty2")
        data = client.get("/api/v1/toppaper/round-importance").json()
        for key in ("has_data", "total_rounds", "beta", "offset", "top_k", "total_parameters", "rounds"):
            assert key in data, f"Missing key {key!r} in empty-state response"


# ---------------------------------------------------------------------------
# Tests: EMA formula correctness with controlled 2-round data
# ---------------------------------------------------------------------------

class TestRoundImportanceEmaFormula:
    """EMA score formula: s(1) = |w(1)|, s(t) = beta*s(t-1) + (1-beta)*|w(t)|."""

    @pytest.fixture(autouse=True)
    def _setup_two_rounds(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Create two synthetic round flat artifacts with known values."""
        rounds_dir = tmp_path / "rounds"
        rounds_dir.mkdir(parents=True)

        # Round 1: known values [0.2, 0.5, -0.1, 0.3]
        self.w1 = torch.tensor([0.2, 0.5, -0.1, 0.3], dtype=torch.float32)
        _make_flat_artifact(self.w1, rounds_dir / "cifar10_flat_round_1.pt")

        # Round 2: known values [0.4, -0.2, 0.6, 0.1]
        self.w2 = torch.tensor([0.4, -0.2, 0.6, 0.1], dtype=torch.float32)
        _make_flat_artifact(self.w2, rounds_dir / "cifar10_flat_round_2.pt")

        monkeypatch.setattr("backend.top_p_router.ROUNDS_DIR", rounds_dir)

    def test_round1_score_equals_abs_w1(self, client: TestClient) -> None:
        """Round 1 score must equal |w^(1)| for every coordinate (EMA base case t=1)."""
        beta = 0.9
        res = client.get(f"/api/v1/toppaper/round-importance?beta={beta}&top_k=5&offset=0")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["has_data"] is True
        assert data["total_rounds"] == 2

        round1 = next(r for r in data["rounds"] if r["round"] == 1)
        items_by_index: Dict[int, Any] = {item["global_index"]: item for item in round1["items"]}

        abs_w1 = torch.abs(self.w1)
        for coord_idx in range(4):
            if coord_idx in items_by_index:
                expected = round(float(abs_w1[coord_idx].item()), 6)
                actual = round(items_by_index[coord_idx]["score"], 6)
                assert abs(actual - expected) < 1e-5, (
                    f"Round 1, coord {coord_idx}: expected {expected}, got {actual}"
                )

    def test_round2_score_follows_ema_formula(self, client: TestClient) -> None:
        """Round 2 score must equal beta*|w(1)| + (1-beta)*|w(2)| per coordinate."""
        beta = 0.9
        res = client.get(f"/api/v1/toppaper/round-importance?beta={beta}&top_k=5&offset=0")
        assert res.status_code == 200, res.text
        data = res.json()

        round2 = next(r for r in data["rounds"] if r["round"] == 2)
        items_by_index: Dict[int, Any] = {item["global_index"]: item for item in round2["items"]}

        abs_w1 = torch.abs(self.w1)
        abs_w2 = torch.abs(self.w2)
        for coord_idx in range(4):
            if coord_idx in items_by_index:
                s1 = float(abs_w1[coord_idx].item())
                s2_expected = beta * s1 + (1.0 - beta) * float(abs_w2[coord_idx].item())
                actual = items_by_index[coord_idx]["score"]
                assert abs(actual - s2_expected) < 1e-5, (
                    f"Round 2, coord {coord_idx}: expected EMA={s2_expected:.6f}, got {actual:.6f}"
                )

    def test_round2_scores_sorted_descending(self, client: TestClient) -> None:
        """Within each round, items must be sorted by score descending."""
        res = client.get("/api/v1/toppaper/round-importance?beta=0.9&top_k=5&offset=0")
        data = res.json()
        for rd in data["rounds"]:
            scores = [item["score"] for item in rd["items"]]
            assert scores == sorted(scores, reverse=True), (
                f"Round {rd['round']} not sorted descending: {scores}"
            )

    def test_rank_numbering_starts_at_one_for_offset_zero(self, client: TestClient) -> None:
        """First item in each round must have rank=1 when offset=0."""
        data = client.get("/api/v1/toppaper/round-importance?beta=0.9&top_k=5&offset=0").json()
        for rd in data["rounds"]:
            assert rd["items"][0]["rank"] == 1, (
                f"First item rank should be 1, got {rd['items'][0]['rank']}"
            )

    def test_rank_delta_none_for_round1(self, client: TestClient) -> None:
        """Round 1 has no predecessor — rank_delta must be None for all items."""
        data = client.get("/api/v1/toppaper/round-importance?beta=0.9&top_k=5&offset=0").json()
        round1 = next(r for r in data["rounds"] if r["round"] == 1)
        for item in round1["items"]:
            assert item["rank_delta"] is None, (
                f"Round 1 rank_delta must be None, got {item['rank_delta']} for idx={item['global_index']}"
            )

    def test_has_data_true_when_rounds_present(self, client: TestClient) -> None:
        """has_data must be True when at least one round artifact exists."""
        data = client.get("/api/v1/toppaper/round-importance").json()
        assert data["has_data"] is True

    def test_total_parameters_matches_tensor_size(self, client: TestClient) -> None:
        """total_parameters must equal the numel of the loaded tensors."""
        data = client.get("/api/v1/toppaper/round-importance?top_k=5").json()
        assert data["total_parameters"] == 4


# ---------------------------------------------------------------------------
# Tests: Pagination (top_k + offset)
# ---------------------------------------------------------------------------

class TestRoundImportancePagination:
    """Pagination must correctly slice items per round."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_dir = tmp_path / "rounds_page"
        rounds_dir.mkdir(parents=True)
        # 10-element tensor with monotonically increasing values
        self.w1 = torch.arange(10, dtype=torch.float32) * 0.1 + 0.1
        _make_flat_artifact(self.w1, rounds_dir / "cifar10_flat_round_1.pt")
        monkeypatch.setattr("backend.top_p_router.ROUNDS_DIR", rounds_dir)

    def test_top_k_limits_items_per_round(self, client: TestClient) -> None:
        """top_k=5 must return exactly 5 items per round."""
        data = client.get("/api/v1/toppaper/round-importance?top_k=5&offset=0").json()
        for rd in data["rounds"]:
            assert len(rd["items"]) == 5, f"Expected 5 items, got {len(rd['items'])}"

    def test_offset_shifts_rank_start(self, client: TestClient) -> None:
        """offset=5 must return items starting at rank 6."""
        data = client.get("/api/v1/toppaper/round-importance?top_k=5&offset=5").json()
        for rd in data["rounds"]:
            assert rd["items"][0]["rank"] == 6, (
                f"Rank with offset=5 should be 6, got {rd['items'][0]['rank']}"
            )

    def test_offset_beyond_total_returns_empty_items(self, client: TestClient) -> None:
        """offset >= total_parameters must return empty items (no error)."""
        data = client.get("/api/v1/toppaper/round-importance?top_k=5&offset=999").json()
        for rd in data["rounds"]:
            assert rd["items"] == [], f"Expected empty items with offset=999, got {rd['items']}"


# ---------------------------------------------------------------------------
# Tests: Schema / response-shape integrity
# ---------------------------------------------------------------------------

class TestRoundImportanceSchema:
    """Verify each item has all required fields with correct types."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_dir = tmp_path / "rounds_schema"
        rounds_dir.mkdir(parents=True)
        w1 = torch.tensor([0.3, -0.7, 0.15, 0.05, -0.4, 0.9], dtype=torch.float32)
        _make_flat_artifact(w1, rounds_dir / "cifar10_flat_round_1.pt")
        monkeypatch.setattr("backend.top_p_router.ROUNDS_DIR", rounds_dir)

    def test_item_contains_all_required_fields(self, client: TestClient) -> None:
        """Every item must have rank, rank_delta, global_index, layer_name, score, value, abs_value."""
        data = client.get("/api/v1/toppaper/round-importance?top_k=5&offset=0").json()
        required = {"rank", "rank_delta", "global_index", "layer_name", "score", "value", "abs_value"}
        for rd in data["rounds"]:
            for item in rd["items"]:
                missing = required - item.keys()
                assert not missing, f"Item missing fields {missing}: {item}"

    def test_response_echoes_beta(self, client: TestClient) -> None:
        """Response must echo back the beta value used for computation."""
        data = client.get("/api/v1/toppaper/round-importance?beta=0.7").json()
        assert abs(data["beta"] - 0.7) < 1e-6, f"beta echo wrong: {data['beta']}"

    def test_html_contains_importance_panel_elements(self) -> None:
        """The HTML must contain the importance panel IDs required by the frontend seam."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        required_ids = [
            'id="inp-importance-beta"',
            'id="sel-importance-page-size"',
            'id="btn-compute-importance"',
            'id="importance-panel"',
        ]
        for id_attr in required_ids:
            assert id_attr in html, f"Missing HTML element {id_attr!r} in top_p_lab.html"

    def test_html_contains_importance_js_function(self) -> None:
        """The HTML must contain the computeImportanceScores JS function definition."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "function computeImportanceScores" in html, (
            "Missing JS function computeImportanceScores in top_p_lab.html"
        )
