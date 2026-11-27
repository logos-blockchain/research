"""Re-rooting (PLAN.md Phase 2b) and the wait for off-chain parents (Phase 2d).

Watch fixture (ids in production order):
chain 1(s0) -> P = 2(s1); a competing branch 1 -> 3(s2) -> b = 5(s3, h3).
P -> S = 4(s3, h3), a sibling of x; P -> x = 6(s4, h3), the watched block.
x -> 7(s6, h4); b -> 8(s8, h4). Ranks at h3: S > b > x (earlier slot, then lower id).
The leader of x sees blocks 1, 2 and x by slot 4, and the rest later (the scenarios vary it).
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from tsi_sim.blocktree import (
    BlockTree,
    _Copies,
    _fork_point,
    _off_chain_parents,
    _parent_wait_row,
    _wait,
    _Watch,
)
from tsi_sim.config import SimConfig, SweepConfig
from tsi_sim.fork import fork_stats, lost_slots, parent_wait
from tsi_sim.measure import measure
from tsi_sim.tsi import countable_refs, density_m

# --- the watch ------------------------------------------------------------------------------
W_SLOT = np.array([-1, 0, 1, 2, 3, 3, 4, 6, 8], np.int64)
W_PARENT = np.array([-1, 0, 1, 1, 2, 3, 2, 6, 5], np.int64)
W_HEIGHT = np.array([0, 1, 2, 2, 3, 3, 3, 4, 4], np.int64)
X = 6


def _keys(height, slot):
    n = height.shape[0]
    c2 = np.int64(n + 1)
    c1 = np.int64(100) * c2
    return height * c1 - slot * c2 - np.arange(n, dtype=np.int64)


def _watch(arr, t_check):
    """Watch x from its slot, observe every later block, check at each time in ``t_check``."""
    key = _keys(W_HEIGHT, W_SLOT)
    wt = _Watch(X, arr, W_PARENT, key, W_SLOT, t=4, horizon=10.0, w=360)
    for b in (7, 8):
        wt.observe(b, W_PARENT)
    out = []
    for t in t_check:
        out.append(wt.check(t) if wt.armed else None)
    return out


def _arr(s, b, seven=20.0, eight=21.0):
    return np.array([0.0, 0.0, 0.5, 10.0, s, b, 4.0, seven, eight])


def test_a_sibling_keeps_x_at_depth_one():
    # S arrives first: the tip moves to S, still under P. Then x's child 7 outranks 8.
    assert _watch(_arr(s=6.0, b=7.0), [8.0, 25.0]) == [None, None]


def test_a_branch_outside_the_parent_puts_x_at_depth_two():
    # b, produced before x, arrives before S: the tip leaves P's subtree at b's arrival.
    assert _watch(_arr(s=7.5, b=7.0), [6.9, 8.0]) == [None, 5]
    assert _fork_point(W_PARENT, W_HEIGHT, X, 5) == 1


def test_simultaneous_arrivals_are_taken_by_rank():
    # x's child 7 (h4) and b (h3) arrive together: 7 outranks b, so the tip never leaves.
    assert _watch(_arr(s=9.0, b=7.0, seven=7.0), [8.0, 25.0]) == [None, None]


def test_the_watch_expires_with_the_window():
    key = _keys(W_HEIGHT, W_SLOT)
    assert _Watch(X, _arr(s=6.0, b=7.0), W_PARENT, key, W_SLOT, t=4, horizon=10.0,
                  w=360).expires == 364


def _private_eight(w):
    """S reaches the leader at 6 and b at 7, so the tip moves to S and stays under P. b's child
    8 (h4) is private (PLAN.md Phase 4) until a release updates its arrival in place."""
    arr = _arr(s=6.0, b=7.0, seven=30.0, eight=1000.0)
    wt = _Watch(X, arr, W_PARENT, _keys(W_HEIGHT, W_SLOT), W_SLOT, t=4, horizon=10.0, w=w)
    for b in (7, 8):
        wt.observe(b, W_PARENT)
    return arr, wt


def test_a_released_block_reaches_the_watch():
    arr, wt = _private_eight(360)
    assert wt.check(25.0) is None
    arr[8] = 9.0
    wt.renote(8)
    assert wt.armed and wt.check(26.0) == 8
    assert _fork_point(W_PARENT, W_HEIGHT, X, 8) == 1


def test_a_release_after_the_watch_expires_is_never_replayed():
    arr, wt = _private_eight(20)                       # expires at slot 24
    assert wt.check(24.0) is None
    arr[8] = 25.0
    wt.renote(8)
    assert not wt.armed


def test_copies_in_view_and_pruning():
    c = _Copies(n=2, base=100)
    for j, (slot_x, arr) in enumerate([(5, [3.0, 9.0]), (8, [7.0, 7.0])]):
        c.add(x=j, slot_x=slot_x, g=0, t_pub=arr[0], col=np.array(arr))
    np.testing.assert_array_equal(c.in_view(0, 7), [100, 101])
    np.testing.assert_array_equal(c.in_view(1, 7), [101])
    assert c.in_view(1, 6) is None
    c.prune(6)                                         # copy 0's slot 5 has left every window
    np.testing.assert_array_equal(c.in_view(0, 7), [101])


# --- counting a copy ------------------------------------------------------------------------
# canonical 1(s0) -> 2(s2) -> 5(s5) -> 6(s6) -> 7(s8) -> 8(s9, tip); fork off 2: 3(s3) -> 4(s4).
# Copy 9 re-roots 4 at slot 4 onto the fork point 2; copy 10 hangs it off 3, which is off the
# chain. Window w = 10, T = 20.
def _tree(carried):
    #                  id: 0   1  2  3  4  5  6  7  8
    tree = BlockTree(
        slot=np.array([-1, 0, 2, 3, 4, 5, 6, 8, 9], np.int64),
        parent=np.array([-1, 0, 1, 2, 3, 2, 5, 6, 7], np.int64),
        height=np.array([0, 1, 2, 3, 4, 3, 4, 5, 6], np.int64),
        leader=np.arange(9, dtype=np.int64),
        uncles=[() for _ in range(9)],
        copy_slot=np.array([4, 4], np.int64), copy_parent=np.array([2, 3], np.int64),
        copy_of=np.array([4, 4], np.int64), copy_pub=np.array([5.0, 5.0]),
    )
    tree.uncles[7] = carried
    return tree


CANON = [8, 7, 6, 5, 2, 1]


@pytest.mark.parametrize(("carried", "w", "anchor", "want"), [
    ((9,), 10, True, {9}),        # the copy counts as the first block of a fork
    ((10,), 10, True, set()),     # its parent is off the chain
    ((9,), 5, True, set()),       # its fork point (s2) is 6 slots back: out under the parent anchor
    ((9,), 5, False, {9}),        # ...and in under the uncle anchor (s4 is 4 back)
])
def test_a_copy_is_counted_as_any_entry(carried, w, anchor, want):
    tree = _tree(carried)
    assert countable_refs(tree, CANON, w, 20, parent_anchor=anchor) == want
    m = 6 + len(want)                                  # six canonical slots, plus slot 4
    assert density_m(tree, CANON, 20, countable=True, w=w, parent_anchor=anchor) == m
    for nb in (False, True):
        ms = measure(tree, np.zeros((2, 9)), np.unique(tree.slot[1:]), 20, cutoff=30,
                     use_numba=nb, countable=True, w=w, parent_anchor=anchor)
        np.testing.assert_array_equal(ms.m, [m, m])
        np.testing.assert_array_equal(ms.ref_deep, [1, 1] if carried == (10,) else [0, 0])


def test_a_counted_copy_covers_its_slot_without_making_it_lost():
    tree = _tree((9,))
    lost = lost_slots(tree, None, T=20, cutoff=30)
    assert lost.occupied == 8                          # slots 0, 2, 3, 4, 5, 6, 8, 9
    assert lost.by_depth == (1, 0, 0, 0)               # slot 3: block 3, never referenced
    assert lost.rerooted == (0, 1, 0, 0)               # slot 4: block 4 at depth 2, via copy 9
    assert lost.occupied - lost.lost == 7              # what measure() counts
    assert fork_stats(tree, None, T=20, cutoff=30)[3] == 0.5   # p_ref: 4 of the orphans 3, 4


# --- selection ------------------------------------------------------------------------------
# chain 1(s0) -> 2(s2) -> 4(s4) -> 7(s10); fork off 1: 3(s3) -> 5(s5, depth 2); fork off 4:
# 6(s8). The producer extends 7 at t = 11. Copy 8 re-roots 5 onto 1 (slot 5); copy 9 sits at
# slot 4, which the chain occupies; copy 10 hangs off 3, which is off the chain.
S_SLOT = np.array([-1, 0, 2, 3, 4, 5, 8, 10, 5, 4, 5], np.int64)
S_PARENT = np.array([-1, 0, 1, 1, 2, 3, 4, 4, 1, 1, 3], np.int64)


def _sel(cap, extra, arrival=None, parent_id=7, **kw):
    from tsi_sim.uncles import select_uncles_at_production

    cfg = SimConfig(max_uncles=cap, uncle_window_anchor=kw.pop("anchor", "parent"),
                    uncle_order=kw.pop("order", "uncle"), **kw)
    arrival = np.zeros(8) if arrival is None else arrival
    return select_uncles_at_production(S_SLOT, S_PARENT, [() for _ in range(11)], arrival, nb=8,
                                       parent_id=parent_id, t=11, config=cfg,
                                       rng=np.random.default_rng(0),
                                       extra=None if extra is None else np.array(extra))


def test_a_copy_in_view_is_a_candidate_in_age_order():
    assert _sel(4, None) == (3, 6)
    assert _sel(4, [8, 9, 10]) == (3, 8, 6)            # 9: occupied slot; 10: parent off chain
    assert _sel(2, [8, 9, 10]) == (3, 8)               # slot 5 is older than slot 8
    assert _sel(2, [8], order="parent") == (3, 8)      # fork point 1 (s0) before 4 (s4)


def test_a_copy_counts_where_no_block_of_the_window_has_reached_the_producer():
    # w = 8 slots (f = 0.125, W = 1): the window at t = 11 holds blocks 3-7, none received by a
    # producer that extends 2. The copy is measured to its own slot under the uncle anchor.
    late = np.array([0.0, 0.0, 0.0, 99.0, 99.0, 99.0, 99.0, 99.0])
    assert _sel(4, [8], arrival=late, parent_id=2, f=0.125, window_absorption=1.0,
                anchor="uncle") == (8,)


def test_a_copy_outside_the_window_is_not_a_candidate():
    # w = 4 slots (f = 0.25, W = 1): the window at t = 11 starts at slot 7; the copy's is 5.
    assert _sel(4, [8], f=0.25, window_absorption=1.0, anchor="uncle") == (6,)


# --- the wait for off-chain parents (Phase 2d) ------------------------------------------------
def test_off_chain_parents_and_the_wait():
    tree = _tree(())
    # block 7's chain is 6, 5, 2, 1: entry 3's parent 2 is on it, entry 4's parent 3 is not
    assert _off_chain_parents(7, (3, 4, 4), tree.parent, tree.slot) == [3]
    assert _off_chain_parents(7, (3,), tree.parent, tree.slot) == []
    col_b = np.array([5.0, 1.0, 3.0])
    cols_u = np.array([[2.0, 6.0], [0.0, 0.5], [4.0, 1.0]])   # two parents, three nodes
    assert _wait(col_b, cols_u) == (2.0, 2.0, 1.0)     # nodes 0 and 2 wait 1 slot each
    assert _wait(col_b, cols_u[:, :1]) == (1.0, 1.0, 1.0)   # for the first parent, node 2 only
    assert _wait(col_b, np.array([[1.0], [0.0], [2.0]])) == (0.0, 0.0, 0.0)


def test_the_wait_row_reads_every_off_chain_parent():
    tree = _tree(())
    parent = tree.ref_parent.copy()
    parent[9] = 4                                      # entry 9 now hangs off 4: depth 3
    # block 7 carries 4 (parent 3) and 9 (parent 4): both parents are off its chain
    M = np.zeros((2, 11))
    M[:, 7] = 10.0                                     # both nodes receive block 7 at 10
    M[:, 3] = (5.0, 12.0)                              # node 1 waits 2 slots for 3
    M[:, 4] = (13.0, 6.0)                              # node 0 waits 3 slots for 4
    assert _parent_wait_row(7, (4, 9), parent, tree.ref_slot, M) == (2.0, 5.0, 3.0)
    assert _parent_wait_row(7, (3,), parent, tree.ref_slot, M) is None   # 3's parent 2 is on it
    # columns from id 4 on (base 4): parent 3 was pruned and has reached every node
    assert _parent_wait_row(7, (4, 9), parent, tree.ref_slot, M[:, 4:], base=4) == (1.0, 3.0, 3.0)
    assert _parent_wait_row(7, (4,), parent, tree.ref_slot, M[:, 4:], base=4) == (0.0, 0.0, 0.0)


def test_parent_wait_reads_the_canonical_window_blocks():
    tree = _tree(())
    tree.parent_wait = np.full((9, 3), np.nan)
    tree.parent_wait[7] = (1.0, 3.0, 3.0)              # one of 4 nodes waits 3 slots
    tree.parent_wait[8] = (0.0, 0.0, 0.0)
    tree.parent_wait[4] = (4.0, 40.0, 10.0)            # off the chain: ignored
    pw = parent_wait(tree, None, T=20, cutoff=30, n_nodes=4)
    assert pw.block_share == 2 / 6
    assert pw.node_share == 0.125 and pw.wait_mean == 3.0 and pw.wait_max == 3.0
    assert parent_wait(tree, None, T=9, cutoff=30, n_nodes=4).node_share == 0.25   # 8 is out
    early = parent_wait(tree, None, T=8, cutoff=30, n_nodes=4)                     # so is 7
    assert early.block_share == 0.0 and np.isnan(early.node_share)
    assert np.isnan(parent_wait(_tree(()), None, T=20, cutoff=30, n_nodes=4).node_share)
    tree.parent_wait[7] = (0.0, 0.0, 0.0)              # no node waits: no mean wait
    calm = parent_wait(tree, None, T=20, cutoff=30, n_nodes=4)
    assert calm.node_share == 0.0 and np.isnan(calm.wait_mean) and calm.wait_max == 0.0


# --- end to end ------------------------------------------------------------------------------
NEW = ["rerooted_share", "rerooted_d2_share", "rerooted_d3plus_share", "reroot_made_share",
       "reroot_lag_mean", "parent_wait_block_share", "parent_wait_node_share", "parent_wait_mean",
       "parent_wait_max", "reroot_share", "reroot_delay", "uncle_depth"]


def _cfg(**kw):
    base = dict(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                blend_delay_max=32.0, max_uncles=4, uncle_window_anchor="parent",
                window_absorption=12.0, uncle_order="parent", k=64, epochs=3,
                genesis_d_factor=1.0, paired_streams=True)
    return SimConfig(**{**base, **kw})


def _rows(**kw):
    from tsi_sim.engine import run_trajectory

    return pd.DataFrame(run_trajectory(_cfg(**kw)))


def _same(a, b, skip=()):
    cols = [c for c in a.columns if c not in skip]
    pd.testing.assert_frame_equal(a[cols], b[cols])


def test_a_zero_share_is_the_spec_arm():
    assert _cfg(reroot_delay=10.0).key() == _cfg().key()
    _same(_rows(reroot_delay=10.0), _rows(), skip=("reroot_delay",))


def test_copies_that_arrive_too_late_change_nothing():
    """Copies are made, travel on their own stream, and never count: every other column holds."""
    spec, late = _rows(), _rows(reroot_share=1.0, reroot_delay=10_000.0)
    assert (late.reroot_made_share > 0).any()
    assert (late.rerooted_share == 0).all()
    _same(late, spec, skip=NEW)


def test_counting_takes_every_copy_selection_emits():
    df = _rows(reroot_share=1.0)
    assert (df.deep_ref_share == 0.0).all()            # no copy is rejected by the counting
    assert (df.rerooted_d2_share > 0).any()            # ...and copies do recover deep slots


def _capture(monkeypatch, **kw):
    import tsi_sim.epoch as ep
    from tsi_sim.engine import run_trajectory

    seen: list = []
    build = ep.build_tree_pernode

    def capture(*a, **k):
        tree, A = build(*a, **k)
        seen.append((a[0], tree, A))
        return tree, A

    monkeypatch.setattr(ep, "build_tree_pernode", capture)
    cfg = _cfg(**kw)
    run_trajectory(cfg)
    return cfg, seen


def _is_under(tree, p, b):
    while tree.height[b] > tree.height[p]:
        b = int(tree.parent[b])
    return b == p


def test_the_watch_matches_a_brute_force_replay(monkeypatch):
    """Every copy, and only those, where a full replay of its leader's view first leaves the
    subtree of the block's parent, at a check time the window still allows."""
    cfg, seen = _capture(monkeypatch, reroot_share=1.0, reroot_delay=3.0)
    w = cfg.effective_uncle_window
    n_copies = 0
    for active, tree, A in seen:
        nb = tree.n_blocks
        key = (tree.height * (nb + 1) * (cfg.epoch_len + 2) - tree.slot * (nb + 1)
               - np.arange(nb))
        want = {}
        for x in range(1, nb):
            p = int(tree.parent[x])
            if p == 0:
                continue
            v, sx = int(tree.leader[x]), int(tree.slot[x])
            last = active[active <= sx + w]
            horizon = float(last.max()) if last.size else -1.0   # the last check before expiry
            best = None
            for b in np.lexsort((-key, A[v])):
                if A[v, b] > horizon:
                    break
                if best is None or key[b] > key[best]:
                    best = int(b)
                    if A[v, b] > sx and not _is_under(tree, p, best):
                        want[x] = (best, float(A[v, b]))
                        break
        got = {int(x): (g, float(pub) - cfg.reroot_delay)
               for x, g, pub in zip(tree.copy_of, tree.copy_parent, tree.copy_pub, strict=True)}
        assert set(got) == set(want)
        for x, (b, tau) in want.items():
            assert got[x][0] == _fork_point(tree.parent, tree.height, x, b)
            assert got[x][1] == pytest.approx(tau)
        n_copies += len(got)
    assert n_copies > 0


