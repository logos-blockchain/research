# The least wait K (hours) for the study's delayed nonce when its sub-windows shrink, read off the
# finality study's wait bound as k_by_nonce.py reads it. Per-nonce factors are DESIGNS.md H.2's
# bounds at a 10-minute margin with one delay evaluator: the walk's bound on E[G_min] plus the blind
# switch plus the evaluator term, at the sub-windows of k = 2160 (4.32 h), 1620 (3.12 h) and
# 1080 (2.08 h), worst case at 10 s; squared for an attack that meets two nonces.
# Usage: python k_short_windows.py
import os
import sys

from joblib import Parallel, delayed

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
F = 1 / 30
EPS = 1e-9

PER_NONCE = {   # (share, sub-window hours): walk bound + blind switch bound + one evaluator
    (0.30, 4.32): 1.040 + 5.5e-3 + 2.4e-11,
    (0.30, 3.12): 1.059 + 7.6e-3 + 3.4e-08,
    (0.30, 2.08): 1.097 + 1.1e-2 + 1.7e-05,
    (1 / 3, 4.32): 1.079 + 1.6e-2 + 1.6e-06,
    (1 / 3, 3.12): 1.124 + 2.2e-2 + 1.2e-04,
    (1 / 3, 2.08): 1.553 + 3.3e-2 + 4.8e-03,
}


def need(alpha, delta, factor):
    from finality_sim.waitbound import wait_curve, wait_needed
    eps = EPS / factor
    return wait_needed(wait_curve(1_500_000, alpha, delta, F, floor=eps / 10), eps) / 3600


if __name__ == "__main__":
    jobs = [(a, w, d) for (a, w) in PER_NONCE for d in (10, 15)]
    res = Parallel(n_jobs=12)(delayed(need)(a, d, PER_NONCE[(a, w)] ** 2) for a, w, d in jobs)
    out = {j: r for j, r in zip(jobs, res)}
    print("share | sub-window (h) | per nonce | two nonces | K at 10 s (h) | K at 15 s (h)")
    for (a, w), f1 in PER_NONCE.items():
        who = "30 %" if a == 0.30 else "a third"
        print(f"{who:8s} | {w:4.2f} | {f1:.3f} | {f1 * f1:.3f} | {out[(a, w, 10)]:.2f} | {out[(a, w, 15)]:.2f}")
