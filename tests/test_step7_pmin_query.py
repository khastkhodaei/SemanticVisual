"""Automated Verification Suite for Step 7: Initiator P_min Query Request.

Verifies:
1. Endpoint GET /api/v1/storyboard/step/7 and POST return HTTP 200 with complete storyboard payload.
2. REQ_P_MIN requests are sent strictly within the same zone:
   - Initiator C2 (Zone 2) -> [C1, C3] with payload: {"msg": "REQ_P_MIN", "tau": 0.80}
   - Initiator C4 (Zone 4) -> [C5, C6, C7] with payload: {"msg": "REQ_P_MIN", "tau": 0.80}
   - Initiator C8 (Zone 8) -> [C9, C10] with payload: {"msg": "REQ_P_MIN", "tau": 0.80}
   - No cross-zone requests occur.
3. All 10 nodes retain their full accumulated metadata profile:
   - neighbors, class distributions, 10D vectors, VRF scores, zone IDs, discovered boundary neighbors.
4. Member nodes have state flag: pending_query = "REQ_P_MIN (tau=0.80)".
5. All 18 physical links remain clean solid slate lines.
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


def test_step7_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/7 return HTTP 200."""
    res_get = client.get("/api/v1/storyboard/step/7")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 7
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 7: INITIATOR P_MIN QUERY"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18

    res_post = client.post("/api/v1/storyboard/step/7")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 7


def test_step7_requests_strictly_within_same_zone():
    """Assert requests are sent ONLY within the same zone (no cross-zone requests)."""
    data = get_10node_step_data(7)
    packets = data["packet_events"]
    assert len(packets) == 7

    node_to_zone = {
        1: 2, 2: 2, 3: 2,
        4: 4, 5: 4, 6: 4, 7: 4,
        8: 8, 9: 8, 10: 8,
    }

    expected_dispatches = {
        2: [1, 3],
        4: [5, 6, 7],
        8: [9, 10],
    }

    actual_dispatches = {2: [], 4: [], 8: []}

    for pkt in packets:
        src = pkt["source_num"]
        tgt = pkt["target_num"]
        src_zone = node_to_zone[src]
        tgt_zone = node_to_zone[tgt]

        # Strict intra-zone assertion: source and target MUST belong to identical zone
        assert src_zone == tgt_zone, f"Cross-zone request detected: C{src} (Zone {src_zone}) -> C{tgt} (Zone {tgt_zone})"
        assert pkt["zone_id"] == src_zone
        assert pkt["type"] == "REQ_P_MIN"
        assert pkt["payload"] == {"msg": "REQ_P_MIN", "tau": 0.80}
        assert pkt["label"] == "REQ(τ=80%)"

        actual_dispatches[src].append(tgt)

    for init_id, targets in expected_dispatches.items():
        assert sorted(actual_dispatches[init_id]) == sorted(targets), (
            f"Initiator C{init_id} dispatched to {actual_dispatches[init_id]}, expected {targets}"
        )


def test_step7_all_10nodes_retain_full_metadata_profile():
    """Assert all 10 nodes retain their full metadata profile."""
    data = get_10node_step_data(7)
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


def test_step7_member_pending_query_state_flag():
    """Assert member nodes have pending_query = 'REQ_P_MIN (tau=0.80)'."""
    data = get_10node_step_data(7)
    nodes = {n["id"]: n for n in data["nodes"]}

    member_ids = [1, 3, 5, 6, 7, 9, 10]
    initiator_ids = [2, 4, 8]

    for m_id in member_ids:
        node = nodes[m_id]
        assert node.get("pending_query") == "REQ_P_MIN (tau=0.80)", (
            f"Node C{m_id} expected pending_query == 'REQ_P_MIN (tau=0.80)', got {node.get('pending_query')}"
        )
        assert node.get("role") == "CLIENT"
        assert node.get("is_initiator") is False

    for init_id in initiator_ids:
        node = nodes[init_id]
        assert node.get("pending_query") is None
        assert node.get("role") == "INITIATOR"
        assert node.get("is_initiator") is True
        assert "Broadcasted REQ_P_MIN (τ=0.80) to zone members" in node.get("dispatched_query", "")


def test_step7_edges_remain_solid_slate_lines():
    """Assert all physical links remain solid slate lines."""
    data = get_10node_step_data(7)
    edges = data["edges"]
    assert len(edges) == len(get_10node_edges())
    assert data["total_edges"] == 18

    for edge in edges:
        assert edge.get("line_style") == "solid"
        assert edge.get("line_color") == "#64748b"


def test_step7_documentation_and_frontend_alignment():
    """Assert STEPS.md and frontend templates document and support Step 7."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 7 — Initiator P_min Query Request" in content
    assert "REQ_P_MIN" in content
    assert "tau = 0.80" in content or "tau = 80%" in content or "\\tau = 0.80" in content

    index_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    assert index_html.exists()
    html_content = index_html.read_text(encoding="utf-8")
    assert "stepNav7" in html_content
    assert "cardPminQuerySection" in html_content

    app_js = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_js.exists()
    js_content = app_js.read_text(encoding="utf-8")
    assert "renderStep7" in js_content
    assert "animateStep7PminPackets" in js_content
