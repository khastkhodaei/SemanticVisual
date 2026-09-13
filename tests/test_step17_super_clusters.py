"""Automated Verification Suite for Step 17: Inter-Zone Meta-Clustering & Global Super-Cluster Formation.

Verifies:
1. Endpoints GET and POST /api/v1/storyboard/step/17 return HTTP 200 with complete storyboard payload.
2. 3 Global Super-Clusters formed:
   - SC-1: Aviation & Vehicles (C1-C3), clusters ["2-A", "8-B"], peers [1, 2, 9], exemplars [1, 9]
   - SC-2: Animals (C4-C6), clusters ["2-B", "4-A", "8-A"], peers [3, 4, 5, 8], exemplars [3, 5, 8]
   - SC-3: Heavy Transport & Amphibians (C7-C10), clusters ["4-B", "8-C"], peers [6, 7, 10], exemplars [7, 10]
3. Cross-zone peer assignments:
   - Node 9 shares SC-1 with Nodes 1 and 2.
   - Node 3 shares SC-2 with Nodes 4, 5, and 8.
   - Node 10 shares SC-3 with Nodes 6 and 7.
4. Node 4 holds similarity_matrix_7x7 with 7x7 matrix and 3 super-clusters overview.
5. Pairwise Cosine Similarity values:
   - Diagonals are 1.0
   - sim(2-A, 8-B) == 1.0
   - sim(4-B, 8-C) == 0.866
   - Orthogonal pairs == 0.0
6. SemanticDFLEngine().run_meta_clustering_super_clusters_10nodes() returns valid step 17 data.
7. STEPS.md contains documentation for Step 17 with 7x7 similarity matrix and 3 Global Super-Clusters.
8. Frontend elements in index.html and app.js support Step 17.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.engine import SemanticDFLEngine
from backend.storyboard_10nodes import get_10node_step_data


@pytest.fixture
def client():
    return TestClient(app)


def test_step17_endpoints_return_200(client):
    """Assert GET and POST /api/v1/storyboard/step/17 return HTTP 200 with proper badge."""
    res_get = client.get("/api/v1/storyboard/step/17")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["step"] == 17
    assert data_get["phase_badge"] == "ACTIVE PHASE: STEP 17: GLOBAL SUPER-CLUSTER FORMATION"
    assert data_get["total_nodes"] == 10
    assert data_get["total_edges"] == 18
    assert data_get["total_steps"] in (17, 18, 19)

    res_post = client.post("/api/v1/storyboard/step/17")
    assert res_post.status_code == 200
    assert res_post.json()["step"] == 17


def test_step17_three_super_clusters_structure(client):
    """Assert 3 super-clusters are returned with correct cluster IDs and exemplars."""
    res = client.get("/api/v1/storyboard/step/17")
    assert res.status_code == 200
    data = res.json()

    super_clusters = data.get("super_clusters", [])
    assert len(super_clusters) == 3

    sc_map = {sc["id"]: sc for sc in super_clusters}
    assert "SC-1" in sc_map
    assert "SC-2" in sc_map
    assert "SC-3" in sc_map

    # SC-1: Aviation & Vehicles
    assert sc_map["SC-1"]["clusters"] == ["2-A", "8-B"]
    assert sc_map["SC-1"]["peers"] == [1, 2, 9]
    assert sc_map["SC-1"]["exemplars"] == [1, 9]

    # SC-2: Animals
    assert sc_map["SC-2"]["clusters"] == ["2-B", "4-A", "8-A"]
    assert sc_map["SC-2"]["peers"] == [3, 4, 5, 8]
    assert sc_map["SC-2"]["exemplars"] == [3, 5, 8]

    # SC-3: Heavy Transport & Amphibians
    assert sc_map["SC-3"]["clusters"] == ["4-B", "8-C"]
    assert sc_map["SC-3"]["peers"] == [6, 7, 10]
    assert sc_map["SC-3"]["exemplars"] == [7, 10]


def test_step17_nodes_assigned_super_clusters_and_cross_zone_peers(client):
    """Assert nodes share super-clusters across zones:
    - Node 9 shares SC-1 with Nodes 1 and 2.
    - Node 3 shares SC-2 with Nodes 4, 5, and 8.
    - Node 10 shares SC-3 with Nodes 6 and 7.
    """
    res = client.get("/api/v1/storyboard/step/17")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}

    # SC-1: Nodes 1, 2, 9
    assert nodes[9]["assigned_super_cluster"] == "SC-1"
    assert nodes[1]["assigned_super_cluster"] == "SC-1"
    assert nodes[2]["assigned_super_cluster"] == "SC-1"
    assert set(nodes[9]["cross_zone_semantic_peers"]) == {1, 2}
    assert set(nodes[1]["cross_zone_semantic_peers"]) == {2, 9}

    # SC-2: Nodes 3, 4, 5, 8
    assert nodes[3]["assigned_super_cluster"] == "SC-2"
    assert nodes[4]["assigned_super_cluster"] == "SC-2"
    assert nodes[5]["assigned_super_cluster"] == "SC-2"
    assert nodes[8]["assigned_super_cluster"] == "SC-2"
    assert set(nodes[3]["cross_zone_semantic_peers"]) == {4, 5, 8}
    assert set(nodes[4]["cross_zone_semantic_peers"]) == {3, 5, 8}

    # SC-3: Nodes 6, 7, 10
    assert nodes[10]["assigned_super_cluster"] == "SC-3"
    assert nodes[6]["assigned_super_cluster"] == "SC-3"
    assert nodes[7]["assigned_super_cluster"] == "SC-3"
    assert set(nodes[10]["cross_zone_semantic_peers"]) == {6, 7}
    assert set(nodes[6]["cross_zone_semantic_peers"]) == {7, 10}


def test_step17_node4_similarity_matrix_7x7(client):
    """Assert Node 4 holds the 7x7 Cosine Similarity Matrix with exact values."""
    res = client.get("/api/v1/storyboard/step/17")
    assert res.status_code == 200
    data = res.json()
    nodes = {n["id"]: n for n in data["nodes"]}
    node4 = nodes[4]

    assert node4["meta_clustering_status"] == "SUPER_CLUSTERS_FORMED"
    matrix_data = node4.get("similarity_matrix_7x7", {})
    cluster_ids = matrix_data.get("cluster_ids", [])
    matrix = matrix_data.get("matrix", [])

    assert cluster_ids == ["2-A", "2-B", "4-A", "4-B", "8-A", "8-B", "8-C"]
    assert len(matrix) == 7
    for row in matrix:
        assert len(row) == 7

    # Diagonal must all be 1.0
    for i in range(7):
        assert matrix[i][i] == 1.0

    # Index mapping
    idx = {cid: i for i, cid in enumerate(cluster_ids)}

    # 2-A and 8-B have identical mask [1,1,1,0,0,0,0,0,0,0] -> similarity 1.0
    assert matrix[idx["2-A"]][idx["8-B"]] == 1.0
    assert matrix[idx["8-B"]][idx["2-A"]] == 1.0

    # 2-B, 4-A, 8-A have identical mask [0,0,0,1,1,1,0,0,0,0] -> similarity 1.0
    assert matrix[idx["2-B"]][idx["4-A"]] == 1.0
    assert matrix[idx["4-A"]][idx["8-A"]] == 1.0
    assert matrix[idx["2-B"]][idx["8-A"]] == 1.0

    # 4-B and 8-C have masks [0,0,0,0,0,0,1,1,1,1] and [0,0,0,0,0,0,0,1,1,1] -> 3 / (2 * sqrt(3)) = 0.866
    assert matrix[idx["4-B"]][idx["8-C"]] == 0.866
    assert matrix[idx["8-C"]][idx["4-B"]] == 0.866

    # Orthogonal clusters must be 0.0
    assert matrix[idx["2-A"]][idx["4-A"]] == 0.0
    assert matrix[idx["8-B"]][idx["8-C"]] == 0.0


def test_step17_engine_method():
    """Verify SemanticDFLEngine().run_meta_clustering_super_clusters_10nodes() produces valid structure."""
    engine = SemanticDFLEngine()
    result = engine.run_meta_clustering_super_clusters_10nodes()
    assert result["step"] == 17
    assert result["total_steps"] in (17, 18, 19)
    assert len(result["nodes"]) == 10
    assert result["top_initiator"] == 4
    assert len(result["super_clusters"]) == 3
    assert len(result["similarity_matrix_7x7"]["matrix"]) == 7


def test_step17_steps_markdown_documentation():
    """Verify STEPS.md contains documentation for Step 17 with 7x7 matrix and 3 Super-Clusters."""
    steps_file = Path(__file__).resolve().parent.parent / "STEPS.md"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "## Step 17 — Inter-Zone Meta-Clustering & Global Super-Cluster Formation" in content
    assert "7x7 Inter-Cluster Similarity Matrix" in content
    assert "Super-Cluster 1" in content
    assert "Super-Cluster 2" in content
    assert "Super-Cluster 3" in content
    assert "SC-1" in content
    assert "SC-2" in content
    assert "SC-3" in content


def test_step17_frontend_elements_and_logic(client):
    """Verify frontend template and app.js contain Step 17 UI elements and rendering logic."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "stepNav17" in res_index.text
    assert "cardSuperClusterSection" in res_index.text
    assert "cardSuperClusterBadge" in res_index.text

    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "renderStep17" in res_js.text
    assert "animateStep17SuperClusters" in res_js.text
    assert "ACTIVE PHASE: STEP 17: GLOBAL SUPER-CLUSTER FORMATION" in res_js.text
    assert "super-cluster-sc1" in res_js.text
    assert "super-cluster-sc2" in res_js.text
    assert "super-cluster-sc3" in res_js.text
