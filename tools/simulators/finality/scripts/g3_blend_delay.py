"""Phase G3: Blend's delay as a lever (PLAN.md, G3).

    python scripts/g3_blend_delay.py      # needs runs/a1, runs/b7; writes runs/g3/blend_delay.csv

For each Blend setting A1 measured (hops, rounds of mixing delay, 0.1 s links): its 99th-percentile
full delay, orphan share and canonical growth g; the depth and time to settle at 1e-9 under random
delay (B5's closed form, the private race with a premined lead, on the clock 30 s / ((1 - alpha) g))
and under a worst case of Delta = ceil(p99) seconds (B2's upper bound, on the clock Delta + 1/p_h
slots a block), without grinding and with the nonce of B7 under G1's delay, whose factor per nonce
is the choices at the cut-off, E[G_min] at k = 2160 (runs/b7/minimum.csv), met twice. The privacy
columns are the Blend report's: a message's whole path is adversarial with chance f_adv^hops, read
at f_adv = 1/3, and the anonymity set a relay blends grows with (2 M + 1)/3 for M rounds of delay.
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


def worst(alpha: float, delay_s: int, factor: float) -> tuple[float, float]:
    ub = upper(alpha, delay_s, K_MAX, floor=EPS / factor ** 2 / 4)
    plain = float(first_depth(ub, EPS)) if ub.min() <= EPS else math.inf
    ground = float(first_depth(ub, EPS / factor ** 2)) if ub.min() <= EPS / factor ** 2 else math.inf
    return plain, ground


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)].sort_values(["blend_hops", "blend_delay_max"])
    b7 = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    g_min = {a: float(b7[(b7.model == "worst, 10 s") & (b7.alpha == round(a, 4)) & (b7.k == 2160)].mean_g.iloc[0])
             for a in ALPHAS}
    deltas = sorted({int(math.ceil(v)) for v in s.vis_full_p99})
    jobs = [(a, d) for a in ALPHAS for d in deltas]
    got = Parallel(n_jobs=-2)(delayed(worst)(a, d, g_min[a]) for a, d in jobs)
    wd = dict(zip(jobs, got))
    rows = []
    for _, r in s.iterrows():
        d = int(math.ceil(r.vis_full_p99))
        for a in ALPHAS:
            g = float(r.growth_per_f)
            q = a / (a + (1 - a) * g)
            rnd = strict_depth(q, math.log(EPS))
            rnd_g = strict_depth(q, math.log(EPS / g_min[a] ** 2))
            ph = occupancy(F, 1 - a)
            clock_r, clock_w = 30 / ((1 - a) * g) / 3600, (d + 1 / ph) / 3600
            rows.append(dict(hops=int(r.blend_hops), rounds=int(r.blend_delay_max), p99_s=float(r.vis_full_p99),
                             delta_s=d, orphan=float(r.orphan_share), growth=g,
                             capture=(1 / 3) ** int(r.blend_hops), blending=(2 * int(r.blend_delay_max) + 1) / 3,
                             alpha=round(a, 4), g_min=g_min[a],
                             random_depth=rnd, random_h=rnd * clock_r,
                             random_ground_depth=rnd_g, random_ground_h=rnd_g * clock_r,
                             worst_depth=wd[(a, d)][0], worst_h=wd[(a, d)][0] * clock_w,
                             worst_ground_depth=wd[(a, d)][1], worst_ground_h=wd[(a, d)][1] * clock_w))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "blend_delay.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
