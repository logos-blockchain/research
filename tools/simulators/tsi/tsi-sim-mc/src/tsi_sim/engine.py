"""Multi-epoch trajectory driver for a single config."""

from __future__ import annotations

from typing import Any

import numpy as np

from . import tsi
from .config import SimConfig
from .epoch import simulate_epoch
from .metrics import metric_row
from .rng import seedseq_for
from .stake import make_stake


def run_trajectory(config: SimConfig) -> list[dict[str, Any]]:
    """Run ``config.epochs`` epochs of TSI, returning one metric row per epoch.

    Stake is drawn once (it is fixed; only ``D_est`` evolves). ``D_est`` starts at the
    hardcoded genesis value ``genesis_d_factor * D_true`` and is updated each epoch from
    the measured density. The RNG is a spawn hierarchy off the config's root SeedSequence:
    child 0 draws the stake, child ``e+1`` drives epoch ``e`` — so every draw is a
    deterministic, order-independent function of the config identity.
    """
    root = seedseq_for(config)
    children = root.spawn(config.epochs + 1)
    stake = make_stake(config, np.random.default_rng(children[0]))
    d_true = float(stake.sum())
    d_est = config.genesis_d_factor * d_true
    T = config.period_T

    rows: list[dict[str, Any]] = []
    for epoch in range(config.epochs):
        er = simulate_epoch(config, stake, d_est, children[epoch + 1])
        d_next = tsi.update_D(d_est, er.m, T, config.f, config.beta, config.fixed_point)
        rows.append(metric_row(config, epoch, d_est, d_next, d_true, er))
        d_est = d_next
    return rows
