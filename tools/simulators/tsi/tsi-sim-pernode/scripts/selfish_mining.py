"""Selfish / private-chain withholding vs TSI — REPORT §6.6, and the per-block issuance question.

Two panels (fig13):
  LEFT  — revenue share adv/(adv+hon) vs stake alpha, for gamma in {0, 0.5, 1}, with the Eyal-Sirer
          closed form overlaid and the profitability thresholds marked. Above threshold the share
          exceeds the diagonal (share = stake), so private-chain withholding IS profitable — the
          opposite of §6.5's abstention withholding.
  RIGHT — TSI coupling: the counted canonical density deflates D_hat to D*·(density fraction);
          uncle references recover orphaned honest blocks back into the count, lifting D_hat toward
          D* (uncle_recovery u in {0, 0.5, 1}). The mechanism that fixes the honest under-count
          (§3.2) also blunts the selfish attacker's estimator deflation.

Issuance / absolute-reward note (the §6.5 GAP-2 question): TSI targets *counted* density = f, so the
canonical block rate is held at ~f regardless of the attack — the canonical "pie" does not inflate
when D_hat deflates (the extra lottery wins are orphans that earn no canonical reward). Hence for a
per-block reward schedule the adversary's ABSOLUTE reward per unit stake equals revenue_share/alpha,
identical to the share metric: §6.5's "unprofitable" abstention result is robust to per-block
issuance, and §6.6's selfish premium (revenue_share/alpha > 1 above threshold) is the real profit.

Run:  python scripts/selfish_mining.py   (writes runs/selfish_*.parquet + fig13)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.selfish import (
    race_from_alpha,
    selfish_revenue_closed_form,
    selfish_threshold,
    tsi_dhat_ratio,
)

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

N_EVENTS = 6_000_000          # per (alpha, gamma) cell; MC noise ~ 1e-3 on the share
GAMMAS = [0.0, 0.5, 1.0]
ALPHAS = [0.05, 0.10, 0.15, 0.20, 0.25, 1 / 3, 0.40, 0.45, 0.49]


def sweep() -> pd.DataFrame:
    rng = np.random.default_rng(20240719)
    rows = []
    for gamma in GAMMAS:
        for alpha in ALPHAS:
            r = race_from_alpha(alpha, N_EVENTS, gamma, rng)
            rows.append(dict(
                alpha=alpha, gamma=gamma,
                share=r.revenue_share,
                closed_form=selfish_revenue_closed_form(alpha, gamma),
                reward_per_stake=r.revenue_share / alpha,          # absolute per-block NPV ratio
                density_fraction=r.density_fraction,               # D_hat/D* at u=0
                dhat_u0=tsi_dhat_ratio(r, 0.0),
                dhat_u50=tsi_dhat_ratio(r, 0.5),
                dhat_u100=tsi_dhat_ratio(r, 1.0),
                orphan_hon_frac=r.orphan_hon / r.events,
            ))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "selfish_sweep.parquet")
    return out


def report(df: pd.DataFrame) -> None:
    print(f"{'gamma':>5} {'thresh':>7}  " + "  ".join(f"a={a:.2f}" for a in [0.2, 1 / 3, 0.4]))
    for gamma in GAMMAS:
        g = df[df.gamma == gamma]
        cells = []
        for a in (0.2, 1 / 3, 0.4):
            row = g[np.isclose(g.alpha, a)].iloc[0]
            cells.append(f"{row.share:.3f}({row.reward_per_stake:.2f}x)")
        print(f"{gamma:5.1f} {selfish_threshold(gamma):7.3f}  " + "  ".join(cells))
    print("(share(reward/stake x); >1x = profitable). D_hat/D* deflation at alpha=0.4, gamma=0:")
    r = df[(df.gamma == 0.0) & np.isclose(df.alpha, 0.4)].iloc[0]
    print(f"   u=0: {r.dhat_u0:.3f}   u=0.5: {r.dhat_u50:.3f}   u=1: {r.dhat_u100:.3f}  "
          f"(orphaned honest {r.orphan_hon_frac*100:.1f}% of blocks)")


def fig13(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    # LEFT: revenue share vs alpha, per gamma, with closed form + diagonal + thresholds
    ax = axes[0]
    aa = np.array(ALPHAS)
    ax.plot(aa, aa, color="0.5", lw=0.9, ls="--", label="honest (share = stake)")
    for i, gamma in enumerate(GAMMAS):
        g = df[df.gamma == gamma].sort_values("alpha")
        c = style.OKABE_ITO[i]
        ax.plot(g.alpha, g.share, "o", ms=4, color=c)
        fine = np.linspace(0.02, 0.49, 200)
        ax.plot(fine, [selfish_revenue_closed_form(a, gamma) for a in fine], "-", lw=1.3,
                color=c, label=rf"$\gamma={gamma}$ (Eyal–Sirer)")
        thr = selfish_threshold(gamma)
        if 0 < thr < 0.5:
            ax.axvline(thr, color=c, lw=0.7, ls=":")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel("revenue share (canonical blocks)")
    ax.set_title("Private-chain withholding is profitable above threshold")
    ax.legend(fontsize=7, loc="upper left")

    # RIGHT: TSI D_hat deflation vs alpha and uncle recovery (gamma=0, worst-case connectivity)
    ax = axes[1]
    g0 = df[df.gamma == 0.0].sort_values("alpha")
    for u, col, lab in [("dhat_u0", style.OKABE_ITO[1], r"no uncles ($\eta$=0)"),
                        ("dhat_u50", style.OKABE_ITO[4], r"$\eta$=0.5"),
                        ("dhat_u100", style.OKABE_ITO[2], r"honest-orphan recovery ($\eta$=1)")]:
        ax.plot(g0.alpha, g0[u], "-o", ms=4, color=col, label=lab)
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--", label=r"honest $D^*$")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel(r"$\hat D / D^*$ (estimator deflation)")
    ax.set_title("Selfish orphaning deflates $\\hat D$; uncles recover it")
    ax.legend(fontsize=7, loc="lower left")

    style.save(fig, FIGS / "fig13_selfish", provenance="scripts/selfish_mining.py")
    plt.close(fig)


def main() -> None:
    print("=== selfish-mining sweep (validated vs Eyal-Sirer) ===")
    df = sweep()
    report(df)
    fig13(df)
    print("wrote fig13_selfish")


if __name__ == "__main__":
    main()
