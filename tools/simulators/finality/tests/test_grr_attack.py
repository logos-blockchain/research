"""Gates for the delay-scheduling attacker (src/finality_sim/grr_attack.py)."""

import math
import sys
import pathlib

import numpy as np
import pytest

from finality_sim.grr_attack import _symbols, attack, occupancy, timelines
from finality_sim.lcbounds import error_lb, slot_pdf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from b2_settlement import alphabet_for  # noqa: E402


def test_attack_on_fine_slots_reproduces_the_lower_bound():
    """Slots ten times finer than Cryptarchia's approach the code's continuous time."""
    adv, d, scale = 0.3, 1 / 3, 10
    f, delta = 1 / (30 * scale), 10 * scale
    a = alphabet_for(adv, d)
    sp = slot_pdf(1 - adv, d, a)
    at_conf, n = np.zeros(12), 0
    for seed in range(2):
        c, _, t = attack(adv, f, delta, 100_000_000, 12, seed)
        at_conf += c
        n += t
    for k in (1, 4, 8, 12):
        p = at_conf[k - 1] / n
        se = math.sqrt(p * (1 - p) / n)
        assert p == pytest.approx(error_lb(k, sp, a, max(30, a + 1)), abs=4 * se)


def test_timelines_replay_the_symbols():
    adv, f, delta, n = 0.25, 1 / 30, 5, 2_000_000
    d_sym, a_sym = _symbols(n, occupancy(f, 1 - adv), occupancy(f, adv), delta, 3)
    honest, adv_slots = timelines(adv, f, delta, n, 3)
    phase = d_sym >= 0
    # the last phase may still be open when the run ends
    assert honest.size - d_sym[phase].sum() in (0, 1, 2, 3)
    assert adv_slots.size - a_sym.sum() in range(0, delta + 2)
    assert np.all(np.diff(honest) > delta)


def test_the_observed_attack_counts_forks_between_none_and_every_diverted_block():
    """With no forks counted the attack against the observed rule is the attack against its
    no-fork deadlines. Counting the honest depth on the competing chain accepts no more often, and
    counting every honest block off the client's chain, no more often still."""
    from finality_sim.further import counting_observed_deadlines
    from finality_sim.grr_attack import _attack_observed, _attack_rule, _symbols_timed
    alpha, f, delta = 0.30, 1 / 30, 10
    t0 = counting_observed_deadlines(alpha, delta, 1e-3, 120, (0,), f)[:, 0]
    d, a, t = _symbols_timed(4_000_000, occupancy(f, 1 - alpha), occupancy(f, alpha), delta, 7)
    blind = _attack_observed(d, a, t, t0, 2000, 2)
    assert blind[:5] == _attack_rule(d, a, t, t0, 2000) and blind[5] == 0 and blind[3] > 0
    on_l, off_s = (_attack_observed(d, a, t, t0, 2000, mode) for mode in (1, 0))
    assert blind[3] >= on_l[3] >= off_s[3]
