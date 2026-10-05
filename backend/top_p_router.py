from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
import torch

from .top_p_lab import run_demo
from .top_p_costs import CostModelRequest, compute_cost_model
from backend.models.cifar_cnn import CIFAR10CNN
from backend.models.flattening import (
    CANONICAL_LAYER_ORDER,
    flatten_parameters,
    load_flat_parameters_artifact,
    save_flat_parameters_artifact,
)
from backend.training.train_cifar import TrainingConfig, train_cifar_model

router = APIRouter(prefix="/api/v1/toppaper", tags=["top-p-lab"])

# Module-level path constant — overridable via monkeypatch in tests
ROUNDS_DIR: Path = Path("output/models/rounds")


class TopPRequest(BaseModel):
    n: int = Field(9, ge=3, le=60)
    M: int = Field(2000, ge=50, le=20000)
    theta: float = Field(0.8, gt=0, le=1)
    q: float = Field(0.8, ge=0.5, le=1)
    beta: float = Field(0.9, ge=0, lt=1)
    rounds: int = Field(3, ge=1, le=20)
    seed: int = 0
    p_max: int | None = None


class CnnTrainingRequest(BaseModel):
    rounds: int = Field(1, ge=1, le=50, description="Number of sequential training rounds")
    epochs: int = Field(5, ge=1, le=100, description="Local epochs per round")
    batch_size: int = Field(64, ge=8, le=512, description="Mini-batch size")
    learning_rate: float = Field(0.01, gt=0.0, le=1.0, description="Learning rate")
    momentum: float = Field(0.9, ge=0.0, le=0.99, description="SGD momentum")
    weight_decay: float = Field(1e-4, ge=0.0, le=0.1, description="Weight decay (L2 regularisation). Must be in [0.0, 0.1].")
    seed: int = Field(42, description="Random seed for reproducibility")
    synthetic: bool = Field(False, description="Use synthetic dataset for fast execution")
    synthetic_samples: int = Field(512, ge=64, le=5000, description="Synthetic samples count")
    distribution: str = Field("full", description="Data distribution: 'full' (10 classes IID) or 'pathological_20' (2 classes / 20% non-IID as in Paper §5.1)")

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, v: str) -> str:
        if v not in ("full", "pathological_20"):
            raise ValueError(f"Invalid distribution '{v}'. Must be 'full' or 'pathological_20'.")
        return v

    @field_validator("weight_decay")
    @classmethod
    def weight_decay_in_range(cls, v: float) -> float:
        if v > 0.1:
            raise ValueError(
                f"weight_decay={v} is out of range. Must be ≤ 0.1 "
                "(Paper §5.1 uses 1e-4). Values above 0.1 cause over-regularisation."
            )
        return v


@router.post("/run")
def run(req: TopPRequest):
    return run_demo(req.n, req.M, req.theta, req.q, req.beta, req.rounds, req.seed, req.p_max)


@router.post("/costs")
def calculate_costs(req: CostModelRequest):
    return compute_cost_model(req)


@router.post("/train-cnn")
def train_cnn(req: CnnTrainingRequest) -> Dict[str, Any]:
    """Train CIFAR-10 CNN and persist checkpoint + flattened parameter artifact bundle."""
    config = TrainingConfig(
        rounds=req.rounds,
        epochs=req.epochs,
        batch_size=req.batch_size,
        learning_rate=req.learning_rate,
        momentum=req.momentum,
        weight_decay=req.weight_decay,
        seed=req.seed,
        synthetic=req.synthetic,
        synthetic_samples=req.synthetic_samples,
        distribution=req.distribution,
        output_dir="output/models",
        checkpoint_dir="output/models/rounds",
    )

    # 1. Run model training
    model, result = train_cifar_model(config)

    # 2. Extract and persist deterministic flat parameter artifact
    flat_tensor, metadata = flatten_parameters(model)
    flat_path = Path("output/models/cifar10_flat_parameters.pt")
    save_flat_parameters_artifact(
        flat_tensor=flat_tensor,
        metadata=metadata,
        output_path=flat_path,
        source_checkpoint=result.checkpoint_path,
    )

    return {
        "final_train_loss": result.final_train_loss,
        "final_train_accuracy": result.final_train_accuracy,
        "final_test_loss": result.final_test_loss,
        "final_test_accuracy": result.final_test_accuracy,
        "duration_seconds": round(result.duration_seconds, 2),
        "round_history": result.round_history,
        "epoch_history": result.epoch_history,
        "checkpoint_path": result.checkpoint_path,
        "metadata_path": result.metadata_path,
        "distribution": config.distribution,
        "target_classes": config.target_classes,
    }



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