def test_the_wait_matches_a_recount_from_the_full_matrix(monkeypatch):
    _, seen = _capture(monkeypatch, uncle_depth=2, prune_arrival=False)
    n_rows = 0
    for _, tree, A in seen:
        for b in range(1, tree.n_blocks):
            us = _off_chain_parents(b, tree.uncles[b], tree.parent, tree.slot)
            if not us:
                assert np.isnan(tree.parent_wait[b]).all()
                continue
            wait = A[:, us].max(axis=1) - A[:, b]
            late = wait > 0
            want = (late.sum(), wait[late].sum(), wait.max() if late.any() else 0.0)
            np.testing.assert_allclose(tree.parent_wait[b], want)
            n_rows += 1
    assert n_rows > 0


def test_the_wait_is_the_same_on_the_pruned_and_full_matrix():
    deep = _rows(uncle_depth=2)
    assert (deep.parent_wait_block_share > 0).any()
    _same(_rows(uncle_depth=2, prune_arrival=False), deep)


# --- configuration --------------------------------------------------------------------------
@pytest.mark.parametrize("kw", [dict(reroot_share=0.5, uncle_depth=2),
                                dict(reroot_share=0.5, uncle_model="old"),
                                dict(reroot_share=0.5, uncle_strategy="random"),
                                dict(reroot_share=0.5, adversary_frac=0.1),
                                dict(reroot_share=0.5, jitter_mean=1.0),
                                dict(reroot_share=1.5), dict(reroot_delay=-1.0)])
