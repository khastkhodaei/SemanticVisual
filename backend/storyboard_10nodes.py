"""10-Node CIFAR-10 SemanticDFL Storyboard Configuration & Topology.

Implements Step 1 of the new 10-node CIFAR-10 SemanticDFL Storyboard:
- 10 nodes (C1 to C10)
- Exact symmetric undirected physical adjacency list
- CIFAR-10 classes C1 to C10 with emoji icons
- Local data distribution percentages (summing to 100% per node)
- Initial state: role='CLIENT', status='NOT_ASSIGNED', zone_id=None
"""

from typing import Any, Dict, List, Optional, Tuple

CIFAR10_CLASSES: Dict[int, Dict[str, Any]] = {
    1: {"class_id": 1, "code": "C1", "name": "Airplane", "english_name": "Airplane", "icon": "✈️"},
    2: {"class_id": 2, "code": "C2", "name": "Automobile", "english_name": "Automobile", "icon": "🚗"},
    3: {"class_id": 3, "code": "C3", "name": "Bird", "english_name": "Bird", "icon": "🐦"},
    4: {"class_id": 4, "code": "C4", "name": "Cat", "english_name": "Cat", "icon": "🐱"},
    5: {"class_id": 5, "code": "C5", "name": "Deer", "english_name": "Deer", "icon": "🦌"},
    6: {"class_id": 6, "code": "C6", "name": "Dog", "english_name": "Dog", "icon": "🐶"},
    7: {"class_id": 7, "code": "C7", "name": "Frog", "english_name": "Frog", "icon": "🐸"},
    8: {"class_id": 8, "code": "C8", "name": "Horse", "english_name": "Horse", "icon": "🐴"},
    9: {"class_id": 9, "code": "C9", "name": "Ship", "english_name": "Ship", "icon": "🚢"},
    10: {"class_id": 10, "code": "C10", "name": "Truck", "english_name": "Truck", "icon": "🚚"},
}

# Exact undirected physical edges per prompt and simulate_steps.MD:
STORYBOARD_10_ADJACENCY: Dict[int, List[int]] = {
    1: [2, 4],
    2: [1, 3],
    3: [2, 5, 6, 7],
    4: [1, 5, 6, 7],
    5: [3, 4, 6, 10],
    6: [3, 4, 5, 8, 9],
    7: [3, 4, 9],
    8: [6, 9, 10],
    9: [6, 7, 8, 10],
    10: [5, 8, 9],
}

# Data Distribution percentage dictionary per node (exact from prompt & simulate_steps.MD):
STORYBOARD_10_DISTRIBUTION: Dict[int, Dict[str, int]] = {
    1: {"C1": 46, "C2": 17, "C3": 37},
    2: {"C1": 19, "C2": 24, "C3": 57},
    3: {"C4": 34, "C5": 20, "C6": 46},
    4: {"C4": 62, "C5": 21, "C6": 17},
    5: {"C4": 53, "C5": 12, "C6": 35},
    6: {"C7": 23, "C8": 19, "C9": 34, "C10": 24},
    7: {"C7": 11, "C8": 41, "C9": 21, "C10": 27},
    8: {"C4": 32, "C5": 38, "C6": 30},
    9: {"C1": 45, "C2": 32, "C3": 23},
    10: {"C7": 12, "C8": 43, "C9": 33, "C10": 12},
}

