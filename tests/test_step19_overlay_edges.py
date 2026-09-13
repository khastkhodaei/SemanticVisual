"""Automated Verification Suite for Step 19: Semantic Overlay Network (SON) Logical Topology Formation.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/19 return HTTP 200 with complete storyboard payload.
2. semantic_overlay_edges contains exactly 7 logical links:
   - Exactly 3 Tier-1 links
   - Exactly 4 Tier-2 links
3. Tier-1 links exist:
   - (2, 1) in SC-1 (MEMBER_TO_EXEMPLAR)
   - (4, 5) in SC-2 (MEMBER_TO_EXEMPLAR)
   - (6, 7) in SC-3 (MEMBER_TO_EXEMPLAR)
4. Tier-2 links exist:
   - (9, 1) in SC-1 (EXEMPLAR_TO_SUPERPEER)
   - (3, 5) in SC-2 (EXEMPLAR_TO_SUPERPEER)
   - (8, 5) in SC-2 (EXEMPLAR_TO_SUPERPEER)
   - (7, 10) in SC-3 (EXEMPLAR_TO_SUPERPEER)
5. active_overlay_neighbors on each node matches expected topology:
   - Node 1: [2, 9]
   - Node 2: [1]
   - Node 3: [5]
   - Node 4: [5]
   - Node 5: [3, 4, 8]
   - Node 6: [7]
   - Node 7: [6, 10]
   - Node 8: [5]
   - Node 9: [1]
   - Node 10: [7]
6. SemanticDFLEngine().run_semantic_overlay_formation_10nodes() produces valid structure.
7. STEPS.md contains documentation for Step 19.
8. Frontend elements in index.html and app.js support Step 19.
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


def test_step19_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/19 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/19")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 19
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 19: SEMANTIC OVERLAY NETWORK (SON) FORMATION"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] == 19

    res_post = client.post("/api/v1/storyboard/step/19")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 19


def test_step19_seven_overlay_edges_structure(client):
    """Assert semantic_overlay_edges contains exactly 7 logical links (3 Tier-1, 4 Tier-2)."""
    res = client.get("/api/v1/storyboard/step/19")
    assert res.status_code == 200
    data = res.json()

    overlay_edges = data.get("semantic_overlay_edges", [])
    assert len(overlay_edges) == 7

    tier1 = [e for e in overlay_edges if e["tier"] == 1]
    tier2 = [e for e in overlay_edges if e["tier"] == 2]
    assert len(tier1) == 3
    assert len(tier2) == 4

    # Validate Tier 1 links
    t1_pairs = {(e["source"], e["target"]): e for e in tier1}
    assert (2, 1) in t1_pairs
    assert (4, 5) in t1_pairs
    assert (6, 7) in t1_pairs
    assert t1_pairs[(2, 1)]["super_cluster"] == "SC-1"
    assert t1_pairs[(4, 5)]["super_cluster"] == "SC-2"
    assert t1_pairs[(6, 7)]["super_cluster"] == "SC-3"

    # Validate Tier 2 links
    t2_pairs = {(e["source"], e["target"]): e for e in tier2}
    assert (9, 1) in t2_pairs
    assert (3, 5) in t2_pairs
    assert (8, 5) in t2_pairs
    assert (7, 10) in t2_pairs
    assert t2_pairs[(9, 1)]["super_cluster"] == "SC-1"
    assert t2_pairs[(3, 5)]["super_cluster"] == "SC-2"
    assert t2_pairs[(8, 5)]["super_cluster"] == "SC-2"
    assert t2_pairs[(7, 10)]["super_cluster"] == "SC-3"


def test_step19_node_active_overlay_neighbors(client):
    """Assert active_overlay_neighbors on each node matches the 2-tier SON topology."""
    res = client.get("/api/v1/storyboard/step/19")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    expected_neighbors = {
        1: {2, 9},
        2: {1},
        3: {5},
        4: {5},
        5: {3, 4, 8},
        6: {7},
        7: {6, 10},
        8: {5},
        9: {1},
        10: {7},
    }

    for nid, expected in expected_neighbors.items():
        actual = set(nodes[nid]["active_overlay_neighbors"])
        assert actual == expected, f"Node {nid} overlay neighbors {actual} != {expected}"


def test_step19_engine_method():
    """Verify SemanticDFLEngine().run_semantic_overlay_formation_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_semantic_overlay_formation_10nodes()
    assert result["step"] == 19
    assert result["total_steps"] == 19
    assert len(result["nodes"]) == 10
    assert len(result["semantic_overlay_edges"]) == 7


def test_step19_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 19."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists(), "STEPS.md must exist"
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 19 — Semantic Overlay Network (SON) Logical Topology Formation" in content
    assert "MEMBER_TO_EXEMPLAR" in content
    assert "EXEMPLAR_TO_SUPERPEER" in content
    assert "7" in content


def test_step19_frontend_components():
    """Verify index.html and app.js contain Step 19 support."""
    index_file = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    app_file = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert index_file.exists()
    assert app_file.exists()

    index_content = index_file.read_text(encoding="utf-8")
    assert 'id="stepNav19"' in index_content
    assert 'cardOverlaySection' in index_content

    app_content = app_file.read_text(encoding="utf-8")
    assert "renderStep19" in app_content
    assert "animateStep19SemanticOverlay" in app_content
    assert "dimmed-physical" in app_content
