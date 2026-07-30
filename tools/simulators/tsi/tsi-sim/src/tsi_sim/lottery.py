"""Stake-weighted slot lottery.

Per node ``i`` and slot, an independent Bernoulli win with probability
``phi_f(alpha_i) = 1 - (1 - f)^alpha_i`` where ``alpha_i = w_i / D_est`` is the node's
relative stake against its inferred total active stake. Multiple winners in a slot are
possible (a guaranteed fork). ``phi`` is taken verbatim from the reference notebook.

Winners are returned as *sparse coordinates* — flat ``(winner_slots, winner_nodes)``
arrays sorted by slot — so downstream code iterates only over the ``O(f * n_slots)``
winners, never over every slot.
"""

from __future__ import annotations

import numpy as np


def phi(f: float, alpha: np.ndarray | float) -> np.ndarray | float:
    """Leader-lottery win probability ``1 - (1 - f)^alpha``."""
    return 1.0 - (1.0 - f) ** alpha


def win_probs(stake: np.ndarray, d_est: float, f: float) -> np.ndarray:
    """Per-node win probability ``phi_f(w_i / D_est)``."""
    return phi(f, stake / d_est)


def sample_wins(
    p_win: np.ndarray, n_slots: int, rng: np.random.Generator, chunk: int = 8192
) -> tuple[np.ndarray, np.ndarray]:
    """Sample lottery wins over ``n_slots`` slots.

    Returns ``(winner_slots, winner_nodes)``: parallel int arrays with one entry per
    (slot, winning node), sorted by slot ascending. Draws are chunked over slots to bound
    peak memory to ``n_nodes * chunk`` bools.
    """
    n = p_win.shape[0]
    p_col = p_win[:, None]
    slot_parts: list[np.ndarray] = []
    node_parts: list[np.ndarray] = []
    for start in range(0, n_slots, chunk):
        width = min(chunk, n_slots - start)
        hits = rng.random((n, width)) < p_col
        node_idx, slot_idx = np.nonzero(hits)
        slot_parts.append(slot_idx.astype(np.int64) + start)
        node_parts.append(node_idx.astype(np.int64))
    if not slot_parts:  # pragma: no cover - n_slots == 0
        return np.empty(0, np.int64), np.empty(0, np.int64)
    winner_slots = np.concatenate(slot_parts)
    winner_nodes = np.concatenate(node_parts)
    order = np.argsort(winner_slots, kind="stable")
    return winner_slots[order], winner_nodes[order]


def group_by_slot(
    winner_slots: np.ndarray, winner_nodes: np.ndarray
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Group sorted winner coordinates into ``(active_slots, winners_per_active_slot)``."""
    if winner_slots.size == 0:
        return np.empty(0, np.int64), []
    active_slots, starts = np.unique(winner_slots, return_index=True)
    groups = np.split(winner_nodes, starts[1:])
    return active_slots, groups
