"""Concurrent block-proposal analysis.

Every lottery win is a block *proposal*. Two proposals produced within ``L`` slots of each
other cannot see one another (a block becomes visible only after the network latency ``L``),
so they are mutually concurrent — competing forks. Bucketing the timeline into
non-overlapping windows of ``L`` slots and counting proposals per bucket gives a direct
view of how many proposals are concurrent, and the busiest bucket is the peak number of
concurrent proposals. This is the quantity that bounds how many uncles can appear, so it
informs the ``MAX_UNCLES`` choice.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .config import SimConfig
from .lottery import sample_wins, win_probs
from .rng import seedseq_for
from .stake import make_stake


def window_counts(winner_slots: np.ndarray, epoch_len: int, bucket: int) -> np.ndarray:
    """Proposals per non-overlapping ``bucket``-slot window over ``[0, epoch_len)``."""
    if epoch_len <= 0:
        return np.empty(0, np.int64)
    bucket = max(int(bucket), 1)
    n_windows = (epoch_len + bucket - 1) // bucket
    if winner_slots.size == 0:
        return np.zeros(n_windows, np.int64)
    return np.bincount(winner_slots // bucket, minlength=n_windows)


def proposal_slots(config: SimConfig, replicate: int = 0) -> np.ndarray:
    """Simulate one epoch of block proposals at the *true* lottery difficulty (D=D_true).

    Returns the sorted slots at which proposals (all lottery winners, including forks) occur.
    Independent of the TSI trajectory — the proposal process depends only on stake, ``f``,
    and ``epoch_len`` — so this is a cheap, self-contained re-simulation for the plots.
    """
    cfg = replace(config, replicate=replicate)
    root = seedseq_for(cfg)
    children = root.spawn(2)
    stake = make_stake(cfg, np.random.default_rng(children[0]))
    p_win = win_probs(stake, float(stake.sum()), cfg.f)
    winner_slots, _ = sample_wins(p_win, cfg.epoch_len, np.random.default_rng(children[1]))
    return winner_slots


def concurrency_stats(config: SimConfig, replicate: int = 0) -> dict:
    """Per-bucket proposal-count stats for one simulated epoch (bucket = ``max(L, 1)``)."""
    ws = proposal_slots(config, replicate)
    bucket = max(config.latency, 1)
    counts = window_counts(ws, config.epoch_len, bucket)
    return {
        "bucket": bucket,
        "counts": counts,
        "max": int(counts.max()) if counts.size else 0,
        "mean": float(counts.mean()) if counts.size else 0.0,
        "p99": float(np.percentile(counts, 99)) if counts.size else 0.0,
    }
