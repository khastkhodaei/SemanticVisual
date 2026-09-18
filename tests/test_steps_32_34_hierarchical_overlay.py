"""Verification suite for Steps 32, 33, and 34 Hierarchical Overlay (Figure 3(f)) Unification.

Tests:
1. Steps 32, 33, and 34 render the exact Figure 3(f) 3-tier canvas layout (getFigure3fLayout, 3 tiers, hull, capsules).
2. All 3 steps call drawFigure3fCanonicalOverlayEdges(ctx, nodePosMap) for canonical inter-tier dashed edges.
3. No in-flight packet animations or transit routing in Steps 32, 33, and 34.
4. Step 32 leaf nodes display REFERENCE_MODEL_BUILT badge/ring.
5. Step 33 leaf nodes display AGGREGATION_COMMITTED badge/ring.
6. Step 34 nodes display ROUND 1 CONVERGED badge/ring.
7. Dual layout toggle labels and canvas headers correctly reference 'Hierarchical Overlay (Figure 3(f))'.
"""

from pathlib import Path
import re
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_steps_32_33_34_layout_button_label_in_app_js():
    """Verify loadStep and layout toggle configure 'Hierarchical Overlay (Figure 3(f))' for steps 32-34."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")

    # loadStep covers steps 30 to 34
    assert re.search(r"stepNumber\s*>=\s*30\s*&&\s*stepNumber\s*<=\s*34", content)
    # updateLayoutButtonLabel covers steps 20 to 34
    assert re.search(r"currentStep\s*>=\s*20\s*&&\s*currentStep\s*<=\s*34", content)


def test_steps_32_33_34_canvas_view_labels_in_toggle_layout():
    """Verify toggleLayout updates canvasViewLabel to 'Hierarchical Overlay (Figure 3(f))' for steps 32-34."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    content = app_path.read_text(encoding="utf-8")

    assert "Reference Model Construction — Hierarchical Overlay (Figure 3(f))" in content
    assert "Round 1 Model Convergence — Hierarchical Overlay (Figure 3(f))" in content
    assert "Simulation Round 1 Complete — Hierarchical Overlay (Figure 3(f))" in content


def test_steps_32_33_34_figure3f_renderers_invoke_canonical_edges_and_layout():
    """Verify renderFigure3fSynthesis, renderFigure3fConvergence, and renderFigure3fFinalization use Figure 3(f) 3 tiers."""
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    content = app_path.read_text(encoding="utf-8")

    step_renderers = [
        ("renderFigure3fSynthesis", "renderPhysicalSynthesis", "REFERENCE_MODEL_BUILT"),
        ("renderFigure3fConvergence", "renderPhysicalConvergence", "AGGREGATION_COMMITTED"),
        ("renderFigure3fFinalization", "renderPhysicalFinalization", "ROUND 1 CONVERGED"),
    ]

    for fn_name, next_fn, expected_badge in step_renderers:
        fn_idx = content.find(f"function {fn_name}(")
        assert fn_idx != -1, f"Missing {fn_name}"
        next_idx = content.find(f"function {next_fn}(", fn_idx)
        assert next_idx != -1, f"Missing {next_fn} after {fn_name}"
        body = content[fn_idx:next_idx]

        # 1. Calls getFigure3fLayout(canvas)
        assert "getFigure3fLayout(canvas)" in body, f"{fn_name} missing getFigure3fLayout(canvas)"

        # 2. Draws canonical edges
        assert "drawFigure3fCanonicalOverlayEdges(ctx, nodePosMap)" in body, f"{fn_name} missing canonical edges"

        # 3. Renders Tier 2 hull and Tier 1 zone capsules
        assert "TIER 2 INTRA-ZONE EXEMPLARS" in body, f"{fn_name} missing pink oval hull"
        assert "capsules.forEach(" in body, f"{fn_name} missing capsule rendering"

        # 4. Renders backplates
        assert "FIGURE3F_3TIER_NODES.forEach(" in body, f"{fn_name} missing 3-tier node backplates"

        # 5. Badges
        assert expected_badge in body, f"{fn_name} missing badge {expected_badge}"

        # 6. Strictly NO packet transit animation or path interpolation
        assert "interpolateFigure3fPath" not in body, f"{fn_name} must not have in-flight packet animations"
        assert "packets.forEach" not in body, f"{fn_name} must not animate packets"
