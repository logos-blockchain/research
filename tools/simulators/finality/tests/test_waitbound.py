"""Gates for the bound for a wait in the model of Gaži, Ren and Russell
(src/finality_sim/waitbound.py, SLOTS.md K.7)."""

import math

import numpy as np

from finality_sim.grr_attack import _symbols_timed, occupancy
from finality_sim.lcbounds import slot_pdf, ub_curve
from finality_sim.waitbound import (Chain, alphabet_for, attack_longest, count_curve, first_step,
                                    play_chain, play_one, steps, wait_curve, wait_needed)

F = 1 / 30


def test_the_pass_with_counts_is_ub_curve():
    """With LCanalysis's counts as costs and no wait, the level pass is B1's ``ub_curve``."""
    for alpha, delta_s in ((0.2, 2), (1 / 3, 10), (0.1, 5)):
        d = F * delta_s
        a = alphabet_for(alpha, d)
        states = max(30, a + 1)
        ref = ub_curve(300, slot_pdf(1 - alpha, d, a), a, states, 1e-16)
        got = count_curve(300, alpha, d, a, states, 1e-16)
        assert np.allclose(got, ref, rtol=1e-12, atol=0.0), (alpha, delta_s)


def test_the_first_step_weighs_its_length():
    """The covering step's weights sum to ``g + (1 − α)·D``: each step weighs its wait plus its
    charged span over the mean step, ``1/g`` block intervals, and the spans average
    ``(1 − α)·D/g``."""
    for alpha, delta_s in ((1 / 3, 10), (0.2, 3)):
        d = F * delta_s
        a = alphabet_for(alpha, d)
        ch = Chain(alpha, d, a, max(30, a + 1), 1e-16)
        row, e_cost, e_dst, e_prob, _, _ = ch.moves(1, 1 + delta_s, 1 + ch.sh * delta_s)
        g = math.exp(-(1 - alpha) * d)
        _, inj_weight, inj_state, _, left = first_step(ch, row, e_cost, e_dst, e_prob, F, g, 10)
        total = float((inj_weight.sum(axis=0) * inj_state.sum(axis=1)).sum()) + left
        assert abs(total - (g + (1 - alpha) * d)) < 1e-6, (alpha, delta_s, total)


def test_the_drawn_steps_follow_the_papers_symbol_law():
    """The steps drawn in continuous time follow ``PoSSlotPdf``'s law: an adversary-only symbol
    at the coalition's share; a phase of ``h`` honest successes at ``g·(1 − g)^(h − 1)``, ``D``
    given ``h`` at ``pd``, and ``A`` given ``H = 1`` and given ``(H, D) = (2, 1)`` with ``pa``'s
    means. At a third and 10 s, within four standard errors."""
    alpha, delta_s = 1 / 3, 10
    d = F * delta_s
    sp = slot_pdf(1 - alpha, d, 16)
    g = math.exp(-(1 - alpha) * d)
    parts = [steps(3_000_000, (1 - alpha) * F, alpha * F, delta_s, 50 + s) for s in range(4)]
    hs = np.concatenate([p[0] for p in parts])
    ds = np.concatenate([p[1] for p in parts])
    as_ = np.concatenate([p[2] for p in parts])

    def close(x, want, n):
        se = math.sqrt(max(want * (1 - want), 1e-12) / n)
        return abs(x - want) <= 4 * se + 1e-4

    assert close(np.mean(hs == 0), alpha, hs.size)
    hon = hs > 0
    n_h = int(hon.sum())
    for h in (1, 2, 3):
        assert close(np.mean(hs[hon] == h), g * (1 - g) ** (h - 1), n_h), h
        sel = hs == h
        for j in range(1, max(1, h - 1) + 1):
            assert close(np.mean(ds[sel] == j), sp.pd[h - 1, j - 1], int(sel.sum())), (h, j)
    for h, j in ((1, 1), (2, 1)):
        sel = (hs == h) & (ds == j)
        a = as_[sel]
        want = float(np.dot(np.arange(16), sp.pa[h - 1, j - 1]))
        assert abs(a.mean() - want) <= 4 * a.std() / math.sqrt(a.size) + 1e-4, (h, j, a.mean(), want)


