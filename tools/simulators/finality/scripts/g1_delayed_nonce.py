"""Phase G1: the smallest contributions with a delayed nonce (PLAN.md, G1).

    python scripts/g1_delayed_nonce.py      # needs runs/a1, runs/b2, runs/b7; writes runs/g1/*.csv

With the nonce of B7 passed through a sequential delay of T minutes on the coalition's hardware,
the coalition decides blind wherever the delay outlasts the time it has to decide. Before the
cut-off it has a few block intervals: a withheld block can be published later only through a fork.
At the cut-off it has until the lead of its private chain is spent. lasts.csv holds the chance that
the lead lasts at least T (src/finality_sim/further.py, lead_lasts) for B6's delay models.
factor.csv holds the factor per nonce that remains, E[1 + (G_min - 1) 1{the lead lasts T}]
(delayed_factor), sampled over 20,000 windows a point with 20,000 near slots, and the depth at 1e-9
with two nonces read as B7 reads its factors, beside the unground depth and B7's estimate.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b7_nonce import depth_reader, models
from finality_sim.further import delayed_factor, lead_lasts

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g1"
ALPHAS = (0.25, 0.30, 1 / 3)
KS = (2160, 1620, 1080)
MINUTES = (1, 2, 5, 10, 20, 30, 60)
DELAYS = (0, 5, 10, 20, 30)
SAMPLES = 20_000
EPS = 1e-9


def factor(name: str, kw: dict, alpha: float, k: int, m: int, minutes: float, seed: int) -> dict:
    window = 6 * math.floor(k / F)
    return dict(model=name, alpha=round(alpha, 4), k=k, sub_windows=m, minutes=minutes,
                factor=delayed_factor(F, alpha, window, m, minutes, SAMPLES, seed, **kw))


def main() -> None:
    ms = {n: kw for n, (kw, _) in models().items() if n != "random, testnet"}
    rows = [dict(model=n, alpha=round(a, 4), minutes=t, p_lasts=lead_lasts(F, a, 60 * t, **kw))
            for n, kw in ms.items() for a in ALPHAS for t in MINUTES]
    OUT.mkdir(parents=True, exist_ok=True)
    lasts = pd.DataFrame(rows)
    lasts.to_csv(OUT / "lasts.csv", index=False)
    print(lasts.pivot_table(index=["model", "alpha"], columns="minutes", values="p_lasts")
          .to_string(float_format=lambda v: f"{v:.2g}"))

    b7 = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}
    pts = [(n, a, k, t) for n in ms for a in ALPHAS for k in KS for t in DELAYS]
    m_of = {k: int(b7[b7.k == k].sub_windows.iloc[0]) for k in KS}
    out = Parallel(n_jobs=-2)(delayed(factor)(n, ms[n], a, k, m_of[k], t, 7919 * k + 31 * int(a * 1000) + 7 * t)
                              for n, a, k, t in pts)
    for (n, a, k, _), r in zip(pts, out):
        at = depth_reader(ms[n], a, log_ub)
        x = b7[(b7.model == n) & (b7.alpha == round(a, 4)) & (b7.k == k)].iloc[0]
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_two"] = at(math.log(EPS / r["factor"] ** 2))
        r["depth_two_lo"], r["depth_two_hi"] = x.depth_two_lo, x.depth_two_hi
    t = pd.DataFrame(out)
    t.to_csv(OUT / "factor.csv", index=False)
    print()
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
