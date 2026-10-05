"""Deterministic Parameter Flattening and Serialization Module.

Implements pure, mathematical parameter flattening and reconstruction routines for
decentralized federated learning signatures and similarity computations in SemanticDFL.

Features:
- Pure functional interface with zero unexpected side-effects on model gradients/state.
- Strict canonical parameter ordering preserving the exact layer sequence.
- Precise slice indexing for bidirectional reconstruction (unflattening).
- L2-norm computation for downstream cosine similarity & Top-P sparsification.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn


from backend.models.cifar_cnn import CIFAR10CNN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ParameterFlattening")

# Canonical layer order matching the SemanticDFL paper architecture
CANONICAL_LAYER_ORDER: List[str] = [
    "conv1.weight",
    "conv1.bias",
    "conv2.weight",
    "conv2.bias",
    "fc1.weight",
    "fc1.bias",
    "fc2.weight",
    "fc2.bias",
]

EXPECTED_PARAMETER_COUNT: int = 2156490
EXPECTED_FMNIST_PARAMETER_COUNT: int = 1663370


def flatten_parameters(model: nn.Module) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """Flatten all model parameters into a single contiguous 1D float32 tensor.

    Preserves the exact canonical layer order:
    `conv1.weight`, `conv1.bias`, `conv2.weight`, `conv2.bias`,
    `fc1.weight`, `fc1.bias`, `fc2.weight`, `fc2.bias`.

    Args:
        model: PyTorch model instance (e.g. CIFAR10CNN, FMNISTCNN).

    Returns:
        Tuple containing:
            - 1D Tensor of shape (num_parameters,), e.g. (2156490,), dtype=torch.float32.
            - Metadata dictionary with layer_slices, l2_norm, num_parameters, model_name, and canonical_layers.
    """
    param_dict = dict(model.named_parameters())
    flat_tensors: List[torch.Tensor] = []
    layer_slices: Dict[str, Dict[str, Any]] = {}
    current_idx: int = 0

    # If all canonical layers are present, use the strict canonical order
    keys_to_process = (
        [k for k in CANONICAL_LAYER_ORDER if k in param_dict]
        if all(k in param_dict for k in CANONICAL_LAYER_ORDER)
        else list(param_dict.keys())
    )

    for name in keys_to_process:
        param = param_dict[name]
        # Detach and convert to CPU float32 1D tensor without mutating gradients
        detached_flat = param.detach().cpu().to(dtype=torch.float32).view(-1)
        numel = detached_flat.numel()

        layer_slices[name] = {
            "start_idx": current_idx,
            "end_idx": current_idx + numel,
            "shape": list(param.shape),
            "numel": numel,
        }
        flat_tensors.append(detached_flat)
        current_idx += numel

    flat_tensor = torch.cat(flat_tensors, dim=0).contiguous()
    l2_norm = float(torch.linalg.norm(flat_tensor).item())
    num_parameters = int(flat_tensor.numel())

    metadata: Dict[str, Any] = {
        "num_parameters": num_parameters,
        "l2_norm": l2_norm,
        "layer_slices": layer_slices,
        "canonical_layers": keys_to_process,
        "model_name": model.__class__.__name__,
    }

    return flat_tensor, metadata


def unflatten_parameters(
    flat_tensor: torch.Tensor,
    layer_slices: Dict[str, Any],
    target_model: nn.Module,
) -> None:
    """Reconstruct layer tensors from a 1D flat tensor and load into target_model in-place.

    Args:
        flat_tensor: 1D Tensor of shape (num_parameters,).
        layer_slices: Dictionary mapping layer names to {start_idx, end_idx, shape, numel}.
        target_model: PyTorch model instance whose parameters will be populated.

    Raises:
        ValueError: If flat_tensor dimensions or layer slices do not align with model parameters.
    """
    if flat_tensor.dim() != 1:
        raise ValueError(f"Expected 1D flat tensor, got shape {tuple(flat_tensor.shape)}")

    state_dict = target_model.state_dict()

    with torch.no_grad():
        for name, slice_info in layer_slices.items():
            if name not in state_dict:
                raise KeyError(f"Layer '{name}' not found in target_model state_dict.")

            start_idx = slice_info["start_idx"]
            end_idx = slice_info["end_idx"]
            shape = tuple(slice_info["shape"])
            numel = slice_info["numel"]

            if end_idx > flat_tensor.numel():
                raise ValueError(
                    f"Slice [{start_idx}:{end_idx}] exceeds tensor length {flat_tensor.numel()}"
                )

            extracted_segment = flat_tensor[start_idx:end_idx].view(shape)
            if extracted_segment.numel() != numel:
                raise ValueError(
                    f"Extracted elements {extracted_segment.numel()} mismatch slice numel {numel}"
                )

            target_device = state_dict[name].device
            target_dtype = state_dict[name].dtype
            state_dict[name].copy_(extracted_segment.to(device=target_device, dtype=target_dtype))


def save_flat_parameters_artifact(
    flat_tensor: torch.Tensor,
    metadata: Dict[str, Any],
    output_path: Union[str, Path],
    source_checkpoint: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Path:
    """Save the flattened parameter vector and metadata bundle to disk.

    Args:
        flat_tensor: 1D parameter tensor.
        metadata: Metadata dictionary from flatten_parameters.
        output_path: Target .pt file path (e.g. output/models/cifar10_flat_parameters.pt).
        source_checkpoint: Optional reference to source checkpoint filename.
        model_name: Optional explicit model architecture name (e.g. 'CIFAR10CNN', 'FMNISTCNN').

    Returns:
        Path to saved artifact.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    resolved_model_name = model_name or metadata.get("model_name", "CIFAR10CNN")
    default_source_ckpt = (
        "output/models/fmnist_cnn_checkpoint.pt"
        if resolved_model_name == "FMNISTCNN"
        else "output/models/cifar10_cnn_checkpoint.pt"
    )

    payload = {
        "flat_parameters": flat_tensor,
        "layer_slices": metadata.get("layer_slices", {}),
        "l2_norm": metadata.get("l2_norm", 0.0),
        "num_parameters": int(flat_tensor.numel()),
        "metadata": {
            "model_name": resolved_model_name,
            "source_checkpoint": source_checkpoint or default_source_ckpt,
            "dtype": str(flat_tensor.dtype),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    temp_file = out_file.with_name(f"{out_file.stem}_tmp_{random.randint(10000, 99999)}{out_file.suffix}")
    try:
        torch.save(payload, temp_file)
        if out_file.exists():
            try:
                out_file.unlink()
            except Exception:
                pass
        temp_file.replace(out_file)
    except Exception:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        torch.save(payload, out_file)

    logger.info("Saved flattened parameter artifact: %s (%d elements)", out_file, flat_tensor.numel())
    return out_file



def load_flat_parameters_artifact(
    artifact_path: Union[str, Path],
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """Load flattened parameter vector and metadata from saved artifact file.

    Args:
        artifact_path: Path to the .pt file.

    Returns:
        Tuple of (flat_tensor, metadata_dict).
    """
    path = Path(artifact_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Artifact file not found: {path}")

    payload = torch.load(path, map_location="cpu")
    flat_tensor = payload["flat_parameters"]
    metadata = {
        "layer_slices": payload.get("layer_slices", {}),
        "l2_norm": payload.get("l2_norm", 0.0),
        "num_parameters": payload.get("num_parameters", flat_tensor.numel()),
        "metadata": payload.get("metadata", {}),
    }
    return flat_tensor, metadata


def export_checkpoint_to_flat_artifact(
    checkpoint_path: Union[str, Path] = "output/models/cifar10_cnn_checkpoint.pt",
    output_path: Union[str, Path] = "output/models/cifar10_flat_parameters.pt",
) -> Tuple[Path, torch.Tensor, Dict[str, Any]]:
    """End-to-end routine: load checkpoint, flatten parameters, and save artifact bundle.

    Args:
        checkpoint_path: Source model checkpoint path.
        output_path: Destination flat parameters artifact path.

    Returns:
        Tuple of (saved_artifact_path, flat_tensor, metadata).
    """
    ckpt_file = Path(checkpoint_path).resolve()
    out_file = Path(output_path).resolve()

    if not ckpt_file.exists():
        logger.warning("Checkpoint %s not found. Instantiating fresh CIFAR10CNN.", ckpt_file)
        model = CIFAR10CNN()
    else:
        logger.info("Loading checkpoint from %s...", ckpt_file)
        model, _ = CIFAR10CNN.load_checkpoint(ckpt_file)

    flat_tensor, metadata = flatten_parameters(model)
    saved_path = save_flat_parameters_artifact(
        flat_tensor=flat_tensor,
        metadata=metadata,
        output_path=out_file,
        source_checkpoint=str(ckpt_file),
    )
    return saved_path, flat_tensor, metadata


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for parameter flattening utility."""
    parser = argparse.ArgumentParser(description="Flatten CIFAR-10 CNN parameters into 1D vector")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="output/models/cifar10_cnn_checkpoint.pt",
        help="Path to source checkpoint",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/models/cifar10_flat_parameters.pt",
        help="Path to output flat parameters artifact",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_checkpoint_to_flat_artifact(args.checkpoint, args.output)
