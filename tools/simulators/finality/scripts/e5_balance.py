"""Phase E5: the DAG's safe region against a delay-scheduling adversary (PLAN.md E5).

    python scripts/e5_balance.py      # writes runs/e5/{balance,hold}.csv

The DAG weighs every honest block of a subDAG, as GHOST weighs every block of a subtree, so the
balancing attacks of Gaži, Motaqy and Russell (src/finality_sim/balance.py) bound it. On
Cryptarchia's slot lottery at production coefficient f_A and delay Delta, balance.csv holds the
smallest adversary share whose reserve drifts upward, with ties broken by the adversary or by a
rule fixed in advance, beside the longest-chain rule's region at the same block rate
(src/finality_sim/ghost.py). hold.csv holds the share of 1,000 attempts, each begun with an empty
reserve, that keep the two subDAGs balanced for an hour and for a day.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim.balance import hold_shares, threshold
from finality_sim.ghost import lcr

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "e5"
FS = (1 / 30, 1 / 20, 1 / 15, 0.1, 0.25)
DELAYS = (1, 2, 5, 10, 20)
HOURS = (1, 24)


def chain_region(f: float, delta: float) -> float:
    lam = -math.log(1 - f)
    lo, hi = 0.0, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if mid * lam < lcr((1 - mid) * lam, delta):
            lo = mid
        else:
            hi = mid
    return lo


def hold_point(f: float, delta: int, alpha: float, seed: int) -> list[dict]:
    lam_h = (1 - alpha) * -math.log(1 - f)
    p = math.exp(-lam_h)
    mean_len = (p ** -delta - 1) / (1 - p)
    horizons = tuple(max(1, round(h * 3600 / mean_len)) for h in HOURS)
    shares = hold_shares(f, alpha, delta, horizons, int(4 * max(HOURS) * 3600 * 1.2), seed)
    return [dict(f=f, delay_s=delta, alpha=alpha, hours=h, phases=k, held=x)
            for h, k, x in zip(HOURS, horizons, shares)]


def main() -> None:
    rows = []
    for f in FS:
        for d in DELAYS:
            rows.append(dict(f=f, delay_s=d,
                             dag_adversarial_ties=threshold(f, d, "adversarial"),
                             dag_fixed_ties=threshold(f, d, "deterministic"),
                             chain=chain_region(f, d)))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "balance.csv", index=False)
    print(t.round(3).to_string(index=False), end="\n\n")
    pts = [(f, d, a) for f in (1 / 30, 0.25) for d in (5, 10) for a in (0.10, 0.25)]
    hold = Parallel(n_jobs=-2)(delayed(hold_point)(f, d, a, i) for i, (f, d, a) in enumerate(pts))
    h = pd.DataFrame([x for p in hold for x in p])
    h.to_csv(OUT / "hold.csv", index=False)
    print(h.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
