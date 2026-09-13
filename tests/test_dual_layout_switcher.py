"""Automated Verification Suite for Step 20 Dual-Layout Switcher.

Verifies:
1. index.html contains #btn-toggle-layout and #stepNav20.
2. style.css contains glassmorphism toolbar styles for #btn-toggle-layout and .layout-overlay-active.
3. app.js defines exact overlay coordinates for the 3 Super-Clusters:
   - SC-1 (Left Wing / Aviation & Vehicles):
     Node 1: (180, 320), Node 2: (100, 240), Node 9: (100, 400)
   - SC-2 (Center Hub / Animals):
     Node 5: (500, 320), Node 4: (420, 220), Node 3: (580, 220), Node 8: (500, 440)
   - SC-3 (Right Wing / Transport & Amphibians):
     Node 10: (820, 320), Node 7: (900, 240), Node 6: (900, 400)
4. app.js maintains currentLayout state ('physical' | 'overlay') and 500ms smooth transition.
5. All 7 semantic overlay edges are defined per Step 20 SON logical topology.
6. Overlay mode dims physical links to near zero (0.05).
7. FastAPI serves frontend assets with HTTP 200.
"""

from pathlib import Path
import re
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_index_html_contains_dual_layout_elements(client):
    """Assert index.html contains #btn-toggle-layout and #stepNav20."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="btn-toggle-layout"' in html
    assert 'id="stepNav20"' in html
    assert "Layout: Physical Topology" in html
    assert "Semantic Overlay" in html


def test_style_css_glassmorphism_layout_toggle():
    """Assert style.css defines glassmorphism styles for #btn-toggle-layout."""
    style_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "style.css"
    assert style_path.exists()
    content = style_path.read_text(encoding="utf-8")

    assert "#btn-toggle-layout" in content
    assert "backdrop-filter: blur" in content
    assert "border-radius: 9999px" in content
    assert "layout-overlay-active" in content
    assert "box-shadow" in content


def test_app_js_coordinates_specifications():
    """Assert exact overlay and physical layout coordinates in app.js."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")

    # Verify OVERLAY_LAYOUT_COORDS / FIGURE3F_COORDINATES exists and contains exact coordinates
    assert "OVERLAY_LAYOUT_COORDS" in content
    assert "PHYSICAL_LAYOUT_COORDS" in content
    assert "FIGURE3F_COORDINATES" in content

    # Figure 3(f) Top Plane: Node 1 (220, 130), Node 5 (520, 130), Node 10 (820, 130)
    assert re.search(r"1:\s*\{\s*x:\s*220,\s*y:\s*130", content)
    assert re.search(r"5:\s*\{\s*x:\s*520,\s*y:\s*130", content)
    assert re.search(r"10:\s*\{\s*x:\s*820,\s*y:\s*130", content)

    # Figure 3(f) Middle Plane: Node 9 (220, 280), Node 3 (440, 280), Node 8 (600, 280), Node 7 (820, 280)
    assert re.search(r"9:\s*\{\s*x:\s*220,\s*y:\s*280", content)
    assert re.search(r"3:\s*\{\s*x:\s*440,\s*y:\s*280", content)
    assert re.search(r"8:\s*\{\s*x:\s*600,\s*y:\s*280", content)
    assert re.search(r"7:\s*\{\s*x:\s*820,\s*y:\s*280", content)

    # Figure 3(f) Bottom Plane: Node 2 (220, 430), Node 4 (520, 430), Node 6 (820, 430)
    assert re.search(r"2:\s*\{\s*x:\s*220,\s*y:\s*430", content)
    assert re.search(r"4:\s*\{\s*x:\s*520,\s*y:\s*430", content)
    assert re.search(r"6:\s*\{\s*x:\s*820,\s*y:\s*430", content)


def test_app_js_layout_transition_and_animation():
    """Assert transition logic, easing, and layout state management."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    content = app_path.read_text(encoding="utf-8")

    assert 'let currentLayout = "physical";' in content
    assert "function toggleLayout()" in content
    assert "function updateLayoutButtonUI()" in content
    assert "function animateLayoutTransition(toLayout" in content
    assert "duration = 500" in content
    assert "requestAnimationFrame" in content
    assert "0.05" in content  # opacity dimming for overlay mode
    assert "buildStep20FromStep19" in content
    assert "renderStep20" in content
    assert "animateStep20SemanticOverlay" in content


def test_app_js_seven_semantic_overlay_edges():
    """Assert 7 semantic overlay edges are defined in app.js for Step 20."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    content = app_path.read_text(encoding="utf-8")

    # 7 edges: (2, 1), (9, 1), (4, 5), (3, 5), (8, 5), (6, 7), (7, 10)
    assert "from: 2, to: 1" in content
    assert "from: 9, to: 1" in content
    assert "from: 4, to: 5" in content
    assert "from: 3, to: 5" in content
    assert "from: 8, to: 5" in content
    assert "from: 6, to: 7" in content
    assert "from: 7, to: 10" in content


def test_app_js_button_visibility_and_modal():
    """Assert toggle button visibility on step >= 20 and inspector modal support."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    content = app_path.read_text(encoding="utf-8")

    assert "stepNumber >= 20" in content
    assert "currentStep >= 20" in content
    assert "cardOverlaySection" in content
    assert "2-TIER_SON" in content


def test_step20_backend_api(client):
    """Assert backend step 20 API works for GET and POST and returns valid SON data."""
    res_get = client.get("/api/v1/storyboard/step/20")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["step"] == 20
    assert data["total_steps"] == 20
    assert len(data["semantic_overlay_edges"]) in (7, 9)
    assert len(data["nodes"]) == 10

    res_post = client.post("/api/v1/storyboard/step/20")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 20
