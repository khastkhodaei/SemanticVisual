"""Automated Test Suite for Fashion-MNIST (FMNIST) CNN Model and Training Benchmark.

Tests adhere strictly to Section 5.1 of the SemanticDFL research paper:
1. Exact paper topology: Two 5x5 Conv layers (Conv1: 1->32, Conv2: 32->64, MaxPool 2x2 stride 2),
   ReLU activations, FC hidden layer (512 units), Output Linear layer (10 classes).
2. Input dimension: Grayscale 1x28x28 images.
3. 10 canonical Fashion-MNIST classes:
   (T-shirt/top, Trouser, Pullover, Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot).
4. Feature extraction: Penultimate representation of shape (B, 512).
5. Exact parameter count: 1,663,370 parameters.
6. Gradient flow: Backward pass yields non-null gradients across all layers.
7. Checkpoint serialization & lossless deserialization round-trip.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest
import torch
import torch.nn as nn

from backend.models.fmnist_cnn import FMNISTCNN, FMNIST_CLASSES, EXPECTED_FMNIST_PARAMETER_COUNT


class TestFMNISTCNNModel:
    """Unit tests for the FMNISTCNN architecture."""

    def test_canonical_classes(self):
        """Verify 10 canonical Fashion-MNIST classes match standard benchmark."""
        assert len(FMNIST_CLASSES) == 10
        expected = {
            0: "T-shirt/top",
            1: "Trouser",
            2: "Pullover",
            3: "Dress",
            4: "Coat",
            5: "Sandal",
            6: "Shirt",
            7: "Sneaker",
            8: "Bag",
            9: "Ankle boot",
        }
        assert FMNIST_CLASSES == expected

    @pytest.mark.parametrize("batch_size", [1, 4, 16, 64])
    def test_forward_output_shape(self, batch_size: int):
        """Verify forward pass produces exact (B, 10) logits for (B, 1, 28, 28) inputs."""
        model = FMNISTCNN()
        model.eval()
        x = torch.randn(batch_size, 1, 28, 28)
        with torch.no_grad():
            out = model(x)

        assert out.shape == (batch_size, 10), f"Expected shape ({batch_size}, 10), got {out.shape}"
        assert not torch.isnan(out).any(), "Output contains NaN values"
        assert not torch.isinf(out).any(), "Output contains Inf values"

    def test_feature_extraction_dimension(self):
        """Verify penultimate feature representation has shape (B, 512)."""
        model = FMNISTCNN()
        model.eval()
        x = torch.randn(8, 1, 28, 28)
        with torch.no_grad():
            features = model.extract_features(x)

        assert features.shape == (8, 512), f"Expected shape (8, 512), got {features.shape}"

    def test_invalid_input_shapes_raise_error(self):
        """Verify invalid input dimensions or channel counts raise ValueError."""
        model = FMNISTCNN()

        # 3D tensor instead of 4D
        with pytest.raises(ValueError, match="Expected 4D input tensor"):
            model(torch.randn(1, 28, 28))

        # Incorrect channel count (3 channels instead of 1)
        with pytest.raises(ValueError, match="Expected input with 1 channels"):
            model(torch.randn(4, 3, 28, 28))

    def test_gradient_flow(self):
        """Verify that backward pass computes valid gradients across all trainable layers."""
        model = FMNISTCNN()
        model.train()
        criterion = nn.CrossEntropyLoss()

        x = torch.randn(4, 1, 28, 28)
        y = torch.tensor([0, 1, 2, 3], dtype=torch.long)

        out = model(x)
        loss = criterion(out, y)
        loss.backward()

        for name, param in model.named_parameters():
            assert param.grad is not None, f"Parameter {name} has no gradient."
            assert not torch.isnan(param.grad).any(), f"Parameter {name} gradient contains NaN."

    def test_topology_summary_and_parameter_count(self):
        """Verify topology metadata dictionary and exact parameter count (1,663,370)."""
        model = FMNISTCNN()
        summary = model.get_topology_summary()

        assert summary["model_type"] == "FMNISTCNN"
        assert summary["in_channels"] == 1
        assert summary["num_classes"] == 10
        assert summary["conv1"]["in_channels"] == 1
        assert summary["conv1"]["out_channels"] == 32
        assert summary["conv1"]["kernel_size"] == 5
        assert summary["conv2"]["in_channels"] == 32
        assert summary["conv2"]["out_channels"] == 64
        assert summary["conv2"]["kernel_size"] == 5
        assert summary["fc1"]["in_features"] == 3136  # 64 * 7 * 7
        assert summary["fc1"]["out_features"] == 512
        assert summary["fc2"]["in_features"] == 512
        assert summary["fc2"]["out_features"] == 10
        assert summary["total_parameters"] == EXPECTED_FMNIST_PARAMETER_COUNT
        assert summary["total_parameters"] == 1663370
        assert summary["total_parameters"] == model.count_parameters()


class TestSerializationAndReload:
    """Tests for model checkpointing, metadata serialization, and lossless deserialization."""

    def test_checkpoint_round_trip_lossless(self):
        """Verify saved checkpoint weights reload with zero numerical discrepancy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_file = Path(tmpdir) / "fmnist_test_model.pt"

            # 1. Initialize and mutate weights
            model_orig = FMNISTCNN()
            with torch.no_grad():
                for param in model_orig.parameters():
                    param.add_(torch.randn_like(param) * 0.1)

            # 2. Save checkpoint
            saved_ckpt, saved_meta = model_orig.save_checkpoint(
                ckpt_file, metadata={"test_accuracy": 0.88}
            )
            assert saved_ckpt.exists()
            assert saved_meta.exists()

            # 3. Reload into a new model instance
            model_reloaded, loaded_meta = FMNISTCNN.load_checkpoint(saved_ckpt)

            # 4. Check weight exact equivalence
            for (k1, v1), (k2, v2) in zip(
                model_orig.state_dict().items(), model_reloaded.state_dict().items()
            ):
                assert k1 == k2
                assert torch.equal(v1, v2), f"Discrepancy detected in layer {k1}."

            # 5. Check inference output exact match
            x = torch.randn(8, 1, 28, 28)
            with torch.no_grad():
                out_orig = model_orig(x)
                out_reloaded = model_reloaded(x)
            assert torch.allclose(out_orig, out_reloaded, atol=1e-7)

            # 6. Check metadata payload
            assert loaded_meta["test_accuracy"] == 0.88
            assert loaded_meta["model_name"] == "FMNISTCNN"

    def test_metadata_json_schema(self):
        """Verify model_metadata.json conforms to expected contract and contains class mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model = FMNISTCNN()
            ckpt_path = Path(tmpdir) / "model.pt"
            _, meta_path = model.save_checkpoint(ckpt_path)

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["model_name"] == "FMNISTCNN"
            assert data["num_parameters"] == 1663370
            assert "topology" in data
            assert "classes" in data
            assert len(data["classes"]) == 10
            assert data["classes"]["0"] == "T-shirt/top" or data["classes"][0] == "T-shirt/top"


class TestParameterFlattening:
    """Unit tests for deterministic parameter flattening and unflattening with FMNISTCNN."""

    def test_fmnist_flat_parameters_shape_and_slices(self):
        """Assert flat parameter tensor shape is exactly (1663370,) and float32."""
        from backend.models.flattening import CANONICAL_LAYER_ORDER, flatten_parameters

        model = FMNISTCNN()
        flat_tensor, metadata = flatten_parameters(model)

        assert flat_tensor.dim() == 1
        assert flat_tensor.shape == (EXPECTED_FMNIST_PARAMETER_COUNT,)
        assert flat_tensor.shape == (1663370,)
        assert flat_tensor.dtype == torch.float32
        assert metadata["num_parameters"] == EXPECTED_FMNIST_PARAMETER_COUNT
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
        assert prev_end == EXPECTED_FMNIST_PARAMETER_COUNT

    def test_fmnist_flatten_unflatten_roundtrip(self):
        """Verify flattening, loading into fresh model, and running forward yields exact parity."""
        from backend.models.flattening import flatten_parameters, unflatten_parameters

        model_source = FMNISTCNN()
        with torch.no_grad():
            for p in model_source.parameters():
                p.add_(torch.randn_like(p) * 0.2)

        flat_tensor, metadata = flatten_parameters(model_source)

        model_target = FMNISTCNN()
        assert not torch.equal(
            list(model_source.parameters())[0], list(model_target.parameters())[0]
        )

        unflatten_parameters(flat_tensor, metadata["layer_slices"], model_target)

        for (k1, v1), (k2, v2) in zip(
            model_source.state_dict().items(), model_target.state_dict().items()
        ):
            assert k1 == k2
            assert torch.equal(v1, v2), f"Numerical mismatch in layer {k1}"

        test_input = torch.randn(16, 1, 28, 28)
        model_source.eval()
        model_target.eval()
        with torch.no_grad():
            out_source = model_source(test_input)
            out_target = model_target(test_input)

        assert torch.allclose(out_source, out_target, atol=1e-7)

    def test_fmnist_flat_artifact_save_load_roundtrip(self):
        """Verify saving and loading flat parameter artifact retains model_name and metadata."""
        from backend.models.flattening import (
            flatten_parameters,
            load_flat_parameters_artifact,
            save_flat_parameters_artifact,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            model = FMNISTCNN()
            flat_tensor, metadata = flatten_parameters(model)
            out_path = Path(tmpdir) / "fmnist_flat_parameters.pt"

            saved_path = save_flat_parameters_artifact(
                flat_tensor=flat_tensor,
                metadata=metadata,
                output_path=out_path,
                source_checkpoint="output/models/fmnist_cnn_checkpoint.pt",
                model_name="FMNISTCNN",
            )
            assert saved_path.exists()

            loaded_tensor, loaded_meta = load_flat_parameters_artifact(saved_path)
            assert loaded_tensor.shape == (EXPECTED_FMNIST_PARAMETER_COUNT,)
            assert loaded_meta["num_parameters"] == EXPECTED_FMNIST_PARAMETER_COUNT
            assert loaded_meta["metadata"]["model_name"] == "FMNISTCNN"


class TestFMNISTTrainingPipeline:
    """Unit tests for the single-client FMNIST training pipeline."""

    def test_fmnist_dataloader_synthetic(self):
        """Verify synthetic dataloader produces correct tensor shapes (B, 1, 28, 28)."""
        from backend.training.train_fmnist import TrainingConfig, get_dataloaders

        config = TrainingConfig(
            batch_size=32,
            synthetic=True,
            synthetic_samples=64,
            seed=42,
        )
        train_loader, test_loader = get_dataloaders(config)

        x_batch, y_batch = next(iter(train_loader))
        assert x_batch.shape == (32, 1, 28, 28)
        assert y_batch.shape == (32,)
        assert y_batch.min() >= 0
        assert y_batch.max() < 10

    def test_single_client_1epoch_paper_hyperparameters(self):
        """Verify single-client local training with paper defaults (lr=0.01, batch_size=64, epochs=1)."""
        from backend.training.train_fmnist import TrainingConfig, train_fmnist_model

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainingConfig(
                rounds=1,
                epochs=1,
                batch_size=64,
                learning_rate=0.01,
                seed=42,
                output_dir=tmpdir,
                checkpoint_dir=str(Path(tmpdir) / "rounds"),
                synthetic=True,
                synthetic_samples=128,
            )
            model, result = train_fmnist_model(config)

            assert Path(result.checkpoint_path).exists()
            assert Path(result.metadata_path).exists()
            assert Path(result.flat_parameters_path).exists()
            assert len(result.epoch_history) == 1
            assert result.final_train_accuracy >= 0.0
            assert result.final_test_accuracy >= 0.0

            # Verify saved metadata content
            with open(result.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["dataset"] == "Fashion-MNIST"
            assert meta["hyperparameters"]["learning_rate"] == 0.01
            assert meta["hyperparameters"]["batch_size"] == 64
            assert meta["hyperparameters"]["epochs"] == 1
            assert meta["classes"]["0"] == "T-shirt/top"

    def test_deterministic_seed_training(self):
        """Verify training with identical seeds produces byte-for-byte identical weights."""
        from backend.training.train_fmnist import TrainingConfig, train_fmnist_model

        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            cfg1 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.01,
                seed=101,
                output_dir=tmp1,
                checkpoint_dir=str(Path(tmp1) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
            )
            cfg2 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.01,
                seed=101,
                output_dir=tmp2,
                checkpoint_dir=str(Path(tmp2) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
            )
            m1, res1 = train_fmnist_model(cfg1)
            m2, res2 = train_fmnist_model(cfg2)

            assert res1.final_train_loss == pytest.approx(res2.final_train_loss, abs=1e-5)
            assert res1.final_test_loss == pytest.approx(res2.final_test_loss, abs=1e-5)
            for p1, p2 in zip(m1.parameters(), m2.parameters()):
                assert torch.allclose(p1, p2, atol=1e-6)


class TestFMNISTTopPSignatures:
    """Unit tests for Top-P signature extraction and directional cosine similarity retention."""

    def test_top_p_signature_extraction_algorithm1(self):
        """Verify Algorithm 1 extracts minimal P_min retaining cos(w, w^[P]) >= theta (0.70)."""
        from backend.training.train_fmnist import extract_top_p_signature

        # Create known weight vector
        w = torch.tensor([0.5, -3.0, 0.2, 2.0, -0.1, 1.5, 0.3, -1.0, 0.4, 0.6], dtype=torch.float32)
        sig_info = extract_top_p_signature(w, theta=0.90, beta=0.0)

        # From worked example: for theta=0.90, P_min is 3
        assert sig_info["p_min"] == 3
        assert sig_info["cosine_similarity"] >= 0.90
        assert len(sig_info["indices"]) == 3
        assert len(sig_info["values"]) == 3
        assert sig_info["payload_bytes"] == 3 * (4 + 2)  # 18 bytes

    def test_fmnist_model_top_p_retention(self):
        """Verify Top-P signature from a trained FMNIST model satisfies theta=0.70 threshold."""
        from backend.models.flattening import flatten_parameters
        from backend.training.train_fmnist import extract_top_p_signature

        model = FMNISTCNN()
        flat_w, _ = flatten_parameters(model)

        theta = 0.70
        sig = extract_top_p_signature(flat_w, theta=theta, beta=0.0)

        assert sig["cosine_similarity"] >= theta
        assert 1 <= sig["p_min"] <= flat_w.numel()
        assert sig["sparsity_ratio"] < 1.0
        assert sig["payload_bytes"] < flat_w.numel() * 4


