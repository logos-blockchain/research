"""Phase B5: the density test that automatic recovery would rest on (PLAN.md B5, H6).

A fork that diverges at block ``d`` is compared with the local chain by the blocks each holds in
the ``W`` slots after ``d`` (``fork-choice.md``, ``maxvalid-bg``). The fork wins only when it is
strictly denser. An adversary holding stake share ``alpha`` withholds its wins and builds the fork
from ``d``. One win signs a block on any branch, so the fork holds one block per slot the
adversary wins: ``N_a ~ Binomial(W, p_a)`` with ``p_a = 1 - (1 - f)^alpha``.

The honest chain's count ``N_h`` in the window, with ``p_h = 1 - (1 - f)^(1 - alpha)``:

- **random delay**: ``Binomial(W, g p_h)``, thinned by the canonical growth over ``f`` that A1
  measured (``g``);
- **worst case** of ``delta`` slots: an honest win at least ``delta + 1`` slots after the last
  counted one extends every honest chain, so ``N_h`` counts a renewal process with gaps
  ``delta + Geometric(p_h)``, and ``P(N_h >= n) = P(Binomial(W - n delta, p_h) >= n)``. The
  probability mass is taken from the lower tail where it is below one half, and from the upper
  tail elsewhere, so that neither difference cancels.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats


def occupancy(f: float, share: float) -> float:
    """Probability that stake share ``share`` wins a given slot."""
    return 1.0 - (1.0 - f) ** share


def honest_logpmf(w: int, ph: float, growth: float | None = None,
                  delta: int | None = None) -> np.ndarray:
    """log P(N_h = n) for n = 0..w, under random delay (``growth``) or a worst case (``delta``)."""
    n = np.arange(w + 1)
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    if growth is not None:
        return stats.binom.logpmf(n, w, growth * ph)
    ge_trials = w - n * delta                     # P(N_h >= n) = P(Bin(ge_trials, p_h) >= n)
    le_trials = w - (n + 1) * delta               # P(N_h <= n) = P(Bin(le_trials, p_h) <= n)
    log_ge = np.full(w + 2, -np.inf)              # n = 0..w+1
    ok = ge_trials >= n
    log_ge[:w + 1][ok] = stats.binom.logsf(n[ok] - 1, ge_trials[ok], ph)
    log_le = np.zeros(w + 1)                      # n = 0..w; one where N_h > n is impossible
    ok = le_trials >= n + 1
    log_le[ok] = stats.binom.logcdf(n[ok], le_trials[ok], ph)
    log_le_prev = np.concatenate(([-np.inf], log_le[:-1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        upper = log_ge[:-1] + np.log1p(-np.exp(log_ge[1:] - log_ge[:-1]))
        lower = log_le + np.log1p(-np.exp(log_le_prev - log_le))
    lower = np.where(np.isneginf(log_le), -np.inf, lower)        # below the float range
    out = np.where(log_le < math.log(0.5), lower, upper)
    return np.where(np.isfinite(log_ge[:-1]), out, -np.inf)


def log_failure(w: int, alpha: float, f: float, growth: float | None = None,
                delta: int | None = None, honest: float | None = None) -> float:
    """Natural log of P(N_a > N_h): the adversary's fork is strictly denser in a window of w.

    The fork carries the share ``alpha``; the honest chain the share ``honest``, by default
    ``1 - alpha``. They differ when the fork also signs with keys of stake that was honest then.
    """
    pa = occupancy(f, alpha)
    ph = occupancy(f, 1.0 - alpha if honest is None else honest)
    n = np.arange(w + 1)
    return float(special.logsumexp(honest_logpmf(w, ph, growth, delta)
                                   + stats.binom.logsf(n, w, pa)))


def honest_rate(alpha: float, f: float, growth: float | None = None,
                delta: int | None = None) -> float:
    """The honest chain's blocks per slot in each model."""
    ph = occupancy(f, 1.0 - alpha)
    return growth * ph if growth is not None else 1.0 / (delta + 1.0 / ph)


def window_needed(alpha: float, eps: float, f: float, growth: float | None = None,
                  delta: int | None = None, w_max: int = 2_000_000) -> int | None:
    """Smallest window (slots) whose failure is at most eps; None past the threshold or w_max."""
    if occupancy(f, alpha) >= honest_rate(alpha, f, growth, delta):
        return None
    target = math.log(eps)

    def ok(w: int) -> bool:
        return log_failure(w, alpha, f, growth, delta) <= target

    hi = 64
    while not ok(hi):
        hi *= 2
        if hi > w_max:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi
