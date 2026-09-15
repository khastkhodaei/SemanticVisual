"""Automated Verification Suite for Step 18: Super-Zone Meta-Cluster & Super-Peer Directives Dispatch.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/18 return HTTP 200 with complete storyboard payload.
2. Directives dispatch strictly along super-zone paths:
   - C4 -> C1 -> C2 (path [4, 1, 2])
   - C4 -> C6 -> C8 (path [4, 6, 8])
   - type == ORDER_SET_SUPER_CLUSTERS
3. Node Lifecycle & Directive Status:
   - Node 4: SUPER_ZONE_DIRECTIVES_DISPATCHED
   - Nodes 2, 8: SUPER_ZONE_DIRECTIVES_RECEIVED
   - Nodes 1, 3, 5, 6, 7, 9, 10: AWAITING_INTRA_ZONE_NOTIFICATION
4. Super-Zone Directives Ledger:
   - SC-1: Classes [1, 2, 3], designated super-peer Node 1 (governs exemplars [1, 9])
   - SC-2: Classes [4, 5, 6], designated super-peer Node 5 (governs exemplars [3, 5, 8])
   - SC-3: Classes [8, 9, 10], designated super-peer Node 10 (governs exemplars [7, 10])
5. SemanticDFLEngine().run_super_peer_designation_10nodes() produces valid structure.
6. STEPS.md contains documentation for Step 18.
7. Frontend elements in index.html and app.js support Step 18.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine


@pytest.fixture
def client():
    return TestClient(app)


def test_step18_directives_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/18 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/18")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 18
    assert "ORDER_SET_SUPER_CLUSTERS" in data_get["phase_badge"]
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] >= 18

    res_post = client.post("/api/v1/storyboard/step/18")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 18


def test_step18_backbone_packet_traces(client):
    """Assert downstream directives follow valid super-zone backbone paths:
    - West relay: C4 -> C1 -> C2 (path [4, 1, 2])
    - East relay: C4 -> C6 -> C8 (path [4, 6, 8])
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
    assert t2["type"] == "ORDER_SET_SUPER_CLUSTERS"
    assert "super_clusters" in t2["payload"]

    t8 = trace_map[8]
    assert t8["from"] == 4
    assert t8["path"] == [4, 6, 8]
    assert t8["type"] == "ORDER_SET_SUPER_CLUSTERS"
    assert "super_clusters" in t8["payload"]


def test_step18_node_directive_statuses(client):
    """Assert node lifecycle and directive status:
    - Node 4: SUPER_ZONE_DIRECTIVES_DISPATCHED
    - Nodes 2, 8: SUPER_ZONE_DIRECTIVES_RECEIVED
    - Nodes 1, 3, 5, 6, 7, 9, 10: AWAITING_INTRA_ZONE_NOTIFICATION
    """
    res = client.get("/api/v1/storyboard/step/18")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[4]["directive_status"] == "SUPER_ZONE_DIRECTIVES_DISPATCHED"
    assert nodes[2]["directive_status"] == "SUPER_ZONE_DIRECTIVES_RECEIVED"
    assert nodes[8]["directive_status"] == "SUPER_ZONE_DIRECTIVES_RECEIVED"

    for nid in [1, 3, 5, 6, 7, 9, 10]:
        assert nodes[nid]["directive_status"] == "AWAITING_INTRA_ZONE_NOTIFICATION"


def test_step18_super_clusters_ledger(client):
    """Assert Super-Zone Directives Ledger contains 3 Global Super-Clusters and designated Super-Peers."""
    res = client.get("/api/v1/storyboard/step/18")
    assert res.status_code == 200
    data = res.json()

    ledger = data.get("super_clusters_ledger", [])
    assert len(ledger) == 3

    sc_map = {item["super_cluster_id"]: item for item in ledger}
    assert "SC-1" in sc_map
    assert "SC-2" in sc_map
    assert "SC-3" in sc_map

    # SC-1
    assert sc_map["SC-1"]["designated_super_peer"] == 1
    assert sc_map["SC-1"]["governed_exemplars"] == [1, 9]
    assert sc_map["SC-1"]["classes"] == [1, 2, 3]

    # SC-2
    assert sc_map["SC-2"]["designated_super_peer"] == 5
    assert sc_map["SC-2"]["governed_exemplars"] == [3, 5, 8]
    assert sc_map["SC-2"]["classes"] == [4, 5, 6]

    # SC-3
    assert sc_map["SC-3"]["designated_super_peer"] == 10
    assert sc_map["SC-3"]["governed_exemplars"] == [7, 10]
    assert sc_map["SC-3"]["classes"] == [8, 9, 10]


def test_step18_engine_method():
    """Verify SemanticDFLEngine().run_super_peer_designation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_super_peer_designation_10nodes()
    assert result["step"] == 18
    assert result["total_steps"] >= 18
    assert len(result["nodes"]) == 10
    assert result["top_initiator"] == 4
    assert len(result["packet_traces"]) == 2


def test_step18_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 18."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists(), "STEPS.md must exist"
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 18 — Super-Zone Meta-Cluster & Super-Peer Directives Dispatch (ORDER_SET_SUPER_CLUSTERS)" in content
    assert "ORDER_SET_SUPER_CLUSTERS" in content
    assert "Node 1" in content
    assert "Node 5" in content
    assert "Node 10" in content
    assert "SUPER_ZONE_DIRECTIVES_DISPATCHED" in content
    assert "SUPER_ZONE_DIRECTIVES_RECEIVED" in content
    assert "AWAITING_INTRA_ZONE_NOTIFICATION" in content


def test_step18_frontend_components():
    """Verify index.html and app.js contain Step 18 support."""
    index_file = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    app_file = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert index_file.exists()
    assert app_file.exists()

    index_content = index_file.read_text(encoding="utf-8")
    assert 'id="stepNav18"' in index_content

    app_content = app_file.read_text(encoding="utf-8")
    assert "renderStep18" in app_content
