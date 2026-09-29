import numpy as np
import pytest
from backend.top_p_lab import (
    importance,
    cos_curve,
    min_p,
    global_p,
    signature,
    order,
    payload_bytes,
)


def test_worked_example_steps():
    # Fixed example parameters
    w = np.array([0.5, -3.0, 0.2, 2.0, -0.1, 1.5, 0.3, -1.0, 0.4, 0.6], dtype=float)
    s = np.abs(w)  # beta = 0
    theta = 0.9

    # Step 1: sort by |w| desc
    ord_idx = order(s)
    sorted_abs = s[ord_idx]
    expected_sorted_abs = np.array([3.0, 2.0, 1.5, 1.0, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    assert np.allclose(sorted_abs, expected_sorted_abs)

    # Step 2: prefix sums c_P of squares, ||w||^2 = 17.16
    c = np.cumsum(sorted_abs ** 2)
    expected_c = np.array([9.0, 13.0, 15.25, 16.25, 16.61, 16.86, 17.02, 17.11, 17.15, 17.16])
    assert np.allclose(c, expected_c)
    assert np.isclose(c[-1], 17.16)

    # Step 3: cos(P) = sqrt(c_P)/||w||
    curve = cos_curve(w, s)
    expected_curve = np.array([0.724, 0.870, 0.943, 0.973, 0.984, 0.991, 0.996, 0.999, 1.000, 1.000])
    assert np.allclose(curve, expected_curve, atol=1e-3)
    # Check specific cos(3) = sqrt(15.25)/sqrt(17.16) ~ 0.943
    assert np.isclose(curve[2], np.sqrt(15.25) / np.sqrt(17.16), atol=1e-3)

    # Step 4: feasibility test and min_p
    trace_09 = []
    p_min_09 = min_p(w, s, theta=0.9, trace=trace_09)
    assert p_min_09 == 3
    p_min_08 = min_p(w, s, theta=0.8)
    assert p_min_08 == 2

    # Step 5: binary search trace checks
    # (lo=1,hi=10,mid=5 yes) -> (1,5,mid=3 yes) -> (1,3,mid=2 no) -> P_min = 3
    assert len(trace_09) == 3
    assert trace_09[0] == {"lo": 1, "hi": 10, "mid": 5, "cos": float(np.sqrt(16.61 / 17.16)), "feasible": True}
    assert trace_09[1] == {"lo": 1, "hi": 5, "mid": 3, "cos": float(np.sqrt(15.25 / 17.16)), "feasible": True}
    assert trace_09[2] == {"lo": 1, "hi": 3, "mid": 2, "cos": float(np.sqrt(13.0 / 17.16)), "feasible": False}

    # Step 6: shared P with 5 clients [3, 2, 4, 3, 6], q=0.8
    p_mins = [3, 2, 4, 3, 6]
    shared_p = global_p(p_mins, q=0.8)
    assert shared_p == 4

    # Step 7: signature payload calculation
    # P=4 entries -> 4 * (4B idx + 2B val) = 24 B vs dense 10 * 4B = 40 B
    sig_idx, sig_val = signature(w, s, P=4)
    sig_bytes = len(sig_idx) * (4 + 2)
    dense_bytes = len(w) * 4
    assert sig_bytes == 24
    assert dense_bytes == 40
    assert payload_bytes(4) == 24
