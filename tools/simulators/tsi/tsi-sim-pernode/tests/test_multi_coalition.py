"""Rival selfish coalitions: the partition, the isolation invariant, and K == 1 compatibility."""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, _coalition_ids, run_trajectory
from tsi_sim.rng import rng_for, seedseq_for
from tsi_sim.stake import make_stake

KW = dict(n_nodes=250, stake_dist="pareto", topology="blend", degree=6, link_latency_mean=0.5,
          link_latency_dist="geo", blend_hops=3, blend_delay_max=8.0, max_uncles=2,
          window_absorption=10.0, k=64, epochs=3, genesis_d_factor=0.5, early_stop=False,
          adversary_frac=0.4, adversary_strategy="selfish", replicate=0,
          prune_arrival=False, windowed_fork_choice=False)


def _tree(cfg):
    """Rebuild one epoch's tree with the coalition split applied."""
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = make_stake(cfg, rng_for(cfg))
    mask = _adversary_mask(cfg, stake)
    ids = _coalition_ids(cfg, stake, mask)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask, coalition_ids=ids)
    return tree, A, stake, mask, ids


def test_k1_is_bit_identical_to_the_single_coalition_path():
    """Adding the knob must not disturb any committed selfish result.

    Both the key (so the RNG stream is untouched) and the trajectory itself.
    """
    a = SimConfig(**KW)
    b = SimConfig(**KW, adversary_coalitions=1)
    assert a.key() == b.key()
    assert pd.DataFrame(run_trajectory(a)).equals(pd.DataFrame(run_trajectory(b)))
    # ...and K > 1 DOES get its own stream, or the two would silently share one.
    assert SimConfig(**KW, adversary_coalitions=2).key() != a.key()


def test_partition_splits_stake_and_is_as_even_as_the_tail_allows():
    """Equal-*stake* rivals is the question §6.9 asks; equal-member-count would not be it.

    Perfect evenness is not achievable and not claimed: under a Pareto tail a single adversarial
    whale can exceed beta/K on its own, and then no partition is even. What LPT guarantees is that
    the spread is at most one member's stake — if bin A ends heaviest, the last item x placed in it
    went there because A was then the lightest, so load(A) - x <= load(B) for every B at that time
    and loads only grow. That bound is what this pins, together with the partition being exact.
    """
    K = 3
    cfg = SimConfig(**{**KW, "adversary_coalitions": K})
    stake = make_stake(cfg, rng_for(cfg))
    mask = _adversary_mask(cfg, stake)
    ids = _coalition_ids(cfg, stake, mask)
    assert ids is not None
    shares = np.array([stake[ids == g].sum() for g in range(K)]) / stake.sum()
    beta = stake[mask].sum() / stake.sum()
    biggest = stake[mask].max() / stake.sum()
    assert shares.max() - shares.min() <= biggest + 1e-12       # the LPT bound
    # an exact partition of the coalition, and nothing else
    assert shares.sum() == pytest.approx(beta)
    assert set(np.nonzero(ids >= 0)[0]) == set(np.nonzero(mask)[0])
    assert (ids[~mask] == -1).all()


def test_k1_returns_no_labels():
    """K == 1 must return None, not an all-zero vector: that is what keeps the old path exact."""
    cfg = SimConfig(**KW)
    stake = make_stake(cfg, rng_for(cfg))
    assert _coalition_ids(cfg, stake, _adversary_mask(cfg, stake)) is None
    assert _coalition_ids(SimConfig(**{**KW, "adversary_frac": 0.0, "adversary_coalitions": 3}),
                          stake, None) is None


def test_rivals_cannot_see_each_others_private_blocks():
    """THE isolation invariant the whole study rests on, checked on the mechanism itself.

    A coalition's unreleased block must be visible to its own members and to nobody else — not
    honest nodes, and (the part K > 1 adds) not a rival coalition either. If it leaked, the rivals
    would effectively be one coalition sharing a view and the experiment would measure nothing.

    This cannot be read off the FINAL arrival matrix: by the end every private block has either
    been released (public arrivals) or stranded (hidden from its own coalition too), so the private
    state is gone. So drive the two coalition objects directly, which is where the rule lives.
    """
    from tsi_sim.blocktree import _SelfishCoalition

    nb, E = 8, 1000
    left = _SelfishCoalition(np.array([0, 1]), nb, E)
    right = _SelfishCoalition(np.array([2, 3]), nb, E)
    height = np.zeros(nb, dtype=np.int64)

    # a public block both sides see
    height[1] = 1
    left.note_block(1, 5.0)
    right.note_block(1, 5.0)

    # `left` mines two private blocks on top of it; `right` mines one
    height[2], height[3] = 2, 3
    left.add_private(2, 10, 1)
    left.add_private(3, 11, 2)
    height[4] = 2
    right.add_private(4, 12, 1)

    # neither side's private chain enters the other's view of the PUBLIC chain
    assert left.public_height(20, height, 5) == 1, "a rival's hidden block raised left's public h"
    assert right.public_height(20, height, 5) == 1, "left's hidden blocks raised right's public h"
    # ...and each side does see its own
    assert left.unreleased[2] and left.unreleased[3] and not left.unreleased[4]
    assert right.unreleased[4] and not right.unreleased[2]
    # a rival's block is invisible in time, not just excluded by the unreleased flag: that is what
    # makes the isolation hold for blocks the engine has not flagged on this side at all.
    assert left.coal_arr[4] > E and right.coal_arr[2] > E

    # once `right` releases, `left` learns of it (the engine notes releases to every rival) and it
    # counts toward left's public height — the channel by which one override buries another's chain
    left.note_block(4, 13.0)
    assert left.public_height(20, height, 5) == 2


