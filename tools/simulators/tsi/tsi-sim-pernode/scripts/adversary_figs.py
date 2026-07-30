"""Render fig8 (uncle-suppression grinding, §6.3) and fig9 (withhold vs suppress, §6.4).

Sources (committed):
  runs/adversary_grid/suppress.parquet  -> fig8_adversary.png
  runs/adversary_grid/withhold.parquet  -> fig9_withhold.png

Both plot D_hat/D vs beta_adv, mean over replicates with a min/max band. Uses the shared
tsi_sim.plotting.style theme. Note post-fix: the honest equilibrium is now 1.0 (not 1.017),
so suppression's ratios sit near 1.0 at low load rather than above it.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tsi_sim.plotting import style

HERE = Path(__file__).resolve().parent.parent
GRID = HERE / "runs" / "adversary_grid"
FIGS = HERE / "report-figures"

# blending budget (s) -> operating load rho (per §6.3)
LOAD = {8.0: 0.56, 16.0: 0.96, 24.0: 1.36}


def _agg(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return df.groupby(keys).mean_ratio.agg(["mean", "min", "max"]).reset_index()


def fig8_suppress() -> Path:
    df = pd.read_parquet(GRID / "suppress.parquet")
    g = _agg(df, ["delay", "beta_adv"])
    fig, ax = plt.subplots()
    for i, delay in enumerate(sorted(g.delay.unique())):
        s = g[g.delay == delay].sort_values("beta_adv")
        c = style.color_for(i)
        x = s.beta_adv.to_numpy()
        ax.fill_between(x, s["min"], s["max"], color=c, alpha=0.15, linewidth=0)
        ax.plot(x, s["mean"], color=c, marker="o", ms=4,
                label=rf"$\rho$ = {LOAD[delay]:.2f}")
    ax.axhline(1.0, color="0.4", ls="--", lw=1.0, zorder=0)
    ax.set_xlabel(r"adversary stake fraction $\beta_{\mathrm{adv}}$")
    ax.set_ylabel(r"$\hat{D}/D$  (uncle suppression)")
    ax.set_title("Uncle-suppression grinding scales with load")
    ax.set_xticks([0.1, 0.3, 0.5])
    ax.legend(title="load", loc="lower left")
    out = FIGS / "fig8_adversary"
    return style.save(fig, out, provenance="runs/adversary_grid/suppress.parquet")[0]


def fig9_withhold() -> Path:
    df = pd.read_parquet(GRID / "withhold.parquet")
    g = _agg(df, ["strategy", "topo", "beta_adv"])
    fig, ax = plt.subplots()
    order = [("withhold", "regular"), ("withhold", "blend"),
             ("suppress", "regular"), ("suppress", "blend")]
    styles = {"withhold": "-", "suppress": "--"}
    colors = {"regular": style.color_for(1), "blend": style.color_for(0)}
    for strat, topo in order:
        s = g[(g.strategy == strat) & (g.topo == topo)].sort_values("beta_adv")
        c = colors[topo]
        x = s.beta_adv.to_numpy()
        ax.fill_between(x, s["min"], s["max"], color=c, alpha=0.10, linewidth=0)
        ax.plot(x, s["mean"], color=c, ls=styles[strat], marker="o", ms=4,
                label=f"{strat}, {topo}")
    # active-stake reference line (1 - beta_adv)
    xr = np.linspace(0.1, 0.5, 50)
    ax.plot(xr, 1 - xr, color="0.4", ls=":", lw=1.2,
            label=r"$1-\beta_{\mathrm{adv}}$ (active stake)")
    ax.set_xlabel(r"adversary stake fraction $\beta_{\mathrm{adv}}$")
    ax.set_ylabel(r"$\hat{D}/D$")
    ax.set_title("Withholding tracks active stake; suppression barely moves it")
    ax.set_xticks([0.1, 0.2, 0.3, 0.4, 0.5])
    ax.legend(loc="lower left", ncol=1)
    out = FIGS / "fig9_withhold"
    return style.save(fig, out, provenance="runs/adversary_grid/withhold.parquet")[0]


def main() -> None:
    style.apply_style()
    p8 = fig8_suppress()
    p9 = fig9_withhold()
    print("wrote", p8)
    print("wrote", p9)


if __name__ == "__main__":
    main()
