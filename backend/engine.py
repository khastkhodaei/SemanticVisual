"""Core Simulation Engine for SemanticDFL Protocol.

Implements Random Geometric Graph (RGG) physical topology generation,
connectivity guarantees, and 50-dimensional heterogeneous semantic weight modeling.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.spatial.distance import cdist


SEMANTIC_CLASSES = {
    0: "Cat_Classifier",
    1: "Car_Classifier",
    2: "Audio_Classifier",
}

BOOST_SLICES = {
    0: (0, 18),
    1: (16, 34),
    2: (32, 50),
}


class SemanticDFLEngine:
    """Engine responsible for physical topology generation and semantic weight modeling."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    def generate_node_weights(self, category: int) -> List[float]:
        """Generate a 50-dimensional parameter vector with category-specific slice boost.

        - Baseline noise: N(0.05, 0.02) across all 50 dimensions.
        - Category boost: N(0.80, 0.12) injected into slice [start, end).
        """
        dim = 50
        # Baseline noise: N(0.05, 0.02)
        weights = self.rng.normal(loc=0.05, scale=0.02, size=dim)

        # Slice-correlated parameter boost: N(0.80, 0.12)
        start, end = BOOST_SLICES[category]
        boost = self.rng.normal(loc=0.80, scale=0.12, size=end - start)
        weights[start:end] = boost

        return [round(float(w), 6) for w in weights]

    def generate_topology(
        self,
        N: int,
        D_limit: float = 0.35,
        maintain_connectivity: bool = True,
    ) -> Dict[str, Any]:
        """Generate Random Geometric Graph (RGG) physical topology and node models.

        Args:
            N: Number of nodes to generate.
            D_limit: Normalized distance threshold for communication (distance / 900.0 <= D_limit).
            maintain_connectivity: Whether to detect singletons and guarantee degree >= 1.

        Returns:
            Dictionary containing:
                - nodes: list of node objects
                - edges: list of undirected edges with Euclidean and normalized distances
                - adjacency_list: dict mapping node ID to list of neighbor IDs
                - metadata: topology parameters and generation stats
        """
        if N <= 0:
            raise ValueError("Number of nodes N must be greater than 0.")
        if D_limit <= 0.0:
            raise ValueError("D_limit must be strictly positive.")

        # Coordinate space: x in [50, 850], y in [50, 550]
        x_coords = self.rng.uniform(50.0, 850.0, size=N)
        y_coords = self.rng.uniform(50.0, 550.0, size=N)
        coords = np.column_stack((x_coords, y_coords))

        # Balanced distribution across 3 latent semantic categories
        categories = [i % 3 for i in range(N)]
        self.rng.shuffle(categories)

        # Pairwise Euclidean distances
        dist_matrix = cdist(coords, coords, metric="euclidean")
        norm_dist_matrix = dist_matrix / 900.0

        # Adjacency tracking
        adjacency: Dict[int, List[int]] = {i: [] for i in range(N)}
        edges_set = set()
        edges_list: List[Dict[str, Any]] = []

        # Connect pairs where norm_dist <= D_limit
        for i in range(N):
            for j in range(i + 1, N):
                if norm_dist_matrix[i, j] <= D_limit:
                    adjacency[i].append(j)
                    adjacency[j].append(i)
                    edge_key = (i, j)
                    edges_set.add(edge_key)
                    edges_list.append({
                        "source": i,
                        "target": j,
                        "distance": round(float(dist_matrix[i, j]), 4),
                        "distance_norm": round(float(norm_dist_matrix[i, j]), 6),
                    })

        # Connectivity Guarantee: Detect isolated/singleton nodes
        if maintain_connectivity and N > 1:
            for i in range(N):
                if len(adjacency[i]) == 0:
                    # Find nearest Euclidean neighbor
                    other_dists = dist_matrix[i].copy()
                    other_dists[i] = np.inf
                    nearest_neighbor = int(np.argmin(other_dists))
                    nearest_dist = float(other_dists[nearest_neighbor])
                    nearest_norm = nearest_dist / 900.0

                    # If nearest neighbor distance exceeds D_limit, nudge node i along the
                    # line towards nearest_neighbor to strictly respect D_limit
                    if nearest_norm > D_limit:
                        max_euclid = D_limit * 900.0 * 0.98  # Safe margin within D_limit
                        vec = coords[nearest_neighbor] - coords[i]
                        unit_vec = vec / (np.linalg.norm(vec) + 1e-9)
                        coords[i] = coords[nearest_neighbor] - unit_vec * max_euclid
                        # Clamp within bounding box [50, 850] x [50, 550]
                        coords[i, 0] = np.clip(coords[i, 0], 50.0, 850.0)
                        coords[i, 1] = np.clip(coords[i, 1], 50.0, 550.0)
                        # Recompute actual distance
                        new_dist = float(np.linalg.norm(coords[i] - coords[nearest_neighbor]))
                        nearest_dist = new_dist
                        nearest_norm = new_dist / 900.0

                    # Add edge
                    u, v = min(i, nearest_neighbor), max(i, nearest_neighbor)
                    if (u, v) not in edges_set:
                        edges_set.add((u, v))
                        adjacency[i].append(nearest_neighbor)
                        adjacency[nearest_neighbor].append(i)
                        edges_list.append({
                            "source": u,
                            "target": v,
                            "distance": round(nearest_dist, 4),
                            "distance_norm": round(nearest_norm, 6),
                        })

        # Sort neighbor lists
        for i in adjacency:
            adjacency[i].sort()

        # Build node objects
        nodes: List[Dict[str, Any]] = []
        for i in range(N):
            cat = categories[i]
            weights = self.generate_node_weights(cat)
            vrf_score = float(self.rng.uniform(0.0, 1.0))

            nodes.append({
                "id": i,
                "coords": {
                    "x": round(float(coords[i, 0]), 2),
                    "y": round(float(coords[i, 1]), 2),
                },
                "category": cat,
                "category_name": SEMANTIC_CLASSES[cat],
                "weights": weights,
                "vrf_score": round(vrf_score, 6),
                "role": "CLIENT",
                "state": "NOT_ASSIGNED",
                "zone_id": None,
                "alive": True,
                "degree": len(adjacency[i]),
            })

        return {
            "nodes": nodes,
            "edges": edges_list,
            "adjacency_list": adjacency,
            "metadata": {
                "num_nodes": N,
                "num_edges": len(edges_list),
                "d_limit": D_limit,
                "avg_degree": round(float(2 * len(edges_list) / N), 2) if N > 0 else 0.0,
            },
        }

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Compute Cosine Similarity between two parameter vectors."""
        a = np.asarray(v1, dtype=np.float64)
        b = np.asarray(v2, dtype=np.float64)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def get_r_hop_neighborhood(
        self,
        node_id: int,
        adjacency_list: Dict[int, List[int]],
        r_hops: int,
    ) -> List[int]:
        """Find all nodes within r_hops physical distance using BFS (including node_id)."""
        visited = {node_id: 0}
        queue = [node_id]

        while queue:
            curr = queue.pop(0)
            curr_dist = visited[curr]
            if curr_dist < r_hops:
                for neighbor in adjacency_list.get(curr, []):
                    if neighbor not in visited:
                        visited[neighbor] = curr_dist + 1
                        queue.append(neighbor)

        return list(visited.keys())

    def run_vrf_election(
        self,
        nodes: List[Dict[str, Any]],
        adjacency_list: Dict[int, List[int]],
        r_hops: int = 2,
    ) -> Dict[str, Any]:
        """Execute VRF Leader Election within R-hop physical neighborhoods.

        Each node p checks its R-hop neighborhood N_R(p).
        Finds m_p = min_{q in N_R(p)} (vrf_score_q, id_q).
        If (vrf_score_p, id_p) == m_p, node p elects itself as INITIATOR.
        """
        node_map = {n["id"]: n for n in nodes}
        initiators = []
        logs: List[Dict[str, str]] = []

        for node in nodes:
            nid = node["id"]
            n_score = node["vrf_score"]
            neighborhood = self.get_r_hop_neighborhood(nid, adjacency_list, r_hops)

            # Find minimum tuple (vrf_score, id) in neighborhood
            is_initiator = True
            min_tuple = (n_score, nid)
            min_peer = nid

            for peer_id in neighborhood:
                if peer_id == nid:
                    continue
                peer_tuple = (node_map[peer_id]["vrf_score"], peer_id)
                if peer_tuple < min_tuple:
                    min_tuple = peer_tuple
                    min_peer = peer_id
                    is_initiator = False

            if is_initiator:
                node["role"] = "INITIATOR"
                node["state"] = "ASSIGNED"
                node["zone_id"] = nid
                initiators.append(nid)
                logs.append({
                    "level": "INFO",
                    "message": f"Node {nid} elected as INITIATOR (VRF={n_score:.4f}) over {len(neighborhood)} peers in {r_hops}-hop neighborhood.",
                })
            else:
                node["role"] = "CLIENT"
                node["state"] = "NOT_ASSIGNED"
                node["zone_id"] = None

        logs.append({
            "level": "SUCCESS",
            "message": f"VRF Election complete: {len(initiators)} INITIATORS elected out of {len(nodes)} nodes (r_hops={r_hops}).",
        })

        return {
            "initiators": initiators,
            "nodes": nodes,
            "logs": logs,
        }

    def run_zone_formation(
        self,
        nodes: List[Dict[str, Any]],
        adjacency_list: Dict[int, List[int]],
        r_hops: int = 2,
        max_zone_size: int = 10,
    ) -> Dict[str, Any]:
        """Simulate TTL-bounded first-wins zone probing with deterministic splitting.

        Implements Algorithm 3 (ZONEFORMATION PROTOCOL):
        1. Initiators broadcast PROBE packets with TTL = R.
        2. First-wins: Unassigned nodes adopt the first initiator whose probe arrives.
        3. Boundary detection: Cross-zone probe arrivals trigger boundary interface alerts.
        4. Deterministic splitting: Zones exceeding S_Z delegate overflow to next lowest VRF node.
        """
        node_map = {n["id"]: n for n in nodes}
        packet_hops: List[Dict[str, Any]] = []
        boundaries: List[Dict[str, Any]] = []
        logs: List[Dict[str, str]] = []

        # Identify initiators
        initiators = [n["id"] for n in nodes if n.get("role") == "INITIATOR"]
        if not initiators:
            # Fallback if election not run yet: elect lowest VRF node as initial initiator
            min_node = min(nodes, key=lambda x: (x["vrf_score"], x["id"]))
            min_node["role"] = "INITIATOR"
            min_node["state"] = "ASSIGNED"
            min_node["zone_id"] = min_node["id"]
            initiators = [min_node["id"]]

        # Track hop distance from initiator for split sorting
        hop_from_initiator: Dict[int, int] = {init_id: 0 for init_id in initiators}
        seen_boundaries = set()

        # Packet format: (initiator_id, sender_id, receiver_id, ttl)
        current_queue: List[Tuple[int, int, int, int]] = []
        for init_id in sorted(initiators):
            for neighbor in adjacency_list.get(init_id, []):
                current_queue.append((init_id, init_id, neighbor, r_hops))

        round_num = 0
        while current_queue and round_num < r_hops + 2:
            round_num += 1
            next_queue: List[Tuple[int, int, int, int]] = []

            # Sort queue for deterministic execution
            current_queue.sort(key=lambda x: (x[0], x[1], x[2]))

            for init_id, sender, receiver, ttl in current_queue:
                recv_node = node_map[receiver]

                # Case 1: Unassigned node adopts initiator (First-Wins)
                if recv_node["state"] == "NOT_ASSIGNED":
                    recv_node["state"] = "ASSIGNED"
                    recv_node["zone_id"] = init_id
                    hop_from_initiator[receiver] = r_hops - ttl + 1
                    packet_hops.append({
                        "round": round_num,
                        "initiator": init_id,
                        "sender": sender,
                        "receiver": receiver,
                        "ttl": ttl,
                        "action": "ADOPTED",
                    })

                    # Forward probe to unvisited physical neighbors if TTL > 1
                    if ttl > 1:
                        for nxt in adjacency_list.get(receiver, []):
                            if nxt != sender and node_map[nxt]["zone_id"] != init_id:
                                next_queue.append((init_id, receiver, nxt, ttl - 1))

                # Case 2: Already assigned node receives probe from another zone -> Boundary Detection
                elif recv_node["zone_id"] != init_id:
                    packet_hops.append({
                        "round": round_num,
                        "initiator": init_id,
                        "sender": sender,
                        "receiver": receiver,
                        "ttl": ttl,
                        "action": "BOUNDARY",
                    })
                    z_a = min(recv_node["zone_id"], init_id)
                    z_b = max(recv_node["zone_id"], init_id)
                    b_key = (z_a, z_b, min(sender, receiver), max(sender, receiver))
                    if b_key not in seen_boundaries:
                        seen_boundaries.add(b_key)
                        boundaries.append({
                            "zone_a": z_a,
                            "zone_b": z_b,
                            "node_a": sender,
                            "node_b": receiver,
                        })

                # Case 3: Redundant probe inside same zone
                else:
                    packet_hops.append({
                        "round": round_num,
                        "initiator": init_id,
                        "sender": sender,
                        "receiver": receiver,
                        "ttl": ttl,
                        "action": "DROPPED_SAME_ZONE",
                    })

            current_queue = next_queue

        logs.append({
            "level": "INFO",
            "message": f"TTL probe propagation finished in {round_num} rounds with {len(packet_hops)} packet transmissions.",
        })
        logs.append({
            "level": "INFO",
            "message": f"Detected {len(boundaries)} inter-zone boundary interfaces.",
        })

        # Ensure reachability: If any node remains unassigned (outside R hops),
        # attach to nearest assigned neighbor or form isolated zone
        unassigned = [n for n in nodes if n["state"] == "NOT_ASSIGNED"]
        for un in unassigned:
            uid = un["id"]
            # Check if any neighbor is assigned
            assigned_neighbors = [nb for nb in adjacency_list.get(uid, []) if node_map[nb]["state"] == "ASSIGNED"]
            if assigned_neighbors:
                target_zone = node_map[assigned_neighbors[0]]["zone_id"]
                un["state"] = "ASSIGNED"
                un["zone_id"] = target_zone
                hop_from_initiator[uid] = hop_from_initiator.get(assigned_neighbors[0], 1) + 1
            else:
                un["state"] = "ASSIGNED"
                un["role"] = "INITIATOR"
                un["zone_id"] = uid
                hop_from_initiator[uid] = 0

        # Step 4: Deterministic Splitting (S_Z Cap)
        # Verify no zone exceeds max_zone_size
        split_occurred = True
        split_count = 0

        while split_occurred:
            split_occurred = False
            # Group nodes by current zone_id
            zones_map: Dict[int, List[Dict[str, Any]]] = {}
            for n in nodes:
                zid = n["zone_id"]
                zones_map.setdefault(zid, []).append(n)

            for zid, members in list(zones_map.items()):
                if len(members) > max_zone_size:
                    split_occurred = True
                    split_count += 1

                    # Initiator of this zone
                    curr_leader = zid

                    # Sort members by (hop distance to initiator, Euclidean distance to initiator)
                    leader_coords = np.array([node_map[curr_leader]["coords"]["x"], node_map[curr_leader]["coords"]["y"]])

                    def member_distance_key(m):
                        m_coords = np.array([m["coords"]["x"], m["coords"]["y"]])
                        euclid = float(np.linalg.norm(m_coords - leader_coords))
                        hops = hop_from_initiator.get(m["id"], 999)
                        return (hops, euclid)

                    sorted_members = sorted(members, key=member_distance_key)

                    # Initiator retains closest max_zone_size members
                    # Overflow subset is delegated to node with lowest VRF score in overflow
                    overflow = sorted_members[max_zone_size:]
                    new_leader = min(overflow, key=lambda m: (m["vrf_score"], m["id"]))
                    new_zone_id = new_leader["id"]

                    new_leader["role"] = "INITIATOR"
                    for m in overflow:
                        m["zone_id"] = new_zone_id
                        hop_from_initiator[m["id"]] = 1 if m["id"] != new_zone_id else 0

                    logs.append({
                        "level": "WARN",
                        "message": f"Zone {zid} cardinality {len(members)} exceeded S_Z={max_zone_size}. Split off {len(overflow)} nodes to new secondary Zone {new_zone_id}.",
                    })

        # Final zone summary & Post-split boundary interface registration
        final_zones: Dict[int, List[int]] = {}
        for n in nodes:
            final_zones.setdefault(n["zone_id"], []).append(n["id"])

        # Detect/finalize all boundary interfaces between distinct zones over physical edges
        for u, neighbors in adjacency_list.items():
            z_u = node_map[u]["zone_id"]
            for v in neighbors:
                z_v = node_map[v]["zone_id"]
                if z_u != z_v:
                    z_a, z_b = min(z_u, z_v), max(z_u, z_v)
                    n_a, n_b = min(u, v), max(u, v)
                    b_key = (z_a, z_b, n_a, n_b)
                    if b_key not in seen_boundaries:
                        seen_boundaries.add(b_key)
                        boundaries.append({
                            "zone_a": z_a,
                            "zone_b": z_b,
                            "node_a": n_a,
                            "node_b": n_b,
                        })

        logs.append({
            "level": "SUCCESS",
            "message": f"Zone formation finalized: {len(final_zones)} zones formed (max size: {max(len(m) for m in final_zones.values())}, S_Z={max_zone_size}, {len(boundaries)} total boundary interfaces).",
        })

        return {
            "nodes": nodes,
            "zones": final_zones,
            "boundaries": boundaries,
            "packet_hops": packet_hops,
            "logs": logs,
        }


    def calculate_global_p_consensus(
        self,
        nodes: List[Dict[str, Any]],
        theta: float = 0.70,
        q: float = 0.20,
    ) -> Dict[str, Any]:
        """Calculate Global-P Signature Cardinality Consensus via Binary Search.

        Simulates Algorithm 1 (BinarySearchForSignatureCardinality):
        1. For each node i, sort coordinates by absolute weight magnitude: |w_{i, r}|.
        2. Binary search over P in [1, M] (M=50) to find minimum P_i^{min} where:
           Cosine(w_i, w_i^{[P]}) = sqrt(sum_{m=1}^P w_{i, j_m}^2) / ||w_i||_2 >= theta.
        3. Compute Network Consensus: Global P = Quantile_q({P_i^{min}}).
        """
        local_p: Dict[int, int] = {}
        directional_similarities: Dict[int, float] = {}
        dim = 50
        logs: List[Dict[str, str]] = []

        for node in nodes:
            nid = node["id"]
            w = np.asarray(node["weights"], dtype=np.float64)
            full_norm = float(np.linalg.norm(w))

            if full_norm == 0.0:
                local_p[nid] = 1
                directional_similarities[nid] = 1.0
                continue

            # Sort indices descending by absolute magnitude
            sorted_indices = np.argsort(-np.abs(w))
            squared_magnitudes = w[sorted_indices] ** 2
            cum_squared = np.cumsum(squared_magnitudes)

            # Binary search in [1, dim]
            low = 1
            high = dim
            best_p = dim
            best_sim = 1.0

            while low <= high:
                mid = (low + high) // 2
                retained_norm = np.sqrt(cum_squared[mid - 1])
                cos_sim = float(retained_norm / full_norm)

                if cos_sim >= theta - 1e-9:
                    best_p = mid
                    best_sim = cos_sim
                    high = mid - 1
                else:
                    low = mid + 1

            local_p[nid] = best_p
            directional_similarities[nid] = round(best_sim, 4)

        p_values = [local_p[n["id"]] for n in nodes]
        exact_quantile = float(np.quantile(p_values, q))
        global_p = int(np.round(exact_quantile))

        logs.append({
            "level": "INFO",
            "message": f"Local P computed for {len(nodes)} nodes (range: [{min(p_values)}, {max(p_values)}], mean: {np.mean(p_values):.2f}).",
        })
        logs.append({
            "level": "SUCCESS",
            "message": f"Global-P consensus reached: Global P = {global_p} (exact {q}-quantile: {exact_quantile:.2f}, theta: {theta}).",
        })

        return {
            "global_p": global_p,
            "exact_quantile": exact_quantile,
            "local_p": local_p,
            "directional_similarities": directional_similarities,
            "theta": theta,
            "q": q,
            "logs": logs,
        }

