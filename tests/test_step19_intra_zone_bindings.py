"""Automated Verification Suite for Step 19: Intra-Zone Super-Peer Designation & Exemplar Hierarchical Binding.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/19 return HTTP 200 with complete storyboard payload.
2. Direct 1-hop physical control traces within each zone:
   - Zone 2:
     * C2 -> C1 (path [2, 1], type ORDER_SET_SUPER_PEER, super_cluster SC-1, subordinates [1, 9])
     * C2 -> C3 (path [2, 3], type ORDER_BIND_EXEMPLAR, super_cluster SC-2, bound_sp 5)
   - Zone 4:
     * C4 -> C5 (path [4, 5], type ORDER_SET_SUPER_PEER, super_cluster SC-2, subordinates [3, 5, 8])
     * C4 -> C7 (path [4, 7], type ORDER_BIND_EXEMPLAR, super_cluster SC-3, bound_sp 10)
   - Zone 8:
     * C8 -> C10 (path [8, 10], type ORDER_SET_SUPER_PEER, super_cluster SC-3, subordinates [7, 10])
     * C8 -> C9 (path [8, 9], type ORDER_BIND_EXEMPLAR, super_cluster SC-1, bound_sp 1)
     * C8 local state update (path [8], type ORDER_BIND_EXEMPLAR, bound_sp 5)
3. Super-Peers:
   - Strictly nodes 1, 5, 10 have is_super_peer == True.
   - Governing assignments:
     * Node 1 -> SC-1, governed exemplars [1, 9]
     * Node 5 -> SC-2, governed exemplars [3, 5, 8]
     * Node 10 -> SC-3, governed exemplars [7, 10]
4. Exemplar Bindings:
   - Node 9 -> SP 1
   - Node 3 -> SP 5
   - Node 8 -> SP 5
   - Node 7 -> SP 10
   - Super-peers bind to themselves (1 -> 1, 5 -> 5, 10 -> 10).
5. Regular Members:
   - Nodes 2, 4, 6 have is_super_peer == False and is_exemplar == False.
6. SemanticDFLEngine().run_intra_zone_bindings_10nodes() produces valid structure.
7. STEPS.md contains documentation for Step 19.
8. Frontend components in index.html and app.js support Step 19.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine


@pytest.fixture
def client():
    return TestClient(app)


def test_step19_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/19 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/19")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 19
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 19: INTRA-ZONE SUPER-PEER & EXEMPLAR BINDING"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] >= 19

    res_post = client.post("/api/v1/storyboard/step/19")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 19


def test_step19_direct_1hop_packet_traces(client):
    """Assert packet traces use strict direct 1-hop physical paths within each zone."""
    res = client.get("/api/v1/storyboard/step/19")
    assert res.status_code == 200
    data = res.json()
    traces = data.get("packet_traces", [])
    assert len(traces) == 7

    # Map traces by (from, to)
    trace_map = {(t["from"], t["to"]): t for t in traces}

    # Zone 2 traces
    assert (2, 1) in trace_map
    t2_1 = trace_map[(2, 1)]
    assert t2_1["path"] == [2, 1]
    assert t2_1["type"] == "ORDER_SET_SUPER_PEER"
    assert t2_1["super_cluster"] == "SC-1"
    assert t2_1["subordinates"] == [1, 9]

    assert (2, 3) in trace_map
    t2_3 = trace_map[(2, 3)]
    assert t2_3["path"] == [2, 3]
    assert t2_3["type"] == "ORDER_BIND_EXEMPLAR"
    assert t2_3["super_cluster"] == "SC-2"
    assert t2_3["bound_sp"] == 5

    # Zone 4 traces
    assert (4, 5) in trace_map
    t4_5 = trace_map[(4, 5)]
    assert t4_5["path"] == [4, 5]
    assert t4_5["type"] == "ORDER_SET_SUPER_PEER"
    assert t4_5["super_cluster"] == "SC-2"
    assert t4_5["subordinates"] == [3, 5, 8]

    assert (4, 7) in trace_map
    t4_7 = trace_map[(4, 7)]
    assert t4_7["path"] == [4, 7]
    assert t4_7["type"] == "ORDER_BIND_EXEMPLAR"
    assert t4_7["super_cluster"] == "SC-3"
    assert t4_7["bound_sp"] == 10

    # Zone 8 traces
    assert (8, 10) in trace_map
    t8_10 = trace_map[(8, 10)]
    assert t8_10["path"] == [8, 10]
    assert t8_10["type"] == "ORDER_SET_SUPER_PEER"
    assert t8_10["super_cluster"] == "SC-3"
    assert t8_10["subordinates"] == [7, 10]

    assert (8, 9) in trace_map
    t8_9 = trace_map[(8, 9)]
    assert t8_9["path"] == [8, 9]
    assert t8_9["type"] == "ORDER_BIND_EXEMPLAR"
    assert t8_9["super_cluster"] == "SC-1"
    assert t8_9["bound_sp"] == 1

    assert (8, 8) in trace_map
    t8_8 = trace_map[(8, 8)]
    assert t8_8["path"] == [8]
    assert t8_8["type"] == "ORDER_BIND_EXEMPLAR"
    assert t8_8["bound_sp"] == 5


def test_step19_super_peers_designation(client):
    """Assert Super-Peers (1, 5, 10) have is_super_peer == True strictly."""
    res = client.get("/api/v1/storyboard/step/19")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # Strictly nodes 1, 5, 10 are super-peers
    for nid in [1, 5, 10]:
        assert nodes[nid]["is_super_peer"] is True

    for nid in [2, 3, 4, 6, 7, 8, 9]:
        assert nodes[nid]["is_super_peer"] is False

    # Governed exemplars
    assert nodes[1]["governed_exemplars"] == [1, 9]
    assert nodes[5]["governed_exemplars"] == [3, 5, 8]
    assert nodes[10]["governed_exemplars"] == [7, 10]


def test_step19_exemplar_bindings(client):
    """Assert exemplar bindings to designated Super-Peers:
    - Node 1 -> SP 1 (self)
    - Node 9 -> SP 1
    - Node 3 -> SP 5
    - Node 5 -> SP 5 (self)
    - Node 8 -> SP 5
    - Node 7 -> SP 10
    - Node 10 -> SP 10 (self)
    """
    res = client.get("/api/v1/storyboard/step/19")
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

    # Regular members (Nodes 2, 4, 6)
    assert nodes[2]["bound_super_peer"] is None
    assert nodes[4]["bound_super_peer"] is None
    assert nodes[6]["bound_super_peer"] is None
    assert nodes[2]["is_exemplar"] is False
    assert nodes[4]["is_exemplar"] is False
    assert nodes[6]["is_exemplar"] is False


def test_step19_engine_method():
    """Verify SemanticDFLEngine().run_intra_zone_bindings_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_intra_zone_bindings_10nodes()
    assert result["step"] == 19
    assert result["total_steps"] >= 19
    assert len(result["nodes"]) == 10
    assert len(result["packet_traces"]) == 7


def test_step19_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 19."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists(), "STEPS.md must exist"
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 19 — Intra-Zone Super-Peer Designation & Exemplar Hierarchical Binding" in content
    assert "ORDER_SET_SUPER_PEER" in content
    assert "ORDER_BIND_EXEMPLAR" in content
    assert "[2, 1]" in content
    assert "[2, 3]" in content
    assert "[4, 5]" in content
    assert "[4, 7]" in content
    assert "[8, 10]" in content
    assert "[8, 9]" in content


def test_step19_frontend_components():
    """Verify index.html and app.js contain Step 19 support."""
    index_file = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    app_file = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert index_file.exists()
    assert app_file.exists()

    index_content = index_file.read_text(encoding="utf-8")
    assert 'id="stepNav19"' in index_content

    app_content = app_file.read_text(encoding="utf-8")
    assert "renderStep19" in app_content
    assert "animateStep19IntraZoneDirectives" in app_content
