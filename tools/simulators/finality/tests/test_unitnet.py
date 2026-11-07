"""Gates for the transport and the privacy of counted units' votes (UNITS.md N.3, N.4, N.6)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from finality_sim import committee as cm
from finality_sim import unitnet as un
from finality_sim.privacy import attribution_days

F = 1 / 30
Q3 = 0.2 ** 3
Q_BLOCK = 1 - (1 - Q3) ** 2


def test_blends_rules_give_todays_parameters():
    """At the specification's ``V = 156`` the read limit is 20, which carries today's ``F_1 = 16``
    with the backlog draining; a node receives 1.24 MB a second."""
    assert un.TODAY_F1 == pytest.approx(16.0, rel=1e-12)
    assert un.read_limit(156) == 20
    assert un.needed_read_limit(16.0) == 20
    assert un.node_budget(20) == 150 <= 156
    for r1 in range(1, 300):
        assert un.read_limit(un.node_budget(r1)) == r1
        assert un.read_limit(un.node_budget(r1) - 1) < r1
    today = un.load(0.0, 0.0, 3)
    assert (today["r1"], today["v"]) == (20, 150)
    assert today["received_mb"] == pytest.approx(4 * 16 * 19_318 / 1e6, rel=1e-12)


def test_the_load_against_blend_load_where_they_coincide():
    """One vote a message at the specification's three layers is ``committee.blend_load``'s
    votes on top of today's cover; each further layer adds one message a connection a vote."""
    for votes in (0.0, 4 / 3, 2.27, 11.5, 50.0):
        assert un.connection_load(votes, 3) == pytest.approx(cm.blend_load(votes)[0], rel=1e-12)
        assert un.connection_load(votes, 8) - un.TODAY_F1 == pytest.approx(8 * votes, rel=1e-12)


def test_the_schedule_hides_stake_up_to_kmax():
    """In simulated rounds of a public draw, every node holding at most ``k_max`` units sends
    exactly one message, empty or not, and a node holding more sends more in some rounds."""
    rng = np.random.default_rng(3)
    kmax = 10
    held = np.concatenate([rng.integers(0, kmax + 1, size=400), [3 * kmax, 5 * kmax]])
    units, n = int(held.sum()), int(0.6 * held.sum())
    owner = np.repeat(np.arange(held.size), held)
    big = []
    for _ in range(200):
        drawn = rng.choice(units, size=n, replace=False)
        k = np.bincount(owner[drawn], minlength=held.size)
        msgs = un.schedule_messages(k, kmax)
        assert msgs.tolist() == [max(1, math.ceil(x / kmax)) for x in k.tolist()]
        assert np.all(msgs[held <= kmax] == 1)
        big.append(msgs[held > kmax])
    assert np.max(big) > 1


def test_the_count_ceiling_against_a_direct_count():
    """The most units a node holds while its drawn units exceed ``k_max`` with chance at most
    ``eps``, counted directly on a small registry; with every unit drawn it is ``k_max``."""
    units, n, kmax, eps = 300, 120, 12, 1e-4

    def tail(held):
        return sum(math.comb(held, k) * math.comb(units - held, n - k)
                   for k in range(kmax + 1, min(held, n) + 1)) / math.comb(units, n)

    direct = max(h for h in range(kmax, units + 1) if tail(h) <= eps)
    assert all(tail(h) > eps for h in range(direct + 1, units + 1))
    assert un.count_ceiling(kmax, n, units, eps) == direct
    assert un.count_ceiling(94, 30_000, 30_000, 1e-9) == 94


def test_kmax_from_the_payload():
    assert un.k_max(per_unit_proof=True) == (18_195 - 40) // 192 == 94
    assert un.k_max(per_unit_proof=False) == (18_195 - 168) // 64 == 281


