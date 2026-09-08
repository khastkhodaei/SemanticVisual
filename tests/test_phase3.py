"""Automated Test Suite for Phase 3 of SemanticDFL Protocol Simulator.

Verifies:
1. Top-P Compact Model Signature extraction and sparse cosine evaluation vs dense numpy dot product.
2. Intra-Zone Dynamic Affinity Propagation (AP) clustering, semantic category coherence,
   and Super-Peer / Replica Set election.
3. Hierarchical Semantic Overlay Network (SON) tree DAG validity and depth bound H <= ceil(log2 N) + 1.
4. FastAPI step endpoints pipeline (/step/signatures, /step/clustering, /step/son-hierarchy).
"""

import math
from collections import defaultdict, deque
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.engine import SemanticDFLEngine
from backend.main import app


def test_sparse_signature_cosine():
    """Verify that sparse_cosine_similarity matches standard NumPy dense dot product

    on masked vectors within tolerance 10^-5.
    """
    engine = SemanticDFLEngine(seed=101)
    N = 10
    global_p = 15
    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]

    sig_res = engine.extract_compact_signatures(nodes=nodes, global_p=global_p)
    signatures = sig_res["signatures"]

    assert len(signatures) == N
    for nid, sig in signatures.items():
        assert len(sig["indices"]) == global_p
        assert len(sig["values"]) == global_p
        assert sig["norm"] > 0

    # Test all pairs
    for i in range(N):
        node_a = nodes[i]
        sig_a = signatures[node_a["id"]]

        # Construct dense masked vector A
        dense_a = np.zeros(50, dtype=np.float64)
        for idx, val in zip(sig_a["indices"], sig_a["values"]):
            dense_a[idx] = val
        norm_dense_a = np.linalg.norm(dense_a)

        for j in range(i, N):
            node_b = nodes[j]
            sig_b = signatures[node_b["id"]]

            # Construct dense masked vector B
            dense_b = np.zeros(50, dtype=np.float64)
            for idx, val in zip(sig_b["indices"], sig_b["values"]):
                dense_b[idx] = val
            norm_dense_b = np.linalg.norm(dense_b)

            sparse_sim = engine.sparse_cosine_similarity(sig_a, sig_b)

            if norm_dense_a == 0 or norm_dense_b == 0:
                expected_dense_sim = 0.0
            else:
                expected_dense_sim = float(np.dot(dense_a, dense_b) / (norm_dense_a * norm_dense_b))

            assert np.isclose(sparse_sim, expected_dense_sim, atol=1e-5), (
                f"Sparse cosine mismatch between node {i} and {j}: "
                f"sparse={sparse_sim:.6f}, dense={expected_dense_sim:.6f}"
            )


def test_affinity_propagation_clustering():
    """Verify dynamic AP clustering:

    - Identical categories are grouped together into coherent clusters.
    - Every cluster has an elected primary Super-Peer and valid Replica set (|R_j| >= 1).
    """
    engine = SemanticDFLEngine(seed=202)
    # Generate 15 nodes with 5 of each category
    nodes = []
    global_p = 18
    for i in range(15):
        cat = i % 3
        weights = engine.generate_node_weights(cat)
        nodes.append({
            "id": i,
            "category": cat,
            "category_name": {0: "Cat_Classifier", 1: "Car_Classifier", 2: "Audio_Classifier"}[cat],
            "weights": weights,
            "vrf_score": 0.5,
            "role": "CLIENT",
            "state": "ASSIGNED",
            "zone_id": 1,
        })

    engine.extract_compact_signatures(nodes, global_p=global_p)
    c_res = engine.cluster_intra_zone(zone_nodes=nodes, global_p=global_p, replication_factor=2)
    clusters = c_res["clusters"]

    assert len(clusters) >= 3, f"Expected at least 3 semantic clusters, got {len(clusters)}"

    # Check that each cluster is category-pure (high semantic coherence)
    node_map = {n["id"]: n for n in nodes}
    for cluster in clusters:
        members = cluster["members"]
        assert len(members) >= 1
        member_cats = [node_map[m]["category"] for m in members]
        # Most frequent category should represent >= 80% of the cluster
        dominant_cat = max(set(member_cats), key=member_cats.count)
        purity = member_cats.count(dominant_cat) / len(member_cats)
        assert purity >= 0.80, f"Cluster {cluster['cluster_id']} has low category purity: {purity:.2f}"

        # Super-Peer election check
        sp_id = cluster["super_peer_id"]
        assert sp_id in members
        assert node_map[sp_id]["role"] == "SUPER_PEER"

        # Replica set election check (|R_j| >= 1)
        replicas = cluster["replica_set"]
        assert len(replicas) >= 1, f"Cluster {cluster['cluster_id']} must have at least 1 replica"
        for r_id in replicas:
            assert r_id in members


