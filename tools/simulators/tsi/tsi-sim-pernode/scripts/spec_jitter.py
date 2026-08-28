"""does per-recipient delay variance reproduce the standalone result? (the diagnostic).

The one fork-loss experiment that could invalidate the REPORT rather than the spec section it
is checking. The hypothesis for the original discrepancy is a modelling difference, not a
measurement one: the standalone simulation drew an independent propagation delay per
(block, recipient), whereas this simulator's Blend cascade floods network-wide from the last
relay, so nodes receive a block at nearly the same time and their views stay synchronised.
Independent per-recipient draws maximise view divergence, which is what manufactures the
depth->=2 forks the first-fork rule cannot recover.

`jitter_mean` adds per-(block, node) arrival noise on top of the cascade, so sweeping it
interpolates between the two models. The deciding observable is `deep_orphan_share`: the fraction
of in-window orphans sitting deeper than the first block of their fork — precisely the structural
quantity behind the spec section's deep-fork claim, and the thing `p_ref` conflates with
"never picked up".

Pass / fail:
  * D-hat/D holds at ~1.000 and deep orphans stay negligible as jitter rises  -> the standalone
    model was simply wrong; its numbers are artefacts and the report is robust to this failure mode.
  * accuracy degrades toward 0.986 and deep orphans reach ~1 % of blocks at some jitter level
    -> record that level and compare it to what Blend plausibly delivers; per-recipient variance
    then becomes a parameter the report must carry, and the spec section's number is defensible
    under a stated assumption.

Exact oracle throughout: the windowed fork choice and the arrival prune are bit-exact only at
jitter_mean == 0, so both are disabled and the full arrival matrix is used.

Run:  python scripts/spec_jitter.py   (writes runs/spec_jitter.parquet)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

REPS = 12
N_JOBS = 12
JITTERS = [0.0, 1.0, 2.0, 4.0, 8.0]
CAPS = [0, 1, 2, 4]

SPEC_POINT = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                  link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                  blend_delay_max=4.0, uncle_strategy="oldest", window_absorption=10.0,
                  k=2160, epochs=20, genesis_d_factor=0.5, early_stop=True,
                  windowed_fork_choice=False, prune_arrival=False,
                  uncle_window_anchor="uncle")   # SPEC AS DEPLOYED, not the §6.12 proposal


def _cell(model: str, jitter: float, u: int, rep: int) -> dict:
    cfg = SimConfig(**SPEC_POINT, uncle_model=model, jitter_mean=jitter,
                    max_uncles=u, replicate=rep)
    t = pd.DataFrame(run_trajectory(cfg))
    t = t[t.epoch >= t.epoch.max() // 2]
    return dict(model=model, jitter_mean=jitter, max_uncles=u, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()),
                fork_rate=float(t.fork_rate.mean()),
                deep_orphan_share=float(t.deep_orphan_share.mean()),
                p_ref=float(t.p_ref.mean()),
                max_reorg_depth=int(t.max_reorg_depth.max()),
                range_ratio=float(t.range_ratio.max()),
                agreement_window=float(t.agreement_window.min()))


def sweep() -> pd.DataFrame:
    jobs = [(m, j, u, r) for m in ("countable", "old") for j in JITTERS
            for u in CAPS for r in range(REPS)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(_cell)(m, j, u, r) for m, j, u, r in jobs))
    df.to_parquet(RUNS / "spec_jitter.parquet", index=False)
    return df


def report(df: pd.DataFrame) -> None:
    print("\n=== accuracy vs per-(block,node) jitter at the spec point (delta_max = 4) ===")
    print(f"{'jitter':>7} | " + "  ".join(f"U={u}" for u in CAPS)
          + f" | {'ceiling U=1':>11} {'gap':>8} {'deep orph':>10} {'fork':>6} {'consensus':>10}")
    for j in JITTERS:
        c = df[(df.model == "countable") & (df.jitter_mean == j)]
        o = df[(df.model == "old") & (df.jitter_mean == j)]
        cells = [f"{c[c.max_uncles == u].mean_ratio.mean():.4f}" for u in CAPS]
        c1 = c[c.max_uncles == 1].mean_ratio.mean()
        o1 = o[o.max_uncles == 1].mean_ratio.mean()
        deep = c[c.max_uncles == 1].deep_orphan_share.mean()
        fork = c[c.max_uncles == 1].fork_rate.mean()
        ok = "exact" if c.range_ratio.max() == 0 else "SPREAD"
        print(f"{j:7.1f} | " + "  ".join(cells)
              + f" | {o1:11.4f} {o1 - c1:+8.4f} {deep:10.4f} {fork:6.3f} {ok:>10}")
    print("\ndeep orph = share of in-window orphans below their fork's first block "
          "(uncountable by construction); gap = ceiling - countable at U=1")


def main() -> None:
    print(f"=== jitter sweep, exact oracle, {len(JITTERS)*len(CAPS)*REPS*2} runs ===")
    report(sweep())
    print(f"\nwrote {RUNS}/spec_jitter.parquet")


if __name__ == "__main__":
    main()
