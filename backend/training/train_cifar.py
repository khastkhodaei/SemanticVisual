"""CIFAR-10 Model Training and Evaluation Pipeline.

Implements isolated, modular dataset ingestion, preprocessing, training, evaluation,
and deterministic artifact serialization for the SemanticDFL CIFAR-10 CNN.

Features:
- Reproducibility via multi-level random seed anchoring.
- Modular training and evaluation loops with typed configuration datastructures.
- Full artifact bundling (weights `.pt` + comprehensive `model_metadata.json`).
- CLI interface with parameter overrides.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset

from backend.models.cifar_cnn import CIFAR10CNN, CIFAR10_CLASSES
from backend.models.flattening import (
    flatten_parameters,
    load_flat_parameters_artifact,
    save_flat_parameters_artifact,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CIFAR10Trainer")


@dataclass
class TrainingConfig:
    """Configuration hyperparameter dataclass for CIFAR-10 training."""

    rounds: int = 1
    epochs: int = 5
    batch_size: int = 64
    learning_rate: float = 0.01
    momentum: float = 0.9
    weight_decay: float = 1e-4
    seed: int = 42
    output_dir: str = "output/models"
    checkpoint_dir: str = "output/models/rounds"
    data_dir: str = "data"
    synthetic: bool = False
    synthetic_samples: int = 512
    distribution: str = "full"
    target_classes: Optional[List[int]] = None
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_name: str = "cifar10_cnn_checkpoint.pt"


@dataclass
class TrainingResult:
    """Summary of completed training session."""

    final_train_loss: float
    final_train_accuracy: float
    final_test_loss: float
    final_test_accuracy: float
    epoch_history: List[Dict[str, Any]] = field(default_factory=list)
    round_history: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint_path: str = ""
    metadata_path: str = ""
    duration_seconds: float = 0.0



def set_seed(seed: int = 42) -> None:
    """Set deterministic seeds across standard library, NumPy, and PyTorch.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_dataloaders(config: TrainingConfig) -> Tuple[DataLoader, DataLoader]:
    """Acquire and prepare training and evaluation DataLoaders.

    If config.synthetic is True or if torchvision download is unavailable/fails,
    generates deterministic synthetic (B, 3, 32, 32) image batches for robust isolated testing.

    Args:
        config: TrainingConfig parameters.

    Returns:
        Tuple of (train_loader, test_loader).
    """
    if config.synthetic:
        logger.info("Using synthetic deterministic dataset of %d samples.", config.synthetic_samples)
        # Create deterministic synthetic tensors
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 3, 32, 32, generator=gen)
        test_samples = max(64, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 3, 32, 32, generator=gen)

        if config.distribution == "pathological_20":
            target_classes = list(config.target_classes) if (config.target_classes is not None and len(config.target_classes) > 0) else [0, 1]
            config.target_classes = target_classes
            logger.info("Applying 20% Pathological Label Skew with classes: %s", target_classes)
            target_tensor = torch.tensor(target_classes, dtype=torch.long)
            train_idx = torch.randint(0, len(target_classes), (config.synthetic_samples,), generator=gen)
            train_y = target_tensor[train_idx]
            test_idx = torch.randint(0, len(target_classes), (test_samples,), generator=gen)
            test_y = target_tensor[test_idx]
        else:
            train_y = torch.randint(0, 10, (config.synthetic_samples,), generator=gen)
            test_y = torch.randint(0, 10, (test_samples,), generator=gen)

        train_dataset = TensorDataset(train_x, train_y)
        test_dataset = TensorDataset(test_x, test_y)

        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=config.batch_size,
            shuffle=False,
        )
        return train_loader, test_loader

    try:
        import torchvision
        import torchvision.transforms as transforms

        cifar_mean = (0.4914, 0.4822, 0.4465)
        cifar_std = (0.2470, 0.2435, 0.2616)

        train_transform = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(cifar_mean, cifar_std),
        ])

        test_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(cifar_mean, cifar_std),
        ])

        data_path = Path(config.data_dir).resolve()
        data_path.mkdir(parents=True, exist_ok=True)

        logger.info("Loading CIFAR-10 from %s (download=True)...", data_path)
        train_dataset = torchvision.datasets.CIFAR10(
            root=str(data_path),
            train=True,
            download=True,
            transform=train_transform,
        )
        test_dataset = torchvision.datasets.CIFAR10(
            root=str(data_path),
            train=False,
            download=True,
            transform=test_transform,
        )

        if config.distribution == "pathological_20":
            target_classes = list(config.target_classes) if (config.target_classes is not None and len(config.target_classes) > 0) else [0, 1]
            config.target_classes = target_classes
            logger.info("Applying 20% Pathological Label Skew with classes: %s", target_classes)
            train_targets = train_dataset.targets if hasattr(train_dataset, "targets") else [y for _, y in train_dataset]
            train_indices = [i for i, label in enumerate(train_targets) if int(label) in target_classes]
            train_dataset = torch.utils.data.Subset(train_dataset, train_indices)

            test_targets = test_dataset.targets if hasattr(test_dataset, "targets") else [y for _, y in test_dataset]
            test_indices = [i for i, label in enumerate(test_targets) if int(label) in target_classes]
            test_dataset = torch.utils.data.Subset(test_dataset, test_indices)

        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=0,
            pin_memory=(config.device == "cuda"),
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=(config.device == "cuda"),
        )
        return train_loader, test_loader

    except Exception as exc:
        logger.warning(
            "Could not download/load full CIFAR-10 dataset (%s). Falling back to synthetic mock pipeline.",
            exc,
        )
        # Fallback to synthetic
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 3, 32, 32, generator=gen)
        test_samples = max(64, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 3, 32, 32, generator=gen)

        if config.distribution == "pathological_20":
            target_classes = list(config.target_classes) if (config.target_classes is not None and len(config.target_classes) > 0) else [0, 1]
            config.target_classes = target_classes
            logger.info("Applying 20% Pathological Label Skew with classes: %s", target_classes)
            target_tensor = torch.tensor(target_classes, dtype=torch.long)
            train_idx = torch.randint(0, len(target_classes), (config.synthetic_samples,), generator=gen)
            train_y = target_tensor[train_idx]
            test_idx = torch.randint(0, len(target_classes), (test_samples,), generator=gen)
            test_y = target_tensor[test_idx]
        else:
            train_y = torch.randint(0, 10, (config.synthetic_samples,), generator=gen)
            test_y = torch.randint(0, 10, (test_samples,), generator=gen)

        train_loader = DataLoader(TensorDataset(train_x, train_y), batch_size=config.batch_size, shuffle=True)
        test_loader = DataLoader(TensorDataset(test_x, test_y), batch_size=config.batch_size, shuffle=False)
        return train_loader, test_loader


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Tuple[float, float]:
    """Execute a single training epoch across all dataloader batches.

    Args:
        model: PyTorch model.
        dataloader: Training DataLoader.
        criterion: Loss function.
        optimizer: Optimizer.
        device: Execution device.

    Returns:
        Tuple of (average_loss, accuracy_percentage).
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, targets in dataloader:
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()

    avg_loss = running_loss / max(1, total)
    accuracy = 100.0 * correct / max(1, total)
    return avg_loss, accuracy


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    """Evaluate model loss and accuracy on a held-out test split.

    Args:
        model: PyTorch model.
        dataloader: Test/Validation DataLoader.
        criterion: Loss function.
        device: Execution device.

    Returns:
        Tuple of (average_test_loss, test_accuracy_percentage).
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, targets in dataloader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)

            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

    avg_loss = running_loss / max(1, total)
    accuracy = 100.0 * correct / max(1, total)
    return avg_loss, accuracy


