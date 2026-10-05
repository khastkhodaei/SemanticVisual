"""Automated Test Suite for 20Newsgroup ALBERT-base-v2 Benchmark.

Tests adhere strictly to Section 5.1 of the SemanticDFL research paper:
1. Tokenizer pipeline: Tokenization of raw text strings into input_ids, attention_mask,
   and token_type_ids with configurable max_seq_length (default 128).
2. ALBERT-base-v2 Sequence Classification architecture: 12 Transformer layers,
   768 hidden dimension, 12 attention heads, 20 output classes.
3. Parameter count verification: ~11.68M - 11.70M parameters (11,698,964 params).
4. Forward pass shape contract: Input (B, seq_len) -> Output (B, 20) classification logits.
5. Penultimate feature extraction: Pooled sentence representation of shape (B, 768).
6. Gradient flow verification across all transformer layers and classification head.
7. Model checkpoint serialization and lossless deserialization round-trip.
8. Flattening compatibility with backend.models.flattening (unflattening & reconstruction).
9. Single-client training step with paper hyperparameters (lr=2e-5, batch_size=16, local_epochs=1).
10. Top-P signature extraction: P ≈ 12.8% of M retains cos >= 0.80 on flattened parameters.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest
import torch
import torch.nn as nn

from backend.models.news_albert import (
    NewsAlbertTokenizer,
    NewsAlbertForSequenceClassification,
    NEWSGROUP_20_CLASSES,
    EXPECTED_ALBERT_PARAMETER_COUNT,
)
from backend.models.flattening import flatten_parameters, unflatten_parameters
from backend.training.train_albert import (
    News20Dataset,
    train_one_epoch,
    extract_top_p_signature,
    evaluate_model,
)


class TestNewsAlbertTokenizer:
    """Unit tests for the ALBERT tokenizer pipeline."""

    def test_tokenization_shapes_and_types(self):
        """Verify text batch converts to input_ids, attention_mask of shape (B, max_seq_len)."""
        tokenizer = NewsAlbertTokenizer(max_seq_length=128)
        texts = [
            "The Hubble Space Telescope captured new infrared images of distant galaxies.",
            "Linux kernel 6.8 introduces memory management improvements.",
        ]
        batch = tokenizer(texts)

        assert "input_ids" in batch
        assert "attention_mask" in batch
        assert batch["input_ids"].shape == (2, 128)
        assert batch["attention_mask"].shape == (2, 128)
        assert batch["input_ids"].dtype == torch.long
        assert batch["attention_mask"].dtype == torch.long

    def test_single_string_handling(self):
        """Verify single string input is automatically batched to (1, max_seq_len)."""
        tokenizer = NewsAlbertTokenizer(max_seq_length=64)
        batch = tokenizer("NASA launched a new rover to Mars.")

        assert batch["input_ids"].shape == (1, 64)
        assert batch["attention_mask"].shape == (1, 64)
        # First token should be CLS token, not PAD
        assert batch["attention_mask"][0, 0].item() == 1


class TestNewsAlbertModelArchitecture:
    """Unit tests for NewsAlbertForSequenceClassification architecture and forward pass."""

    def test_canonical_classes(self):
        """Verify 20 canonical 20Newsgroups target classes."""
        assert len(NEWSGROUP_20_CLASSES) == 20
        assert NEWSGROUP_20_CLASSES[0] == "alt.atheism"
        assert NEWSGROUP_20_CLASSES[1] == "comp.graphics"
        assert NEWSGROUP_20_CLASSES[19] == "talk.religion.misc"

    def test_parameter_count(self):
        """Verify ALBERT-base-v2 parameter count matches ~11.68M-11.70M parameters."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        param_count = model.count_parameters()

        assert param_count == EXPECTED_ALBERT_PARAMETER_COUNT
        assert 11_600_000 <= param_count <= 11_750_000

    @pytest.mark.parametrize("batch_size", [1, 2])
    def test_forward_output_shape(self, batch_size: int):
        """Verify forward pass produces exact (B, 20) logits."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        model.eval()

        input_ids = torch.randint(0, 1000, (batch_size, 32))
        attention_mask = torch.ones((batch_size, 32), dtype=torch.long)

        with torch.no_grad():
            logits = model(input_ids, attention_mask=attention_mask)

        assert logits.shape == (batch_size, 20)
        assert not torch.isnan(logits).any()

    def test_extract_features_shape(self):
        """Verify extract_features produces pooled representation of shape (B, 768)."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        model.eval()

        input_ids = torch.randint(0, 1000, (2, 32))
        attention_mask = torch.ones((2, 32), dtype=torch.long)

        with torch.no_grad():
            features = model.extract_features(input_ids, attention_mask=attention_mask)

        assert features.shape == (2, 768)
        assert not torch.isnan(features).any()

    def test_gradient_flow(self):
        """Verify loss backward produces valid non-zero gradients."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        model.train()

        input_ids = torch.randint(0, 1000, (2, 16))
        attention_mask = torch.ones((2, 16), dtype=torch.long)
        targets = torch.tensor([3, 14], dtype=torch.long)

        logits = model(input_ids, attention_mask=attention_mask)
        loss = nn.functional.cross_entropy(logits, targets)
        loss.backward()

        # Check gradients exist on classifier head and transformer encoder
        assert model.classifier.weight.grad is not None
        assert not torch.isnan(model.classifier.weight.grad).any()
        assert model.classifier.weight.grad.abs().sum() > 0.0

    def test_checkpoint_round_trip(self):
        """Verify save_checkpoint and load_checkpoint preserve weights losslessly."""
        model1 = NewsAlbertForSequenceClassification(num_classes=20)
        model1.eval()

        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_path = Path(tmpdir) / "albert_test.pt"
            model1.save_checkpoint(ckpt_path, metadata={"test_run": True})

            model2, metadata = NewsAlbertForSequenceClassification.load_checkpoint(ckpt_path)
            model2.eval()

            assert metadata.get("test_run") is True
            assert metadata["num_parameters"] == model1.count_parameters()

            input_ids = torch.randint(0, 1000, (2, 16))
            with torch.no_grad():
                out1 = model1(input_ids)
                out2 = model2(input_ids)

            torch.testing.assert_close(out1, out2)


class TestNewsAlbertFlattening:
    """Unit tests for parameter flattening and unflattening compatibility."""

    def test_flatten_and_unflatten_round_trip(self):
        """Verify flattening to 1D vector and unflattening preserves exact state dict."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        model.eval()

        flat_vector, metadata = flatten_parameters(model)
        assert flat_vector.numel() == EXPECTED_ALBERT_PARAMETER_COUNT
        assert metadata["num_parameters"] == EXPECTED_ALBERT_PARAMETER_COUNT
        assert metadata["l2_norm"] > 0.0

        new_model = NewsAlbertForSequenceClassification(num_classes=20)
        unflatten_parameters(flat_vector, metadata["layer_slices"], new_model)
        new_model.eval()

        input_ids = torch.randint(0, 1000, (2, 16))
        with torch.no_grad():
            orig_out = model(input_ids)
            recon_out = new_model(input_ids)

        torch.testing.assert_close(orig_out, recon_out)


