"""Automated Test Suite for CIFAR-10 CNN Model, Flattening, and Training Pipeline.

Tests:
1. Shape contract: Input (B, 3, 32, 32) -> Output (B, 10) across diverse batch sizes.
2. Feature extraction: Intermediate layer yields (B, 512) representations.
3. Gradient propagation: Loss backward populates non-null gradients on all parameters.
4. Deterministic training: Same seed yields identical model weights and metrics.
5. Serialization & Round-Trip: Checkpoint saved to disk and reloaded with 0.0 error.
6. Metadata verification: Checks all required fields in model_metadata.json.
7. Flattening & Unflattening:
   - Shape & length: (2156490,) flat float32 tensor.
   - Exact round-trip parameter parity (0.0 discrepancy).
   - Equivalence of forward pass outputs on fresh model after unflattening.
   - Artifact file integrity (output/models/cifar10_flat_parameters.pt).
"""

import json
from pathlib import Path
import tempfile
import pytest
import torch
import torch.nn as nn

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
from backend.training.train_cifar import (
    TrainingConfig,
    evaluate_model,
    set_seed,
    train_cifar_model,
    train_one_epoch,
)


class TestCIFAR10CNNModel:
    """Unit tests for the CIFAR10CNN architecture."""

    @pytest.mark.parametrize("batch_size", [1, 4, 16, 64])
    def test_forward_output_shape(self, batch_size: int):
        """Verify forward pass produces exact (B, 10) logits for (B, 3, 32, 32) inputs."""
        model = CIFAR10CNN()
        model.eval()
        x = torch.randn(batch_size, 3, 32, 32)
        with torch.no_grad():
            out = model(x)

        assert out.shape == (batch_size, 10), f"Expected shape ({batch_size}, 10), got {out.shape}"
        assert not torch.isnan(out).any(), "Output contains NaN values"
        assert not torch.isinf(out).any(), "Output contains Inf values"

    def test_feature_extraction_dimension(self):
        """Verify penultimate feature representation has shape (B, 512)."""
        model = CIFAR10CNN()
        model.eval()
        x = torch.randn(8, 3, 32, 32)
        with torch.no_grad():
            features = model.extract_features(x)

        assert features.shape == (8, 512), f"Expected shape (8, 512), got {features.shape}"

    def test_invalid_input_shapes_raise_error(self):
        """Verify invalid input dimensions or channel counts raise ValueError."""
        model = CIFAR10CNN()

        # 3D tensor instead of 4D
        with pytest.raises(ValueError, match="Expected 4D input tensor"):
            model(torch.randn(3, 32, 32))

        # Incorrect channel count (e.g., 1 channel instead of 3)
        with pytest.raises(ValueError, match="Expected input with 3 channels"):
            model(torch.randn(4, 1, 32, 32))

    def test_gradient_flow(self):
        """Verify that backward pass computes valid gradients across all trainable layers."""
        model = CIFAR10CNN()
        model.train()
        criterion = nn.CrossEntropyLoss()

        x = torch.randn(4, 3, 32, 32)
        y = torch.tensor([0, 1, 2, 3], dtype=torch.long)

        out = model(x)
        loss = criterion(out, y)
        loss.backward()

        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient."
            assert not torch.isnan(param.grad).any(), f"Parameter {name} gradient contains NaN."

    def test_topology_summary(self):
        """Verify topology metadata dictionary accurately reflects architecture parameters."""
        model = CIFAR10CNN()
        summary = model.get_topology_summary()

        assert summary["model_type"] == "CIFAR10CNN"
        assert summary["in_channels"] == 3
        assert summary["num_classes"] == 10
        assert summary["conv1"]["kernel_size"] == 5
        assert summary["conv1"]["out_channels"] == 32
        assert summary["conv2"]["out_channels"] == 64
        assert summary["fc1"]["out_features"] == 512
        assert summary["total_parameters"] == EXPECTED_PARAMETER_COUNT
        assert summary["total_parameters"] == model.count_parameters()


