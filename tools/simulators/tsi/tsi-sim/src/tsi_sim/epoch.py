"""Single-epoch simulation: lottery -> block tree -> uncles -> density counting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import lottery, tsi
from .blocktree import build_tree
from .config import SimConfig
from .latency import make_latency


@dataclass
class EpochResult:
    m: int                 # TSI block count in window
    q: float               # honest active-slot fraction (window)
    q_eff: float           # uncle-recovered active-slot fraction (window)
    n_active: int          # active slots in window
    n_honest: int          # honest slots in window
    n_recovered: int       # orphan slots recovered by uncles in window
    total_winners_window: int   # total lottery wins in window (incl. multi-winner)
    n_blocks: int          # real blocks produced this epoch
    n_canonical: int       # canonical chain length
    n_orphans: int         # orphaned blocks


def simulate_epoch(
    config: SimConfig, stake: np.ndarray, d_est: float, rng: np.random.Generator
) -> EpochResult:
    f = config.f
    T = config.period_T
    p_win = lottery.win_probs(stake, d_est, f)
    winner_slots, winner_nodes = lottery.sample_wins(p_win, config.epoch_len, rng)
    active_slots, groups = lottery.group_by_slot(winner_slots, winner_nodes)

    latency = make_latency(config)
    tree = build_tree(active_slots, groups, latency, rng)
    canonical = tree.canonical_chain()
    from .uncles import annotate_uncles

    annotate_uncles(tree, canonical, config, rng)

    m = tsi.density_m(tree, canonical, T)
    ref = tsi.referenced_uncle_ids(tree, canonical)
    ss = tsi.slot_stats(tree, canonical, ref, active_slots, T)

    total_winners_window = int((winner_slots < T).sum())
    n_real = tree.n_blocks - 1
    return EpochResult(
        m=m,
        q=ss.q,
        q_eff=ss.q_eff,
        n_active=ss.n_active,
        n_honest=ss.n_honest,
        n_recovered=ss.n_recovered,
        total_winners_window=total_winners_window,
        n_blocks=n_real,
        n_canonical=len(canonical),
        n_orphans=n_real - len(canonical),
    )
