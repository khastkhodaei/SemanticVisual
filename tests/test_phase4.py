"""Automated Test Suite for Phase 4 (Final Phase) of SemanticDFL Protocol Simulator.

Verifies:
1. Personalized FL Training Engine: Parameter updates and comparative convergence trends.
2. Dynamic Churn Resilience: Super-Peer failure and instant replica failover takeover.
3. Web UI Delivery & API Endpoints: HTML static delivery, Cytoscape/Chart/KaTeX tags,
   and POST /api/v1/fl/step and /api/v1/fl/churn endpoint validation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.engine import SemanticDFLEngine
from backend.main import app


def test_personalized_fl_step():
    """Verify that simulate_fl_round executes local drift, anchor mixing,

    and generates valid comparative accuracy metrics across rounds.
    """
    engine = SemanticDFLEngine(seed=404)
    N = 18
    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]

    # Record initial weights for comparison
    initial_weights = [list(n["weights"]) for n in nodes]

    # Execute Round 1
    res_r1 = engine.simulate_fl_round(
        nodes=nodes,
        round_num=1,
        k_pull=3,
        kappa=0.5,
        alpha=0.6,
    )

    metrics_r1 = res_r1["metrics"]
    assert res_r1["round"] == 1
    assert res_r1["active_clients"] == N
    assert "acc_semantic" in metrics_r1
    assert "acc_fedavg" in metrics_r1
    assert "acc_solo" in metrics_r1

    # Verify that weights updated (non-identical to initial)
    weights_changed = any(
        nodes[i]["weights"] != initial_weights[i] for i in range(N)
    )
    assert weights_changed, "Model parameters should update after FL step"

    # Execute Round 5 and check progression
    res_r5 = engine.simulate_fl_round(
        nodes=nodes,
        round_num=5,
        k_pull=3,
        kappa=0.5,
        alpha=0.6,
    )
    metrics_r5 = res_r5["metrics"]

    # Comparative trends: SemanticDFL > FedAvg >= Solo
    assert metrics_r5["acc_semantic"] > metrics_r5["acc_fedavg"], (
        f"SemanticDFL ({metrics_r5['acc_semantic']}) should outperform FedAvg ({metrics_r5['acc_fedavg']})"
    )
    assert metrics_r5["acc_fedavg"] >= metrics_r5["acc_solo"] - 0.05
    assert metrics_r5["acc_semantic"] >= metrics_r1["acc_semantic"] - 0.05, "Accuracy should improve or stabilize over rounds"


def test_superpeer_churn_and_replica_takeover():
    """Verify that when a SUPER_PEER fails, an eligible replica is instantly promoted

    to active SUPER_PEER and the takeover event is logged.
    """
    engine = SemanticDFLEngine(seed=505)
    N = 20
    topology = engine.generate_topology(N=N, D_limit=0.35)
    nodes = topology["nodes"]
    adj = topology["adjacency_list"]

    # Set up zones and clustering to elect Super-Peers and Replicas
    engine.run_vrf_election(nodes, adj, r_hops=2)
    zone_res = engine.run_zone_formation(nodes, adj, r_hops=2, max_zone_size=8)
    engine.extract_compact_signatures(nodes, global_p=15)

    c_res = engine.cluster_intra_zone(nodes, global_p=15, replication_factor=2)
    clusters = c_res["clusters"]
    assert len(clusters) > 0, "Clusters must be generated"

    # Find an active SUPER_PEER with a replica set
    target_cluster = None
    for c in clusters:
        if len(c.get("replica_set", [])) >= 1 and c["replica_set"][0] != c["super_peer_id"]:
            target_cluster = c
            break

    if not target_cluster:
        target_cluster = clusters[0]

    sp_to_kill = target_cluster["super_peer_id"]
    sp_node = next(n for n in nodes if n["id"] == sp_to_kill)
    assert sp_node["role"] == "SUPER_PEER"

    # Execute FL round with churn injection
    fl_res = engine.simulate_fl_round(
        nodes=nodes,
        round_num=3,
        k_pull=3,
        kappa=0.5,
        alpha=0.6,
        churn_node_id=sp_to_kill,
        clusters=clusters,
    )

    # 1. Dead node should be deactivated
    assert sp_node["alive"] is False
    assert sp_node["role"] == "DEAD"

    # 2. Replica takeover verification
    takeover = fl_res["replica_takeover"]
    assert takeover is not None, "Replica takeover must be triggered on Super-Peer churn"
    assert takeover["failed_super_peer"] == sp_to_kill
    promoted_id = takeover["promoted_replica"]

    promoted_node = next(n for n in nodes if n["id"] == promoted_id)
    assert promoted_node["role"] == "SUPER_PEER"
    assert promoted_node["alive"] is True

    # 3. Log event verification
    logs = [log["message"] for log in fl_res["logs"]]
    assert any("[REPLICA TAKEOVER]" in msg for msg in logs), "Takeover event must be explicitly logged"


def test_ui_delivery_and_endpoints():
    """Verify frontend HTML delivery with required CDN script tags

    and test POST /api/v1/fl/step and /api/v1/fl/churn endpoints.
    """
    client = TestClient(app)

    # 1. Verify GET / serves HTML containing required CDN scripts
    get_resp = client.get("/")
    assert get_resp.status_code == 200
    html = get_resp.text
    assert "cytoscape" in html.lower(), "HTML must contain Cytoscape.js script tag"
    assert "chart.js" in html.lower(), "HTML must contain Chart.js script tag"
    assert "katex" in html.lower(), "HTML must contain KaTeX script/stylesheet"
    assert "tailwind" in html.lower(), "HTML must contain Tailwind CSS script"

    # 2. Initialize simulation session
    init_resp = client.post("/api/v1/init", json={"num_nodes": 16, "d_limit": 0.35, "r_hops": 2, "max_zone_size": 6, "theta": 0.70, "q": 0.20})
    assert init_resp.status_code == 200
    session_id = init_resp.json()["session_id"]

    # 3. Run FL step endpoint
    fl_step_resp = client.post("/api/v1/fl/step", json={"session_id": session_id, "k_pull": 2, "kappa": 0.5, "alpha": 0.6})
    assert fl_step_resp.status_code == 200
    fl_data = fl_step_resp.json()
    assert "metrics" in fl_data
    assert fl_data["round"] == 1
    assert "acc_semantic" in fl_data["metrics"]
    assert "history" in fl_data
    assert len(fl_data["history"]) == 1

    # 4. Run FL churn endpoint
    churn_resp = client.post("/api/v1/fl/churn", json={"session_id": session_id, "node_id": 2, "k_pull": 2, "kappa": 0.5, "alpha": 0.6})
    assert churn_resp.status_code == 200
    churn_data = churn_resp.json()
    assert churn_data["round"] == 2
    assert churn_data["churn_node_id"] == 2
    assert len(churn_data["history"]) == 2
    # Node 2 should be marked dead
    node_2 = next(n for n in churn_data["nodes"] if n["id"] == 2)
    assert node_2["alive"] is False
