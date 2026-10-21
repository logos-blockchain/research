"""Gates for settlement after a wait of T slots (src/finality_sim/slots.py, SLOTS.md K.1)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from numba import njit

from finality_sim.elapsed import log_fail
from finality_sim.grr_attack import timelines as worst_timelines
from finality_sim.race import race_depths
from finality_sim.recovery import occupancy
from finality_sim.slots import (lead_law, log_fail_all, race_wait, race_wait_longest, rates,
                                wait_logfail, worst_logbound)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from b2_settlement import upper  # noqa: E402

F = 1 / 30
G = 0.845


def test_the_chance_at_every_depth_is_b4s():
    """``log_fail_all`` is ``elapsed.log_fail`` at every depth, in one pass."""
    for alpha, t in ((0.25, 400.0), (0.3, 3_000.0), (1 / 3, 12_000.0)):
        a, h = rates(alpha, G)
        allv = log_fail_all(400, t, a, h)
        for n in (1, 3, 17, 80, 250, 400):
            assert allv[n] == pytest.approx(log_fail(n, t, a, h), rel=1e-9, abs=1e-11)


@pytest.fixture(scope="module")
def model_timelines():
    """Independent slots at the closed form's rates, as B4's model timelines."""
    a, h = rates(0.25, G)
    rng = np.random.default_rng(11)
    out = []
    for _ in range(64):
        canon = np.nonzero(rng.random(80_000) < h)[0].astype(np.int64)
        adv = np.nonzero(rng.random(80_000) < a)[0].astype(np.int64)
        out.append((canon, adv))
    return out


def test_the_wait_matches_the_race_on_its_model(model_timelines):
    """The closed form against the premined race played on the model's slots, scored ``T`` slots
    after each target, at waits where the chance is near one in a hundred."""
    waits = (500, 900, 1_300)
    succ = np.zeros(len(waits))
    n = 0
    for canon, adv in model_timelines:
        s, scored = race_wait(canon, adv, waits, premine=True)
        succ += s
        n += scored
    assert n > 80_000
    for i, t in enumerate(waits):
        p = math.exp(wait_logfail(t, 0.25, G))
        assert 2e-3 < p < 0.1
        assert abs(succ[i] / n - p) <= 4 * math.sqrt(p / n), (t, succ[i] / n, p)


def test_a_wait_on_a_regular_chain_is_a_depth():
    """With one canonical block every ``c`` slots, a wait of ``d·c`` slots, or up to ``c − 1``
    more, accepts with the race's state at depth ``d``: target by target, the race beats the
    wait exactly when it beats the depth."""
    rng = np.random.default_rng(3)
    c, d_max = 40, 30
    canon = np.arange(0, 400_000, c, dtype=np.int64)
    adv = np.nonzero(rng.random(400_000) < 0.018)[0].astype(np.int64)
    deepest = race_depths(canon, adv, d_max, premine=True)
    for extra in (0, c - 1):
        longest = race_wait_longest(canon, adv, [d * c + extra for d in range(1, d_max + 1)])
        both = (deepest >= 0) & (longest >= 0)
        assert both.sum() > 9_000
        for d in (1, 2, 4, 9, 20, 30):
            beat_depth = deepest[both] >= d
            beat_wait = longest[both] >= d * c + extra
            assert beat_depth.sum() > 0
            assert np.array_equal(beat_depth, beat_wait), (d, extra)


@njit(cache=True)
def _walk_samples(p_a, p_h, delta, n_slots, burn, every, seed):
    """The excess of the coalition's wins over the honest renewals since any earlier slot, in
    one run, sampled every ``every`` slots after ``burn``."""
    np.random.seed(seed)
    out = np.empty((n_slots - burn) // every + 1, np.int64)
    w, dead, k = 0, 0, 0
    for t in range(n_slots):
        a = np.random.random() < p_a
        h = np.random.random() < p_h
        r = 0
        if dead > 0:
            dead -= 1
        elif h:
            r, dead = 1, delta
        w = max(0, w + (1 if a else 0) - r)
        if t >= burn and (t - burn) % every == 0:
            out[k] = w
            k += 1
    return out[:k]


def test_the_lead_law_is_the_walk_it_stands_for():
    """``lead_law`` against the walk sampled in 30 independent runs: above it, within the runs'
    error, at every level, and at most a tenth above it where the tail is measured well."""
    alpha, delta = 0.3, 10
    p_a, p_h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    law = lead_law(p_a, p_h, delta)
    tail = np.cumsum(law[::-1])[::-1]
    runs = [_walk_samples(p_a, p_h, delta, 400_000, 20_000, 50, s) for s in range(30)]
    for z in range(1, 9):
        per = np.array([np.mean(r >= z) for r in runs])
        se = per.std(ddof=1) / math.sqrt(per.size)
        assert per.mean() <= tail[z] + 4 * se, (z, per.mean(), tail[z])
        assert tail[z] <= 1.1 * per.mean() + 4 * se, (z, per.mean(), tail[z])


def test_the_worst_bound_lies_above_the_played_attack():
    """The bound against the premined private race on the worst case's own timelines, honest
    blocks only at renewals, scored ``T`` slots after each target. It also falls with ``T``."""
    alpha, delta = 0.3, 10
    log_ub = np.log(np.minimum(upper(alpha, delta, 400), 1.0))
    waits = (600, 1_200, 2_400)
    succ = np.zeros(len(waits))
    n = 0
    for seed in range(24):
        canon, adv = worst_timelines(alpha, F, delta, 200_000, seed)
        s, scored = race_wait(canon, adv, waits, premine=True)
        succ += s
        n += scored
    bounds = [math.exp(worst_logbound(t, alpha, delta, log_ub)[0]) for t in waits]
    assert all(b2 < b1 for b1, b2 in zip(bounds, bounds[1:]))
    assert succ[0] > 100
    for i in range(len(waits)):
        rate = succ[i] / n
        assert bounds[i] >= rate - 4 * math.sqrt(max(rate, 1 / n) / n), (waits[i], rate, bounds[i])
