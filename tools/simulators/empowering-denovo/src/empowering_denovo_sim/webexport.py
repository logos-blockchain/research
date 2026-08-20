"""Export the de-novo calculator's inputs and its golden cross-check.

Same contract as `simulations/EmPoWering`'s panel: the page re-implements the closed forms in
JavaScript, which is a second implementation, so `params.json` is generated from the same
config the Python reads and `golden.json` carries a grid of triples with the outputs Python
computes. The page recomputes every row on load and wears the result as a badge;
`selfcheck.mjs` runs the same comparison under node so `make web` fails on drift instead of
leaving it to whoever opens the page.

Only closed forms are exported -- everything the calculator shows is derivable without the
engine, which is what makes a faithful browser twin possible at all.
"""
from __future__ import annotations

import json
from pathlib import Path

from .params import (EFFICIENCY_PERSISTENT, EFFICIENCY_RETIRING_FAST,
                     EFFICIENCY_RETIRING_SLOW, Triple)

# (pool_fraction, expected_nodes, expected_years, txs_per_block, spike_k)
# Spread over the corners: both band edges, both kinds of unsatisfiable, the sparse
# post-phase, a long horizon, and the reference triple with two spike sizes.
GRID = [
    (0.005, 25_000, 4.0, 600, 10),
    (0.005, 25_000, 4.0, 600, 100),
    (0.005, 10_000, 4.0, 600, 10),
    (0.005, 5_000, 4.0, 600, 10),      # implied 10% -- below the band
    (0.005, 40_000, 4.0, 600, 10),     # implied 80% -- above the band
    (0.010, 50_000, 4.0, 600, 10),
    (0.002, 20_000, 2.0, 300, 10),     # implied 100% -- far above
    (0.005, 25_000, 4.0, 20, 10),      # sparse: capacity floors at one claim per block
    (0.005, 25_000, 8.0, 600, 10),
    (0.020, 60_000, 6.0, 1024, 50),
]


