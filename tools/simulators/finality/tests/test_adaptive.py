"""Gates for the coalition's adaptive play against the observed counting rule
(src/finality_sim/adaptive.py, DESIGNS.md H.3)."""

import functools
import math

import numpy as np
import pytest

from finality_sim.adaptive import (catch_up, cycle_pmf, decay, induction, payoff, second_leader,
                                   upper_bound_sweep, view_risk, walk_lead)
from finality_sim.further import counting_ratio
from finality_sim.recovery import occupancy

F = 1 / 30


def test_the_worst_case_walk_matches_a_simulation():
    """The stationary lead and the catch-up of the walk, against cycles drawn slot by slot: a
    geometric wait for an honest win, the coalition's wins over it and the delay, the honest wins
    of the delay, and a second honest leader of the ending slot."""
    alpha, delta = 1 / 3, 10
    p_a, p_h, q2 = occupancy(F, alpha), occupancy(F, 1 - alpha), second_leader(alpha, F)
    u = cycle_pmf(p_a, p_h, delta, second=q2)
    _, tail = walk_lead(u, 400)
    c = catch_up(u, tail)
    rng = np.random.default_rng(5)

    def gains(size):
        wait = rng.geometric(p_h, size)
        return (rng.binomial(delta + wait, p_a) + rng.binomial(delta, p_h, size)
                + (rng.random(size) < q2))
    lead = np.zeros(20_000, np.int64)
    for _ in range(3_000):                                     # chains run to stationarity
        lead = np.maximum(0, lead + gains(lead.size) - 1)
    for k in (1, 2, 4, 8):
        p = np.mean(lead >= k)
        assert tail[k] == pytest.approx(p, abs=4 * math.sqrt(p * (1 - p) / lead.size))
    for x in (1, 2, 5):
        short = np.full(20_000, x, np.int64)                   # blocks short of overtaking
        won = np.zeros(short.size, bool)
        for _ in range(2_000):
            g = gains(short.size)
            won |= g >= short
            short = short - g + 1
        p = won.mean()
        assert c[x] == pytest.approx(p, abs=4 * math.sqrt(p * (1 - p) / won.size))


def test_the_walk_returns_to_a_tie_with_its_mean_gain():
    """A walk that falls by at most one a step regains its start with chance its mean gain, so
    c(1) = E[U], which is the counting ratio without a second leader; the lead's tail falls by
    Lundberg's factor."""
    alpha, delta = 0.30, 10
    p_a, p_h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    for second in (0.0, second_leader(alpha, F)):
        u = cycle_pmf(p_a, p_h, delta, second=second)
        _, tail = walk_lead(u, 600)
        mean = float((np.arange(u.size) * u).sum())
        assert catch_up(u, tail)[1] == pytest.approx(mean, rel=1e-9)
        assert tail[201] / tail[200] == pytest.approx(decay(u), rel=1e-3)
    assert float((np.arange(400) * cycle_pmf(p_a, p_h, delta)).sum()) == pytest.approx(
        counting_ratio(alpha, delta, F), rel=1e-9)


def test_the_induction_is_what_its_policy_achieves():
    """Play the induction's own choices on drawn wins and leads: the mean payoff at acceptance is
    the induction's value."""
    alpha, delta, eps = 0.25, 10, 1e-2
    got = induction(alpha, delta, eps, "bound", 200, F, policy=True)
    p_a = occupancy(F, alpha)
    kb, nh, signs, pay, lead = got["kb"], got["nh"], got["signs"], got["pay"], got["lead"]
    b_max, p_max = signs[0].shape[0] - 1, signs[0].shape[1] - 1
    rng = np.random.default_rng(17)
    size = 400_000
    b = np.zeros(size, np.int64)
    p = rng.choice(lead.size, size, p=lead)
    out = np.full(size, np.nan)
    live = np.ones(size, bool)
    for t in range(got["t_end"] + 1):
        acc = live & ((b >= kb[t]) | (t == got["t_end"]))
        out[acc] = pay[np.clip(nh[t] + 1 - p[acc], 0, pay.size - 1)]
        live &= ~acc
        if t == got["t_end"]:
            break
        win = live & (rng.random(size) < p_a)
        sign = win & signs[t][np.minimum(b, b_max), np.minimum(p, p_max)]
        b = b + sign
        p = p + (win & ~sign)
    se = out.std() / math.sqrt(size)
    assert got["value"] == pytest.approx(out.mean(), abs=4 * se)
    assert got["value"] > 1.04 * got["own"]                    # signing to time acceptance pays


def test_the_upper_bound_sweep_matches_a_direct_recursion():
    """The vectorised sweep against a recursion written state by state on a small instance."""
    delta, p_a, p_h = 2, 0.2, 0.3
    ns = np.array([3, 3, 4, 4, 4, 5, 5, 6, 6, 6, 7, 7])
    n_y, n_s = 9, 6
    stop = np.array([1.0] + [0.6 ** (y + 1) for y in range(n_y - 1)])

    @functools.lru_cache(maxsize=None)
    def value(t, phase, y, s):
        y, s = min(y, n_y - 2), min(s, n_s - 1)                # y from -1, capped as the sweep caps
        here = stop[y + 1] if y >= -1 else 1.0
        if y < -1:
            return 1.0
        if t == ns.size - 1:
            return here
        if s == 0:
            return max(here, cont(t, phase, min(y + 1, n_y - 2), 1))
        return max(here, cont(t, phase, y, s))

    def cont(t, phase, y, s):
        step = int(ns[t + 1] - ns[t])
        out = 0.0
        for won, pw in ((0, 1 - p_a), (1, p_a)):
            yy = y + step - won
            if phase == 0:
                out += pw * ((1 - p_h) * value(t + 1, 0, yy, s + step) + p_h * value(t + 1, delta, yy, s + step))
            elif phase == 1:
                out += pw * value(t + 1, 0, yy, s + step - 1)
            else:
                out += pw * value(t + 1, phase - 1, yy, s + step)
        return out
    v = np.broadcast_to(stop[None, :, None], (delta + 1, n_y, n_s)).copy()
    v = upper_bound_sweep(v, stop[None, :, None], ns, p_a, p_h)
    for phase in range(delta + 1):
        for i in range(n_y):
            for s in range(n_s):
                assert v[phase, i, s] == pytest.approx(value(0, phase, i - 1, s), rel=1e-12)


def test_a_play_breaks_the_bound_per_view_and_holds_it_per_target():
    """Signing every win on both chains while delaying honest blocks: some accepted views fail
    more often than the rule's bound and eps, yet the play fails per target well below eps."""
    r = view_risk(0.25, 10, 1e-3, 500, F)
    v = r["likeliest"]
    assert v["risk"] > 1e-3 > v["bound"] and v["coalition"] > v["honest"]
    assert r["per_target"] < 1e-3 and r["above"] < 1e-6
    pay = payoff(0.25, 10, "bound", 50, F)
    assert np.all(np.diff(pay) <= 0) and pay[0] == 1.0
