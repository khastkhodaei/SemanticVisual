"""Unit and Integration Tests for Step 22: Hierarchical Semantic Peer Search & Discovery Query."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import get_10node_step_data, TOTAL_STEPS


@pytest.fixture
def client():
    return TestClient(app)


def test_step22_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/22 returns HTTP 200 with complete metadata."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()

    assert data["step"] == 22
    assert "Step 22" in data["title"]
    assert "Peer Search" in data["title"] or "Discovery" in data["title"]
    assert len(data["nodes"]) == 10
    assert data["total_steps"] == 22
    assert len(data["discovery_packets"]) == 7


def test_step22_all_nodes_search_status_resolved(client):
    """Assert all 10 nodes have search_status == 'RESOLVED'."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    nodes = res.json()["nodes"]

    for n in nodes:
        assert n.get("search_status") == "RESOLVED", f"Node {n['id']} search_status is not RESOLVED"
        assert n.get("federation_partners") is not None
        assert n.get("target_classes") is not None
        assert n.get("discovery_route") is not None


def test_step22_federation_partner_sets(client):
    """Assert nodes in SC-1, SC-2, and SC-3 share correct federation partner sets."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    node_map = {n["id"]: n for n in res.json()["nodes"]}

    # SC-1: Nodes 1, 2, 9
    for nid in [1, 2, 9]:
        assert node_map[nid]["federation_partners"] == [1, 2, 9]
        assert node_map[nid]["target_classes"] == "1, 2, 3"
        assert node_map[nid]["super_cluster"] == "SC-1"

    # SC-2: Nodes 3, 4, 5, 8
    for nid in [3, 4, 5, 8]:
        assert node_map[nid]["federation_partners"] == [3, 4, 5, 8]
        assert node_map[nid]["target_classes"] == "4, 5, 6"
        assert node_map[nid]["super_cluster"] == "SC-2"

    # SC-3: Nodes 6, 7, 10
    for nid in [6, 7, 10]:
        assert node_map[nid]["federation_partners"] == [6, 7, 10]
        assert node_map[nid]["target_classes"] == "8, 9, 10"
        assert node_map[nid]["super_cluster"] == "SC-3"


def test_step22_discovery_packet_traces(client):
    """Assert the 7 specified discovery packet traces are returned."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    packets = res.json()["discovery_packets"]
    assert len(packets) == 7

    paths = [p["path"] for p in packets]
    assert [2, 1] in paths
    assert [4, 5] in paths
    assert [6, 7] in paths
    assert [9, 8, 6, 4, 1] in paths
    assert [3, 5] in paths
    assert [8, 6, 5] in paths
    assert [7, 9, 10] in paths


def test_step22_total_steps_constant():
    """Verify TOTAL_STEPS is 22."""
    assert TOTAL_STEPS == 22
    step22 = get_10node_step_data(22)
    assert step22["total_steps"] == 22