class TestSerializationAndReload:
    """Tests for model checkpointing, metadata serialization, and lossless deserialization."""

    def test_checkpoint_round_trip_lossless(self):
        """Verify saved checkpoint weights reload with zero numerical discrepancy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_file = Path(tmpdir) / "test_model.pt"

            # 1. Initialize and mutate weights
            model_orig = CIFAR10CNN()
            with torch.no_grad():
                for param in model_orig.parameters():
                    param.add_(torch.randn_like(param) * 0.1)

            # 2. Save checkpoint
            saved_ckpt, saved_meta = model_orig.save_checkpoint(
                ckpt_file, metadata={"test_metric": 0.95}
            )
            assert saved_ckpt.exists()
            assert saved_meta.exists()

            # 3. Reload into a new model instance
            model_reloaded, loaded_meta = CIFAR10CNN.load_checkpoint(saved_ckpt)

            # 4. Check weight exact equivalence
            for (k1, v1), (k2, v2) in zip(
                model_orig.state_dict().items(), model_reloaded.state_dict().items()
            ):
                assert k1 == k2
                assert torch.equal(v1, v2), f"Discrepancy detected in layer {k1}."

            # 5. Check inference output exact match
            x = torch.randn(8, 3, 32, 32)
            with torch.no_grad():
                out_orig = model_orig(x)
                out_reloaded = model_reloaded(x)
            assert torch.allclose(out_orig, out_reloaded, atol=1e-7)

            # 6. Check metadata payload
            assert loaded_meta["test_metric"] == 0.95
            assert loaded_meta["model_name"] == "CIFAR10CNN"

    def test_metadata_json_schema(self):
        """Verify model_metadata.json conforms to expected contract and contains class mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model = CIFAR10CNN()
            ckpt_path = Path(tmpdir) / "model.pt"
            _, meta_path = model.save_checkpoint(ckpt_path)

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "model_name" in data
            assert "num_parameters" in data
            assert "topology" in data
            assert "classes" in data
            assert len(data["classes"]) == 10
            assert data["classes"]["0"] == "airplane" or data["classes"][0] == "airplane"


