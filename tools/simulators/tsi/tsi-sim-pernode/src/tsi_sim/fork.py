"""Fork structure of the global block tree: fork rate and reorg depth.

Both are read off the final canonical chain (the best arrived tip\'s ancestry, the chain all
honest nodes agree on past k-finality):

* ``fork_rate``  = orphaned blocks / total blocks, over blocks with slot in the window. The
  share of produced blocks that lost their race and left the canonical chain.
* ``max_reorg_depth`` = the length of the deepest *maximal orphan branch* — the number of
  consecutive non-canonical blocks a node that had adopted that branch would discard on
  switching to canonical. This is the worst-case reorg (reorganisation) an honest node could
  suffer, and its cost is what deep-fork-avoidance optimises.

``lost_slots`` reads the same chain: the occupied slots of the window that neither the chain
nor the uncles it counts cover, split by fork depth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .blocktree import BlockTree


def canonical_and_depth(tree: BlockTree, A, cutoff: int) -> tuple[np.ndarray, np.ndarray]:
    """The final canonical chain as a block mask, and each block's fork depth.

    The chain is the best *arrived* tip's ancestry by (height, -slot, -id). ``A`` is only used
    to exclude withheld blocks (which reach no node) from the tip selection. ``depth[b]`` is the
    length of the non-canonical run ending at ``b``: 0 on the chain, 1 for the first block of a
    fork. Requires ``tree.n_blocks > 1``.
    """
    nb = tree.n_blocks
    ids = np.arange(nb)
    if isinstance(A, np.ndarray):
        arrived = (A <= cutoff).any(axis=0)
    else:
        arrived = np.ones(nb, dtype=bool)
    arrived[0] = True
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])

    canonical = np.zeros(nb, dtype=bool)
    b = best
    while b > 0:
        canonical[b] = True
        b = int(tree.parent[b])
    canonical[0] = True

    # Parent-before-child holds because a block\'s parent has a strictly smaller id (built earlier).
    depth = np.zeros(nb, dtype=np.int64)
    for b in range(1, nb):
        if not canonical[b]:
            depth[b] = depth[int(tree.parent[b])] + 1
    return canonical, depth


def fork_stats(tree: BlockTree, A, T: int, cutoff: int,
               coalition_mask=None) -> tuple[float, int, float, float, float, float]:
    """Return ``(fork_rate, max_reorg_depth, mean_reorg_depth, p_ref, p_ref_honest,
    deep_orphan_share)``.

    ``p_ref`` is the emergent **reference rate**: the fraction of in-window orphans that some
    canonical block references as an uncle — the quantity the §6.8 soft-inclusion argument
    assumes is high. ``A`` is the arrival matrix (full ``np.ndarray`` or pruned): only used to
    exclude withheld blocks (which reach no node) from canonical-tip selection.

    ``p_ref_honest`` restricts that to orphans produced by nodes OUTSIDE ``coalition_mask``.
    Under a private-chain attack the two diverge and only the honest one measures the repair the
    report credits to uncle counting: an attacker's own discarded blocks are its loss to bear,
    and counting them would flatter `p_ref` with orphans nobody is owed. Equal to ``p_ref`` when
    no mask is given.
    """
    nb = tree.n_blocks
    if nb <= 1:
        return 0.0, 0, 0.0, 1.0, 1.0, 0.0
    in_win = (tree.slot >= 0) & (tree.slot < T)
    total = int(in_win.sum())
    if total == 0:
        return 0.0, 0, 0.0, 1.0, 1.0, 0.0

    canonical, depth = canonical_and_depth(tree, A, cutoff)

    orphan_in_win = in_win & ~canonical
    n_orphan = int(orphan_in_win.sum())
    fork_rate = float(n_orphan) / total
    # reorg depth per maximal orphan branch = depth at its deepest block; take branch tips
    has_child = np.zeros(nb, dtype=bool)
    has_child[tree.parent[1:]] = True
    tips = (~has_child) & orphan_in_win
    branch_depths = depth[tips]
    max_depth = int(branch_depths.max()) if branch_depths.size else 0
    mean_depth = float(branch_depths.mean()) if branch_depths.size else 0.0

    # p_ref: fraction of in-window orphans referenced as an uncle by a canonical block, directly
    # or through a re-rooted copy (a spent win stands for no block)
    referenced = np.zeros(nb, dtype=bool)
    for b in np.nonzero(canonical)[0]:
        for u in tree.uncles[b]:
            o = tree.original(u)
            if o >= 0:
                referenced[o] = True
    ref_orphans = int((orphan_in_win & referenced).sum())
    p_ref = ref_orphans / n_orphan if n_orphan else 1.0

    if coalition_mask is None:
        p_ref_honest = p_ref
    else:
        honest_orphan = orphan_in_win & ~np.asarray(coalition_mask)[tree.leader]
        n_ho = int(honest_orphan.sum())
        p_ref_honest = (int((honest_orphan & referenced).sum()) / n_ho) if n_ho else 1.0

    # Share of in-window orphans that sit DEEPER than the first block of their fork, i.e. whose
    # parent is itself off-chain. These are exactly the blocks the countable rule can never
    # reference (§2.1), so this is the direct structural observable behind the first-fork cost —
    # p_ref conflates it with orphans that were merely never picked up.
    deep_orphan_share = (float((depth[orphan_in_win] >= 2).sum()) / n_orphan) if n_orphan else 0.0
    return fork_rate, max_depth, mean_depth, p_ref, p_ref_honest, deep_orphan_share


@dataclass(frozen=True)
class LostSlots:
    """Occupied slots of the window that the count misses, by the fork depth of their blocks."""

    occupied: int                         # distinct occupied slots in [0, T)
    by_depth: tuple[int, int, int, int]   # lost slots whose shallowest block is at depth
                                          # 1, 2, 3, >= 4
    d2_parent_ref: int                    # depth-2 lost slots with a block whose parent (the
                                          # first block of its fork) is a counted uncle
    rerooted: tuple[int, int, int, int] = (0, 0, 0, 0)   # slots only counted re-rooted copies
                                          # cover, by the same depth; not lost
    spent: tuple[int, int] = (0, 0)       # slots of [0, T) only spent notes won (no block
                                          # holds them), and those the count covers
    honest: tuple[int, int, int, int] = (0, 0, 0, 0)   # lost slots holding a block from outside
                                          # the coalition, by the shallowest such block's depth
    unpublished: int = 0                  # lost slots none of whose blocks reached a node
                                          # outside the coalition

    @property
    def lost(self) -> int:
        return sum(self.by_depth)


def lost_slots(tree: BlockTree, A, T: int, cutoff: int, scope_refs: bool = True,
               coalition_mask=None) -> LostSlots:
    """Classify the occupied slots of ``[0, T)`` against the final canonical chain.

    A slot is covered when it holds a canonical block or an uncle the chain counts: one carried
    by a canonical block, and under ``scope_refs`` (the spec rule) by one that lies in the window
    itself. Every other occupied slot is lost, and is filed under the smallest fork depth among its
    blocks (``canonical_and_depth``). ``d2_parent_ref`` marks the depth-2 lost slots a cousin rule
    could count: those with a block whose parent is a counted uncle. A counted re-rooted copy
    covers its original's slot; the slots only copies cover are filed under ``rerooted`` instead.
    A counted spent win covers its slot too.

    ``honest`` files the lost slots that hold a block of a node outside ``coalition_mask`` (every
    block without one) under the smallest depth among those blocks. ``unpublished`` counts the lost
    slots whose blocks reached no node outside the coalition: an adversary's withheld blocks and
    the private blocks it never released (PLAN.md Phase 4).

    ``occupied - lost + spent[1]`` equals the slot count ``measure`` reads from the same chain
    (asserted in tests/test_fork.py), so the depth shares sum to the estimator's own shortfall.
    """
    nb = tree.n_blocks
    if nb <= 1:
        return LostSlots(0, (0, 0, 0, 0), 0)
    canonical, depth = canonical_and_depth(tree, A, cutoff)
    in_win = (tree.slot >= 0) & (tree.slot < T) & (np.arange(nb) > 0)
    honest_node = (None if coalition_mask is None else ~np.asarray(coalition_mask))
    honest_block = (np.ones(nb, bool) if honest_node is None
                    else honest_node[np.maximum(tree.leader, 0)])
    if not isinstance(A, np.ndarray):
        public = np.ones(nb, bool)
    else:
        public = ((A if honest_node is None else A[honest_node]) <= cutoff).any(axis=0)
    counted = np.zeros(nb, dtype=bool)
    copy_slots: set[int] = set()
    spent_slots: set[int] = set()
    for b in np.nonzero(canonical & in_win if scope_refs else canonical)[0]:
        for u in tree.uncles[b]:
            if u < nb:
                counted[u] = True
            elif tree.copy_of[u - nb] >= 0:
                copy_slots.add(int(tree.copy_slot[u - nb]))
            else:
                spent_slots.add(int(tree.copy_slot[u - nb]))
    occupied = set(tree.slot[in_win].tolist())
    lone = {int(s) for s in tree.copy_slot[tree.copy_of < 0] if 0 <= s < T} - occupied
    covered = set(tree.slot[in_win & (canonical | counted)].tolist()) | spent_slots
    shallowest: dict[int, int] = {}
    shallowest_honest: dict[int, int] = {}
    parent_ref: set[int] = set()
    published: set[int] = set()
    for b in np.nonzero(in_win & ~canonical)[0]:
        s = int(tree.slot[b])
        if s in covered:
            continue
        d = int(depth[b])
        shallowest[s] = min(shallowest.get(s, d), d)
        if honest_block[b]:
            shallowest_honest[s] = min(shallowest_honest.get(s, d), d)
        if public[b]:
            published.add(s)
        if d == 2 and counted[int(tree.parent[b])]:
            parent_ref.add(s)
    by_depth = [0, 0, 0, 0]
    rerooted = [0, 0, 0, 0]
    for s, d in shallowest.items():
        (rerooted if s in copy_slots else by_depth)[min(d, 4) - 1] += 1
    honest = [0, 0, 0, 0]
    for s, d in shallowest_honest.items():
        if s not in copy_slots:
            honest[min(d, 4) - 1] += 1
    return LostSlots(occupied=len(occupied),
                     by_depth=(by_depth[0], by_depth[1], by_depth[2], by_depth[3]),
                     d2_parent_ref=sum(1 for s in parent_ref
                                       if shallowest[s] == 2 and s not in copy_slots),
                     rerooted=(rerooted[0], rerooted[1], rerooted[2], rerooted[3]),
                     spent=(len(lone), len(lone & spent_slots)),
                     honest=(honest[0], honest[1], honest[2], honest[3]),
                     unpublished=sum(1 for s in shallowest
                                     if s not in published and s not in copy_slots))


@dataclass(frozen=True)
class ParentWait:
    """The validators route F makes wait (PLAN.md Phase 2d), over the canonical window blocks."""

    block_share: float     # share of those blocks with an entry whose parent is off the chain
    node_share: float      # mean over such blocks of the node share that receives the block
                           # before every such parent
    wait_mean: float       # mean wait of those nodes, slots
    wait_max: float        # longest wait, slots


def parent_wait(tree: BlockTree, A, T: int, cutoff: int, n_nodes: int) -> ParentWait:
    """Aggregate ``tree.parent_wait`` over the canonical blocks of ``[0, T)``.

    NaN where nothing is measured: every field without deeper rules, all but ``block_share`` in
    an epoch whose chain carries no such entry, and ``wait_mean`` in one where no node waits.
    """
    nan = float("nan")
    if tree.parent_wait is None:
        return ParentWait(nan, nan, nan, nan)
    canonical, _ = canonical_and_depth(tree, A, cutoff)
    in_win = canonical & (tree.slot >= 0) & (tree.slot < T)
    in_win[0] = False
    rows = tree.parent_wait[in_win]
    has = ~np.isnan(rows[:, 0])
    if not has.any():
        return ParentWait(0.0 if rows.shape[0] else nan, nan, nan, nan)
    late, total, longest = rows[has].T
    return ParentWait(block_share=float(has.mean()),
                      node_share=float((late / n_nodes).mean()),
                      wait_mean=float(total.sum() / late.sum()) if late.sum() else nan,
                      wait_max=float(longest.max()))
