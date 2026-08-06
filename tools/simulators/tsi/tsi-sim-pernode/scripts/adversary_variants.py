"""The residual §6.5-scope adversary variants — REPORT §8.3 item 11.

Three probes the robustness studies left open, each asking whether a bound reported as
best-case-for-the-defender actually moves:

  A. WHALE COALITION   — §6.5 flags that a coalition of a few large holders has a "lumpier share
     statistic" than a random one at the same stake. Both arms hold the same stake fraction
     (engine._adversary_mask fills whales-first up to the target, so the realised shares match);
     what differs is the member count, hence the run-to-run spread of the coalition's realised
     block share. Measured for both levers: uncle suppression (§6.3) and withholding (§6.4).

  B. JITTER > 0        — the dynamic withhold-rejoin results (§6.5) were all run at jitter = 0.
     §6.1 shows jitter never reaches the finalized density window in the HONEST case; this asks
     the same of the attacked case. Run in the guaranteed-exact mode (windowed fork choice and
     arrival pruning off), since those speed-ups are only bit-exact at jitter = 0.

  C. VERY SLOW beta    — §6.5 sweeps the estimator gain down to beta = 0.25. "Very slow" beta is
     listed as untested: with memory ~1/beta epochs, beta = 0.05 remembers ~20 epochs, so a
     withhold notch should shrink further while the attacker's take stays flat (profitability is
     beta-independent, §6.5(iii)). This checks that the trend continues rather than turning.

Run:  python scripts/adversary_variants.py   (writes runs/adversary_variants_*.parquet)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.memguard import ArrivalMatrixTooLarge

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

EPOCHS = 20
REPS = 12
N_JOBS = 6

# §6.4's own withhold geometry (blend_delay_max = 4), so the concentration comparison is
# like-for-like against the published withhold/suppress numbers rather than at a heavier load.
# The heavier point is probed separately by study_withhold_load, where it does something else
# entirely — see that function.
WHALE_BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                  link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                  blend_delay_max=4.0, max_uncles=2, uncle_window=300, k=256,
                  epochs=EPOCHS, genesis_d_factor=0.5)

# §6.5 cell geometry: equal stakes so coalition_frac == adversary_frac exactly, light transport
# so the dynamic lever is measured on its own rather than through fork noise.
DYN_BASE = dict(n_nodes=600, stake_dist="uniform", topology="regular", degree=8,
                link_latency_mean=0.3, link_latency_dist="geo", max_uncles=2, uncle_window=300,
                genesis_d_factor=0.5, k=64, adversary_strategy="withhold",
                adversary_frac=0.3, adversary_period=6, adversary_withhold_epochs=3)


def _tail(cfg: SimConfig) -> pd.DataFrame:
    """One trajectory, burn-in discarded (the report's 50 % convention)."""
    df = pd.DataFrame(run_trajectory(cfg))
    return df[df.epoch >= cfg.epochs // 2]


def _tail_or_collapse(cfg: SimConfig) -> tuple[pd.DataFrame | None, bool]:
    """``(tail, collapsed)``. A run whose estimate falls into the §6.2 collapsed branch produces
    blocks at up to one per node per slot, so the arrival matrix blows past the memory guard and
    :class:`ArrivalMatrixTooLarge` is raised. That is a *result*, not an error — dropping the cell
    would silently bias a mean upward — so it is caught and reported as a collapse.
    """
    try:
        return _tail(cfg), False
    except ArrivalMatrixTooLarge:
        return None, True


def study_whale() -> pd.DataFrame:
    def cell(badv: float, selection: str, strategy: str, rep: int) -> dict:
        t, collapsed = _tail_or_collapse(
            SimConfig(adversary_frac=badv, adversary_selection=selection,
                      adversary_strategy=strategy, replicate=rep, **WHALE_BASE))
        row = dict(beta_adv=badv, selection=selection, strategy=strategy, rep=rep,
                   collapsed=collapsed)
        if t is not None:
            row |= dict(mean_ratio=float(t.mean_ratio.mean()),
                        adv_block_share=float(t.adv_block_share.mean()))
        return row

    jobs = [(b, s, st, r) for b in (0.1, 0.3, 0.5) for s in ("random", "whale")
            for st in ("suppress", "withhold") for r in range(REPS)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(cell)(b, s, st, r) for b, s, st, r in jobs))
    df.to_parquet(RUNS / "adversary_variants_whale.parquet", index=False)
    return df


def study_jitter() -> pd.DataFrame:
    def cell(jitter: float, rep: int) -> dict:
        # jitter > 0 makes the windowed/pruned engine an approximation, so use the exact oracle.
        t = _tail(SimConfig(jitter_mean=jitter, replicate=rep,
                            windowed_fork_choice=False, prune_arrival=False,
                            epochs=EPOCHS, **DYN_BASE))
        return dict(jitter_mean=jitter, rep=rep,
                    mean_ratio=float(t.mean_ratio.mean()),
                    notch=float(t.mean_ratio.max() - t.mean_ratio.min()),
                    adv_block_share=float(t.adv_block_share.mean()),
                    range_ratio=float(t.range_ratio.max()))

    jobs = [(j, r) for j in (0.0, 0.3, 1.0) for r in range(8)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(cell)(j, r) for j, r in jobs))
    df.to_parquet(RUNS / "adversary_variants_jitter.parquet", index=False)
    return df


