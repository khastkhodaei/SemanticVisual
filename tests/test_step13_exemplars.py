"""Automated Verification Suite for Step 13: Intra-Zone Cluster Exemplar Designation & Member Assignment.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/13 return HTTP 200 with complete storyboard payload.
2. Packet traces ledger has exactly 10 traces:
   - Direct path [4, 6] exists with ORDER_ASSIGN_EXEMPLAR.
   - Direct path [4, 7] exists with ORDER_SET_EXEMPLAR.
   - Exact 1-hop physical routes for all 10 packet traces.
3. Exemplar designations & member assignments:
   - Nodes 1, 3, 5, 7, 8, 9, 10 have is_exemplar == True.
   - Nodes 2, 4, 6 have is_exemplar == False and assigned_exemplar equal to 1, 5, and 7 respectively.
4. Detailed node metadata for all 10 nodes matching exact specification.
5. SemanticDFLEngine().run_cluster_exemplar_designation_10nodes() returns valid step 13 data.
6. STEPS.md contains verbatim documentation for Step 13.
7. Frontend app.js implements required badges, formula, animation, and inspector modal safety.
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
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 13: INTRA-ZONE EXEMPLAR & MEMBER ASSIGNMENT"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert len(data_get["packet_traces"]) == 10

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

    # Specific assigned_exemplar checks for regular members
    assert nodes[2]["assigned_exemplar"] == 1
    assert nodes[4]["assigned_exemplar"] == 5
    assert nodes[6]["assigned_exemplar"] == 7


def test_step13_packet_traces_ledger(client):
    """Assert packet_traces length is exactly 10, with explicit [4, 6] and [4, 7] routes."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    traces = data.get("packet_traces", [])
    assert len(traces) == 10

    # Assert direct path [4, 6] exists with ORDER_ASSIGN_EXEMPLAR
    trace_4_6 = next((t for t in traces if t["path"] == [4, 6]), None)
    assert trace_4_6 is not None, "Direct 1-hop path [4, 6] must exist in packet traces"
    assert trace_4_6["type"] == "ORDER_ASSIGN_EXEMPLAR"
    assert trace_4_6["from"] == 4
    assert trace_4_6["to"] == 6
    assert trace_4_6["assigned_exemplar"] == 7
    assert trace_4_6["cluster_id"] == "4-B"
    assert trace_4_6["signature"] == [8, 9, 10]

    # Assert direct path [4, 7] exists with ORDER_SET_EXEMPLAR
    trace_4_7 = next((t for t in traces if t["path"] == [4, 7]), None)
    assert trace_4_7 is not None, "Direct 1-hop path [4, 7] must exist in packet traces"
    assert trace_4_7["type"] == "ORDER_SET_EXEMPLAR"
    assert trace_4_7["from"] == 4
    assert trace_4_7["to"] == 7
    assert trace_4_7["peers"] == [6, 7]
    assert trace_4_7["cluster_id"] == "4-B"
    assert trace_4_7["signature"] == [8, 9, 10]

    # Verify all 10 paths match the ledger
    expected_ledger = [
        {"from": 2, "to": 1, "path": [2, 1], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "2-A"},
        {"from": 2, "to": 3, "path": [2, 3], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "2-B"},
        {"from": 2, "to": 2, "path": [2], "type": "ORDER_ASSIGN_EXEMPLAR", "cluster_id": "2-A"},
        {"from": 4, "to": 5, "path": [4, 5], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "4-A"},
        {"from": 4, "to": 7, "path": [4, 7], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "4-B"},
        {"from": 4, "to": 6, "path": [4, 6], "type": "ORDER_ASSIGN_EXEMPLAR", "cluster_id": "4-B"},
        {"from": 4, "to": 4, "path": [4], "type": "ORDER_ASSIGN_EXEMPLAR", "cluster_id": "4-A"},
        {"from": 8, "to": 8, "path": [8], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "8-A"},
        {"from": 8, "to": 9, "path": [8, 9], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "8-B"},
        {"from": 8, "to": 10, "path": [8, 10], "type": "ORDER_SET_EXEMPLAR", "cluster_id": "8-C"},
    ]

    for exp in expected_ledger:
        match = next(
            (t for t in traces if t["from"] == exp["from"] and t["to"] == exp["to"] and t["path"] == exp["path"] and t["type"] == exp["type"]),
            None
        )
        assert match is not None, f"Missing expected trace {exp} in Step 13 packet ledger"


