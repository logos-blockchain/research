"""Phase B2: settlement depth over attacker share and delay (PLAN.md B2, Q2, Q3).

    python scripts/b2_settlement.py         # writes runs/b2/{curves.csv,depths.csv}

For each attacker share ``a`` and delay ``Delta`` (seconds; ``D = f * Delta`` block
intervals at f = 1/30), the upper and lower bounds of Gaži, Ren and Russell (the port in
``finality_sim.lcbounds``) at depths 20..120. Beyond the computed depths the curves are
extended by a log-linear fit over the last four depths; every extended depth is marked
``extrapolated``.

The symbol alphabet is sized per point so that the truncated mass of the honest-run length,
``(1 - g)^A`` with ``g = exp(-(1 - a) D)``, stays below 1e-10, and the Markov chain keeps at
least 30 states and one more than the alphabet (the original code assumes the alphabet does not
exceed the states). General symbols of probability at most 1e-16 are skipped; the mass they carry
per step is recorded as ``skipped``. Delays run to 20 s; beyond that the alphabet the bound needs
makes the computation impractical here.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from finality_sim.lcbounds import error_lb, error_ub, skipped_mass, slot_pdf

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "b2"
ADV = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
DELAYS_S = (1, 2, 3, 5, 8, 10, 15, 20)
DEPTHS = (20, 40, 60, 80, 100, 120)
MIN_STATES = 30
MIN_PROB = 1e-16
EPSILONS = (1e-3, 1e-6, 1e-9)


def alphabet_for(adv: float, d: float, tail: float = 1e-10) -> int:
    g = math.exp(-(1 - adv) * d)
    return max(10, math.ceil(math.log(tail) / math.log(1 - g)) + 1)


def curve(adv: float, delay_s: float) -> list[dict]:
    d = F * delay_s
    a = alphabet_for(adv, d)
    states = max(MIN_STATES, a + 1)
    sp = slot_pdf(1 - adv, d, a)
    skipped = skipped_mass(sp, a, MIN_PROB)
    rows = []
    for k in DEPTHS:
        rows.append(dict(adv=adv, delay_s=delay_s, D=d, alphabet=a, states=states,
                         skipped=skipped, depth=k,
                         ub=error_ub(k, sp, a, states, MIN_PROB),
                         lb=error_lb(k, sp, a, states, min_prob=MIN_PROB)))
    # convergence at the deepest point: the attack followed twice as long
    k = DEPTHS[-1]
    lb2 = error_lb(k, sp, a, states, steps=2 * 4 * k, min_prob=MIN_PROB)
    rows[-1]["lb_doubled_rel_change"] = abs(lb2 - rows[-1]["lb"]) / max(rows[-1]["lb"], 1e-300)
    return rows


def depth_for(curve_df: pd.DataFrame, col: str, eps: float) -> tuple[float, bool]:
    """Smallest depth with the bound at or below eps; log-linear extension past the grid."""
    c = curve_df.sort_values("depth")
    k, v = c.depth.to_numpy(float), c[col].to_numpy(float)
    hit = np.nonzero(v <= eps)[0]
    if hit.size:
        i = hit[0]
        if i == 0:
            return float(k[0]), False
        # interpolate log-linearly between the bracketing depths
        x0, x1, y0, y1 = k[i - 1], k[i], math.log(v[i - 1]), math.log(v[i])
        return x0 + (math.log(eps) - y0) * (x1 - x0) / (y1 - y0), False
    tail = slice(-4, None)
    slope, icpt = np.polyfit(k[tail], np.log(v[tail]), 1)
    if slope >= 0:
        return math.inf, True
    return (math.log(eps) - icpt) / slope, True


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(a, s) for a in ADV for s in DELAYS_S]
    parts = Parallel(n_jobs=-2, backend="loky")(delayed(curve)(a, s) for a, s in jobs)
    curves = pd.DataFrame([r for p in parts for r in p])
    curves.to_csv(OUT / "curves.csv", index=False)
    rows = []
    for (a, s), c in curves.groupby(["adv", "delay_s"], sort=False):
        for eps in EPSILONS:
            r = dict(adv=a, delay_s=s, D=c.D.iloc[0], eps=eps)
            for col in ("ub", "lb"):
                depth, extra = depth_for(c, col, eps)
                r[f"{col}_depth"] = depth
                r[f"{col}_extrapolated"] = extra
            rows.append(r)
    depths = pd.DataFrame(rows)
    depths.to_csv(OUT / "depths.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 400):
        print(depths.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
