"""Gates for the further routes (src/finality_sim/further.py)."""

import math

import numpy as np
import pytest
from scipy import stats

from finality_sim.further import density_chance, density_depth, time_rule_depth
from finality_sim.private_race import log_strict, strict_depth

F = 1 / 30


def test_attestation_seats_separate_the_sides_and_diverge_at_a_third():
    from finality_sim.further import attestation_seats
    n, theta = attestation_seats(0.30, 1e-9, 1e-6)
    assert n > 0 and theta > 0
    assert stats.poisson.sf(theta - 1, 0.30 * n) <= 1e-9                 # the fork rarely passes
    assert stats.poisson.cdf(theta - 1, 0.35 * n) <= 1e-6               # a side rarely fails
    n_less, th_less = attestation_seats(0.30, 1e-9, 1e-6)
    assert n_less == n
    prev_theta = int(stats.poisson.isf(1e-9, 0.30 * (n - 1))) + 1
    assert stats.poisson.cdf(prev_theta - 1, 0.35 * (n - 1)) > 1e-6     # n is the fewest
    assert attestation_seats(0.25, 1e-9, 1e-6)[0] < n < attestation_seats(0.32, 1e-9, 1e-6)[0]
    assert attestation_seats(1 / 3, 1e-9, 1e-6) == (-1, -1)
    assert attestation_seats(0.30, 1e-9, 1e-6, undelivered=0.1)[0] > n


def test_attestation_seats_are_the_fewest_by_a_scan_of_every_count():
    """Every count from one seat up, by the incomplete gamma function: for ``X`` Poisson in ``μ``,
    ``P(X ≥ t) = P(t, μ)`` and ``P(X < t) = Q(t, μ)``. The threshold is the least ``t`` with
    ``P(t, α n) ≤ ε``; the count holds when ``Q(θ, side·n) ≤ ε_live``; no smaller count holds."""
    from scipy import special

    from finality_sim.further import attestation_seats
    for alpha, lost in ((0.20, 0.0), (0.25, 0.0), (0.25, 0.1), (0.30, 0.0)):
        side = (1 - alpha) / 2 * (1 - lost)
        theta, first = 1, None
        for n in range(1, 20_000):
            while special.gammainc(theta, alpha * n) > 1e-9:          # theta never falls with n
                theta += 1
            if special.gammaincc(theta, side * n) <= 1e-6:
                first = (n, theta)
                break
        assert attestation_seats(alpha, 1e-9, 1e-6, lost) == first


def test_the_detector_rarely_fires_on_a_full_chain_and_catches_a_half():
    from finality_sim.further import detector_power
    threshold, (full, half) = detector_power(0.30, 0.845, 36 * 3600, 1e-9, (0.70, 0.35), F)
    assert 0 < threshold and full <= 1e-9 and half > 0.999


def test_the_detectors_threshold_is_the_eps_tail_of_the_honest_count():
    """The threshold is the largest count below which the honest stake alone falls with chance at
    most eps: by a running sum of the count's law, ``P(N < θ) ≤ ε < P(N ≤ θ)``."""
    from finality_sim.further import detector_power
    from finality_sim.recovery import honest_logpmf, occupancy
    for alpha, hours in ((0.30, 36), (1 / 3, 72)):
        threshold, _ = detector_power(alpha, 0.845, hours * 3600, 1e-9, (0.5,), F)
        pmf = np.exp(honest_logpmf(hours * 3600, occupancy(F, 1 - alpha), growth=0.845))
        below = math.fsum(pmf[:threshold])
        assert below <= 1e-9 < below + pmf[threshold]


