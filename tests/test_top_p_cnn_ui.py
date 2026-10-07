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



    def test_paper_preset_exact_values_match_spec(self):
        """Verify Paper §5.1 preset values match the spec exactly (tracer-bullet contract)."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Extract only the applyTrainingPreset function block for targeted assertions
        fn_start = html_content.find("function applyTrainingPreset(type)")
        fn_end = html_content.find("async function startCnnTraining", fn_start)
        assert fn_start != -1, "applyTrainingPreset function not found"
        fn_body = html_content[fn_start:fn_end]

        # Locate the 'paper' branch
        paper_start = fn_body.find("type === 'paper'")
        assert paper_start != -1, "'paper' branch missing in applyTrainingPreset"
        paper_branch = fn_body[paper_start : fn_body.find("} else", paper_start)]

        # Spec §5.1: rounds=3, epochs=1, batch_size=64, lr=0.01, momentum=0.9,
        #            weight_decay=0.0001, seed=42, synthetic=false
        assert ".value = 3" in paper_branch, "Paper preset rounds must be 3 (§5.1)"
        assert ".value = 1" in paper_branch, "Paper preset epochs must be 1 (§5.1)"
        assert ".value = 64" in paper_branch, "Paper preset batch_size must be 64 (§5.1)"
        assert ".value = 0.01" in paper_branch, "Paper preset lr must be 0.01 (§5.1)"
        assert ".value = 0.9" in paper_branch, "Paper preset momentum must be 0.9 (§5.1)"
        assert ".value = 0.0001" in paper_branch, "Paper preset weight_decay must be 0.0001 (§5.1)"
        assert ".value = 42" in paper_branch, "Paper preset seed must be 42 (§5.1)"
        assert ".value = 'false'" in paper_branch, "Paper preset synthetic must be 'false' (§5.1 uses real CIFAR-10)"

    def test_mock_preset_exact_values(self):
        """Verify Quick Mock preset sets synthetic=true and rounds=1."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        fn_start = html_content.find("function applyTrainingPreset(type)")
        fn_end = html_content.find("async function startCnnTraining", fn_start)
        fn_body = html_content[fn_start:fn_end]

        mock_start = fn_body.find("type === 'mock'")
        assert mock_start != -1, "'mock' branch missing in applyTrainingPreset"
        # The mock branch ends at the 'else if' for paper
        mock_branch = fn_body[mock_start : fn_body.find("} else if", mock_start)]

        assert ".value = 1" in mock_branch, "Mock preset rounds must be 1"
        assert ".value = 'true'" in mock_branch, "Mock preset synthetic must be 'true' (fast path)"

    def test_form_input_field_attributes(self):
        """Verify min/max/step/default attributes on every training form field to prevent field-shifting."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Each tuple: (field_id, attribute_snippet) that MUST appear in the HTML
        required_attrs = [
            ('train-rounds',   'min="1"'),
            ('train-rounds',   'max="200"'),
            ('train-rounds',   'value="1"'),
            ('train-epochs',   'min="1"'),
            ('train-epochs',   'max="100"'),
            ('train-batch',    'min="8"'),
            ('train-batch',    'max="512"'),
            ('train-batch',    'value="64"'),
            ('train-lr',       'step="0.005"'),
            ('train-lr',       'min="0.0001"'),
            ('train-lr',       'max="1.0"'),
            ('train-momentum', 'step="0.05"'),
            ('train-momentum', 'min="0.0"'),
            ('train-momentum', 'max="0.99"'),
            ('train-decay',    'step="0.0001"'),
            ('train-decay',    'min="0.0"'),
            ('train-decay',    'max="0.1"'),
            ('train-seed',     'value="42"'),
        ]

        for field_id, attr in required_attrs:
            # Find the specific input element by ID and check that attribute is present nearby
            id_pos = html_content.find(f'id="{field_id}"')
            assert id_pos != -1, f'id="{field_id}" not found in HTML'
            # Check within a 300-char window around the ID declaration
            snippet = html_content[max(0, id_pos - 50) : id_pos + 300]
            assert attr in snippet, (
                f'Field id="{field_id}" missing attribute {attr!r}. '
                f'Snippet: {snippet!r}'
            )

    def test_top_magnitude_panel_redundancy_cleanup(self):
        """Verify the redundant static top magnitude panel, badge, tbody, and button are removed from Tab 2."""
        html_path = "frontend/static/top_p_lab.html"
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        assert 'id="cnn-sec-topmagnitude"' not in html_content
        assert 'id="cnn-filter-top"' not in html_content
        assert 'id="cnn-top-tbody"' not in html_content
        assert 'id="cnn-top-badge"' not in html_content
        assert "All Slices (Head + Tail)" in html_content
        assert "All Slices (Head + Tail + Top-K)" not in html_content

