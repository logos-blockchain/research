"""Flat parquet-row builders for the result tables."""

from __future__ import annotations

from .config import SimConfig


def propagation_row(config: SimConfig, blend_hops: int, max_blend_delay: int,
                    unresponsive_frac: float, redundancy: int, prop: dict,
                    churn_mode: str | None = None) -> dict:
    return {
        "n_nodes": config.n_nodes,
        "degree": config.degree,
        "blend_hops": blend_hops,
        "max_blend_delay": max_blend_delay,
        "unresponsive_frac": unresponsive_frac,
        "churn_mode": churn_mode or config.churn_mode,
        "n_regions": config.n_regions,
        "region_locality": config.region_locality,
        "redundancy": redundancy,
        "graph_seed": config.graph_seed,
        "n_rounds": config.n_rounds,
        "transport_jitter_mean_ms": config.transport_jitter_mean_ms,
        "processing_lags_ms": str(tuple(config.processing_lags_ms)),
        "processing_lag_probs": str(tuple(config.processing_lag_probs)),
        **prop,
    }


def traffic_row(config: SimConfig, blend_hops: int, max_blend_delay: int,
                cover_rate_mult: float, traffic: dict, quota: dict,
                min_blend_delay: int | None = None, release_mode: str | None = None,
                timing: dict | None = None) -> dict:
    """One cover-traffic cell: what the timeline measured, plus the epoch emission budget.

    ``traffic`` comes from the windowed simulation (blending, mixing, counts) and ``quota`` from
    the epoch-scale emission budget, which needs no graph and so is computed separately.
    """
    return {
        "n_nodes": config.n_nodes,
        "degree": config.degree,
        "blend_hops": blend_hops,
        "max_blend_delay": max_blend_delay,
        "min_blend_delay": config.min_blend_delay if min_blend_delay is None else min_blend_delay,
        "release_mode": release_mode or config.release_mode,
        "cover_rate_mult": cover_rate_mult,
        "block_interval_slots": config.block_interval_slots,
        "slots_per_epoch": config.slots_per_epoch,
        "stake_dist": config.stake_dist,
        "stake_inference_ratio": config.stake_inference_ratio,
        "graph_seed": config.graph_seed,
        "traffic_window_slots": config.traffic_window_slots,
        **traffic,
        **quota,
        **(timing or {}),
    }


def adversary_row(config: SimConfig, f_adv: float, mode: str, placement_rep: int,
                  adv: dict) -> dict:
    return {
        "n_nodes": config.n_nodes,
        "degree": config.degree,
        "f_adv": f_adv,
        "adversary_mode": mode,
        "graph_seed": config.graph_seed,
        "placement_rep": placement_rep,
        **adv,
    }


def deanon_row(config: SimConfig, blend_hops: int, f_adv: float, mode: str,
               placement_rep: int, redundancy: int, adv: dict, deanon: dict,
               att: dict | None = None) -> dict:
    """One row of the deanonymization table: a (placement x blend-path-length x redundancy) cell.

    ``blend_hops`` and ``redundancy`` come from the propagation grid, the rest from the adversary
    placement; they are crossed here because deanonymization is where propagation paths meet the
    adversary set.
    """
    return {
        "n_nodes": config.n_nodes,
        "degree": config.degree,
        "blend_hops": blend_hops,
        "redundancy": redundancy,
        "f_adv": f_adv,
        "adversary_mode": mode,
        "graph_seed": config.graph_seed,
        "placement_rep": placement_rep,
        "n_adv": adv["n_adv"],
        "n_honest": adv["n_honest"],
        "observed_frac": adv["observed_frac"],
        **deanon,
        **(att or {}),
        # Confidence-weighted attribution: the whole-path capture rate times the share of nodes the
        # adversary could actually name as originator at that confidence, rather than the binary
        # "has an adversarial peer" that full_deanon_rate uses.
        **({f"confident_deanon_{k.rsplit('_', 1)[1]}": deanon["deanon_rate"] * v
            for k, v in att.items() if k.startswith("attributable_frac_")} if att else {}),
    }
