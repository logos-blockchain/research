"""What the first-fork restriction costs against a selfish adversary — REPORT §6.6 (fig36).

§6.6 reads the estimator repair off a free knob: the uncle-recovery fraction ``eta``, quoted at
``eta = 1`` ("honest-orphan recovery"). The countable uncle model (§2.1) can reference only the
**first block of a fork**, so ``eta`` is not free — it is capped by how the adversary *shapes* the
blocks it orphans:

  * **SM1** acts the moment the honest branch reaches length 1 (match at a 1-lead, override at a
    2-lead, publish-one above it), so it never buries a second block behind the first. Every orphan
    it makes is the first block of its fork and the cap is exactly 1 — the restriction is free.
  * The **optimal** (Sapirshtein–Sompolinsky–Zohar) policy *waits*, then overrides a run of ``h``
    honest blocks at once. That run is one chain, so the deployed rules recover **one** uncle from
    it, not ``h``, and the cap falls to ~0.44 at ``alpha = 0.4``.

So SM1 is a faithful proxy for selfish-mining *revenue* (§6.6 quotes 0.484 vs the optimum's 0.488
at gamma = 0) but **not** for TSI's estimator damage: the two differ by a factor of ~2 in
recoverable orphans. The panel on the right is the consequence — the repair §6.6 credits to uncle
counting is roughly half of what the unrestricted model shows, and it *degrades* with alpha where
the unrestricted model improves.

Two panels (fig36):
  LEFT  — the recovery ceiling ``eta_countable`` vs stake, per gamma, against SM1's flat 1.0.
  RIGHT — the resulting ``D_hat/D*`` at gamma = 0: no uncles, countable (p_ref = 1 and 0.85), and
          the unrestricted baseline §6.6 reports.

Run:  python scripts/countable_selfish.py   (writes runs/countable_selfish.parquet + fig36)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.reorg import (
    alpha_effective,
    countable_recovery_from_depths,
    simulate_deepest_reorg,
)
from tsi_sim.selfish import race_from_alpha, selfish_threshold, tsi_dhat_ratio
from tsi_sim.selfish_mdp import optimal_policy_stats

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

# cap 64 keeps the orphan *shape* converged (it settles more slowly than the revenue: the drift
# from cap 48 to 64 is ~3e-4 in eta at alpha = 0.4, ~5e-3 at alpha = 0.45).
CAP = 64
GAMMAS = [0.0, 0.5]
ALPHAS = [0.26, 0.28, 0.30, 0.34, 0.36, 0.38, 0.40, 0.42, 0.44, 0.46]
P_REF_REALISTIC = 0.85        # the §6.8 stand-in for the emergent honest-referencer rate
N_EVENTS = 4_000_000          # SM1 comparison arm


def sweep() -> pd.DataFrame:
    rng = np.random.default_rng(20260805)
    rows = []
    for gamma in GAMMAS:
        for alpha in ALPHAS:
            s = optimal_policy_stats(alpha, gamma, cap=CAP)
            sm1 = race_from_alpha(alpha, N_EVENTS, gamma, rng)
            rows.append(dict(
                alpha=alpha, gamma=gamma, cap=CAP,
                above_threshold=alpha > selfish_threshold(gamma),
                deviates=s.deviates,
                revenue_opt=s.revenue,
                revenue_sm1=sm1.revenue_share,
                density_fraction=s.density_fraction,
                orphan_hon_blocks=s.orphan_hon_blocks,
                orphan_hon_runs=s.orphan_hon_runs,
                eta_countable=s.countable_recovery if s.deviates else np.nan,
                eta_countable_adv=s.countable_recovery_adv if s.deviates else np.nan,
                # the estimator, as §6.6 reports it (unrestricted) and as deployed (countable)
                dhat_u0=s.dhat_ratio(p_ref=0.0),
                dhat_unrestricted=s.dhat_ratio(p_ref=1.0, countable=False),
                dhat_countable=s.dhat_ratio(p_ref=1.0, countable=True),
                dhat_countable_pref=s.dhat_ratio(p_ref=P_REF_REALISTIC, countable=True),
                # SM1's own repair, for contrast: eta = 1 is attainable there
                dhat_sm1_eta1=tsi_dhat_ratio(sm1, 1.0),
                eta_sm1=sm1.countable_recovery,
            ))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "countable_selfish.parquet")
    return out


def report(df: pd.DataFrame) -> None:
    print(f"{'gamma':>5} {'alpha':>6} {'rev_opt':>8} {'rev_SM1':>8} {'eta_cnt':>8} {'eta_SM1':>8} "
          f"{'no unc':>7} {'unrestr':>8} {'count':>7} {'cnt@.85':>8}")
    for _, r in df[df.deviates].iterrows():
        print(f"{r.gamma:5.1f} {r.alpha:6.2f} {r.revenue_opt:8.4f} {r.revenue_sm1:8.4f} "
              f"{r.eta_countable:8.4f} {r.eta_sm1:8.4f} {r.dhat_u0:7.4f} "
              f"{r.dhat_unrestricted:8.4f} {r.dhat_countable:7.4f} {r.dhat_countable_pref:8.4f}")
    hit = df[(df.gamma == 0.0) & np.isclose(df.alpha, 0.40)]
    if not hit.empty:
        r = hit.iloc[0]
        print(f"\nHeadline (alpha=0.40, gamma=0): revenue {r.revenue_sm1:.3f} (SM1) vs "
              f"{r.revenue_opt:.3f} (optimal) — a faithful proxy;")
        print(f"  but eta 1.000 (SM1) vs {r.eta_countable:.3f} (optimal) — not a faithful proxy, "
              f"and D_hat {r.dhat_unrestricted:.3f} -> {r.dhat_countable:.3f}.")


def fig36(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    # LEFT: the recovery ceiling, optimal policy vs SM1
    ax = axes[0]
    ax.axhline(1.0, color="0.5", lw=1.1, ls="--",
               label="SM1 — every orphan countable")
    for i, gamma in enumerate(GAMMAS):
        g = df[(df.gamma == gamma) & df.deviates].sort_values("alpha")
        ax.plot(g.alpha, g.eta_countable, "-o", ms=4, color=style.OKABE_ITO[i + 1],
                label=rf"optimal policy, $\gamma={gamma}$")
        thr = selfish_threshold(gamma)
        ax.axvline(thr, color=style.OKABE_ITO[i + 1], lw=0.7, ls=":")
    ax.set_ylim(0, 1.08)
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel(r"countable recovery ceiling $\eta$")
    ax.set_title("The optimum buries orphans SM1 leaves reachable")
    ax.legend(fontsize=7, loc="lower left")

    # RIGHT: the estimator consequence at gamma = 0
    ax = axes[1]
    g0 = df[(df.gamma == 0.0) & df.deviates].sort_values("alpha")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--", label=r"honest $D^*$")
    ax.plot(g0.alpha, g0.dhat_unrestricted, "-s", ms=4, color=style.OKABE_ITO[2],
            label=r"unrestricted count, $p_{ref}=1$ (fig13's $\eta=1$)")
    ax.plot(g0.alpha, g0.dhat_countable, "-o", ms=4, color=style.OKABE_ITO[3],
            label=r"countable, $p_{ref}=1$ (deployed rule)")
    ax.plot(g0.alpha, g0.dhat_countable_pref, "-^", ms=4, color=style.OKABE_ITO[5],
            label=rf"countable, $p_{{ref}}={P_REF_REALISTIC}$")
    ax.plot(g0.alpha, g0.dhat_u0, "-v", ms=4, color=style.OKABE_ITO[1],
            label=r"no uncles ($\eta=0$)")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel(r"$\hat D / D^*$ (estimator deflation)")
    ax.set_title(r"About half the repair fig13's $\eta=1$ implies")
    ax.legend(fontsize=7, loc="lower left")

    style.save(fig, FIGS / "fig36_countable_selfish", provenance="scripts/countable_selfish.py")
    plt.close(fig)


def reorg_ceilings() -> pd.DataFrame:
    """The same ceiling for the *depth*-maximising adversary of §6.10, for cross-reference.

    A depth-``d`` reorg discards ``d`` consecutive public blocks — one chain, one countable uncle.
    Reported at the honest fork rate ``o = 0`` and at the measured Blend value ``o = 0.35``, which
    inflates the adversary's effective share and so its reorg depths.
    """
    rows = []
    for o in (0.0, 0.35):
        for alpha in (0.10, 0.20, 0.30):
            ae = alpha_effective(alpha, o)
            depths = simulate_deepest_reorg(ae, 4_000_000, np.random.default_rng(5))
            rows.append(dict(alpha=alpha, orphan_rate=o, alpha_eff=ae, attacks=int(depths.size),
                             mean_depth=float(depths.mean()),
                             eta_countable=countable_recovery_from_depths(depths)))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "countable_selfish_reorg.parquet")
    print("\n=== depth-maximising adversary (§6.10) — same first-fork ceiling ===")
    print(f"{'alpha':>6} {'o':>5} {'a_eff':>7} {'E[d]':>6} {'eta_cnt':>8}")
    for _, r in out.iterrows():
        print(f"{r.alpha:6.2f} {r.orphan_rate:5.2f} {r.alpha_eff:7.4f} {r.mean_depth:6.3f} "
              f"{r.eta_countable:8.4f}")
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reuse", action="store_true",
                    help="re-render from runs/countable_selfish.parquet instead of re-solving the "
                         "MDP (the solve is ~15 min; the figure is not)")
    args = ap.parse_args()

    cached = RUNS / "countable_selfish.parquet"
    if args.reuse and cached.exists():
        print(f"=== re-rendering from {cached.name} ===")
        df = pd.read_parquet(cached)
    else:
        print(f"=== countable recovery under a selfish adversary (MDP cap={CAP}) ===")
        df = sweep()
        reorg_ceilings()
    report(df)
    fig36(df)
    print("wrote fig36_countable_selfish")


if __name__ == "__main__":
    main()
