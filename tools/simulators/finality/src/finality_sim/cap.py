"""A cap on the total-stake inference's correction, and the floor (SLOTS.md, K.8).

The inference sets each epoch's estimate ``D`` from the occupied slots of the observation period,
the first ``P = 6⌊k/f⌋`` slots of the epoch before, with a full correction
(``cryptarchia-total-stake-inference.md``, ``beta = 1``): ``D' = D·N/(f·P)``. A chain made by stake
``s`` of the true total ``S`` occupies a slot with chance ``p(s·S/D) = 1 − (1 − f)^(s·S/D)`` and,
in expectation, corrects to ``D' = D·p(s·S/D)/f``. A cap ``c`` bounds each correction from below:
``D' ≥ (1 − c)·D``. Estimates here are over ``S``.

Both forms of the floor (``floor.py``) hold a side back only while its stake over its estimate
stays low. The inference cannot tell a side cut off from the rest from stake that left, so the
cap lengthens both alike: how long a side of share ``σ`` stays below the floor, and how long
finality stalls after the active stake genuinely falls to ``r``.

- **The density form** fixes a block once the ``K`` slots after it hold ``φ`` blocks. A side,
  at its fastest one block per occupied slot, can do that with chance above ``ε`` once its
  stake over its estimate exceeds ``σ*``, the largest share the floor holds back
  (``floor.provisional_share``), a window after the correction that takes it there. A chain
  whose stake fell resumes once its stake over its estimate reaches ``r*``, the least share whose
  chain reaches ``φ`` within ``K`` with chance ``1 − ε`` (``resume_share``), a window after.
- **The depth form** fixes a block once it is ``K`` slots old and ``φ`` blocks follow it. A side
  fixes once it has made ``φ + 1`` blocks, at a rate that steps up at each correction.
- **Alignment.** Corrections take effect at epoch starts and read the period before. A split at
  a period's start is corrected first one epoch ``E`` later: the protection's earliest. A fall
  just after a period ends is first corrected ``2E − P`` later: the stall's latest.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from .floor import log_short
from .recovery import occupancy

F = 1 / 30


def correct(d: float, share: float, cap: float | None, f: float = F) -> float:
    """One correction of the estimate ``d`` for a chain made by ``share``, both over the true
    total: ``D' = D·p(share/D)/f``, at least ``(1 − cap)·D`` (``cap = None``: no cap)."""
    full = d * occupancy(f, share / d) / f
    return full if cap is None else max(full, (1.0 - cap) * d)


def estimates(share: float, cap: float | None, n: int, f: float = F) -> np.ndarray:
    """The estimate over the true total after 0..n corrections, from the true total."""
    out = np.empty(n + 1)
    out[0] = 1.0
    for j in range(1, n + 1):
        out[j] = correct(out[j - 1], share, cap, f)
    return out


def corrections_until(share: float, target: float, cap: float | None, f: float = F,
                      n_max: int = 10_000) -> int:
    """The corrections after which the chain's stake over its estimate first exceeds ``target``;
    0 if it does already, −1 if not within ``n_max``."""
    if share > target:
        return 0
    d = 1.0
    for j in range(1, n_max + 1):
        d = correct(d, share, cap, f)
        if share / d > target:
            return j
    return -1


def resume_share(w: int, phi: int, eps: float, f: float = F, growth: float | None = None,
                 delta: int | None = None) -> float:
    """The least share whose chain reaches ``φ`` blocks within ``w`` slots with chance at least
    ``1 − ε``: ``P(N < φ) ≤ ε`` (``floor.log_short``), under random delay at ``growth`` or a worst
    case of ``delta``."""
    target = math.log(eps)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if log_short(w, phi, mid, f, growth, delta) <= target else (mid, hi)
    return hi


def density_protection(sigma: float, sigma_star: float, cap: float | None, epoch: int, w: int,
                       f: float = F) -> float:
    """The slots a side of share ``σ`` stays below the density floor at its fastest, its
    corrections earliest: the correction that takes its stake over its estimate past ``σ*``, at
    ``j·E``, and a window ``w`` after it; ``w`` if it is past ``σ*`` already, inf if never."""
    j = corrections_until(sigma, sigma_star, cap, f)
    if j < 0:
        return math.inf
    return j * epoch + w


def density_stall(r: float, r_star: float, cap: float | None, epoch: int, period: int, w: int,
                  f: float = F) -> float:
    """The slots finality stalls under the density form after the active stake falls to ``r``,
    its corrections latest: the correction that takes its stake over its estimate to ``r*``, the
    first at ``2E − P`` and one an epoch after, and a window ``w`` after it; 0 if ``r`` reaches
    ``r*`` already."""
    if r >= r_star:
        return 0.0
    j = corrections_until(r, r_star * (1 - 1e-12), cap, f)
    if j < 0:
        return math.inf
    return (2 * epoch - period) + (j - 1) * epoch + w


