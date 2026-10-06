"""Gates for the anonymous-seat committee (src/finality_sim/committee.py)."""

import numpy as np
import pytest
from scipy import stats

from finality_sim.committee import liveness_tail, safety_tail, smallest_committee


def brute_safety(n, alpha, q2, inflation):
    """P(H + 2A >= q2) by convolving the two pmfs directly, every honest seat voting."""
    top = int(3 * n * inflation + 200)
    ph = stats.poisson.pmf(np.arange(top), inflation * (1 - alpha) * n)
    p2a = np.zeros(2 * top)
    p2a[::2] = stats.poisson.pmf(np.arange(top), inflation * alpha * n)
    return float(np.convolve(ph, p2a)[q2:].sum())


@pytest.mark.parametrize("inflation", [1.0, 1.05])
def test_the_safety_tail_is_the_convolution(inflation):
    for n, alpha, q2 in ((665, 0.10, 2 * 458), (2085, 0.20, 2 * 1429), (5355, 0.25, 2 * 3642)):
        assert safety_tail(n, alpha, q2, inflation) == pytest.approx(
            brute_safety(n, alpha, q2, inflation), rel=1e-6, abs=1e-300)


def test_liveness_counts_only_the_votes_that_count():
    assert liveness_tail(5355, 0.25, 3642, awake=0.9) == pytest.approx(
        stats.poisson.cdf(3641, 0.9 * 0.75 * 5355))


@pytest.mark.parametrize("alpha, awake, inflation", [(0.25, 1.0, 1.05), (0.20, 0.9, 1.0)])
def test_the_committee_is_the_smallest_that_holds_both_tails(alpha, awake, inflation):
    eps = 1e-9
    n, q = smallest_committee(alpha, eps, awake, inflation)
    assert safety_tail(n, alpha, 2 * q, inflation) <= eps
    assert liveness_tail(n, alpha, q, awake) <= eps
    # one seat fewer: the least quorum that holds safety there already fails liveness
    m = n - 1
    q_m = next(x for x in range(q - 50, q + 50) if safety_tail(m, alpha, 2 * x, inflation) <= eps)
    assert liveness_tail(m, alpha, q_m, awake) > eps


def test_no_committee_once_the_quorum_cannot_fit():
    """A quorum must exceed inflation (1 + alpha) n / 2 and stay below awake (1 - alpha) n."""
    assert smallest_committee(1 / 3 + 1e-3, 1e-6) is None
    assert smallest_committee(0.30, 1e-6, awake=0.9) is None          # 0.63 <= 0.65
    assert smallest_committee(0.32, 1e-6, inflation=1.05) is None     # 0.68 <= 0.693
    assert smallest_committee(0.28, 1e-6, awake=0.9) is not None      # 0.648 > 0.64
