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


def test_issue3_winner_colors_and_backend_attributes():
    """Verify Issue #3 winner colors: Node 4 (dark green), Node 2 (dark red), Node 8 (dark yellow)."""
    data = get_10node_step_data(4)
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[4]["winner_color"] == "dark green"
    assert nodes[4]["winner_bg"] == "#166534"
    assert nodes[4]["winner_border"] == "#14532d"

    assert nodes[2]["winner_color"] == "dark red"
    assert nodes[2]["winner_bg"] == "#991b1b"
    assert nodes[2]["winner_border"] == "#7f1d1d"

    assert nodes[8]["winner_color"] == "dark yellow"
    assert nodes[8]["winner_bg"] == "#a16207"
    assert nodes[8]["winner_border"] == "#713f12"

    for nid in EXPECTED_CANDIDATES:
        assert nodes[nid]["winner_color"] is None


def test_issue3_steps_md_visualization_rules():
    """Verify STEPS.md documents the visualization sequence and winner highlight colors."""
    with open("STEPS.md", "r", encoding="utf-8") as f:
        steps_md = f.read()

    assert "Dark Green" in steps_md
    assert "Dark Red" in steps_md
    assert "Dark Yellow" in steps_md
    assert "Score Transmission" in steps_md
    assert "Score Reception" in steps_md
    assert "Winner Selection" in steps_md
    assert "Initiator Identification" in steps_md


def test_issue3_frontend_winner_classes_and_sequence():
    """Verify frontend app.js implements sequence flow and winner classes."""
    with open("frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "winner-node-4" in js
    assert "winner-node-2" in js
    assert "winner-node-8" in js
    assert "#166534" in js  # dark green
    assert "#991b1b" in js  # dark red
    assert "#a16207" in js  # dark yellow
    assert "👑 Winner" in js
    assert "[1/4 SCORE TRANSMISSION]" in js
    assert "[2/4 SCORE RECEPTION]" in js
    assert "[3/4 WINNER SELECTION]" in js
    assert "[4/4 INITIATOR IDENTIFIED]" in js

