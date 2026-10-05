"""Automated Test Suite for Google Speech Commands ResNet-18 Benchmark.

Tests adhere strictly to Section 5.1 of the SemanticDFL research paper:
1. Audio feature extraction: Raw 16 kHz audio waveform (16,000 samples) converted to
   Log-Mel spectrogram tensor of shape (B, 1, 64, 101).
2. ResNet-18 architecture adapted for 1-channel Log-Mel spectrogram inputs with 10 command classes:
   (yes, no, up, down, left, right, on, off, stop, go).
3. Parameter count: ~11.17M - 11.2M parameters.
4. Forward pass shape contract: Input (B, 1, 64, 101) -> Output (B, 10).
5. Penultimate feature extraction representation of shape (B, 512).
6. Gradient flow across residual blocks and convolutional layers.
7. Checkpoint serialization and lossless deserialization round-trip.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest
import torch
import torch.nn as nn

from backend.models.speech_resnet import (
    AudioToLogMelSpectrogram,
    SpeechResNet18,
    SPEECH_COMMANDS_CLASSES,
    EXPECTED_SPEECH_PARAMETER_COUNT,
)


class TestAudioPreprocessing:
    """Unit tests for waveform-to-LogMel spectrogram audio preprocessing."""

    def test_waveform_to_log_mel_spectrogram_shape(self):
        """Verify 1-second 16kHz audio waveform converts to (B, 1, 64, 101) Log-Mel spectrogram."""
        preprocessor = AudioToLogMelSpectrogram(sample_rate=16000, n_mels=64, n_fft=400, hop_length=160)
        # Batch of 4 1-second audio clips
        waveform = torch.randn(4, 16000)
        spec = preprocessor(waveform)

        assert spec.dim() == 4
        assert spec.shape == (4, 1, 64, 101), f"Expected shape (4, 1, 64, 101), got {spec.shape}"
        assert not torch.isnan(spec).any(), "Spectrogram contains NaN values"
        assert not torch.isinf(spec).any(), "Spectrogram contains Inf values"

    def test_single_waveform_input_handling(self):
        """Verify 1D waveform (16000,) is automatically reshaped to (1, 1, 64, 101)."""
        preprocessor = AudioToLogMelSpectrogram(sample_rate=16000, n_mels=64, n_fft=400, hop_length=160)
        waveform = torch.randn(16000)
        spec = preprocessor(waveform)

        assert spec.shape == (1, 1, 64, 101)


class TestSpeechResNet18Model:
    """Unit tests for the SpeechResNet18 architecture."""

    def test_canonical_classes(self):
        """Verify 10 canonical Google Speech Commands core target classes."""
        assert len(SPEECH_COMMANDS_CLASSES) == 10
        expected = {
            0: "yes",
            1: "no",
            2: "up",
            3: "down",
            4: "left",
            5: "right",
            6: "on",
            7: "off",
            8: "stop",
            9: "go",
        }
        assert SPEECH_COMMANDS_CLASSES == expected

    @pytest.mark.parametrize("batch_size", [1, 2, 4])
    def test_forward_output_shape(self, batch_size: int):
        """Verify forward pass produces exact (B, 10) logits for (B, 1, 64, 101) inputs."""
        model = SpeechResNet18(num_classes=10)
        model.eval()
        x = torch.randn(batch_size, 1, 64, 101)
        with torch.no_grad():
            out = model(x)

        assert out.shape == (batch_size, 10), f"Expected shape ({batch_size}, 10), got {out.shape}"
        assert not torch.isnan(out).any(), "Output contains NaN values"
        assert not torch.isinf(out).any(), "Output contains Inf values"

    def test_feature_extraction_dimension(self):
        """Verify penultimate feature representation has shape (B, 512)."""
        model = SpeechResNet18()
        model.eval()
        x = torch.randn(2, 1, 64, 101)
        with torch.no_grad():
            features = model.extract_features(x)

        assert features.shape == (2, 512), f"Expected shape (2, 512), got {features.shape}"

    def test_invalid_input_shapes_raise_error(self):
        """Verify invalid input dimensions or channel counts raise ValueError."""
        model = SpeechResNet18()

        # 3D tensor instead of 4D
        with pytest.raises(ValueError, match="Expected 4D input tensor"):
            model(torch.randn(1, 64, 101))

        # Incorrect channel count (3 channels instead of 1)
        with pytest.raises(ValueError, match="Expected input with 1 channels"):
            model(torch.randn(2, 3, 64, 101))

    def test_parameter_count_matches_paper_specification(self):
        """Verify total parameter count is ~11.17M - 11.2M as cited in paper and PAPER_COSTS.md."""
        model = SpeechResNet18(num_classes=10)
        param_count = model.count_parameters()
        assert 11_100_000 <= param_count <= 11_300_000, (
            f"Expected parameter count in range [11.1M, 11.3M], got {param_count}"
        )
        assert param_count == EXPECTED_SPEECH_PARAMETER_COUNT

    def test_gradient_flow(self):
        """Verify backward pass computes valid gradients across all trainable layers."""
        model = SpeechResNet18(num_classes=10)
        model.train()
        criterion = nn.CrossEntropyLoss()

        x = torch.randn(2, 1, 64, 101)
        y = torch.tensor([0, 9], dtype=torch.long)

        out = model(x)
        loss = criterion(out, y)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"Parameter {name} has no gradient."
                assert not torch.isnan(param.grad).any(), f"Parameter {name} gradient contains NaN."

    def test_topology_summary(self):
        """Verify topology metadata dictionary accurately reflects architecture parameters."""
        model = SpeechResNet18(num_classes=10)
        summary = model.get_topology_summary()

        assert summary["model_type"] == "SpeechResNet18"
        assert summary["in_channels"] == 1
        assert summary["num_classes"] == 10
        assert "stem" in summary
        assert "stages" in summary
        assert summary["total_parameters"] == model.count_parameters()


class TestSerializationAndReload:
    """Tests for model checkpointing and lossless deserialization."""

    def test_checkpoint_round_trip_lossless(self):
        """Verify saved checkpoint weights reload with zero numerical discrepancy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_file = Path(tmpdir) / "speech_resnet_test.pt"

            model_orig = SpeechResNet18(num_classes=10)
            with torch.no_grad():
                for param in model_orig.parameters():
                    param.add_(torch.randn_like(param) * 0.05)

            saved_ckpt, saved_meta = model_orig.save_checkpoint(
                ckpt_file, metadata={"test_metric": 0.92}
            )
            assert saved_ckpt.exists()
            assert saved_meta.exists()

            model_reloaded, loaded_meta = SpeechResNet18.load_checkpoint(saved_ckpt)

            for (k1, v1), (k2, v2) in zip(
                model_orig.state_dict().items(), model_reloaded.state_dict().items()
            ):
                assert k1 == k2
                assert torch.equal(v1, v2), f"Discrepancy detected in layer {k1}."

            model_orig.eval()
            model_reloaded.eval()
            x = torch.randn(2, 1, 64, 101)
            with torch.no_grad():
                out_orig = model_orig(x)
                out_reloaded = model_reloaded(x)
            assert torch.allclose(out_orig, out_reloaded, atol=1e-5)

            assert loaded_meta["test_metric"] == 0.92
            assert loaded_meta["model_name"] == "SpeechResNet18"


