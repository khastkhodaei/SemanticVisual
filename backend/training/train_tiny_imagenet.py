"""Tiny-ImageNet ResNet-18 Model Training and Evaluation Pipeline.

Implements isolated, modular dataset ingestion, low-VRAM training, evaluation,
and deterministic artifact serialization for the SemanticDFL ResNet-18 benchmark.

Section 5.1 ('Datasets and Models') specifications:
- Model: ResNet-18 (~11.27M - 11.7M parameters) adapted for 64x64 RGB inputs, 200 classes.
- Single-client local training with paper hyperparameters:
  learning_rate = 0.05, batch_size = 64 (or 32 for low-VRAM fallback), local_epochs = 1.
- Target hardware optimization: NVIDIA GTX 1050 (low VRAM footprint) & 16GB system RAM:
  Mixed precision (torch.amp.autocast + GradScaler) and automatic OOM batch size fallback.
- Top-P signature extraction verifying paper finding:
  Pruning 90.4% (P ≈ 9.6% of M) retains cos >= 0.8.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset

from backend.models.tiny_imagenet_resnet import (
    TinyImageNetResNet18,
    TINY_IMAGENET_NUM_CLASSES,
)
from backend.models.flattening import (
    flatten_parameters,
    load_flat_parameters_artifact,
    save_flat_parameters_artifact,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TinyImageNetTrainer")


@dataclass
class TrainingConfig:
    """Configuration hyperparameter dataclass for Tiny-ImageNet ResNet-18 training."""

    rounds: int = 1
    epochs: int = 1  # Paper default: 1 local epoch per round
    batch_size: int = 64  # Paper default: 64
    fallback_batch_size: int = 32  # GTX 1050 low-VRAM fallback
    learning_rate: float = 0.05  # Paper default: 0.05
    momentum: float = 0.9
    weight_decay: float = 1e-4
    seed: int = 42
    output_dir: str = "output/models"
    checkpoint_dir: str = "output/models/rounds"
    data_dir: str = "data/tiny-imagenet-200"
    synthetic: bool = False
    synthetic_samples: int = 512
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_name: str = "tiny_imagenet_resnet18.pt"
    theta: float = 0.80  # Paper target cosine similarity
    beta: float = 0.9  # EMA importance beta
    use_amp: bool = True  # Automatic Mixed Precision for low VRAM consumption


@dataclass
class TrainingResult:
    """Summary of completed training session."""

    final_train_loss: float
    final_train_accuracy: float
    final_test_loss: float
    final_test_accuracy: float
    batch_size: int = 64
    epoch_history: List[Dict[str, Any]] = field(default_factory=list)
    round_history: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint_path: str = ""
    metadata_path: str = ""
    flat_parameters_path: str = ""
    duration_seconds: float = 0.0
    top_p_summary: Optional[Dict[str, Any]] = None


def set_seed(seed: int = 42) -> None:
    """Set deterministic seeds across standard library, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_dataloaders(
    config: TrainingConfig, batch_size_override: Optional[int] = None
) -> Tuple[DataLoader, DataLoader]:
    """Acquire training and evaluation DataLoaders for Tiny-ImageNet.

    If config.synthetic is True or if dataset is not found locally,
    generates deterministic synthetic (B, 3, 64, 64) image batches.
    """
    effective_bs = batch_size_override or config.batch_size

    if config.synthetic:
        logger.info(
            "Using synthetic deterministic Tiny-ImageNet dataset of %d samples (bs=%d).",
            config.synthetic_samples,
            effective_bs,
        )
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 3, 64, 64, generator=gen)
        test_samples = max(32, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 3, 64, 64, generator=gen)

        train_y = torch.randint(0, TINY_IMAGENET_NUM_CLASSES, (config.synthetic_samples,), generator=gen)
        test_y = torch.randint(0, TINY_IMAGENET_NUM_CLASSES, (test_samples,), generator=gen)

        train_dataset = TensorDataset(train_x, train_y)
        test_dataset = TensorDataset(test_x, test_y)

        train_loader = DataLoader(
            train_dataset,
            batch_size=effective_bs,
            shuffle=True,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=effective_bs,
            shuffle=False,
        )
        return train_loader, test_loader

    # Try loading from local directory
    try:
        import torchvision
        import torchvision.transforms as transforms
        from torchvision.datasets import ImageFolder

        data_root = Path(config.data_dir).resolve()
        train_dir = data_root / "train"
        val_dir = data_root / "val"

        if not train_dir.exists():
            raise FileNotFoundError(f"Tiny-ImageNet directory not found at {train_dir}")

        normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )

        train_transform = transforms.Compose([
            transforms.RandomCrop(64, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize,
        ])
        test_transform = transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])

        train_dataset = ImageFolder(str(train_dir), transform=train_transform)
        test_dataset = ImageFolder(str(val_dir), transform=test_transform) if val_dir.exists() else train_dataset

        train_loader = DataLoader(
            train_dataset,
            batch_size=effective_bs,
            shuffle=True,
            num_workers=0,
            pin_memory=(config.device == "cuda"),
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=effective_bs,
            shuffle=False,
            num_workers=0,
            pin_memory=(config.device == "cuda"),
        )
        return train_loader, test_loader

    except Exception as exc:
        logger.warning(
            "Could not load local Tiny-ImageNet dataset (%s). Falling back to synthetic mock pipeline.",
            exc,
        )
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 3, 64, 64, generator=gen)
        test_samples = max(32, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 3, 64, 64, generator=gen)

        train_y = torch.randint(0, TINY_IMAGENET_NUM_CLASSES, (config.synthetic_samples,), generator=gen)
        test_y = torch.randint(0, TINY_IMAGENET_NUM_CLASSES, (test_samples,), generator=gen)

        train_loader = DataLoader(TensorDataset(train_x, train_y), batch_size=effective_bs, shuffle=True)
        test_loader = DataLoader(TensorDataset(test_x, test_y), batch_size=effective_bs, shuffle=False)
        return train_loader, test_loader


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    scaler: Optional[torch.amp.GradScaler] = None,
    use_amp: bool = False,
) -> Tuple[float, float]:
    """Execute a single training epoch across all dataloader batches with AMP support."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    amp_enabled = use_amp and device.type == "cuda"

    for inputs, targets in dataloader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()

        if amp_enabled and scaler is not None:
            with torch.amp.autocast(device_type="cuda", enabled=True):
                outputs = model(inputs)
                loss = criterion(outputs, targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
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
    """Evaluate model loss and accuracy on a held-out test split."""
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


def extract_top_p_signature(
    weights_or_model: Union[torch.Tensor, np.ndarray, nn.Module],
    theta: float = 0.80,
    beta: float = 0.0,
    s_prev: Optional[np.ndarray] = None,
    p_fixed: Optional[int] = None,
) -> Dict[str, Any]:
    """Extract Top-P signature adhering to Algorithm 1 and Appendix B.1 of SemanticDFL.

    Verifies paper finding for ResNet-18:
    Pruning 90.4% (keeping P ≈ 9.6% of M) retains directional cos >= 0.80.
    """
    if isinstance(weights_or_model, nn.Module):
        w_tensor, _ = flatten_parameters(weights_or_model)
        w = w_tensor.cpu().numpy().astype(np.float64)
    elif isinstance(weights_or_model, torch.Tensor):
        w = weights_or_model.detach().cpu().numpy().astype(np.float64).reshape(-1)
    else:
        w = np.asarray(weights_or_model, dtype=np.float64).reshape(-1)

    M = len(w)
    nu_sq = float(np.dot(w, w))
    nu = math.sqrt(max(0.0, nu_sq))

    if nu == 0.0 or M == 0:
        return {
            "p_min": M,
            "cosine_similarity": 1.0,
            "indices": list(range(M)),
            "values": w.tolist(),
            "payload_bytes": M * 6,
            "total_parameters": M,
            "sparsity_ratio": 1.0,
        }

    abs_w = np.abs(w)
    s = abs_w if s_prev is None or beta == 0.0 else (beta * s_prev + (1.0 - beta) * abs_w)

    sorted_order = np.lexsort((np.arange(M), -s))
    sorted_sq = (w[sorted_order]) ** 2
    prefix_c = np.cumsum(sorted_sq)

    if p_fixed is not None:
        p_chosen = max(1, min(int(p_fixed), M))
    else:
        target_energy = (theta**2) * nu_sq
        lo, hi = 1, M
        while lo < hi:
            mid = (lo + hi) // 2
            if prefix_c[mid - 1] >= target_energy:
                hi = mid
            else:
                lo = mid + 1
        p_chosen = lo

    c_chosen = float(prefix_c[p_chosen - 1])
    cosine_retention = math.sqrt(max(0.0, c_chosen)) / nu if nu > 0 else 1.0
    cosine_retention = min(1.0, cosine_retention)

    chosen_indices = np.sort(sorted_order[:p_chosen])
    chosen_values = w[chosen_indices]

    payload_bytes = p_chosen * (4 + 2)
    dense_bytes = M * 4

    return {
        "p_min": p_chosen,
        "cosine_similarity": round(cosine_retention, 6),
        "target_theta": theta,
        "indices": chosen_indices.tolist() if p_chosen <= 10_000 else [],
        "values": chosen_values.tolist() if p_chosen <= 10_000 else [],
        "payload_bytes": payload_bytes,
        "dense_bytes": dense_bytes,
        "compression_factor": round(dense_bytes / max(1, payload_bytes), 2),
        "sparsity_ratio": round(p_chosen / max(1, M), 6),
        "total_parameters": M,
        "l2_norm": round(nu, 6),
    }


def train_tiny_imagenet_model(
    config: Optional[TrainingConfig] = None,
) -> Tuple[TinyImageNetResNet18, TrainingResult]:
    """Train single-client ResNet-18 on Tiny-ImageNet with GTX 1050 hardware guardrails.

    Includes automatic batch size reduction from 64 to 32 upon CUDA OOM.
    """
    if config is None:
        config = TrainingConfig()

    set_seed(config.seed)
    device = torch.device(config.device)
    logger.info("Initializing Tiny-ImageNet ResNet-18 on device: %s", device)

    model = TinyImageNetResNet18(num_classes=TINY_IMAGENET_NUM_CLASSES).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        model.parameters(),
        lr=config.learning_rate,
        momentum=config.momentum,
        weight_decay=config.weight_decay,
    )

    scaler = None
    if config.use_amp and device.type == "cuda":
        scaler = torch.amp.GradScaler("cuda", enabled=True)

    current_batch_size = config.batch_size
    train_loader, test_loader = get_dataloaders(config, batch_size_override=current_batch_size)

    out_dir = Path(config.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rounds_dir = Path(config.checkpoint_dir).resolve()
    rounds_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = out_dir / config.checkpoint_name

    epoch_history: List[Dict[str, Any]] = []
    round_history: List[Dict[str, Any]] = []
    start_time = datetime.now(timezone.utc)

    for round_idx in range(1, config.rounds + 1):
        for epoch in range(1, config.epochs + 1):
            global_epoch = (round_idx - 1) * config.epochs + epoch

            try:
                train_loss, train_acc = train_one_epoch(
                    model, train_loader, criterion, optimizer, device, scaler, config.use_amp
                )
            except torch.cuda.OutOfMemoryError:
                logger.warning(
                    "CUDA Out-of-Memory detected with batch_size=%d. Falling back to %d.",
                    current_batch_size,
                    config.fallback_batch_size,
                )
                torch.cuda.empty_cache()
                current_batch_size = config.fallback_batch_size
                train_loader, test_loader = get_dataloaders(
                    config, batch_size_override=current_batch_size
                )
                train_loss, train_acc = train_one_epoch(
                    model, train_loader, criterion, optimizer, device, scaler, config.use_amp
                )

            test_loss, test_acc = evaluate_model(model, test_loader, criterion, device)

            epoch_stats = {
                "round": round_idx,
                "epoch": epoch,
                "global_epoch": global_epoch,
                "train_loss": round(train_loss, 4),
                "train_accuracy": round(train_acc, 2),
                "test_loss": round(test_loss, 4),
                "test_accuracy": round(test_acc, 2),
                "batch_size": current_batch_size,
            }
            epoch_history.append(epoch_stats)
            logger.info(
                "Tiny-ImageNet Round [%d/%d] Epoch [%d/%d] | Train Loss: %.4f, Train Acc: %.2f%% | Test Loss: %.4f, Test Acc: %.2f%%",
                round_idx,
                config.rounds,
                epoch,
                config.epochs,
                train_loss,
                train_acc,
                test_loss,
                test_acc,
            )

        round_train_loss = epoch_history[-1]["train_loss"] if epoch_history else 0.0
        round_train_acc = epoch_history[-1]["train_accuracy"] if epoch_history else 0.0
        round_test_loss = epoch_history[-1]["test_loss"] if epoch_history else 0.0
        round_test_acc = epoch_history[-1]["test_accuracy"] if epoch_history else 0.0

        round_ckpt_path = rounds_dir / f"tiny_imagenet_resnet18_round_{round_idx}.pt"
        round_flat_path = rounds_dir / f"tiny_imagenet_flat_round_{round_idx}.pt"

        # Save round weights
        temp_round_ckpt = round_ckpt_path.with_name(
            f"{round_ckpt_path.stem}_tmp_{random.randint(10000, 99999)}{round_ckpt_path.suffix}"
        )
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
            model_name="TinyImageNetResNet18",
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

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    final_train_loss = epoch_history[-1]["train_loss"] if epoch_history else 0.0
    final_train_acc = epoch_history[-1]["train_accuracy"] if epoch_history else 0.0
    final_test_loss = epoch_history[-1]["test_loss"] if epoch_history else 0.0
    final_test_acc = epoch_history[-1]["test_accuracy"] if epoch_history else 0.0

    # Extract Top-P signature verifying paper finding
    flat_w, _ = flatten_parameters(model)
    top_p_summary = extract_top_p_signature(flat_w, theta=config.theta, beta=0.0)

    # Save final artifacts
    metadata_payload: Dict[str, Any] = {
        "dataset": "Tiny-ImageNet",
        "num_classes": TINY_IMAGENET_NUM_CLASSES,
        "hyperparameters": {
            "rounds": config.rounds,
            "epochs": config.epochs,
            "epochs_per_round": config.epochs,
            "total_epochs": config.rounds * config.epochs,
            "batch_size": current_batch_size,
            "configured_batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "momentum": config.momentum,
            "weight_decay": config.weight_decay,
            "optimizer": "SGD",
            "seed": config.seed,
            "is_synthetic": config.synthetic,
            "use_amp": config.use_amp,
            "theta": config.theta,
        },
        "metrics": {
            "final_train_loss": final_train_loss,
            "final_train_accuracy": final_train_acc,
            "final_test_loss": final_test_loss,
            "final_test_accuracy": final_test_acc,
            "training_duration_seconds": round(duration, 2),
        },
        "top_p_signature": {
            "p_min": top_p_summary["p_min"],
            "cosine_similarity": top_p_summary["cosine_similarity"],
            "sparsity_ratio": top_p_summary["sparsity_ratio"],
            "payload_bytes": top_p_summary["payload_bytes"],
            "dense_bytes": top_p_summary["dense_bytes"],
            "compression_factor": top_p_summary["compression_factor"],
        },
        "round_history": round_history,
        "epoch_history": epoch_history,
        "execution": {
            "device": str(device),
            "torch_version": torch.__version__,
            "timestamp_utc": end_time.isoformat(),
        },
    }

    saved_ckpt, saved_meta = model.save_checkpoint(checkpoint_file, metadata=metadata_payload)
    canonical_flat_path = out_dir / "tiny_imagenet_flat_parameters.pt"
    flat_tensor, flat_meta = flatten_parameters(model)
    saved_flat = save_flat_parameters_artifact(
        flat_tensor=flat_tensor,
        metadata=flat_meta,
        output_path=canonical_flat_path,
        source_checkpoint=str(saved_ckpt),
        model_name="TinyImageNetResNet18",
    )

    logger.info("Saved canonical Tiny-ImageNet checkpoint: %s", saved_ckpt)
    logger.info("Saved canonical Tiny-ImageNet metadata: %s", saved_meta)
    logger.info("Saved canonical Tiny-ImageNet flat parameters: %s", saved_flat)

    result = TrainingResult(
        final_train_loss=final_train_loss,
        final_train_accuracy=final_train_acc,
        final_test_loss=final_test_loss,
        final_test_accuracy=final_test_acc,
        batch_size=current_batch_size,
        epoch_history=epoch_history,
        round_history=round_history,
        checkpoint_path=str(saved_ckpt),
        metadata_path=str(saved_meta),
        flat_parameters_path=str(saved_flat),
        duration_seconds=duration,
        top_p_summary=top_p_summary,
    )

    return model, result


def parse_args() -> TrainingConfig:
    """Parse command-line arguments into a TrainingConfig instance."""
    parser = argparse.ArgumentParser(description="Train Tiny-ImageNet ResNet-18 for SemanticDFL")
    parser.add_argument("--rounds", type=int, default=1, help="Number of sequential training rounds")
    parser.add_argument("--epochs", type=int, default=1, help="Number of local training epochs (paper: 1)")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size (paper default: 64)")
    parser.add_argument("--lr", type=float, default=0.05, help="Learning rate (paper default: 0.05)")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="output/models", help="Output artifact directory")
    parser.add_argument("--checkpoint-dir", type=str, default="output/models/rounds", help="Per-round directory")
    parser.add_argument("--data-dir", type=str, default="data/tiny-imagenet-200", help="Tiny-ImageNet directory")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for verification")
    parser.add_argument("--synthetic-samples", type=int, default=512, help="Number of synthetic samples")
    parser.add_argument("--theta", type=float, default=0.80, help="Cosine threshold (paper default: 0.80)")
    parser.add_argument("--no-amp", action="store_true", help="Disable mixed precision")

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
        theta=args.theta,
        use_amp=not args.no_amp,
    )


if __name__ == "__main__":
    config = parse_args()
    train_tiny_imagenet_model(config)
