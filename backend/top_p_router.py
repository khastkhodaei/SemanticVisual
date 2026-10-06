from pathlib import Path
import re
import math
import shutil
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator
import numpy as np
import torch

from .top_p_lab import run_demo
from .top_p_costs import CostModelRequest, compute_cost_model
from backend.models.cifar_cnn import CIFAR10CNN
from backend.models.fmnist_cnn import FMNISTCNN
from backend.models.tiny_imagenet_resnet import TinyImageNetResNet18
from backend.models.speech_resnet import SpeechResNet18
from backend.models.news_albert import NewsAlbertForSequenceClassification
from backend.models.flattening import (
    CANONICAL_LAYER_ORDER,
    flatten_parameters,
    load_flat_parameters_artifact,
    save_flat_parameters_artifact,
)
from backend.training.train_cifar import (
    TrainingConfig as CifarTrainingConfig,
    train_cifar_model,
)
from backend.training.train_fmnist import (
    TrainingConfig as FmnistTrainingConfig,
    train_fmnist_model,
)
from backend.training.train_tiny_imagenet import (
    TrainingConfig as TinyTrainingConfig,
    train_tiny_imagenet_model,
)
from backend.training.train_speech import (
    TrainingConfig as SpeechTrainingConfig,
    train_speech_model,
)
from backend.training.train_albert import (
    TrainingConfig as AlbertTrainingConfig,
    run_training_pipeline as train_albert_pipeline,
)

router = APIRouter(prefix="/api/v1/toppaper", tags=["top-p-lab"])

# Module-level path constant — overridable via monkeypatch in tests
ROUNDS_DIR: Path = Path("output/models/rounds")


