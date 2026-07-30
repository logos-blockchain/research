"""Per-epoch metric rows and equilibrium summaries."""

from __future__ import annotations

from typing import Any

import numpy as np

from .config import SimConfig
from .epoch import EpochResult

# Config fields recorded on every row for grouping/plotting.
_CONFIG_FIELDS = (
    "n_nodes", "stake_dist", "pareto_shape", "latency", "uncle_window",
    "max_uncles", "uncle_strategy", "uncle_random_p", "f", "beta", "k",
    "genesis_d_factor", "epochs", "replicate",
)


def metric_row(
    config: SimConfig,
    epoch: int,
    d_in: float,
    d_out: float,
    d_true: float,
    er: EpochResult,
) -> dict[str, Any]:
    row: dict[str, Any] = {field: getattr(config, field) for field in _CONFIG_FIELDS}
    row.update(
        epoch=epoch,
        d_in=d_in,
        d_out=d_out,
        d_true=d_true,
        ratio=d_out / d_true,
        m=er.m,
        measured_density=er.m / config.period_T,
        q=er.q,
        q_eff=er.q_eff,
        n_active=er.n_active,
        n_honest=er.n_honest,
        n_recovered=er.n_recovered,
        total_winners_window=er.total_winners_window,
        n_blocks=er.n_blocks,
        n_canonical=er.n_canonical,
        n_orphans=er.n_orphans,
        orphan_rate=er.n_orphans / er.n_blocks if er.n_blocks else float("nan"),
    )
    return row


def equilibrium_stats(ratios: np.ndarray, burn_in: int) -> dict[str, float]:
    """Mean/variance of the stake ratio after ``burn_in`` epochs."""
    tail = ratios[burn_in:]
    if tail.size == 0:
        tail = ratios[-1:]
    return {
        "mean_ratio": float(np.mean(tail)),
        "var_ratio": float(np.var(tail)),
        "std_ratio": float(np.std(tail)),
    }


def epochs_to_within(ratios: np.ndarray, target: float, eps: float) -> int:
    """First epoch index after which ``|ratio - target| <= eps`` holds for the rest."""
    within = np.abs(ratios - target) <= eps
    n = within.size
    for i in range(n):
        if within[i:].all():
            return i
    return n  # never converged within the run
