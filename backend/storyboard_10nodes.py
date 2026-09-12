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
    elif step_number == 8:
        # Step 8: Local Binary Search & P_min^i Reporting
        # Each client executes local binary search on interval p in [1, 10] to find minimal P_min^i for tau=0.80
        # Zone members then dispatch reverse report packets back to their zone initiator.
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

        step8_eval_data = {
            1: {
                "sorted_weights": [0.46, 0.37, 0.17],
                "ratios_cosine": {1: 0.749, 2: 0.961, 3: 1.000},
                "ratios_energy": {1: 0.561, 2: 0.923, 3: 1.000},
                "ratio_p1": 0.749, "ratio_p2": 0.961, "ratio_p3": 1.000,
                "p_min_cosine": 2, "p_min_energy": 2, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 2,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.961, "ratio_pct": "96.1%", "meets": True, "action": "Ratio 96.1% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.749, "ratio_pct": "74.9%", "meets": False, "action": "Boundary test: Ratio 74.9% < 80% -> search right (L=2)"},
                ]
            },
            2: {
                "sorted_weights": [0.57, 0.24, 0.19],
                "ratios_cosine": {1: 0.881, 2: 0.956, 3: 1.000},
                "ratios_energy": {1: 0.776, 2: 0.914, 3: 1.000},
                "ratio_p1": 0.881, "ratio_p2": 0.956, "ratio_p3": 1.000,
                "p_min_cosine": 1, "p_min_energy": 2, "p_min": 1, "p_min_reported": 1,
                "target_initiator": 2,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.956, "ratio_pct": "95.6%", "meets": True, "action": "Ratio 95.6% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.881, "ratio_pct": "88.1%", "meets": True, "action": "Boundary test: Ratio 88.1% >= 80% -> search left (R=0)"},
                ]
            },
            3: {
                "sorted_weights": [0.46, 0.34, 0.20],
                "ratios_cosine": {1: 0.759, 2: 0.944, 3: 1.000},
                "ratios_energy": {1: 0.576, 2: 0.891, 3: 1.000},
                "ratio_p1": 0.759, "ratio_p2": 0.944, "ratio_p3": 1.000,
                "p_min_cosine": 2, "p_min_energy": 2, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 2,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.944, "ratio_pct": "94.4%", "meets": True, "action": "Ratio 94.4% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.759, "ratio_pct": "75.9%", "meets": False, "action": "Boundary test: Ratio 75.9% < 80% -> search right (L=2)"},
                ]
            },
            4: {
                "sorted_weights": [0.62, 0.21, 0.17],
                "ratios_cosine": {1: 0.917, 2: 0.968, 3: 1.000},
                "ratios_energy": {1: 0.841, 2: 0.938, 3: 1.000},
                "ratio_p1": 0.917, "ratio_p2": 0.968, "ratio_p3": 1.000,
                "p_min_cosine": 1, "p_min_energy": 2, "p_min": 1, "p_min_reported": 1,
                "target_initiator": 4,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.968, "ratio_pct": "96.8%", "meets": True, "action": "Ratio 96.8% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.917, "ratio_pct": "91.7%", "meets": True, "action": "Boundary test: Ratio 91.7% >= 80% -> search left (R=0)"},
                ]
            },
            5: {
                "sorted_weights": [0.53, 0.35, 0.12],
                "ratios_cosine": {1: 0.820, 2: 0.983, 3: 1.000},
                "ratios_energy": {1: 0.672, 2: 0.965, 3: 1.000},
                "ratio_p1": 0.820, "ratio_p2": 0.983, "ratio_p3": 1.000,
                "p_min_cosine": 1, "p_min_energy": 2, "p_min": 1, "p_min_reported": 1,
                "target_initiator": 4,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.983, "ratio_pct": "98.3%", "meets": True, "action": "Ratio 98.3% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.820, "ratio_pct": "82.0%", "meets": True, "action": "Boundary test: Ratio 82.0% >= 80% -> search left (R=0)"},
                ]
            },
            6: {
                "sorted_weights": [0.34, 0.24, 0.23, 0.19],
                "ratios_cosine": {1: 0.664, 2: 0.813, 3: 0.929, 4: 1.000},
                "ratios_energy": {1: 0.441, 2: 0.661, 3: 0.862, 4: 1.000},
                "ratio_p1": 0.664, "ratio_p2": 0.813, "ratio_p3": 0.929,
                "p_min_cosine": 2, "p_min_energy": 3, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 4,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.813, "ratio_pct": "81.3%", "meets": True, "action": "Ratio 81.3% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.664, "ratio_pct": "66.4%", "meets": False, "action": "Boundary test: Ratio 66.4% < 80% -> search right (L=2)"},
                ]
            },
            7: {
                "sorted_weights": [0.41, 0.27, 0.21, 0.11],
                "ratios_cosine": {1: 0.752, 2: 0.901, 3: 0.979, 4: 1.000},
                "ratios_energy": {1: 0.565, 2: 0.812, 3: 0.959, 4: 1.000},
                "ratio_p1": 0.752, "ratio_p2": 0.901, "ratio_p3": 0.979,
                "p_min_cosine": 2, "p_min_energy": 3, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 4,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.901, "ratio_pct": "90.1%", "meets": True, "action": "Ratio 90.1% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.752, "ratio_pct": "75.2%", "meets": False, "action": "Boundary test: Ratio 75.2% < 80% -> search right (L=2)"},
                ]
            },
            8: {
                "sorted_weights": [0.38, 0.32, 0.30],
                "ratios_cosine": {1: 0.655, 2: 0.856, 3: 1.000},
                "ratios_energy": {1: 0.429, 2: 0.733, 3: 1.000},
                "ratio_p1": 0.655, "ratio_p2": 0.856, "ratio_p3": 1.000,
                "p_min_cosine": 2, "p_min_energy": 3, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 8,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.856, "ratio_pct": "85.6%", "meets": True, "action": "Ratio 85.6% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.655, "ratio_pct": "65.5%", "meets": False, "action": "Boundary test: Ratio 65.5% < 80% -> search right (L=2)"},
                ]
            },
            9: {
                "sorted_weights": [0.45, 0.32, 0.23],
                "ratios_cosine": {1: 0.752, 2: 0.923, 3: 1.000},
                "ratios_energy": {1: 0.565, 2: 0.852, 3: 1.000},
                "ratio_p1": 0.752, "ratio_p2": 0.923, "ratio_p3": 1.000,
                "p_min_cosine": 2, "p_min_energy": 3, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 8,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.923, "ratio_pct": "92.3%", "meets": True, "action": "Ratio 92.3% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.752, "ratio_pct": "75.2%", "meets": False, "action": "Boundary test: Ratio 75.2% < 80% -> search right (L=2)"},
                ]
            },
            10: {
                "sorted_weights": [0.43, 0.33, 0.12, 0.12],
                "ratios_cosine": {1: 0.757, 2: 0.954, 3: 0.977, 4: 1.000},
                "ratios_energy": {1: 0.573, 2: 0.910, 3: 0.955, 4: 1.000},
                "ratio_p1": 0.757, "ratio_p2": 0.954, "ratio_p3": 0.977,
                "p_min_cosine": 2, "p_min_energy": 3, "p_min": 2, "p_min_reported": 2,
                "target_initiator": 8,
                "binary_search_steps": [
                    {"step": 1, "low": 1, "high": 10, "mid": 5, "ratio": 1.000, "ratio_pct": "100.0%", "meets": True, "action": "Ratio 100% >= 80% -> search left (R=4)"},
                    {"step": 2, "low": 1, "high": 4, "mid": 2, "ratio": 0.954, "ratio_pct": "95.4%", "meets": True, "action": "Ratio 95.4% >= 80% -> search left (R=1)"},
                    {"step": 3, "low": 1, "high": 1, "mid": 1, "ratio": 0.757, "ratio_pct": "75.7%", "meets": False, "action": "Boundary test: Ratio 75.7% < 80% -> search right (L=2)"},
                ]
            },
        }

        # Reverse report packet traces from members to zone initiators
        packet_events = [
            # Zone 2: Node 1 -> C2, Node 3 -> C2
            {
                "packet_id": "report_1_to_2",
                "source": "C1",
                "target": "C2",
                "source_num": 1,
                "target_num": 2,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 2,
                "label": "P_min = 2",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 2, "source_id": 1},
            },
            {
                "packet_id": "report_3_to_2",
                "source": "C3",
                "target": "C2",
                "source_num": 3,
                "target_num": 2,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 2,
                "label": "P_min = 2",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 2, "source_id": 3},
            },
            # Zone 4: Node 5 -> C4, Node 6 -> C4, Node 7 -> C4
            {
                "packet_id": "report_5_to_4",
                "source": "C5",
                "target": "C4",
                "source_num": 5,
                "target_num": 4,
                "type": "REPORT_P_MIN",
                "p_min": 1,
                "p_min_cosine": 1,
                "p_min_energy": 2,
                "label": "P_min = 1",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 1, "p_min_cosine": 1, "p_min_energy": 2, "source_id": 5},
            },
            {
                "packet_id": "report_6_to_4",
                "source": "C6",
                "target": "C4",
                "source_num": 6,
                "target_num": 4,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 3,
                "label": "P_min = 2",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 3, "source_id": 6},
            },
            {
                "packet_id": "report_7_to_4",
                "source": "C7",
                "target": "C4",
                "source_num": 7,
                "target_num": 4,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 3,
                "label": "P_min = 2",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 3, "source_id": 7},
            },
            # Zone 8: Node 9 -> C8, Node 10 -> C8
            {
                "packet_id": "report_9_to_8",
                "source": "C9",
                "target": "C8",
                "source_num": 9,
                "target_num": 8,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 3,
                "label": "P_min = 2",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 3, "source_id": 9},
            },
            {
                "packet_id": "report_10_to_8",
                "source": "C10",
                "target": "C8",
                "source_num": 10,
                "target_num": 8,
                "type": "REPORT_P_MIN",
                "p_min": 2,
                "p_min_cosine": 2,
                "p_min_energy": 3,
                "label": "P_min = 2",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"msg": "REPORT_P_MIN", "p_min": 2, "p_min_cosine": 2, "p_min_energy": 3, "source_id": 10},
            },
        ]

        step8_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            zid = node_to_zone[nid]
            is_init = (nid in initiators)
            ev = step8_eval_data[nid]

            # Full metadata preservation
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

            if is_init:
                n_copy["discovered_neighbor_zones"] = list(discovered_neighbor_zones.get(nid, []))
            else:
                n_copy["discovered_neighbor_zones"] = []

            # Step 8 Local Binary Search & P_min evaluation attributes
            n_copy["sorted_weights"] = list(ev["sorted_weights"])
            n_copy["ratios_cosine"] = dict(ev["ratios_cosine"])
            n_copy["ratios_energy"] = dict(ev["ratios_energy"])
            n_copy["ratio_p1"] = ev["ratio_p1"]
            n_copy["ratio_p2"] = ev["ratio_p2"]
            n_copy["ratio_p3"] = ev["ratio_p3"]
            n_copy["p_min_cosine"] = ev["p_min_cosine"]
            n_copy["p_min_energy"] = ev["p_min_energy"]
            n_copy["p_min"] = ev["p_min"]
            n_copy["p_min_reported"] = ev["p_min_reported"]
            n_copy["binary_search_steps"] = list(ev["binary_search_steps"])
            n_copy["binary_search_trace"] = list(ev["binary_search_steps"])
            n_copy["target_initiator"] = f"C{zid}"
            n_copy["target_initiator_id"] = zid
            n_copy["binary_search"] = {
                "sorted_non_zero_weights": list(ev["sorted_weights"]),
                "quality_ratios_cosine": {k: round(v * 100.0, 1) for k, v in ev["ratios_cosine"].items()},
                "quality_ratios_energy": {k: round(v * 100.0, 1) for k, v in ev["ratios_energy"].items()},
                "p_min_cosine": ev["p_min_cosine"],
                "p_min_energy": ev["p_min_energy"],
                "steps": list(ev["binary_search_steps"]),
            }

            if is_init:
                n_copy["is_reporting"] = False
                n_copy["self_p_min"] = ev["p_min"]
                if nid == 2:
                    n_copy["received_reports"] = {1: 2, 3: 2}
                elif nid == 4:
                    n_copy["received_reports"] = {5: 1, 6: 2, 7: 2}
                elif nid == 8:
                    n_copy["received_reports"] = {9: 2, 10: 2}
            else:
                n_copy["is_reporting"] = True
                n_copy["reported_to_initiator"] = zid

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
            step8_nodes.append(n_copy)

        # Edges for Step 8: All 18 physical links remain solid slate lines
        step8_edges = []
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
            step8_edges.append(e_copy)

        terminal_logs = [
            "[STEP 8] Local Binary Search & P_min Reporting initialized (tau = 0.80).",
            "[EVALUATION] All 10 nodes executed binary search on interval p in [1, 10] over sorted parameter weights.",
            "[REPORT] Zone 2 Member C1 reported P_min = 2 to Initiator C2 👑.",
            "[REPORT] Zone 2 Member C3 reported P_min = 2 to Initiator C2 👑.",
            "[REPORT] Zone 4 Member C5 reported P_min = 1 [cos] / 2 [energy] to Initiator C4 👑.",
            "[REPORT] Zone 4 Member C6 reported P_min = 2 [cos] / 3 [energy] to Initiator C4 👑.",
            "[REPORT] Zone 4 Member C7 reported P_min = 2 [cos] / 3 [energy] to Initiator C4 👑.",
            "[REPORT] Zone 8 Member C9 reported P_min = 2 [cos] / 3 [energy] to Initiator C8 👑.",
            "[REPORT] Zone 8 Member C10 reported P_min = 2 [cos] / 3 [energy] to Initiator C8 👑.",
            "[STATUS] Zone Initiators C2, C4, C8 gathered member P_min reports and prepared for consensus.",
        ]

        return {
            "step": 8,
            "title": "Step 8: Local Binary Search & P_min^i Reporting",
            "phase_badge": "ACTIVE PHASE: STEP 8: LOCAL BINARY SEARCH & P_MIN REPORTING",
            "description": "Each client executes local binary search over parameter dimension p in [1, 10] to find minimal signature length retaining 80% quality, then reports to zone initiator.",
            "formula": "\\text{BinarySearch}(p \\in [1, 10]) \\rightarrow P_{\\min}^i, \\quad \\text{REPORT}(P_{\\min}^i) \\rightarrow I_{Z}",
            "formula_desc": "Each client executes local binary search on interval p in [1, 10] on sorted absolute weights to find minimal P_min retaining 80% quality.",
            "nodes": step8_nodes,
            "edges": step8_edges,
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
    elif step_number == 9:
        # Step 9: Inter-Initiator P_min Exchange via Boundary Gateways & Global Quantile Consensus
        # Initiators (C2, C4, C8) mutually exchange zone proposals via boundary peers (C1 and C6)
        # to reach consensus on Global P = 3.
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

        local_zone_proposals = {
            2: 2,
            4: 3,
            8: 3,
        }

        received_neighbor_p_map = {
            2: {"C4": 3},
            4: {"C2": 2, "C8": 3},
            8: {"C4": 3},
        }

        # Multi-hop exchange traces via boundary gateway nodes
        packet_events = [
            # C2 -> C1 -> C4 (P=2)
            {
                "packet_id": "pkt_exchange_2_1_4",
                "source": "C2",
                "target": "C4",
                "source_num": 2,
                "target_num": 4,
                "relay": "C1",
                "relay_num": 1,
                "path": ["C2", "C1", "C4"],
                "path_nums": [2, 1, 4],
                "type": "INTER_INITIATOR_EXCHANGE",
                "p_val": 2,
                "p_min": 2,
                "label": "P=2",
                "color": "#059669",
                "route_label": "C2 -> C1 -> C4",
                "zone_id": 2,
                "payload": {"msg": "PROPOSAL_EXCHANGE", "p_val": 2, "from_zone": 2, "relay": 1, "to_zone": 4},
            },
            # C4 -> C1 -> C2 (P=3)
            {
                "packet_id": "pkt_exchange_4_1_2",
                "source": "C4",
                "target": "C2",
                "source_num": 4,
                "target_num": 2,
                "relay": "C1",
                "relay_num": 1,
                "path": ["C4", "C1", "C2"],
                "path_nums": [4, 1, 2],
                "type": "INTER_INITIATOR_EXCHANGE",
                "p_val": 3,
                "p_min": 3,
                "label": "P=3",
                "color": "#ea580c",
                "route_label": "C4 -> C1 -> C2",
                "zone_id": 4,
                "payload": {"msg": "PROPOSAL_EXCHANGE", "p_val": 3, "from_zone": 4, "relay": 1, "to_zone": 2},
            },
            # C4 -> C6 -> C8 (P=3)
            {
                "packet_id": "pkt_exchange_4_6_8",
                "source": "C4",
                "target": "C8",
                "source_num": 4,
                "target_num": 8,
                "relay": "C6",
                "relay_num": 6,
                "path": ["C4", "C6", "C8"],
                "path_nums": [4, 6, 8],
                "type": "INTER_INITIATOR_EXCHANGE",
                "p_val": 3,
                "p_min": 3,
                "label": "P=3",
                "color": "#ea580c",
                "route_label": "C4 -> C6 -> C8",
                "zone_id": 4,
                "payload": {"msg": "PROPOSAL_EXCHANGE", "p_val": 3, "from_zone": 4, "relay": 6, "to_zone": 8},
            },
            # C8 -> C6 -> C4 (P=3)
            {
                "packet_id": "pkt_exchange_8_6_4",
                "source": "C8",
                "target": "C4",
                "source_num": 8,
                "target_num": 4,
                "relay": "C6",
                "relay_num": 6,
                "path": ["C8", "C6", "C4"],
                "path_nums": [8, 6, 4],
                "type": "INTER_INITIATOR_EXCHANGE",
                "p_val": 3,
                "p_min": 3,
                "label": "P=3",
                "color": "#7c3aed",
                "route_label": "C8 -> C6 -> C4",
                "zone_id": 8,
                "payload": {"msg": "PROPOSAL_EXCHANGE", "p_val": 3, "from_zone": 8, "relay": 6, "to_zone": 4},
            },
        ]

        # Prior evaluation data from Step 8 for metadata preservation
        step8_data = get_10node_step_data(8)
        step8_nodes_map = {n["id"]: n for n in step8_data["nodes"]}

        step9_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(step8_nodes_map[nid])
            is_init = (nid in initiators)
            zid = node_to_zone[nid]

            # Set global consensus agreement
            n_copy["agreed_global_p"] = 3
            n_copy["consensus_status"] = "AGREED"

            if is_init:
                n_copy["local_zone_p"] = local_zone_proposals[nid]
                n_copy["received_neighbor_p"] = dict(received_neighbor_p_map[nid])
                n_copy["relay_active"] = False
                n_copy["relayed_packets"] = []
                if nid == 2:
                    n_copy["negotiation_table"] = {
                        "local_zone_proposal": 2,
                        "received_from_neighbors": [{"neighbor": "C4", "via": "C1 (Boundary Gateway)", "p_val": 3}],
                        "proposals_considered": [2, 3],
                        "formula": "max(2, 3) = 3 (global 80% quantile)",
                        "agreed_p": 3,
                        "status": "AGREED",
                    }
                elif nid == 4:
                    n_copy["negotiation_table"] = {
                        "local_zone_proposal": 3,
                        "received_from_neighbors": [
                            {"neighbor": "C2", "via": "C1 (Boundary Gateway)", "p_val": 2},
                            {"neighbor": "C8", "via": "C6 (Boundary Gateway)", "p_val": 3},
                        ],
                        "proposals_considered": [2, 3, 3],
                        "formula": "max(2, 3, 3) = 3 (global 80% quantile)",
                        "agreed_p": 3,
                        "status": "AGREED",
                    }
                elif nid == 8:
                    n_copy["negotiation_table"] = {
                        "local_zone_proposal": 3,
                        "received_from_neighbors": [{"neighbor": "C4", "via": "C6 (Boundary Gateway)", "p_val": 3}],
                        "proposals_considered": [3, 3],
                        "formula": "max(3, 3) = 3 (global 80% quantile)",
                        "agreed_p": 3,
                        "status": "AGREED",
                    }
            elif nid == 1:
                n_copy["relay_active"] = True
                n_copy["relayed_packets"] = [
                    {"packet": "P_Z2=2", "from": "C2", "to": "C4", "p_val": 2, "label": "P=2", "route": "C2 -> C1 -> C4"},
                    {"packet": "P_Z4=3", "from": "C4", "to": "C2", "p_val": 3, "label": "P=3", "route": "C4 -> C1 -> C2"},
                ]
                n_copy["relay_description"] = "Active Gateway forwarding proposal exchanges between Initiator C2 (P=2) and Initiator C4 (P=3)."
            elif nid == 6:
                n_copy["relay_active"] = True
                n_copy["relayed_packets"] = [
                    {"packet": "P_Z4=3", "from": "C4", "to": "C8", "p_val": 3, "label": "P=3", "route": "C4 -> C6 -> C8"},
                    {"packet": "P_Z8=3", "from": "C8", "to": "C4", "p_val": 3, "label": "P=3", "route": "C8 -> C6 -> C4"},
                ]
                n_copy["relay_description"] = "Active Gateway forwarding proposal exchanges between Initiator C4 (P=3) and Initiator C8 (P=3)."
            else:
                n_copy["relay_active"] = False
                n_copy["relayed_packets"] = []
                n_copy["member_status"] = "Awaiting Step 10 Global-P Broadcast from Initiator"

            step9_nodes.append(n_copy)

        # Edges for Step 9: All 18 physical links remain solid slate lines
        step9_edges = []
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
            step9_edges.append(e_copy)

        terminal_logs = [
            "[STEP 9] Inter-Initiator P_min Exchange & Global Consensus initialized (q = 0.80).",
            "[BOUNDARY ROUTING] Initiators utilize boundary gateway nodes C1 and C6 discovered in Step 6.",
            "[RELAY C1] Node C1 relayed Packet P_Z2=2 (C2 -> C1 -> C4) and Packet P_Z4=3 (C4 -> C1 -> C2).",
            "[RELAY C6] Node C6 relayed Packet P_Z4=3 (C4 -> C6 -> C8) and Packet P_Z8=3 (C8 -> C6 -> C4).",
            "[NEGOTIATION] Initiator C2 received neighbor proposal from C4: P=3 (holds local P=2).",
            "[NEGOTIATION] Initiator C4 received neighbor proposals from C2: P=2, C8: P=3 (holds local P=3).",
            "[NEGOTIATION] Initiator C8 received neighbor proposal from C4: P=3 (holds local P=3).",
            "[CONSENSUS] P = min(Quantile_0.8({P_min^i}), P_max) = max(2, 3, 3) = 3.",
            "[CONSENSUS] All 3 Zone Initiators (C2, C4, C8) reached unanimous consensus on Global P = 3.",
            "[READY] Prepared for Step 10: Global-P Broadcast & Signature Extraction.",
        ]

        return {
            "step": 9,
            "title": "Step 9: Inter-Initiator P_min Exchange via Boundary Gateways & Global Consensus",
            "phase_badge": "ACTIVE PHASE: STEP 9: INTER-INITIATOR CONSENSUS EXCHANGE",
            "description": "Initiators exchange zone proposals via boundary peers C1 and C6, reaching unanimous global consensus on unified signature length P = 3.",
            "formula": "P = \\min(\\text{Quantile}_{0.8}(\\{P_{\\min}^i\\}), P_{\\max}) = 3, \\quad I_p \\xleftrightarrow{\\text{Frontier}} I_q",
            "formula_desc": "Initiators relay their zone proposals through boundary nodes C1 and C6 to agree on a unified global P=3.",
            "nodes": step9_nodes,
            "edges": step9_edges,
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
            "agreed_global_p": 3,
            "consensus_status": "AGREED",
            "tau": 0.80,
            "quantile_q": 0.80,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 10:
        # Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)
        # With global consensus locked at P=3, each Zone Initiator broadcasts an official directive to its members:
        # ORDER_EXTRACT(P = 3)
        initiators = [2, 4, 8]
        node_to_zone = {
            1: 2, 2: 2, 3: 2,
            4: 4, 5: 4, 6: 4, 7: 4,
            8: 8, 9: 8, 10: 8,
        }

        zone_members = {
            2: [1, 3],
            4: [5, 6, 7],
            8: [9, 10],
        }

        discovered_neighbor_zones = {
            2: ["C4"],
            4: ["C2", "C8"],
            8: ["C4"],
        }

        initiator_colors = {
            2: "#059669",
            4: "#ea580c",
            8: "#7c3aed",
        }

        # Outgoing intra-zone order packets from Initiators to zone members
        packet_events = [
            # Zone 2: C2 -> [1, 3]
            {
                "packet_id": "order_2_to_1",
                "source": "C2",
                "target": "C1",
                "source_num": 2,
                "target_num": 1,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 2},
            },
            {
                "packet_id": "order_2_to_3",
                "source": "C2",
                "target": "C3",
                "source_num": 2,
                "target_num": 3,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#059669",
                "zone_id": 2,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 2},
            },
            # Zone 4: C4 -> [5, 6, 7]
            {
                "packet_id": "order_4_to_5",
                "source": "C4",
                "target": "C5",
                "source_num": 4,
                "target_num": 5,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 4},
            },
            {
                "packet_id": "order_4_to_6",
                "source": "C4",
                "target": "C6",
                "source_num": 4,
                "target_num": 6,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 4},
            },
            {
                "packet_id": "order_4_to_7",
                "source": "C4",
                "target": "C7",
                "source_num": 4,
                "target_num": 7,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 4},
            },
            # Zone 8: C8 -> [9, 10]
            {
                "packet_id": "order_8_to_9",
                "source": "C8",
                "target": "C9",
                "source_num": 8,
                "target_num": 9,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 8},
            },
            {
                "packet_id": "order_8_to_10",
                "source": "C8",
                "target": "C10",
                "source_num": 8,
                "target_num": 10,
                "type": "ORDER_EXTRACT",
                "target_p": 3,
                "label": "ORDER: P=3",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {"cmd": "ORDER_EXTRACT", "target_p": 3, "from_initiator": 8},
            },
        ]

        # Preserve metadata from Step 9
        step9_data = get_10node_step_data(9)
        step9_nodes_map = {n["id"]: n for n in step9_data["nodes"]}

        step10_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(step9_nodes_map[nid])
            is_init = (nid in initiators)
            zid = node_to_zone[nid]

            # Step 10 extraction order attributes on all 10 nodes
            n_copy["target_signature_length"] = 3
            n_copy["order_received_from"] = f"C{zid}"
            n_copy["order_received_from_id"] = zid
            n_copy["order_status"] = "READY_TO_EXTRACT"
            n_copy["agreed_global_p"] = 3
            n_copy["consensus_status"] = "AGREED"

            if is_init:
                n_copy["order_directive"] = f"Broadcasted ORDER_EXTRACT(P=3) to Zone {zid} members"
                n_copy["target_members"] = zone_members[nid]
                n_copy["extraction_details"] = {
                    "role": "ZONE_INITIATOR",
                    "action": "BROADCAST_ORDER",
                    "command": "ORDER_EXTRACT",
                    "target_p": 3,
                    "target_members": [f"C{m}" for m in zone_members[nid]],
                    "status": "READY_TO_EXTRACT",
                }
            else:
                n_copy["order_directive"] = f"Received ORDER_EXTRACT(P=3) from Initiator C{zid} 👑"
                n_copy["extraction_details"] = {
                    "role": "ZONE_MEMBER",
                    "action": "LOCK_DIMENSION",
                    "command": "ORDER_EXTRACT",
                    "target_p": 3,
                    "received_from": f"C{zid}",
                    "status": "READY_TO_EXTRACT",
                }

            step10_nodes.append(n_copy)

        # Edges for Step 10: All 18 physical links remain solid slate lines
        step10_edges = []
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
            step10_edges.append(e_copy)

        terminal_logs = [
            "[STEP 10] Initiator Extraction Order Broadcast initialized (Global P = 3).",
            "[BROADCAST] Zone 2 Initiator C2 dispatched ORDER_EXTRACT(P=3) to members [C1, C3].",
            "[BROADCAST] Zone 4 Initiator C4 dispatched ORDER_EXTRACT(P=3) to members [C5, C6, C7].",
            "[BROADCAST] Zone 8 Initiator C8 dispatched ORDER_EXTRACT(P=3) to members [C9, C10].",
            "[LOCK] All 10 edge nodes locked target signature length to P = 3.",
            "[STATUS] All 10 nodes status updated to READY_TO_EXTRACT.",
            "[READY] Prepared for Step 11: Local Compact Top-P Signature Extraction.",
        ]

        return {
            "step": 10,
            "title": "Step 10: Initiator Extraction Order Broadcast (ORDER_EXTRACT P=3)",
            "phase_badge": "ACTIVE PHASE: STEP 10: EXTRACTION ORDER BROADCAST (P=3)",
            "description": "Zone Initiators broadcast official extraction order directive ORDER_EXTRACT(P=3) to all zone members, locking signature length across all 10 nodes.",
            "formula": "\\text{ORDER\\_EXTRACT}(P = 3) \\quad \\forall i \\in Z_I",
            "formula_desc": "Initiators broadcast the agreed global length P=3 down to all zone peers.",
            "nodes": step10_nodes,
            "edges": step10_edges,
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
            "agreed_global_p": 3,
            "target_p": 3,
            "order_status": "READY_TO_EXTRACT",
            "tau": 0.80,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 11:
        # Step 11: Top-P Signature Extraction with Dual Representation (Network Indices vs. Visual Bitmask)
        # Highlight the core engineering contrast from the SemanticDFL paper:
        # 1. Network Reality: Peers dispatch lightweight integer index sets without values (e.g. indices = [1, 2, 3])
        #    to save bandwidth (3 Bytes vs 40 Bytes) and preserve data privacy (zero parameter leakage).
        # 2. Pedagogical Visualization: The UI expands these indices into an interactive 10-cell binary mask for clear visual tracking.
        initiators = [2, 4, 8]
        node_to_zone = {
            1: 2, 2: 2, 3: 2,
            4: 4, 5: 4, 6: 4, 7: 4,
            8: 8, 9: 8, 10: 8,
        }

        zone_members = {
            2: [1, 3],
            4: [5, 6, 7],
            8: [9, 10],
        }

        # Deterministic Top-3 active class IDs (1-indexed CIFAR-10 classes) per node
        # Consistent with non-zero coordinates in STORYBOARD_10_VECTORS & prompt specification
        top_p_indices_map = {
            1: [1, 2, 3],
            2: [1, 2, 3],
            3: [4, 5, 6],
            4: [4, 5, 6],
            5: [4, 5, 6],
            6: [7, 9, 10],
            7: [8, 9, 10],
            8: [4, 5, 6],
            9: [1, 2, 3],
            10: [8, 9, 10],
        }

        # 10D binary indicator mask m_i in {0, 1}^10
        binary_masks_map = {}
        for nid, idx_set in top_p_indices_map.items():
            mask = [1 if (c in idx_set) else 0 for c in range(1, 11)]
            binary_masks_map[nid] = mask

        # Zone Signature Registries on Initiators: { peer_id: top_p_indices }
        zone_collected_registries = {
            2: {
                1: top_p_indices_map[1],
                2: top_p_indices_map[2],
                3: top_p_indices_map[3],
            },
            4: {
                4: top_p_indices_map[4],
                5: top_p_indices_map[5],
                6: top_p_indices_map[6],
                7: top_p_indices_map[7],
            },
            8: {
                8: top_p_indices_map[8],
                9: top_p_indices_map[9],
                10: top_p_indices_map[10],
            },
        }

        initiator_colors = {
            2: "#059669",
            4: "#ea580c",
            8: "#7c3aed",
        }

        # Wire packet traces from members to zone initiators
        # Payload explicitly carries: {"type": "TOP_P_SIG", "indices": node.top_p_indices}
        packet_events = [
            # Zone 2 members -> C2
            {
                "packet_id": "sig_1_to_2",
                "source": "C1",
                "target": "C2",
                "source_num": 1,
                "target_num": 2,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[1],
                "label": "SIG: {C1, C2, C3}",
                "color": "#059669",
                "zone_id": 2,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[1],
                    "source_node": 1,
                    "target_initiator": 2,
                    "payload_bytes": 3,
                },
            },
            {
                "packet_id": "sig_3_to_2",
                "source": "C3",
                "target": "C2",
                "source_num": 3,
                "target_num": 2,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[3],
                "label": "SIG: {C4, C5, C6}",
                "color": "#059669",
                "zone_id": 2,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[3],
                    "source_node": 3,
                    "target_initiator": 2,
                    "payload_bytes": 3,
                },
            },
            # Zone 4 members -> C4
            {
                "packet_id": "sig_5_to_4",
                "source": "C5",
                "target": "C4",
                "source_num": 5,
                "target_num": 4,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[5],
                "label": "SIG: {C4, C5, C6}",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[5],
                    "source_node": 5,
                    "target_initiator": 4,
                    "payload_bytes": 3,
                },
            },
            {
                "packet_id": "sig_6_to_4",
                "source": "C6",
                "target": "C4",
                "source_num": 6,
                "target_num": 4,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[6],
                "label": "SIG: {C7, C9, C10}",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[6],
                    "source_node": 6,
                    "target_initiator": 4,
                    "payload_bytes": 3,
                },
            },
            {
                "packet_id": "sig_7_to_4",
                "source": "C7",
                "target": "C4",
                "source_num": 7,
                "target_num": 4,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[7],
                "label": "SIG: {C8, C9, C10}",
                "color": "#ea580c",
                "zone_id": 4,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[7],
                    "source_node": 7,
                    "target_initiator": 4,
                    "payload_bytes": 3,
                },
            },
            # Zone 8 members -> C8
            {
                "packet_id": "sig_9_to_8",
                "source": "C9",
                "target": "C8",
                "source_num": 9,
                "target_num": 8,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[9],
                "label": "SIG: {C1, C2, C3}",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[9],
                    "source_node": 9,
                    "target_initiator": 8,
                    "payload_bytes": 3,
                },
            },
            {
                "packet_id": "sig_10_to_8",
                "source": "C10",
                "target": "C8",
                "source_num": 10,
                "target_num": 8,
                "type": "TOP_P_SIG",
                "indices": top_p_indices_map[10],
                "label": "SIG: {C8, C9, C10}",
                "color": "#7c3aed",
                "zone_id": 8,
                "payload": {
                    "type": "TOP_P_SIG",
                    "indices": top_p_indices_map[10],
                    "source_node": 10,
                    "target_initiator": 8,
                    "payload_bytes": 3,
                },
            },
        ]

        # Preserve metadata from Step 10
        step10_data = get_10node_step_data(10)
        step10_nodes_map = {n["id"]: n for n in step10_data["nodes"]}

        step11_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(step10_nodes_map[nid])
            is_init = (nid in initiators)
            zid = node_to_zone[nid]

            # Dual representation attributes
            indices = top_p_indices_map[nid]
            mask_10d = binary_masks_map[nid]
            n_copy["top_p_indices"] = indices
            n_copy["binary_mask_10d"] = mask_10d
            n_copy["dispatched_payload_bytes"] = 3  # 3 x sizeof(uint8)
            n_copy["raw_weights_bytes"] = 40       # 10 x sizeof(float32)
            n_copy["bandwidth_reduction_pct"] = 92.5
            n_copy["wire_format"] = "uint8[3]"
            n_copy["zero_parameter_leakage"] = True
            n_copy["target_signature_length"] = 3
            n_copy["signature_extracted"] = True
            n_copy["status"] = "INITIATOR" if is_init else "CLIENT"

            # Active CIFAR-10 class tags for visual bitmask
            n_copy["active_classes"] = [
                {
                    "class_id": cid,
                    "code": CIFAR10_CLASSES[cid]["code"],
                    "name": CIFAR10_CLASSES[cid]["name"],
                    "icon": CIFAR10_CLASSES[cid]["icon"],
                }
                for cid in indices
            ]

            if is_init:
                # Initiator holds collected zone registry
                n_copy["zone_collected_signatures"] = zone_collected_registries[nid]
                n_copy["signature_role"] = "ZONE_INITIATOR"
                n_copy["signature_summary"] = (
                    f"Initiator C{nid} extracted local signature {indices} and collected "
                    f"signatures from Zone {zid} members: {list(zone_collected_registries[nid].keys())}."
                )
            else:
                n_copy["zone_collected_signatures"] = {}
                n_copy["signature_role"] = "ZONE_MEMBER"
                n_copy["signature_summary"] = (
                    f"Member C{nid} extracted signature {indices} (3 Bytes) and dispatched "
                    f"to Zone {zid} Initiator C{zid}."
                )

            step11_nodes.append(n_copy)

        # Edges for Step 11: All 18 physical links remain clean solid slate lines
        step11_edges = []
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
            step11_edges.append(e_copy)

        terminal_logs = [
            "[STEP 11] Top-P Signature Extraction initialized (Consensus P = 3).",
            "[EXTRACTION] All 10 edge peers extracted top-3 unweighted coordinate indices.",
            "[PRIVACY] Transmitted payloads contain zero floating-point weights (zero parameter leakage).",
            "[BANDWIDTH] Wire payload size: 3 Bytes (3 × uint8) vs. 40 Bytes raw vector (92.5% reduction).",
            "[DISPATCH] Zone 2 members [C1, C3] dispatched signatures to Initiator C2.",
            "[DISPATCH] Zone 4 members [C5, C6, C7] dispatched signatures to Initiator C4.",
            "[DISPATCH] Zone 8 members [C9, C10] dispatched signatures to Initiator C8.",
            "[REGISTRY] Initiators C2, C4, C8 successfully aggregated all zone signatures.",
            "[READY] Prepared for Step 12: Intra-Zone Semantic Affinity Clustering.",
        ]

        return {
            "step": 11,
            "title": "Step 11: Top-P Signature Extraction with Dual Representation (Network Indices vs. Visual Bitmask)",
            "phase_badge": "ACTIVE PHASE: STEP 11: SIGNATURE EXTRACTION & DISPATCH",
            "description": "Peers extract compact unweighted 3-index sets (3 Bytes) to eliminate parameter leakage, while the dashboard renders 10D binary indicator masks.",
            "formula": "S_i = \\text{Top-}3(\\text{indices of } |\\mathbf{w}_i|) \\subset \\{1, \\dots, 10\\}, \\quad \\mathbf{m}_i \\in \\{0, 1\\}^{10}",
            "formula_desc": "Network layer transmits raw index sets (zero weights attached). Dashboard renders 10D binary indicators for visual clarity.",
            "nodes": step11_nodes,
            "edges": step11_edges,
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
            "agreed_global_p": 3,
            "target_p": 3,
            "zone_collected_registries": zone_collected_registries,
            "tau": 0.80,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 12:
        # Step 12: Intra-Zone Semantic Clustering via Cosine Similarity & Affinity Propagation (AP)
        # Each Zone Initiator evaluates semantic similarity across its collected member signatures
        # (m_i, m_j in {0, 1}^10) using Cosine Similarity metric:
        # Sim(i, j) = (m_i . m_j) / (||m_i||_2 * ||m_j||_2) = |m_i cap m_j| / 3
        # Then executes Affinity Propagation clustering.
        initiators = [2, 4, 8]
        node_to_zone = {
            1: 2, 2: 2, 3: 2,
            4: 4, 5: 4, 6: 4, 7: 4,
            8: 8, 9: 8, 10: 8,
        }

        # Exact Intra-Zone Cosine Similarity Matrices
        similarity_matrices = {
            2: {
                "peer_ids": [1, 2, 3],
                "peers": ["C1", "C2", "C3"],
                "matrix": [
                    [1.0, 1.0, 0.0],
                    [1.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
            },
            4: {
                "peer_ids": [4, 5, 6, 7],
                "peers": ["C4", "C5", "C6", "C7"],
                "matrix": [
                    [1.0, 1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.67],
                    [0.0, 0.0, 0.67, 1.0],
                ],
            },
            8: {
                "peer_ids": [8, 9, 10],
                "peers": ["C8", "C9", "C10"],
                "matrix": [
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
            },
        }

        # Exact Affinity Propagation Clusters per Zone
        zone_clusters_map = {
            2: {
                "2-A": {
                    "cluster_id": "2-A",
                    "exemplar": 2,
                    "members": [1, 2],
                    "members_str": ["C1", "C2"],
                    "shared_classes": ["Airplane (C1)", "Automobile (C2)", "Bird (C3)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 2-A (Exemplar C2)",
                    "color": "#059669",
                },
                "2-B": {
                    "cluster_id": "2-B",
                    "exemplar": 3,
                    "members": [3],
                    "members_str": ["C3"],
                    "shared_classes": ["Cat (C4)", "Deer (C5)", "Dog (C6)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 2-B (Exemplar C3)",
                    "color": "#0d9488",
                },
            },
            4: {
                "4-A": {
                    "cluster_id": "4-A",
                    "exemplar": 4,
                    "members": [4, 5],
                    "members_str": ["C4", "C5"],
                    "shared_classes": ["Cat (C4)", "Deer (C5)", "Dog (C6)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 4-A (Exemplar C4)",
                    "color": "#ea580c",
                },
                "4-B": {
                    "cluster_id": "4-B",
                    "exemplar": 6,
                    "members": [6, 7],
                    "members_str": ["C6", "C7"],
                    "shared_classes": ["Ship (C9)", "Truck (C10)"],
                    "overlap_pct": 66.7,
                    "label": "Cluster 4-B (Exemplar C6)",
                    "color": "#d97706",
                },
            },
            8: {
                "8-A": {
                    "cluster_id": "8-A",
                    "exemplar": 8,
                    "members": [8],
                    "members_str": ["C8"],
                    "shared_classes": ["Cat (C4)", "Deer (C5)", "Dog (C6)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 8-A (Exemplar C8)",
                    "color": "#7c3aed",
                },
                "8-B": {
                    "cluster_id": "8-B",
                    "exemplar": 9,
                    "members": [9],
                    "members_str": ["C9"],
                    "shared_classes": ["Airplane (C1)", "Automobile (C2)", "Bird (C3)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 8-B (Exemplar C9)",
                    "color": "#6366f1",
                },
                "8-C": {
                    "cluster_id": "8-C",
                    "exemplar": 10,
                    "members": [10],
                    "members_str": ["C10"],
                    "shared_classes": ["Horse (C8)", "Ship (C9)", "Truck (C10)"],
                    "overlap_pct": 100.0,
                    "label": "Cluster 8-C (Exemplar C10)",
                    "color": "#8b5cf6",
                },
            },
        }

        # Direct node to cluster assignment lookup
        node_cluster_assignments = {
            1: {"cluster_id": "2-A", "exemplar": 2, "peers": [1, 2], "color": "#059669"},
            2: {"cluster_id": "2-A", "exemplar": 2, "peers": [1, 2], "color": "#059669"},
            3: {"cluster_id": "2-B", "exemplar": 3, "peers": [3], "color": "#0d9488"},
            4: {"cluster_id": "4-A", "exemplar": 4, "peers": [4, 5], "color": "#ea580c"},
            5: {"cluster_id": "4-A", "exemplar": 4, "peers": [4, 5], "color": "#ea580c"},
            6: {"cluster_id": "4-B", "exemplar": 6, "peers": [6, 7], "color": "#d97706"},
            7: {"cluster_id": "4-B", "exemplar": 6, "peers": [6, 7], "color": "#d97706"},
            8: {"cluster_id": "8-A", "exemplar": 8, "peers": [8], "color": "#7c3aed"},
            9: {"cluster_id": "8-B", "exemplar": 9, "peers": [9], "color": "#6366f1"},
            10: {"cluster_id": "8-C", "exemplar": 10, "peers": [10], "color": "#8b5cf6"},
        }

        # Preserve metadata from Step 11
        step11_data = get_10node_step_data(11)
        step11_nodes_map = {n["id"]: n for n in step11_data["nodes"]}

        step12_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(step11_nodes_map[nid])
            is_init = (nid in initiators)
            zid = node_to_zone[nid]

            # Populate clustering attributes
            c_info = node_cluster_assignments[nid]
            n_copy["assigned_cluster_id"] = c_info["cluster_id"]
            n_copy["cluster_id"] = c_info["cluster_id"]
            n_copy["cluster_exemplar"] = c_info["exemplar"]
            n_copy["cluster_peers"] = c_info["peers"]
            n_copy["cluster_peers_str"] = [f"C{p}" for p in c_info["peers"]]
            n_copy["cluster_color"] = c_info["color"]
            n_copy["cluster_status"] = "CLUSTERED"

            if is_init:
                # Initiators hold intra-zone similarity matrix and cluster registry
                n_copy["intra_zone_similarity_matrix"] = similarity_matrices[nid]
                n_copy["clusters"] = zone_clusters_map[nid]
                n_copy["zone_clusters"] = zone_clusters_map[nid]
                n_copy["clustering_role"] = "ZONE_INITIATOR (CLUSTERING_ENGINE)"
            else:
                n_copy["intra_zone_similarity_matrix"] = {}
                n_copy["clusters"] = {}
                n_copy["zone_clusters"] = {}
                n_copy["clustering_role"] = "ZONE_MEMBER (CLUSTER_PARTITIONED)"

            step12_nodes.append(n_copy)

        # Edges for Step 12: All 18 physical links remain clean solid slate lines
        step12_edges = []
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
            step12_edges.append(e_copy)

        terminal_logs = [
            "[STEP 12] Intra-Zone Semantic Clustering initialized via Affinity Propagation (AP).",
            "[SIMILARITY] Zone 2 Initiator C2 computed 3x3 Cosine Similarity matrix: Sim(1,2)=1.0, Sim(1,3)=0.0, Sim(2,3)=0.0.",
            "[CLUSTER] Zone 2 partitioned into 2 clusters: Cluster 2-A {C1, C2} (Exemplar C2) & Cluster 2-B {C3} (Exemplar C3).",
            "[SIMILARITY] Zone 4 Initiator C4 computed 4x4 Cosine Similarity matrix: Sim(4,5)=1.0, Sim(6,7)=0.67, cross-pairs=0.0.",
            "[CLUSTER] Zone 4 partitioned into 2 clusters: Cluster 4-A {C4, C5} (Exemplar C4) & Cluster 4-B {C6, C7} (Exemplar C6).",
            "[SIMILARITY] Zone 8 Initiator C8 computed 3x3 Cosine Similarity matrix: All non-diagonal similarities = 0.0.",
            "[CLUSTER] Zone 8 partitioned into 3 orthogonal clusters: Cluster 8-A {C8}, Cluster 8-B {C9}, Cluster 8-C {C10}.",
            "[ANALYSIS] Orthogonal distribution in Zone 8 highlights necessity for inter-zone Semantic Overlay links in Step 13.",
            "[SUCCESS] All 10 edge peers successfully assigned to semantic clusters.",
        ]

        return {
            "step": 12,
            "title": "Step 12: Intra-Zone Semantic Clustering (Affinity Propagation)",
            "phase_badge": "ACTIVE PHASE: STEP 12: INTRA-ZONE SEMANTIC CLUSTERING (AP)",
            "description": "Each Zone Initiator computes pairwise Cosine Similarities across member signatures and runs Affinity Propagation to form semantic clusters.",
            "formula": "\\text{Sim}(i, j) = \\frac{|\\mathbf{m}_i \\cap \\mathbf{m}_j|}{3}, \\quad \\text{AP}(S) \\to \\mathcal{C}_k",
            "formula_desc": "Initiators run Affinity Propagation on intra-zone cosine similarities to partition peers into semantic clusters.",
            "nodes": step12_nodes,
            "edges": step12_edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "similarity_matrices": similarity_matrices,
            "all_clusters": zone_clusters_map,
            "zones": {
                2: [1, 2, 3],
                4: [4, 5, 6, 7],
                8: [8, 9, 10],
            },
            "boundary_nodes": [1, 6],
            "agreed_global_p": 3,
            "target_p": 3,
            "tau": 0.80,
            "terminal_logs": terminal_logs,
        }
    elif step_number == 13:
        # Step 13: Hierarchical Top-Level Zone Creation (Figure 3(e))
        # The base zone initiators {C2, C4, C8} form a higher-level overlay graph G_init: C2 <-> C4 <-> C8.
        # Phase 1: 1-hop bidirectional VRF score exchange across overlay links:
        #   - C2 <-> C4 (path [2, 1, 4] and [4, 1, 2])
        #   - C4 <-> C8 (path [8, 6, 4] and [4, 6, 8])
        # Phase 2: Node 4 (C4) elected as Top-Level Super-Initiator (👑👑) as central bridge.
        # Phase 3: Symmetrical TOP_PROBE(TTL=1) outward from C4 to both C2 (via C1) and C8 (via C6).
        # Phase 4: Formation of Super-Zone Z_TOP rooted at Node 4.
        step12_data = get_10node_step_data(12)
        step12_nodes_map = {n["id"]: n for n in step12_data["nodes"]}

        initiators = [2, 4, 8]
        top_initiator = 4
        super_zone_members = [2, 4, 8]

        step13_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(step12_nodes_map[nid])

            if nid == top_initiator:
                n_copy["top_level_role"] = "TOP_INITIATOR"
                n_copy["top_level_status"] = "ELECTED_TOP_LEVEL_SUPER_INITIATOR"
                n_copy["is_top_initiator"] = True
                n_copy["top_level_zone"] = "Z_TOP"
                n_copy["super_zone_role"] = "SUPER_INITIATOR"
                n_copy["governing_initiators"] = [2, 4, 8]
                n_copy["governing_initiators_str"] = ["C2", "C4", "C8"]
                n_copy["vrf_top_rank"] = 1
                n_copy["received_overlay_scores"] = {2: 0.0837, 8: 0.0275}
                n_copy["overlay_scoreboard"] = [
                    {"node": 4, "node_str": "C4", "score": 0.0412, "role": "Self (Central Bridge & Winner 👑👑)"},
                    {"node": 2, "node_str": "C2", "score": 0.0837, "role": "Overlay Neighbor (West)", "path": [2, 1, 4]},
                    {"node": 8, "node_str": "C8", "score": 0.0275, "role": "Overlay Neighbor (East)", "path": [8, 6, 4]},
                ]
            elif nid in [2, 8]:
                n_copy["top_level_role"] = "SUPER_ZONE_MEMBER"
                n_copy["top_level_status"] = "SUPER_ZONE_MEMBER"
                n_copy["is_top_initiator"] = False
                n_copy["top_level_zone"] = "Z_TOP"
                n_copy["super_zone_role"] = "SUPER_ZONE_MEMBER"
                n_copy["super_zone_root"] = 4
                n_copy["super_zone_root_str"] = "C4"
                n_copy["vrf_top_rank"] = 3 if nid == 2 else 2
                n_copy["received_top_probe"] = {
                    "from": 4,
                    "from_str": "C4",
                    "ttl": 1,
                    "root": 4,
                    "super_zone": "Z_TOP",
                    "via": 1 if nid == 2 else 6,
                }
            else:
                n_copy["top_level_role"] = "BASE_ZONE_MEMBER"
                n_copy["top_level_status"] = "SUPERVISED_CLIENT"
                n_copy["is_top_initiator"] = False
                n_copy["top_level_zone"] = "Z_TOP"
                n_copy["super_zone_role"] = "SUPERVISED_CLIENT"

            step13_nodes.append(n_copy)

        # 1-Hop VRF Score Exchanges (Phase A)
        vrf_exchange_events = [
            {
                "packet_id": "vrf_2_to_4",
                "type": "VRF_EXCHANGE",
                "score": 0.0837,
                "source": "C2",
                "target": "C4",
                "source_num": 2,
                "target_num": 4,
                "relay": "C1",
                "relay_num": 1,
                "path": [2, 1, 4],
                "path_str": ["C2", "C1", "C4"],
                "color": "#3b82f6",
                "label": "VRF_EXCHANGE(0.0837)",
                "route_label": "C2 -> C1 -> C4",
                "msg": "C2 transmits VRF score (0.0837) to C4 via C1",
            },
            {
                "packet_id": "vrf_8_to_4",
                "type": "VRF_EXCHANGE",
                "score": 0.0275,
                "source": "C8",
                "target": "C4",
                "source_num": 8,
                "target_num": 4,
                "relay": "C6",
                "relay_num": 6,
                "path": [8, 6, 4],
                "path_str": ["C8", "C6", "C4"],
                "color": "#8b5cf6",
                "label": "VRF_EXCHANGE(0.0275)",
                "route_label": "C8 -> C6 -> C4",
                "msg": "C8 transmits VRF score (0.0275) to C4 via C6",
            },
            {
                "packet_id": "vrf_4_to_2",
                "type": "VRF_EXCHANGE",
                "score": 0.0412,
                "source": "C4",
                "target": "C2",
                "source_num": 4,
                "target_num": 2,
                "relay": "C1",
                "relay_num": 1,
                "path": [4, 1, 2],
                "path_str": ["C4", "C1", "C2"],
                "color": "#f59e0b",
                "label": "VRF_EXCHANGE(0.0412)",
                "route_label": "C4 -> C1 -> C2",
                "msg": "C4 transmits VRF score (0.0412) to C2 via C1",
            },
            {
                "packet_id": "vrf_4_to_8",
                "type": "VRF_EXCHANGE",
                "score": 0.0412,
                "source": "C4",
                "target": "C8",
                "source_num": 4,
                "target_num": 8,
                "relay": "C6",
                "relay_num": 6,
                "path": [4, 6, 8],
                "path_str": ["C4", "C6", "C8"],
                "color": "#f59e0b",
                "label": "VRF_EXCHANGE(0.0412)",
                "route_label": "C4 -> C6 -> C8",
                "msg": "C4 transmits VRF score (0.0412) to C8 via C6",
            },
        ]

        # Symmetrical TOP_PROBE Broadcasts from C4 (Phase B)
        probe_events = [
            {
                "packet_id": "top_probe_4_1_2",
                "type": "TOP_PROBE",
                "ttl": 1,
                "root": 4,
                "source": "C4",
                "target": "C2",
                "source_num": 4,
                "target_num": 2,
                "relay": "C1",
                "relay_num": 1,
                "path": [4, 1, 2],
                "path_nums": [4, 1, 2],
                "path_str": ["C4", "C1", "C2"],
                "color": "#eab308",
                "label": "TOP_PROBE(TTL=1)",
                "route_label": "C4 -> C1 -> C2",
                "msg": "C4 broadcasts TOP_PROBE outward West to C2 (via C1)",
                "payload": {
                    "msg": "TOP_PROBE",
                    "root_initiator": 4,
                    "vrf_score": 0.0412,
                    "ttl": 1,
                    "super_zone": "Z_TOP",
                },
            },
            {
                "packet_id": "top_probe_4_6_8",
                "type": "TOP_PROBE",
                "ttl": 1,
                "root": 4,
                "source": "C4",
                "target": "C8",
                "source_num": 4,
                "target_num": 8,
                "relay": "C6",
                "relay_num": 6,
                "path": [4, 6, 8],
                "path_nums": [4, 6, 8],
                "path_str": ["C4", "C6", "C8"],
                "color": "#eab308",
                "label": "TOP_PROBE(TTL=1)",
                "route_label": "C4 -> C6 -> C8",
                "msg": "C4 broadcasts TOP_PROBE outward East to C8 (via C6)",
                "payload": {
                    "msg": "TOP_PROBE",
                    "root_initiator": 4,
                    "vrf_score": 0.0412,
                    "ttl": 1,
                    "super_zone": "Z_TOP",
                },
            },
        ]

        packet_events = vrf_exchange_events + probe_events

        # Edges for Step 13: All physical links remain clean solid slate lines
        step13_edges = []
        for e in edges:
            e_copy = dict(e)
            e_copy["style"] = "solid"
            e_copy["line_color"] = "#64748b"
            e_copy["line_style"] = "solid"
            step13_edges.append(e_copy)

        terminal_logs = [
            "[STEP 13] Hierarchical Top-Level Zone Creation initialized (Figure 3(e)).",
            "[OVERLAY GRAPH] Base zone initiators form higher-level overlay graph G_init: V_init={C2, C4, C8}, E_init={(C2, C4), (C4, C8)}.",
            "[PHASE 1: VRF EXCHANGE] 1-hop VRF score exchange across overlay links:",
            "  - C2 -> C4: score=0.0837 (path [2, 1, 4]) | C4 -> C2: score=0.0412 (path [4, 1, 2])",
            "  - C8 -> C4: score=0.0275 (path [8, 6, 4]) | C4 -> C8: score=0.0412 (path [4, 6, 8])",
            "[PHASE 2: ELECTION] Node C4 elected Top-Level Super-Initiator 👑👑 (Central bridge interconnecting C2 and C8).",
            "[PHASE 3: SYMMETRICAL PROBING] Initiator C4 symmetrically broadcasts TOP_PROBE(TTL=1) outward:",
            "  - C4 -> C1 (gateway) -> C2 (West branch complete, accepted by C2)",
            "  - C4 -> C6 (gateway) -> C8 (East branch complete, accepted by C8)",
            "[PHASE 4: SUPER-ZONE FORMED] Top-Level Super-Zone Z_TOP established (Root: C4 👑👑, Member Initiators: [C2, C4, C8]).",
            "[SUPERVISORY PLANE] Hierarchical control plane active for global cluster catalog exchange in Step 14.",
        ]

        top_level_zone = {
            "id": "Z_TOP",
            "root_initiator": 4,
            "member_initiators": [2, 4, 8],
            "root_initiator_str": "C4",
            "member_initiators_str": ["C2", "C4", "C8"],
            "vrf_scores": {2: 0.0837, 4: 0.0412, 8: 0.0275},
            "winner_initiator": 4,
            "ttl": 1,
            "overlay_edges": [
                {"source": 4, "target": 2, "via": 1, "hop": 1, "path": [4, 1, 2]},
                {"source": 4, "target": 8, "via": 6, "hop": 1, "path": [4, 6, 8]},
            ],
            "score_exchanges": [
                {"type": "VRF_EXCHANGE", "score": 0.0837, "path": [2, 1, 4], "source": 2, "target": 4},
                {"type": "VRF_EXCHANGE", "score": 0.0275, "path": [8, 6, 4], "source": 8, "target": 4},
                {"type": "VRF_EXCHANGE", "score": 0.0412, "path": [4, 1, 2], "source": 4, "target": 2},
                {"type": "VRF_EXCHANGE", "score": 0.0412, "path": [4, 6, 8], "source": 4, "target": 8},
            ],
            "probe_broadcasts": [
                {"type": "TOP_PROBE", "ttl": 1, "root": 4, "path": [4, 1, 2], "target": 2},
                {"type": "TOP_PROBE", "ttl": 1, "root": 4, "path": [4, 6, 8], "target": 8},
            ],
        }

        return {
            "step": 13,
            "title": "Step 13: Hierarchical Top-Level Zone Creation (Figure 3(e))",
            "phase_badge": "ACTIVE PHASE: STEP 13: TOP-LEVEL INITIATOR ELECTION & SUPER-ZONE (C4 👑👑)",
            "description": "Initiators exchange VRF scores across overlay links. Central bridge C4 is elected Top-Level Initiator and symmetrically floods TOP_PROBE to C2 and C8.",
            "formula": "\\mathcal{G}_{\\text{init}} = \\{I_2 \\leftrightarrow I_4 \\leftrightarrow I_8\\}, \\quad I_{\\text{top}} = C_4, \\quad \\text{TOP\\_PROBE}(C_4, \\text{TTL}=1) \\to \\mathcal{Z}_{\\text{Top}}",
            "formula_desc": "Initiators exchange VRF scores across overlay links. Central bridge C4 is elected Top-Level Initiator and symmetrically floods TOP_PROBE to C2 and C8.",
            "nodes": step13_nodes,
            "edges": step13_edges,
            "overlay_topology": {
                "nodes": [2, 4, 8],
                "nodes_str": ["C2", "C4", "C8"],
                "edges": [
                    {"source": 4, "target": 2, "via": 1, "hop": 1, "path": [4, 1, 2]},
                    {"source": 4, "target": 8, "via": 6, "hop": 1, "path": [4, 6, 8]},
                ],
            },
            "top_level_zone": top_level_zone,
            "super_zone": top_level_zone,
            "packet_events": packet_events,
            "packet_exchanges": packet_events,
            "vrf_exchange_events": vrf_exchange_events,
            "probe_events": probe_events,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [2, 4, 8],
            "top_initiator": 4,
            "similarity_matrices": step12_data["similarity_matrices"],
            "all_clusters": step12_data["all_clusters"],
            "zones": {
                2: [1, 2, 3],
                4: [4, 5, 6, 7],
                8: [8, 9, 10],
            },
            "boundary_nodes": [1, 6],
            "agreed_global_p": 3,
            "target_p": 3,
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




