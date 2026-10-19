"""Where do the occupied slots the countable rule loses sit in the fork tree? (cousins pilot)

The countable rule references only the first block of a fork. This script measures what a
deeper rule could recover at most. It runs a trajectory to equilibrium under the spec 1.2.5
rule (parent-anchored window, W = 12, parent order), takes the global block tree of the last
epoch, and classifies every occupied slot of the observation window ``[0, T)`` against the
final canonical chain:

* **canonical** — the slot holds a canonical block;
* **recovered** — otherwise, the slot holds an uncle carried by a canonical block that lies in
  the window (the spec's count, ``ref_scope="window"``);
* **lost** — neither. A lost slot is split by the smallest fork depth among its blocks
  (depth 1 = parent on the canonical chain), and a depth-2 lost slot is further marked when
  its depth-1 parent is itself a recovered uncle — the condition the cousin rule would add.

Shares are of all occupied slots in the window. The classification is static: it reads one
tree and ignores the feedback a larger count would have on the next epoch's difficulty, so it
is a ceiling for the cousin model, not a prediction of it. The depth-2 "parent referenced"
share depends on today's selector, which skips an uncle whose slot is already occupied.

Run:  python scripts/depth_profile.py    (writes runs/depth_profile.parquet, prints the table)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig

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


def classify(tree, A, T: int, E: int) -> dict:
    """Classify the occupied slots of ``[0, T)`` (see the module docstring)."""
    nb = tree.n_blocks
    ids = np.arange(nb)
    arrived = (A <= E).any(axis=0) if isinstance(A, np.ndarray) else np.ones(nb, dtype=bool)
    arrived[0] = True
    # best arrived tip by (height, -slot, -id), as fork.fork_stats picks it
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])
    canon = np.zeros(nb, dtype=bool)
    b = best
    while b > 0:
        canon[b] = True
        b = int(tree.parent[b])
    canon[0] = True
    # depth[b] = non-canonical run ending at b; a parent always has the smaller id
    depth = np.zeros(nb, dtype=np.int64)
    for b in range(1, nb):
        if not canon[b]:
            depth[b] = depth[int(tree.parent[b])] + 1
    win = (tree.slot >= 0) & (tree.slot < T) & (ids > 0)
    refd = np.zeros(nb, dtype=bool)
    for b in np.nonzero(canon & win)[0]:           # only in-window referencers count
        for u in tree.uncles[b]:
            refd[u] = True
    occupied = set(tree.slot[win].tolist())
    canonical = set(tree.slot[win & canon].tolist())
    recovered = set(tree.slot[win & refd].tolist()) - canonical
    lost = occupied - canonical - recovered
    by_slot: dict[int, list[int]] = {}
    for b in np.nonzero(win & ~canon)[0]:
        s = int(tree.slot[b])
        if s in lost:
            by_slot.setdefault(s, []).append(int(b))
    n_d = {1: 0, 2: 0, 3: 0, 4: 0}                 # 4 stands for depth >= 4
    d2_parent_ref = 0
    for bs in by_slot.values():
        dmin = min(int(depth[b]) for b in bs)
        n_d[min(dmin, 4)] += 1
        if dmin == 2 and any(depth[b] == 2 and refd[int(tree.parent[b])] for b in bs):
            d2_parent_ref += 1
    n = len(occupied)
    return dict(occupied=n, lost=len(lost) / n, lost_d1=n_d[1] / n, lost_d2=n_d[2] / n,
                lost_d2_parent_ref=d2_parent_ref / n, lost_d3=n_d[3] / n,
                lost_d4plus=n_d[4] / n, fork_rate=float((win & ~canon).sum() / win.sum()))


def _run(k: int, delay: float, cap: int, rep: int) -> dict:
    import tsi_sim.epoch as ep
    from tsi_sim.engine import run_trajectory

    captured: dict = {}
    build = ep.build_tree_pernode

    def capture(*a, **kw):
        tree, A = build(*a, **kw)
        captured["tree"], captured["A"] = tree, A
        return tree, A

    ep.build_tree_pernode = capture                # keep the LAST epoch's tree
    cfg = SimConfig(**BASE, k=k, blend_delay_max=delay, max_uncles=cap, replicate=rep)
    try:
        rows = run_trajectory(cfg)
    finally:
        ep.build_tree_pernode = build              # workers are reused across jobs
    out = classify(captured["tree"], captured["A"], cfg.period_T, cfg.epoch_len)
    return dict(k=k, blend_delay_max=delay, max_uncles=cap, replicate=rep,
                d_ratio_last=rows[-1]["mean_ratio"], **out)


def main() -> None:
    jobs = [(256, d, u, r) for d in DELAYS for u in CAPS for r in range(REPS)]
    jobs += [(2160, d, u, r) for d, u in FULL for r in range(FULL_REPS)]
    rows = Parallel(n_jobs=N_JOBS)(delayed(_run)(*j) for j in jobs)
    df = pd.DataFrame(rows)
    df.to_parquet(RUNS / "depth_profile.parquet")
    cols = ["lost", "lost_d1", "lost_d2", "lost_d2_parent_ref", "lost_d3", "lost_d4plus"]
    g = df.groupby(["k", "blend_delay_max", "max_uncles"])
    mean = g[cols].mean() * 100
    sem = g[cols].sem() * 100
    print("% of occupied slots in the window, mean (SEM)")
    for key in mean.index:
        cells = "  ".join(f"{c}={mean.loc[key, c]:.3f}({sem.loc[key, c]:.3f})" for c in cols)
        print(f"k={key[0]} delay={key[1]:g} U={key[2]}  {cells}")


if __name__ == "__main__":
    main()