def test_the_played_chain_freezes_in_the_step_the_wait_passes():
    """On a hand-built run: an adversary-only symbol ending at 10, then single honest phases
    ending at 40, 70, 100, ... From the reach 0 at a target at 0, the margin after each step is
    1, 0, −1, −2, ... A wait that passes in the first two steps fails; one that passes in the
    third, where the margin is −1 and only falls, does not."""
    n = 40
    hs = np.ones(n, np.int64)
    ds = np.ones(n, np.int64)
    as_ = np.zeros(n, np.int64)
    hs[0], ds[0], as_[0] = 0, 0, 1
    ends = np.array([10.0] + [40.0 + 30 * i for i in range(n - 1)])
    assert play_one(hs, ds, as_, ends, 0, 0, 0.0, 5.0)
    assert play_one(hs, ds, as_, ends, 0, 0, 0.0, 35.0)
    assert not play_one(hs, ds, as_, ends, 0, 0, 0.0, 65.0)


def test_the_attack_against_a_wait_on_a_known_run():
    """On a hand-built run the attack holds two chains at the public depth until the symbol that
    closes 30 slots after the first target's predecessor, and 20 after the second's."""
    d_sym = np.array([1, -1, 1, 2] + [3] * 10, np.int64)
    a_sym = np.array([0, 1, 0, 0] + [0] * 10, np.int64)
    t_sym = np.array([10, 20, 40, 70] + [100 + 30 * i for i in range(10)], np.int64)
    longest = attack_longest(d_sym, a_sym, t_sym, 1, 4)
    assert longest[1] == 30 and longest[2] == 20, longest[:4]


def test_the_bound_covers_its_chain_played_with_true_lengths():
    """The bounding chain played on steps drawn in the model's continuous time, with their true
    lengths and targets at uniform times, fails at most as often as the bound and at least 0.7
    times as often: the clock's rounding, the covering step's weight and the spans charged at
    ``h·Δ`` cost little. At a third and 10 s, where the spans are longest."""
    alpha, delta_s = 1 / 3, 10
    waits = np.array([1_800.0, 3_600.0, 7_200.0])
    curve = wait_curve(8_000, alpha, delta_s, slots=False)
    fails = np.zeros(waits.size)
    total = 0
    for seed in range(8):
        hs, ds, as_, ends = steps(4_000_000, (1 - alpha) * F, alpha * F, delta_s, seed)
        f, done = play_chain(hs, ds, as_, ends, waits, 40_000, 200, 20_000.0, 100 + seed)
        fails += f
        total += done
    for i, t in enumerate(waits):
        rate = fails[i] / total
        se = math.sqrt(rate * (1 - rate) / total)
        bound = curve[int(t) - 1]
        assert rate <= bound + 4 * se, (t, rate, bound)
        assert bound <= rate / 0.7 + 4 * se, (t, rate, bound)


