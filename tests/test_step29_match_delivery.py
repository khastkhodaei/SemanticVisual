"""Tests for Step 29: Top-K Partner Match Delivery to Requesting Clients (K = 2)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STORYBOARD_10_ADJACENCY,
    STEP29_FINAL_DELIVERY_PACKETS,
    STEP29_LOCKED_PARTNERS,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step29_endpoint_success(client):
    """Assert GET /api/v1/storyboard/step/29 returns HTTP 200."""
    res = client.get("/api/v1/storyboard/step/29")
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 29
    assert data["total_steps"] >= 29
    assert len(data["nodes"]) == 10
    assert "final_delivery_packets" in data or "packets" in data
    assert "client_locked_partners" in data or "locked_partners" in data


def test_step29_final_delivery_packets_physical_paths(client):
    """Assert final_delivery_packets contains strictly valid Step 1 physical paths."""
    res = client.get("/api/v1/storyboard/step/29")
    assert res.status_code == 200
    data = res.json()

    packets = data.get("final_delivery_packets") or data.get("packets")
    assert packets is not None
    assert len(packets) == 7

    # Verify specific multi-hop routes
    routes_by_destination = {p["to"]: p["path"] for p in packets}
    assert routes_by_destination[2] == [1, 2]
    assert routes_by_destination[9] == [1, 4, 7, 9]
    assert routes_by_destination[3] == [5, 3]
    assert routes_by_destination[4] == [5, 4]
    assert routes_by_destination[8] == [5, 6, 8]
    assert routes_by_destination[7] == [10, 9, 7]
    assert routes_by_destination[6] == [10, 9, 7, 4, 6]

    # Strictly verify that every hop in every path is a valid physical ad-hoc link
    for pkt in packets:
        path = pkt["path"]
        assert len(path) >= 2
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            assert v in STORYBOARD_10_ADJACENCY[u], f"Physical link ({u}, {v}) not found in adjacency list"
            assert u in STORYBOARD_10_ADJACENCY[v], f"Physical link ({v}, {u}) not found in adjacency list"


def test_step29_all_ten_nodes_contain_top_k_two(client):
    """Assert all 10 nodes contain exactly 2 items in top_k and are locked."""
    res = client.get("/api/v1/storyboard/step/29")
    assert res.status_code == 200
    data = res.json()

    nodes = data["nodes"]
    assert len(nodes) == 10

    for n in nodes:
        nid = n["id"]
        assert "top_k" in n, f"Node {nid} missing top_k"
        top_k = n["top_k"]
        assert len(top_k) == 2, f"Node {nid} top_k length is {len(top_k)}, expected exactly 2"
        for item in top_k:
            assert "peer" in item
            assert "sim" in item
            assert item["peer"] in range(1, 11)
            assert 0.0 <= item["sim"] <= 1.0

        assert n["status"] == "FEDERATION_PARTNERS_LOCKED"
        assert n.get("is_federation_locked") is True


def test_step29_deterministic_partner_matches(client):
    """Assert exact expected partners and cosine similarity scores for all 10 clients."""
    res = client.get("/api/v1/storyboard/step/29")
    assert res.status_code == 200
    data = res.json()

    nodes_by_id = {n["id"]: n for n in data["nodes"]}

    # C1: {C9 (0.9429), C2 (0.8531)}
    c1_peers = [p["peer"] for p in nodes_by_id[1]["top_k"]]
    assert c1_peers == [9, 2]
    assert nodes_by_id[1]["top_k"][0]["sim"] == 0.9429

    # C6: {C7 (0.5365), C10 (0.5341)}
    c6_peers = [p["peer"] for p in nodes_by_id[6]["top_k"]]
    assert c6_peers == [7, 10]
    assert nodes_by_id[6]["top_k"][0]["sim"] == 0.5365
    assert nodes_by_id[6]["top_k"][1]["sim"] == 0.5341

    # C10: {C7 (0.9378), C6 (0.5341)}
    c10_peers = [p["peer"] for p in nodes_by_id[10]["top_k"]]
    assert c10_peers == [7, 6]
    assert nodes_by_id[10]["top_k"][0]["sim"] == 0.9378
    assert nodes_by_id[10]["top_k"][1]["sim"] == 0.5341
