"""Optimal selfish mining + uncle-reward incentive design — REPORT §6.6 / §6.7 (fig14).

Two questions:
  A. How much does the *optimal* (Sapirshtein MDP) selfish strategy beat SM1, and where is the
     profitability threshold? (fig14, left)
  B. Do block/uncle REWARDS defuse the attack? Paying an uncle reward to orphaned honest blocks
     compensates them, so the selfish attacker's *reward* share falls below its block share and the
     profitability threshold moves up. (fig14, right)

Adversarial framing (see report §6.7): uncle rewards (i) compensate honestly-orphaned producers,
(ii) disincentivise hiding (a withheld block never propagates -> can never be an uncle -> forfeits
both block and uncle reward), and (iii) shrink the selfish premium. The reward scheme's own attack
surface — "uncle farming" (deliberately orphaning your own blocks to collect uncle rewards) — is
bounded because uncles must be real VRF winners and an uncle pays w_uncle < 1 < a canonical block.

Run:  python scripts/selfish_rewards.py   (writes runs/selfish_rewards.parquet + fig14)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.selfish import (
    RewardParams,
    honest_reward_recovery,
    race_from_alpha,
    reward_shares,
    selfish_revenue_closed_form,
)
from tsi_sim.selfish_mdp import optimal_selfish_revenue

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

N_EVENTS = 4_000_000
ALPHAS = [0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3, 0.36, 0.40, 0.43, 0.46]
W_UNCLES = [0.0, 0.25, 0.5, 1.0]


def sweep_optimal() -> pd.DataFrame:
    """Optimal (MDP) vs SM1 vs honest revenue, plus reward-share under each uncle reward (g=0)."""
    rng = np.random.default_rng(7)
    rows = []
    for alpha in ALPHAS:
        for gamma in (0.0, 0.5):
            opt = optimal_selfish_revenue(alpha, gamma, cap=40, iters=3000)
            rows.append(dict(kind="revenue", alpha=alpha, gamma=gamma,
                             sm1=selfish_revenue_closed_form(alpha, gamma), optimal=opt))
        # reward-share (gamma=0 SM1 race) under each uncle reward
        r = race_from_alpha(alpha, N_EVENTS, 0.0, rng)
        for wu in W_UNCLES:
            rp = RewardParams(w_uncle=wu, p_ref=1.0)
            rows.append(dict(kind="reward", alpha=alpha, w_uncle=wu,
                             block_share=r.revenue_share,
                             reward_share=reward_shares(r, rp).adv_reward_share,
                             honest_recovery=honest_reward_recovery(r, rp)))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "selfish_rewards.parquet")
    return out


def _threshold(alphas, shares):
    """First alpha where share > alpha (profitability boundary), by linear interp; None if never."""
    a = np.array(alphas)
    d = np.array(shares) - a
    for i in range(1, len(a)):
        if d[i - 1] <= 0 < d[i]:
            t = a[i - 1] + (a[i] - a[i - 1]) * (-d[i - 1]) / (d[i] - d[i - 1])
            return float(t)
    return None


def report(df: pd.DataFrame) -> None:
    rev = df[df.kind == "revenue"]
    print("optimal (MDP) vs SM1 revenue, gamma=0 / 0.5:")
    for alpha in (1 / 3, 0.4, 0.46):
        for g in (0.0, 0.5):
            row = rev[(np.isclose(rev.alpha, alpha)) & (rev.gamma == g)].iloc[0]
            print(f"  a={alpha:.3f} g={g}: optimal={row.optimal:.3f} SM1={row.sm1:.3f} "
                  f"(gap {row.optimal-row.sm1:+.3f})")
    rw = df[df.kind == "reward"]
    print("\nuncle reward -> selfish profitability threshold (gamma=0, SM1):")
    for wu in W_UNCLES:
        s = rw[rw.w_uncle == wu].sort_values("alpha")
        thr = _threshold(s.alpha.tolist(), s.reward_share.tolist())
        rec = s[np.isclose(s.alpha, 0.40)].honest_recovery.iloc[0]
        print(f"  w_uncle={wu}: threshold alpha* = {thr if thr is None else round(thr,3)}  "
              f"(honest reward recovery @a=0.4: {rec:.3f})")


def fig14(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))
    aa = np.array(ALPHAS)

    # LEFT: optimal vs SM1 vs honest revenue
    ax = axes[0]
    rev = df[df.kind == "revenue"]
    ax.plot(aa, aa, color="0.5", lw=0.9, ls="--", label="honest (= stake)")
    for i, g in enumerate((0.0, 0.5)):
        s = rev[rev.gamma == g].sort_values("alpha")
        c = style.OKABE_ITO[i]
        ax.plot(s.alpha, s.optimal, "-o", ms=4, color=c, label=rf"optimal, $\gamma={g}$")
        ax.plot(s.alpha, s.sm1, ":", lw=1.4, color=c, label=rf"SM1, $\gamma={g}$")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel("revenue share")
    ax.set_title("Optimal selfish (MDP) vs SM1")
    ax.legend(fontsize=7, loc="upper left")

    # RIGHT: reward-share vs alpha under uncle rewards (gamma=0)
    ax = axes[1]
    rw = df[df.kind == "reward"]
    ax.plot(aa, aa, color="0.5", lw=0.9, ls="--", label="break-even (= stake)")
    for i, wu in enumerate(W_UNCLES):
        s = rw[rw.w_uncle == wu].sort_values("alpha")
        ax.plot(s.alpha, s.reward_share, "-o", ms=4, color=style.OKABE_ITO[i],
                label=rf"$w_u={wu}$")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel("attacker reward share")
    ax.set_title("Uncle rewards shrink the selfish premium")
    ax.legend(fontsize=7, loc="upper left")

    style.save(fig, FIGS / "fig14_optimal_rewards", provenance="scripts/selfish_rewards.py")
    plt.close(fig)


def main() -> None:
    print("=== optimal-selfish + uncle-reward sweep ===")
    df = sweep_optimal()
    report(df)
    fig14(df)
    print("wrote fig14_optimal_rewards")


if __name__ == "__main__":
    main()
