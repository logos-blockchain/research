"""Phase G7: the total-stake inference as a lever (FURTHER.md, G7).

    python scripts/g7_inference.py      # needs runs/b2; writes runs/g7/*.csv (about 3 minutes on 14 cores)

A coalition that withholds every block it wins for a period lowers the inferred stake by its share
and raises every lottery threshold by 1/(1 - alpha) for the next epoch (finality_sim.inference).

inference.csv, per share: the raise; the worst case of Delta = 10 s read at the old rates,
Delta/(1 - alpha); B2's proven depth at 1e-9 there (scripts/b2_settlement.upper) and the hours on
the raised worst-case clock, Delta + 1/f; the engine's orphan share and growth per honest win at
the raised block rate on the specification's Blend (C1's settings, 8 replicates, interval
30 (1 - alpha) s), the private race's closed form at 1e-9 at that growth (B5) and its hours on
the raised random-delay clock; the time k = 2160 blocks take on the raised honest chain; and the
most the coalition gains by choosing the raise level after seeing its own wins, the Brownian value
sqrt(2M/pi) and a Monte Carlo of the Poisson path, as a share of its wins.

clamp.csv: the periods and days a coalition needs to lower the inferred stake by its share when
the inference lowers it by at most a cap a period, for caps of 5, 10 and 20 % and k = 2160.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F, first_depth, upper
from c1_rate import BASE, REPLICATES
from finality_sim.baseline import run
from finality_sim.inference import (deflated_delay, extra_wins, periods_to_deflate, raise_factor,
                                    raised_rates, selection_excess)
from finality_sim.private_race import strict_depth
from finality_sim.recovery import occupancy
from tsi_sim.config import SimConfig

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g7"
ALPHAS = (0.25, 0.30, 1 / 3)
DELTA = 10.0
EPS = 1e-9
K = 2160


def growth(alpha: float, rep: int) -> dict:
    interval = 30.0 * (1.0 - alpha)
    cfg = SimConfig(**BASE, f=1 / interval, blend_hops=3, blend_delay_max=3.0, replicate=rep)
    m = run(cfg)
    return dict(alpha=round(alpha, 4), replicate=rep, orphan=m.orphan_share,
                growth=m.growth_rate * interval)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(a, r) for a in ALPHAS for r in range(REPLICATES)]
    g = pd.DataFrame(Parallel(n_jobs=-2, backend="loky")(delayed(growth)(*j) for j in jobs))
    g = g.groupby("alpha", sort=False).agg(orphan=("orphan", "mean"), growth=("growth", "mean")).reset_index()
    base = pd.read_csv(HERE / "runs" / "c1" / "summary.csv")
    g0 = float(base[(base.hops == 3) & (base.delta_max == 3) & (base.interval == 30)].growth_per_f.iloc[0])
    lam = -math.log(1 - F)
    epoch = 10 * math.floor(K / F)
    period = 6 * math.floor(K / F)
    rows = []
    for a in ALPHAS:
        raise_ = raise_factor(a)
        d_eq = deflated_delay(DELTA, a)
        depth_w = first_depth(upper(a, d_eq, 6000, floor=EPS / 10), EPS)
        h_r, a_r = raised_rates(F, a)
        clock_w = DELTA + 1.0 / h_r                                  # the raised worst-case clock
        gr = float(g[g.alpha == round(a, 4)].growth.iloc[0])
        q0, q1 = a / (a + (1 - a) * g0), a / (a + (1 - a) * gr)
        d0, d1 = strict_depth(q0, math.log(EPS)), strict_depth(q1, math.log(EPS))
        clock_r = 1.0 / (gr * lam * raise_)                           # honest canonical blocks per slot, raised
        m = extra_wins(F, a, epoch)
        levels = int(round(period * occupancy(F, a)))                # one level per block it can withhold
        brown, mc = selection_excess(m, levels, 20_000, 7 + int(a * 1000))
        rows.append(dict(alpha=round(a, 4), raise_factor=raise_, delay_eq_s=d_eq,
                         worst_depth_base=int(pd.read_csv(HERE / "runs" / "b2" / "depths.csv").query(
                             "delay_s == 10 and eps == 1e-9 and abs(adv - @a) < 1e-3").ub_depth.iloc[0]),
                         worst_depth=depth_w, worst_hours=depth_w * clock_w / 3600,
                         orphan=float(g[g.alpha == round(a, 4)].orphan.iloc[0]), growth=gr, growth_base=g0,
                         random_depth_base=d0, random_depth=d1, random_hours=d1 * clock_r / 3600,
                         k_hours=K * clock_r / 3600, extra_wins=m, levels=levels,
                         excess_brownian=brown, excess_mc=mc,
                         excess_share=mc / (epoch * a_r)))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "inference.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    rows = []
    for cap in (0.05, 0.10, 0.20):
        row = dict(cap=cap)
        for a in ALPHAS:
            n = periods_to_deflate(a, cap)
            row[f"periods_{round(a, 4)}"] = n
            row[f"days_{round(a, 4)}"] = n * period / 86_400
        rows.append(row)
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "clamp.csv", index=False)
    print()
    print(c.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
