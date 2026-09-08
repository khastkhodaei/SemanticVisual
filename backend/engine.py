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
