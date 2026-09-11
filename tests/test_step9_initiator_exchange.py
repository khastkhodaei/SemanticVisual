"""Automated Verification Suite for Step 9: Inter-Initiator P_min Exchange & Global Consensus.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/9 return HTTP 200 with complete storyboard payload.
2. Inter-Initiator proposal exchange via boundary gateway nodes:
   - Initiator C2 holds local P=2, receives C4's P=3 via C1.
   - Initiator C4 holds local P=3, receives C2's P=2 via C1 and C8's P=3 via C6.
   - Initiator C8 holds local P=3, receives C4's P=3 via C6.
3. Unanimous Global Consensus on P = 3:
   - agreed_global_p == 3 on all three initiators (and all nodes).
   - consensus_status == 'AGREED'.
4. Boundary Relay Gateway Nodes:
   - Node 1 and Node 6 have relay_active == True and populated relayed_packets.
   - Non-gateway members have relay_active == False.
5. Packet Events:
   - Contains exactly 4 multi-hop exchange traces:
     * C2 -> C1 -> C4 (P=2)
     * C4 -> C1 -> C2 (P=3)
     * C4 -> C6 -> C8 (P=3)
     * C8 -> C6 -> C4 (P=3)
6. All 10 nodes retain full accumulated metadata profile.
7. Physical links remain clean solid slate lines (#64748b).
8. Documentation in STEPS.md and frontend UI components are aligned.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    STORYBOARD_10_VECTORS,
    STORYBOARD_10_VRF_SCORES,
    get_10node_edges,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step9_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/9 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/9")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 9
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 9: INTER-INITIATOR CONSENSUS EXCHANGE"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["agreed_global_p"] == 3
    assert data_get["consensus_status"] == "AGREED"

    res_post = client.post("/api/v1/storyboard/step/9")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 9


def test_step9_initiators_exchange_proposals_and_reach_consensus():
    """Assert C2 receives C4; C4 receives C2 and C8; C8 receives C4; and all agree on P=3."""
    data = get_10node_step_data(9)
    nodes = {n["id"]: n for n in data["nodes"]}

    # C2 assertions
    c2 = nodes[2]
    assert c2["is_initiator"] is True
    assert c2["local_zone_p"] == 2
    assert c2["received_neighbor_p"] == {"C4": 3}
    assert c2["agreed_global_p"] == 3
    assert c2["consensus_status"] == "AGREED"

    # C4 assertions
    c4 = nodes[4]
    assert c4["is_initiator"] is True
    assert c4["local_zone_p"] == 3
    assert c4["received_neighbor_p"] == {"C2": 2, "C8": 3}
    assert c4["agreed_global_p"] == 3
    assert c4["consensus_status"] == "AGREED"

    # C8 assertions
    c8 = nodes[8]
    assert c8["is_initiator"] is True
    assert c8["local_zone_p"] == 3
    assert c8["received_neighbor_p"] == {"C4": 3}
    assert c8["agreed_global_p"] == 3
    assert c8["consensus_status"] == "AGREED"


def test_step9_boundary_relay_gateways():
    """Assert Node 1 and Node 6 act as active relays while other members do not."""
    data = get_10node_step_data(9)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1 is gateway for C2 <-> C4
    c1 = nodes[1]
    assert c1["is_boundary"] is True
    assert c1["relay_active"] is True
    assert len(c1["relayed_packets"]) == 2
    c1_sources = {p["from"] for p in c1["relayed_packets"]}
    c1_targets = {p["to"] for p in c1["relayed_packets"]}
    assert c1_sources == {"C2", "C4"}
    assert c1_targets == {"C2", "C4"}

    # Node 6 is gateway for C4 <-> C8
    c6 = nodes[6]
    assert c6["is_boundary"] is True
    assert c6["relay_active"] is True
    assert len(c6["relayed_packets"]) == 2
    c6_sources = {p["from"] for p in c6["relayed_packets"]}
    c6_targets = {p["to"] for p in c6["relayed_packets"]}
    assert c6_sources == {"C4", "C8"}
    assert c6_targets == {"C4", "C8"}

    # Other members should have relay_active == False
    for nid in [3, 5, 7, 9, 10]:
        assert nodes[nid]["relay_active"] is False
        assert nodes[nid]["relayed_packets"] == []
        assert nodes[nid]["agreed_global_p"] == 3


def test_step9_multi_hop_packet_events():
    """Assert exactly 4 multi-hop exchange traces with correct paths and values."""
    data = get_10node_step_data(9)
    packets = data["packet_events"]
    assert len(packets) == 4

    expected_routes = {
        "pkt_exchange_2_1_4": {"src": 2, "relay": 1, "tgt": 4, "p": 2, "label": "P=2"},
        "pkt_exchange_4_1_2": {"src": 4, "relay": 1, "tgt": 2, "p": 3, "label": "P=3"},
        "pkt_exchange_4_6_8": {"src": 4, "relay": 6, "tgt": 8, "p": 3, "label": "P=3"},
        "pkt_exchange_8_6_4": {"src": 8, "relay": 6, "tgt": 4, "p": 3, "label": "P=3"},
    }

    found_ids = set()
    for pkt in packets:
        pid = pkt["packet_id"]
        assert pid in expected_routes
        exp = expected_routes[pid]

        assert pkt["source_num"] == exp["src"]
        assert pkt["relay_num"] == exp["relay"]
        assert pkt["target_num"] == exp["tgt"]
        assert pkt["path_nums"] == [exp["src"], exp["relay"], exp["tgt"]]
        assert pkt["p_val"] == exp["p"]
        assert pkt["label"] == exp["label"]
        assert pkt["type"] == "INTER_INITIATOR_EXCHANGE"
        found_ids.add(pid)

    assert found_ids == set(expected_routes.keys())


def test_step9_all_10nodes_retain_full_metadata_profile():
    """Assert all 10 nodes retain their full metadata profile."""
    data = get_10node_step_data(9)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid in range(1, 11):
        assert nid in nodes
        n = nodes[nid]

        # Neighbors
        assert n["neighbors"] == sorted(STORYBOARD_10_ADJACENCY[nid])
        assert n["neighbors_str"] == [f"C{nb}" for nb in n["neighbors"]]

        # Class distributions
        assert n["distribution"] == STORYBOARD_10_DISTRIBUTION[nid]
        assert n["data_distribution"] == STORYBOARD_10_DISTRIBUTION[nid]

        # 10D normalized vectors
        assert n["vector_10d"] == STORYBOARD_10_VECTORS[nid]
        assert n["normalized_vector"] == STORYBOARD_10_VECTORS[nid]

        # VRF scores
        assert pytest.approx(n["vrf_score"], abs=1e-4) == STORYBOARD_10_VRF_SCORES[nid]

        # Zone IDs
        assert n["assigned_zone"] in [2, 4, 8]
        assert n["zone_id"] == n["assigned_zone"]
        assert n["status"] == "ASSIGNED"

        # Prior evaluation fields
        assert "p_min_cosine" in n
        assert "p_min_energy" in n
        assert "binary_search" in n


def test_step9_edges_remain_solid_slate_lines():
    """Assert all physical links remain solid slate lines."""
    data = get_10node_step_data(9)
    edges = data["edges"]
    assert len(edges) == len(get_10node_edges())
    assert data["total_edges"] == 18

    for edge in edges:
        assert edge.get("line_style") == "solid"
        assert edge.get("line_color") == "#64748b"


def test_step9_documentation_and_frontend_alignment():
    """Assert STEPS.md and frontend templates document and support Step 9."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 9 — Inter-Initiator Exchange via Boundary Peers & Global Consensus" in content
    assert "Node 1" in content
    assert "Node 6" in content
    assert "P = 3" in content

    index_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    assert index_html.exists()
    html_content = index_html.read_text(encoding="utf-8")
    assert "stepNav9" in html_content
    assert "cardConsensusSection" in html_content

    app_js = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_js.exists()
    js_content = app_js.read_text(encoding="utf-8")
    assert "renderStep9" in js_content
    assert "animateStep9ConsensusRelays" in js_content
