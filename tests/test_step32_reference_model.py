"""Tests for Step 32: Reference Model Construction & Similarity Weight Alignment."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STEP32_REFERENCE_MODELS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step32_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/32 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/32")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 32
    assert data["total_steps"] >= 32
    assert len(data["nodes"]) == 10
    assert "reference_models" in data


def test_step32_exact_reference_vector_values(client):
    """Assert precomputed reference vectors match mathematical specifications."""
    res = client.get("/api/v1/storyboard/step/32")
    assert res.status_code == 200
    data = res.json()

    nodes_by_id = {n["id"]: n for n in data["nodes"]}

    # Assert Node 1 ref_vector[0] == 0.3742
    n1 = nodes_by_id[1]
    assert n1["ref_vector"][0] == 0.3742
    assert n1["status"] == "REFERENCE_MODEL_BUILT"

    # Assert Node 4 ref_vector[3] == 0.4990
    n4 = nodes_by_id[4]
    assert n4["ref_vector"][3] == 0.4990
    assert n4["status"] == "REFERENCE_MODEL_BUILT"

    # Assert Node 7 ref_vector[7] == 0.3287
    n7 = nodes_by_id[7]
    assert n7["ref_vector"][7] == 0.3287
    assert n7["status"] == "REFERENCE_MODEL_BUILT"


def test_step32_all_nodes_reference_model_built(client):
    """Assert all 10 nodes have status == 'REFERENCE_MODEL_BUILT' and normalized weights sum to ~1."""
    res = client.get("/api/v1/storyboard/step/32")
    assert res.status_code == 200
    data = res.json()

    for n in data["nodes"]:
        nid = n["id"]
        assert n["status"] == "REFERENCE_MODEL_BUILT"
        assert "ref_vector" in n
        assert len(n["ref_vector"]) == 10

        ref_info = STEP32_REFERENCE_MODELS[nid]
        assert n["ref_vector"] == ref_info["ref_vector"]

        # Verify normalized weights sum to 1.0
        alpha_sum = ref_info["alpha_self"] + sum(ref_info["partner_weights"].values())
        assert abs(alpha_sum - 1.0) < 0.001


def test_step32_post_endpoint(client):
    """Assert POST /api/v1/storyboard/step/32 returns HTTP 200."""
    res = client.post("/api/v1/storyboard/step/32")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 32
