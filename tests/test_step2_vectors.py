"""Automated Verification Suite for Step 2: Local Training & Normalized 10D Vector Generation.

Verifies:
1. Exact 10-dimensional numerical vectors for all 10 nodes.
2. Vector lengths are exactly 10 and each sums to 1.0 (L1 normalized).
3. Cosine similarity between nodes in the same latent group (Node 1 and Node 9) is >= 0.85.
4. Cosine similarity between disjoint semantic groups (Node 1 and Node 3) is 0.00.
5. POST and GET /api/v1/storyboard/step/2 return all 10 nodes with 'LOCAL_TRAINED' status,
   the exact 10D vectors, and the required '[LOCAL TRAINING]' terminal logs.
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.storyboard_10nodes import (
    STORYBOARD_10_VECTORS,
    get_10node_step_data,
    get_10node_nodes,
)


@pytest.fixture
def client():
    return TestClient(app)


EXPECTED_EXACT_VECTORS = {
    1: [0.46, 0.17, 0.37, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    2: [0.19, 0.24, 0.57, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    3: [0.00, 0.00, 0.00, 0.34, 0.20, 0.46, 0.00, 0.00, 0.00, 0.00],
    4: [0.00, 0.00, 0.00, 0.62, 0.21, 0.17, 0.00, 0.00, 0.00, 0.00],
    5: [0.00, 0.00, 0.00, 0.53, 0.12, 0.35, 0.00, 0.00, 0.00, 0.00],
    6: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.23, 0.19, 0.34, 0.24],
    7: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.11, 0.41, 0.21, 0.27],
    8: [0.00, 0.00, 0.00, 0.32, 0.38, 0.30, 0.00, 0.00, 0.00, 0.00],
    9: [0.45, 0.32, 0.23, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    10: [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.12, 0.43, 0.33, 0.12],
}


def cosine_similarity(v1, v2):
    """Compute cosine similarity between two numerical vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def test_storyboard_vectors_exact_match():
    """Assert all 10 vectors match the exact numerical arrays specified in requirements."""
    for node_id, expected_vec in EXPECTED_EXACT_VECTORS.items():
        actual_vec = STORYBOARD_10_VECTORS[node_id]
        assert len(actual_vec) == 10, f"Node {node_id} vector length is {len(actual_vec)}, expected 10"
        assert actual_vec == expected_vec, f"Node {node_id} vector mismatch: expected {expected_vec}, got {actual_vec}"


def test_storyboard_vectors_normalization():
    """Assert each vector has length 10 and sums to 1.0 (L1 normalized)."""
    for node_id, vec in STORYBOARD_10_VECTORS.items():
        assert len(vec) == 10, f"Node {node_id} vector length must be exactly 10"
        vec_sum = sum(vec)
        assert abs(vec_sum - 1.0) < 1e-6, f"Node {node_id} vector sum {vec_sum} != 1.0"


def test_latent_group_cosine_similarity():
    """Assert nodes in same latent group have cosine similarity >= 0.85, disjoint groups have 0.00."""
    v1 = STORYBOARD_10_VECTORS[1]
    v9 = STORYBOARD_10_VECTORS[9]
    sim_1_9 = cosine_similarity(v1, v9)
    assert sim_1_9 >= 0.85, f"Cosine similarity between Node 1 and Node 9 should be >= 0.85, got {sim_1_9:.4f}"

    # Disjoint groups: Node 1 (C1..C3) vs Node 3 (C4..C6)
    v3 = STORYBOARD_10_VECTORS[3]
    sim_1_3 = cosine_similarity(v1, v3)
    assert sim_1_3 == 0.00, f"Cosine similarity between Node 1 and Node 3 should be 0.00, got {sim_1_3:.4f}"

    # Same latent group peers: (Node 3, Node 5) and (Node 6, Node 7)
    v5 = STORYBOARD_10_VECTORS[5]
    sim_3_5 = cosine_similarity(v3, v5)
    assert sim_3_5 >= 0.85, f"Cosine similarity between Node 3 and Node 5 should be >= 0.85, got {sim_3_5:.4f}"

    v6 = STORYBOARD_10_VECTORS[6]
    v7 = STORYBOARD_10_VECTORS[7]
    sim_6_7 = cosine_similarity(v6, v7)
    assert sim_6_7 >= 0.85, f"Cosine similarity between Node 6 and Node 7 should be >= 0.85, got {sim_6_7:.4f}"


def test_step2_data_structure():
    """Assert get_10node_step_data(2) returns 10 nodes with status LOCAL_TRAINED and exact vectors."""
    step2_data = get_10node_step_data(2)
    assert step2_data["step"] == 2
    assert step2_data["total_nodes"] == 10
    nodes = step2_data["nodes"]
    assert len(nodes) == 10

    for node in nodes:
        nid = node["id"]
        assert node["status"] == "LOCAL_TRAINED"
        assert node["vector"] == EXPECTED_EXACT_VECTORS[nid]
        assert node["normalized_vector"] == EXPECTED_EXACT_VECTORS[nid]
        assert len(node["vector"]) == 10

    # Verify terminal logs
    logs = step2_data["terminal_logs"]
    assert len(logs) == 10
    for nid in range(1, 11):
        expected_log = f"[LOCAL TRAINING] Node C{nid} completed local training. Generated 10D class representation vector."
        assert expected_log in logs, f"Missing expected terminal log for Node C{nid}"


