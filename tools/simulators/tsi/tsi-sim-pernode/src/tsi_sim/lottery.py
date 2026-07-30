"""Stake-weighted slot lottery (sparse sampler).

Per node ``i`` and slot, an independent Bernoulli win with probability
``phi_f(alpha_i) = 1 - (1 - f)^alpha_i`` where ``alpha_i = w_i / D_est``. Multiple winners
in a slot are possible (a guaranteed fork).

The number of slots a node wins is exactly ``Binomial(n_slots, p_i)``, and the won slots
are a uniformly-random distinct subset — this is *distributionally identical* to drawing an
independent Bernoulli(p_i) in every slot, but avoids materialising the dense
``(n_nodes, n_slots)`` array (which was ~95% of the whole simulator's runtime). Winners are
returned as sparse ``(winner_slots, winner_nodes)`` coordinates, sorted by slot.
"""

from __future__ import annotations

import numpy as np
from joblib import Parallel, delayed


def phi(f: float, alpha: np.ndarray | float) -> np.ndarray | float:
    """Leader-lottery win probability ``1 - (1 - f)^alpha``."""
    return 1.0 - (1.0 - f) ** alpha


def win_probs(stake: np.ndarray, d_est: float, f: float) -> np.ndarray:
    """Per-node win probability ``phi_f(w_i / D_est)``."""
    return phi(f, stake / d_est)


def _winners_from_counts(
    counts: np.ndarray, offset: int, span: int, rng: np.random.Generator
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """For each winning node, sample ``counts[i]`` distinct slots in ``[offset, offset+span)``."""
    nz = np.nonzero(counts)[0]
    slot_parts: list[np.ndarray] = []
    node_parts: list[np.ndarray] = []
    for i in nz:
        c = int(counts[i])
        slots_i = rng.choice(span, size=c, replace=False).astype(np.int64) + offset
        slot_parts.append(slots_i)
        node_parts.append(np.full(c, i, np.int64))
    return slot_parts, node_parts


def _finalize(
    slot_parts: list[np.ndarray], node_parts: list[np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    if not slot_parts:
        return np.empty(0, np.int64), np.empty(0, np.int64)
    winner_slots = np.concatenate(slot_parts)
    winner_nodes = np.concatenate(node_parts)
    order = np.argsort(winner_slots, kind="stable")
    return winner_slots[order], winner_nodes[order]


def sample_wins(
    p_win: np.ndarray, n_slots: int, rng: np.random.Generator, chunk: int = 8192
) -> tuple[np.ndarray, np.ndarray]:
    """Sample lottery wins over ``n_slots`` slots (sparse; ``chunk`` kept for API compat)."""
    counts = rng.binomial(n_slots, p_win)
    slot_parts, node_parts = _winners_from_counts(counts, 0, n_slots, rng)
    return _finalize(slot_parts, node_parts)


def sample_wins_chunked(
    p_win: np.ndarray,
    n_slots: int,
    seedseq: np.random.SeedSequence,
    n_chunks: int,
    n_jobs: int = -1,
) -> tuple[np.ndarray, np.ndarray]:
    """Parallel sparse lottery: partition slots into ``n_chunks`` independent ranges.

    Correct because ``Binomial(n_slots, p) = sum_c Binomial(L_c, p)`` and per-chunk distinct
    subsets are independent. Deterministic given ``(seedseq, n_chunks)`` — but the exact
    winner identities differ from the serial sampler and *change with* ``n_chunks``, so
    ``n_chunks`` must be a pinned, recorded config parameter, never derived from core count.

    Note: after the sparse rewrite the lottery is a small fraction of an epoch, so this has
    little ROI versus across-config parallelism; it exists for the rare isolated config with
    an enormous ``n_slots`` and no across-config work to fill cores.
    """
    if n_chunks <= 1:
        return sample_wins(p_win, n_slots, np.random.default_rng(seedseq))
    bounds = np.linspace(0, n_slots, n_chunks + 1).astype(np.int64)
    children = seedseq.spawn(n_chunks)

    def one_chunk(c: int) -> tuple[list[np.ndarray], list[np.ndarray]]:
        lo, hi = int(bounds[c]), int(bounds[c + 1])
        span = hi - lo
        rng = np.random.default_rng(children[c])
        counts = rng.binomial(span, p_win)
        return _winners_from_counts(counts, lo, span, rng)

    results = Parallel(n_jobs=n_jobs, prefer="threads")(
        delayed(one_chunk)(c) for c in range(n_chunks)
    )
    slot_parts: list[np.ndarray] = []
    node_parts: list[np.ndarray] = []
    for sp, npar in results:
        slot_parts.extend(sp)
        node_parts.extend(npar)
    return _finalize(slot_parts, node_parts)


def group_by_slot(
    winner_slots: np.ndarray, winner_nodes: np.ndarray
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Group sorted winner coordinates into ``(active_slots, winners_per_active_slot)``."""
    if winner_slots.size == 0:
        return np.empty(0, np.int64), []
    active_slots, starts = np.unique(winner_slots, return_index=True)
    groups = np.split(winner_nodes, starts[1:])
    return active_slots, groups
