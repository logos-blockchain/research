import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.latency import FixedSlotLatency, RealisticLatency, make_latency


def test_fixed_slot_latency():
    lat = FixedSlotLatency(3)
    assert lat.visible_at(10, np.random.default_rng(0)) == 13


def test_realistic_latency_zero_mean_immediate():
    lat = RealisticLatency(0.0)
    assert lat.visible_at(5, np.random.default_rng(0)) == 5


def test_realistic_latency_positive_delays():
    lat = RealisticLatency(4.0)
    rng = np.random.default_rng(0)
    vals = [lat.visible_at(100, rng) for _ in range(200)]
    assert all(v >= 101 for v in vals)       # strictly after production
    assert np.mean([v - 100 for v in vals]) > 1.0


def test_make_latency_dispatch():
    assert isinstance(make_latency(SimConfig(latency=2)), FixedSlotLatency)
    assert isinstance(make_latency(SimConfig(latency=2, latency_stochastic=True)), RealisticLatency)


def test_stochastic_latency_integration_runs():
    cfg = SimConfig(n_nodes=500, k=8, epochs=5, latency=6, latency_stochastic=True, max_uncles=2)
    rows = run_trajectory(cfg)
    assert len(rows) == 5
    assert all(np.isfinite(r["ratio"]) for r in rows)