# Normalized 10-dimensional vectors from simulate_steps.MD (Step 2)
STORYBOARD_10_VECTORS: Dict[int, List[float]] = {
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

# Balanced, readable planar 2D coordinates from scenario_data.json
STORYBOARD_10_COORDINATES: Dict[int, Tuple[float, float]] = {
    1: (130.0, 140.0),
    2: (130.0, 380.0),
    3: (310.0, 380.0),
    4: (310.0, 140.0),
    5: (480.0, 420.0),
    6: (480.0, 240.0),
    7: (480.0, 90.0),
    8: (700.0, 380.0),
    9: (700.0, 140.0),
    10: (840.0, 380.0),
}

# Deterministic local VRF scores for Step 3 (seed_{e-1})
STORYBOARD_10_VRF_SCORES: Dict[int, float] = {
    1: 0.1543,
    2: 0.0837,
    3: 0.2318,
    4: 0.0412,
    5: 0.3185,
    6: 0.4721,
    7: 0.3564,
    8: 0.0275,
    9: 0.2947,
    10: 0.4126,
}



def get_dominant_class(distribution: Dict[str, int]) -> Dict[str, Any]:
    """Identify the dominant class (highest percentage share) in a node's distribution."""
    best_key = max(distribution, key=lambda k: distribution[k])
    class_id = int(best_key.replace("C", ""))
    return CIFAR10_CLASSES[class_id]


def get_10node_edges() -> List[Dict[str, Any]]:
    """Build unique undirected physical edges from the symmetric adjacency list."""
    edges = []
    seen = set()
    for u in sorted(STORYBOARD_10_ADJACENCY.keys()):
        for v in sorted(STORYBOARD_10_ADJACENCY[u]):
            edge_key = (min(u, v), max(u, v))
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append({
                    "id": f"e{edge_key[0]}_{edge_key[1]}",
                    "source": f"C{edge_key[0]}",
                    "target": f"C{edge_key[1]}",
                    "source_num": edge_key[0],
                    "target_num": edge_key[1],
                })
    return edges


def get_10node_nodes() -> List[Dict[str, Any]]:
    """Build all 10 nodes with initial states, dominant class labels, and local data distributions."""
    nodes = []
    for nid in range(1, 11):
        dist = STORYBOARD_10_DISTRIBUTION[nid]
        dom = get_dominant_class(dist)
        nbrs = sorted(STORYBOARD_10_ADJACENCY[nid])
        coord = STORYBOARD_10_COORDINATES[nid]

        vec_10d = list(STORYBOARD_10_VECTORS[nid])
        assigned_classes = [i for i, val in enumerate(vec_10d) if val > 0.0]
        class_distribution_0idx = {
            int(k.replace("C", "")) - 1: v for k, v in dist.items()
        }

        nodes.append({
            "id": nid,
            "node_id": f"C{nid}",
            "role": "CLIENT",
            "status": "NOT_ASSIGNED",
            "zone_id": None,
            "is_initiator": False,
            "is_boundary": False,
            "vrf_score": None,
            "neighbors": nbrs,
            "neighbors_str": [f"C{nb}" for nb in nbrs],
            "degree": len(nbrs),
            "dominant_class": dom["code"],
            "dominant_class_id": dom["class_id"],
            "dominant_class_name": dom["name"],
            "dominant_class_icon": dom["icon"],
            "assigned_classes": assigned_classes,
            "class_distribution": class_distribution_0idx,
            "vector_10d": vec_10d,
            "class_id": dom["class_id"],
            "class_title": dom["name"],
            "class_icon": dom["icon"],
            "data_distribution": dist,
            "distribution": dist,
            "vector": vec_10d,
            "normalized_vector": vec_10d,
            "weights": vec_10d,
            "x": coord[0],
            "y": coord[1],
            "coords": {"x": coord[0], "y": coord[1]},
            "label": f"C{nid}",
        })
    return nodes


def get_10node_config() -> Dict[str, Any]:
    """Global configuration summary for 10-node CIFAR-10 setup."""
    nodes = get_10node_nodes()
    edges = get_10node_edges()

    class_holding_counts = {idx: 0 for idx in range(10)}
    class_holding_clients = {idx: [] for idx in range(10)}
    for n in nodes:
        for cidx in n["assigned_classes"]:
            class_holding_counts[cidx] += 1
            class_holding_clients[cidx].append(f"C{n['id']}")

    classes_list = []
    for idx in range(10):
        cid = idx + 1
        cinfo = CIFAR10_CLASSES[cid]
        classes_list.append({
            "class_id": idx,
            "class_num": cid,
            "name": cinfo["name"],
            "english_name": cinfo["english_name"],
            "icon": cinfo["icon"],
            "code": cinfo["code"],
            "count": class_holding_counts[idx],
            "clients": class_holding_clients[idx],
        })

    return {
        "num_nodes": 10,
        "avg_degree": round(sum(n["degree"] for n in nodes) / len(nodes), 2),  # 3.4
        "total_edges": 18,
        "unique_edges": len(edges),
        "num_classes": 10,
        "classes": classes_list,
    }


def get_10node_step_data(step_number: int) -> Dict[str, Any]:
    """Retrieve storyboard step data for 10-node simulation."""
    nodes = get_10node_nodes()
    edges = get_10node_edges()

    if step_number == 1:
        return {
            "step": 1,
            "title": "Step 1: 10-Node CIFAR-10 Physical Ad-Hoc Topology",
            "phase_badge": "Step 1: Network Creation",
            "description": "Ad-hoc physical mesh of 10 edge clients initialized with Non-IID CIFAR-10 data distributions. Status: NOT_ASSIGNED, Role: CLIENT, Zone: null.",
            "nodes": nodes,
            "edges": edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [],
            "terminal_logs": [
                "[Topology] Initialized 10-node CIFAR-10 ad-hoc network.",
                "[Topology] Configured 18 physical links (17 unique undirected edges) with symmetric adjacency.",
                "[Dataset] Loaded CIFAR-10 percentage distributions (sum=100% per node).",
                "[State] All 10 nodes initialized with role='CLIENT', status='NOT_ASSIGNED', zone_id=null."
            ]
        }
    elif step_number == 2:
        # Step 2: Local Training and Normalized 10D Vector Generation
        step2_nodes = []
        for n in nodes:
            n_copy = dict(n)
            n_copy["status"] = "LOCAL_TRAINED"
            n_copy["vector"] = STORYBOARD_10_VECTORS[n["id"]]
            n_copy["normalized_vector"] = STORYBOARD_10_VECTORS[n["id"]]
            n_copy["weights"] = STORYBOARD_10_VECTORS[n["id"]]
            n_copy["vector_10d"] = STORYBOARD_10_VECTORS[n["id"]]
            step2_nodes.append(n_copy)

        terminal_logs = [
            f"[LOCAL TRAINING] Node C{n['id']} completed local training. Generated 10D class representation vector."
            for n in step2_nodes
        ]

        return {
            "step": 2,
            "title": "Step 2: Local Training & Normalized 10D Vector Generation",
            "phase_badge": "Step 2: Local Vectors",
            "description": "Each client trains on local CIFAR-10 data, outputting a normalized 10-dimensional vector representing class proportions.",
            "formula": "\\mathbf{w}_i = [C_1, C_2, \\dots, C_{10}], \\quad \\sum_{c=1}^{10} w_{i, c} = 1.0",
            "formula_desc": "Each client maps local trained parameter distribution to a 10-dimensional normalized vector representing class proportions.",
            "nodes": step2_nodes,
            "edges": edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [],
            "terminal_logs": terminal_logs,
        }
    elif step_number == 3:
        # Step 3: Local VRF Score Calculation (No score transmission, retains Step 2 node info)
        step3_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            vrf = STORYBOARD_10_VRF_SCORES[nid]

            # Retain Step 2 vector information
            n_copy["vector"] = STORYBOARD_10_VECTORS[nid]
            n_copy["vector_10d"] = STORYBOARD_10_VECTORS[nid]
            n_copy["normalized_vector"] = STORYBOARD_10_VECTORS[nid]
            n_copy["weights"] = STORYBOARD_10_VECTORS[nid]

            n_copy["status"] = "VRF_COMPUTED"
            n_copy["role"] = "CLIENT"
            n_copy["is_initiator"] = False
            n_copy["zone_id"] = None
            n_copy["is_boundary"] = False
            n_copy["vrf_score"] = vrf
            # In Step 3, scores are not received from neighbors
            n_copy["neighbor_scores"] = {}
            n_copy["neighbor_scores_str"] = {}
            n_copy["neighbor_scoreboard"] = []
            step3_nodes.append(n_copy)

        terminal_logs = [
            f"[VRF GENERATION] Node C{nid} computed local VRF seed score: {STORYBOARD_10_VRF_SCORES[nid]}"
            for nid in range(1, 11)
        ]
        terminal_logs.append("[STATUS] All 10 nodes completed local VRF score calculation. Scores remain local.")

        return {
            "step": 3,
            "title": "Step 3: Local VRF Score Calculation",
            "phase_badge": "Step 3: Local VRF",
            "description": "Each peer independently calculates its local VRF score σ_p = VRF(seed_{e-1}) using its private key. Scores are not transmitted to neighbors in this step.",
            "formula": "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1})",
            "formula_desc": "Each peer calculates its local VRF score from the previous epoch seed. Scores remain local.",
            "nodes": step3_nodes,
            "edges": edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [],
            "packet_exchanges": [],
            "terminal_logs": terminal_logs,
        }
    elif step_number == 4:
        # Step 4: 1-Hop Neighbor Score Exchange, VRF Comparison & Initiator Election
        step4_nodes = []
        initiators = [2, 4, 8]

        # 36 mutual 1-hop score packet transmission events along the 18 physical links
        packet_exchanges = []
        for e in edges:
            u = e["source_num"]
            v = e["target_num"]
            packet_exchanges.append({
                "from": u,
                "to": v,
                "from_label": f"C{u}",
                "to_label": f"C{v}",
                "type": "VRF_SCORE",
                "score": STORYBOARD_10_VRF_SCORES[u],
                "msg": f"C{u} sends VRF score {STORYBOARD_10_VRF_SCORES[u]} to 1-hop neighbor C{v}",
            })
            packet_exchanges.append({
                "from": v,
                "to": u,
                "from_label": f"C{v}",
                "to_label": f"C{u}",
                "type": "VRF_SCORE",
                "score": STORYBOARD_10_VRF_SCORES[v],
                "msg": f"C{v} sends VRF score {STORYBOARD_10_VRF_SCORES[v]} to 1-hop neighbor C{u}",
            })

        # Evaluation details for each node (closed 1-hop ball minimum)
        eval_details = {
            1: {"min_id": 4, "neighbors": [2, 4]},
            2: {"min_id": 2, "neighbors": [1, 3]},
            3: {"min_id": 2, "neighbors": [2, 5, 6, 7]},
            4: {"min_id": 4, "neighbors": [1, 5, 6, 7]},
            5: {"min_id": 4, "neighbors": [3, 4, 6, 10]},
            6: {"min_id": 8, "neighbors": [3, 4, 5, 8, 9]},
            7: {"min_id": 4, "neighbors": [3, 4, 9]},
            8: {"min_id": 8, "neighbors": [6, 9, 10]},
            9: {"min_id": 8, "neighbors": [6, 7, 8, 10]},
            10: {"min_id": 8, "neighbors": [5, 8, 9]},
        }

        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            self_score = STORYBOARD_10_VRF_SCORES[nid]
            winner_id = eval_details[nid]["min_id"]
            min_score = STORYBOARD_10_VRF_SCORES[winner_id]
            is_init = (nid in initiators)

            # Retain Step 2 vector information
            n_copy["vector"] = STORYBOARD_10_VECTORS[nid]
            n_copy["vector_10d"] = STORYBOARD_10_VECTORS[nid]
            n_copy["normalized_vector"] = STORYBOARD_10_VECTORS[nid]
            n_copy["weights"] = STORYBOARD_10_VECTORS[nid]

            n_copy["vrf_score"] = self_score
            n_copy["role"] = "INITIATOR" if is_init else "CLIENT"
            n_copy["is_initiator"] = is_init
            n_copy["status"] = "INITIATOR" if is_init else "CANDIDATE"
            n_copy["winner_id"] = winner_id
            n_copy["winner_label"] = f"C{winner_id}"
            n_copy["min_score"] = min_score
            n_copy["min_score_node"] = winner_id

            if is_init:
                n_copy["decision_banner"] = "🏆 Self-Elected Initiator (Holds minimum score in 1-hop ball)"
                if nid == 4:
                    n_copy["winner_color"] = "dark green"
                    n_copy["winner_bg"] = "#166534"
                    n_copy["winner_border"] = "#14532d"
                elif nid == 2:
                    n_copy["winner_color"] = "dark red"
                    n_copy["winner_bg"] = "#991b1b"
                    n_copy["winner_border"] = "#7f1d1d"
                elif nid == 8:
                    n_copy["winner_color"] = "dark yellow"
                    n_copy["winner_bg"] = "#a16207"
                    n_copy["winner_border"] = "#713f12"
            else:
                n_copy["decision_banner"] = f"Candidate Member (Minimum held by C{winner_id} with σ={min_score:.4f})"
                n_copy["winner_color"] = None
                n_copy["winner_bg"] = None
                n_copy["winner_border"] = None

            # Build neighbor scoreboard with winning minimum marked
            neighbor_scoreboard = []
            for nb_id in eval_details[nid]["neighbors"]:
                nb_score = STORYBOARD_10_VRF_SCORES[nb_id]
                neighbor_scoreboard.append({
                    "neighbor_id": nb_id,
                    "label": f"C{nb_id}",
                    "vrf_score": nb_score,
                    "is_min": (nb_id == winner_id),
                })
            n_copy["neighbor_scoreboard"] = neighbor_scoreboard
            n_copy["neighbor_scores"] = {item['neighbor_id']: item["vrf_score"] for item in neighbor_scoreboard}
            n_copy["neighbor_scores_str"] = {f"C{item['neighbor_id']}": item["vrf_score"] for item in neighbor_scoreboard}
            n_copy["self_is_min"] = is_init
            step4_nodes.append(n_copy)

        unique_undirected = sorted({(min(e['source_num'], e['target_num']), max(e['source_num'], e['target_num'])) for e in edges})
        terminal_logs = [
            f"[VRF EXCHANGE] Node C{u} <-> Node C{v} exchanged 1-hop VRF scores ({STORYBOARD_10_VRF_SCORES[u]} vs {STORYBOARD_10_VRF_SCORES[v]})"
            for u, v in unique_undirected
        ]
        terminal_logs.append("[EXCHANGE COMPLETE] 1-hop scoreboards populated across all direct physical neighbors.")
        terminal_logs.append("[ELECTION] Evaluating 1-hop neighborhood minimums: m_p = min_{q in N_1(p) U {p}} (sigma_q, id_q).")
        for nid in range(1, 11):
            s = STORYBOARD_10_VRF_SCORES[nid]
            nbr_str = ", ".join(f"C{q}: {STORYBOARD_10_VRF_SCORES[q]:.4f}" for q in eval_details[nid]["neighbors"])
            win = eval_details[nid]["min_id"]
            if nid in initiators:
                terminal_logs.append(
                    f"Node C{nid} ({s:.4f}): Neighbors [{nbr_str}]. Min is C{win}. (🏆 INITIATOR)"
                )
            else:
                terminal_logs.append(
                    f"Node C{nid} ({s:.4f}): Neighbors [{nbr_str}]. Min is C{win}. (Candidate)"
                )

        terminal_logs.append("[RESULT] Initiator Election Complete: Exactly Nodes C2, C4, and C8 elected as Initiators.")

        return {
            "step": 4,
            "title": "Step 4: 1-Hop Neighbor Score Exchange & Initiator Election",
            "phase_badge": "Step 4: Initiator Election",
            "description": "Clients exchange VRF scores with 1-hop neighbors and evaluate closed-ball minimums. Nodes 2, 4, and 8 hold the minimum score in their respective 1-hop balls and elect themselves as Initiators.",
            "formula": "m_p = \\min_{q \\in \\mathcal{N}_1(p) \\cup \\{p\\}} (\\sigma_q, id_q)",
            "formula_desc": "If (sigma_p, id_p) == m_p, node p elects itself as an Initiator. Otherwise, it remains a Candidate Member.",
            "nodes": step4_nodes,
            "edges": edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "packet_exchanges": packet_exchanges,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 5:
        # Step 5: Zone Creation via PROBE Message Flooding (TTL = 1)
        # Initiators (Nodes 2, 4, 8) broadcast a PROBE packet strictly to their 1-hop physical neighbors (TTL = 1)
        # Initiator 2 -> [1, 3]
        # Initiator 4 -> [1, 5, 6, 7]
        # Initiator 8 -> [6, 9, 10]
        initiators = [2, 4, 8]

        probe_targets = {
            2: [1, 3],
            4: [1, 5, 6, 7],
            8: [6, 9, 10],
        }

        # Simulated network latency and arrival timestamps per probe (First-Wins Arbitration)
        # Node 1: Initiator 2 arrives at t = 10.4 ms (Winner), Initiator 4 at t = 16.8 ms (Delayed)
        # Node 6: Initiator 4 arrives at t = 11.2 ms (Winner), Initiator 8 at t = 18.5 ms (Delayed)
        probe_latencies = {
            (2, 1): {"time_str": "t = 10.4 ms", "ms": 10.4, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (4, 1): {"time_str": "t = 16.8 ms", "ms": 16.8, "winner": False, "notice": "✕ Delayed / Will be dropped"},
            (2, 3): {"time_str": "t = 9.8 ms", "ms": 9.8, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (4, 5): {"time_str": "t = 12.1 ms", "ms": 12.1, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (4, 6): {"time_str": "t = 11.2 ms", "ms": 11.2, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (8, 6): {"time_str": "t = 18.5 ms", "ms": 18.5, "winner": False, "notice": "✕ Delayed / Will be dropped"},
            (4, 7): {"time_str": "t = 13.5 ms", "ms": 13.5, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (8, 9): {"time_str": "t = 10.9 ms", "ms": 10.9, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
            (8, 10): {"time_str": "t = 14.2 ms", "ms": 14.2, "winner": True, "notice": "✓ FIRST-WINS WINNER"},
        }

        packet_events = []
        for init_id in sorted(probe_targets.keys()):
            for target_id in sorted(probe_targets[init_id]):
                z_color = "#059669" if init_id == 2 else ("#ea580c" if init_id == 4 else "#7c3aed")
                lat_info = probe_latencies.get(
                    (init_id, target_id),
                    {"time_str": "t = 12.0 ms", "ms": 12.0, "winner": True, "notice": "✓ FIRST-WINS WINNER"}
                )
                packet_events.append({
                    "packet_id": f"probe_{init_id}_{target_id}",
                    "initiator_id": init_id,
                    "source": f"C{init_id}",
                    "target": f"C{target_id}",
                    "source_num": init_id,
                    "target_num": target_id,
                    "ttl": 1,
                    "type": "PROBE",
                    "label": f"PROBE({init_id}, TTL=1)",
                    "zone": init_id,
                    "color": z_color,
                    "timestamp": lat_info["time_str"],
                    "latency_ms": lat_info["ms"],
                    "is_winner": lat_info["winner"],
                    "status": lat_info["notice"],
                })

        # Palettes:
        # Zone 2: Emerald Green (#059669)
        # Zone 4: Coral / Orange (#ea580c)
        # Zone 8: Violet / Purple (#7c3aed)
        zone_configs = {
            2: {"name": "Zone 2", "palette": "Emerald Green", "color": "#059669", "bg": "#d1fae5", "border": "#047857"},
            4: {"name": "Zone 4", "palette": "Coral/Orange", "color": "#ea580c", "bg": "#ffedd5", "border": "#c2410c"},
            8: {"name": "Zone 8", "palette": "Violet/Purple", "color": "#7c3aed", "bg": "#ede9fe", "border": "#6d28d9"},
        }

        step5_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            n_copy["vrf_score"] = STORYBOARD_10_VRF_SCORES[nid]
            n_copy["vector_10d"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["data_distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["neighbors"] = sorted(STORYBOARD_10_ADJACENCY[nid])
            n_copy["neighbors_str"] = [f"C{nb}" for nb in n_copy["neighbors"]]

            is_init = (nid in initiators)
            n_copy["is_initiator"] = is_init
            n_copy["role"] = "INITIATOR" if is_init else "CLIENT"

            # Determine received probes with network arrival timestamps and first-wins arbitration
            probes_rec = []
            for init_id, targets in probe_targets.items():
                if nid in targets:
                    lat_info = probe_latencies.get(
                        (init_id, nid),
                        {"time_str": "t = 12.0 ms", "ms": 12.0, "winner": True, "notice": "✓ FIRST-WINS WINNER"}
                    )
                    probes_rec.append({
                        "initiator_id": init_id,
                        "initiator_label": f"C{init_id}",
                        "ttl": 1,
                        "zone": init_id,
                        "zone_name": f"Zone {init_id}",
                        "timestamp": lat_info["time_str"],
                        "latency_ms": lat_info["ms"],
                        "winner": lat_info["winner"],
                        "is_winner": lat_info["winner"],
                        "status": lat_info["notice"],
                        "explanation": lat_info["notice"],
                    })
            probes_rec.sort(key=lambda p: p["latency_ms"])
            n_copy["zone_probes_received"] = probes_rec

            # Probes sent (for initiators)
            if is_init:
                n_copy["probes_sent"] = [
                    {"target_id": tgt, "target_label": f"C{tgt}", "ttl": 1}
                    for tgt in probe_targets[nid]
                ]
            else:
                n_copy["probes_sent"] = []

            # In Step 5: Prevent premature zone coloring on non-initiators.
            # All non-initiators remain solid neutral blue (#2563eb).
            # Only elected Initiators (Nodes 2, 4, 8) keep their distinct initiator colors.
            if nid == 1:
                n_copy["is_boundary"] = True
                n_copy["boundary_zones"] = [2, 4]
                n_copy["assigned_zone"] = 2
                n_copy["first_wins_zone"] = 2
                n_copy["first_wins_initiator"] = 2
                n_copy["first_wins_notice"] = "Per Algorithm 3 (First-Wins rule), this node will formally join Zone 2 in the next step."
                n_copy["zone_id"] = 2
                n_copy["zone_label"] = "Zone 2 / Zone 4 (Boundary)"
                n_copy["status"] = "CLIENT"
                n_copy["bg_color"] = "#2563eb"
                n_copy["border_color"] = "#1d4ed8"
                n_copy["border_width"] = 2.0
            elif nid == 6:
                n_copy["is_boundary"] = True
                n_copy["boundary_zones"] = [4, 8]
                n_copy["assigned_zone"] = 4
                n_copy["first_wins_zone"] = 4
                n_copy["first_wins_initiator"] = 4
                n_copy["first_wins_notice"] = "Per Algorithm 3 (First-Wins rule), this node will formally join Zone 4 in the next step."
                n_copy["zone_id"] = 4
                n_copy["zone_label"] = "Zone 4 / Zone 8 (Boundary)"
                n_copy["status"] = "CLIENT"
                n_copy["bg_color"] = "#2563eb"
                n_copy["border_color"] = "#1d4ed8"
                n_copy["border_width"] = 2.0
            elif nid == 2:
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 2
                n_copy["zone_id"] = 2
                n_copy["zone_label"] = "Zone 2 (Initiator)"
                n_copy["status"] = "INITIATOR"
                n_copy["bg_color"] = "#991b1b"
                n_copy["border_color"] = "#7f1d1d"
                n_copy["border_width"] = 4.5
                n_copy["winner_color"] = "dark red"
            elif nid == 3:
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 2
                n_copy["first_wins_zone"] = 2
                n_copy["first_wins_initiator"] = 2
                n_copy["first_wins_notice"] = "Per Algorithm 3 (First-Wins rule), this node will formally join Zone 2 in the next step."
                n_copy["zone_id"] = 2
                n_copy["zone_label"] = "Zone 2 (Pending Join)"
                n_copy["status"] = "CLIENT"
                n_copy["bg_color"] = "#2563eb"
                n_copy["border_color"] = "#1d4ed8"
                n_copy["border_width"] = 2.0
            elif nid == 4:
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 4
                n_copy["zone_id"] = 4
                n_copy["zone_label"] = "Zone 4 (Initiator)"
                n_copy["status"] = "INITIATOR"
                n_copy["bg_color"] = "#166534"
                n_copy["border_color"] = "#14532d"
                n_copy["border_width"] = 4.5
                n_copy["winner_color"] = "dark green"
            elif nid in (5, 7):
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 4
                n_copy["first_wins_zone"] = 4
                n_copy["first_wins_initiator"] = 4
                n_copy["first_wins_notice"] = "Per Algorithm 3 (First-Wins rule), this node will formally join Zone 4 in the next step."
                n_copy["zone_id"] = 4
                n_copy["zone_label"] = "Zone 4 (Pending Join)"
                n_copy["status"] = "CLIENT"
                n_copy["bg_color"] = "#2563eb"
                n_copy["border_color"] = "#1d4ed8"
                n_copy["border_width"] = 2.0
            elif nid == 8:
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 8
                n_copy["zone_id"] = 8
                n_copy["zone_label"] = "Zone 8 (Initiator)"
                n_copy["status"] = "INITIATOR"
                n_copy["bg_color"] = "#a16207"
                n_copy["border_color"] = "#713f12"
                n_copy["border_width"] = 4.5
                n_copy["winner_color"] = "dark yellow"
            else:  # nid in (9, 10)
                n_copy["is_boundary"] = False
                n_copy["boundary_zones"] = []
                n_copy["assigned_zone"] = 8
                n_copy["first_wins_zone"] = 8
                n_copy["first_wins_initiator"] = 8
                n_copy["first_wins_notice"] = "Per Algorithm 3 (First-Wins rule), this node will formally join Zone 8 in the next step."
                n_copy["zone_id"] = 8
                n_copy["zone_label"] = "Zone 8 (Pending Join)"
                n_copy["status"] = "CLIENT"
                n_copy["bg_color"] = "#2563eb"
                n_copy["border_color"] = "#1d4ed8"
                n_copy["border_width"] = 2.0

            n_copy["zone_color"] = zone_configs[n_copy["assigned_zone"]]["color"]
            n_copy["zone_name"] = zone_configs[n_copy["assigned_zone"]]["name"]

            step5_nodes.append(n_copy)

        step5_edges = []
        for e in edges:
            e_copy = dict(e)
            e_copy["is_inter_zone"] = False
            e_copy["is_boundary"] = False
            e_copy["is_boundary_edge"] = False
            e_copy["style"] = "solid"
            e_copy["line_color"] = "#64748b"
            step5_edges.append(e_copy)

        terminal_logs = [
            "[PROBE FLOODING] Initiators broadcast PROBE(TTL=1) to 1-hop physical neighbors.",
            "Initiator C2 (Zone 2 - Emerald Green) dispatches PROBE to: [C1, C3]",
            "Initiator C4 (Zone 4 - Coral/Orange) dispatches PROBE to: [C1, C5, C6, C7]",
            "Initiator C8 (Zone 8 - Violet/Purple) dispatches PROBE to: [C6, C9, C10]",
            "[PROBE ARRIVAL] C3 adopts Zone 2 from Initiator C2.",
            "[PROBE ARRIVAL] C5 and C7 adopt Zone 4 from Initiator C4.",
            "[PROBE ARRIVAL] C9 and C10 adopt Zone 8 from Initiator C8.",
            "[BOUNDARY OVERLAP] Node C1 received intersecting PROBE messages from Initiators C2 and C4 -> Marked Boundary Node (Zone 2 ∩ Zone 4).",
            "[BOUNDARY OVERLAP] Node C6 received intersecting PROBE messages from Initiators C4 and C8 -> Marked Boundary Node (Zone 4 ∩ Zone 8).",
            "[ZONE FORMATION] 3 Semantic Zones created via PROBE flooding (TTL=1). All 10 peers assigned.",
        ]

        return {
            "step": 5,
            "title": "Step 5: Zone Creation via PROBE Flooding (TTL = 1)",
            "phase_badge": "STEP 5: ZONE PROBE FLOODING (TTL=1)",
            "description": "Elected Initiators (Nodes 2, 4, and 8) dispatch a PROBE packet with TTL=1 to 1-hop neighbors, creating Zone 2 (Emerald Green), Zone 4 (Coral/Orange), and Zone 8 (Violet/Purple) with Boundary Nodes 1 and 6.",
            "formula": "\\text{PROBE}(p, \\text{TTL}=1), \\quad p \\in \\{2, 4, 8\\}",
            "formula_desc": "Elected Initiators broadcast a PROBE packet with TTL=1 to discover and claim their 1-hop physical neighbors.",
            "nodes": step5_nodes,
            "edges": step5_edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "packet_events": packet_events,
            "packet_exchanges": packet_events,
            "zones": {
                2: [1, 2, 3],
                4: [1, 4, 5, 6, 7],
                8: [6, 8, 9, 10],
            },
            "boundary_nodes": [1, 6],
            "terminal_logs": terminal_logs,
        }
    elif step_number == 6:
        # Step 6: Official Zone Formation & Inter-Zone Boundary Discovery (Algorithm 3, Lines 17-20)
        # Following First-Wins arrival from Step 5, clients officially adopt their winning initiator's zone identity.
        # Zone 2 (Leader: C2 👑): Members: Node 1, Node 3 (rendered in Zone 2 color with pastel tone)
        # Zone 4 (Leader: C4 👑): Members: Node 5, Node 6, Node 7 (rendered in Zone 4 color with pastel tone)
        # Zone 8 (Leader: C8 👑): Members: Node 9, Node 10 (rendered in Zone 8 color with pastel tone)

        initiators = [2, 4, 8]

        # Zone assignments:
        zone_members = {
            2: [1, 2, 3],
            4: [4, 5, 6, 7],
            8: [8, 9, 10],
        }

        node_to_zone = {}
        for zid, members in zone_members.items():
            for m in members:
                node_to_zone[m] = zid

        # Initiator neighbor discovery knowledge
        discovered_neighbor_zones = {
            2: ["C4"],
            4: ["C2", "C8"],
            8: ["C4"],
        }

        # Frontier dual boundary notifications (Algorithm 3, L17-L20)
        sent_boundary_notifications = {
            1: [
                {"target": "C2 (Own Initiator)", "introduced_neighbor": "C4"},
                {"target": "C4 (Competing Initiator)", "introduced_neighbor": "C2"},
            ],
            6: [
                {"target": "C4 (Own Initiator)", "introduced_neighbor": "C8"},
                {"target": "C8 (Competing Initiator)", "introduced_neighbor": "C4"},
            ],
        }

        # Reverse boundary announcement packet events
        packet_events = [
            {
                "packet_id": "boundary_1_to_2",
                "source": "C1",
                "target": "C2",
                "source_num": 1,
                "target_num": 2,
                "type": "NEIGHBOR_ALERT",
                "label": "NEIGHBOR(C4)",
                "color": "#10b981",
                "msg": "Node C1 notifies own Initiator C2 of adjacent Initiator C4",
                "introduced_neighbor": "C4",
                "target_role": "Own Initiator",
            },
            {
                "packet_id": "boundary_1_to_4",
                "source": "C1",
                "target": "C4",
                "source_num": 1,
                "target_num": 4,
                "type": "NEIGHBOR_ALERT",
                "label": "NEIGHBOR(C2)",
                "color": "#f97316",
                "msg": "Node C1 notifies competing Initiator C4 of adjacent Initiator C2",
                "introduced_neighbor": "C2",
                "target_role": "Competing Initiator",
            },
            {
                "packet_id": "boundary_6_to_4",
                "source": "C6",
                "target": "C4",
                "source_num": 6,
                "target_num": 4,
                "type": "NEIGHBOR_ALERT",
                "label": "NEIGHBOR(C8)",
                "color": "#f97316",
                "msg": "Node C6 notifies own Initiator C4 of adjacent Initiator C8",
                "introduced_neighbor": "C8",
                "target_role": "Own Initiator",
            },
            {
                "packet_id": "boundary_6_to_8",
                "source": "C6",
                "target": "C8",
                "source_num": 6,
                "target_num": 8,
                "type": "NEIGHBOR_ALERT",
                "label": "NEIGHBOR(C4)",
                "color": "#8b5cf6",
                "msg": "Node C6 notifies competing Initiator C8 of adjacent Initiator C4",
                "introduced_neighbor": "C4",
                "target_role": "Competing Initiator",
            },
        ]

        step6_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            zid = node_to_zone[nid]
            is_init = (nid in initiators)

            # Metadata preservation
            n_copy["vrf_score"] = STORYBOARD_10_VRF_SCORES[nid]
            n_copy["vector_10d"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["vector"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["normalized_vector"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["data_distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["neighbors"] = sorted(STORYBOARD_10_ADJACENCY[nid])
            n_copy["neighbors_str"] = [f"C{nb}" for nb in n_copy["neighbors"]]

            # Status & Roles:
            # Per requirement: "Assert all 10 nodes have status == 'ASSIGNED'"
            n_copy["status"] = "ASSIGNED"
            n_copy["role"] = "INITIATOR" if is_init else "CLIENT"
            n_copy["is_initiator"] = is_init
            n_copy["assigned_zone"] = zid
            n_copy["zone_id"] = zid
            n_copy["leader_id"] = zid

            # Boundary status
            is_frontier = (nid in (1, 6))
            n_copy["is_boundary"] = is_frontier
            n_copy["is_frontier"] = is_frontier
            if nid == 1:
                n_copy["boundary_zones"] = [2, 4]
                n_copy["zone_label"] = "Zone 2 (Frontier)"
            elif nid == 6:
                n_copy["boundary_zones"] = [4, 8]
                n_copy["zone_label"] = "Zone 4 (Frontier)"
            elif is_init:
                n_copy["boundary_zones"] = []
                n_copy["zone_label"] = f"Zone {zid} (Leader)"
            else:
                n_copy["boundary_zones"] = []
                n_copy["zone_label"] = f"Zone {zid} (Member)"

            # Boundary notifications payload
            if is_init:
                n_copy["discovered_neighbor_zones"] = list(discovered_neighbor_zones.get(nid, []))
                n_copy["sent_boundary_notifications"] = []
            elif is_frontier:
                n_copy["discovered_neighbor_zones"] = []
                n_copy["sent_boundary_notifications"] = list(sent_boundary_notifications.get(nid, []))
            else:
                n_copy["discovered_neighbor_zones"] = []
                n_copy["sent_boundary_notifications"] = []

            # Tonal color morphing:
            # Initiators maintain bold, deep zone color & crown badge (👑)
            # Members adopt softer pastel tone
            if is_init:
                if nid == 2:
                    n_copy["bg_color"] = "#059669"
                    n_copy["border_color"] = "#047857"
                elif nid == 4:
                    n_copy["bg_color"] = "#ea580c"
                    n_copy["border_color"] = "#c2410c"
                elif nid == 8:
                    n_copy["bg_color"] = "#7c3aed"
                    n_copy["border_color"] = "#6d28d9"
                n_copy["border_width"] = 4.5
                n_copy["color_tone"] = "deep"
            else:
                if zid == 2:
                    n_copy["bg_color"] = "#34d399"
                    n_copy["border_color"] = "#10b981"
                elif zid == 4:
                    n_copy["bg_color"] = "#fb923c"
                    n_copy["border_color"] = "#f97316"
                elif zid == 8:
                    n_copy["bg_color"] = "#a78bfa"
                    n_copy["border_color"] = "#8b5cf6"
                n_copy["border_width"] = 2.5
                n_copy["color_tone"] = "pastel"

            n_copy["color"] = n_copy["bg_color"]

            step6_nodes.append(n_copy)

        # Edges for Step 6:
        # Inter-zone links between frontier peers (Edge 1-4, Edge 6-8, etc.) styled as dashed boundary lines (#f87171)
        step6_edges = []
        for e in edges:
            e_copy = dict(e)
            u = e["source_num"]
            v = e["target_num"]
            z_u = node_to_zone[u]
            z_v = node_to_zone[v]
            is_cross_zone = (z_u != z_v)
            is_frontier_pair = (min(u, v) == 1 and max(u, v) == 4) or (min(u, v) == 6 and max(u, v) == 8)

            e_copy["is_inter_zone"] = is_cross_zone
            e_copy["is_boundary"] = is_cross_zone
            e_copy["is_boundary_edge"] = is_cross_zone
            e_copy["is_frontier_edge"] = is_frontier_pair
            e_copy["style"] = "solid"
            e_copy["line_color"] = "#64748b"
            e_copy["line_style"] = "solid"
            step6_edges.append(e_copy)

        terminal_logs = [
            "[ZONE FORMATION] All 10 nodes officially assigned (First-Wins adopted).",
            "Zone 2 (Leader: C2 👑): Members [C1, C3] morphed to Zone 2 Pastel Palette (#34d399).",
            "Zone 4 (Leader: C4 👑): Members [C5, C6, C7] morphed to Zone 4 Pastel Palette (#fb923c).",
            "Zone 8 (Leader: C8 👑): Members [C9, C10] morphed to Zone 8 Pastel Palette (#a78bfa).",
            "[BOUNDARY NOTIFICATIONS] Frontier peers dispatch dual announcements (Algorithm 3, L17-L20):",
            "[DISCOVERY NOTICE] Frontier C1 dispatched NEIGHBOR(C4) to Initiator C2.",
            "[DISCOVERY NOTICE] Frontier C1 dispatched NEIGHBOR(C2) to Initiator C4.",
            "[DISCOVERY NOTICE] Frontier C6 dispatched NEIGHBOR(C8) to Initiator C4.",
            "[DISCOVERY NOTICE] Frontier C6 dispatched NEIGHBOR(C4) to Initiator C8.",
            "[DISCOVERY COMPLETE] Initiator C2 discovered: [C4]. Initiator C4 discovered: [C2, C8]. Initiator C8 discovered: [C4].",
            "[STATUS] Inter-zone boundary overlay established. All 10 peers ready for semantic aggregation.",
        ]

        return {
            "step": 6,
            "title": "Step 6: Official Zone Formation & Inter-Zone Boundary Discovery",
            "phase_badge": "STEP 6: ZONE CREATION & BOUNDARY DISCOVERY",
            "description": "Following First-Wins arbitration, clients adopt their winning initiator's zone identity. Frontier peers dispatch dual boundary notifications so initiators learn adjacent zones.",
            "formula": "\\text{First-Wins} \\rightarrow \\text{ASSIGNED}(Z_I), \\quad \\text{NEIGHBOR}(p, q) \\rightarrow I_p \\text{ learns } I_q",
            "formula_desc": "Clients morph into their initiator's zone color. Frontier peers send dual notifications so initiators learn adjacent zones.",
            "nodes": step6_nodes,
            "edges": step6_edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "packet_events": packet_events,
            "packet_exchanges": packet_events,
            "zones": {
                2: [1, 2, 3],
                4: [4, 5, 6, 7],
                8: [8, 9, 10],
            },
            "boundary_nodes": [1, 6],
            "discovered_neighbor_zones": discovered_neighbor_zones,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 7:
        # Step 7: Initiator P_min Query Request
        # Elected Zone Initiators (C2, C4, C8) broadcast REQ_P_MIN strictly within their zones
        zone_members = {
            2: [1, 3],
            4: [5, 6, 7],
            8: [9, 10],
        }

        initiators = [2, 4, 8]
        node_to_zone = {
            1: 2, 2: 2, 3: 2,
            4: 4, 5: 4, 6: 4, 7: 4,
            8: 8, 9: 8, 10: 8,
        }

        discovered_neighbor_zones = {
            2: ["C4"],
            4: ["C2", "C8"],
            8: ["C4"],
        }

        # Packet dispatch events strictly within each zone
        packet_events = [
            # Zone 2: Initiator 2 -> [1, 3]
            {
                "packet_id": "pmin_2_to_1",
                "source": "C2",
                "target": "C1",
                "source_num": 2,
                "target_num": 1,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            {
                "packet_id": "pmin_2_to_3",
                "source": "C2",
                "target": "C3",
                "source_num": 2,
                "target_num": 3,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            # Zone 4: Initiator 4 -> [5, 6, 7]
            {
                "packet_id": "pmin_4_to_5",
                "source": "C4",
                "target": "C5",
                "source_num": 4,
                "target_num": 5,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            {
                "packet_id": "pmin_4_to_6",
                "source": "C4",
                "target": "C6",
                "source_num": 4,
                "target_num": 6,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            {
                "packet_id": "pmin_4_to_7",
                "source": "C4",
                "target": "C7",
                "source_num": 4,
                "target_num": 7,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            # Zone 8: Initiator 8 -> [9, 10]
            {
                "packet_id": "pmin_8_to_9",
                "source": "C8",
                "target": "C9",
                "source_num": 8,
                "target_num": 9,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
            {
                "packet_id": "pmin_8_to_10",
                "source": "C8",
                "target": "C10",
                "source_num": 8,
                "target_num": 10,
                "type": "REQ_P_MIN",
                "label": "REQ(τ=80%)",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"msg": "REQ_P_MIN", "tau": 0.80},
                "msg": "REQ_P_MIN",
                "tau": 0.80,
            },
        ]

        step7_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            zid = node_to_zone[nid]
            is_init = (nid in initiators)

            # Metadata preservation
            n_copy["vrf_score"] = STORYBOARD_10_VRF_SCORES[nid]
            n_copy["vector_10d"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["vector"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["normalized_vector"] = list(STORYBOARD_10_VECTORS[nid])
            n_copy["distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["data_distribution"] = dict(STORYBOARD_10_DISTRIBUTION[nid])
            n_copy["neighbors"] = sorted(STORYBOARD_10_ADJACENCY[nid])
            n_copy["neighbors_str"] = [f"C{nb}" for nb in n_copy["neighbors"]]

            # Status & Roles
            n_copy["status"] = "ASSIGNED"
            n_copy["role"] = "INITIATOR" if is_init else "CLIENT"
            n_copy["is_initiator"] = is_init
            n_copy["assigned_zone"] = zid
            n_copy["zone_id"] = zid
            n_copy["leader_id"] = zid

            # Boundary status preserved
            is_frontier = (nid in (1, 6))
            n_copy["is_boundary"] = is_frontier
            n_copy["is_frontier"] = is_frontier
            if nid == 1:
                n_copy["boundary_zones"] = [2, 4]
                n_copy["zone_label"] = "Zone 2 (Frontier)"
            elif nid == 6:
                n_copy["boundary_zones"] = [4, 8]
                n_copy["zone_label"] = "Zone 4 (Frontier)"
            elif is_init:
                n_copy["boundary_zones"] = []
                n_copy["zone_label"] = f"Zone {zid} (Leader)"
            else:
                n_copy["boundary_zones"] = []
                n_copy["zone_label"] = f"Zone {zid} (Member)"

            # Discovered neighbor zones preserved
            if is_init:
                n_copy["discovered_neighbor_zones"] = list(discovered_neighbor_zones.get(nid, []))
            else:
                n_copy["discovered_neighbor_zones"] = []

            # Step 7 specific state flags:
            if is_init:
                n_copy["pending_query"] = None
                n_copy["dispatched_query"] = "Broadcasted REQ_P_MIN (τ=0.80) to zone members"
                n_copy["active_query"] = "REQ_P_MIN (tau=0.80)"
                n_copy["target_members"] = zone_members[nid]
            else:
                n_copy["pending_query"] = "REQ_P_MIN (tau=0.80)"
                n_copy["query_from_initiator"] = zid
                n_copy["target_tau"] = 0.80

            # Tonal colors preserved
            if is_init:
                if nid == 2:
                    n_copy["bg_color"] = "#059669"
                    n_copy["border_color"] = "#047857"
                elif nid == 4:
                    n_copy["bg_color"] = "#ea580c"
                    n_copy["border_color"] = "#c2410c"
                elif nid == 8:
                    n_copy["bg_color"] = "#7c3aed"
                    n_copy["border_color"] = "#6d28d9"
                n_copy["border_width"] = 4.5
                n_copy["color_tone"] = "deep"
            else:
                if zid == 2:
                    n_copy["bg_color"] = "#34d399"
                    n_copy["border_color"] = "#10b981"
                elif zid == 4:
                    n_copy["bg_color"] = "#fb923c"
                    n_copy["border_color"] = "#f97316"
                elif zid == 8:
                    n_copy["bg_color"] = "#a78bfa"
                    n_copy["border_color"] = "#8b5cf6"
                n_copy["border_width"] = 2.5
                n_copy["color_tone"] = "pastel"

            n_copy["color"] = n_copy["bg_color"]
            step7_nodes.append(n_copy)

        # Edges for Step 7: All 18 physical links remain solid slate lines
        step7_edges = []
        for e in edges:
            e_copy = dict(e)
            u = e["source_num"]
            v = e["target_num"]
            z_u = node_to_zone[u]
            z_v = node_to_zone[v]
            is_cross_zone = (z_u != z_v)
            e_copy["is_inter_zone"] = is_cross_zone
            e_copy["is_boundary"] = is_cross_zone
            e_copy["is_boundary_edge"] = is_cross_zone
            e_copy["style"] = "solid"
            e_copy["line_color"] = "#64748b"
            e_copy["line_style"] = "solid"
            step7_edges.append(e_copy)

        terminal_logs = [
            "[STEP 7] Initiator P_min Query Request initialized (tau = 0.80).",
            "[BROADCAST] Initiator C2 (Zone 2) dispatched REQ_P_MIN(tau=0.80) to zone members [C1, C3].",
            "[BROADCAST] Initiator C4 (Zone 4) dispatched REQ_P_MIN(tau=0.80) to zone members [C5, C6, C7].",
            "[BROADCAST] Initiator C8 (Zone 8) dispatched REQ_P_MIN(tau=0.80) to zone members [C9, C10].",
            "[STATUS] All zone members received query and set pending_query = 'REQ_P_MIN (tau=0.80)'.",
            "[READY] All 10 peers ready for local binary search of P_min^i in Step 8.",
        ]

        return {
            "step": 7,
            "title": "Step 7: Initiator P_min Query Request",
            "phase_badge": "ACTIVE PHASE: STEP 7: INITIATOR P_MIN QUERY",
            "description": "Zone Initiators prompt zone members to evaluate the minimum signature length P_min^i needed to retain 80% model quality.",
            "formula": "\\text{REQ\\_P\\_MIN}(\\tau = 0.80) \\quad \\forall i \\in Z_I",
            "formula_desc": "Zone Initiators prompt zone members to evaluate the minimum signature length P_min^i needed to retain 80% model quality.",
            "nodes": step7_nodes,
            "edges": step7_edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "packet_events": packet_events,
            "packet_exchanges": packet_events,
            "zones": {
                2: [1, 2, 3],
                4: [4, 5, 6, 7],
                8: [8, 9, 10],
            },
            "boundary_nodes": [1, 6],
            "discovered_neighbor_zones": discovered_neighbor_zones,
            "tau": 0.80,
            "terminal_logs": terminal_logs,
        }
    else:
        return {
            "step": step_number,
            "title": f"Step {step_number}: SemanticDFL Protocol",
            "phase_badge": f"Step {step_number}",
            "description": "SemanticDFL Protocol execution.",
            "nodes": nodes,
            "edges": edges,
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [],
            "terminal_logs": [
                f"[Protocol] Executing Step {step_number} on 10-node network."
            ]
        }


