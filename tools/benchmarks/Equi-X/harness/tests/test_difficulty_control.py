"""The difficulty controllers must converge: drive E so the observed signal
(mint rate for Design A, pressure for Design B) reaches its target, using only
the measured 1/E mint-rate curve."""
import math

from equix_bench.difficulty_control import (
    LoadController, MEASURED_MINT, MintRateController, equilibrium_E,
    mint_rate_per_machine, simulate_dos, simulate_mining,
)


def test_mint_rate_matches_measured_and_is_monotonic():
    for e, r in MEASURED_MINT:
        assert abs(mint_rate_per_machine(e) - r) < 1e-6
    rates = [mint_rate_per_machine(e) for e in (50, 100, 300, 1000, 3000, 10000, 100000)]
    assert all(a > b for a, b in zip(rates, rates[1:]))          # strictly decreasing
    # 1/E extrapolation only OUTSIDE the measured range: doubling E halves the rate.
    top_e, top_r = max(MEASURED_MINT)
    assert abs(mint_rate_per_machine(2 * top_e) - top_r / 2) < 1e-6
    assert abs(mint_rate_per_machine(50) - MEASURED_MINT[0][1] * MEASURED_MINT[0][0] / 50) < 1e-6


def test_mint_rate_controller_converges_to_target():
    # 10 machines, target 3 tok/s. Controller should settle E so 10·M(E) ≈ 3.
    tr = simulate_mining(lambda t: 10.0, target_rate=3.0, steps=60)
    assert abs(tr.signal[-1] - 3.0) / 3.0 < 0.05                  # within 5%
    assert 10 * mint_rate_per_machine(tr.E[-1]) == tr.signal[-1]


def test_mint_rate_controller_tracks_capacity_step():
    # Capacity doubles at t=30; controller must roughly double E to hold the rate.
    tr = simulate_mining(lambda t: 5.0 if t < 30 else 10.0, target_rate=2.0, steps=80)
    assert abs(tr.signal[-1] - 2.0) / 2.0 < 0.05
    E_before = tr.E[29]
    assert tr.E[-1] > 1.6 * E_before                             # ~2× more difficulty


def test_equilibrium_E_inverts_the_curve():
    # At the solved E, `machines` x M(E) must equal the target rate.
    for machines, target in [(6.0, 2.0), (1.0, 0.5), (20.0, 2.0)]:
        E = equilibrium_E(machines, target)
        assert abs(machines * mint_rate_per_machine(E) - target) / target < 0.001


def test_production_tuning_is_stable_under_noise_and_reproducible():
    # Gentle gains + seeded E + measurement noise: settled rate stays near target,
    # and the same seed gives the same trace.
    def cap(t):
        return 6.0
    mk = lambda: MintRateController(target_rate=2.0, E=equilibrium_E(6.0, 2.0), max_factor=2.0, ewma=0.15)
    a = simulate_mining(cap, 2.0, steps=120, ctrl=mk(), noise=0.08, seed=1)
    b = simulate_mining(cap, 2.0, steps=120, ctrl=mk(), noise=0.08, seed=1)
    assert a.E == b.E                                     # reproducible for a fixed seed
    tail = a.signal[80:]
    mean = sum(tail) / len(tail)
    assert abs(mean - 2.0) / 2.0 < 0.05                   # settled within 5% of target
    # Seeded near equilibrium -> no big cold-start excursion in E.
    assert max(a.E) / min(a.E) < 3.0


def test_load_controller_direction_and_deadband():
    c = LoadController(p_set=0.8, E=1000.0, e_min=100.0)
    assert c.update(1.5) > 1000.0                                # overloaded -> raise E
    c2 = LoadController(p_set=0.8, E=1000.0, e_min=100.0)
    assert c2.update(0.2) < 1000.0                               # idle -> lower E
    c3 = LoadController(p_set=0.8, E=1000.0, deadband=0.05)
    assert c3.update(0.81) == 1000.0                             # within deadband -> hold


def test_adaptive_attacker_bounds_mean_load_but_sawtooths():
    # An attacker that only attacks while E is below a give-up point must not be
    # able to hold the node saturated continuously (mean load bounded), yet the
    # decay controller visibly oscillates (E spans a wide range).
    def adaptive(t, E):
        return 6.0 if (10 <= t < 80 and E < 800.0) else 0.0
    tr = simulate_dos(lambda t: 8.0, lambda t: 0.0, service_capacity=40.0,
                      steps=100, adaptive_attackers=adaptive)
    window = slice(10, 80)
    util = tr.extra["util"][window]
    assert sum(util) / len(util) < 0.9              # mean load bounded, not pinned at 1
    assert max(tr.E[window]) / min(tr.E[window]) > 3  # E sawtooths, not settled
    # Attacker gets a nonzero share (it isn't shut out) but not a constant one.
    on = [a for a in tr.extra["attacker_rate"][window] if a > 0]
    assert 0 < len(on) < 70


def test_load_controller_throttles_attack():
    # Flood during [20,50); node capacity 40 req/s, honest 8 req/s.
    tr = simulate_dos(lambda t: 8.0, lambda t: 6.0 if 20 <= t < 50 else 0.0,
                      service_capacity=40.0, steps=90)
    # After the controller reacts, sustained utilization must fall back to ~p_set.
    late_attack_util = tr.extra["util"][45]
    assert late_attack_util < 0.95                               # not saturated anymore
    # E rises during the attack and decays again afterwards.
    assert max(tr.E[20:50]) > 3 * tr.E[19]
    assert tr.E[-1] < max(tr.E[20:50])
