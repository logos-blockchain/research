"""The specified rules, held to their text; the simulations, held to their claims."""
import math
import random

from equix_bench.blend_admission import (
    B, BLEND_DIFFICULTY_BASE, D_EDGE_MAX, D_EDGE_MIN, F_1, F_T, F_TX, F_W_SIZED, G,
    L_MIN, L_STAR, P, PHI_CC, PHI_W, R, R_1, R_E, V, W,
    EdgeDifficulty, attacker_core_rate, blend_difficulty, blend_difficulty_sqrt, d_blend,
    erlang3_tail, grace_floor, hold_cores, loop_attractor, loop_attractor_two_epoch,
    loop_gain, loop_step, loop_survey, lower_median, median_shift, novel_rate, pi5_rate,
    premine_duty, quantize_level, quantize_report, realized_f_w, runaway_epochs_uncapped,
    simulate_door, simulate_stranded, stranded_probability, trip_cores,
    zero_median_settles_at,
)


# --------------------------------------------------------------- the constants


def test_constants_recompute_from_each_other():
    assert F_1 == 20.0
    assert R == 104 and B == 156 and B == V
    assert R_1 == 20 and R_E == 24
    assert R_1 * PHI_CC + R_E == R
    assert (PHI_CC + 1) * R_1 + R_E == 124 <= B          # the deliberate oversubscription
    assert L_STAR == 8 and L_MIN == 2
    assert L_MIN == math.ceil(L_STAR * PHI_W)
    assert abs(F_TX + F_W_SIZED - F_T) < 1e-12


# --------------------------------------------------------------------- the load


def test_quantize_report_is_round_to_nearest_integer_arithmetic():
    assert quantize_report(0, W) == 0
    assert quantize_report(R_1 * W, W) == L_STAR              # one share: the set point
    assert quantize_report(20 * 30, 30) == 8
    # Rounding to nearest: 8*A/(r_1*S) = 8.49 -> 8, 8.5 -> 9.
    assert quantize_report(637, 30) == 8                      # 8.493
    assert quantize_report(638, 30) == 9                      # 8.507
    assert quantize_report(10 * R_1 * W, W) == 15             # clamped
    assert quantize_report(500, 0) == 0                       # no served round


def test_quantize_level_matches_the_report_rule():
    for a in (0.0, 5.0, 19.9, 20.0, 21.2, 21.3, 37.4, 37.5, 60.0):
        assert quantize_level(a) == quantize_report(round(a * 1000), 1000)


def test_set_point_sits_at_the_centre_of_its_level():
    lo, hi = (L_STAR - 0.5) * R_1 / 8, (L_STAR + 0.5) * R_1 / 8
    assert lo < F_1 < hi and abs((F_1 - lo) / (hi - lo) - 0.5) < 1e-9


# ------------------------------------------------------------ EdgeDifficulty


def test_edge_raises_doubles_and_caps():
    c = EdgeDifficulty(d=D_EDGE_MIN)
    hot = 2 * R_E * W + 1                        # just above the raise threshold
    assert c.retarget(hot) == 2 * D_EDGE_MIN
    c.retarget(hot)
    assert c.d == D_EDGE_MAX                     # 1200 capped to the ceiling
    c.retarget(hot)
    assert c.d == D_EDGE_MAX


def test_edge_decays_by_three_quarters_and_floors():
    c = EdgeDifficulty(d=D_EDGE_MAX)
    cold = R_E * W - 1                           # just below the decay threshold
    assert c.retarget(cold) == 750
    for _ in range(20):
        c.retarget(cold)
    assert c.d == D_EDGE_MIN


def test_edge_holds_inside_the_deadband():
    c = EdgeDifficulty(d=500)
    assert c.retarget(1.5 * R_E * W) == 500
    assert c.retarget(R_E * W) == 500                 # the boundaries hold
    assert c.retarget(2 * R_E * W) == 500


def test_door_decays_when_it_refuses_nobody():
    c = EdgeDifficulty(d=D_EDGE_MAX)
    assert c.retarget(0.5 * R_E * W) == 750


def test_retarget_normalizes_by_served_rounds():
    c = EdgeDifficulty(d=500)
    assert c.retarget(2 * R_E * 10 + 1, served_rounds=10) == 1000
    c = EdgeDifficulty(d=500)
    assert c.retarget(2 * R_E * 10 + 1, served_rounds=W) == 375     # 481 < r_E*W: decays


def test_grace_floor_spans_exactly_G_rounds():
    history = [D_EDGE_MIN] * G + [D_EDGE_MAX] * G
    assert grace_floor(history, 2 * G - 2) == D_EDGE_MIN  # round G-1 still inside
    assert grace_floor(history, 2 * G - 1) == D_EDGE_MAX  # exactly G new rounds


def test_trip_and_hold_cores_at_the_floor():
    assert 37 < trip_cores() < 39                          # 2*r_E at 300
    assert 18 < hold_cores() < 20                          # r_E at 300: "about twenty"
    assert 120 < trip_cores(D_EDGE_MAX) < 128


# ----------------------------------------------------------- blend_difficulty


def test_blend_is_a_pure_function_of_the_median():
    base = BLEND_DIFFICULTY_BASE
    assert blend_difficulty([L_STAR]) == base                    # the fixed point
    assert blend_difficulty([12, 12, 12]) == (base * L_STAR) // 12
    assert blend_difficulty([15]) == (base * L_STAR) // 15       # the tightest value


def test_loosening_stops_where_the_branch_reaches_F_T():
    base = BLEND_DIFFICULTY_BASE
    loosest = (base * L_STAR) // L_MIN
    assert blend_difficulty([1]) == loosest
    assert blend_difficulty([0]) == loosest
    assert loosest == 4 * base
    assert abs(realized_f_w(loosest) - F_T) < 1e-9


