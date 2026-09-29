from fastapi import APIRouter
from pydantic import BaseModel, Field

from .top_p_lab import run_demo
from .top_p_costs import CostModelRequest, compute_cost_model

router = APIRouter(prefix="/api/v1/toppaper", tags=["top-p-lab"])


class TopPRequest(BaseModel):
    n: int = Field(9, ge=3, le=60)
    M: int = Field(2000, ge=50, le=20000)
    theta: float = Field(0.8, gt=0, le=1)
    q: float = Field(0.8, ge=0.5, le=1)
    beta: float = Field(0.9, ge=0, lt=1)
    rounds: int = Field(3, ge=1, le=20)
    seed: int = 0
    p_max: int | None = None


@router.post("/run")
def run(req: TopPRequest):
    return run_demo(req.n, req.M, req.theta, req.q, req.beta, req.rounds, req.seed, req.p_max)


@router.post("/costs")
def calculate_costs(req: CostModelRequest):
    return compute_cost_model(req)
