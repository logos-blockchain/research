import numpy as np

from pd.mixclock import mean_residual_ms, mix_wait


def test_zero_max_delay_is_zero():
    rng = np.random.default_rng(0)
    w = mix_wait(rng, 0, 1000)
    assert np.all(w == 0.0)


def test_residual_within_bounds():
    rng = np.random.default_rng(1)
    m = 5
    w = mix_wait(rng, m, 100000)
    assert w.min() >= 0.0
    assert w.max() <= m * 1000.0 + 1e-6  # residual within a covering interval (<= M seconds)


def test_mean_matches_analytic():
    rng = np.random.default_rng(2)
    for m in (1, 3, 8):
        w = mix_wait(rng, m, 400000)
        assert abs(w.mean() - mean_residual_ms(m)) < 0.03 * mean_residual_ms(m)
