"""Deeper references (``SimConfig.uncle_depth``): the oracle, both kernels, and selection.

Counting fixture, window T = 40, reference window w = 10:
canonical 1(s0) -> 2(s2) -> 3(s5) -> 4(s12) -> 5(s14) -> 6(s16) -> 13(s18) -> 14(s20, tip),
the longest chain.
Fork off 3 (fork point s5): 7(s6, depth 1) -> 8(s7, d2) -> 9(s8, d3) -> 10(s9, d4).
Fork off 2 (fork point s2): 11(s3, d1) -> 12(s4, d2).
Block 4 carries (7, 8), block 5 carries (9, 12), block 6 carries (10,). Uncle 11 is never
referenced, so 12 fails the ancestry condition. Under the parent anchor the window is measured
to the fork point: 12 sits 12 slots from its fork point at block 5, and 10 sits 11 from its fork
point at block 6, so both are outside w = 10. Under the uncle anchor both are inside.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig
from tsi_sim.measure import measure
from tsi_sim.tsi import countable_refs, density_m
from tsi_sim.uncles import select_uncles_at_production

W = 10
T = 40
CANONICAL = [14, 13, 6, 5, 4, 3, 2, 1]


def _tree() -> BlockTree:
    #                  id: 0   1  2  3   4   5   6  7  8  9  10 11 12  13  14
    tree = BlockTree(
        slot=np.array([-1, 0, 2, 5, 12, 14, 16, 6, 7, 8, 9, 3, 4, 18, 20], np.int64),
        parent=np.array([-1, 0, 1, 2, 3, 4, 5, 3, 7, 8, 9, 2, 11, 6, 13], np.int64),
        height=np.array([0, 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 3, 4, 7, 8], np.int64),
        leader=np.arange(15, dtype=np.int64),
        uncles=[() for _ in range(15)],
    )
    tree.uncles[4] = (7, 8)
    tree.uncles[5] = (9, 12)
    tree.uncles[6] = (10,)
    return tree


# (max_depth, parent_anchor) -> countable set
EXPECTED = {
    (1, False): {7}, (1, True): {7},
    (2, False): {7, 8}, (2, True): {7, 8},
    (3, False): {7, 8, 9}, (3, True): {7, 8, 9},
    (4, False): {7, 8, 9, 10}, (4, True): {7, 8, 9},
    (0, False): {7, 8, 9, 10, 12}, (0, True): {7, 8, 9},
}
# references the depth rule rejects (deeper arms; checked before the window)
DEEP = {2: 3, 3: 2, 4: 1, 0: 0}
CANON_SLOTS = 8                                    # {0, 2, 5, 12, 14, 16, 18, 20}


@pytest.mark.parametrize(("depth", "anchor"), sorted(EXPECTED))
def test_oracle(depth, anchor):
    got = countable_refs(_tree(), CANONICAL, W, T, parent_anchor=anchor, max_depth=depth)
    assert got == EXPECTED[(depth, anchor)]


@pytest.mark.parametrize("use_numba", [False, True])
@pytest.mark.parametrize(("depth", "anchor"), sorted(EXPECTED))
def test_kernels_match_the_oracle(depth, anchor, use_numba):
    tree = _tree()
    A = np.zeros((2, tree.n_blocks))               # both nodes received everything
    active = np.unique(tree.slot[1:])
    ms = measure(tree, A, active, T, cutoff=30, use_numba=use_numba, countable=True, w=W,
                 parent_anchor=anchor, max_depth=depth)
    want = CANON_SLOTS + len(EXPECTED[(depth, anchor)])   # every uncle sits in its own slot
    assert want == density_m(tree, CANONICAL, T, countable=True, w=W, parent_anchor=anchor,
                             max_depth=depth)
    np.testing.assert_array_equal(ms.m, [want, want])
    if depth != 1:
        np.testing.assert_array_equal(ms.ref_deep, [DEEP[depth]] * 2)


def _capture_epoch(monkeypatch, cfg):
    import tsi_sim.epoch as ep
    from tsi_sim.engine import run_trajectory

    seen: dict = {}
    build = ep.build_tree_pernode

    def capture(*a, **kw):
        seen["tree"], seen["A"] = build(*a, **kw)
        return seen["tree"], seen["A"]

    monkeypatch.setattr(ep, "build_tree_pernode", capture)
    rows = run_trajectory(cfg)
    return seen["tree"], seen["A"], pd.DataFrame(rows)


def _deep_cfg(depth, **kw):
    base = dict(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                blend_delay_max=32.0, max_uncles=4, uncle_window_anchor="parent",
                window_absorption=12.0, uncle_order="parent", uncle_depth=depth, k=64,
                epochs=2, genesis_d_factor=1.0)
    return SimConfig(**{**base, **kw})


@pytest.mark.parametrize("depth", [2, 3, 0])
def test_kernels_match_the_oracle_on_simulated_trees(monkeypatch, depth):
    from tsi_sim.blocktree import tips_for_all_nodes
    from tsi_sim.fork import canonical_and_depth

    cfg = _deep_cfg(depth)
    tree, A, _ = _capture_epoch(monkeypatch, cfg)
    T, E, w = cfg.period_T, cfg.epoch_len, cfg.effective_uncle_window
    canon, fork_depth = canonical_and_depth(tree, A, E)
    carried = [u for b in np.nonzero(canon)[0] for u in tree.uncles[b]]
    assert max(int(fork_depth[u]) for u in carried) >= 2  # the tree has deeper entries
    active = np.unique(tree.slot[tree.slot >= 0])
    got = {nb: measure(tree, A, active, T, E, use_numba=nb, countable=True, w=w,
                       parent_anchor=True, max_depth=depth) for nb in (False, True)}
    np.testing.assert_array_equal(got[False].m, got[True].m)
    tips = tips_for_all_nodes(tree, A, E)
    for tip in np.unique(tips):
        want = density_m(tree, tree.ancestors(int(tip)), T, countable=True, w=w,
                         parent_anchor=True, max_depth=depth)
        np.testing.assert_array_equal(got[True].m[tips == tip], want)


@pytest.mark.parametrize("depth", [2, 3, 0])
def test_selection_and_counting_agree_end_to_end(monkeypatch, depth):
    """Counting must accept every entry selection emits, and deeper entries must occur."""
    from tsi_sim.fork import canonical_and_depth

    cfg = _deep_cfg(depth)
    tree, A, df = _capture_epoch(monkeypatch, cfg)
    assert (df.deep_ref_share == 0.0).all(), df.deep_ref_share.tolist()
    canon, fork_depth = canonical_and_depth(tree, A, cfg.epoch_len)
    carried = [u for b in np.nonzero(canon)[0] for u in tree.uncles[b]]
    assert max(int(fork_depth[u]) for u in carried) >= 2   # deeper entries were counted


# --- selection --------------------------------------------------------------------------
# chain 1(s0) -> 2(s2) -> 3(s4) -> 8(s10); the producer extends 8 at t = 11.
# Fork off 2: 4(s4, depth 1, its slot already occupied by block 3) -> 5(s5, d2) -> 7(s7, d3).
# Fork off 3: 6(s6, d1, a free slot).
SEL_SLOT = np.array([-1, 0, 2, 4, 4, 5, 6, 7, 10], np.int64)
SEL_PARENT = np.array([-1, 0, 1, 2, 2, 4, 3, 5, 3], np.int64)


def _select(depth, cap, uncles=None, arrival=None, **kw):
    cfg = SimConfig(max_uncles=cap, uncle_window_anchor=kw.pop("anchor", "parent"),
                    uncle_order=kw.pop("order", "parent"), uncle_depth=depth, **kw)
    uncles = uncles or [() for _ in range(9)]
    arrival = np.zeros(9) if arrival is None else arrival
    return select_uncles_at_production(SEL_SLOT, SEL_PARENT, uncles, arrival, nb=9,
                                       parent_id=8, t=11, config=cfg,
                                       rng=np.random.default_rng(0))


def test_depth_one_is_the_first_fork_rule():
    assert _select(1, 4) == (6,)          # 4's slot is occupied; 5 and 7 are deeper


def test_a_missing_fork_block_is_carried_first():
    assert _select(2, 2) == (4, 5)        # 4 adds no slot, but unlocks 5
    assert _select(2, 4) == (4, 5, 6)     # 7 is too deep at depth 2


def test_no_room_to_unlock_leaves_the_entry_for_a_cheaper_one():
    assert _select(2, 1) == (6,)          # 5 would cost two entries
    assert _select(3, 1) == (6,)          # 7 would cost three


def test_a_referenced_fork_block_needs_no_entry():
    uncles = [() for _ in range(9)]
    uncles[8] = (4,)                      # the chain already carries 4
    assert _select(2, 1, uncles=uncles) == (5,)


def test_depth_three_and_the_parent_order():
    # by fork point: 5 and 7 (fork point s2) before 6 (fork point s4)
    assert _select(3, 4) == (4, 5, 7, 6)
    # by the uncle's own slot: 5 (s5), 6 (s6), 7 (s7)
    assert _select(3, 4, order="uncle") == (4, 5, 6, 7)


def test_the_ceiling_needs_no_ancestry():
    assert _select(0, 2) == (5, 7)        # no fork block carried; oldest fork point first


def test_the_fork_point_must_lie_in_the_window():
    # w = 8 slots (f = 0.25, W = 2): the window at t = 11 starts at s3. Fork point 2 (s2) is
    # out under the parent anchor, so only 6 (fork point 3, s4) qualifies.
    assert _select(3, 4, f=0.25, window_absorption=2.0) == (6,)
    # Under the uncle anchor the window is measured to each entry's own slot.
    assert _select(3, 4, f=0.25, window_absorption=2.0, anchor="uncle",
                   order="uncle") == (4, 5, 6, 7)


def test_a_fork_block_out_of_view_cannot_be_carried():
    arrival = np.zeros(9)
    arrival[4] = 99.0                     # the producer has not received 4
    assert _select(3, 4, arrival=arrival) == (6,)


# --- configuration ----------------------------------------------------------------------
@pytest.mark.parametrize("kw", [dict(uncle_depth=-1),
                                dict(uncle_depth=2, uncle_model="old"),
                                dict(uncle_depth=2, uncle_strategy="random")])
def test_validation(kw):
    with pytest.raises(ValueError):
        SimConfig(**kw)


def test_depth_key_is_tagged_and_paired():
    a = SimConfig(uncle_window_anchor="parent")
    b = SimConfig(uncle_window_anchor="parent", uncle_depth=2)
    assert a.key() != b.key()
    assert a.key() == SimConfig(uncle_window_anchor="parent", uncle_depth=1).key()
    pa = SimConfig(uncle_window_anchor="parent", paired_streams=True)
    assert pa.seed_key() == SimConfig(uncle_window_anchor="parent", uncle_depth=0,
                                      paired_streams=True).seed_key()