class TestParameterFlattening:
    """Unit tests for deterministic parameter flattening and unflattening routines."""

    def test_flat_parameters_shape_and_length(self):
        """Assert flat parameter tensor shape is exactly (2156490,) and float32."""
        model = CIFAR10CNN()
        flat_tensor, metadata = flatten_parameters(model)

        assert flat_tensor.dim() == 1
        assert flat_tensor.shape == (EXPECTED_PARAMETER_COUNT,)
        assert flat_tensor.shape == (2156490,)
        assert flat_tensor.dtype == torch.float32
        assert metadata["num_parameters"] == EXPECTED_PARAMETER_COUNT
        assert metadata["l2_norm"] > 0.0
        assert len(metadata["layer_slices"]) == len(CANONICAL_LAYER_ORDER)

        # Validate slice continuity: start_idx of layer i+1 == end_idx of layer i
        prev_end = 0
        for layer_name in CANONICAL_LAYER_ORDER:
            assert layer_name in metadata["layer_slices"]
            info = metadata["layer_slices"][layer_name]
            assert info["start_idx"] == prev_end
            assert info["end_idx"] == info["start_idx"] + info["numel"]
            prev_end = info["end_idx"]
        assert prev_end == EXPECTED_PARAMETER_COUNT

    def test_flatten_unflatten_roundtrip(self):
        """Verify flattening, loading into fresh model, and running forward yields exact parity."""
        # 1. Instantiate source model with mutated weights
        model_source = CIFAR10CNN()
        with torch.no_grad():
            for p in model_source.parameters():
                p.add_(torch.randn_like(p) * 0.2)

        # 2. Flatten parameters
        flat_tensor, metadata = flatten_parameters(model_source)

        # 3. Instantiate target model (with different initial weights)
        model_target = CIFAR10CNN()

        # Verify target has different initial parameters
        assert not torch.equal(
            list(model_source.parameters())[0], list(model_target.parameters())[0]
        )

        # 4. Unflatten parameters into target model
        unflatten_parameters(flat_tensor, metadata["layer_slices"], model_target)

        # 5. Check exact parameter equality across every layer
        for (k1, v1), (k2, v2) in zip(
            model_source.state_dict().items(), model_target.state_dict().items()
        ):
            assert k1 == k2
            assert torch.equal(v1, v2), f"Numerical mismatch in layer {k1}"

        # 6. Check forward inference output parity
        test_input = torch.randn(16, 3, 32, 32)
        model_source.eval()
        model_target.eval()
        with torch.no_grad():
            out_source = model_source(test_input)
            out_target = model_target(test_input)

        assert torch.allclose(out_source, out_target, atol=1e-7)

    def test_flat_artifact_file_integrity(self):
        """Assert output/models/cifar10_flat_parameters.pt exists and has valid schema."""
        artifact_path = Path("output/models/cifar10_flat_parameters.pt")
        assert artifact_path.exists(), "Artifact file output/models/cifar10_flat_parameters.pt does not exist."

        flat_tensor, metadata = load_flat_parameters_artifact(artifact_path)
        assert flat_tensor.shape == (2156490,)
        assert flat_tensor.dtype == torch.float32
        assert metadata["num_parameters"] == 2156490
        assert metadata["l2_norm"] > 0.0
        assert "layer_slices" in metadata
        assert len(metadata["layer_slices"]) == 8
        assert "metadata" in metadata
        assert metadata["metadata"]["model_name"] == "CIFAR10CNN"

    def test_unflatten_invalid_dimensions_raise_error(self):
        """Verify invalid flat tensor sizes or malformed slices raise errors."""
        model = CIFAR10CNN()
        _, metadata = flatten_parameters(model)

        # 2D tensor instead of 1D
        with pytest.raises(ValueError, match="Expected 1D flat tensor"):
            unflatten_parameters(torch.randn(10, 10), metadata["layer_slices"], model)

        # Tensor too short
        short_tensor = torch.randn(100)
        with pytest.raises(ValueError, match="exceeds tensor length"):
            unflatten_parameters(short_tensor, metadata["layer_slices"], model)


class TestTrainingPipeline:
    """Unit tests for the end-to-end training and evaluation pipeline."""

    def test_deterministic_seed(self):
        """Verify training with fixed seed produces deterministic weights and results."""
        config1 = TrainingConfig(
            epochs=1,
            batch_size=16,
            learning_rate=0.01,
            seed=42,
            synthetic=True,
            synthetic_samples=64,
        )
        config2 = TrainingConfig(
            epochs=1,
            batch_size=16,
            learning_rate=0.01,
            seed=42,
            synthetic=True,
            synthetic_samples=64,
        )

        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            config1.output_dir = tmpdir1
            config2.output_dir = tmpdir2

            model1, res1 = train_cifar_model(config1)
            model2, res2 = train_cifar_model(config2)

            assert res1.final_train_loss == pytest.approx(res2.final_train_loss, abs=1e-5)
            assert res1.final_test_loss == pytest.approx(res2.final_test_loss, abs=1e-5)

            for p1, p2 in zip(model1.parameters(), model2.parameters()):
                assert torch.allclose(p1, p2, atol=1e-6)

    def test_train_pipeline_saves_artifacts(self):
        """Verify train_cifar_model properly produces all checkpoint artifacts in target directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                epochs=2,
                batch_size=32,
                learning_rate=0.01,
                seed=123,
                output_dir=tmpdir,
                synthetic=True,
                synthetic_samples=128,
            )
            model, result = train_cifar_model(config)

            assert Path(result.checkpoint_path).exists()
            assert Path(result.metadata_path).exists()
            assert len(result.epoch_history) == 2
            assert result.final_train_accuracy >= 0.0
            assert result.final_test_accuracy >= 0.0

            # Verify saved metadata content
            with open(result.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["dataset"] == "CIFAR-10"
            assert meta["hyperparameters"]["learning_rate"] == 0.01
            assert meta["hyperparameters"]["batch_size"] == 32
            assert "metrics" in meta
            assert "timestamp_utc" in meta["execution"]