def outputs(t: Triple, txs: int, spike_k: int) -> dict:
    d = t.derived()
    cfg = d.cfg
    sub0 = d.opening_sub_pool()
    reward0 = d.opening_reward()
    diverted_per_block = txs * cfg.avg_tx_fee * cfg.pow_share_num // cfg.pow_share_den
    budget_post = diverted_per_block * cfg.blocks_per_epoch
    capacity = budget_post // d.anchor
    return {
        "bootstrap_epochs": d.bootstrap_epochs,
        "endowment_lepta": d.endowment_genesis,
        "implied_efficiency": d.implied_efficiency,
        "satisfiable": d.satisfiable,
        "satisfiable_if_retiring": d.satisfiable_if_retiring,
        "sub_pool_lepta": sub0,
        "reward0_lepta": reward0,
        "claims_to_bond": -(-cfg.min_stake // (reward0 - cfg.claim_fee)),
        "anchor_lepta": d.anchor,
        "fee_drag_at_anchor": cfg.claim_fee / d.anchor,
        "capacity_post": capacity,
        "target_per_block": max(1, capacity // cfg.blocks_per_epoch),
        "spike_saturation_block": cfg.blocks_per_epoch // spike_k,
        "spike_borrow_multiple": spike_k,      # what the epoch spends, in budgets
        "whale_epoch_ceiling_lepta": cfg.blocks_per_epoch * cfg.max_block_txs * reward0,
    }


def profitability_inputs() -> dict:
    """Everything the profitability page needs that is not a closed form it can compute."""
    from empowering_sim import market

    from . import power, priceviz
    ref = Triple().derived()
    cfg = ref.cfg
    classes = {k.key: k for k in market.from_powcost("poseidon2_reward", 0.20, "total")}
    devices = []
    for key, label, rate in (
            ("pi5-core", "Raspberry Pi 5, one core", power.minimal(cfg).candidates_per_second),
            ("pi5-board", "Raspberry Pi 5, whole board", power.board(cfg).candidates_per_second),
            ("best-measured", "best measured class, all cores",
             power.worst(cfg).candidates_per_second)):
        # watt-hours per candidate, back-derived from the estimator at its reference price
        cost = classes["rpi5"].cost_per_candidate_usd
        if key == "best-measured":
            cost = classes["apple"].cost_per_candidate_usd
        devices.append({"key": key, "label": label, "candidates_per_second": rate,
                        "wh_per_candidate": cost / priceviz.REFERENCE_ELECTRICITY_USD_PER_KWH
                        * 1000.0})
    return {
        "devices": devices,
        "reference_electricity_usd_per_kwh": priceviz.REFERENCE_ELECTRICITY_USD_PER_KWH,
        "genesis_difficulty_target": str(cfg.genesis_difficulty_target),
        "field_modulus": str(__import__("empowering_sim.config",
                                        fromlist=["FIELD_MODULUS"]).FIELD_MODULUS),
        "claim_fee_lepta": cfg.claim_fee,
        "anchor_lepta": 2 * cfg.avg_tx_fee,
        "opening_reward_lepta": ref.opening_reward(),
        "curves": [{"key": c.key, "label": c.label, "note": c.note, "points": c.points}
                   for c in priceviz.curves(400)],
    }


def comparison_rows() -> list[dict]:
    """Simulated outcomes for the three designs. NOT closed forms -- exported, not recomputed.

    The page displays these as measurements with the run that produced them named, rather than
    pretending a browser can re-derive them.
    """
    from . import variant
    d = Triple().derived()
    rows = []
    for cap, label in ((0.0, "de novo"), (variant.DEFAULT_CAP, "de novo*")):
        for retire in (True, False):
            o = variant.evaluate(d, cap, label, retire=retire)
            rows.append({"design": label, "regime": "retiring" if retire else "persistent",
                         "cap": cap, "bonds": o.uniform_bonds, "transition": o.transition,
                         "spike_bonded": o.spike_bonded_fraction,
                         "spike_median_epochs": o.spike_median_epochs,
                         "whale_capture": o.whale_capture})
    return rows


def export(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    ref = Triple()
    cfg = ref.derived().cfg
    params = {
        "launch_supply_lgo": cfg.launch_supply,
        "base_units_per_lgo": cfg.base_units_per_lgo,
        "epochs_per_year": cfg.epochs_per_year,
        "blocks_per_epoch": cfg.blocks_per_epoch,
        "max_block_txs": cfg.max_block_txs,
        "min_stake_lepta": cfg.min_stake,
        "transfer_fee_lepta": cfg.avg_tx_fee,
        "claim_fee_lepta": cfg.claim_fee,
        "pow_share_num": cfg.pow_share_num,
        "pow_share_den": cfg.pow_share_den,
        "efficiency_persistent": EFFICIENCY_PERSISTENT,
        "efficiency_retiring_slow": EFFICIENCY_RETIRING_SLOW,
        "efficiency_retiring_fast": EFFICIENCY_RETIRING_FAST,
        "reference": {"pool_fraction": ref.pool_fraction, "expected_nodes": ref.expected_nodes,
                      "expected_years": ref.expected_years, "txs_per_block": cfg.txs_per_block},
    }
    pj = out / "params.json"
    pj.write_text(json.dumps(params, indent=2) + "\n")

    rows = []
    for pool, nodes, years, txs, k in GRID:
        t = Triple(pool_fraction=pool, expected_nodes=nodes, expected_years=years)
        rows.append({"in": {"pool_fraction": pool, "expected_nodes": nodes,
                            "expected_years": years, "txs_per_block": txs, "spike_k": k},
                     "out": outputs(t, txs, k)})
    gj = out / "golden.json"
    gj.write_text(json.dumps({"rows": rows}, indent=2) + "\n")

    fj = out / "profitability.json"
    fj.write_text(json.dumps(profitability_inputs(), indent=2) + "\n")

    cj = out / "comparison.json"
    cj.write_text(json.dumps({"rows": comparison_rows(),
                              "current_design": {
                                  "note": "measured on the EmPoWering-simulator branch",
                                  "elevated_retiring": 25934, "elevated_persistent": 5682,
                                  "door_closes_at_100_per_epoch": 34,
                                  "point_of_no_return_at_100_per_epoch": 212}},
                             indent=2) + "\n")
    return [pj, gj, fj, cj]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="empowering_denovo_sim.webexport")
    ap.add_argument("--out", type=Path, default=Path("web"))
    for f in export(ap.parse_args().out):
        print(f"  wrote {f}")
