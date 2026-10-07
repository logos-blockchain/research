"""Phase G, further routes (PLAN.md, phase G).

G1, a delayed nonce. If the nonce passes through a sequential delay that outlasts the time the
coalition has to decide, the coalition decides blind and gains nothing from a choice. At the
cut-off it has until its private chain's lead is spent. ``lead_lasts`` is the chance that the lead
``Z`` after the cut-off (B6, ``finality_sim.grinding.post_cutoff``) lasts at least ``slots`` slots,
taking a lead of ``z`` to last ``z / (h_c - a)`` slots, its mean under a drift of ``h_c - a``
canonical honest blocks per slot net of the coalition's wins. ``delayed_factor`` is the factor per
nonce that remains under a delay: the choices at the cut-off count only in the windows whose lead
lasts that long.

G4, settlement on a chain nobody withholds from. B4's elapsed-time rule accepts the ``n``-th
canonical block counting the target when the coalition's exact chance, given the time ``t`` since
the target's parent, is at most ``ε``. ``time_rule_depth`` is the block at which it accepts when
blocks arrive at their mean spacing: at the full rate ``g λ`` of a chain nobody withholds from, or
at the honest rate ``(1 - α) g λ`` of one the coalition withholds from. The total-stake inference
sets the lottery's thresholds from the previous period's occupied slots, so a coalition that
withholds for a whole period raises every rate by ``1 / (1 - α)``: the honest chain then runs at
``g λ`` while the coalition wins at ``α λ / (1 - α)``. The ``adjusted`` rule takes those rates,
which bound the coalition in both worlds since the catch-up ratio ``a / h`` is the same.
``density_depth`` is a rule that reads the chain's density directly; ``density_chance`` gives the
exact conditional chance at its acceptance, for comparison with the elapsed-time rule.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from finality_sim.elapsed import deadlines, log_fail
from finality_sim.grinding import post_cutoff
from finality_sim.nonce import _rates, min_rule_choices
from finality_sim.private_race import log_strict, strict_depth


def lead_lasts(f: float, alpha: float, slots: float, growth: float | None = None,
               delta: int | None = None) -> float:
    """P(the coalition's lead after the cut-off lasts at least ``slots`` slots)."""
    a, _, _, rate = _rates(f, alpha, growth, delta)
    z = post_cutoff(f, alpha, growth, delta)
    need = math.ceil(slots * (rate - a))
    return float(z[need:].sum()) if need < z.size else 0.0


def delayed_factor(f: float, alpha: float, window_slots: int, sub_windows: int, minutes: float,
                   n_samples: int, seed: int, growth: float | None = None,
                   delta: int | None = None, near_slots: int = 20_000) -> float:
    """E[1 + (G_min - 1)·1{the lead lasts at least ``minutes``}] over sampled windows."""
    a, _, _, rate = _rates(f, alpha, growth, delta)
    g, _, z = min_rule_choices(f, alpha, window_slots, n_samples, seed, sub_windows=sub_windows,
                               growth=growth, delta=delta, near_slots=near_slots, with_lead=True)
    need = math.ceil(60 * minutes * (rate - a))
    return float(np.mean(1.0 + (g - 1.0) * (z >= need)))


def _rule_rates(alpha: float, g: float, f: float, adjusted: bool) -> tuple[float, float]:
    lam = -math.log(1 - f)
    if adjusted:
        return alpha * lam / (1 - alpha), g * lam
    return alpha * lam, (1 - alpha) * g * lam


def time_rule_depth(alpha: float, g: float, eps: float, f: float = 1 / 30, full_rate: bool = True,
                    adjusted: bool = False) -> int:
    """The first canonical block counting the target at which B4's elapsed-time rule accepts when
    the ``n``-th block arrives ``n / rate`` slots after the parent, ``rate`` the full rate ``g λ`` or
    the withheld-from rate ``(1 - α) g λ``; -1 if none within three times B5's depth."""
    lam = -math.log(1 - f)
    a, h = _rule_rates(alpha, g, f, adjusted)
    world = g * lam if full_rate else (1 - alpha) * g * lam
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    dl = deadlines(a, h, eps, 3 * plain + 60)
    for n in range(1, dl.size):
        if dl[n] >= 0 and dl[n] >= n / world:
            return n
    return -1


def density_depth(alpha: float, g: float, eps: float, f: float = 1 / 30, step: float = 0.01,
                  test: bool = True) -> tuple[int, float]:
    """The depth at which a chain at the full rate settles against every withheld share up to
    ``alpha`` under a rule that multiplies the race's chance by the chance of seeing that many
    blocks under the attack, and the share that needs the most depth. Without ``test`` the density
    is ignored and the depth is B5's at ``alpha``."""
    lam = -math.log(1 - f)
    shares = np.arange(step, alpha + step / 2, step)
    shares = np.append(shares[shares < alpha], alpha)
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    for d in range(1, plain + 1):
        n = d + 1
        t = n / (g * lam)
        worst, worst_w = -math.inf, alpha
        for w in shares:
            q = w / (w + (1 - w) * g)
            lp = log_strict(q, n)
            if test:
                lp += float(stats.poisson.logsf(n - 1, (1 - w) * g * lam * t))
            if lp > worst:
                worst, worst_w = lp, float(w)
        if worst <= math.log(eps):
            return d, worst_w
    return plain, alpha


def density_chance(alpha: float, g: float, eps: float, f: float = 1 / 30) -> float:
    """log of the coalition's exact conditional chance (B4) at the point where ``density_depth``
    accepts a chain at the full rate."""
    lam = -math.log(1 - f)
    d, _ = density_depth(alpha, g, eps, f)
    n = d + 1
    a, h = _rule_rates(alpha, g, f, False)
    return log_fail(n, n / (g * lam), a, h)
