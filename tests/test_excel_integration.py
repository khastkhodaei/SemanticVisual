"""Automated Integration Tests for Excel-Driven SemanticDFL Storyboard Simulator.

Verifies:
1. Excel workbook 'semantic_dfl_simulation_data.xlsx' is read successfully.
2. Exactly 50 nodes and 90 physical edges are parsed.
3. All 10 Initiators match Sheet 3 (C1, C6, C11, C16, C21, C26, C31, C36, C41, C46).
4. All 50 nodes have a valid assigned zone and hop distance <= 3.
5. REST API endpoints (/api/v1/storyboard/config, nodes, step/1..4) operate deterministically.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.excel_loader import ExcelDataLoader
from backend.main import app


@pytest.fixture
def excel_loader():
    return ExcelDataLoader.get_instance()


@pytest.fixture
def client():
    return TestClient(app)


def test_excel_workbook_loaded(excel_loader):
    """Verify that semantic_dfl_simulation_data.xlsx is found and loaded."""
    assert excel_loader.excel_path.exists()
    assert excel_loader.wb is not None
    assert len(excel_loader.wb.sheetnames) >= 3


def test_node_and_edge_counts(excel_loader):
    """Assert exactly 50 nodes and 90 physical edges are parsed from the Excel workbook."""
    nodes = excel_loader.get_all_nodes()
    edges = excel_loader.get_all_edges()

    assert len(nodes) == 50, f"Expected 50 nodes, got {len(nodes)}"
    assert len(edges) == 90, f"Expected 90 edges, got {len(edges)}"

    # Check node ID continuity: 1 to 50
    node_ids = {n["id"] for n in nodes}
    assert node_ids == set(range(1, 51))


def test_initiators_match_sheet3(excel_loader):
    """Assert all 10 Initiators match Sheet 3: C1, C6, C11, C16, C21, C26, C31, C36, C41, C46."""
    expected_initiators = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]
    actual_initiators = excel_loader.initiators

    assert actual_initiators == expected_initiators, (
        f"Expected initiators {expected_initiators}, got {actual_initiators}"
    )

    # Verify each initiator node has is_initiator == True
    nodes_by_id = {n["id"]: n for n in excel_loader.get_all_nodes()}
    for init_id in expected_initiators:
        node = nodes_by_id[init_id]
        assert node["is_initiator"] is True
        assert "Initiator" in node["status"] or "آغازگر" in node["status"]
        assert node["hops_to_initiator"] == 0


def test_zones_and_hop_distance(excel_loader):
    """Assert that all 50 nodes have a valid assigned zone and hop distance <= 3."""
    nodes = excel_loader.get_all_nodes()
    expected_zones = {
        "زون C1", "زون C6", "زون C11", "زون C16", "زون C21",
        "زون C26", "زون C31", "زون C36", "زون C41", "زون C46"
    }

    assigned_zones_found = set()
    for n in nodes:
        assert n["assigned_zone"] in expected_zones, (
            f"Node {n['id']} has invalid zone: {n['assigned_zone']}"
        )
        assigned_zones_found.add(n["assigned_zone"])
        assert 0 <= n["hops_to_initiator"] <= 3, (
            f"Node {n['id']} has hop distance {n['hops_to_initiator']} > 3"
        )
        assert len(n["neighbors"]) >= 3, f"Node {n['id']} degree < 3"

    assert assigned_zones_found == expected_zones
    assert len(assigned_zones_found) == 10


def test_api_storyboard_config(client):
    """Verify GET /api/v1/storyboard/config endpoint."""
    res = client.get("/api/v1/storyboard/config")
    assert res.status_code == 200
    data = res.json()
    assert data["num_nodes"] == 50
    assert data["total_edges"] == 90
    assert data["num_classes"] == 10
    assert len(data["classes"]) == 10


def test_api_storyboard_nodes(client):
    """Verify GET /api/v1/storyboard/nodes endpoint."""
    res = client.get("/api/v1/storyboard/nodes")
    assert res.status_code == 200
    data = res.json()
    assert data["total_nodes"] == 50
    assert data["total_edges"] == 90
    assert len(data["nodes"]) == 50
    assert len(data["edges"]) == 90


def test_api_storyboard_step_progression(client):
    """Verify GET /api/v1/storyboard/step/{1..4} returns deterministic step payloads."""
    # Step 1: Base Topology
    s1 = client.get("/api/v1/storyboard/step/1")
    assert s1.status_code == 200
    d1 = s1.json()
    assert d1["step"] == 1
    assert len(d1["nodes"]) == 50
    assert len(d1["edges"]) == 90
    assert d1["nodes"][0]["vrf_score"] is None
    assert d1["nodes"][0]["role"] == "CLIENT"

    # Step 2: Local VRF
    s2 = client.get("/api/v1/storyboard/step/2")
    assert s2.status_code == 200
    d2 = s2.json()
    assert d2["step"] == 2
    assert d2["nodes"][0]["vrf_score"] == 0.0235  # C1 score from Sheet 3
    assert "formula" in d2

    # Step 3: VRF Comparison & Local Initiator Deciding (Algorithm 2)
    s3 = client.get("/api/v1/storyboard/step/3")
    assert s3.status_code == 200
    d3 = s3.json()
    assert d3["step"] == 3
    assert len(d3["initiators"]) == 10
    assert "m_p" in d3["formula"]

    # In Step 3, only initiators are marked; non-initiator nodes have no assigned zone
    nodes_s3 = {n["id"]: n for n in d3["nodes"]}
    for init_id in [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]:
        assert nodes_s3[init_id]["is_initiator"] is True
        assert "Initiator" in nodes_s3[init_id]["decision_result"]

    for non_init_id in [2, 3, 4, 5, 7, 8, 9, 10]:
        assert nodes_s3[non_init_id]["is_initiator"] is False
        assert nodes_s3[non_init_id]["assigned_zone"] is None
        assert "Candidate" in nodes_s3[non_init_id]["decision_result"]

    # Verify 3-hop scoreboard data
    c1_sb = nodes_s3[1]["scoreboard_3hop"]
    assert len(c1_sb["hop_1"]) > 0
    assert len(c1_sb["hop_2"]) > 0
    assert len(c1_sb["hop_3"]) > 0

    # In Step 3, all 10 Initiators have their distinct assigned zone color seeds
    init_colors = {nodes_s3[init_id]["zone_color"] for init_id in [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]}
    assert len(init_colors) == 10, "Expected 10 distinct initiator seed colors"
    for non_init_id in [2, 3, 4, 5, 7, 8, 9, 10]:
        assert nodes_s3[non_init_id]["zone_color"] == "#2563eb"

    # Step 4: Zone Formation, First-Wins & Probe Conflicts (Algorithm 3)
    s4 = client.get("/api/v1/storyboard/step/4")
    assert s4.status_code == 200
    d4 = s4.json()
    assert d4["step"] == 4
    assert len(d4["initiators"]) == 10
    assert len(d4["zones"]) == 10
    assert len(d4["boundary_edges"]) == 29
    assert "PROBE" in d4["formula"]
    assert "waves" in d4
    assert len(d4["waves"]["wave1"]) > 0
    assert "boundary_alerts" in d4["waves"]
    assert len(d4["waves"]["boundary_alerts"]) > 0

    # In Step 4, all nodes have granular packet tracing fields
    nodes_s4 = {n["id"]: n for n in d4["nodes"]}
    for nid, node in nodes_s4.items():
        assert node["assigned_zone"] is not None
        assert "FIRST" in node["first_wins_text"]
        assert "winner_initiator" in node
        assert "accepted_probe" in node
        assert "rejected_probes" in node
        assert "forwarded_to" in node
        assert "boundary_notifications_emitted" in node

        # Verify accepted_probe structure
        acc = node["accepted_probe"]
        assert "from_initiator" in acc
        assert "sender" in acc
        assert "hop" in acc
        assert "arrival_wave" in acc

        if node["is_initiator"]:
            assert acc["hop"] == 0
            assert acc["sender"] is None
        else:
            assert acc["hop"] >= 1
            assert acc["sender"] is not None

    # Invalid Step
    s_err = client.get("/api/v1/storyboard/step/5")
    assert s_err.status_code == 400


def test_step4_hop1_morphing_and_dual_alerts(client, excel_loader):
    """Assert Hop 1 color adoption, frontier dual competing alerts, and initiator neighbor discovery."""
    res = client.get("/api/v1/storyboard/step/4")
    assert res.status_code == 200
    d4 = res.json()

    nodes_map = {n["id"]: n for n in d4["nodes"]}

    # 1. Hop 1 peers adopt their respective zone colors upon probe reception
    wave1 = d4["waves"]["wave1"]
    assert len(wave1) > 0

    hop1_nodes = [n for n in d4["nodes"] if n["hops_to_initiator"] == 1]
    assert len(hop1_nodes) > 0

    for n in hop1_nodes:
        init_id = n["winner_initiator_id"]
        expected_color = excel_loader.node_vrf[init_id]["zone_color"]
        assert n["zone_color"] == expected_color
        assert n["accepted_probe"]["hop"] == 1
        assert n["accepted_probe"]["from_initiator"] == f"C{init_id}"
        # Check there is a first-wins transmission in wave1
        assert any(
            p["target"] == n["id"] and p["initiator"] == init_id and p["is_first_wins"]
            for p in wave1
        )

    # 2. Frontier nodes correctly identify both competing initiators (Algorithm 3 L18-L19)
    # C5 is reached by C1 (adopted) and C6 (rejected)
    c5 = nodes_map[5]
    assert c5["accepted_probe_from"] == "C1"
    assert "C6" in c5["rejected_probe_from"]
    assert c5["boundary_status"] == "Dual NEIGHBOR alerts emitted"
    c5_alerts = c5["dual_neighbor_alerts"]
    assert len(c5_alerts) >= 2
    alert_targets = {a["to_initiator"] for a in c5_alerts}
    assert "C1" in alert_targets and "C6" in alert_targets

    # C50 is reached by C1 (adopted) and C46 (rejected)
    c50 = nodes_map[50]
    assert c50["accepted_probe_from"] == "C1"
    assert "C46" in c50["rejected_probe_from"]
    c50_alert_targets = {a["to_initiator"] for a in c50["dual_neighbor_alerts"]}
    assert "C1" in c50_alert_targets and "C46" in c50_alert_targets

    # C10 is reached by C6 (adopted) and C11 (rejected)
    c10 = nodes_map[10]
    assert c10["accepted_probe_from"] == "C6"
    assert "C11" in c10["rejected_probe_from"]
    c10_alert_targets = {a["to_initiator"] for a in c10["dual_neighbor_alerts"]}
    assert "C6" in c10_alert_targets and "C11" in c10_alert_targets

    # 3. Initiators successfully register their adjacent zones
    init_neighbors = d4.get("initiator_neighbors", {})
    assert len(init_neighbors) == 10

    for init_id in [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]:
        init_key = f"C{init_id}"
        assert init_key in init_neighbors
        discovered = init_neighbors[init_key]
        assert len(discovered) >= 2, f"Initiator {init_key} discovered fewer than 2 neighbors: {discovered}"

        # Node level discovered zones
        init_node = nodes_map[init_id]
        assert len(init_node["discovered_neighbor_zones"]) >= 2

    # Verify Initiator C1 discovered Zone C6 and Zone C26
    c1_adj = init_neighbors["C1"]
    assert any("C6" in z for z in c1_adj), f"C1 should discover adjacent Zone C6, got {c1_adj}"
    assert any("C26" in z for z in c1_adj), f"C1 should discover adjacent Zone C26, got {c1_adj}"

    # 4. Terminal logs verify HOP 1 ACCEPT and NEIGHBOR ALERT traces
    logs = d4["terminal_logs"]
    assert any("[HOP 1 ACCEPT]" in log for log in logs)
    assert any("[NEIGHBOR ALERT]" in log for log in logs)

