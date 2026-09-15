"""Automated Verification Suite for Step 18: Super-Peer Designation & Hierarchical Overlay Binding.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/18 return HTTP 200 with complete storyboard payload.
2. Super-Peers:
   - Nodes 1, 5, 10 have is_super_peer == True.
   - Governed exemplars match [1, 9], [3, 5, 8], and [7, 10].
3. Non-super-peer nodes (2, 3, 4, 6, 7, 8, 9) have is_super_peer == False.
4. Exemplar bindings:
   - Node 1 -> SP 1 (self)
   - Node 9 -> SP 1
   - Node 3 -> SP 5
   - Node 5 -> SP 5 (self)
   - Node 8 -> SP 5
   - Node 7 -> SP 10
   - Node 10 -> SP 10 (self)
5. Regular members (Nodes 2, 4, 6) have bound_super_peer is None and valid exemplar_node_id representation.
6. Packet traces follow valid physical paths [4, 1, 2] and [4, 6, 8] with directive payloads.
7. SemanticDFLEngine().run_super_peer_designation_10nodes() produces valid structure.
8. STEPS.md contains documentation for Step 18.
9. Frontend elements in index.html and app.js support Step 18.
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


def test_step18_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/18 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/18")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 18
    assert data_get["phase_badge"] in (
        "ACTIVE PHASE: STEP 18: SUPER-ZONE DIRECTIVES DISPATCH (ORDER_SET_SUPER_CLUSTERS)",
        "ACTIVE PHASE: STEP 18: SUPER-PEER DESIGNATION & HIERARCHICAL BINDING",
    )
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] >= 18

    res_post = client.post("/api/v1/storyboard/step/18")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 18


def test_step18_super_peers_designation(client):
    """Assert Super-Peers (1, 5, 10) have is_super_peer == True and correct governed exemplars."""
    res = client.get("/api/v1/storyboard/step/18")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # Super-Peers
    assert nodes[1]["is_super_peer"] is True
    assert nodes[5]["is_super_peer"] is True
    assert nodes[10]["is_super_peer"] is True
    assert nodes[1]["governed_exemplars"] == [1, 9]
    assert nodes[5]["governed_exemplars"] == [3, 5, 8]
    assert nodes[10]["governed_exemplars"] == [7, 10]

    # Non-super-peers
    for nid in [2, 3, 4, 6, 7, 8, 9]:
        assert nodes[nid]["is_super_peer"] is False


def test_step18_exemplar_bindings(client):
    """Assert exemplar bindings to designated Super-Peers:
    - Node 1 -> SP 1, Node 9 -> SP 1
    - Node 3 -> SP 5, Node 5 -> SP 5, Node 8 -> SP 5
    - Node 7 -> SP 10, Node 10 -> SP 10
    """
    res = client.get("/api/v1/storyboard/step/18")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[1]["bound_super_peer"] == 1
    assert nodes[9]["bound_super_peer"] == 1
    assert nodes[3]["bound_super_peer"] == 5
    assert nodes[5]["bound_super_peer"] == 5
    assert nodes[8]["bound_super_peer"] == 5
    assert nodes[7]["bound_super_peer"] == 10
    assert nodes[10]["bound_super_peer"] == 10

    # Regular members do not bind directly to SP, represented by local exemplar
    assert nodes[2]["bound_super_peer"] is None
    assert nodes[4]["bound_super_peer"] is None
    assert nodes[6]["bound_super_peer"] is None

    assert nodes[2]["exemplar_node_id"] == 1
    assert nodes[4]["exemplar_node_id"] == 5
    assert nodes[6]["exemplar_node_id"] == 7


def test_step18_packet_traces_valid_paths(client):
    """Assert downstream directives follow valid physical multi-hop paths:
    - C4 -> C1 -> C2 (path [4, 1, 2])
    - C4 -> C6 -> C8 (path [4, 6, 8])
    """
    res = client.get("/api/v1/storyboard/step/18")
    assert res.status_code == 200
    data = res.json()
    traces = data.get("packet_traces", [])
    assert len(traces) == 2

    trace_map = {t["to"]: t for t in traces}
    assert 2 in trace_map
    assert 8 in trace_map

    t2 = trace_map[2]
    assert t2["from"] == 4
    assert t2["path"] == [4, 1, 2]
    assert t2["type"] in ("ORDER_SET_SUPER_CLUSTERS", "ORDER_SET_SUPER_PEER")
    assert "super_peer_SC1" in t2["directives"]

    t8 = trace_map[8]
    assert t8["from"] == 4
    assert t8["path"] == [4, 6, 8]
    assert t8["type"] in ("ORDER_SET_SUPER_CLUSTERS", "ORDER_SET_SUPER_PEER")
    assert "super_peer_SC3" in t8["directives"]


def test_step18_engine_method():
    """Verify SemanticDFLEngine().run_super_peer_designation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_super_peer_designation_10nodes()
    assert result["step"] == 18
    assert result["total_steps"] >= 18
    assert len(result["nodes"]) == 10
    assert result["top_initiator"] == 4
    assert len(result["super_peers"]) == 3
    assert len(result["packet_traces"]) == 2


def test_step18_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 18."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists(), "STEPS.md must exist"
    content = steps_file.read_text(encoding="utf-8")
    assert (
        "## Step 18 — Super-Zone Meta-Cluster & Super-Peer Directives Dispatch (ORDER_SET_SUPER_CLUSTERS)" in content
        or "## Step 18 — Super-Peer Designation & Hierarchical Overlay Binding" in content
    )
    assert "ORDER_SET_SUPER_CLUSTERS" in content or "ORDER_SET_SUPER_PEER" in content
    assert "Node 1" in content
    assert "Node 5" in content
    assert "Node 10" in content


def test_step18_frontend_components():
    """Verify index.html and app.js contain Step 18 support."""
    index_file = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    app_file = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert index_file.exists()
    assert app_file.exists()

    index_content = index_file.read_text(encoding="utf-8")
    assert 'id="stepNav18"' in index_content
    assert 'cardSuperPeerSection' in index_content

    app_content = app_file.read_text(encoding="utf-8")
    assert "renderStep18" in app_content
    assert "animateStep18SuperPeerDirectives" in app_content
    assert "super-peer-node" in app_content
