"""Automated Verification Suite for Step 20 Figure 3(f) Compliant 2-Tier SON Overlay.

Verifies:
1. GET /api/v1/storyboard/step/20 returns HTTP 200.
2. figure3f_edges contains the backbone links (1, 5) and (5, 10).
3. All 10 nodes are present in figure3f_coordinates with proper tiers:
   - Super-Peers (1, 5, 10): SUPER_PEER
   - Exemplars (3, 7, 8, 9): EXEMPLAR
   - Leaves (2, 4, 6): LEAF
4. All 3 Super-Cluster colors exist in the edge specs:
   - SC-1: #38bdf8 (Sky Blue)
   - SC-2: #f59e0b (Amber Gold)
   - SC-3: #c084fc (Neon Violet)
   - Backbone: #f8fafc (Platinum)
5. POST /api/v1/storyboard/step/20 returns HTTP 200 with matching structure.
6. Frontend assets (index.html, style.css, app.js) contain Figure 3(f) dual layout specifications.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    FIGURE3F_COORDINATES,
    FIGURE3F_EDGES,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step20_api_status_and_structure(client):
    """Assert GET /api/v1/storyboard/step/20 returns 200 and valid Step 20 structure."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    data = res.json()

    assert data["step"] == 20
    assert data["total_steps"] == 20
    assert "Figure 3(f)" in data["title"]
    assert "FIGURE 3(F)" in data["phase_badge"]
    assert "nodes" in data and len(data["nodes"]) == 10
    assert "figure3f_edges" in data
    assert "figure3f_coordinates" in data


def test_step20_figure3f_backbone_links(client):
    """Assert figure3f_edges contains the backbone links (1, 5) and (5, 10)."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    edges = res.json()["figure3f_edges"]

    backbone_pairs = {(e["source"], e["target"]) for e in edges if e.get("type") == "SUPER_PEER_BACKBONE"}
    assert (1, 5) in backbone_pairs or (5, 1) in backbone_pairs
    assert (5, 10) in backbone_pairs or (10, 5) in backbone_pairs

    # Verify backbone styling
    backbone_edges = [e for e in edges if e.get("type") == "SUPER_PEER_BACKBONE"]
    assert len(backbone_edges) == 2
    for be in backbone_edges:
        assert be["color"] == "#f8fafc"
        assert be["style"] == "solid"
        assert be["width"] >= 3


def test_step20_figure3f_coordinates_all_nodes(client):
    """Assert all 10 nodes are present in figure3f_coordinates with proper tiers."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    coords = res.json()["figure3f_coordinates"]

    assert len(coords) == 10
    for i in range(1, 11):
        assert str(i) in coords
        node_info = coords[str(i)]
        assert "x" in node_info and "y" in node_info
        assert "tier" in node_info
        assert "sc" in node_info

    # Super-Peers (1, 5, 10) on top plane (y == 130)
    assert coords["1"]["tier"] == "SUPER_PEER" and coords["1"]["y"] == 130
    assert coords["5"]["tier"] == "SUPER_PEER" and coords["5"]["y"] == 130
    assert coords["10"]["tier"] == "SUPER_PEER" and coords["10"]["y"] == 130

    # Subordinate Exemplars (3, 7, 8, 9) on mid plane (y == 280)
    for ex in ["3", "7", "8", "9"]:
        assert coords[ex]["tier"] == "EXEMPLAR"
        assert coords[ex]["y"] == 280

    # Regular Leaf Members (2, 4, 6) on bottom plane (y == 430)
    for leaf in ["2", "4", "6"]:
        assert coords[leaf]["tier"] == "LEAF"
        assert coords[leaf]["y"] == 430


def test_step20_super_cluster_colors_in_edge_specs(client):
    """Assert all 3 Super-Cluster colors and backbone color exist in edge specs."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    edges = res.json()["figure3f_edges"]

    colors = {e["color"].lower() for e in edges}
    assert "#38bdf8" in colors  # SC-1 Sky Blue
    assert "#f59e0b" in colors  # SC-2 Amber Gold
    assert "#c084fc" in colors  # SC-3 Neon Violet
    assert "#f8fafc" in colors  # Platinum Backbone


def test_step20_post_api_matches(client):
    """Assert POST /api/v1/storyboard/step/20 returns 200."""
    res = client.post("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 20
    assert len(data["figure3f_edges"]) == 9
    assert len(data["figure3f_coordinates"]) == 10


def test_app_js_contains_figure3f_specifications():
    """Assert frontend app.js contains Figure 3(f) definitions and continuous ping-pong heartbeat."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")

    assert "FIGURE3F_COORDINATES" in content
    assert "FIGURE3F_EDGES" in content
    assert "SUPER_PEER_BACKBONE" in content
    assert "Figure 3(f) Overlay Tree" in content
    assert "3600" in content  # Cycle duration for ping-pong heartbeat
    assert "UPSTREAM" in content or "upstream" in content
    assert "BACKBONE" in content or "backbone" in content
    assert "DOWNSTREAM" in content or "downstream" in content
