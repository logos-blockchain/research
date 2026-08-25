"""How far can a PROFITABLE adversary deflate the estimate? — REPORT §8.3 item 16 (fig37).

§6.6 measures the countable recovery ceiling under two adversaries, and both optimise something
other than the estimator: revenue (the SSZ objective) and reorg depth. Item 16 recorded the
consequence — those are upper bounds on `eta`, not lower bounds on the damage — and asked what an
adversary optimising deflation directly would do.

Two answers, because the obvious question is the wrong one:

  * **Unconstrained**, the deflation optimum is pure abstention: publish nothing, adopt when
    overtaken, drive `D_hat` to exactly `1 - alpha` and revenue to zero. §6.4 already covers this
    and shows it is *correct* measurement — a coalition that publishes nothing is not
    participating, so `1 - alpha` is the right answer for the stake that is.
  * **Constrained to stay paid**, the question bites. Sweeping the mixed objective
    `lam * (adversary blocks) - (contribution to D_hat)` traces the profit/deflation frontier;
    the point of interest is where the revenue *share* reaches `alpha`, i.e. where the adversary
    does no worse than mining honestly. Everything below that line is self-punishing griefing,
    already bounded by §6.5.

The headline: at `alpha = 0.4` an adversary content with break-even revenue pushes `D_hat` to
~0.64, against the revenue-optimal policy's 0.81. The revenue-optimal adversary is not the
estimator's worst case, and the gap is free — it costs only the selfish premium.

Note the sweep parameter is not monotone in revenue: selfish mining wins a larger share of a
*smaller* pie, so raw adversary block rate is maximised by honest mining and large `lam` returns
there. That is fine — the sweep is used to enumerate candidate policies and their measured
(share, `D_hat`) pairs, not as a monotone path, and any point on it is a legitimate strategy.

Run:  python scripts/deflation_frontier.py   (writes runs/deflation_frontier.parquet + fig37)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.selfish_mdp import deflation_frontier, deflation_optimal_stats, optimal_policy_stats

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

CAP = 64
GAMMA = 0.0
ALPHAS = [0.30, 1 / 3, 0.36, 0.38, 0.40, 0.42, 0.45]
LAMS = [round(x, 2) for x in np.arange(0.0, 3.05, 0.1)]


def sweep() -> pd.DataFrame:
    rows = []
    for a in ALPHAS:
        ro = optimal_policy_stats(a, GAMMA, cap=CAP)
        do = deflation_optimal_stats(a, GAMMA, cap=CAP)
        for lam in LAMS:
            r = deflation_frontier(a, GAMMA, lam, cap=CAP)
            r |= dict(revenue_optimal=ro.revenue,
                      dhat_revenue_optimal=ro.dhat_ratio(1.0, True) if ro.deviates else 1.0,
                      dhat_abstention=do.dhat_ratio(1.0, True))
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_parquet(RUNS / "deflation_frontier.parquet", index=False)
    return df


def best_profitable(df: pd.DataFrame) -> pd.DataFrame:
    """Per alpha, the frontier point minimising D_hat among those that actually pay.

    "Pays" means ABSOLUTE reward per unit time at least matching honest mining
    (``pay_vs_honest >= 1``), not merely a revenue *share* at least matching stake. The two
    differ by ``density / dhat``: the share's denominator is the canonical block rate, but the
    pay rate is set by the estimator, which holds counted density at ``f`` per slot. Using the
    share alone credits the attacker with pay it does not receive — at alpha = 0.36 it marks
    points as break-even that are ~5 % short.
    """
    out = []
    for _a, g in df.groupby("alpha"):
        paid = g[g.pay_vs_honest >= 1.0 - 1e-9]
        if paid.empty:
            continue
        out.append(paid.loc[paid.dhat_countable.idxmin()])
    return pd.DataFrame(out)


def report(df: pd.DataFrame) -> None:
    best = best_profitable(df)
    print(f"{'alpha':>6} {'rev-opt rev':>12} {'rev-opt D':>10} | "
          f"{'best paid rev':>14} {'pay/hon':>8} {'D':>7} {'extra deflation':>16}")
    for a, g in df.groupby("alpha"):
        ro_r, ro_d = g.revenue_optimal.iloc[0], g.dhat_revenue_optimal.iloc[0]
        b = best[best.alpha == a]
        if b.empty:
            print(f"{a:6.3f} {ro_r:12.4f} {ro_d:10.4f} |  (no policy in the sweep both pays "
                  f"and deflates)")
            continue
        b = b.iloc[0]
        print(f"{a:6.3f} {ro_r:12.4f} {ro_d:10.4f} | {b.revenue:14.4f} "
              f"{b.pay_vs_honest:8.3f} {b.dhat_countable:7.4f} {ro_d - b.dhat_countable:+16.4f}")
    print("\n(extra deflation > 0 means the paying-but-deflating policy beats the revenue-optimal "
          "one at damaging the estimate, at no cost versus honest mining; 'pay/hon' is ABSOLUTE "
          "reward per unit time, not revenue share)")


def fig37(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    # LEFT: the frontier itself for a few alphas — revenue share against the estimate
    ax = axes[0]
    for i, a in enumerate([0.36, 0.40, 0.45]):
        g = df[np.isclose(df.alpha, a)].sort_values("lam")
        c = style.OKABE_ITO[i + 1]
        ax.plot(g.revenue, g.dhat_countable, "-o", ms=3, color=c, label=rf"$\alpha={a}$")
        ax.axvline(a, color=c, lw=0.7, ls=":")
        ro = g.dhat_revenue_optimal.iloc[0]
        ax.plot([g.revenue_optimal.iloc[0]], [ro], "*", ms=11, color=c)
    ax.set_xlabel("adversary revenue share (dotted line = its stake, i.e. break-even)")
    ax.set_ylabel(r"$\hat D / D^*$")
    ax.set_title("Profit/deflation frontier (★ = revenue-optimal)")
    ax.legend(fontsize=7, loc="lower right")

    # RIGHT: how much worse the estimator gets once the adversary stops maximising revenue
    ax = axes[1]
    best = best_profitable(df).sort_values("alpha")
    ref = df.groupby("alpha").agg(d_ro=("dhat_revenue_optimal", "first"),
                                  d_ab=("dhat_abstention", "first")).reset_index()
    ax.plot(ref.alpha, ref.d_ro, "-*", ms=9, color=style.OKABE_ITO[2],
            label="revenue-optimal (§6.6)")
    ax.plot(best.alpha, best.dhat_countable, "-o", ms=4, color=style.OKABE_ITO[3],
            label="best deflation at break-even pay")
    ax.plot(ref.alpha, ref.d_ab, "--v", ms=4, color=style.OKABE_ITO[1],
            label=r"abstention ($1-\alpha$, unpaid)")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--")
    ax.set_xlabel(r"adversary stake $\alpha$")
    ax.set_ylabel(r"$\hat D / D^*$")
    ax.set_title("The revenue-optimal adversary is not the worst case")
    ax.legend(fontsize=7, loc="lower left")

    style.save(fig, FIGS / "fig37_deflation_frontier", provenance="scripts/deflation_frontier.py")
    plt.close(fig)


def main() -> None:
    print(f"=== profit/deflation frontier (MDP cap={CAP}, gamma={GAMMA}) ===")
    df = sweep()
    report(df)
    fig37(df)
    print("wrote fig37_deflation_frontier")


if __name__ == "__main__":
    main()
