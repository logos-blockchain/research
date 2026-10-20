"""The forks a client receives beside a target block: the blocks that could sit on a chain
without it (DESIGNS.md, H.3).

A block descends from the target or not. An honest block that descends from the target can never
sit on a chain that excludes it, so a client bounding such a chain counts only the received blocks
that do not descend from the target and have a slot after the target's parent's; the blocks with
earlier slots belong to the lead before the parent. A chain holds at most one block per slot, so
the client counts the distinct slots of those blocks: one win signed on many branches counts once.
A received block whose ancestry the client cannot yet resolve counts as a fork.
"""

from __future__ import annotations

import numpy as np


def fork_points(parent: np.ndarray, canonical: np.ndarray) -> np.ndarray:
    """For each block, its deepest canonical ancestor, itself when canonical. Parents precede
    children in id order."""
    fp = np.arange(parent.size)
    for b in range(1, parent.size):
        if not canonical[b]:
            fp[b] = fp[parent[b]]
    return fp


def fork_counts(tree, public: np.ndarray, canonical: np.ndarray) -> np.ndarray:
    """For each canonical block in slot order, the number of distinct slots among the public
    blocks with a slot after its parent's that do not descend from it: those whose deepest
    canonical ancestor lies below it. A slot counts when any of its blocks does. Every public
    block counts, however late it arrives, so the count is the client's at any time after the
    forks have reached it."""
    fp = fork_points(tree.parent, canonical)
    cids = np.nonzero(canonical)[0]
    cids = cids[np.argsort(tree.slot[cids], kind="stable")]
    parent_slot = tree.slot[tree.parent[cids]]
    height = tree.height[cids]
    xs = np.nonzero(public & ~canonical)[0]
    if xs.size == 0:
        return np.zeros(cids.size, np.int64)
    slots, at = np.unique(tree.slot[xs], return_inverse=True)
    low = np.full(slots.size, np.iinfo(np.int64).max)          # the lowest fork point at each slot
    np.minimum.at(low, at, tree.height[fp[xs]].astype(np.int64))
    hit = (slots[None, :] > parent_slot[:, None]) & (low[None, :] < height[:, None])
    return hit.sum(axis=1).astype(np.int64)
