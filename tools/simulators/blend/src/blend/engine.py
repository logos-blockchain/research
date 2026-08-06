"""Build-once engine: one topology -> propagation rows (per blend setting) + adversary rows.

The graph build and propagation depend only on ``(n_nodes, degree, graph_seed)``; the adversary
metrics are cheap and exact. So a topology is built once and measured across the whole
propagation and adversary sub-grids.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from .adversary import (
    adversary_metrics,
    attribution_metrics,
    deanon_metrics,
    mean_upstream_hops,
    neighbourhood_confidence,
    place_adversary,
)
from .config import WORSTCASE_MODES, SimConfig
from .graph import build_graph
from .metrics import adversary_row, deanon_row, propagation_row, traffic_row
from .propagation import assign_responsive, propagation_metrics
from .quota import assign_stake, quota_summary
from .rng import (
    placement_seedseq,
    responsive_seedseq,
    round_seedseq,
    stake_seedseq,
    traffic_seedseq,
)
from .traffic import simulate_window, timing_linkability, traffic_metrics


def run_graph_cell(base: SimConfig, prop_grid: list[tuple[int, int]],
                   unresponsive_fracs: list[float], redundancies: list[int],
                   adv_grid: list[tuple[float, str]],
                   churn_modes: list[str] | None = None,
                   cover_rates: list[float] | None = None,
                   release_designs: list[tuple[int, str]] | None = None,
                   ) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Build ``base``'s topology once; return (propagation, adversary, deanon, traffic rows).

    ``base`` carries the topology (n_nodes, degree, graph_seed) and all shared knobs;
    ``prop_grid`` = [(blend_hops, max_blend_delay)], ``unresponsive_fracs`` = the relay-dropout
    axis, ``redundancies`` = the messaging-redundancy axis (R independent cascades per emission),
    ``adv_grid`` = [(f_adv, mode)]. Deanonymization crosses each adversary placement with the
    propagation grid's blend-path lengths and redundancies, so it is emitted alongside the
    adversary rows. ``cover_rates`` (empty by default) turns on the cover-traffic study: each rate
    plays a timeline through the same graph and pairs it with the epoch emission budget, which is
    graph-free and therefore computed separately.
    """
    graph = build_graph(base)
    upstream = mean_upstream_hops(graph, np.random.default_rng(base.root_seed))
    blend_hops_set = sorted({bh for bh, _ in prop_grid})
    modes = churn_modes or [base.churn_mode]

    prop_rows: list[dict] = []
    for cm in modes:
        for uf in unresponsive_fracs:
            responsive = assign_responsive(
                base.n_nodes, uf, np.random.default_rng(responsive_seedseq(base, uf, cm)),
                cm, base.n_regions)
            for blend_hops, max_blend_delay in prop_grid:
                for R in redundancies:
                    rng = np.random.default_rng(
                        round_seedseq(base, blend_hops, max_blend_delay, uf, R))
                    prop = propagation_metrics(
                        graph, blend_hops, max_blend_delay, uf, R, responsive, base, rng)
                    prop_rows.append(
                        propagation_row(base, blend_hops, max_blend_delay, uf, R, prop, cm))

    adv_rows: list[dict] = []
    deanon_rows: list[dict] = []
    for f_adv, mode in adv_grid:
        if mode in WORSTCASE_MODES and base.n_nodes > base.worstcase_max_n:
            continue  # worst-case is an envelope characterized at N <= worstcase_max_n
        n_placements = base.n_placements if mode == "random" else 1
        for rep in range(n_placements):
            rng = np.random.default_rng(placement_seedseq(base, f_adv, mode, rep))
            adv_mask = place_adversary(graph, f_adv, mode, rng, base.worstcase_max_n)
            adv = adversary_metrics(graph, adv_mask)
            att = attribution_metrics(graph, adv_mask)
            # upper end of the attribution bracket: the adversary also sees the message upstream
            att = dict(att, upstream_hops=upstream,
                       neighbourhood_conf=neighbourhood_confidence(f_adv, upstream))
            adv_rows.append(adversary_row(base, f_adv, mode, rep, adv))
            for bh in blend_hops_set:
                for R in redundancies:
                    dz = deanon_metrics(graph.n, adv["n_adv"], adv["observed_frac"], bh, R)
                    deanon_rows.append(
                        deanon_row(base, bh, f_adv, mode, rep, R, adv, dz, att))

    traffic_rows: list[dict] = []
    for rate in (cover_rates or []):
        cfg = dataclasses.replace(base, cover_rate_mult=rate)
        f = 1.0 / base.block_interval_slots
        srng = np.random.default_rng(stake_seedseq(base, rate))
        stake = assign_stake(base.n_nodes, base.stake_dist, srng, base.stake_zipf_a)
        quota = quota_summary(stake, f, base.n_nodes, base.slots_per_epoch, srng,
                              base.stake_inference_ratio, rate)
        for blend_hops, max_blend_delay in prop_grid:
            for lo, mode in (release_designs or [(base.min_blend_delay, base.release_mode)]):
                trng = np.random.default_rng(
                    traffic_seedseq(base, blend_hops, max_blend_delay, rate))
                win = simulate_window(graph, cfg, trng, base.traffic_window_slots,
                                      max_blend_delay, blend_hops, mode, lo)
                tm = traffic_metrics(win, cfg, max_blend_delay)
                tl = timing_linkability(win, cfg, max_blend_delay, lo, mode)
                traffic_rows.append(
                    traffic_row(base, blend_hops, max_blend_delay, rate, tm, quota, lo, mode, tl))

    return prop_rows, adv_rows, deanon_rows, traffic_rows


def run_trajectory(config: SimConfig) -> dict:
    """Single-cell convenience for tests/verify: build the graph, run one propagation cell
    (``config.blend_hops``/``config.max_blend_delay``) and one adversary cell."""
    graph = build_graph(config)
    uf = config.unresponsive_frac
    responsive = assign_responsive(
        config.n_nodes, uf,
        np.random.default_rng(responsive_seedseq(config, uf, config.churn_mode)),
        config.churn_mode, config.n_regions)
    R = config.redundancy
    prng = np.random.default_rng(
        round_seedseq(config, config.blend_hops, config.max_blend_delay, uf, R))
    prop = propagation_metrics(
        graph, config.blend_hops, config.max_blend_delay, uf, R, responsive, config, prng)
    arng = np.random.default_rng(
        placement_seedseq(config, config.f_adv, config.adversary_mode, config.replicate))
    adv_mask = place_adversary(
        graph, config.f_adv, config.adversary_mode, arng, config.worstcase_max_n)
    adv = adversary_metrics(graph, adv_mask)
    deanon = deanon_metrics(graph.n, adv["n_adv"], adv["observed_frac"], config.blend_hops, R)
    return {"graph": graph, "propagation": prop, "adversary": adv, "adv_mask": adv_mask,
            "deanon": deanon}
