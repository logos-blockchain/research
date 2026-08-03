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


def mix_wait(rng: np.random.Generator, max_blend_delay: int, size: int) -> np.ndarray:
    """``size`` i.i.d. mixing-delay residuals (ms) for a Uniform{0..max_blend_delay}-sec clock."""
    m = int(max_blend_delay)
    if m <= 0 or size <= 0:
        return np.zeros(max(size, 0), dtype=float)
    s = np.arange(1, m + 1, dtype=float)
    probs = s / s.sum()                              # size-biased over positive intervals
    covering = rng.choice(s, size=size, p=probs)
    residual_seconds = rng.uniform(0.0, covering)    # uniform phase within the covering interval
    return residual_seconds * 1000.0                 # -> milliseconds


def mean_residual_ms(max_blend_delay: int) -> float:
    """Analytic mean mixing delay (ms): (2M+1)/6 seconds."""
    m = int(max_blend_delay)
    if m <= 0:
        return 0.0
    return (2.0 * m + 1.0) / 6.0 * 1000.0