def study_slow_beta() -> pd.DataFrame:
    def cell(beta: float, rep: int) -> dict:
        t = _tail(SimConfig(beta=beta, replicate=rep, epochs=40, **DYN_BASE))
        return dict(beta=beta, rep=rep,
                    mean_ratio=float(t.mean_ratio.mean()),
                    notch=float(t.mean_ratio.max() - t.mean_ratio.min()),
                    adv_block_share=float(t.adv_block_share.mean()))

    jobs = [(b, r) for b in (1.0, 0.25, 0.1, 0.05) for r in range(8)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(cell)(b, r) for b, r in jobs))
    df.to_parquet(RUNS / "adversary_variants_beta.parquet", index=False)
    return df


def study_withhold_load() -> pd.DataFrame:
    """D. Does static withholding reach the §6.2 fold? (unplanned — found by A blowing up.)

    §6.2 fits a static feedback map that folds into a collapsed low branch at `rho ~ 1.08`, and
    records that the full per-node dynamics never get there. But the same section gives the
    mechanism that would take them there: the realised load is `rho_eff = rho / r`, so an
    estimate deflated to `r` multiplies the load by `1/r`. Withholding deflates `r` to about
    `1 - beta_adv` BY DESIGN (§6.4), so a 50 % coalition doubles the load — and at the design
    point `rho ~ 0.56` that lands on `rho_eff ~ 1.1`, past the fold.

    This sweeps the blending budget under static withholding at `beta_adv` 0.3/0.5 — for BOTH
    coalition selections, since the one observed collapse was a whale cell — and records how often
    the estimate collapses, which is the direct test of "never reached in the dynamics".
    """
    def cell(badv: float, delay: float, selection: str, rep: int) -> dict:
        cfg = SimConfig(**{**WHALE_BASE, "blend_delay_max": delay},
                        adversary_frac=badv, adversary_strategy="withhold",
                        adversary_selection=selection, replicate=rep)
        t, collapsed = _tail_or_collapse(cfg)
        row = dict(beta_adv=badv, blend_delay_max=delay, selection=selection, rep=rep,
                   collapsed=collapsed)
        if t is not None:
            row |= dict(mean_ratio=float(t.mean_ratio.mean()),
                        min_ratio=float(t.mean_ratio.min()),
                        adv_block_share=float(t.adv_block_share.mean()))
        return row

    jobs = [(b, d, s, r) for b in (0.3, 0.5) for d in (4.0, 8.0)
            for s in ("random", "whale") for r in range(REPS)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(cell)(b, d, s, r) for b, d, s, r in jobs))
    df.to_parquet(RUNS / "adversary_variants_withhold_load.parquet", index=False)
    return df


def _report_withhold_load(df: pd.DataFrame) -> None:
    print("\n=== D. static withholding vs the §6.2 fold (rho_eff = rho / r) ===")
    print(f"{'b_adv':>6} {'delta':>6} {'sel':>7} {'collapsed':>10} {'D-hat/D':>18} "
          f"{'worst epoch':>12}")
    for badv in sorted(df.beta_adv.unique()):
        for delay in sorted(df.blend_delay_max.unique()):
            for sel in sorted(df.selection.unique()):
                g = df[(df.beta_adv == badv) & (df.blend_delay_max == delay)
                       & (df.selection == sel)]
                ok = g[~g.collapsed]
                mr = (f"{ok.mean_ratio.mean():8.4f}+-{ok.mean_ratio.std(ddof=1):.4f}"
                      if len(ok) > 1 else f"{'n/a':>16}")
                worst = f"{ok.min_ratio.min():12.4f}" if len(ok) else f"{'n/a':>12}"
                print(f"{badv:6.1f} {delay:6.1f} {sel:>7} {int(g.collapsed.sum()):5d}/{len(g):<4d}"
                      f" {mr} {worst}")


def _report_whale(df: pd.DataFrame) -> None:
    print("\n=== A. whale vs random coalition (same stake, far fewer members) ===")
    print(f"{'strategy':>9} {'b_adv':>6} {'sel':>7} {'D-hat/D':>16} {'adv block share':>20}")
    for strategy in ("suppress", "withhold"):
        for badv in (0.1, 0.3, 0.5):
            for sel in ("random", "whale"):
                g = df[(df.strategy == strategy) & (df.beta_adv == badv) & (df.selection == sel)]
                print(f"{strategy:>9} {badv:6.1f} {sel:>7} "
                      f"{g.mean_ratio.mean():8.4f}+-{g.mean_ratio.std(ddof=1):.4f} "
                      f"{g.adv_block_share.mean():12.4f}+-{g.adv_block_share.std(ddof=1):.4f}")


def _report_simple(df: pd.DataFrame, key: str, title: str) -> None:
    print(f"\n=== {title} ===")
    cols = [c for c in ("mean_ratio", "notch", "adv_block_share", "range_ratio") if c in df]
    agg = df.groupby(key)[cols].agg(["mean", "std"])
    print(agg.round(4).to_string())


def main() -> None:
    print("=== residual adversary variants (report §8.3 item 11) ===")
    _report_whale(study_whale())
    _report_simple(study_jitter(), "jitter_mean", "B. dynamic withhold-rejoin under jitter")
    _report_simple(study_slow_beta(), "beta", "C. dynamic withhold-rejoin at very slow beta")
    _report_withhold_load(study_withhold_load())
    print(f"\nwrote {RUNS}/adversary_variants_{{whale,jitter,beta,withhold_load}}.parquet")


if __name__ == "__main__":
    main()
