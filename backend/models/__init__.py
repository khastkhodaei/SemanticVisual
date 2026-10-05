"""Model architecture and parameter serialization modules for SemanticDFL."""

from backend.models.cifar_cnn import CIFAR10CNN, CIFAR10_CLASSES
from backend.models.fmnist_cnn import (
    FMNISTCNN,
    FMNIST_CLASSES,
    EXPECTED_FMNIST_PARAMETER_COUNT,
)
from backend.models.tiny_imagenet_resnet import (
    TinyImageNetResNet18,
    TINY_IMAGENET_NUM_CLASSES,
)
from backend.models.speech_resnet import (
    AudioToLogMelSpectrogram,
    SpeechResNet18,
    SPEECH_COMMANDS_CLASSES,
    EXPECTED_SPEECH_PARAMETER_COUNT,
)
from backend.models.news_albert import (
    NewsAlbertTokenizer,
    NewsAlbertForSequenceClassification,
    NEWSGROUP_20_CLASSES,
    EXPECTED_ALBERT_PARAMETER_COUNT,
)
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
    "FMNISTCNN",
    "FMNIST_CLASSES",
    "EXPECTED_FMNIST_PARAMETER_COUNT",
    "TinyImageNetResNet18",
    "TINY_IMAGENET_NUM_CLASSES",
    "SpeechResNet18",
    "SPEECH_COMMANDS_CLASSES",
    "AudioToLogMelSpectrogram",
    "EXPECTED_SPEECH_PARAMETER_COUNT",
    "NewsAlbertTokenizer",
    "NewsAlbertForSequenceClassification",
    "NEWSGROUP_20_CLASSES",
    "EXPECTED_ALBERT_PARAMETER_COUNT",
    "CANONICAL_LAYER_ORDER",
    "EXPECTED_PARAMETER_COUNT",
    "flatten_parameters",
    "unflatten_parameters",
    "save_flat_parameters_artifact",
    "load_flat_parameters_artifact",
    "export_checkpoint_to_flat_artifact",
]
