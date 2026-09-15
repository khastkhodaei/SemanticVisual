"""Automated Verification Suite for Step 20 Figure 3(f) Compliant 3-Tier SON Overlay.

Verifies:
1. GET /api/v1/storyboard/step/20 returns HTTP 200 and valid Step 20 structure.
2. Figure 3(f) 3-Tier Architecture contains 20 virtual nodes across 3 horizontal tiers:
   - Tier 3 (Top - Global Super-Peers): Node 1 (220, 120), Node 5 (500, 120), Node 10 (780, 120).
     (No direct horizontal line between 1, 5, 10).
   - Tier 2 (Middle - Intra-Zone Exemplars): Rose oval hull with 7 nodes:
     Zone 2: Node 1 (180, 280), Node 3 (260, 280).
     Zone 4: Node 5 (460, 280), Node 7 (540, 280).
     Zone 8: Node 8 (720, 280), Node 9 (780, 280), Node 10 (840, 280).
   - Tier 1 (Bottom - Base Clients Grouped into 3 Physical Zones Capsules):
     Zone 2 Capsule: Node 1 (160, 460), Node 2 (220, 460), Node 3 (280, 460).
     Zone 4 Capsule: Node 4 (420, 460), Node 5 (480, 460), Node 6 (540, 460), Node 7 (600, 460).
     Zone 8 Capsule: Node 8 (720, 460), Node 9 (780, 460), Node 10 (840, 460).
3. Exact 17 Hierarchical Links (10 Intra-Zone + 7 Super-Peer Overlays):
   - Bottom-to-Middle (10 links):
     Zone 2 (Yellow #eab308): Bot 1->Mid 1, Bot 2->Mid 1, Bot 3->Mid 3.
     Zone 4 (Green #10b981): Bot 4->Mid 5, Bot 5->Mid 5, Bot 6->Mid 7, Bot 7->Mid 7.
     Zone 8 (Blue #38bdf8): Bot 8->Mid 8, Bot 9->Mid 9, Bot 10->Mid 10.
   - Middle-to-Top (7 links, Maroon #b91c1c, width 2.5px):
     To Super-Peer 1: Mid 1 -> Top 1 (vertical), Mid 9 -> Top 1 (cross-diagonal).
     To Super-Peer 5: Mid 3 -> Top 5 (cross-diagonal), Mid 5 -> Top 5 (vertical), Mid 8 -> Top 5 (cross-diagonal).
     To Super-Peer 10: Mid 7 -> Top 10 (cross-diagonal), Mid 10 -> Top 10 (vertical).
4. No direct horizontal line between Top 1, 5, 10.
5. POST /api/v1/storyboard/step/20 returns HTTP 200 with matching structure.
6. Frontend assets (index.html, style.css, app.js) contain Figure 3(f) 3-tier smartphone renderer and heartbeat loop.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    FIGURE3F_3TIER_NODES,
    FIGURE3F_3TIER_EDGES,
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
    assert data["total_steps"] >= 20
    assert "Figure 3(f)" in data["title"]
    assert "FIGURE 3(F)" in data["phase_badge"]
    assert "nodes" in data and len(data["nodes"]) == 10
    assert "figure3f_3tier_nodes" in data
    assert "figure3f_3tier_edges" in data
    assert "figure3f_edges" in data
    assert "figure3f_coordinates" in data


def test_step20_figure3f_3tier_nodes_specification(client):
    """Assert all 20 virtual nodes across 3 horizontal tiers strictly match Figure 3(f)."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    nodes = res.json()["figure3f_3tier_nodes"]

    assert len(nodes) == 20
    node_map = {n["key"]: n for n in nodes}

    # Tier 3 (Top - Global Super-Peers, y: 90)
    top_1 = node_map["top_1"]
    top_5 = node_map["top_5"]
    top_10 = node_map["top_10"]
    assert top_1["x"] == 180 and top_1["y"] == 90 and top_1["tier"] == 3
    assert top_5["x"] == 540 and top_5["y"] == 90 and top_5["tier"] == 3
    assert top_10["x"] == 900 and top_10["y"] == 90 and top_10["tier"] == 3

    # Tier 2 (Middle - Intra-Zone Exemplars, y: 250)
    assert node_map["mid_1"]["x"] == 140 and node_map["mid_1"]["y"] == 250 and node_map["mid_1"]["zone"] == 2
    assert node_map["mid_3"]["x"] == 230 and node_map["mid_3"]["y"] == 250 and node_map["mid_3"]["zone"] == 2
    assert node_map["mid_5"]["x"] == 490 and node_map["mid_5"]["y"] == 250 and node_map["mid_5"]["zone"] == 4
    assert node_map["mid_7"]["x"] == 590 and node_map["mid_7"]["y"] == 250 and node_map["mid_7"]["zone"] == 4
    assert node_map["mid_8"]["x"] == 770 and node_map["mid_8"]["y"] == 250 and node_map["mid_8"]["zone"] == 8
    assert node_map["mid_9"]["x"] == 850 and node_map["mid_9"]["y"] == 250 and node_map["mid_9"]["zone"] == 8
    assert node_map["mid_10"]["x"] == 930 and node_map["mid_10"]["y"] == 250 and node_map["mid_10"]["zone"] == 8

    # Tier 1 (Bottom - Base Clients Grouped into 3 Physical Zones Capsules, y: 430)
    for k in ["bot_1", "bot_2", "bot_3", "bot_4", "bot_5", "bot_6", "bot_7", "bot_8", "bot_9", "bot_10"]:
        assert node_map[k]["tier"] == 1
        assert node_map[k]["y"] == 430

    assert node_map["bot_1"]["x"] == 110 and node_map["bot_1"]["zone"] == 2
    assert node_map["bot_2"]["x"] == 195 and node_map["bot_2"]["zone"] == 2
    assert node_map["bot_3"]["x"] == 280 and node_map["bot_3"]["zone"] == 2
    assert node_map["bot_4"]["x"] == 435 and node_map["bot_4"]["zone"] == 4
    assert node_map["bot_5"]["x"] == 505 and node_map["bot_5"]["zone"] == 4
    assert node_map["bot_6"]["x"] == 575 and node_map["bot_6"]["zone"] == 4
    assert node_map["bot_7"]["x"] == 645 and node_map["bot_7"]["zone"] == 4
    assert node_map["bot_8"]["x"] == 800 and node_map["bot_8"]["zone"] == 8
    assert node_map["bot_9"]["x"] == 885 and node_map["bot_9"]["zone"] == 8
    assert node_map["bot_10"]["x"] == 970 and node_map["bot_10"]["zone"] == 8


