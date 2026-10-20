"""Phase G3: Blend's delay as a lever (PLAN.md, G3).

    python scripts/g3_blend_delay.py      # needs runs/a1, runs/b7; writes runs/g3/blend_delay.csv

For each Blend setting A1 measured (hops, rounds of mixing delay, 0.1 s links): its 99th-percentile
full delay, orphan share and canonical growth g; the depth and time to settle at 1e-9 under random
delay (B5's closed form, the private race with a premined lead, on the clock 30 s / ((1 - alpha) g))
and under a worst case of Delta = ceil(p99) seconds (B2's upper bound, on the clock Delta + 1/p_h
slots a block), without grinding and with the nonce of B7 under G1's delay, whose factor per nonce
is at most the choices at the cut-off, E[G_min] at k = 2160 with B7's 25 sub-windows, met twice;
E[G_min] is sampled per setting and delay model (finality_sim.nonce.min_rule_choices, 20,000 windows
with 20,000 near slots): under random delay at the setting's growth, under the worst case at its
Delta, and only where the depth without grinding is finite. The privacy
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
from finality_sim.nonce import min_rule_choices
from finality_sim.private_race import strict_depth
from finality_sim.recovery import occupancy

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g3"
ALPHAS = (0.30, 1 / 3)
EPS = 1e-9
K_MAX = 8000


WINDOW = 6 * math.floor(2160 / F)
SUB_WINDOWS = 25
SAMPLES = 20_000


def g_min(alpha: float, seed: int, **kw) -> tuple[float, float]:
    """E[G_min] and the share of windows whose deepest fork reaches past the near slots."""
    g, deep = min_rule_choices(F, alpha, WINDOW, SAMPLES, seed, sub_windows=SUB_WINDOWS, near_slots=20_000, **kw)
    return float(g.mean()), float(deep)


def worst(alpha: float, delay_s: int) -> tuple[float, float, float, float]:
    """The depth at 1e-9 under a worst case of ``delay_s`` without grinding, E[G_min] there and its
    deep share, and the depth with that factor met twice."""
    plain_ub = upper(alpha, delay_s, K_MAX, floor=EPS / 4)
    if plain_ub.min() > EPS:
        return math.inf, math.nan, math.nan, math.inf
    factor, deep = g_min(alpha, 7 * delay_s + int(alpha * 1000), delta=delay_s)
    ub = upper(alpha, delay_s, K_MAX, floor=EPS / factor ** 2 / 4)
    ground = float(first_depth(ub, EPS / factor ** 2)) if ub.min() <= EPS / factor ** 2 else math.inf
    return float(first_depth(plain_ub, EPS)), factor, deep, ground


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)].sort_values(["blend_hops", "blend_delay_max"])
    deltas = sorted({int(math.ceil(v)) for v in s.vis_full_p99})
    jobs = [(a, d) for a in ALPHAS for d in deltas]
    got = Parallel(n_jobs=4)(delayed(worst)(a, d) for a, d in jobs)
    wd = dict(zip(jobs, got))
    rjobs = [(a, float(r.growth_per_f), i) for a in ALPHAS for i, (_, r) in enumerate(s.iterrows())]
    rg = Parallel(n_jobs=4)(delayed(g_min)(a, 31 * i + int(a * 1000), growth=g) for a, g, i in rjobs)
    random_g = {(a, g): x for (a, g, _), x in zip(rjobs, rg)}
    rows = []
    for _, r in s.iterrows():
        d = int(math.ceil(r.vis_full_p99))
        for a in ALPHAS:
            g = float(r.growth_per_f)
            q = a / (a + (1 - a) * g)
            gm_r, deep_r = random_g[(a, g)]
            rnd = strict_depth(q, math.log(EPS))
            rnd_g = strict_depth(q, math.log(EPS / gm_r ** 2))
            ph = occupancy(F, 1 - a)
            clock_r, clock_w = 30 / ((1 - a) * g) / 3600, (d + 1 / ph) / 3600
            plain, gm_w, deep_w, ground = wd[(a, d)]
            rows.append(dict(hops=int(r.blend_hops), rounds=int(r.blend_delay_max), p99_s=float(r.vis_full_p99),
                             delta_s=d, orphan=float(r.orphan_share), growth=g,
                             capture=(1 / 3) ** int(r.blend_hops), blending=(2 * int(r.blend_delay_max) + 1) / 3,
                             alpha=round(a, 4), g_min_random=gm_r, deep_random=deep_r, g_min_worst=gm_w,
                             deep_worst=deep_w,
                             random_depth=rnd, random_h=rnd * clock_r,
                             random_ground_depth=rnd_g, random_ground_h=rnd_g * clock_r,
                             worst_depth=plain, worst_h=plain * clock_w,
                             worst_ground_depth=ground, worst_ground_h=ground * clock_w))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "blend_delay.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
