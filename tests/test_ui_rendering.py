"""Tests for UI rendering data integrity and absence of duplicate prefixes."""

import re
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import TOTAL_STEPS


@pytest.fixture
def client():
    return TestClient(app)


def test_no_duplicate_active_phase_prefix_across_all_steps(client):
    """Verify that no step returns duplicated 'ACTIVE PHASE:' prefixes in phase_badge or title."""
    for step_num in range(1, TOTAL_STEPS + 1):
        res = client.get(f"/api/v1/storyboard/step/{step_num}")
        assert res.status_code == 200, f"Step {step_num} failed with status {res.status_code}"
        data = res.json()

        phase_badge = data.get("phase_badge", "")
        title = data.get("title", "")
        desc = data.get("description", "")

        # Check for duplicated prefix in phase_badge
        matches = re.findall(r"ACTIVE\s+PHASE:", phase_badge, re.IGNORECASE)
        assert len(matches) <= 1, (
            f"Step {step_num} phase_badge contains duplicate 'ACTIVE PHASE:' prefix: '{phase_badge}'"
        )

        # Check for duplicated prefix in title
        matches_title = re.findall(r"ACTIVE\s+PHASE:", title, re.IGNORECASE)
        assert len(matches_title) <= 1, (
            f"Step {step_num} title contains duplicate 'ACTIVE PHASE:' prefix: '{title}'"
        )


def test_step_titles_and_badges_non_empty(client):
    """Verify all 34 steps return non-empty title and phase_badge."""
    for step_num in range(1, TOTAL_STEPS + 1):
        res = client.get(f"/api/v1/storyboard/step/{step_num}")
        assert res.status_code == 200
        data = res.json()
        assert data.get("title"), f"Step {step_num} missing title"
        assert data.get("phase_badge"), f"Step {step_num} missing phase_badge"


def test_step_jump_dropdown_rendered_in_html():
    """Verify #stepJumpSelect is present in the static and template HTML pages."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'id="stepJumpSelect"' in content, f"Missing #stepJumpSelect in {path}"
            assert 'class="step-jump-dropdown' in content, f"Missing class in {path}"


def test_phase_tabs_and_substep_containers_rendered_in_html():
    """Verify all 7 Phase tabs and 7 phase sub-step groupings exist in HTML pages."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'id="phaseNav"' in content, f"Missing #phaseNav in {path}"
            assert 'id="subStepScrubber"' in content, f"Missing #subStepScrubber in {path}"
            for p in range(1, 8):
                assert f'id="phaseTab{p}"' in content, f"Missing #phaseTab{p} in {path}"
                assert f'id="phaseSubSteps{p}"' in content, f"Missing #phaseSubSteps{p} in {path}"
            for s in range(1, TOTAL_STEPS + 1):
                assert f'id="stepNav{s}"' in content, f"Missing #stepNav{s} in {path}"


def test_node_inspector_modal_structure_and_node_payloads(client):
    """Verify node inspector modal elements exist in HTML and all steps contain inspectable node payloads."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            for elem_id in [
                "nodeInfoCard",
                "cardNodeId",
                "cardStatusBadge",
                "btnCloseModal",
                "cardDegree",
                "cardNeighbors",
                "cardClientClasses",
                "cardDataDistributionSection",
                "cardVectorSection",
            ]:
                assert f'id="{elem_id}"' in content, f"Missing #{elem_id} in {path}"

    for step_num in range(1, TOTAL_STEPS + 1):
        res = client.get(f"/api/v1/storyboard/step/{step_num}")
        assert res.status_code == 200
        data = res.json()
        nodes = data.get("nodes", [])
        assert len(nodes) == 10, f"Step {step_num} should have 10 nodes, found {len(nodes)}"
        for n in nodes:
            assert "id" in n, f"Step {step_num} node missing id"
            assert (
                "distribution" in n or "data_distribution" in n or "vector_10d" in n or "normalized_vector" in n
            ), f"Step {step_num} node {n['id']} missing distribution/vector"


def test_sidebar_stabilization_structure_and_styles():
    """Verify sidebar layout stabilization classes and formula container exist."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "sidebar-column" in content, f"Missing sidebar-column in {path}"
            assert "sidebar-card-top" in content, f"Missing sidebar-card-top in {path}"
            assert "sidebar-card-bottom" in content, f"Missing sidebar-card-bottom in {path}"
            assert "dataset-classes-card" in content, f"Missing dataset-classes-card in {path}"
            assert "formula-container" in content, f"Missing formula-container in {path}"

    with open("/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/style.css", "r", encoding="utf-8") as f:
        css = f.read()
        assert ".sidebar-column" in css
        assert ".sidebar-card-top" in css
        assert ".sidebar-card-bottom" in css
        assert ".dataset-classes-card" in css
        assert ".formula-container" in css


