"""Fashion-MNIST (FMNIST) Model Training and Evaluation Pipeline.

Implements isolated, modular dataset ingestion, preprocessing, training, evaluation,
and deterministic artifact serialization for the SemanticDFL Fashion-MNIST CNN.

Section 5.1 ('Datasets and Models') specifications:
- Two 5x5 Conv layers (Conv1: 1->32, Conv2: 32->64), MaxPool (2x2, stride=2),
  ReLU activations, Fully Connected hidden layer (512 units), Output Linear layer (10 classes).
- Single-client local training with paper hyperparameters:
  learning_rate = 0.01, batch_size = 64, local_epochs = 1.
- Integration with parameter flattening and Top-P signature extraction (Algorithm 1 / Appendix B.1).
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

from backend.models.fmnist_cnn import (
    FMNISTCNN,
    FMNIST_CLASSES,
    EXPECTED_FMNIST_PARAMETER_COUNT,
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
logger = logging.getLogger("FMNISTTrainer")


@dataclass
class TrainingConfig:
    """Configuration hyperparameter dataclass for Fashion-MNIST training."""

    rounds: int = 1
    epochs: int = 1  # Paper default: 1 local epoch per round
    batch_size: int = 64  # Paper default: 64
    learning_rate: float = 0.01  # Paper default: 0.01
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
    checkpoint_name: str = "fmnist_cnn_checkpoint.pt"
    theta: float = 0.70  # Paper cosine threshold
    beta: float = 0.9  # EMA importance beta


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
    flat_parameters_path: str = ""
    duration_seconds: float = 0.0
    top_p_summary: Optional[Dict[str, Any]] = None


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
    """Acquire and prepare training and evaluation DataLoaders for Fashion-MNIST.

    If config.synthetic is True or if torchvision download is unavailable/fails,
    generates deterministic synthetic (B, 1, 28, 28) image batches for robust isolated testing.

    Args:
        config: TrainingConfig parameters.

    Returns:
        Tuple of (train_loader, test_loader).
    """
    if config.synthetic:
        logger.info(
            "Using synthetic deterministic FMNIST dataset of %d samples.",
            config.synthetic_samples,
        )
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 1, 28, 28, generator=gen)
        test_samples = max(64, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 1, 28, 28, generator=gen)

        if config.distribution == "pathological_20":
            target_classes = (
                list(config.target_classes)
                if (config.target_classes is not None and len(config.target_classes) > 0)
                else [0, 1]
            )
            config.target_classes = target_classes
            logger.info("Applying 20%% Pathological Label Skew with classes: %s", target_classes)
            target_tensor = torch.tensor(target_classes, dtype=torch.long)
            train_idx = torch.randint(
                0, len(target_classes), (config.synthetic_samples,), generator=gen
            )
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

        # Standard Fashion-MNIST normalization: mean=0.2860, std=0.3530
        fmnist_mean = (0.2860,)
        fmnist_std = (0.3530,)

        train_transform = transforms.Compose([
            transforms.RandomCrop(28, padding=2),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(fmnist_mean, fmnist_std),
        ])

        test_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(fmnist_mean, fmnist_std),
        ])

        data_path = Path(config.data_dir).resolve()
        data_path.mkdir(parents=True, exist_ok=True)

        logger.info("Loading Fashion-MNIST from %s (download=True)...", data_path)
        train_dataset = torchvision.datasets.FashionMNIST(
            root=str(data_path),
            train=True,
            download=True,
            transform=train_transform,
        )
        test_dataset = torchvision.datasets.FashionMNIST(
            root=str(data_path),
            train=False,
            download=True,
            transform=test_transform,
        )

        if config.distribution == "pathological_20":
            target_classes = (
                list(config.target_classes)
                if (config.target_classes is not None and len(config.target_classes) > 0)
                else [0, 1]
            )
            config.target_classes = target_classes
            logger.info("Applying 20%% Pathological Label Skew with classes: %s", target_classes)
            train_targets = (
                train_dataset.targets
                if hasattr(train_dataset, "targets")
                else [y for _, y in train_dataset]
            )
            train_indices = [
                i for i, label in enumerate(train_targets) if int(label) in target_classes
            ]
            train_dataset = torch.utils.data.Subset(train_dataset, train_indices)

            test_targets = (
                test_dataset.targets
                if hasattr(test_dataset, "targets")
                else [y for _, y in test_dataset]
            )
            test_indices = [
                i for i, label in enumerate(test_targets) if int(label) in target_classes
            ]
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
            "Could not download/load full Fashion-MNIST dataset (%s). Falling back to synthetic mock pipeline.",
            exc,
        )
        gen = torch.Generator().manual_seed(config.seed)
        train_x = torch.randn(config.synthetic_samples, 1, 28, 28, generator=gen)
        test_samples = max(64, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 1, 28, 28, generator=gen)

        if config.distribution == "pathological_20":
            target_classes = (
                list(config.target_classes)
                if (config.target_classes is not None and len(config.target_classes) > 0)
                else [0, 1]
            )
            config.target_classes = target_classes
            logger.info("Applying 20%% Pathological Label Skew with classes: %s", target_classes)
            target_tensor = torch.tensor(target_classes, dtype=torch.long)
            train_idx = torch.randint(
                0, len(target_classes), (config.synthetic_samples,), generator=gen
            )
            train_y = target_tensor[train_idx]
            test_idx = torch.randint(0, len(target_classes), (test_samples,), generator=gen)
            test_y = target_tensor[test_idx]
        else:
            train_y = torch.randint(0, 10, (config.synthetic_samples,), generator=gen)
            test_y = torch.randint(0, 10, (test_samples,), generator=gen)

        train_loader = DataLoader(
            TensorDataset(train_x, train_y), batch_size=config.batch_size, shuffle=True
        )
        test_loader = DataLoader(
            TensorDataset(test_x, test_y), batch_size=config.batch_size, shuffle=False
        )
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


def extract_top_p_signature(
    weights_or_model: Union[torch.Tensor, np.ndarray, nn.Module],
    theta: float = 0.70,
    beta: float = 0.0,
    s_prev: Optional[np.ndarray] = None,
    p_fixed: Optional[int] = None,
) -> Dict[str, Any]:
    """Extract Top-P signature adhering to Algorithm 1 and Appendix B.1 of SemanticDFL.

    Algorithm:
    1. Flat parameter vector w in R^M.
    2. EMA importance score s = beta * s_prev + (1 - beta) * |w|.
    3. Sort parameters descending by score with deterministic ascending index tie-break.
    4. Compute cumulative energy prefix sums c_P = sum_{j=1}^P w_pi(j)^2.
    5. If p_fixed is None, find minimal P_min via binary search such that
       cos(w, w^[P]) = sqrt(c_P) / ||w|| >= theta.
    6. Return sparse representation (indices, values) and compression metrics.

    Args:
        weights_or_model: 1D parameter tensor/array or PyTorch nn.Module.
        theta: Directional cosine similarity threshold (default: 0.70 from paper).
        beta: EMA importance weight factor (default: 0.0 for raw magnitude).
        s_prev: Optional previous round importance score vector.
        p_fixed: Optional predetermined signature dimension P.

    Returns:
        Dictionary with p_min, cosine_similarity, indices, values, payload_bytes, etc.
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

    # Deterministic argsort: descending by score s, tie-break ascending by index
    sorted_order = np.lexsort((np.arange(M), -s))
    sorted_sq = (w[sorted_order]) ** 2
    prefix_c = np.cumsum(sorted_sq)

    if p_fixed is not None:
        p_chosen = max(1, min(int(p_fixed), M))
    else:
        # Binary search for minimal P such that c_P >= theta^2 * nu^2
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

    # Payload: 4-byte index + 2-byte half-precision float (FP16) per paper
    payload_bytes = p_chosen * (4 + 2)
    dense_bytes = M * 4

    return {
        "p_min": p_chosen,
        "cosine_similarity": round(cosine_retention, 6),
        "target_theta": theta,
        "indices": chosen_indices.tolist(),
        "values": chosen_values.tolist(),
        "payload_bytes": payload_bytes,
        "dense_bytes": dense_bytes,
        "compression_factor": round(dense_bytes / max(1, payload_bytes), 2),
        "sparsity_ratio": round(p_chosen / max(1, M), 6),
        "total_parameters": M,
        "l2_norm": round(nu, 6),
    }


