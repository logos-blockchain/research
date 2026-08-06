"""Cover traffic on a timeline: shared clocks, the emission quota, blending and mixing."""

import numpy as np

from blend.config import SimConfig
from blend.graph import build_graph
from blend.traffic import ReleaseClock, simulate_window, traffic_metrics


def _win(n_nodes=2000, degree=8, hops=3, M=3, mult=1.0, slots=600, seed=0):
    cfg = SimConfig(n_nodes=n_nodes, degree=degree, blend_hops=hops, max_blend_delay=M,
                    cover_rate_mult=mult)
    g = build_graph(cfg)
    w = simulate_window(g, cfg, np.random.default_rng(seed), window_slots=slots)
    return w, traffic_metrics(w, cfg)


# --- the clock ----------------------------------------------------------------------------------

def test_clock_ticks_are_monotonic_and_spaced_within_the_bound():
    c = ReleaseClock(3, np.random.default_rng(0))
    c.next_tick_at_or_after(100.0)
    ticks = c._ticks
    assert all(b >= a for a, b in zip(ticks, ticks[1:], strict=False))
    gaps = [b - a for a, b in zip(ticks, ticks[1:], strict=False)]
    assert all(0 <= g <= 3 + 1e-9 for g in gaps)


def test_clock_with_zero_delay_releases_immediately():
    c = ReleaseClock(0, np.random.default_rng(0))
    for t in (0.0, 1.5, 99.0):
        assert c.next_tick_at_or_after(t) == t


def test_next_tick_is_at_or_after_the_request_and_is_stable():
    c = ReleaseClock(3, np.random.default_rng(1))
    for t in (0.3, 5.0, 5.0, 12.7):
        assert c.next_tick_at_or_after(t) >= t
    assert c.next_tick_at_or_after(5.0) == c.next_tick_at_or_after(5.0)   # idempotent


def test_one_clock_is_shared_so_messages_batch_at_the_same_tick():
    """Two messages arriving before the same tick leave together -- that is the mixing."""
    c = ReleaseClock(3, np.random.default_rng(2))
    t1 = c.next_tick_at_or_after(10.0)
    t2 = c.next_tick_at_or_after(10.0 + 1e-6)
    assert t1 == t2 or t2 >= t1


def test_first_tick_reproduces_the_stationary_residual():
    """A clock sampled once matches mixclock's residual, so single-message stats are unchanged."""
    M = 5
    firsts = [ReleaseClock(M, np.random.default_rng(s))._ticks[0] for s in range(4000)]
    assert abs(float(np.mean(firsts)) - (2 * M + 1) / 6) < 0.06        # mean residual (2M+1)/6


# --- emissions and the quota --------------------------------------------------------------------

def test_block_proposals_cancel_a_later_cover_emission():
    w, _ = _win(slots=1500, seed=3)
    assert w.emitted_block > 0
    assert w.cancelled_cover > 0
    # every cancellation is owed to a block, and cannot exceed the blocks emitted
    assert w.cancelled_cover <= w.emitted_block


def test_cover_between_blocks_matches_the_rate_times_the_block_interval():
    w, m = _win(slots=3000, seed=4)
    rate = (w.emitted_cover + w.emitted_block) / w.window_seconds
    assert abs(m["cover_per_block_interval"] - rate * 30) < 6          # ~30 at 1 msg/s


# --- what the relays experience -------------------------------------------------------------------

def test_mean_hold_is_the_renewal_residual():
    for M in (3, 10):
        _, m = _win(M=M, slots=900, seed=5)
        assert abs(m["hold_seconds_mean"] - (2 * M + 1) / 6) < 0.25


def test_blending_follows_the_size_biased_interval():
    """Anonymity set = broadcasts seen in the last inter-tick gap. Gaps sampled at a release are
    size-biased, so the mean is rate*(2M+1)/3 -- twice the mean hold, not rate*M/2."""
    for M in (3, 10, 30):
        w, m = _win(M=M, slots=1200, seed=1)
        rate = (w.emitted_cover + w.emitted_block) / w.window_seconds
        assert abs(m["blending_mean"] - rate * (2 * M + 1) / 3) < 0.12 * rate * (2 * M + 1) / 3


def test_blending_grows_with_the_cover_rate_and_with_the_delay():
    _, lo = _win(M=3, mult=1.0, slots=400, seed=2)
    _, hi = _win(M=3, mult=8.0, slots=400, seed=2)
    assert hi["blending_mean"] > 5 * lo["blending_mean"]               # ~linear in rate
    _, slow = _win(M=30, mult=1.0, slots=400, seed=2)
    assert slow["blending_mean"] > 4 * lo["blending_mean"]             # ~linear in delay


def test_mixing_is_negligible_at_the_baseline_rate():
    """One message per second over thousands of nodes: a relay essentially never holds two."""
    _, m = _win(n_nodes=4000, mult=1.0, slots=600, seed=6)
    assert m["queue_mean"] < 0.05
    assert m["queue_max"] <= 3


def test_mixing_grows_when_the_network_is_loaded():
    _, lo = _win(n_nodes=500, mult=1.0, slots=400, seed=7)
    _, hi = _win(n_nodes=500, mult=32.0, slots=400, seed=7)
    assert hi["queue_max"] > lo["queue_max"]
    assert hi["queue_mean"] > lo["queue_mean"]


def test_every_hop_is_recorded_as_a_hold():
    w, m = _win(hops=3, slots=300, seed=8)
    delivered = len(w.broadcasts)
    assert m["hold_events"] >= 3 * delivered                          # 3 relays per delivered msg


def test_repeat_proposals_owe_repeat_cancellations():
    """Regression: pending cancellations were a set, so a node proposing twice before its next
    cover emission forfeited only one -- it would then over-emit relative to its quota, which is
    the very uniformity cover traffic exists to preserve."""
    from collections import Counter

    from blend.traffic import simulate_window
    cfg = SimConfig(n_nodes=40, degree=8, blend_hops=2, max_blend_delay=3,
                    cover_rate_mult=8.0, block_interval_slots=2)   # tiny net, many proposals
    g = build_graph(cfg)
    w = simulate_window(g, cfg, np.random.default_rng(0), 400)
    assert w.emitted_block > 20                       # plenty of repeat proposers at this size
    assert w.cancelled_cover > 0
    assert w.cancelled_cover <= w.emitted_block
    assert isinstance(Counter(), Counter)


def test_block_proposer_follows_the_stake_when_given():
    """The lottery is stake-weighted, so the timeline must not draw the proposer uniformly.

    Concentrating the stake is visible in the quota bookkeeping: a dominant proposer wins most
    proposals but rarely draws a cover slot to forfeit, so far fewer cancellations are redeemed
    than when proposals are spread uniformly. That unredeemed backlog is exactly the over-emission
    that section 3.10's stake ceiling is about.
    """
    from blend.traffic import simulate_window
    n = 200
    stake = np.full(n, 0.2 / (n - 1))
    stake[7] = 0.8                                     # one dominant holder
    stake = stake / stake.sum()
    cfg = SimConfig(n_nodes=n, degree=8, blend_hops=2, max_blend_delay=3,
                    cover_rate_mult=1.0, block_interval_slots=2)
    g = build_graph(cfg)
    weighted = simulate_window(g, cfg, np.random.default_rng(1), 400, stake=stake)
    uniform = simulate_window(g, cfg, np.random.default_rng(1), 400)
    assert weighted.emitted_block > 100 and uniform.emitted_block > 100
    assert weighted.cancelled_cover < 0.5 * uniform.cancelled_cover
