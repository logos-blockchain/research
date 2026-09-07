"""The specified rules, held to their text; the simulations, held to their claims."""
import random

from equix_bench.blend_admission import (
    BLEND_DIFFICULTY_BASE, D_EDGE_MAX, D_EDGE_MIN, G, L_STAR, LAMBDA_E, P, W,
    EdgeDifficulty, attacker_core_rate, blend_difficulty, d_blend, erlang3_tail,
    grace_floor, lower_median, pi5_rate, premine_duty, quantize,
    runaway_epochs_uncapped, simulate_door, simulate_stranded,
    stranded_probability, zero_median_settles_at,
)

V = 157.0


# ------------------------------------------------------------ EdgeDifficulty


def test_edge_raises_doubles_and_caps():
    c = EdgeDifficulty(d=D_EDGE_MIN)
    hot = (L_STAR + 2) * V * W / 8 + 1          # just above the raise threshold
    assert c.retarget(hot, V) == 2 * D_EDGE_MIN
    c.retarget(hot, V)
    assert c.d == D_EDGE_MAX                     # 1200 capped to the ceiling
    c.retarget(hot, V)
    assert c.d == D_EDGE_MAX


def test_edge_decays_by_three_quarters_and_floors():
    c = EdgeDifficulty(d=D_EDGE_MAX)
    cold = (L_STAR + 1) * V * W / 8 - 1          # just below the decay threshold
    assert c.retarget(cold, V) == 750
    for _ in range(20):
        c.retarget(cold, V)
    assert c.d == D_EDGE_MIN


def test_edge_holds_inside_the_deadband():
    c = EdgeDifficulty(d=500)
    assert c.retarget((L_STAR + 1.5) * V * W / 8, V) == 500


def test_equilibrium_load_decays_the_door():
    # The network steers the median load to l* — below the decay threshold, so
    # a door at any price decays there rather than freezing (the R2 property).
    c = EdgeDifficulty(d=D_EDGE_MAX)
    assert c.retarget(L_STAR * V * W / 8, V) == 750


def test_grace_floor_spans_exactly_G_rounds():
    history = [D_EDGE_MIN] * G + [D_EDGE_MAX] * G
    assert grace_floor(history, 2 * G - 2) == D_EDGE_MIN  # round G-1 still inside
    assert grace_floor(history, 2 * G - 1) == D_EDGE_MAX  # exactly G new rounds


# ----------------------------------------------------------- blend_difficulty


def test_blend_is_a_pure_function_of_the_median():
    base = BLEND_DIFFICULTY_BASE
    assert blend_difficulty([L_STAR]) == base                    # the fixed point
    assert blend_difficulty([8, 8, 8]) == (base * L_STAR) // 8   # no step clamp
    assert blend_difficulty([1]) == base * L_STAR                # the loosest value
    assert blend_difficulty([15]) == (base * L_STAR) // 15       # the tightest value


def test_blend_empty_is_base_and_zero_is_the_level_one_fixed_point():
    base = BLEND_DIFFICULTY_BASE
    assert blend_difficulty([]) == base                          # no information -> the prior
    assert blend_difficulty([0, 0, 1]) == base * L_STAR          # lower median 0, floored at 1
    assert zero_median_settles_at() == L_STAR * base


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


def test_small_flood_never_trips_the_raise():
    # 32 cores at the floor sit at load level ~3.4 — inside the deadband. The
    # price's crowd-out role begins at the trip point (~57 cores); below it the
    # defense is redundancy plus the per-door cost, not escalation.
    tr = simulate_door(1800, lambda t: 32.0 if t >= 300 else 0.0, seed=0)
    assert max(tr.d) == D_EDGE_MIN


def test_large_flood_drives_price_to_ceiling_holds_and_decays():
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0, seed=0)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    # The deadband holds the ceiling under constant fire: no decay-under-attack.
    assert min(tr.d[800:2400]) == D_EDGE_MAX
    # After the flood: x3/4 steps home in five retargets.
    assert tr.d[-1] == D_EDGE_MIN
    # The verification budget holds: headers + token checks under one core.
    assert max(tr.cpu) < 1.0


def test_door_decays_at_the_pow_equilibrium_ambient():
    # Ambient at the sized operating point (~50 arrivals) sits below the decay
    # threshold, so the price still comes home after a flood.
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0,
                       core_mean=48.0, seed=4)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    assert tr.d[-1] == D_EDGE_MIN


def test_attacks_flutter_at_most_one_step():
    # With minting priced at the grace floor (rule 2), the floor lags each rise
    # by up to G rounds, so mid-size and adaptive attacks flutter between two
    # adjacent steps; a large constant flood holds the ceiling. Never a wide
    # sawtooth.
    for cores, giveup in ((120, 800), (200, 800), (120, None)):
        tr = simulate_door(3600, lambda t, c=cores: float(c) if 600 <= t < 2400 else 0.0,
                           adaptive_giveup=giveup, seed=0)
        assert set(tr.d[700:2400]) <= {750, 1000}
    big = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0, seed=0)
    assert set(big.d[700:2400]) == {D_EDGE_MAX}   # constant large flood: held


def test_attacker_offers_track_its_hashpower():
    # 32 cores never escalate, so the price stays at the floor and the offer
    # rate is the attacker's floor-price mint rate plus the honest rate.
    tr = simulate_door(1200, lambda t: 32.0, seed=1)
    tail = tr.offered[900:]
    mean_offers = sum(tail) / len(tail)
    expect = 32 * attacker_core_rate(D_EDGE_MIN) + 2.0
    assert abs(mean_offers - expect) / expect < 0.15


def test_stranded_rate_is_small_at_the_chosen_grace():
    assert stranded_probability(1 / pi5_rate(D_EDGE_MAX)) < 1e-9  # 4 cores
    assert stranded_probability(4 / pi5_rate(D_EDGE_MAX)) < 0.002 # 1 core
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0, seed=0)
    s, n = simulate_stranded(tr, lambda d: pi5_rate(d) / 4.0, seed=2)
    assert n > 0 and s / n < 0.02


def test_leader_budget_numbers():
    assert premine_duty(D_EDGE_MAX) < 0.02                        # ~1.2% of a Pi 5
    assert 0.02 < erlang3_tail(1 / pi5_rate(D_EDGE_MAX), 15) < 0.10
    assert erlang3_tail(1 / pi5_rate(D_EDGE_MIN), 15) < 1e-4


def test_quantize_matches_the_spec_levels():
    assert quantize(0.0) == 0
    assert quantize(0.5) == 4
    assert quantize(L_STAR / 8) == L_STAR
    assert quantize(10.0) == 15                                   # clamped


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
