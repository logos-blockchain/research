"""Per-epoch per-node divergence rows and equilibrium summaries."""

from __future__ import annotations

from typing import Any

import numpy as np

from .config import SimConfig
from .epoch import EpochResult

# Config fields recorded on every row for grouping/plotting.
_CONFIG_FIELDS = (
    "n_nodes", "stake_dist", "pareto_shape", "latency", "topology", "degree",
    "link_latency_mean", "link_latency_dist", "blend_hops", "blend_delay_max",
    "init_dest", "init_spread", "uncle_window", "max_uncles", "uncle_strategy",
    "f", "beta", "k", "genesis_d_factor", "epochs", "fixed_point", "legacy_block_count",
    "replicate",
    "adversary_frac", "adversary_strategy", "adversary_period", "adversary_withhold_epochs",
)


def divergence_row(
    config: SimConfig, epoch: int, d_in: np.ndarray, er: EpochResult, d_true: float
) -> dict[str, Any]:
    """One row per (config, epoch): per-node D_est spread + chain agreement."""
    ratio = np.asarray(er.d_next, dtype=float) / d_true      # (N,)
    row: dict[str, Any] = {field: getattr(config, field) for field in _CONFIG_FIELDS}
    row.update(
        epoch=epoch,
        mean_ratio=float(ratio.mean()),
        median_ratio=float(np.median(ratio)),
        std_ratio=float(ratio.std()),
        min_ratio=float(ratio.min()),
        max_ratio=float(ratio.max()),
        range_ratio=float(ratio.max() - ratio.min()),      # the headline divergence measure
        iqr_ratio=float(np.percentile(ratio, 75) - np.percentile(ratio, 25)),
        p10_ratio=float(np.percentile(ratio, 10)),
        p90_ratio=float(np.percentile(ratio, 90)),
        mean_ratio_in=float((np.asarray(d_in, dtype=float) / d_true).mean()),
        range_ratio_in=float(np.ptp(np.asarray(d_in, dtype=float) / d_true)),
        mean_m=float(np.mean(er.m)),
        mean_q=float(np.nanmean(er.q)),
        mean_q_eff=float(np.nanmean(er.q_eff)),
        std_q=float(np.nanstd(er.q)),
        agreement_window=er.agreement_window,
        agreement_tip=er.agreement_tip,
        mean_orphan_rate=er.mean_orphan_rate,
        n_active_window=er.n_active_window,
        n_blocks=er.n_blocks,
        adv_blocks=er.adv_blocks,
        honest_blocks=er.honest_blocks,
        adv_block_share=(
            er.adv_blocks / (er.adv_blocks + er.honest_blocks)
            if (er.adv_blocks + er.honest_blocks) > 0 else 0.0
        ),
        fork_rate=er.fork_rate,
        max_reorg_depth=er.max_reorg_depth,
        mean_reorg_depth=er.mean_reorg_depth,
        p_ref=er.p_ref,
    )
    return row


def equilibrium_stats(values: np.ndarray, burn_in: int) -> dict[str, float]:
    """Mean/variance of ``values`` after ``burn_in`` epochs."""
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {"mean": float("nan"), "var": float("nan"), "std": float("nan")}
    tail = values[burn_in:]
    if tail.size == 0:
        tail = values[-1:]
    return {"mean": float(np.mean(tail)), "var": float(np.var(tail)), "std": float(np.std(tail))}


def epochs_to_within(values: np.ndarray, target: float, eps: float) -> int:
    """First epoch after which ``|values - target| <= eps`` holds for the rest."""
    within = np.abs(np.asarray(values, dtype=float) - target) <= eps
    if within.size == 0:
        return 0
    false_idx = np.flatnonzero(~within)
    return int(false_idx[-1] + 1) if false_idx.size else 0
