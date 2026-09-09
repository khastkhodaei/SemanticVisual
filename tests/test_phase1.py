"""Automated test suite for Phase 1 of SemanticDFL Protocol Simulator.

Verifies:
1. RGG Physical Topology & Connectivity Guarantee (degree >= 1, distance_norm <= D_limit)
2. Heterogeneous 50-dimensional semantic weight modeling and cosine similarity correlations
3. FastAPI /api/v1/init endpoint and in-memory SessionStore
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.engine import SemanticDFLEngine
from backend.main import app, session_store


def test_rgg_connectivity():
    """Verify that generated RGG topologies have no disconnected singletons

    and that all generated edges strictly respect the D_limit threshold.
    """
    engine = SemanticDFLEngine(seed=42)
    d_limit = 0.35

    for N in [15, 30, 60]:
        topology = engine.generate_topology(N=N, D_limit=d_limit, maintain_connectivity=True)
        nodes = topology["nodes"]
        edges = topology["edges"]
        adj = topology["adjacency_list"]

        assert len(nodes) == N, f"Expected {N} nodes, found {len(nodes)}"
        assert len(adj) == N, f"Expected adjacency list size {N}, found {len(adj)}"

        # 1. Verify every node has degree >= 1 (no disconnected singletons)
        for node in nodes:
            node_id = node["id"]
            degree = node["degree"]
            neighbors = adj[node_id]
            assert degree >= 1, f"Node {node_id} has degree {degree} < 1 (isolated singleton) for N={N}"
            assert len(neighbors) >= 1, f"Node {node_id} has empty neighbor list for N={N}"
            assert degree == len(neighbors), f"Degree metadata mismatch for node {node_id}"

        # 2. Verify all generated edge distances strictly respect the D_limit threshold
        # Using a small floating point epsilon (1e-5) for numerical precision
        for edge in edges:
            u = edge["source"]
            v = edge["target"]
            dist_norm = edge["distance_norm"]
            assert dist_norm <= d_limit + 1e-5, (
                f"Edge ({u}, {v}) distance_norm {dist_norm} exceeds D_limit {d_limit}"
            )


def test_semantic_weight_correlation():
    """Verify 50-dimensional heterogeneous parameter modeling across 3 categories.

    - Mean cosine similarity between pairs belonging to SAME category >= 0.70
    - Mean cosine similarity between pairs belonging to DIFFERENT categories <= 0.45
    """
    engine = SemanticDFLEngine(seed=2026)
    N = 60
    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]

    same_cat_sims = []
    diff_cat_sims = []

    for i in range(N):
        node_a = nodes[i]
        weights_a = node_a["weights"]

        # Validate dimensional constraints
        assert len(weights_a) == 50, f"Node {i} weights must be 50-dimensional, got {len(weights_a)}"
        assert node_a["category"] in [0, 1, 2], f"Invalid category {node_a['category']}"
        assert node_a["role"] == "CLIENT"
        assert node_a["state"] == "NOT_ASSIGNED"
        assert node_a["zone_id"] is None
        assert node_a["alive"] is True
        assert 0.0 <= node_a["vrf_score"] < 1.0

        for j in range(i + 1, N):
            node_b = nodes[j]
            weights_b = node_b["weights"]
            sim = engine.cosine_similarity(weights_a, weights_b)

            if node_a["category"] == node_b["category"]:
                same_cat_sims.append(sim)
            else:
                diff_cat_sims.append(sim)

    assert len(same_cat_sims) > 0, "No intra-category pairs generated"
    assert len(diff_cat_sims) > 0, "No inter-category pairs generated"

    mean_same = float(np.mean(same_cat_sims))
    mean_diff = float(np.mean(diff_cat_sims))

    print(f"\n[Validation] Intra-category Mean Cosine Sim: {mean_same:.4f} (Required: >= 0.70)")
    print(f"[Validation] Inter-category Mean Cosine Sim: {mean_diff:.4f} (Required: <= 0.45)")

    # Assertions according to specification
    assert mean_same >= 0.70, f"Mean intra-category similarity {mean_same:.4f} < 0.70"
    assert mean_diff <= 0.45, f"Mean inter-category similarity {mean_diff:.4f} > 0.45"


def test_init_api_endpoint():
    """Verify FastAPI /api/v1/init endpoint returns valid session, topology, and logs."""
    client = TestClient(app)

    # Health check endpoint verification
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    health_json = health_resp.json()
    assert health_json["status"] == "ok"
    assert "active_sessions" in health_json

    # Test initialization payload
    payload = {
        "num_nodes": 24,
        "d_limit": 0.35,
        "r_hops": 2,
        "max_zone_size": 8,
        "theta": 0.70,
        "q": 0.20,
    }

    response = client.post("/api/v1/init", json=payload)
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}, {response.text}"

    data = response.json()

    # Verify session ID
    assert "session_id" in data
    session_id = data["session_id"]
    assert len(session_id) > 0

    # Verify topology contents
    assert "nodes" in data
    assert len(data["nodes"]) == 24
    assert "edges" in data
    assert len(data["edges"]) > 0
    assert "adjacency_list" in data
    assert len(data["adjacency_list"]) == 24
    assert "metadata" in data
    assert data["metadata"]["num_nodes"] == 24

    # Verify logs
    assert "logs" in data
    assert len(data["logs"]) >= 3
    assert any("Initializing simulation session" in log["message"] for log in data["logs"])
    assert any("RGG topology generated" in log["message"] for log in data["logs"])

    # Verify session is persisted in SessionStore
    saved_session = session_store.get_session(session_id)
    assert saved_session is not None
    assert saved_session["session_id"] == session_id
    assert len(saved_session["nodes"]) == 24


def test_benchmark_homogeneous_models_and_non_iid_partitions():
    """Verify that all nodes share a homogeneous model family while possessing

    cluster-aligned Non-IID label partitions, and verify benchmark switching.
    """
    engine = SemanticDFLEngine(seed=777)
    client = TestClient(app)

    benchmarks = ["FMNIST (CNN)", "Tiny ImageNet (ResNet-18)", "Google Speech (ResNet-18)"]

    for bench in benchmarks:
        topo = engine.generate_topology(N=18, D_limit=0.35, benchmark=bench)
        nodes = topo["nodes"]
        meta = topo["metadata"]

        assert meta["benchmark"] == bench
        expected_arch = meta["model_architecture"]

        # 1. Homogeneous model family across all nodes
        for node in nodes:
            assert node["benchmark"] == bench
            assert node["model_architecture"] == expected_arch
            assert "Cluster" in node["category_name"]
            assert len(node["weights"]) == 50

        # 2. Test API initialization with this benchmark preset
        resp = client.post("/api/v1/init", json={
            "benchmark": bench,
            "num_nodes": 12,
            "d_limit": 0.35,
            "r_hops": 2,
            "max_zone_size": 6,
            "theta": 0.70,
            "q": 0.20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["metadata"]["benchmark"] == bench
        assert data["metadata"]["model_architecture"] == expected_arch
        assert all(n["model_architecture"] == expected_arch for n in data["nodes"])


def test_step1_storyboard_topology_and_data_distribution():
    """Verify Step 1: 50-node overlay-free physical ad-hoc network topology (Figure 3a).

    1. Exactly 50 nodes (C_1 to C_50) generated with status='NOT_ASSIGNED', role='CLIENT', zone_id=None.
    2. Physical graph is connected (single connected component) with node degrees between 3 and 6.
    3. Identical classes (e.g. C1, C2, C20, C21, C35 with Cat 🐱) have cosine similarity >= 0.80.
    4. Disjoint classes have low cosine similarity (< 0.20).
    5. API endpoint initializes 50-node storyboard session cleanly.
    """
    from collections import deque

    engine = SemanticDFLEngine(seed=2026)
    topo = engine.generate_topology(N=50)

    nodes = topo["nodes"]
    edges = topo["edges"]
    adj = topo["adjacency_list"]

    # 1. Exactly 50 nodes, all NOT_ASSIGNED, role CLIENT, zone_id None
    assert len(nodes) == 50, f"Expected 50 nodes, got {len(nodes)}"
    for node in nodes:
        assert node["status"] == "NOT_ASSIGNED"
        assert node["role"] == "CLIENT"
        assert node["zone_id"] is None
        assert len(node["weights"]) == 50
        assert 3 <= node["degree"] <= 6, f"Node {node['id']} degree {node['degree']} outside [3, 6]"
        assert "class_name" in node
        assert "class_icon" in node
        assert node["label"].startswith(f"C{node['id']} ")

    # 2. Verify graph is connected (single connected component, no isolated singletons)
    visited = set()
    queue = deque([nodes[0]["id"]])
    visited.add(nodes[0]["id"])
    while queue:
        curr = queue.popleft()
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    assert len(visited) == 50, f"Graph is disconnected: reached {len(visited)}/50 nodes"
    assert len(edges) > 0

    # 3. Verify cosine similarities: identical class pairs >= 0.80, disjoint < 0.20
    node_map = {n["id"]: n for n in nodes}
    cat_nodes = [n["id"] for n in nodes if n["class_id"] == 0]
    assert set(cat_nodes) == {1, 2, 20, 21, 22, 35}, f"Unexpected Cat nodes: {cat_nodes}"

    # Pairwise Cat nodes similarity (including C1 and C20 which are physically separated)
    sim_c1_c20 = engine.cosine_similarity(node_map[1]["weights"], node_map[20]["weights"])
    sim_c1_c2 = engine.cosine_similarity(node_map[1]["weights"], node_map[2]["weights"])
    sim_c21_c35 = engine.cosine_similarity(node_map[21]["weights"], node_map[35]["weights"])

    assert sim_c1_c20 >= 0.80, f"C1 and C20 similarity {sim_c1_c20} < 0.80"
    assert sim_c1_c2 >= 0.80, f"C1 and C2 similarity {sim_c1_c2} < 0.80"
    assert sim_c21_c35 >= 0.80, f"C21 and C35 similarity {sim_c21_c35} < 0.80"

    # Disjoint classes (Cat vs Car, Cat vs Dog, etc.)
    sim_c1_c3 = engine.cosine_similarity(node_map[1]["weights"], node_map[3]["weights"])  # Cat vs Car
    assert sim_c1_c3 < 0.20, f"C1 (Cat) and C3 (Car) similarity {sim_c1_c3} >= 0.20"

    # 4. API endpoint verification for default 50-node initialization
    client = TestClient(app)
    resp = client.post("/api/v1/init", json={"num_nodes": 50})
    assert resp.status_code == 200
    api_data = resp.json()
    assert len(api_data["nodes"]) == 50
    assert all(n["status"] == "NOT_ASSIGNED" for n in api_data["nodes"])


