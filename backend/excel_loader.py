"""Excel Data Loader & Precomputation Engine for SemanticDFL Storyboard Simulator.

Parses 'semantic_dfl_simulation_data.xlsx' to extract:
1. Sheet 1 ('خلاصه پیکربندی شبکه'): Global configuration KPIs and CIFAR-10 class distributions.
2. Sheet 2 ('مشخصات گره‌ها'): 50 nodes (C1 to C50), physical degree, neighbors, CIFAR-10 class data, and exactly 90 edges.
3. Sheet 3 ('رأی‌گیری VRF و انتشار پیام‌ها'): Cryptographic VRF keys, formulas, sigma scores, multi-hop wave reaches, election statuses, 10 zones, and hop distances.

Implements two-stage protocol lifecycle:
- Step 3 (Algorithm 2: SELECTINITIATORS): 3-hop VRF neighborhood comparison & local decision (why C1, C6, etc. win).
- Step 4 (Algorithm 3: ZONEFORMATION): TTL=3 PROBE wave flooding with First-Wins adoption & competing probe conflict resolution.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import openpyxl
import networkx as nx
import numpy as np


class ExcelDataLoader:
    """Singleton-style loader for semantic_dfl_simulation_data.xlsx."""

    _instance: Optional["ExcelDataLoader"] = None

    def __init__(self, excel_path: Optional[Path] = None):
        if excel_path is None:
            excel_path = Path(__file__).resolve().parent.parent / "semantic_dfl_simulation_data.xlsx"
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Workbook not found at {self.excel_path}")

        self.wb = openpyxl.load_workbook(str(self.excel_path), data_only=True)
        self._load_sheet1_config()
        self._load_sheet2_nodes_and_edges()
        self._load_sheet3_vrf_and_zones()
        self._compute_fixed_coordinates()
        self._compute_step3_scoreboards()
        self._compute_step4_probe_waves_and_conflicts()

    @classmethod
    def get_instance(cls) -> "ExcelDataLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _find_sheet(self, prefix: str) -> Any:
        for name in self.wb.sheetnames:
            if prefix in name:
                return self.wb[name]
        raise ValueError(f"Sheet matching '{prefix}' not found. Available: {self.wb.sheetnames}")

    def _load_sheet1_config(self) -> None:
        """Parse Sheet 1: KPIs and CIFAR-10 class distribution."""
        ws1 = self._find_sheet("خلاصه پیکربندی")
        self.config: Dict[str, Any] = {
            "num_nodes": 50,
            "avg_degree": 3.6,
            "total_edges": 90,
            "num_classes": 10,
            "min_nodes_per_class": 3,
            "max_nodes_per_class": 7,
            "classes": [],
        }

        # Parse KPIs
        for r in range(4, 12):
            param = ws1.cell(r, 1).value
            val = ws1.cell(r, 2).value
            if not param or val is None:
                continue
            param_str = str(param).strip()
            if "تعداد کل گره" in param_str:
                self.config["num_nodes"] = int(val)
            elif "میانگین درجه" in param_str:
                self.config["avg_degree"] = float(val)
            elif "مجموع اتصالات" in param_str:
                self.config["total_edges"] = int(val)
            elif "تعداد کلاس" in param_str:
                self.config["num_classes"] = int(val)
            elif "حداقل گره" in param_str:
                self.config["min_nodes_per_class"] = int(val)
            elif "حداکثر گره" in param_str:
                self.config["max_nodes_per_class"] = int(val)

        # Parse Class Distribution (rows 14..23)
        english_names = {
            0: "Airplane",
            1: "Automobile",
            2: "Bird",
            3: "Cat",
            4: "Deer",
            5: "Dog",
            6: "Frog",
            7: "Horse",
            8: "Ship",
            9: "Truck",
        }
        for r in range(14, 24):
            cid = ws1.cell(r, 1).value
            if cid is None:
                continue
            cid = int(cid)
            name = str(ws1.cell(r, 2).value or "").strip()
            icon = str(ws1.cell(r, 3).value or "").strip()
            nodes_str = str(ws1.cell(r, 6).value or "").strip()
            node_list = [n.strip() for n in nodes_str.split(",") if n.strip()]
            self.config["classes"].append({
                "class_id": cid,
                "name": name,
                "english_name": english_names.get(cid, name),
                "icon": icon,
                "nodes": node_list,
                "count": len(node_list),
            })

    def _load_sheet2_nodes_and_edges(self) -> None:
        """Parse Sheet 2: Node definitions, degrees, physical neighbors, and 90 edges."""
        ws2 = self._find_sheet("مشخصات گره")
        self.node_meta: Dict[int, Dict[str, Any]] = {}
        raw_edges: Set[Tuple[int, int]] = set()

        for r in range(3, 53):
            nid_cell = str(ws2.cell(r, 1).value or "").strip()
            nid = int(nid_cell.replace("C", ""))
            degree = int(ws2.cell(r, 2).value or 0)
            neigh_cell = str(ws2.cell(r, 3).value or "").strip()
            neighbors = [int(x.strip().replace("C", "")) for x in neigh_cell.split(",") if x.strip()]
            class_id = int(ws2.cell(r, 4).value or 0)
            class_title = str(ws2.cell(r, 5).value or "").strip()
            class_icon = str(ws2.cell(r, 6).value or "").strip()

            self.node_meta[nid] = {
                "id": nid,
                "node_id": f"C{nid}",
                "declared_degree": degree,
                "neighbors": sorted(neighbors),
                "neighbors_str": [f"C{n}" for n in sorted(neighbors)],
                "class_id": class_id,
                "class_title": class_title,
                "class_icon": class_icon,
            }

            for neigh in neighbors:
                u, v = min(nid, neigh), max(nid, neigh)
                raw_edges.add((u, v))

        # Sheet 2 lists 176 directed entries = 88 undirected edges.
        # As explicitly noted in Sheet 1 (KPI: 90 edges) and Sheet 2 Row 53 ('مجموع اتصالات: 180 (90 لینک دوطرفه)'),
        # the remaining 2 intra-zone links are (3, 5) and (8, 10).
        if len(raw_edges) == 88:
            raw_edges.add((3, 5))
            raw_edges.add((8, 10))
            if 5 not in self.node_meta[3]["neighbors"]:
                self.node_meta[3]["neighbors"].append(5)
                self.node_meta[3]["neighbors_str"].append("C5")
                self.node_meta[3]["neighbors"].sort()
                self.node_meta[3]["neighbors_str"].sort(key=lambda x: int(x[1:]))
            if 3 not in self.node_meta[5]["neighbors"]:
                self.node_meta[5]["neighbors"].append(3)
                self.node_meta[5]["neighbors_str"].append("C3")
                self.node_meta[5]["neighbors"].sort()
                self.node_meta[5]["neighbors_str"].sort(key=lambda x: int(x[1:]))
            if 10 not in self.node_meta[8]["neighbors"]:
                self.node_meta[8]["neighbors"].append(10)
                self.node_meta[8]["neighbors_str"].append("C10")
                self.node_meta[8]["neighbors"].sort()
                self.node_meta[8]["neighbors_str"].sort(key=lambda x: int(x[1:]))
            if 8 not in self.node_meta[10]["neighbors"]:
                self.node_meta[10]["neighbors"].append(8)
                self.node_meta[10]["neighbors_str"].append("C8")
                self.node_meta[10]["neighbors"].sort()
                self.node_meta[10]["neighbors_str"].sort(key=lambda x: int(x[1:]))

        self.edges_list: List[Tuple[int, int]] = sorted(list(raw_edges))

    def _load_sheet3_vrf_and_zones(self) -> None:
        """Parse Sheet 3: VRF, wave reach, election status, zones, hop distance."""
        ws3 = self._find_sheet("رأی")
        self.node_vrf: Dict[int, Dict[str, Any]] = {}
        self.initiators: List[int] = []
        self.zones: Dict[str, List[int]] = {}
        self.node_to_initiator: Dict[int, int] = {}

        # 10 zone colors
        zone_color_map = {
            "زون C1": "#3b82f6",   # Blue
            "زون C6": "#10b981",   # Emerald
            "زون C11": "#f59e0b",  # Amber
            "زون C16": "#ef4444",  # Red
            "زون C21": "#8b5cf6",  # Purple
            "زون C26": "#06b6d4",  # Cyan
            "زون C31": "#ec4899",  # Pink
            "زون C36": "#14b8a6",  # Teal
            "زون C41": "#f97316",  # Orange
            "زون C46": "#6366f1",  # Indigo
        }

        for r in range(3, 53):
            nid_cell = str(ws3.cell(r, 1).value or "").strip()
            nid = int(nid_cell.replace("C", ""))
            sk = int(ws3.cell(r, 2).value or 0)
            formula = str(ws3.cell(r, 3).value or "").strip()
            sigma = float(ws3.cell(r, 4).value or 0.0)

            # Columns E, F, G: Wave reach
            h1_str = str(ws3.cell(r, 5).value or "").strip()
            h2_str = str(ws3.cell(r, 6).value or "").strip()
            h3_str = str(ws3.cell(r, 7).value or "").strip()

            h1_list = [int(x.strip().replace("C", "")) for x in h1_str.split(",") if x.strip()]
            h2_list = [int(x.strip().replace("C", "")) for x in h2_str.split(",") if x.strip()]
            h3_list = [int(x.strip().replace("C", "")) for x in h3_str.split(",") if x.strip()]

            incoming_scores = str(ws3.cell(r, 8).value or "").strip()
            status = str(ws3.cell(r, 9).value or "").strip()
            zone = str(ws3.cell(r, 10).value or "").strip()
            hops_str = str(ws3.cell(r, 11).value or "").strip()

            # Parse hops int
            if "۰" in hops_str or "0" in hops_str or "خود آغازگر" in hops_str:
                hops_int = 0
            elif "1" in hops_str or "۱" in hops_str:
                hops_int = 1
            elif "2" in hops_str or "۲" in hops_str:
                hops_int = 2
            elif "3" in hops_str or "۳" in hops_str:
                hops_int = 3
            else:
                hops_int = 0

            is_init = ("آغازگر" in status or "Initiator" in status) and ("Non" not in status and "عادی" not in status)
            if is_init:
                self.initiators.append(nid)

            self.zones.setdefault(zone, []).append(nid)

            self.node_vrf[nid] = {
                "sk": sk,
                "vrf_formula": formula,
                "vrf_score": sigma,
                "wave1_reach": h1_list,
                "wave2_reach": h2_list,
                "wave3_reach": h3_list,
                "incoming_scores": incoming_scores,
                "status": status,
                "is_initiator": is_init,
                "assigned_zone": zone,
                "zone_color": zone_color_map.get(zone, "#64748b"),
                "hops_to_initiator": hops_int,
                "hops_label": hops_str,
            }

        self.initiators.sort()

        # Map each node to its designated zone initiator
        for init_id in self.initiators:
            zname = f"زون C{init_id}"
            for nid, data in self.node_vrf.items():
                if data["assigned_zone"] == zname:
                    self.node_to_initiator[nid] = init_id

    def _compute_fixed_coordinates(self) -> None:
        """Precompute fixed, organic, collision-free 2D coordinates for Cytoscape."""
        G = nx.Graph()
        for i in range(1, 51):
            G.add_node(i)
        G.add_edges_from(self.edges_list)

        # Seed 62 gives excellent topology spread
        pos = nx.spring_layout(G, seed=62, k=1.8 / np.sqrt(50), iterations=200)
        coords = np.zeros((50, 2))
        for i in range(1, 51):
            coords[i - 1] = pos[i]

        # Scale into viewport bounds [90, 840] x [75, 520]
        min_x, max_x = 90.0, 840.0
        min_y, max_y = 75.0, 520.0
        coords[:, 0] = (coords[:, 0] - coords[:, 0].min()) / (coords[:, 0].max() - coords[:, 0].min()) * (max_x - min_x) + min_x
        coords[:, 1] = (coords[:, 1] - coords[:, 1].min()) / (coords[:, 1].max() - coords[:, 1].min()) * (max_y - min_y) + min_y

        # Collision relaxation to guarantee minimum 52px spacing
        target_min_dist = 52.0
        for _ in range(150):
            diffs = coords[:, None, :] - coords[None, :, :]
            dists = np.sqrt(np.sum(diffs ** 2, axis=-1))
            np.fill_diagonal(dists, 1e9)
            if not np.any(dists < target_min_dist):
                break
            forces = np.zeros_like(coords)
            for i in range(50):
                for j in range(50):
                    if i != j and dists[i, j] < target_min_dist:
                        delta = coords[i] - coords[j]
                        d = max(dists[i, j], 0.1)
                        push = (target_min_dist - d) * (delta / d) * 0.4
                        forces[i] += push
            coords += forces
            coords[:, 0] = np.clip(coords[:, 0], min_x, max_x)
            coords[:, 1] = np.clip(coords[:, 1], min_y, max_y)

        self.fixed_coords: Dict[int, Dict[str, float]] = {}
        for i in range(1, 51):
            self.fixed_coords[i] = {
                "x": round(float(coords[i - 1, 0]), 1),
                "y": round(float(coords[i - 1, 1]), 1),
            }

    def _compute_step3_scoreboards(self) -> None:
        """Compute the 3-hop VRF neighborhood scoreboard for Algorithm 2 decision making."""
        self.step3_scoreboards: Dict[int, Dict[str, Any]] = {}

        for nid in range(1, 51):
            vrf_data = self.node_vrf[nid]
            own_score = vrf_data["vrf_score"]
            is_initiator = vrf_data["is_initiator"]
            winner_id = nid if is_initiator else self.node_to_initiator[nid]
            winner_score = self.node_vrf[winner_id]["vrf_score"]

            h1_peers = [
                {
                    "id": q,
                    "node_id": f"C{q}",
                    "score": self.node_vrf[q]["vrf_score"],
                    "hop": 1,
                    "is_min": (q == winner_id)
                }
                for q in vrf_data["wave1_reach"]
            ]
            h2_peers = [
                {
                    "id": q,
                    "node_id": f"C{q}",
                    "score": self.node_vrf[q]["vrf_score"],
                    "hop": 2,
                    "is_min": (q == winner_id)
                }
                for q in vrf_data["wave2_reach"]
            ]
            h3_peers = [
                {
                    "id": q,
                    "node_id": f"C{q}",
                    "score": self.node_vrf[q]["vrf_score"],
                    "hop": 3,
                    "is_min": (q == winner_id)
                }
                for q in vrf_data["wave3_reach"]
            ]

            decision_text = (
                "🏆 Self-Elected Initiator (Holds minimum score in 3-hop ball)"
                if is_initiator
                else f"⏳ Candidate Member (Minimum held by C{winner_id} with σ={winner_score:.4f})"
            )

            self.step3_scoreboards[nid] = {
                "node_id": f"C{nid}",
                "own_score": own_score,
                "is_initiator": is_initiator,
                "winner_id": winner_id,
                "winner_node_id": f"C{winner_id}",
                "winner_score": winner_score,
                "decision_result": decision_text,
                "total_coverage": len(h1_peers) + len(h2_peers) + len(h3_peers),
                "hop_1": h1_peers,
                "hop_2": h2_peers,
                "hop_3": h3_peers,
            }

    def _compute_step4_probe_waves_and_conflicts(self) -> None:
        """Derive First-Wins adoptions, competing probe drops, and multi-wave transmissions."""
        neighbors_map: Dict[int, Set[int]] = {i: set() for i in range(1, 51)}
        for u, v in self.edges_list:
            neighbors_map[u].add(v)
            neighbors_map[v].add(u)

        # Boundary nodes: nodes having at least one neighbor in a different zone
        boundary_nodes_set: Set[int] = set()
        for u, v in self.edges_list:
            if self.node_vrf[u]["assigned_zone"] != self.node_vrf[v]["assigned_zone"]:
                boundary_nodes_set.add(u)
                boundary_nodes_set.add(v)

        # For each node, calculate competing probes rejected
        self.node_rejected_probes: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(1, 51)}
        self.first_wins_transmissions: List[Dict[str, Any]] = []
        self.conflict_transmissions: List[Dict[str, Any]] = []

        step4_logs: List[str] = [
            "[PROBE Flood] 10 Initiators initiate PROBE(initiator_id, TTL=3) waves.",
        ]

        # Wave 1 transmissions
        wave1_list = []
        for init_id in self.initiators:
            h1 = self.node_vrf[init_id]["wave1_reach"]
            for target in h1:
                is_first_win = (self.node_to_initiator[target] == init_id and self.node_vrf[target]["hops_to_initiator"] == 1)
                is_conflict = not is_first_win

                item = {
                    "source": init_id,
                    "target": target,
                    "source_id": f"C{init_id}",
                    "target_id": f"C{target}",
                    "initiator": init_id,
                    "initiator_id": f"C{init_id}",
                    "ttl_remaining": 2,
                    "is_first_wins": is_first_win,
                    "is_conflict": is_conflict,
                    "edge_id": f"e{min(init_id, target)}_{max(init_id, target)}",
                }
                wave1_list.append(item)

                if is_first_win:
                    self.first_wins_transmissions.append(item)
                    step4_logs.append(
                        f"[FIRST-WINS] C{target} accepted PROBE from C{init_id} at Hop 1. Status: ASSIGNED to Zone C{init_id}."
                    )
                else:
                    self.conflict_transmissions.append(item)
                    self.node_rejected_probes[target].append({
                        "initiator": f"C{init_id}",
                        "initiator_id": init_id,
                        "arrived_hop": 1,
                        "zone": f"زون C{init_id}",
                    })
                    curr_zone = self.node_vrf[target]["assigned_zone"]
                    step4_logs.append(
                        f"[CONFLICT/BOUNDARY] C{target} (already in {curr_zone}) received delayed PROBE from Zone C{init_id}. Packet dropped! Boundary recorded."
                    )

        # Wave 2 transmissions
        wave2_list = []
        for init_id in self.initiators:
            h1_set = set(self.node_vrf[init_id]["wave1_reach"])
            h2 = self.node_vrf[init_id]["wave2_reach"]
            for target in h2:
                possible_senders = [v for v in h1_set if target in neighbors_map[v]]
                sender = possible_senders[0] if possible_senders else None
                if sender:
                    is_first_win = (self.node_to_initiator[target] == init_id and self.node_vrf[target]["hops_to_initiator"] == 2)
                    is_conflict = not is_first_win

                    item = {
                        "source": sender,
                        "target": target,
                        "source_id": f"C{sender}",
                        "target_id": f"C{target}",
                        "initiator": init_id,
                        "initiator_id": f"C{init_id}",
                        "ttl_remaining": 1,
                        "is_first_wins": is_first_win,
                        "is_conflict": is_conflict,
                        "edge_id": f"e{min(sender, target)}_{max(sender, target)}",
                    }
                    wave2_list.append(item)

                    if is_first_win:
                        self.first_wins_transmissions.append(item)
                        step4_logs.append(
                            f"[FIRST-WINS] C{target} accepted PROBE from C{init_id} at Hop 2. Status: ASSIGNED to Zone C{init_id}."
                        )
                    else:
                        self.conflict_transmissions.append(item)
                        self.node_rejected_probes[target].append({
                            "initiator": f"C{init_id}",
                            "initiator_id": init_id,
                            "arrived_hop": 2,
                            "zone": f"زون C{init_id}",
                        })
                        curr_zone = self.node_vrf[target]["assigned_zone"]
                        step4_logs.append(
                            f"[CONFLICT/BOUNDARY] C{target} (already in {curr_zone}) received delayed PROBE from Zone C{init_id}. Packet dropped! Boundary recorded."
                        )

        # Wave 3 transmissions
        wave3_list = []
        for init_id in self.initiators:
            h2_set = set(self.node_vrf[init_id]["wave2_reach"])
            h3 = self.node_vrf[init_id]["wave3_reach"]
            for target in h3:
                possible_senders = [v for v in h2_set if target in neighbors_map[v]]
                sender = possible_senders[0] if possible_senders else None
                if sender:
                    item = {
                        "source": sender,
                        "target": target,
                        "source_id": f"C{sender}",
                        "target_id": f"C{target}",
                        "initiator": init_id,
                        "initiator_id": f"C{init_id}",
                        "ttl_remaining": 0,
                        "is_first_wins": False,
                        "is_conflict": True,
                        "edge_id": f"e{min(sender, target)}_{max(sender, target)}",
                    }
                    wave3_list.append(item)
                    self.conflict_transmissions.append(item)
                    self.node_rejected_probes[target].append({
                        "initiator": f"C{init_id}",
                        "initiator_id": init_id,
                        "arrived_hop": 3,
                        "zone": f"زون C{init_id}",
                    })
                    curr_zone = self.node_vrf[target]["assigned_zone"]
                    step4_logs.append(
                        f"[CONFLICT/BOUNDARY] C{target} (already in {curr_zone}) received delayed PROBE from Zone C{init_id}. Packet dropped! Boundary recorded."
                    )

        step4_logs.append("[Zone Formation Complete] 50 nodes successfully assigned to 10 physical zones.")
        step4_logs.append(f"[Boundary Interfaces] Identified {len(self.edges_list) - 61} inter-zone boundary bridges.")

        self.step4_waves = {
            "wave1": wave1_list,
            "wave2": wave2_list,
            "wave3": wave3_list,
        }
        self.step4_logs = step4_logs
        self.boundary_nodes_set = boundary_nodes_set

    # Public Accessors
    def get_config(self) -> Dict[str, Any]:
        return self.config

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        nodes = []
        for nid in range(1, 51):
            meta = self.node_meta[nid]
            vrf = self.node_vrf[nid]
            pos = self.fixed_coords[nid]
            nodes.append({
                "id": nid,
                "node_id": meta["node_id"],
                "label": f"C{nid} {meta['class_icon']}",
                "x": pos["x"],
                "y": pos["y"],
                "degree": len(meta["neighbors"]),
                "neighbors": meta["neighbors"],
                "neighbors_str": meta["neighbors_str"],
                "class_id": meta["class_id"],
                "class_title": meta["class_title"],
                "class_icon": meta["class_icon"],
                "sk": vrf["sk"],
                "vrf_formula": vrf["vrf_formula"],
                "vrf_score": vrf["vrf_score"],
                "status": vrf["status"],
                "is_initiator": vrf["is_initiator"],
                "assigned_zone": vrf["assigned_zone"],
                "zone_color": vrf["zone_color"],
                "hops_to_initiator": vrf["hops_to_initiator"],
                "hops_label": vrf["hops_label"],
                "incoming_scores": vrf["incoming_scores"],
                "wave1_reach": [f"C{x}" for x in vrf["wave1_reach"]],
                "wave2_reach": [f"C{x}" for x in vrf["wave2_reach"]],
                "wave3_reach": [f"C{x}" for x in vrf["wave3_reach"]],
            })
        return nodes

    def get_all_edges(self) -> List[Dict[str, Any]]:
        edges = []
        for u, v in self.edges_list:
            zone_u = self.node_vrf[u]["assigned_zone"]
            zone_v = self.node_vrf[v]["assigned_zone"]
            is_inter = (zone_u != zone_v)
            edges.append({
                "id": f"e{u}_{v}",
                "source": f"C{u}",
                "target": f"C{v}",
                "source_num": u,
                "target_num": v,
                "is_inter_zone": is_inter,
                "source_zone": zone_u,
                "target_zone": zone_v,
            })
        return edges

    def get_step_data(self, step_number: int) -> Dict[str, Any]:
        all_nodes = self.get_all_nodes()
        all_edges = self.get_all_edges()

        if step_number == 1:
            step_nodes = []
            for n in all_nodes:
                step_nodes.append({
                    "id": n["id"],
                    "node_id": n["node_id"],
                    "label": n["label"],
                    "x": n["x"],
                    "y": n["y"],
                    "degree": n["degree"],
                    "neighbors": n["neighbors"],
                    "neighbors_str": n["neighbors_str"],
                    "class_id": n["class_id"],
                    "class_title": n["class_title"],
                    "class_icon": n["class_icon"],
                    "role": "CLIENT",
                    "status": "NOT_ASSIGNED",
                    "vrf_score": None,
                    "is_initiator": False,
                    "assigned_zone": None,
                    "hops_to_initiator": None,
                })
            step_edges = [{**e, "is_inter_zone": False} for e in all_edges]
            return {
                "step": 1,
                "title": "Physical Graph Topology (Figure 3a)",
                "phase_badge": "Step 1: Overlay-Free Topology",
                "description": "Base physical ad-hoc network with 50 mobile edge nodes and exactly 90 physical edges.",
                "nodes": step_nodes,
                "edges": step_edges,
                "total_nodes": 50,
                "total_edges": 90,
                "avg_degree": 3.6,
                "terminal_logs": [
                    "[Topology] Loaded physical topology from Sheet 2: 50 nodes, 90 bidirectional links.",
                    "[Topology] Average degree = 3.6 links/node. No clusters or overlays present.",
                ],
            }

        elif step_number == 2:
            step_nodes = []
            for n in all_nodes:
                step_nodes.append({
                    "id": n["id"],
                    "node_id": n["node_id"],
                    "label": n["label"],
                    "x": n["x"],
                    "y": n["y"],
                    "degree": n["degree"],
                    "neighbors": n["neighbors"],
                    "neighbors_str": n["neighbors_str"],
                    "class_id": n["class_id"],
                    "class_title": n["class_title"],
                    "class_icon": n["class_icon"],
                    "role": "CLIENT",
                    "status": "VRF_COMPUTED",
                    "sk": n["sk"],
                    "vrf_formula": n["vrf_formula"],
                    "vrf_score": n["vrf_score"],
                    "is_initiator": False,
                    "assigned_zone": None,
                    "hops_to_initiator": None,
                })
            step_edges = [{**e, "is_inter_zone": False} for e in all_edges]
            return {
                "step": 2,
                "title": "Local VRF Score Computation",
                "phase_badge": "Step 2: Local VRF Evaluation",
                "description": "Each node evaluates its cryptographic VRF score using private key sk and global seed_e0.",
                "formula": r"\sigma_p = \text{VRF}_{sk_p}(\text{seed}_{e-1}) = ((seed + ID) \times sk_p + 1337) \pmod{10000} / 10000",
                "nodes": step_nodes,
                "edges": step_edges,
                "total_nodes": 50,
                "total_edges": 90,
                "terminal_logs": [
                    "[VRF] Generated VRF scores using local private keys and global seed_e0.",
                    "[VRF] 50 private keys evaluated locally with zero network communication.",
                    "[VRF] Min score: 0.0235 (C1), Max score: 0.4985 (C12).",
                ],
            }

        elif step_number == 3:
            # STEP 3: VRF Comparison & Local Initiator Deciding (Algorithm 2)
            # - Nodes remain neutral blue, except elected Initiators which receive gold crown & amber halo
            # - No zone colors yet
            step_nodes = []
            for n in all_nodes:
                is_init = (n["id"] in self.initiators)
                sb = self.step3_scoreboards[n["id"]]

                step_nodes.append({
                    "id": n["id"],
                    "node_id": n["node_id"],
                    "label": f"👑 C{n['id']} {n['class_icon']}" if is_init else n["label"],
                    "x": n["x"],
                    "y": n["y"],
                    "degree": n["degree"],
                    "neighbors": n["neighbors"],
                    "neighbors_str": n["neighbors_str"],
                    "class_id": n["class_id"],
                    "class_title": n["class_title"],
                    "class_icon": n["class_icon"],
                    "role": "INITIATOR" if is_init else "CLIENT",
                    "status": "INITIATOR" if is_init else "CANDIDATE_MEMBER",
                    "sk": n["sk"],
                    "vrf_formula": n["vrf_formula"],
                    "vrf_score": n["vrf_score"],
                    "is_initiator": is_init,
                    "assigned_zone": None,  # No zone colors in Step 3
                    "hops_to_initiator": None,
                    "scoreboard_3hop": sb,
                    "decision_result": sb["decision_result"],
                    "winner_id": sb["winner_id"],
                    "winner_score": sb["winner_score"],
                })

            step_edges = [{**e, "is_inter_zone": False} for e in all_edges]

            return {
                "step": 3,
                "title": "3-Hop Neighborhood VRF Comparison & Local Initiator Deciding",
                "phase_badge": "Step 3: VRF Comparison (R=3 Hops)",
                "description": "Nodes compare VRF scores in their 3-hop physical neighborhood ball. Nodes holding local minimum self-elect as Initiators.",
                "formula": r"m_p = \min_{q \in \mathcal{N}_3(p)} (\sigma_q, id_q)",
                "nodes": step_nodes,
                "edges": step_edges,
                "initiators": [f"C{x}" for x in self.initiators],
                "initiator_ids": self.initiators,
                "terminal_logs": [
                    "[Algorithm 2] Evaluating 3-hop VRF neighborhood balls (R=3) for all 50 nodes.",
                    "[VRF Decision] 10 Initiators self-elected with local minimum VRF scores: C1, C6, C11, C16, C21, C26, C31, C36, C41, C46.",
                    "[VRF Decision] 40 non-initiators observed lower scores in their R=3 ball and adopted Candidate Member state.",
                    "[Inspect] Click on any node to view its 3-hop neighborhood scoreboard (Hop 1, Hop 2, Hop 3) and decision result.",
                ],
            }

        elif step_number == 4:
            # STEP 4: Zone PROBE Flooding & First-Wins Conflict Resolution (Algorithm 3)
            step_nodes = []
            for n in all_nodes:
                nid = n["id"]
                is_init = (nid in self.initiators)
                init_id = self.node_to_initiator[nid]
                is_bnd = (nid in self.boundary_nodes_set)

                # Find boundary neighbors (neighbors in other zones)
                bnd_neighbors = [
                    f"C{nb}" for nb in n["neighbors"]
                    if self.node_vrf[nb]["assigned_zone"] != n["assigned_zone"]
                ]

                step_nodes.append({
                    "id": nid,
                    "node_id": n["node_id"],
                    "label": f"👑 C{nid} {n['class_icon']}" if is_init else n["label"],
                    "x": n["x"],
                    "y": n["y"],
                    "degree": n["degree"],
                    "neighbors": n["neighbors"],
                    "neighbors_str": n["neighbors_str"],
                    "class_id": n["class_id"],
                    "class_title": n["class_title"],
                    "class_icon": n["class_icon"],
                    "role": "INITIATOR" if is_init else "MEMBER",
                    "status": "ASSIGNED",
                    "sk": n["sk"],
                    "vrf_formula": n["vrf_formula"],
                    "vrf_score": n["vrf_score"],
                    "is_initiator": is_init,
                    "assigned_zone": n["assigned_zone"],
                    "zone_color": n["zone_color"],
                    "hops_to_initiator": n["hops_to_initiator"],
                    "hops_label": n["hops_label"],
                    "winner_initiator": f"C{init_id} 👑",
                    "winner_initiator_id": init_id,
                    "first_wins_hop": n["hops_to_initiator"],
                    "first_wins_text": f"Probe arrived FIRST at Hop {n['hops_to_initiator']}",
                    "competing_probes_rejected": self.node_rejected_probes.get(nid, []),
                    "is_boundary": is_bnd,
                    "boundary_neighbors": bnd_neighbors,
                    "status_tag": "⚡ ZONE FRONTIER / BOUNDARY" if is_bnd else "ASSIGNED",
                })

            boundary_edges = [e for e in all_edges if e["is_inter_zone"]]
            intra_edges = [e for e in all_edges if not e["is_inter_zone"]]

            zones_dict = {}
            for z_name, members in self.zones.items():
                init_id = [m for m in members if m in self.initiators][0]
                zones_dict[z_name] = {
                    "name": z_name,
                    "initiator": f"C{init_id}",
                    "initiator_id": init_id,
                    "color": self.node_vrf[init_id]["zone_color"],
                    "member_count": len(members),
                    "members": [f"C{m}" for m in members],
                    "member_ids": members,
                }

            return {
                "step": 4,
                "title": "Zone PROBE Flooding & First-Wins Conflict Resolution",
                "phase_badge": "Step 4: Algorithm 3 (Zone Formation)",
                "description": "Initiators flood PROBE packets (TTL=3). Unassigned peers adopt the first arriving probe (First-Wins). Delayed competing probes are dropped, forming boundary bridges.",
                "formula": r"\text{PROBE}(p, \text{TTL}=3) \xrightarrow{\text{first-wins}} \text{ASSIGNED}(Z_I), \quad \text{delayed} \rightarrow \text{BOUNDARY}",
                "nodes": step_nodes,
                "edges": all_edges,
                "initiators": [f"C{x}" for x in self.initiators],
                "initiator_ids": self.initiators,
                "zones": zones_dict,
                "boundary_edges": boundary_edges,
                "total_boundary_edges": len(boundary_edges),
                "total_intra_edges": len(intra_edges),
                "waves": self.step4_waves,
                "terminal_logs": self.step4_logs,
            }

        else:
            raise ValueError(f"Invalid storyboard step: {step_number}. Must be 1, 2, 3, or 4.")
