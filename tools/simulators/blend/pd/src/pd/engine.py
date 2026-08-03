"""Build-once engine: one topology -> propagation rows (per blend setting) + adversary rows.

The graph build and propagation depend only on ``(n_nodes, degree, graph_seed)``; the adversary
metrics are cheap and exact. So a topology is built once and measured across the whole
propagation and adversary sub-grids.
"""

from __future__ import annotations

import numpy as np

from .adversary import adversary_metrics, deanon_metrics, place_adversary
from .config import WORSTCASE_MODES, SimConfig
from .graph import build_graph
from .metrics import adversary_row, deanon_row, propagation_row
from .propagation import assign_responsive, propagation_metrics
from .rng import placement_seedseq, responsive_seedseq, round_seedseq


def run_graph_cell(base: SimConfig, prop_grid: list[tuple[int, int]],
                   unresponsive_fracs: list[float],
                   adv_grid: list[tuple[float, str]],
                   ) -> tuple[list[dict], list[dict], list[dict]]:
    """Build ``base``'s topology once; return (propagation, adversary, deanonymization rows).

    ``base`` carries the topology (n_nodes, degree, graph_seed) and all shared knobs;
    ``prop_grid`` = [(blend_hops, max_blend_delay)], ``unresponsive_fracs`` = the relay-dropout
    axis (propagation-only), ``adv_grid`` = [(f_adv, mode)]. Deanonymization crosses each adversary
    placement with the propagation grid's blend-path lengths, so it is emitted alongside the
    adversary rows.
    """
    graph = build_graph(base)
    blend_hops_set = sorted({bh for bh, _ in prop_grid})

    prop_rows: list[dict] = []
    for uf in unresponsive_fracs:
        responsive = assign_responsive(
            base.n_nodes, uf, np.random.default_rng(responsive_seedseq(base, uf)))
        for blend_hops, max_blend_delay in prop_grid:
            rng = np.random.default_rng(round_seedseq(base, blend_hops, max_blend_delay, uf))
            prop = propagation_metrics(
                graph, blend_hops, max_blend_delay, uf, responsive, base, rng)
            prop_rows.append(propagation_row(base, blend_hops, max_blend_delay, uf, prop))

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
            adv_rows.append(adversary_row(base, f_adv, mode, rep, adv))
            for bh in blend_hops_set:
                dz = deanon_metrics(graph.n, adv["n_adv"], adv["observed_frac"], bh)
                deanon_rows.append(deanon_row(base, bh, f_adv, mode, rep, adv, dz))

    return prop_rows, adv_rows, deanon_rows


def run_trajectory(config: SimConfig) -> dict:
    """Single-cell convenience for tests/verify: build the graph, run one propagation cell
    (``config.blend_hops``/``config.max_blend_delay``) and one adversary cell."""
    graph = build_graph(config)
    uf = config.unresponsive_frac
    responsive = assign_responsive(
        config.n_nodes, uf, np.random.default_rng(responsive_seedseq(config, uf)))
    prng = np.random.default_rng(
        round_seedseq(config, config.blend_hops, config.max_blend_delay, uf))
    prop = propagation_metrics(
        graph, config.blend_hops, config.max_blend_delay, uf, responsive, config, prng)
    arng = np.random.default_rng(
        placement_seedseq(config, config.f_adv, config.adversary_mode, config.replicate))
    adv_mask = place_adversary(
        graph, config.f_adv, config.adversary_mode, arng, config.worstcase_max_n)
    adv = adversary_metrics(graph, adv_mask)
    deanon = deanon_metrics(graph.n, adv["n_adv"], adv["observed_frac"], config.blend_hops)
    return {"graph": graph, "propagation": prop, "adversary": adv, "adv_mask": adv_mask,
            "deanon": deanon}
