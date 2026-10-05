"""Integration tests for GET /api/v1/toppaper/energy-distribution endpoint and Step 2 panel.

Seam: the public HTTP interface of the Step 2 Energy Distribution & Cumulative Prefix Sums pipeline.
All expected mathematical properties (total energy nu^2, norm nu, prefix sum c_M == nu^2,
cos(M) == 1.0, and strict monotonicity) are verified independently against the paper specification.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict

import pytest
import torch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.flattening import save_flat_parameters_artifact
import backend.top_p_router as router_mod


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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestEnergyDistributionEmptyState:
    """Endpoint must degrade gracefully when no round artifacts exist."""

    def test_empty_state_returns_200_with_has_data_false(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        empty_dir = tmp_path / "empty_rounds_dir"
        empty_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(router_mod, "ROUNDS_DIR", empty_dir)

        res = client.get("/api/v1/toppaper/energy-distribution")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is False
        assert data["total_rounds"] == 0
        assert data["rounds"] == []


class TestEnergyDistributionMath:
    """Verify energy prefix sums c_P and directional cosine cos(P) mathematical correctness."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.rounds_dir = tmp_path / "rounds_energy_math"
        self.rounds_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(router_mod, "ROUNDS_DIR", self.rounds_dir)

        # Vector with known values: [3.0, -4.0]
        # |w| = [3.0, 4.0] -> sorted descending: index 1 (-4.0), index 0 (3.0)
        # nu^2 = 3^2 + (-4)^2 = 9 + 16 = 25, nu = 5.0
        # P = 1: c_1 = 16.0, energy_pct = 64.0%, cos(1) = 4.0 / 5.0 = 0.8
        # P = 2: c_2 = 25.0, energy_pct = 100.0%, cos(2) = 5.0 / 5.0 = 1.0
        w1 = torch.tensor([3.0, -4.0], dtype=torch.float32)
        _make_flat_artifact(w1, self.rounds_dir / "cifar10_flat_round_1.pt")

    def test_total_energy_and_final_cosine(self, client: TestClient) -> None:
        """For P=M, c_M must equal nu^2 and cos(M) must strictly equal 1.0."""
        res = client.get("/api/v1/toppaper/energy-distribution?beta=0.9")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is True
        assert data["total_rounds"] == 1
        assert data["total_parameters"] == 2

        r1 = data["rounds"][0]
        assert abs(r1["nu_sq"] - 25.0) < 1e-4
        assert abs(r1["nu"] - 5.0) < 1e-4

        # Check last milestone at P=M=2
        last_m = r1["milestones"][-1]
        assert last_m["p"] == 2
        assert abs(last_m["c_p"] - 25.0) < 1e-4
        assert abs(last_m["energy_pct"] - 100.0) < 1e-4
        assert abs(last_m["cosine"] - 1.0) < 1e-4

        # Check first milestone at P=1
        first_m = r1["milestones"][0]
        assert first_m["p"] == 1
        assert abs(first_m["c_p"] - 16.0) < 1e-4
        assert abs(first_m["energy_pct"] - 64.0) < 1e-4
        assert abs(first_m["cosine"] - 0.8) < 1e-4

    def test_monotonicity_of_energy_and_cosine(self, client: TestClient) -> None:
        """c_P and cos(P) must be strictly non-decreasing across all points."""
        w = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=torch.float32)
        _make_flat_artifact(w, self.rounds_dir / "cifar10_flat_round_1.pt")

        res = client.get("/api/v1/toppaper/energy-distribution?beta=0.9")
        assert res.status_code == 200
        r1 = res.json()["rounds"][0]

        prev_c = 0.0
        prev_cos = 0.0
        for m in r1["milestones"]:
            assert m["c_p"] >= prev_c - 1e-6, f"Milestone energy decreased: {m}"
            assert m["cosine"] >= prev_cos - 1e-6, f"Milestone cosine decreased: {m}"
            prev_c = m["c_p"]
            prev_cos = m["cosine"]

        prev_cos = 0.0
        for pt in r1["curve"]:
            assert pt["cosine"] >= prev_cos - 1e-6, f"Curve cosine decreased: {pt}"
            prev_cos = pt["cosine"]

    def test_dynamic_recomputation_with_custom_beta(self, client: TestClient) -> None:
        """Custom beta query parameter must be reflected in the response."""
        res = client.get("/api/v1/toppaper/energy-distribution?beta=0.6&force_recompute=true")
        assert res.status_code == 200
        data = res.json()
        assert abs(data["beta"] - 0.6) < 1e-6
        assert data["source"] == "dynamic_recomputed"


class TestEnergyDistributionUIAndDocs:
    """Verify HTML elements, Chart.js canvas, and sorting complexity documentation."""

    def test_html_contains_sorting_complexity_docs(self) -> None:
        """Step 1 documentation must contain Appendix B sorting complexity note."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert "Sorting Complexity" in html
        assert "Appendix B, Page 29" in html
        assert "T_{\\text{ref}}" in html

    def test_html_contains_energy_panel_elements(self) -> None:
        """HTML must contain #energy-panel, #btn-compute-energy, chart canvas, and JS function."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert 'id="energy-panel"' in html
        assert 'id="btn-compute-energy"' in html
        assert 'id="chart-energy-curve"' in html
        assert "function loadEnergyDistribution" in html
