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

