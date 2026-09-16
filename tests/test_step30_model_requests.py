"""Tests for Step 30: Pull-Based P2P Model Request Dispatch (REQ_MODEL_WEIGHTS)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STORYBOARD_10_ADJACENCY,
    STEP30_P2P_MODEL_REQUESTS,
    STEP30_NODE_OUTBOUND_REQUESTS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step30_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/30 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/30")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 30
    assert data["total_steps"] >= 30
    assert len(data["nodes"]) == 10
    assert "p2p_model_requests" in data or "packets" in data
    assert "outbound_requests" in data


def test_step30_twenty_request_traces(client):
    """Assert p2p_model_requests contains exactly 20 request traces (2 per node)."""
    res = client.get("/api/v1/storyboard/step/30")
    assert res.status_code == 200
    data = res.json()

    requests = data.get("p2p_model_requests") or data.get("packets")
    assert requests is not None
    assert len(requests) == 20

    # Verify each node (1 to 10) emitted exactly 2 requests
    requests_by_sender = {}
    for req in requests:
        assert req["type"] == "REQ_MODEL_WEIGHTS"
        sender = req["from"]
        requests_by_sender.setdefault(sender, []).append(req)

    for nid in range(1, 11):
        assert nid in requests_by_sender, f"Node {nid} has not emitted requests"
        assert len(requests_by_sender[nid]) == 2, f"Node {nid} emitted {len(requests_by_sender[nid])} requests, expected 2"


def test_step30_physical_paths_validity(client):
    """Assert all 20 request paths are strictly valid on Step 1 physical graph."""
    res = client.get("/api/v1/storyboard/step/30")
    assert res.status_code == 200
    data = res.json()

    requests = data.get("p2p_model_requests") or data.get("packets")
    for req in requests:
        path = req["path"]
        assert len(path) >= 2, f"Path {path} is too short"
        assert path[0] == req["from"], f"Path start {path[0]} does not match sender {req['from']}"
        assert path[-1] == req["to"], f"Path end {path[-1]} does not match target {req['to']}"
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            assert v in STORYBOARD_10_ADJACENCY[u], f"Edge ({u}, {v}) not in physical adjacency list"
            assert u in STORYBOARD_10_ADJACENCY[v], f"Edge ({v}, {u}) not in physical adjacency list"


def test_step30_all_nodes_dispatched_status(client):
    """Assert all 10 nodes have status == 'DISPATCHED_MODEL_REQUESTS'."""
    res = client.get("/api/v1/storyboard/step/30")
    assert res.status_code == 200
    data = res.json()

    nodes = data["nodes"]
    assert len(nodes) == 10

    for n in nodes:
        nid = n["id"]
        assert n["status"] == "DISPATCHED_MODEL_REQUESTS", f"Node {nid} status is {n['status']}"
        assert "outbound_requests" in n
        assert len(n["outbound_requests"]) == 2
