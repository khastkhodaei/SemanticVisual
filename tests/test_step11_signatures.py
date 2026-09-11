"""Automated Verification Suite for Step 11: Top-P Signature Extraction with Dual Representation.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/11 return HTTP 200 with complete storyboard payload.
2. All 10 nodes contain both dual representations:
   - top_p_indices: List[int] of length 3 (1-indexed CIFAR-10 class IDs).
   - binary_mask_10d: List[int] of 10 binary elements (sum == 3).
   - dispatched_payload_bytes: 3 bytes (3 x sizeof(uint8) vs 40 bytes raw vector).
   - zero_parameter_leakage: True.
3. Initiator collection registries:
   - Initiator C2 (Zone 2) holds signatures for {1, 2, 3}.
   - Initiator C4 (Zone 4) holds signatures for {4, 5, 6, 7}.
   - Initiator C8 (Zone 8) holds signatures for {8, 9, 10}.
4. Packet traces carry {"type": "TOP_P_SIG", "indices": node.top_p_indices} from members to zone initiators:
   - Node 1 -> C2: "SIG: {C1, C2, C3}"
   - Node 6 -> C4: "SIG: {C7, C9, C10}"
   - Node 10 -> C8: "SIG: {C8, C9, C10}"
5. Engine method extract_top_p_signatures_10nodes executes correctly.
6. Documentation in STEPS.md contains Step 11.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine
from backend.storyboard_10nodes import (
    CIFAR10_CLASSES,
    STORYBOARD_10_ADJACENCY,
    STORYBOARD_10_DISTRIBUTION,
    STORYBOARD_10_VECTORS,
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step11_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/11 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/11")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 11
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 11: SIGNATURE EXTRACTION & DISPATCH"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["agreed_global_p"] == 3
    assert data_get["target_p"] == 3

    res_post = client.post("/api/v1/storyboard/step/11")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 11


def test_step11_all_10nodes_contain_dual_representation():
    """Assert all 10 nodes contain both top_p_indices (length 3) and binary_mask_10d (sum == 3)."""
    data = get_10node_step_data(11)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == 10

    for nid, node in nodes.items():
        # 1. Top-P Indices representation (Network Reality)
        indices = node["top_p_indices"]
        assert isinstance(indices, list)
        assert len(indices) == 3, f"Node {nid} must have exactly 3 top-P indices"
        assert all(isinstance(c, int) and 1 <= c <= 10 for c in indices), f"Indices for Node {nid} must be in range 1..10"

        # 2. Binary Mask 10D representation (Visual Bitmask)
        mask = node["binary_mask_10d"]
        assert isinstance(mask, list)
        assert len(mask) == 10, f"Node {nid} binary mask must be 10-dimensional"
        assert sum(mask) == 3, f"Node {nid} binary mask sum must equal 3 (P=3 active bits)"
        assert all(b in (0, 1) for b in mask), f"Node {nid} binary mask must contain only 0s and 1s"

        # Consistency between indices and mask
        for c in range(1, 11):
            expected_bit = 1 if (c in indices) else 0
            assert mask[c - 1] == expected_bit, f"Mismatch at class {c} for Node {nid}"

        # Wire payload metrics
        assert node["dispatched_payload_bytes"] == 3
        assert node["raw_weights_bytes"] == 40
        assert node["bandwidth_reduction_pct"] == 92.5
        assert node["zero_parameter_leakage"] is True


def test_step11_specific_node_signatures():
    """Assert specific nodes have exact expected signature indices from CIFAR-10 data."""
    data = get_10node_step_data(11)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1: Classes 1, 2, 3
    assert nodes[1]["top_p_indices"] == [1, 2, 3]
    assert nodes[1]["binary_mask_10d"] == [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]

    # Node 6: Classes 7, 9, 10
    assert nodes[6]["top_p_indices"] == [7, 9, 10]
    assert nodes[6]["binary_mask_10d"] == [0, 0, 0, 0, 0, 0, 1, 0, 1, 1]

    # Node 10: Classes 8, 9, 10
    assert nodes[10]["top_p_indices"] == [8, 9, 10]
    assert nodes[10]["binary_mask_10d"] == [0, 0, 0, 0, 0, 0, 0, 1, 1, 1]


def test_step11_initiator_collection_registries():
    """Assert Initiator C2 holds signatures for {1, 2, 3}; C4 holds {4, 5, 6, 7}; C8 holds {8, 9, 10}."""
    data = get_10node_step_data(11)
    nodes = {n["id"]: n for n in data["nodes"]}

    c2_reg = nodes[2]["zone_collected_signatures"]
    c4_reg = nodes[4]["zone_collected_signatures"]
    c8_reg = nodes[8]["zone_collected_signatures"]

    # In Python dict, keys are integers
    assert set(c2_reg.keys()) == {1, 2, 3}, f"Initiator C2 registry keys mismatch: {c2_reg.keys()}"
    assert set(c4_reg.keys()) == {4, 5, 6, 7}, f"Initiator C4 registry keys mismatch: {c4_reg.keys()}"
    assert set(c8_reg.keys()) == {8, 9, 10}, f"Initiator C8 registry keys mismatch: {c8_reg.keys()}"

    # Also check via HTTP client to ensure JSON serialization supports string/int mapping
    client = TestClient(app)
    res = client.get("/api/v1/storyboard/step/11")
    http_nodes = {n["id"]: n for n in res.json()["nodes"]}

    http_c2_reg = http_nodes[2]["zone_collected_signatures"]
    http_c4_reg = http_nodes[4]["zone_collected_signatures"]
    http_c8_reg = http_nodes[8]["zone_collected_signatures"]

    assert {int(k) for k in http_c2_reg.keys()} == {1, 2, 3}
    assert {int(k) for k in http_c4_reg.keys()} == {4, 5, 6, 7}
    assert {int(k) for k in http_c8_reg.keys()} == {8, 9, 10}


def test_step11_packet_traces_from_members_to_initiators():
    """Assert packet events carry TOP_P_SIG with member indices inward to zone initiators."""
    data = get_10node_step_data(11)
    packets = data["packet_events"]

    # Exactly 7 member packets are dispatched (10 nodes - 3 initiators)
    assert len(packets) == 7

    # Check key packet labels
    pkt_labels = {f"{p['source']}->{p['target']}": p for p in packets}

    assert "C1->C2" in pkt_labels
    assert pkt_labels["C1->C2"]["label"] == "SIG: {C1, C2, C3}"
    assert pkt_labels["C1->C2"]["payload"]["type"] == "TOP_P_SIG"
    assert pkt_labels["C1->C2"]["payload"]["indices"] == [1, 2, 3]

    assert "C6->C4" in pkt_labels
    assert pkt_labels["C6->C4"]["label"] == "SIG: {C7, C9, C10}"
    assert pkt_labels["C6->C4"]["payload"]["type"] == "TOP_P_SIG"
    assert pkt_labels["C6->C4"]["payload"]["indices"] == [7, 9, 10]

    assert "C10->C8" in pkt_labels
    assert pkt_labels["C10->C8"]["label"] == "SIG: {C8, C9, C10}"
    assert pkt_labels["C10->C8"]["payload"]["type"] == "TOP_P_SIG"
    assert pkt_labels["C10->C8"]["payload"]["indices"] == [8, 9, 10]


def test_step11_engine_method():
    """Assert SemanticDFLEngine.extract_top_p_signatures_10nodes operates cleanly."""
    engine = SemanticDFLEngine()
    res = engine.extract_top_p_signatures_10nodes()
    assert res["p"] == 3
    assert len(res["nodes"]) == 10
    assert len(res["packet_events"]) == 7


def test_step11_steps_md_documented():
    """Assert STEPS.md contains Step 11 documentation."""
    steps_path = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_path.exists()
    content = steps_path.read_text(encoding="utf-8")
    assert "## Step 11 — Top-P Signature Extraction with Dual Representation" in content
    assert "Protocol Reality" in content
    assert "Pedagogical Simulator Representation" in content
    assert "10D Binary Mask" in content
