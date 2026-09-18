"""Automated Regression Test Suite for Step 1: 10-Node CIFAR-10 Storyboard Topology.

Verifies Issue #17 requirements:
1. Enforces strict 10-node CIFAR-10 topology across the engine and REST API.
2. Automated regression test confirms len(response.json()["nodes"]) == 10 on Step 1 endpoint.
3. Automated regression test confirms default /api/v1/init produces exactly 10 nodes.
4. Physical edges and Non-IID local data distributions match STEPS.md ground truth.
"""

import pytest
from fastapi.testclient import TestClient

from backend.config import CANONICAL_EDGES, NODE_DATA_DISTRIBUTIONS, TOTAL_NODES
from backend.engine import SemanticDFLEngine, load_step1_data
from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    get_10node_config,
    get_10node_edges,
    get_10node_nodes,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step1_endpoint_returns_exact_10_nodes(client):
    """Confirm len(response.json()['nodes']) == 10 on Step 1 endpoint."""
    response = client.get("/api/v1/storyboard/step/1")
    assert response.status_code == 200
    data = response.json()

    assert "nodes" in data
    # Acceptance criterion: len(response.json()["nodes"]) == 10
    assert len(response.json()["nodes"]) == 10

    node_ids = {node["id"] for node in data["nodes"]}
    assert node_ids == set(range(1, 11))

    for node in data["nodes"]:
        assert node["role"] == "CLIENT"
        assert node["status"] == "NOT_ASSIGNED"
        assert node["zone_id"] is None
        assert node["vrf_score"] is None
        assert node["label"] == f"C{node['id']}"
        assert node["coords"]["x"] is not None
        assert node["coords"]["y"] is not None


def test_simulation_init_defaults_to_10_nodes(client):
    """Confirm POST /api/v1/init with empty payload defaults to 10 nodes instead of 50."""
    response = client.post("/api/v1/init", json={})
    assert response.status_code == 200
    data = response.json()

    assert "nodes" in data
    assert len(response.json()["nodes"]) == 10
    assert data["metadata"]["num_nodes"] == 10


def test_storyboard_nodes_and_config_endpoints(client):
    """Confirm /api/v1/storyboard/nodes and /config return 10 nodes."""
    nodes_resp = client.get("/api/v1/storyboard/nodes")
    assert nodes_resp.status_code == 200
    assert len(nodes_resp.json()["nodes"]) == 10
    assert nodes_resp.json()["total_nodes"] == 10

    config_resp = client.get("/api/v1/storyboard/config")
    assert config_resp.status_code == 200
    assert config_resp.json()["num_nodes"] == 10


def test_canonical_edges_and_data_distributions_match_steps_md():
    """Confirm CANONICAL_EDGES and NODE_DATA_DISTRIBUTIONS match STEPS.md specification."""
    assert TOTAL_NODES == 10

    expected_canonical_edges = {
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

    assert CANONICAL_EDGES == expected_canonical_edges

    # Check bidirectional symmetry
    for u, nbrs in CANONICAL_EDGES.items():
        for v in nbrs:
            assert u in CANONICAL_EDGES[v], f"Symmetry broken between {u} and {v}"

    expected_distributions = {
        1: {"C1": 0.46, "C2": 0.17, "C3": 0.37},
        2: {"C1": 0.19, "C2": 0.24, "C3": 0.57},
        3: {"C4": 0.34, "C5": 0.20, "C6": 0.46},
        4: {"C4": 0.62, "C5": 0.21, "C6": 0.17},
        5: {"C4": 0.53, "C5": 0.12, "C6": 0.35},
        6: {"C7": 0.23, "C8": 0.19, "C9": 0.34, "C10": 0.24},
        7: {"C7": 0.11, "C8": 0.41, "C9": 0.21, "C10": 0.27},
        8: {"C4": 0.32, "C5": 0.38, "C6": 0.30},
        9: {"C1": 0.45, "C2": 0.32, "C3": 0.23},
        10: {"C7": 0.12, "C8": 0.43, "C9": 0.33, "C10": 0.12},
    }

    assert NODE_DATA_DISTRIBUTIONS == expected_distributions

    for nid, dist in NODE_DATA_DISTRIBUTIONS.items():
        total = round(sum(dist.values()), 4)
        assert total == 1.0, f"Node {nid} distribution sum is {total}, expected 1.0"


def test_engine_generate_topology_and_step1():
    """Confirm SemanticDFLEngine methods generate 10-node topology."""
    engine = SemanticDFLEngine()

    step1 = engine.generate_storyboard_step1()
    assert len(step1["nodes"]) == 10
    assert step1["step"] == 1

    topo_default = engine.generate_topology(benchmark="Non-IID 10-Class Storyboard")
    assert len(topo_default["nodes"]) == 10
    assert topo_default["metadata"]["num_nodes"] == 10

    topo_10 = engine.generate_topology(N=10, benchmark="Non-IID 10-Class Storyboard")
    assert len(topo_10["nodes"]) == 10
    assert topo_10["metadata"]["num_nodes"] == 10

    topo_direct = engine.get_10node_topology()
    assert len(topo_direct["nodes"]) == 10
