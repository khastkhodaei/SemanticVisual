"""Tests for Step 26: Upward Similarity Score Reporting to Cluster Exemplars."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step26_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/26 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/26")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 26
    assert len(data["nodes"]) == 10
    assert "score_reporting_packets" in data or "packets" in data


def test_step26_packet_paths(client):
    """Assert packet from 6 to 7 strictly traverses path [6, 4, 7], and others match."""
    res = client.get("/api/v1/storyboard/step/26")
    assert res.status_code == 200
    data = res.json()

    packets = data.get("score_reporting_packets") or data.get("packets", [])
    packet_map = {(p["from"], p["to"]): p for p in packets}

    # C6 -> C7 must be strictly [6, 4, 7]
    assert (6, 7) in packet_map
    pkt_6_7 = packet_map[(6, 7)]
    assert pkt_6_7["path"] == [6, 4, 7]

    # C2 -> C1
    assert (2, 1) in packet_map
    assert packet_map[(2, 1)]["path"] == [2, 1]

    # C4 -> C5
    assert (4, 5) in packet_map
    assert packet_map[(4, 5)]["path"] == [4, 5]


def test_step26_exemplars_transition_status(client):
    """Assert all exemplars transition to status: 'ZONE_SCORES_INGESTED'."""
    res = client.get("/api/v1/storyboard/step/26")
    assert res.status_code == 200
    data = res.json()

    exemplar_ids = [1, 3, 5, 7, 8, 9, 10]
    nodes_by_id = {n["id"]: n for n in data["nodes"]}

    for eid in exemplar_ids:
        assert nodes_by_id[eid]["status"] == "ZONE_SCORES_INGESTED"
        assert "ingested_member_scores" in nodes_by_id[eid] or "ingested_scores" in nodes_by_id[eid]