def test_hierarchical_son_tree():
    """Verify Hierarchical SON tree DAG validity and depth bound H <= ceil(log2 N) + 1."""
    engine = SemanticDFLEngine(seed=303)
    N = 36
    global_p = 15
    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]
    adj = topology["adjacency_list"]

    # Elect leaders and form zones
    engine.run_vrf_election(nodes, adj, r_hops=2)
    zone_res = engine.run_zone_formation(nodes, adj, r_hops=2, max_zone_size=8)
    zones = zone_res["zones"]

    # Build SON hierarchy tree
    son_res = engine.build_hierarchical_son(nodes=nodes, zones=zones, global_p=global_p, max_fanout=4)

    tree_nodes = son_res["tree_nodes"]
    tree_edges = son_res["tree_edges"]
    depth_H = son_res["depth"]

    assert len(tree_nodes) >= N
    assert len(tree_edges) > 0

    # 1. Depth bound: H <= ceil(log2 N) + 1
    max_allowed_depth = math.ceil(math.log2(N)) + 1
    assert depth_H <= max_allowed_depth, (
        f"Hierarchy depth H={depth_H} exceeds theoretical bound ceil(log2 {N}) + 1 = {max_allowed_depth}"
    )

    # 2. Verify tree structure is a valid Directed Acyclic Graph (DAG)
    # Build graph: source -> target
    graph = defaultdict(list)
    in_degrees = defaultdict(int)
    all_node_ids = set()

    for node in tree_nodes:
        all_node_ids.add(node["id"])

    for edge in tree_edges:
        u = edge["source"]
        v = edge["target"]
        assert u in all_node_ids, f"Edge source {u} not in tree_nodes"
        assert v in all_node_ids, f"Edge target {v} not in tree_nodes"
        graph[u].append(v)
        in_degrees[v] += 1
        if u not in in_degrees:
            in_degrees[u] = 0

    # Topological sort (Kahn's algorithm) to prove acyclicity
    queue = deque([n for n in all_node_ids if in_degrees[n] == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for nxt in graph[curr]:
            in_degrees[nxt] -= 1
            if in_degrees[nxt] == 0:
                queue.append(nxt)

    assert visited_count == len(all_node_ids), "Cycle detected! Tree structure is not a valid DAG."

    # 3. Assert that leaf nodes point correctly to their parent super-peers
    leaf_nodes = [n for n in tree_nodes if n["level"] == 0]
    for leaf in leaf_nodes:
        # Check if there is an outgoing edge from leaf to a level-1 super peer
        targets = graph[leaf["id"]]
        if leaf["type"] != "super_peer":
            assert len(targets) == 1, f"Leaf node {leaf['id']} must point to exactly 1 parent super-peer"
            target_node = next(n for n in tree_nodes if n["id"] == targets[0])
            assert target_node["level"] >= 1, f"Leaf node {leaf['id']} points to non-super-peer level {target_node['level']}"


def test_phase3_endpoints():
    """Verify FastAPI Phase 3 endpoints: /step/signatures, /step/clustering, /step/son-hierarchy."""
    client = TestClient(app)

    # Step 0: Initialize simulation
    init_payload = {
        "num_nodes": 24,
        "d_limit": 0.35,
        "r_hops": 2,
        "max_zone_size": 8,
        "theta": 0.70,
        "q": 0.20,
    }
    init_resp = client.post("/api/v1/init", json=init_payload)
    assert init_resp.status_code == 200
    session_id = init_resp.json()["session_id"]

    # Run VRF and Zones steps
    client.post("/api/v1/step/vrf", json={"session_id": session_id})
    client.post("/api/v1/step/zones", json={"session_id": session_id})
    client.post("/api/v1/step/global-p", json={"session_id": session_id})

    # Step 1: Extract Signatures
    sig_resp = client.post("/api/v1/step/signatures", json={"session_id": session_id, "global_p": 16})
    assert sig_resp.status_code == 200
    sig_data = sig_resp.json()
    assert "signatures" in sig_data
    assert len(sig_data["signatures"]) == 24
    assert sig_data["global_p"] == 16
    assert len(sig_data["sample_similarities"]) > 0

    # Step 2: Intra-Zone AP Clustering
    clust_resp = client.post("/api/v1/step/clustering", json={"session_id": session_id, "replication_factor": 2})
    assert clust_resp.status_code == 200
    clust_data = clust_resp.json()
    assert "clusters" in clust_data
    assert len(clust_data["clusters"]) >= 1
    assert "super_peers" in clust_data
    assert len(clust_data["super_peers"]) == len(clust_data["clusters"])

    # Step 3: Global SON Hierarchy Construction
    son_resp = client.post("/api/v1/step/son-hierarchy", json={"session_id": session_id, "max_fanout": 4})
    assert son_resp.status_code == 200
    son_data = son_resp.json()
    assert "depth" in son_data
    assert son_data["depth"] >= 2
    assert "tree_nodes" in son_data
    assert len(son_data["tree_nodes"]) >= 24
    assert "tree_edges" in son_data
    assert len(son_data["tree_edges"]) > 0