def test_step13_detailed_node_profiles(client):
    """Assert all 10 nodes have exact requested cluster_id, profile signatures, and exemplar mappings."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1: is_exemplar: True, assigned_exemplar: 1, cluster_id: "2-A", cluster_peers: [1, 2], profile_signature: [1, 2, 3]
    assert nodes[1]["is_exemplar"] is True
    assert nodes[1]["assigned_exemplar"] == 1
    assert nodes[1]["cluster_id"] == "2-A"
    assert nodes[1]["cluster_peers"] == [1, 2]
    assert nodes[1]["profile_signature"] == [1, 2, 3]

    # Node 2: is_exemplar: False, assigned_exemplar: 1, cluster_id: "2-A", cluster_peers: [1, 2], profile_signature: [1, 2, 3]
    assert nodes[2]["is_exemplar"] is False
    assert nodes[2]["assigned_exemplar"] == 1
    assert nodes[2]["cluster_id"] == "2-A"
    assert nodes[2]["cluster_peers"] == [1, 2]
    assert nodes[2]["profile_signature"] == [1, 2, 3]

    # Node 3: is_exemplar: True, assigned_exemplar: 3, cluster_id: "2-B", cluster_peers: [3], profile_signature: [4, 5, 6]
    assert nodes[3]["is_exemplar"] is True
    assert nodes[3]["assigned_exemplar"] == 3
    assert nodes[3]["cluster_id"] == "2-B"
    assert nodes[3]["cluster_peers"] == [3]
    assert nodes[3]["profile_signature"] == [4, 5, 6]

    # Node 4: is_exemplar: False, assigned_exemplar: 5, cluster_id: "4-A", cluster_peers: [4, 5], profile_signature: [4, 5, 6]
    assert nodes[4]["is_exemplar"] is False
    assert nodes[4]["assigned_exemplar"] == 5
    assert nodes[4]["cluster_id"] == "4-A"
    assert nodes[4]["cluster_peers"] == [4, 5]
    assert nodes[4]["profile_signature"] == [4, 5, 6]

    # Node 5: is_exemplar: True, assigned_exemplar: 5, cluster_id: "4-A", cluster_peers: [4, 5], profile_signature: [4, 5, 6]
    assert nodes[5]["is_exemplar"] is True
    assert nodes[5]["assigned_exemplar"] == 5
    assert nodes[5]["cluster_id"] == "4-A"
    assert nodes[5]["cluster_peers"] == [4, 5]
    assert nodes[5]["profile_signature"] == [4, 5, 6]

    # Node 6: is_exemplar: False, assigned_exemplar: 7, cluster_id: "4-B", cluster_peers: [6, 7], profile_signature: [8, 9, 10]
    assert nodes[6]["is_exemplar"] is False
    assert nodes[6]["assigned_exemplar"] == 7
    assert nodes[6]["cluster_id"] == "4-B"
    assert nodes[6]["cluster_peers"] == [6, 7]
    assert nodes[6]["profile_signature"] == [8, 9, 10]

    # Node 7: is_exemplar: True, assigned_exemplar: 7, cluster_id: "4-B", cluster_peers: [6, 7], profile_signature: [8, 9, 10]
    assert nodes[7]["is_exemplar"] is True
    assert nodes[7]["assigned_exemplar"] == 7
    assert nodes[7]["cluster_id"] == "4-B"
    assert nodes[7]["cluster_peers"] == [6, 7]
    assert nodes[7]["profile_signature"] == [8, 9, 10]

    # Node 8: is_exemplar: True, assigned_exemplar: 8, cluster_id: "8-A", cluster_peers: [8], profile_signature: [4, 5, 6]
    assert nodes[8]["is_exemplar"] is True
    assert nodes[8]["assigned_exemplar"] == 8
    assert nodes[8]["cluster_id"] == "8-A"
    assert nodes[8]["cluster_peers"] == [8]
    assert nodes[8]["profile_signature"] == [4, 5, 6]

    # Node 9: is_exemplar: True, assigned_exemplar: 9, cluster_id: "8-B", cluster_peers: [9], profile_signature: [1, 2, 3]
    assert nodes[9]["is_exemplar"] is True
    assert nodes[9]["assigned_exemplar"] == 9
    assert nodes[9]["cluster_id"] == "8-B"
    assert nodes[9]["cluster_peers"] == [9]
    assert nodes[9]["profile_signature"] == [1, 2, 3]

    # Node 10: is_exemplar: True, assigned_exemplar: 10, cluster_id: "8-C", cluster_peers: [10], profile_signature: [8, 9, 10]
    assert nodes[10]["is_exemplar"] is True
    assert nodes[10]["assigned_exemplar"] == 10
    assert nodes[10]["cluster_id"] == "8-C"
    assert nodes[10]["cluster_peers"] == [10]
    assert nodes[10]["profile_signature"] == [8, 9, 10]


def test_step13_engine_method():
    """Assert SemanticDFLEngine().run_cluster_exemplar_designation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_cluster_exemplar_designation_10nodes()
    assert result["step"] == 13
    assert len(result["nodes"]) == 10
    assert len(result["edges"]) in (17, 18)
    assert result["total_edges"] == 18
    assert len(result["packet_traces"]) == 10


