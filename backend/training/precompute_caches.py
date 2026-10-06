"""Ahead-of-Time Precomputation Engine for Top-P Benchmark Analytics.

Generates precomputed caches for all 5 benchmark models across all 100 rounds:
1. Multi-Round Importance Scores & Coordinate Ranking (Step 1)
2. Cumulative Energy Distribution & Geometry Curve (Step 2)
3. Algorithm 1 Binary Search Minimum Coordinate Budget P_min (Step 3)

This drops downstream UI response time from >100 seconds to <5 milliseconds.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from backend.models.flattening import load_flat_parameters_artifact
from backend.top_p_router import (
    BENCHMARK_FILE_PATTERNS,
    find_round_files_for_benchmark,
)

logger = logging.getLogger("PrecomputeCaches")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

CANONICAL_THETAS: List[float] = [0.8, 0.9, 0.95, 0.99, 1.0]


def _get_layer_for_index(idx: int, layer_slices: Dict[str, Any]) -> str:
    """Resolve originating layer name for global coordinate index."""
    for layer_name, info in layer_slices.items():
        if info["start_idx"] <= idx < info["end_idx"]:
            return layer_name
    return "unknown"


def run_binary_search_pmin_on_prefix(
    c_prefix: torch.Tensor,
    nu_sq: float,
    nu: float,
    total_params: int,
    theta: float,
    beta: float,
    round_num: int,
    bench: str,
    available_rounds: List[int],
    tolerance: int = 1,
) -> Dict[str, Any]:
    """Execute Algorithm 1 binary search on precomputed cumulative energy prefix tensor."""
    if nu_sq == 0.0 or nu == 0.0:
        return {
            "has_data": True,
            "benchmark": bench,
            "total_parameters": total_params,
            "theta": theta,
            "beta": beta,
            "round_num": round_num,
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
            "source": "cached_beta_0.9",
        }

    threshold_energy = (theta ** 2) * nu_sq - 1e-9
    lo = 1
    hi = total_params
    trace: List[Dict[str, Any]] = []
    step_num = 1

    while (hi - lo) >= tolerance:
        mid = (lo + hi) // 2
        c_mid = float(c_prefix[mid - 1].item())
        cond_met = c_mid >= threshold_energy
        mid_cos = math.sqrt(max(0.0, c_mid)) / nu if nu > 0 else 0.0
        mid_cos = min(1.0, mid_cos)

        if cond_met:
            action = "shrink_high"
            next_hi = mid
            next_lo = lo
        else:
            action = "expand_low"
            next_lo = mid + 1
            next_hi = hi

        trace.append({
            "step": step_num,
            "low": lo,
            "high": hi,
            "lo": lo,
            "hi": hi,
            "mid": mid,
            "c_mid": round(c_mid, 6),
            "mid_cosine": round(mid_cos, 7),
            "cos_mid": round(mid_cos, 7),
            "cos": round(mid_cos, 7),
            "condition_met": cond_met,
            "feasible": cond_met,
            "action": action,
        })

        lo = next_lo
        hi = next_hi
        step_num += 1

    p_min = lo
    c_pmin = float(c_prefix[p_min - 1].item())
    achieved_cosine = math.sqrt(max(0.0, c_pmin)) / nu if nu > 0 else 0.0
    achieved_cosine = min(1.0, achieved_cosine)

    sparsity_pct = (1.0 - float(p_min) / float(total_params)) * 100.0
    retained_pct = (float(p_min) / float(total_params)) * 100.0

    return {
        "has_data": True,
        "benchmark": bench,
        "total_parameters": total_params,
        "theta": theta,
        "beta": beta,
        "round_num": round_num,
        "p_min": p_min,
        "achieved_cosine": round(achieved_cosine, 7),
        "sparsity_percentage": round(sparsity_pct, 4),
        "retained_percentage": round(retained_pct, 4),
        "nu_sq": round(nu_sq, 6),
        "nu": round(nu, 6),
        "c_pmin": round(c_pmin, 6),
        "total_checks": len(trace),
        "trace": trace,
        "available_rounds": available_rounds,
        "source": "cached_beta_0.9",
    }


def precompute_caches_for_benchmark(
    benchmark: str,
    rounds_dir: Optional[Path] = None,
    beta: float = 0.9,
    top_k: int = 1000,
    thetas: Optional[List[float]] = None,
) -> Dict[str, Path]:
    """Precompute and persist Step 1, Step 2, and Step 3 caches for a benchmark."""
    if thetas is None:
        thetas = CANONICAL_THETAS

    bench = benchmark.lower()
    meta = BENCHMARK_FILE_PATTERNS.get(bench)
    if not meta:
        raise ValueError(f"Unknown benchmark: {bench}")

    if rounds_dir is None:
        rounds_dir = Path("output/models/rounds").resolve()

    round_files, target_dir = find_round_files_for_benchmark(rounds_dir, bench)
    if not round_files:
        logger.warning("No round files found for benchmark: %s in %s", bench, rounds_dir)
        return {}

    total_rounds = len(round_files)
    logger.info("Processing benchmark '%s': %d round files found in %s", bench, total_rounds, target_dir)

    # Inspect first round to determine total parameters and layer slices
    first_tensor, first_meta = load_flat_parameters_artifact(round_files[0][1])
    total_params = int(first_tensor.numel())
    all_layer_slices = first_meta.get("layer_slices", {})
    available_rounds = [r[0] for r in round_files]
    effective_top_k = min(top_k, total_params)

    del first_tensor, first_meta

    # Candidate P indices for Step 2
    candidate_p = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, total_params]
    sampled_p = sorted(list({p for p in candidate_p if 1 <= p <= total_params} | {1, total_params}))

    if total_params <= 60:
        curve_p_indices = list(range(1, total_params + 1))
    else:
        raw_p = np.unique(np.geomspace(1, total_params, num=min(60, total_params)).astype(int))
        curve_p_indices = sorted(list({int(p) for p in raw_p if 1 <= p <= total_params} | {1, total_params}))

    p_1pct = max(1, int(round(0.01 * total_params)))

    importance_rounds_data: List[Dict[str, Any]] = []
    energy_rounds_data: List[Dict[str, Any]] = []
    pmin_rounds_data: Dict[str, Dict[str, Any]] = {}

    prev_score: Optional[torch.Tensor] = None
    prev_inv_ranks: Optional[torch.Tensor] = None

    logger.info("[%s] Streaming across %d rounds (total_params=%d, beta=%.2f)...", bench, total_rounds, total_params, beta)

    for t_idx, (round_num, fpath) in enumerate(round_files):
        wt, _ = load_flat_parameters_artifact(fpath)
        wt = wt.float()

        abs_wt = torch.abs(wt)
        if prev_score is None:
            st = abs_wt
        else:
            st = beta * prev_score + (1.0 - beta) * abs_wt

        # Sort coordinates descending by EMA score
        sorted_indices = torch.argsort(-st, stable=True)

        # Build Step 1 Importance items for top_k
        top_indices = sorted_indices[:effective_top_k]
        items: List[Dict[str, Any]] = []
        for rank_pos, g_idx_t in enumerate(top_indices):
            global_idx = int(g_idx_t.item())
            rank = rank_pos + 1
            if prev_inv_ranks is None:
                rank_delta = None
            else:
                prev_rank = int(prev_inv_ranks[global_idx].item())
                rank_delta = prev_rank - rank

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
        importance_rounds_data.append({"round": round_num, "items": items})

        # Build Step 2 Energy & Step 3 P_min
        w_sorted_sq = (wt[sorted_indices]) ** 2
        c_prefix = torch.cumsum(w_sorted_sq, dim=0)
        nu_sq = float(c_prefix[-1].item())
        nu = math.sqrt(max(0.0, nu_sq))

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
                cos_val = math.sqrt(max(0.0, c_p)) / max(1e-12, nu) if nu > 0 else 0.0
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
                cos_val = math.sqrt(max(0.0, c_p)) / max(1e-12, nu) if nu > 0 else 0.0
                cos_val = min(1.0, cos_val)
            curve_points.append({
                "p": p,
                "c_p": round(c_p, 6),
                "energy_pct": round(ep, 4),
                "cosine": round(cos_val, 6),
            })

        energy_rounds_data.append({
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

        # Algorithm 1 binary search for canonical thetas
        round_pmin_thetas: Dict[str, Any] = {}
        for th in thetas:
            th_key = f"{th:.2f}"
            round_pmin_thetas[th_key] = run_binary_search_pmin_on_prefix(
                c_prefix=c_prefix,
                nu_sq=nu_sq,
                nu=nu,
                total_params=total_params,
                theta=th,
                beta=beta,
                round_num=round_num,
                bench=bench,
                available_rounds=available_rounds,
            )
        pmin_rounds_data[str(round_num)] = round_pmin_thetas

        # Update inverse rank tensor for next round's rank_delta
        current_inv_ranks = torch.empty(total_params, dtype=torch.int32)
        current_inv_ranks[sorted_indices] = torch.arange(1, total_params + 1, dtype=torch.int32)
        prev_inv_ranks = current_inv_ranks
        prev_score = st

        del wt, abs_wt, sorted_indices, top_indices, w_sorted_sq, c_prefix

    importance_payload = {
        "has_data": True,
        "benchmark": bench,
        "total_rounds": total_rounds,
        "beta": beta,
        "offset": 0,
        "top_k": effective_top_k,
        "total_parameters": total_params,
        "cached_top_k": effective_top_k,
        "rounds": importance_rounds_data,
        "rounds_data": importance_rounds_data,
        "source": "cached_beta_0.9",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    energy_payload = {
        "has_data": True,
        "benchmark": bench,
        "total_rounds": total_rounds,
        "beta": beta,
        "total_parameters": total_params,
        "rounds": energy_rounds_data,
        "source": "cached_beta_0.9",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    pmin_payload = {
        "has_data": True,
        "benchmark": bench,
        "beta": beta,
        "total_parameters": total_params,
        "available_rounds": available_rounds,
        "rounds": pmin_rounds_data,
        "source": "cached_beta_0.9",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # 6. Save cache artifacts to target benchmark directory
    imp_pt = target_dir / meta["importance_cache"]
    imp_json = target_dir / meta["importance_cache"].replace(".pt", ".json")
    torch.save(importance_payload, imp_pt)
    try:
        with open(imp_json, "w", encoding="utf-8") as f:
            json.dump(importance_payload, f, indent=2)
    except Exception as e:
        logger.warning("[%s] Could not save json importance cache: %s", bench, e)

    eng_pt = target_dir / meta["energy_cache"]
    eng_json = target_dir / meta["energy_cache"].replace(".pt", ".json")
    torch.save(energy_payload, eng_pt)
    try:
        with open(eng_json, "w", encoding="utf-8") as f:
            json.dump(energy_payload, f, indent=2)
    except Exception as e:
        logger.warning("[%s] Could not save json energy cache: %s", bench, e)

    pmin_pt = target_dir / meta["pmin_cache"]
    pmin_json = target_dir / meta["pmin_cache"].replace(".pt", ".json")
    torch.save(pmin_payload, pmin_pt)
    try:
        with open(pmin_json, "w", encoding="utf-8") as f:
            json.dump(pmin_payload, f, indent=2)
    except Exception as e:
        logger.warning("[%s] Could not save json pmin cache: %s", bench, e)

    logger.info("Successfully persisted all 3 caches for benchmark '%s' in %s", bench, target_dir)
    return {
        "importance": imp_pt,
        "energy": eng_pt,
        "pmin": pmin_pt,
    }


def precompute_all_benchmarks(
    rounds_dir: Optional[Path] = None,
    beta: float = 0.9,
    top_k: int = 1000,
) -> Dict[str, Dict[str, Path]]:
    """Precompute caches across all 5 benchmark models."""
    benchmarks = ["fmnist", "cifar10", "speech", "tiny_imagenet", "20news"]
    results: Dict[str, Dict[str, Path]] = {}
    for bench in benchmarks:
        logger.info("=== Starting Ahead-of-Time Precomputation for Benchmark [%s] ===", bench)
        try:
            cached_files = precompute_caches_for_benchmark(
                benchmark=bench,
                rounds_dir=rounds_dir,
                beta=beta,
                top_k=top_k,
            )
            results[bench] = cached_files
        except Exception as err:
            logger.error("Failed to precompute caches for [%s]: %s", bench, err, exc_info=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ahead-of-Time Top-P Cache Generator")
    parser.add_argument("--benchmark", type=str, default="all", help="Benchmark name (fmnist, cifar10, speech, tiny_imagenet, 20news, or 'all')")
    parser.add_argument("--rounds-dir", type=str, default="output/models/rounds", help="Base rounds directory")
    parser.add_argument("--beta", type=float, default=0.9, help="EMA smoothing factor")
    parser.add_argument("--top-k", type=int, default=1000, help="Number of coordinates to cache per round")
    args = parser.parse_args()

    rdir = Path(args.rounds_dir).resolve()
    if args.benchmark.lower() == "all":
        precompute_all_benchmarks(rounds_dir=rdir, beta=args.beta, top_k=args.top_k)
    else:
        precompute_caches_for_benchmark(benchmark=args.benchmark, rounds_dir=rdir, beta=args.beta, top_k=args.top_k)
