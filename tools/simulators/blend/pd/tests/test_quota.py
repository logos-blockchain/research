"""The emission-quota stake ceiling: exact bind, the D_hat/D normalisation, and epoch compliance."""

import math

import numpy as np

from pd.quota import (
    alpha_max,
    emission_quota_per_slot,
    expected_blocks_per_epoch,
    max_alpha_for_confidence,
    quota_exceedance_prob,
    quota_per_epoch,
    s_max_true,
    win_prob,
)

F = 1.0 / 30.0


def test_quota_is_one_emission_per_slot_network_wide():
    n = 20_000
    assert emission_quota_per_slot(n) * n == 1.0            # whole network emits once per slot
    assert emission_quota_per_slot(n, 4.0) * n == 4.0       # the multiplier scales it


def test_alpha_max_is_where_the_win_rate_equals_the_quota():
    n = 20_000
    a = alpha_max(n, F)
    assert abs(win_prob(a, F) - emission_quota_per_slot(n)) < 1e-15


def test_alpha_max_is_below_the_q_over_f_approximation():
    """q/f is a small-q expansion and errs optimistic, so the exact bind must be lower."""
    for n in (1_000, 20_000, 10**6):
        exact = alpha_max(n, F)
        approx = emission_quota_per_slot(n) / F
        assert exact < approx
        assert abs(approx / exact - 1) < 0.02               # ~1.7% at f = 1/30


def test_alpha_max_scales_inversely_with_network_size_and_with_cover_rate():
    assert abs(alpha_max(20_000, F) / alpha_max(200_000, F) - 10.0) < 0.01
    assert abs(alpha_max(20_000, F, 8.0) / alpha_max(20_000, F, 1.0) - 8.0) < 0.01


def test_true_stake_ceiling_is_scaled_by_the_inference_ratio():
    """The lottery uses sigma/D_hat, so the ceiling in TRUE stake carries the D_hat/D factor."""
    n = 20_000
    a = alpha_max(n, F)
    assert s_max_true(n, F, 1.0) == a                       # accurate estimator: no correction
    assert abs(s_max_true(n, F, 0.74) - 0.74 * a) < 1e-15   # deflated estimate tightens it
    assert s_max_true(n, F, 0.64) < s_max_true(n, F, 0.74) < a


def test_expected_blocks_equal_the_quota_at_alpha_max():
    n, S = 20_000, 648_000
    a = alpha_max(n, F)
    assert abs(expected_blocks_per_epoch(a, F, S) - quota_per_epoch(n, S)) < 1e-6


def test_a_node_at_the_mean_bind_overruns_about_half_the_time():
    n, S = 20_000, 648_000
    p = quota_exceedance_prob(alpha_max(n, F), F, n, S)
    assert 0.35 < p < 0.65                                  # mean bind is a coin flip, as expected


def test_confidence_ceiling_is_stricter_than_the_mean_bind():
    n, S = 20_000, 648_000
    safe = max_alpha_for_confidence(F, n, S, confidence=0.99)
    assert safe < alpha_max(n, F)
    assert quota_exceedance_prob(safe, F, n, S) <= 0.01 + 1e-9
    assert 0.5 < safe / alpha_max(n, F) < 0.9               # Poisson noise eats real headroom


def test_exceedance_matches_a_direct_simulation():
    """Closed-form exceedance vs drawing epochs of block wins."""
    n, S = 2_000, 20_000
    a = alpha_max(n, F) * 0.8
    closed = quota_exceedance_prob(a, F, n, S)
    rng = np.random.default_rng(0)
    quota = quota_per_epoch(n, S)
    wins = rng.binomial(S, win_prob(a, F), size=20_000)
    emp = float(np.mean(wins > math.floor(quota)))
    assert abs(closed - emp) < max(0.01, 0.1 * closed)
