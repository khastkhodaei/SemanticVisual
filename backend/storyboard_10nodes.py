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

# Balanced, readable planar 2D coordinates for Cytoscape viewport
STORYBOARD_10_COORDINATES: Dict[int, Tuple[float, float]] = {
    1: (130.0, 160.0),
    2: (130.0, 370.0),
    4: (290.0, 160.0),
    3: (290.0, 370.0),
    7: (470.0, 110.0),
    6: (490.0, 265.0),
    5: (470.0, 420.0),
    9: (670.0, 140.0),
    8: (710.0, 265.0),
    10: (670.0, 390.0),
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
            "label": f"C{nid} {dom['icon']}",
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
