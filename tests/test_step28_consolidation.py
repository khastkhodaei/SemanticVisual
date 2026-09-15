"""Tests for Step 28: Global Super-Peer Cross-Cluster Similarity Consolidation."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    super_peer_consolidated_rankings,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step28_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/28 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/28")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 28
    assert len(data["nodes"]) == 10
    assert "super_peer_consolidated_rankings" in data or "consolidated_rankings" in data


def test_step28_sp5_rankings(client):
    """Assert SP 5 lists Node 4 as rank 1 for Q5 with score 0.9453."""
    res = client.get("/api/v1/storyboard/step/28")
    assert res.status_code == 200
    data = res.json()

    rankings = data.get("super_peer_consolidated_rankings") or data.get("consolidated_rankings")
    sp5 = rankings.get("5") or rankings.get(5)
    assert sp5 is not None
    q5_ranks = sp5["Q5"]
    assert q5_ranks[0]["peer"] == 4
    assert q5_ranks[0]["rank"] == 1
    assert q5_ranks[0]["sim"] == 0.9453


def test_step28_sp10_rankings(client):
    """Assert SP 10 lists Node 10 as rank 1 for Q7 with score 0.9378."""
    res = client.get("/api/v1/storyboard/step/28")
    assert res.status_code == 200
    data = res.json()

    rankings = data.get("super_peer_consolidated_rankings") or data.get("consolidated_rankings")
    sp10 = rankings.get("10") or rankings.get(10)
    assert sp10 is not None
    q7_ranks = sp10["Q7"]
    assert q7_ranks[0]["peer"] == 10
    assert q7_ranks[0]["rank"] == 1
    assert q7_ranks[0]["sim"] == 0.9378


def test_step28_super_peers_matchmaking_locked(client):
    """Assert Super-Peers transition to status: 'GLOBAL_MATCHMAKING_LOCKED'."""
    res = client.get("/api/v1/storyboard/step/28")
    assert res.status_code == 200
    data = res.json()

    sp_ids = [1, 5, 10]
    nodes_by_id = {n["id"]: n for n in data["nodes"]}

    for sp_id in sp_ids:
        assert nodes_by_id[sp_id]["status"] == "GLOBAL_MATCHMAKING_LOCKED"
        assert nodes_by_id[sp_id]["is_matchmaking_locked"] is True
