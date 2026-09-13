"""Unit and Integration Tests for Step 22: Hierarchical Semantic Peer Search & Discovery Query."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storyboard_10nodes import (
    get_10node_step_data,
    TOTAL_STEPS,
    STORYBOARD_10_ADJACENCY,
)


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
    assert len(data.get("discovery_packets", [])) == 7
    assert len(data.get("packet_traces", [])) == 7


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
    """Assert packet_traces strictly traverse valid Step 1 physical edges with correct paths."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    packets = data.get("packet_traces") or data.get("discovery_packets")
    assert len(packets) == 7

    path_by_source = {p["from"]: p["path"] for p in packets}

    # Assert node 6 uses path [6, 4, 7, 9, 10]
    assert path_by_source[6] == [6, 4, 7, 9, 10], f"Node 6 path mismatch: {path_by_source[6]}"

    # Assert node 9 uses path [9, 7, 4, 1]
    assert path_by_source[9] == [9, 7, 4, 1], f"Node 9 path mismatch: {path_by_source[9]}"

    # Assert all other paths match specified physical ledger
    assert path_by_source[2] == [2, 1]
    assert path_by_source[4] == [4, 5]
    assert path_by_source[3] == [3, 5]
    assert path_by_source[8] == [8, 6, 5]
    assert path_by_source[7] == [7, 9, 10]

    # Assert all paths consist solely of adjacent physical edges in the Step 1 graph
    for pkt in packets:
        path = pkt["path"]
        assert len(path) >= 2, f"Invalid trivial path: {path}"
        assert pkt["type"] == "REQ_PEER_DISCOVERY"
        assert pkt.get("label") == "DISCOVERY_QUERY"
        assert pkt.get("target_sp") == path[-1]

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            assert v in STORYBOARD_10_ADJACENCY[u], (
                f"Edge ({u}, {v}) in path {path} does NOT exist in Step 1 physical graph!"
            )
            assert u in STORYBOARD_10_ADJACENCY[v], (
                f"Symmetric edge ({v}, {u}) in path {path} does NOT exist in Step 1 physical graph!"
            )


def test_step22_outbound_queries_for_senders(client):
    """Assert all sender nodes (2, 3, 4, 6, 7, 8, 9) have outbound_query metadata."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    node_map = {n["id"]: n for n in data["nodes"]}

    for nid in [2, 3, 4, 6, 7, 8, 9]:
        node = node_map[nid]
        assert node["is_sender"] is True
        q = node.get("outbound_query")
        assert q is not None, f"Node {nid} missing outbound_query"
        assert q["status"] == "OUTBOUND_SENT"
        assert q["target_sp"] in [1, 5, 10]
        assert len(q["path"]) >= 2
        assert q["path"][0] == nid
        assert q["path"][-1] == q["target_sp"]

    # Specific checks requested
    assert node_map[6]["outbound_query"]["path"] == [6, 4, 7, 9, 10]
    assert node_map[6]["outbound_query"]["target_sp"] == 10
    assert node_map[9]["outbound_query"]["path"] == [9, 7, 4, 1]
    assert node_map[9]["outbound_query"]["target_sp"] == 1


def test_step22_super_peer_inboxes(client):
    """Assert Super-Peers (1, 5, 10) have populated inboxes with requesting clients and actions."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    node_map = {n["id"]: n for n in data["nodes"]}

    # SP 1: Requests from Nodes 2 and 9
    sp1 = node_map[1]
    assert sp1["is_super_peer"] is True
    inbox1_senders = [item["from"] for item in sp1["sp_inbox"]]
    assert sorted(inbox1_senders) == [2, 9]

    # SP 5: Requests from Nodes 3, 4, and 8
    sp5 = node_map[5]
    assert sp5["is_super_peer"] is True
    inbox5_senders = [item["from"] for item in sp5["sp_inbox"]]
    assert sorted(inbox5_senders) == [3, 4, 8]

    # SP 10: Requests from Nodes 6 and 7
    sp10 = node_map[10]
    assert sp10["is_super_peer"] is True
    inbox10_senders = [item["from"] for item in sp10["sp_inbox"]]
    assert sorted(inbox10_senders) == [6, 7]