@router.get("/round-importance")
def get_round_importance(
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor β ∈ [0, 0.99]"),
    top_k: int = Query(20, ge=5, le=500, description="Items per page (rank slice size)"),
    offset: int = Query(0, ge=0, description="Pagination offset — rank start (0-indexed)"),
    force_recompute: bool = Query(False, description="Bypass cache and force on-demand recalculation"),
) -> Dict[str, Any]:
    """Compute multi-round EMA importance scores and return side-by-side comparison data.

    For each saved round flat-parameter artifact the EMA chain is:
        s^(1) = |w^(1)|
        s^(t) = β · s^(t-1) + (1 - β) · |w^(t)|   for t > 1

    Fast Path (< 10ms):
        When force_recompute=False and beta=0.9, attempts to load from the precomputed
        cache file `cifar10_importance_cache_beta09.pt` if present.
    """
    import backend.top_p_router as _self_module  # resolve monkeypatched ROUNDS_DIR at call time
    rounds_dir: Path = _self_module.ROUNDS_DIR

    # ── 1. Discover round artifacts in ascending round order ────────────────
    import re as _re
    round_files: List[tuple] = []  # (round_number, Path)
    if rounds_dir.exists():
        for f in rounds_dir.iterdir():
            m = _re.match(r"cifar10_flat_round_(\d+)\.pt$", f.name)
            if m:
                round_files.append((int(m.group(1)), f))
    round_files.sort(key=lambda x: x[0])

    # ── 2. Empty-state graceful response ────────────────────────────────────
    if not round_files:
        return {
            "has_data": False,
            "total_rounds": 0,
            "beta": beta,
            "offset": offset,
            "top_k": top_k,
            "total_parameters": 0,
            "rounds": [],
            "rounds_data": [],
            "source": "dynamic_recomputed",
        }

    # ── 2b. Fast-Path: Pre-Computed Cache (beta = 0.9) ──────────────────────
    if not force_recompute and abs(beta - 0.9) < 1e-6:
        cache_path = rounds_dir / "cifar10_importance_cache_beta09.pt"
        if cache_path.exists():
            try:
                cached_data = torch.load(cache_path, weights_only=False)
                cached_rounds = cached_data.get("rounds_data", cached_data.get("rounds", []))
                cached_top_k = cached_data.get("cached_top_k", len(cached_rounds[0]["items"]) if cached_rounds else 0)
                if (
                    cached_rounds
                    and len(cached_rounds) == len(round_files)
                    and (offset + top_k) <= cached_top_k
                ):
                    sliced_rounds = []
                    for rd in cached_rounds:
                        sliced_items = rd["items"][offset : offset + top_k]
                        sliced_rounds.append({"round": rd["round"], "items": sliced_items})
                    return {
                        "has_data": True,
                        "total_rounds": cached_data.get("total_rounds", len(round_files)),
                        "beta": 0.9,
                        "offset": offset,
                        "top_k": top_k,
                        "total_parameters": cached_data.get("total_parameters", 0),
                        "rounds": sliced_rounds,
                        "rounds_data": sliced_rounds,
                        "source": "cached_beta_0.9",
                    }
            except Exception:
                pass  # Fall back to dynamic calculation

    # ── 3. Load all round tensors & metadata once ───────────────────────────
    round_tensors: List[torch.Tensor] = []
    all_layer_slices: Dict[str, Any] = {}
    for _, fpath in round_files:
        ft, meta = load_flat_parameters_artifact(fpath)
        round_tensors.append(ft.float())
        if not all_layer_slices:
            all_layer_slices = meta.get("layer_slices", {})

    total_params = int(round_tensors[0].numel())

    # ── 4. Chain EMA scores ─────────────────────────────────────────────────
    ema_scores: List[torch.Tensor] = []
    prev_score: Optional[torch.Tensor] = None
    for wt in round_tensors:
        abs_wt = torch.abs(wt)
        if prev_score is None:
            st = abs_wt.clone()
        else:
            st = beta * prev_score + (1.0 - beta) * abs_wt
        ema_scores.append(st)
        prev_score = st

    # ── 5. Rank each round: descending score, ties broken by ascending index ─
    #   argsort(-score) with stable sort = ascending index tie-break
    round_ranks: List[torch.Tensor] = []  # rank_order[i] = global_index at rank i
    round_rank_of_index: List[Dict[int, int]] = []  # index → rank (1-based)
    for st in ema_scores:
        # stable sort on negated scores → ties go to lower index first
        sorted_indices = torch.argsort(-st, stable=True)
        round_ranks.append(sorted_indices)
        rank_of_idx = {int(sorted_indices[r].item()): r + 1 for r in range(total_params)}
        round_rank_of_index.append(rank_of_idx)

    # ── 6. Build paginated per-round items ──────────────────────────────────
    rounds_data: List[Dict[str, Any]] = []
    for t_idx, (round_num, _) in enumerate(round_files):
        sorted_indices = round_ranks[t_idx]
        st = ema_scores[t_idx]
        wt = round_tensors[t_idx]

        page_start = min(offset, total_params)
        page_end = min(offset + top_k, total_params)
        page_indices = sorted_indices[page_start:page_end]

        items: List[Dict[str, Any]] = []
        for rank_pos, global_idx_t in enumerate(page_indices):
            global_idx = int(global_idx_t.item())
            rank = page_start + rank_pos + 1  # 1-based rank

            # rank_delta: positive = improved rank (moved up), None for round 1
            if t_idx == 0:
                rank_delta = None
            else:
                prev_rank = round_rank_of_index[t_idx - 1].get(global_idx)
                rank_delta = None if prev_rank is None else (prev_rank - rank)

            raw_val = float(wt[global_idx].item())
            score_val = float(st[global_idx].item())
            layer_name = _get_layer_for_index(global_idx, all_layer_slices)

            items.append({
                "rank": rank,
                "rank_delta": rank_delta,
                "global_index": global_idx,
                "layer_name": layer_name,
                "score": round(score_val, 6),
                "value": round(raw_val, 6),
                "abs_value": round(abs(raw_val), 6),
            })

        rounds_data.append({"round": round_num, "items": items})

    return {
        "has_data": True,
        "total_rounds": len(round_files),
        "beta": beta,
        "offset": offset,
        "top_k": top_k,
        "total_parameters": total_params,
        "rounds": rounds_data,
        "rounds_data": rounds_data,
        "source": "dynamic_recomputed",
    }