# ── Global 5-Benchmark Descriptor Catalog (Paper §5.1) ──────────────────────
BENCHMARKS_CATALOG: Dict[str, Dict[str, Any]] = {
    "cifar10": {
        "id": "cifar10",
        "name": "CIFAR-10",
        "model_name": "CIFAR10CNN",
        "dataset_name": "CIFAR-10",
        "total_parameters": 2156490,
        "parameter_count": 2156490,
        "m_formatted": "2.15M",
        "modality": "Vision (3x32x32 RGB)",
        "input_shape": [3, 32, 32],
        "num_classes": 10,
        "paper_optimal_p_ratio": 0.123,
        "paper_optimal_p_percent": 12.3,
        "paper_optimal_p": 265248,
        "topology": "2-Stage ConvNet (Conv1: 3->32, Conv2: 32->64, FC: 512, 10 classes)",
        "paper_hyperparameters": {
            "learning_rate": 0.01,
            "batch_size": 64,
            "epochs": 5,
            "momentum": 0.9,
            "weight_decay": 0.0001,
        },
        "canonical_layers": [
            "conv1.weight", "conv1.bias",
            "conv2.weight", "conv2.bias",
            "fc1.weight", "fc1.bias",
            "fc2.weight", "fc2.bias",
        ],
        "checkpoint_file": "cifar10_cnn_checkpoint.pt",
        "flat_artifact_file": "cifar10_flat_parameters.pt",
        "paper_section": "§5.1",
    },
    "fmnist": {
        "id": "fmnist",
        "name": "Fashion-MNIST",
        "model_name": "FMNISTCNN",
        "dataset_name": "Fashion-MNIST",
        "total_parameters": 1663370,
        "parameter_count": 1663370,
        "m_formatted": "1.65M",
        "modality": "Vision (1x28x28 Grayscale)",
        "input_shape": [1, 28, 28],
        "num_classes": 10,
        "paper_optimal_p_ratio": 0.123,
        "paper_optimal_p_percent": 12.3,
        "paper_optimal_p": 204595,
        "topology": "2-Stage ConvNet (Conv1: 1->32, Conv2: 32->64, FC: 512, 10 classes)",
        "paper_hyperparameters": {
            "learning_rate": 0.01,
            "batch_size": 64,
            "epochs": 1,
            "momentum": 0.9,
            "weight_decay": 0.0001,
        },
        "canonical_layers": [
            "conv1.weight", "conv1.bias",
            "conv2.weight", "conv2.bias",
            "fc1.weight", "fc1.bias",
            "fc2.weight", "fc2.bias",
        ],
        "checkpoint_file": "fmnist_cnn_checkpoint.pt",
        "flat_artifact_file": "fmnist_flat_parameters.pt",
        "paper_section": "§5.1",
    },
    "tiny_imagenet": {
        "id": "tiny_imagenet",
        "name": "Tiny-ImageNet",
        "model_name": "TinyImageNetResNet18",
        "dataset_name": "Tiny-ImageNet",
        "total_parameters": 11271432,
        "parameter_count": 11271432,
        "m_formatted": "11.27M",
        "modality": "Vision (3x64x64 RGB)",
        "input_shape": [3, 64, 64],
        "num_classes": 200,
        "paper_optimal_p_ratio": 0.096,
        "paper_optimal_p_percent": 9.6,
        "paper_optimal_p": 1082057,
        "topology": "ResNet-18 (4 Residual Stages [2, 2, 2, 2], Adaptive AvgPool, 200 classes)",
        "paper_hyperparameters": {
            "learning_rate": 0.05,
            "batch_size": 64,
            "epochs": 1,
            "momentum": 0.9,
            "weight_decay": 0.0001,
        },
        "canonical_layers": [
            "conv1.weight", "bn1.weight", "bn1.bias",
            "layer1.0.conv1.weight", "layer1.0.bn1.weight", "layer1.0.bn1.bias",
            "layer1.0.conv2.weight", "layer1.0.bn2.weight", "layer1.0.bn2.bias",
            "layer1.1.conv1.weight", "layer1.1.bn1.weight", "layer1.1.bn1.bias",
            "layer1.1.conv2.weight", "layer1.1.bn2.weight", "layer1.1.bn2.bias",
            "layer2.0.conv1.weight", "layer2.0.bn1.weight", "layer2.0.bn1.bias",
            "layer2.0.conv2.weight", "layer2.0.bn2.weight", "layer2.0.bn2.bias",
            "layer2.0.downsample.0.weight", "layer2.0.downsample.1.weight", "layer2.0.downsample.1.bias",
            "layer2.1.conv1.weight", "layer2.1.bn1.weight", "layer2.1.bn1.bias",
            "layer2.1.conv2.weight", "layer2.1.bn2.weight", "layer2.1.bn2.bias",
            "layer3.0.conv1.weight", "layer3.0.bn1.weight", "layer3.0.bn1.bias",
            "layer3.0.conv2.weight", "layer3.0.bn2.weight", "layer3.0.bn2.bias",
            "layer3.0.downsample.0.weight", "layer3.0.downsample.1.weight", "layer3.0.downsample.1.bias",
            "layer3.1.conv1.weight", "layer3.1.bn1.weight", "layer3.1.bn1.bias",
            "layer3.1.conv2.weight", "layer3.1.bn2.weight", "layer3.1.bn2.bias",
            "layer4.0.conv1.weight", "layer4.0.bn1.weight", "layer4.0.bn1.bias",
            "layer4.0.conv2.weight", "layer4.0.bn2.weight", "layer4.0.bn2.bias",
            "layer4.0.downsample.0.weight", "layer4.0.downsample.1.weight", "layer4.0.downsample.1.bias",
            "layer4.1.conv1.weight", "layer4.1.bn1.weight", "layer4.1.bn1.bias",
            "layer4.1.conv2.weight", "layer4.1.bn2.weight", "layer4.1.bn2.bias",
            "fc.weight", "fc.bias",
        ],
        "checkpoint_file": "tiny_imagenet_resnet18_checkpoint.pt",
        "flat_artifact_file": "tiny_imagenet_flat_parameters.pt",
        "paper_section": "§5.1",
    },
    "speech": {
        "id": "speech",
        "name": "Google Speech Commands",
        "model_name": "SpeechResNet18",
        "dataset_name": "Google Speech Commands",
        "total_parameters": 11172810,
        "parameter_count": 11172810,
        "m_formatted": "11.17M",
        "modality": "Audio (1x32x32 Log-Mel Spectrograms)",
        "input_shape": [1, 32, 32],
        "num_classes": 10,
        "paper_optimal_p_ratio": 0.112,
        "paper_optimal_p_percent": 11.2,
        "paper_optimal_p": 1251355,
        "topology": "ResNet-18 adapted for 1-channel Log-Mel Spectrograms (10 speech classes)",
        "paper_hyperparameters": {
            "learning_rate": 0.05,
            "batch_size": 64,
            "epochs": 1,
            "momentum": 0.9,
            "weight_decay": 0.0001,
        },
        "canonical_layers": [
            "conv1.weight", "bn1.weight", "bn1.bias",
            "layer1.0.conv1.weight", "layer1.0.bn1.weight", "layer1.0.bn1.bias",
            "layer1.0.conv2.weight", "layer1.0.bn2.weight", "layer1.0.bn2.bias",
            "layer1.1.conv1.weight", "layer1.1.bn1.weight", "layer1.1.bn1.bias",
            "layer1.1.conv2.weight", "layer1.1.bn2.weight", "layer1.1.bn2.bias",
            "layer2.0.conv1.weight", "layer2.0.bn1.weight", "layer2.0.bn1.bias",
            "layer2.0.conv2.weight", "layer2.0.bn2.weight", "layer2.0.bn2.bias",
            "layer2.0.downsample.0.weight", "layer2.0.downsample.1.weight", "layer2.0.downsample.1.bias",
            "layer2.1.conv1.weight", "layer2.1.bn1.weight", "layer2.1.bn1.bias",
            "layer2.1.conv2.weight", "layer2.1.bn2.weight", "layer2.1.bn2.bias",
            "layer3.0.conv1.weight", "layer3.0.bn1.weight", "layer3.0.bn1.bias",
            "layer3.0.conv2.weight", "layer3.0.bn2.weight", "layer3.0.bn2.bias",
            "layer3.0.downsample.0.weight", "layer3.0.downsample.1.weight", "layer3.0.downsample.1.bias",
            "layer3.1.conv1.weight", "layer3.1.bn1.weight", "layer3.1.bn1.bias",
            "layer3.1.conv2.weight", "layer3.1.bn2.weight", "layer3.1.bn2.bias",
            "layer4.0.conv1.weight", "layer4.0.bn1.weight", "layer4.0.bn1.bias",
            "layer4.0.conv2.weight", "layer4.0.bn2.weight", "layer4.0.bn2.bias",
            "layer4.0.downsample.0.weight", "layer4.0.downsample.1.weight", "layer4.0.downsample.1.bias",
            "layer4.1.conv1.weight", "layer4.1.bn1.weight", "layer4.1.bn1.bias",
            "layer4.1.conv2.weight", "layer4.1.bn2.weight", "layer4.1.bn2.bias",
            "fc.weight", "fc.bias",
        ],
        "checkpoint_file": "speech_resnet18_checkpoint.pt",
        "flat_artifact_file": "speech_flat_parameters.pt",
        "paper_section": "§5.1",
    },
    "20news": {
        "id": "20news",
        "name": "20 Newsgroups",
        "model_name": "NewsAlbert",
        "dataset_name": "20 Newsgroups",
        "total_parameters": 11698964,
        "parameter_count": 11698964,
        "m_formatted": "11.68M",
        "modality": "Text (Tokenized Sequences, 128 max length)",
        "input_shape": [128],
        "num_classes": 20,
        "paper_optimal_p_ratio": 0.128,
        "paper_optimal_p_percent": 12.8,
        "paper_optimal_p": 1497467,
        "topology": "ALBERT-base-v2 (12 Transformer Layers, 768 Hidden Dim, 20 news classes)",
        "paper_hyperparameters": {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 1,
            "momentum": 0.0,
            "weight_decay": 0.01,
        },
        "canonical_layers": [
            "albert.embeddings.word_embeddings.weight",
            "albert.embeddings.position_embeddings.weight",
            "albert.embeddings.token_type_embeddings.weight",
            "albert.embeddings.LayerNorm.weight",
            "albert.embeddings.LayerNorm.bias",
            "albert.encoder.embedding_hidden_mapping_in.weight",
            "albert.encoder.embedding_hidden_mapping_in.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.full_layer_layer_norm.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.full_layer_layer_norm.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.query.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.query.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.key.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.key.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.value.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.value.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.dense.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.dense.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.LayerNorm.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.attention.LayerNorm.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.ffn.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.ffn.bias",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.ffn_output.weight",
            "albert.encoder.albert_layer_groups.0.albert_layers.0.ffn_output.bias",
            "albert.pooler.weight",
            "albert.pooler.bias",
            "classifier.weight",
            "classifier.bias",
        ],
        "checkpoint_file": "albert_checkpoint.pt",
        "flat_artifact_file": "albert_flat_parameters.pt",
        "paper_section": "§5.1",
    },
}

