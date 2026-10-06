"""Gates for the confirmation rule that reads elapsed time (src/finality_sim/elapsed.py)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from finality_sim.elapsed import deadlines, log_fail, settle
from finality_sim.race import race, race_depths

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from b5_what_k_holds import log_strict  # noqa: E402

F = 1 / 30
A, H = 1 - (1 - F) ** 0.25, 0.845 * (1 - (1 - F) ** 0.75)


def test_averaged_over_arrival_times_the_failure_is_the_depth_tables():
    """Over t ~ Gamma(n, h), P(n, t) averages to B5's negative binomial form."""
    for n in (5, 22, 40):
        t = np.linspace(1e-6, 60 * n / H, 20_001)
        p = np.exp([log_fail(n, x, A, H) for x in t])
        mean = np.trapezoid(p * stats.gamma.pdf(t, n, scale=1 / H), t)
        assert mean == pytest.approx(math.exp(log_strict(A / (A + H), n)), rel=1e-6)


def test_deadlines_are_the_latest_times_that_settle():
    eps = 1e-6
    dl = deadlines(A, H, eps, 80)
    n = np.arange(1, 81)
    assert np.array_equal(dl[1:] >= 0, (n + 1) * math.log(A / H) <= math.log(eps))  # t = 0 settles
    assert np.all(np.diff(dl[dl >= 0]) > 0)
    for n in np.nonzero(dl >= 0)[0][::7]:
        assert log_fail(n, dl[n], A, H) <= math.log(eps) < log_fail(n, dl[n] + 1e-3, A, H)


@pytest.fixture(scope="module")
def timelines():
    rng = np.random.default_rng(5)
    out = []
    for _ in range(48):
        canon = np.nonzero(rng.random(60_000) < H)[0].astype(np.int64)
        adv = np.nonzero(rng.random(60_000) < A)[0].astype(np.int64)
        out.append((canon, adv))
    return out


def test_race_depths_count_what_race_counts(timelines):
    canon, adv = timelines[0]
    succ, scored = race(canon, adv, 40, premine=False)
    deepest = race_depths(canon, adv, 40, premine=False)
    assert (deepest >= 0).sum() == scored
    for k in range(1, 41):
        assert (deepest >= k).sum() == succ[k - 1]


def test_the_rule_holds_eps_for_the_race_it_assumes(timelines):
    eps = 0.01
    dl = deadlines(A, H, eps, 200)
    fails = n = 0
    for canon, adv in timelines:
        deepest = race_depths(canon, adv, 120, premine=False)
        k, _, _ = settle(canon, dl, 10)
        ok = (k >= 1) & (deepest >= 0)
        fails += int(np.sum(deepest[ok] >= k[ok]))
        n += int(ok.sum())
    assert n > 50_000
    assert fails / n <= eps


def test_the_rule_holds_eps_however_fast_the_blocks_came(timelines):
    """Banded by how long the depth rule's blocks took, the elapsed-time rule still holds eps in
    every band; the depth rule holds it only on average, and fails in the slowest band."""
    eps, depth = 0.01, 10
    dl = deadlines(A, H, eps, 200)
    k_all, d_all, slow = [], [], []
    for canon, adv in timelines:
        deepest = race_depths(canon, adv, 120, premine=False)
        k, _, t_depth = settle(canon, dl, depth)
        ok = (k >= 1) & (deepest >= 0) & (t_depth >= 0)
        k_all.append(deepest[ok] >= k[ok])
        d_all.append(deepest[ok] >= depth)
        slow.append(t_depth[ok])
    k_all, d_all, slow = (np.concatenate(x) for x in (k_all, d_all, slow))
    edges = np.quantile(slow, [0, 0.25, 0.5, 0.75, 0.95, 1])
    band = np.clip(np.searchsorted(edges, slow, side="right") - 1, 0, 4)
    for b in range(5):
        fail = k_all[band == b]
        assert fail.mean() <= eps + 4 * np.sqrt(eps / fail.size), (b, fail.mean())
    assert d_all[band == 4].mean() > 3 * eps
