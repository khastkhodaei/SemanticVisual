"""Automated Verification Suite for Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3).

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/10 return HTTP 200 with complete storyboard payload.
2. Order dispatch traces originate strictly from zone initiators to intra-zone members:
   - Initiator C2 (Zone 2) -> [C1, C3] with payload: {"cmd": "ORDER_EXTRACT", "target_p": 3}
   - Initiator C4 (Zone 4) -> [C5, C6, C7] with payload: {"cmd": "ORDER_EXTRACT", "target_p": 3}
   - Initiator C8 (Zone 8) -> [C9, C10] with payload: {"cmd": "ORDER_EXTRACT", "target_p": 3}
   - Exactly 7 intra-zone order packets are generated; no cross-zone orders occur.
3. All 10 nodes have target_signature_length == 3 and order_status == 'READY_TO_EXTRACT'.
4. All 10 nodes retain full accumulated metadata profile:
   - neighbors, class distributions, 10D vectors, VRF scores, zone IDs, boundary flags.
5. All 18 physical links remain clean solid slate lines (#64748b).
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


def test_step10_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/10 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/10")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 10
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 10: EXTRACTION ORDER BROADCAST (P=3)"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["target_p"] == 3
    assert data_get["order_status"] == "READY_TO_EXTRACT"

    res_post = client.post("/api/v1/storyboard/step/10")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 10


def test_step10_all_10nodes_locked_to_target_p3():
    """Assert all 10 nodes have target_signature_length == 3 and order_status == 'READY_TO_EXTRACT'."""
    data = get_10node_step_data(10)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    node_to_zone = {
        1: 2, 2: 2, 3: 2,
        4: 4, 5: 4, 6: 4, 7: 4,
        8: 8, 9: 8, 10: 8,
    }

    for nid in range(1, 11):
        assert nid in nodes
        n = nodes[nid]
        zid = node_to_zone[nid]

        assert n["target_signature_length"] == 3, f"Node C{nid} target_signature_length != 3"
        assert n["order_status"] == "READY_TO_EXTRACT", f"Node C{nid} order_status != 'READY_TO_EXTRACT'"
        assert n["order_received_from"] == f"C{zid}"
        assert n["agreed_global_p"] == 3


def test_step10_order_dispatches_originate_strictly_from_zone_initiators():
    """Assert order packets originate strictly from zone initiators to their own members."""
    data = get_10node_step_data(10)
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

        # Strict intra-zone assertions
        assert src in [2, 4, 8], f"Non-initiator dispatched order: C{src}"
        assert src_zone == tgt_zone, f"Cross-zone order detected: C{src} -> C{tgt}"
        assert pkt["type"] == "ORDER_EXTRACT"
        assert pkt["target_p"] == 3
        assert pkt["payload"]["cmd"] == "ORDER_EXTRACT"
        assert pkt["payload"]["target_p"] == 3
        assert pkt["label"] == "ORDER: P=3"

        actual_dispatches[src].append(tgt)

    for init_id, targets in expected_dispatches.items():
        assert sorted(actual_dispatches[init_id]) == sorted(targets), (
            f"Initiator C{init_id} dispatched to {actual_dispatches[init_id]}, expected {targets}"
        )


def test_step10_all_10nodes_retain_full_metadata_profile():
    """Assert all 10 nodes retain their full metadata profile."""
    data = get_10node_step_data(10)
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

    # Frontier boundaries preserved
    assert nodes[1]["is_boundary"] is True
    assert nodes[6]["is_boundary"] is True


def test_step10_edges_remain_solid_slate_lines():
    """Assert all physical links remain solid slate lines."""
    data = get_10node_step_data(10)
    edges = data["edges"]
    assert len(edges) == len(get_10node_edges())
    assert data["total_edges"] == 18

    for edge in edges:
        assert edge.get("line_style") == "solid"
        assert edge.get("line_color") == "#64748b"


def test_step10_documentation_and_frontend_alignment():
    """Assert STEPS.md and frontend templates document and support Step 10."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 10 — Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)" in content
    assert "ORDER_EXTRACT" in content
    assert "P = 3" in content

    index_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "index.html"
    assert index_html.exists()
    html_content = index_html.read_text(encoding="utf-8")
    assert "stepNav10" in html_content
    assert "cardOrderExtractSection" in html_content

    app_js = Path(__file__).resolve().parent.parent / "frontend" / "static" / "app.js"
    assert app_js.exists()
    js_content = app_js.read_text(encoding="utf-8")
    assert "renderStep10" in js_content
    assert "animateStep10OrderPackets" in js_content
