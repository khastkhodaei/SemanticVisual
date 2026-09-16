"""Tests for Step 31: Sparse Parameter Delivery & Local Buffer Ingestion (REP_MODEL_WEIGHTS)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STORYBOARD_10_ADJACENCY,
    STEP31_MODEL_RESPONSE_PACKETS,
    STEP31_NODE_BUFFERS,
    STEP31_SPARSE_VECTORS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step31_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/31 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/31")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 31
    assert data["total_steps"] >= 31
    assert len(data["nodes"]) == 10
    assert "model_response_packets" in data or "packets" in data
    assert "node_buffers" in data


def test_step31_twenty_packets_valid_physical_links(client):
    """Assert all 20 packets strictly use valid physical links."""
    res = client.get("/api/v1/storyboard/step/31")
    assert res.status_code == 200
    data = res.json()

    packets = data.get("model_response_packets") or data.get("packets")
    assert packets is not None
    assert len(packets) == 20

    for pkt in packets:
        assert pkt["type"] == "REP_MODEL_WEIGHTS"
        assert pkt["bytes"] == 15
        assert len(pkt["sparse_vector"]) == 10
        path = pkt["path"]
        assert len(path) >= 2, f"Path {path} too short"
        assert path[0] == pkt["from"], f"Path start {path[0]} != sender {pkt['from']}"
        assert path[-1] == pkt["to"], f"Path end {path[-1]} != receiver {pkt['to']}"

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            assert v in STORYBOARD_10_ADJACENCY[u], f"Edge ({u}, {v}) not in physical adjacency list"
            assert u in STORYBOARD_10_ADJACENCY[v], f"Edge ({v}, {u}) not in physical adjacency list"


def test_step31_each_node_has_two_partner_vectors_in_buffer(client):
    """Assert each node has exactly 2 ingested partner vectors in its memory buffer."""
    res = client.get("/api/v1/storyboard/step/31")
    assert res.status_code == 200
    data = res.json()

    nodes = data["nodes"]
    assert len(nodes) == 10

    for n in nodes:
        nid = n["id"]
        assert n["status"] == "LOCAL_BUFFER_INGESTED", f"Node {nid} has unexpected status {n['status']}"
        assert n["buffer_status"] == "BUFFER_READY_FOR_ALIGNMENT"

        buf = n.get("memory_buffer") or n.get("ingested_buffer")
        assert buf is not None, f"Node {nid} has missing memory buffer"

        partner_vectors = buf.get("partner_vectors", [])
        assert len(partner_vectors) == 2, f"Node {nid} has {len(partner_vectors)} partner vectors, expected 2"

        # Check self model is also present in buffer
        assert "self_model" in buf
        assert buf["self_model"]["node_id"] == nid
        assert len(buf["self_model"]["sparse_vector"]) == 10

        # Check 10D non-zero floats
        p1 = partner_vectors[0]
        p2 = partner_vectors[1]
        assert len(p1["sparse_vector"]) == 10
        assert len(p2["sparse_vector"]) == 10
        assert p1["bytes"] == 15
        assert p2["bytes"] == 15


def test_step31_post_endpoint(client):
    """Assert POST /api/v1/storyboard/step/31 returns HTTP 200."""
    res = client.post("/api/v1/storyboard/step/31")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 31
