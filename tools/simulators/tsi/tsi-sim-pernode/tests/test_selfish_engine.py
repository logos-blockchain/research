"""The private-chain (SM1) adversary inside the per-node engine (§6.6, open item 5).

§6.8 recorded that "the per-node engine has no private-chain strategy", which is why the
selfish results came from the global race model with uncle recovery as a free knob. These
tests pin the engine version: that it leaves every honest result untouched, that its blocks
are conserved, and that it actually orphans honest work rather than merely hiding its own.
"""

import numpy as np
import pytest

from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, run_trajectory
from tsi_sim.stake import stake_for

BASE = dict(n_nodes=200, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=8.0,
            max_uncles=2, k=32, epochs=4, genesis_d_factor=0.5, early_stop=False)


def _traj(**over):
    return run_trajectory(SimConfig(**{**BASE, **over}))


def test_selfish_at_zero_stake_keeps_the_honest_fast_paths():
    """With no coalition, `selfish` must not disturb the honest engine at all.

    Note it is NOT bit-identical to `suppress` at frac = 0: adversary_strategy sits in the base
    RNG key, so switching it reseeds the run even though the field is inert without a coalition.
    That is pre-existing and harmless (both are valid honest runs), so the invariant worth
    pinning is the one that protects committed results — that the windowed fork choice and the
    arrival prune, which `selfish` disables when it IS active, stay enabled and stay exact here.
    """
    exact = _traj(adversary_strategy="selfish", adversary_frac=0.0,
                  windowed_fork_choice=False, prune_arrival=False)
    fast = _traj(adversary_strategy="selfish", adversary_frac=0.0)
    assert [r["mean_ratio"] for r in fast] == [r["mean_ratio"] for r in exact]
    assert max(r["range_ratio"] for r in fast) == 0.0        # honest run: nodes agree exactly


def test_selfish_key_is_distinct_from_the_other_strategies():
    # adversary_strategy already sits in the base key, so no historical seed moves; this just
    # pins that the new value is not silently aliased onto an existing stream.
    keys = {s: SimConfig(**BASE, adversary_frac=0.3, adversary_strategy=s).key()
            for s in ("suppress", "withhold", "selfish")}
    assert len(set(keys.values())) == 3


def test_selfish_is_deterministic():
    a = _traj(adversary_frac=0.3, adversary_strategy="selfish")
    b = _traj(adversary_frac=0.3, adversary_strategy="selfish")
    assert [r["mean_ratio"] for r in a] == [r["mean_ratio"] for r in b]


def _tree(**over):
    cfg = SimConfig(**{**BASE, **over})
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    from tsi_sim import lottery, topology
    root = __import__("tsi_sim.rng", fromlist=["seedseq_for"]).seedseq_for(cfg)
    kids = root.spawn(cfg.epochs + 3)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d_est = np.full(cfg.n_nodes, cfg.genesis_d_factor * stake.sum())
    p = lottery.win_probs(stake, d_est, cfg.f)
    ws, wn = lottery.sample_wins(p, cfg.epoch_len, np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask)
    return cfg, tree, A, mask


def test_private_blocks_are_invisible_to_honest_nodes_while_hidden():
    cfg, tree, A, mask = _tree(adversary_frac=0.3, adversary_strategy="selfish")
    E = cfg.epoch_len
    honest = ~mask
    # Every block is either public (some honest node has it) or hidden from ALL honest nodes.
    reaches_honest = (A[honest] <= E).any(axis=0)
    hidden = ~reaches_honest
    hidden[0] = False
    # a hidden block is never a partial leak: no honest node holds it
    assert not (A[honest][:, hidden] <= E).any()
    # and every hidden block was produced by the coalition, never by an honest node
    assert mask[tree.leader[hidden]].all()


def test_released_blocks_never_precede_their_parent():
    # The release path applies its own no-earlier-than-parent clamp; a violation would let a
    # node build on a child before its parent and corrupt the tree.
    cfg, tree, A, mask = _tree(adversary_frac=0.3, adversary_strategy="selfish")
    for b in range(1, tree.n_blocks):
        p = int(tree.parent[b])
        assert (A[:, b] >= A[:, p] - 1e-9).all(), f"block {b} precedes parent {p}"


