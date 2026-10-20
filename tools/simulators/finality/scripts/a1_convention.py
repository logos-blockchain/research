"""The random-delay convention and the engine's own arms (RATE.md A1, FURTHER.md G7).

    python scripts/a1_convention.py      # writes runs/a1/convention.csv (about 2 minutes on 4 cores)

The report's random-delay depths read B5's closed form, q = a / (a + (1 - a) g), at A1's growth
with every node producing on the specification's Blend: canonical blocks per slot over f, eight
runs on Pareto stakes. G6 and G7 read the same form at the growth per honest win, canonical blocks
per slot over (1 - a) lambda with lambda = -ln(1 - f), on B3's engine, whose stakes are equal. The
two differ in three ways, each measured here with every node producing, one Blend copy released
at the slot: the runs (A1's eight against 32 on its seeds), the stakes (Pareto against equal, on
A1's seeds), and the unit (per f against per win, which takes the adversary's rate as a f or as
a lambda; its exact rate 1 - (1 - f)^a lies between). Per setting: the orphan share and the growth
per f with their standard errors, and the depth at 1e-9 per f, at the exact rate and per win.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from a1_baseline import BASE, SPEC
from b3_race import BASE as B3_BASE
from finality_sim.baseline import run
from finality_sim.private_race import strict_depth

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "a1"
F = BASE["f"]
LAM = -math.log(1 - F)
SHARES = (0.25, 0.30, 1 / 3)
# (setting, engine settings, runs)
SETTINGS = (("A1, Pareto stakes", dict(BASE, **SPEC), 8),
            ("A1, Pareto stakes", dict(BASE, **SPEC), 32),
            ("A1's seeds, equal stakes", dict(BASE, **SPEC, stake_dist="uniform"), 32),
            ("B3's engine, equal stakes", dict(B3_BASE, **SPEC, adversary_frac=0.0), 64))


def one(settings: dict, rep: int) -> dict:
    m = run(SimConfig(**settings, replicate=rep))
    return dict(orphan=m.orphan_share, growth=m.growth_rate / F)


def depths(a: float, g_f: float) -> tuple[float, float, float]:
    """B5's depth at 1e-9 with the adversary's rate taken as a f, as 1 - (1 - f)^a and as a lambda,
    against the honest canonical rate (1 - a) g_f f."""
    h = (1 - a) * g_f * F
    return tuple(strict_depth(r / (r + h), math.log(1e-9))
                 for r in (a * F, 1 - (1 - F) ** a, a * LAM))


def main() -> None:
    runs = {}
    for name, s, n in SETTINGS:
        key = (name, s["stake_dist"], s.get("n_nodes"))
        if key not in runs:
            m = max(n2 for name2, _, n2 in SETTINGS if name2 == name)
            runs[key] = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(
                delayed(one)(s, r) for r in range(m)))
    rows = []
    for name, s, n in SETTINGS:
        g = runs[(name, s["stake_dist"], s.get("n_nodes"))].iloc[:n]
        g_f = float(g.growth.mean())
        for a in SHARES:
            d_f, d_x, d_w = depths(a, g_f)
            rows.append(dict(setting=name, runs=n, alpha=round(a, 4), orphan=float(g.orphan.mean()),
                             orphan_sem=float(g.orphan.std(ddof=1) / math.sqrt(n)), growth_per_f=g_f,
                             growth_per_f_sem=float(g.growth.std(ddof=1) / math.sqrt(n)),
                             growth_per_win=g_f * F / LAM, depth_per_f=d_f, depth_exact=d_x,
                             depth_per_win=d_w))
    t = pd.DataFrame(rows)
    # A1's eight runs are A1's own: the row must reproduce the growth A1 published.
    summary = OUT / "summary.csv"
    if summary.exists():
        a1 = pd.read_csv(summary)
        a1 = a1[(a1.family == "rounds") & (a1.blend_hops == 3) & (a1.blend_delay_max == 3.0)
                & (a1.link_latency_mean == 0.1)]
        if abs(float(a1.growth_per_f.iloc[0]) - float(t.growth_per_f.iloc[0])) > 1e-12:
            raise SystemExit("A1's eight runs do not reproduce runs/a1/summary.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "convention.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
