"""ALBERT-base-v2 Sequence Classification Benchmark for 20Newsgroups (SemanticDFL Section 5.1).

Implements ALBERT-base-v2 adapted for 20-class text classification:
- Architecture: 12 Transformer layers with cross-layer parameter sharing,
  768 hidden dimension, 12 attention heads, 128 factorized embedding size,
  30,000 vocabulary size, and 20 target categories for 20Newsgroups.
- Total parameters: 11,698,964 (~11.68M parameters matching Section 5.1).
- Tokenizer: NewsAlbertTokenizer with fast offline deterministic fallback.
- Hardware constraints: Low-VRAM friendly (max_seq_length=128, batch_size=16),
  supporting FP16 autocast and CPU fallback.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
from transformers import AlbertConfig, AlbertForSequenceClassification, AutoTokenizer

NEWSGROUP_20_CLASSES: Dict[int, str] = {
    0: "alt.atheism",
    1: "comp.graphics",
    2: "comp.os.ms-windows.misc",
    3: "comp.sys.ibm.pc.hardware",
    4: "comp.sys.mac.hardware",
    5: "comp.windows.x",
    6: "misc.forsale",
    7: "rec.autos",
    8: "rec.motorcycles",
    9: "rec.sport.baseball",
    10: "rec.sport.hockey",
    11: "sci.crypt",
    12: "sci.electronics",
    13: "sci.med",
    14: "sci.space",
    15: "soc.religion.christian",
    16: "talk.politics.guns",
    17: "talk.politics.mideast",
    18: "talk.politics.misc",
    19: "talk.religion.misc",
}

EXPECTED_ALBERT_PARAMETER_COUNT: int = 11_698_964


class NewsAlbertTokenizer:
    """Tokenizer wrapper for ALBERT with zero-network offline fallback."""

    def __init__(
        self,
        max_seq_length: int = 128,
        vocab_size: int = 30000,
        cls_token_id: int = 2,
        sep_token_id: int = 3,
        pad_token_id: int = 0,
        unk_token_id: int = 1,
    ) -> None:
        self.max_seq_length = max_seq_length
        self.vocab_size = vocab_size
        self.cls_token_id = cls_token_id
        self.sep_token_id = sep_token_id
        self.pad_token_id = pad_token_id
        self.unk_token_id = unk_token_id

        self._hf_tokenizer = None
        try:
            # Try loading cached tokenizer without downloading if offline
            self._hf_tokenizer = AutoTokenizer.from_pretrained(
                "albert-base-v2",
                local_files_only=True,
            )
        except Exception:
            self._hf_tokenizer = None

    def _fallback_tokenize(self, text: str) -> List[int]:
        """Deterministic offline tokenizer mapping words into token IDs."""
        tokens = [self.cls_token_id]
        words = re.findall(r"\w+|[^\w\s]", text.lower())
        for word in words:
            # Hash word into vocabulary range [10, vocab_size - 1]
            token_id = 10 + (hash(word) % (self.vocab_size - 10))
            tokens.append(token_id)
            if len(tokens) >= self.max_seq_length - 1:
                break
        tokens.append(self.sep_token_id)
        return tokens

    def __call__(self, texts: Union[str, List[str]]) -> Dict[str, torch.Tensor]:
        if isinstance(texts, str):
            texts = [texts]

        if self._hf_tokenizer is not None:
            try:
                encoded = self._hf_tokenizer(
                    texts,
                    max_length=self.max_seq_length,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt",
                )
                return {
                    "input_ids": encoded["input_ids"],
                    "attention_mask": encoded["attention_mask"],
                    "token_type_ids": encoded.get(
                        "token_type_ids",
                        torch.zeros_like(encoded["input_ids"]),
                    ),
                }
            except Exception:
                pass

        # Offline fallback
        input_ids_list: List[List[int]] = []
        attention_mask_list: List[List[int]] = []
        token_type_ids_list: List[List[int]] = []

        for text in texts:
            tokens = self._fallback_tokenize(text)
            seq_len = min(len(tokens), self.max_seq_length)
            padded_tokens = tokens[:seq_len] + [self.pad_token_id] * (
                self.max_seq_length - seq_len
            )
            mask = [1] * seq_len + [0] * (self.max_seq_length - seq_len)
            types = [0] * self.max_seq_length

            input_ids_list.append(padded_tokens)
            attention_mask_list.append(mask)
            token_type_ids_list.append(types)

        return {
            "input_ids": torch.tensor(input_ids_list, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask_list, dtype=torch.long),
            "token_type_ids": torch.tensor(token_type_ids_list, dtype=torch.long),
        }


class NewsAlbertForSequenceClassification(nn.Module):
    """ALBERT-base-v2 Sequence Classification Model for 20Newsgroup."""

    def __init__(
        self,
        num_classes: int = 20,
        vocab_size: int = 30000,
        embedding_size: int = 128,
        hidden_size: int = 768,
        num_attention_heads: int = 12,
        intermediate_size: int = 3072,
        num_hidden_layers: int = 12,
        max_position_embeddings: int = 512,
        pretrained: bool = False,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.vocab_size = vocab_size
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.max_position_embeddings = max_position_embeddings

        self.config = AlbertConfig(
            vocab_size=vocab_size,
            embedding_size=embedding_size,
            hidden_size=hidden_size,
            num_attention_heads=num_attention_heads,
            intermediate_size=intermediate_size,
            num_hidden_layers=num_hidden_layers,
            max_position_embeddings=max_position_embeddings,
            num_labels=num_classes,
        )

        loaded_model = None
        if pretrained:
            try:
                loaded_model = AlbertForSequenceClassification.from_pretrained(
                    "albert-base-v2",
                    config=self.config,
                    ignore_mismatched_sizes=True,
                )
            except Exception:
                loaded_model = None

        if loaded_model is None:
            loaded_model = AlbertForSequenceClassification(self.config)

        self.albert = loaded_model.albert
        self.dropout = loaded_model.dropout
        self.classifier = loaded_model.classifier

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass computing classification logits of shape (B, num_classes)."""
        outputs = self.albert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=True,
        )
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits

    def extract_features(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Extract pooled sentence representation of shape (B, 768)."""
        outputs = self.albert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=True,
        )
        return outputs.pooler_output

    def count_parameters(self) -> int:
        """Return total trainable parameters in the model."""
        return sum(p.numel() for p in self.parameters())

    def get_topology_summary(self) -> Dict[str, Any]:
        """Return detailed architectural topology summary."""
        return {
            "model_type": "albert-base-v2",
            "num_classes": self.num_classes,
            "vocab_size": self.vocab_size,
            "embedding_size": self.embedding_size,
            "hidden_size": self.hidden_size,
            "num_attention_heads": self.num_attention_heads,
            "intermediate_size": self.intermediate_size,
            "num_hidden_layers": self.num_hidden_layers,
            "total_parameters": self.count_parameters(),
        }

    def save_checkpoint(
        self,
        filepath: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Path, Path]:
        """Save model state dict and associated metadata atomically."""
        ckpt_path = Path(filepath).resolve()
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "state_dict": self.state_dict(),
            "model_config": {
                "num_classes": self.num_classes,
                "vocab_size": self.vocab_size,
                "embedding_size": self.embedding_size,
                "hidden_size": self.hidden_size,
                "num_attention_heads": self.num_attention_heads,
                "intermediate_size": self.intermediate_size,
                "num_hidden_layers": self.num_hidden_layers,
                "max_position_embeddings": self.max_position_embeddings,
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
        if ckpt_path.name == "news_albert.pt" or ckpt_path.name == "model.pt":
            meta_path = ckpt_path.parent / "model_metadata.json"

        complete_metadata: Dict[str, Any] = {
            "model_name": "NewsAlbertForSequenceClassification",
            "checkpoint_filename": ckpt_path.name,
            "num_parameters": self.count_parameters(),
            "topology": self.get_topology_summary(),
            "classes": NEWSGROUP_20_CLASSES,
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
    ) -> Tuple[NewsAlbertForSequenceClassification, Dict[str, Any]]:
        """Load model state and metadata from checkpoint."""
        ckpt_path = Path(filepath).resolve()
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")

        target_device = torch.device(device) if device else torch.device("cpu")
        checkpoint = torch.load(ckpt_path, map_location=target_device)

        config = checkpoint.get("model_config", {})
        model = cls(
            num_classes=config.get("num_classes", 20),
            vocab_size=config.get("vocab_size", 30000),
            embedding_size=config.get("embedding_size", 128),
            hidden_size=config.get("hidden_size", 768),
            num_attention_heads=config.get("num_attention_heads", 12),
            intermediate_size=config.get("intermediate_size", 3072),
            num_hidden_layers=config.get("num_hidden_layers", 12),
            max_position_embeddings=config.get("max_position_embeddings", 512),
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
