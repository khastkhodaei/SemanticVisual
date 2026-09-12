"""Automated Verification Suite for Step 15: Top-Level Catalog Query Dispatch (REQ_CLUSTER_CATALOG).

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/15 return HTTP 200 with complete storyboard payload.
2. Step 15 packet traces:
   - Packet 1: from=4, to=2, path=[4, 1, 2], type="REQ_CLUSTER_CATALOG", root=4
   - Packet 2: from=4, to=8, path=[4, 6, 8], type="REQ_CLUSTER_CATALOG", root=4
3. Node query states:
   - Node 4: query_status == "DISPATCHED_TO_ALL_INITIATORS"
   - Node 2: query_status == "RECEIVED_PENDING_RESPONSE"
   - Node 8: query_status == "RECEIVED_PENDING_RESPONSE"
4. Preservation of base data, Step 13 exemplars, and Step 14 super-zone structure.
5. SemanticDFLEngine().run_top_level_catalog_query_10nodes() returns valid step 15 data.
6. STEPS.md contains documentation for Step 15 with REQ_CLUSTER_CATALOG.
7. Frontend elements in index.html and app.js support Step 15.
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


def test_step15_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/15 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/15")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 15
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 15: TOP-LEVEL CATALOG QUERY DISPATCH"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] in (15, 16, 17)

    res_post = client.post("/api/v1/storyboard/step/15")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 15


def test_step15_packet_traces_and_routes(client):
    """Assert packet traces contain paths [4, 1, 2] and [4, 6, 8] with type REQ_CLUSTER_CATALOG and root 4."""
    res = client.get("/api/v1/storyboard/step/15")
    assert res.status_code == 200
    data = res.json()

    traces = data.get("packet_events") or data.get("packet_traces", [])
    assert len(traces) == 2

    west_trace = next((t for t in traces if t["to"] == 2), None)
    assert west_trace is not None
    assert west_trace["from"] == 4
    assert west_trace["path"] == [4, 1, 2]
    assert west_trace["type"] == "REQ_CLUSTER_CATALOG"
    assert west_trace["root"] == 4

    east_trace = next((t for t in traces if t["to"] == 8), None)
    assert east_trace is not None
    assert east_trace["from"] == 4
    assert east_trace["path"] == [4, 6, 8]
    assert east_trace["type"] == "REQ_CLUSTER_CATALOG"
    assert east_trace["root"] == 4


def test_step15_node_query_status(client):
    """Assert Node 4 is DISPATCHED_TO_ALL_INITIATORS and Nodes 2 & 8 are RECEIVED_PENDING_RESPONSE."""
    res = client.get("/api/v1/storyboard/step/15")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[4]["query_status"] == "DISPATCHED_TO_ALL_INITIATORS"
    assert len(nodes[4]["outbound_catalog_requests"]) == 2

    assert nodes[2]["query_status"] == "RECEIVED_PENDING_RESPONSE"
    assert nodes[2]["received_catalog_query"]["from"] == 4
    assert nodes[2]["received_catalog_query"]["path"] == [4, 1, 2]
    assert nodes[2]["received_catalog_query"]["type"] == "REQ_CLUSTER_CATALOG"

    assert nodes[8]["query_status"] == "RECEIVED_PENDING_RESPONSE"
    assert nodes[8]["received_catalog_query"]["from"] == 4
    assert nodes[8]["received_catalog_query"]["path"] == [4, 6, 8]
    assert nodes[8]["received_catalog_query"]["type"] == "REQ_CLUSTER_CATALOG"


def test_step15_preserves_base_exemplar_and_super_zone_data(client):
    """Assert Step 15 maintains all base data, Step 13 exemplars, and Step 14 super-zone metadata."""
    res = client.get("/api/v1/storyboard/step/15")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # Exemplars preserved
    assert nodes[1]["is_exemplar"] is True
    assert nodes[1]["cluster_id"] == "2-A"
    assert nodes[3]["is_exemplar"] is True
    assert nodes[3]["cluster_id"] == "2-B"
    assert nodes[5]["is_exemplar"] is True
    assert nodes[5]["cluster_id"] == "4-A"
    assert nodes[7]["is_exemplar"] is True
    assert nodes[7]["cluster_id"] == "4-B"

    # Super-Zone metadata preserved
    assert nodes[4]["is_top_initiator"] is True
    assert nodes[4]["top_level_zone"] == "Z_TOP"
    assert nodes[2]["top_level_zone"] == "Z_TOP"
    assert nodes[8]["top_level_zone"] == "Z_TOP"


def test_step15_engine_method():
    """Verify SemanticDFLEngine().run_top_level_catalog_query_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_top_level_catalog_query_10nodes()
    assert result["step"] == 15
    assert result["total_steps"] in (15, 16, 17)
    assert len(result["nodes"]) == 10
    assert result["top_initiator"] == 4
    assert len(result["packet_events"]) == 2


def test_step15_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 15 with REQ_CLUSTER_CATALOG."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 15 — Top-Level Catalog Query Dispatch (`REQ_CLUSTER_CATALOG`)" in content
    assert "REQ_CLUSTER_CATALOG" in content
    assert "[4, 1, 2]" in content
    assert "[4, 6, 8]" in content
    assert "DISPATCHED_TO_ALL_INITIATORS" in content
    assert "RECEIVED_PENDING_RESPONSE" in content


def test_step15_frontend_elements_and_logic(client):
    """Verify frontend template and app.js contain Step 15 UI elements and rendering logic."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "stepNav15" in res_index.text
    assert "cardCatalogReqSection" in res_index.text
    assert "cardCatalogReqBadge" in res_index.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "renderStep15" in res_js.text
    assert "animateStep15CatalogQuery" in res_js.text
    assert "drawCatalogQueryPacket" in res_js.text
    assert "ACTIVE PHASE: STEP 15: TOP-LEVEL CATALOG QUERY DISPATCH" in res_js.text
    assert "Outbound Query: REQ_CLUSTER_CATALOG dispatched to C2 and C8" in res_js.text
    assert "Inbound Query Received: Preparing intra-zone cluster catalog response" in res_js.text
