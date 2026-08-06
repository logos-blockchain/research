"""Free-running release-clock mixing delay for a blend relay.

Each relay releases on its own ongoing schedule whose successive intervals are
``S ~ Uniform{0,1,...,max_blend_delay}`` whole seconds (0 = release now), re-drawn after each
release. A message arrives at a stationary random phase relative to this clock, so the mixing
delay it experiences is the renewal-process **residual life** to the next release:

    covering interval  S*  is size-biased:  P(S* = s) proportional to s   (s in 1..M);
    phase within it is uniform, so residual  R = Uniform(0, S*)  seconds.

Mean residual = (2M+1)/6 seconds (= E[S^2]/(2 E[S]) for S ~ Uniform{0..M}). Returned in ms.
"""

from __future__ import annotations

import numpy as np


def mix_wait(rng: np.random.Generator, max_blend_delay: int, size: int,
             min_blend_delay: int = 0) -> np.ndarray:
    """``size`` i.i.d. mixing-delay residuals (ms) for a Uniform{min..max}-second clock.

    ``min_blend_delay`` excludes short intervals. Note it cannot change the *mean* residual: a
    zero-length interval is instantaneous, so it never covers a message arrival and is never
    sampled by the size-biased draw. Dropping mass that was never sampled leaves the mean where it
    was -- what a minimum actually removes is the chance of an interval too short to mix in.
    """
    m, lo = int(max_blend_delay), max(int(min_blend_delay), 0)
    if m <= 0 or size <= 0 or lo > m:
        return np.zeros(max(size, 0), dtype=float)
    s = np.arange(max(lo, 1), m + 1, dtype=float)    # zero-length intervals never cover an arrival
    probs = s / s.sum()                              # size-biased over the eligible intervals
    covering = rng.choice(s, size=size, p=probs)
    residual_seconds = rng.uniform(0.0, covering)    # uniform phase within the covering interval
    return residual_seconds * 1000.0                 # -> milliseconds


def mean_residual_ms(max_blend_delay: int, min_blend_delay: int = 0) -> float:
    """Analytic mean mixing delay (ms), the renewal residual ``E[S^2]/(2E[S])``.

    For ``Uniform{0..M}`` this is ``(2M+1)/6`` seconds, and excluding zero-length intervals leaves
    it unchanged -- see :func:`mix_wait`.
    """
    m, lo = int(max_blend_delay), max(int(min_blend_delay), 0)
    if m <= 0 or lo > m:
        return 0.0
    s = np.arange(lo, m + 1, dtype=float)
    if s.sum() <= 0:
        return 0.0
    return float((s * s).sum() / s.sum() / 2.0) * 1000.0


def mean_interval_s(max_blend_delay: int, min_blend_delay: int = 0) -> float:
    """Mean gap between releases, ``E[S]`` seconds -- this one *does* move with the minimum."""
    m, lo = int(max_blend_delay), max(int(min_blend_delay), 0)
    if m <= 0 or lo > m:
        return 0.0
    return float(np.arange(lo, m + 1, dtype=float).mean())
