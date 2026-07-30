"""Total Stake Inference: density counting and the per-epoch estimate update.

The estimate counts *slots*, preserving the pre-uncle design invariant "one count per
slot" (the slot lottery is calibrated so slots activate at rate ``f``; multiple winners
of one slot must not inflate the count): ``m = canonical-occupied slots in window +
distinct referenced-uncle slots in window that are NOT already canonical-occupied``.
``legacy_block_count=True`` reproduces the earlier (buggy) block-id counting, which
double-counted same-slot co-winners and inflated the equilibrium by c(f); kept only as a
flag, not used by any study.
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


def density_m(tree: BlockTree, canonical_ids: list[int], T: int,
              legacy_block_count: bool = False) -> int:
    """Slot count ``m`` for the TSI update: canonical slots + recovered uncle slots.

    A slot counts at most once: canonical blocks occupy distinct slots by construction, and
    a referenced uncle contributes only if its slot is not already canonical-occupied (and
    only once per slot, however many same-slot uncles are referenced). ``legacy_block_count``
    reproduces the earlier per-block-id counting (double-counts multi-winner slots).
    """
    s = tree.slot[canonical_ids]
    in_win = (s >= 0) & (s < T)
    honest = int(in_win.sum())
    ref = referenced_uncle_ids(tree, canonical_ids)
    if legacy_block_count:
        return honest + sum(1 for u in ref if _in_window(int(tree.slot[u]), T))
    canon_slots = set(int(x) for x in s[in_win])
    rec_slots = {int(tree.slot[u]) for u in ref
                 if _in_window(int(tree.slot[u]), T) and int(tree.slot[u]) not in canon_slots}
    return honest + len(rec_slots)


# On-chain fixed-point scale for the target rate f. The original spec used 1000 (three decimals),
# which rounds f=1/30 to f_p=0.033 and leaves a ~1% (f/f_p) over-estimate — the sole residual bias
# after the slot-counting fix (Appendix A). Raised to 1_000_000 (six decimals) per the report's
# recommendation: f_p=0.033333, so f/f_p=1.00000, and the residual drops below 10^-5 (negligible).
PRECISION = 1_000_000


def _f_eff(f: float, fixed_point: bool) -> float:
    """Target rate used in the recursion: exact ``f``, or the spec's integer quantisation.

    Guards the quantised path against ``f`` so small that ``int(f*PRECISION) == 0`` (e.g. f < .001),
    which would make ``f_eff = 0`` and divide-by-zero in the recursion.
    """
    if not fixed_point:
        return f
    q = int(f * PRECISION)
    if q == 0:
        raise ValueError(
            f"fixed_point=True with f={f} quantises the target rate to 0 "
            f"(int(f*{PRECISION})==0); use f >= 1/{PRECISION} or fixed_point=False")
    return q / PRECISION


def update_D(
    d_prev: float, m: int, T: int, f: float, beta: float, fixed_point: bool = False
) -> float:
    """Spec TSI recursion: ``max(1, D_prev * (1 - beta*(f_eff - m/T)/f_eff))``.

    With ``fixed_point=True`` the target rate ``f`` is quantised as the on-chain algorithm does
    (``f_p = int(f*PRECISION)/PRECISION``). At the raised ``PRECISION = 10**6`` this is
    ``f_p = 0.033333`` for f=1/30, so ``f/f_p = 1.00001`` and the residual over-estimate is
    below 10^-5 (negligible) — the report's f-precision recommendation, applied. (At the
    original spec ``PRECISION = 1000`` the offset was ~1%.)
    """
    f_eff = _f_eff(f, fixed_point)
    measured_density = m / T
    d_new = d_prev * (1.0 - beta * (f_eff - measured_density) / f_eff)
    return max(d_new, 1.0)


def update_D_vec(
    d_prev: np.ndarray, m: np.ndarray, T: int, f: float, beta: float, fixed_point: bool = False,
) -> np.ndarray:
    """Per-node TSI recursion: :func:`update_D` applied elementwise over ``(N,)`` arrays.

    Each node updates its OWN estimate ``d_prev[i]`` from its OWN measured slot count
    ``m[i]``. Identical formula to :func:`update_D`, clamped at 1.
    """
    f_eff = _f_eff(f, fixed_point)
    measured_density = np.asarray(m, dtype=float) / T
    d_new = np.asarray(d_prev, dtype=float) * (1.0 - beta * (f_eff - measured_density) / f_eff)
    return np.maximum(d_new, 1.0)


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
