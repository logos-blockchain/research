"""Time-to-link and stake-inference laws, and a Monte-Carlo check of the emission process."""

import math

import numpy as np

from pd.linkability import (
    capture_prob,
    obs_for_precision,
    redundant,
    stake_rel_precision,
    time_to_link_seconds,
    time_to_stake_seconds,
)


def test_redundant_values_and_bounds():
    assert abs(redundant(0.1, 1) - 0.1) < 1e-12
    assert abs(redundant(0.1, 2) - 0.19) < 1e-12
    assert redundant(0.0, 4) == 0.0
    assert redundant(1.0, 3) == 1.0
    # strictly increasing in R for 0 < x < 1
    vals = [redundant(0.2, R) for R in (1, 2, 3, 4)]
    assert all(b > a for a, b in zip(vals, vals[1:], strict=False))


def test_capture_prob_linkable_vs_population():
    d1 = 0.2 ** 3
    assert abs(capture_prob(d1, 1.0, 1) - d1) < 1e-12                    # linkable, single cascade
    assert abs(capture_prob(d1, 0.5, 1) - 0.5 * d1) < 1e-12
    assert abs(capture_prob(d1, 1.0, 2) - (1 - (1 - d1) ** 2)) < 1e-12


def test_time_to_link_matches_geometric_definition():
    p, alpha, slot = 0.02, 0.9, 30.0
    q = p / 0.01                       # stake=0.01 -> s*q = p
    t = time_to_link_seconds(0.01, q, alpha, slot)
    n = round(t / slot)
    assert 1 - (1 - p) ** n >= alpha - 1e-12
    assert 1 - (1 - p) ** (n - 1) < alpha


def test_time_to_link_scales_inverse_stake():
    q, alpha = 0.01, 0.9
    t1 = time_to_link_seconds(0.01, q, alpha)
    t2 = time_to_link_seconds(0.005, q, alpha)
    assert abs(t2 / t1 - 2.0) < 0.02     # halving stake ~doubles the time


def test_time_to_link_unlinkable_is_infinite():
    assert time_to_link_seconds(0.05, 0.0, 0.9) == math.inf
    assert time_to_stake_seconds(0.01, 0.0, 100) == math.inf


def test_redundancy_cuts_time_by_about_R():
    d1, s, alpha = 0.2 ** 3, 0.01, 0.9   # small d1 -> q_R ~ R*d1
    t1 = time_to_link_seconds(s, capture_prob(d1, 1.0, 1), alpha)
    t4 = time_to_link_seconds(s, capture_prob(d1, 1.0, 4), alpha)
    assert 3.5 < t1 / t4 < 4.0           # ~4x faster with R=4


def test_time_to_stake_scaling():
    q = 0.008
    lin = time_to_stake_seconds(0.01, q, 200) / time_to_stake_seconds(0.01, q, 100)
    assert abs(lin - 2) < 1e-9                       # linear in n_obs
    inv = time_to_stake_seconds(0.001, q, 100) / time_to_stake_seconds(0.01, q, 100)
    assert abs(inv - 10) < 1e-9                      # inverse in threshold
    assert abs(time_to_stake_seconds(0.05, q, 100) - 100 / (0.05 * q) * 30) < 1e-6


def test_obs_for_precision_and_precision():
    assert obs_for_precision(0.1) == 100
    assert obs_for_precision(0.05) == 400
    assert obs_for_precision(0.5) == 4
    assert abs(stake_rel_precision(100) - 0.1) < 1e-12


def test_time_to_link_matches_simulation():
    """Empirical alpha-quantile of the first-observation slot matches the closed form."""
    s, q, alpha = 0.02, 0.05, 0.9        # p = s*q = 1e-3
    rng = np.random.default_rng(7)
    first = rng.geometric(s * q, size=300_000)      # slots until first success, support {1,2,...}
    emp_slots = float(np.quantile(first, alpha))
    closed_slots = time_to_link_seconds(s, q, alpha) / 30.0
    assert abs(emp_slots - closed_slots) / closed_slots < 0.02
