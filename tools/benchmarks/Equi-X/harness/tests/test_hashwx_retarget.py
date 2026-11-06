"""The reward retarget in target form, held to what the specification will claim."""
import statistics

from equix_bench.hashwx_retarget import (
    SLOTS_PER_BLOCK, TWO64, rounding_bias, rules, settled_target, simulate, step, widest_bits,
)


def test_a_target_of_the_target_rate_is_a_fixed_point_in_expectation():
    for rule in rules():
        if rule.den == 1:
            assert step(rule, rule.cap // 4, rule.num) == rule.cap // 4


def test_the_floor_is_the_smallest_target_a_block_without_claims_raises():
    for rule in rules():
        assert (rule.floor - 1) * rule.P // rule.F == rule.floor - 1
        assert rule.floor * rule.P // rule.F > rule.floor


def test_the_cap_and_the_floor_bound_the_update():
    for rule in rules():
        assert step(rule, rule.cap, 0) == rule.cap
        assert step(rule, rule.floor, 10**6) == rule.floor


def test_intermediates_fit_128_bits():
    for rule in rules():
        assert widest_bits(rule) < 128


def test_it_steers_to_the_target_rate():
    rule = rules()[1]                                 # the bootstrap, whose smoothing is 999/1000
    hashes = 4 * TWO64 * rule.rate / (SLOTS_PER_BLOCK * rule.cap)
    claims, _ = simulate(rule, [(200_000, hashes)], 5, settled_target(rule, hashes))
    assert abs(statistics.mean(claims[50_000:]) / rule.rate - 1) < 0.03


def test_rounding_does_not_bias_it_at_the_scale_of_the_caps():
    for rule in rules():
        assert abs(rounding_bias(rule, rule.cap, 100_000, 7) - 1) < 0.001
