"""20Newsgroup ALBERT-base-v2 Model Training and Evaluation Pipeline.

Implements isolated, modular dataset ingestion, tokenization, training,
evaluation, and deterministic artifact serialization for the SemanticDFL
20Newsgroups NLP benchmark (Section 5.1).

Paper Specifications:
- Model: ALBERT-base-v2 (~11.68M parameters, 12 layers, 768 hidden dimension, 12 heads).
- Task: 20-category text classification on 20Newsgroups.
- Single-client local training with paper hyperparameters:
  learning_rate = 2e-5 (AdamW), batch_size = 16, local_epochs = 1.
- Top-P signature extraction verifying Section 5.1:
  Pruning 87.2% of weights (P ≈ 12.8% of M) retains directional cos >= 0.80.
- Hardware constraints: Low-VRAM friendly (max_seq_length=128, batch_size=16),
  with mixed precision (FP16 autocast) and CPU fallback.
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
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset

from backend.models.news_albert import (
    NewsAlbertTokenizer,
    NewsAlbertForSequenceClassification,
    NEWSGROUP_20_CLASSES,
    EXPECTED_ALBERT_PARAMETER_COUNT,
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
logger = logging.getLogger("AlbertTrainer")


@dataclass
class TrainingConfig:
    """Hyperparameter configuration for 20Newsgroup ALBERT-base-v2 training."""

    rounds: int = 1
    epochs: int = 1  # Paper default: 1 local epoch per round
    batch_size: int = 16  # Paper default: 16
    learning_rate: float = 2e-5  # Paper default: 2e-5
    weight_decay: float = 0.01
    max_seq_length: int = 128  # Safe for low-VRAM (GTX 1050)
    seed: int = 42
    output_dir: str = "output/models"
    checkpoint_dir: str = "output/models/rounds"
    synthetic: bool = False
    synthetic_samples: int = 256
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    use_amp: bool = torch.cuda.is_available()
    checkpoint_name: str = "news_albert.pt"
    theta: float = 0.80  # Target cosine similarity


@dataclass
class TrainingResult:
    """Summary of training execution and metrics."""

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
    """Set deterministic random seeds across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class News20Dataset(Dataset):
    """Dataset for 20Newsgroups text classification with synthetic fallback."""

    def __init__(
        self,
        texts: Optional[List[str]] = None,
        labels: Optional[List[int]] = None,
        num_samples: int = 256,
        max_seq_length: int = 128,
        synthetic: bool = False,
        seed: int = 42,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.tokenizer = NewsAlbertTokenizer(max_seq_length=max_seq_length)
        self.data: List[Dict[str, torch.Tensor]] = []

        if synthetic or (texts is None and labels is None):
            self._generate_synthetic_data(num_samples=num_samples, seed=seed)
        else:
            assert texts is not None and labels is not None
            assert len(texts) == len(labels)
            for text, label in zip(texts, labels):
                tokens = self.tokenizer(text)
                self.data.append(
                    {
                        "input_ids": tokens["input_ids"].squeeze(0),
                        "attention_mask": tokens["attention_mask"].squeeze(0),
                        "token_type_ids": tokens["token_type_ids"].squeeze(0),
                        "label": torch.tensor(int(label), dtype=torch.long),
                    }
                )

    def _generate_synthetic_data(self, num_samples: int, seed: int = 42) -> None:
        rng = np.random.RandomState(seed)
        sample_topics = [
            "space exploration telemetry orbital satellite astrophysics cosmos rocket",
            "computer graphics rendering opengl shaders polygon texture raytracing",
            "cryptography encryption public key rsa aes cipher signatures security",
            "medicine health disease clinical trials pharmacology treatment biology",
            "motorcycle engine torque carburetor throttle suspension gear helmet",
            "baseball inning pitching batter home run umpire strikeout league",
            "hockey puck goaltender powerplay defense stick skate tournament",
            "politics legislature constitution congress vote election senate policy",
        ]
        for i in range(num_samples):
            topic = sample_topics[i % len(sample_topics)]
            text = f"News item {i}: {topic} and discussion of {topic.split()[0]}."
            label = int(rng.randint(0, 20))
            tokens = self.tokenizer(text)
            self.data.append(
                {
                    "input_ids": tokens["input_ids"].squeeze(0),
                    "attention_mask": tokens["attention_mask"].squeeze(0),
                    "token_type_ids": tokens["token_type_ids"].squeeze(0),
                    "label": torch.tensor(label, dtype=torch.long),
                }
            )

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return self.data[idx]


def get_dataloaders(config: TrainingConfig) -> Tuple[DataLoader, DataLoader]:
    """Prepare training and evaluation DataLoaders."""
    if config.synthetic:
        train_samples = config.synthetic_samples
        test_samples = max(16, config.synthetic_samples // 4)
        train_ds = News20Dataset(
            num_samples=train_samples,
            max_seq_length=config.max_seq_length,
            synthetic=True,
            seed=config.seed,
        )
        test_ds = News20Dataset(
            num_samples=test_samples,
            max_seq_length=config.max_seq_length,
            synthetic=True,
            seed=config.seed + 100,
        )
    else:
        try:
            from sklearn.datasets import fetch_20newsgroups

            train_raw = fetch_20newsgroups(subset="train", remove=("headers", "footers", "quotes"))
            test_raw = fetch_20newsgroups(subset="test", remove=("headers", "footers", "quotes"))
            train_ds = News20Dataset(
                texts=train_raw.data,
                labels=train_raw.target.tolist(),
                max_seq_length=config.max_seq_length,
            )
            test_ds = News20Dataset(
                texts=test_raw.data,
                labels=test_raw.target.tolist(),
                max_seq_length=config.max_seq_length,
            )
        except Exception as e:
            logger.warning("Could not fetch 20Newsgroups (%s); falling back to synthetic.", e)
            return get_dataloaders(
                TrainingConfig(
                    synthetic=True,
                    synthetic_samples=config.synthetic_samples,
                    max_seq_length=config.max_seq_length,
                    batch_size=config.batch_size,
                    seed=config.seed,
                )
            )

    train_loader = DataLoader(
        train_ds,
        batch_size=config.batch_size,
        shuffle=True,
        drop_last=False,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=config.batch_size,
        shuffle=False,
        drop_last=False,
    )
    return train_loader, test_loader


class EvalResult(dict):
    """Evaluation result dictionary supporting tuple unpacking `(loss, accuracy)`."""

    def __iter__(self) -> Iterator[float]:
        yield self["loss"]
        yield self["accuracy"]


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    lr: float = 2e-5,
    device: Union[str, torch.device] = "cpu",
    use_amp: bool = False,
    optimizer: Optional[torch.optim.Optimizer] = None,
) -> Dict[str, Any]:
    """Execute a single local training epoch (Section 5.1)."""
    target_device = torch.device(device)
    model.to(target_device)
    model.train()

    if optimizer is None:
        optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    criterion = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp and target_device.type == "cuda")

    running_loss = 0.0
    correct = 0
    total = 0

    for batch in dataloader:
        input_ids = batch["input_ids"].to(target_device)
        attention_mask = batch.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(target_device)
        labels = batch["label"].to(target_device)

        optimizer.zero_grad()

        if use_amp and target_device.type == "cuda":
            with torch.amp.autocast("cuda"):
                outputs = model(input_ids, attention_mask=attention_mask)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(input_ids, attention_mask=attention_mask)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        _, predicted = outputs.max(1)
        total += batch_size
        correct += predicted.eq(labels).sum().item()

    avg_loss = running_loss / max(1, total)
    acc = correct / max(1, total)
    return {
        "loss": avg_loss,
        "accuracy": acc,
        "samples_trained": total,
    }


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: Union[str, torch.device] = "cpu",
) -> EvalResult:
    """Evaluate model loss and classification accuracy on evaluation split."""
    target_device = torch.device(device)
    model.to(target_device)
    model.eval()

    criterion = nn.CrossEntropyLoss()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(target_device)
            attention_mask = batch.get("attention_mask")
            if attention_mask is not None:
                attention_mask = attention_mask.to(target_device)
            labels = batch["label"].to(target_device)

            outputs = model(input_ids, attention_mask=attention_mask)
            loss = criterion(outputs, labels)

            batch_size = labels.size(0)
            running_loss += loss.item() * batch_size
            _, predicted = outputs.max(1)
            total += batch_size
            correct += predicted.eq(labels).sum().item()

    avg_loss = running_loss / max(1, total)
    acc = correct / max(1, total)
    return EvalResult({
        "loss": avg_loss,
        "accuracy": acc,
        "samples_evaluated": total,
    })


