"""Fork structure of the global block tree: fork rate and reorg depth.

Both are read off the final canonical chain (the best arrived tip\'s ancestry, the chain all
honest nodes agree on past k-finality):

* ``fork_rate``  = orphaned blocks / total blocks, over blocks with slot in the window. The
  share of produced blocks that lost their race and left the canonical chain.
* ``max_reorg_depth`` = the length of the deepest *maximal orphan branch* — the number of
  consecutive non-canonical blocks a node that had adopted that branch would discard on
  switching to canonical. This is the worst-case reorg (reorganisation) an honest node could
  suffer, and its cost is what deep-fork-avoidance optimises.
"""

from __future__ import annotations

import numpy as np

from .blocktree import BlockTree


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

    in_win = (tree.slot >= 0) & (tree.slot < T)
    total = int(in_win.sum())
    if total == 0:
        return 0.0, 0, 0.0, 1.0, 1.0, 0.0

    # depth[b] = length of the non-canonical run ending at b (0 if canonical). Parent-before-child
    # holds because a block\'s parent has a strictly smaller id (built earlier).
    depth = np.zeros(nb, dtype=np.int64)
    for b in range(1, nb):
        if not canonical[b]:
            depth[b] = depth[int(tree.parent[b])] + 1

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

    # p_ref: fraction of in-window orphans referenced as an uncle by a canonical block
    referenced = np.zeros(nb, dtype=bool)
    for b in np.nonzero(canonical)[0]:
        for u in tree.uncles[b]:
            referenced[u] = True
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
