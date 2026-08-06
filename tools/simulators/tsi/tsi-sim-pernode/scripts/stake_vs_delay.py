"""Relative stake estimate vs network delay (fig16).

Shows the report's central relationship: the recovered *relative stake* ``D̂/D`` as a function of the
mean block-visibility delay ``D_vis`` (seconds), one curve per uncle cap ``U``. Accuracy holds at
the 1.0 exact-recovery bound while the load ``ρ = f·D_vis`` stays below ``⌈U⌉``, then collapses — so
larger delay needs more uncles. Blend transport, f = 1/30 (30 s blocks); delay swept via the
per-hop blending budget ``blend_delay_max``.

Run:  python scripts/stake_vs_delay.py   (writes runs/stake_vs_delay.parquet + fig16)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim import topology
from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.plotting import style

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

F = 1.0 / 30.0
HOPS = 3
DELAYS = [1.0, 4.0, 8.0, 12.0, 16.0, 20.0, 26.0, 32.0, 40.0]   # per-hop blending budget (s)
UNCLES = [0, 1, 2, 3]
BASE = dict(n_nodes=800, k=48, epochs=16, stake_dist="uniform", topology="blend", degree=8,
            link_latency_mean=0.3, link_latency_dist="geo", blend_hops=HOPS, uncle_window=300,
            genesis_d_factor=0.5, f=F)


def d_vis(delay: float) -> float:
    """Mean visibility delay D_vis = hops·δ/2 + (hops+1)·ℓ_mean, ℓ_mean = mean shortest-path."""
    cfg = SimConfig(**BASE, blend_delay_max=delay, max_uncles=1)
    pl = topology.build_path_latency(cfg, np.random.default_rng(np.random.SeedSequence(0)))
    off = pl[~np.eye(pl.shape[0], dtype=bool)]
    l_mean = float(off[np.isfinite(off)].mean())
    return HOPS * delay / 2.0 + (HOPS + 1) * l_mean


def sweep() -> pd.DataFrame:
    rows = []
    for delay in DELAYS:
        dv = d_vis(delay)
        for U in UNCLES:
            reps = []
            for r in range(5):
                df = pd.DataFrame(run_trajectory(SimConfig(
                    replicate=r, blend_delay_max=delay, max_uncles=U, **BASE)))
                reps.append(df[df.epoch >= 8].mean_ratio.mean())
            ratio = float(np.mean(reps))
            sem = float(np.std(reps) / np.sqrt(len(reps)))
            rows.append(dict(delay=delay, d_vis=dv, rho=F * dv, U=U, ratio=ratio, sem=sem))
            print(f"delay={delay:4.0f}s D_vis={dv:5.1f} rho={F*dv:4.2f} U={U}: D̂/D={ratio:.3f}")
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "stake_vs_delay.parquet")
    return out


def fig16(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--", label="exact recovery (1.0)")
    for i, U in enumerate(UNCLES):
        s = df[df.U == U].sort_values("d_vis")
        ax.errorbar(s.d_vis, s.ratio, yerr=s["sem"], fmt="-o", ms=4, capsize=2,
                    color=style.OKABE_ITO[i], label=f"U = {U}")
    # rho = 1, 2, 3 boundaries: D_vis = k/f  <-> rho = f*D_vis = k
    for k in (1, 2, 3):
        dv = k / F
        if dv <= df.d_vis.max() * 1.02:
            ax.axvline(dv, color="0.7", lw=0.7, ls=":")
            ax.text(dv, 0.32, f"ρ={k}", rotation=90, va="bottom", ha="right", fontsize=7,
                    color="0.4")
    ax.set_xlabel(r"mean block-visibility delay $D_{\rm vis}$ (s)   [load $\rho = f\,D_{\rm vis}$]")
    ax.set_ylabel(r"relative stake estimate  $\hat D / D$")
    ax.set_title(r"Recovered relative stake vs delay (blend, $f=1/30$): "
                 r"$U$ must grow with $\rho=\lceil f D_{\rm vis}\rceil$")
    ax.set_ylim(0.3, 1.02)   # bounded by 1: cap at the exact-recovery bound, no above-1 headroom
    ax.legend(fontsize=8, loc="lower left")
    style.save(fig, FIGS / "fig16_stake_vs_delay", provenance="scripts/stake_vs_delay.py")
    plt.close(fig)


def main() -> None:
    print("=== relative stake estimate vs delay ===")
    df = sweep()
    fig16(df)
    print("wrote fig16_stake_vs_delay")


if __name__ == "__main__":
    main()
