"""Automated Verification Suite for Step 13: Intra-Zone Cluster Exemplar Designation & Profile Assignment.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/13 return HTTP 200 with complete storyboard payload.
2. Exemplar designations:
   - Nodes 1, 3, 5, 7, 8, 9, 10 have is_exemplar == True.
   - Nodes 2, 4, 6 have is_exemplar == False.
3. Detailed node exemplar metadata:
   - Node 1: cluster_id == "2-A", exemplar_for == [1, 2], profile_signature == [1, 2, 3]
   - Node 2: cluster_id == "2-A", exemplar_node_id == 1
   - Node 3: cluster_id == "2-B", exemplar_for == [3], profile_signature == [4, 5, 6]
   - Node 4: cluster_id == "4-A", exemplar_node_id == 5
   - Node 5: cluster_id == "4-A", exemplar_for == [4, 5], profile_signature == [4, 5, 6]
   - Node 6: cluster_id == "4-B", exemplar_node_id == 7
   - Node 7: cluster_id == "4-B", exemplar_for == [6, 7], profile_signature == [7, 8, 9, 10]
   - Node 8: cluster_id == "8-A", exemplar_for == [8], profile_signature == [4, 5, 6]
   - Node 9: cluster_id == "8-B", exemplar_for == [9], profile_signature == [1, 2, 3]
   - Node 10: cluster_id == "8-C", exemplar_for == [10], profile_signature == [8, 9, 10]
4. ORDER_SET_EXEMPLAR control packet events:
   - C2 -> Node 1, C2 -> Node 3
   - C4 -> Node 5, C4 -> Node 7
   - C8 -> Node 8, C8 -> Node 9, C8 -> Node 10
5. SemanticDFLEngine().run_cluster_exemplar_designation_10nodes() returns valid step 13 data.
6. STEPS.md contains documentation for Step 13.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine
from backend.storyboard_10nodes import get_10node_step_data


@pytest.fixture
def client():
    return TestClient(app)


def test_step13_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/13 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/13")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 13
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 13: CLUSTER EXEMPLAR DESIGNATION"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] == 14

    res_post = client.post("/api/v1/storyboard/step/13")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 13


def test_step13_node_exemplar_flags(client):
    """Assert nodes 1, 3, 5, 7, 8, 9, 10 have is_exemplar == True and 2, 4, 6 have False."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    exemplar_ids = [1, 3, 5, 7, 8, 9, 10]
    non_exemplar_ids = [2, 4, 6]

    for nid in exemplar_ids:
        assert nodes[nid]["is_exemplar"] is True, f"Node {nid} should be an exemplar"

    for nid in non_exemplar_ids:
        assert nodes[nid]["is_exemplar"] is False, f"Node {nid} should NOT be an exemplar"