def test_step13_steps_markdown_documentation():
    """Assert STEPS.md contains verbatim Step 13 cluster exemplar designation & member assignment documentation."""
    steps_path = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_path.exists()
    content = steps_path.read_text(encoding="utf-8")
    assert "Step 13 — Intra-Zone Cluster Exemplar Designation & Member Assignment" in content
    assert "ORDER_SET_EXEMPLAR" in content
    assert "ORDER_ASSIGN_EXEMPLAR" in content
    assert "10-Packet Trace Ledger (Direct 1-Hop Physical Routes)" in content
    assert "`[4, 6]`" in content
    assert "`[4, 7]`" in content
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
    assert "Bound Member" in content
    assert "window.handleNodeClick = handleNodeClick" in content
    assert "window.openNodeModal = openNodeModal" in content
    assert "window.selectNode = selectNode" in content
    assert "window.showFallbackModal = showFallbackModal" in content
    assert 'console.log("Clicked node:", node)' in content


def test_step13_payload_contains_all_base_and_exemplar_fields(client):
    """Verify each node object (1 to 10) explicitly contains all fields expected by earlier steps and Step 13."""
    res = client.get("/api/v1/storyboard/step/13")
    assert res.status_code == 200
    data = res.json()
    nodes = data.get("nodes", [])
    assert len(nodes) == 10

    required_fields = [
        "id", "zone", "role", "vrf_score", "data_distribution",
        "normalized_vector", "top_p_indices", "binary_mask",
        "is_exemplar", "assigned_exemplar", "cluster_id", "cluster_peers", "profile_signature"
    ]

    for n in nodes:
        for f in required_fields:
            assert f in n, f"Node {n.get('id')} missing required field '{f}'"
        assert isinstance(n["is_exemplar"], bool)
        assert isinstance(n["assigned_exemplar"], int)
        assert isinstance(n["cluster_id"], str)
        assert isinstance(n["cluster_peers"], list)
        assert isinstance(n["profile_signature"], list)
        assert isinstance(n["data_distribution"], dict)
        assert isinstance(n["normalized_vector"], list)
        assert isinstance(n["binary_mask"], list)
