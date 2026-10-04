"""Model architecture and parameter serialization modules for SemanticDFL."""

from backend.models.cifar_cnn import CIFAR10CNN, CIFAR10_CLASSES
from backend.models.flattening import (
    CANONICAL_LAYER_ORDER,
    EXPECTED_PARAMETER_COUNT,
    export_checkpoint_to_flat_artifact,
    flatten_parameters,
    load_flat_parameters_artifact,
    save_flat_parameters_artifact,
    unflatten_parameters,
)

__all__ = [
    "CIFAR10CNN",
    "CIFAR10_CLASSES",
    "CANONICAL_LAYER_ORDER",
    "EXPECTED_PARAMETER_COUNT",
    "flatten_parameters",
    "unflatten_parameters",
    "save_flat_parameters_artifact",
    "load_flat_parameters_artifact",
    "export_checkpoint_to_flat_artifact",
]
