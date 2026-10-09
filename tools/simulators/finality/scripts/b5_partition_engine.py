"""Phase I.3: B5's partition test on the engine (PLAN.md, I.3).

    python scripts/b5_partition_engine.py      # needs runs/a1, runs/b5; writes runs/b5/partition_engine.csv

The engine (tsi_sim, partition_share / partition_start / partition_slots) splits the honest nodes
into a side holding a share s of all stake and the rest, for a 36-hour span, while a coalition of
share alpha withholds every block it wins (finality_sim.partition). On the specification's Blend
with B3's settings, 256 runs a cell and 512 for the ties: each side's density over the span, as
rule 8 counts it, and the coalition's fork's; the share of runs in which the fork is strictly
denser than the smaller side, beside B5's closed form at the side's realised share
(finality_sim.recovery.log_failure) at A1's growth and at the growth the side showed; each side's
growth per honest win against A1's; the share of runs in which the smaller side's chain is the
longer at the span's end, which the longest-chain rule follows at rejoin; and, without a
coalition, the share of runs in which two even sides tie in density, beside ties.csv.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b3_race import BASE, CONFIGS
from finality_sim.partition import measure
from finality_sim.recovery import log_failure, occupancy

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b5"
F = 1 / 30
ALPHAS = (0.25, 0.30, 1 / 3)
SIDES = (0.30, 0.35, 0.40)
REPLICATES = 256
TIE_REPLICATES = 512
K = 512                                   # an epoch of 153,600 slots holds the span and a rejoin
START = 10_000
SPAN = 36 * 3600


def one(alpha: float, side: float, rep: int) -> dict:
    cfg = SimConfig(**{**BASE, "k": K}, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep,
                    partition_share=side, partition_start=START, partition_slots=SPAN)
    return dict(alpha_set=round(alpha, 4), side_set=round(side, 4), replicate=rep, **measure(cfg))


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    g = float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])
    cells = [(a, sd, REPLICATES) for a in ALPHAS for sd in SIDES] + [(0.0, 0.5, TIE_REPLICATES)]
    rows = Parallel(n_jobs=-2, backend="loky")(delayed(one)(a, sd, r) for a, sd, n in cells for r in range(n))
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "partition_engine_runs.parquet")
    out = []
    for (a, sd), grp in df.groupby(["alpha_set", "side_set"], sort=False):
        small = grp.density_a if sd <= 0.5 else grp.density_b          # side a holds the share set
        other = grp.density_b if sd <= 0.5 else grp.density_a
        share_small = float(grp.share_a.mean())
        row = dict(alpha=a, side=sd, runs=len(grp), share_small=share_small,
                   share_other=float(grp.share_b.mean()),
                   density_small=float(small.mean()), density_other=float(other.mean()),
                   fork=float(grp.fork.mean()),
                   growth_small=float((grp.density_a / grp.made_a).mean()),
                   growth_other=float((grp.density_b / grp.made_b).mean()), growth_a1=g,
                   beaten=float(np.mean(grp.fork > small)), beaten_or_tie=float(np.mean(grp.fork >= small)),
                   closed_form=math.exp(log_failure(SPAN, a, F, growth=g, honest=share_small)) if a > 0 else math.nan,
                   closed_form_set=math.exp(log_failure(SPAN, a, F, growth=g, honest=sd)) if a > 0 else math.nan,
                   closed_form_side_growth=math.exp(log_failure(
                       SPAN, a, F, growth=float((grp.density_a / grp.made_a).mean()), honest=share_small)) if a > 0 else math.nan,
                   beaten_sem=float(np.sqrt(max(np.mean(grp.fork > small) * (1 - np.mean(grp.fork > small)), 1e-4) / len(grp))),
                   small_longer=float(np.mean(grp.length_a > grp.length_b)),
                   equal_length=float(np.mean(grp.length_a == grp.length_b)),
                   density_tie=float(np.mean(grp.density_a == grp.density_b)))
        out.append(row)
    t = pd.DataFrame(out)
    t.to_csv(OUT / "partition_engine.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
