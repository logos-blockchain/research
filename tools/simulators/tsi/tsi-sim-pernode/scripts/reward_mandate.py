"""Soft (reward-weighted) uncle inclusion — REPORT §6.7 / §6.8 (fig15).

Inclusion is a SOFT rule (omission forfeits the nephew reward; it is NOT a block-validity rule) —
because no node can prove which forks a producer could see within the window, so a *validity* rule
cannot be encoded fork-safely (§6.8). Under a soft rule the reference rate ``p_ref`` is EMERGENT: an
honest orphan was published, so any honest canonical block that sees it within ``W`` references it
for the nephew reward — the attacker only suppresses on *its own* canonical blocks. So ``p_ref`` is
high in practice (honest referencers), driven toward 1 by a larger ``W`` and toward 0 only by deep
reorgs whose orphans age out of the window before an honest block references them.

fig15 sweeps that emergent ``p_ref`` for the SM1 selfish attacker (gamma=0, self-uncle on):
  LEFT  — reward share vs ``p_ref``: the ``p_ref → 0`` end (attacker suppresses all / tiny ``W``) is
          the *backfire* (share above block-only); the honest-referencer / large-``W`` end
          (``p_ref → 1``) reaches ~stake. The crossover below block-only is near ``p_ref ≈ 0.3``.
  RIGHT — honest-orphan reward recovery vs ``p_ref`` (the fairness metric).

So the soft rule delivers the fairness + selfish-mitigation of a hard mandate *without* the fork
risk, to the extent ``W``/visibility keep ``p_ref`` high; the residual is exactly the "can't
guarantee a node sees every fork in the window" gap. Also prints the bribery bound (§6.9).

Run:  python scripts/reward_mandate.py   (writes runs/reward_mandate.parquet + fig15)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.selfish import RewardParams, honest_reward_recovery, race_from_alpha, reward_shares

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

N_EVENTS = 4_000_000
ALPHAS = [0.35, 0.40, 0.46]        # near / above the selfish threshold, where uncle rewards matter
P_REFS = [0.0, 0.2, 0.3, 0.5, 0.7, 0.85, 1.0]
W_U, W_N = 0.875, 0.03125          # Ethereum-like: w_u + w_n = 0.906 < 1 (farming-safe)


def sweep() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    rows = []
    for alpha in ALPHAS:
        r = race_from_alpha(alpha, N_EVENTS, 0.0, rng)
        for p in P_REFS:
            # soft rule: honest referencers take the nephew (adv_nephew=0), attacker self-uncles
            rp = RewardParams(w_uncle=W_U, w_nephew=W_N, p_ref=p, p_ref_adv=1.0, adv_nephew=0.0)
            rec = honest_reward_recovery(r, RewardParams(w_uncle=W_U, p_ref=p))
            rows.append(dict(alpha=alpha, p_ref=p, block=r.revenue_share,
                             reward_share=reward_shares(r, rp).adv_reward_share, recovery=rec))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "reward_mandate.parquet")
    return out


def report(df: pd.DataFrame) -> None:
    print(f"Soft rule, Ethereum-like w_u={W_U}, w_n={W_N} (sum {W_U+W_N:.3f} < 1, farming-safe):")
    for alpha in ALPHAS:
        s = df[df.alpha == alpha].sort_values("p_ref")
        block = s.block.iloc[0]
        print(f"alpha={alpha} block_share={block:.3f} stake={alpha}: reward_share by p_ref")
        for _, row in s.iterrows():
            tag = " BACKFIRE" if row.reward_share > block + 1e-3 else ""
            print(f"   p_ref={row.p_ref:.2f}: share={row.reward_share:.3f} "
                  f"rec={row.recovery:.2f}{tag}")
    print("\nbribery to suppress a reference (§6.9): a soft rule costs the briber only w_nephew =",
          W_N, "(cheap) but never forks; a hard rule would cost a full block but cannot be encoded "
          "fork-safely.")


def fig15(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    ax = axes[0]
    for i, alpha in enumerate(ALPHAS):
        s = df[df.alpha == alpha].sort_values("p_ref")
        c = style.OKABE_ITO[i]
        ax.plot(s.p_ref, s.reward_share, "-o", ms=4, color=c, label=rf"$\alpha={alpha}$")
        ax.axhline(s.block.iloc[0], color=c, lw=0.8, ls=":", alpha=0.7)   # block-only reference
    ax.axvspan(0, 0.3, color="0.9", label="attacker-suppressed / small W")
    ax.set_xlabel(r"emergent reference rate $p_{\rm ref}$ (grows with $W$)")
    ax.set_ylabel("attacker reward share")
    ax.set_title("Soft rule: high $p_{\\rm ref}$ (honest refs) → ~stake")
    ax.legend(fontsize=7, loc="upper right")

    ax = axes[1]
    for i, alpha in enumerate(ALPHAS):
        s = df[df.alpha == alpha].sort_values("p_ref")
        ax.plot(s.p_ref, s.recovery, "-o", ms=4, color=style.OKABE_ITO[i],
                label=rf"$\alpha={alpha}$")
    ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
    ax.set_xlabel(r"emergent reference rate $p_{\rm ref}$")
    ax.set_ylabel("honest reward recovery")
    ax.set_title(r"Honest-orphan compensation ($w_u=0.875$)")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7, loc="lower right")

    style.save(fig, FIGS / "fig15_mandate", provenance="scripts/reward_mandate.py")
    plt.close(fig)


def main() -> None:
    print("=== soft (reward-weighted) uncle inclusion: reward share vs emergent p_ref ===")
    df = sweep()
    report(df)
    fig15(df)
    print("wrote fig15_mandate")


if __name__ == "__main__":
    main()