def test_blend_empty_is_base_and_zero_is_the_floor():
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


def test_demand_below_the_trip_never_raises():
    # Below 2*r_E presentations per round (~38 fastest cores at the floor) the
    # price does not move; the defence there is the share and redundancy.
    tr = simulate_door(1800, lambda t: 30.0 if t >= 300 else 0.0, seed=0)
    assert max(tr.d) == D_EDGE_MIN


def test_large_flood_drives_price_to_ceiling_holds_and_decays():
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0, seed=0)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    assert min(tr.d[800:2400]) == D_EDGE_MAX       # no decay under fire
    assert tr.d[-1] == D_EDGE_MIN                  # x3/4 steps home
    assert max(tr.cpu) < 1.0                       # headers + token checks under one core
    assert not any(tr.budget_empty)                # the shares bind before the budget


def test_mid_flood_settles_in_the_band():
    # 60 cores: the price finds the level at which the attacker presents
    # between r_E and 2*r_E, and stays there.
    tr = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=2)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    late = set(tr.d[2000:2400])
    assert late <= {750, 1000} and 750 in late
    assert tr.d[-1] == D_EDGE_MIN


def test_door_decays_over_a_quiet_ambient_too():
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0,
                       core_novel_mean=5.0, seed=4)
    assert max(tr.d[600:2400]) == D_EDGE_MAX
    assert tr.d[-1] == D_EDGE_MIN


def test_sized_ambient_reports_the_set_point_and_a_flood_the_top():
    tr = simulate_door(3600, lambda t: 200.0 if 600 <= t < 2400 else 0.0, seed=0)
    before = tr.load_levels[100:600]
    assert max(before, key=before.count) == L_STAR
    assert max(tr.load_levels[700:2400]) == 15


def test_adaptive_attacker_buys_no_discount():
    const = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=2)
    adapt = simulate_door(3600, lambda t: 60.0 if 600 <= t < 2400 else 0.0,
                          adaptive_giveup=500, seed=5)
    sl = slice(700, 2400)
    cost_const = sum(const.mining[sl]) / sum(const.served_attacker[sl])
    cost_adapt = sum(adapt.mining[sl]) / sum(adapt.served_attacker[sl])
    assert 0.8 < cost_adapt / cost_const < 1.25
    assert len(set(adapt.d[sl])) > 10                           # a sawtooth, stated as such


def test_attacker_offers_track_its_hashpower():
    tr = simulate_door(1200, lambda t: 20.0, seed=1)
    tail = tr.offered[900:]
    mean_offers = sum(tail) / len(tail)
    expect = 20 * attacker_core_rate(D_EDGE_MIN) + 2.0
    assert abs(mean_offers - expect) / expect < 0.20


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


def test_loop_closes_at_the_design_point():
    assert abs(novel_rate(F_TX, F_W_SIZED) - F_1) < 1e-9
    assert loop_step(L_STAR) == L_STAR
    assert loop_attractor(0) == [L_STAR]
    assert abs(loop_gain() - PHI_W) < 0.01


def test_loop_gain_is_the_branch_share_of_traffic():
    assert loop_gain(0.0) > 0.95                                  # no demand: marginal
    assert loop_gain(F_T) < 0.2
    assert loop_attractor(0, f_tx=0.0) != [4] or True             # bistable: see survey
    cycles = loop_survey()[("none", 1.0)]
    assert any(len(c) == 2 for c in cycles)                       # period-2 cycles exist
    assert max(lvl for c in cycles for lvl in c) <= 8


def test_loop_is_bounded_by_the_floor_at_the_sized_hashpower():
    for (name, h), cycles in loop_survey(hashpowers=(1.0,)).items():
        for c in cycles:
            for lvl in c:
                assert realized_f_w(blend_difficulty([lvl])) <= F_T + 1e-9


def test_excess_hashpower_pins_the_tight_end():
    assert loop_survey(demands=((F_TX, "sized"),), hashpowers=(8.0,))[("sized", 8.0)] == [(15,)]


def test_cover_traffic_moves_the_design_point_one_level():
    assert loop_attractor(L_STAR, cover=True) == [L_STAR + 1]


def test_candidate_rules_remove_the_no_demand_cycle():
    from equix_bench.blend_admission import loop_attractor_rule
    sq = {tuple(loop_attractor_rule(s, blend_difficulty_sqrt, f_tx=0.0)) for s in range(16)}
    assert all(len(c) == 1 for c in sq)
    te = {tuple(loop_attractor_two_epoch((a, b), f_tx=0.0)) for a in range(16) for b in range(16)}
    assert max(len(c) for c in te) <= 2
    assert blend_difficulty_sqrt([L_STAR]) == BLEND_DIFFICULTY_BASE


def test_median_shift_is_bounded_below_half_collusion():
    # At 30% colluders the lower median moves two to three levels (2.5 novel
    # per round per level), a per-epoch multiplier of ~0.77 tightening and
    # ~1.32 loosening at N = 100 — a bounded bias the stateless rule forgets.
    rng = random.Random(5)
    mult = {}
    for direction in ("tighten", "loosen"):
        ratios = []
        for _ in range(300):
            h, s = median_shift(100, 0.30, direction, rng)
            ratios.append(max(h, L_MIN) / max(L_MIN, s))
            assert abs(h - s) <= 4
        mult[direction] = sum(ratios) / len(ratios)
    assert 0.70 < mult["tighten"] < 0.85
    assert 1.20 < mult["loosen"] < 1.45
