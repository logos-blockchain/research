"""Dynamic (withhold-then-rejoin) grinding analysis — REPORT §6.5.

Static withholding (§6.4) deflates D_est to the active-stake line (1-beta_adv) but is
self-punishing (the coalition forfeits every withheld block). The dynamic variant abstains to
depress D_est, then re-activates to mine at the depressed difficulty. Its feasibility is set by
how fast D_est moves, i.e. the estimator gain `beta` (config.beta), since the update

    D_{t+1} = (1-beta)*D_t + beta * S_t * D*                          (exact, leading order)

is an EMA of the active-stake signal S_t*D* with memory ~1/beta epochs (S_t = active fraction,
D* = honest-equilibrium estimate). Four studies:

  1. SAWTOOTH + EMA LAW   — D_est(t) trajectory vs beta, overlaid with the EMA prediction (fig10)
  2. PROFITABILITY        — realized reward / stake share vs withhold duty and beta_adv (fig11)
  3. GRIEFING FRONTIER    — estimator distortion achieved vs reward forfeited (fig11, right)
  4. TIPPING near rho~=1  — does a withhold PULSE recover, or tip into the §6.2 collapsed
                            branch and stay deflated (self-sustaining)?                 (fig12)

Run:  python scripts/dynamic_withhold.py   (writes runs/dynamic_withhold_*.parquet + fig10-12)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.plotting import style

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

# equal stakes => coalition_frac == adversary_frac EXACTLY (clean parametric control of beta_adv)
BASE = dict(n_nodes=1000, stake_dist="uniform", topology="regular", degree=8,
            link_latency_mean=0.3, link_latency_dist="geo", max_uncles=2, uncle_window=300,
            genesis_d_factor=0.5, k=64, adversary_strategy="withhold")


def traj(reps: int, **cfg) -> pd.DataFrame:
    """Run `reps` replicates of one config, tagged with replicate id."""
    out = []
    for r in range(reps):
        df = pd.DataFrame(run_trajectory(SimConfig(replicate=r, **cfg)))
        out.append(df)
    return pd.concat(out, ignore_index=True)


def honest_equilibrium(beta: float, reps: int = 4, **over) -> float:
    """Honest-run tail-mean D_est/D_true (the level D*/D_true the EMA relaxes toward)."""
    kw = {**BASE, **over}
    kw.pop("adversary_strategy", None)
    df = traj(reps, epochs=20, beta=beta, adversary_frac=0.0, **kw)
    return float(df[df.epoch >= 12].mean_ratio.mean())


# ---------------------------------------------------------------------------------------------
# STUDY 1 — sawtooth trajectory + EMA-law overlay
# ---------------------------------------------------------------------------------------------
def study1_sawtooth() -> pd.DataFrame:
    betas = [0.25, 0.5, 1.0]
    period, wh = 6, 3          # 50% duty, wide on/off blocks so the sawtooth shape is visible
    epochs, reps, badv = 42, 6, 0.3
    rows = []
    for beta in betas:
        df = traj(reps, epochs=epochs, beta=beta, adversary_frac=badv,
                  adversary_period=period, adversary_withhold_epochs=wh, **BASE)
        g = df.groupby("epoch")
        d_hat = g.mean_ratio.mean().to_numpy()
        active = g.active_stake_frac.mean().to_numpy()          # 1 or (1-badv) per epoch
        rstar = honest_equilibrium(beta)
        # EMA prediction: D_hat[t] = (1-beta)*D_hat[t-1] + beta*S_t*D*, seeded from genesis. The
        # end-of-epoch-t estimate uses THIS epoch's active fraction active[t] (not active[t-1]).
        pred = np.empty(epochs)
        prev = BASE["genesis_d_factor"]
        for t in range(epochs):
            pred[t] = (1 - beta) * prev + beta * active[t] * rstar
            prev = pred[t]
        for t in range(epochs):
            rows.append(dict(beta=beta, epoch=t, d_hat=d_hat[t], active=active[t],
                             ema_pred=pred[t], rstar=rstar))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "dynamic_withhold_sawtooth.parquet")
    rms = float(np.sqrt(((out.d_hat - out.ema_pred) ** 2)[out.epoch >= 3].mean()))
    print(f"[S1] sawtooth: EMA-law RMS(D_hat - pred), epoch>=3 = {rms:.4f}")
    for beta in betas:
        s = out[(out.beta == beta) & (out.epoch >= 12)]
        lo, hi = s.d_hat.min(), s.d_hat.max()
        print(f"     beta={beta}: swing D_hat in [{lo:.3f}, {hi:.3f}]  amplitude={hi-lo:.3f}")
    return out


# ---------------------------------------------------------------------------------------------
# STUDY 2 + 3 — profitability and griefing frontier
# ---------------------------------------------------------------------------------------------
# duty psi -> (period, withhold_epochs); 0.0 anchor is "never withhold" (always participate)
SCHEDULES = [
    ("never", 0.0, None),
    ("p10/1", 0.10, (10, 1)),
    ("p4/1", 0.25, (4, 1)),
    ("p3/1", 1 / 3, (3, 1)),
    ("p2/1", 0.50, (2, 1)),
    ("p3/2", 2 / 3, (3, 2)),
    ("p4/3", 0.75, (4, 3)),
    ("static", 1.0, (1, 1)),
]


def _reward_over_stake(df: pd.DataFrame, badv: float, burn: int) -> float:
    t = df[df.epoch >= burn]
    total = float((t.adv_blocks + t.honest_blocks).sum())
    return float(t.adv_blocks.sum() / (badv * total)) if total else float("nan")


def study2_profitability() -> pd.DataFrame:
    epochs, reps, burn = 26, 8, 12
    rows = []
    # (a) duty x beta at beta_adv = 0.3
    for beta in (0.5, 1.0):
        for label, psi, sched in SCHEDULES:
            if sched is None:                          # never withhold == honest participation
                df = traj(reps, epochs=epochs, beta=beta, adversary_frac=0.3,
                          adversary_strategy="suppress",
                          **{k: v for k, v in BASE.items() if k != "adversary_strategy"})
            else:
                p, w = sched
                df = traj(reps, epochs=epochs, beta=beta, adversary_frac=0.3,
                          adversary_period=p, adversary_withhold_epochs=w, **BASE)
            ros = _reward_over_stake(df, 0.3, burn)
            distortion = float(1.0 - df[df.epoch >= burn].mean_ratio.mean())   # mean deflation
            rows.append(dict(kind="duty", beta=beta, badv=0.3, label=label, duty=psi,
                             reward_over_stake=ros, distortion=distortion))
            print(f"[S2] beta={beta} badv=0.30 {label:7s} duty={psi:.2f}  "
                  f"reward/stake={ros:.3f}  distortion={distortion:.3f}")
    # (b) beta_adv sweep at the alternate schedule (period2/wh1), beta=1
    for badv in (0.1, 0.2, 0.3, 0.4):
        df = traj(reps, epochs=epochs, beta=1.0, adversary_frac=badv,
                  adversary_period=2, adversary_withhold_epochs=1, **BASE)
        ros = _reward_over_stake(df, badv, burn)
        rows.append(dict(kind="badv", beta=1.0, badv=badv, label="p2/1", duty=0.5,
                         reward_over_stake=ros, distortion=float(1 - df[df.epoch >= burn]
                                                                 .mean_ratio.mean())))
        print(f"[S2b] beta=1.0 badv={badv:.2f} alternate  reward/stake={ros:.3f}")
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "dynamic_withhold_profit.parquet")
    return out


# ---------------------------------------------------------------------------------------------
# STUDY 4 — tipping: does a withhold PULSE recover or trap the estimator?
# ---------------------------------------------------------------------------------------------
def study4_tipping() -> pd.DataFrame:
    # Push the operating load rho = f * D_vis up via block rate f AND mixnet delay, then apply a
    # short withhold pulse and watch whether D_est recovers to the honest level or stays collapsed.
    epochs, reps, pulse, badv = 34, 5, 4, 0.4
    base = dict(n_nodes=400, stake_dist="uniform", topology="blend", degree=8,
                link_latency_mean=0.3, link_latency_dist="geo", blend_hops=4,
                max_uncles=2, uncle_window=300, genesis_d_factor=0.6, k=32,
                adversary_strategy="withhold")
    # operating points from mild to aggressive load
    points = [
        ("f=1/30 d=6", dict(f=1 / 30, blend_delay_max=6.0)),
        ("f=1/15 d=12", dict(f=1 / 15, blend_delay_max=12.0)),
        ("f=1/10 d=18", dict(f=1 / 10, blend_delay_max=18.0)),
        ("f=1/10 d=30", dict(f=1 / 10, blend_delay_max=30.0)),
    ]
    rows = []
    for label, over in points:
        # honest reference (no pulse)
        hon = traj(reps, epochs=epochs, beta=1.0, adversary_frac=0.0,
                   **{**base, **over, "adversary_strategy": "suppress"})
        hon_g = hon.groupby("epoch").mean_ratio.mean()
        # pulse: withhold first `pulse` epochs, honest forever after
        pul = traj(reps, epochs=epochs, beta=1.0, adversary_frac=badv,
                   adversary_period=epochs, adversary_withhold_epochs=pulse, **{**base, **over})
        pul_g = pul.groupby("epoch").mean_ratio.mean()
        hon_eq = float(hon_g[hon_g.index >= epochs - 8].mean())
        post = float(pul_g[pul_g.index >= epochs - 8].mean())           # long after the pulse
        recovered = post > 0.9 * hon_eq
        print(f"[S4] {label:14s} honest_eq={hon_eq:.3f}  post-pulse={post:.3f}  "
              f"{'RECOVERS' if recovered else 'TRAPPED (collapsed)'}")
        for t in range(epochs):
            rows.append(dict(point=label, epoch=t, honest=float(hon_g.get(t, np.nan)),
                             pulse=float(pul_g.get(t, np.nan)), hon_eq=hon_eq,
                             recovered=recovered, pulse_len=pulse))
    out = pd.DataFrame(rows)
    out.to_parquet(RUNS / "dynamic_withhold_tipping.parquet")
    return out


# ---------------------------------------------------------------------------------------------
# FIGURES
# ---------------------------------------------------------------------------------------------
def fig10(saw: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4), sharey=True)
    for ax, beta in zip(axes, sorted(saw.beta.unique()), strict=True):
        s = saw[saw.beta == beta].sort_values("epoch")
        rstar = s.rstar.iloc[0]
        ax.axhline(rstar, color="0.6", lw=0.8, ls=":", label="honest $D^*$")
        ax.axhline((1 - 0.3) * rstar, color="0.6", lw=0.8, ls="--",
                   label=r"active $(1-\beta_{adv})D^*$")
        ax.plot(s.epoch, s.d_hat, "-o", ms=3, color=style.OKABE_ITO[0], label=r"$\hat D$ (sim)")
        ax.plot(s.epoch, s.ema_pred, "-", lw=1.4, color=style.OKABE_ITO[1],
                label="EMA law")
        ax.set_title(rf"$\beta={beta}$  ($\tau={-1/np.log(1-beta):.1f}$ ep)" if beta < 1
                     else rf"$\beta={beta}$ (1-epoch)")
        ax.set_xlabel("epoch")
        ax.set_xlim(6, s.epoch.max())
    axes[0].set_ylabel(r"$\hat D / D_{\rm true}$")
    axes[0].legend(fontsize=7, loc="lower right")
    fig.suptitle(r"Dynamic withholding drives an EMA sawtooth; estimator gain $\beta$ sets its "
                 "speed & depth", y=1.02)
    style.save(fig, FIGS / "fig10_sawtooth", provenance="scripts/dynamic_withhold.py::study1")
    plt.close(fig)


def fig11(prof: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    # left: reward/stake vs duty, per beta (+ beta_adv sweep inset points)
    ax = axes[0]
    duty = prof[prof.kind == "duty"]
    for i, beta in enumerate(sorted(duty.beta.unique())):
        s = duty[duty.beta == beta].sort_values("duty")
        ax.plot(s.duty, s.reward_over_stake, "-o", ms=4, color=style.OKABE_ITO[i],
                label=rf"$\beta={beta}$")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--", label="break-even")
    ax.set_xlabel(r"withhold duty $\psi$ (fraction of epochs)")
    ax.set_ylabel(r"realized reward / stake share")
    ax.set_title(r"Dynamic withholding is unprofitable ($\beta_{adv}=0.3$)")
    ax.legend(fontsize=8)
    # right: griefing frontier — distortion achieved vs reward forfeited
    ax = axes[1]
    for i, beta in enumerate(sorted(duty.beta.unique())):
        s = duty[duty.beta == beta].sort_values("duty")
        ax.plot(1 - s.reward_over_stake, s.distortion, "-o", ms=4, color=style.OKABE_ITO[i],
                label=rf"$\beta={beta}$")
    lim = max(0.01, float((1 - duty.reward_over_stake).max()))
    ax.plot([0, lim], [0, lim], color="0.6", lw=0.8, ls=":", label="1:1 (linear cost)")
    ax.set_xlabel("reward forfeited  (1 - reward/stake)")
    ax.set_ylabel(r"mean estimator distortion  $1-\overline{\hat D/D}$")
    ax.set_title("Griefing is bounded & linearly costly")
    ax.legend(fontsize=8)
    style.save(fig, FIGS / "fig11_profitability", provenance="scripts/dynamic_withhold.py::study2")
    plt.close(fig)


def fig12(tip: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    points = list(dict.fromkeys(tip.point))
    for i, pt in enumerate(points):
        s = tip[tip.point == pt].sort_values("epoch")
        rec = bool(s.recovered.iloc[0])
        c = style.OKABE_ITO[i]
        ax.plot(s.epoch, s.pulse, "-o", ms=3, color=c,
                label=f"{pt}  {'recovers' if rec else 'TRAPPED'}")
        ax.plot(s.epoch, s.honest, "-", lw=0.8, color=c, alpha=0.35)
    plen = int(tip.pulse_len.iloc[0])
    ax.axvspan(0, plen - 1, color="0.85", label=f"withhold pulse ({plen} ep)")
    ax.set_xlabel("epoch")
    ax.set_ylabel(r"$\hat D / D_{\rm true}$")
    ax.set_title("Withhold pulse vs operating load: transient recovery or collapse-branch trap")
    ax.legend(fontsize=7, loc="lower right")
    style.save(fig, FIGS / "fig12_tipping", provenance="scripts/dynamic_withhold.py::study4")
    plt.close(fig)


def main() -> None:
    print("=== STUDY 1: sawtooth + EMA law ===")
    saw = study1_sawtooth()
    print("\n=== STUDY 2/3: profitability + griefing ===")
    prof = study2_profitability()
    print("\n=== STUDY 4: tipping near rho~=1 ===")
    tip = study4_tipping()
    print("\n=== FIGURES ===")
    fig10(saw)
    fig11(prof)
    fig12(tip)
    print("wrote fig10_sawtooth, fig11_profitability, fig12_tipping")


if __name__ == "__main__":
    main()
