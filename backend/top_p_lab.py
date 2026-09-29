"""Top-P signature lab — follows SemanticDFL paper Sec. 3.2 + Appendix B.1.
Standalone: does not import or modify engine.py / storyboard_10nodes.py."""
import numpy as np


def importance(w, s_prev=None, beta=0.0):
    """s_r^(t) = beta * s_r^(t-1) + (1-beta) * |w_r^(t)|   (beta=0 -> raw magnitude)."""
    a = np.abs(w)
    return a if s_prev is None else beta * s_prev + (1.0 - beta) * a


def order(s):
    """Indices by descending score, ties broken by ascending index (deterministic)."""
    return np.lexsort((np.arange(len(s)), -s))


def cos_curve(w, s):
    """cos(w, w^[P]) for every P=1..M  =  sqrt(c_P) / ||w||  (prefix sums c_P)."""
    c = np.cumsum(w[order(s)] ** 2)
    return np.sqrt(c / c[-1]) if c[-1] > 0 else np.ones(len(w))


def min_p(w, s, theta, trace=None):
    """Algorithm 1: binary search for the minimal P with cos(w, w^[P]) >= theta."""
    nu2 = float(w @ w)
    if nu2 == 0.0:
        return len(w)
    c = np.cumsum(w[order(s)] ** 2)
    lo, hi = 1, len(w)
    while lo < hi:
        mid = (lo + hi) // 2
        ok = bool(c[mid - 1] >= theta ** 2 * nu2)      # Feasible(P): c_P >= theta^2 * nu^2
        if trace is not None:
            trace.append({"lo": lo, "hi": hi, "mid": mid,
                          "cos": float(np.sqrt(c[mid - 1] / nu2)), "feasible": ok})
        if ok:
            hi = mid
        else:
            lo = mid + 1
    return lo


def global_p(p_mins, q=0.8, p_max=None):
    """P := min{ Quantile_q({P_min^i}), P_max }, q in [0.8, 0.9]."""
    srt = np.sort(np.asarray(p_mins))
    k = int(np.ceil(q * len(srt) - 1e-9))               # smallest P with >= q-fraction of clients below it
    p = int(srt[max(k, 1) - 1])
    return min(p, p_max) if p_max else p


def signature(w, s, P):
    """Raw masked vector u = mask(w, I): (sorted indices, raw values), no normalization."""
    idx = np.sort(order(s)[:P])
    return idx, w[idx]


def sparse_cos(a, b):
    """Cosine between two sparse signatures; only I_i ∩ I_j contributes to the dot product."""
    (ia, va), (ib, vb) = a, b
    _, ka, kb = np.intersect1d(ia, ib, assume_unique=True, return_indices=True)
    den = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(va[ka] @ vb[kb] / den) if den else 0.0


def payload_bytes(P, b_idx=4, b_val=2):
    """O(P (b_idx + b_val)) — paper uses 4-byte index + 2-byte value."""
    return P * (b_idx + b_val)


def synthetic_clients(n, M, n_clusters=3, seed=0):
    """Heavy-tailed weights sharing a per-cluster base direction (latent clusters)."""
    rng = np.random.default_rng(seed)
    scale = np.exp(rng.normal(0, 1.2, M))               # few large, many small coordinates
    bases = rng.normal(0, 1, (n_clusters, M)) * scale
    labels = np.arange(n) % n_clusters
    W = np.stack([bases[c] + 0.35 * rng.normal(0, 1, M) * scale for c in labels])
    return W, labels


def run_demo(n=9, M=2000, theta=0.8, q=0.8, beta=0.9, rounds=3, seed=0, p_max=None):
    W, labels = synthetic_clients(n, M, seed=seed)
    rng = np.random.default_rng(seed + 1)
    S = [None] * n
    for _ in range(rounds):                              # EMA importance evolves across rounds
        W = W + 0.05 * rng.normal(0, 1, W.shape) * np.abs(W).mean()
        S = [importance(W[i], S[i], beta) for i in range(n)]
    trace = []
    p_mins = [min_p(W[i], S[i], theta, trace if i == 0 else None) for i in range(n)]
    P = global_p(p_mins, q, p_max)
    sigs = [signature(W[i], S[i], P) for i in range(n)]
    full = np.array([[W[i] @ W[j] / (np.linalg.norm(W[i]) * np.linalg.norm(W[j]))
                      for j in range(n)] for i in range(n)])
    sparse = np.array([[sparse_cos(sigs[i], sigs[j]) for j in range(n)] for i in range(n)])
    curve = cos_curve(W[0], S[0])
    return {
        "M": M, "theta": theta, "q": q, "beta": beta, "n": n, "labels": labels.tolist(),
        "p_mins": p_mins, "global_p": P, "global_p_pct": 100.0 * P / M,
        "cos_at_global_p": [float(cos_curve(W[i], S[i])[P - 1]) for i in range(n)],
        "frac_meeting_theta": float(np.mean([c >= theta for c in
                                             [cos_curve(W[i], S[i])[P - 1] for i in range(n)]])),
        "curve": {"P": list(range(1, M + 1)), "cos": curve.tolist()},
        "trace": trace,
        "signature0": {"indices": sigs[0][0][:12].tolist(), "values": np.round(sigs[0][1][:12], 4).tolist(),
                       "nnz": int(len(sigs[0][0]))},
        "full_cos": np.round(full, 3).tolist(), "sparse_cos": np.round(sparse, 3).tolist(),
        "mean_abs_err": float(np.abs(full - sparse).mean()),
        "payload": {"signature_bytes": payload_bytes(P), "dense_fp32_bytes": 4 * M,
                    "ratio": 4 * M / payload_bytes(P)},
    }
