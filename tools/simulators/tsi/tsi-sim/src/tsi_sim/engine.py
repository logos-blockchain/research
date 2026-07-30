"""Multi-epoch trajectory driver for a single config."""

from __future__ import annotations

from typing import Any

from . import tsi
from .config import SimConfig
from .epoch import simulate_epoch
from .metrics import metric_row
from .rng import rng_for
from .stake import make_stake


def run_trajectory(config: SimConfig) -> list[dict[str, Any]]:
    """Run ``config.epochs`` epochs of TSI, returning one metric row per epoch.

    Stake is drawn once (it is fixed; only ``D_est`` evolves). ``D_est`` starts at the
    hardcoded genesis value ``genesis_d_factor * D_true`` and is updated each epoch from
    the measured density.
    """
    rng = rng_for(config)
    stake = make_stake(config, rng)
    d_true = float(stake.sum())
    d_est = config.genesis_d_factor * d_true
    T = config.period_T

    rows: list[dict[str, Any]] = []
    for epoch in range(config.epochs):
        er = simulate_epoch(config, stake, d_est, rng)
        d_next = tsi.update_D(d_est, er.m, T, config.f, config.beta)
        rows.append(metric_row(config, epoch, d_est, d_next, d_true, er))
        d_est = d_next
    return rows