def train_fmnist_model(
    config: Optional[TrainingConfig] = None,
) -> Tuple[FMNISTCNN, TrainingResult]:
    """Train single-client Fashion-MNIST CNN and persist model weights + metadata.

    Args:
        config: TrainingConfig object (uses paper default parameters if omitted).

    Returns:
        Tuple of (trained_model, TrainingResult).
    """
    if config is None:
        config = TrainingConfig()

    set_seed(config.seed)
    device = torch.device(config.device)
    logger.info("Initializing Fashion-MNIST CNN on device: %s", device)

    model = FMNISTCNN().to(device)
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
        "Starting FMNIST training for %d rounds x %d epochs (batch_size=%d, lr=%.4f)...",
        config.rounds,
        config.epochs,
        config.batch_size,
        config.learning_rate,
    )

    for round_idx in range(1, config.rounds + 1):
        for epoch in range(1, config.epochs + 1):
            global_epoch = (round_idx - 1) * config.epochs + epoch
            train_loss, train_acc = train_one_epoch(
                model, train_loader, criterion, optimizer, device
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
            }
            epoch_history.append(epoch_stats)
            logger.info(
                "FMNIST Round [%d/%d] Epoch [%d/%d] | Train Loss: %.4f, Train Acc: %.2f%% | Test Loss: %.4f, Test Acc: %.2f%%",
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

        round_ckpt_path = rounds_dir / f"fmnist_cnn_round_{round_idx}.pt"
        round_flat_path = rounds_dir / f"fmnist_flat_round_{round_idx}.pt"

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
            model_name="FMNISTCNN",
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

    # Extract Top-P signature for final trained model
    flat_w, _ = flatten_parameters(model)
    top_p_summary = extract_top_p_signature(flat_w, theta=config.theta, beta=0.0)

    # Build comprehensive metadata package
    metadata_payload: Dict[str, Any] = {
        "dataset": "Fashion-MNIST",
        "num_classes": 10,
        "class_mapping": FMNIST_CLASSES,
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

    # Save final artifacts
    saved_ckpt, saved_meta = model.save_checkpoint(checkpoint_file, metadata=metadata_payload)
    canonical_flat_path = out_dir / "fmnist_flat_parameters.pt"
    flat_tensor, flat_meta = flatten_parameters(model)
    saved_flat = save_flat_parameters_artifact(
        flat_tensor=flat_tensor,
        metadata=flat_meta,
        output_path=canonical_flat_path,
        source_checkpoint=str(saved_ckpt),
        model_name="FMNISTCNN",
    )

    logger.info("Saved canonical FMNIST checkpoint: %s", saved_ckpt)
    logger.info("Saved canonical FMNIST metadata: %s", saved_meta)
    logger.info("Saved canonical FMNIST flat parameters: %s", saved_flat)

    result = TrainingResult(
        final_train_loss=final_train_loss,
        final_train_accuracy=final_train_acc,
        final_test_loss=final_test_loss,
        final_test_accuracy=final_test_acc,
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
    parser = argparse.ArgumentParser(description="Train Fashion-MNIST CNN for SemanticDFL")
    parser.add_argument(
        "--rounds", type=int, default=1, help="Number of sequential training rounds"
    )
    parser.add_argument(
        "--epochs", type=int, default=1, help="Number of local training epochs per round (paper: 1)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=64, help="Mini-batch size (paper default: 64)"
    )
    parser.add_argument(
        "--lr", type=float, default=0.01, help="Learning rate (paper default: 0.01)"
    )
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--output-dir", type=str, default="output/models", help="Output artifact directory"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="output/models/rounds",
        help="Per-round checkpoint directory",
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Fashion-MNIST raw dataset directory"
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use synthetic dataset for fast verification",
    )
    parser.add_argument(
        "--synthetic-samples",
        type=int,
        default=512,
        help="Number of synthetic samples if --synthetic",
    )
    parser.add_argument(
        "--distribution",
        type=str,
        default="full",
        choices=["full", "pathological_20"],
        help="Data distribution",
    )
    parser.add_argument(
        "--theta",
        type=float,
        default=0.70,
        help="Directional cosine similarity threshold (paper default: 0.70)",
    )

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
        theta=args.theta,
    )


if __name__ == "__main__":
    config = parse_args()
    train_fmnist_model(config)
