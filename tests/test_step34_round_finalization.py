"""Tests for Step 34: Round 1 Finalization, System Benchmarks & Next-Epoch Transition."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STEP34_SIMULATION_SUMMARY,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step34_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/34 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/34")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 34
    assert data["total_steps"] == 34
    assert len(data["nodes"]) == 10
    assert "simulation_summary" in data


def test_step34_simulation_summary_content(client):
    """Assert simulation_summary has status == 'SIMULATION_ROUND_1_COMPLETE' and benchmark fields."""
    res = client.get("/api/v1/storyboard/step/34")
    assert res.status_code == 200
    data = res.json()

    summary = data["simulation_summary"]
    assert summary["status"] == "SIMULATION_ROUND_1_COMPLETE"
    assert summary["total_nodes"] == 10
    assert summary["total_super_clusters"] == 3
    assert summary["bandwidth_savings_pct"] == 62.5
    assert summary["average_model_accuracy_gain"] == "+4.93%"
    assert summary["next_epoch_seed"] == "0x8f3c4e9b21a7"
    assert summary["nodes_ready_for_epoch_2"] is True


def test_step34_total_steps_constant():
    """Assert TOTAL_STEPS == 34."""
    assert TOTAL_STEPS == 34


def test_step34_nodes_ready_for_epoch_2(client):
    """Assert all 10 nodes have epoch_2_ready == True and status == 'EPOCH_1_FINALIZED'."""
    res = client.get("/api/v1/storyboard/step/34")
    assert res.status_code == 200
    data = res.json()

    for n in data["nodes"]:
        assert n["status"] == "EPOCH_1_FINALIZED"
        assert n["epoch_2_ready"] is True
        assert n["epoch_2_seed"] == "0x8f3c4e9b21a7"
        assert n["bandwidth_savings_pct"] == 62.5


def test_step34_post_endpoint_success(client):
    """Assert POST /api/v1/storyboard/step/34 returns HTTP 200."""
    res = client.post("/api/v1/storyboard/step/34")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 34
    assert data["total_steps"] == 34
