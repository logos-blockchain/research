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


def test_q_effective_interpolates_between_q_and_one():
    # r = 0 -> no recovery (chain-only q); r = 1 -> every wasted slot recovered (q_u = 1).
    for q in (0.3, 0.65, 0.9):
        assert abs(float(theory.q_effective(q, 0.0)) - q) < 1e-15
        assert abs(float(theory.q_effective(q, 1.0)) - 1.0) < 1e-15
        # monotone and strictly between for partial recovery
        half = float(theory.q_effective(q, 0.5))
        assert q < half < 1.0


def test_q_effective_round_trips_the_measured_recovery_rate():
    # The identity the report quotes: given measured q and q_u, r = (q_u - q)/(1 - q)
    # reconstructs q_u exactly. This is how plot_countable_vs_old.py derives its overlay.
    for q, q_u in ((0.3129, 0.6147), (0.5380, 0.9874), (0.7485, 0.9992)):
        r = (q_u - q) / (1.0 - q)
        assert abs(float(theory.q_effective(q, r)) - q_u) < 1e-12


def test_q_effective_recovers_unbiased_equilibrium():
    # Full recovery must lift the equilibrium to exactly 1 for any starting q.
    for q in (0.3, 0.65, 0.9):
        assert abs(float(theory.expected_ratio(F, theory.q_effective(q, 1.0))) - 1.0) < 1e-12


def test_window_miss_prob_decays_as_exp_minus_w():
    # P(no canonical block in w_u = W/f slots) = (1-f)^(W/f) = exp(W * ln(1-f)/f).
    # The docstring's "~ e^-W" is the f -> 0 limit: ln(1-f)/f = -(1 + f/2 + ...) = -1.0170
    # at f = 1/30, so the true decay is slightly FASTER than e^-W, by a factor that grows
    # with W (16% low by W = 10). Assert the exact form, and bracket the heuristic.
    rate = np.log(1.0 - F) / F
    assert -1.02 < rate < -1.0
    for w_abs in (1.0, 3.0, 10.0):
        p = float(theory.window_miss_prob(F, w_abs))
        assert abs(p - (1.0 - F) ** (w_abs / F)) < 1e-15
        assert abs(p - np.exp(rate * w_abs)) < 1e-15          # exact closed form
        assert np.exp(-1.02 * w_abs) < p < np.exp(-w_abs)     # brackets the e^-W heuristic
    # the spec default W = 10 makes the window a negligible loss channel
    assert float(theory.window_miss_prob(F, 10.0)) < 1e-4
    # strictly decreasing in W
    ps = [float(theory.window_miss_prob(F, w)) for w in (1, 2, 3, 5, 7, 10)]
    assert all(a > b for a, b in zip(ps[:-1], ps[1:], strict=True))