@router.get("/energy-distribution")
def get_energy_distribution(
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor"),
    force_recompute: bool = Query(False, description="Force dynamic recalculation"),
) -> Dict[str, Any]:
    """Calculate or retrieve the cumulative energy distribution and prefix sums c_P across rounds.

    Computes total energy nu^2 = ||w||_2^2, L2 norm nu, prefix sums of sorted squared weights
    c_P = sum_{m=1}^P (w_{J_m})^2, and directional cosine similarity cos(P) = sqrt(c_P) / nu.
    """
    import backend.top_p_router as _self_module
    rounds_dir: Path = _self_module.ROUNDS_DIR

    import re as _re
    import math as _math
    import numpy as _np

    round_files: List[tuple] = []
    if rounds_dir.exists():
        for f in rounds_dir.iterdir():
            m = _re.match(r"cifar10_flat_round_(\d+)\.pt$", f.name)
            if m:
                round_files.append((int(m.group(1)), f))
    round_files.sort(key=lambda x: x[0])

    if not round_files:
        return {
            "has_data": False,
            "total_rounds": 0,
            "beta": beta,
            "total_parameters": 0,
            "rounds": [],
            "source": "dynamic_recomputed",
        }

    # Fast Path: Pre-Computed Cache (beta = 0.9)
    if not force_recompute and abs(beta - 0.9) < 1e-6:
        cache_path = rounds_dir / "cifar10_energy_cache_beta09.pt"
        if cache_path.exists():
            try:
                cached_data = torch.load(cache_path, weights_only=False)
                cached_rounds = cached_data.get("rounds", [])
                if cached_rounds and len(cached_rounds) == len(round_files):
                    return {
                        "has_data": True,
                        "total_rounds": cached_data.get("total_rounds", len(round_files)),
                        "beta": 0.9,
                        "total_parameters": cached_data.get("total_parameters", 0),
                        "rounds": cached_rounds,
                        "source": "cached_beta_0.9",
                    }
            except Exception:
                pass  # Fall back to dynamic calculation

    # Load all round tensors
    round_tensors: List[torch.Tensor] = []
    for _, fpath in round_files:
        ft, _ = load_flat_parameters_artifact(fpath)
        round_tensors.append(ft.float())

    total_params = int(round_tensors[0].numel())

    # Chain EMA scores
    ema_scores: List[torch.Tensor] = []
    prev_score: Optional[torch.Tensor] = None
    for wt in round_tensors:
        abs_wt = torch.abs(wt)
        if prev_score is None:
            st = abs_wt.clone()
        else:
            st = beta * prev_score + (1.0 - beta) * abs_wt
        ema_scores.append(st)
        prev_score = st

    candidate_p = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, total_params]
    sampled_p = sorted(list({p for p in candidate_p if 1 <= p <= total_params} | {1, total_params}))

    if total_params <= 60:
        curve_p_indices = list(range(1, total_params + 1))
    else:
        raw_p = _np.unique(_np.geomspace(1, total_params, num=min(60, total_params)).astype(int))
        curve_p_indices = sorted(list({int(p) for p in raw_p if 1 <= p <= total_params} | {1, total_params}))

    p_1pct = max(1, int(round(0.01 * total_params)))
    rounds_data: List[Dict[str, Any]] = []

    for t_idx, (round_num, _) in enumerate(round_files):
        st = ema_scores[t_idx]
        wt = round_tensors[t_idx]
        sorted_indices = torch.argsort(-st, stable=True)
        w_sorted_sq = (wt[sorted_indices]) ** 2
        c_prefix = torch.cumsum(w_sorted_sq, dim=0)
        nu_sq = float(c_prefix[-1].item())
        nu = _math.sqrt(max(0.0, nu_sq))

        c_1pct = float(c_prefix[p_1pct - 1].item())
        top_1pct_energy_pct = (c_1pct / max(1e-12, nu_sq)) * 100.0

        milestones = []
        for p in sampled_p:
            if p == total_params:
                c_p = nu_sq
                ep = 100.0
                cos_val = 1.0
            else:
                c_p = float(c_prefix[p - 1].item())
                ep = (c_p / max(1e-12, nu_sq)) * 100.0
                cos_val = _math.sqrt(max(0.0, c_p)) / max(1e-12, nu) if nu > 0 else 0.0
                cos_val = min(1.0, cos_val)
            milestones.append({
                "p": p,
                "c_p": round(c_p, 6),
                "energy_pct": round(ep, 4),
                "cosine": round(cos_val, 6),
            })

        curve_points = []
        for p in curve_p_indices:
            if p == total_params:
                c_p = nu_sq
                ep = 100.0
                cos_val = 1.0
            else:
                c_p = float(c_prefix[p - 1].item())
                ep = (c_p / max(1e-12, nu_sq)) * 100.0
                cos_val = _math.sqrt(max(0.0, c_p)) / max(1e-12, nu) if nu > 0 else 0.0
                cos_val = min(1.0, cos_val)
            curve_points.append({
                "p": p,
                "c_p": round(c_p, 6),
                "energy_pct": round(ep, 4),
                "cosine": round(cos_val, 6),
            })

        rounds_data.append({
            "round": round_num,
            "nu_sq": round(nu_sq, 6),
            "total_energy": round(nu_sq, 6),
            "nu": round(nu, 6),
            "l2_norm": round(nu, 6),
            "top_1pct_energy_pct": round(top_1pct_energy_pct, 4),
            "milestones": milestones,
            "curve": curve_points,
            "curve_data": curve_points,
        })

    return {
        "has_data": True,
        "total_rounds": len(round_files),
        "beta": beta,
        "total_parameters": total_params,
        "rounds": rounds_data,
        "source": "dynamic_recomputed",
    }


