"""Proposer-local uncle selection.

For each canonical block ``B`` (processed oldest-first so ancestors' references are
known), candidates are orphan (non-canonical) blocks ``U`` with
``0 < slot_B - slot_U <= W`` that have not already been referenced by an ancestor of
``B``. Two strategies match the spec: deterministic oldest-first, and random (oldest-first
order, a coin of probability ``uncle_random_p`` per candidate, capped at ``U``). The spec's
coin is unbiased (``uncle_random_p = 0.5``, the default); other values are a non-spec
sensitivity knob. Dedup across ancestors is enforced by threading a ``referenced`` set down
the canonical chain.
"""

from __future__ import annotations

import numpy as np

from .blocktree import BlockTree
from .config import SimConfig


def _orphans_sorted(tree: BlockTree, canonical_ids: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """Return orphan block ids sorted by (slot, id) and their slots."""
    canonical = np.zeros(tree.n_blocks, dtype=bool)
    canonical[canonical_ids] = True
    all_real = np.arange(1, tree.n_blocks)
    orphan_ids = all_real[~canonical[1:]]
    orphan_slots = tree.slot[orphan_ids]
    order = np.lexsort((orphan_ids, orphan_slots))  # by slot, then id
    return orphan_ids[order], orphan_slots[order]


def annotate_uncles(
    tree: BlockTree, canonical_ids: list[int], config: SimConfig, rng: np.random.Generator
) -> None:
    """Fill ``tree.uncles[B]`` for every canonical block ``B`` per the selection rule."""
    u_max = config.max_uncles
    if u_max <= 0:
        return
    w = config.uncle_window
    orphan_ids, orphan_slots = _orphans_sorted(tree, canonical_ids)
    if orphan_ids.size == 0:
        return

    referenced: set[int] = set()
    # oldest canonical block first
    for b in reversed(canonical_ids):
        sb = int(tree.slot[b])
        lo = int(np.searchsorted(orphan_slots, sb - w, side="left"))   # slot_U >= sb - W
        hi = int(np.searchsorted(orphan_slots, sb, side="left"))       # slot_U <  sb
        if hi <= lo:
            continue
        window_ids = orphan_ids[lo:hi]  # already oldest-first
        selected = _select(window_ids, referenced, config, rng)
        if selected:
            tree.uncles[b] = tuple(selected)
            referenced.update(selected)


def _select(
    window_ids: np.ndarray, referenced: set[int], config: SimConfig, rng: np.random.Generator
) -> list[int]:
    u_max = config.max_uncles
    out: list[int] = []
    if config.uncle_strategy == "oldest":
        for bid in window_ids.tolist():
            if bid in referenced:
                continue
            out.append(bid)
            if len(out) >= u_max:
                break
    elif config.uncle_strategy == "random":
        p = config.uncle_random_p
        for bid in window_ids.tolist():
            if bid in referenced:
                continue
            if rng.random() < p:
                out.append(bid)
                if len(out) >= u_max:
                    break
    else:  # pragma: no cover - guarded by Literal
        raise ValueError(config.uncle_strategy)
    return out
