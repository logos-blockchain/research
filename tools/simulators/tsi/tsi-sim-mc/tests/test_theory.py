import numpy as np

from tsi_sim import theory

F = 1 / 30
T = 10000


def test_expected_ratio_unbiased_at_q1():
    assert abs(float(theory.expected_ratio(F, 1.0)) - 1.0) < 1e-12


def test_expected_ratio_monotone_in_q():
    qs = np.linspace(0.5, 1.0, 20)
    er = theory.expected_ratio(F, qs)
    assert np.all(np.diff(er) > 0)          # accuracy improves as q -> 1
    assert np.all(er <= 1.0 + 1e-12)        # always an underestimate


def test_variance_bound_matches_at_q1():
    v = float(theory.variance_ratio(F, 1.0, T))
    assert abs(v - theory.variance_bound(F, T)) < 1e-15


def test_optimal_beta_is_half_stability_bound():
    for q in (0.7, 0.85, 0.95):
        opt = float(theory.optimal_beta(F, q))
        bound = float(theory.beta_stability_bound(F, q))
        assert abs(opt - bound / 2) < 1e-12


def test_block_count_ceiling_above_one():
    c = theory.block_count_ceiling(F)
    assert 1.015 < c < 1.02                 # -ln(1-1/30)/(1/30) ~ 1.01705


def test_fixed_point_bias_about_one_percent():
    b = theory.fixed_point_bias(F)
    assert abs(b - (F / (33 / 1000))) < 1e-12
    assert 1.005 < b < 1.02
