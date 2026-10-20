"""Gates for the convergence-opportunity bound (finality_sim.cobound)."""

import math

import numpy as np
from scipy.stats import skellam

from finality_sim import cobound
from finality_sim.delayfc import curve

F = 1 / 30


def test_the_bound_lies_above_every_attack():
    """Every exact attack of J.2, with ties steered and under a fixed rule, stays below the bound
    at every depth, for targets that open a phase, as J.2's do: with one move per win against
    the bound with one event per win, and with retraction, two moves per win, against the bound
    with two. Under the fixed rule with retraction the attack switches between its two balanced
    states by backward induction, the strongest that keeps a move's direction."""
    for alpha, delta, events, modes in (
            (0.30, 1, 1, ("attack", "balance", "private")),
            (0.30, 5, 1, ("attack", "balance", "private")),
            (0.20, 1, 2, ("attack", "balance"))):
        bound = cobound.error_curve(F, alpha, delta, events, 60_000, opens_phase=True)
        for mode in modes:
            for ties in ("fixed",) if mode == "private" else ("fixed", "steered"):
                best = {"policy": "best"} if events == 2 and ties == "fixed" else {}
                c = curve(F, alpha, delta, ties, mode, 60_000, moves=events, **best)
                attack = c["hold" if mode == "balance" else "ever"]
                assert attack.size <= bound.size
                assert np.all(attack <= bound[: attack.size] * (1 + 1e-9) + 1e-15)


def _slot_level(alpha, delta, events, depth, n, seed, burn=150_000, margin=150_000):
    """The bound's event, max over v < s_B and u >= s_B + T of Y(v, u) >= -2, on drawn slots:
    the share of honest slots that meet it."""
    lam_h, lam_a = cobound.rates(F, alpha)
    rng = np.random.default_rng(seed)
    h, a = rng.poisson(lam_h, n), rng.poisson(lam_a, n)
    busy = np.concatenate(([0], np.cumsum(h > 0)))
    s = np.arange(delta, n - delta)
    co = np.zeros(n, bool)
    co[s] = ((h[s] == 1) & (busy[s] - busy[s - delta] == 0)
             & (busy[s + delta + 1] - busy[s + 1] == 0))
    confirmed = np.zeros(n)
    confirmed[delta:] = co[: n - delta]
    walk = np.cumsum(events * a - confirmed)
    low = np.minimum.accumulate(walk)
    high = np.maximum.accumulate(walk[::-1])[::-1]
    targets = np.nonzero(h[burn : n - margin] > 0)[0] + burn
    return float(np.mean(high[targets + depth] - low[targets - 1] >= -2))


def test_the_chain_matches_a_slot_level_count():
    """32 independent draws of 1.5 million slots each, against the chain, within 4 standard
    errors, with one event per win and with two."""
    for alpha, delta, events, depth in ((0.25, 2, 1, 500), (0.20, 5, 2, 3000)):
        exact = cobound.error_curve(F, alpha, delta, events, depth)[depth]
        runs = np.array([_slot_level(alpha, delta, events, depth, 1_500_000, 100 + r)
                         for r in range(32)])
        sem = runs.std(ddof=1) / math.sqrt(runs.size)
        assert abs(runs.mean() - exact) < 4 * sem


def test_with_no_delay_the_bound_is_the_continuous_race():
    """At Δ = 0 an opportunity is a slot with one honest block; in slots fifty times finer the
    bound is the race of a walk up at the coalition's rate and down at the honest one, with the
    premined lead geometric of ratio ρ = λ_a / λ_h, the target's own step, and a deficit d made
    good with chance ρ^d, in closed form."""
    alpha, k = 0.30, 50
    lam = -math.log(1 - F)
    lam_h, lam_a = (1 - alpha) * lam, alpha * lam
    rho = lam_a / lam_h
    fine = cobound.error_curve(1 - math.exp(-lam / k), alpha, 0, 1, k * 600)
    m = np.arange(200)
    d = np.arange(-600, 200)
    z = m[:, None] - 1 + d[None, :]
    reach = np.where(z >= -2, 1.0, rho ** np.maximum(0, -2 - z).astype(float))
    lead = (1 - rho) * rho ** m
    for t in (100, 300, 600):
        steps = skellam.pmf(d, lam_a * t, lam_h * t)
        closed = float((lead[:, None] * steps[None, :] * reach).sum())
        assert abs(fine[k * t] / closed - 1) < 0.01
