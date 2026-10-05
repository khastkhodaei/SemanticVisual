"""Google Speech Commands ResNet-18 Benchmark Architecture (SemanticDFL Section 5.1).

Implements ResNet-18 adapted for 1-channel Log-Mel spectrogram inputs representing
1-second 16kHz audio command waveforms:
- Preprocessor: AudioToLogMelSpectrogram converting (B, 16000) audio waveforms into
  (B, 1, 64, 101) Log-Mel spectrograms using pure PyTorch FFT with zero external audio dependencies.
- Model: ResNet-18 with 1-channel stem, 4 residual stages [2, 2, 2, 2] over [64, 128, 256, 512]
  channels, adaptive average pooling (512 features), and 10 classification outputs.
- 10 canonical command classes: yes, no, up, down, left, right, on, off, stop, go.
- Total parameters: 11,172,810 (~11.17M - 11.2M parameters).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import numpy as np
import torch
import torch.nn as nn

SPEECH_COMMANDS_CLASSES: Dict[int, str] = {
    0: "yes",
    1: "no",
    2: "up",
    3: "down",
    4: "left",
    5: "right",
    6: "on",
    7: "off",
    8: "stop",
    9: "go",
}

EXPECTED_SPEECH_PARAMETER_COUNT: int = 11_172_810


def _build_mel_filterbank(
    sample_rate: int = 16000,
    n_fft: int = 400,
    n_mels: int = 64,
    f_min: float = 0.0,
    f_max: Optional[float] = None,
) -> torch.Tensor:
    """Construct standard triangular Mel-filterbank matrix in pure PyTorch."""
    if f_max is None:
        f_max = float(sample_rate // 2)

    def hz_to_mel(hz: float) -> float:
        return 2595.0 * math.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel: float) -> float:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    mel_min = hz_to_mel(f_min)
    mel_max = hz_to_mel(f_max)
    mel_points = torch.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = mel_to_hz(mel_points)

    num_freqs = n_fft // 2 + 1
    fft_freqs = torch.linspace(0, sample_rate // 2, num_freqs)

    filterbank = torch.zeros(n_mels, num_freqs)
    for m in range(1, n_mels + 1):
        f_left = hz_points[m - 1]
        f_center = hz_points[m]
        f_right = hz_points[m + 1]

        lower = (fft_freqs - f_left) / max(1e-6, f_center - f_left)
        upper = (f_right - fft_freqs) / max(1e-6, f_right - f_center)
        filterbank[m - 1] = torch.maximum(torch.tensor(0.0), torch.minimum(lower, upper))

    return filterbank


class AudioToLogMelSpectrogram(nn.Module):
    """Pure PyTorch Audio Preprocessor: Waveform -> Log-Mel Spectrogram.

    Converts 1-second 16kHz raw audio waveform (16,000 samples) into
    Log-Mel spectrogram tensor of shape (B, 1, n_mels, time_steps) e.g. (B, 1, 64, 101).
    Zero external dependencies (pure PyTorch torch.stft).
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        n_mels: int = 64,
        n_fft: int = 400,
        hop_length: int = 160,
    ) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length

        mel_fb = _build_mel_filterbank(sample_rate, n_fft, n_mels)
        self.register_buffer("mel_filterbank", mel_fb)
        self.register_buffer("window", torch.hann_window(n_fft))

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        """Transform raw waveform into Log-Mel spectrogram.

        Args:
            waveform: Tensor of shape (B, time_samples) or (time_samples,), e.g. (B, 16000).

        Returns:
            Log-Mel spectrogram tensor of shape (B, 1, n_mels, time_steps).
        """
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        elif waveform.dim() == 3:
            waveform = waveform.squeeze(1)

        # Ensure correct device
        if self.window.device != waveform.device:
            self.window = self.window.to(waveform.device)
        if self.mel_filterbank.device != waveform.device:
            self.mel_filterbank = self.mel_filterbank.to(waveform.device)

        # Compute Short-Time Fourier Transform (STFT)
        stft_res = torch.stft(
            waveform,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.n_fft,
            window=self.window,
            center=True,
            pad_mode="reflect",
            normalized=False,
            onesided=True,
            return_complex=True,
        )

        # Power spectrogram
        power_spec = stft_res.abs().pow(2)  # Shape: (B, num_freqs, time_steps)

        # Mel filterbank mapping: (n_mels, num_freqs) @ (B, num_freqs, time_steps)
        mel_spec = torch.matmul(self.mel_filterbank, power_spec)

        # Log scale compression
        log_mel = torch.log(torch.clamp(mel_spec, min=1e-6))

        # Add channel dimension: (B, 1, n_mels, time_steps)
        return log_mel.unsqueeze(1)