def compute_and_save_importance_cache(
    rounds_dir: Path,
    beta: float = 0.9,
    top_k: int = 1000,
) -> Optional[Path]:
    """Compute and persist the multi-round importance score cache for beta=0.9."""
    import re
    round_files: List[Tuple[int, Path]] = []
    if rounds_dir.exists():
        for f in rounds_dir.iterdir():
            m = re.match(r"cifar10_flat_round_(\d+)\.pt$", f.name)
            if m:
                round_files.append((int(m.group(1)), f))
    round_files.sort(key=lambda x: x[0])
    if not round_files:
        return None

    round_tensors: List[torch.Tensor] = []
    all_layer_slices: Dict[str, Any] = {}
    for _, fpath in round_files:
        ft, meta = load_flat_parameters_artifact(fpath)
        round_tensors.append(ft.float())
        if not all_layer_slices:
            all_layer_slices = meta.get("layer_slices", {})

    total_params = int(round_tensors[0].numel())

    # Chain EMA scores: s^(1) = |w^(1)|, s^(t) = beta*s^(t-1) + (1-beta)*|w^(t)|
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

    # Rank each round with deterministic index tie-break (stable descending argsort)
    round_ranks: List[torch.Tensor] = []
    round_rank_of_index: List[torch.Tensor] = []
    for st in ema_scores:
        sorted_indices = torch.argsort(-st, stable=True)
        round_ranks.append(sorted_indices)
        # Vectorized inverse permutation: rank_tensor[global_index] = 1-based rank
        rank_tensor = torch.empty(total_params, dtype=torch.int64)
        rank_tensor[sorted_indices] = torch.arange(1, total_params + 1, dtype=torch.int64)
        round_rank_of_index.append(rank_tensor)

    rounds_data: List[Dict[str, Any]] = []
    effective_top_k = min(top_k, total_params)
    for t_idx, (round_num, _) in enumerate(round_files):
        sorted_indices = round_ranks[t_idx][:effective_top_k]
        st = ema_scores[t_idx]
        wt = round_tensors[t_idx]

        items: List[Dict[str, Any]] = []
        for rank_pos, g_idx_t in enumerate(sorted_indices):
            global_idx = int(g_idx_t.item())
            rank = rank_pos + 1
            if t_idx == 0:
                rank_delta = None
            else:
                prev_rank = int(round_rank_of_index[t_idx - 1][global_idx].item())
                rank_delta = prev_rank - rank

            raw_val = float(wt[global_idx].item())
            score_val = float(st[global_idx].item())
            layer_name = "unknown"
            for lname, linfo in all_layer_slices.items():
                if linfo["start_idx"] <= global_idx < linfo["end_idx"]:
                    layer_name = lname
                    break

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

    cache_payload = {
        "has_data": True,
        "total_rounds": len(round_files),
        "beta": beta,
        "offset": 0,
        "top_k": effective_top_k,
        "total_parameters": total_params,
        "cached_top_k": effective_top_k,
        "rounds": rounds_data,
        "rounds_data": rounds_data,
        "source": "cached_beta_0.9",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    cache_path = rounds_dir / "cifar10_importance_cache_beta09.pt"
    torch.save(cache_payload, cache_path)

    json_path = rounds_dir / "cifar10_importance_cache_beta09.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(cache_payload, f, indent=2)
    except Exception as e:
        logger.warning("Could not write json cache: %s", e)

    logger.info("Persisted importance score cache (beta=%.2f, top_%d) to %s", beta, effective_top_k, cache_path.name)
    return cache_path


def compute_and_save_energy_cache(
    rounds_dir: Path,
    beta: float = 0.9,
) -> Optional[Path]:
    """Compute and persist the cumulative energy distribution and prefix sums cache for beta=0.9."""
    import re
    import math

    round_files: List[Tuple[int, Path]] = []
    if rounds_dir.exists():
        for f in rounds_dir.iterdir():
            m = re.match(r"cifar10_flat_round_(\d+)\.pt$", f.name)
            if m:
                round_files.append((int(m.group(1)), f))
    round_files.sort(key=lambda x: x[0])
    if not round_files:
        return None

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
        raw_p = np.unique(np.geomspace(1, total_params, num=min(60, total_params)).astype(int))
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

    cache_payload = {
        "has_data": True,
        "total_rounds": len(round_files),
        "beta": beta,
        "total_parameters": total_params,
        "rounds": rounds_data,
        "source": "cached_beta_0.9",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    cache_path = rounds_dir / "cifar10_energy_cache_beta09.pt"
    torch.save(cache_payload, cache_path)

    json_path = rounds_dir / "cifar10_energy_cache_beta09.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(cache_payload, f, indent=2)
    except Exception as e:
        logger.warning("Could not write energy json cache: %s", e)

    logger.info("Persisted energy distribution cache (beta=%.2f) to %s", beta, cache_path.name)
    return cache_path


def train_cifar_model(config: Optional[TrainingConfig] = None) -> Tuple[CIFAR10CNN, TrainingResult]:
    """Train CIFAR-10 CNN and persist model weights + metadata artifact bundle.

    Args:
        config: TrainingConfig object (uses default parameters if omitted).

    Returns:
        Tuple of (trained_model, TrainingResult).
    """
    if config is None:
        config = TrainingConfig()

    set_seed(config.seed)
    device = torch.device(config.device)
    logger.info("Initializing CIFAR-10 CNN on device: %s", device)

    model = CIFAR10CNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        model.parameters(),
        lr=config.learning_rate,
        momentum=config.momentum,
        weight_decay=config.weight_decay,
    )

    train_loader, test_loader = get_dataloaders(config)

    out_dir = Path(config.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rounds_dir = Path(config.checkpoint_dir).resolve()
    rounds_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = out_dir / config.checkpoint_name

    epoch_history: List[Dict[str, Any]] = []
    round_history: List[Dict[str, Any]] = []
    start_time = datetime.now(timezone.utc)

    logger.info(
        "Starting training for %d rounds x %d epochs (batch_size=%d, lr=%.4f)...",
        config.rounds,
        config.epochs,
        config.batch_size,
        config.learning_rate,
    )

    for round_idx in range(1, config.rounds + 1):
        logger.info("=== Starting Round [%d/%d] ===", round_idx, config.rounds)
        for epoch in range(1, config.epochs + 1):
            global_epoch = (round_idx - 1) * config.epochs + epoch
            train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
            test_loss, test_acc = evaluate_model(model, test_loader, criterion, device)

            epoch_stats = {
                "round": round_idx,
                "epoch": epoch,
                "global_epoch": global_epoch,
                "train_loss": round(train_loss, 4),
                "train_accuracy": round(train_acc, 2),
                "test_loss": round(test_loss, 4),
                "test_accuracy": round(test_acc, 2),
            }
            epoch_history.append(epoch_stats)
            logger.info(
                "Round [%d/%d] Epoch [%d/%d] (Global %d) | Train Loss: %.4f, Train Acc: %.2f%% | Test Loss: %.4f, Test Acc: %.2f%%",
                round_idx,
                config.rounds,
                epoch,
                config.epochs,
                global_epoch,
                train_loss,
                train_acc,
                test_loss,
                test_acc,
            )

        # End of round: save round-specific checkpoint and flat parameter tensor
        round_train_loss = epoch_history[-1]["train_loss"] if epoch_history else 0.0
        round_train_acc = epoch_history[-1]["train_accuracy"] if epoch_history else 0.0
        round_test_loss = epoch_history[-1]["test_loss"] if epoch_history else 0.0
        round_test_acc = epoch_history[-1]["test_accuracy"] if epoch_history else 0.0

        round_ckpt_path = rounds_dir / f"cifar10_cnn_round_{round_idx}.pt"
        round_flat_path = rounds_dir / f"cifar10_flat_round_{round_idx}.pt"

        # Save round weights
        temp_round_ckpt = round_ckpt_path.with_name(f"{round_ckpt_path.stem}_tmp_{random.randint(10000, 99999)}{round_ckpt_path.suffix}")
        try:
            torch.save(model.state_dict(), temp_round_ckpt)
            if round_ckpt_path.exists():
                try:
                    round_ckpt_path.unlink()
                except Exception:
                    pass
            temp_round_ckpt.replace(round_ckpt_path)
        except Exception:
            if temp_round_ckpt.exists():
                try:
                    temp_round_ckpt.unlink()
                except Exception:
                    pass
            torch.save(model.state_dict(), round_ckpt_path)


        # Flatten and save round flat parameters
        flat_tensor, flat_meta = flatten_parameters(model)
        save_flat_parameters_artifact(
            flat_tensor=flat_tensor,
            metadata=flat_meta,
            output_path=round_flat_path,
            source_checkpoint=str(round_ckpt_path),
        )

        round_stats = {
            "round": round_idx,
            "train_loss": round_train_loss,
            "train_accuracy": round_train_acc,
            "test_loss": round_test_loss,
            "test_accuracy": round_test_acc,
            "checkpoint_path": str(round_ckpt_path),
            "flat_parameters_path": str(round_flat_path),
        }
        round_history.append(round_stats)
        logger.info(
            "Round [%d/%d] Complete | Saved Checkpoint: %s | Flat Parameters: %s",
            round_idx,
            config.rounds,
            round_ckpt_path.name,
            round_flat_path.name,
        )

        # Compute and persist EMA importance cache (beta=0.9, top 1000 coordinates)
        try:
            compute_and_save_importance_cache(rounds_dir=rounds_dir, beta=0.9, top_k=1000)
        except Exception as cache_err:
            logger.warning("Could not persist round importance cache: %s", cache_err)

        # Compute and persist energy distribution cache (beta=0.9)
        try:
            compute_and_save_energy_cache(rounds_dir=rounds_dir, beta=0.9)
        except Exception as cache_err:
            logger.warning("Could not persist round energy cache: %s", cache_err)

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    final_train_loss = epoch_history[-1]["train_loss"] if epoch_history else 0.0
    final_train_acc = epoch_history[-1]["train_accuracy"] if epoch_history else 0.0
    final_test_loss = epoch_history[-1]["test_loss"] if epoch_history else 0.0
    final_test_acc = epoch_history[-1]["test_accuracy"] if epoch_history else 0.0

    # Build comprehensive metadata package
    metadata_payload: Dict[str, Any] = {
        "dataset": "CIFAR-10",
        "num_classes": 10,
        "class_mapping": CIFAR10_CLASSES,
        "hyperparameters": {
            "rounds": config.rounds,
            "epochs": config.epochs,
            "epochs_per_round": config.epochs,
            "total_epochs": config.rounds * config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "momentum": config.momentum,
            "weight_decay": config.weight_decay,
            "optimizer": "SGD",
            "seed": config.seed,
            "is_synthetic": config.synthetic,
            "distribution": config.distribution,
            "target_classes": config.target_classes,
        },
        "metrics": {
            "final_train_loss": final_train_loss,
            "final_train_accuracy": final_train_acc,
            "final_test_loss": final_test_loss,
            "final_test_accuracy": final_test_acc,
            "training_duration_seconds": round(duration, 2),
        },
        "round_history": round_history,
        "epoch_history": epoch_history,
        "execution": {
            "device": str(device),
            "torch_version": torch.__version__,
            "timestamp_utc": end_time.isoformat(),
        },
    }

    # Save canonical final artifacts
    saved_ckpt, saved_meta = model.save_checkpoint(checkpoint_file, metadata=metadata_payload)
    logger.info("Saved canonical model checkpoint: %s", saved_ckpt)
    logger.info("Saved canonical metadata bundle: %s", saved_meta)

    result = TrainingResult(
        final_train_loss=final_train_loss,
        final_train_accuracy=final_train_acc,
        final_test_loss=final_test_loss,
        final_test_accuracy=final_test_acc,
        epoch_history=epoch_history,
        round_history=round_history,
        checkpoint_path=str(saved_ckpt),
        metadata_path=str(saved_meta),
        duration_seconds=duration,
    )

    return model, result


def parse_args() -> TrainingConfig:
    """Parse command-line arguments into a TrainingConfig instance."""
    parser = argparse.ArgumentParser(description="Train CIFAR-10 CNN for SemanticDFL")
    parser.add_argument("--rounds", type=int, default=1, help="Number of sequential training rounds")
    parser.add_argument("--epochs", type=int, default=5, help="Number of local training epochs per round")
    parser.add_argument("--batch-size", type=int, default=64, help="Mini-batch size (paper default: 64)")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate (paper default: 0.01)")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="output/models", help="Output artifact directory")
    parser.add_argument("--checkpoint-dir", type=str, default="output/models/rounds", help="Per-round checkpoint directory")
    parser.add_argument("--data-dir", type=str, default="data", help="CIFAR-10 raw dataset directory")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for fast verification")
    parser.add_argument("--synthetic-samples", type=int, default=512, help="Number of synthetic samples if --synthetic")
    parser.add_argument("--distribution", type=str, default="full", choices=["full", "pathological_20"], help="Data distribution: 'full' or 'pathological_20'")

    args = parser.parse_args()
    return TrainingConfig(
        rounds=args.rounds,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        seed=args.seed,
        output_dir=args.output_dir,
        checkpoint_dir=args.checkpoint_dir,
        data_dir=args.data_dir,
        synthetic=args.synthetic,
        synthetic_samples=args.synthetic_samples,
        distribution=args.distribution,
    )


if __name__ == "__main__":
    cfg = parse_args()
    train_cifar_model(cfg)

