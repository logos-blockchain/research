"""Phase I.3: B5's partition test on the engine (PLAN.md, I.3).

    python scripts/b5_partition_engine.py              # needs runs/a1; writes runs/b5/partition_engine*.csv (about 20 minutes on 4 cores)
    python scripts/b5_partition_engine.py summarise    # the tables again from the runs already made

The engine (tsi_sim, partition_share / partition_start / partition_slots) splits the honest nodes
into a side holding a share s of all stake and the rest, for a 36-hour span, while a coalition of
share alpha withholds every block it wins (finality_sim.partition). On the specification's Blend
with B3's settings, 256 runs a cell and 512 for the ties, in four variants: the coalition's nodes
on the rest's side of the cut or on the side's (partition_adversary_side, the adversary's choice),
and one Blend copy or the specification's two (blend_copies). Per cell: each side's density over
the span, as rule 8 counts it, and the coalition's fork's; the share of runs in which the fork is
strictly denser than the side; each side's growth per occupied slot, its chain's blocks in the
span over the slots its leaders occupied there, which is the unit of A1's growth and of B5's
closed form (finality_sim.recovery.log_failure), read at the side's realised share at A1's growth
and at the side's own growth; the share of runs in which each side's chain is the longer at the
span's end, which the longest-chain rule follows at rejoin; each side's density against the
threshold of H.1's detector (finality_sim.further.detector_power); and, without a coalition, the
share of runs in which two even sides tie in density, beside ties.csv.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b3_race import BASE, CONFIGS
from finality_sim.further import detector_power
from finality_sim.partition import measure
from finality_sim.recovery import log_failure

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b5"
F = 1 / 30
ALPHAS = (0.25, 0.30, 1 / 3)
SIDES = (0.30, 0.35, 0.40)
VARIANTS = (("rest", 1), ("side", 1), ("rest", 2), ("side", 2))   # the coalition's nodes, Blend copies
REPLICATES = 256
TIE_REPLICATES = 512
K = 512                                   # an epoch of 153,600 slots holds the span and a rejoin
START = 10_000
SPAN = 36 * 3600
EPS_DETECTOR = 1e-9


def one(alpha: float, side: float, where: str, copies: int, rep: int) -> dict:
    cfg = SimConfig(**{**BASE, "k": K}, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep,
                    partition_share=side, partition_start=START, partition_slots=SPAN,
                    partition_adversary_side=where, blend_copies=copies)
    return dict(alpha_set=round(alpha, 4), side_set=round(side, 4), adversary_side=where, copies=copies,
                replicate=rep, **measure(cfg))


def a1_growth() -> float:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    return float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])


def summarise(df: pd.DataFrame, g: float) -> pd.DataFrame:
    out = []
    for (a, sd, where, copies), grp in df.groupby(["alpha_set", "side_set", "adversary_side", "copies"],
                                                  sort=False):
        n = len(grp)
        share_a, share_b = float(grp.share_a.mean()), float(grp.share_b.mean())
        growth_a = float(grp.density_a.mean() / grp.occupied_a.mean())
        growth_b = float(grp.density_b.mean() / grp.occupied_b.mean())
        beaten = float(np.mean(grp.fork > grp.density_a))
        sem = math.sqrt(max(beaten * (1 - beaten), 1e-4) / n)
        row = dict(alpha=a, side=sd, adversary_side=where, copies=copies, runs=n, share_small=share_a,
                   share_other=share_b, density_small=float(grp.density_a.mean()),
                   density_other=float(grp.density_b.mean()), fork=float(grp.fork.mean()),
                   growth_small=growth_a, growth_other=growth_b, growth_a1=g,
                   beaten=beaten, beaten_or_tie=float(np.mean(grp.fork >= grp.density_a)), beaten_sem=sem,
                   small_longer=float(np.mean(grp.length_a > grp.length_b)),
                   other_longer=float(np.mean(grp.length_b > grp.length_a)),
                   equal_length=float(np.mean(grp.length_a == grp.length_b)),
                   density_tie=float(np.mean(grp.density_a == grp.density_b)))
        if a > 0:
            cf_a1 = math.exp(log_failure(SPAN, a, F, growth=g, honest=share_a))
            cf_side = math.exp(log_failure(SPAN, a, F, growth=growth_a, honest=share_a))
            row.update(closed_form=cf_a1, closed_form_side_growth=cf_side,
                       z_a1=(cf_a1 - beaten) / sem, z_side=(cf_side - beaten) / sem)
        threshold, (power_a, power_b) = detector_power(a, g, SPAN, EPS_DETECTOR, (share_a, share_b), F)
        row.update(detector_threshold=threshold, detector_small=float(np.mean(grp.density_a < threshold)),
                   detector_other=float(np.mean(grp.density_b < threshold)),
                   detector_small_closed=power_a, detector_other_closed=power_b)
        out.append(row)
    return pd.DataFrame(out)


def main(rerun: bool = True) -> None:
    g = a1_growth()
    if rerun:
        cells = ([(a, sd, where, copies, REPLICATES) for where, copies in VARIANTS for a in ALPHAS for sd in SIDES]
                 + [(0.0, 0.5, "rest", copies, TIE_REPLICATES) for copies in (1, 2)])
        rows = Parallel(n_jobs=4, backend="loky")(delayed(one)(a, sd, where, copies, r)
                                                  for a, sd, where, copies, n in cells for r in range(n))
        pd.DataFrame(rows).to_parquet(OUT / "partition_engine_runs.parquet")
    t = summarise(pd.read_parquet(OUT / "partition_engine_runs.parquet"), g)
    base = (t["adversary_side"] == "rest") & (t.copies == 1)
    t[base].to_csv(OUT / "partition_engine.csv", index=False)
    t.to_csv(OUT / "partition_engine_variants.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main(rerun=sys.argv[1:] != ["summarise"])
