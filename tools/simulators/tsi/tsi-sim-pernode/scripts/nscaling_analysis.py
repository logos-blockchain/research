"""N-scaling of the one-uncle boundary: figures fig23/fig24 + §3.8 numbers.

Combines the direct ladder (nscaling-a/b + 32k tiers, N = 1k..32k) with the exact topology
probe (l_mean(N, degree) to N = 10^6) and the load law rho = f*D_vis:
  fig23 — U=1 accuracy vs N per degree, case (a) vs (b), at the 8-s blending budget.
  fig24 — the ladder collapsed onto rho (validating that N enters only via l_mean), with the
          probe's rho(N) curves extrapolating each degree to 10^6 and the U=1 boundary marked.

Run:  python scripts/nscaling_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting import style  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"

F = 1.0 / 30.0
HOPS = 3


def load_ladder() -> pd.DataFrame:
    parts = []
    for stem in ("nscaling-a", "nscaling-b", "nscaling32-a", "nscaling32-b"):
        cands = sorted(RUNS.glob(f"*_{stem}/results.parquet"))
        if not cands:
            raise SystemExit(f"missing run for {stem}")
        d = pd.read_parquet(cands[-1])
        d["case"] = "b" if stem.endswith("-b") else "a"
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    # Per-trajectory 50% burn-in (matches the report's line-55 convention). A global
    # epoch.max()//2 threshold discards the early-stopping large-N tiers entirely, which
    # dropped deg6/deg8's N=32000 points and left deg4's on a single replicate.
    _keys = ["case", "n_nodes", "degree", "blend_delay_max", "max_uncles", "replicate"]
    tail = df[df.epoch >= df.groupby(_keys).epoch.transform("max") // 2]
    eq = tail.groupby(["case", "n_nodes", "degree", "blend_delay_max", "max_uncles",
                       "replicate"], as_index=False).mean_ratio.mean()
    return eq


def lmean_fits(probe: pd.DataFrame) -> dict[int, tuple[float, float]]:
    """Per-degree log-fit l_mean ~ a*ln(N) + b from the exact probe."""
    lm = probe.groupby(["n", "degree"], as_index=False).l_mean.mean()
    fits = {}
    for deg in sorted(lm.degree.unique()):
        s = lm[lm.degree == deg]
        a, b = np.polyfit(np.log(s.n), s.l_mean, 1)
        fits[int(deg)] = (float(a), float(b))
    return fits


def rho_of(eq: pd.DataFrame, probe: pd.DataFrame) -> pd.DataFrame:
    # fitted l_mean covers every ladder N (the probe grid is log-spaced, not the ladder's)
    fits = lmean_fits(probe)
    m = eq.copy()
    m["l_mean"] = [fits[int(d)][0] * np.log(n) + fits[int(d)][1]
                   for d, n in zip(m.degree, m.n_nodes, strict=True)]
    m["d_vis"] = HOPS * m.blend_delay_max / 2.0 + (HOPS + 1) * m.l_mean
    m["rho"] = F * m.d_vis
    return m


def fig23(eq: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), sharey=True)
    for ax, case, title in ((axes[0], "a", "case (a): geo delays"),
                            (axes[1], "b", "case (b): + 10% Poisson(3) stragglers")):
        s = eq[(eq.case == case) & (eq.blend_delay_max == 8.0) & (eq.max_uncles == 1)]
        for i, deg in enumerate((4, 6, 8)):
            g = s[s.degree == deg].groupby("n_nodes").mean_ratio.agg(["mean", "sem"])
            ax.errorbar(g.index, g["mean"], yerr=g["sem"], fmt="-o", ms=4, capsize=2,
                        color=style.OKABE_ITO[i], label=f"degree {deg}")
        u2 = eq[(eq.case == case) & (eq.blend_delay_max == 8.0) & (eq.max_uncles == 2)]
        g2 = u2.groupby("n_nodes").mean_ratio.mean()
        ax.plot(g2.index, g2.values, ":", color="0.5", lw=1.2, label="U = 2 (all degrees)")
        ax.axhline(0.98, color="0.75", lw=0.8, ls="--")
        ax.text(1100, 0.982, "0.98 recovery bar", fontsize=7, color="0.5")
        ax.set_xscale("log")
        ax.set_xlabel("network size  N")
        ax.set_title(title)
        ax.legend(fontsize=8, loc="lower left")
    axes[0].set_ylim(top=1.01)   # bounded by 1: cap at the exact-recovery bound (above-1 is noise)
    axes[0].set_ylabel(r"stake estimate accuracy  $\hat D / D$")
    fig.suptitle(r"U = 1 erodes with network size (blend, $\delta_{max}$ = 8 s, f = 1/30)",
                 y=1.02)
    style.save(fig, FIGS / "fig23_nscaling_u1", provenance="scripts/nscaling_analysis.py")
    plt.close(fig)


def fig24(m: pd.DataFrame, probe: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    # left: ladder accuracy vs rho, all (N, degree, delay) cells collapse onto one curve
    for case, marker, lbl in (("a", "o", "case (a)"), ("b", "s", "case (b)")):
        s = m[(m.case == case) & (m.max_uncles == 1)]
        g = s.groupby(["n_nodes", "degree", "blend_delay_max"]).agg(
            rho=("rho", "mean"), acc=("mean_ratio", "mean")).reset_index()
        ax1.scatter(g.rho, g.acc, s=18, marker=marker, alpha=0.75, label=lbl)
    ax1.axvline(1.0, color="0.6", lw=0.8, ls=":")
    ax1.text(0.98, 0.05, r"$\rho=1$", rotation=90, fontsize=7, color="0.4",
             va="bottom", ha="right", transform=ax1.get_xaxis_transform())
    ax1.set_xlabel(r"load  $\rho = f\,D_{vis}(N, d, \delta)$")
    ax1.set_ylabel(r"$\hat D / D$ at U = 1")
    ax1.set_ylim(top=1.01)   # bounded by 1: cap at the exact-recovery bound
    ax1.set_title("ladder collapses onto the load law")
    ax1.legend(fontsize=8)
    # right: probe rho(N) per degree to 1M, delta=8
    lm = probe.groupby(["n", "degree"], as_index=False).l_mean.mean()
    for i, deg in enumerate((4, 6, 8)):
        s = lm[lm.degree == deg].sort_values("n")
        rho = F * (HOPS * 8.0 / 2.0 + (HOPS + 1) * s.l_mean)
        ax2.plot(s.n, rho, "-o", ms=4, color=style.OKABE_ITO[i], label=f"degree {deg}")
    ax2.axhline(1.0, color="0.6", lw=0.8, ls=":")
    ax2.axhline(0.96, color="tab:red", lw=0.8, ls="--")
    ax2.text(1.0e6, 0.955, "measured U=1 failure (ρ=0.96, §3.6)", fontsize=7, color="tab:red",
             ha="right", va="top")
    ax2.set_xscale("log")
    ax2.set_xlabel("network size  N")
    ax2.set_ylabel(r"load  $\rho$  at  $\delta_{max}$ = 8 s")
    ax2.set_title(r"exact probe: $\rho(N)$ to $10^6$ nodes")
    ax2.legend(fontsize=8, loc="upper left")
    style.save(fig, FIGS / "fig24_nscaling_probe", provenance="scripts/nscaling_analysis.py")
    plt.close(fig)


def main() -> None:
    probe = pd.read_parquet(RUNS / "topology_probe.parquet")
    eq = load_ladder()
    m = rho_of(eq, probe)
    fig23(eq)
    fig24(m, probe)
    # §3.8 numbers
    print("=== U=1 accuracy vs N (delta=8) ===")
    t = eq[(eq.blend_delay_max == 8.0) & (eq.max_uncles == 1)]
    print(t.groupby(["case", "degree", "n_nodes"]).mean_ratio.mean().round(3).to_string())
    print("\n=== probe rho(delta=8) at 1M ===")
    lm = probe.groupby(["n", "degree"]).l_mean.mean().reset_index()
    one = lm[lm.n == 1_000_000]
    for _, r in one.iterrows():
        rho = F * (HOPS * 4.0 + 4 * r.l_mean)
        print(f"degree {int(r.degree)}: l_mean={r.l_mean:.2f} rho={rho:.3f}")
    for d, a, b in ((4, 0.326, -0.23), (6, 0.192, -0.06), (8, 0.143, 0.00)):
        nstar = np.exp(((0.96 / F - HOPS * 4.0) / 4 - b) / a)
        print(f"degree {d}: U=1 failure crossing at N* ≈ {nstar:.2e}")


if __name__ == "__main__":
    main()
