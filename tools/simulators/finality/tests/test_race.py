"""Gates for the private-chain race (src/finality_sim/race.py).

On a timeline where each block is the adversary's with probability q, independently, the race
without premining is the classic double-spend race. The receiver accepts after K blocks on top
of the target, so the honest chain holds n = K + 1 blocks counting the target while the attacker
holds M, negative binomial. From there a +-1 walk with up-probability q decides.

- Ties to the attacker (``win_at = 0``): Rosenfeld's race, P = I_{4pq}(n, 1/2) (Grunspan and
  Perez-Marco, Theorem 1; gated in firstlook.py).
- Strictly longer (``win_at = 1``): P = P(M >= n + 1) + sum_{m <= n} NB(m) (q/p)^(n + 1 - m).

With premining the coalition's lead just before the target is stationary, geometric with ratio
q/p, in place of its wins since the parent.
"""

import numpy as np
import pytest
from scipy import special, stats

from finality_sim.race import race


def bernoulli_timeline(q: float, n: int, seed: int):
    rng = np.random.default_rng(seed)
    adv = rng.random(n) < q
    slots = np.arange(n, dtype=np.int64)
    return slots[~adv], slots[adv]


def strict(q: float, n: int) -> float:
    p = 1 - q
    m = np.arange(n + 1)
    behind = (stats.nbinom.pmf(m, n, p) * (q / p) ** (n + 1 - m)).sum()
    return float(stats.nbinom.sf(n, n, p) + behind)


def closed(q: float, k: int, premine: bool, win_at: int) -> float:
    """Success at acceptance depth k: the lead at the target (stationary with premining, the wins
    since the parent without), plus the wins during k blocks, then a +-1 walk."""
    p, rho = 1 - q, q / (1 - q)
    m = np.arange(400)
    pm = stats.nbinom.pmf(m, k, p)
    lead = np.arange(200)
    pl = (1 - rho) * rho ** lead if premine else p * q ** lead
    need = (k + 1 + win_at) - (lead[:, None] + m[None, :])
    return float((pl[:, None] * pm[None, :] * np.where(need <= 0, 1.0, rho ** np.maximum(need, 0))).sum())


def test_the_closed_forms_agree():
    for q in (0.1, 0.25):
        for k in range(1, 9):
            assert closed(q, k, False, 1) == pytest.approx(strict(q, k + 1), rel=1e-9)
            assert closed(q, k, False, 0) == pytest.approx(
                special.betainc(k + 1, 0.5, 4 * q * (1 - q)), rel=1e-9)


@pytest.mark.parametrize("q", [0.1, 0.25])
@pytest.mark.parametrize("win_at", [0, 1])
@pytest.mark.parametrize("premine", [False, True])
def test_the_race_matches_its_closed_form(q, win_at, premine):
    canon, adv = bernoulli_timeline(q, 400_000, seed=7)
    succ, scored = race(canon, adv, k_max=8, premine=premine, win_at=win_at)
    checked = 0
    for k in range(1, 9):
        want = closed(q, k, premine, win_at)
        if want * scored < 100:                 # too few successes to test at this depth
            continue
        se = np.sqrt(want * (1 - want) / scored)
        # overlapping targets are correlated; allow 6 naive standard errors
        assert abs(succ[k - 1] / scored - want) <= 6 * se, (k, succ[k - 1] / scored, want)
        checked += 1
    assert checked >= 4