def test_the_counting_bound_loosens_with_the_share_and_the_delay():
    from finality_sim.further import counting_deadlines, counting_depth, counting_logp, counting_ratio
    assert counting_ratio(1 / 3, 10, F) > counting_ratio(0.25, 10, F) > counting_ratio(0.10, 10, F)
    assert counting_ratio(1 / 3, 20, F) > counting_ratio(1 / 3, 10, F)
    full = 0.845 * -math.log(1 - F)
    d10, d25 = counting_depth(0.10, 10, 1e-3, full, F), counting_depth(0.25, 10, 1e-3, full, F)
    assert 0 < d10 < d25
    assert counting_depth(0.25, 10, 1e-6, full, F) > d25
    # the bound rises with time and with the share, and the deadline brackets it
    assert counting_logp(60, 1000.0, 0.25, 10, F) < counting_logp(60, 3000.0, 0.25, 10, F)
    assert counting_logp(60, 2000.0, 0.25, 10, F) < counting_logp(60, 2000.0, 0.30, 10, F)
    dl = counting_deadlines(0.25, 10, 1e-3, 80, F)
    n = int(np.nonzero(dl >= 0)[0][0])
    assert counting_logp(n, dl[n], 0.25, 10, F) <= math.log(1e-3) < counting_logp(n, dl[n] + 1.0, 0.25, 10, F)



def test_the_counting_bound_matches_its_own_random_variables():
    """Monte Carlo of the bound's model: L geometric at the catch-up ratio, A and H Poisson at the
    slot occupancies, failure when L + 2A + H reaches 2n + 1 or by a catch-up with chance
    rho^(deficit)."""
    from finality_sim.further import counting_logp, counting_ratio
    from finality_sim.recovery import occupancy
    alpha, delta, n, t = 0.25, 10, 20, 600.0
    a, h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    rho = counting_ratio(alpha, delta, F)
    rng = np.random.default_rng(9)
    size = 2_000_000
    lead = rng.geometric(1 - rho, size) - 1
    x = lead + 2 * rng.poisson(a * t, size) + rng.poisson(h * t, size)
    deficit = 2 * n + 1 - x
    p = np.where(deficit <= 0, 1.0, rho ** np.maximum(deficit, 0)).mean()
    assert math.exp(counting_logp(n, t, alpha, delta, F)) == pytest.approx(p, rel=0.02)


def test_the_timed_attack_reproduces_the_untimed_one_at_a_depth():
    """A rule that accepts at depth K regardless of time is the depth rule: the attack's failures at
    confirmation match the untimed attack's at that K."""
    from finality_sim.grr_attack import _attack, _attack_rule, _symbols, _symbols_timed, occupancy
    p_h, p_a = occupancy(F, 0.75), occupancy(F, 0.25)
    d, a = _symbols(2_000_000, p_h, p_a, 10, 3)
    dt, at_, tt = _symbols_timed(2_000_000, p_h, p_a, 10, 3)
    assert np.array_equal(d, dt) and np.array_equal(a, at_) and np.all(np.diff(tt) > 0)
    k = 12
    conf, ever, targets = _attack(d, a, 40, 2000)
    deadline = np.full(41, -1.0)
    deadline[k + 1:] = np.inf
    rc, re, rt, acc, _ = _attack_rule(dt, at_, tt, deadline, 2000)
    assert rt == targets and acc <= rt
    assert rc == conf[k - 1]


def test_hostile_relays_hold_a_block_for_the_longest_delay():
    """G6's engine flag: a relay in the adversary's mask adds blend_delay_max, an honest one a
    uniform draw on 1..blend_delay_max rounds."""
    from tsi_sim.config import SimConfig
    from tsi_sim.topology import _blend_arrival_column
    n = 30
    cfg = SimConfig(n_nodes=n, topology="blend", degree=6, blend_hops=3, blend_delay_max=3.0,
                    blend_delay_dist="rounds", k=16, epochs=1, f=1 / 30, blend_adversary_relays=True)
    path = np.zeros((n, n))
    hostile = np.ones(n, dtype=bool)
    for seed in range(4):
        assert np.all(_blend_arrival_column(path, 0, 50, cfg, np.random.default_rng(seed), hostile) == 59.0)
    honest = {float(_blend_arrival_column(path, 0, 50, cfg, np.random.default_rng(s), np.zeros(n, bool))[1])
              for s in range(100)}
    assert len(honest) > 3 and min(honest) >= 53.0 and max(honest) <= 59.0


def test_the_time_rule_settles_an_unattacked_chain_sooner_and_the_adjusted_rule_later():
    g, eps, alpha = 0.845, 1e-6, 0.30
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    full, held = time_rule_depth(alpha, g, eps, F), time_rule_depth(alpha, g, eps, F, full_rate=False)
    assert 0 < full < held <= plain
    assert time_rule_depth(alpha, g, eps, F, adjusted=True) > full
    assert time_rule_depth(alpha, g, eps, F, full_rate=False, adjusted=True) > held


