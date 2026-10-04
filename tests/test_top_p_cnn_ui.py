"""Contract-Driven Test Suite for Top-P CNN Parameter Inspection API & UI integration."""

from fastapi.testclient import TestClient
import pytest
import torch

from backend.main import app
from backend.models.flattening import CANONICAL_LAYER_ORDER, EXPECTED_PARAMETER_COUNT


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


class TestTopPCNNWeightsEndpoint:
    """Tests for the GET /api/v1/toppaper/cnn-weights endpoint."""

    def test_cnn_weights_default_contract(self, client: TestClient):
        """Verify default query parameters return expected payload structure and shapes."""
        response = client.get("/api/v1/toppaper/cnn-weights")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["total_parameters"] == EXPECTED_PARAMETER_COUNT
        assert data["total_parameters"] == 2156490
        assert data["l2_norm"] > 0.0

        # Check slices structure
        assert "slices" in data
        slices = data["slices"]
        assert len(slices["head"]) == 15
        assert len(slices["tail"]) == 15
        assert len(slices["top_magnitude"]) == 20

        # Verify Head indices and layer binding
        assert slices["head"][0]["index"] == 0
        assert slices["head"][0]["layer"] == "conv1.weight"
        assert "value" in slices["head"][0]
        assert "abs_value" in slices["head"][0]

        # Verify Tail indices and layer binding
        assert slices["tail"][-1]["index"] == 2156489
        assert slices["tail"][-1]["layer"] == "fc2.bias"

        # Verify Top magnitude sorting
        top_mag = slices["top_magnitude"]
        for i in range(len(top_mag) - 1):
            assert top_mag[i]["abs_value"] >= top_mag[i + 1]["abs_value"]

        # Check layer distribution summary
        layer_summary = data["layer_distribution_summary"]
        assert len(layer_summary) == len(CANONICAL_LAYER_ORDER)
        assert layer_summary[0]["layer"] == "conv1.weight"
        assert layer_summary[0]["count"] == 2400
        assert layer_summary[-1]["layer"] == "fc2.bias"
        assert layer_summary[-1]["count"] == 10

        # Sum of counts must equal total parameters
        total_count = sum(item["count"] for item in layer_summary)
        assert total_count == EXPECTED_PARAMETER_COUNT

    def test_cnn_weights_custom_query_params(self, client: TestClient):
        """Verify custom head, tail, and top_k query parameter filters."""
        response = client.get("/api/v1/toppaper/cnn-weights?head=8&tail=12&top_k=25")
        assert response.status_code == 200

        data = response.json()
        assert len(data["slices"]["head"]) == 8
        assert len(data["slices"]["tail"]) == 12
        assert len(data["slices"]["top_magnitude"]) == 25

    def test_cnn_weights_invalid_query_params_validation(self, client: TestClient):
        """Verify validation errors when parameters exceed constraints."""
        # head < 1
        res = client.get("/api/v1/toppaper/cnn-weights?head=0")
        assert res.status_code == 422

        # top_k > 500
        res = client.get("/api/v1/toppaper/cnn-weights?top_k=9999")
        assert res.status_code == 422


class TestTopPCNNTrainingUIPresets:
    """Tests verifying training UI HTML controls, input bindings, and preset definitions."""

    def test_training_controller_html_structure_and_presets(self):
        """Verify top_p_lab.html contains training controller input IDs, preset buttons, and handlers."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Verify exact element IDs exist in HTML
        required_input_ids = [
            'id="train-rounds"',
            'id="train-epochs"',
            'id="train-batch"',
            'id="train-lr"',
            'id="train-momentum"',
            'id="train-decay"',
            'id="train-seed"',
            'id="train-synthetic"',
            'id="btn-train-cnn"',
            'id="train-status-banner"',
        ]
        for input_id in required_input_ids:
            assert input_id in html_content, f"Missing required input ID {input_id} in top_p_lab.html"

        # Verify preset buttons in HTML
        assert "applyTrainingPreset('mock')" in html_content
        assert "applyTrainingPreset('paper')" in html_content
        assert "applyTrainingPreset('reset')" in html_content

        # Verify JS function definition and preset values
        assert "function applyTrainingPreset(type)" in html_content
        assert "Paper Default (§5.1)" in html_content

