"""Automated Verification Suite for Step 14: Top-Level Initiator Election & Super-Zone Creation (Figure 3(e)).

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/14 return HTTP 200 with complete storyboard payload.
2. Endpoint /api/v1/storyboard/step/14 validates:
   - top_level_zone['root_initiator'] == 4
   - top_level_zone['id'] == 'Z_TOP'
   - All three initiators {2, 4, 8} belong to Z_TOP (member_initiators).
3. Evaluates central bridge top-level election:
   - Node 4 has top_level_role == "TOP_INITIATOR" and is_top_initiator is True.
   - Nodes 2 and 8 have top_level_role == "SUPER_ZONE_MEMBER" and belong to Z_TOP (Root: C4).
   - Regular nodes (1, 3, 5, 6, 7, 9, 10) have top_level_role == "BASE_ZONE_MEMBER".
4. 1-hop bidirectional VRF score exchange events on overlay graph G_init:
   - C2 -> C4: score 0.0837 via path [2, 1, 4]
   - C8 -> C4: score 0.0275 via path [8, 6, 4]
   - C4 -> C2: score 0.0412 via path [4, 1, 2]
   - C4 -> C8: score 0.0412 via path [4, 6, 8]
5. Symmetrical TOP_PROBE broadcasts from C4 with TTL=1:
   - C4 -> C1 -> C2 (root=4, ttl=1)
   - C4 -> C6 -> C8 (root=4, ttl=1)
6. Base zone memberships and Step 12 intra-zone clusters remain preserved:
   - Zones: Zone 2 {1, 2, 3}, Zone 4 {4, 5, 6, 7}, Zone 8 {8, 9, 10}
   - Clusters: 2-A {1, 2}, 2-B {3}, 4-A {4, 5}, 4-B {6, 7}, 8-A {8}, 8-B {9}, 8-C {10}
7. SemanticDFLEngine().run_top_level_zone_creation_10nodes() produces valid structure with root 4 and step 14.
8. STEPS.md contains documentation for Step 14 with C4 Top-Level Initiator.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine
from backend.storyboard_10nodes import (
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step14_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/14 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/14")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 14
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 14: TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] == 14

    res_post = client.post("/api/v1/storyboard/step/14")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 14


def test_step14_top_level_zone_structure():
    """Assert top_level_zone root_initiator is 4 and member initiators are {2, 4, 8}."""
    data = get_10node_step_data(14)
    assert "top_level_zone" in data
    top_zone = data["top_level_zone"]
    assert top_zone["id"] == "Z_TOP"
    assert top_zone["root_initiator"] == 4
    assert top_zone["winner_initiator"] == 4
    assert set(top_zone["member_initiators"]) == {2, 4, 8}
    assert top_zone["ttl"] == 1
    assert top_zone["vrf_scores"][4] == 0.0412
    assert top_zone["vrf_scores"][8] == 0.0275
    assert top_zone["vrf_scores"][2] == 0.0837


def test_step14_node_roles_and_election():
    """Assert Node 4 is elected TOP_INITIATOR and Nodes 2 & 8 are SUPER_ZONE_MEMBER."""
    data = get_10node_step_data(14)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 4 is elected Top-Level Initiator (Super-Initiator)
    assert nodes[4]["top_level_role"] == "TOP_INITIATOR"
    assert nodes[4]["is_top_initiator"] is True
    assert nodes[4]["top_level_zone"] == "Z_TOP"
    assert set(nodes[4]["governing_initiators"]) == {2, 4, 8}

    # Nodes 2 and 8 are Super-Zone members
    assert nodes[2]["top_level_role"] == "SUPER_ZONE_MEMBER"
    assert nodes[2]["is_top_initiator"] is False
    assert nodes[2]["top_level_zone"] == "Z_TOP"
    assert nodes[2]["super_zone_root"] == 4

    assert nodes[8]["top_level_role"] == "SUPER_ZONE_MEMBER"
    assert nodes[8]["is_top_initiator"] is False
    assert nodes[8]["top_level_zone"] == "Z_TOP"
    assert nodes[8]["super_zone_root"] == 4

    # Regular client nodes
    for nid in [1, 3, 5, 6, 7, 9, 10]:
        assert nodes[nid]["top_level_role"] == "BASE_ZONE_MEMBER"
        assert nodes[nid]["is_top_initiator"] is False


def test_step14_vrf_score_exchange_events():
    """Assert 1-hop bidirectional VRF score exchanges between C2 <-> C4 and C4 <-> C8."""
    data = get_10node_step_data(14)
    vrf_events = data.get("vrf_exchange_events", [])
    assert len(vrf_events) == 4

    exchanges = {(e["source_num"], e["target_num"]): e for e in vrf_events}
    # C2 -> C4
    assert (2, 4) in exchanges
    assert exchanges[(2, 4)]["score"] == 0.0837
    assert exchanges[(2, 4)]["path"] == [2, 1, 4]

    # C8 -> C4
    assert (8, 4) in exchanges
    assert exchanges[(8, 4)]["score"] == 0.0275
    assert exchanges[(8, 4)]["path"] == [8, 6, 4]

    # C4 -> C2
    assert (4, 2) in exchanges
    assert exchanges[(4, 2)]["score"] == 0.0412
    assert exchanges[(4, 2)]["path"] == [4, 1, 2]

    # C4 -> C8
    assert (4, 8) in exchanges
    assert exchanges[(4, 8)]["score"] == 0.0412
    assert exchanges[(4, 8)]["path"] == [4, 6, 8]


def test_step14_symmetrical_top_probe_traces():
    """Assert symmetrical high-level probe traces from C4 outward to C2 and C8."""
    data = get_10node_step_data(14)
    probe_events = data.get("probe_events", [])
    assert len(probe_events) == 2

    west_probe = next(p for p in probe_events if p["target_num"] == 2)
    assert west_probe["source_num"] == 4
    assert west_probe["relay_num"] == 1
    assert west_probe["path_nums"] == [4, 1, 2]
    assert west_probe["ttl"] == 1
    assert west_probe["root"] == 4

    east_probe = next(p for p in probe_events if p["target_num"] == 8)
    assert east_probe["source_num"] == 4
    assert east_probe["relay_num"] == 6
    assert east_probe["path_nums"] == [4, 6, 8]
    assert east_probe["ttl"] == 1
    assert east_probe["root"] == 4


def test_step14_preserves_base_zones_and_step12_clusters():
    """Assert base zone memberships and Step 12 clusters remain preserved."""
    data = get_10node_step_data(14)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Base zone memberships
    assert data["zones"][2] == [1, 2, 3]
    assert data["zones"][4] == [4, 5, 6, 7]
    assert data["zones"][8] == [8, 9, 10]

    # Cluster assignments and designated exemplars preserved from Step 13
    assert nodes[1]["assigned_cluster_id"] == "2-A" and nodes[1]["cluster_exemplar"] == 1
    assert nodes[2]["assigned_cluster_id"] == "2-A" and nodes[2]["cluster_exemplar"] == 1
    assert nodes[3]["assigned_cluster_id"] == "2-B" and nodes[3]["cluster_exemplar"] == 3

    assert nodes[4]["assigned_cluster_id"] == "4-A" and nodes[4]["cluster_exemplar"] == 5
    assert nodes[5]["assigned_cluster_id"] == "4-A" and nodes[5]["cluster_exemplar"] == 5
    assert nodes[6]["assigned_cluster_id"] == "4-B" and nodes[6]["cluster_exemplar"] == 7
    assert nodes[7]["assigned_cluster_id"] == "4-B" and nodes[7]["cluster_exemplar"] == 7

    assert nodes[8]["assigned_cluster_id"] == "8-A" and nodes[8]["cluster_exemplar"] == 8
    assert nodes[9]["assigned_cluster_id"] == "8-B" and nodes[9]["cluster_exemplar"] == 9
    assert nodes[10]["assigned_cluster_id"] == "8-C" and nodes[10]["cluster_exemplar"] == 10

    # Physical links remain clean slate lines
    assert len(data["edges"]) in (17, 18)
    assert data["total_edges"] == 18
    for edge in data["edges"]:
        assert edge["line_color"] == "#64748b"
        assert edge["line_style"] == "solid"


def test_step14_overlay_scoreboards_and_traces():
    """Assert all three initiators have overlay_scoreboard and explicit VRF traces."""
    data = get_10node_step_data(14)
    nodes = {n["id"]: n for n in data["nodes"]}

    # 1. Assert top_level_zone['root_initiator'] == 4
    assert data["top_level_zone"]["root_initiator"] == 4

    # 2. Assert all three initiators have overlay_scoreboard containing entries for nodes 2, 4, 8
    # Node 2 Scoreboard
    sb2 = nodes[2].get("overlay_scoreboard")
    assert sb2 is not None
    assert sb2["self"]["id"] == 2
    assert sb2["self"]["score"] == 0.0837
    assert sb2["elected_leader"] == 4
    recv2 = {r["id"]: r for r in sb2["received"]}
    assert 4 in recv2 and recv2[4]["score"] == 0.0412 and recv2[4]["via"] == "direct"
    assert 8 in recv2 and recv2[8]["score"] == 0.0275 and recv2[8]["via"] == "relayed_by_C4"

    # Node 4 Scoreboard
    sb4 = nodes[4].get("overlay_scoreboard")
    assert sb4 is not None
    assert sb4["self"]["id"] == 4
    assert sb4["self"]["score"] == 0.0412
    assert sb4["elected_leader"] == 4
    assert sb4["is_winner"] is True
    recv4 = {r["id"]: r for r in sb4["received"]}
    assert 2 in recv4 and recv4[2]["score"] == 0.0837 and recv4[2]["via"] == "direct"
    assert 8 in recv4 and recv4[8]["score"] == 0.0275 and recv4[8]["via"] == "direct"

    # Node 8 Scoreboard
    sb8 = nodes[8].get("overlay_scoreboard")
    assert sb8 is not None
    assert sb8["self"]["id"] == 8
    assert sb8["self"]["score"] == 0.0275
    assert sb8["elected_leader"] == 4
    recv8 = {r["id"]: r for r in sb8["received"]}
    assert 4 in recv8 and recv8[4]["score"] == 0.0412 and recv8[4]["via"] == "direct"
    assert 2 in recv8 and recv8[2]["score"] == 0.0837 and recv8[2]["via"] == "relayed_by_C4"

    # 3. Assert elected_leader == 4 across all three initiators
    assert sb2["elected_leader"] == 4
    assert sb4["elected_leader"] == 4
    assert sb8["elected_leader"] == 4

    # 4. Assert explicit VRF communication traces
    traces = data.get("vrf_communication_traces", [])
    assert len(traces) == 4
    t1 = next(t for t in traces if t["from"] == 2 and t["to"] == 4)
    assert t1["payload"] == {"C2_vrf": 0.0837}
    assert t1["path"] == [2, 1, 4]

    t2 = next(t for t in traces if t["from"] == 8 and t["to"] == 4)
    assert t2["payload"] == {"C8_vrf": 0.0275}
    assert t2["path"] == [8, 6, 4]

    t3 = next(t for t in traces if t["from"] == 4 and t["to"] == 2)
    assert t3["payload"] == {"C4_vrf": 0.0412, "relayed_C8_vrf": 0.0275}
    assert t3["path"] == [4, 1, 2]

    t4 = next(t for t in traces if t["from"] == 4 and t["to"] == 8)
    assert t4["payload"] == {"C4_vrf": 0.0412, "relayed_C2_vrf": 0.0837}
    assert t4["path"] == [4, 6, 8]


def test_step14_engine_method():
    """Verify SemanticDFLEngine().run_top_level_zone_creation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_top_level_zone_creation_10nodes()
    assert result["step"] == 14
    assert result["total_steps"] == 14
    assert len(result["nodes"]) == 10
    assert result["top_level_zone"]["root_initiator"] == 4
    assert set(result["top_level_zone"]["member_initiators"]) == {2, 4, 8}


