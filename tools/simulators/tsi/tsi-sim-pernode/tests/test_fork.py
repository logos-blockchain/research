"""Fork rate and reorg depth from the global tree."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

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
    fr, mx, mn, pr, _, _ = fork_stats(tree, None, T=10, cutoff=100)
    assert fr == 0.0 and mx == 0 and mn == 0.0


def test_single_orphan_depth_one():
    # canonical 1(s0),2(s1),4(s3); orphan 3(s2) hangs off block1 -> branch depth 1
    tree = make_tree([-1, 0, 1, 2, 3], [-1, 0, 1, 1, 2], [0, 1, 2, 2, 3])
    fr, mx, mn, pr, _, _ = fork_stats(tree, None, T=10, cutoff=100)
    assert mx == 1
    assert abs(fr - 1 / 4) < 1e-9        # 1 orphan of 4 in-window blocks


def test_deep_orphan_branch():
    # canonical spine 1..3 (heights 1,2,3); a 2-deep orphan branch 4->5 off block1
    # blocks: 0 gen; 1(s0,h1),2(s1,h2),3(s2,h3) canonical; 4(s1,h2)->1, 5(s2,h3)->4 orphan
    tree = make_tree([-1, 0, 1, 2, 1, 2], [-1, 0, 1, 2, 1, 4], [0, 1, 2, 3, 2, 3])
    fr, mx, mn, pr, _, _ = fork_stats(tree, None, T=10, cutoff=100)
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


def _lost_slots_tree():
    """Window [0, 20); canonical 1(s0) 2(s2) 5(s5) 11(s10) 12(s11) 13(s12) 15(s25) 16(s26).

    Fork off 2: 3(s3, depth 1) -> 4(s4, d2) -> 6(s6, d3) -> 7(s7, d4) -> 14(s14, d5), and a
    second child of 3, 8(s7, d2), sharing slot 7 with the depth-4 block 7.
    Fork off 5: 9(s8, d1) -> 10(s9, d2).
    Block 5 (in the window) carries uncle 3; block 15 (past the window) carries uncle 9.
    """
    #             id: 0   1  2  3  4  5  6  7  8  9 10  11  12  13  14  15  16
    tree = make_tree([-1, 0, 2, 3, 4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 14, 25, 26],
                     [-1, 0, 1, 2, 3, 2, 4, 6, 3, 5, 9, 5, 11, 12, 7, 13, 15],
                     [0, 1, 2, 3, 4, 3, 5, 6, 4, 4, 5, 4, 5, 6, 7, 7, 8])
    tree.uncles[5] = (3,)
    tree.uncles[15] = (9,)
    return tree


def test_lost_slots_by_depth_and_scope():
    from tsi_sim.fork import lost_slots

    tree = _lost_slots_tree()
    # Window scope (the spec rule): only block 5's reference counts, so slot 3 is covered.
    # Lost: s4 (d2, parent 3 counted), s6 (d3), s7 (shallowest d2 via block 8, parent 3
    # counted), s8 (d1), s9 (d2, parent 9 not counted), s14 (d5, filed under >= 4).
    w = lost_slots(tree, None, T=20, cutoff=100, scope_refs=True)
    assert w.occupied == 13
    assert w.by_depth == (1, 3, 1, 1)
    assert w.d2_parent_ref == 2
    # Chain scope: block 15's reference reaches back and covers slot 8, so its child's slot 9
    # now has a counted parent too.
    c = lost_slots(tree, None, T=20, cutoff=100, scope_refs=False)
    assert c.occupied == 13
    assert c.by_depth == (0, 3, 1, 1)
    assert c.d2_parent_ref == 3


@pytest.mark.parametrize("model,scope", [("countable", "window"), ("countable", "chain"),
                                         ("old", "window")])
def test_lost_slots_match_the_measured_count(monkeypatch, model, scope):
    """occupied - lost must equal the slot count measure() hands the estimator, exactly."""
    import tsi_sim.engine as engine
    import tsi_sim.epoch as ep
    from tsi_sim.fork import lost_slots

    seen: dict = {}
    build, sim = ep.build_tree_pernode, engine.simulate_epoch

    def capture_tree(*a, **kw):
        seen["tree"], seen["A"] = build(*a, **kw)
        return seen["tree"], seen["A"]

    def capture_result(*a, **kw):
        seen["er"] = sim(*a, **kw)
        return seen["er"]

    monkeypatch.setattr(ep, "build_tree_pernode", capture_tree)
    monkeypatch.setattr(engine, "simulate_epoch", capture_result)
    cfg = SimConfig(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=32.0, max_uncles=2, uncle_model=model, ref_scope=scope,
                    uncle_window_anchor="parent", window_absorption=12.0, k=64, epochs=2,
                    genesis_d_factor=1.0)
    run_trajectory(cfg)
    tree, A, er = seen["tree"], seen["A"], seen["er"]
    lost = lost_slots(tree, A, cfg.period_T, cfg.epoch_len,
                      scope_refs=scope == "window" and model != "old")
    assert lost.lost > 0                                     # the fixture loses slots
    if model == "countable":
        assert lost.by_depth[1] > 0      # ...and has deep forks the first-fork rule misses
    assert er.agreement_window == 1.0                        # one chain over the window
    assert lost.occupied == er.n_active_window
    assert np.all(er.m == lost.occupied - lost.lost)
    shares = (er.lost_d1_share, er.lost_d2_share, er.lost_d3_share, er.lost_d4plus_share)
    assert shares == tuple(n / lost.occupied for n in lost.by_depth)
    assert er.lost_d2_parent_ref_share == lost.d2_parent_ref / lost.occupied
