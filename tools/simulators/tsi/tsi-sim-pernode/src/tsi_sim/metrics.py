"""Per-epoch per-node divergence rows."""

from __future__ import annotations

from typing import Any

import numpy as np

from .config import SimConfig
from .epoch import EpochResult

# Config fields recorded on every row for grouping/plotting.
_CONFIG_FIELDS = (
    "n_nodes", "stake_dist", "pareto_shape", "latency", "topology", "degree",
    "link_latency_mean", "link_latency_dist", "blend_hops", "blend_delay_max",
    "init_dest", "init_spread", "uncle_model", "window_absorption",
    "uncle_window", "max_uncles", "uncle_strategy", "uncle_window_anchor",
    # Recorded so downstream analysis can TELL whether a countable/--old pair actually shared
    # its RNG streams. The paired test is only valid on paired runs, and without this column
    # the analysis silently falls back to the much weaker unpaired test.
    "paired_streams",
    "f", "beta", "k", "genesis_d_factor", "epochs", "fixed_point", "legacy_block_count",
    "replicate",
    "f_precision",
    "adversary_frac", "adversary_strategy", "adversary_selection", "adversary_period",
    "adversary_withhold_epochs",
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
        p_ref_honest=er.p_ref_honest,
        deep_orphan_share=er.deep_orphan_share,
        deep_ref_share=er.deep_ref_share,
    )
    return row
