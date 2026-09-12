"""FastAPI Service for SemanticDFL Protocol Simulator.

Provides REST endpoints for topology initialization, health monitoring,
and in-memory session state management.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.engine import SemanticDFLEngine, load_step1_data
from backend.storyboard_10nodes import (
    get_10node_config,
    get_10node_nodes,
    get_10node_edges,
    get_10node_step_data,
    TOTAL_STEPS,
)

TOTAL_STEPS: int = 14



class SimulationInitRequest(BaseModel):
    benchmark: str = Field(default="Non-IID 10-Class Storyboard", description="Homogeneous model family and Non-IID benchmark task")
    num_nodes: int = Field(default=50, ge=2, le=500, description="Number of participating nodes")
    d_limit: float = Field(default=0.35, gt=0.0, le=1.0, description="Physical Euclidean distance communication cutoff / 900")
    r_hops: int = Field(default=2, ge=1, le=10, description="R-hop neighborhood exploration limit")
    max_zone_size: int = Field(default=10, ge=2, le=100, description="Maximum number of nodes in a semantic zone")
    theta: float = Field(default=0.70, ge=0.0, le=1.0, description="Semantic similarity clustering threshold")
    q: float = Field(default=0.20, ge=0.0, le=1.0, description="Byzantine / Sybil adversary fraction")



class SimulationLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class SessionStore:
    """Thread-safe in-memory session manager for simulation instances."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._sessions[session_id] = data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


# Initialize FastAPI app
app = FastAPI(
    title="SemanticDFL Protocol Simulator API",
    description="Backend service for simulating Decentralized Federated Learning with Semantic Clustering (ACM 2026)",
    version="1.0.0",
)

