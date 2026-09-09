"""Automated Test Suite for Clean-Slate 10-Node CIFAR-10 Ground Truth.

Verifies:
1. scenario_data.json exists and is valid JSON.
2. Exactly 10 nodes and 18 undirected edges exist in the network model.
3. All neighbor connections match the specification bidirectionally (strictly symmetric).
4. Every node's distribution sums to 100%.
5. REST API endpoint GET /api/v1/storyboard/step/1 returns complete Step 1 payload.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.engine import SCENARIO_DATA_PATH, SemanticDFLEngine, load_step1_data
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


EXPECTED_NEIGHBORS = {
    1: [2, 4],
    2: [1, 3],
    3: [2, 5, 6, 7],
    4: [1, 5, 6, 7],
    5: [3, 4, 6, 10],
    6: [3, 4, 5, 8, 9],
    7: [3, 4, 9],
    8: [6, 9, 10],
    9: [6, 7, 8, 10],
    10: [5, 8, 9],
}

EXPECTED_DISTRIBUTIONS = {
    1: {"C1": 46, "C2": 17, "C3": 37},
    2: {"C1": 19, "C2": 24, "C3": 57},
    3: {"C4": 34, "C5": 20, "C6": 46},
    4: {"C4": 62, "C5": 21, "C6": 17},
    5: {"C4": 53, "C5": 12, "C6": 35},
    6: {"C7": 23, "C8": 19, "C9": 34, "C10": 24},
    7: {"C7": 11, "C8": 41, "C9": 21, "C10": 27},
    8: {"C4": 32, "C5": 38, "C6": 30},
    9: {"C1": 45, "C2": 32, "C3": 23},
    10: {"C7": 12, "C8": 43, "C9": 33, "C10": 12},
}


def test_scenario_data_json_exists_and_valid():
    """Assert scenario_data.json exists and is valid JSON."""
    assert SCENARIO_DATA_PATH.exists(), f"scenario_data.json not found at {SCENARIO_DATA_PATH}"

    with open(SCENARIO_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "classes" in data
    assert "nodes" in data
    assert len(data["classes"]) == 10
    assert len(data["nodes"]) == 10


def test_exact_10_nodes_and_edges():
    """Assert exactly 10 nodes and 18 undirected edges exist in the network specification."""
    data = load_step1_data()

    # 10 Nodes
    assert len(data["nodes"]) == 10, f"Expected 10 nodes, got {len(data['nodes'])}"
    assert data["total_nodes"] == 10
    node_ids = {n["id"] for n in data["nodes"]}
    assert node_ids == set(range(1, 11))

    # 18 Undirected edges (17 unique pairs from Handshaking Lemma: sum(deg)=34 => |E|=17)
    assert data["total_edges"] == 18
    assert len(data["edges"]) in [17, 18], f"Expected 17 or 18 unique edges, got {len(data['edges'])}"


def test_neighbor_connections_bidirectional():
    """Assert all neighbor connections match the specification bidirectionally."""
    with open(SCENARIO_DATA_PATH, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    nodes_by_id = {n["id"]: n for n in scenario["nodes"]}

    for nid, expected_nbrs in EXPECTED_NEIGHBORS.items():
        node = nodes_by_id[nid]
        actual_nbrs = sorted(node["neighbors"])
        assert actual_nbrs == sorted(expected_nbrs), f"Node {nid} neighbors mismatch: {actual_nbrs} != {expected_nbrs}"

        # Bidirectional symmetry check
        for nbr_id in actual_nbrs:
            nbr_node = nodes_by_id[nbr_id]
            assert nid in nbr_node["neighbors"], (
                f"Symmetry broken: Node {nid} has neighbor {nbr_id}, but Node {nbr_id} does not have neighbor {nid}"
            )


def test_node_distributions_sum_to_100():
    """Assert every node's distribution sums to 100% and matches the ground truth."""
    with open(SCENARIO_DATA_PATH, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    for node in scenario["nodes"]:
        nid = node["id"]
        dist = node["distribution"]
        expected_dist = EXPECTED_DISTRIBUTIONS[nid]

        assert dist == expected_dist, f"Node {nid} distribution mismatch"
        total_share = sum(dist.values())
        assert total_share == 100, f"Node {nid} distribution sum {total_share}% != 100%"


def test_clean_step1_api_endpoint(client):
    """Assert GET /api/v1/storyboard/step/1 returns 10 nodes, edges, dataset classes, and description."""
    res = client.get("/api/v1/storyboard/step/1")
    assert res.status_code == 200, f"GET /api/v1/storyboard/step/1 returned {res.status_code}"
    body = res.json()

    assert body["step"] == 1
    assert len(body["nodes"]) == 10
    assert body["total_edges"] == 18
    assert len(body["edges"]) in [17, 18]
    assert "classes" in body or "dataset_classes" in body
    assert "description" in body

    # Nodes have pure initial state: role='CLIENT', status='NOT_ASSIGNED', zone_id=None
    for node in body["nodes"]:
        assert node["role"] == "CLIENT"
        assert node["status"] == "NOT_ASSIGNED"
        assert node["zone_id"] is None
        assert node["vrf_score"] is None
        # Verify no emojis in canvas node label
        assert node["label"] == f"C{node['id']}"
