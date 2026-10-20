"""Phase B3: a private-chain attack replayed on the engine's own timelines (PLAN.md B3).

The engine runs with a coalition holding stake share ``alpha`` that withholds every block it
wins (``adversary_strategy = "withhold"``), and with every node's stake estimate at the true
stake. Honest nodes then build the public chain from honest stake alone, under the engine's
random Blend delays, while the coalition's wins are recorded. A win can sign a block on any
branch (the ticket does not depend on the parent), and a chain holds one block per slot, so the
coalition's private chain grows by one block per distinct slot it wins.

The race, for a target canonical block ``b_i`` at slot ``t_i``:

- Before ``t_i`` the coalition keeps a private fork of lead ``L >= 0`` over the public chain
  (``premine``): a win adds one; a public block takes one, and at zero the coalition moves to the
  new public tip. Without ``premine`` it forks at the parent of ``b_i`` when the parent appears,
  so ``L`` counts its wins from then until ``t_i`` (the classic double-spend race, where the
  attacker starts as the honest network starts on the target block).
- At ``t_i`` the public chain gains ``b_i``, so the race stands at ``R = L - 1``; afterwards a
  win adds one and a canonical block takes one.
- The receiver accepts ``b_i`` once ``K`` canonical blocks lie on top of it. The attack succeeds
  if ``R >= win_at`` at some moment after that. With ``win_at = 1`` (the default) the coalition
  must release a strictly longer chain, as Cryptarchia's Online rule keeps the first-seen chain on
  ties. With ``win_at = 0`` ties go to the attacker, as in Nakamoto's and Rosenfeld's races and in
  the adversarial tie-breaking of the worst-case delay model.

Public blocks count at their production slot, the most advanced view any honest node can hold,
so the race is scored against the best-informed node. Within a slot, wins are counted first.
"""

from __future__ import annotations

import numpy as np
from numba import njit
from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, _partition_mask
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import make_stake


def _tree(config: SimConfig, stake_scale: float = 1.0):
    """The engine's block tree with every node's stake estimate at ``stake_scale`` times the true
    stake: ``(tree, arrival, stake, mask, side, public)`` with ``arrival[i, b]`` the slot block
    ``b`` reaches node ``i``, ``mask`` the coalition's nodes (all false without one), ``side`` one
    side of a partition or ``None``, and ``public`` the honest blocks."""
    if config.adversary_strategy != "withhold":
        raise ValueError("needs adversary_strategy='withhold'")
    root = seedseq_for(config)
    c_stake, c_graph, c_lottery, c_aux = root.spawn(4)
    stake = make_stake(config, np.random.default_rng(c_stake))
    mask = _adversary_mask(config, stake)
    side = _partition_mask(config, stake, mask)
    path_latency = topology.build_path_latency(config, np.random.default_rng(c_graph))
    d_est = np.full(config.n_nodes, float(stake.sum()) * stake_scale)
    p = lottery.win_probs(stake, d_est, config.f)
    slots, nodes = lottery.sample_wins(p, config.epoch_len, np.random.default_rng(c_lottery))
    active, groups = lottery.group_by_slot(slots, nodes)
    tree, arrival = build_tree_pernode(active, groups, path_latency, config,
                                       np.random.default_rng(c_aux), adversary_mask=mask,
                                       partition_mask=side)
    if mask is None:
        mask = np.zeros(config.n_nodes, dtype=bool)
    adv = mask[tree.leader.clip(min=0)] & (tree.slot >= 0)
    public = (tree.slot >= 0) & ~adv
    return tree, arrival, stake, mask, side, public


def partition_tree(config: SimConfig):
    """``_tree`` for a partitioned network: ``(tree, arrival, stake, mask, side, public)``."""
    if config.partition_share <= 0.0:
        raise ValueError("needs partition_share > 0")
    return _tree(config)


def withhold_tree(config: SimConfig, stake_scale: float = 1.0):
    """The engine's block tree under a withholding coalition: ``(tree, arrival, mask, public,
    canonical)`` with ``arrival[i, b]`` the slot block ``b`` reaches node ``i``, ``mask`` the
    coalition's nodes, ``public`` the honest blocks and ``canonical`` the best public chain.
    ``stake_scale`` as in ``_tree``."""
    if config.adversary_frac <= 0:
        raise ValueError("needs adversary_frac > 0")
    tree, arrival, _, mask, _, public = _tree(config, stake_scale)
    # best public tip: highest, then earliest slot, then lowest id
    ids = np.nonzero(public)[0]
    order = np.lexsort((-ids, -tree.slot[ids], tree.height[ids]))
    b = int(ids[order[-1]])
    canonical = np.zeros(tree.n_blocks, dtype=bool)
    while b > 0:
        canonical[b] = True
        b = int(tree.parent[b])
    return tree, arrival, mask, public, canonical