# Enable CORS for cross-origin frontend dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory session store
session_store = SessionStore()


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend service liveness."""
    return {
        "status": "ok",
        "service": "SemanticDFL Protocol Simulator",
        "version": "1.0.0",
        "active_sessions": len(session_store.list_sessions()),
    }


@app.get("/api/v1/storyboard/config", tags=["Storyboard"])
def get_storyboard_config():
    """Returns global network configuration and CIFAR-10 class metrics for 10-node setup."""
    d1 = load_step1_data()
    return {
        "num_nodes": 10,
        "avg_degree": 3.4,
        "total_edges": 18,
        "unique_edges": len(d1["edges"]),
        "num_classes": len(d1["classes"]),
        "classes": d1["classes"],
    }


@app.get("/api/v1/storyboard/nodes", tags=["Storyboard"])
def get_storyboard_nodes():
    """Returns 10 nodes with fixed coordinates, CIFAR-10 data, and physical links."""
    d1 = load_step1_data()
    return {
        "nodes": d1["nodes"],
        "edges": d1["edges"],
        "total_nodes": 10,
        "total_edges": 18,
        "unique_edges": len(d1["edges"]),
    }


@app.get("/api/v1/storyboard/step/1", tags=["Storyboard"])
def get_storyboard_step_1():
    """Returns the 10 nodes, 18 edges, dataset classes, and step description."""
    return load_step1_data()


@app.get("/api/v1/storyboard/step/5", tags=["Storyboard"])
def get_storyboard_step_5():
    """Returns deterministic data for Storyboard Step 5 (Zone Creation via PROBE Flooding TTL=1)."""
    return get_10node_step_data(5)


@app.post("/api/v1/storyboard/step/5", tags=["Storyboard"])
def post_storyboard_step_5():
    """Execute / return deterministic data for Storyboard Step 5."""
    return get_10node_step_data(5)


@app.get("/api/v1/storyboard/step/6", tags=["Storyboard"])
def get_storyboard_step_6():
    """Returns deterministic data for Storyboard Step 6 (Official Zone Formation & Boundary Discovery)."""
    return get_10node_step_data(6)


@app.post("/api/v1/storyboard/step/6", tags=["Storyboard"])
def post_storyboard_step_6():
    """Execute / return deterministic data for Storyboard Step 6."""
    return get_10node_step_data(6)


@app.get("/api/v1/storyboard/step/7", tags=["Storyboard"])
def get_storyboard_step_7():
    """Returns deterministic data for Storyboard Step 7 (Initiator P_min Query Request)."""
    return get_10node_step_data(7)


@app.post("/api/v1/storyboard/step/7", tags=["Storyboard"])
def post_storyboard_step_7():
    """Execute / return deterministic data for Storyboard Step 7."""
    return get_10node_step_data(7)


@app.get("/api/v1/storyboard/step/8", tags=["Storyboard"])
def get_storyboard_step_8():
    """Returns deterministic data for Storyboard Step 8 (Local Binary Search & P_min Reporting)."""
    return get_10node_step_data(8)


@app.post("/api/v1/storyboard/step/8", tags=["Storyboard"])
def post_storyboard_step_8():
    """Execute / return deterministic data for Storyboard Step 8."""
    return get_10node_step_data(8)


@app.get("/api/v1/storyboard/step/9", tags=["Storyboard"])
def get_storyboard_step_9():
    """Returns deterministic data for Storyboard Step 9 (Inter-Initiator P_min Exchange & Global Consensus)."""
    return get_10node_step_data(9)


@app.post("/api/v1/storyboard/step/9", tags=["Storyboard"])
def post_storyboard_step_9():
    """Execute / return deterministic data for Storyboard Step 9."""
    return get_10node_step_data(9)


@app.get("/api/v1/storyboard/step/10", tags=["Storyboard"])
def get_storyboard_step_10():
    """Returns deterministic data for Storyboard Step 10 (Initiator Extraction Order Broadcast)."""
    return get_10node_step_data(10)


@app.post("/api/v1/storyboard/step/10", tags=["Storyboard"])
def post_storyboard_step_10():
    """Execute / return deterministic data for Storyboard Step 10."""
    return get_10node_step_data(10)


@app.get("/api/v1/storyboard/step/11", tags=["Storyboard"])
def get_storyboard_step_11():
    """Returns deterministic data for Storyboard Step 11 (Top-P Signature Extraction)."""
    return get_10node_step_data(11)


@app.post("/api/v1/storyboard/step/11", tags=["Storyboard"])
def post_storyboard_step_11():
    """Execute / return deterministic data for Storyboard Step 11."""
    return get_10node_step_data(11)


@app.get("/api/v1/storyboard/step/12", tags=["Storyboard"])
def get_storyboard_step_12():
    """Returns deterministic data for Storyboard Step 12 (Intra-Zone Semantic Clustering)."""
    return get_10node_step_data(12)


@app.post("/api/v1/storyboard/step/12", tags=["Storyboard"])
def post_storyboard_step_12():
    """Execute / return deterministic data for Storyboard Step 12."""
    return get_10node_step_data(12)


@app.get("/api/v1/storyboard/step/13", tags=["Storyboard"])
def get_storyboard_step_13():
    """Returns deterministic data for Storyboard Step 13 (Intra-Zone Cluster Exemplar Designation & Profile Assignment)."""
    return get_10node_step_data(13)


@app.post("/api/v1/storyboard/step/13", tags=["Storyboard"])
def post_storyboard_step_13():
    """Execute / return deterministic data for Storyboard Step 13."""
    return get_10node_step_data(13)


@app.get("/api/v1/storyboard/step/14", tags=["Storyboard"])
def get_storyboard_step_14():
    """Returns deterministic data for Storyboard Step 14 (Hierarchical Top-Level Zone Creation)."""
    return get_10node_step_data(14)


@app.post("/api/v1/storyboard/step/14", tags=["Storyboard"])
def post_storyboard_step_14():
    """Execute / return deterministic data for Storyboard Step 14."""
    return get_10node_step_data(14)


@app.get("/api/v1/storyboard/step/{step_number}", tags=["Storyboard"])
def get_storyboard_step(step_number: int):
    """Returns deterministic data for Storyboard Step (1 to 14) for 10-node simulation."""
    if step_number == 1:
        return load_step1_data()
    if step_number not in list(range(1, TOTAL_STEPS + 1)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step number {step_number}. Must be between 1 and {TOTAL_STEPS}.",
        )
    return get_10node_step_data(step_number)


@app.post("/api/v1/storyboard/step/{step_number}", tags=["Storyboard"])
def post_storyboard_step(step_number: int):
    """Execute / return deterministic data for Storyboard Step (1 to 14) for 10-node simulation."""
    if step_number == 1:
        return load_step1_data()
    if step_number not in list(range(1, TOTAL_STEPS + 1)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step number {step_number}. Must be between 1 and {TOTAL_STEPS}.",
        )
    return get_10node_step_data(step_number)



@app.post("/api/v1/init", status_code=status.HTTP_200_OK, tags=["Simulation"])
def init_simulation(req: SimulationInitRequest):
    """Initialize a new simulation session with RGG topology and heterogeneous weights."""
    try:
        session_id = str(uuid.uuid4())
        logs: List[Dict[str, str]] = []

        def log_event(level: str, msg: str):
            logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": msg,
            })

        log_event("INFO", f"Initializing simulation session {session_id} with Benchmark='{req.benchmark}', N={req.num_nodes}, D_limit={req.d_limit}")

        engine = SemanticDFLEngine()
        topology = engine.generate_topology(
            N=req.num_nodes,
            D_limit=req.d_limit,
            maintain_connectivity=True,
            benchmark=req.benchmark,
        )

        num_edges = len(topology["edges"])
        avg_deg = topology["metadata"]["avg_degree"]
        model_arch = topology["metadata"]["model_architecture"]
        log_event("INFO", f"RGG topology generated: {req.num_nodes} nodes, {num_edges} physical edges (avg degree: {avg_deg})")

        log_event("INFO", f"Model Family: {model_arch} | Non-IID Skew: 3 partition clusters | Benchmark: {req.benchmark}")
        log_event("INFO", f"Configured parameters: r_hops={req.r_hops}, max_zone_size={req.max_zone_size}, theta={req.theta}, q={req.q}")



        session_data = {
            "session_id": session_id,
            "params": req.model_dump(),
            "nodes": topology["nodes"],
            "edges": topology["edges"],
            "adjacency_list": topology["adjacency_list"],
            "metadata": topology["metadata"],
            "logs": logs,
        }

        # Store in session state
        session_store.create_session(session_id, session_data)
        log_event("SUCCESS", "Simulation state successfully stored in session manager.")

        return {
            "session_id": session_id,
            "params": req.model_dump(),
            "nodes": topology["nodes"],
            "edges": topology["edges"],
            "adjacency_list": topology["adjacency_list"],
            "metadata": topology["metadata"],
            "logs": logs,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize simulation: {str(e)}",
        )


class VRFComputeStepRequest(BaseModel):
    session_id: str


@app.post("/api/v1/step/vrf-compute", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_vrf_compute(req: VRFComputeStepRequest):
    """Execute Step 2: Local VRF score calculation without neighbor exchange or leader election."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    result = engine.compute_local_vrf(nodes=session["nodes"])

    session["nodes"] = result["nodes"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "nodes": result["nodes"],
        "logs": result["logs"],
    }


