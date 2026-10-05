"""ResNet-18 Architecture for Tiny-ImageNet Benchmark (SemanticDFL Section 5.1).

This module implements ResNet-18 adapted for 64x64 3-channel RGB images with 200 classes:
- Custom stem Conv1 (kernel 3x3 or 5x5, stride 1 or 2, padding matching spatial preservation)
- 4 residual stages with BasicBlocks (expansion=1) containing [2, 2, 2, 2] blocks (64, 128, 256, 512 channels)
- Global adaptive average pooling to 512-dimensional feature representations
- Final linear classifier with 200 output logits for Tiny-ImageNet categories
- Total parameter count: ~11.27M - 11.7M parameters
"""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import torch
import torch.nn as nn

TINY_IMAGENET_NUM_CLASSES: int = 200
EXPECTED_TINY_IMAGENET_PARAMETER_COUNT_APPROX: int = 11_271_432


def conv3x3(in_planes: int, out_planes: int, stride: int = 1, groups: int = 1, dilation: int = 1) -> nn.Conv2d:
    """3x3 convolution with padding."""
    return nn.Conv2d(
        in_planes,
        out_planes,
        kernel_size=3,
        stride=stride,
        padding=dilation,
        groups=groups,
        bias=False,
        dilation=dilation,
    )


def conv1x1(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    """1x1 convolution."""
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)