def _honest_orphans_in_window(cfg, tree, A, mask) -> int:
    """In-window orphans produced by NON-coalition nodes — the displaced honest work."""
    E, T = cfg.epoch_len, cfg.period_T
    nb = tree.n_blocks
    ids = np.arange(nb)
    arrived = (A <= E).any(axis=0)
    arrived[0] = True
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])
    canonical = np.zeros(nb, dtype=bool)
    b = best
    while b > 0:
        canonical[b] = True
        b = int(tree.parent[b])
    in_win = (tree.slot >= 0) & (tree.slot < T)
    return int((in_win & ~canonical & ~mask[tree.leader]).sum())


def test_selfish_displaces_honest_work_where_withholding_only_hides_its_own():
    # This is the distinction between the two levers, and the reason only one of them is
    # profitable: withholding discards the coalition's OWN blocks (a dead loss, and honest
    # blocks keep their places), while a private chain overrides HONEST blocks off the chain.
    # Compare the honest orphan count at matched stake -- not fork_rate, which counts the
    # withholder's own vanished blocks as orphans too and so runs high for the wrong reason.
    kw = dict(adversary_frac=0.4, max_uncles=0)
    cfg_s, tree_s, A_s, mask_s = _tree(adversary_strategy="selfish", **kw)
    cfg_w, tree_w, A_w, mask_w = _tree(adversary_strategy="withhold", **kw)
    assert (_honest_orphans_in_window(cfg_s, tree_s, A_s, mask_s)
            > _honest_orphans_in_window(cfg_w, tree_w, A_w, mask_w))


def test_selfish_deflates_the_estimate_below_the_honest_baseline():
    tail = slice(2, None)
    honest = np.mean([r["mean_ratio"] for r in _traj(max_uncles=0)[tail]])
    selfish = np.mean([r["mean_ratio"] for r in
                       _traj(adversary_frac=0.35, adversary_strategy="selfish",
                             max_uncles=0)[tail]])
    assert selfish < honest


def test_uncle_counting_repairs_part_of_the_selfish_deflation():
    # The §6.6 claim, now measurable in the engine rather than through the free knob eta:
    # uncles recover some of the loss, and (per §6.6/fig36) not all of it.
    tail = slice(2, None)
    d0 = np.mean([r["mean_ratio"] for r in
                  _traj(adversary_frac=0.35, adversary_strategy="selfish", max_uncles=0)[tail]])
    d2 = np.mean([r["mean_ratio"] for r in
                  _traj(adversary_frac=0.35, adversary_strategy="selfish", max_uncles=2)[tail]])
    assert d2 > d0


def test_p_ref_honest_defaults_to_p_ref_without_a_coalition():
    from tsi_sim.fork import fork_stats
    cfg, tree, A, _ = _tree()
    # Unpack by position, not with a splat: fork_stats has grown a field twice now, and a
    # trailing `*_, a, b` silently re-binds to different quantities each time it does.
    (_fork_rate, _max_d, _mean_d, p_ref, p_ref_honest,
     deep_orphan_share) = fork_stats(tree, A, cfg.period_T, cutoff=cfg.epoch_len)
    assert p_ref == p_ref_honest              # no coalition -> the two coincide
    assert 0.0 <= deep_orphan_share <= 1.0


@pytest.mark.parametrize("strategy", ["selfish", "withhold"])
def test_hidden_blocks_are_excluded_from_the_canonical_chain(strategy):
    # A chain no honest node ever saw must not be crowned canonical, or it would collect
    # phantom rewards and phantom density.
    from tsi_sim.epoch import _canonical_producer_split
    cfg, tree, A, mask = _tree(adversary_frac=0.4, adversary_strategy=strategy)
    E, T = cfg.epoch_len, cfg.period_T
    adv, hon = _canonical_producer_split(tree, A, mask, T, E)
    reaches_honest = (A[~mask] <= E).any(axis=0)
    # walk the chosen canonical tip: every block on it is public
    ids = np.arange(tree.n_blocks)
    arrived = (A <= E).any(axis=0)
    arrived[0] = True
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])
    b = best
    while b > 0:
        assert reaches_honest[b], f"canonical block {b} was never public"
        b = int(tree.parent[b])
    assert adv + hon > 0
