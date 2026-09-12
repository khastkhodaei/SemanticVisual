"""Automated Verification Suite for Step 13: Hierarchical Top-Level Zone Creation (Figure 3(e)).

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/13 return HTTP 200 with complete storyboard payload.
2. Endpoint /api/v1/storyboard/step/13 validates:
   - top_level_zone['root_initiator'] == 8
   - top_level_zone['id'] == 'Z_TOP'
   - All three initiators {2, 4, 8} belong to Z_TOP (member_initiators).
3. Evaluates top-level VRF election:
   - Node 8 has top_level_role == "TOP_INITIATOR" and is_top_initiator is True.
   - Nodes 2 and 4 have top_level_role == "SUPER_ZONE_MEMBER" and belong to Z_TOP.
   - Regular nodes (1, 3, 5, 6, 7, 9, 10) have top_level_role == "BASE_ZONE_MEMBER".
4. Multi-hop high-level probe traces:
   - Packet TOP_PROBE: C8 -> C6 -> C4 (Hop 1, TTL=2)
   - Packet TOP_PROBE: C4 -> C1 -> C2 (Hop 2, TTL=1)
5. Base zone memberships and Step 12 intra-zone clusters remain preserved:
   - Zones: Zone 2 {1, 2, 3}, Zone 4 {4, 5, 6, 7}, Zone 8 {8, 9, 10}
   - Clusters: 2-A {1, 2}, 2-B {3}, 4-A {4, 5}, 4-B {6, 7}, 8-A {8}, 8-B {9}, 8-C {10}
6. SemanticDFLEngine().run_top_level_zone_creation_10nodes() produces valid structure.
7. STEPS.md contains documentation for Step 13.
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


def test_step13_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/13 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/13")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 13
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 13: TOP-LEVEL ZONE CREATION (FIGURE 3(e))"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18

    res_post = client.post("/api/v1/storyboard/step/13")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 13


def test_step13_top_level_zone_structure():
    """Assert top_level_zone root_initiator is 8 and member initiators are {2, 4, 8}."""
    data = get_10node_step_data(13)
    assert "top_level_zone" in data
    top_zone = data["top_level_zone"]
    assert top_zone["id"] == "Z_TOP"
    assert top_zone["root_initiator"] == 8
    assert set(top_zone["member_initiators"]) == {2, 4, 8}
    assert top_zone["min_vrf"] == 0.0275
    assert top_zone["vrf_scores"][8] == 0.0275
    assert top_zone["vrf_scores"][4] == 0.0412
    assert top_zone["vrf_scores"][2] == 0.0837


def test_step13_node_roles_and_election():
    """Assert Node 8 is elected TOP_INITIATOR and Nodes 2 & 4 are SUPER_ZONE_MEMBER."""
    data = get_10node_step_data(13)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 8 is elected Top-Level Initiator (Super-Initiator)
    assert nodes[8]["top_level_role"] == "TOP_INITIATOR"
    assert nodes[8]["is_top_initiator"] is True
    assert nodes[8]["top_level_zone"] == "Z_TOP"
    assert set(nodes[8]["governing_initiators"]) == {2, 4, 8}

    # Nodes 2 and 4 are Super-Zone members
    assert nodes[2]["top_level_role"] == "SUPER_ZONE_MEMBER"
    assert nodes[2]["is_top_initiator"] is False
    assert nodes[2]["top_level_zone"] == "Z_TOP"

    assert nodes[4]["top_level_role"] == "SUPER_ZONE_MEMBER"
    assert nodes[4]["is_top_initiator"] is False
    assert nodes[4]["top_level_zone"] == "Z_TOP"

    # Regular client nodes
    for nid in [1, 3, 5, 6, 7, 9, 10]:
        assert nodes[nid]["top_level_role"] == "BASE_ZONE_MEMBER"
        assert nodes[nid]["is_top_initiator"] is False


def test_step13_top_probe_packet_traces():
    """Assert high-level probe traces: C8 -> C6 -> C4 and C4 -> C1 -> C2."""
    data = get_10node_step_data(13)
    packets = data["packet_events"]
    assert len(packets) == 2

    # Hop 1: C8 -> C6 -> C4
    pkt1 = packets[0]
    assert pkt1["type"] == "TOP_PROBE"
    assert pkt1["source_num"] == 8
    assert pkt1["relay_num"] == 6
    assert pkt1["target_num"] == 4
    assert pkt1["path_nums"] == [8, 6, 4]
    assert pkt1["ttl"] == 2

    # Hop 2: C4 -> C1 -> C2
    pkt2 = packets[1]
    assert pkt2["type"] == "TOP_PROBE"
    assert pkt2["source_num"] == 4
    assert pkt2["relay_num"] == 1
    assert pkt2["target_num"] == 2
    assert pkt2["path_nums"] == [4, 1, 2]
    assert pkt2["ttl"] == 1


def test_step13_preserves_base_zones_and_step12_clusters():
    """Assert base zone memberships and Step 12 clusters remain preserved."""
    data = get_10node_step_data(13)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Base zone memberships
    assert data["zones"][2] == [1, 2, 3]
    assert data["zones"][4] == [4, 5, 6, 7]
    assert data["zones"][8] == [8, 9, 10]

    # Cluster assignments from Step 12
    assert nodes[1]["assigned_cluster_id"] == "2-A" and nodes[1]["cluster_exemplar"] == 2
    assert nodes[2]["assigned_cluster_id"] == "2-A" and nodes[2]["cluster_exemplar"] == 2
    assert nodes[3]["assigned_cluster_id"] == "2-B" and nodes[3]["cluster_exemplar"] == 3

    assert nodes[4]["assigned_cluster_id"] == "4-A" and nodes[4]["cluster_exemplar"] == 4
    assert nodes[5]["assigned_cluster_id"] == "4-A" and nodes[5]["cluster_exemplar"] == 4
    assert nodes[6]["assigned_cluster_id"] == "4-B" and nodes[6]["cluster_exemplar"] == 6
    assert nodes[7]["assigned_cluster_id"] == "4-B" and nodes[7]["cluster_exemplar"] == 6

    assert nodes[8]["assigned_cluster_id"] == "8-A" and nodes[8]["cluster_exemplar"] == 8
    assert nodes[9]["assigned_cluster_id"] == "8-B" and nodes[9]["cluster_exemplar"] == 9
    assert nodes[10]["assigned_cluster_id"] == "8-C" and nodes[10]["cluster_exemplar"] == 10

    # Physical links remain clean slate lines
    assert len(data["edges"]) in (17, 18)
    assert data["total_edges"] == 18
    for edge in data["edges"]:
        assert edge["line_color"] == "#64748b"
        assert edge["line_style"] == "solid"


def test_step13_engine_method():
    """Verify SemanticDFLEngine().run_top_level_zone_creation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_top_level_zone_creation_10nodes()
    assert result["step"] == 13
    assert len(result["nodes"]) == 10
    assert result["top_level_zone"]["root_initiator"] == 8
    assert set(result["top_level_zone"]["member_initiators"]) == {2, 4, 8}


def test_step13_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 13."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text()
    assert "## Step 13 — Hierarchical Top-Level Zone Creation (Figure 3(e))" in content
    assert r"\mathcal{G}_{\text{init}}" in content
    assert "Super-Initiator 👑👑" in content
    assert "TOP_PROBE" in content
    assert r"\mathcal{Z}_{\text{Top}}" in content


def test_step13_frontend_elements_and_logic(client):
    """Verify frontend template and app.js contain Step 13 UI elements and rendering logic."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "stepNav13" in res_index.text
    assert "cardTopZoneSection" in res_index.text
    assert "cardTopZoneBadge" in res_index.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "renderStep13" in res_js.text
    assert "animateStep13TopProbe" in res_js.text
    assert "👑👑 ELECTED TOP-LEVEL SUPER-INITIATOR" in res_js.text
    assert "ACTIVE PHASE: STEP 13: TOP-LEVEL ZONE CREATION (FIGURE 3(e))" in res_js.text
    assert "top-initiator-node" in res_js.text