def test_splitting_changes_the_fork_structure():
    """K > 1 must actually behave differently, or the knob is inert.

    Rivals cut each other's leads short, so the private chains are far shallower than the single
    coalition's. This pins the direction, not a value.
    """
    def max_fork_depth(cfg):
        tree, A, *_ = _tree(cfg)
        seen = A.min(axis=0) <= cfg.epoch_len
        h = np.where(seen, tree.height, -1)
        chain, c = set(), int(np.argmax(h))
        while c > 0:
            chain.add(c)
            c = int(tree.parent[c])
        best = 0
        for b in range(1, tree.n_blocks):
            if b in chain:
                continue
            d, x = 0, b
            while x > 0 and x not in chain:
                x = int(tree.parent[x])
                d += 1
            best = max(best, d)
        return best

    deep_one = max_fork_depth(SimConfig(**KW))
    deep_many = max_fork_depth(SimConfig(**{**KW, "adversary_coalitions": 4}))
    assert deep_many < deep_one, (
        f"4 rivals held a deeper private chain ({deep_many}) than one coalition ({deep_one})")


def test_partition_is_ignored_where_it_provably_cannot_matter():
    """Under suppression the deflation depends on summed stake alone (§6.9, exact by construction),
    so the partition must leave that path untouched.

    Compared at the TREE, holding every RNG input fixed and varying only ``coalition_ids``. A
    trajectory comparison would not show this: K enters ``key()``, so two trajectories draw
    different stake, graph and lottery, and at test scale that difference swamps the effect.
    """
    cfg = SimConfig(**{**KW, "adversary_strategy": "suppress", "adversary_coalitions": 4})
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = make_stake(cfg, rng_for(cfg))
    mask = _adversary_mask(cfg, stake)
    ids = _coalition_ids(cfg, stake, mask)
    assert ids is not None and (ids >= 0).any()
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)

    def build(coalition_ids):
        tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                     adversary_mask=mask, coalition_ids=coalition_ids)
        return tree, A

    t0, a0 = build(None)
    t1, a1 = build(ids)
    assert np.array_equal(t0.parent, t1.parent) and np.array_equal(t0.leader, t1.leader)
    assert np.array_equal(t0.slot, t1.slot) and t0.uncles == t1.uncles
    assert np.array_equal(a0, a1)


def test_realised_adversary_stake_stays_on_its_label():
    """The coalition must hold the stake the knob names — including in the tail.

    A plain cumulative-prefix cut let one whale straddling the cutoff carry the coalition far past
    its label: ~10% of Pareto replicates at adversary_frac = 0.4 realised a MAJORITY, up to 0.97.
    The median was always on-label, so only a tail check catches it. This is the regression guard.
    """
    import warnings as _w

    for nominal in (0.2, 0.3, 0.4):
        got, unreachable = [], 0
        for rep in range(40):
            cfg = SimConfig(n_nodes=800, stake_dist="pareto",
                            adversary_frac=nominal, replicate=rep)
            stake = make_stake(cfg, rng_for(cfg))
            with _w.catch_warnings(record=True) as caught:
                _w.simplefilter("always")
                mask = _adversary_mask(cfg, stake)
                unreachable += any("not reachable" in str(c.message) for c in caught)
            got.append(float(stake[mask].sum() / stake.sum()))
        got = np.array(got)
        on_label = got[np.abs(got - nominal) <= 0.2 * nominal]
        # every reachable draw lands essentially exactly on the label...
        assert np.abs(on_label - nominal).max() < 0.01 * nominal, f"{nominal}: {on_label.max()}"
        # ...nothing silently becomes a majority attacker...
        assert (got > 0.5).sum() == 0, f"{nominal} produced a majority coalition: {got.max()}"
        # ...and any draw that misses the label is loud about it, not silent.
        assert unreachable == len(got) - len(on_label)


def test_lead_cap_only_changes_runaway_private_chains():
    """The cap must be inert unless `wait` has stopped terminating.

    Held paired (same RNG, cap the only difference) so this is the mechanism and not a reseed.
    """
    cfg_kw = {**KW, "n_nodes": 400, "adversary_frac": 0.3}
    ref = SimConfig(**cfg_kw)
    kids = seedseq_for(ref).spawn(ref.epochs + 3)
    stake = make_stake(ref, rng_for(ref))
    mask = _adversary_mask(ref, stake)
    pl = topology.build_path_latency(ref, np.random.default_rng(kids[1]))
    d = np.full(ref.n_nodes, ref.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, ref.f), ref.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)

    def build(cap):
        cfg = SimConfig(**{**cfg_kw, "selfish_lead_cap": cap})
        return build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                  adversary_mask=mask)

    t_unc, a_unc = build(-1)          # textbook SM1, no cap
    t_cap, a_cap = build(0)           # default: cap at k
    stranded = (a_unc > ref.epoch_len).all(axis=0)[1:]
    adv = np.array([mask[int(t_unc.leader[b])] for b in range(1, t_unc.n_blocks)])
    frac_stranded = int((adv & stranded).sum()) / max(int(adv.sum()), 1)
    if frac_stranded < 0.5:
        # `wait` terminated normally, so the cap never fired and the trees must be identical
        assert np.array_equal(a_unc, a_cap) and np.array_equal(t_unc.parent, t_cap.parent)
    else:
        # it ran away: the cap must have rescued the chain from the epoch boundary
        cap_stranded = (a_cap > ref.epoch_len).all(axis=0)[1:]
        assert int((adv & cap_stranded).sum()) < int((adv & stranded).sum())
