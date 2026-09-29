import json
import math
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.top_p_costs import (
    signature_bytes,
    dense_bytes,
    query_signatures,
    query_cost,
    pull_cost,
    search_share,
    signature_build_cost,
    MIB,
)

client = TestClient(app)

RESNET18_M = 11_700_000


def test_signature_bytes_resnet18_worked_example():
    # S_sig for ResNet-18 (M = 11.7M)
    # P = 10% -> ~6.7 MB (+-2%)
    s_10 = signature_bytes(RESNET18_M, 0.10) / MIB
    assert math.isclose(s_10, 6.7, rel_tol=0.02)

    # Tiny-ImageNet P = 10.8% -> ~7.24 MB (+-2%)
    s_108 = signature_bytes(RESNET18_M, 0.108) / MIB
    assert math.isclose(s_108, 7.24, rel_tol=0.02)

    # Google-Speech P = 13.3% -> ~8.91 MB (+-2%)
    s_133 = signature_bytes(RESNET18_M, 0.133) / MIB
    assert math.isclose(s_133, 8.91, rel_tol=0.02)


def test_query_signatures_count_and_transfer_cost():
    # 7 superpeers + 4 leaves * 2 = 15 signatures
    num_sigs = query_signatures(visited_superpeers=7, probed_leaves=4, leaf_size=2)
    assert num_sigs == 15

    # 15 signatures @ 10.8% -> ~109 MB (+-2%), ~4.4 s (+-2%)
    sig_bytes_108 = signature_bytes(RESNET18_M, 0.108)
    q_108 = query_cost(num_sigs, sig_bytes_108, bw_mb_s=25.0)
    assert math.isclose(q_108["mb"], 109.0, rel_tol=0.02)
    assert math.isclose(q_108["seconds"], 4.4, rel_tol=0.02)

    # 15 signatures @ 13.3% -> ~133 MB (+-2%), ~5.3 s (+-2%)
    sig_bytes_133 = signature_bytes(RESNET18_M, 0.133)
    q_133 = query_cost(num_sigs, sig_bytes_133, bw_mb_s=25.0)
    assert math.isclose(q_133["mb"], 133.0, rel_tol=0.02)
    assert math.isclose(q_133["seconds"], 5.3, rel_tol=0.02)


def test_pull_and_serve_cost_strict_and_overhead():
    # Pull + serve K=10 full models counts 10 downloads + 10 uploads
    model_bytes = dense_bytes(RESNET18_M, bytes_per_param=4)
    
    # Default overhead factor = 1.00 -> strictly 2*K*model_bytes / bandwidth ≈ 37.4 s (+-1%)
    p_cost_default = pull_cost(K=10, model_bytes=model_bytes, bw_mb_s=25.0, overhead_factor=1.0)
    assert math.isclose(p_cost_default["mb"], 935.0, rel_tol=0.02)
    assert math.isclose(p_cost_default["seconds"], 37.4, rel_tol=0.01)

    # Paper preset overhead factor = 1.03 -> ≈ 38.5 s (+-1%) [Derived: 38.5 s ÷ 37.4 s]
    p_cost_paper = pull_cost(K=10, model_bytes=model_bytes, bw_mb_s=25.0, overhead_factor=1.03)
    assert math.isclose(p_cost_paper["seconds"], 38.5, rel_tol=0.01)
    assert p_cost_paper["reference_paper_seconds"] == 38.5


def test_search_share():
    search_s = 5.34
    round_s = 5.34 + 37.40
    share = search_share(search_s, round_s)
    assert 10.0 <= share <= 13.0


def test_signature_build_cost():
    meta = signature_build_cost(RESNET18_M)
    assert "time_complexity" in meta
    assert "memory_complexity" in meta


def test_costs_endpoint_default_and_presets():
    # Default endpoint call (overhead_factor = 1.0)
    resp = client.post("/api/v1/toppaper/costs", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "signature_mb" in data
    assert "query_cost" in data
    assert "pull_cost" in data
    assert math.isclose(data["pull_cost"]["seconds"], 37.4, rel_tol=0.01)
    assert "search_share_pct" in data
    assert "comparison_table" in data

    # Tiny-ImageNet preset with paper overhead factor 1.03
    resp_tiny = client.post("/api/v1/toppaper/costs", json={
        "M": 11_700_000,
        "P_pct": 10.8,
        "bw_mb_s": 25.0,
        "K": 10,
        "overhead_factor": 1.03
    })
    assert resp_tiny.status_code == 200
    d_tiny = resp_tiny.json()
    assert math.isclose(d_tiny["signature_mb"], 7.24, rel_tol=0.02)
    assert math.isclose(d_tiny["query_cost"]["mb"], 109.0, rel_tol=0.02)
    assert math.isclose(d_tiny["pull_cost"]["seconds"], 38.5, rel_tol=0.01)

    # Google-Speech preset with paper overhead factor 1.03
    resp_speech = client.post("/api/v1/toppaper/costs", json={
        "M": 11_700_000,
        "P_pct": 13.3,
        "bw_mb_s": 25.0,
        "K": 10,
        "overhead_factor": 1.03
    })
    assert resp_speech.status_code == 200
    d_speech = resp_speech.json()
    assert math.isclose(d_speech["signature_mb"], 8.91, rel_tol=0.02)
    assert math.isclose(d_speech["query_cost"]["mb"], 133.0, rel_tol=0.02)
    assert math.isclose(d_speech["pull_cost"]["seconds"], 38.5, rel_tol=0.01)


def test_costs_endpoint_validation_error():
    # 422 on invalid input (e.g. negative M, P_pct > 100, negative bandwidth)
    resp = client.post("/api/v1/toppaper/costs", json={"M": -50})
    assert resp.status_code == 422

    resp2 = client.post("/api/v1/toppaper/costs", json={"P_pct": 150.0})
    assert resp2.status_code == 422


def test_faq_json_validity():
    faq_path = Path(__file__).resolve().parent.parent / "frontend" / "static" / "top_p_faq.json"
    assert faq_path.exists(), "top_p_faq.json file must exist in frontend/static/"

    with open(faq_path, "r", encoding="utf-8") as f:
        faq_data = json.load(f)

    assert isinstance(faq_data, list)
    assert len(faq_data) >= 10, "Should have rich Q&A items"

    for entry in faq_data:
        assert "id" in entry
        assert "category" in entry
        assert "q" in entry and len(entry["q"]) > 0
        assert "a" in entry and len(entry["a"]) > 0
        assert "refs" in entry and isinstance(entry["refs"], list)
