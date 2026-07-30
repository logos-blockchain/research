"""Block tree, latency-driven forks, and honest longest-chain fork choice.

Blocks are stored in parallel arrays (id == index). A virtual genesis is block 0 at
slot -1, height 0. Every real block is produced at an active slot by one winning node
and points at the best tip *visible to that node at production time*, which is what makes
network latency (and same-slot multi-winners) produce forks.

Fork choice is honest longest-chain with a first-seen tie-break (prefer higher height,
then earlier slot, then lower id) — no adversary is modelled, so the spec's density /
deep-fork rules never engage.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from .latency import LatencyModel

GENESIS = 0


@dataclass
class BlockTree:
    slot: np.ndarray          # int64, slot of each block (genesis = -1)
    parent: np.ndarray        # int64, parent id (genesis = -1)
    height: np.ndarray        # int64, chain height (genesis = 0)
    leader: np.ndarray        # int64, producing node id (genesis = -1)
    uncles: list[tuple[int, ...]]   # referenced uncle ids per block (filled later)

    @property
    def n_blocks(self) -> int:
        return self.slot.shape[0]

    def ancestors(self, block_id: int) -> list[int]:
        """Ancestor chain of ``block_id`` from itself down to (excluding) genesis."""
        out: list[int] = []
        b = block_id
        while b > GENESIS:
            out.append(b)
            b = int(self.parent[b])
        return out

    def canonical_chain(self) -> list[int]:
        """Honest longest-chain: ancestors of the best tip over the whole tree.

        Returns real block ids (genesis excluded), tip-first.
        """
        tip = self._best_over_all()
        return self.ancestors(tip)

    def _rank(self, bid: int) -> tuple[int, int, int]:
        # Preference order for "better tip": higher height, earlier slot, lower id.
        return (int(self.height[bid]), -int(self.slot[bid]), -bid)

    def _best_over_all(self) -> int:
        best = GENESIS
        best_rank = self._rank(GENESIS)
        for bid in range(1, self.n_blocks):
            r = self._rank(bid)
            if r > best_rank:
                best_rank, best = r, bid
        return best


def build_tree(
    active_slots: np.ndarray,
    winners_per_slot: list[np.ndarray],
    latency: LatencyModel,
    rng: np.random.Generator,
) -> BlockTree:
    """Construct the block tree from grouped lottery winners under a latency model."""
    # Preallocate with genesis in slot 0.
    slot = [-1]
    parent = [-1]
    height = [0]
    leader = [-1]

    # global_best = best publicly-visible tip so far, as (height, slot, id).
    def better(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
        # higher height, then earlier slot, then lower id
        ah, as_, ai = a
        bh, bs, bi = b
        if ah != bh:
            return a if ah > bh else b
        if as_ != bs:
            return a if as_ < bs else b
        return a if ai < bi else b

    global_best = (0, -1, GENESIS)
    own_best: dict[int, tuple[int, int, int]] = {}
    # min-heap of (visible_at, block_id) awaiting public visibility
    pending: list[tuple[int, int]] = []

    next_id = 1
    for si in range(active_slots.shape[0]):
        t = int(active_slots[si])
        # advance visibility frontier to slot t
        while pending and pending[0][0] <= t:
            _, bid = heapq.heappop(pending)
            cand = (height[bid], slot[bid], bid)
            global_best = better(global_best, cand)
        for v in winners_per_slot[si].tolist():
            gb = global_best
            ob = own_best.get(v, (0, -1, GENESIS))
            chosen = better(gb, ob)
            p_id = chosen[2]
            h = chosen[0] + 1
            bid = next_id
            next_id += 1
            slot.append(t)
            parent.append(p_id)
            height.append(h)
            leader.append(v)
            own_best[v] = (h, t, bid)
            va = latency.visible_at(t, rng)
            heapq.heappush(pending, (va, bid))

    return BlockTree(
        slot=np.asarray(slot, np.int64),
        parent=np.asarray(parent, np.int64),
        height=np.asarray(height, np.int64),
        leader=np.asarray(leader, np.int64),
        uncles=[() for _ in range(next_id)],
    )
