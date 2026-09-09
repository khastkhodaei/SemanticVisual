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


@pytest.mark.skip(reason="Legacy 50-node storyboard replaced by 10-node CIFAR-10 specification")
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


@pytest.mark.skip(reason="Legacy 50-node storyboard replaced by 10-node CIFAR-10 specification")
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


@pytest.mark.skip(reason="Legacy 50-node storyboard replaced by 10-node CIFAR-10 specification")
def test_storyboard_step3_vrf_exchange():
    """Verify Step 3: Algorithm 2 (SELECTINITIATORS) with R = 3 hops.

    Requirements:
    1. Spatial dispersion: all nodes maintain min pairwise distance >= 65px (no clumping).
    2. BFS explicitly explores up to distance 3 (hop 1, hop 2, and hop 3).
    3. Election condition: node p is elected INITIATOR iff its (sigma_p, p) is the strict minimum
       within its 3-hop neighborhood N_3(p).
    4. R=3 spatial dispersion: all elected initiators have pairwise hop distance strictly > 3.
    5. FastAPI /api/v1/step/vrf-exchange endpoint succeeds with default r_hops=3.
    """
    engine = SemanticDFLEngine(seed=42)
    step1 = engine.generate_storyboard_step1()
    nodes = step1["nodes"]
    adj = step1["adjacency_list"]

    # Assertion 1: Dispersed layout with min distance >= 65px
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            xi, yi = nodes[i]["coords"]["x"], nodes[i]["coords"]["y"]
            xj, yj = nodes[j]["coords"]["x"], nodes[j]["coords"]["y"]
            dist = np.hypot(xi - xj, yi - yj)
            assert dist >= 64.9, f"Nodes C{nodes[i]['id']} and C{nodes[j]['id']} are too close ({dist:.2f}px < 65px)"

    # Compute local VRF first (Step 2)
    engine.compute_local_vrf(nodes=nodes)

    # Execute Step 3: VRF Exchange with R=3
    exchange_res = engine.run_vrf_exchange(nodes=nodes, adjacency_list=adj, r_hops=3)
    initiators = exchange_res["initiators"]

    assert len(initiators) >= 1, "At least one initiator must be elected"

    # Assertion 2: BFS explicitly explores up to distance 3
    for n in nodes:
        assert "neighborhood_scores" in n
        hops_present = set(item["hop"] for item in n["neighborhood_scores"])
        assert 1 in hops_present, f"Node {n['id']} missing hop 1 neighbors"
        assert 2 in hops_present, f"Node {n['id']} missing hop 2 neighbors"
        assert 3 in hops_present, f"Node {n['id']} missing hop 3 neighbors"

        # Verification of min_score and min_peer_id in 3-hop ball
        min_items = [item for item in n["neighborhood_scores"] if item["is_min"]]
        assert len(min_items) == 1
        expected_min_tuple = min((item["score"], item["id"]) for item in n["neighborhood_scores"])
        assert (min_items[0]["score"], min_items[0]["id"]) == expected_min_tuple

        if n["id"] in initiators:
            assert n["role"] == "INITIATOR"
            assert n["status"] == "ASSIGNED"
            assert min_items[0]["id"] == n["id"]
        else:
            assert n["role"] == "CLIENT"
            assert n["status"] == "NOT_ASSIGNED"

    # Assertion 3: R=3 spatial dispersion between all pairs of elected initiators (pairwise hop distance > 3)
    for i in range(len(initiators)):
        la = initiators[i]
        r3_nbrs = set(engine.get_r_hop_neighborhood(la, adj, r_hops=3))
        for j in range(i + 1, len(initiators)):
            lb = initiators[j]
            assert lb not in r3_nbrs, f"R=3 dispersion violation: Initiator C{la} and Initiator C{lb} within 3 hops!"

    # Assertion 4: Test FastAPI endpoint /api/v1/step/vrf-exchange
    client = TestClient(app)
    init_res = client.post("/api/v1/init", json={"benchmark": "Non-IID 10-Class Storyboard"})
    assert init_res.status_code == 200
    session_id = init_res.json()["session_id"]

    # Run Step 2
    step2_res = client.post("/api/v1/step/vrf-compute", json={"session_id": session_id})
    assert step2_res.status_code == 200

    # Run Step 3 (default r_hops=3)
    step3_res = client.post("/api/v1/step/vrf-exchange", json={"session_id": session_id})
    assert step3_res.status_code == 200
    step3_data = step3_res.json()
    assert step3_data["initiators"] == initiators
    assert all("neighborhood_scores" in n for n in step3_data["nodes"])
    assert any("[VRF WINNER]" in log["message"] for log in step3_data["logs"])


