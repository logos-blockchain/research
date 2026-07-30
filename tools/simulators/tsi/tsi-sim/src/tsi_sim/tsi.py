"""Total Stake Inference: density counting and the per-epoch estimate update.

The estimate update counts *blocks* exactly as the spec's ``density_over_slots`` does:
``m = honest-chain blocks in window + deduplicated referenced uncle blocks (by their own
slot) in window``. We additionally report slot-based ``q`` / ``q_eff`` (honest and
uncle-recovered active-slot fractions) for comparison against the closed-form theory,
which is written in terms of active-slot utilisation. The two differ only at rare
multi-winner slots.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .blocktree import BlockTree


def referenced_uncle_ids(tree: BlockTree, canonical_ids: list[int]) -> set[int]:
    """Deduplicated set of uncle ids referenced by the canonical chain."""
    ref: set[int] = set()
    for b in canonical_ids:
        ref.update(tree.uncles[b])
    return ref


def _in_window(slot: int, T: int) -> bool:
    return 0 <= slot < T


def density_m(tree: BlockTree, canonical_ids: list[int], T: int) -> int:
    """Block count ``m`` for the TSI update (honest blocks + deduped uncles, in window)."""
    s = tree.slot[canonical_ids]
    honest = int(((s >= 0) & (s < T)).sum())
    ref = referenced_uncle_ids(tree, canonical_ids)
    uncle = sum(1 for u in ref if _in_window(int(tree.slot[u]), T))
    return honest + uncle


def update_D(d_prev: float, m: int, T: int, f: float, beta: float) -> float:
    """Spec TSI recursion: ``max(1, D_prev * (1 - beta*(f - m/T)/f))``."""
    measured_density = m / T
    d_new = d_prev * (1.0 - beta * (f - measured_density) / f)
    return max(d_new, 1.0)


@dataclass
class SlotStats:
    n_active: int          # active slots (>=1 winner) in window
    n_honest: int          # honest-chain-occupied slots in window
    n_recovered: int       # orphan-only slots recovered via referenced uncles
    q: float               # n_honest / n_active
    q_eff: float           # (n_honest + n_recovered) / n_active


def slot_stats(
    tree: BlockTree,
    canonical_ids: list[int],
    ref_uncle_ids: set[int],
    active_slots: np.ndarray,
    T: int,
) -> SlotStats:
    """Slot-based utilisation stats used for theory overlays."""
    active_in = active_slots[(active_slots >= 0) & (active_slots < T)]
    n_active = int(active_in.size)
    honest_slots = {int(tree.slot[b]) for b in canonical_ids if _in_window(int(tree.slot[b]), T)}
    recovered: set[int] = set()
    for u in ref_uncle_ids:
        su = int(tree.slot[u])
        if _in_window(su, T) and su not in honest_slots:
            recovered.add(su)
    n_honest = len(honest_slots)
    n_rec = len(recovered)
    q = n_honest / n_active if n_active else float("nan")
    q_eff = (n_honest + n_rec) / n_active if n_active else float("nan")
    return SlotStats(n_active=n_active, n_honest=n_honest, n_recovered=n_rec, q=q, q_eff=q_eff)
