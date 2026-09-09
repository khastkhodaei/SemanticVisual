"""Test suite for Step 3: Local VRF Generation & 1-Hop Neighbor Score Exchange.

Verifies:
1. All 10 nodes generate exact deterministic VRF scores according to the specification table.
2. For each node, 1-hop neighbor scores match the exact physical links (18 links).
3. No node is marked as INITIATOR in Step 3 (role remains CLIENT, status remains NOT_ASSIGNED).
4. GET and POST /api/v1/storyboard/step/3 endpoints return valid Step 3 payloads with packet exchanges.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_VRF_SCORES,
    STORYBOARD_10_ADJACENCY,
    get_10node_step_data,
)


EXPECTED_VRF_SCORES = {
    1: 0.1543,
    2: 0.0837,
    3: 0.2318,
    4: 0.0412,
    5: 0.3185,
    6: 0.4721,
    7: 0.3564,
    8: 0.0275,
    9: 0.2947,
    10: 0.4126,
}


@pytest.fixture
def client():
    return TestClient(app)


def test_scenario_data_json_vrf_scores():
    """Verify backend/scenario_data.json stores the exact VRF score for all 10 nodes."""
    scenario_path = Path(__file__).resolve().parent.parent / "backend" / "scenario_data.json"
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    assert len(nodes) == 10
    for n in nodes:
        nid = n["id"]
        assert "vrf_score" in n, f"Node {nid} missing vrf_score in scenario_data.json"
        assert n["vrf_score"] == EXPECTED_VRF_SCORES[nid]


def test_storyboard_step3_data_exact_vrf_scores():
    """Verify get_10node_step_data(3) returns exact VRF scores for all 10 nodes."""
    data = get_10node_step_data(3)
    assert data["step"] == 3
    assert len(data["nodes"]) == 10

    for n in data["nodes"]:
        nid = n["id"]
        assert n["vrf_score"] == EXPECTED_VRF_SCORES[nid]


def test_storyboard_step3_1hop_neighbor_scores_match_edges():
    """Verify received 1-hop scores match exact physical neighbor lists across the 18 links."""
    data = get_10node_step_data(3)
    nodes = {n["id"]: n for n in data["nodes"]}

    for nid, expected_nbrs in STORYBOARD_10_ADJACENCY.items():
        node = nodes[nid]
        neighbor_scores = node["neighbor_scores"]
        neighbor_scores_str = node["neighbor_scores_str"]
        neighbor_scoreboard = node["neighbor_scoreboard"]

        # Assert neighbor IDs match
        assert sorted(neighbor_scores.keys()) == sorted(expected_nbrs)
        assert sorted(neighbor_scores_str.keys()) == sorted([f"C{nb}" for nb in expected_nbrs])
        assert len(neighbor_scoreboard) == len(expected_nbrs)

        # Assert scores match each neighbor's VRF score
        for nb in expected_nbrs:
            assert neighbor_scores[nb] == EXPECTED_VRF_SCORES[nb]
            assert neighbor_scores_str[f"C{nb}"] == EXPECTED_VRF_SCORES[nb]


def test_storyboard_step3_no_initiators_declared():
    """Assert no node is marked as INITIATOR in Step 3 (role=CLIENT, is_initiator=False)."""
    data = get_10node_step_data(3)
    assert data["active_leaders"] == []

    for n in data["nodes"]:
        assert n["is_initiator"] is False, f"Node {n['id']} unexpectedly marked as initiator in Step 3"
        assert n["role"] == "CLIENT"
        assert n["status"] == "NOT_ASSIGNED"
        assert n["zone_id"] is None


def test_storyboard_step3_packet_exchanges():
    """Verify Step 3 produces mutual score exchange packets along the physical links."""
    data = get_10node_step_data(3)
    packets = data["packet_exchanges"]
    num_edges = len(data["edges"])
    assert len(packets) == num_edges * 2, f"Expected {num_edges * 2} directed transmissions ({num_edges} edges x 2), got {len(packets)}"

    for pkt in packets:
        assert pkt["type"] == "VRF_SCORE"
        src = pkt["from"]
        tgt = pkt["to"]
        assert pkt["score"] == EXPECTED_VRF_SCORES[src]
        assert tgt in STORYBOARD_10_ADJACENCY[src]


def test_get_step3_api_endpoint(client):
    """Assert GET /api/v1/storyboard/step/3 returns HTTP 200 with complete Step 3 payload."""
    res = client.get("/api/v1/storyboard/step/3")
    assert res.status_code == 200
    body = res.json()
    assert body["step"] == 3
    assert len(body["nodes"]) == 10
    assert len(body["edges"]) in [17, 18]
    assert len(body["packet_exchanges"]) == len(body["edges"]) * 2
    assert body["nodes"][1]["vrf_score"] == 0.0837  # Node 2
    assert body["nodes"][1]["neighbor_scores"]["1"] == 0.1543 or body["nodes"][1]["neighbor_scores"].get(1) == 0.1543


def test_post_step3_api_endpoint(client):
    """Assert POST /api/v1/storyboard/step/3 returns HTTP 200 with complete Step 3 payload."""
    res = client.post("/api/v1/storyboard/step/3")
    assert res.status_code == 200
    body = res.json()
    assert body["step"] == 3
    assert len(body["nodes"]) == 10