def test_info_against_a_simulated_observer():
    """An observer averaging the drawn units of ``m`` attributed messages estimates the stake
    with the relative spread ``1/sqrt(m·c)``, for the public draw's hypergeometric count and the
    private draw's binomial one."""
    rng = np.random.default_rng(5)
    units, n, held, m, trials = 30_000, 5_602, 30, 20, 40_000
    k = rng.hypergeometric(held, units - held, n, size=(trials, m))
    est = k.mean(axis=1) * units / n
    assert est.std() / held == pytest.approx(1 / math.sqrt(m * un.info_public(held, n, units)),
                                              rel=0.03)
    p = 0.53
    k = rng.binomial(held, p, size=(trials, m))
    est = k.mean(axis=1) / p
    assert est.std() / held == pytest.approx(1 / math.sqrt(m * un.info_private(held, p)),
                                              rel=0.03)
    assert math.isinf(un.info_public(held, units, units))


def _first_passage(n_obs, rate_unit, rate_msg, info, epoch_s, epoch_info, rng, trials):
    """Simulated mean days until the observations reach ``n_obs``: events of the merged Poisson
    process add one observation or ``info``, and each epoch's end adds ``epoch_info``."""
    total = rate_unit + rate_msg
    epochs = math.isfinite(epoch_s) and epoch_info > 0
    out = np.empty(trials)
    for i in range(trials):
        t, have, done = 0.0, 0.0, False
        while not done:
            nxt = t + rng.exponential(1 / total)
            if epochs:
                e = math.floor(t / epoch_s) + 1
                while e * epoch_s <= nxt:
                    if have + epoch_info * e >= n_obs:
                        t, done = e * epoch_s, True
                        break
                    e += 1
                if done:
                    break
            t = nxt
            have += 1.0 if rng.random() < rate_unit / total else info
            ep = epoch_info * math.floor(t / epoch_s) if epochs else 0.0
            done = have + ep >= n_obs
        out[i] = t
    return out.mean() / 86400


def test_size_days_against_closed_forms():
    """Without attributed messages the time is the Blend report's; with messages each worth one
    observation it is the merged Poisson process's ``n/rate``; an exact sizing at an epoch's end
    with chance ``p`` takes ``E/p``."""
    s = 0.001
    rate_b = s * Q_BLOCK * F
    assert un.size_days(100, rate_b) == pytest.approx(attribution_days(s, 100, Q_BLOCK), rel=2e-3)
    assert un.size_days(100, rate_b) == pytest.approx(100 / rate_b / 86400, rel=2e-3)
    n, r, q = 5602, 600, 0.2 ** 5
    rate_v = s * n * q / r
    assert un.size_days(100, rate_b, rate_v, info=1.0) == pytest.approx(
        attribution_days(s, 100, Q_BLOCK, F, seats=n, round_s=r, q_votes=q), rel=5e-3)
    e, p = 648_000.0, 0.2
    assert un.size_days(100, 1e-12, epoch_s=e, epoch_exact=p) == pytest.approx(e / p / 86400,
                                                                              rel=5e-3)


def test_size_days_against_a_simulated_observer():
    """Messages worth several observations each, and observations added at each epoch's end, at
    the simulated first-passage mean."""
    rng = np.random.default_rng(9)
    cases = [(100, 2e-6, 4e-7, 6.9, math.inf, 0.0),
             (100, 2e-6, 1e-6, 0.69, math.inf, 0.0),
             (100, 2e-7, 0.0, 1.0, 86400.0, 30.0)]
    for n_obs, ru, rm, info, e, ei in cases:
        sim = _first_passage(n_obs, ru, rm, info, e, ei, rng, trials=4000)
        got = un.size_days(n_obs, ru, rm, info, epoch_s=e, epoch_info=ei)
        assert got == pytest.approx(sim, rel=0.03)


def test_tie_chance_and_delivery():
    assert un.tie_chance(3, 0.5) == pytest.approx(0.875, rel=1e-12)
    assert un.tie_chance(249, 0.008) == pytest.approx(1 - 0.992 ** 249, rel=1e-12)
    assert un.delivery_bound(10.344, 3) == pytest.approx(10.344, rel=1e-12)
    assert un.delivery_bound(10.344, 8) == pytest.approx(10.344 + 5 * 3, rel=1e-12)
