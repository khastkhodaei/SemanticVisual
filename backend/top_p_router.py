from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
import torch

from .top_p_lab import run_demo
from .top_p_costs import CostModelRequest, compute_cost_model
from backend.models.cifar_cnn import CIFAR10CNN
from backend.models.flattening import (
    CANONICAL_LAYER_ORDER,
    flatten_parameters,
    load_flat_parameters_artifact,
)

router = APIRouter(prefix="/api/v1/toppaper", tags=["top-p-lab"])


class TopPRequest(BaseModel):
    n: int = Field(9, ge=3, le=60)
    M: int = Field(2000, ge=50, le=20000)
    theta: float = Field(0.8, gt=0, le=1)
    q: float = Field(0.8, ge=0.5, le=1)
    beta: float = Field(0.9, ge=0, lt=1)
    rounds: int = Field(3, ge=1, le=20)
    seed: int = 0
    p_max: int | None = None


@router.post("/run")
def run(req: TopPRequest):
    return run_demo(req.n, req.M, req.theta, req.q, req.beta, req.rounds, req.seed, req.p_max)


@router.post("/costs")
def calculate_costs(req: CostModelRequest):
    return compute_cost_model(req)


def _get_layer_for_index(idx: int, layer_slices: Dict[str, Any]) -> str:
    """Resolve the originating layer name for a given global flat index."""
    for layer_name, info in layer_slices.items():
        if info["start_idx"] <= idx < info["end_idx"]:
            return layer_name
    return "unknown"


@router.get("/cnn-weights")
def get_cnn_weights(
    head: int = Query(15, ge=1, le=500, description="Number of starting parameters to inspect"),
    tail: int = Query(15, ge=1, le=500, description="Number of ending parameters to inspect"),
    top_k: int = Query(20, ge=1, le=500, description="Number of highest absolute magnitude weights"),
) -> Dict[str, Any]:
    """Inspect true flattened weights from the trained CIFAR-10 CNN model."""
    flat_path = Path("output/models/cifar10_flat_parameters.pt")
    ckpt_path = Path("output/models/cifar10_cnn_checkpoint.pt")

    flat_tensor: Optional[torch.Tensor] = None
    metadata: Dict[str, Any] = {}

    if flat_path.exists():
        flat_tensor, metadata = load_flat_parameters_artifact(flat_path)
    elif ckpt_path.exists():
        model, _ = CIFAR10CNN.load_checkpoint(ckpt_path)
        flat_tensor, metadata = flatten_parameters(model)
    else:
        # Graceful fallback to fresh CIFAR10CNN architecture instance
        model = CIFAR10CNN()
        flat_tensor, metadata = flatten_parameters(model)

    total_params = int(flat_tensor.numel())
    l2_norm = round(float(torch.linalg.norm(flat_tensor).item()), 4)
    layer_slices = metadata.get("layer_slices", {})

    # 1. Head items (first `head` parameters)
    head_count = min(head, total_params)
    head_items: List[Dict[str, Any]] = []
    for i in range(head_count):
        raw_val = float(flat_tensor[i].item())
        head_items.append({
            "index": i,
            "layer": _get_layer_for_index(i, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 2. Tail items (last `tail` parameters)
    tail_count = min(tail, total_params)
    tail_start = total_params - tail_count
    tail_items: List[Dict[str, Any]] = []
    for i in range(tail_count):
        idx = tail_start + i
        raw_val = float(flat_tensor[idx].item())
        tail_items.append({
            "index": idx,
            "layer": _get_layer_for_index(idx, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 3. Top-K magnitude items
    top_k_count = min(top_k, total_params)
    abs_tensor = torch.abs(flat_tensor)
    top_values, top_indices = torch.topk(abs_tensor, k=top_k_count)
    top_magnitude_items: List[Dict[str, Any]] = []
    for val_t, idx_t in zip(top_values, top_indices):
        idx = int(idx_t.item())
        raw_val = float(flat_tensor[idx].item())
        top_magnitude_items.append({
            "index": idx,
            "layer": _get_layer_for_index(idx, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 4. Layer distribution summary
    layer_summary: List[Dict[str, Any]] = []
    for layer_name in CANONICAL_LAYER_ORDER:
        if layer_name in layer_slices:
            info = layer_slices[layer_name]
            layer_summary.append({
                "layer": layer_name,
                "count": info["numel"],
                "start": info["start_idx"],
                "end": info["end_idx"],
                "shape": info["shape"],
                "percentage": round(100.0 * info["numel"] / total_params, 2),
            })

    return {
        "total_parameters": total_params,
        "l2_norm": l2_norm,
        "slices": {
            "head": head_items,
            "tail": tail_items,
            "top_magnitude": top_magnitude_items,
        },
        "layer_distribution_summary": layer_summary,
        "checkpoint_info": {
            "model_name": "CIFAR10CNN",
            "dataset": "CIFAR-10",
            "checkpoint_exists": ckpt_path.exists(),
            "flat_artifact_exists": flat_path.exists(),
        },
    }