def withhold_timelines(config: SimConfig,
                       stake_scale: float = 1.0) -> tuple[np.ndarray, np.ndarray, float]:
    """Canonical slots, the coalition's distinct winning slots, and the honest orphan share."""
    tree, _, mask, public, canonical = withhold_tree(config, stake_scale)
    adv = mask[tree.leader.clip(min=0)] & (tree.slot >= 0)
    canon_slots = np.sort(tree.slot[canonical]).astype(np.int64)
    adv_slots = np.unique(tree.slot[adv]).astype(np.int64)
    orphan = 1.0 - canonical[public].sum() / public.sum()
    return canon_slots, adv_slots, float(orphan)


def fallback_blocks(tree, arrival: np.ndarray, public: np.ndarray, fallback_slots: float) -> np.ndarray:
    """The honest blocks that reached their first other node no sooner than the sender's fallback
    would deliver them, ``1 + fallback_slots`` after the slot: under dropping relays, the blocks
    every copy of which was dropped."""
    out = np.zeros(public.size, dtype=bool)
    for b in np.nonzero(public)[0]:
        col = arrival[:, b].copy()
        col[int(tree.leader[b])] = np.inf                     # the producer holds it from the slot
        out[b] = col.min() - tree.slot[b] >= 1.0 + fallback_slots
    return out


def fallback_share(tree, arrival: np.ndarray, public: np.ndarray, fallback_slots: float) -> float:
    """The share of honest blocks delivered by the sender's fallback (``fallback_blocks``)."""
    return float(fallback_blocks(tree, arrival, public, fallback_slots)[public].mean())


@njit(cache=True)
def _race(canon, adv, k_max, give_up, premine, win_at):
    """Successes per K (index K-1), the number of scored targets, and for each target the deepest
    acceptance the attack beats (0 if none, -1 if the target is not scored)."""
    n_c, n_a = canon.size, adv.size
    succ = np.zeros(k_max, np.int64)
    deepest = np.full(n_c, -1, np.int64)
    scored = 0
    # lead just before each canonical block: premined, or counted from the parent's appearance
    lead_before = np.zeros(n_c, np.int64)
    since_parent = np.zeros(n_c, np.int64)
    lead, ia = 0, 0
    for i in range(n_c):
        wins = 0
        while ia < n_a and adv[ia] <= canon[i]:       # wins count first within a slot
            lead += 1
            wins += 1
            ia += 1
        lead_before[i] = lead
        since_parent[i] = wins
        lead = lead - 1 if lead > 0 else 0
    # races
    ja0 = 0
    for i in range(n_c - k_max - 1):
        start = lead_before[i] if premine else since_parent[i]
        r = start - 1
        while ja0 < n_a and adv[ja0] <= canon[i]:
            ja0 += 1
        ja, ic = ja0, i + 1
        best_after = np.full(k_max, -(1 << 30), np.int64)
        depth = 0                                     # canonical blocks on top of b_i so far
        truncated = False
        while True:
            next_adv = adv[ja] if ja < n_a else np.int64(1 << 62)
            next_can = canon[ic] if ic < n_c else np.int64(1 << 62)
            if next_adv == (1 << 62) and next_can == (1 << 62):
                truncated = True
                break
            if next_adv <= next_can:
                r += 1
                ja += 1
            else:
                r -= 1
                ic += 1
                depth += 1
            for kk in range(min(depth, k_max)):       # accepted at depth kk+1 already
                if r > best_after[kk]:
                    best_after[kk] = r
            if r < -give_up and depth >= k_max:
                break
        if truncated and depth < k_max:
            continue
        scored += 1
        deepest[i] = 0
        for kk in range(k_max):
            if best_after[kk] >= win_at:
                succ[kk] += 1
                deepest[i] = kk + 1
    return succ, scored, deepest


def race(canon_slots: np.ndarray, adv_slots: np.ndarray, k_max: int, give_up: int = 60,
         premine: bool = True, win_at: int = 1) -> tuple[np.ndarray, int]:
    """Attack successes at each acceptance depth 1..k_max, and the number of scored targets."""
    succ, scored, _ = _race(np.asarray(canon_slots, np.int64), np.asarray(adv_slots, np.int64),
                            k_max, give_up, premine, win_at)
    return succ, scored


def race_depths(canon_slots: np.ndarray, adv_slots: np.ndarray, k_max: int, give_up: int = 60,
                premine: bool = True, win_at: int = 1) -> np.ndarray:
    """For each canonical block, the deepest acceptance depth (at most k_max) the attack beats: 0
    if none, -1 if the block is not scored."""
    return _race(np.asarray(canon_slots, np.int64), np.asarray(adv_slots, np.int64), k_max,
                 give_up, premine, win_at)[2]