def test_validation(kw):
    with pytest.raises(ValueError):
        SimConfig(**kw)


def test_reroot_key_is_tagged_and_paired():
    a = SimConfig(uncle_window_anchor="parent", paired_streams=True)
    b = dataclasses.replace(a, reroot_share=0.5, reroot_delay=10.0)
    assert a.key() != b.key() != dataclasses.replace(b, reroot_delay=20.0).key()
    assert a.seed_key() == b.seed_key()


def test_the_sweep_runs_rerooting_at_depth_one_only():
    sw = SweepConfig(uncle_depth=[1, 2], reroot_share=[0.0, 1.0], reroot_delay=[0.0, 10.0],
                     max_uncles=[2], replicates=1)
    arms = sorted((c.uncle_depth, c.reroot_share, c.reroot_delay) for c in sw.expand())
    assert arms == [(1, 0.0, 0.0), (1, 1.0, 0.0), (1, 1.0, 10.0), (2, 0.0, 0.0)]


def test_the_rerooting_set_holds_its_stake_share():
    from tsi_sim.engine import _reroot_mask
    from tsi_sim.stake import make_stake

    cfg = SimConfig(n_nodes=500, stake_dist="pareto", reroot_share=0.5)
    stake = make_stake(cfg, np.random.default_rng(1))
    mask = _reroot_mask(cfg, stake)
    assert abs(stake[mask].sum() / stake.sum() - 0.5) <= stake.max() / stake.sum()
    same = _reroot_mask(dataclasses.replace(cfg, reroot_delay=30.0, max_uncles=4), stake)
    np.testing.assert_array_equal(mask, same)          # every arm of a replicate: the same set
    other = _reroot_mask(dataclasses.replace(cfg, replicate=1), stake)
    assert not np.array_equal(mask, other)
    assert _reroot_mask(dataclasses.replace(cfg, reroot_share=0.0), stake) is None
    assert _reroot_mask(dataclasses.replace(cfg, reroot_share=1.0), stake).all()
