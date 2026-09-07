"""The specified rules, held to their text; the simulations, held to their claims."""
import random

from equix_bench.blend_admission import (
    A_MAX, BLEND_DIFFICULTY_BASE, D_EDGE_MAX, D_EDGE_MIN, F_1, F_W_MAX, G,
    L_MIN, L_STAR, LAMBDA_E, M_1_MAX, P, PHI_CC_MAX, W,
    EdgeDifficulty, attacker_core_rate, blend_difficulty, d_blend, erlang3_tail,
    grace_floor, loop_attractor, loop_step, loop_survey, lower_median, pi5_rate,
    premine_duty, quantize, realized_f_w, runaway_epochs_uncapped, simulate_door,
    simulate_stranded, stranded_probability, zero_median_settles_at,
)


# ------------------------------------------------------------ EdgeDifficulty


def test_edge_raises_doubles_and_caps():
    c = EdgeDifficulty(d=D_EDGE_MIN)
    hot = 2 * LAMBDA_E * W + 1                   # just above the raise threshold
    assert c.retarget(hot) == 2 * D_EDGE_MIN
    c.retarget(hot)
    assert c.d == D_EDGE_MAX                     # 1200 capped to the ceiling
    c.retarget(hot)
    assert c.d == D_EDGE_MAX


def test_edge_decays_by_three_quarters_and_floors():
    c = EdgeDifficulty(d=D_EDGE_MAX)
    cold = LAMBDA_E * W - 1                      # just below the decay threshold
    assert c.retarget(cold) == 750
    for _ in range(20):
        c.retarget(cold)
    assert c.d == D_EDGE_MIN


def test_edge_holds_inside_the_deadband():
    c = EdgeDifficulty(d=500)
    assert c.retarget(1.5 * LAMBDA_E * W) == 500


def test_door_decays_when_it_refuses_nobody():
    # At or below the acceptance rate no presentation is refused, so the price
    # must come down rather than freeze.
    c = EdgeDifficulty(d=D_EDGE_MAX)
    assert c.retarget(0.5 * LAMBDA_E * W) == 750


def test_raise_threshold_is_twice_the_decay_threshold():
    # A doubling of d halves a fixed solver's rate, so a narrower band would
    # oscillate: the band must be at least 2x.
    c = EdgeDifficulty(d=500)
    assert c.retarget(LAMBDA_E * W) == 500            # inside
    assert c.retarget(2 * LAMBDA_E * W) == 500        # still inside


def test_grace_floor_spans_exactly_G_rounds():
    history = [D_EDGE_MIN] * G + [D_EDGE_MAX] * G
    assert grace_floor(history, 2 * G - 2) == D_EDGE_MIN  # round G-1 still inside
    assert grace_floor(history, 2 * G - 1) == D_EDGE_MAX  # exactly G new rounds


# ----------------------------------------------------------- blend_difficulty


def test_blend_is_a_pure_function_of_the_median():
    base = BLEND_DIFFICULTY_BASE
    assert blend_difficulty([L_STAR]) == base                    # the fixed point
    assert blend_difficulty([8, 8, 8]) == (base * L_STAR) // 8   # no step clamp
    assert blend_difficulty([15]) == (base * L_STAR) // 15       # the tightest value


def test_loosening_stops_where_the_drain_condition_does():
    base = BLEND_DIFFICULTY_BASE
    loosest = (base * L_STAR) // L_MIN
    assert blend_difficulty([1]) == loosest
    assert blend_difficulty([0]) == loosest
    # The loosest threshold admits F_W_MAX, and the drain condition holds there.
    assert realized_f_w(loosest) == F_W_MAX
    assert F_1 + F_W_MAX * 3 < M_1_MAX


def test_blend_empty_is_base_and_zero_is_the_level_one_fixed_point():
    base = BLEND_DIFFICULTY_BASE
    assert blend_difficulty([]) == base                          # no information -> the prior
    assert blend_difficulty([0, 0, 1]) == (base * L_STAR) // L_MIN
    assert zero_median_settles_at() == (L_STAR * base) // L_MIN


def test_d_blend_bootstrap_epochs_and_wrapper():
    reports = {0: [5, 5], 1: [7], 2: [3]}
    lookup = lambda e: reports.get(e, [])
    for s_epoch in (0, 1, 2):
        assert d_blend(s_epoch, lookup) == BLEND_DIFFICULTY_BASE
    assert d_blend(3, lookup) == blend_difficulty([5, 5])        # reads epoch 0
    assert d_blend(9, lookup) == BLEND_DIFFICULTY_BASE           # epoch 6 unreported -> prior


def test_lower_median_is_deterministic():
    assert lower_median([3, 1, 2]) == 2
    assert lower_median([4, 1]) == 1                              # even count: lower


def test_uncapped_runaway_would_take_nineteen_epochs():
    assert runaway_epochs_uncapped() == 19                        # BASE = p // 2**19


# ------------------------------------------------------------------- studies


def test_demand_below_the_band_never_trips_the_raise():
    # The raise trips above 2*Lambda_E presentations per round, which at the
    # floor price needs ~19 of the fastest measured cores. Below it the defence
    # is the acceptance rate and redundancy, not escalation.
    tr = simulate_door(1800, lambda t: 10.0 if t >= 300 else 0.0, seed=0)
    assert max(tr.d) == D_EDGE_MIN


