"""Single per-node epoch: per-node lottery -> global tree + arrival matrix -> per-node
canonical chain, density, and self-update of each node's own D_est."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import fork, lottery, tsi
from .blocktree import build_tree_pernode
from .config import SimConfig
from .measure import measure


@dataclass
class EpochResult:
    d_next: np.ndarray        # (N,) each node's updated D_est
    m: np.ndarray             # (N,) per-node measured slot count (canonical + recovered)
    q: np.ndarray             # (N,) per-node honest active-slot fraction
    q_eff: np.ndarray         # (N,) per-node uncle-recovered fraction
    n_blocks: int             # real blocks produced
    n_active_window: int      # global active slots in window
    agreement_window: float   # fraction of nodes sharing the modal window prefix
    agreement_tip: float      # fraction of nodes sharing the modal current tip
    mean_orphan_rate: float   # mean over nodes of (blocks not on my chain)/blocks
    adv_blocks: int           # coalition blocks on the canonical chain, in window (reward)
    honest_blocks: int        # non-coalition blocks on the canonical chain, in window
    fork_rate: float          # orphaned / total blocks in window
    max_reorg_depth: int      # deepest maximal orphan branch (blocks a reorg would discard)
    mean_reorg_depth: float   # mean maximal-orphan-branch depth
    p_ref: float              # emergent reference rate: in-window orphans referenced as uncles
    p_ref_honest: float       # ...restricted to orphans produced OUTSIDE the coalition
    deep_orphan_share: float  # in-window orphans deeper than their fork's first block
                              # (uncountable by construction, §2.1)
    deep_ref_share: float     # share of examined references rejected by the parent-on-chain
                              # (first-fork) counting rule; 0 under the old model
    # Occupied window slots the count misses, as shares of all occupied window slots, by the
    # smallest fork depth among their blocks (fork.lost_slots). They sum to the shortfall of
    # the counted slots against the occupied ones.
    lost_d1_share: float
    lost_d2_share: float
    lost_d2_parent_ref_share: float   # ...depth-2 slots whose fork's first block is counted
    lost_d3_share: float
    lost_d4plus_share: float
    # Re-rooting (PLAN.md Phase 2b), as shares of the occupied window slots: the slots only
    # counted copies cover (all, and by the depth of their blocks), and the copies made for blocks
    # in the window. reroot_lag_mean is the mean time from a copy's slot to its publication.
    rerooted_share: float
    rerooted_d2_share: float
    rerooted_d3plus_share: float
    reroot_made_share: float
    reroot_lag_mean: float
    # Deeper rules (PLAN.md Phase 2d, fork.parent_wait): validators that receive a block before
    # the off-chain parents of its entries.
    parent_wait_block_share: float
    parent_wait_node_share: float
    parent_wait_mean: float
    parent_wait_max: float
    # Spent stake (PLAN.md Phase 2c): the window slots that hold a block, per slot; the window
    # slots only the spent coalition won, per slot; and the share of those the count covers (NaN
    # when there are none).
    block_rate: float
    spent_win_rate: float
    spent_counted_share: float


def _canonical_producer_split(
    tree, A, coalition_mask: np.ndarray | None, T: int, cutoff: int
) -> tuple[int, int]:
    """Split the finalized canonical chain's in-window blocks by producer coalition.

    The canonical chain is the best *arrived* tip's ancestry (honest longest-chain, first-seen
    tie-break); past k-finality every node agrees on it, so it is the reward-bearing chain.
    Returns ``(adv_blocks, honest_blocks)`` counting blocks with slot in ``[0, T)``.

    A withheld block never arrives (``A[:, b] > cutoff`` at every node) yet keeps a valid height, so
    it must be **excluded** from tip selection — otherwise a never-propagated coalition block could
    be chosen as the canonical tip and credited a phantom reward. Only the *full* matrix carries
    withheld columns; the pruned path is never used with withholding, so all blocks arrived there.
    """
    nb = tree.n_blocks
    if nb <= 1:
        return 0, 0
    ids = np.arange(nb)
    if isinstance(A, np.ndarray):
        arrived = (A <= cutoff).any(axis=0)      # (nb,) — withheld cols (A=E+1) -> False
    else:
        arrived = np.ones(nb, dtype=bool)        # pruned path never withholds
    arrived[0] = True                            # genesis is known to all
    # best arrived tip by (height, -slot, -id); never-arrived blocks pushed below genesis
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])
    adv = honest = 0
    b = best
    while b > 0:
        s = int(tree.slot[b])
        if 0 <= s < T:
            if coalition_mask is not None and coalition_mask[int(tree.leader[b])]:
                adv += 1
            else:
                honest += 1
        b = int(tree.parent[b])
    return adv, honest


def simulate_epoch(
    config: SimConfig,
    stake: np.ndarray,
    d_est: np.ndarray,
    path_latency: np.ndarray,
    epoch_ss: np.random.SeedSequence,
    adversary_mask: np.ndarray | None = None,
    coalition_mask: np.ndarray | None = None,
    inactive_mask: np.ndarray | None = None,
    coalition_ids: np.ndarray | None = None,
    reroot_mask: np.ndarray | None = None,
    spent_mask: np.ndarray | None = None,
) -> EpochResult:
    """``adversary_mask`` drives BEHAVIOUR this epoch (None == honest); ``coalition_mask`` is the
    fixed coalition identity used only for reward attribution (so a rejoin epoch, mask None, still
    credits the coalition's honestly-produced blocks). Defaults to ``adversary_mask`` when unset.
    ``coalition_ids`` splits the adversary into rival selfish groups (``engine._coalition_ids``).
    ``reroot_mask`` marks the nodes that re-root (``engine._reroot_mask``; None == none).
    ``spent_mask`` marks the nodes whose notes are spent (``engine._spent_mask``; None == none).
    """
    f, T, E = config.f, config.period_T, config.epoch_len
    lottery_ss, aux_ss = epoch_ss.spawn(2)
    aux_rng = np.random.default_rng(aux_ss)
    # Copies draw from a third child, so the lottery and the tree keep their streams.
    reroot_rng = (np.random.default_rng(epoch_ss.spawn(1)[0]) if reroot_mask is not None
                  else None)

    # per-node lottery: d_est is a VECTOR -> per-node win prob, sparse sampler unchanged
    p = lottery.win_probs(stake, d_est, f)
    if inactive_mask is not None:
        p = np.where(inactive_mask, 0.0, p)     # churned-out nodes win no slots this epoch
    winner_slots, winner_nodes = lottery.sample_wins(p, E, np.random.default_rng(lottery_ss))
    active_slots, groups = lottery.group_by_slot(winner_slots, winner_nodes)

    tree, A = build_tree_pernode(active_slots, groups, path_latency, config, aux_rng,
                                 adversary_mask=adversary_mask,
                                 coalition_ids=coalition_ids,
                                 reroot_mask=reroot_mask, reroot_rng=reroot_rng,
                                 spent_mask=spent_mask)

    # measurement: each node's own canonical chain, deduped by tip + numba-accelerated
    ms = measure(tree, A, active_slots, T, cutoff=E,
                 legacy_block_count=config.legacy_block_count,
                 countable=config.uncle_model != "old",
                 w=config.effective_uncle_window,
                 parent_anchor=config.uncle_window_anchor == "parent",
                 scope_refs=config.ref_scope == "window",
                 max_depth=config.uncle_depth)
    n_active_window = int((active_slots < T).sum())

    d_next = tsi.update_D_vec(d_est, ms.m, T, f, config.beta, config.fixed_point,
                              config.f_precision)

    attribution = coalition_mask if coalition_mask is not None else adversary_mask
    adv_blocks, honest_blocks = _canonical_producer_split(tree, A, attribution, T, E)
    (fork_rate, max_reorg_depth, mean_reorg_depth, p_ref, p_ref_honest,
     deep_orphan_share) = fork.fork_stats(
        tree, A, T, cutoff=E, coalition_mask=attribution)
    ref_total = int(ms.ref_total.sum())
    deep_ref_share = (int(ms.ref_deep.sum()) / ref_total) if ref_total else 0.0
    # measure() scopes references to the window under the countable model only.
    lost = fork.lost_slots(tree, A, T, cutoff=E,
                           scope_refs=config.ref_scope == "window" and config.uncle_model != "old")
    occ = lost.occupied or 1
    made = (tree.copy_of >= 0) & (tree.copy_slot >= 0) & (tree.copy_slot < T)
    lag = tree.copy_pub[made] - tree.copy_slot[made]
    lone, lone_counted = lost.spent
    pw = fork.parent_wait(tree, A, T, cutoff=E, n_nodes=config.n_nodes)

    return EpochResult(
        d_next=d_next, m=ms.m, q=ms.q, q_eff=ms.q_eff, n_blocks=tree.n_blocks - 1,
        n_active_window=n_active_window,
        agreement_window=ms.agreement_window, agreement_tip=ms.agreement_tip,
        mean_orphan_rate=float(ms.orphan_rate.mean()),
        adv_blocks=adv_blocks, honest_blocks=honest_blocks,
        fork_rate=fork_rate, max_reorg_depth=max_reorg_depth, mean_reorg_depth=mean_reorg_depth,
        p_ref=p_ref, p_ref_honest=p_ref_honest, deep_orphan_share=deep_orphan_share,
        deep_ref_share=deep_ref_share,
        lost_d1_share=lost.by_depth[0] / occ, lost_d2_share=lost.by_depth[1] / occ,
        lost_d2_parent_ref_share=lost.d2_parent_ref / occ, lost_d3_share=lost.by_depth[2] / occ,
        lost_d4plus_share=lost.by_depth[3] / occ,
        rerooted_share=sum(lost.rerooted) / occ, rerooted_d2_share=lost.rerooted[1] / occ,
        rerooted_d3plus_share=(lost.rerooted[2] + lost.rerooted[3]) / occ,
        reroot_made_share=int(made.sum()) / occ,
        reroot_lag_mean=float(lag.mean()) if lag.size else float("nan"),
        parent_wait_block_share=pw.block_share, parent_wait_node_share=pw.node_share,
        parent_wait_mean=pw.wait_mean, parent_wait_max=pw.wait_max,
        block_rate=lost.occupied / T, spent_win_rate=lone / T,
        spent_counted_share=lone_counted / lone if lone else float("nan"),
    )