class TestParameterFlattening:
    """Unit tests for parameter flattening and unflattening with SpeechResNet18."""

    def test_speech_resnet_flatten_parameters_shape_and_slices(self):
        """Assert flat parameter tensor matches trainable parameter count with slice continuity."""
        from backend.models.flattening import flatten_parameters

        model = SpeechResNet18(num_classes=10)
        expected_count = model.count_parameters()

        flat_tensor, metadata = flatten_parameters(model)

        assert flat_tensor.dim() == 1
        assert flat_tensor.shape == (expected_count,)
        assert flat_tensor.shape == (EXPECTED_SPEECH_PARAMETER_COUNT,)
        assert flat_tensor.dtype == torch.float32
        assert metadata["num_parameters"] == expected_count
        assert metadata["l2_norm"] > 0.0
        assert metadata["model_name"] == "SpeechResNet18"

        # Check slice continuity
        prev_end = 0
        for layer_name in metadata["canonical_layers"]:
            info = metadata["layer_slices"][layer_name]
            assert info["start_idx"] == prev_end
            assert info["end_idx"] == info["start_idx"] + info["numel"]
            prev_end = info["end_idx"]
        assert prev_end == expected_count

    def test_speech_resnet_flatten_unflatten_roundtrip(self):
        """Verify flattening, loading into fresh model, and running forward yields exact parity."""
        from backend.models.flattening import flatten_parameters, unflatten_parameters

        model_source = SpeechResNet18(num_classes=10)
        with torch.no_grad():
            for p in model_source.parameters():
                p.add_(torch.randn_like(p) * 0.05)

        flat_tensor, metadata = flatten_parameters(model_source)

        model_target = SpeechResNet18(num_classes=10)
        unflatten_parameters(flat_tensor, metadata["layer_slices"], model_target)

        for (k1, v1), (k2, v2) in zip(
            model_source.state_dict().items(), model_target.state_dict().items()
        ):
            assert k1 == k2
            assert torch.equal(v1, v2), f"Numerical mismatch in layer {k1}"

        model_source.eval()
        model_target.eval()
        test_input = torch.randn(2, 1, 64, 101)
        with torch.no_grad():
            out_source = model_source(test_input)
            out_target = model_target(test_input)

        assert torch.allclose(out_source, out_target, atol=1e-5)

    def test_speech_resnet_flat_artifact_save_load_roundtrip(self):
        """Verify saving and loading flat parameter artifact retains model_name and metadata."""
        from backend.models.flattening import (
            flatten_parameters,
            load_flat_parameters_artifact,
            save_flat_parameters_artifact,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            model = SpeechResNet18(num_classes=10)
            flat_tensor, metadata = flatten_parameters(model)
            out_path = Path(tmpdir) / "speech_resnet_flat_parameters.pt"

            saved_path = save_flat_parameters_artifact(
                flat_tensor=flat_tensor,
                metadata=metadata,
                output_path=out_path,
                source_checkpoint="output/models/speech_resnet18.pt",
                model_name="SpeechResNet18",
            )
            assert saved_path.exists()

            loaded_tensor, loaded_meta = load_flat_parameters_artifact(saved_path)
            assert loaded_tensor.shape == (EXPECTED_SPEECH_PARAMETER_COUNT,)
            assert loaded_meta["num_parameters"] == EXPECTED_SPEECH_PARAMETER_COUNT
            assert loaded_meta["metadata"]["model_name"] == "SpeechResNet18"


class TestSpeechTrainingPipeline:
    """Unit tests for the single-client Google Speech Commands ResNet-18 training pipeline."""

    def test_speech_dataloader_synthetic(self):
        """Verify synthetic dataloader produces correct spectrogram shapes (B, 1, 64, 101) and labels [0..9]."""
        from backend.training.train_speech import TrainingConfig, get_dataloaders

        config = TrainingConfig(
            batch_size=32,
            synthetic=True,
            synthetic_samples=64,
            seed=42,
        )
        train_loader, test_loader = get_dataloaders(config)

        x_batch, y_batch = next(iter(train_loader))
        assert x_batch.shape == (32, 1, 64, 101)
        assert y_batch.shape == (32,)
        assert y_batch.min() >= 0
        assert y_batch.max() < 10

    def test_single_client_1epoch_paper_hyperparameters(self):
        """Verify single-client local training with paper defaults (lr=0.01, batch_size=64, epochs=1)."""
        from backend.training.train_speech import TrainingConfig, train_speech_model

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
            model, result = train_speech_model(config)

            assert Path(result.checkpoint_path).exists()
            assert Path(result.metadata_path).exists()
            assert Path(result.flat_parameters_path).exists()
            assert len(result.epoch_history) == 1
            assert result.final_train_accuracy >= 0.0
            assert result.final_test_accuracy >= 0.0

            with open(result.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["dataset"] == "Google Speech Commands"
            assert meta["hyperparameters"]["learning_rate"] == 0.01
            assert meta["hyperparameters"]["batch_size"] == 64
            assert meta["hyperparameters"]["epochs"] == 1
            assert meta["num_classes"] == 10
            assert meta["classes"]["0"] == "yes"

    def test_deterministic_seed_training(self):
        """Verify training with identical seeds produces identical model weights."""
        from backend.training.train_speech import TrainingConfig, train_speech_model

        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            cfg1 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.01,
                seed=55,
                output_dir=tmp1,
                checkpoint_dir=str(Path(tmp1) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
            )
            cfg2 = TrainingConfig(
                epochs=1,
                batch_size=32,
                learning_rate=0.01,
                seed=55,
                output_dir=tmp2,
                checkpoint_dir=str(Path(tmp2) / "rounds"),
                synthetic=True,
                synthetic_samples=64,
            )
            m1, res1 = train_speech_model(cfg1)
            m2, res2 = train_speech_model(cfg2)

            assert res1.final_train_loss == pytest.approx(res2.final_train_loss, abs=1e-5)
            assert res1.final_test_loss == pytest.approx(res2.final_test_loss, abs=1e-5)
            for p1, p2 in zip(m1.parameters(), m2.parameters()):
                assert torch.allclose(p1, p2, atol=1e-6)


class TestSpeechTopPSignatures:
    """Unit tests for Top-P signature extraction on Google Speech Commands ResNet-18."""

    def test_top_p_pruning_88_8_percent_paper_finding(self):
        """Verify paper finding: retaining P ≈ 11.2% of M (pruning 88.8%) retains cos >= 0.8."""
        from backend.training.train_speech import extract_top_p_signature

        torch.manual_seed(42)
        M = 100_000
        # Student-T distribution matches heavy-tailed neural network weight gradients
        w = torch.distributions.StudentT(df=3.0).sample((M,))

        # Prune 88.8% of weights -> keep P = 11.2% of M
        p_paper = int(round(0.112 * M))
        sig = extract_top_p_signature(w, p_fixed=p_paper, beta=0.0)

        assert sig["p_min"] == p_paper
        assert sig["sparsity_ratio"] == pytest.approx(0.112, abs=0.001)
        assert sig["cosine_similarity"] >= 0.80, (
            f"Expected cos >= 0.80 with P=11.2% (pruning 88.8%), got {sig['cosine_similarity']}"
        )

    def test_top_p_algorithm1_binary_search_theta_08(self):
        """Verify Algorithm 1 binary search extracts minimal P satisfying theta=0.80."""
        from backend.training.train_speech import extract_top_p_signature

        torch.manual_seed(99)
        M = 50_000
        w = torch.distributions.StudentT(df=2.8).sample((M,))

        sig = extract_top_p_signature(w, theta=0.80, beta=0.0)
        assert sig["cosine_similarity"] >= 0.80
        # Paper finding: pruning 84% - 93% retains cos >= 0.8 -> P_min should be <= 16% of M
        assert sig["sparsity_ratio"] <= 0.16
        assert sig["payload_bytes"] < M * 4


