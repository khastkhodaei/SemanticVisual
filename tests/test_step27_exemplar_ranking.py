"""Tests for Step 27: Exemplar Similarity Ranking & Upward Dispatch to Super-Peers."""

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


def test_step27_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/27 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/27")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 27
    assert len(data["nodes"]) == 10
    assert "exemplar_ranked_packets" in data or "packets" in data


def test_step27_path_from_9_to_1_strictly_9_7_4_1(client):
    """Assert path from 9 to 1 is strictly [9, 7, 4, 1]."""
    res = client.get("/api/v1/storyboard/step/27")
    assert res.status_code == 200
    data = res.json()

    packets = data.get("exemplar_ranked_packets") or data.get("packets", [])
    pkt_9_1 = next((p for p in packets if p["from"] == 9 and p["to"] == 1), None)

    assert pkt_9_1 is not None
    assert pkt_9_1["path"] == [9, 7, 4, 1]


def test_step27_super_peers_transition_status(client):
    """Assert Super-Peers transition to status: 'EXEMPLAR_RANKINGS_INGESTED'."""
    res = client.get("/api/v1/storyboard/step/27")
    assert res.status_code == 200
    data = res.json()

    sp_ids = [1, 5, 10]
    nodes_by_id = {n["id"]: n for n in data["nodes"]}

    for sp_id in sp_ids:
        assert nodes_by_id[sp_id]["status"] == "EXEMPLAR_RANKINGS_INGESTED"
