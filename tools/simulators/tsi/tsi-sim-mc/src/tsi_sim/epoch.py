"""Single-epoch simulation: lottery -> block tree -> uncles -> density counting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import concurrency, lottery, tsi
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
    max_concurrent: int    # most block proposals in any latency-sized (max(L,1)) bucket
    mean_concurrent: float # mean proposals per latency-sized bucket


def simulate_epoch(
    config: SimConfig, stake: np.ndarray, d_est: float, epoch_ss: np.random.SeedSequence
) -> EpochResult:
    f = config.f
    T = config.period_T
    # independent sub-streams: one for the lottery, one for the tree/uncle auxiliary draws
    lottery_ss, aux_ss = epoch_ss.spawn(2)
    aux_rng = np.random.default_rng(aux_ss)

    p_win = lottery.win_probs(stake, d_est, f)
    if config.lottery_chunks > 1:
        winner_slots, winner_nodes = lottery.sample_wins_chunked(
            p_win, config.epoch_len, lottery_ss, config.lottery_chunks
        )
    else:
        winner_slots, winner_nodes = lottery.sample_wins(
            p_win, config.epoch_len, np.random.default_rng(lottery_ss)
        )
    active_slots, groups = lottery.group_by_slot(winner_slots, winner_nodes)

    latency = make_latency(config)
    tree = build_tree(active_slots, groups, latency, aux_rng)
    canonical = tree.canonical_chain()
    from .uncles import annotate_uncles

    annotate_uncles(tree, canonical, config, aux_rng)

    m = tsi.density_m(tree, canonical, T)
    ref = tsi.referenced_uncle_ids(tree, canonical)
    ss = tsi.slot_stats(tree, canonical, ref, active_slots, T)

    total_winners_window = int((winner_slots < T).sum())
    n_real = tree.n_blocks - 1
    # Concurrent proposals: bucket the whole epoch into latency-sized windows and count
    # block proposals (every winner is a proposal) per bucket. The max bucket is the peak
    # number of mutually-concurrent proposals (they cannot see each other within L slots).
    bucket = max(config.latency, 1)
    counts = concurrency.window_counts(winner_slots, config.epoch_len, bucket)
    max_concurrent = int(counts.max()) if counts.size else 0
    mean_concurrent = float(counts.mean()) if counts.size else 0.0
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
        max_concurrent=max_concurrent,
        mean_concurrent=mean_concurrent,
    )