def test_large_flood_drives_price_to_ceiling_holds_and_decays():
    tr = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=0)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    # The deadband holds the ceiling under constant fire: no decay-under-attack.
    assert min(tr.d[800:2400]) == D_EDGE_MAX
    # After the flood: x3/4 steps home in five retargets.
    assert tr.d[-1] == D_EDGE_MIN
    # The verification budget holds: headers + token checks under one core.
    assert max(tr.cpu) < 1.0


def test_door_decays_at_the_pow_equilibrium_ambient():
    # The door reads edge presentations only, so core ambient cannot hold the
    # price up: it still comes home after a flood.
    tr = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0,
                       core_mean=48.0, seed=4)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    assert tr.d[-1] == D_EDGE_MIN


def test_attacks_flutter_at_most_one_step():
    # With minting priced at the grace floor (rule 2), the floor lags each rise
    # by up to G rounds, so mid-size and adaptive attacks flutter between two
    # adjacent steps; a large constant flood holds the ceiling. Never a wide
    # sawtooth.
    for cores, giveup in ((40, 800), (60, 800), (40, None)):
        tr = simulate_door(3600, lambda t, c=cores: float(c) if 600 <= t < 2400 else 0.0,
                           adaptive_giveup=giveup, seed=0)
        assert set(tr.d[700:2400]) <= {750, 1000}
    big = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=0)
    assert set(big.d[700:2400]) == {D_EDGE_MAX}   # constant large flood: held


def test_attacker_offers_track_its_hashpower():
    # Ten cores never escalate, so the price stays at the floor and the offer
    # rate is the attacker's floor-price mint rate plus the honest rate.
    tr = simulate_door(1200, lambda t: 10.0, seed=1)
    tail = tr.offered[900:]
    mean_offers = sum(tail) / len(tail)
    expect = 10 * attacker_core_rate(D_EDGE_MIN) + 2.0
    assert abs(mean_offers - expect) / expect < 0.20


def test_trip_point_is_about_nineteen_fastest_cores():
    cores = 2 * LAMBDA_E / attacker_core_rate(D_EDGE_MIN)
    assert 18 < cores < 20


def test_stranded_rate_is_small_at_the_chosen_grace():
    assert stranded_probability(1 / pi5_rate(D_EDGE_MAX)) < 1e-9  # 4 cores
    assert stranded_probability(4 / pi5_rate(D_EDGE_MAX)) < 0.002 # 1 core
    tr = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=0)
    s, n = simulate_stranded(tr, lambda d: pi5_rate(d) / 4.0, seed=2)
    assert n > 0 and s / n < 0.02


def test_leader_budget_numbers():
    assert premine_duty(D_EDGE_MAX) < 0.02                        # ~1.2% of a Pi 5
    assert 0.02 < erlang3_tail(1 / pi5_rate(D_EDGE_MAX), 15) < 0.10
    assert erlang3_tail(1 / pi5_rate(D_EDGE_MIN), 15) < 1e-4


def test_quantize_is_the_envelope_share():
    assert quantize(0.0) == 0
    assert quantize(60.0) == L_STAR              # the sized traffic is the set point
    assert quantize(A_MAX) == 8                  # a full envelope, on every node
    assert quantize(10 * A_MAX) == 15            # clamped


def test_sized_traffic_sits_well_inside_its_band():
    band_lo, band_hi = L_STAR * A_MAX / 8, (L_STAR + 1) * A_MAX / 8
    assert band_lo < 60 < band_hi
    assert (60 - band_lo) / (band_hi - band_lo) > 0.4   # 44%, not on an edge


def test_loop_closes_at_the_design_point():
    # Full degree with the edge allowance used is an exact fixed point.
    assert loop_step(L_STAR, PHI_CC_MAX, LAMBDA_E) == L_STAR
    assert loop_attractor(PHI_CC_MAX, LAMBDA_E, 0) == [L_STAR]


def test_every_attractor_is_bounded_and_drain_safe():
    for (phi, edge), cycles in loop_survey().items():
        for cycle in cycles:
            assert len(cycle) <= 2, (phi, edge, cycle)      # never wider than one step
            for level in cycle:
                f_w = realized_f_w(blend_difficulty([level]))
                assert f_w <= F_W_MAX
                assert F_1 + f_w * 3 < M_1_MAX


def test_one_corner_is_bistable():
    # Phi_CC^Min with no edge traffic admits both a fixed point at 3 and a
    # 2<->4 cycle, depending on where the network starts. Bounded and
    # drain-safe, but it is the one configuration without a unique attractor.
    assert loop_survey()[(6, 0.0)] == [(2, 4), (3,)]


def test_median_shift_is_bounded_below_half_collusion():
    rng = random.Random(5)
    diffs = []
    for _ in range(300):
        h, s = _shift(rng, 0.30)
        diffs.append(abs(h - s))
    # At 30% colluders the shifted median moves one or two levels in nearly
    # every trial; the pure re-anchor to BASE*l*/median bounds the effect and
    # gives it no memory.
    assert sum(d <= 2 for d in diffs) / len(diffs) > 0.99
    assert sum(diffs) / len(diffs) <= 2.0


def _shift(rng, c):
    from equix_bench.blend_admission import median_shift
    return median_shift(100, c, "tighten", rng)
