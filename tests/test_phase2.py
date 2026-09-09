"""Automated Test Suite for Phase 2 of SemanticDFL Protocol Simulator.

Verifies:
1. VRF Leader Election & R-hop spatial dispersion guarantee
2. TTL-Bounded First-Wins Zone Probing & Deterministic S_Z Cardinality Splitting
3. Global-P Consensus via Binary Search and Quantile Retention
4. FastAPI Step Endpoints Pipeline (/step/vrf, /step/zones, /step/global-p)
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.engine import SemanticDFLEngine
from backend.main import app, session_store


def test_vrf_leader_dispersion():
    """Verify that VRF leader election guarantees spatial dispersion:

    No two elected INITIATORS can be within R physical hops of each other.
    """
    engine = SemanticDFLEngine(seed=123)
    r_hops = 2
    topology = engine.generate_topology(N=40, D_limit=0.35)
    nodes = topology["nodes"]
    adj = topology["adjacency_list"]

    result = engine.run_vrf_election(nodes=nodes, adjacency_list=adj, r_hops=r_hops)
    initiators = result["initiators"]

    assert len(initiators) >= 1, "At least one initiator must be elected"
    assert len(result["logs"]) > 0

    # Verify dispersion: Check pairwise hop distance between all initiators
    # using BFS to ensure hop_distance(init_a, init_b) > r_hops
    for i in range(len(initiators)):
        init_a = initiators[i]
        # BFS from init_a up to r_hops
        visited_r_hops = set(engine.get_r_hop_neighborhood(init_a, adj, r_hops))

        for j in range(i + 1, len(initiators)):
            init_b = initiators[j]
            assert init_b not in visited_r_hops, (
                f"Dispersion violation: Initiator {init_a} and Initiator {init_b} "
                f"are within {r_hops} physical hops of each other!"
            )


def test_zone_first_wins_and_cap():
    """Verify TTL first-wins zone probing, boundary detection, and S_Z splitting cap."""
    engine = SemanticDFLEngine(seed=456)
    r_hops = 2
    max_zone_size = 8
    N = 45

    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]
    adj = topology["adjacency_list"]

    # 1. Run VRF election
    engine.run_vrf_election(nodes=nodes, adjacency_list=adj, r_hops=r_hops)

    # 2. Run Zone Formation
    zone_res = engine.run_zone_formation(
        nodes=nodes,
        adjacency_list=adj,
        r_hops=r_hops,
        max_zone_size=max_zone_size,
    )

    updated_nodes = zone_res["nodes"]
    zones = zone_res["zones"]
    boundaries = zone_res["boundaries"]
    packet_hops = zone_res["packet_hops"]

    # Assertion 1: All nodes have a single valid assigned zone_id
    for node in updated_nodes:
        assert node["state"] == "ASSIGNED", f"Node {node['id']} should be ASSIGNED"
        assert node["zone_id"] is not None, f"Node {node['id']} has null zone_id"
        assert isinstance(node["zone_id"], int), f"Node {node['id']} zone_id must be integer"
        assert node["zone_id"] in zones, f"Node {node['id']} zone_id not found in zones registry"

    # Assertion 2: Strict S_Z cardinality cap - no zone has size > max_zone_size
    for zid, members in zones.items():
        assert len(members) <= max_zone_size, (
            f"Cardinality violation: Zone {zid} has {len(members)} nodes, exceeding S_Z={max_zone_size}"
        )

    # Total members across all zones must equal N
    total_members = sum(len(m) for m in zones.values())
    assert total_members == N, f"Expected {N} total zone members, found {total_members}"

    # Assertion 3: Boundary events are detected between neighboring zones
    assert len(packet_hops) > 0, "Packet hops must be recorded for trajectory analysis"
    assert len(boundaries) > 0, "Inter-zone boundary events should be detected in connected topology"
    for b in boundaries:
        assert b["zone_a"] != b["zone_b"], f"Boundary detected inside the same zone: {b}"


def test_global_p_binary_search():
    """Verify decentralized binary search for local P_i^{min} and quantile consensus."""
    engine = SemanticDFLEngine(seed=789)
    N = 30
    theta = 0.70
    q = 0.20

    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]

    gp_res = engine.calculate_global_p_consensus(nodes=nodes, theta=theta, q=q)

    local_p = gp_res["local_p"]
    directional_sims = gp_res["directional_similarities"]
    global_p = gp_res["global_p"]
    exact_q = gp_res["exact_quantile"]

    # Assertion 1: For each node, pruned signature with size P_i^{min} meets >= theta similarity
    for node in nodes:
        nid = node["id"]
        p_val = local_p[nid]
        assert 1 <= p_val <= 50, f"Node {nid} local P={p_val} outside [1, 50]"

        # Validate directional cosine similarity independently
        w = np.asarray(node["weights"], dtype=np.float64)
        full_norm = float(np.linalg.norm(w))
        sorted_indices = np.argsort(-np.abs(w))
        retained_sq = sum(w[sorted_indices[:p_val]] ** 2)
        computed_sim = np.sqrt(retained_sq) / full_norm

        assert computed_sim >= theta - 1e-6, (
            f"Node {nid} similarity {computed_sim:.4f} with P={p_val} does not satisfy theta={theta}"
        )
        assert directional_sims[nid] >= theta - 1e-4

        # Minimality check: P_i^{min} - 1 must fail the theta threshold (if p_val > 1)
        if p_val > 1:
            smaller_retained_sq = sum(w[sorted_indices[:p_val - 1]] ** 2)
            smaller_sim = np.sqrt(smaller_retained_sq) / full_norm
            assert smaller_sim < theta, (
                f"P={p_val} is not minimal for node {nid}: P-1 yields similarity {smaller_sim:.4f} >= {theta}"
            )

    # Assertion 2: Verify global_p matches exact q-quantile
    p_values = [local_p[n["id"]] for n in nodes]
    expected_quantile = float(np.quantile(p_values, q))
    assert np.isclose(exact_q, expected_quantile)
    assert global_p == int(np.round(expected_quantile))


def test_phase2_endpoints():
    """Verify FastAPI step endpoints sequentially: /init -> /step/vrf -> /step/zones -> /step/global-p."""
    client = TestClient(app)

    # Step 0: Initialize simulation session
    init_payload = {
        "num_nodes": 20,
        "d_limit": 0.35,
        "r_hops": 2,
        "max_zone_size": 6,
        "theta": 0.75,
        "q": 0.25,
    }
    init_resp = client.post("/api/v1/init", json=init_payload)
    assert init_resp.status_code == 200
    session_id = init_resp.json()["session_id"]

    # Step 1: Execute VRF election step
    vrf_resp = client.post("/api/v1/step/vrf", json={"session_id": session_id})
    assert vrf_resp.status_code == 200
    vrf_data = vrf_resp.json()
    assert "initiators" in vrf_data
    assert len(vrf_data["initiators"]) >= 1
    assert any(n["role"] == "INITIATOR" for n in vrf_data["nodes"])

    # Step 2: Execute Zone formation step
    zones_resp = client.post("/api/v1/step/zones", json={"session_id": session_id})
    assert zones_resp.status_code == 200
    zones_data = zones_resp.json()
    assert "zones" in zones_data
    assert "boundaries" in zones_data
    assert "packet_hops" in zones_data
    assert all(len(members) <= 6 for members in zones_data["zones"].values())

    # Step 3: Execute Global-P consensus step
    gp_resp = client.post("/api/v1/step/global-p", json={"session_id": session_id})
    assert gp_resp.status_code == 200
    gp_data = gp_resp.json()
    assert "global_p" in gp_data
    assert 1 <= gp_data["global_p"] <= 50
    assert "local_p" in gp_data
    assert len(gp_data["local_p"]) == 20
    assert gp_data["theta"] == 0.75
    assert gp_data["q"] == 0.25

    # Step 4: Verify error handling on non-existent session
    bad_resp = client.post("/api/v1/step/vrf", json={"session_id": "non-existent-session-id"})
    assert bad_resp.status_code == 404


def test_storyboard_step2_vrf_election():
    """Verify Step 2 VRF Leader Election on the 50-node Storyboard topology.

    Requirements:
    1. Elects exactly the designated 10 leaders: [2, 7, 13, 17, 22, 28, 32, 37, 42, 47].
    2. All 10 leaders satisfy R=2 spatial dispersion (pairwise hop distance > 2).
    3. Leaders have role="INITIATOR", status="ASSIGNED", and VRF score < 0.10.
    4. Non-leaders have role="CLIENT", status="NOT_ASSIGNED", and VRF score > 0.30.
    """
    engine = SemanticDFLEngine(seed=42)
    step1 = engine.generate_storyboard_step1()
    nodes = step1["nodes"]
    adj = step1["adjacency_list"]

    # In Step 1, all nodes must have None vrf_score
    assert all(n["vrf_score"] is None for n in nodes)
    assert all(n["role"] == "CLIENT" for n in nodes)
    assert all(n["status"] == "NOT_ASSIGNED" for n in nodes)

    # Run Step 2 VRF Election
    vrf_res = engine.run_vrf_election(nodes=nodes, adjacency_list=adj, r_hops=2)
    initiators = vrf_res["initiators"]

    expected_leaders = [2, 7, 13, 17, 22, 28, 32, 37, 42, 47]
    assert sorted(initiators) == expected_leaders, (
        f"Expected leaders {expected_leaders}, got {sorted(initiators)}"
    )

    # Verify R=2 spatial dispersion between all pairs of leaders
    for i in range(len(initiators)):
        leader_a = initiators[i]
        r2_neighbors = set(engine.get_r_hop_neighborhood(leader_a, adj, r_hops=2))
        for j in range(i + 1, len(initiators)):
            leader_b = initiators[j]
            assert leader_b not in r2_neighbors, (
                f"Dispersion violation: Leader C{leader_a} and Leader C{leader_b} "
                f"are within 2 hops of each other!"
            )

    # Verify node roles, statuses, and scores
    for n in nodes:
        nid = n["id"]
        if nid in expected_leaders:
            assert n["role"] == "INITIATOR"
            assert n["status"] == "ASSIGNED"
            assert n["zone_id"] == nid
            assert n["vrf_score"] < 0.10
        else:
            assert n["role"] == "CLIENT"
            assert n["status"] == "NOT_ASSIGNED"
            assert n["zone_id"] is None
            assert n["vrf_score"] > 0.30

    # Test via FastAPI client
    client = TestClient(app)
    init_res = client.post("/api/v1/init", json={"benchmark": "Non-IID 10-Class Storyboard"})
    assert init_res.status_code == 200
    session_id = init_res.json()["session_id"]

    step2_res = client.post("/api/v1/step/vrf", json={"session_id": session_id})
    assert step2_res.status_code == 200
    step2_data = step2_res.json()
    assert sorted(step2_data["initiators"]) == expected_leaders
    assert len(step2_data["logs"]) > 0


def test_storyboard_step2_local_vrf_compute():
    """Verify Step 2 Pure Local VRF Computation:

    1. Each node evaluates sigma_p in [0, 1).
    2. All nodes remain strictly in role='CLIENT' and status='NOT_ASSIGNED'.
    3. Node coordinates and adjacency are fully preserved.
    4. FastAPI /api/v1/step/vrf-compute endpoint succeeds and populates vrf_score for all 50 nodes.
    """
    engine = SemanticDFLEngine(seed=42)
    step1 = engine.generate_storyboard_step1()
    nodes = step1["nodes"]

    # Initial Step 1 state
    assert all(n["vrf_score"] is None for n in nodes)
    assert all(n["role"] == "CLIENT" for n in nodes)
    assert all(n["status"] == "NOT_ASSIGNED" for n in nodes)

    # Save original coordinates
    original_coords = {n["id"]: (n["coords"]["x"], n["coords"]["y"]) for n in nodes}

    # Execute Step 2 Local Computation
    compute_res = engine.compute_local_vrf(nodes=nodes)
    computed_nodes = compute_res["nodes"]

    # Assertion 1: All 50 nodes have valid VRF score in [0, 1)
    for n in computed_nodes:
        assert n["vrf_score"] is not None
        assert isinstance(n["vrf_score"], float)
        assert 0.0 <= n["vrf_score"] < 1.0

        # Assertion 2: Strict pure Step 2 scope - no leaders, all CLIENTs
        assert n["role"] == "CLIENT"
        assert n["status"] == "NOT_ASSIGNED"
        assert n["zone_id"] is None

        # Assertion 3: Coordinates preserved
        nid = n["id"]
        assert (n["coords"]["x"], n["coords"]["y"]) == original_coords[nid]

    assert len(compute_res["logs"]) == 51  # 50 individual + 1 summary

    # Assertion 4: Test FastAPI endpoint /api/v1/step/vrf-compute
    client = TestClient(app)
    init_res = client.post("/api/v1/init", json={"benchmark": "Non-IID 10-Class Storyboard"})
    assert init_res.status_code == 200
    session_id = init_res.json()["session_id"]

    res = client.post("/api/v1/step/vrf-compute", json={"session_id": session_id})
    assert res.status_code == 200
    res_data = res.json()
    assert len(res_data["nodes"]) == 50
    assert all(n["vrf_score"] is not None for n in res_data["nodes"])
    assert all(n["role"] == "CLIENT" for n in res_data["nodes"])
    assert all(n["status"] == "NOT_ASSIGNED" for n in res_data["nodes"])


