"""FastAPI Service for SemanticDFL Protocol Simulator.

Provides REST endpoints for topology initialization, health monitoring,
and in-memory session state management.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.engine import SemanticDFLEngine


class SimulationInitRequest(BaseModel):
    num_nodes: int = Field(default=30, ge=2, le=500, description="Number of participating nodes")
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

        log_event("INFO", f"Initializing simulation session {session_id} with N={req.num_nodes}, D_limit={req.d_limit}")

        engine = SemanticDFLEngine()
        topology = engine.generate_topology(N=req.num_nodes, D_limit=req.d_limit, maintain_connectivity=True)

        num_edges = len(topology["edges"])
        avg_deg = topology["metadata"]["avg_degree"]
        log_event("INFO", f"RGG topology generated: {req.num_nodes} nodes, {num_edges} physical edges (avg degree: {avg_deg})")
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


class VRFStepRequest(BaseModel):
    session_id: str
    r_hops: Optional[int] = Field(default=None, ge=1, le=10)


class ZonesStepRequest(BaseModel):
    session_id: str
    r_hops: Optional[int] = Field(default=None, ge=1, le=10)
    max_zone_size: Optional[int] = Field(default=None, ge=2, le=100)


class GlobalPStepRequest(BaseModel):
    session_id: str
    theta: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    q: Optional[float] = Field(default=None, ge=0.0, le=1.0)


@app.post("/api/v1/step/vrf", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_vrf_election(req: VRFStepRequest):
    """Execute VRF leader election step on the current simulation session."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    r_hops = req.r_hops if req.r_hops is not None else session["params"].get("r_hops", 2)

    result = engine.run_vrf_election(
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


@app.post("/api/v1/step/zones", status_code=status.HTTP_200_OK, tags=["Simulation"])
def step_zone_formation(req: ZonesStepRequest):
    """Execute TTL-bounded zone probing and deterministic splitting step."""
    session = session_store.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {req.session_id} not found")

    engine = SemanticDFLEngine()
    r_hops = req.r_hops if req.r_hops is not None else session["params"].get("r_hops", 2)
    max_zone_size = req.max_zone_size if req.max_zone_size is not None else session["params"].get("max_zone_size", 10)

    result = engine.run_zone_formation(
        nodes=session["nodes"],
        adjacency_list=session["adjacency_list"],
        r_hops=r_hops,
        max_zone_size=max_zone_size,
    )

    session["nodes"] = result["nodes"]
    session["zones"] = result["zones"]
    session["boundaries"] = result["boundaries"]
    session["packet_hops"] = result["packet_hops"]
    session["logs"].extend(result["logs"])

    return {
        "session_id": req.session_id,
        "zones": result["zones"],
        "boundaries": result["boundaries"],
        "packet_hops": result["packet_hops"],
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

