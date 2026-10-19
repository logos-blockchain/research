"""Where do the occupied slots the countable rule loses sit in the fork tree? (cousins pilot)

The countable rule references only the first block of a fork. This script measures what a
deeper rule could recover at most, under the spec 1.2.5 rule (parent-anchored window, W = 12,
parent order). Each epoch, the engine files every occupied slot of the observation window that
the count misses under the smallest fork depth among its blocks (``fork.lost_slots``; depth 1 =
parent on the canonical chain). It also marks the depth-2 slots whose fork's first block is a
counted uncle: the condition a cousin rule would add. The shares are of all occupied window
slots. They are averaged over each trajectory's post-burn-in epochs (``equilibrium``), then over
replicates.

The shares are a ceiling for a deeper rule, not a prediction of it. They describe trees grown
under today's rule, and ignore the feedback a larger count would have on the next epoch's
difficulty. The "parent referenced" share depends on today's selector, which skips an uncle
whose slot is already occupied.

Run:  python scripts/depth_profile.py    (writes runs/depth_profile.parquet, prints the table)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.plotting.figures_pernode import equilibrium

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

N_JOBS = 4
DELAYS = [4.0, 8.0, 16.0, 32.0]          # rho ~ 0.36 / 0.56 / 0.96 / 1.76 (§3.2)
CAPS = [1, 2, 4]
REPS = 10                                # at k = 256
FULL = [(16.0, 4), (32.0, 4)]            # (delay, U) cells re-run at k = 2160
FULL_REPS = 2

# The spec 1.2.5 rule: parent-anchored window at W = 12, oldest parent first.
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
            uncle_strategy="oldest", window_absorption=12.0, uncle_window_anchor="parent",
            uncle_order="parent", epochs=8, genesis_d_factor=1.0, early_stop=False)

COLS = ["lost_d1_share", "lost_d2_share", "lost_d2_parent_ref_share", "lost_d3_share",
        "lost_d4plus_share"]


def _run(k: int, delay: float, cap: int, rep: int) -> pd.DataFrame:
    cfg = SimConfig(**BASE, k=k, blend_delay_max=delay, max_uncles=cap, replicate=rep)
    return equilibrium(pd.DataFrame(run_trajectory(cfg)))


def main() -> None:
    jobs = [(256, d, u, r) for d in DELAYS for u in CAPS for r in range(REPS)]
    jobs += [(2160, d, u, r) for d, u in FULL for r in range(FULL_REPS)]
    df = pd.concat(Parallel(n_jobs=N_JOBS)(delayed(_run)(*j) for j in jobs), ignore_index=True)
    df["lost_share"] = df[[c for c in COLS if c != "lost_d2_parent_ref_share"]].sum(axis=1)
    df.to_parquet(RUNS / "depth_profile.parquet")
    cols = ["lost_share", *COLS]
    g = df.groupby(["k", "blend_delay_max", "max_uncles"])
    mean = g[cols].mean() * 100
    sem = g[cols].sem() * 100
    print("% of occupied slots in the window, mean (SEM over replicates)")
    for key in mean.index:
        cells = "  ".join(
            f"{c.removesuffix('_share')}={mean.loc[key, c]:.3f}({sem.loc[key, c]:.3f})"
            for c in cols)
        print(f"k={key[0]} delay={key[1]:g} U={key[2]} D/D={g.mean_ratio.mean()[key]:.4f}  {cells}")


if __name__ == "__main__":
    main()