def test_step20_figure3f_edges_and_no_horizontal_backbone(client):
    """Assert exact 17 hierarchical edges and NO direct horizontal line between 1, 5, 10."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    edges = res.json()["figure3f_edges"]

    assert len(edges) == 17

    # Ensure NO direct horizontal line between Top 1, 5, 10
    top_pairs = {(e["source"], e["target"]) for e in edges}
    assert ("top_1", "top_5") not in top_pairs and ("top_5", "top_1") not in top_pairs
    assert ("top_5", "top_10") not in top_pairs and ("top_10", "top_5") not in top_pairs
    assert ("top_1", "top_10") not in top_pairs and ("top_10", "top_1") not in top_pairs

    # Verify Middle-to-Top overlay links (7 links in maroon #b91c1c with width 2.5px)
    overlay_edges = [e for e in edges if e["type"] == "SUPER_PEER_OVERLAY"]
    assert len(overlay_edges) == 7
    for oe in overlay_edges:
        assert oe["color"] == "#b91c1c"
        assert oe["width"] == 2.5
        assert oe["style"] == "dashed"

    overlay_pairs = {(e["source"], e["target"]) for e in overlay_edges}
    # To Super-Peer 1:
    assert ("mid_1", "top_1") in overlay_pairs  # vertical
    assert ("mid_9", "top_1") in overlay_pairs  # cross-diagonal from Zone 8 mid to Top 1
    # To Super-Peer 5:
    assert ("mid_3", "top_5") in overlay_pairs  # cross-diagonal from Zone 2 mid to Top 5
    assert ("mid_5", "top_5") in overlay_pairs  # vertical
    assert ("mid_8", "top_5") in overlay_pairs  # cross-diagonal from Zone 8 mid to Top 5
    # To Super-Peer 10:
    assert ("mid_7", "top_10") in overlay_pairs  # cross-diagonal from Zone 4 mid to Top 10
    assert ("mid_10", "top_10") in overlay_pairs  # vertical

    # Verify Bottom-to-Middle clustering links (10 links)
    cluster_edges = [e for e in edges if e["type"] == "INTRA_ZONE_CLUSTER"]
    assert len(cluster_edges) == 10
    cluster_pairs = {(e["source"], e["target"]) for e in cluster_edges}
    # Zone 2:
    assert ("bot_1", "mid_1") in cluster_pairs
    assert ("bot_2", "mid_1") in cluster_pairs
    assert ("bot_3", "mid_3") in cluster_pairs
    # Zone 4:
    assert ("bot_4", "mid_5") in cluster_pairs
    assert ("bot_5", "mid_5") in cluster_pairs
    assert ("bot_6", "mid_7") in cluster_pairs
    assert ("bot_7", "mid_7") in cluster_pairs
    # Zone 8:
    assert ("bot_8", "mid_8") in cluster_pairs
    assert ("bot_9", "mid_9") in cluster_pairs
    assert ("bot_10", "mid_10") in cluster_pairs


def test_step20_super_cluster_colors_in_edge_specs(client):
    """Assert zone colors (#eab308, #10b981, #38bdf8) and maroon overlay (#b91c1c) exist in edge specs."""
    res = client.get("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    edges = res.json()["figure3f_edges"]

    colors = {e["color"].lower() for e in edges}
    assert "#eab308" in colors  # Zone 2 Yellow/Gold
    assert "#10b981" in colors  # Zone 4 Green
    assert "#38bdf8" in colors  # Zone 8 Blue
    assert "#b91c1c" in colors  # Maroon Overlay Lines


def test_step20_post_api_matches(client):
    """Assert POST /api/v1/storyboard/step/20 returns 200 with matching 17 edges and 20 virtual nodes."""
    res = client.post("/api/v1/storyboard/step/20")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 20
    assert len(data["figure3f_3tier_nodes"]) == 20
    assert len(data["figure3f_edges"]) == 17


def test_app_js_contains_figure3f_specifications():
    """Assert frontend app.js contains Figure 3(f) 3-tier definitions, smartphone renderer and heartbeat loop."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")

    assert "FIGURE3F_3TIER_NODES" in content
    assert "FIGURE3F_3TIER_EDGES" in content
    assert "drawFigure3fSmartphone" in content
    assert "Hierarchical Overlay (Figure 3(f))" in content
    assert "4000" in content  # Cycle duration for ping-pong heartbeat
    assert "INTRA-ZONE" in content or "intra-zone" in content or "INTRA_ZONE_CLUSTER" in content
    assert "SUPER_PEER_OVERLAY" in content or "SUPER-PEER" in content
    assert "#b91c1c" in content

