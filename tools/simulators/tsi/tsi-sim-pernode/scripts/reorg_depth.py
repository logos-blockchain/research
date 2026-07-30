"""Fork depth and private-chain reorg depth vs parameters and adversary stake (fig27, fig28).

Honest fork depth (adversary 0 %) is measured by the engine (runs/fork_rate_vs_delay.parquet:
fork_rate and max_reorg_depth vs Blend delay and uncle cap). The adversarial deepest-reorg tail
comes from src/tsi_sim/reorg.py, coupled to the measured honest orphan rate via alpha_eff.

  fig27 — P(reorg depth >= d) vs d, per adversary stake {0, 10, 20, 30 %}, at the recommended
          operating point; closed-form tail with Monte-Carlo validation markers.
  fig28 — reorg depth vs Blend delay: the honest max depth (engine, U=0 vs U=2) and the
          adversarial 99.9-percentile depth per stake — both fall steeply as delay drops
          (fewer forks) and as uncles keep the block rate at f.

Run:  python scripts/reorg_depth.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting import style  # noqa: E402
from tsi_sim.reorg import alpha_effective, reorg_depth_tail  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
F = 1.0 / 30.0
STAKES = [0.0, 0.1, 0.2, 0.3]
COL = {0.0: "0.5", 0.1: style.OKABE_ITO[0], 0.2: style.OKABE_ITO[1], 0.3: style.OKABE_ITO[2]}


def depth_for_prob(alpha_eff: float, p: float = 1e-3) -> float:
    """Smallest depth d with P(reorg >= d) < p (a practical worst-case reorg to defend against)."""
    if alpha_eff <= 0.0:
        return 0.0
    if alpha_eff >= 0.5:
        return float("inf")
    r = alpha_eff / (1.0 - alpha_eff)
    return float(np.ceil(np.log(p) / np.log(r)))


def fig27(o_ref: float) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    rng = np.random.default_rng(20260723)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ds = np.arange(1, 13)
    for alpha in STAKES:
        ae = alpha_effective(alpha, o_ref)
        if alpha == 0.0:
            ax.plot(ds, [0] * len(ds), "-", color=COL[alpha], lw=1.4,
                    label="0 % (no private chain)")
            continue
        tail = [reorg_depth_tail(ae, int(d)) for d in ds]
        ax.plot(ds, tail, "-", color=COL[alpha], lw=1.6,
                label=f"{alpha:.0%}  (α_eff={ae:.2f})")
        # Monte-Carlo of the stationary catch-up tail: the fraction of time a reflected
        # random walk (adversary lead over the public chain, down-drift since ae<1/2) sits
        # at least d ahead converges to the closed form r^d — the quantity the lines plot.
        walk = rng.random(4_000_000) < ae
        lead = 0
        occ = np.zeros(len(ds) + 1, dtype=np.int64)
        for up in walk:
            lead = lead + 1 if up else max(lead - 1, 0)
            if lead:
                occ[1:min(lead, len(ds)) + 1] += 1
        pts = [occ[int(d)] / walk.size for d in ds[:6]]
        ax.plot(ds[:6], pts, "s", ms=4, color=COL[alpha], alpha=0.5)
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 1.5)
    ax.set_xlabel("reorg depth  d  (confirmations reversed)")
    ax.set_ylabel(r"$P(\mathrm{reorg\ depth} \geq d)$")
    ax.set_title(f"Deepest-reorg tail vs adversary stake (Blend, operating point o≈{o_ref:.2f})\n"
                 "lines: closed form; squares: Monte-Carlo")
    ax.legend(fontsize=8, title="adversary stake")
    style.save(fig, FIGS / "fig27_reorg_tail", provenance="scripts/reorg_depth.py")
    plt.close(fig)


def fig28(fr: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    # honest measured max reorg depth (engine), U=0 vs U=2
    for U, ls, lbl in ((0, ":", "honest, U=0 (overproduces)"), (2, "-", "honest, U=2")):
        s = fr[fr.U == U].sort_values("delta")
        ax.plot(s.delta, s.max_depth, ls, color="0.4", lw=1.4, marker="o", ms=4, label=lbl)
    # adversarial 99.9-pct depth vs delay, per stake, using U=2 honest orphan rate.
    # inf (alpha_eff >= 1/2: unbounded) is drawn as an off-top marker with a "∞" callout.
    base = fr[fr.U == 2].sort_values("delta")
    ax.set_ylim(0, 40)
    for alpha in (0.1, 0.2, 0.3):
        raw = [depth_for_prob(alpha_effective(alpha, o)) for o in base.fork_rate]
        depths = [min(d, 39) for d in raw]
        ax.plot(base.delta, depths, "-", color=COL[alpha], lw=1.6, marker="s", ms=4,
                label=f"adversary {alpha:.0%} (99.9-pct)")
        for x, r in zip(base.delta, raw, strict=True):
            if np.isinf(r):
                ax.annotate("∞ (unbounded)", (x, 39), color=COL[alpha], fontsize=7,
                            ha="center", va="top")
    ax.axvline(16.8, color="0.8", lw=0.8, ls="--")
    ax.text(15.8, 37, "ρ≈1 (δ≈17 s)", fontsize=7, color="0.5", ha="right")
    ax.set_xlabel("Blend per-hop blending budget  δ  (s)   [more delay → more forks]")
    ax.set_ylabel("reorg depth (blocks)")
    ax.set_title("Reorg depth grows with delay and adversary stake — "
                 "shrunk by uncles (block rate at f) and by ρ<1")
    ax.legend(fontsize=8, ncols=2)
    style.save(fig, FIGS / "fig28_reorg_depth_vs_delay", provenance="scripts/reorg_depth.py")
    plt.close(fig)


def measure_fork_rate() -> pd.DataFrame:
    """Honest fork rate + max reorg depth vs Blend delay and uncle cap (engine, adversary 0 %)."""
    from tsi_sim.config import SimConfig
    from tsi_sim.engine import run_trajectory
    rows = []
    for delta in (2.0, 4.0, 8.0, 16.0, 32.0):
        for u in (0, 2):
            frs, mds = [], []
            for rep in range(3):
                df = pd.DataFrame(run_trajectory(SimConfig(
                    n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=delta, max_uncles=u, uncle_window=300, k=256,
                    epochs=16, genesis_d_factor=0.5, early_stop=True, replicate=rep)))
                t = df[df.epoch >= 6]
                frs.append(t.fork_rate.mean())
                mds.append(t.max_reorg_depth.max())
            rows.append(dict(delta=delta, U=u, fork_rate=float(np.mean(frs)),
                             max_depth=int(np.max(mds))))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "fork_rate_vs_delay.parquet")
    return out


def measure_fork_rate_scale() -> pd.DataFrame:
    """Honest fork rate vs N and peering degree at the recommended budget (U=2, δ=8 s).

    Widens the reorg study (§6.10): since a bigger/sparser network raises the honest fork rate,
    and the adversary's effective share depends on it, reorg depth should be shown vs N/degree.
    """
    from tsi_sim.config import SimConfig
    from tsi_sim.engine import run_trajectory
    rows = []
    for n in (1000, 4000, 16000):
        for deg in (4, 6, 8):
            frs = []
            for rep in range(3):
                df = pd.DataFrame(run_trajectory(SimConfig(
                    n_nodes=n, stake_dist="pareto", topology="blend", degree=deg,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=8.0, max_uncles=2, uncle_window=300, k=256,
                    epochs=16, genesis_d_factor=0.5, early_stop=True, replicate=rep)))
                frs.append(df[df.epoch >= 6].fork_rate.mean())
            o = float(np.mean(frs))
            row = dict(n=n, degree=deg, fork_rate=o)
            for alpha in (0.1, 0.2, 0.3):
                row[f"d999_{int(alpha * 100)}"] = depth_for_prob(alpha_effective(alpha, o))
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "fork_rate_vs_scale.parquet")
    print(out.round(3).to_string(index=False))
    return out


def main() -> None:
    if "--measure" in sys.argv:
        print(measure_fork_rate().to_string(index=False))
        return
    if "--measure-scale" in sys.argv:
        measure_fork_rate_scale()
        return
    fr = pd.read_parquet(RUNS / "fork_rate_vs_delay.parquet")
    o_ref = float(fr[(fr.U == 2) & (fr.delta == 8.0)].fork_rate.iloc[0])
    fig27(o_ref)
    fig28(fr)
    print("=== reorg-depth summary (U=2 operating points) ===")
    for _, row in fr[fr.U == 2].sort_values("delta").iterrows():
        line = f"δ={row.delta:4.0f}s  honest o={row.fork_rate:.2f} max_depth={row.max_depth}"
        for alpha in (0.1, 0.2, 0.3):
            dd = depth_for_prob(alpha_effective(alpha, row.fork_rate))
            line += f" | {alpha:.0%}: d99.9={dd:.0f}"
        print(line)
    print("wrote fig27_reorg_tail, fig28_reorg_depth_vs_delay")


if __name__ == "__main__":
    main()
