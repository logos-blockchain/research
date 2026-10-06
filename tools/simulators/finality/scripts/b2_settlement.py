"""Phase B2: settlement depth over attacker share and delay (PLAN.md B2, Q2, Q3).

    python scripts/b2_settlement.py    # writes runs/b2/{ub.parquet,curves,depths,third,states}.csv

For each attacker share ``a`` and delay ``Delta`` (seconds; ``D = f * Delta`` block intervals at
f = 1/30), the bounds of Gaži, Ren and Russell (the port in ``finality_sim.lcbounds``). The upper
bound is computed at every depth until it falls to UB_FLOOR (``ub_curve``). The lower bound is
computed at depths 20..120 and extended past them by a log-linear fit over the last four depths;
every extended depth is marked ``extrapolated``.

The symbol alphabet is sized per point so that the truncated mass of the honest-run length,
``(1 - g)^A`` with ``g = exp(-(1 - a) D)``, stays below 1e-10, and the Markov chain keeps at
least 30 states and one more than the alphabet (the original code assumes the alphabet does not
exceed the states). General symbols of probability at most 1e-16 are skipped; the mass they carry
per step is recorded as ``skipped``. Delays run to 20 s; beyond that the alphabet the bound needs
makes the computation impractical here. third.csv: the upper bound's depth at 1e-9 against a
third of the stake at every whole second of delay from 10 s to 15 s. states.csv: the upper bound's
depths at 1e-9 and 1e-30 with the states and with twice as many.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from finality_sim.lcbounds import error_lb, skipped_mass, slot_pdf, ub_curve

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "b2"
ADV = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
DELAYS_S = (1, 2, 3, 5, 8, 10, 15, 20)
DEPTHS = (20, 40, 60, 80, 100, 120)
MIN_STATES = 30
MIN_PROB = 1e-16
EPSILONS = (1e-3, 1e-6, 1e-9)
UB_FLOOR = 1e-60                 # B6 reads the upper bound down to 1e-9 over its grinding factors
UB_CAP = 60_000


def alphabet_for(adv: float, d: float, tail: float = 1e-10) -> int:
    g = math.exp(-(1 - adv) * d)
    return max(10, math.ceil(math.log(tail) / math.log(1 - g)) + 1)


def upper(adv: float, delay_s: float, k_max: int, floor: float = 0.0,
          states: int | None = None) -> np.ndarray:
    """The upper bound at depths 1 .. k_max, or until it is at most ``floor``."""
    d = F * delay_s
    a = alphabet_for(adv, d)
    return ub_curve(k_max, slot_pdf(1 - adv, d, a), a,
                    max(MIN_STATES, a + 1) if states is None else states, MIN_PROB, floor)


def first_depth(ub: np.ndarray, eps: float) -> int:
    """The smallest depth whose upper bound is at most eps."""
    return int(np.argmax(ub <= eps)) + 1


def curve(adv: float, delay_s: float) -> tuple[list[dict], np.ndarray]:
    d = F * delay_s
    a = alphabet_for(adv, d)
    states = max(MIN_STATES, a + 1)
    sp = slot_pdf(1 - adv, d, a)
    skipped = skipped_mass(sp, a, MIN_PROB)
    ub = upper(adv, delay_s, UB_CAP, UB_FLOOR)
    if ub[-1] > UB_FLOOR:
        raise ValueError("the upper bound did not reach its floor within UB_CAP")
    rows = []
    for k in DEPTHS:
        rows.append(dict(adv=adv, delay_s=delay_s, D=d, alphabet=a, states=states,
                         skipped=skipped, depth=k, ub=ub[k - 1],
                         lb=error_lb(k, sp, a, states, min_prob=MIN_PROB)))
    # convergence at the deepest point: the attack followed twice as long
    k = DEPTHS[-1]
    lb2 = error_lb(k, sp, a, states, steps=2 * 4 * k, min_prob=MIN_PROB)
    rows[-1]["lb_doubled_rel_change"] = abs(lb2 - rows[-1]["lb"]) / max(rows[-1]["lb"], 1e-300)
    return rows, ub


def depth_for(curve_df: pd.DataFrame, col: str, eps: float) -> tuple[float, bool]:
    """Depth with the bound at eps, log-linear between the computed depths and past them."""
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
    curves = pd.DataFrame([r for p, _ in parts for r in p])
    curves.to_csv(OUT / "curves.csv", index=False)
    pd.concat([pd.DataFrame(dict(adv=a, delay_s=s, depth=np.arange(1, ub.size + 1), ub=ub))
               for (a, s), (_, ub) in zip(jobs, parts)]).to_parquet(OUT / "ub.parquet")
    rows = []
    for (a, s), (_, ub) in zip(jobs, parts):
        c = curves[(curves.adv == a) & (curves.delay_s == s)]
        for eps in EPSILONS:
            lb, extra = depth_for(c, "lb", eps)
            rows.append(dict(adv=a, delay_s=s, D=c.D.iloc[0], eps=eps, ub_depth=first_depth(ub, eps),
                             lb_depth=lb, lb_extrapolated=extra))
    depths = pd.DataFrame(rows)
    depths.to_csv(OUT / "depths.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 400):
        print(depths.round(3).to_string(index=False))
    third()
    states()


def doubled(adv: float, delay_s: float) -> dict:
    a = alphabet_for(adv, F * delay_s)
    row = dict(adv=adv, delay_s=delay_s, states=max(MIN_STATES, a + 1))
    for name, n in (("", row["states"]), ("doubled_", 2 * row["states"])):
        ub = upper(adv, delay_s, UB_CAP, 1e-30, n)
        row |= {f"{name}depth_1e-09": first_depth(ub, 1e-9), f"{name}depth_1e-30": first_depth(ub, 1e-30)}
    return row


def states() -> None:
    t = pd.DataFrame(Parallel(n_jobs=-2)(delayed(doubled)(a, s) for a in ADV for s in DELAYS_S))
    t.to_csv(OUT / "states.csv", index=False)
    print(t.to_string(index=False))


def third() -> None:
    t = pd.DataFrame([dict(delay_s=s, ub_depth=first_depth(upper(1 / 3, s, UB_CAP, 1e-9), 1e-9))
                      for s in range(10, 16)])
    t.to_csv(OUT / "third.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
