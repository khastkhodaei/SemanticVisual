"""Automated Verification Suite for Step 16: Zone Catalog Response & Global Catalog Aggregation at C4.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/16 return HTTP 200 with complete storyboard payload.
2. Step 16 response packet traces:
   - Packet 1: from=2, to=4, path=[2, 1, 4], type="REP_CLUSTER_CATALOG"
   - Packet 2: from=8, to=4, path=[8, 6, 4], type="REP_CLUSTER_CATALOG"
3. Node 4 contains global_cluster_catalog of 7 items and total_registered_clusters == 7.
4. All 7 exemplars [1, 3, 5, 7, 8, 9, 10] are present in the global catalog.
5. Node query/response states:
   - Node 4: aggregation_status == "GLOBAL_CATALOG_ASSEMBLED"
   - Node 2: catalog_response_status == "RESPONSE_DISPATCHED", reported_clusters contains 2-A and 2-B
   - Node 8: catalog_response_status == "RESPONSE_DISPATCHED", reported_clusters contains 8-A, 8-B, 8-C
6. Preservation of base data, Step 13 exemplars, and Step 14 super-zone structure.
7. SemanticDFLEngine().run_zone_catalog_response_10nodes() returns valid step 16 data.
8. STEPS.md contains documentation for Step 16 with REP_CLUSTER_CATALOG and Global Cluster Registry.
9. Frontend elements in index.html and app.js support Step 16.
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


def test_step16_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/16 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/16")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 16
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 16: ZONE CATALOG RESPONSE & GLOBAL AGGREGATION"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] == 16

    res_post = client.post("/api/v1/storyboard/step/16")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 16


def test_step16_packet_traces_and_routes(client):
    """Assert response packet traces contain paths [2, 1, 4] and [8, 6, 4] with type REP_CLUSTER_CATALOG."""
    res = client.get("/api/v1/storyboard/step/16")
    assert res.status_code == 200
    data = res.json()

    traces = data.get("packet_events") or data.get("packet_traces", [])
    assert len(traces) == 2

    west_trace = next((t for t in traces if t["from"] == 2 and t["to"] == 4), None)
    assert west_trace is not None
    assert west_trace["path"] == [2, 1, 4]
    assert west_trace["type"] == "REP_CLUSTER_CATALOG"
    assert len(west_trace["payload"]) == 2

    east_trace = next((t for t in traces if t["from"] == 8 and t["to"] == 4), None)
    assert east_trace is not None
    assert east_trace["path"] == [8, 6, 4]
    assert east_trace["type"] == "REP_CLUSTER_CATALOG"
    assert len(east_trace["payload"]) == 3


def test_step16_node4_global_cluster_catalog(client):
    """Assert Node 4 contains global_cluster_catalog of 7 items and all 7 exemplars are present."""
    res = client.get("/api/v1/storyboard/step/16")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}
    node4 = nodes[4]

    assert node4["aggregation_status"] == "GLOBAL_CATALOG_ASSEMBLED"
    assert node4["total_registered_clusters"] == 7
    catalog = node4.get("global_cluster_catalog", [])
    assert len(catalog) == 7

    exemplars = sorted([c["exemplar"] for c in catalog])
    assert exemplars == [1, 3, 5, 7, 8, 9, 10]

    cluster_ids = sorted([c["cluster_id"] for c in catalog])
    assert cluster_ids == ["2-A", "2-B", "4-A", "4-B", "8-A", "8-B", "8-C"]

    # Verify specific clusters and zones
    c2a = next(c for c in catalog if c["cluster_id"] == "2-A")
    assert c2a["zone"] == 2
    assert c2a["exemplar"] == 1
    assert c2a["members"] == [1, 2]
    assert c2a["signature"] == [1, 2, 3]

    c4a = next(c for c in catalog if c["cluster_id"] == "4-A")
    assert c4a["zone"] == 4
    assert c4a["exemplar"] == 5
    assert c4a["members"] == [4, 5]
    assert c4a["signature"] == [4, 5, 6]

    c8c = next(c for c in catalog if c["cluster_id"] == "8-C")
    assert c8c["zone"] == 8
    assert c8c["exemplar"] == 10
    assert c8c["members"] == [10]
    assert c8c["signature"] == [8, 9, 10]


def test_step16_nodes_2_and_8_reported_clusters(client):
    """Assert Nodes 2 and 8 report their respective intra-zone clusters."""
    res = client.get("/api/v1/storyboard/step/16")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[2]["catalog_response_status"] == "RESPONSE_DISPATCHED"
    assert len(nodes[2]["reported_clusters"]) == 2
    assert [c["cluster_id"] for c in nodes[2]["reported_clusters"]] == ["2-A", "2-B"]

    assert nodes[8]["catalog_response_status"] == "RESPONSE_DISPATCHED"
    assert len(nodes[8]["reported_clusters"]) == 3
    assert [c["cluster_id"] for c in nodes[8]["reported_clusters"]] == ["8-A", "8-B", "8-C"]


def test_step16_preserves_base_exemplar_and_super_zone_data(client):
    """Assert Step 16 maintains all base data, Step 13 exemplars, and Step 14 super-zone metadata."""
    res = client.get("/api/v1/storyboard/step/16")
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


def test_step16_engine_method():
    """Verify SemanticDFLEngine().run_zone_catalog_response_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_zone_catalog_response_10nodes()
    assert result["step"] == 16
    assert result["total_steps"] == 16
    assert len(result["nodes"]) == 10
    assert result["top_initiator"] == 4
    assert len(result["global_cluster_catalog"]) == 7
    assert len(result["packet_events"]) == 2


def test_step16_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 16 with REP_CLUSTER_CATALOG."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 16 — Zone Catalog Response & Global Catalog Aggregation at C4" in content
    assert "REP_CLUSTER_CATALOG" in content
    assert "[2, 1, 4]" in content
    assert "[8, 6, 4]" in content
    assert "GLOBAL_CATALOG_ASSEMBLED" in content
    assert "RESPONSE_DISPATCHED" in content
    assert "7 Clusters" in content


def test_step16_frontend_elements_and_logic(client):
    """Verify frontend template and app.js contain Step 16 UI elements and rendering logic."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "stepNav16" in res_index.text
    assert "cardGlobalCatalogSection" in res_index.text
    assert "cardGlobalCatalogBadge" in res_index.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "renderStep16" in res_js.text
    assert "animateStep16CatalogResponse" in res_js.text
    assert "drawCatalogResponsePacket" in res_js.text
    assert "ACTIVE PHASE: STEP 16: ZONE CATALOG RESPONSE & GLOBAL AGGREGATION" in res_js.text
    assert "REP_CATALOG (Z2)" in res_js.text
    assert "REP_CATALOG (Z8)" in res_js.text
    assert "7 CLUSTERS AGGREGATED" in res_js.text
