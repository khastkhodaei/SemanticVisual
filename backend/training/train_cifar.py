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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CIFAR10Trainer")


@dataclass
class TrainingConfig:
    """Configuration hyperparameter dataclass for CIFAR-10 training."""

    epochs: int = 5
    batch_size: int = 64
    learning_rate: float = 0.01
    momentum: float = 0.9
    weight_decay: float = 1e-4
    seed: int = 42
    output_dir: str = "output/models"
    data_dir: str = "data"
    synthetic: bool = False
    synthetic_samples: int = 512
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_name: str = "cifar10_cnn_checkpoint.pt"


@dataclass
class TrainingResult:
    """Summary of completed training session."""

    final_train_loss: float
    final_train_accuracy: float
    final_test_loss: float
    final_test_accuracy: float
    epoch_history: List[Dict[str, float]] = field(default_factory=list)
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
        train_y = torch.randint(0, 10, (config.synthetic_samples,), generator=gen)
        
        test_samples = max(64, config.synthetic_samples // 4)
        test_x = torch.randn(test_samples, 3, 32, 32, generator=gen)
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
        train_y = torch.randint(0, 10, (config.synthetic_samples,), generator=gen)
        test_x = torch.randn(max(64, config.synthetic_samples // 4), 3, 32, 32, generator=gen)
        test_y = torch.randint(0, 10, (max(64, config.synthetic_samples // 4),), generator=gen)

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
    checkpoint_file = out_dir / config.checkpoint_name

    epoch_history: List[Dict[str, float]] = []
    start_time = datetime.now(timezone.utc)

    logger.info(
        "Starting training for %d epochs (batch_size=%d, lr=%.4f)...",
        config.epochs,
        config.batch_size,
        config.learning_rate,
    )

    for epoch in range(1, config.epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        test_loss, test_acc = evaluate_model(model, test_loader, criterion, device)

        epoch_stats = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_accuracy": round(train_acc, 2),
            "test_loss": round(test_loss, 4),
            "test_accuracy": round(test_acc, 2),
        }
        epoch_history.append(epoch_stats)
        logger.info(
            "Epoch [%d/%d] | Train Loss: %.4f, Train Acc: %.2f%% | Test Loss: %.4f, Test Acc: %.2f%%",
            epoch,
            config.epochs,
            train_loss,
            train_acc,
            test_loss,
            test_acc,
        )

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
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "momentum": config.momentum,
            "weight_decay": config.weight_decay,
            "optimizer": "SGD",
            "seed": config.seed,
            "is_synthetic": config.synthetic,
        },
        "metrics": {
            "final_train_loss": final_train_loss,
            "final_train_accuracy": final_train_acc,
            "final_test_loss": final_test_loss,
            "final_test_accuracy": final_test_acc,
            "training_duration_seconds": round(duration, 2),
        },
        "epoch_history": epoch_history,
        "execution": {
            "device": str(device),
            "torch_version": torch.__version__,
            "timestamp_utc": end_time.isoformat(),
        },
    }

    # Save artifacts
    saved_ckpt, saved_meta = model.save_checkpoint(checkpoint_file, metadata=metadata_payload)
    logger.info("Saved model checkpoint: %s", saved_ckpt)
    logger.info("Saved metadata bundle: %s", saved_meta)

    result = TrainingResult(
        final_train_loss=final_train_loss,
        final_train_accuracy=final_train_acc,
        final_test_loss=final_test_loss,
        final_test_accuracy=final_test_acc,
        epoch_history=epoch_history,
        checkpoint_path=str(saved_ckpt),
        metadata_path=str(saved_meta),
        duration_seconds=duration,
    )

    return model, result


def parse_args() -> TrainingConfig:
    """Parse command-line arguments into a TrainingConfig instance."""
    parser = argparse.ArgumentParser(description="Train CIFAR-10 CNN for SemanticDFL")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Mini-batch size (paper default: 64)")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate (paper default: 0.01)")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="output/models", help="Output artifact directory")
    parser.add_argument("--data-dir", type=str, default="data", help="CIFAR-10 raw dataset directory")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for fast verification")
    parser.add_argument("--synthetic-samples", type=int, default=512, help="Number of synthetic samples if --synthetic")

    args = parser.parse_args()
    return TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        seed=args.seed,
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        synthetic=args.synthetic,
        synthetic_samples=args.synthetic_samples,
    )


if __name__ == "__main__":
    cfg = parse_args()
    train_cifar_model(cfg)