def test_step13_detailed_node_profiles(client):
    """Assert all 10 nodes have exact requested cluster_id, profile signatures, and exemplar mappings."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # Zone 2 (Initiator: Node 2)
    # Node 1: is_exemplar: True, cluster_id: "2-A", exemplar_for: [1, 2], profile_signature: [1, 2, 3]
    assert nodes[1]["is_exemplar"] is True
    assert nodes[1]["cluster_id"] == "2-A"
    assert nodes[1]["exemplar_for"] == [1, 2]
    assert nodes[1]["profile_signature"] == [1, 2, 3]

    # Node 2: is_exemplar: False, cluster_id: "2-A", exemplar_node_id: 1
    assert nodes[2]["is_exemplar"] is False
    assert nodes[2]["cluster_id"] == "2-A"
    assert nodes[2]["exemplar_node_id"] == 1

    # Node 3: is_exemplar: True, cluster_id: "2-B", exemplar_for: [3], profile_signature: [4, 5, 6]
    assert nodes[3]["is_exemplar"] is True
    assert nodes[3]["cluster_id"] == "2-B"
    assert nodes[3]["exemplar_for"] == [3]
    assert nodes[3]["profile_signature"] == [4, 5, 6]

    # Zone 4 (Initiator: Node 4)
    # Node 4: is_exemplar: False, cluster_id: "4-A", exemplar_node_id: 5
    assert nodes[4]["is_exemplar"] is False
    assert nodes[4]["cluster_id"] == "4-A"
    assert nodes[4]["exemplar_node_id"] == 5

    # Node 5: is_exemplar: True, cluster_id: "4-A", exemplar_for: [4, 5], profile_signature: [4, 5, 6]
    assert nodes[5]["is_exemplar"] is True
    assert nodes[5]["cluster_id"] == "4-A"
    assert nodes[5]["exemplar_for"] == [4, 5]
    assert nodes[5]["profile_signature"] == [4, 5, 6]

    # Node 6: is_exemplar: False, cluster_id: "4-B", exemplar_node_id: 7
    assert nodes[6]["is_exemplar"] is False
    assert nodes[6]["cluster_id"] == "4-B"
    assert nodes[6]["exemplar_node_id"] == 7

    # Node 7: is_exemplar: True, cluster_id: "4-B", exemplar_for: [6, 7], profile_signature: [7, 8, 9, 10]
    assert nodes[7]["is_exemplar"] is True
    assert nodes[7]["cluster_id"] == "4-B"
    assert nodes[7]["exemplar_for"] == [6, 7]
    assert nodes[7]["profile_signature"] == [7, 8, 9, 10]

    # Zone 8 (Initiator: Node 8)
    # Node 8: is_exemplar: True, cluster_id: "8-A", exemplar_for: [8], profile_signature: [4, 5, 6]
    assert nodes[8]["is_exemplar"] is True
    assert nodes[8]["cluster_id"] == "8-A"
    assert nodes[8]["exemplar_for"] == [8]
    assert nodes[8]["profile_signature"] == [4, 5, 6]

    # Node 9: is_exemplar: True, cluster_id: "8-B", exemplar_for: [9], profile_signature: [1, 2, 3]
    assert nodes[9]["is_exemplar"] is True
    assert nodes[9]["cluster_id"] == "8-B"
    assert nodes[9]["exemplar_for"] == [9]
    assert nodes[9]["profile_signature"] == [1, 2, 3]

    # Node 10: is_exemplar: True, cluster_id: "8-C", exemplar_for: [10], profile_signature: [8, 9, 10]
    assert nodes[10]["is_exemplar"] is True
    assert nodes[10]["cluster_id"] == "8-C"
    assert nodes[10]["exemplar_for"] == [10]
    assert nodes[10]["profile_signature"] == [8, 9, 10]


def test_step13_order_set_exemplar_events(client):
    """Assert packet traces for ORDER_SET_EXEMPLAR control packets."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    events = data.get("order_set_exemplar_events", [])
    assert len(events) == 7

    event_map = {(e["initiator_id"], e["exemplar_id"]): e for e in events}

    # C2 -> Node 1, C2 -> Node 3 (Direct 1-Hop)
    assert (2, 1) in event_map
    assert event_map[(2, 1)]["cluster_id"] == "2-A"
    assert event_map[(2, 1)]["profile_signature"] == [1, 2, 3]
    assert event_map[(2, 1)]["peer_members"] == [1, 2]
    assert event_map[(2, 1)]["path"] == [2, 1]

    assert (2, 3) in event_map
    assert event_map[(2, 3)]["cluster_id"] == "2-B"
    assert event_map[(2, 3)]["profile_signature"] == [4, 5, 6]
    assert event_map[(2, 3)]["peer_members"] == [3]
    assert event_map[(2, 3)]["path"] == [2, 3]

    # C4 -> Node 5, C4 -> Node 7 (Strictly Direct 1-Hop, NEVER via C6)
    assert (4, 5) in event_map
    assert event_map[(4, 5)]["cluster_id"] == "4-A"
    assert event_map[(4, 5)]["profile_signature"] == [4, 5, 6]
    assert event_map[(4, 5)]["peer_members"] == [4, 5]
    assert event_map[(4, 5)]["path"] == [4, 5]

    assert (4, 7) in event_map
    assert event_map[(4, 7)]["cluster_id"] == "4-B"
    assert event_map[(4, 7)]["profile_signature"] == [7, 8, 9, 10]
    assert event_map[(4, 7)]["peer_members"] == [6, 7]
    assert event_map[(4, 7)]["path"] == [4, 7], "C4 to C7 must be direct 1-hop physical link [4, 7]"
    assert 6 not in event_map[(4, 7)]["path"], "C4 to C7 must NEVER route via C6"

    # C8 -> Node 8 (local), C8 -> Node 9, C8 -> Node 10 (Direct 1-Hop)
    assert (8, 8) in event_map
    assert event_map[(8, 8)]["cluster_id"] == "8-A"
    assert event_map[(8, 8)]["profile_signature"] == [4, 5, 6]
    assert event_map[(8, 8)]["peer_members"] == [8]

    assert (8, 9) in event_map
    assert event_map[(8, 9)]["cluster_id"] == "8-B"
    assert event_map[(8, 9)]["profile_signature"] == [1, 2, 3]
    assert event_map[(8, 9)]["peer_members"] == [9]
    assert event_map[(8, 9)]["path"] == [8, 9]

    assert (8, 10) in event_map
    assert event_map[(8, 10)]["cluster_id"] == "8-C"
    assert event_map[(8, 10)]["profile_signature"] == [8, 9, 10]
    assert event_map[(8, 10)]["peer_members"] == [10]
    assert event_map[(8, 10)]["path"] == [8, 10]


def test_step13_engine_method():
    """Assert SemanticDFLEngine().run_cluster_exemplar_designation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_cluster_exemplar_designation_10nodes()
    assert result["step"] == 13
    assert result["total_steps"] == 14
    assert len(result["nodes"]) == 10
    assert len(result["edges"]) in (17, 18)
    assert result["total_edges"] == 18
    assert len(result["order_set_exemplar_events"]) == 7


def test_step13_steps_markdown_documentation():
    """Assert STEPS.md contains Step 13 cluster exemplar designation documentation."""
    steps_path = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_path.exists()
    content = steps_path.read_text(encoding="utf-8")
    assert "Step 13 — Intra-Zone Cluster Exemplar Designation & Profile Assignment" in content
    assert "ORDER_SET_EXEMPLAR" in content
    assert "Node 1" in content
    assert "Node 5" in content
    assert "Node 7" in content
    assert "Step 14 — Top-Level Initiator Election & Super-Zone Creation (Figure 3(e))" in content


def test_step13_frontend_modal_and_drag_safety():
    """Assert frontend/static/app.js implements defensive modal rendering and drag/click separation."""
    app_js_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # 1. Canvas Drag vs Click distinction logic
    assert "isDragging" in content
    assert "Math.hypot(e.clientX - startX, e.clientY - startY) > 5" in content
    assert "autoungrabify: true" in content

    # 2. Defensive renderNodeModal implementation
    assert "function renderNodeModal" in content
    assert "window.renderNodeModal = renderNodeModal" in content
    assert "window.showNodeModal = showNodeModal" in content
    assert "const isExemplar = Boolean(" in content
    assert "const exemplarFor = Array.isArray(" in content
    assert "const profileSig = Array.isArray(" in content
    assert "const exemplarNodeId = " in content
    assert "Regular Cluster Member" in content
    assert "DESIGNATED CLUSTER EXEMPLAR" in content

