"""Export the config and a golden cross-check for the browser panel.

The panel re-implements the model in JavaScript so it can run with no backend. That is a
second implementation, and second implementations drift. Two things stop it here:

* ``params.json`` is generated from the same TOML the Python reads, so the panel never
  carries its own copy of a constant; and
* ``golden.json`` is a grid of inputs with the outputs *Python* computes. The page
  recomputes each row in JavaScript on load and shows a pass/fail badge, so a divergence
  is visible in the tool itself rather than discovered by a reader.

Regenerate with ``make web``; the panel refuses to claim agreement it has not checked.
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

from . import core, sampled
from .params import Params, load

# (T, beta_num, rho_den, n_tx, genesis_fraction) -- spread over the interesting corners,
# including the ones that used to crash: beta = 0, and the far end of the T sweep.
GRID = [
    (10, 10, 100, 600, 0.005), (11, 11, 100, 600, 0.005), (50, 50, 100, 600, 0.005),
    (10, 2, 100, 600, 0.005), (10, 33, 100, 600, 0.005), (100, 10, 100, 600, 0.005),
    (500, 10, 100, 1024, 0.005), (10, 10, 200, 300, 0.01), (10, 10, 50, 119, 0.10),
    (1, 10, 100, 20, 0.005), (10, 0, 100, 600, 0.005),
]


def _outputs(p: Params, n_tx: int) -> dict:
    lo, hi = core.iso_margin_window(p)
    return {
        "phi_lepta": p.phi * p.base_units_per_lgo,
        "psi": p.psi,
        "sigma_over_phi": core.sigma_over_phi(p, n_tx),
        "fee_load": core.fee_load(p, n_tx),
        "min_fee_load": core.min_fee_load(p),
        "r_star": core.r_star(p, n_tx),
        "r_min": core.r_min(p),
        "sigma0_over_phi": core.sigma(p.R0, p) / p.phi,
        "builder_edge": core.builder_edge(p, n_tx),
        "drain_per_block": p.T * p.rho_den / p.rho_num,
        "subordination_cap": core.subordination_beta_cap(p),
        "drain_safe_T": core.drain_safe_T(p),
        "window_lo": lo, "window_hi": hi,
        "reconverge": core.reconvergence_blocks(p),
        "rate_bias": sampled.predicted_rate_bias(p),
        "rel_sd": sampled.predicted_relative_sd(p),
        "epoch_sd": sampled.predicted_epoch_sd(p),
        "peak_adversary": core.peak_adversary_share(p, p.adversary_h, 1.0, 0.30),
        "asymptote": core.adversary_asymptote(p.adversary_h, 1.0),
    }


def _clean(v):
    """JSON has no inf/nan; the panel compares against these sentinels explicitly."""
    if isinstance(v, float):
        if v != v:
            return "nan"
        if v == float("inf"):
            return "inf"
        if v == float("-inf"):
            return "-inf"
    return v


def export(config: str, out: Path) -> list[Path]:
    p = load(config)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    pj = out / "params.json"
    pj.write_text(json.dumps({k: _clean(v) for k, v in asdict(p).items()}, indent=2) + "\n")
    written.append(pj)

    rows = []
    for T, bn, rd, n_tx, gf in GRID:
        q = replace(p, T=T, beta_num=bn, rho_den=rd, genesis_pool_fraction=gf)
        rows.append({"in": {"T": T, "beta_num": bn, "rho_den": rd, "n_tx": n_tx,
                            "genesis_pool_fraction": gf},
                     "out": {k: _clean(v) for k, v in _outputs(q, n_tx).items()}})
    gj = out / "golden.json"
    gj.write_text(json.dumps({"config": p.name, "rows": rows}, indent=2) + "\n")
    written.append(gj)
    return written


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="empowering.webexport")
    ap.add_argument("--config", default="configs/specified.toml")
    ap.add_argument("--out", type=Path, default=Path("web"))
    a = ap.parse_args()
    for f in export(a.config, a.out):
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