def test_the_adjusted_rule_accepts_where_the_exact_chance_at_the_deflated_rates_first_falls_to_eps():
    """The adjusted rates are the Poisson rates of the lottery at the thresholds a period of
    withholding leaves (``finality_sim.inference.raised_rates``): the coalition at
    ``-ln(1 - occupancy(f, α/(1 - α)))``, the honest chain at ``g`` times ``-ln(1 - f)``. On a chain
    nobody withholds from, the rule accepts at the first block whose exact chance (B4) is at most
    ``ε`` at those rates."""
    from finality_sim.elapsed import log_fail
    from finality_sim.inference import raised_rates
    g, eps, lam = 0.845, 1e-9, -math.log(1 - F)
    for alpha in (0.30, 1 / 3):
        honest, coalition = raised_rates(F, alpha)
        a, h = -math.log(1 - coalition), g * -math.log(1 - honest)
        n = time_rule_depth(alpha, g, eps, F, adjusted=True)
        chance = [log_fail(m, m / (g * lam), a, h) for m in range(1, n + 1)]
        assert chance[-1] <= math.log(eps) < min(chance[:-1])


def test_without_the_density_test_the_rule_is_the_depth_table():
    g, eps = 0.845, 1e-6
    d, w = density_depth(0.30, g, eps, F, test=False)
    assert d == strict_depth(0.30 / (0.30 + 0.70 * g), math.log(eps)) and w == 0.30


def test_the_density_rule_is_sound_where_it_accepts_and_later_than_the_time_rule():
    """At its acceptance the exact conditional chance is below eps, and B4's elapsed-time rule has
    accepted earlier; one block before, some share exceeds the density rule's own condition."""
    g, eps, alpha = 0.845, 1e-6, 0.30
    d, w = density_depth(alpha, g, eps, F)
    assert density_chance(alpha, g, eps, F) <= math.log(eps)
    assert time_rule_depth(alpha, g, eps, F) < d + 1
    lam = -math.log(1 - F)

    def worst(depth):
        n = depth + 1
        t = n / (g * lam)
        out = -np.inf
        for s in np.append(np.arange(0.01, alpha, 0.01), alpha):
            q = s / (s + (1 - s) * g)
            out = max(out, log_strict(q, n) + float(stats.poisson.logsf(n - 1, (1 - s) * g * lam * t)))
        return out
    assert worst(d) <= math.log(eps) < worst(d - 1) and 0 < w <= alpha


def test_the_observed_counting_bound_matches_its_own_random_variables():
    """Monte Carlo of the observed bound's model: L geometric at the catch-up ratio, A Poisson at
    the coalition's occupancy over t, H_late Poisson at the honest occupancy over delta, failure
    when L + A + H_late reaches n + 1 - forks or by a catch-up with chance rho^(deficit)."""
    from finality_sim.further import counting_observed_logp, counting_ratio
    from finality_sim.recovery import occupancy
    alpha, delta, n, t, forks = 0.25, 10, 20, 600.0, 3
    a, h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    rho = counting_ratio(alpha, delta, F)
    rng = np.random.default_rng(11)
    size = 2_000_000
    x = (rng.geometric(1 - rho, size) - 1) + rng.poisson(a * t, size) + rng.poisson(h * delta, size)
    deficit = n + 1 - forks - x
    p = np.where(deficit <= 0, 1.0, rho ** np.maximum(deficit, 0)).mean()
    assert math.exp(counting_observed_logp(n, t, forks, alpha, delta, F)) == pytest.approx(p, rel=0.02)


