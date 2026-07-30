"""End-to-end statistical checks against closed-form theory (scaled k)."""

import numpy as np
import pandas as pd
import pytest

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.theory import expected_ratio

F = 1 / 30


def _tail_mean(col, **cfg):
    reps = cfg.pop("reps", 6)
    burn = cfg["epochs"] // 2
    vals = []
    for r in range(reps):
        df = pd.DataFrame(run_trajectory(SimConfig(replicate=r, **cfg)))
        vals.append(df[col].iloc[burn:].mean())
    return float(np.mean(vals))


def test_baseline_exact_without_forks():
    # No latency, no uncles: active-slot rate == f, so the estimate is unbiased.
    ratio = _tail_mean("ratio", n_nodes=1000, stake_dist="uniform", latency=0,
                       max_uncles=0, k=64, epochs=35, genesis_d_factor=0.5, reps=6)
    assert abs(ratio - 1.0) < 0.02


@pytest.mark.slow
def test_u0_matches_expected_ratio():
    cfg = dict(n_nodes=1000, stake_dist="uniform", latency=6, max_uncles=0,
               k=96, epochs=45, genesis_d_factor=0.5)
    ratio = _tail_mean("ratio", reps=8, **cfg)
    q = _tail_mean("q", reps=8, **cfg)
    assert abs(ratio - float(expected_ratio(F, q))) < 0.02


@pytest.mark.slow
def test_uncles_recover_accuracy():
    common = dict(n_nodes=1000, stake_dist="uniform", latency=8, uncle_strategy="oldest",
                  k=96, epochs=45, genesis_d_factor=0.5)
    r0 = _tail_mean("ratio", max_uncles=0, reps=8, **common)
    r4 = _tail_mean("ratio", max_uncles=4, reps=8, **common)
    qe4 = _tail_mean("q_eff", max_uncles=4, reps=8, **common)
    assert qe4 > 0.99
    assert abs(r4 - 1) < abs(r0 - 1)     # uncles reduce the error
    assert abs(r4 - 1) < 0.03            # residual is the small block-count overshoot
