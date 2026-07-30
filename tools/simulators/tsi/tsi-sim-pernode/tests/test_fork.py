"""Fork rate and reorg depth from the global tree."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.fork import fork_stats


def make_tree(slots, parents, heights):
    n = len(slots)
    return BlockTree(
        slot=np.array(slots, np.int64), parent=np.array(parents, np.int64),
        height=np.array(heights, np.int64), leader=np.zeros(n, np.int64),
        uncles=[() for _ in range(n)],
    )


def test_no_forks():
    # a straight chain 1->2->3, no orphans
    tree = make_tree([-1, 0, 1, 2], [-1, 0, 1, 2], [0, 1, 2, 3])
    fr, mx, mn, pr = fork_stats(tree, None, T=10, cutoff=100)
    assert fr == 0.0 and mx == 0 and mn == 0.0


def test_single_orphan_depth_one():
    # canonical 1(s0),2(s1),4(s3); orphan 3(s2) hangs off block1 -> branch depth 1
    tree = make_tree([-1, 0, 1, 2, 3], [-1, 0, 1, 1, 2], [0, 1, 2, 2, 3])
    fr, mx, mn, pr = fork_stats(tree, None, T=10, cutoff=100)
    assert mx == 1
    assert abs(fr - 1 / 4) < 1e-9        # 1 orphan of 4 in-window blocks


def test_deep_orphan_branch():
    # canonical spine 1..3 (heights 1,2,3); a 2-deep orphan branch 4->5 off block1
    # blocks: 0 gen; 1(s0,h1),2(s1,h2),3(s2,h3) canonical; 4(s1,h2)->1, 5(s2,h3)->4 orphan
    tree = make_tree([-1, 0, 1, 2, 1, 2], [-1, 0, 1, 2, 1, 4], [0, 1, 2, 3, 2, 3])
    fr, mx, mn, pr = fork_stats(tree, None, T=10, cutoff=100)
    assert mx == 2                        # branch 4->5 is 2 deep
    assert abs(fr - 2 / 5) < 1e-9         # 2 orphans of 5


def test_engine_reports_fork_columns():
    cfg = SimConfig(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=16.0, max_uncles=1, uncle_window=300, k=256, epochs=8)
    df = pd.DataFrame(run_trajectory(cfg))
    for col in ("fork_rate", "max_reorg_depth", "mean_reorg_depth"):
        assert col in df.columns
    # heavy delay -> real forks
    assert df[df.epoch >= 4].fork_rate.mean() > 0.0
    assert df.max_reorg_depth.max() >= 1
