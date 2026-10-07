"""Phase G3: Blend's delay as a lever (PLAN.md, G3).

    python scripts/g3_blend_delay.py      # needs runs/a1; writes runs/g3/blend_delay.csv

For each Blend setting A1 measured (hops, rounds of mixing delay, 0.1 s links): its 99th-percentile
full delay, orphan share and canonical growth g; the depth and time to settle at 1e-9 without
grinding under random delay (B5's closed form, the private race with a premined lead, on the clock
30 s / ((1 - alpha) g)); and under a worst case of Delta = ceil(p99) seconds (B2's upper bound, on
the clock Delta + 1/p_h slots a block). Grinding (B6) and the nonce of B7 multiply these depths
alike; this lever is read without them.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F, first_depth, upper
from finality_sim.private_race import strict_depth
from finality_sim.recovery import occupancy

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g3"
ALPHAS = (0.30, 1 / 3)
EPS = 1e-9
K_MAX = 8000


def worst(alpha: float, delay_s: int) -> float:
    ub = upper(alpha, delay_s, K_MAX, floor=EPS / 4)
    return float(first_depth(ub, EPS)) if ub.min() <= EPS else math.inf


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)].sort_values(["blend_hops", "blend_delay_max"])
    deltas = sorted({int(math.ceil(v)) for v in s.vis_full_p99})
    jobs = [(a, d) for a in ALPHAS for d in deltas]
    got = Parallel(n_jobs=-2)(delayed(worst)(a, d) for a, d in jobs)
    wd = dict(zip(jobs, got))
    rows = []
    for _, r in s.iterrows():
        d = int(math.ceil(r.vis_full_p99))
        for a in ALPHAS:
            g = float(r.growth_per_f)
            q = a / (a + (1 - a) * g)
            rnd = strict_depth(q, math.log(EPS))
            ph = occupancy(F, 1 - a)
            rows.append(dict(hops=int(r.blend_hops), rounds=int(r.blend_delay_max), p99_s=float(r.vis_full_p99),
                             delta_s=d, orphan=float(r.orphan_share), growth=g, alpha=round(a, 4),
                             random_depth=rnd, random_h=rnd * 30 / ((1 - a) * g) / 3600,
                             worst_depth=wd[(a, d)], worst_h=wd[(a, d)] * (d + 1 / ph) / 3600))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "blend_delay.csv", index=False)
    with pd.option_context("display.width", 200):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