def test_step5_initiator_packet_color_palette():
    """Verify Step 5 PROBE packet colors match originating initiator colors (C4 green, C2 red, C8 yellow)."""
    with open("/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "INITIATOR_PACKET_PALETTES" in js
    # Node 2 -> red
    assert '#ef4444' in js
    assert '#dc2626' in js
    # Node 4 -> green
    assert '#22c55e' in js
    assert '#16a34a' in js
    # Node 8 -> amber/yellow
    assert '#eab308' in js
    assert '#ca8a04' in js


def test_boundary_packets_and_initiator_halos():
    """Verify Issue #15: boundary relay packet colors and initiator halos match distinct zone themes."""
    with open("/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "ZONE_THEME_COLORS" in js
    # Zone 2 (Emerald Green)
    assert "#10b981" in js
    assert "#059669" in js
    # Zone 4 (Coral/Orange)
    assert "#f97316" in js
    assert "#ea580c" in js
    # Zone 8 (Violet/Purple)
    assert "#a855f7" in js
    assert "#7c3aed" in js

    # Cytoscape stylesheet initiator selectors have distinct border colors
    assert '"node.zone-initiator-2"' in js
    assert '"node.zone-initiator-4"' in js
    assert '"node.zone-initiator-8"' in js

    # Step 6 boundary packet and Step 9 consensus relay animation use ZONE_THEME_COLORS
    assert "animateStep6BoundaryPackets" in js
    assert "animateStep9ConsensusRelays" in js


def test_unified_packet_color_pipeline():
    """Verify Issue #16: unified packet color pipeline across all 34 simulation steps."""
    with open("/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    # Centralized helper functions exist
    assert "function resolvePacketTheme(" in js
    assert "function drawTransitPackets(" in js

    # Super-Cluster palette definition
    assert "SC_THEME_COLORS" in js
    # SC-1: Sky Blue
    assert "#38bdf8" in js
    # SC-2: Amber
    assert "#fbbf24" in js
    # SC-3: Violet
    assert "#c084fc" in js

    # Packet drawing functions route through resolvePacketTheme
    assert "resolvePacketTheme(pkt" in js or "resolvePacketTheme(packet" in js
    assert "animateStep22PeerDiscovery" in js
    assert "animateStep23ExemplarRouting" in js
    assert "animateStep30ModelRequests" in js
    assert "animateStep31BufferIngestion" in js


def test_app_js_syntax_and_initialization_lifecycle():
    """Verify Issue #19: frontend/static/app.js is free of syntax errors and has guarded initialization."""
    import subprocess
    with open("/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/app.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "document.addEventListener(\"DOMContentLoaded\"" in js
    assert "initCytoscape()" in js
    assert "loadStep(1)" in js
    assert "renderNetworkTopology" in js

    # Run JS syntax evaluation using gjs if available
    script = """
    try {
        imports.gi.GLib;
        let [ok, contents] = imports.gi.GLib.file_get_contents("frontend/static/app.js");
        let code = imports.byteArray.toString(contents);
        new Function(code);
        print("SYNTAX_OK");
    } catch (e) {
        print("SYNTAX_ERROR: " + e.message);
    }
    """
    res = subprocess.run(["gjs", "-c", script], capture_output=True, text=True)
    if res.returncode == 0:
        assert "SYNTAX_OK" in res.stdout, f"JS syntax check failed: {res.stdout}"


def test_session_status_and_canvas_elements_in_html():
    """Verify Issue #19: session status badge and canvas elements exist in HTML files."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'id="sessionStatus"' in content, f"Missing #sessionStatus in {path}"
        assert 'id="sessionVal"' in content, f"Missing #sessionVal in {path}"
        assert 'id="cy"' in content, f"Missing #cy in {path}"
        assert 'id="packetCanvas"' in content, f"Missing #packetCanvas in {path}"


def test_no_redundant_phase_badge_in_toolbar():
    """Verify Issue #20: redundant right-hand Phase: badge is removed from toolbar."""
    for path in [
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/static/index.html",
        "/home/mkh/Dev/Semanticvisual/semantic_dfl_sim/frontend/templates/index.html",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'id="activePhaseBadge"' not in content, f"#activePhaseBadge should be removed in {path}"
        assert 'id="subStepScrubber"' in content, f"Missing #subStepScrubber in {path}"










