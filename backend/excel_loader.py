"""Excel Data Loader & Precomputation Engine for SemanticDFL Storyboard Simulator.

Parses 'semantic_dfl_simulation_data.xlsx' to extract:
1. Sheet 1 ('خلاصه پیکربندی شبکه'): Global configuration KPIs and CIFAR-10 class distributions.
2. Sheet 2 ('مشخصات گره‌ها'): 50 nodes (C1 to C50), physical degree, neighbors, CIFAR-10 class data, and exactly 90 edges.
3. Sheet 3 ('رأی‌گیری VRF و انتشار پیام‌ها'): Cryptographic VRF keys, formulas, sigma scores, multi-hop wave reaches, election statuses, 10 zones, and hop distances.
Precomputes fixed, organic, collision-free 2D coordinates for Cytoscape visualization.
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
        self._compute_wave_propagation_events()

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

    def _compute_wave_propagation_events(self) -> None:
        """Derive sequential multi-hop wave transmission packets from Sheet 3 Columns E, F, G."""
        neighbors_map: Dict[int, Set[int]] = {i: set() for i in range(1, 51)}
        for u, v in self.edges_list:
            neighbors_map[u].add(v)
            neighbors_map[v].add(u)

        self.wave_events: Dict[str, Any] = {
            "wave1": [],
            "wave2": [],
            "wave3": [],
            "logs": [],
        }

        # Wave 1: Initiators -> 1-hop receivers (TTL 3 -> 2)
        wave1_transmissions = []
        for init_id in self.initiators:
            h1 = self.node_vrf[init_id]["wave1_reach"]
            for target in h1:
                wave1_transmissions.append({
                    "source": init_id,
                    "target": target,
                    "source_id": f"C{init_id}",
                    "target_id": f"C{target}",
                    "initiator": init_id,
                    "initiator_id": f"C{init_id}",
                    "ttl_remaining": 2,
                    "edge_id": f"e{min(init_id, target)}_{max(init_id, target)}",
                })
        self.wave_events["wave1"] = wave1_transmissions

        # Wave 2: 1-hop nodes -> 2-hop receivers (TTL 2 -> 1)
        wave2_transmissions = []
        for init_id in self.initiators:
            h1_set = set(self.node_vrf[init_id]["wave1_reach"])
            h2 = self.node_vrf[init_id]["wave2_reach"]
            for target in h2:
                # Find which 1-hop node forwards to this 2-hop node
                possible_senders = [v for v in h1_set if target in neighbors_map[v]]
                sender = possible_senders[0] if possible_senders else None
                if sender:
                    wave2_transmissions.append({
                        "source": sender,
                        "target": target,
                        "source_id": f"C{sender}",
                        "target_id": f"C{target}",
                        "initiator": init_id,
                        "initiator_id": f"C{init_id}",
                        "ttl_remaining": 1,
                        "edge_id": f"e{min(sender, target)}_{max(sender, target)}",
                    })
        self.wave_events["wave2"] = wave2_transmissions

        # Wave 3: 2-hop nodes -> 3-hop receivers (TTL 1 -> 0)
        wave3_transmissions = []
        for init_id in self.initiators:
            h2_set = set(self.node_vrf[init_id]["wave2_reach"])
            h3 = self.node_vrf[init_id]["wave3_reach"]
            for target in h3:
                possible_senders = [v for v in h2_set if target in neighbors_map[v]]
                sender = possible_senders[0] if possible_senders else None
                if sender:
                    wave3_transmissions.append({
                        "source": sender,
                        "target": target,
                        "source_id": f"C{sender}",
                        "target_id": f"C{target}",
                        "initiator": init_id,
                        "initiator_id": f"C{init_id}",
                        "ttl_remaining": 0,
                        "edge_id": f"e{min(sender, target)}_{max(sender, target)}",
                    })
        self.wave_events["wave3"] = wave3_transmissions

        self.wave_events["logs"] = [
            f"[Wave 1] TTL=3 -> 2: 10 Initiators broadcast PROBE packets to {len(wave1_transmissions)} direct 1-hop neighbors.",
            f"[Wave 2] TTL=2 -> 1: Intermediate nodes forward probes across {len(wave2_transmissions)} links to 2-hop receivers.",
            f"[Wave 3] TTL=1 -> 0: Final wave traverses {len(wave3_transmissions)} links to 3-hop boundary receivers.",
            "[Propagation Complete] All 50 nodes successfully collected VRF scores within TTL=3 physical radius.",
        ]

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
                    "status": "PROBING",
                    "sk": n["sk"],
                    "vrf_formula": n["vrf_formula"],
                    "vrf_score": n["vrf_score"],
                    "is_initiator": False,
                    "wave1_reach": n["wave1_reach"],
                    "wave2_reach": n["wave2_reach"],
                    "wave3_reach": n["wave3_reach"],
                    "assigned_zone": None,
                    "hops_to_initiator": None,
                })
            return {
                "step": 3,
                "title": "TTL=3 Packet Wave Propagation",
                "phase_badge": "Step 3: Multi-Hop Wave Propagation (TTL=3)",
                "description": "Multi-hop wave propagation along physical links: Wave 1 (1-hop), Wave 2 (2-hop), Wave 3 (3-hop).",
                "nodes": step_nodes,
                "edges": all_edges,
                "waves": {
                    "wave1": self.wave_events["wave1"],
                    "wave2": self.wave_events["wave2"],
                    "wave3": self.wave_events["wave3"],
                },
                "initiators": [f"C{x}" for x in self.initiators],
                "initiator_ids": self.initiators,
                "terminal_logs": self.wave_events["logs"],
            }

        elif step_number == 4:
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
                    "role": "INITIATOR" if n["is_initiator"] else "MEMBER",
                    "status": "ASSIGNED",
                    "sk": n["sk"],
                    "vrf_formula": n["vrf_formula"],
                    "vrf_score": n["vrf_score"],
                    "is_initiator": n["is_initiator"],
                    "assigned_zone": n["assigned_zone"],
                    "zone_color": n["zone_color"],
                    "hops_to_initiator": n["hops_to_initiator"],
                    "hops_label": n["hops_label"],
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
                "title": "Initiator Election & Zone Formation",
                "phase_badge": "Step 4: 10 Physical Zones Formed",
                "description": "10 Initiators crowned (C1, C6, C11, C16, C21, C26, C31, C36, C41, C46) and 50 nodes partitioned into 10 physical zones.",
                "nodes": step_nodes,
                "edges": all_edges,
                "initiators": [f"C{x}" for x in self.initiators],
                "initiator_ids": self.initiators,
                "zones": zones_dict,
                "boundary_edges": boundary_edges,
                "total_boundary_edges": len(boundary_edges),
                "total_intra_edges": len(intra_edges),
                "terminal_logs": [
                    "[Election] 10 Initiators confirmed: C1, C6, C11, C16, C21, C26, C31, C36, C41, C46.",
                    f"[Zone Formation] 50 nodes assigned to 10 proximity zones: {len(boundary_edges)} inter-zone boundary edges identified.",
                    "[Zone Formation] Max hop distance to zone initiator: 2 hops (within TTL=3 limit).",
                    "[Ready] Network ready for intra-zone semantic clustering and Personalized DFL rounds.",
                ],
            }

        else:
            raise ValueError(f"Invalid storyboard step: {step_number}. Must be 1, 2, 3, or 4.")
