"""Unit and Integration Tests for Step 24: Cluster Exemplar Forwarding to Leaf Members (Tier 2 -> Tier 1)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STORYBOARD_10_ADJACENCY,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step24_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/24 returns HTTP 200 with complete metadata."""
    res = client.get("/api/v1/storyboard/step/24")
    assert res.status_code == 200
    data = res.json()

    assert data["step"] == 24
    assert "Step 24" in data["title"]
    assert "Leaf" in data["title"] or "Exemplar" in data["title"] or "Forwarding" in data["title"]
    assert len(data["nodes"]) == 10
    assert data["total_steps"] == 24
    assert len(data.get("leaf_packet_traces", [])) == 3


def test_step24_leaf_packet_traces_exact_paths(client):
    """Assert leaf_packet_traces contains exact paths [1, 2], [5, 4], and [7, 4, 6]."""
    res = client.get("/api/v1/storyboard/step/24")
    assert res.status_code == 200
    traces = res.json()["leaf_packet_traces"]

    assert len(traces) == 3
    trace_map = {(t["from"], t["to"]): t for t in traces}

    # 1. Exemplar C1 -> Leaf C2: strictly [1, 2]
    assert (1, 2) in trace_map
    t_1_2 = trace_map[(1, 2)]
    assert t_1_2["path"] == [1, 2]
    assert t_1_2["type"] == "FWD_QUERY_TO_LEAF"
    assert t_1_2["origin_client"] == 9
    assert t_1_2["signature"] == [1, 2, 3]
    assert t_1_2["authorized_peers"] == [1, 9]
    assert t_1_2["label"] == "LEAF_DISPATCH (C1 -> C2)"

    # 2. Exemplar C5 -> Leaf C4: strictly [5, 4]
    assert (5, 4) in trace_map
    t_5_4 = trace_map[(5, 4)]
    assert t_5_4["path"] == [5, 4]
    assert t_5_4["type"] == "FWD_QUERY_TO_LEAF"
    assert t_5_4["origin_client"] == 3
    assert t_5_4["signature"] == [4, 5, 6]
    assert t_5_4["authorized_peers"] == [3, 5, 8]
    assert t_5_4["label"] == "LEAF_DISPATCH (C5 -> C4)"

    # 3. Exemplar C7 -> Leaf C6: strictly [7, 4, 6] traversing gateway node 4
    assert (7, 6) in trace_map
    t_7_6 = trace_map[(7, 6)]
    assert t_7_6["path"] == [7, 4, 6]
    assert t_7_6["path"][1] == 4, "Route from 7 to 6 must strictly traverse gateway node 4"
    assert t_7_6["type"] == "FWD_QUERY_TO_LEAF"
    assert t_7_6["origin_client"] == 10
    assert t_7_6["signature"] == [8, 9, 10]
    assert t_7_6["authorized_peers"] == [7, 10]
    assert t_7_6["label"] == "LEAF_DISPATCH (C7 -> C6)"


def test_step24_leaf_inboxes_non_empty(client):
    """Assert Leaf nodes 2, 4, 6 have non-empty leaf_inboxes."""
    res = client.get("/api/v1/storyboard/step/24")
    assert res.status_code == 200
    data = res.json()

    leaf_inboxes = data.get("leaf_inboxes", {})
    for leaf_id in [2, 4, 6]:
        inbox = leaf_inboxes.get(str(leaf_id)) or leaf_inboxes.get(leaf_id)
        assert inbox is not None and len(inbox) > 0, f"Leaf {leaf_id} has empty top-level leaf_inbox"

    # Check node level leaf_inbox and status FEDERATION_CLUSTER_LOCKED
    nodes = {n["id"]: n for n in data["nodes"]}
    for leaf_id in [2, 4, 6]:
        node = nodes[leaf_id]
        assert node.get("is_leaf") is True
        assert "leaf_inbox" in node
        assert len(node["leaf_inbox"]) > 0
        assert node["status"] == "FEDERATION_CLUSTER_LOCKED"

    # Check specific delivered models
    node2_peers = [item["from_peer"] for item in nodes[2]["leaf_inbox"]]
    assert 1 in node2_peers and 9 in node2_peers

    node4_peers = [item["from_peer"] for item in nodes[4]["leaf_inbox"]]
    assert 3 in node4_peers and 5 in node4_peers and 8 in node4_peers

    node6_peers = [item["from_peer"] for item in nodes[6]["leaf_inbox"]]
    assert 7 in node6_peers and 10 in node6_peers


def test_step24_total_steps_constant():
    """Verify TOTAL_STEPS is 24."""
    assert TOTAL_STEPS == 24

    step24 = get_10node_step_data(24)
    assert step24["total_steps"] == 24
