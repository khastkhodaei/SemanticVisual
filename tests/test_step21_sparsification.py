"""Unit and Integration Tests for Step 21: Local Model Parameter Pruning & Sparse Weight Extraction (P = 3)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import get_10node_step_data, TOTAL_STEPS


@pytest.fixture
def client():
    return TestClient(app)


def test_step21_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/21 returns HTTP 200 with complete metadata."""
    res = client.get("/api/v1/storyboard/step/21")
    assert res.status_code == 200
    data = res.json()

    assert data["step"] == 21
    assert "Step 21" in data["title"]
    assert "P = 3" in data["title"]
    assert data["bandwidth_savings"] == "62.5%"
    assert data["sparsification_p"] == 3
    assert data["raw_payload_bytes"] == 40
    assert data["sparse_payload_bytes"] == 15
    assert len(data["nodes"]) == 10
    assert data["total_steps"] == 21


def test_step21_all_nodes_exactly_three_sparse_weights(client):
    """Assert every client has exactly 3 non-zero weights in sparse_weights."""
    res = client.get("/api/v1/storyboard/step/21")
    assert res.status_code == 200
    nodes = res.json()["nodes"]

    for n in nodes:
        sparse_w = n.get("sparse_weights")
        assert sparse_w is not None
        assert len(sparse_w) == 10

        non_zero = [w for w in sparse_w if abs(w) > 1e-6]
        assert len(non_zero) == 3, f"Node {n['id']} does not have exactly 3 non-zero weights: {sparse_w}"
        assert len(n["active_indices"]) == 3
        assert n["status"] == "LOCAL_SPARSE_MODEL_READY"
        assert n["raw_bytes"] == 40
        assert n["sparse_bytes"] == 15
        assert n["bandwidth_savings"] == "62.5%"


def test_step21_multi_class_pruning_nodes_6_7_10(client):
    """Assert nodes 6, 7, and 10 correctly prune non-top-3 weights to 0.0."""
    res = client.get("/api/v1/storyboard/step/21")
    assert res.status_code == 200
    node_map = {n["id"]: n for n in res.json()["nodes"]}

    # Node 6: raw had class 8 (0.19), class 7 (0.23), class 9 (0.34), class 10 (0.24)
    # Pruned class 8 (index 7 in 0-based array) strictly to 0.0
    n6 = node_map[6]
    assert n6["sparse_weights"][7] == 0.0  # index 8 in 1-based is index 7 in 0-based
    assert n6["sparse_weights"][6] == 0.23  # class 7
    assert n6["sparse_weights"][8] == 0.34  # class 9
    assert n6["sparse_weights"][9] == 0.24  # class 10
    assert n6["active_indices"] == [7, 9, 10]
    assert 8 in n6["pruned_indices"]

    # Node 7: raw had class 7 (0.11), class 8 (0.41), class 9 (0.21), class 10 (0.27)
    # Pruned class 7 (index 6 in 0-based array) strictly to 0.0
    n7 = node_map[7]
    assert n7["sparse_weights"][6] == 0.0  # class 7 pruned
    assert n7["sparse_weights"][7] == 0.41  # class 8
    assert n7["sparse_weights"][8] == 0.21  # class 9
    assert n7["sparse_weights"][9] == 0.27  # class 10
    assert n7["active_indices"] == [8, 9, 10]
    assert 7 in n7["pruned_indices"]

    # Node 10: raw had class 7 (0.12), class 8 (0.43), class 9 (0.33), class 10 (0.12)
    # Pruned class 7 (index 6 in 0-based array) strictly to 0.0
    n10 = node_map[10]
    assert n10["sparse_weights"][6] == 0.0  # class 7 pruned
    assert n10["sparse_weights"][7] == 0.43  # class 8
    assert n10["sparse_weights"][8] == 0.33  # class 9
    assert n10["sparse_weights"][9] == 0.12  # class 10
    assert n10["active_indices"] == [8, 9, 10]
    assert 7 in n10["pruned_indices"]


def test_step21_total_steps_constant():
    """Verify TOTAL_STEPS is 21."""
    assert TOTAL_STEPS == 21
    step21 = get_10node_step_data(21)
    assert step21["total_steps"] == 21
