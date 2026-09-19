"""Automated Verification Suite for Step 12: Intra-Zone Semantic Clustering via Cosine Similarity & Affinity Propagation (AP).

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/12 return HTTP 200 with complete storyboard payload.
2. Initiators evaluate intra-zone Cosine Similarity matrices:
   - Zone 2 (Initiator C2): 3x3 matrix with Sim(1, 2) = 1.0, Sim(1, 3) = 0.0, Sim(2, 3) = 0.0.
   - Zone 4 (Initiator C4): 4x4 matrix with Sim(4, 5) = 1.0, Sim(6, 7) = 0.67, cross-pairs = 0.0.
   - Zone 8 (Initiator C8): 3x3 matrix with all non-diagonal similarities = 0.0.
3. Affinity Propagation deterministic clustering partitions:
   - Zone 2: Cluster 2-A {1, 2} (Exemplar C2) & Cluster 2-B {3} (Exemplar C3).
   - Zone 4: Cluster 4-A {4, 5} (Exemplar C4) & Cluster 4-B {6, 7} (Exemplar C7).
   - Zone 8: 3 orthogonal clusters: Cluster 8-A {8}, Cluster 8-B {9}, Cluster 8-C {10}.
4. All 10 nodes contain:
   - assigned_cluster_id
   - cluster_exemplar
   - cluster_peers
5. Engine method run_intra_zone_clustering_10nodes executes correctly.
6. Documentation in STEPS.md contains Step 12.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine
from backend.storyboard_10nodes import (
    get_10node_step_data,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_step12_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/12 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/12")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 12
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 12: INTRA-ZONE SEMANTIC CLUSTERING (AP)"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18

    res_post = client.post("/api/v1/storyboard/step/12")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 12


def test_step12_zone2_clustering():
    """Assert Zone 2 (Initiator C2) produces clusters {1, 2} and {3}."""
    data = get_10node_step_data(12)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Node 1 and Node 2 in Cluster 2-A with Exemplar 2
    assert nodes[1]["assigned_cluster_id"] == "2-A"
    assert nodes[1]["cluster_exemplar"] == 2
    assert set(nodes[1]["cluster_peers"]) == {1, 2}

    assert nodes[2]["assigned_cluster_id"] == "2-A"
    assert nodes[2]["cluster_exemplar"] == 2
    assert set(nodes[2]["cluster_peers"]) == {1, 2}

    # Node 3 in Cluster 2-B with Exemplar 3
    assert nodes[3]["assigned_cluster_id"] == "2-B"
    assert nodes[3]["cluster_exemplar"] == 3
    assert set(nodes[3]["cluster_peers"]) == {3}

    # Verify Initiator C2 holds the full intra-zone similarity matrix and clusters
    c2_matrix = nodes[2]["intra_zone_similarity_matrix"]
    assert c2_matrix["peers"] == ["C1", "C2", "C3"]
    assert c2_matrix["matrix"] == [
        [1.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    clusters = nodes[2]["clusters"]
    assert "2-A" in clusters and "2-B" in clusters
    assert set(clusters["2-A"]["members"]) == {1, 2}
    assert set(clusters["2-B"]["members"]) == {3}


def test_step12_zone4_clustering():
    """Assert Zone 4 (Initiator C4) produces clusters {4, 5} and {6, 7}."""
    data = get_10node_step_data(12)
    nodes = {n["id"]: n for n in data["nodes"]}

    # Nodes 4 & 5 in Cluster 4-A with Exemplar 4
    assert nodes[4]["assigned_cluster_id"] == "4-A"
    assert nodes[4]["cluster_exemplar"] == 4
    assert set(nodes[4]["cluster_peers"]) == {4, 5}

    assert nodes[5]["assigned_cluster_id"] == "4-A"
    assert nodes[5]["cluster_exemplar"] == 4
    assert set(nodes[5]["cluster_peers"]) == {4, 5}

    # Nodes 6 & 7 in Cluster 4-B with Exemplar 7
    assert nodes[6]["assigned_cluster_id"] == "4-B"
    assert nodes[6]["cluster_exemplar"] == 7
    assert set(nodes[6]["cluster_peers"]) == {6, 7}

    assert nodes[7]["assigned_cluster_id"] == "4-B"
    assert nodes[7]["cluster_exemplar"] == 7
    assert set(nodes[7]["cluster_peers"]) == {6, 7}

    # Verify Initiator C4 holds the full 4x4 intra-zone similarity matrix and clusters
    c4_matrix = nodes[4]["intra_zone_similarity_matrix"]
    assert c4_matrix["peers"] == ["C4", "C5", "C6", "C7"]
    assert c4_matrix["matrix"] == [
        [1.0, 1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.67],
        [0.0, 0.0, 0.67, 1.0],
    ]
    clusters = nodes[4]["clusters"]
    assert "4-A" in clusters and "4-B" in clusters
    assert set(clusters["4-A"]["members"]) == {4, 5}
    assert set(clusters["4-B"]["members"]) == {6, 7}


def test_step12_zone8_clustering():
    """Assert Zone 8 (Initiator C8) produces 3 orthogonal single-peer clusters {8}, {9}, {10}."""
    data = get_10node_step_data(12)
    nodes = {n["id"]: n for n in data["nodes"]}

    assert nodes[8]["assigned_cluster_id"] == "8-A"
    assert nodes[8]["cluster_exemplar"] == 8
    assert set(nodes[8]["cluster_peers"]) == {8}

    assert nodes[9]["assigned_cluster_id"] == "8-B"
    assert nodes[9]["cluster_exemplar"] == 9
    assert set(nodes[9]["cluster_peers"]) == {9}

    assert nodes[10]["assigned_cluster_id"] == "8-C"
    assert nodes[10]["cluster_exemplar"] == 10
    assert set(nodes[10]["cluster_peers"]) == {10}

    # Verify Initiator C8 holds 3x3 diagonal matrix
    c8_matrix = nodes[8]["intra_zone_similarity_matrix"]
    assert c8_matrix["peers"] == ["C8", "C9", "C10"]
    assert c8_matrix["matrix"] == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    clusters = nodes[8]["clusters"]
    assert set(clusters.keys()) == {"8-A", "8-B", "8-C"}


def test_step12_engine_method():
    """Verify SemanticDFLEngine().run_intra_zone_clustering_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_intra_zone_clustering_10nodes()
    assert result["step"] == 12
    assert len(result["nodes"]) == 10
    assert len(result["edges"]) in (17, 18)
    assert "Zone 2" in result["terminal_logs"][1]


def test_step12_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 12."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 12 — Intra-Zone Semantic Clustering (Affinity Propagation)" in content
    assert r"\text{Sim}(i, j)" in content
    assert "Cluster 2-A" in content
    assert "Cluster 4-A" in content
    assert "Cluster 8-A" in content
