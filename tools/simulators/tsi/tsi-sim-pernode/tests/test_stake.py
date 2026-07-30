import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.stake import make_stake


def _rng():
    return np.random.default_rng(0)


def test_uniform_equal_and_sum():
    cfg = SimConfig(n_nodes=100, stake_dist="uniform", total_stake=1e9)
    w = make_stake(cfg, _rng())
    assert w.shape == (100,)
    assert np.allclose(w, w[0])                       # equal weights
    assert abs(w.sum() - 1e9) < 1e-3


def test_uniform_random_varies_but_sums():
    cfg = SimConfig(n_nodes=200, stake_dist="uniform", uniform_random=True, total_stake=5e8)
    w = make_stake(cfg, _rng())
    assert w.std() > 0
    assert abs(w.sum() - 5e8) < 1e-2
    assert np.all(w >= 0)


def test_pareto_sum_fixed_and_heavier_tailed():
    n = 5000
    uni = make_stake(SimConfig(n_nodes=n, stake_dist="uniform", total_stake=1e9), _rng())
    par = make_stake(SimConfig(n_nodes=n, stake_dist="pareto", pareto_shape=1.16,
                               total_stake=1e9), _rng())
    assert abs(par.sum() - 1e9) < 1.0
    assert par.max() > uni.max() * 5        # heavy tail: richest holds far more
    assert np.all(par >= 0)


def test_total_stake_fixed_across_distributions():
    uni = make_stake(SimConfig(n_nodes=1000, stake_dist="uniform", total_stake=7e8), _rng())
    par = make_stake(SimConfig(n_nodes=1000, stake_dist="pareto", total_stake=7e8), _rng())
    assert abs(uni.sum() - par.sum()) < 1.0   # comparability guarantee
