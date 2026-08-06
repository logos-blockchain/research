"""What the DEPLOYED chain would read at the spec's own operating point — handoff E1/E2/E6.

The report measures the mechanism: it drives the estimator to exact `f`, so its numbers isolate
fork loss from every other effect. That is the right default for design questions and the wrong
one for "what will the deployed chain read", because the spec's estimator quantises the target
rate — `cryptarchia-total-stake-inference.md` carries `const PRECISION: u64 = 1e3`, so
`f_p = 0.033` at `f = 1/30` and the recursion drives density to a target ~1 % below `f`.

E1 pins the operating point from `analysis-block-times-blend-network.md`: `blending_delay` is a
FIXED per-hop dwell of 2 s (the `3d+5` max-delay arithmetic gives 11 s at d=2 and 14 s at d=3,
matching the prose), so the simulator's `Uniform(0, delta_max)` matches it in the mean at
`delta_max = 4` -> `D_vis ~ 8 s`, `rho ~ 0.27`.

Three arms, everything else identical:

    exact f   fixed_point=False              the report's convention        -> expect 1.000
    spec      fixed_point=True, 1e3          what the chain does today      -> expect ~1.010
    proposed  fixed_point=True, 1e6          the report's recommendation    -> expect ~1.00001

The point of running rather than quoting `theory.fixed_point_bias`: the closed form predicts the
offset in isolation, and this confirms it survives the full per-node dynamics at the deployment's
actual load, alongside the fork loss rather than instead of it.

Run:  python scripts/spec_point.py   (writes runs/spec_point.parquet)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.theory import fixed_point_bias

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

EPOCHS = 20
REPS = 20
N_JOBS = 6

# The spec's operating point (E1), with the spec's own MAX_UNCLES rather than the report's U = 2.
SPEC_POINT = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                  link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                  blend_delay_max=4.0, max_uncles=4, uncle_strategy="oldest",
                  window_absorption=10.0, k=2160, epochs=EPOCHS,
                  genesis_d_factor=0.5, early_stop=True)

ARMS = [("exact f (report convention)", False, 1_000_000),
        ("spec today (PRECISION = 1e3)", True, 1_000),
        ("recommended (PRECISION = 1e6)", True, 1_000_000)]


def _cell(label: str, fixed_point: bool, precision: int, rep: int) -> dict:
    cfg = SimConfig(**SPEC_POINT, fixed_point=fixed_point, f_precision=precision, replicate=rep)
    t = pd.DataFrame(run_trajectory(cfg))
    t = t[t.epoch >= t.epoch.max() // 2]
    return dict(arm=label, fixed_point=fixed_point, f_precision=precision, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()),
                fork_rate=float(t.fork_rate.mean()),
                p_ref=float(t.p_ref.mean()),
                range_ratio=float(t.range_ratio.max()))


def main() -> None:
    print("=== the spec's operating point: delta_max = 4, D_vis ~ 8 s, rho ~ 0.27, U = 4 ===")
    jobs = [(lab, fp, pr, r) for lab, fp, pr in ARMS for r in range(REPS)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(_cell)(lab, fp, pr, r) for lab, fp, pr, r in jobs))
    df.to_parquet(RUNS / "spec_point.parquet", index=False)

    f = SimConfig(**SPEC_POINT).f
    print(f"\n{'arm':>32} {'D-hat/D':>18} {'predicted':>10} {'consensus':>10}")
    for lab, fp, pr in ARMS:
        g = df[df.arm == lab]
        pred = fixed_point_bias(f, pr) if fp else 1.0
        print(f"{lab:>32} {g.mean_ratio.mean():10.5f}+-{g.mean_ratio.sem():.5f} "
              f"{pred:10.5f} {('exact' if g.range_ratio.max() == 0 else 'SPREAD'):>10}")
    print(f"\nfork rate {df.fork_rate.mean():.3f}, p_ref {df.p_ref.mean():.4f}, "
          f"{REPS} replicates, k = 2160")
    print(f"wrote {RUNS}/spec_point.parquet")


if __name__ == "__main__":
    main()
