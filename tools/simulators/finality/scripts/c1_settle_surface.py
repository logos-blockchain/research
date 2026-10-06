"""Phase C1: minutes to settle over block interval and delay, under random Blend delays.

    python scripts/c1_settle_surface.py      # needs runs/c1/summary.csv (scripts/c1_rate.py)

Depth comes from the private race from the target's parent, without a premined lead, and
Cryptarchia's strict tie rule, which B3 found within a few blocks of the closed form at the
attacker's share of chain-extending blocks, ``q = a / (a + (1 - a) g)``, where ``g`` is the
measured canonical growth per occupied-slot rate. Time per canonical block is ``interval / g``. H3
asks whether the time falls at least as fast as ``1 / (1 - o)`` as the orphan share ``o`` falls.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent.parent
ALPHAS = (0.10, 0.25)
EPS = (1e-6, 1e-9)


def strict(q: float, n: int) -> float:
    p = 1 - q
    m = np.arange(n + 1)
    return float(stats.nbinom.sf(n, n, p) + (stats.nbinom.pmf(m, n, p) * (q / p) ** (n + 1 - m)).sum())


def depth(q: float, eps: float) -> int:
    k = 1
    while strict(q, k + 1) > eps:
        k += 1
        if k > 5000:
            return -1
    return k


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "c1" / "summary.csv")
    rows = []
    for _, r in s.iterrows():
        g = r.growth_per_f
        for a in ALPHAS:
            q = a / (a + (1 - a) * g)
            for eps in EPS:
                d = depth(q, eps)
                rows.append(dict(hops=r.hops, delta_max=r.delta_max, interval=r.interval,
                                 orphan=r.orphan_share, growth=g, alpha=a, eps=eps, depth=d,
                                 minutes=d * r.interval / g / 60))
    t = pd.DataFrame(rows)
    t.to_csv(HERE / "runs" / "c1" / "settle_surface.csv", index=False)
    for a in ALPHAS:
        for eps in EPS:
            p = t[(t.alpha == a) & (t.eps == eps)].pivot_table(
                index=["hops", "delta_max"], columns="interval", values="minutes")
            print(f"\nminutes to settle, alpha={a}, eps={eps:.0e} (rows: hops, Delta_max rounds;"
                  " columns: block interval s)")
            print(p[sorted(p.columns, reverse=True)].round(0).to_string())


if __name__ == "__main__":
    main()
