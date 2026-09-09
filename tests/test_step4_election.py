"""Automated Verification Suite for Step 4: VRF Score Comparison & Initiator Election.

Verifies:
1. Exactly Nodes 2, 4, and 8 have role == 'INITIATOR' and is_initiator == True.
2. All other 7 nodes have role == 'CLIENT' and is_initiator == False.
3. Every node evaluates the minimum VRF score in its closed 1-hop ball m_p = min_{q in N_1(p) U {p}} (sigma_q, id_q).
4. GET and POST /api/v1/storyboard/step/4 return HTTP 200 with step 4 payload and active_leaders == [2, 4, 8].
5. STEPS.md accurately reflects Step 4 specifications.
6. Frontend index.html and app.js include the Step 4 election banner, 4-step stepper, and navigation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_VRF_SCORES,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


EXPECTED_INITIATORS = {2, 4, 8}
EXPECTED_CANDIDATES = {1, 3, 5, 6, 7, 9, 10}

EXPECTED_WINNERS = {
    1: 4,
    2: 2,
    3: 2,
    4: 4,
    5: 4,
    6: 8,
    7: 4,
    8: 8,
    9: 8,
    10: 8,
}


def test_step4_initiators_exact_roles():
    """Assert that exactly Nodes 2, 4, and 8 have role == 'INITIATOR' and all other 7 have role == 'CLIENT'."""
    data = get_10node_step_data(4)
    nodes = data["nodes"]
    assert len(nodes) == 10

    initiator_ids = set()
    client_ids = set()

    for node in nodes:
        nid = node["id"]
        role = node["role"]
        is_init = node["is_initiator"]

        if role == "INITIATOR":
            initiator_ids.add(nid)
            assert is_init is True, f"Node {nid} has role 'INITIATOR' but is_initiator is False"
            assert node["status"] == "INITIATOR"
            assert "Self-Elected Initiator" in node["decision_banner"]
        else:
            client_ids.add(nid)
            assert role == "CLIENT", f"Node {nid} has unexpected role '{role}'"
            assert is_init is False, f"Node {nid} has role 'CLIENT' but is_initiator is True"
            assert node["status"] == "CANDIDATE"
            assert "Candidate Member" in node["decision_banner"]

    assert initiator_ids == EXPECTED_INITIATORS, f"Expected initiators {EXPECTED_INITIATORS}, got {initiator_ids}"
    assert client_ids == EXPECTED_CANDIDATES, f"Expected candidates {EXPECTED_CANDIDATES}, got {client_ids}"
    assert data["active_leaders"] == [2, 4, 8]


def test_step4_mathematical_closed_ball_minimums():
    """Verify that closed 1-hop ball minimum m_p = min_{q in N_1(p) U {p}} (sigma_q, id_q) matches ground truth."""
    for p in range(1, 11):
        closed_ball = [p] + STORYBOARD_10_ADJACENCY[p]
        # Evaluate lexicographic minimum (score, id)
        min_tuple = min((STORYBOARD_10_VRF_SCORES[q], q) for q in closed_ball)
        calculated_winner = min_tuple[1]

        expected_winner = EXPECTED_WINNERS[p]
        assert calculated_winner == expected_winner, (
            f"Node {p}: expected winner {expected_winner}, got {calculated_winner} "
            f"with ball scores {[(q, STORYBOARD_10_VRF_SCORES[q]) for q in closed_ball]}"
        )


def test_get_step4_api_endpoint(client):
    """Assert GET /api/v1/storyboard/step/4 returns HTTP 200 with complete Step 4 payload."""
    res = client.get("/api/v1/storyboard/step/4")
    assert res.status_code == 200, f"GET /api/v1/storyboard/step/4 returned {res.status_code}"
    body = res.json()

    assert body["step"] == 4
    assert body["active_leaders"] == [2, 4, 8]
    assert len(body["nodes"]) == 10

    for node in body["nodes"]:
        nid = node["id"]
        if nid in EXPECTED_INITIATORS:
            assert node["role"] == "INITIATOR"
            assert node["is_initiator"] is True
        else:
            assert node["role"] == "CLIENT"
            assert node["is_initiator"] is False


def test_post_step4_api_endpoint(client):
    """Assert POST /api/v1/storyboard/step/4 returns HTTP 200 with complete Step 4 payload."""
    res = client.post("/api/v1/storyboard/step/4")
    assert res.status_code == 200, f"POST /api/v1/storyboard/step/4 returned {res.status_code}"
    body = res.json()

    assert body["step"] == 4
    assert body["active_leaders"] == [2, 4, 8]


def test_step4_packet_exchanges():
    """Verify Step 4 contains mutual score exchange transmissions along physical links."""
    data = get_10node_step_data(4)
    packets = data["packet_exchanges"]
    num_edges = len(data["edges"])
    assert len(packets) == num_edges * 2, f"Expected {num_edges * 2} transmissions, got {len(packets)}"
    for pkt in packets:
        assert pkt["type"] == "VRF_SCORE"
        src = pkt["from"]
        tgt = pkt["to"]
        assert pkt["score"] == STORYBOARD_10_VRF_SCORES[src]
        assert tgt in STORYBOARD_10_ADJACENCY[src]


def test_step4_1hop_neighbor_scores_match_edges():
    """Verify Step 4 nodes contain received neighbor scoreboards matching physical edges."""
    data = get_10node_step_data(4)
    nodes = {n["id"]: n for n in data["nodes"]}

    for nid, expected_nbrs in STORYBOARD_10_ADJACENCY.items():
        node = nodes[nid]
        neighbor_scores = node["neighbor_scores"]
        neighbor_scores_str = node["neighbor_scores_str"]
        neighbor_scoreboard = node["neighbor_scoreboard"]

        assert sorted(neighbor_scores.keys()) == sorted(expected_nbrs)
        assert sorted(neighbor_scores_str.keys()) == sorted([f"C{nb}" for nb in expected_nbrs])
        assert len(neighbor_scoreboard) == len(expected_nbrs)

        for nb in expected_nbrs:
            assert neighbor_scores[nb] == STORYBOARD_10_VRF_SCORES[nb]
            assert neighbor_scores_str[f"C{nb}"] == STORYBOARD_10_VRF_SCORES[nb]


def test_steps_md_step4_documentation():
    """Verify STEPS.md contains Step 4 formula, evaluation, and winner summary."""
    with open("STEPS.md", "r", encoding="utf-8") as f:
        content = f.read()

    assert "## Step 4 — 1-Hop Score Exchange, VRF Comparison & Initiator Election" in content or "## Step 4 —" in content
    assert "Node 2 (0.0837)" in content
    assert "Node 4 (0.0412)" in content
    assert "Node 8 (0.0275)" in content
    assert "Exactly Nodes 2, 4, and 8 become the Initiators" in content



def test_frontend_step4_modal_and_nav():
    """Verify frontend HTML and JS contain Step 4 election banner, title, and navigation support."""
    with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="stepNav4"' in html
    assert 'id="cardElectionBanner"' in html
    assert 'id="cardScoreboardTitle"' in html

    with open("frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "STORYBOARD_10_VRF_SCORES" in js
    assert "renderStep4" in js
    assert "cardElectionBanner" in js
    assert "Self-Elected Initiator" in js
    assert "Candidate Member" in js