def extract_top_p_signature(
    weights_or_model: Union[torch.Tensor, np.ndarray, nn.Module],
    theta: float = 0.80,
    p_ratio: Optional[float] = None,
    p_fixed: Optional[int] = None,
) -> Dict[str, Any]:
    """Extract Top-P signature adhering to Algorithm 1 and Section 5.1 of SemanticDFL.

    Paper specification for ALBERT-base-v2 (Section 5.1):
    Pruning 87.2% of weights (P ≈ 12.8% of M) retains cos >= 0.80 on flattened parameters.
    """
    if isinstance(weights_or_model, nn.Module):
        w_tensor, _ = flatten_parameters(weights_or_model)
    elif isinstance(weights_or_model, np.ndarray):
        w_tensor = torch.from_numpy(weights_or_model.reshape(-1)).float()
    else:
        w_tensor = weights_or_model.detach().cpu().float().view(-1)

    M = w_tensor.numel()
    if M == 0:
        return {
            "p_min": 0,
            "p_ratio": 0.0,
            "cosine_similarity": 1.0,
            "top_p_indices": [],
            "top_p_values": [],
            "payload_bytes": 0,
            "dense_bytes": 0,
            "total_parameters": 0,
        }

    l2_norm = torch.linalg.norm(w_tensor).item()
    if l2_norm == 0.0:
        return {
            "p_min": M,
            "p_ratio": 1.0,
            "cosine_similarity": 1.0,
            "top_p_indices": list(range(min(M, 1000))),
            "top_p_values": [0.0] * min(M, 1000),
            "payload_bytes": M * 6,
            "dense_bytes": M * 4,
            "total_parameters": M,
        }

    abs_sq = w_tensor.abs() ** 2

    # Determine P
    if p_fixed is not None:
        p_chosen = max(1, min(int(p_fixed), M))
    elif p_ratio is not None:
        p_chosen = max(1, min(int(round(p_ratio * M)), M))
    else:
        # Dynamic search for target theta
        sorted_sq, _ = torch.sort(abs_sq, descending=True)
        cumsum = torch.cumsum(sorted_sq, dim=0)
        target_energy = (theta**2) * (l2_norm**2)
        idx = torch.searchsorted(cumsum, torch.tensor(target_energy, dtype=cumsum.dtype))
        p_chosen = int(idx.item()) + 1
        p_chosen = max(1, min(p_chosen, M))

    # Top-K extraction
    topk_res = torch.topk(abs_sq, k=p_chosen, sorted=False)
    chosen_indices_tensor = topk_res.indices
    chosen_sq_sum = topk_res.values.sum().item()

    cos_sim = math.sqrt(max(0.0, chosen_sq_sum)) / l2_norm
    cos_sim = min(1.0, cos_sim)

    # Convert indices and values for payload representation
    indices_list = chosen_indices_tensor[:10000].tolist()
    values_list = w_tensor[chosen_indices_tensor[:10000]].tolist()

    payload_bytes = p_chosen * 6  # 4 bytes value + 2 bytes index
    dense_bytes = M * 4

    return {
        "p_min": p_chosen,
        "p_ratio": round(p_chosen / M, 6),
        "cosine_similarity": round(cos_sim, 6),
        "target_theta": theta,
        "top_p_indices": indices_list,
        "top_p_values": values_list,
        "payload_bytes": payload_bytes,
        "dense_bytes": dense_bytes,
        "compression_factor": round(dense_bytes / max(1, payload_bytes), 2),
        "total_parameters": M,
    }