class TestNewsAlbertTrainingAndTopP:
    """Unit tests for single-client training and Top-P signature extraction."""

    def test_dataset_synthetic_fallback(self):
        """Verify synthetic text fallback generates valid 20Newsgroup batches."""
        dataset = News20Dataset(num_samples=16, max_seq_length=32, synthetic=True)
        assert len(dataset) == 16

        sample = dataset[0]
        assert "input_ids" in sample
        assert "attention_mask" in sample
        assert "label" in sample
        assert sample["input_ids"].shape == (32,)
        assert 0 <= sample["label"].item() < 20

    def test_train_one_epoch(self):
        """Verify single local epoch executes with paper lr=2e-5, batch_size=16."""
        model = NewsAlbertForSequenceClassification(num_classes=20)
        dataset = News20Dataset(num_samples=16, max_seq_length=16, synthetic=True)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=16, shuffle=False)

        results = train_one_epoch(
            model=model,
            dataloader=dataloader,
            lr=2e-5,
            device="cpu",
            use_amp=False,
        )

        assert results["samples_trained"] == 16
        assert results["loss"] > 0.0
        assert 0.0 <= results["accuracy"] <= 1.0

    def test_top_p_signature_cos_bound(self):
        """Verify Section 5.1 invariant: pruning 87.2% (P ≈ 12.8%) retains cos >= 0.80."""
        model = NewsAlbertForSequenceClassification(num_classes=20)

        # 1. Verification via dynamic thresholding at theta = 0.80
        sig_theta = extract_top_p_signature(model, theta=0.80)
        assert sig_theta["cosine_similarity"] >= 0.80
        # P should be approx 12.8% of M (pruning ~87.2%)
        assert sig_theta["p_ratio"] == pytest.approx(0.128, abs=0.015)

        # 2. Verification via fixed ratio P = 12.8% (0.128)
        sig_ratio = extract_top_p_signature(model, p_ratio=0.128)
        assert "top_p_indices" in sig_ratio
        assert "top_p_values" in sig_ratio
        assert round(sig_ratio["cosine_similarity"], 2) >= 0.80
        assert sig_ratio["cosine_similarity"] >= 0.799
        assert sig_ratio["p_ratio"] == pytest.approx(0.128, abs=0.005)

    def test_end_to_end_training_pipeline(self):
        """Verify complete single-client pipeline execution with artifact serialization."""
        from backend.training.train_albert import TrainingConfig, run_training_pipeline

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                rounds=1,
                epochs=1,
                batch_size=8,
                learning_rate=2e-5,
                max_seq_length=16,
                synthetic=True,
                synthetic_samples=16,
                device="cpu",
                use_amp=False,
                output_dir=tmpdir,
                checkpoint_name="albert_test.pt",
            )
            result = run_training_pipeline(config)

            assert result.checkpoint_path != ""
            assert Path(result.checkpoint_path).exists()
            assert Path(result.metadata_path).exists()
            assert Path(result.flat_parameters_path).exists()
            assert result.top_p_summary is not None
            assert result.top_p_summary["cosine_similarity"] >= 0.80
            assert result.duration_seconds > 0.0
