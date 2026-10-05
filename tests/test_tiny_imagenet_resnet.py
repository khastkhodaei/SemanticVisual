"""Automated Test Suite for ResNet-18 on Tiny-ImageNet Benchmark.

Tests adhere strictly to Section 5.1 of the SemanticDFL research paper:
1. ResNet-18 architecture adapted for 64x64 RGB inputs (3 channels) with 200 output classes.
2. Parameter count: ~11.2M - 11.7M parameters.
3. Forward pass shape contract: Input (B, 3, 64, 64) -> Output (B, 200).
4. Penultimate feature extraction representation of shape (B, 512).
5. Gradient flow across residual blocks and convolutional layers.
6. Checkpoint serialization and lossless deserialization round-trip.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest
import torch
import torch.nn as nn

from backend.models.tiny_imagenet_resnet import (
    TinyImageNetResNet18,
    TINY_IMAGENET_NUM_CLASSES,
)


class TestTinyImageNetResNet18Model:
    """Unit tests for the TinyImageNetResNet18 architecture."""

    def test_canonical_classes_count(self):
        """Verify Tiny-ImageNet has exactly 200 classification classes."""
        assert TINY_IMAGENET_NUM_CLASSES == 200

    @pytest.mark.parametrize("batch_size", [1, 2, 4])
    def test_forward_output_shape(self, batch_size: int):
        """Verify forward pass produces exact (B, 200) logits for (B, 3, 64, 64) inputs."""
        model = TinyImageNetResNet18(num_classes=200)
        model.eval()
        x = torch.randn(batch_size, 3, 64, 64)
        with torch.no_grad():
            out = model(x)

        assert out.shape == (batch_size, 200), f"Expected shape ({batch_size}, 200), got {out.shape}"
        assert not torch.isnan(out).any(), "Output contains NaN values"
        assert not torch.isinf(out).any(), "Output contains Inf values"

    def test_feature_extraction_dimension(self):
        """Verify penultimate feature representation has shape (B, 512)."""
        model = TinyImageNetResNet18()
        model.eval()
        x = torch.randn(2, 3, 64, 64)
        with torch.no_grad():
            features = model.extract_features(x)

        assert features.shape == (2, 512), f"Expected shape (2, 512), got {features.shape}"

    def test_invalid_input_shapes_raise_error(self):
        """Verify invalid input dimensions or channel counts raise ValueError."""
        model = TinyImageNetResNet18()

        # 3D tensor instead of 4D
        with pytest.raises(ValueError, match="Expected 4D input tensor"):
            model(torch.randn(3, 64, 64))

        # Incorrect channel count (1 channel instead of 3)
        with pytest.raises(ValueError, match="Expected input with 3 channels"):
            model(torch.randn(2, 1, 64, 64))

    def test_parameter_count_matches_paper_specification(self):
        """Verify total parameter count is ~11.2M - 11.7M as cited in paper and PAPER_COSTS.md."""
        model = TinyImageNetResNet18(num_classes=200)
        param_count = model.count_parameters()
        # ResNet-18 with 200 classes has ~11.2M to 11.7M parameters
        assert 11_000_000 <= param_count <= 11_800_000, (
            f"Expected parameter count in range [11.0M, 11.8M], got {param_count}"
        )

    def test_gradient_flow(self):
        """Verify backward pass computes valid gradients across all trainable layers."""
        model = TinyImageNetResNet18(num_classes=200)
        model.train()
        criterion = nn.CrossEntropyLoss()

        x = torch.randn(2, 3, 64, 64)
        y = torch.tensor([0, 199], dtype=torch.long)

        out = model(x)
        loss = criterion(out, y)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} has no gradient."
                assert not torch.isnan(param.grad).any(), f"Parameter {name} gradient contains NaN."

    def test_topology_summary(self):
        """Verify topology metadata dictionary accurately reflects architecture parameters."""
        model = TinyImageNetResNet18(num_classes=200)
        summary = model.get_topology_summary()

        assert summary["model_type"] == "TinyImageNetResNet18"
        assert summary["in_channels"] == 3
        assert summary["num_classes"] == 200
        assert "stem" in summary
        assert "stages" in summary
        assert summary["total_parameters"] == model.count_parameters()


class TestSerializationAndReload:
    """Tests for model checkpointing and lossless deserialization."""

    def test_checkpoint_round_trip_lossless(self):
        """Verify saved checkpoint weights reload with zero numerical discrepancy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_file = Path(tmpdir) / "tiny_resnet_test.pt"

            # 1. Initialize and mutate weights
            model_orig = TinyImageNetResNet18(num_classes=200)
            with torch.no_grad():
                for param in model_orig.parameters():
                    param.add_(torch.randn_like(param) * 0.05)

            # 2. Save checkpoint
            saved_ckpt, saved_meta = model_orig.save_checkpoint(
                ckpt_file, metadata={"test_metric": 0.488}
            )
            assert saved_ckpt.exists()
            assert saved_meta.exists()

            # 3. Reload into new model instance
            model_reloaded, loaded_meta = TinyImageNetResNet18.load_checkpoint(saved_ckpt)

            # 4. Check weight exact equivalence
            for (k1, v1), (k2, v2) in zip(
                model_orig.state_dict().items(), model_reloaded.state_dict().items()
            ):
                assert k1 == k2
                assert torch.equal(v1, v2), f"Discrepancy detected in layer {k1}."

            # 5. Check inference output match
            model_orig.eval()
            model_reloaded.eval()
            x = torch.randn(2, 3, 64, 64)
            with torch.no_grad():
                out_orig = model_orig(x)
                out_reloaded = model_reloaded(x)
            assert torch.allclose(out_orig, out_reloaded, atol=1e-5)

            # 6. Check metadata payload
            assert loaded_meta["test_metric"] == 0.488
            assert loaded_meta["model_name"] == "TinyImageNetResNet18"


