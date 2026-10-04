"""CIFAR-10 Convolutional Neural Network (CNN) Architecture.

This module implements the exact 2-convolutional-layer CNN architecture specified
in the SemanticDFL research paper (Section 5.1, 'Datasets and Models'):
- Two 5x5 Convolutional layers (Conv1: 3->32, Conv2: 32->64)
- MaxPool2d (2x2, stride=2) after each Conv layer
- Fully Connected feature layer (512 units) with ReLU
- Output Linear classification layer (10 classes for CIFAR-10)

Adheres strictly to clean modular architecture with full type hints, parameter
introspection, and robust serialization interfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn



# Canonical CIFAR-10 Class Map (10 classes)
CIFAR10_CLASSES: Dict[int, str] = {
    0: "airplane",
    1: "automobile",
    2: "bird",
    3: "cat",
    4: "deer",
    5: "dog",
    6: "frog",
    7: "horse",
    8: "ship",
    9: "truck",
}


class CIFAR10CNN(nn.Module):
    """2-Stage Convolutional Neural Network for CIFAR-10 Image Classification.

    Topology:
        - Conv1: Conv2d(in_channels=3, out_channels=32, kernel_size=5, stride=1, padding=2) -> ReLU -> MaxPool2d(2, 2)
        - Conv2: Conv2d(in_channels=32, out_channels=64, kernel_size=5, stride=1, padding=2) -> ReLU -> MaxPool2d(2, 2)
        - FC1: Linear(in_features=64 * 8 * 8 = 4096, out_features=512) -> ReLU
        - Dropout (optional, default 0.0)
        - FC2: Linear(in_features=512, out_features=10)
    """

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 10,
        conv1_channels: int = 32,
        conv2_channels: int = 64,
        fc1_dim: int = 512,
        kernel_size: int = 5,
        padding: int = 2,
        dropout_rate: float = 0.0,
    ) -> None:
        """Initialize the CIFAR10CNN architecture.

        Args:
            in_channels: Number of input image channels (default: 3 for RGB CIFAR-10).
            num_classes: Number of target classification categories (default: 10).
            conv1_channels: Number of feature maps in the first conv layer (default: 32).
            conv2_channels: Number of feature maps in the second conv layer (default: 64).
            fc1_dim: Dimensionality of the dense hidden layer (default: 512).
            kernel_size: Spatial dimensions of convolution kernels (default: 5).
            padding: Padding size for convolutions (default: 2 to preserve 32x32 -> 16x16 -> 8x8).
            dropout_rate: Dropout probability before the final classifier (default: 0.0).
        """
        super().__init__()

        self.in_channels = in_channels
        self.num_classes = num_classes
        self.conv1_channels = conv1_channels
        self.conv2_channels = conv2_channels
        self.fc1_dim = fc1_dim
        self.kernel_size = kernel_size
        self.padding = padding
        self.dropout_rate = dropout_rate

        # Convolutional Block 1
        self.conv1 = nn.Conv2d(
            in_channels=in_channels,
            out_channels=conv1_channels,
            kernel_size=kernel_size,
            stride=1,
            padding=padding,
        )
        self.relu1 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Convolutional Block 2
        self.conv2 = nn.Conv2d(
            in_channels=conv1_channels,
            out_channels=conv2_channels,
            kernel_size=kernel_size,
            stride=1,
            padding=padding,
        )
        self.relu2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Compute flattened feature dimension dynamically
        # Default 32x32: after pool1 (16x16), after pool2 (8x8) -> 64 * 8 * 8 = 4096
        self.flattened_dim = self._calculate_flattened_dim()

        # Fully Connected Block
        self.fc1 = nn.Linear(self.flattened_dim, fc1_dim)
        self.relu3 = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(p=dropout_rate) if dropout_rate > 0.0 else nn.Identity()
        self.fc2 = nn.Linear(fc1_dim, num_classes)

    def _calculate_flattened_dim(self) -> int:
        """Compute the flattened spatial dimension by passing a dummy tensor."""
        with torch.no_grad():
            dummy = torch.zeros(1, self.in_channels, 32, 32)
            x = self.pool1(self.relu1(self.conv1(dummy)))
            x = self.pool2(self.relu2(self.conv2(x)))
            return int(x.numel())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass computing class logits for an input batch.

        Args:
            x: Input tensor of shape (B, in_channels, H, W), expected (B, 3, 32, 32).

        Returns:
            Logits tensor of shape (B, num_classes), e.g. (B, 10).
        """
        if x.dim() != 4:
            raise ValueError(f"Expected 4D input tensor (B, C, H, W), got shape {tuple(x.shape)}")
        if x.size(1) != self.in_channels:
            raise ValueError(
                f"Expected input with {self.in_channels} channels, got {x.size(1)} channels."
            )

        # Feature Extraction
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)

        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)

        # Classification Head
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = self.relu3(x)
        x = self.dropout(x)
        logits = self.fc2(x)
        return logits

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract the 512-dimensional penultimate feature representation.

        Args:
            x: Input image tensor of shape (B, 3, 32, 32).

        Returns:
            Dense latent representation of shape (B, 512).
        """
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.pool1(x)

        x = self.conv2(x)
        x = self.relu2(x)
        x = self.pool2(x)

        x = torch.flatten(x, 1)
        x = self.fc1(x)
        features = self.relu3(x)
        return features

    def count_parameters(self) -> int:
        """Return the total number of trainable parameters in the model."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_topology_summary(self) -> Dict[str, Any]:
        """Return a structured metadata dictionary describing the architecture."""
        return {
            "model_type": "CIFAR10CNN",
            "in_channels": self.in_channels,
            "num_classes": self.num_classes,
            "conv1": {
                "in_channels": self.in_channels,
                "out_channels": self.conv1_channels,
                "kernel_size": self.kernel_size,
                "padding": self.padding,
                "activation": "ReLU",
                "pool": "MaxPool2d(2, 2)",
            },
            "conv2": {
                "in_channels": self.conv1_channels,
                "out_channels": self.conv2_channels,
                "kernel_size": self.kernel_size,
                "padding": self.padding,
                "activation": "ReLU",
                "pool": "MaxPool2d(2, 2)",
            },
            "fc1": {
                "in_features": self.flattened_dim,
                "out_features": self.fc1_dim,
                "activation": "ReLU",
            },
            "dropout_rate": self.dropout_rate,
            "fc2": {
                "in_features": self.fc1_dim,
                "out_features": self.num_classes,
            },
            "total_parameters": self.count_parameters(),
        }

    def save_checkpoint(
        self,
        filepath: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Path, Path]:
        """Serialize model weights state_dict and associated metadata atomically.

        Args:
            filepath: Target file path for the .pt checkpoint (e.g. output/models/cifar10_cnn.pt).
            metadata: Optional dictionary with training metrics and hyperparameter metadata.

        Returns:
            Tuple of (checkpoint_path, metadata_path).
        """
        ckpt_path = Path(filepath).resolve()
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare checkpoint payload
        checkpoint_payload = {
            "state_dict": self.state_dict(),
            "model_config": {
                "in_channels": self.in_channels,
                "num_classes": self.num_classes,
                "conv1_channels": self.conv1_channels,
                "conv2_channels": self.conv2_channels,
                "fc1_dim": self.fc1_dim,
                "kernel_size": self.kernel_size,
                "padding": self.padding,
                "dropout_rate": self.dropout_rate,
            },
            "total_parameters": self.count_parameters(),
        }
        temp_ckpt = ckpt_path.with_name(f"{ckpt_path.stem}_tmp_{random.randint(10000, 99999)}{ckpt_path.suffix}")

        try:
            torch.save(checkpoint_payload, temp_ckpt)
            if ckpt_path.exists():
                try:
                    ckpt_path.unlink()
                except Exception:
                    pass
            temp_ckpt.replace(ckpt_path)
        except Exception:
            if temp_ckpt.exists():
                try:
                    temp_ckpt.unlink()
                except Exception:
                    pass
            torch.save(checkpoint_payload, ckpt_path)


        # Prepare and save JSON metadata
        meta_path = ckpt_path.parent / "model_metadata.json"
        complete_metadata: Dict[str, Any] = {
            "model_name": "CIFAR10CNN",
            "checkpoint_filename": ckpt_path.name,
            "num_parameters": self.count_parameters(),
            "topology": self.get_topology_summary(),
            "classes": CIFAR10_CLASSES,
        }
        if metadata:
            complete_metadata.update(metadata)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(complete_metadata, f, indent=2)

        return ckpt_path, meta_path

    @classmethod
    def load_checkpoint(
        cls,
        filepath: Union[str, Path],
        device: Optional[Union[str, torch.device]] = None,
    ) -> Tuple[CIFAR10CNN, Dict[str, Any]]:
        """Load model weights and metadata from a saved checkpoint file.

        Args:
            filepath: Path to the .pt checkpoint file.
            device: Target torch device (CPU or CUDA).

        Returns:
            Tuple of (instantiated_model, metadata_dict).
        """
        ckpt_path = Path(filepath).resolve()
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")

        target_device = torch.device(device) if device else torch.device("cpu")
        checkpoint = torch.load(ckpt_path, map_location=target_device)

        config = checkpoint.get("model_config", {})
        model = cls(
            in_channels=config.get("in_channels", 3),
            num_classes=config.get("num_classes", 10),
            conv1_channels=config.get("conv1_channels", 32),
            conv2_channels=config.get("conv2_channels", 64),
            fc1_dim=config.get("fc1_dim", 512),
            kernel_size=config.get("kernel_size", 5),
            padding=config.get("padding", 2),
            dropout_rate=config.get("dropout_rate", 0.0),
        )
        model.load_state_dict(checkpoint["state_dict"])
        model.to(target_device)
        model.eval()

        # Load metadata if present
        meta_path = ckpt_path.parent / "model_metadata.json"
        metadata: Dict[str, Any] = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        return model, metadata
