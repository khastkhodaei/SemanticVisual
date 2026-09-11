"""Automated Verification Suite for Step 8: Local Binary Search & P_min Reporting.

Verifies:
1. Endpoint GET /api/v1/storyboard/step/8 and POST return HTTP 200 with complete storyboard payload.
2. All 10 nodes compute exact P_min values matching the specification table (both Cosine and Energy metrics):
   - Node 1: Cosine=2, Energy=2
   - Node 2: Cosine=1, Energy=2
   - Node 3: Cosine=2, Energy=2
   - Node 4: Cosine=1, Energy=2
   - Node 5: Cosine=1, Energy=2
   - Node 6: Cosine=2, Energy=3
   - Node 7: Cosine=2, Energy=3
   - Node 8: Cosine=2, Energy=3
   - Node 9: Cosine=2, Energy=3
   - Node 10: Cosine=2, Energy=3
3. Reverse reporting traces map strictly to the correct zone initiator:
   - Node 1 -> C2 (P_min = 2)
   - Node 3 -> C2 (P_min = 2)
   - Node 5 -> C4 (P_min = 1)
   - Node 6 -> C4 (P_min = 2)
   - Node 7 -> C4 (P_min = 2)
   - Node 9 -> C8 (P_min = 2)
   - Node 10 -> C8 (P_min = 2)
   - No cross-zone reports occur; exactly 7 member report packets are generated.
4. All 10 nodes retain their full accumulated metadata profile:
   - neighbors, class distributions, 10D vectors, VRF scores, zone IDs, discovered boundary neighbors.
5. p_min_reported field is correctly populated on each node.
6. Documentation in STEPS.md and frontend UI components are aligned.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    STORYBOARD_10_VECTORS,
    STORYBOARD_10_VRF_SCORES,
    get_10node_edges,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


EXPECTED_EVAL_SPEC = {
    1: {"sorted": [0.46, 0.37, 0.17], "r1": 74.9, "r2": 96.1, "r3": 100.0, "p_cos": 2, "p_energy": 2, "init": 2},
    2: {"sorted": [0.57, 0.24, 0.19], "r1": 88.1, "r2": 95.6, "r3": 100.0, "p_cos": 1, "p_energy": 2, "init": 2},
    3: {"sorted": [0.46, 0.34, 0.20], "r1": 75.9, "r2": 94.4, "r3": 100.0, "p_cos": 2, "p_energy": 2, "init": 2},
    4: {"sorted": [0.62, 0.21, 0.17], "r1": 91.7, "r2": 96.8, "r3": 100.0, "p_cos": 1, "p_energy": 2, "init": 4},
    5: {"sorted": [0.53, 0.35, 0.12], "r1": 82.0, "r2": 98.3, "r3": 100.0, "p_cos": 1, "p_energy": 2, "init": 4},
    6: {"sorted": [0.34, 0.24, 0.23, 0.19], "r1": 66.4, "r2": 81.3, "r3": 92.9, "p_cos": 2, "p_energy": 3, "init": 4},
    7: {"sorted": [0.41, 0.27, 0.21, 0.11], "r1": 75.2, "r2": 90.1, "r3": 97.9, "p_cos": 2, "p_energy": 3, "init": 4},
    8: {"sorted": [0.38, 0.32, 0.30], "r1": 65.5, "r2": 85.6, "r3": 100.0, "p_cos": 2, "p_energy": 3, "init": 8},
    9: {"sorted": [0.45, 0.32, 0.23], "r1": 75.2, "r2": 92.3, "r3": 100.0, "p_cos": 2, "p_energy": 3, "init": 8},
    10: {"sorted": [0.43, 0.33, 0.12, 0.12], "r1": 75.7, "r2": 95.4, "r3": 97.7, "p_cos": 2, "p_energy": 3, "init": 8},
}


def test_step8_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/8 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/8")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 8
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 8: LOCAL BINARY SEARCH & P_MIN REPORTING"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18

    res_post = client.post("/api/v1/storyboard/step/8")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 8


def test_step8_all_10nodes_compute_exact_pmin():
    """Assert all 10 nodes compute exact P_min values matching the specification table."""
    data = get_10node_step_data(8)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid, spec in EXPECTED_EVAL_SPEC.items():
        node = nodes[nid]
        assert "binary_search" in node, f"Node C{nid} missing binary_search payload"
        bs = node["binary_search"]

        # Check P_min values
        assert bs["p_min_cosine"] == spec["p_cos"], (
            f"Node C{nid} p_min_cosine mismatch: got {bs['p_min_cosine']}, expected {spec['p_cos']}"
        )
        assert bs["p_min_energy"] == spec["p_energy"], (
            f"Node C{nid} p_min_energy mismatch: got {bs['p_min_energy']}, expected {spec['p_energy']}"
        )
        assert node["p_min_reported"] == spec["p_cos"], (
            f"Node C{nid} p_min_reported mismatch: got {node['p_min_reported']}, expected {spec['p_cos']}"
        )

        # Check sorted non-zero weights
        assert bs["sorted_non_zero_weights"] == spec["sorted"]

        # Check quality retention ratios at p=1, 2, 3
        ratios = bs["quality_ratios_cosine"]
        assert pytest.approx(ratios.get(1, 0.0), abs=0.2) == spec["r1"]
        assert pytest.approx(ratios.get(2, 0.0), abs=0.2) == spec["r2"]
        assert pytest.approx(ratios.get(3, 0.0), abs=0.2) == spec["r3"]

        # Check target initiator assignment
        assert node["target_initiator"] == f"C{spec['init']}"


def test_step8_reverse_report_packets_mapped_strictly_to_initiator():
    """Assert reverse report packets are sent strictly from members to their zone initiator."""
    data = get_10node_step_data(8)
    packets = data["packet_events"]
    assert len(packets) == 7

    node_to_zone = {
        1: 2, 2: 2, 3: 2,
        4: 4, 5: 4, 6: 4, 7: 4,
        8: 8, 9: 8, 10: 8,
    }

    expected_reports = {
        1: 2,
        3: 2,
        5: 4,
        6: 4,
        7: 4,
        9: 8,
        10: 8,
    }

    actual_reports = {}

    for pkt in packets:
        src = pkt["source_num"]
        tgt = pkt["target_num"]
        src_zone = node_to_zone[src]
        tgt_zone = node_to_zone[tgt]

        # Must be intra-zone reverse report
        assert src_zone == tgt_zone, f"Cross-zone report detected: C{src} -> C{tgt}"
        assert pkt["type"] == "REPORT_P_MIN"
        assert pkt["zone_id"] == src_zone
        assert tgt == expected_reports[src], f"Expected C{src} to report to C{expected_reports[src]}, got C{tgt}"

        spec = EXPECTED_EVAL_SPEC[src]
        assert pkt["payload"]["p_min"] == spec["p_cos"]
        assert pkt["payload"]["p_min_energy"] == spec["p_energy"]
        assert pkt["label"] == f"P_min = {spec['p_cos']}"

        actual_reports[src] = tgt

    assert actual_reports == expected_reports


def test_step8_all_10nodes_retain_full_metadata_profile():
    """Assert all 10 nodes retain their full metadata profile."""
    data = get_10node_step_data(8)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid in range(1, 11):
        assert nid in nodes
        n = nodes[nid]

        # Neighbors
        assert n["neighbors"] == sorted(STORYBOARD_10_ADJACENCY[nid])
        assert n["neighbors_str"] == [f"C{nb}" for nb in n["neighbors"]]

        # Class distributions
        assert n["distribution"] == STORYBOARD_10_DISTRIBUTION[nid]
        assert n["data_distribution"] == STORYBOARD_10_DISTRIBUTION[nid]

        # 10D normalized vectors
        assert n["vector_10d"] == STORYBOARD_10_VECTORS[nid]
        assert n["normalized_vector"] == STORYBOARD_10_VECTORS[nid]

        # VRF scores
        assert pytest.approx(n["vrf_score"], abs=1e-4) == STORYBOARD_10_VRF_SCORES[nid]

        # Zone IDs
        assert n["assigned_zone"] in [2, 4, 8]
        assert n["zone_id"] == n["assigned_zone"]
        assert n["status"] == "ASSIGNED"

    # Initiators retain discovered boundary neighbor knowledge
    assert nodes[2]["discovered_neighbor_zones"] == ["C4"]
    assert sorted(nodes[4]["discovered_neighbor_zones"]) == ["C2", "C8"]
    assert nodes[8]["discovered_neighbor_zones"] == ["C4"]

    # Boundary flags preserved
    assert nodes[1]["is_boundary"] is True
    assert nodes[6]["is_boundary"] is True


def test_step8_edges_remain_solid_slate_lines():
    """Assert all physical links remain solid slate lines."""
    data = get_10node_step_data(8)
    edges = data["edges"]
    assert len(edges) == len(get_10node_edges())
    assert data["total_edges"] == 18

    for edge in edges:
        assert edge.get("line_style") == "solid"
        assert edge.get("line_color") == "#64748b"


def test_step8_documentation_and_frontend_alignment():
    """Assert STEPS.md and frontend templates document and support Step 8."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 8 — Local Binary Search & P_min^i Reporting" in content
    assert "QualityRatio" in content
    assert "P_min (Cosine >= 80%)" in content or "Cosine >= 80%" in content
    assert "Node 6" in content

    index_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    assert index_html.exists()
    html_content = index_html.read_text(encoding="utf-8")
    assert "stepNav8" in html_content
    assert "cardBinarySearchSection" in html_content

    app_js = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_js.exists()
    js_content = app_js.read_text(encoding="utf-8")
    assert "renderStep8" in js_content
    assert "animateStep8ReportPackets" in js_content
