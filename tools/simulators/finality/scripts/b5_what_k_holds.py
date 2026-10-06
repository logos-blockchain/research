"""Phase B5: the largest attacker share each k holds (PLAN.md B5).

    python scripts/b5_what_k_holds.py       # needs runs/a1; writes runs/b5/*.csv

Worst case: B2's upper bound at depth k (scripts/b2_settlement.py) on a grid of shares 0.05 to 1/3
in steps of 0.005, its log linear in the share between grid points; a k that holds a third reads
">= 1/3", one that holds no share of the grid "< 0.05".

Random delays: the private race from the target's parent (B3's race without a premined lead) and
Cryptarchia's strict tie rule, at the attacker's share of chain-extending blocks
q = a / (a + (1 - a) g), with the canonical growth g measured in A1 (runs/a1/summary.csv) at
testnet's Blend (1 hop, 1 round) and the specification's (3 hops, up to 3 rounds), 0.1 s links. B3
found this closed form within a few blocks of the race on the engine's timelines.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import special, stats

from b2_settlement import DELAYS_S, upper

HERE = pathlib.Path(__file__).resolve().parent.parent
KS = (2160, 1080, 432, 216, 120)
EPS = (1e-6, 1e-9, 1e-12)
GRID = np.append(np.round(np.arange(0.05, 1 / 3, 0.005), 4), 1 / 3)


def log_strict(q: float, n: int) -> float:
    """log P(attacker ever strictly ahead) after n honest blocks counting the target."""
    p = 1 - q
    m = np.arange(n + 1)
    terms = stats.nbinom.logpmf(m, n, p) + (n + 1 - m) * np.log(q / p)
    return float(np.logaddexp(stats.nbinom.logsf(n, n, p), special.logsumexp(terms)))


def max_alpha(k: int, g: float, eps: float) -> float:
    lo, hi = 0.0, 0.5
    for _ in range(60):
        a = (lo + hi) / 2
        q = a / (a + (1 - a) * g)
        if q < 0.5 and log_strict(q, k + 1) <= np.log(eps):
            lo = a
        else:
            hi = a
    return lo


def worst_log(alpha: float, delay_s: int) -> np.ndarray:
    """log of B2's upper bound at each k of KS."""
    with np.errstate(divide="ignore"):
        return np.log(upper(alpha, delay_s, max(KS))[np.array(KS) - 1])


def held_worst(logs: np.ndarray, eps: float, ln_r: np.ndarray | float = 0.0) -> float:
    """The largest share of GRID's span at which logs + ln_r stays at or below ln eps, linear
    between grid points: nan if none does, inf if a third does."""
    y = logs + ln_r - math.log(eps)
    if y[0] > 0:
        return math.nan
    if y[-1] <= 0:
        return math.inf
    i = int(np.nonzero(y > 0)[0][0])
    return float(GRID[i - 1] - y[i - 1] * (GRID[i] - GRID[i - 1]) / (y[i] - y[i - 1]))


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    ref = {"testnet (1 hop, 1 round)": s[(s.blend_hops == 1) & (s.blend_delay_max == 1)],
           "specification (3 hops, 3 rounds)": s[(s.blend_hops == 3) & (s.blend_delay_max == 3)]}
    rows = []
    for name, r in ref.items():
        g = float(r.growth_per_f.iloc[0])
        for eps in EPS:
            rows.append(dict(blend=name, growth=round(g, 3), eps=eps,
                             **{f"k={k}": max_alpha(k, g, eps) for k in KS}))
    t = pd.DataFrame(rows)
    out = HERE / "runs" / "b5"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "random_delay.csv", index=False)
    print(t.to_string(index=False))

    logs = Parallel(n_jobs=-2)(delayed(worst_log)(float(a), d) for d in DELAYS_S for a in GRID)
    logs = np.array(logs).reshape(len(DELAYS_S), GRID.size, len(KS))
    pd.DataFrame([dict(delay_s=d, alpha=a, k=k, log_ub=v) for d, lg in zip(DELAYS_S, logs)
                  for a, row in zip(GRID, lg) for k, v in zip(KS, row)]).to_csv(
        out / "worst_logs.csv", index=False, float_format="%.17g")
    rows = []
    for eps in EPS:
        for d, lg in zip(DELAYS_S, logs):
            rows.append(dict(eps=eps, delay_s=d,
                             **{f"k={k}": held_worst(lg[:, j], eps) for j, k in enumerate(KS)}))
    w = pd.DataFrame(rows)
    w.to_csv(out / "worst_case.csv", index=False)
    print()
    print(w.to_string(index=False))


if __name__ == "__main__":
    main()
