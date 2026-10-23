"""Snapshot-only references (PLAN.md Phase 2c, route C) and the spent-stake coalition.

Counting fixture (ids in production order), window w = 10, T = 20:
canonical 1(s0) -> 2(s2) -> 3(s5) -> 5(s8) -> 6(s12) -> 7(s14, tip).
Orphans: 4(s6) off 3; 8(s9) and 9(s11) off 5.
Spent wins: 10(s7, parent 3), 11(s5, parent 2: the chain holds slot 5), 12(s9, parent 1: orphan 8
holds slot 9), 13(s1, parent 1: 13 slots before block 7), 14(s10, parent 5).
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig, SweepConfig
from tsi_sim.fork import fork_stats, lost_slots
from tsi_sim.measure import measure
from tsi_sim.tsi import countable_refs, density_m

# --- counting --------------------------------------------------------------------------------
CANON = [7, 6, 5, 3, 2, 1]


def _tree(carried6=(), carried7=()):
    #                  id: 0   1  2  3  4  5  6   7   8  9
    tree = BlockTree(
        slot=np.array([-1, 0, 2, 5, 6, 8, 12, 14, 9, 11], np.int64),
        parent=np.array([-1, 0, 1, 2, 3, 3, 5, 6, 5, 5], np.int64),
        height=np.array([0, 1, 2, 3, 4, 4, 5, 6, 5, 5], np.int64),
        leader=np.arange(10, dtype=np.int64),
        uncles=[() for _ in range(10)],
        copy_slot=np.array([7, 5, 9, 1, 10], np.int64),
        copy_parent=np.array([3, 2, 1, 1, 5], np.int64),
        copy_of=np.full(5, -1, np.int64),
        copy_pub=np.array([7.0, 5.0, 9.0, 1.0, 10.0]),
    )
    tree.uncles[6], tree.uncles[7] = carried6, carried7
    return tree


def _m(tree, anchor):
    ms = [measure(tree, np.zeros((2, 10)), np.unique(tree.slot[1:]), 20, cutoff=30,
                  use_numba=nb, countable=True, w=10, parent_anchor=anchor, max_depth=0)
          for nb in (False, True)]
    for x in ms:
        np.testing.assert_array_equal(x.ref_deep, [0, 0])
    return [x.m.tolist() for x in ms]


@pytest.mark.parametrize(("carried", "anchor", "want", "m"), [
    ((10,), False, {10}, 7),          # counts, and adds its slot
    ((11,), False, {11}, 6),          # counts, but the chain already holds its slot
    ((13,), False, set(), 6),         # 13 slots back: outside the window
    ((12,), False, {12}, 7),          # its own slot is 5 back, whatever its parent
    ((12,), True, set(), 6),          # ...its parent is 14 back: out under the parent anchor
    ((10, 12), False, {10, 12}, 8),
])
def test_a_spent_win_counts_by_its_own_slot(carried, anchor, want, m):
    tree = _tree(carried7=carried)
    assert countable_refs(tree, CANON, 10, 20, parent_anchor=anchor, max_depth=0) == want
    assert density_m(tree, CANON, 20, countable=True, w=10, parent_anchor=anchor,
                     max_depth=0) == m
    assert _m(tree, anchor) == [[m, m], [m, m]]


def test_a_counted_spent_win_covers_its_slot():
    tree = _tree(carried6=(4, 12), carried7=(10, 11))
    lost = lost_slots(tree, None, T=20, cutoff=30)
    assert lost.occupied == 9                          # slots 0, 2, 5, 6, 8, 9, 11, 12, 14
    assert lost.by_depth == (1, 0, 0, 0)               # slot 11: orphan 9; slot 9 is covered by 12
    assert lost.rerooted == (0, 0, 0, 0)
    assert lost.spent == (3, 1)                        # slots 1, 7, 10 hold no block; 7 counts
    assert _m(tree, False)[0] == [9, 9] == [lost.occupied - lost.lost + lost.spent[1]] * 2
    assert fork_stats(tree, None, T=20, cutoff=30)[3] == 1 / 3   # p_ref: 4 of the orphans 4, 8, 9


# --- selection -------------------------------------------------------------------------------
# chain 1(s0) -> 2(s2) -> 4(s4) -> 7(s10); fork off 1: 3(s3) -> 5(s5); fork off 4: 6(s8).
# The producer extends 7 at t = 11. Spent wins: 8 (s6, parent 5, off the chain), 9 (s4, which
# the chain occupies), 10 (s1).
S_SLOT = np.array([-1, 0, 2, 3, 4, 5, 8, 10, 6, 4, 1], np.int64)
S_PARENT = np.array([-1, 0, 1, 1, 2, 3, 4, 4, 5, 2, 1], np.int64)


def _sel(cap, **kw):
    from tsi_sim.uncles import select_uncles_at_production

    cfg = SimConfig(max_uncles=cap, uncle_depth=0, uncle_window_anchor="uncle",
                    window_absorption=kw.pop("window_absorption", 12.0), **kw)
    return select_uncles_at_production(S_SLOT, S_PARENT, [() for _ in range(11)], np.zeros(8),
                                       nb=8, parent_id=7, t=11, config=cfg,
                                       rng=np.random.default_rng(0), extra=np.array([8, 9, 10]))


def test_a_spent_win_in_view_is_a_candidate_in_age_order():
    assert _sel(4) == (10, 3, 5, 8)                    # 9: the chain occupies slot 4
    assert _sel(2) == (10, 3)
    assert _sel(4, f=0.25, window_absorption=1.0) == (6,)   # w = 4: the window starts at slot 7


# --- end to end ------------------------------------------------------------------------------
def _cfg(**kw):
    base = dict(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                blend_delay_max=32.0, max_uncles=4, uncle_window_anchor="uncle",
                window_absorption=12.0, uncle_depth=0, k=64, epochs=3, genesis_d_factor=1.0,
                paired_streams=True)
    return SimConfig(**{**base, **kw})


def _capture(monkeypatch, cfg):
    """Run ``cfg``; return its stake and, per epoch, the lottery groups, the tree and A."""
    import tsi_sim.epoch as ep
    from tsi_sim.engine import run_trajectory
    from tsi_sim.stake import stake_for

    seen: list = []
    build = ep.build_tree_pernode

    def capture(*a, **k):
        tree, A = build(*a, **k)
        seen.append((a[0], a[1], tree, A))
        return tree, A

    monkeypatch.setattr(ep, "build_tree_pernode", capture)
    rows = pd.DataFrame(run_trajectory(cfg))
    return stake_for(cfg), seen, rows


def _keys(tree, cfg):
    nb = tree.n_blocks
    return tree.height * (nb + 1) * (cfg.epoch_len + 2) - tree.slot * (nb + 1) - np.arange(nb)


def test_spent_wins_become_entries_on_the_tip_their_leader_extends(monkeypatch):
    from tsi_sim.engine import _spent_mask

    cfg = _cfg(spent_share=0.4)
    stake, seen, _ = _capture(monkeypatch, cfg)
    mask = _spent_mask(cfg, stake)
    n_entries = 0
    for active, groups, tree, A in seen:
        wins = [(int(t), int(v)) for t, g in zip(active, groups, strict=True) for v in g]
        blocks = zip(tree.slot[1:].tolist(), tree.leader[1:].tolist(), strict=True)
        assert sorted(blocks) == sorted((t, v) for t, v in wins if not mask[v])   # every other win
        assert (tree.copy_of == -1).all()
        assert sorted(tree.copy_slot.tolist()) == sorted(t for t, v in wins if mask[v])
        key = _keys(tree, cfg)
        for t, p in zip(tree.copy_slot.tolist(), tree.copy_parent.tolist(), strict=True):
            first = int(np.searchsorted(tree.slot, t, side="left"))   # blocks before slot t
            tips = set()
            for v in (v for s, v in wins if s == t and mask[v]):
                seen_v = np.nonzero(A[v, :first] <= t)[0]
                tips.add(int(seen_v[np.argmax(key[seen_v])]))
            assert p in tips
        n_entries += tree.copy_slot.size
    assert n_entries > 0


def test_entries_keep_the_honest_streams(monkeypatch):
    """In epoch 0 both arms draw the same wins. A block with the same parent in both trees, whose
    parent arrived at the same times, arrives at the same times too: its draw is the honest one."""
    _, honest, _ = _capture(monkeypatch, _cfg(prune_arrival=False))
    _, spent, _ = _capture(monkeypatch, _cfg(spent_share=0.4))
    (_, _, t0, A0), (_, _, t1, A1) = honest[0], spent[0]
    idx0 = {(int(s), int(v)): b for b, (s, v) in enumerate(zip(t0.slot, t0.leader, strict=True))}
    first_spent = int(t1.copy_slot.min())
    matched = 0
    for b1 in range(1, t1.n_blocks):
        if t1.slot[b1] <= first_spent:
            continue
        b0 = idx0[(int(t1.slot[b1]), int(t1.leader[b1]))]
        p0, p1 = int(t0.parent[b0]), int(t1.parent[b1])
        same_parent = (t0.slot[p0], t0.leader[p0]) == (t1.slot[p1], t1.leader[p1])
        if same_parent and np.array_equal(A0[:, p0], A1[:, p1]):
            np.testing.assert_array_equal(A0[:, b0], A1[:, b1])
            matched += 1
    assert matched >= 10


def test_spent_stake_rows(monkeypatch):
    from tsi_sim.engine import _spent_mask

    cfg = _cfg(spent_share=0.4)
    stake, _, df = _capture(monkeypatch, cfg)
    mask = _spent_mask(cfg, stake)
    assert (df.active_stake_frac == 1.0 - stake[mask].sum() / stake.sum()).all()
    assert (df.deep_ref_share == 0.0).all()            # counting takes every entry selected
    assert (df.spent_counted_share > 0.0).all()
    assert (df.reroot_made_share == 0.0).all() and df.reroot_lag_mean.isna().all()
    assert (df.rerooted_share == 0.0).all()


# --- configuration --------------------------------------------------------------------------
@pytest.mark.parametrize("kw", [dict(uncle_depth=1), dict(uncle_depth=2),
                                dict(uncle_window_anchor="parent"), dict(adversary_frac=0.1),
                                dict(spent_share=1.0), dict(spent_share=-0.1)])
def test_validation(kw):
    with pytest.raises(ValueError):
        SimConfig(**{**dict(spent_share=0.25, uncle_depth=0), **kw})


def test_spent_key_is_tagged_and_paired():
    a = SimConfig(uncle_depth=0, paired_streams=True)
    b = dataclasses.replace(a, spent_share=0.25)
    assert a.key() != b.key() != dataclasses.replace(b, spent_share=0.5).key()
    assert a.seed_key() == b.seed_key()


def test_the_sweep_runs_spent_stake_under_route_c_only():
    sw = SweepConfig(uncle_depth=[1, 0], uncle_window_anchor=["parent", "uncle"],
                     spent_share=[0.0, 0.5], max_uncles=[2], replicates=1)
    arms = sorted((c.uncle_depth, c.uncle_window_anchor, c.spent_share) for c in sw.expand())
    assert arms == [(0, "parent", 0.0), (0, "uncle", 0.0), (0, "uncle", 0.5), (1, "parent", 0.0),
                    (1, "uncle", 0.0)]


def test_the_spent_set_holds_its_stake_share():
    from tsi_sim.engine import _spent_mask
    from tsi_sim.stake import make_stake

    cfg = SimConfig(n_nodes=500, stake_dist="pareto", uncle_depth=0, spent_share=0.5)
    stake = make_stake(cfg, np.random.default_rng(1))
    mask = _spent_mask(cfg, stake)
    assert abs(stake[mask].sum() / stake.sum() - 0.5) <= stake.max() / stake.sum()
    same = _spent_mask(dataclasses.replace(cfg, max_uncles=4, blend_delay_max=16.0), stake)
    np.testing.assert_array_equal(mask, same)          # every arm of a replicate: the same set
    assert not np.array_equal(mask, _spent_mask(dataclasses.replace(cfg, replicate=1), stake))
    assert _spent_mask(dataclasses.replace(cfg, spent_share=0.0), stake) is None
