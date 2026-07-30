"""Appendix B: the U=0 estimate fluctuates around 1 — sampling noise, not bias (figB1, figB2).

Data:
  (1) clean zero-delay series (full_mesh, L=0, U=0, uniform stakes) at k in {256, 1024, 2160}
      -> runs/fluctuation_u0.parquet   (this script, --run)
  (2) the committed full-scale N=1000 run (regular sub-slot links and blend, U=0, k=2160)
      -> per-epoch tails read directly.

Figures:
  figB1 — high-precision per-epoch trace of (D_hat/D - 1) in per-mil at k=2160: the clean
          zero-delay series and the realistic 0.1-slot direct-gossip series, with the
          +-sigma_th = sqrt((1-f)/(f T)) band.
  figB2 — left: per-epoch deviation distributions vs k with the 1/sqrt(T) law; right: the
          delay progression (0.1 -> 1.0-slot links, blend): mean drops below 1 and
          P(D_hat/D > 1) -> 0 as orphan loss takes over.

Run:  python scripts/appendix_fluct.py --run     (simulate series (1), ~30-60 min)
      python scripts/appendix_fluct.py           (render figures + print stats)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from joblib import Parallel, delayed  # noqa: E402

from tsi_sim.config import SimConfig  # noqa: E402
from tsi_sim.engine import run_trajectory  # noqa: E402
from tsi_sim.plotting import style  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"

F = 1.0 / 30.0
KS = (256, 1024, 2160)
REPS = 4
EPOCHS = 120


def sigma_theory(k: int) -> float:
    t_win = 6 * int(k / F)
    return float(np.sqrt((1 - F) / (F * t_win)))


def _one(k: int, rep: int) -> pd.DataFrame:
    cfg = SimConfig(n_nodes=400, stake_dist="uniform", topology="full_mesh", latency=0,
                    max_uncles=0, uncle_window=300, k=k, epochs=EPOCHS,
                    genesis_d_factor=1.0, replicate=rep)
    df = pd.DataFrame(run_trajectory(cfg))
    df["k_run"] = k
    return df[["k_run", "replicate", "epoch", "mean_ratio", "range_ratio"]]


def run() -> None:
    jobs = [(k, r) for k in KS for r in range(REPS)]
    parts = Parallel(n_jobs=3, prefer="processes")(delayed(_one)(k, r) for k, r in jobs)
    out = pd.concat(parts, ignore_index=True)
    out.to_parquet(RUNS / "fluctuation_u0.parquet")
    print(f"wrote {len(out)} rows -> runs/fluctuation_u0.parquet")


def figs() -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    clean = pd.read_parquet(RUNS / "fluctuation_u0.parquet")
    full = pd.read_parquet(sorted(RUNS.glob("2026-07-23_*_fullscale-small/results.parquet"))[-1])
    u0 = full[full.max_uncles == 0]

    # ---- figB1: high-precision traces at k=2160 ----
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    s = clean[(clean.k_run == 2160) & (clean.replicate == 0) & (clean.epoch >= 4)]
    ax.plot(s.epoch, (s.mean_ratio - 1) * 1e3, "-o", ms=3,
            color=style.OKABE_ITO[0], label="zero delay (full mesh), U = 0")
    r = (u0[(u0.topology == "regular") & (u0.link_latency_mean == 0.1) & (u0.degree == 6)
            & (u0.replicate == 0) & (u0.epoch >= 4)])
    ax.plot(r.epoch, (r.mean_ratio - 1) * 1e3, "-s", ms=3,
            color=style.OKABE_ITO[1], label="direct gossip, 0.1-slot links, U = 0")
    sg = sigma_theory(2160) * 1e3
    ax.axhspan(-sg, sg, color="0.9", zorder=0)
    ax.axhline(0.0, color="0.5", lw=0.8)
    ax.text(119, -sg * 1.45, r"$\pm\sigma_{th} = \sqrt{(1-f)/(fT)}$", fontsize=8,
            color="0.4", ha="right")
    ax.set_xlabel("epoch")
    ax.set_ylabel(r"$(\hat D / D - 1) \times 10^{3}$   (per-mil)")
    ax.set_title("U = 0, k = 2160: per-epoch sampling noise around the ≤1 equilibrium")
    ax.legend(fontsize=8)
    style.save(fig, FIGS / "figB1_fluctuation_trace", provenance="scripts/appendix_fluct.py")
    plt.close(fig)

    # ---- figB2: sigma vs k (left), delay progression (middle), sigma vs delay/U (right) ----
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13.6, 4.0))
    for i, k in enumerate(KS):
        s = clean[(clean.k_run == k) & (clean.epoch >= 8)]
        dev = (s.mean_ratio - 1) * 1e3
        ax1.hist(dev, bins=31, density=True, histtype="step", lw=1.4,
                 color=style.OKABE_ITO[i],
                 label=f"k={k}:  sd {dev.std()/1e3:.4f} (th {sigma_theory(k):.4f})")
    ax1.axvline(0, color="0.5", lw=0.8)
    ax1.set_xlabel(r"$(\hat D / D - 1) \times 10^{3}$")
    ax1.set_ylabel("density")
    ax1.set_title(r"noise shrinks as $1/\sqrt{T}$ (window size)")
    ax1.legend(fontsize=7)

    rows = []
    for lat in (0.1, 0.2, 0.5, 1.0):
        s = u0[(u0.topology == "regular") & (u0.link_latency_mean == lat)
               & (u0.epoch >= 15)].mean_ratio
        rows.append(dict(case=f"gossip {lat}", mean=s.mean(), p_gt1=(s > 1).mean(),
                         lo=s.quantile(0.05), hi=s.quantile(0.95)))
    b = u0[(u0.topology == "blend") & (u0.epoch >= 15)].mean_ratio
    rows.append(dict(case="Blend", mean=b.mean(), p_gt1=(b > 1).mean(),
                     lo=b.quantile(0.05), hi=b.quantile(0.95)))
    dd = pd.DataFrame(rows)
    x = np.arange(len(dd))
    ax2.errorbar(x, dd["mean"], yerr=[dd["mean"] - dd.lo, dd.hi - dd["mean"]],
                 fmt="o", ms=5, capsize=3, color=style.OKABE_ITO[0])
    for xi, (_, row) in zip(x, dd.iterrows(), strict=True):
        ax2.annotate(f"P(>1)={row.p_gt1:.0%}", (xi, row.hi), textcoords="offset points",
                     xytext=(0, 6), ha="center", fontsize=7, color="0.35")
    ax2.axhline(1.0, color="0.5", lw=0.8, ls=":")
    ax2.set_xticks(x, dd.case, rotation=20, ha="right", fontsize=8)
    ax2.set_ylabel(r"$\hat D / D$  (U = 0, k = 2160)")
    ax2.set_title("orphan loss pulls the mean below 1;\nexcursions above 1 vanish with delay")

    # right: per-epoch sigma (within a trajectory) vs case, U=0 vs U=1
    def per_epoch_sigma(s: pd.DataFrame) -> float:
        return float(s.groupby(["degree", "replicate"]).mean_ratio.std().mean())

    cases: list[tuple[str, pd.DataFrame]] = []
    for lat in (0.1, 0.2, 0.5, 1.0):
        cases.append((f"gossip {lat}",
                      full[(full.topology == "regular") & (full.link_latency_mean == lat)
                           & (full.epoch >= 15)]))
    for dl in (1.0, 2.0, 3.0):
        cases.append((f"blend δ={dl:g}",
                      full[(full.topology == "blend") & (full.blend_delay_max == dl)
                           & (full.epoch >= 15)]))
    x3 = np.arange(len(cases))
    for u, marker, lbl in ((0, "o", "U = 0"), (1, "s", "U = 1")):
        sig = [per_epoch_sigma(s[s.max_uncles == u]) for _, s in cases]
        ax3.plot(x3, sig, marker, ms=6, ls="-", lw=1.0,
                 color=style.OKABE_ITO[0 if u else 1], label=lbl)
    ax3.axhline(sigma_theory(2160), color="0.5", lw=0.9, ls="--")
    ax3.text(0.05, sigma_theory(2160) * 1.15, r"sampling floor $\sigma_{th}$",
             fontsize=7, color="0.4")
    ax3.set_yscale("log")
    ax3.set_xticks(x3, [c for c, _ in cases], rotation=20, ha="right", fontsize=8)
    ax3.set_ylabel(r"per-epoch $\sigma$ of $\hat D / D$")
    ax3.set_title("Blend delay amplifies U = 0 noise ~17×;\none uncle restores the floor")
    ax3.legend(fontsize=8)
    style.save(fig, FIGS / "figB2_fluctuation_stats", provenance="scripts/appendix_fluct.py")
    plt.close(fig)

    # ---- stats for the appendix text ----
    print("=== clean zero-delay series ===")
    for k in KS:
        s = clean[(clean.k_run == k) & (clean.epoch >= 8)].mean_ratio
        print(f"k={k}: mean={s.mean():.5f} sd={s.std():.5f} (th {sigma_theory(k):.5f}) "
              f"P(>1)={(s > 1).mean():.2f} min={s.min():.4f} max={s.max():.4f}")


if __name__ == "__main__":
    if "--run" in sys.argv:
        run()
    else:
        figs()