class VRFStepRequest(BaseModel):
    session_id: str
    r_hops: Optional[int] = Field(default=None, ge=1, le=10)


class VRFExchangeStepRequest(BaseModel):
    session_id: str
    r_hops: Optional[int] = Field(default=3, ge=1, le=10)


@app.post("/api/v1/step/vrf-exchange", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_vrf_exchange(req: VRFExchangeStepRequest):
    """Execute Step 3: R-Hop Neighborhood VRF Exchange & Initiator Selection."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    r_hops = req.r_hops if req.r_hops is not None else session["params"].get("r_hops", 3)

    result = engine.run_vrf_exchange(
        nodes=session["nodes"],
        adjacency_list=session["adjacency_list"],
        r_hops=r_hops,
    )

    session["nodes"] = result["nodes"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "initiators": result["initiators"],
        "nodes": result["nodes"],
        "logs": result["logs"],
    }


@app.post("/api/v1/step/vrf", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_vrf_election(req: VRFStepRequest):
    """Legacy endpoint for Step 3 VRF leader election."""
    return step_vrf_exchange(VRFExchangeStepRequest(session_id=req.session_id, r_hops=req.r_hops))


class ZoneProbingStepRequest(BaseModel):
    session_id: str
    ttl: Optional[int] = Field(default=3, ge=1, le=10)
    max_zone_size: Optional[int] = Field(default=8, ge=2, le=100)


class ZonesStepRequest(BaseModel):
    session_id: str
    r_hops: Optional[int] = Field(default=None, ge=1, le=10)
    max_zone_size: Optional[int] = Field(default=None, ge=2, le=100)


class GlobalPStepRequest(BaseModel):
    session_id: str
    theta: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    q: Optional[float] = Field(default=None, ge=0.0, le=1.0)


@app.post("/api/v1/step/zone-probing", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_zone_probing(req: ZoneProbingStepRequest):
    """Execute Step 4: TTL=3 Zone Formation (Algorithm 3 from ACM 2026 paper)."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    ttl = req.ttl if req.ttl is not None else 3
    max_zone_size = req.max_zone_size if req.max_zone_size is not None else 8

    result = engine.run_zone_probing(
        nodes=session["nodes"],
        adjacency_list=session["adjacency_list"],
        ttl=ttl,
        max_zone_size=max_zone_size,
    )

    session["nodes"] = result["nodes"]
    session["zones"] = result["zones"]
    session["boundary_edges"] = result["boundary_edges"]
    session["boundaries"] = result["boundaries"]
    session["packet_hops"] = result["packet_hops"]
    session["packet_wave_events"] = result["packet_wave_events"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "zones": result["zones"],
        "boundary_edges": result["boundary_edges"],
        "boundaries": result["boundaries"],
        "packet_hops": result["packet_hops"],
        "packet_wave_events": result["packet_wave_events"],
        "nodes": result["nodes"],
        "logs": result["logs"],
    }


@app.post("/api/v1/step/zones", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_zone_formation(req: ZonesStepRequest):
    """Execute TTL-bounded zone probing and deterministic splitting step (legacy route)."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    r_hops = req.r_hops if req.r_hops is not None else session["params"].get("r_hops", 2)
    max_zone_size = req.max_zone_size if req.max_zone_size is not None else session["params"].get("max_zone_size", 10)

    result = engine.run_zone_probing(
        nodes=session["nodes"],
        adjacency_list=session["adjacency_list"],
        ttl=r_hops,
        max_zone_size=max_zone_size,
    )

    session["nodes"] = result["nodes"]
    session["zones"] = result["zones"]
    session["boundary_edges"] = result["boundary_edges"]
    session["boundaries"] = result["boundaries"]
    session["packet_hops"] = result["packet_hops"]
    session["packet_wave_events"] = result["packet_wave_events"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "zones": result["zones"],
        "boundary_edges": result["boundary_edges"],
        "boundaries": result["boundaries"],
        "packet_hops": result["packet_hops"],
        "packet_wave_events": result["packet_wave_events"],
        "nodes": result["nodes"],
        "logs": result["logs"],
    }


@app.post("/api/v1/step/global-p", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_global_p_consensus(req: GlobalPStepRequest):
    """Execute Global-P binary search and quantile consensus step."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    theta = req.theta if req.theta is not None else session["params"].get("theta", 0.70)
    q = req.q if req.q is not None else session["params"].get("q", 0.20)

    result = engine.calculate_global_p_consensus(
        nodes=session["nodes"],
        theta=theta,
        q=q,
    )

    session["global_p"] = result["global_p"]
    session["exact_quantile"] = result["exact_quantile"]
    session["local_p"] = result["local_p"]
    session["directional_similarities"] = result["directional_similarities"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "global_p": result["global_p"],
        "exact_quantile": result["exact_quantile"],
        "local_p": result["local_p"],
        "directional_similarities": result["directional_similarities"],
        "theta": result["theta"],
        "q": result["q"],
        "logs": result["logs"],
    }


class SignaturesStepRequest(BaseModel):
    session_id: str
    global_p: Optional[int] = Field(default=None, ge=1, le=50)


class ClusteringStepRequest(BaseModel):
    session_id: str
    replication_factor: int = Field(default=2, ge=1, le=10)


class HierarchyStepRequest(BaseModel):
    session_id: str
    max_fanout: int = Field(default=4, ge=2, le=20)


@app.post("/api/v1/step/signatures", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_extract_signatures(req: SignaturesStepRequest):
    """Extract Top-P compact signatures for all nodes in the simulation session."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    global_p = req.global_p if req.global_p is not None else session.get("global_p", 15)

    sig_res = engine.extract_compact_signatures(nodes=session["nodes"], global_p=global_p)
    session["signatures"] = sig_res["signatures"]
    session["global_p"] = global_p

    # Compute a few sample pairwise sparse cosine similarities for dashboard display
    nodes = session["nodes"]
    sample_similarities = []
    if len(nodes) >= 2:
        for i in range(min(5, len(nodes))):
            for j in range(i + 1, min(6, len(nodes))):
                sim = engine.sparse_cosine_similarity(nodes[i]["signature"], nodes[j]["signature"])
                sample_similarities.append({
                    "node_a": nodes[i]["id"],
                    "cat_a": nodes[i].get("category_name"),
                    "node_b": nodes[j]["id"],
                    "cat_b": nodes[j].get("category_name"),
                    "sparse_cosine": round(sim, 4),
                })

    logs = [{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "SUCCESS",
        "message": f"Extracted Top-{global_p} compact signatures for {len(nodes)} nodes with sparse representations.",
    }]
    session["logs"].extend(logs)

    return {
        "session_id": req.session_id,
        "global_p": global_p,
        "signatures": sig_res["signatures"],
        "sample_similarities": sample_similarities,
        "logs": logs,
    }


@app.post("/api/v1/step/clustering", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_intra_zone_clustering(req: ClusteringStepRequest):
    """Execute intra-zone Affinity Propagation clustering, electing Super-Peers and Replica sets."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    global_p = session.get("global_p", 15)
    zones = session.get("zones", {})

    if not zones:
        # If zones step not run explicitly, group by existing zone_id or single zone
        zones_map: Dict[int, List[int]] = {}
        for n in session["nodes"]:
            zid = n.get("zone_id", 0) or 0
            zones_map.setdefault(zid, []).append(n["id"])
        zones = zones_map
        session["zones"] = zones

    all_clusters = []
    node_map = {n["id"]: n for n in session["nodes"]}

    for zid, member_ids in zones.items():
        z_nodes = [node_map[mid] for mid in member_ids]
        c_res = engine.cluster_intra_zone(z_nodes, global_p=global_p, replication_factor=req.replication_factor)
        all_clusters.extend(c_res["clusters"])

    super_peers = [c["super_peer_id"] for c in all_clusters]
    session["clusters"] = all_clusters

    logs = [{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "SUCCESS",
        "message": f"Intra-zone AP clustering complete: {len(all_clusters)} clusters and Super-Peers formed across {len(zones)} zones.",
    }]
    session["logs"].extend(logs)

    return {
        "session_id": req.session_id,
        "clusters": all_clusters,
        "super_peers": super_peers,
        "nodes": session["nodes"],
        "logs": logs,
    }


@app.post("/api/v1/step/son-hierarchy", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_son_hierarchy(req: HierarchyStepRequest):
    """Construct multi-level Hierarchical Semantic Overlay Network (SON) tree."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    global_p = session.get("global_p", 15)
    zones = session.get("zones", {})

    if not zones:
        zones_map: Dict[int, List[int]] = {}
        for n in session["nodes"]:
            zid = n.get("zone_id", 0) or 0
            zones_map.setdefault(zid, []).append(n["id"])
        zones = zones_map
        session["zones"] = zones

    tree_result = engine.build_hierarchical_son(
        nodes=session["nodes"],
        zones=zones,
        global_p=global_p,
        max_fanout=req.max_fanout,
    )

    session["son_tree"] = tree_result
    session["logs"].extend(tree_result["logs"])

    return {
        "session_id": req.session_id,
        "depth": tree_result["depth"],
        "tree_nodes": tree_result["tree_nodes"],
        "tree_edges": tree_result["tree_edges"],
        "level_1_clusters": tree_result["level_1_clusters"],
        "logs": tree_result["logs"],
    }


class FLStepRequest(BaseModel):
    session_id: str
    k_pull: Optional[int] = Field(default=3, ge=1, le=20)
    kappa: Optional[float] = Field(default=0.5, gt=0.0, le=5.0)
    alpha: Optional[float] = Field(default=0.6, ge=0.0, le=1.0)


class FLChurnRequest(BaseModel):
    session_id: str
    node_id: int
    k_pull: Optional[int] = Field(default=3, ge=1, le=20)
    kappa: Optional[float] = Field(default=0.5, gt=0.0, le=5.0)
    alpha: Optional[float] = Field(default=0.6, ge=0.0, le=1.0)


@app.post("/api/v1/fl/step", status_code=status.HTTP_200_OK, tags=["Federated Learning"])
def step_fl_round(req: FLStepRequest):
    """Execute one round of Personalized Federated Learning."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    current_round = session.get("current_round", 0) + 1
    session["current_round"] = current_round

    k_pull = req.k_pull if req.k_pull is not None else 3
    kappa = req.kappa if req.kappa is not None else 0.5
    alpha = req.alpha if req.alpha is not None else 0.6
    global_p = session.get("global_p", 15)

    result = engine.simulate_fl_round(
        nodes=session["nodes"],
        round_num=current_round,
        k_pull=k_pull,
        kappa=kappa,
        alpha=alpha,
        churn_node_id=None,
        clusters=session.get("clusters"),
        global_p=global_p,
    )

    session["nodes"] = result["nodes"]
    session.setdefault("accuracy_history", []).append(result["metrics"])
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "round": current_round,
        "active_clients": result["active_clients"],
        "total_clients": result["total_clients"],
        "metrics": result["metrics"],
        "history": session["accuracy_history"],
        "nodes": session["nodes"],
        "replica_takeover": result["replica_takeover"],
        "logs": result["logs"],
    }


@app.post("/api/v1/fl/churn", status_code=status.HTTP_200_OK, tags=["Federated Learning"])
def step_fl_churn(req: FLChurnRequest):
    """Inject node churn failure and execute instant replica failover."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    current_round = session.get("current_round", 0) + 1
    session["current_round"] = current_round

    k_pull = req.k_pull if req.k_pull is not None else 3
    kappa = req.kappa if req.kappa is not None else 0.5
    alpha = req.alpha if req.alpha is not None else 0.6
    global_p = session.get("global_p", 15)

    result = engine.simulate_fl_round(
        nodes=session["nodes"],
        round_num=current_round,
        k_pull=k_pull,
        kappa=kappa,
        alpha=alpha,
        churn_node_id=req.node_id,
        clusters=session.get("clusters"),
        global_p=global_p,
    )

    session["nodes"] = result["nodes"]
    session.setdefault("accuracy_history", []).append(result["metrics"])
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "round": current_round,
        "churn_node_id": req.node_id,
        "active_clients": result["active_clients"],
        "total_clients": result["total_clients"],
        "metrics": result["metrics"],
        "history": session["accuracy_history"],
        "nodes": session["nodes"],
        "replica_takeover": result["replica_takeover"],
        "logs": result["logs"],
    }


# Frontend static files and dashboard routes
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", tags=["UI"])
def serve_dashboard():
    """Serve the Cyberpunk Interactive Simulation Dashboard."""
    index_path = templates_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>SemanticDFL Simulation Dashboard</h1><p>Frontend template not found.</p>")



