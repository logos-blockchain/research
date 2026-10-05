"""Phase D6: votes on the engine's block trees (PLAN.md D6).

A round starts at slot ``t``. Each node votes for the block its own chain holds ``L`` slots back:
the latest block with ``slot <= t - L`` on the best chain it has received by ``t`` (height, then
earlier slot, then lower id, as the engine's fork choice). Its seats, a Poisson draw with the
expectation its stake gives, all carry that vote. A vote reaches node ``j`` through Blend as a block
from the same sender would. Node ``j`` holds a certificate once the seats of the votes it has
received for one block reach the quorum ``Q``.
"""

from __future__ import annotations

import numpy as np


def local_tips(tree, arrival: np.ndarray, t: float) -> np.ndarray:
    """Each node's best received block at time ``t``."""
    c2 = float(tree.slot.size + 1)
    c1 = (float(tree.slot.max()) + 2.0) * c2
    key = tree.height * c1 - tree.slot * c2 - np.arange(tree.slot.size)
    masked = np.where(arrival <= t, key[None, :], -np.inf)
    return masked.argmax(axis=1)


def vote_targets(tree, tips: np.ndarray, t: float, lag: int) -> np.ndarray:
    """For each tip, its latest ancestor (itself included) whose slot is at most ``t - lag``."""
    out = np.empty(tips.size, np.int64)
    cache: dict[int, int] = {}
    for i, b0 in enumerate(tips.tolist()):
        if b0 in cache:
            out[i] = cache[b0]
            continue
        b = b0
        while b > 0 and tree.slot[b] > t - lag:
            b = int(tree.parent[b])
        cache[b0] = b
        out[i] = b
    return out


def certificate_times(vote_arrival: np.ndarray, seats: np.ndarray, targets: np.ndarray,
                      quorum: int) -> np.ndarray:
    """When each node first holds ``quorum`` seats on one block (inf if never).

    ``vote_arrival[i, j]`` is when voter ``i``'s vote reaches node ``j``.
    """
    n_nodes = vote_arrival.shape[1]
    out = np.full(n_nodes, np.inf)
    for b in np.unique(targets):
        voters = np.nonzero((targets == b) & (seats > 0))[0]
        if seats[voters].sum() < quorum:
            continue
        arr = vote_arrival[voters]                       # (voters, nodes)
        order = np.argsort(arr, axis=0)
        cum = np.cumsum(seats[voters][order], axis=0)
        first = np.argmax(cum >= quorum, axis=0)
        t_b = np.take_along_axis(arr, order, axis=0)[first, np.arange(n_nodes)]
        out = np.minimum(out, t_b)
    return out
