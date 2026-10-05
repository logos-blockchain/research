"""Phase B5: the largest attacker share each k holds (PLAN.md B5).

    python scripts/b5_what_k_holds.py       # random delays; worst case from runs/b2/depths.csv

Worst case: the upper bound of B2. Between B2's grid of shares (0.05 to 1/3) the log of the depth
is interpolated linearly in the share; a k beyond the grid reads ">= 1/3" or "< 0.05".

Random delays: the private race with premining and Cryptarchia's strict tie rule, at the
attacker's share of chain-extending blocks q = a / (a + (1 - a) g), with the canonical growth g
measured in A1 (runs/a1/summary.csv) at testnet's Blend (1 hop, 1 round) and the
specification's (3 hops, up to 3 rounds), 0.1 s links. B3 found this closed form within a few
blocks of the race on the engine's timelines.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from scipy import special, stats

HERE = pathlib.Path(__file__).resolve().parent.parent
KS = (2160, 1080, 432, 216, 120)
EPS = (1e-6, 1e-9, 1e-12)


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

    d = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    rows = []
    for (eps, delay), g in d.groupby(["eps", "delay_s"]):
        g = g.sort_values("adv")
        a, logd = g.adv.to_numpy(), np.log(g.ub_depth.to_numpy())
        row = dict(eps=eps, delay_s=delay)
        for k in KS:
            if logd[0] > np.log(k):
                row[f"k={k}"] = "< 0.05"
            elif logd[-1] <= np.log(k):
                row[f"k={k}"] = ">= 1/3"
            else:
                i = int(np.nonzero(logd > np.log(k))[0][0])
                x = a[i - 1] + (np.log(k) - logd[i - 1]) * (a[i] - a[i - 1]) / (logd[i] - logd[i - 1])
                row[f"k={k}"] = f"{x:.3f}"
        rows.append(row)
    w = pd.DataFrame(rows)
    w.to_csv(out / "worst_case.csv", index=False)
    print()
    print(w.to_string(index=False))


if __name__ == "__main__":
    main()
