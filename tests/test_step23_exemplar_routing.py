"""Unit and Integration Tests for Step 23: Super-Peer Query Routing & Forwarding to Target Exemplars."""

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
    assert "Super-Peer" in data["title"] or "Routing" in data["title"] or "Forwarding" in data["title"]
    assert len(data["nodes"]) == 10
    assert data["total_steps"] == 23
    assert len(data.get("packet_traces", [])) == 4


def test_step23_packet_traces_exact_paths(client):
    """Assert packet_traces length is 4 and specific paths are strictly verified."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    traces = res.json()["packet_traces"]

    assert len(traces) == 4

    trace_map = {(t["from"], t["to"]): t for t in traces}

    # 1. SP 1 -> Exemplar C9: strictly [1, 4, 7, 9]
    assert (1, 9) in trace_map
    t_1_9 = trace_map[(1, 9)]
    assert t_1_9["path"] == [1, 4, 7, 9]
    assert t_1_9["type"] == "FWD_DISCOVERY_MATCH"
    assert t_1_9["matched_cluster"] == "8-B"
    assert t_1_9["matched_peers"] == [1, 2]
    assert t_1_9["signature"] == [1, 2, 3]

    # 2. SP 5 -> Exemplar C3: strictly [5, 3]
    assert (5, 3) in trace_map
    t_5_3 = trace_map[(5, 3)]
    assert t_5_3["path"] == [5, 3]
    assert t_5_3["matched_peers"] == [4, 5, 8]
    assert t_5_3["signature"] == [4, 5, 6]

    # 3. SP 5 -> Exemplar C8: strictly [5, 6, 8]
    assert (5, 8) in trace_map
    t_5_8 = trace_map[(5, 8)]
    assert t_5_8["path"] == [5, 6, 8]
    assert t_5_8["matched_peers"] == [3, 4, 5]
    assert t_5_8["signature"] == [4, 5, 6]

    # 4. SP 10 -> Exemplar C7: strictly [10, 9, 7]
    assert (10, 7) in trace_map
    t_10_7 = trace_map[(10, 7)]
    assert t_10_7["path"] == [10, 9, 7]
    assert t_10_7["matched_peers"] == [6, 10]
    assert t_10_7["signature"] == [8, 9, 10]


def test_step23_exemplars_authorized_partners(client):
    """Assert Exemplars 3, 7, 8, 9 have populated authorized_partners."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    nodes = {n["id"]: n for n in res.json()["nodes"]}

    # Exemplar 9: status "MATCH_RECEIVED_FROM_SP1", authorized_partners [1, 2, 9]
    assert nodes[9]["status"] == "MATCH_RECEIVED_FROM_SP1"
    assert nodes[9]["authorized_partners"] == [1, 2, 9]
    assert nodes[9]["sp_authorization_inbox"]["authorizing_sp"] == 1
    assert nodes[9]["sp_authorization_inbox"]["status"] == "MATCH_RECEIVED_FROM_SP1"

    # Exemplar 3: status "MATCH_RECEIVED_FROM_SP5", authorized_partners [3, 4, 5, 8]
    assert nodes[3]["status"] == "MATCH_RECEIVED_FROM_SP5"
    assert nodes[3]["authorized_partners"] == [3, 4, 5, 8]
    assert nodes[3]["sp_authorization_inbox"]["authorizing_sp"] == 5

    # Exemplar 8: status "MATCH_RECEIVED_FROM_SP5", authorized_partners [3, 4, 5, 8]
    assert nodes[8]["status"] == "MATCH_RECEIVED_FROM_SP5"
    assert nodes[8]["authorized_partners"] == [3, 4, 5, 8]
    assert nodes[8]["sp_authorization_inbox"]["authorizing_sp"] == 5

    # Exemplar 7: status "MATCH_RECEIVED_FROM_SP10", authorized_partners [6, 7, 10]
    assert nodes[7]["status"] == "MATCH_RECEIVED_FROM_SP10"
    assert nodes[7]["authorized_partners"] == [6, 7, 10]
    assert nodes[7]["sp_authorization_inbox"]["authorizing_sp"] == 10


def test_step23_super_peer_statuses(client):
    """Assert Super-Peers (1, 5, 10) have status 'SUPER_PEER_DISPATCH_COMPLETE'."""
    res = client.get("/api/v1/storyboard/step/23")
    assert res.status_code == 200
    nodes = {n["id"]: n for n in res.json()["nodes"]}

    for sp_id in [1, 5, 10]:
        assert nodes[sp_id]["status"] == "SUPER_PEER_DISPATCH_COMPLETE"
        assert nodes[sp_id]["sp_dispatch_status"] == "SUPER_PEER_DISPATCH_COMPLETE"


def test_step23_total_steps_constant():
    """Verify TOTAL_STEPS is 23."""
    assert TOTAL_STEPS == 23

    step23 = get_10node_step_data(23)
    assert step23["total_steps"] == 23
