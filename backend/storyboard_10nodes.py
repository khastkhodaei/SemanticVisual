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
        # Step 3: Local VRF Generation & 1-Hop Neighbor Score Exchange
        step3_nodes = []
        for n in nodes:
            nid = n["id"]
            n_copy = dict(n)
            vrf = STORYBOARD_10_VRF_SCORES[nid]
            nbrs = n["neighbors"]
            neighbor_scores = {nb: STORYBOARD_10_VRF_SCORES[nb] for nb in nbrs}
            neighbor_scores_str = {f"C{nb}": STORYBOARD_10_VRF_SCORES[nb] for nb in nbrs}
            neighbor_scoreboard = [
                {
                    "neighbor_id": nb,
                    "label": f"C{nb}",
                    "vrf_score": STORYBOARD_10_VRF_SCORES[nb],
                }
                for nb in nbrs
            ]

            n_copy["status"] = "NOT_ASSIGNED"
            n_copy["role"] = "CLIENT"
            n_copy["is_initiator"] = False
            n_copy["zone_id"] = None
            n_copy["is_boundary"] = False
            n_copy["vrf_score"] = vrf
            n_copy["neighbor_scores"] = neighbor_scores
            n_copy["neighbor_scores_str"] = neighbor_scores_str
            n_copy["neighbor_scoreboard"] = neighbor_scoreboard
            step3_nodes.append(n_copy)

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

        terminal_logs = [
            f"[VRF GENERATION] Node C{nid} computed local VRF seed score: {STORYBOARD_10_VRF_SCORES[nid]}"
            for nid in range(1, 11)
        ]
        unique_undirected = sorted({(min(e['source_num'], e['target_num']), max(e['source_num'], e['target_num'])) for e in edges})
        terminal_logs.extend([
            f"[VRF EXCHANGE] Node C{u} <-> Node C{v} exchanged 1-hop VRF scores ({STORYBOARD_10_VRF_SCORES[u]} vs {STORYBOARD_10_VRF_SCORES[v]})"
            for u, v in unique_undirected
        ])
        terminal_logs.append("[STATUS] All 10 nodes completed 1-hop score exchange. Local neighborhood scoreboards populated.")

        return {
            "step": 3,
            "title": "Step 3: VRF Generation & 1-Hop Neighbor Score Exchange",
            "phase_badge": "Step 3: VRF Exchange",
            "description": "Each peer calculates its local VRF score and exchanges it with direct 1-hop physical neighbors.",
            "formula": "\\sigma_p = \\text{VRF}_{sk_p}(\\text{seed}_{e-1}), \\quad \\text{Exchange with } q \\in \\mathcal{N}_1(p)",
            "formula_desc": "Each peer calculates its local VRF score and exchanges it with direct 1-hop physical neighbors.",
            "nodes": step3_nodes,
            "edges": edges,
            "adjacency_list": {i: STORYBOARD_10_ADJACENCY[i] for i in range(1, 11)},
            "coords": {i: {"x": STORYBOARD_10_COORDINATES[i][0], "y": STORYBOARD_10_COORDINATES[i][1]} for i in range(1, 11)},
            "total_nodes": 10,
            "total_edges": 18,
            "unique_edges": len(edges),
            "active_leaders": [],
            "packet_exchanges": packet_exchanges,
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
