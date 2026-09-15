"""Tests for Step 25: Local Semantic Cosine Similarity Evaluation."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    node_similarity_evaluations,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step25_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/25 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/25")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 25
    assert len(data["nodes"]) == 10
    assert "node_similarity_evaluations" in data or "similarity_evaluations" in data


def test_step25_node1_cosine_similarities(client):
    """Assert Node 1 shows cosine_sim == 0.9429 for Node 9 and 0.8531 for Node 2."""
    res = client.get("/api/v1/storyboard/step/25")
    assert res.status_code == 200
    data = res.json()

    # Find Node 1
    node1 = next(n for n in data["nodes"] if n["id"] == 1)
    sims = node1.get("similarity_evaluations") or node1.get("cosine_similarities")
    sim_map = {item["peer"]: item["cosine_sim"] for item in sims}

    assert sim_map[9] == 0.9429
    assert sim_map[2] == 0.8531


def test_step25_node7_cosine_similarities(client):
    """Assert Node 7 shows cosine_sim == 0.9378 for Node 10."""
    res = client.get("/api/v1/storyboard/step/25")
    assert res.status_code == 200
    data = res.json()

    node7 = next(n for n in data["nodes"] if n["id"] == 7)
    sims = node7.get("similarity_evaluations") or node7.get("cosine_similarities")
    sim_map = {item["peer"]: item["cosine_sim"] for item in sims}

    assert sim_map[10] == 0.9378


def test_step25_all_nodes_evaluated_status(client):
    """Assert all nodes transition to status: 'LOCAL_SIMILARITY_EVALUATED'."""
    res = client.get("/api/v1/storyboard/step/25")
    assert res.status_code == 200
    data = res.json()

    for n in data["nodes"]:
        assert n["status"] == "LOCAL_SIMILARITY_EVALUATED"
