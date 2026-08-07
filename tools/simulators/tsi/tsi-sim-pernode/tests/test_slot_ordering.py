"""Slot-ordering invariants the uncle window rests on.

These look too obvious to test, which is exactly why they are worth pinning: the design
argument for windowing an uncle's PARENT rather than the uncle itself is a two-line
implication that holds only if both of them do.

    sl_parent(U) < sl_U        a block's slot strictly exceeds its parent's
    sl_U        < sl_A         a referenced uncle strictly precedes its referencer

    =>  sl_A - sl_U  <  sl_A - sl_parent(U)

so a window on the parent is strictly tighter than the same window on the uncle, and
bounding the parent bounds the uncle for free. If either invariant were violated — by a
same-slot parent, say — the implication would fail and the two rules would have to be
imposed separately.
"""

import numpy as np
import pytest

from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.rng import rng_for, seedseq_for
from tsi_sim.stake import make_stake

GEOMETRIES = [
    dict(topology="blend", blend_delay_max=4.0, blend_hops=3),    # the deployed operating point
    dict(topology="blend", blend_delay_max=16.0, blend_hops=3),   # near the load boundary
    dict(topology="regular", link_latency_mean=0.2),              # sub-slot direct gossip
]


def _tree(**over):
    cfg = SimConfig(**{**dict(n_nodes=300, stake_dist="pareto", degree=6,
                              link_latency_mean=0.5, link_latency_dist="geo", max_uncles=4,
                              k=96, epochs=3, genesis_d_factor=0.5,
                              prune_arrival=False, windowed_fork_choice=False), **over})
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = make_stake(cfg, rng_for(cfg))
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, _A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]))
    return cfg, tree


@pytest.mark.parametrize("geom", GEOMETRIES)
def test_a_blocks_slot_strictly_exceeds_its_parents(geom):
    _cfg, tree = _tree(**geom)
    s, par = tree.slot, tree.parent
    bad = [b for b in range(1, tree.n_blocks) if par[b] > 0 and s[par[b]] >= s[b]]
    assert not bad, f"{len(bad)} blocks do not strictly postdate their parent, e.g. {bad[:3]}"


@pytest.mark.parametrize("geom", GEOMETRIES)
def test_a_referenced_uncle_strictly_precedes_its_referencer(geom):
    _cfg, tree = _tree(**geom)
    s = tree.slot
    bad = [(b, u) for b in range(1, tree.n_blocks) for u in tree.uncles[b] if s[u] >= s[b]]
    assert not bad, f"{len(bad)} references do not precede their referencer, e.g. {bad[:3]}"


@pytest.mark.parametrize("geom", GEOMETRIES)
def test_parent_window_would_subsume_the_uncle_window(geom):
    # The implication itself, checked on real trees rather than argued: for every reference the
    # parent gap is at least the uncle gap, so any bound on the former bounds the latter.
    _cfg, tree = _tree(**geom)
    s, par = tree.slot, tree.parent
    pairs = [(int(s[b] - s[u]), int(s[b] - s[par[u]]))
             for b in range(1, tree.n_blocks) for u in tree.uncles[b]]
    if not pairs:
        pytest.skip("no uncles referenced in this geometry")
    assert all(gp >= gu for gu, gp in pairs)
    assert all(gu > 0 for gu, _ in pairs)


def test_the_counting_rule_rejects_a_non_preceding_uncle():
    # sl_A > sl_U is enforced at COUNTING, not merely at selection -- so a hand-built block
    # carrying a same-slot or future reference gains nothing from it. Both kernels implement
    # the `d <= 0` guard; this pins the behaviour rather than the implementation.
    from tsi_sim.measure import _measure_tips_py

    # chain: 0 <- 1 <- 2 ; block 2 references block 3, which shares block 2's slot
    parent = np.array([-1, 0, 1, 1], dtype=np.int64)
    slot = np.array([-1, 0, 10, 10], dtype=np.int64)          # block 3 does NOT precede block 2
    uncle_flat = np.array([3], dtype=np.int64)
    uncle_ptr = np.array([0, 0, 0, 1, 1], dtype=np.int64)     # only block 2 carries a reference
    stamps = [np.full(4, -1, dtype=np.int64) for _ in range(2)]
    m, honest, rec, refs, deep, _clen, _fp = _measure_tips_py(
        np.array([2], dtype=np.int64), parent, slot, uncle_flat, uncle_ptr,
        T=100, w=300, countable=True,
        uncle_stamp=stamps[0], honest_stamp=np.full(101, -1, dtype=np.int64),
        chain_stamp=stamps[1])
    assert refs[0] == 1                # the reference was examined
    assert rec[0] == 0                 # ...and recovered nothing
    assert m[0] == honest[0]           # the count is the chain alone