def test_post_step2_api(client):
    """Assert POST /api/v1/storyboard/step/2 returns HTTP 200 with complete Step 2 payload."""
    res = client.post("/api/v1/storyboard/step/2")
    assert res.status_code == 200, f"POST /api/v1/storyboard/step/2 failed with status {res.status_code}"
    body = res.json()
    assert body["step"] == 2
    assert len(body["nodes"]) == 10

    for node in body["nodes"]:
        nid = node["id"]
        assert node["status"] == "LOCAL_TRAINED"
        assert node["vector"] == EXPECTED_EXACT_VECTORS[nid]
        assert len(node["vector"]) == 10

    logs = body["terminal_logs"]
    assert len(logs) == 10
    for nid in range(1, 11):
        expected_log = f"[LOCAL TRAINING] Node C{nid} completed local training. Generated 10D class representation vector."
        assert expected_log in logs


def test_get_step2_api(client):
    """Assert GET /api/v1/storyboard/step/2 also returns HTTP 200 with complete Step 2 payload."""
    res = client.get("/api/v1/storyboard/step/2")
    assert res.status_code == 200, f"GET /api/v1/storyboard/step/2 failed with status {res.status_code}"
    body = res.json()
    assert body["step"] == 2
    assert len(body["nodes"]) == 10
    assert body["nodes"][0]["vector"] == EXPECTED_EXACT_VECTORS[1]


def test_node_payload_normalized_class_attributes(client):
    """Verify nodes include assigned_classes, class_distribution, dominant_class, and vector_10d."""
    res = client.get("/api/v1/storyboard/nodes")
    assert res.status_code == 200
    nodes = res.json()["nodes"]
    assert len(nodes) == 10

    for n in nodes:
        nid = n["id"]
        assert "assigned_classes" in n
        assert "class_distribution" in n
        assert "dominant_class" in n
        assert "vector_10d" in n
        assert n["vector_10d"] == EXPECTED_EXACT_VECTORS[nid]

    # Node 1 exact checks
    n1 = nodes[0]
    assert n1["assigned_classes"] == [0, 1, 2]
    assert n1["dominant_class"] == "C1"
    assert n1["class_distribution"]["0"] == 46 or n1["class_distribution"].get(0) == 46


def test_class_filter_logic():
    """Verify class filtering logic finds exact expected nodes for each class."""
    nodes = get_10node_nodes()

    def filter_class(class_id):
        return [
            n["id"]
            for n in nodes
            if class_id in n["assigned_classes"] or (n["vector_10d"][class_id] > 0.0)
        ]

    # Airplane (C1, 0-indexed: 0) -> Nodes 1, 2, 9
    airplane_nodes = filter_class(0)
    assert sorted(airplane_nodes) == [1, 2, 9]

    # Cat (C4, 0-indexed: 3) -> Nodes 3, 4, 5, 8
    cat_nodes = filter_class(3)
    assert sorted(cat_nodes) == [3, 4, 5, 8]

    # Frog (C7, 0-indexed: 6) -> Nodes 6, 7, 10
    frog_nodes = filter_class(6)
    assert sorted(frog_nodes) == [6, 7, 10]


def test_step2_frontend_modal_elements_and_logic():
    """Verify frontend HTML and JS contain required Step 2 node inspector vector elements."""
    with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="cardVectorSection"' in html_content
    assert 'id="cardVectorArray"' in html_content
    assert 'id="cardVectorBreakdownBody"' in html_content

    with open("frontend/static/app.js", "r", encoding="utf-8") as f:
        js_content = f.read()

    assert "STORYBOARD_10_VECTORS" in js_content
    assert 'cardVectorSection' in js_content
    assert 'cardVectorArray' in js_content
    assert 'cardVectorBreakdownBody' in js_content
    assert 'LOCAL_TRAINED' in js_content


def test_steps_md_vector_consistency():
    """Verify vectors in STEPS.md match backend EXPECTED_EXACT_VECTORS for all 10 nodes."""
    with open("STEPS.md", "r", encoding="utf-8") as f:
        steps_md = f.read()

    for nid, vec in EXPECTED_EXACT_VECTORS.items():
        vec_str = ", ".join(f"{x:.2f}" for x in vec)
        expected_line = f"Node {nid}"
        assert expected_line in steps_md, f"Node {nid} not found in STEPS.md"
        assert f"[{vec_str}]" in steps_md, f"Vector for Node {nid} [{vec_str}] not found in STEPS.md"