class BasicBlock(nn.Module):
    """Standard ResNet BasicBlock with two 3x3 convolutions and identity/downsample shortcut."""

    expansion: int = 1

    def __init__(
        self,
        inplanes: int,
        planes: int,
        stride: int = 1,
        downsample: Optional[nn.Module] = None,
        groups: int = 1,
        base_width: int = 64,
        dilation: int = 1,
        norm_layer: Optional[Callable[..., nn.Module]] = None,
    ) -> None:
        super().__init__()
        if norm_layer is None:
            norm_layer = nn.BatchNorm2d
        if groups != 1 or base_width != 64:
            raise ValueError("BasicBlock only supports groups=1 and base_width=64")
        if dilation > 1:
            raise NotImplementedError("Dilation > 1 not supported in BasicBlock")

        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = norm_layer(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = norm_layer(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)

        return out


class TinyImageNetResNet18(nn.Module):
    """ResNet-18 adapted for Tiny-ImageNet (64x64 inputs, 200 classes).

    Architecture:
        - Stem: Conv2d(3, 64, kernel_size=3/5, stride=1/2, padding) -> BatchNorm2d(64) -> ReLU -> MaxPool2d
        - Stage 1 (layer1): 2 BasicBlocks (64 channels)
        - Stage 2 (layer2): 2 BasicBlocks (128 channels, stride 2)
        - Stage 3 (layer3): 2 BasicBlocks (256 channels, stride 2)
        - Stage 4 (layer4): 2 BasicBlocks (512 channels, stride 2)
        - Head: AdaptiveAvgPool2d((1, 1)) -> Linear(512, num_classes=200)
    """

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 200,
        stem_kernel_size: int = 3,
        stem_stride: int = 1,
        zero_init_residual: bool = False,
    ) -> None:
        """Initialize TinyImageNetResNet18.

        Args:
            in_channels: Input image channel count (default: 3 for RGB).
            num_classes: Target class categories (default: 200 for Tiny-ImageNet).
            stem_kernel_size: Kernel dimension for initial convolution (default: 3, supports 5).
            stem_stride: Stride for initial convolution (default: 1 for 64x64).
            zero_init_residual: Zero-initialize the last BN in each residual branch.
        """
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.stem_kernel_size = stem_kernel_size
        self.stem_stride = stem_stride
        self.inplanes = 64

        padding = stem_kernel_size // 2

        # Custom Stem for 64x64 inputs
        self.conv1 = nn.Conv2d(
            in_channels,
            self.inplanes,
            kernel_size=stem_kernel_size,
            stride=stem_stride,
            padding=padding,
            bias=False,
        )
        self.bn1 = nn.BatchNorm2d(self.inplanes)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        # ResNet-18 stages: [2, 2, 2, 2] BasicBlocks
        self.layer1 = self._make_layer(BasicBlock, 64, 2, stride=1)
        self.layer2 = self._make_layer(BasicBlock, 128, 2, stride=2)
        self.layer3 = self._make_layer(BasicBlock, 256, 2, stride=2)
        self.layer4 = self._make_layer(BasicBlock, 512, 2, stride=2)

        # Global Pooling and Linear Classification Head
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * BasicBlock.expansion, num_classes)

        # Weight initialization
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

        if zero_init_residual:
            for m in self.modules():
                if isinstance(m, BasicBlock) and m.bn2.weight is not None:
                    nn.init.constant_(m.bn2.weight, 0)

    def _make_layer(
        self,
        block: Type[BasicBlock],
        planes: int,
        blocks: int,
        stride: int = 1,
    ) -> nn.Sequential:
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(self.inplanes, planes * block.expansion, stride),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass computing class logits for an input batch.

        Args:
            x: Input image tensor of shape (B, in_channels, 64, 64).

        Returns:
            Logits tensor of shape (B, num_classes).
        """
        if x.dim() != 4:
            raise ValueError(f"Expected 4D input tensor (B, C, H, W), got shape {tuple(x.shape)}")
        if x.size(1) != self.in_channels:
            raise ValueError(
                f"Expected input with {self.in_channels} channels, got {x.size(1)} channels."
            )

        # Stem
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        # Residual Stages
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        # Head
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract the 512-dimensional penultimate feature representation.

        Args:
            x: Input image tensor of shape (B, in_channels, 64, 64).

        Returns:
            Dense feature tensor of shape (B, 512).
        """
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        features = torch.flatten(x, 1)
        return features

    def count_parameters(self) -> int:
        """Return total trainable parameter count."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_topology_summary(self) -> Dict[str, Any]:
        """Return structured topology metadata dictionary."""
        return {
            "model_type": "TinyImageNetResNet18",
            "in_channels": self.in_channels,
            "num_classes": self.num_classes,
            "stem": {
                "kernel_size": self.stem_kernel_size,
                "stride": self.stem_stride,
                "out_channels": 64,
            },
            "stages": {
                "layer1": "2 BasicBlocks (64 channels)",
                "layer2": "2 BasicBlocks (128 channels)",
                "layer3": "2 BasicBlocks (256 channels)",
                "layer4": "2 BasicBlocks (512 channels)",
            },
            "head": {
                "pooling": "AdaptiveAvgPool2d((1, 1))",
                "in_features": 512,
                "out_features": self.num_classes,
            },
            "total_parameters": self.count_parameters(),
        }

    def save_checkpoint(
        self,
        filepath: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Path, Path]:
        """Serialize model weights state_dict and associated metadata atomically."""
        ckpt_path = Path(filepath).resolve()
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "state_dict": self.state_dict(),
            "model_config": {
                "in_channels": self.in_channels,
                "num_classes": self.num_classes,
                "stem_kernel_size": self.stem_kernel_size,
                "stem_stride": self.stem_stride,
            },
            "total_parameters": self.count_parameters(),
        }

        temp_ckpt = ckpt_path.with_name(
            f"{ckpt_path.stem}_tmp_{random.randint(10000, 99999)}{ckpt_path.suffix}"
        )
        try:
            torch.save(payload, temp_ckpt)
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
            torch.save(payload, ckpt_path)

        meta_path = ckpt_path.parent / f"{ckpt_path.stem}_metadata.json"
        if ckpt_path.name == "tiny_imagenet_resnet18.pt" or ckpt_path.name == "model.pt":
            meta_path = ckpt_path.parent / "model_metadata.json"

        complete_metadata: Dict[str, Any] = {
            "model_name": "TinyImageNetResNet18",
            "checkpoint_filename": ckpt_path.name,
            "num_parameters": self.count_parameters(),
            "topology": self.get_topology_summary(),
            "num_classes": self.num_classes,
        }
        if metadata:
            complete_metadata.update(metadata)

        default_meta_path = ckpt_path.parent / "model_metadata.json"
        with open(default_meta_path, "w", encoding="utf-8") as f:
            json.dump(complete_metadata, f, indent=2)

        if default_meta_path != meta_path:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(complete_metadata, f, indent=2)

        return ckpt_path, default_meta_path

    @classmethod
    def load_checkpoint(
        cls,
        filepath: Union[str, Path],
        device: Optional[Union[str, torch.device]] = None,
    ) -> Tuple[TinyImageNetResNet18, Dict[str, Any]]:
        """Load model weights and metadata from a saved checkpoint file."""
        ckpt_path = Path(filepath).resolve()
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")

        target_device = torch.device(device) if device else torch.device("cpu")
        checkpoint = torch.load(ckpt_path, map_location=target_device)

        config = checkpoint.get("model_config", {})
        model = cls(
            in_channels=config.get("in_channels", 3),
            num_classes=config.get("num_classes", 200),
            stem_kernel_size=config.get("stem_kernel_size", 3),
            stem_stride=config.get("stem_stride", 1),
        )
        model.load_state_dict(checkpoint["state_dict"])
        model.to(target_device)
        model.eval()

        meta_candidates = [
            ckpt_path.parent / f"{ckpt_path.stem}_metadata.json",
            ckpt_path.parent / "model_metadata.json",
        ]
        metadata: Dict[str, Any] = {}
        for candidate in meta_candidates:
            if candidate.exists():
                with open(candidate, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                break

        return model, metadata
