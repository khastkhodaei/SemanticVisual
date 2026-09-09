"""Automated Verification Suite for Step 5: Zone Creation via PROBE Flooding (TTL = 1).

Verifies:
1. Initiators 2, 4, and 8 dispatch PROBE packets strictly to their 1-hop physical neighbors with TTL = 1.
   - Initiator 2 -> [1, 3]
   - Initiator 4 -> [1, 5, 6, 7]
   - Initiator 8 -> [6, 9, 10]
2. All 10 nodes retain complete metadata accumulated from prior steps:
   - neighbors, distribution, vector_10d, vrf_score, role.
3. Overlapping probes correctly identify and flag boundary gateway nodes:
   - Node 1 (Zone 2 and Zone 4)
   - Node 6 (Zone 4 and Zone 8)
4. API endpoints GET and POST /api/v1/storyboard/step/5 return HTTP 200 with full packet traces.
5. STEPS.md documents Step 5 specifications and palettes.
6. Frontend files (index.html, app.js, style.css) support Step 5 stepper, navigation, and modal details.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    STORYBOARD_10_VECTORS,
    STORYBOARD_10_VRF_SCORES,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


EXPECTED_PROBE_TARGETS = {
    2: [1, 3],
    4: [1, 5, 6, 7],
    8: [6, 9, 10],
}


def test_step5_initiator_probe_dispatches_exact_1hop_neighbors():
    """Assert Nodes 2, 4, and 8 dispatch PROBE packets strictly to their 1-hop physical neighbors with TTL = 1."""
    data = get_10node_step_data(5)
    packets = data.get("packet_events") or data.get("packet_exchanges")
    assert packets is not None
    assert len(packets) == 9, f"Expected 9 PROBE packet events, got {len(packets)}"

    dispatched = {}
    for pkt in packets:
        init_id = pkt["initiator_id"]
        tgt_id = pkt["target_num"]
        ttl = pkt["ttl"]
        assert ttl == 1, f"Packet {pkt['packet_id']} has TTL={ttl}, expected 1"
        assert pkt["type"] == "PROBE"
        assert "PROBE" in pkt["label"]
        dispatched.setdefault(init_id, []).append(tgt_id)

    for init_id, expected_targets in EXPECTED_PROBE_TARGETS.items():
        actual_targets = sorted(dispatched.get(init_id, []))
        assert actual_targets == sorted(expected_targets), (
            f"Initiator {init_id} probe targets {actual_targets} != expected {expected_targets}"
        )
        # Verify strict 1-hop physical neighbor constraint
        neighbors = STORYBOARD_10_ADJACENCY[init_id]
        for tgt in actual_targets:
            assert tgt in neighbors, f"Target Node {tgt} is not a 1-hop physical neighbor of Initiator {init_id}"


def test_step5_all_10nodes_retain_full_metadata():
    """Assert all 10 nodes preserve neighbors, distribution, vector_10d, vrf_score, and role."""
    data = get_10node_step_data(5)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid in range(1, 11):
        node = nodes[nid]
        # 1. neighbors
        assert "neighbors" in node
        assert sorted(node["neighbors"]) == sorted(STORYBOARD_10_ADJACENCY[nid])

        # 2. distribution
        assert "distribution" in node
        assert node["distribution"] == STORYBOARD_10_DISTRIBUTION[nid]
        assert sum(node["distribution"].values()) == 100

        # 3. vector_10d
        assert "vector_10d" in node
        assert len(node["vector_10d"]) == 10
        assert node["vector_10d"] == STORYBOARD_10_VECTORS[nid]
        assert sum(node["vector_10d"]) == pytest.approx(1.0, abs=1e-3)

        # 4. vrf_score
        assert "vrf_score" in node
        assert node["vrf_score"] == pytest.approx(STORYBOARD_10_VRF_SCORES[nid], abs=1e-4)

        # 5. role & styling
        if nid in (2, 4, 8):
            assert node["role"] == "INITIATOR"
            assert node["is_initiator"] is True
            assert node["status"] == "INITIATOR"
            assert node["bg_color"] in ("#991b1b", "#166534", "#a16207")
        else:
            assert node["role"] == "CLIENT"
            assert node["is_initiator"] is False
            # Premature zone coloring prevention: non-initiators must remain solid neutral blue
            assert node["bg_color"] == "#2563eb"
            assert node["border_color"] == "#1d4ed8"


def test_step5_boundary_nodes_and_zone_membership():
    """Assert boundary nodes 1 and 6 receive overlapping probes and are correctly flagged."""
    data = get_10node_step_data(5)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1: receives probes from Initiator 2 and 4
    n1 = nodes[1]
    assert n1["is_boundary"] is True
    assert set(n1["boundary_zones"]) == {2, 4}
    rec1_inits = {p["initiator_id"] for p in n1["zone_probes_received"]}
    assert rec1_inits == {2, 4}

    # Node 6: receives probes from Initiator 4 and 8
    n6 = nodes[6]
    assert n6["is_boundary"] is True
    assert set(n6["boundary_zones"]) == {4, 8}
    rec6_inits = {p["initiator_id"] for p in n6["zone_probes_received"]}
    assert rec6_inits == {4, 8}

    # Non-boundary nodes
    for nid in (2, 3, 4, 5, 7, 8, 9, 10):
        assert nodes[nid]["is_boundary"] is False

    # Check assigned zones
    assert nodes[2]["assigned_zone"] == 2
    assert nodes[3]["assigned_zone"] == 2
    assert nodes[4]["assigned_zone"] == 4
    assert nodes[5]["assigned_zone"] == 4
    assert nodes[7]["assigned_zone"] == 4
    assert nodes[8]["assigned_zone"] == 8
    assert nodes[9]["assigned_zone"] == 8
    assert nodes[10]["assigned_zone"] == 8


def test_step5_arrival_timestamps_and_first_wins_arbitration():
    """Assert simulated network arrival timestamps and First-Wins arbitration metadata."""
    data = get_10node_step_data(5)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1: C2 arrived at t = 10.4 ms (Winner), C4 arrived at t = 16.8 ms (Delayed)
    n1 = nodes[1]
    n1_probes = {p["initiator_id"]: p for p in n1["zone_probes_received"]}
    assert n1_probes[2]["timestamp"] == "t = 10.4 ms"
    assert n1_probes[2]["winner"] is True
    assert n1_probes[4]["timestamp"] == "t = 16.8 ms"
    assert n1_probes[4]["winner"] is False
    assert "First-Wins" in n1["first_wins_notice"]

    # Node 6: C4 arrived at t = 11.2 ms (Winner), C8 arrived at t = 18.5 ms (Delayed)
    n6 = nodes[6]
    n6_probes = {p["initiator_id"]: p for p in n6["zone_probes_received"]}
    assert n6_probes[4]["timestamp"] == "t = 11.2 ms"
    assert n6_probes[4]["winner"] is True
    assert n6_probes[8]["timestamp"] == "t = 18.5 ms"
    assert n6_probes[8]["winner"] is False
    assert "First-Wins" in n6["first_wins_notice"]

    # Check packet events contain latency and timestamp
    for pkt in data["packet_events"]:
        assert "timestamp" in pkt
        assert "latency_ms" in pkt
        assert "is_winner" in pkt


def test_step5_api_endpoints(client):
    """Assert GET and POST /api/v1/storyboard/step/5 return HTTP 200 with full payload."""
    res_get = client.get("/api/v1/storyboard/step/5")
    assert res_get.status_code == 200
    d_get = res_get.json()
    assert d_get["step"] == 5
    assert d_get["phase_badge"] == "STEP 5: ZONE PROBE FLOODING (TTL=1)"
    assert len(d_get["nodes"]) == 10
    assert len(d_get["packet_events"]) == 9
    assert d_get["active_leaders"] == [2, 4, 8]
    assert d_get["boundary_nodes"] == [1, 6]

    res_post = client.post("/api/v1/storyboard/step/5")
    assert res_post.status_code == 200
    d_post = res_post.json()
    assert d_post["step"] == 5
    assert len(d_post["nodes"]) == 10
    assert len(d_post["packet_events"]) == 9


def test_step5_steps_md_documentation():
    """Verify STEPS.md documents Step 5 requirements and zone formation rules."""
    with open("STEPS.md", "r", encoding="utf-8") as f:
        md = f.read()

    assert "## Step 5 — Zone Creation via PROBE Flooding (TTL = 1)" in md
    assert r"\text{PROBE}(p, \text{TTL} = 1)" in md
    assert "Initiator 2" in md
    assert "Initiator 4" in md
    assert "Initiator 8" in md
    assert "Node 1 and Node 3" in md
    assert "Node 1, Node 5, Node 6, and Node 7" in md
    assert "Node 6, Node 9, and Node 10" in md
    assert "Zone 2 Palette (Emerald Green - `#059669`)" in md
    assert "Zone 4 Palette (Coral / Orange - `#ea580c`)" in md
    assert "Zone 8 Palette (Violet / Purple - `#7c3aed`)" in md
    assert "Node 1:" in md
    assert "Node 6:" in md


def test_step5_frontend_elements_and_logic():
    """Verify index.html and app.js implement Step 5 navigation and modal elements."""
    with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="stepNav5"' in html
    assert 'id="activePhaseBadge"' in html
    assert 'id="zoneLegendItem"' in html
    assert 'id="cardProbeSection"' in html
    assert 'id="cardVectorBarsContainer"' in html

    with open("frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "renderStep5" in js
    assert "animateStep5ProbePackets" in js
    assert "useZoneColors: false" in js
    assert "activePhaseBadge" in js
    assert "STEP 5: ZONE PROBE FLOODING (TTL=1)" in js
    assert "Overlapping Probes Detected (First-Wins Arbitration)" in js
    assert "t = 11.2 ms" in js
    assert "t = 18.5 ms" in js
    assert "PROBE(TTL=1)" in js
    assert "stepNav" in js
    assert "cardProbeSection" in js
    assert "cardVectorBarsContainer" in js