@pytest.mark.skip(reason="Legacy 50-node storyboard replaced by 10-node CIFAR-10 specification")
def test_storyboard_step4_zone_probing():
    """Verify Step 4 TTL=3 Zone Formation (Algorithm 3 from ACM 2026 paper).

    Assertions:
    1. Multi-hop wave simulation assigns all connected nodes a valid zone_id.
    2. Strict zone cardinality cap (|Z_I| <= S_Z = 8) is enforced.
    3. Boundary edges are cleanly identified between differing zones (zone_a != zone_b).
    4. FastAPI endpoint /api/v1/step/zone-probing executes deterministically.
    """
    engine = SemanticDFLEngine(seed=10)
    topo = engine.generate_storyboard_step1()
    nodes = topo["nodes"]
    adj = topo["adjacency_list"]

    # Compute VRF and run Step 3 VRF exchange
    engine.compute_local_vrf(nodes=nodes)
    step3_res = engine.run_vrf_exchange(nodes=nodes, adjacency_list=adj, r_hops=3)
    initiators = step3_res["initiators"]
    assert len(initiators) >= 1

    # Execute Step 4 Zone Probing with TTL=3, S_Z=8
    ttl = 3
    sz_cap = 8
    probing_res = engine.run_zone_probing(nodes=nodes, adjacency_list=adj, ttl=ttl, max_zone_size=sz_cap)

    updated_nodes = probing_res["nodes"]
    zones = probing_res["zones"]
    boundary_edges = probing_res["boundary_edges"]
    wave_events = probing_res["packet_wave_events"]

    # 1. Verify every connected node has valid zone_id and ASSIGNED status
    assert len(updated_nodes) == 50
    for node in updated_nodes:
        assert node["status"] == "ASSIGNED"
        assert node["state"] == "ASSIGNED"
        assert node["zone_id"] is not None
        assert isinstance(node["zone_id"], int)
        assert node["zone_id"] in zones
        assert node["hop_distance"] is not None
        assert node["parent_probe_sender"] is not None
        assert isinstance(node["is_boundary"], bool)

    # Total members across all zones equals total peers (50)
    total_members = sum(len(mems) for mems in zones.values())
    assert total_members == 50

    # 2. Strict Zone Cardinality Cap: |Z_I| <= S_Z = 8
    for zid, members in zones.items():
        assert len(members) <= sz_cap, (
            f"Cardinality violation: Zone {zid} has {len(members)} nodes, exceeding S_Z={sz_cap}"
        )

    # 3. Boundary Edges cleanly identified between differing zones
    assert len(boundary_edges) > 0
    node_map = {n["id"]: n for n in updated_nodes}
    for edge in boundary_edges:
        assert "source" in edge
        assert "target" in edge
        assert "zone_a" in edge
        assert "zone_b" in edge
        assert edge["zone_a"] != edge["zone_b"], f"Boundary edge within same zone: {edge}"
        assert edge["zone_a"] == node_map[edge["source"]]["zone_id"] or edge["zone_a"] == node_map[edge["target"]]["zone_id"]
        assert edge["zone_b"] == node_map[edge["source"]]["zone_id"] or edge["zone_b"] == node_map[edge["target"]]["zone_id"]

    # Boundary incident nodes must have is_boundary == True
    b_nodes = set()
    for edge in boundary_edges:
        b_nodes.add(edge["source"])
        b_nodes.add(edge["target"])
    for node in updated_nodes:
        if node["id"] in b_nodes:
            assert node["is_boundary"] is True
            assert len(node["boundary_neighbors"]) > 0

    # 4. Multi-hop wave events recorded
    assert len(wave_events) > 0
    wave_nums = set(ev["wave"] for ev in wave_events)
    assert 1 in wave_nums
    assert 2 in wave_nums
    assert 3 in wave_nums

    # 5. FastAPI endpoint /api/v1/step/zone-probing
    client = TestClient(app)
    init_res = client.post("/api/v1/init", json={"benchmark": "Non-IID 10-Class Storyboard"})
    assert init_res.status_code == 200
    session_id = init_res.json()["session_id"]

    client.post("/api/v1/step/vrf-compute", json={"session_id": session_id})
    client.post("/api/v1/step/vrf-exchange", json={"session_id": session_id, "r_hops": 3})

    step4_res = client.post("/api/v1/step/zone-probing", json={"session_id": session_id, "ttl": 3, "max_zone_size": 8})
    assert step4_res.status_code == 200
    step4_data = step4_res.json()

    assert "zones" in step4_data
    assert "boundary_edges" in step4_data
    assert "packet_wave_events" in step4_data
    assert all(len(m) <= 8 for m in step4_data["zones"].values())
    assert all(n["status"] == "ASSIGNED" for n in step4_data["nodes"])
    assert any("[ZONE FORMATION]" in l["message"] for l in step4_data["logs"])