@router.get("/binary-search-pmin")
def get_binary_search_pmin(
    theta: float = Query(0.8, gt=0.0, le=1.0, description="Target cosine similarity threshold"),
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor"),
    round_num: int = Query(1, ge=1, description="Round to inspect (defaults to 1 or latest)"),
    tolerance: int = Query(1, ge=1, description="Binary search termination tolerance eps_P"),
    force_recompute: bool = Query(False, description="Force dynamic recalculation"),
) -> Dict[str, Any]:
    """Execute Algorithm 1 (Appendix B / Page 29) binary search for minimal coordinate budget P_min.

    Finds min P in [1, M] such that cos(w, w^[P]) >= theta <=> c_P >= theta^2 * ||w||_2^2.
    Returns step-by-step iteration trace, achieved cosine, sparsity gain, and logarithmic complexity.
    """
    import backend.top_p_router as _self_module
    rounds_dir: Path = _self_module.ROUNDS_DIR

    import re as _re
    import math as _math

    # 1. Discover round files
    round_files: List[tuple] = []
    if rounds_dir.exists():
        for f in rounds_dir.iterdir():
            m = _re.match(r"cifar10_flat_round_(\d+)\.pt$", f.name)
            if m:
                round_files.append((int(m.group(1)), f))
    round_files.sort(key=lambda x: x[0])

    fallback_file: Optional[Path] = None
    if not round_files:
        canonical_flat = rounds_dir / "cifar10_flat_parameters.pt"
        if canonical_flat.exists():
            fallback_file = canonical_flat
        else:
            return {
                "has_data": False,
                "total_parameters": 0,
                "theta": theta,
                "beta": beta,
                "round_num": round_num,
                "p_min": 0,
                "achieved_cosine": 0.0,
                "sparsity_percentage": 0.0,
                "retained_percentage": 0.0,
                "nu_sq": 0.0,
                "nu": 0.0,
                "c_pmin": 0.0,
                "total_checks": 0,
                "trace": [],
                "available_rounds": [],
                "source": "empty",
            }

    # 2. Select target round and chain EMA scores
    available_rounds = [r[0] for r in round_files] if round_files else [1]
    if round_files:
        effective_idx = min(len(round_files) - 1, max(0, round_num - 1))
        target_round = round_files[effective_idx][0]

        ema_score: Optional[torch.Tensor] = None
        target_w: Optional[torch.Tensor] = None
        for i in range(effective_idx + 1):
            wt, _ = load_flat_parameters_artifact(round_files[i][1])
            wt = wt.float()
            abs_w = torch.abs(wt)
            if ema_score is None:
                ema_score = abs_w.clone()
            else:
                ema_score = beta * ema_score + (1.0 - beta) * abs_w
            if i == effective_idx:
                target_w = wt
    else:
        target_round = 1
        target_w, _ = load_flat_parameters_artifact(fallback_file)  # type: ignore[arg-type]
        target_w = target_w.float()
        ema_score = torch.abs(target_w)

    total_params = int(target_w.numel())
    if total_params == 0:
        return {
            "has_data": False,
            "total_parameters": 0,
            "theta": theta,
            "beta": beta,
            "round_num": target_round,
            "p_min": 0,
            "achieved_cosine": 0.0,
            "sparsity_percentage": 0.0,
            "retained_percentage": 0.0,
            "nu_sq": 0.0,
            "nu": 0.0,
            "c_pmin": 0.0,
            "total_checks": 0,
            "trace": [],
            "available_rounds": available_rounds,
            "source": "empty",
        }

    # 3. Sort coordinates descending by score s
    sorted_indices = torch.argsort(-ema_score, stable=True)
    w_sorted_sq = (target_w[sorted_indices]) ** 2
    c_prefix = torch.cumsum(w_sorted_sq, dim=0)
    nu_sq = float(c_prefix[-1].item())
    nu = _math.sqrt(max(0.0, nu_sq))

    if nu_sq == 0.0:
        return {
            "has_data": True,
            "total_parameters": total_params,
            "theta": theta,
            "beta": beta,
            "round_num": target_round,
            "p_min": 1,
            "achieved_cosine": 1.0,
            "sparsity_percentage": round((1.0 - 1.0 / total_params) * 100.0, 4),
            "retained_percentage": round((1.0 / total_params) * 100.0, 4),
            "nu_sq": 0.0,
            "nu": 0.0,
            "c_pmin": 0.0,
            "total_checks": 0,
            "trace": [],
            "available_rounds": available_rounds,
            "source": "dynamic_recomputed",
        }

    # 4. Binary Search Loop (Algorithm 1)
    threshold_energy = (theta ** 2) * nu_sq - 1e-9
    lo = 1
    hi = total_params
    trace: List[Dict[str, Any]] = []
    step_num = 1

    while (hi - lo) >= tolerance:
        mid = (lo + hi) // 2
        c_mid = float(c_prefix[mid - 1].item())
        ok = (c_mid >= threshold_energy)
        cos_mid = _math.sqrt(max(0.0, c_mid)) / max(1e-12, nu) if nu > 0 else 0.0
        cos_mid = min(1.0, cos_mid)

        if ok:
            action = f"Feasible (cos={cos_mid:.7f} ≥ {theta:.7f}): tighten upper bound hi = {mid}"
            trace.append({
                "step": step_num,
                "lo": lo,
                "hi": hi,
                "mid": mid,
                "c_mid": round(c_mid, 6),
                "cos_mid": round(cos_mid, 7),
                "cos": round(cos_mid, 7),
                "feasible": True,
                "action": action,
            })
            hi = mid
        else:
            action = f"Below θ (cos={cos_mid:.7f} < {theta:.7f}): advance lower bound lo = {mid + 1}"
            trace.append({
                "step": step_num,
                "lo": lo,
                "hi": hi,
                "mid": mid,
                "c_mid": round(c_mid, 6),
                "cos_mid": round(cos_mid, 7),
                "cos": round(cos_mid, 7),
                "feasible": False,
                "action": action,
            })
            lo = mid + 1
        step_num += 1

    p_min = hi
    c_pmin = float(c_prefix[p_min - 1].item())
    achieved_cosine = _math.sqrt(max(0.0, c_pmin)) / max(1e-12, nu) if nu > 0 else 1.0
    achieved_cosine = min(1.0, achieved_cosine)

    sparsity_percentage = round((1.0 - (p_min / total_params)) * 100.0, 4)
    retained_percentage = round((p_min / total_params) * 100.0, 4)

    return {
        "has_data": True,
        "total_parameters": total_params,
        "theta": theta,
        "beta": beta,
        "round_num": target_round,
        "p_min": p_min,
        "achieved_cosine": round(achieved_cosine, 7),
        "sparsity_percentage": sparsity_percentage,
        "retained_percentage": retained_percentage,
        "nu_sq": round(nu_sq, 6),
        "nu": round(nu, 6),
        "c_pmin": round(c_pmin, 6),
        "total_checks": len(trace),
        "trace": trace,
        "available_rounds": available_rounds,
        "source": "dynamic_recomputed",
    }