def _rates(share: float, cap: float | None, first: float, epoch: int, n: int, f: float,
           growth: float | None, delta: int | None) -> tuple[np.ndarray, np.ndarray]:
    """The chain's blocks per slot between corrections: from 0, then from ``first`` and every
    epoch after, as its estimate falls. One block per occupied slot unless ``growth``; the
    renewal rate ``1/(Δ + 1/p)`` under a worst case of ``delta``."""
    est = estimates(share, cap, n, f)
    starts = np.concatenate(([0.0], first + epoch * np.arange(n)))
    rates = np.empty(n + 1)
    for j in range(n + 1):
        p = occupancy(f, share / est[j])
        rates[j] = 1.0 / (delta + 1.0 / p) if delta is not None else (growth or 1.0) * p
    return starts, rates


def blocks_by(n_blocks: int, share: float, cap: float | None, first: float, epoch: int,
              eps: float | None = None, f: float = F, growth: float | None = None,
              delta: int | None = None, n_corr: int = 400) -> float:
    """The slot by which a chain made by ``share`` holds ``n_blocks``, its rate stepping up at each
    correction (the first at ``first``, then every epoch): on average, or, with ``eps``, the
    earliest slot at which it holds them with chance ``eps``, the count Poisson over the rates,
    whose upper tail exceeds the binomial's."""
    starts, rates = _rates(share, cap, first, epoch, n_corr, f, growth, delta)
    ends = np.append(starts[1:], math.inf)
    if eps is None:
        need = float(n_blocks)
        for s, e, r in zip(starts, ends, rates):
            if need <= r * (e - s):
                return s + need / r
            need -= r * (e - s)
        return math.inf

    def mean_at(t: float) -> float:
        m = 0.0
        for s, e, r in zip(starts, ends, rates):
            if t <= s:
                break
            m += r * (min(t, e) - s)
        return m

    target = math.log(eps)
    lo, hi = 0.0, 1.0
    while stats.poisson.logsf(n_blocks - 1, mean_at(hi)) < target:
        lo, hi = hi, hi * 2
        if hi > 1e12:
            return math.inf
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if stats.poisson.logsf(n_blocks - 1, mean_at(mid)) >= target else (mid, hi)
    return hi


def depth_protection(sigma: float, phi: int, cap: float | None, epoch: int, w: int,
                     eps: float | None = None, f: float = F) -> float:
    """The slots a side of share ``σ``, at its fastest, takes to fix a fork under the depth form,
    its corrections earliest: ``φ + 1`` blocks, and its first block ``w`` slots old."""
    first = 1.0 / occupancy(f, sigma) if eps is None else 0.0
    return max(w + first, blocks_by(phi + 1, sigma, cap, epoch, epoch, eps, f))


def depth_finality(r: float, phi: int, cap: float | None, epoch: int, period: int, w: int,
                   f: float = F, growth: float | None = None, delta: int | None = None) -> float:
    """The slots until a block made just as the active stake falls to ``r`` is fixed under the
    depth form, on average, its corrections latest: ``w`` slots, or ``φ`` blocks after it if they
    take longer."""
    return max(float(w), blocks_by(phi, r, cap, 2 * epoch - period, epoch, None, f, growth, delta))


def slow(r: float, cap: float | None, epoch: int, period: int, within: float = 0.05,
         f: float = F) -> float:
    """The slots after a fall to ``r``, its corrections latest, until the chain fills its slots
    within ``within`` of ``f`` again."""
    if occupancy(f, r) >= (1 - within) * f:
        return 0.0
    j = corrections_until(r, math.log(1 - (1 - within) * f) / math.log(1 - f), cap, f)
    if j < 0:
        return math.inf
    return 2 * epoch - period + (j - 1) * epoch


def _tdiv(a: int, b: int) -> int:
    """Integer division toward zero, as Rust's."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def spec_correction(tse: int, occupied: int, period: int, f: float, beta: float = 1.0) -> int:
    """``total_stake_inference`` of ``cryptarchia-total-stake-inference.md`` at ``47a73cdc``, in
    its integer arithmetic: ``PRECISION = 1e3``, ``f_p = truncate(f·PRECISION)``."""
    precision = 1000
    beta_p = int(beta * precision)
    f_p = int(f * precision)
    tse_p = tse * precision
    measured_p = occupied * precision
    expected_p = period * f_p
    error_p = _tdiv(tse_p * (expected_p - measured_p), expected_p)
    correction_p = _tdiv(beta_p * error_p, precision)
    return max(_tdiv(tse_p - correction_p, precision), 1)


def spec_rate(f: float, period: int, stake: int = 10**12, n: int = 60) -> float:
    """The occupied slots per slot at which the specification's inference rests, with every unit
    of ``stake`` producing: the estimate corrected ``n`` times from the true stake on the expected
    count of occupied slots."""
    d = stake
    for _ in range(n):
        d = spec_correction(d, round(period * occupancy(f, stake / d)), period, f)
    return occupancy(f, stake / d)
