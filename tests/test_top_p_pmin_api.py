"""Integration tests for GET /api/v1/toppaper/binary-search-pmin endpoint and Step 3 panel.

Seam: the public HTTP interface of the Step 3 Minimal Signature Budget Search (P_min & Algorithm 1 Trace).
Verifies:
1. Empty-state graceful handling.
2. Exact mathematical correctness of Algorithm 1 binary search against analytical models.
3. Monotonicity of P_min with respect to theta.
4. Logarithmic iteration complexity bound ceil(log2 M).
5. HTML DOM structure and interactive function bindings.
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


class TestPminEmptyState:
    """Endpoint must degrade gracefully when no round artifacts exist."""

    def test_empty_state_returns_200_with_has_data_false(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        empty_dir = tmp_path / "empty_rounds_dir"
        empty_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(router_mod, "ROUNDS_DIR", empty_dir)

        res = client.get("/api/v1/toppaper/binary-search-pmin")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is False
        assert data["p_min"] == 0
        assert data["trace"] == []


class TestPminAlgorithm1Math:
    """Verify exact binary search convergence, feasibility, and monotonicity."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.rounds_dir = tmp_path / "rounds_pmin_math"
        self.rounds_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(router_mod, "ROUNDS_DIR", self.rounds_dir)

        # Vector with known values: [3.0, -4.0]
        # Sorted descending: |-4.0| (sq=16), |3.0| (sq=9)
        # nu^2 = 25.0, nu = 5.0
        # P = 1: c_1 = 16.0, cos(1) = 0.8
        # P = 2: c_2 = 25.0, cos(2) = 1.0
        w1 = torch.tensor([3.0, -4.0], dtype=torch.float32)
        _make_flat_artifact(w1, self.rounds_dir / "cifar10_flat_round_1.pt")

    def test_pmin_boundary_conditions(self, client: TestClient) -> None:
        """Theta = 0.8 must resolve to P_min = 1, theta = 0.85 must resolve to P_min = 2."""
        # Case 1: theta = 0.80 -> P=1 meets exactly cos=0.8
        res = client.get("/api/v1/toppaper/binary-search-pmin?theta=0.8&beta=0.0&round_num=1")
        assert res.status_code == 200
        data = res.json()
        assert data["has_data"] is True
        assert data["p_min"] == 1
        assert abs(data["achieved_cosine"] - 0.8) < 1e-4
        assert data["sparsity_percentage"] == 50.0
        assert data["retained_percentage"] == 50.0

        # Case 2: theta = 0.85 -> P=1 has cos=0.8 < 0.85, so must pick P=2
        res2 = client.get("/api/v1/toppaper/binary-search-pmin?theta=0.85&beta=0.0&round_num=1")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["p_min"] == 2
        assert abs(data2["achieved_cosine"] - 1.0) < 1e-4

        # Case 3: theta = 1.0 -> must pick P=M=2
        res3 = client.get("/api/v1/toppaper/binary-search-pmin?theta=1.0&beta=0.0&round_num=1")
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["p_min"] == 2
        assert abs(data3["achieved_cosine"] - 1.0) < 1e-4

    def test_monotonicity_and_logarithmic_complexity(self, client: TestClient) -> None:
        """P_min must be monotonic non-decreasing with theta and iterations <= ceil(log2 M) + 1."""
        # 16-parameter tensor
        w = torch.tensor([float(i) for i in range(1, 17)], dtype=torch.float32)
        _make_flat_artifact(w, self.rounds_dir / "cifar10_flat_round_1.pt")

        thetas = [0.2, 0.4, 0.6, 0.75, 0.85, 0.95, 1.0]
        prev_p = 0
        for th in thetas:
            res = client.get(f"/api/v1/toppaper/binary-search-pmin?theta={th}&beta=0.9&round_num=1")
            assert res.status_code == 200
            d = res.json()
            p_min = d["p_min"]
            assert p_min >= prev_p, f"P_min decreased from {prev_p} to {p_min} for higher theta={th}"
            assert d["achieved_cosine"] >= th - 1e-5, f"Achieved cosine {d['achieved_cosine']} < target {th}"
            
            # Binary search trace check
            trace = d["trace"]
            assert len(trace) <= math.ceil(math.log2(16)) + 1
            assert d["total_checks"] == len(trace)
            prev_p = p_min


class TestPminUIAndDocs:
    """Verify HTML elements and JavaScript state handlers for Step 3."""

    def test_html_contains_pmin_panel_elements(self) -> None:
        """HTML must contain #pmin-panel, #inp-pmin-theta, #btn-run-pmin-search, #table-pmin-trace."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        assert 'id="pmin-panel"' in html
        assert 'id="inp-pmin-theta"' in html
        assert 'id="btn-run-pmin-search"' in html
        assert 'id="table-pmin-trace"' in html
        assert "function runPminBinarySearch" in html
