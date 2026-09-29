import numpy as np
from backend.top_p_lab import (importance, cos_curve, min_p, global_p, signature,
                               sparse_cos, order, run_demo)

rng = np.random.default_rng(3)
W = rng.normal(0, 1, 500) * np.exp(rng.normal(0, 1, 500))


def test_cos_is_monotone_and_reaches_one():
    c = cos_curve(W, np.abs(W))
    assert np.all(np.diff(c) >= -1e-12) and abs(c[-1] - 1) < 1e-9


def test_min_p_is_minimal():
    p = min_p(W, np.abs(W), 0.8)
    c = cos_curve(W, np.abs(W))
    assert c[p - 1] >= 0.8 and (p == 1 or c[p - 2] < 0.8)


def test_signature_is_raw_masked_vector_with_P_nonzeros():
    idx, val = signature(W, np.abs(W), 40)
    assert len(idx) == 40 and np.array_equal(val, W[idx])


def test_ties_broken_by_index():
    assert list(order(np.array([1.0, 1.0, 1.0]))) == [0, 1, 2]


def test_sparse_cos_matches_dense_masked_cos():
    a, b = W, W + rng.normal(0, 0.5, 500)
    sa, sb = signature(a, np.abs(a), 60), signature(b, np.abs(b), 60)
    da, db = np.zeros(500), np.zeros(500)
    da[sa[0]], db[sb[0]] = sa[1], sb[1]
    assert abs(sparse_cos(sa, sb) - da @ db / (np.linalg.norm(da) * np.linalg.norm(db))) < 1e-9


def test_ema_importance_and_global_p_quantile():
    s = importance(np.array([1.0, -2.0]), np.array([4.0, 0.0]), beta=0.5)
    assert np.allclose(s, [2.5, 1.0])
    assert global_p([1, 2, 3, 4, 10], q=0.8) == 4


def test_demo_payload_and_quantile_guarantee():
    r = run_demo()
    assert r["frac_meeting_theta"] >= r["q"] - 1e-9
    assert r["payload"]["ratio"] > 1
