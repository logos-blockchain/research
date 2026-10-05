"""Gates for the private-chain race (src/finality_sim/race.py).

On a timeline where each block is the adversary's with probability q, independently, the race
without premining is the classic double-spend race. The receiver accepts after K blocks on top
of the target, so the honest chain holds n = K + 1 blocks counting the target while the attacker
holds M, negative binomial. From there a +-1 walk with up-probability q decides.

- Ties to the attacker (``win_at = 0``): Rosenfeld's race, P = I_{4pq}(n, 1/2) (Grunspan and
  Perez-Marco, Theorem 1; gated in firstlook.py).
- Strictly longer (``win_at = 1``): P = P(M >= n + 1) + sum_{m <= n} NB(m) (q/p)^(n + 1 - m).
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


@pytest.mark.parametrize("q", [0.1, 0.25])
@pytest.mark.parametrize("win_at", [0, 1])
def test_race_without_premining_matches_closed_form(q, win_at):
    canon, adv = bernoulli_timeline(q, 400_000, seed=7)
    succ, scored = race(canon, adv, k_max=8, premine=False, win_at=win_at)
    for k in (1, 2, 4, 8):
        n = k + 1
        want = special.betainc(n, 0.5, 4 * q * (1 - q)) if win_at == 0 else strict(q, n)
        got = succ[k - 1] / scored
        se = np.sqrt(want * (1 - want) / scored)
        # overlapping targets are correlated; allow 6 naive standard errors
        assert abs(got - want) <= 6 * se + 1e-4, (k, got, want)


def test_premining_only_helps_the_attacker():
    canon, adv = bernoulli_timeline(0.25, 200_000, seed=3)
    s0, n0 = race(canon, adv, k_max=6, premine=False)
    s1, n1 = race(canon, adv, k_max=6, premine=True)
    assert np.all(s1 / n1 >= s0 / n0)