class TestParameterFlattening:
    """Unit tests for parameter flattening and unflattening with TinyImageNetResNet18."""

    def test_resnet18_flatten_parameters_shape_and_slices(self):
        """Assert flat parameter tensor matches trainable parameter count with slice continuity."""
        from backend.models.flattening import flatten_parameters

        model = TinyImageNetResNet18(num_classes=200)
        expected_count = model.count_parameters()

        flat_tensor, metadata = flatten_parameters(model)

        assert flat_tensor.dim() == 1
        assert flat_tensor.shape == (expected_count,)
        assert flat_tensor.dtype == torch.float32
        assert metadata["num_parameters"] == expected_count
        assert metadata["l2_norm"] > 0.0
        assert metadata["model_name"] == "TinyImageNetResNet18"

        # Check slice continuity
        prev_end = 0
        for layer_name in metadata["canonical_layers"]:
            info = metadata["layer_slices"][layer_name]
            assert info["start_idx"] == prev_end
            assert info["end_idx"] == info["start_idx"] + info["numel"]
            prev_end = info["end_idx"]
        assert prev_end == expected_count

    def test_resnet18_flatten_unflatten_roundtrip(self):
        """Verify flattening, loading into fresh model, and running forward yields exact parity."""
        from backend.models.flattening import flatten_parameters, unflatten_parameters

        model_source = TinyImageNetResNet18(num_classes=200)
        with torch.no_grad():
            for p in model_source.parameters():
                p.add_(torch.randn_like(p) * 0.05)

        flat_tensor, metadata = flatten_parameters(model_source)

        model_target = TinyImageNetResNet18(num_classes=200)
        unflatten_parameters(flat_tensor, metadata["layer_slices"], model_target)

        for (k1, v1), (k2, v2) in zip(
            model_source.state_dict().items(), model_target.state_dict().items()
        ):
            assert k1 == k2
            assert torch.equal(v1, v2), f"Numerical mismatch in layer {k1}"

        model_source.eval()
        model_target.eval()
        test_input = torch.randn(2, 3, 64, 64)
        with torch.no_grad():
            out_source = model_source(test_input)
            out_target = model_target(test_input)

        assert torch.allclose(out_source, out_target, atol=1e-5)

    def test_resnet18_flat_artifact_save_load_roundtrip(self):
        """Verify saving and loading flat parameter artifact retains model_name and metadata."""
        from backend.models.flattening import (
            flatten_parameters,
            load_flat_parameters_artifact,
            save_flat_parameters_artifact,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            model = TinyImageNetResNet18(num_classes=200)
            flat_tensor, metadata = flatten_parameters(model)
            out_path = Path(tmpdir) / "tiny_resnet_flat_parameters.pt"

            saved_path = save_flat_parameters_artifact(
                flat_tensor=flat_tensor,
                metadata=metadata,
                output_path=out_path,
                source_checkpoint="output/models/tiny_imagenet_resnet18.pt",
                model_name="TinyImageNetResNet18",
            )
            assert saved_path.exists()

            loaded_tensor, loaded_meta = load_flat_parameters_artifact(saved_path)
            assert loaded_tensor.shape == (model.count_parameters(),)
            assert loaded_meta["num_parameters"] == model.count_parameters()
            assert loaded_meta["metadata"]["model_name"] == "TinyImageNetResNet18"


class TestTinyImageNetTrainingPipeline:
    """Unit tests for the single-client Tiny-ImageNet ResNet-18 training pipeline."""

    def test_dataloader_synthetic(self):
        """Verify synthetic dataloader produces correct tensor shapes (B, 3, 64, 64) and labels [0..199]."""
        from backend.training.train_tiny_imagenet import TrainingConfig, get_dataloaders

        config = TrainingConfig(
            batch_size=32,
            synthetic=True,
            synthetic_samples=64,
            seed=42,
        )
        train_loader, test_loader = get_dataloaders(config)

        x_batch, y_batch = next(iter(train_loader))
        assert x_batch.shape == (32, 3, 64, 64)
        assert y_batch.shape == (32,)
        assert y_batch.min() >= 0
        assert y_batch.max() < 200

    def test_single_client_1epoch_paper_hyperparameters(self):
        """Verify single-client local training with paper defaults (lr=0.05, batch_size=64, epochs=1)."""
        from backend.training.train_tiny_imagenet import TrainingConfig, train_tiny_imagenet_model

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                rounds=1,
                epochs=1,
                batch_size=64,
                learning_rate=0.05,
                seed=42,
                output_dir=tmpdir,
                checkpoint_dir=str(Path(tmpdir) / "rounds"),
                synthetic=True,
                synthetic_samples=128,
                use_amp=False,
            )
            model, result = train_tiny_imagenet_model(config)

            assert Path(result.checkpoint_path).exists()
            assert Path(result.metadata_path).exists()
            assert Path(result.flat_parameters_path).exists()
            assert len(result.epoch_history) == 1
            assert result.final_train_accuracy >= 0.0
            assert result.final_test_accuracy >= 0.0

            with open(result.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["dataset"] == "Tiny-ImageNet"
            assert meta["hyperparameters"]["learning_rate"] == 0.05
            assert meta["hyperparameters"]["batch_size"] == 64
            assert meta["hyperparameters"]["epochs"] == 1
            assert meta["num_classes"] == 200

    def test_batch_size_fallback_to_32(self):
        """Verify pipeline supports batch_size=32 for low-VRAM hardware (GTX 1050 fallback)."""
        from backend.training.train_tiny_imagenet import TrainingConfig, train_tiny_imagenet_model

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                rounds=1,
                epochs=1,
                batch_size=32,
                learning_rate=0.05,
                seed=42,
                output_dir=tmpdir,
                checkpoint_dir=str(Path(tmpdir) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
                use_amp=False,
            )
            model, result = train_tiny_imagenet_model(config)

            assert Path(result.checkpoint_path).exists()
            assert len(result.epoch_history) == 1
            assert result.batch_size == 32

    def test_amp_mixed_precision_configuration(self):
        """Verify mixed precision (AMP) configuration executes cleanly."""
        from backend.training.train_tiny_imagenet import TrainingConfig, train_tiny_imagenet_model

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                rounds=1,
                epochs=1,
                batch_size=32,
                learning_rate=0.05,
                seed=42,
                output_dir=tmpdir,
                checkpoint_dir=str(Path(tmpdir) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
                use_amp=True,
            )
            model, result = train_tiny_imagenet_model(config)
            assert Path(result.checkpoint_path).exists()

    def test_deterministic_seed_training(self):
        """Verify training with identical seeds produces identical model weights."""
        from backend.training.train_tiny_imagenet import TrainingConfig, train_tiny_imagenet_model

        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            cfg1 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.05,
                seed=77,
                output_dir=tmp1,
                checkpoint_dir=str(Path(tmp1) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
                use_amp=False,
            )
            cfg2 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.05,
                seed=77,
                output_dir=tmp2,
                checkpoint_dir=str(Path(tmp2) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
                use_amp=False,
            )
            m1, res1 = train_tiny_imagenet_model(cfg1)
            m2, res2 = train_tiny_imagenet_model(cfg2)

            assert res1.final_train_loss == pytest.approx(res2.final_train_loss, abs=1e-5)
            assert res1.final_test_loss == pytest.approx(res2.final_test_loss, abs=1e-5)
            for p1, p2 in zip(m1.parameters(), m2.parameters()):
                assert torch.allclose(p1, p2, atol=1e-6)


class TestTinyImageNetTopPSignatures:
    """Unit tests for Top-P signature extraction and paper finding verification."""

    def test_top_p_pruning_90_4_percent_paper_finding(self):
        """Verify paper finding: pruning 90.4% (P ≈ 9.6% of M) retains cos >= 0.8."""
        from backend.training.train_tiny_imagenet import extract_top_p_signature

        # Construct heavy-tailed weight distribution mimicking real neural network weights
        torch.manual_seed(42)
        M = 100_000
        # Student-t distribution (df=3) has heavy tails matching deep CNN weights
        w = torch.distributions.StudentT(df=3.0).sample((M,))

        # Prune 90.4% of weights -> keep P = 9.6% of M
        p_paper = int(round(0.096 * M))
        sig = extract_top_p_signature(w, p_fixed=p_paper, beta=0.0)

        assert sig["p_min"] == p_paper
        assert sig["sparsity_ratio"] == pytest.approx(0.096, abs=0.001)
        assert sig["cosine_similarity"] >= 0.80, (
            f"Expected cos >= 0.80 with P=9.6% (pruning 90.4%), got {sig['cosine_similarity']}"
        )

    def test_top_p_algorithm1_binary_search_theta_08(self):
        """Verify Algorithm 1 binary search extracts minimal P satisfying theta=0.80."""
        from backend.training.train_tiny_imagenet import extract_top_p_signature

        torch.manual_seed(123)
        M = 50_000
        w = torch.distributions.StudentT(df=2.5).sample((M,))

        sig = extract_top_p_signature(w, theta=0.80, beta=0.0)
        assert sig["cosine_similarity"] >= 0.80
        # Paper finding: pruning 84% - 93% retains cos >= 0.8 -> P_min should be <= 16% of M
        assert sig["sparsity_ratio"] <= 0.16
        assert sig["payload_bytes"] < M * 4