BENCHMARK_FILE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "cifar10": {
        "round_file_re": r"^(?:cifar10_)?flat_round_(\d+)\.pt$",
        "canonical_flat": "cifar10_flat_parameters.pt",
        "checkpoint": "cifar10_cnn_checkpoint.pt",
        "importance_cache": "cifar10_importance_cache_beta09.pt",
        "energy_cache": "cifar10_energy_cache_beta09.pt",
        "pmin_cache": "cifar10_pmin_cache_beta09.pt",
        "model_cls": CIFAR10CNN,
        "model_name": "CIFAR10CNN",
        "dataset_name": "CIFAR-10",
        "canonical_layers": BENCHMARKS_CATALOG["cifar10"]["canonical_layers"],
    },
    "fmnist": {
        "round_file_re": r"^(?:fmnist_)?flat_round_(\d+)\.pt$",
        "canonical_flat": "fmnist_flat_parameters.pt",
        "checkpoint": "fmnist_cnn_checkpoint.pt",
        "importance_cache": "fmnist_importance_cache_beta09.pt",
        "energy_cache": "fmnist_energy_cache_beta09.pt",
        "pmin_cache": "fmnist_pmin_cache_beta09.pt",
        "model_cls": FMNISTCNN,
        "model_name": "FMNISTCNN",
        "dataset_name": "Fashion-MNIST",
        "canonical_layers": BENCHMARKS_CATALOG["fmnist"]["canonical_layers"],
    },
    "tiny_imagenet": {
        "round_file_re": r"^(?:tiny_imagenet_)?flat_round_(\d+)\.pt$",
        "canonical_flat": "tiny_imagenet_flat_parameters.pt",
        "checkpoint": "tiny_imagenet_resnet18.pt",
        "importance_cache": "tiny_imagenet_importance_cache_beta09.pt",
        "energy_cache": "tiny_imagenet_energy_cache_beta09.pt",
        "pmin_cache": "tiny_imagenet_pmin_cache_beta09.pt",
        "model_cls": TinyImageNetResNet18,
        "model_name": "TinyImageNetResNet18",
        "dataset_name": "Tiny-ImageNet",
        "canonical_layers": BENCHMARKS_CATALOG["tiny_imagenet"]["canonical_layers"],
    },
    "speech": {
        "round_file_re": r"^(?:speech_)?flat_round_(\d+)\.pt$",
        "canonical_flat": "speech_flat_parameters.pt",
        "checkpoint": "speech_resnet18.pt",
        "importance_cache": "speech_importance_cache_beta09.pt",
        "energy_cache": "speech_energy_cache_beta09.pt",
        "pmin_cache": "speech_pmin_cache_beta09.pt",
        "model_cls": SpeechResNet18,
        "model_name": "SpeechResNet18",
        "dataset_name": "Google Speech Commands",
        "canonical_layers": BENCHMARKS_CATALOG["speech"]["canonical_layers"],
    },
    "20news": {
        "round_file_re": r"^(?:20news_|albert_)?flat_round_(\d+)\.pt$",
        "canonical_flat": "albert_flat_parameters.pt",
        "checkpoint": "news_albert.pt",
        "importance_cache": "albert_importance_cache_beta09.pt",
        "energy_cache": "albert_energy_cache_beta09.pt",
        "pmin_cache": "albert_pmin_cache_beta09.pt",
        "model_cls": NewsAlbertForSequenceClassification,
        "model_name": "NewsAlbertForSequenceClassification",
        "dataset_name": "20 Newsgroups",
        "canonical_layers": BENCHMARKS_CATALOG["20news"]["canonical_layers"],
    },
}


def find_round_files_for_benchmark(rounds_dir: Path, benchmark: str) -> Tuple[List[Tuple[int, Path]], Path]:
    """Find round artifacts for a benchmark, searching benchmark subdirectory first, then base directory."""
    bench_key = benchmark.lower()
    meta = BENCHMARK_FILE_PATTERNS.get(bench_key, BENCHMARK_FILE_PATTERNS["cifar10"])
    pat = re.compile(meta["round_file_re"])

    sub_dir = rounds_dir / bench_key
    candidate_dirs = [sub_dir, rounds_dir] if sub_dir.exists() else [rounds_dir]

    for d in candidate_dirs:
        found: List[Tuple[int, Path]] = []
        if d.exists():
            for f in d.iterdir():
                m = pat.match(f.name)
                if m:
                    found.append((int(m.group(1)), f))
        if found:
            found.sort(key=lambda x: x[0])
            return found, d

    return [], sub_dir if sub_dir.exists() else rounds_dir


def find_cache_file(target_dir: Path, base_dir: Path, cache_name: str) -> Optional[Path]:
    """Find precomputed cache file checking target directory then base directory."""
    p1 = target_dir / cache_name
    if p1.exists():
        return p1
    p2 = base_dir / cache_name
    if p2.exists():
        return p2
    return None


_RAM_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_cached_file(path: Path) -> Any:
    """Load a torch checkpoint/cache artifact with high-performance RAM caching keyed by path and mtime."""
    key = str(path.resolve())
    mtime = path.stat().st_mtime
    cached_entry = _RAM_CACHE.get(key)
    if cached_entry is not None and cached_entry.get("mtime") == mtime:
        return cached_entry["data"]
    data = torch.load(path, weights_only=False)
    _RAM_CACHE[key] = {"mtime": mtime, "data": data}
    return data


def clear_ram_cache() -> None:
    """Explicitly clear the in-memory RAM cache."""
    _RAM_CACHE.clear()


class TopPRequest(BaseModel):
    n: int = Field(9, ge=3, le=60)
    M: int = Field(2000, ge=50, le=20000)
    theta: float = Field(0.8, gt=0, le=1)
    q: float = Field(0.8, ge=0.5, le=1)
    beta: float = Field(0.9, ge=0, lt=1)
    rounds: int = Field(3, ge=1, le=20)
    seed: int = 0
    p_max: int | None = None


