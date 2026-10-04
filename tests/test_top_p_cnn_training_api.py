"""Integration Test Suite for Interactive CIFAR-10 CNN Training API endpoint."""

from fastapi.testclient import TestClient
import pytest
from pathlib import Path

from backend.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


class TestCnnTrainingEndpoint:
    """Tests for POST /api/v1/toppaper/train-cnn endpoint."""

    def test_train_cnn_synthetic_fast_execution(self, client: TestClient):
        """Verify training endpoint runs synthetic training and returns valid TrainingResult."""
        payload = {
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.01,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 64,
        }

        response = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "final_train_loss" in data
        assert "final_train_accuracy" in data
        assert "final_test_loss" in data
        assert "final_test_accuracy" in data
        assert "duration_seconds" in data
        assert "epoch_history" in data
        assert len(data["epoch_history"]) == 1
        assert data["final_train_accuracy"] >= 0.0

        # Verify output checkpoint and flat parameter artifacts exist on disk
        ckpt_path = Path("output/models/cifar10_cnn_checkpoint.pt")
        flat_path = Path("output/models/cifar10_flat_parameters.pt")
        assert ckpt_path.exists(), "Checkpoint file missing after training"
        assert flat_path.exists(), "Flat parameter artifact missing after training"

    def test_train_cnn_multi_round_synthetic(self, client: TestClient):
        """Verify multi-round training preserves per-round checkpoints and returns round_history."""
        payload = {
            "rounds": 2,
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.01,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "seed": 42,
            "synthetic": True,
            "synthetic_samples": 64,
        }

        response = client.post("/api/v1/toppaper/train-cnn", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "round_history" in data, "round_history missing in response"
        assert len(data["round_history"]) == 2, f"Expected 2 rounds in history, got {len(data['round_history'])}"

        # Check round 1 and round 2 details
        r1 = data["round_history"][0]
        r2 = data["round_history"][1]
        assert r1["round"] == 1
        assert r2["round"] == 2
        assert "train_loss" in r1 and "train_accuracy" in r1
        assert "test_loss" in r1 and "test_accuracy" in r1
        assert "checkpoint_path" in r1 and "flat_parameters_path" in r1

        # Checkpoint files on disk
        round_1_ckpt = Path("output/models/rounds/cifar10_cnn_round_1.pt")
        round_2_ckpt = Path("output/models/rounds/cifar10_cnn_round_2.pt")
        round_1_flat = Path("output/models/rounds/cifar10_flat_round_1.pt")
        round_2_flat = Path("output/models/rounds/cifar10_flat_round_2.pt")

        assert round_1_ckpt.exists(), "Round 1 checkpoint missing on disk"
        assert round_2_ckpt.exists(), "Round 2 checkpoint missing on disk"
        assert round_1_flat.exists(), "Round 1 flat parameters missing on disk"
        assert round_2_flat.exists(), "Round 2 flat parameters missing on disk"

    def test_train_cnn_validation_bounds(self, client: TestClient):
        """Verify invalid hyperparameter values trigger validation errors."""
        # epochs < 1
        res = client.post("/api/v1/toppaper/train-cnn", json={"epochs": 0})
        assert res.status_code == 422

        # rounds < 1
        res = client.post("/api/v1/toppaper/train-cnn", json={"rounds": 0})
        assert res.status_code == 422

        # rounds > 50
        res = client.post("/api/v1/toppaper/train-cnn", json={"rounds": 100})
        assert res.status_code == 422

        # batch_size > 512
        res = client.post("/api/v1/toppaper/train-cnn", json={"batch_size": 1000})
        assert res.status_code == 422

        # learning_rate <= 0
        res = client.post("/api/v1/toppaper/train-cnn", json={"learning_rate": -0.05})
        assert res.status_code == 422

