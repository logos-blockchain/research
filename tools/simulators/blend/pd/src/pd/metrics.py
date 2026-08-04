"""Flat parquet-row builders for the two result tables."""

from __future__ import annotations

from .config import SimConfig


def propagation_row(config: SimConfig, blend_hops: int, max_blend_delay: int,
                    unresponsive_frac: float, redundancy: int, prop: dict) -> dict:
    return {
        "n_nodes": config.n_nodes,
        "degree": config.degree,
        "blend_hops": blend_hops,
        "max_blend_delay": max_blend_delay,
        "unresponsive_frac": unresponsive_frac,
        "redundancy": redundancy,
        "graph_seed": config.graph_seed,
        "n_rounds": config.n_rounds,
        "transport_jitter_mean_ms": config.transport_jitter_mean_ms,
        "processing_lags_ms": str(tuple(config.processing_lags_ms)),
        "processing_lag_probs": str(tuple(config.processing_lag_probs)),
        **prop,
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
               placement_rep: int, redundancy: int, adv: dict, deanon: dict) -> dict:
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
    }
