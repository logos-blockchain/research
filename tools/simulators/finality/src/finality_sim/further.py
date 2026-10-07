"""Phase G, further routes (PLAN.md, phase G).

G1, a delayed nonce. If the nonce passes through a sequential delay that outlasts the time the
coalition has to decide, the coalition decides blind and gains nothing from a choice. At the
cut-off it has until its private chain's lead is spent. ``lead_lasts`` is the chance that the lead
``Z`` after the cut-off (B6, ``finality_sim.grinding.post_cutoff``) lasts at least ``slots`` slots,
taking a lead of ``z`` to last ``z / (h_c - a)`` slots, its mean under a drift of ``h_c - a``
canonical honest blocks per slot net of the coalition's wins.

G4, settlement that reads density. A private attack on a target withholds the coalition's blocks
from the target's parent on, so the canonical chain runs at the honest rate ``(1 - w) g λ`` for a
withheld share ``w`` instead of the full rate ``g λ``, with ``λ = -ln(1 - f)`` and ``g`` the
canonical growth per win. A client that sees ``n`` blocks counting the target ``t`` slots after
the parent accepts when, for every ``w`` up to its bound ``α``, the private race's chance at that
depth times the chance that a chain under attack ``w`` shows at least ``n`` blocks in ``t`` slots
is at most ``ε``. ``density_depth`` gives the depth at which a chain with everyone producing, at
the full rate, is accepted. The chain's count is taken as Poisson.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from finality_sim.grinding import post_cutoff
from finality_sim.nonce import _rates
from finality_sim.private_race import log_strict, strict_depth


def lead_lasts(f: float, alpha: float, slots: float, growth: float | None = None,
               delta: int | None = None) -> float:
    """P(the coalition's lead after the cut-off lasts at least ``slots`` slots)."""
    a, _, _, rate = _rates(f, alpha, growth, delta)
    z = post_cutoff(f, alpha, growth, delta)
    need = math.ceil(slots * (rate - a))
    return float(z[need:].sum()) if need < z.size else 0.0


def density_depth(alpha: float, g: float, eps: float, f: float = 1 / 30, step: float = 0.01,
                  test: bool = True) -> tuple[int, float]:
    """The depth at which a chain at the full rate settles against every withheld share up to
    ``alpha``, and the share that needs the most depth. Without ``test`` the density is ignored
    and the depth is B5's at ``alpha``."""
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