class CnnTrainingRequest(BaseModel):
    benchmark: str = Field("cifar10", description="Benchmark identifier: cifar10, fmnist, tiny_imagenet, speech, 20news")
    rounds: int = Field(1, ge=1, le=200, description="Number of sequential training rounds")
    epochs: int = Field(5, ge=1, le=100, description="Local epochs per round")
    batch_size: int = Field(64, ge=8, le=512, description="Mini-batch size")
    learning_rate: float = Field(0.01, gt=0.0, le=1.0, description="Learning rate")
    momentum: float = Field(0.9, ge=0.0, le=0.99, description="SGD momentum")
    weight_decay: float = Field(1e-4, ge=0.0, le=0.1, description="Weight decay (L2 regularisation). Must be in [0.0, 0.1].")
    seed: int = Field(42, description="Random seed for reproducibility")
    synthetic: bool = Field(False, description="Use synthetic dataset for fast execution")
    synthetic_samples: int = Field(512, ge=16, le=5000, description="Synthetic samples count")
    distribution: str = Field("full", description="Data distribution: 'full' (10 classes IID) or 'pathological_20' (2 classes / 20% non-IID as in Paper §5.1)")

    @field_validator("benchmark")
    @classmethod
    def validate_benchmark(cls, v: str) -> str:
        v_clean = v.lower()
        if v_clean not in ("cifar10", "fmnist", "tiny_imagenet", "speech", "20news"):
            raise ValueError(f"Invalid benchmark '{v}'. Must be one of: 'cifar10', 'fmnist', 'tiny_imagenet', 'speech', '20news'.")
        return v_clean

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, v: str) -> str:
        if v not in ("full", "pathological_20"):
            raise ValueError(f"Invalid distribution '{v}'. Must be 'full' or 'pathological_20'.")
        return v

    @field_validator("weight_decay")
    @classmethod
    def weight_decay_in_range(cls, v: float) -> float:
        if v > 0.1:
            raise ValueError(
                f"weight_decay={v} is out of range. Must be ≤ 0.1 "
                "(Paper §5.1 uses 1e-4). Values above 0.1 cause over-regularisation."
            )
        return v


@router.get("/benchmarks")
def get_benchmarks() -> Dict[str, Any]:
    """Return catalog of all 5 Paper §5.1 benchmark models, datasets, and hyperparameters."""
    return {
        "benchmarks": BENCHMARKS_CATALOG,
        "count": len(BENCHMARKS_CATALOG),
        "default": "cifar10",
    }


@router.post("/run")
def run(req: TopPRequest):
    return run_demo(req.n, req.M, req.theta, req.q, req.beta, req.rounds, req.seed, req.p_max)


@router.post("/costs")
def calculate_costs(req: CostModelRequest):
    return compute_cost_model(req)


@router.post("/train-cnn")
def train_cnn(req: CnnTrainingRequest) -> Dict[str, Any]:
    """Train selected benchmark model and persist checkpoint + flattened parameter artifact bundle."""
    bench = req.benchmark.lower()

    if bench == "cifar10":
        config = CifarTrainingConfig(
            rounds=req.rounds,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            momentum=req.momentum,
            weight_decay=req.weight_decay,
            seed=req.seed,
            synthetic=req.synthetic,
            synthetic_samples=req.synthetic_samples,
            distribution=req.distribution,
            output_dir="output/models",
            checkpoint_dir="output/models/rounds",
        )
        model, result = train_cifar_model(config)
        flat_tensor, metadata = flatten_parameters(model)
        flat_path = Path("output/models/cifar10_flat_parameters.pt")
        save_flat_parameters_artifact(
            flat_tensor=flat_tensor,
            metadata=metadata,
            output_path=flat_path,
            source_checkpoint=result.checkpoint_path,
        )

    elif bench == "fmnist":
        config = FmnistTrainingConfig(
            rounds=req.rounds,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            momentum=req.momentum,
            weight_decay=req.weight_decay,
            seed=req.seed,
            synthetic=req.synthetic,
            synthetic_samples=req.synthetic_samples,
            distribution=req.distribution,
            output_dir="output/models",
            checkpoint_dir="output/models/rounds",
        )
        model, result = train_fmnist_model(config)
        flat_tensor, metadata = flatten_parameters(model)
        flat_path = Path("output/models/fmnist_flat_parameters.pt")
        save_flat_parameters_artifact(
            flat_tensor=flat_tensor,
            metadata=metadata,
            output_path=flat_path,
            source_checkpoint=result.checkpoint_path,
            model_name="FMNISTCNN",
        )

    elif bench == "tiny_imagenet":
        config = TinyTrainingConfig(
            rounds=req.rounds,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            momentum=req.momentum,
            weight_decay=req.weight_decay,
            seed=req.seed,
            synthetic=req.synthetic,
            synthetic_samples=req.synthetic_samples,
            device="cuda" if torch.cuda.is_available() else "cpu",
            output_dir="output/models",
            checkpoint_dir="output/models/rounds",
        )
        model, result = train_tiny_imagenet_model(config)
        flat_tensor, metadata = flatten_parameters(model)
        flat_path = Path("output/models/tiny_imagenet_flat_parameters.pt")
        save_flat_parameters_artifact(
            flat_tensor=flat_tensor,
            metadata=metadata,
            output_path=flat_path,
            source_checkpoint=result.checkpoint_path,
            model_name="TinyImageNetResNet18",
        )

    elif bench == "speech":
        config = SpeechTrainingConfig(
            rounds=req.rounds,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            momentum=req.momentum,
            weight_decay=req.weight_decay,
            seed=req.seed,
            synthetic=req.synthetic,
            synthetic_samples=req.synthetic_samples,
            device="cuda" if torch.cuda.is_available() else "cpu",
            output_dir="output/models",
            checkpoint_dir="output/models/rounds",
        )
        model, result = train_speech_model(config)
        flat_tensor, metadata = flatten_parameters(model)
        flat_path = Path("output/models/speech_flat_parameters.pt")
        save_flat_parameters_artifact(
            flat_tensor=flat_tensor,
            metadata=metadata,
            output_path=flat_path,
            source_checkpoint=result.checkpoint_path,
            model_name="SpeechResNet18",
        )

    elif bench == "20news":
        config = AlbertTrainingConfig(
            rounds=req.rounds,
            epochs=req.epochs,
            batch_size=min(req.batch_size, 32),
            learning_rate=req.learning_rate if req.learning_rate < 0.001 else 2e-5,
            weight_decay=req.weight_decay,
            seed=req.seed,
            synthetic=req.synthetic,
            synthetic_samples=min(req.synthetic_samples, 256),
            device="cuda" if torch.cuda.is_available() else "cpu",
            output_dir="output/models",
            checkpoint_dir="output/models/rounds",
        )
        result = train_albert_pipeline(config)

    # Mirror round artifacts to benchmark subdirectory for clean scoping
    sub_rounds_dir = Path("output/models/rounds") / bench
    sub_rounds_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(result, "round_history") and result.round_history:
        for rh in result.round_history:
            if "flat_parameters_path" in rh and Path(rh["flat_parameters_path"]).exists():
                src_p = Path(rh["flat_parameters_path"])
                dest_p = sub_rounds_dir / src_p.name
                if not dest_p.exists() or dest_p.stat().st_mtime < src_p.stat().st_mtime:
                    try:
                        shutil.copy2(src_p, dest_p)
                    except Exception:
                        pass

    # Automatically precompute downstream caches for instant UI responsiveness on real training
    if not req.synthetic:
        try:
            from backend.training.precompute_caches import precompute_caches_for_benchmark
            precompute_caches_for_benchmark(benchmark=bench, rounds_dir=Path("output/models/rounds"))
            clear_ram_cache()
        except Exception as cache_exc:
            logger.warning("Could not auto-generate precomputed caches for %s: %s", bench, cache_exc)

    return {
        "benchmark": bench,
        "final_train_loss": result.final_train_loss,
        "final_train_accuracy": result.final_train_accuracy,
        "final_test_loss": result.final_test_loss,
        "final_test_accuracy": result.final_test_accuracy,
        "duration_seconds": round(result.duration_seconds, 2),
        "round_history": result.round_history,
        "epoch_history": result.epoch_history,
        "checkpoint_path": result.checkpoint_path,
        "metadata_path": result.metadata_path,
        "distribution": req.distribution,
        "target_classes": getattr(result, "target_classes", None) or getattr(config, "target_classes", None),
    }


