"""Release designs: a minimum interval, and jitter vs clock-tick release under a timing attack."""

import numpy as np

from blend.config import SimConfig
from blend.graph import build_graph
from blend.mixclock import mean_interval_s, mean_residual_ms, mix_wait
from blend.traffic import ReleaseClock, simulate_window, timing_linkability, traffic_metrics


def _run(mode="clock", M=30, lo=0, rate=1.0, slots=120, n=2000, seed=3):
    cfg = SimConfig(n_nodes=n, degree=8, blend_hops=3, max_blend_delay=M, min_blend_delay=lo,
                    release_mode=mode, cover_rate_mult=rate)
    g = build_graph(cfg)
    w = simulate_window(g, cfg, np.random.default_rng(seed), slots)
    return traffic_metrics(w, cfg), timing_linkability(w, cfg)


# --- the minimum interval -------------------------------------------------------------------------

def test_a_minimum_interval_does_not_change_the_mean_hold():
    """A zero-length gap is instantaneous, so it never covers an arrival and is never sampled.
    Excluding it removes mass the residual never saw -- the mean hold is identical."""
    for M in (3, 10, 30):
        assert abs(mean_residual_ms(M, 0) - mean_residual_ms(M, 1)) < 1e-9


def test_a_minimum_interval_does_lengthen_the_gap_between_releases():
    """What it does change is E[S]: release opportunities become rarer."""
    for M in (3, 10, 30):
        assert mean_interval_s(M, 1) > mean_interval_s(M, 0)


def test_sampled_holds_match_the_analytic_mean_with_and_without_a_minimum():
    rng = np.random.default_rng(0)
    for M in (3, 30):
        for lo in (0, 1):
            got = float(np.mean(mix_wait(rng, M, 60_000, lo)))
            assert abs(got - mean_residual_ms(M, lo)) < 0.05 * mean_residual_ms(M, lo)


def test_clock_respects_the_minimum_interval():
    c = ReleaseClock(5, np.random.default_rng(0), min_blend_delay=2)
    c.next_tick_at_or_after(200.0)
    gaps = [b - a for a, b in zip(c._ticks, c._ticks[1:], strict=False)]
    assert all(2 - 1e-9 <= g <= 5 + 1e-9 for g in gaps)


def test_the_minimum_does_not_measurably_change_anonymity():
    """Follows from the mean hold being unchanged: blending and linkability track it."""
    a, ta = _run(lo=0)
    b, tb = _run(lo=1)
    assert abs(a["hold_seconds_mean"] - b["hold_seconds_mean"]) < 0.5
    assert abs(ta["timing_linked_frac"] - tb["timing_linked_frac"]) < 0.05


# --- jitter vs clock ------------------------------------------------------------------------------

def test_both_designs_cost_the_same_delay():
    """The comparison is only meaningful at a matched latency budget."""
    c, _ = _run("clock")
    j, _ = _run("jitter")
    assert abs(c["hold_seconds_mean"] - j["hold_seconds_mean"]) < 1.0


def test_timing_linkage_is_near_total_at_the_baseline_rate():
    """The headline: a relay handles so little traffic that in->out matching is trivial under
    EITHER design, so neither provides timing protection at one message per second."""
    for mode in ("clock", "jitter"):
        _, t = _run(mode, rate=1.0)
        assert t["map_success"] > 0.9
        assert t["timing_set_mean"] < 1.3


def test_more_traffic_is_what_buys_timing_protection():
    _, lo_rate = _run("clock", rate=1.0)
    _, hi_rate = _run("clock", rate=64.0, slots=60)
    assert hi_rate["timing_set_mean"] > lo_rate["timing_set_mean"]
    assert hi_rate["map_success"] < lo_rate["map_success"]


def test_perplexity_flatters_jitter_more_than_the_best_guess_does():
    """A heavy tail keeps old arrivals nominally possible while contributing almost nothing, so
    the effective-set advantage of jitter overstates its real advantage under a MAP attack."""
    _, c = _run("clock", rate=64.0, slots=60)
    _, j = _run("jitter", rate=64.0, slots=60)
    set_gain = j["timing_set_mean"] / c["timing_set_mean"]
    map_gain = (1 - j["map_success"]) / (1 - c["map_success"])
    assert set_gain > 1.0 and map_gain > 1.0        # jitter wins on both
    assert set_gain > map_gain                      # but the set measure overstates by how much


def test_knowing_the_tick_schedule_gains_the_adversary_nothing():
    """The clock design concedes the same whether or not the observer knows the tick times.

    A silent tick implies nothing was pending at it, and any arrival older than the previous
    release has demonstrably already left. So the candidate window bounded by the true previous
    tick and the one bounded by the previous observed release contain the same arrivals. This
    matters because it removes the obvious objection to the jitter-vs-clock comparison: the clock
    design is not being handicapped by a generous adversary assumption.
    """
    for n, rate, slots in ((2000, 1.0, 120), (200, 32.0, 90)):     # sparse and dense
        cfg = SimConfig(n_nodes=n, degree=8, blend_hops=3, max_blend_delay=30,
                        release_mode="clock", cover_rate_mult=rate)
        g = build_graph(cfg)
        w = simulate_window(g, cfg, np.random.default_rng(5), slots)
        strong = timing_linkability(w, cfg, adversary_knows_schedule=True)
        weak = timing_linkability(w, cfg, adversary_knows_schedule=False)
        assert abs(strong["timing_set_mean"] - weak["timing_set_mean"]) < 1e-9
        assert abs(strong["map_success"] - weak["map_success"]) < 1e-9


def test_jitter_beats_the_clock_at_a_matched_delay_budget():
    """The verdict, on the measure a heavy tail cannot flatter: at equal mean delay the
    independent-draw design leaves the adversary's best guess wrong more often."""
    _, c = _run("clock", rate=64.0, slots=60)
    _, j = _run("jitter", rate=64.0, slots=60)
    assert j["map_success"] < c["map_success"]
    assert j["timing_set_mean"] > c["timing_set_mean"]
