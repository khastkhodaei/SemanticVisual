"""Unit Tests for Ahead-of-Time Precomputation Engine."""

from __future__ import annotations

from pathlib import Path
import pytest
import torch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.flattening import save_flat_parameters_artifact
from backend.training.precompute_caches import precompute_caches_for_benchmark
import backend.top_p_router as router_mod


def _make_dummy_round(flat_tensor: torch.Tensor, path: Path, layer_name: str = "conv1.weight") -> None:
    meta = {
        "layer_slices": {
            layer_name: {
                "start_idx": 0,
                "end_idx": flat_tensor.numel(),
                "shape": [flat_tensor.numel()],
                "numel": flat_tensor.numel(),
            }
        },
        "l2_norm": float(torch.linalg.norm(flat_tensor).item()),
        "num_parameters": flat_tensor.numel(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    save_flat_parameters_artifact(flat_tensor=flat_tensor, metadata=meta, output_path=path)


def test_precompute_caches_engine_contract(tmp_path: Path):
    """Verify precompute_caches_for_benchmark produces valid, consumable cache artifacts."""
    router_mod.clear_ram_cache()

    mock_rounds = tmp_path / "rounds"
    sub_dir = mock_rounds / "cifar10"
    sub_dir.mkdir(parents=True, exist_ok=True)

    # Create 3 synthetic rounds
    t1 = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])
    t2 = torch.tensor([2.0, 2.0, 2.0, 4.0, 6.0])
    t3 = torch.tensor([0.5, 3.0, 1.0, 5.0, 7.0])

    _make_dummy_round(t1, sub_dir / "cifar10_flat_round_1.pt")
    _make_dummy_round(t2, sub_dir / "cifar10_flat_round_2.pt")
    _make_dummy_round(t3, sub_dir / "cifar10_flat_round_3.pt")

    res = precompute_caches_for_benchmark("cifar10", rounds_dir=mock_rounds, beta=0.9, top_k=5)

    assert "importance" in res
    assert "energy" in res
    assert "pmin" in res
    assert res["importance"].exists()
    assert res["energy"].exists()
    assert res["pmin"].exists()

    # Verify Importance Cache
    imp_data = torch.load(res["importance"], weights_only=False)
    assert imp_data["has_data"] is True
    assert imp_data["total_rounds"] == 3
    assert len(imp_data["rounds"]) == 3
    assert len(imp_data["rounds"][0]["items"]) == 5

    # Verify Energy Cache
    eng_data = torch.load(res["energy"], weights_only=False)
    assert eng_data["has_data"] is True
    assert eng_data["total_rounds"] == 3
    assert len(eng_data["rounds"]) == 3
    assert "milestones" in eng_data["rounds"][0]
    assert "curve" in eng_data["rounds"][0]

    # Verify P_min Cache
    pmin_data = torch.load(res["pmin"], weights_only=False)
    assert pmin_data["has_data"] is True
    assert "1" in pmin_data["rounds"]
    assert "0.80" in pmin_data["rounds"]["1"]
    assert pmin_data["rounds"]["1"]["0.80"]["source"] == "cached_beta_0.9"
