"""Unit and Integration Tests for Step 23: Super-Peer Semantic Query Routing to Cluster Exemplars."""

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


def test_step23_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/23 returns HTTP 200 with complete metadata."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    data = res.json()

    assert data["step"] == 23
    assert "Step 23" in data["title"]
    assert "Super-Peer" in data["title"] or "Routing" in data["title"] or "Exemplar" in data["title"]
    assert len(data["nodes"]) == 10
    assert data["total_steps"] == 23
    assert len(data.get("packet_traces", [])) == 4


def test_step23_packet_traces_exact_paths(client):
    """Assert packet_traces contains exact paths [1, 4, 7, 9], [5, 3], [5, 6, 8], and [10, 9, 7]."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    traces = res.json()["packet_traces"]

    assert len(traces) == 4
    trace_map = {(t["from"], t["to"]): t for t in traces}

    # 1. SP 1 -> Exemplar C9: strictly [1, 4, 7, 9]
    assert (1, 9) in trace_map
    t_1_9 = trace_map[(1, 9)]
    assert t_1_9["path"] == [1, 4, 7, 9]
    assert t_1_9["type"] == "FWD_QUERY_TO_EXEMPLAR"
    assert t_1_9["origin_client"] == 2
    assert t_1_9["signature"] == [1, 2, 3]
    assert t_1_9["sparse_vector"] == [0.19, 0.24, 0.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    # 2. SP 5 -> Exemplar C3: strictly [5, 3]
    assert (5, 3) in trace_map
    t_5_3 = trace_map[(5, 3)]
    assert t_5_3["path"] == [5, 3]
    assert t_5_3["type"] == "FWD_QUERY_TO_EXEMPLAR"
    assert t_5_3["origin_client"] == 4
    assert t_5_3["signature"] == [4, 5, 6]
    assert t_5_3["sparse_vector"] == [0.0, 0.0, 0.0, 0.62, 0.21, 0.17, 0.0, 0.0, 0.0, 0.0]

    # 3. SP 5 -> Exemplar C8: strictly [5, 6, 8]
    assert (5, 8) in trace_map
    t_5_8 = trace_map[(5, 8)]
    assert t_5_8["path"] == [5, 6, 8]
    assert t_5_8["type"] == "FWD_QUERY_TO_EXEMPLAR"
    assert t_5_8["origin_client"] == 3
    assert t_5_8["signature"] == [4, 5, 6]
    assert t_5_8["sparse_vector"] == [0.0, 0.0, 0.0, 0.34, 0.20, 0.46, 0.0, 0.0, 0.0, 0.0]

    # 4. SP 10 -> Exemplar C7: strictly [10, 9, 7]
    assert (10, 7) in trace_map
    t_10_7 = trace_map[(10, 7)]
    assert t_10_7["path"] == [10, 9, 7]
    assert t_10_7["type"] == "FWD_QUERY_TO_EXEMPLAR"
    assert t_10_7["origin_client"] == 6
    assert t_10_7["signature"] == [7, 9, 10]
    assert t_10_7["sparse_vector"] == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.23, 0.0, 0.34, 0.24]


def test_step23_exemplar_inboxes_non_empty(client):
    """Assert Exemplars 1, 3, 5, 7, 8, 9, 10 all have non-empty exemplar_inboxes."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    data = res.json()

    exemplar_inboxes = data.get("exemplar_inboxes", {})
    # Check top-level exemplar_inboxes
    for ex_id in [1, 3, 5, 7, 8, 9, 10]:
        inbox = exemplar_inboxes.get(str(ex_id)) or exemplar_inboxes.get(ex_id)
        assert inbox is not None and len(inbox) > 0, f"Exemplar {ex_id} has empty top-level inbox"

    # Check node level exemplar_inbox
    nodes = {n["id"]: n for n in data["nodes"]}
    for ex_id in [1, 3, 5, 7, 8, 9, 10]:
        node = nodes[ex_id]
        assert node.get("is_exemplar") is True
        assert "exemplar_inbox" in node
        assert len(node["exemplar_inbox"]) > 0


def test_step23_dual_role_nodes(client):
    """Assert dual-role nodes 1, 5, 10 have both Super-Peer and Exemplar attributes."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    nodes = {n["id"]: n for n in res.json()["nodes"]}

    for sp_id in [1, 5, 10]:
        node = nodes[sp_id]
        assert node["is_super_peer"] is True
        assert node["is_exemplar"] is True
        assert node["status"] == "SUPER_PEER_DISPATCH_COMPLETE"
        assert len(node["exemplar_inbox"]) > 0
        assert len(node.get("sp_dispatches", [])) > 0


def test_step23_total_steps_constant():
    """Verify TOTAL_STEPS is 23."""
    assert TOTAL_STEPS == 23

    step23 = get_10node_step_data(23)
    assert step23["total_steps"] == 23
