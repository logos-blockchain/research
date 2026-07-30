"""Render per-node divergence & topology figures (importable + CLI ``tsi-figures``)."""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import pandas as pd

from . import figures_pernode as F
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
    """Render every applicable figure from ``df`` into directory ``out``; return the count.

    Graph figures are produced per graph topology present (``regular`` and/or ``blend``) so the
    two propagation models are never merged; each is plotted against its own latency knob
    (per-link latency for ``regular``, per-hop mixing delay for ``blend``).
    """
    out = Path(out)
    prov = F._prov(df)
    written: list[Path] = []
    present = set(df["topology"].unique())
    graph_topos = [t for t in F.GRAPH_TOPOLOGIES if t in present] or ["regular"]
    for dist in sorted(df["stake_dist"].unique()):
        for topo in graph_topos:
            tag = f"{dist}_{topo}"
            sub = df[(df["stake_dist"] == dist) & (df["topology"] == topo)]
            written += style.save(F.divergence_vs_epoch(df, dist, topo),
                                  out / f"01_divergence_{tag}", prov)
            if sub.empty:
                continue                     # latency / heatmap figures need real graph data
            written += style.save(F.accuracy_vs_link_latency(df, dist, topo),
                                  out / f"02_accuracy_vs_latency_{tag}", prov)
            written += style.save(F.accuracy_vs_u(df, dist, topo),
                                  out / f"03_accuracy_vs_u_{tag}", prov)
            written += style.save(F.tip_agreement_vs_latency(df, dist, topo),
                                  out / f"04_tip_agreement_{tag}", prov)
            # accuracy heatmap (latency knob x U) for every peering degree
            for deg in sorted(int(x) for x in sub["degree"].unique()):
                written += style.save(F.heatmap_accuracy(df, dist, deg, topo),
                                      out / f"06_heatmap_{tag}_deg{deg}", prov)
            fig = F.heterogeneous_recovery(df, dist, topo)      # per topology (never merged)
            if fig is not None:
                written += style.save(fig, out / f"05_heterogeneous_recovery_{tag}", prov)
            # uncle-window study figures — only when W is actually swept
            if sub["uncle_window"].nunique() > 1:
                written += style.save(F.accuracy_vs_uncle_window(df, dist, topo),
                                      out / f"07_accuracy_vs_window_{tag}", prov)
                written += style.save(F.heatmap_window_delay(df, dist, topo),
                                      out / f"08_window_delay_heatmap_{tag}", prov)
    return len(written)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Render per-node TSI figures")
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
