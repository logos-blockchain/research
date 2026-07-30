"""Honest stake churn (TSI tracks active stake) and the emergent p_ref metric."""

from __future__ import annotations

import pandas as pd

from tsi_sim.config import SimConfig
from tsi_sim.engine import _churn_active_fraction, run_trajectory

BASE = dict(n_nodes=400, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=4.0,
            max_uncles=2, uncle_window=300, k=256, epochs=16, genesis_d_factor=0.5)


def test_churn_schedule_shapes():
    sine = SimConfig(**BASE, churn_amp=0.3, churn_period=4, churn_mode="sine")
    assert _churn_active_fraction(sine, 0) == 1.0            # cos(0)=1 -> no drop
    assert abs(_churn_active_fraction(sine, 2) - 0.7) < 1e-9  # trough at half period
    ramp = SimConfig(**BASE, churn_amp=0.3, churn_period=4, churn_mode="ramp")
    assert abs(_churn_active_fraction(ramp, 4) - 0.7) < 1e-9
    assert abs(_churn_active_fraction(ramp, 8) - 0.7) < 1e-9  # holds after ramp
    step = SimConfig(**BASE, churn_amp=0.3, churn_period=4, churn_mode="step")
    assert _churn_active_fraction(step, 3) == 1.0
    assert abs(_churn_active_fraction(step, 4) - 0.7) < 1e-9


def test_churn_zero_is_bit_identical():
    off = pd.DataFrame(run_trajectory(SimConfig(**BASE)))
    z = pd.DataFrame(run_trajectory(SimConfig(**BASE, churn_amp=0.0)))
    assert (off.mean_ratio.to_numpy() == z.mean_ratio.to_numpy()).all()


def test_tsi_tracks_active_stake_under_churn():
    """A step drop in active stake: D_hat/D_active stays ~1, D_hat/D_total drops to active_frac."""
    cfg = SimConfig(**{**BASE, "epochs": 20}, churn_amp=0.3, churn_period=6, churn_mode="step")
    df = pd.DataFrame(run_trajectory(cfg))
    tail = df[df.epoch >= 14]
    # D_hat/D_total tracks the reduced active fraction (~0.7)
    assert 0.6 < tail.mean_ratio.mean() < 0.8
    # corrected for active fraction, accuracy is ~1
    corrected = (tail.mean_ratio / tail.active_stake_frac).mean()
    assert abs(corrected - 1.0) < 0.05
    assert tail.range_ratio.max() == 0.0            # churn does not break consensus


def test_p_ref_recorded_and_high_at_recommended_window():
    cfg = SimConfig(**{**BASE, "blend_delay_max": 8.0, "uncle_window": 300})
    df = pd.DataFrame(run_trajectory(cfg))
    assert "p_ref" in df.columns
    # at a generous window, most orphans get referenced
    assert df[df.epoch >= 8].p_ref.mean() > 0.7
