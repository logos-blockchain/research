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
) -> EpochResult:
    """``adversary_mask`` drives BEHAVIOUR this epoch (None == honest); ``coalition_mask`` is the
    fixed coalition identity used only for reward attribution (so a rejoin epoch, mask None, still
    credits the coalition's honestly-produced blocks). Defaults to ``adversary_mask`` when unset.
    """
    f, T, E = config.f, config.period_T, config.epoch_len
    lottery_ss, aux_ss = epoch_ss.spawn(2)
    aux_rng = np.random.default_rng(aux_ss)

    # per-node lottery: d_est is a VECTOR -> per-node win prob, sparse sampler unchanged
    p = lottery.win_probs(stake, d_est, f)
    if inactive_mask is not None:
        p = np.where(inactive_mask, 0.0, p)     # churned-out nodes win no slots this epoch
    winner_slots, winner_nodes = lottery.sample_wins(p, E, np.random.default_rng(lottery_ss))
    active_slots, groups = lottery.group_by_slot(winner_slots, winner_nodes)

    tree, A = build_tree_pernode(active_slots, groups, path_latency, config, aux_rng,
                                 adversary_mask=adversary_mask)

    # measurement: each node's own canonical chain, deduped by tip + numba-accelerated
    ms = measure(tree, A, active_slots, T, cutoff=E,
                 legacy_block_count=config.legacy_block_count,
                 countable=config.uncle_model != "old",
                 w=config.effective_uncle_window)
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

    return EpochResult(
        d_next=d_next, m=ms.m, q=ms.q, q_eff=ms.q_eff, n_blocks=tree.n_blocks - 1,
        n_active_window=n_active_window,
        agreement_window=ms.agreement_window, agreement_tip=ms.agreement_tip,
        mean_orphan_rate=float(ms.orphan_rate.mean()),
        adv_blocks=adv_blocks, honest_blocks=honest_blocks,
        fork_rate=fork_rate, max_reorg_depth=max_reorg_depth, mean_reorg_depth=mean_reorg_depth,
        p_ref=p_ref, p_ref_honest=p_ref_honest, deep_orphan_share=deep_orphan_share,
        deep_ref_share=deep_ref_share,
    )
