"""Window sufficiency at scale + the W-as-buffer question (fig25, report §3.4).

From the window-scale sweep (N = 1 000 vs 10 000, W = 50..600, delta in {8, 16, 32} s, U in
{1, 2}, k = 256): the window floor's position is N-invariant, a wider window buys back the
near-boundary (rho ~ 1) undershoot at U = 1, and no window fixes sustained overload (rho > U).

Run:  python scripts/window_scale_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting import style  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"

BAR = 0.98


def main() -> None:
    src = sorted(RUNS.glob("*_window-scale/results.parquet"))[-1]
    df = pd.read_parquet(src)
    # Early stop terminates each config once it converges (~epoch 16), well short of the
    # nominal ``epochs`` (40). A fixed ``epoch >= 20`` tail would drop almost every config;
    # take the second half of each config's *actually-run* epochs instead (matches the
    # burn_frac=0.5 tail used elsewhere).
    keys = ["n_nodes", "blend_delay_max", "uncle_window", "max_uncles", "replicate"]
    tail_from = df.groupby(keys).epoch.transform("max") * 0.5
    t = df[df.epoch >= tail_from]
    eq = (t.groupby(["n_nodes", "blend_delay_max", "uncle_window", "max_uncles"],
                    as_index=False).mean_ratio.mean())

    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.0), sharey=True)
    for ax, delay in zip(axes, (8.0, 16.0, 32.0), strict=True):
        for n, u in ((1000, 1), (10000, 1), (1000, 2), (10000, 2)):
            s = eq[(eq.blend_delay_max == delay) & (eq.n_nodes == n)
                   & (eq.max_uncles == u)].sort_values("uncle_window")
            ax.plot(s.uncle_window, s.mean_ratio,
                    "-o" if u == 1 else "--s", ms=4, lw=1.3,
                    color=style.OKABE_ITO[0 if n == 1000 else 1],
                    label=f"N={n:,}, U={u}" if delay == 8.0 else None)
        ax.axhline(BAR, color="0.7", lw=0.8, ls="--")
        ax.set_xlabel("uncle window  W  (slots)")
        ax.set_title(f"blending budget δ = {delay:g} s")
    axes[0].set_ylabel(r"$\hat D / D$")
    axes[0].text(60, BAR + 0.006, "0.98 recovery bar", fontsize=7, color="0.5")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Window sufficiency at scale: a wider W buys back the ρ ≈ 1 boundary (middle) "
                 "but cannot fix sustained overload (right)", y=1.03)
    style.save(fig, FIGS / "fig25_window_scale",
               provenance=f"scripts/window_scale_analysis.py ({src.parent.name})")
    plt.close(fig)
    print("wrote fig25_window_scale")

    for delay in (8.0, 16.0, 32.0):
        s = eq[(eq.blend_delay_max == delay) & (eq.max_uncles == 1)]
        piv = s.pivot(index="n_nodes", columns="uncle_window", values="mean_ratio")
        print(f"\nU=1 δ={delay:g}:")
        print(piv.round(3).to_string())


if __name__ == "__main__":
    main()
