# The study's candidate (smallest chained contributions of 25 sub-windows, a delay of one sub-window
# plus a margin), measured with the finality study's own functions (finality_sim.formation,
# fork_bound) at a worst case of 10 s, where DESIGNS.md H.2 derives it, and at 15 s, where it does not.
# (The study's sampler does not support a delay shorter than the sub-window, so margins start at 0.)
# Usage: python candidate.py > candidate.out
import math
import os
import sys

import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
F = 1 / 30
K_BLOCKS = 2160
M = 25
WINDOW = 6 * math.floor(K_BLOCKS / F)
SUB = WINDOW // M
MARGINS = [0, 600, 1200, 1800, 3600]
FRACTIONS = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85)


def cell(alpha, delta):
    from finality_sim.fork_bound import gmin_bound
    from finality_sim.formation import blind_bound, evaluator_bound, formation_counts, open_curve
    from finality_sim.nonce import _rates
    _, _, _, rate = _rates(F, alpha, None, delta)
    r = formation_counts(F, alpha, WINDOW, M, MARGINS, 50_000, 17 + delta + int(alpha * 1000), delta=delta)
    bounds = [gmin_bound(F, alpha, SUB, int(fr * SUB * rate), delta=delta) for fr in FRACTIONS]
    stay = min(bounds, key=lambda b: b["bound"] - b["cross"])
    cross = min(bounds, key=lambda b: b["cross"])
    gb = stay["bound"] - stay["cross"] + cross["cross"]
    ts, shares = open_curve(F, alpha, SUB + 3600, 100_000, 29 + delta + int(alpha * 1000), delta=delta)
    rows = []
    for i, mg in enumerate(MARGINS):
        row = dict(alpha=alpha, delta=delta, margin=mg, g=float(r["g"].mean()), open=float(r["open"][:, i].mean()),
                   chained=float(r["chained"][:, i].mean()), per_win=float(r["per_win"][:, i].mean()),
                   blind=float(r["blind_chained"][:, i].mean()), multi=float(r["multi"][:, i].mean()),
                   gmin_bound=gb)
        if mg >= 0:
            e = evaluator_bound(F, alpha, SUB, mg, delta=delta)
            row |= dict(survive=e["survive"], multi_bound=e["bound"], blind_bound=blind_bound(ts, shares, mg, SUB))
        rows.append(row)
    return rows


if __name__ == "__main__":
    got = Parallel(n_jobs=4)(delayed(cell)(a, d) for a in (0.30, 1 / 3) for d in (10, 15))
    print(f"sub-window {SUB} slots = {SUB / 3600:.2f} h; 50,000 windows a cell")
    print("share | delay | margin (min) | E[G_min] | open at margin | per win | chained, sampled | blind, sampled | "
          "branch seen, sampled | walk bound on G_min | blind bound | survival(W+margin) | branch bound")
    for rows in got:
        for r in rows:
            who = "30 %" if r["alpha"] == 0.30 else "a third"
            tail = (f"{r['blind_bound']:.2e} | {r['survive']:.2e} | {r['multi_bound']:.2e}" if "survive" in r else "- | - | -")
            print(f"{who:8s} | {r['delta']:2d} s | {r['margin'] / 60:6.0f} | {r['g']:.4f} | {r['open']:.4f} | {r['per_win']:.4f} | "
                  f"{r['chained']:.4f} | {r['blind']:.2e} | {r['multi']:.2e} | {r['gmin_bound']:.4f} | {tail}")
    np.save("candidate.npy", np.array([[list(r.get(k, np.nan) for k in ("alpha", "delta", "margin", "g", "open", "per_win", "chained", "blind", "multi", "gmin_bound", "blind_bound", "survive", "multi_bound")) for r in rows] for rows in got]))
