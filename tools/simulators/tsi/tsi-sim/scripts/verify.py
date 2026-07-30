#!/usr/bin/env python
"""Analytic sanity checks: simulator vs closed-form theory.

Run with the project venv:  python scripts/verify.py
Exits non-zero if any check fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tsi_sim.config import SimConfig  # noqa: E402
from tsi_sim.engine import run_trajectory  # noqa: E402
from tsi_sim.epoch import simulate_epoch  # noqa: E402
from tsi_sim.rng import rng_for  # noqa: E402
from tsi_sim.stake import make_stake  # noqa: E402
from tsi_sim.theory import expected_ratio  # noqa: E402

F = 1.0 / 30.0
K = 128            # scaled: T = 6*floor(128/f) = 23040 slots
EPOCHS = 45
REPS = 12
BURN = 25


def tail_mean(cfg: SimConfig, col: str, reps: int = REPS) -> tuple[float, float]:
    vals = []
    for r in range(reps):
        df = pd.DataFrame(run_trajectory(cfg.__class__(**{**cfg.__dict__, "replicate": r})))
        vals.append(df[col].iloc[BURN:].mean())
    return float(np.mean(vals)), float(np.std(vals) / np.sqrt(reps))


def check(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main() -> int:
    results = []

    # 1. Active-slot rate ~= f when D_est = D_true, L=0, U=0.
    cfg = SimConfig(n_nodes=2000, stake_dist="uniform", latency=0, max_uncles=0,
                    k=K, epochs=1, genesis_d_factor=1.0)
    rng = rng_for(cfg)
    stake = make_stake(cfg, rng)
    er = simulate_epoch(cfg, stake, float(stake.sum()), rng)
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

    # 4. q_eff -> 1 and ratio -> ~1 as U grows (uncles recover forks).
    base = dict(n_nodes=1000, stake_dist="uniform", latency=8, uncle_strategy="oldest",
                k=K, epochs=EPOCHS, genesis_d_factor=0.5)
    r0, _ = tail_mean(SimConfig(max_uncles=0, **base), "ratio")
    r4, _ = tail_mean(SimConfig(max_uncles=4, **base), "ratio")
    qe4, _ = tail_mean(SimConfig(max_uncles=4, **base), "q_eff")
    results.append(check("uncles recover accuracy (q_eff->1, |ratio-1| shrinks)",
                         qe4 > 0.99 and abs(r4 - 1) < abs(r0 - 1) and abs(r4 - 1) < 0.03,
                         f"ratio U0={r0:.4f} -> U4={r4:.4f}; q_eff(U4)={qe4:.4f}"))

    print()
    n_pass = sum(results)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
