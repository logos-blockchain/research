"""Render pd figures from the propagation + adversary parquets (pd-figures)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import figures, style

# (prop, adv) builders.
_BUILDERS = [
    ("01_delay_vs_degree", figures.delay_vs_degree),
    ("02_delay_vs_blendhops", figures.delay_vs_blendhops),
    ("03_delay_vs_N", figures.delay_vs_N),
    ("04_observed_vs_fadv", figures.observed_vs_fadv),
    ("05_eclipse_vs_fadv", figures.eclipse_vs_fadv),
    ("06_observed_vs_degree", figures.observed_vs_degree),
    ("07_eclipse_vs_degree", figures.eclipse_vs_degree),
    ("08_heatmap_observed", figures.heatmap_observed),
    ("09_heatmap_eclipse", figures.heatmap_eclipse),
    ("10_delivery_vs_unresponsive", figures.delivery_vs_unresponsive),
    ("11_coverage_vs_unresponsive", figures.coverage_vs_unresponsive),
    ("20_coverage_percolation", figures.coverage_percolation),
    ("22_churn_correlated_vs_uniform", figures.churn_correlated_vs_uniform),
]

# (prop, adv, deanon) builders — deanonymization crosses propagation paths with the adversary set,
# and the linkability-over-time figures (time to link / learn stake, and the redundancy trade-off).
_DEANON_BUILDERS = [
    ("12_deanon_vs_blendhops", figures.deanon_vs_blendhops),
    ("13_full_deanon_vs_blendhops", figures.full_deanon_vs_blendhops),
    ("14_full_deanon_vs_fadv", figures.full_deanon_vs_fadv),
    ("15_full_deanon_vs_degree", figures.full_deanon_vs_degree),
    ("16_time_to_link_vs_stake", figures.time_to_link_vs_stake),
    ("17_time_to_link_vs_stake_redundancy", figures.time_to_link_vs_stake_redundancy),
    ("18_time_to_stake_vs_threshold", figures.time_to_stake_vs_threshold),
    ("19_redundancy_tradeoff", figures.redundancy_tradeoff),
    ("21_redundancy_time_to_link", figures.redundancy_time_to_link),
]


def render(prop_df: pd.DataFrame, adv_df: pd.DataFrame, deanon_df: pd.DataFrame,
           out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    prov = figures._prov(prop_df, adv_df, deanon_df)
    jobs = ([(name, fn, (prop_df, adv_df)) for name, fn in _BUILDERS]
            + [(name, fn, (prop_df, adv_df, deanon_df)) for name, fn in _DEANON_BUILDERS])
    written: list[Path] = []
    for name, fn, fn_args in jobs:
        try:
            fig = fn(*fn_args)
        except Exception as e:  # noqa: BLE001 — a bad slice shouldn't kill the whole render
            print(f"skip {name}: {e}")
            continue
        if fig is not None:
            written += style.save(fig, out_dir / name, provenance=prov)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render pd figures from a run directory")
    ap.add_argument("--run", required=True, help="runs/<ts>_<label>/ containing the parquets")
    ap.add_argument("--out", default=None, help="output dir (default <run>/figures)")
    args = ap.parse_args(argv)
    run = Path(args.run)
    prop_df = pd.read_parquet(run / "propagation.parquet")
    adv_df = pd.read_parquet(run / "adversary.parquet")
    dz_path = run / "deanon.parquet"
    deanon_df = pd.read_parquet(dz_path) if dz_path.exists() else pd.DataFrame()
    out = Path(args.out) if args.out else run / "figures"
    written = render(prop_df, adv_df, deanon_df, out)
    print(f"wrote {len(written)} figures -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