def run_training_pipeline(config: TrainingConfig) -> TrainingResult:
    """Execute complete single-client training pipeline for ALBERT 20Newsgroups."""
    set_seed(config.seed)
    start_time = time.time()

    model = NewsAlbertForSequenceClassification(num_classes=20)
    train_loader, test_loader = get_dataloaders(config)

    epoch_history = []
    for epoch in range(1, config.epochs + 1):
        train_metrics = train_one_epoch(
            model=model,
            dataloader=train_loader,
            lr=config.learning_rate,
            device=config.device,
            use_amp=config.use_amp,
        )
        test_metrics = evaluate_model(
            model=model,
            dataloader=test_loader,
            device=config.device,
        )
        epoch_history.append({
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_accuracy": train_metrics["accuracy"],
            "test_loss": test_metrics["loss"],
            "test_accuracy": test_metrics["accuracy"],
        })
        logger.info(
            "Epoch %d: train_loss=%.4f, train_acc=%.2f%%, test_loss=%.4f, test_acc=%.2f%%",
            epoch,
            train_metrics["loss"],
            train_metrics["accuracy"] * 100,
            test_metrics["loss"],
            test_metrics["accuracy"] * 100,
        )

    # Save checkpoint
    out_dir = Path(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_dir / config.checkpoint_name
    model.save_checkpoint(ckpt_path)
    meta_path = out_dir / "model_metadata.json"

    # Save flattened parameter artifact
    flat_path = out_dir / "albert_parameters.bin"
    flat_tensor, flat_meta = flatten_parameters(model)
    save_flat_parameters_artifact(
        flat_tensor=flat_tensor,
        metadata=flat_meta,
        output_path=flat_path,
        model_name="NewsAlbertForSequenceClassification",
    )

    # Extract Top-P signature
    top_p_summary = extract_top_p_signature(flat_tensor, theta=config.theta)

    duration = time.time() - start_time
    return TrainingResult(
        final_train_loss=epoch_history[-1]["train_loss"] if epoch_history else 0.0,
        final_train_accuracy=epoch_history[-1]["train_accuracy"] if epoch_history else 0.0,
        final_test_loss=epoch_history[-1]["test_loss"] if epoch_history else 0.0,
        final_test_accuracy=epoch_history[-1]["test_accuracy"] if epoch_history else 0.0,
        epoch_history=epoch_history,
        checkpoint_path=str(ckpt_path),
        metadata_path=str(meta_path),
        flat_parameters_path=str(flat_path),
        duration_seconds=duration,
        top_p_summary=top_p_summary,
    )


def parse_args() -> TrainingConfig:
    """Parse command line arguments into TrainingConfig."""
    parser = argparse.ArgumentParser(description="Train 20Newsgroup ALBERT-base-v2 for SemanticDFL")
    parser.add_argument("--rounds", type=int, default=1, help="Number of training rounds")
    parser.add_argument("--epochs", type=int, default=1, help="Local epochs per round (paper: 1)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (paper default: 16)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate (paper default: 2e-5)")
    parser.add_argument("--weight-decay", type=float, default=0.01, help="Weight decay")
    parser.add_argument("--max-seq-length", type=int, default=128, help="Max sequence length (default: 128)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="output/models", help="Output directory")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic dataset for verification")
    parser.add_argument("--synthetic-samples", type=int, default=256, help="Number of synthetic samples")
    parser.add_argument("--theta", type=float, default=0.80, help="Target cosine similarity")

    args = parser.parse_args()
    return TrainingConfig(
        rounds=args.rounds,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        max_seq_length=args.max_seq_length,
        seed=args.seed,
        output_dir=args.output_dir,
        synthetic=args.synthetic,
        synthetic_samples=args.synthetic_samples,
        theta=args.theta,
    )


if __name__ == "__main__":
    cfg = parse_args()
    res = run_training_pipeline(cfg)
    print(f"Training completed in {res.duration_seconds:.2f}s.")
    print(f"Final Train Loss: {res.final_train_loss:.4f}, Train Acc: {res.final_train_accuracy*100:.2f}%")
    print(f"Final Test Loss: {res.final_test_loss:.4f}, Test Acc: {res.final_test_accuracy*100:.2f}%")
    if res.top_p_summary:
        print(f"Top-P Sparsity: {res.top_p_summary['p_ratio']*100:.2f}%, Cosine Sim: {res.top_p_summary['cosine_similarity']:.4f}")

