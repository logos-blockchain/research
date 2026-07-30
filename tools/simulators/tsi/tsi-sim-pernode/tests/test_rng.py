import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.rng import rng_for, seedseq_for


def test_seedseq_and_rng_deterministic():
    cfg = SimConfig(k=8, epochs=3)
    a = np.random.default_rng(seedseq_for(cfg)).random(5)
    b = rng_for(cfg).random(5)
    np.testing.assert_array_equal(a, b)


def test_distinct_configs_get_distinct_streams():
    c0 = SimConfig(k=8, epochs=3, latency=0)
    c1 = SimConfig(k=8, epochs=3, latency=1)
    assert not np.array_equal(rng_for(c0).random(4), rng_for(c1).random(4))


def test_trajectory_is_order_independent_and_reproducible():
    cfg = SimConfig(n_nodes=300, topology="regular", degree=8, k=8, epochs=6,
                    link_latency_mean=2.0, max_uncles=2)
    r1 = run_trajectory(cfg)
    r2 = run_trajectory(cfg)
    assert [row["mean_ratio"] for row in r1] == [row["mean_ratio"] for row in r2]


def test_replicates_differ():
    a = run_trajectory(SimConfig(n_nodes=300, topology="regular", k=8, epochs=6,
                                 link_latency_mean=2.0, replicate=0))
    b = run_trajectory(SimConfig(n_nodes=300, topology="regular", k=8, epochs=6,
                                 link_latency_mean=2.0, replicate=1))
    assert a[-1]["mean_ratio"] != b[-1]["mean_ratio"]
