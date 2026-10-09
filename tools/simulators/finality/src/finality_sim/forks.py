"""The forks a client receives beside a target block: the blocks that could sit on a chain
without it (DESIGNS.md, H.3).

A block descends from the target or not. An honest block that descends from the target can never
sit on a chain that excludes it, so a client bounding such a chain counts only the received blocks
that do not descend from the target and have a slot after the target's parent's; the blocks with
earlier slots belong to the lead before the parent.
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
    """For each canonical block in slot order, the number of public blocks with a slot after its
    parent's that do not descend from it: those whose deepest canonical ancestor lies below it.
    Every public block counts, however late it arrives, so the count is the client's at any time
    after the forks have reached it."""
    fp = fork_points(tree.parent, canonical)
    cids = np.nonzero(canonical)[0]
    cids = cids[np.argsort(tree.slot[cids], kind="stable")]
    parent_slot = tree.slot[tree.parent[cids]]
    height = tree.height[cids]
    xs = np.nonzero(public & ~canonical)[0]
    if xs.size == 0:
        return np.zeros(cids.size, np.int64)
    x_slot = tree.slot[xs]
    x_fork_height = tree.height[fp[xs]]
    hit = (x_slot[None, :] > parent_slot[:, None]) & (x_fork_height[None, :] < height[:, None])
    return hit.sum(axis=1).astype(np.int64)