def conv3x3(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    """3x3 convolution with padding."""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride, padding=1, bias=False)


def conv1x1(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    """1x1 convolution."""
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)


class BasicBlock(nn.Module):
    """Standard ResNet BasicBlock with two 3x3 convolutions and skip connection."""

    expansion: int = 1

    def __init__(
        self,
        inplanes: int,
        planes: int,
        stride: int = 1,
        downsample: Optional[nn.Module] = None,
    ) -> None:
        super().__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
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


class SpeechResNet18(nn.Module):
    """ResNet-18 adapted for 1-channel Log-Mel spectrogram inputs (Google Speech Commands).

    Topology:
        - Stem: Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=False) -> BatchNorm2d(64) -> ReLU -> MaxPool2d
        - Stage 1 (layer1): 2 BasicBlocks (64 channels)
        - Stage 2 (layer2): 2 BasicBlocks (128 channels, stride 2)
        - Stage 3 (layer3): 2 BasicBlocks (256 channels, stride 2)
        - Stage 4 (layer4): 2 BasicBlocks (512 channels, stride 2)
        - Head: AdaptiveAvgPool2d((1, 1)) -> Linear(512, num_classes=10)
    """

    def __init__(
        self,
        in_channels: int = 1,
        num_classes: int = 10,
        stem_kernel_size: int = 3,
        stem_stride: int = 1,
    ) -> None:
        """Initialize SpeechResNet18.

        Args:
            in_channels: Number of spectrogram channels (default: 1 for Log-Mel spectrogram).
            num_classes: Number of speech command target categories (default: 10).
            stem_kernel_size: Initial convolution kernel size (default: 3).
            stem_stride: Initial convolution stride (default: 1).
        """
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.inplanes = 64

        padding = stem_kernel_size // 2

        # 1-channel stem for audio spectrogram
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

        # 4 residual stages
        self.layer1 = self._make_layer(BasicBlock, 64, 2, stride=1)
        self.layer2 = self._make_layer(BasicBlock, 128, 2, stride=2)
        self.layer3 = self._make_layer(BasicBlock, 256, 2, stride=2)
        self.layer4 = self._make_layer(BasicBlock, 512, 2, stride=2)

        # Head
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * BasicBlock.expansion, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

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
        """Forward pass computing command class logits.

        Args:
            x: Input spectrogram tensor of shape (B, 1, 64, 101).

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

        # Classification Head
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract the 512-dimensional penultimate feature representation.

        Args:
            x: Input spectrogram tensor of shape (B, 1, 64, 101).

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
            "model_type": "SpeechResNet18",
            "in_channels": self.in_channels,
            "num_classes": self.num_classes,
            "stem": {
                "in_channels": self.in_channels,
                "out_channels": 64,
                "kernel_size": 3,
                "stride": 1,
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
        if ckpt_path.name == "speech_resnet18.pt" or ckpt_path.name == "model.pt":
            meta_path = ckpt_path.parent / "model_metadata.json"

        complete_metadata: Dict[str, Any] = {
            "model_name": "SpeechResNet18",
            "checkpoint_filename": ckpt_path.name,
            "num_parameters": self.count_parameters(),
            "topology": self.get_topology_summary(),
            "classes": SPEECH_COMMANDS_CLASSES,
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
    ) -> Tuple[SpeechResNet18, Dict[str, Any]]:
        """Load model weights and metadata from a saved checkpoint file."""
        ckpt_path = Path(filepath).resolve()
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")

        target_device = torch.device(device) if device else torch.device("cpu")
        checkpoint = torch.load(ckpt_path, map_location=target_device)

        config = checkpoint.get("model_config", {})
        model = cls(
            in_channels=config.get("in_channels", 1),
            num_classes=config.get("num_classes", 10),
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
