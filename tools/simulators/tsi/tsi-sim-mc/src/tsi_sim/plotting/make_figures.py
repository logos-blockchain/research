"""Render academic figures from a results frame (importable + CLI ``tsi-figures``)."""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import pandas as pd

from . import figures as F
from . import style


def timestamped_figdir(outdir: str | Path, label: str) -> Path:
    """A fresh ``<outdir>/<YYYY-MM-DD_HHMMSS>_<label>`` folder (never overwrites)."""
    ts = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = Path(outdir) / f"{ts}_{label}"
    d, i = base, 2
    while d.exists():
        d = base.with_name(f"{base.name}_{i}")
        i += 1
    return d


def render(df: pd.DataFrame, out: str | Path) -> int:
    """Render every applicable figure from ``df`` into directory ``out``; return the count."""
    out = Path(out)
    prov = F._provenance(df)
    dists = sorted(df["stake_dist"].unique())
    latencies = sorted(df["latency"].unique())
    lat_focus = latencies[len(latencies) // 2] if latencies else 0
    written: list[Path] = []

    for dist in dists:
        written += style.save(F.accuracy_vs_u(df, dist), out / f"01_accuracy_vs_u_{dist}", prov)
        written += style.save(F.qeff_vs_u(df, dist), out / f"02_qeff_vs_u_{dist}", prov)
        written += style.save(F.convergence(df, dist, lat_focus),
                              out / f"03_convergence_{dist}_L{lat_focus}", prov)
        written += style.save(F.orphan_diagnostics(df, dist), out / f"08_orphans_{dist}", prov)
        for n in sorted(df["n_nodes"].unique()):
            n = int(n)
            written += style.save(F.heatmap_accuracy(df, dist, n),
                                  out / f"04_heatmap_{dist}_N{n}", prov)
            written += style.save(F.concurrency_vs_latency(df, dist, n),
                                  out / f"09_concurrency_vs_latency_{dist}_N{n}", prov)
            written += style.save(F.concurrency_timeseries(df, dist, n),
                                  out / f"10_concurrency_timeseries_{dist}_N{n}", prov)
        written += style.save(F.variance_vs_u(df, dist, lat_focus),
                              out / f"06_variance_vs_u_{dist}_L{lat_focus}", prov)
        if df[(df["stake_dist"] == dist) & (df["max_uncles"] > 0)]["uncle_strategy"].nunique() > 1:
            written += style.save(F.strategy_comparison(df, dist, lat_focus),
                                  out / f"07_strategy_{dist}_L{lat_focus}", prov)

    written += style.save(
        F.dist_comparison(df, lat_focus), out / f"05_dist_comparison_L{lat_focus}", prov
    )
    return len(written)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Render TSI figures")
    ap.add_argument("--results", required=True)
    ap.add_argument("--outdir", default="figures",
                    help="parent dir; a dated sub-folder is created (never overwrites)")
    ap.add_argument("--label", default=None, help="run label (default: results file stem)")
    ap.add_argument("--out", default=None, help="explicit output dir (skips the dated folder)")
    args = ap.parse_args(argv)
    label = args.label or Path(args.results).stem
    out = Path(args.out) if args.out else timestamped_figdir(args.outdir, label)
    n = render(pd.read_parquet(args.results), out)
    print(f"wrote {n} figures -> {out}")


if __name__ == "__main__":  # pragma: no cover
    main()