def test_the_slotted_reading_covers_the_slot_lottery():
    """On per-slot lottery outcomes (``grr_attack``) a phase also holds the slot of its first
    honest success, so the coalition wins in ``Δ + 1`` slots of a lone honest success. Per honest
    phase, the coalition's wins lie at or below the slotted reading's, ``Δ + 1`` slots at
    ``−ln(1 − f)`` a slot, within 5 %, and above the continuous reading's at ``Δ`` and ``f``: by
    half at 1 s. The honest depth's spacing on slots, ``Δ + 1/p_h``, lies at or below the slotted
    reading's, ``Δ + 1 + 1/((1 − α)·λ)``."""
    lam = -math.log(1 - F)

    def mean_a(rate, delay, alpha):
        sp = slot_pdf(1 - alpha, rate * delay, 40)
        p = sp.ph[:, None, None] * sp.pd[:, :, None] * sp.pa
        return float((p * np.arange(40)[None, None, :]).sum() / p.sum())

    for alpha, delta_s in ((1 / 3, 1), (1 / 3, 10)):
        runs = [_symbols_timed(3_000_000, occupancy(F, 1 - alpha), occupancy(F, alpha), delta_s, 70 + s)
                for s in range(4)]
        d = np.concatenate([r[0] for r in runs])
        a = np.concatenate([r[1] for r in runs])[d > 0]
        se = a.std() / math.sqrt(a.size)
        slotted, continuous = mean_a(lam, delta_s + 1, alpha), mean_a(F, delta_s, alpha)
        assert a.mean() - 4 * se <= slotted <= 1.05 * a.mean(), (delta_s, a.mean(), slotted)
        assert continuous < a.mean() - 4 * se, (delta_s, a.mean(), continuous)
        if delta_s == 1:
            assert continuous < 0.6 * a.mean()
        assert delta_s + 1 / occupancy(F, 1 - alpha) <= delta_s + 1 + 1 / ((1 - alpha) * lam)
    on_slots = wait_curve(3_000, 1 / 3, 10)
    assert np.allclose(on_slots, wait_curve(3_000, 1 / 3, 11, lam, slots=False), rtol=1e-12)


def test_a_deflated_inference_is_the_lottery_at_a_raised_rate():
    """Raising both shares' rates by ``1/(1 − α)`` is the slot lottery at
    ``f' = 1 − (1 − f)^(1/(1 − α))`` with the shares unchanged, and it lengthens the wait at 10 s."""
    alpha = 1 / 3
    raised = 1 - (1 - F) ** (1 / (1 - alpha))
    dfl = wait_curve(4_000, alpha, 10, scale=1 / (1 - alpha))
    assert np.allclose(dfl, wait_curve(4_000, alpha, 10, raised), rtol=1e-12)
    assert dfl[3_599] > wait_curve(4_000, alpha, 10)[3_599]


def test_the_bound_lies_above_the_papers_attack_against_a_wait():
    """The attack the paper's lower bound plays, on per-slot lottery outcomes with every honest
    block delayed ``Δ`` (``grr_attack``), scored against waits of ``T`` slots from each target,
    succeeds at most as often as the bound on slots allows, and the bound falls with the wait.
    A long-lived fork beats many targets in a row, so the standard error is the spread of the
    runs' rates."""
    for alpha, delta_s, waits in ((1 / 3, 10, (900, 1_800, 3_600)), (0.25, 5, (450, 900, 1_800)),
                                  (1 / 3, 1, (900, 1_800, 3_600))):
        curve = wait_curve(12_000, alpha, delta_s)
        bounds = [curve[t - 1] for t in waits]
        assert all(b2 < b1 for b1, b2 in zip(bounds, bounds[1:]))
        rates = []
        for seed in range(8):
            d_sym, a_sym, t_sym = _symbols_timed(3_000_000, occupancy(F, 1 - alpha),
                                                 occupancy(F, alpha), delta_s, seed)
            longest = attack_longest(d_sym, a_sym, t_sym, 2_000, 60)
            scored = longest[longest > -2]
            rates.append([(scored >= t).mean() for t in waits])
        rates = np.array(rates)
        mean, se = rates.mean(axis=0), rates.std(axis=0, ddof=1) / math.sqrt(len(rates))
        assert mean[0] > 1e-3, (alpha, mean)
        for i, t in enumerate(waits):
            assert mean[i] <= bounds[i] + 3 * se[i], (alpha, delta_s, t, mean[i], se[i], bounds[i])


def test_the_wait_needed_reads_the_curve():
    curve = np.array([0.5, 0.2, 1e-3, 1e-7, 1e-10])
    assert wait_needed(curve, 1e-3) == 3
    assert wait_needed(curve, 1e-9) == 5
    assert wait_needed(curve, 1e-12) == -1
