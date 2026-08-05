"""Proposer-local uncle selection.

Two models, switched by ``config.uncle_model`` (CLI: ``--old``):

**countable** (default) — the spec's counting-only model (cryptarchia-v1-protocol.md,
Uncle Selection): candidates are orphan blocks in the producer's view within the DERIVED
window ``w_u = window_absorption / f`` whose **parent lies on the producer's chain** (only
the first block of a fork is countable), excluding candidates whose slot is already
occupied on that chain (by a canonical block or an already-referenced uncle), and picking
at most one uncle per slot, oldest-first (or the ``random`` sensitivity knob).

**old** (pre-redesign; kept verbatim for ``--old`` reproduction) — candidates are ANY
orphan blocks in view with ``0 < slot_B - slot_U <= uncle_window``, regardless of fork
depth, that are not on the producer's chain and not already referenced by it; dedup is by
block id only (no slot exclusion).

Selected refs are baked at production and immutable once adopted, so density counting
stays view-independent under both models.

``select_uncles_at_production`` is the ONLY selection entry point — blocktree.py calls it
once per produced block. Tests drive it through the same signature (see
tests/test_uncles.py ``annotate_via_production``) rather than through a parallel offline
implementation, so there is no second copy of the rules to drift out of sync.
"""

from __future__ import annotations

import numpy as np

from .blocktree import GENESIS
from .config import SimConfig


def _select(
    window_ids: np.ndarray,
    referenced: set[int],
    config: SimConfig,
    rng: np.random.Generator,
    slot: np.ndarray | None = None,
    one_per_slot: bool = False,
) -> list[int]:
    """Pick up to ``max_uncles`` candidates. ``one_per_slot`` adds the countable model's
    per-slot dedup (a second same-slot candidate adds no occupied slot, so it is skipped)."""
    u_max = config.max_uncles
    out: list[int] = []
    slots_taken: set[int] = set()
    if config.uncle_strategy == "oldest":
        for bid in window_ids.tolist():
            if bid in referenced:
                continue
            if one_per_slot:
                s = int(slot[bid])
                if s in slots_taken:
                    continue
                slots_taken.add(s)
            out.append(bid)
            if len(out) >= u_max:
                break
    elif config.uncle_strategy == "random":
        p = config.uncle_random_p
        for bid in window_ids.tolist():
            if bid in referenced:
                continue
            if one_per_slot and int(slot[bid]) in slots_taken:
                continue
            if rng.random() < p:
                if one_per_slot:
                    slots_taken.add(int(slot[bid]))
                out.append(bid)
                if len(out) >= u_max:
                    break
    else:  # pragma: no cover - guarded by Literal
        raise ValueError(config.uncle_strategy)
    return out


def select_uncles_at_production(
    slot: np.ndarray,
    parent: np.ndarray,
    uncles: list,
    arrival_v: np.ndarray,
    nb: int,
    parent_id: int,
    t: int,
    config: SimConfig,
    rng: np.random.Generator,
    arr_base: int = 0,
) -> tuple[int, ...]:
    """Uncles a block gets when produced by node ``v`` (arrival row ``arrival_v``) at slot ``t``.

    Candidates are blocks in ``v``'s view (``arrival_v[b] <= t``) with slot in
    ``[t-w_u, t)`` that are NOT on the chain ``v`` extends (ancestors of ``parent_id``) and
    not already referenced by that chain; the countable model (default) additionally
    requires the candidate's **parent to lie on that chain** (first block of its fork),
    excludes candidates whose slot is already occupied on the chain, and picks at most one
    per slot. Selected once and baked globally (same for everyone who adopts the block), so
    density counting stays view-independent.

    ``arrival_v`` is indexed by *block id minus ``arr_base``* — ``arr_base=0`` for the full arrival
    matrix row ``A[v]``, or the sliding-window buffer's base offset when pruning (every uncle-window
    block ``[t-w_u, t)`` is inside the kept span, so the buffer row covers all candidates).
    """
    u_max = config.max_uncles
    if u_max <= 0:
        return ()
    w = config.effective_uncle_window
    slot_view = slot[:nb]
    lo = int(np.searchsorted(slot_view, t - w, side="left"))   # slot >= t-w_u
    hi = int(np.searchsorted(slot_view, t, side="left"))       # slot <  t
    if hi <= lo:
        return ()
    # blocks in the window that have arrived at v (candidates before excluding own chain)
    arrived = np.nonzero(arrival_v[lo - arr_base:hi - arr_base] <= t)[0] + lo
    if arrived.size == 0:
        return ()

    if config.uncle_model == "old":
        # --- old model (pre countable redesign; kept verbatim for --old) ----------------
        # v's own chain within the window + the uncles it already references (for dedup)
        on_chain: set[int] = set()
        referenced: set[int] = set()
        a = int(parent_id)
        while a > GENESIS and int(slot[a]) >= t - w:
            on_chain.add(a)
            referenced.update(uncles[a])
            a = int(parent[a])
        cands = np.array(
            [b for b in arrived.tolist()
             if b > GENESIS and b not in on_chain and b not in referenced],
            dtype=np.int64,
        )
        if cands.size == 0:
            return ()
        return tuple(_select(cands, set(), config, rng))   # cands already oldest-first (slot,id)

    # --- countable model (spec counting rules; the default) -----------------------------
    # Window walk over v's chain: chain blocks, their referenced uncles, and the slots both
    # occupy (the spec's occupied-slot exclusion in Uncle Selection).
    on_chain = set()
    referenced = set()
    occupied: set[int] = set()
    a = int(parent_id)
    while a > GENESIS and int(slot[a]) >= t - w:
        on_chain.add(a)
        occupied.add(int(slot[a]))
        for u in uncles[a]:
            referenced.add(u)
            su = int(slot[u])
            if su >= t - w:
                occupied.add(su)
        a = int(parent[a])
    pre = [b for b in arrived.tolist()
           if b > GENESIS and b not in on_chain and b not in referenced
           and int(slot[b]) not in occupied]
    if not pre:
        return ()
    # Parent-on-chain (only the first block of a fork is countable): the window walk covers
    # parents inside the window; extend chain membership exactly far enough below it to
    # decide the oldest candidate parent (cheap — parents are typically recent).
    pmin = min(int(slot[int(parent[b])]) for b in pre)
    below: set[int] = set()
    while a > GENESIS and int(slot[a]) >= pmin:
        below.add(a)
        a = int(parent[a])
    chain_ids = on_chain | below
    cands = np.array(
        [b for b in pre if int(parent[b]) == GENESIS or int(parent[b]) in chain_ids],
        dtype=np.int64,
    )
    if cands.size == 0:
        return ()
    # cands already oldest-first (slot, id); one uncle per slot per the spec's selection.
    return tuple(_select(cands, set(), config, rng, slot=slot, one_per_slot=True))