def test_step14_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 14 with C4 Top-Level Initiator."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text()
    assert "## Step 14 — Top-Level Initiator Election & Super-Zone Creation (Figure 3(e))" in content
    assert r"\mathcal{G}_{\text{init}}" in content
    assert "Phase 1: Inward VRF Score Reporting to Central Bridge" in content
    assert "Phase 2: Outward Relay of Network-Wide Scores from" in content
    assert "Overlay VRF Scoreboards on Initiators" in content
    assert "Phase 3: Symmetrical TOP_PROBE Broadcast from" in content
    assert "Phase 4: Formation of Super-Zone" in content
    assert r"\mathcal{Z}_{\text{Top}}" in content


def test_step14_frontend_elements_and_logic(client):
    """Verify frontend template and app.js contain Step 14 UI elements and rendering logic."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "stepNav14" in res_index.text
    assert "cardTopZoneSection" in res_index.text
    assert "cardTopZoneBadge" in res_index.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "renderStep14" in res_js.text
    assert "animateStep14TopProbe" in res_js.text
    assert "renderOverlayVrfScoreboardHtml" in res_js.text
    assert "Overlay VRF Scoreboard (Super-Initiator Election)" in res_js.text
    assert "👑👑 ELECTED TOP-LEVEL SUPER-INITIATOR" in res_js.text
    assert "ACTIVE PHASE: STEP 14: TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)" in res_js.text
    assert "top-initiator-node" in res_js.text
