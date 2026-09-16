"""Tests for Step 33: Local Model Aggregation (FedAvg) & Convergence Commitment."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STEP33_AGGREGATED_MODELS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step33_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/33 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/33")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 33
    assert data["total_steps"] == 33
    assert len(data["nodes"]) == 10
    assert "aggregated_models" in data


def test_step33_post_endpoint_success(client):
    """Assert POST /api/v1/storyboard/step/33 returns HTTP 200."""
    res = client.post("/api/v1/storyboard/step/33")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 33
    assert data["total_steps"] == 33


def test_step33_all_nodes_aggregation_committed(client):
    """Assert all 10 nodes have status == 'AGGREGATION_COMMITTED'."""
    res = client.get("/api/v1/storyboard/step/33")
    assert res.status_code == 200
    data = res.json()

    for n in data["nodes"]:
        assert n["status"] == "AGGREGATION_COMMITTED"
        assert n["round"] == 1
        assert "accuracy_gain" in n
        assert n["is_converged"] is True
        assert n["model_state"] == "FEDERATED_MODEL_CONVERGED"


def test_step33_node1_exact_weights(client):
    """Assert Node 1 weights match [0.3742, 0.2419, 0.3838, ...]."""
    res = client.get("/api/v1/storyboard/step/33")
    assert res.status_code == 200
    data = res.json()

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    n1 = nodes_by_id[1]
    expected_n1_weights = [0.3742, 0.2419, 0.3838, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert n1["weights"] == expected_n1_weights
    assert n1["accuracy_gain"] == "+4.8%"


def test_step33_all_nodes_weights_match_registry(client):
    """Assert all 10 nodes match the precomputed registry weights and accuracy gains."""
    res = client.get("/api/v1/storyboard/step/33")
    assert res.status_code == 200
    data = res.json()

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    for nid, expected in STEP33_AGGREGATED_MODELS.items():
        node = nodes_by_id[nid]
        assert node["weights"] == expected["weights"]
        assert node["accuracy_gain"] == expected["accuracy_gain"]
        assert node["status"] == expected["status"]