def test_the_observed_rule_holds_where_the_counting_bound_is_empty_and_a_publishing_coalition_stalls_it():
    from finality_sim.elapsed import settle
    from finality_sim.further import (counting_depth, counting_observed_deadlines, counting_observed_depth,
                                      counting_observed_logp, observed_settle)
    from finality_sim.recovery import occupancy
    full = 0.845 * -math.log(1 - F)
    third = 1 / 3
    withheld = (1 - third) * full
    d0 = counting_observed_depth(third, 10, 1e-9, withheld, 0)
    d2 = counting_observed_depth(third, 10, 1e-9, withheld, 2)
    assert counting_depth(third, 10, 1e-9, withheld, F) == -1 and 0 < d0 < d2 < d0 + 10
    assert counting_observed_depth(third, 10, 1e-9, full, 0) < d0
    h = occupancy(F, 1 - third)
    h_w = 1.0 / (10 + 1.0 / h)
    assert counting_observed_depth(third, 10, 1e-9, h_w, 0, h - h_w) > d2       # a balancing coalition
    assert counting_observed_depth(third, 10, 1e-9, withheld, 0, occupancy(F, third)) == -1
    assert counting_observed_depth(0.25, 10, 1e-9, 0.75 * full, 0, occupancy(F, 0.25)) > 0
    # the deadlines bracket the bound, fall with the forks, and the play reads them
    dl = counting_observed_deadlines(0.25, 10, 1e-3, 60, (0, 2))
    n = int(np.nonzero(dl[:, 0] >= 0)[0][0])
    assert counting_observed_logp(n, dl[n, 0], 0, 0.25, 10, F) <= math.log(1e-3) \
        < counting_observed_logp(n, dl[n, 0] + 1.0, 0, 0.25, 10, F)
    assert np.all((dl[:, 1] < dl[:, 0]) | (dl[:, 0] < 0))
    rng = np.random.default_rng(3)
    canon = np.cumsum(rng.integers(20, 60, 400)).astype(np.int64)
    k0, t0 = observed_settle(canon, dl, np.zeros(canon.size, np.int64), (0, 2))
    k_ref, t_ref, _ = settle(canon, dl[:, 0], 1)
    assert np.array_equal(k0, k_ref) and np.array_equal(t0, t_ref) and (k0 >= 1).sum() > 100
    k2, _ = observed_settle(canon, dl, np.full(canon.size, 2, np.int64), (0, 2))
    assert np.all((k2 >= k0) | (k2 < 0)) and np.any(k2 > k0)
    k9, _ = observed_settle(canon, dl, np.full(canon.size, 9, np.int64), (0, 2))
    assert np.all(k9 == -1)
    # the coalition's own blocks on a balancing chain are forks too, and stall the rule
    assert counting_observed_depth(third, 10, 1e-9, h_w, 0, h - h_w + occupancy(F, third)) == -1


def test_the_observed_rule_reads_the_clients_clock():
    """A client that holds each block ten slots after its slot reads a later clock: it accepts no
    sooner, and where it accepts at the same block, ten slots later."""
    from finality_sim.further import counting_observed_deadlines, observed_settle
    dl = counting_observed_deadlines(0.25, 10, 1e-3, 60, (0,))
    rng = np.random.default_rng(3)
    canon = np.cumsum(rng.integers(20, 60, 400)).astype(np.int64)
    none = np.zeros(canon.size, np.int64)
    k0, t0 = observed_settle(canon, dl, none, (0,))
    k1, t1 = observed_settle(canon, dl, none, (0,), canon + 10)
    assert np.all((k1 >= k0) | (k1 < 0)) and np.any(k1 > k0)
    same = (k1 == k0) & (k0 >= 1)
    assert same.sum() > 100 and np.all(t1[same] == t0[same] + 10)


def test_a_tie_that_goes_to_the_coalition_matches_its_random_variables():
    """Monte Carlo of the observed bound's model when a tie suffices: failure when L + A + H_late
    reaches n - forks, or by a catch-up from there."""
    from finality_sim.further import counting_observed_logp, counting_ratio
    from finality_sim.recovery import occupancy
    alpha, delta, n, t, forks = 0.30, 10, 30, 900.0, 2
    a, h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    rho = counting_ratio(alpha, delta, F)
    rng = np.random.default_rng(13)
    size = 2_000_000
    x = (rng.geometric(1 - rho, size) - 1) + rng.poisson(a * t, size) + rng.poisson(h * delta, size)
    deficit = n - forks - x
    p = np.where(deficit <= 0, 1.0, rho ** np.maximum(deficit, 0)).mean()
    assert math.exp(counting_observed_logp(n, t, forks, alpha, delta, F, ties_to_coalition=True)) \
        == pytest.approx(p, rel=0.02)
