"""Analytic sanity checks: simulator vs closed-form theory (``tsi-verify``).

Replicate runs are evaluated across CPU cores. Exits non-zero if any check fails.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .config import SimConfig
from .engine import run_trajectory
from .epoch import simulate_epoch
from .rng import seedseq_for
from .stake import make_stake
from .theory import block_count_ceiling, expected_ratio, fixed_point_bias

F = 1.0 / 30.0
K = 128            # scaled: T = 6*floor(128/f) = 23040 slots
EPOCHS = 45
REPS = 12
BURN = 25


def tail_mean(cfg: SimConfig, col: str, reps: int = REPS, n_jobs: int = -1) -> tuple[float, float]:
    """Mean over ``reps`` replicates of each trajectory's post-burn-in tail mean of ``col``."""
    def one(r: int) -> float:
        df = pd.DataFrame(run_trajectory(replace(cfg, replicate=r)))
        return float(df[col].iloc[BURN:].mean())

    vals = np.array(Parallel(n_jobs=n_jobs, backend="loky", inner_max_num_threads=1)(
        delayed(one)(r) for r in range(reps)
    ))
    return float(vals.mean()), float(vals.std() / np.sqrt(reps))


def check(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main() -> int:
    results = []

    # 1. Active-slot rate ~= f when D_est = D_true, L=0, U=0.
    cfg = SimConfig(n_nodes=2000, stake_dist="uniform", latency=0, max_uncles=0,
                    k=K, epochs=1, genesis_d_factor=1.0)
    ss = seedseq_for(cfg)
    children = ss.spawn(2)
    stake = make_stake(cfg, np.random.default_rng(children[0]))
    er = simulate_epoch(cfg, stake, float(stake.sum()), children[1])
    active_rate = er.n_active / cfg.period_T
    results.append(check("active-slot rate ~ f (L=0,U=0,D=D_true)",
                         abs(active_rate - F) / F < 0.05,
                         f"active_rate={active_rate:.5f} f={F:.5f}"))

    # 2. U=0 equilibrium ratio ~= expected_ratio(f, measured q).
    cfg = SimConfig(n_nodes=1000, stake_dist="uniform", latency=4, max_uncles=0,
                    k=K, epochs=EPOCHS, genesis_d_factor=0.5)
    ratio, se = tail_mean(cfg, "ratio")
    q, _ = tail_mean(cfg, "q")
    pred = float(expected_ratio(F, q))
    results.append(check("U=0 ratio ~ theory(q)",
                         abs(ratio - pred) < 0.02 + 2 * se,
                         f"sim={ratio:.4f}±{se:.4f} theory(q={q:.3f})={pred:.4f}"))

    # 3. Underestimate at higher latency (q < 1 => ratio < 1), U=0.
    cfg = SimConfig(n_nodes=1000, stake_dist="uniform", latency=10, max_uncles=0,
                    k=K, epochs=EPOCHS, genesis_d_factor=0.5)
    ratio, se = tail_mean(cfg, "ratio")
    q, _ = tail_mean(cfg, "q")
    results.append(check("U=0 underestimates true stake at latency",
                         ratio < 0.98 and q < 0.98,
                         f"ratio={ratio:.4f} q={q:.3f}"))

    # 4. q_eff -> 1 and ratio -> block-count ceiling as U grows (uncles recover forks).
    #    The residual |ratio-1| ~ 0.017 is the intrinsic winners-vs-active-slots floor
    #    (density_m counts blocks), NOT a convergence failure -- see check 5.
    base = dict(n_nodes=1000, stake_dist="uniform", latency=8, uncle_strategy="oldest",
                k=K, epochs=EPOCHS, genesis_d_factor=0.5)
    r0, _ = tail_mean(SimConfig(max_uncles=0, **base), "ratio")
    r4, _ = tail_mean(SimConfig(max_uncles=4, **base), "ratio")
    qe4, _ = tail_mean(SimConfig(max_uncles=4, **base), "q_eff")
    results.append(check("uncles recover accuracy (q_eff->1, |ratio-1| shrinks)",
                         qe4 > 0.99 and abs(r4 - 1) < abs(r0 - 1) and abs(r4 - 1) < 0.03,
                         f"ratio U0={r0:.4f} -> U4={r4:.4f}; q_eff(U4)={qe4:.4f}"))

    # 5. Full recovery equilibrates at the block-count ceiling -ln(1-f)/f (~1.017), not 1.
    ceiling = float(block_count_ceiling(F))
    r4_val, se4 = tail_mean(SimConfig(max_uncles=4, **base), "ratio")
    results.append(check("full-recovery ratio ~ block-count ceiling",
                         abs(r4_val - ceiling) < 0.015 + 2 * se4,
                         f"ratio(U4)={r4_val:.4f} ceiling=-ln(1-f)/f={ceiling:.4f}"))

    # 6. Fixed-point mode adds the spec's ~1% f-truncation overestimate.
    fp_base = dict(n_nodes=1000, stake_dist="uniform", latency=0, max_uncles=0,
                   k=K, epochs=EPOCHS, genesis_d_factor=1.0)
    r_float, _ = tail_mean(SimConfig(fixed_point=False, **fp_base), "ratio")
    r_fixed, _ = tail_mean(SimConfig(fixed_point=True, **fp_base), "ratio")
    bias = float(fixed_point_bias(F))
    results.append(check("fixed_point mode adds ~1% f-truncation bias",
                         r_fixed > r_float and abs(r_fixed / r_float - bias) < 0.01,
                         f"float={r_float:.4f} fixed={r_fixed:.4f} ratio={r_fixed/r_float:.4f} "
                         f"expected~{bias:.4f}"))

    print()
    n_pass = sum(results)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
