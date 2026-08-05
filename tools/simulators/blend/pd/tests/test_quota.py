"""The emission-quota stake ceiling: exact bind, the D_hat/D normalisation, and epoch compliance."""

import math

import numpy as np

from pd.quota import (
    alpha_max,
    assign_stake,
    emission_quota_per_slot,
    expected_blocks_per_epoch,
    inferred_alpha,
    max_alpha_for_confidence,
    quota_exceedance_prob,
    quota_per_epoch,
    s_max_true,
    simulate_epoch_emissions,
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


# --- stake distribution and the measured ceiling --------------------------------------------------

def test_stake_distributions_normalise_and_zipf_is_heavy_tailed():
    n = 5_000
    rng = np.random.default_rng(0)
    uni = assign_stake(n, "uniform", rng)
    zipf = assign_stake(n, "zipf", rng, zipf_a=1.0)
    for s in (uni, zipf):
        assert abs(s.sum() - 1.0) < 1e-12
        assert (s > 0).all()
    assert np.allclose(uni, 1.0 / n)
    assert zipf.max() > 50 * uni.max()          # a real head, unlike the flat case


def test_inferred_alpha_divides_by_the_estimator_ratio():
    """The lottery weighs sigma/D_hat, so a low estimate inflates every node's alpha."""
    s = np.array([0.001, 0.01])
    assert np.allclose(inferred_alpha(s, 1.0), s)
    assert np.allclose(inferred_alpha(s, 0.5), s * 2.0)


def test_uniform_stake_stays_inside_the_quota_at_scale():
    """At 1/N each, every node's block rate is f/N -- far under a 1/N emission budget."""
    n, S = 20_000, 648_000
    s = assign_stake(n, "uniform", np.random.default_rng(1))
    r = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(2))
    assert r["compliant_frac"] == 1.0
    assert r["overrun"].sum() == 0


def test_heavy_tailed_stake_makes_the_head_overrun_its_quota():
    n, S = 20_000, 648_000
    s = assign_stake(n, "zipf", np.random.default_rng(3), zipf_a=1.0)
    r = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(4))
    assert 0.0 < r["compliant_frac"] < 1.0            # the head breaks, the tail does not
    assert r["min_overrun_stake"] > r["stake"].min()  # it is the large holders that break
    assert r["overrun"][np.argmax(s)] > 0             # the biggest staker certainly does


def test_the_measured_ceiling_matches_the_closed_form():
    """Where compliance actually breaks must bracket the analytic alpha_max."""
    n, S = 20_000, 648_000
    s = assign_stake(n, "zipf", np.random.default_rng(5), zipf_a=0.8)
    r = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(6))
    predicted = alpha_max(n, F)
    assert r["max_compliant_stake"] < 3.0 * predicted
    assert r["min_overrun_stake"] > 0.3 * predicted


def test_a_low_stake_estimate_tightens_the_measured_ceiling():
    """D_hat/D is an input, and lowering it must push more nodes over their quota."""
    n, S = 20_000, 648_000
    s = assign_stake(n, "zipf", np.random.default_rng(7), zipf_a=1.0)
    accurate = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(8),
                                        stake_inference_ratio=1.0)
    deflated = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(8),
                                        stake_inference_ratio=0.64)
    assert deflated["compliant_frac"] < accurate["compliant_frac"]
    assert deflated["max_compliant_stake"] <= accurate["max_compliant_stake"]


def test_more_cover_traffic_raises_the_ceiling():
    """The quota is the budget, so paying more cover traffic admits more concentrated stake."""
    n, S = 20_000, 648_000
    s = assign_stake(n, "zipf", np.random.default_rng(9), zipf_a=1.0)
    lean = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(10), cover_rate_mult=1.0)
    rich = simulate_epoch_emissions(s, F, n, S, np.random.default_rng(10), cover_rate_mult=32.0)
    assert rich["compliant_frac"] > lean["compliant_frac"]
    assert rich["max_compliant_stake"] > lean["max_compliant_stake"]


def test_exceedance_survives_a_large_quota():
    """Regression: exp(-lam) underflows past lam ~ 745, which silently collapsed a hand-rolled
    Poisson CDF to 0 and reported every node as exceeding. Raising the cover rate reaches that
    regime immediately, so the mean bind must still be a coin flip at every rate."""
    n, S = 20_000, 648_000
    for rate in (1.0, 16.0, 64.0, 256.0):
        p = quota_exceedance_prob(alpha_max(n, F, rate), F, n, S, rate)
        assert 0.4 < p < 0.6, (rate, p)


def test_the_safe_ceiling_approaches_the_mean_bind_as_the_quota_grows():
    """Poisson noise shrinks relative to the mean, so the headroom needed for confidence shrinks."""
    n, S = 20_000, 648_000
    ratios = [max_alpha_for_confidence(F, n, S, 0.99, r) / alpha_max(n, F, r)
              for r in (1.0, 16.0, 256.0)]
    assert all(b > a for a, b in zip(ratios, ratios[1:], strict=False))
    assert ratios[-1] > 0.9