def test_step22_relay_gateway_activity(client):
    """Assert relay gateway nodes (4, 7, 9) have active forwarding activity entries."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    node_map = {n["id"]: n for n in data["nodes"]}

    for nid in [4, 7, 9]:
        node = node_map[nid]
        assert node["is_relay_gateway"] is True
        assert len(node["relay_forwarding"]) >= 2
        for r in node["relay_forwarding"]:
            assert nid in r["path"][1:-1], f"Node {nid} not intermediate hop in relay path {r['path']}"


def test_step22_exact_top_p_numeric_payloads(client):
    """Assert all senders have exact 10D sparse weight vectors and 3 active Top-P indices."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    node_map = {n["id"]: n for n in data["nodes"]}

    expected_payloads = {
        2: {
            "target_sp": 1,
            "path": [2, 1],
            "top_p_indices": [1, 2, 3],
            "sparse_vector": [0.19, 0.24, 0.57, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        },
        9: {
            "target_sp": 1,
            "path": [9, 7, 4, 1],
            "top_p_indices": [1, 2, 3],
            "sparse_vector": [0.45, 0.32, 0.23, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        },
        3: {
            "target_sp": 5,
            "path": [3, 5],
            "top_p_indices": [4, 5, 6],
            "sparse_vector": [0.00, 0.00, 0.00, 0.34, 0.20, 0.46, 0.00, 0.00, 0.00, 0.00],
        },
        4: {
            "target_sp": 5,
            "path": [4, 5],
            "top_p_indices": [4, 5, 6],
            "sparse_vector": [0.00, 0.00, 0.00, 0.62, 0.21, 0.17, 0.00, 0.00, 0.00, 0.00],
        },
        8: {
            "target_sp": 5,
            "path": [8, 6, 5],
            "top_p_indices": [4, 5, 6],
            "sparse_vector": [0.00, 0.00, 0.00, 0.32, 0.38, 0.30, 0.00, 0.00, 0.00, 0.00],
        },
        6: {
            "target_sp": 10,
            "path": [6, 4, 7, 9, 10],
            "top_p_indices": [7, 9, 10],
            "sparse_vector": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.23, 0.00, 0.34, 0.24],
        },
        7: {
            "target_sp": 10,
            "path": [7, 9, 10],
            "top_p_indices": [8, 9, 10],
            "sparse_vector": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.41, 0.21, 0.27],
        },
    }

    for nid, exp in expected_payloads.items():
        q = node_map[nid]["outbound_query"]
        assert q["target_sp"] == exp["target_sp"]
        assert q["path"] == exp["path"]
        assert q["top_p_indices"] == exp["top_p_indices"]
        assert q["sparse_vector"] == exp["sparse_vector"]


def test_step22_super_peer_inbox_numeric_vectors(client):
    """Assert Super-Peers (1, 5, 10) have exact numeric vectors in inboxes."""
    res = client.get("/api/v1/storyboard/step/22")
    assert res.status_code == 200
    data = res.json()
    node_map = {n["id"]: n for n in data["nodes"]}

    # SP 1
    sp1_inbox = {item["sender"]: item for item in node_map[1]["sp_inbox"]}
    assert sp1_inbox[2]["indices"] == [1, 2, 3]
    assert sp1_inbox[2]["weights"] == [0.19, 0.24, 0.57, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert sp1_inbox[9]["indices"] == [1, 2, 3]
    assert sp1_inbox[9]["weights"] == [0.45, 0.32, 0.23, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    # SP 5
    sp5_inbox = {item["sender"]: item for item in node_map[5]["sp_inbox"]}
    assert sp5_inbox[3]["indices"] == [4, 5, 6]
    assert sp5_inbox[3]["weights"] == [0.0, 0.0, 0.0, 0.34, 0.20, 0.46, 0.0, 0.0, 0.0, 0.0]
    assert sp5_inbox[4]["indices"] == [4, 5, 6]
    assert sp5_inbox[4]["weights"] == [0.0, 0.0, 0.0, 0.62, 0.21, 0.17, 0.0, 0.0, 0.0, 0.0]
    assert sp5_inbox[8]["indices"] == [4, 5, 6]
    assert sp5_inbox[8]["weights"] == [0.0, 0.0, 0.0, 0.32, 0.38, 0.30, 0.0, 0.0, 0.0, 0.0]

    # SP 10
    sp10_inbox = {item["sender"]: item for item in node_map[10]["sp_inbox"]}
    assert sp10_inbox[6]["indices"] == [7, 9, 10]
    assert sp10_inbox[6]["weights"] == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.23, 0.0, 0.34, 0.24]
    assert sp10_inbox[7]["indices"] == [8, 9, 10]
    assert sp10_inbox[7]["weights"] == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.41, 0.21, 0.27]


def test_step22_total_steps_constant():
    """Verify TOTAL_STEPS is 22."""
    assert TOTAL_STEPS == 22

    step22 = get_10node_step_data(22)
    assert step22["total_steps"] == 22