def _get_layer_for_index(idx: int, layer_slices: Dict[str, Any]) -> str:
    """Resolve the originating layer name for a given global flat index."""
    for layer_name, info in layer_slices.items():
        if info["start_idx"] <= idx < info["end_idx"]:
            return layer_name
    return "unknown"


@router.get("/cnn-weights")
def get_cnn_weights(
    benchmark: str = Query("cifar10", description="Benchmark model identifier"),
    head: int = Query(15, ge=1, le=500, description="Number of starting parameters to inspect"),
    tail: int = Query(15, ge=1, le=500, description="Number of ending parameters to inspect"),
    top_k: int = Query(20, ge=1, le=500, description="Number of highest absolute magnitude weights"),
    round_num: Optional[int] = Query(None, ge=1, description="Round number to inspect (defaults to latest available round)"),
) -> Dict[str, Any]:
    """Inspect true flattened weights from the selected benchmark model."""
    bench = benchmark.lower()
    meta = BENCHMARK_FILE_PATTERNS.get(bench, BENCHMARK_FILE_PATTERNS["cifar10"])
    rounds_dir = Path("output/models/rounds")
    round_files, target_dir = find_round_files_for_benchmark(rounds_dir, bench)
    available_rounds = [r[0] for r in round_files] if round_files else []

    selected_round: Optional[int] = None
    flat_tensor: Optional[torch.Tensor] = None
    metadata: Dict[str, Any] = {}

    if round_files:
        if round_num is not None:
            match = [f for r, f in round_files if r == round_num]
            if match:
                selected_round = round_num
                flat_tensor, metadata = load_flat_parameters_artifact(match[0])
            else:
                selected_round = round_files[-1][0]
                flat_tensor, metadata = load_flat_parameters_artifact(round_files[-1][1])
        else:
            selected_round = round_files[-1][0]
            flat_tensor, metadata = load_flat_parameters_artifact(round_files[-1][1])
    else:
        canonical_flat_name = meta["canonical_flat"]
        checkpoint_name = meta["checkpoint"]
        sub_flat_path = Path(f"output/models/rounds/{bench}/{canonical_flat_name}")
        flat_path = Path(f"output/models/{canonical_flat_name}")
        ckpt_path = Path(f"output/models/{checkpoint_name}")

        if sub_flat_path.exists():
            flat_tensor, metadata = load_flat_parameters_artifact(sub_flat_path)
        elif flat_path.exists():
            flat_tensor, metadata = load_flat_parameters_artifact(flat_path)
        elif ckpt_path.exists():
            model_cls = meta["model_cls"]
            if hasattr(model_cls, "load_checkpoint"):
                model, _ = model_cls.load_checkpoint(ckpt_path)
            else:
                model = model_cls()
                model.load_state_dict(torch.load(ckpt_path, weights_only=True))
            flat_tensor, metadata = flatten_parameters(model)
        else:
            model = meta["model_cls"]()
            flat_tensor, metadata = flatten_parameters(model)

    total_params = int(flat_tensor.numel())
    l2_norm = round(float(torch.linalg.norm(flat_tensor).item()), 4)
    layer_slices = metadata.get("layer_slices", {})

    # 1. Head items (first `head` parameters)
    head_count = min(head, total_params)
    head_items: List[Dict[str, Any]] = []
    for i in range(head_count):
        raw_val = float(flat_tensor[i].item())
        head_items.append({
            "index": i,
            "layer": _get_layer_for_index(i, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 2. Tail items (last `tail` parameters)
    tail_count = min(tail, total_params)
    tail_start = total_params - tail_count
    tail_items: List[Dict[str, Any]] = []
    for i in range(tail_count):
        idx = tail_start + i
        raw_val = float(flat_tensor[idx].item())
        tail_items.append({
            "index": idx,
            "layer": _get_layer_for_index(idx, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 3. Top-K magnitude items
    top_k_count = min(top_k, total_params)
    abs_tensor = torch.abs(flat_tensor)
    top_values, top_indices = torch.topk(abs_tensor, k=top_k_count)
    top_magnitude_items: List[Dict[str, Any]] = []
    for val_t, idx_t in zip(top_values, top_indices):
        idx = int(idx_t.item())
        raw_val = float(flat_tensor[idx].item())
        top_magnitude_items.append({
            "index": idx,
            "layer": _get_layer_for_index(idx, layer_slices),
            "value": round(raw_val, 6),
            "abs_value": round(abs(raw_val), 6),
        })

    # 4. Layer distribution summary
    canonical_layers = meta.get("canonical_layers", list(layer_slices.keys()))
    layer_summary: List[Dict[str, Any]] = []
    for layer_name in canonical_layers:
        if layer_name in layer_slices:
            info = layer_slices[layer_name]
            layer_summary.append({
                "layer": layer_name,
                "count": info["numel"],
                "start": info["start_idx"],
                "end": info["end_idx"],
                "shape": info["shape"],
                "percentage": round(100.0 * info["numel"] / total_params, 2),
            })

    head_layer = head_items[0]["layer"] if head_items else "Head"
    tail_layer = tail_items[-1]["layer"] if tail_items else "Tail"
    catalog_info = BENCHMARKS_CATALOG.get(bench, {})

    return {
        "benchmark": bench,
        "round_num": selected_round,
        "available_rounds": available_rounds,
        "is_latest_round": (selected_round == available_rounds[-1]) if (selected_round and available_rounds) else False,
        "total_parameters": total_params,
        "l2_norm": l2_norm,
        "head_layer": head_layer,
        "tail_layer": tail_layer,
        "model_name": meta["model_name"],
        "dataset_name": meta["dataset_name"],
        "num_classes": catalog_info.get("num_classes", 10),
        "modality": catalog_info.get("modality", ""),
        "slices": {
            "head": head_items,
            "tail": tail_items,
            "top_magnitude": top_magnitude_items,
        },
        "layer_distribution_summary": layer_summary,
        "checkpoint_info": {
            "model_name": meta["model_name"],
            "dataset": meta["dataset_name"],
            "benchmark": bench,
            "round_num": selected_round,
            "checkpoint_exists": True,
            "flat_artifact_exists": True,
        },
    }


@router.get("/round-importance")
def get_round_importance(
    benchmark: str = Query("cifar10", description="Benchmark model identifier"),
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor β ∈ [0, 0.99]"),
    top_k: int = Query(20, ge=5, le=500, description="Items per page (rank slice size)"),
    offset: int = Query(0, ge=0, description="Pagination offset — rank start (0-indexed)"),
    force_recompute: bool = Query(False, description="Bypass cache and force on-demand recalculation"),
) -> Dict[str, Any]:
    """Compute multi-round EMA importance scores and return side-by-side comparison data.

    For each saved round flat-parameter artifact the EMA chain is:
        s^(1) = |w^(1)|
        s^(t) = β · s^(t-1) + (1 - β) · |w^(t)|   for t > 1
    """
    import backend.top_p_router as _self_module
    rounds_dir: Path = _self_module.ROUNDS_DIR
    bench = benchmark.lower()

    # Discover round artifacts in ascending round order
    round_files, target_dir = find_round_files_for_benchmark(rounds_dir, bench)

    # Empty-state graceful response
    if not round_files:
        return {
            "has_data": False,
            "benchmark": bench,
            "total_rounds": 0,
            "beta": beta,
            "offset": offset,
            "top_k": top_k,
            "total_parameters": 0,
            "rounds": [],
            "rounds_data": [],
            "source": "dynamic_recomputed",
        }

    # Fast-Path: Pre-Computed Cache (beta = 0.9)
    if not force_recompute and abs(beta - 0.9) < 1e-6:
        meta = BENCHMARK_FILE_PATTERNS.get(bench, BENCHMARK_FILE_PATTERNS["cifar10"])
        cache_name = meta["importance_cache"]
        cache_path = find_cache_file(target_dir, rounds_dir, cache_name)
        if cache_path and cache_path.exists():
            try:
                cached_data = _load_cached_file(cache_path)
                cached_rounds = cached_data.get("rounds_data", cached_data.get("rounds", []))
                cached_top_k = cached_data.get("cached_top_k", len(cached_rounds[0]["items"]) if cached_rounds else 0)
                if (
                    cached_rounds
                    and len(cached_rounds) == len(round_files)
                    and (offset + top_k) <= cached_top_k
                ):
                    sliced_rounds = []
                    for rd in cached_rounds:
                        sliced_items = rd["items"][offset : offset + top_k]
                        sliced_rounds.append({"round": rd["round"], "items": sliced_items})
                    return {
                        "has_data": True,
                        "benchmark": bench,
                        "total_rounds": cached_data.get("total_rounds", len(round_files)),
                        "beta": 0.9,
                        "offset": offset,
                        "top_k": top_k,
                        "total_parameters": cached_data.get("total_parameters", 0),
                        "rounds": sliced_rounds,
                        "rounds_data": sliced_rounds,
                        "source": "cached_beta_0.9",
                    }
            except Exception:
                pass  # Fall back to dynamic calculation

    # Load all round tensors & metadata once
    round_tensors: List[torch.Tensor] = []
    all_layer_slices: Dict[str, Any] = {}
    for _, fpath in round_files:
        ft, meta = load_flat_parameters_artifact(fpath)
        round_tensors.append(ft.float())
        if not all_layer_slices:
            all_layer_slices = meta.get("layer_slices", {})

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

    # Rank each round: descending score, ties broken by ascending index (vectorized PyTorch ranking)
    round_ranks: List[torch.Tensor] = []
    round_inv_ranks: List[torch.Tensor] = []
    for st in ema_scores:
        sorted_indices = torch.argsort(-st, stable=True)
        round_ranks.append(sorted_indices)
        inv_ranks = torch.empty(total_params, dtype=torch.int32)
        inv_ranks[sorted_indices] = torch.arange(1, total_params + 1, dtype=torch.int32)
        round_inv_ranks.append(inv_ranks)

    # Build paginated per-round items
    rounds_data: List[Dict[str, Any]] = []
    for t_idx, (round_num, _) in enumerate(round_files):
        sorted_indices = round_ranks[t_idx]
        st = ema_scores[t_idx]
        wt = round_tensors[t_idx]

        page_start = min(offset, total_params)
        page_end = min(offset + top_k, total_params)
        page_indices = sorted_indices[page_start:page_end]

        items: List[Dict[str, Any]] = []
        for rank_pos, global_idx_t in enumerate(page_indices):
            global_idx = int(global_idx_t.item())
            rank = page_start + rank_pos + 1

            if t_idx == 0:
                rank_delta = None
            else:
                prev_rank = int(round_inv_ranks[t_idx - 1][global_idx].item())
                rank_delta = prev_rank - rank

            raw_val = float(wt[global_idx].item())
            score_val = float(st[global_idx].item())
            layer_name = _get_layer_for_index(global_idx, all_layer_slices)

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

    return {
        "has_data": True,
        "benchmark": bench,
        "total_rounds": len(round_files),
        "beta": beta,
        "offset": offset,
        "top_k": top_k,
        "total_parameters": total_params,
        "rounds": rounds_data,
        "rounds_data": rounds_data,
        "source": "dynamic_recomputed",
    }


@router.get("/energy-distribution")
def get_energy_distribution(
    benchmark: str = Query("cifar10", description="Benchmark model identifier"),
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor"),
    force_recompute: bool = Query(False, description="Force dynamic recalculation"),
) -> Dict[str, Any]:
    """Calculate or retrieve the cumulative energy distribution and prefix sums c_P across rounds."""
    import backend.top_p_router as _self_module
    rounds_dir: Path = _self_module.ROUNDS_DIR
    bench = benchmark.lower()

    round_files, target_dir = find_round_files_for_benchmark(rounds_dir, bench)

    if not round_files:
        return {
            "has_data": False,
            "benchmark": bench,
            "total_rounds": 0,
            "beta": beta,
            "total_parameters": 0,
            "rounds": [],
            "source": "dynamic_recomputed",
        }

    # Fast Path: Pre-Computed Cache (beta = 0.9)
    if not force_recompute and abs(beta - 0.9) < 1e-6:
        meta = BENCHMARK_FILE_PATTERNS.get(bench, BENCHMARK_FILE_PATTERNS["cifar10"])
        cache_name = meta["energy_cache"]
        cache_path = find_cache_file(target_dir, rounds_dir, cache_name)
        if cache_path and cache_path.exists():
            try:
                cached_data = _load_cached_file(cache_path)
                cached_rounds = cached_data.get("rounds", [])
                if cached_rounds and len(cached_rounds) == len(round_files):
                    return {
                        "has_data": True,
                        "benchmark": bench,
                        "total_rounds": cached_data.get("total_rounds", len(round_files)),
                        "beta": 0.9,
                        "total_parameters": cached_data.get("total_parameters", 0),
                        "rounds": cached_rounds,
                        "source": "cached_beta_0.9",
                    }
            except Exception:
                pass

    # Load all round tensors
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

    return {
        "has_data": True,
        "benchmark": bench,
        "total_rounds": len(round_files),
        "beta": beta,
        "total_parameters": total_params,
        "rounds": rounds_data,
        "source": "dynamic_recomputed",
    }


@router.get("/binary-search-pmin")
def get_binary_search_pmin(
    benchmark: str = Query("cifar10", description="Benchmark model identifier"),
    theta: float = Query(0.8, gt=0.0, le=1.0, description="Target cosine similarity threshold"),
    beta: float = Query(0.9, ge=0.0, le=0.99, description="EMA smoothing factor"),
    round_num: int = Query(1, ge=1, description="Round to inspect (defaults to 1 or latest)"),
    tolerance: int = Query(1, ge=1, description="Binary search termination tolerance eps_P"),
    force_recompute: bool = Query(False, description="Force dynamic recalculation"),
) -> Dict[str, Any]:
    """Execute Algorithm 1 (Appendix B / Page 29) binary search for minimal coordinate budget P_min."""
    import backend.top_p_router as _self_module
    rounds_dir: Path = _self_module.ROUNDS_DIR
    bench = benchmark.lower()

    round_files, target_dir = find_round_files_for_benchmark(rounds_dir, bench)

    fallback_file: Optional[Path] = None
    if not round_files:
        meta = BENCHMARK_FILE_PATTERNS.get(bench, BENCHMARK_FILE_PATTERNS["cifar10"])
        canonical_flat_name = meta["canonical_flat"]
        cands = [
            target_dir / canonical_flat_name,
            rounds_dir / canonical_flat_name,
        ]
        for c in cands:
            if c.exists():
                fallback_file = c
                break

        if fallback_file is None:
            return {
                "has_data": False,
                "benchmark": bench,
                "total_parameters": 0,
                "theta": theta,
                "beta": beta,
                "round_num": round_num,
                "p_min": 0,
                "achieved_cosine": 0.0,
                "sparsity_percentage": 0.0,
                "retained_percentage": 0.0,
                "nu_sq": 0.0,
                "nu": 0.0,
                "c_pmin": 0.0,
                "total_checks": 0,
                "trace": [],
                "available_rounds": [],
                "source": "empty",
            }

    # Select target round and chain EMA scores
    available_rounds = [r[0] for r in round_files] if round_files else [1]
    if round_files:
        effective_idx = min(len(round_files) - 1, max(0, round_num - 1))
        target_round = round_files[effective_idx][0]
    else:
        effective_idx = 0
        target_round = 1

    # Fast-Path: Pre-Computed P_min Cache (beta = 0.9, tolerance = 1)
    if not force_recompute and abs(beta - 0.9) < 1e-6 and tolerance == 1:
        meta = BENCHMARK_FILE_PATTERNS.get(bench, BENCHMARK_FILE_PATTERNS["cifar10"])
        cache_name = meta.get("pmin_cache")
        if cache_name:
            cache_path = find_cache_file(target_dir, rounds_dir, cache_name)
            if cache_path and cache_path.exists():
                try:
                    cached_data = _load_cached_file(cache_path)
                    rounds_dict = cached_data.get("rounds", {})
                    round_entry = rounds_dict.get(str(target_round), rounds_dict.get(target_round))
                    if round_entry:
                        theta_key = f"{theta:.2f}"
                        if theta_key in round_entry:
                            res = dict(round_entry[theta_key])
                            res["source"] = "cached_beta_0.9"
                            res["available_rounds"] = available_rounds

                            # Normalize trace items for consistent frontend compatibility
                            raw_trace = res.get("trace", [])
                            normalized_trace = []
                            for t in raw_trace:
                                lo_val = t.get("lo", t.get("low", 1))
                                hi_val = t.get("hi", t.get("high", 1))
                                mid_val = t.get("mid", (lo_val + hi_val) // 2)
                                cos_val = float(t.get("cos_mid", t.get("mid_cosine", t.get("cos", 0.0))))
                                is_feasible = bool(t.get("feasible", t.get("condition_met", cos_val >= theta)))
                                c_mid_val = t.get("c_mid", round(cos_val ** 2, 6))
                                act = t.get("action", "")
                                if not act or act in ("shrink_high", "expand_low"):
                                    act = (
                                        f"Feasible (cos={cos_val:.7f} ≥ {theta:.2f}): tighten upper bound hi = {mid_val}"
                                        if is_feasible
                                        else f"Below θ (cos={cos_val:.7f} < {theta:.2f}): advance lower bound lo = {mid_val + 1}"
                                    )
                                normalized_trace.append({
                                    "step": t.get("step", len(normalized_trace) + 1),
                                    "lo": lo_val,
                                    "hi": hi_val,
                                    "low": lo_val,
                                    "high": hi_val,
                                    "mid": mid_val,
                                    "c_mid": c_mid_val,
                                    "cos_mid": cos_val,
                                    "cos": cos_val,
                                    "mid_cosine": cos_val,
                                    "feasible": is_feasible,
                                    "condition_met": is_feasible,
                                    "action": act,
                                })
                            res["trace"] = normalized_trace
                            return res
                except Exception:
                    pass

    if round_files:
        ema_score: Optional[torch.Tensor] = None
        target_w: Optional[torch.Tensor] = None
        for i in range(effective_idx + 1):
            wt, _ = load_flat_parameters_artifact(round_files[i][1])
            wt = wt.float()
            abs_w = torch.abs(wt)
            if ema_score is None:
                ema_score = abs_w.clone()
            else:
                ema_score = beta * ema_score + (1.0 - beta) * abs_w
            if i == effective_idx:
                target_w = wt
    else:
        target_round = 1
        target_w, _ = load_flat_parameters_artifact(fallback_file)  # type: ignore[arg-type]
        target_w = target_w.float()
        ema_score = torch.abs(target_w)

    total_params = int(target_w.numel())
    if total_params == 0:
        return {
            "has_data": False,
            "benchmark": bench,
            "total_parameters": 0,
            "theta": theta,
            "beta": beta,
            "round_num": target_round,
            "p_min": 0,
            "achieved_cosine": 0.0,
            "sparsity_percentage": 0.0,
            "retained_percentage": 0.0,
            "nu_sq": 0.0,
            "nu": 0.0,
            "c_pmin": 0.0,
            "total_checks": 0,
            "trace": [],
            "available_rounds": available_rounds,
            "source": "empty",
        }

    # Sort coordinates descending by score s
    sorted_indices = torch.argsort(-ema_score, stable=True)
    w_sorted_sq = (target_w[sorted_indices]) ** 2
    c_prefix = torch.cumsum(w_sorted_sq, dim=0)
    nu_sq = float(c_prefix[-1].item())
    nu = math.sqrt(max(0.0, nu_sq))

    if nu_sq == 0.0:
        return {
            "has_data": True,
            "benchmark": bench,
            "total_parameters": total_params,
            "theta": theta,
            "beta": beta,
            "round_num": target_round,
            "p_min": 1,
            "achieved_cosine": 1.0,
            "sparsity_percentage": round((1.0 - 1.0 / total_params) * 100.0, 4),
            "retained_percentage": round((1.0 / total_params) * 100.0, 4),
            "nu_sq": 0.0,
            "nu": 0.0,
            "c_pmin": 0.0,
            "total_checks": 0,
            "trace": [],
            "available_rounds": available_rounds,
            "source": "dynamic_recomputed",
        }

    # Binary Search Loop (Algorithm 1)
    threshold_energy = (theta ** 2) * nu_sq - 1e-9
    lo = 1
    hi = total_params
    trace: List[Dict[str, Any]] = []
    step_num = 1

    while (hi - lo) >= tolerance:
        mid = (lo + hi) // 2
        c_mid = float(c_prefix[mid - 1].item())
        ok = (c_mid >= threshold_energy)
        cos_mid = math.sqrt(max(0.0, c_mid)) / max(1e-12, nu) if nu > 0 else 0.0
        cos_mid = min(1.0, cos_mid)

        if ok:
            action = f"Feasible (cos={cos_mid:.7f} ≥ {theta:.7f}): tighten upper bound hi = {mid}"
            trace.append({
                "step": step_num,
                "lo": lo,
                "hi": hi,
                "mid": mid,
                "c_mid": round(c_mid, 6),
                "cos_mid": round(cos_mid, 7),
                "cos": round(cos_mid, 7),
                "feasible": True,
                "action": action,
            })
            hi = mid
        else:
            action = f"Below θ (cos={cos_mid:.7f} < {theta:.7f}): advance lower bound lo = {mid + 1}"
            trace.append({
                "step": step_num,
                "lo": lo,
                "hi": hi,
                "mid": mid,
                "c_mid": round(c_mid, 6),
                "cos_mid": round(cos_mid, 7),
                "cos": round(cos_mid, 7),
                "feasible": False,
                "action": action,
            })
            lo = mid + 1
        step_num += 1

    p_min = hi
    c_pmin = float(c_prefix[p_min - 1].item())
    achieved_cosine = math.sqrt(max(0.0, c_pmin)) / max(1e-12, nu) if nu > 0 else 1.0
    achieved_cosine = min(1.0, achieved_cosine)

    sparsity_percentage = round((1.0 - (p_min / total_params)) * 100.0, 4)
    retained_percentage = round((p_min / total_params) * 100.0, 4)

    return {
        "has_data": True,
        "benchmark": bench,
        "total_parameters": total_params,
        "theta": theta,
        "beta": beta,
        "round_num": target_round,
        "p_min": p_min,
        "achieved_cosine": round(achieved_cosine, 7),
        "sparsity_percentage": sparsity_percentage,
        "retained_percentage": retained_percentage,
        "nu_sq": round(nu_sq, 6),
        "nu": round(nu, 6),
        "c_pmin": round(c_pmin, 6),
        "total_checks": len(trace),
        "trace": trace,
        "available_rounds": available_rounds,
        "source": "dynamic_recomputed",
    }
