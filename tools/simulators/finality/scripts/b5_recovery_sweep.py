"""Phase B5: the recovery horizon H against stake turnover (PLAN.md B5, H6).

    python scripts/b5_recovery_sweep.py      # needs runs/a1; writes runs/b5/recovery_sweep.csv

Automatic recovery (SETTLEMENT.md B5) compares a fork that diverges within H by its density in
the W slots after the divergence. Cryptarchia has no forward security, so whoever holds the key of
a note that was eligible at the divergence and has been spent since can sign for it on the fork,
where the note is still unspent. A share mu(a) = 1 - exp(-tau a) of the stake moves within an age
a, for a turnover rate tau per day. An adversary holding alpha that obtains a fraction c of the
freed keys signs the fork with alpha + c (1 - alpha) mu(a), while the honest chain kept 1 - alpha.

Over the horizon, the chance is at most the sum over divergence points, one per honest block, of
the window's failure at the age of each point (src/finality_sim/recovery.py), capped at one. The
sweep reports the longest H that keeps it at or below eps. Delay: random (the specification's
Blend, A1's growth) and a worst case of 10 s.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from finality_sim.recovery import log_failure

HERE = pathlib.Path(__file__).resolve().parent.parent
F = 1 / 30
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
# share of stake moved per day; 0.125 % and 0.243 % are Bitcoin's yearly and monthly rates
TAUS = (1e-4, 3e-4, 5e-4, 1e-3, 1.25e-3, 2.43e-3, 3e-3, 1e-2, 3e-2, 1e-1)
CS = (0.1, 1.0)                                          # share of freed keys the adversary gets
WINDOWS_H = (1, 2, 4, 8)                                 # density window, hours
EPS = (1e-6, 1e-9)
FORK = np.linspace(0.0, 0.8, 161)                        # fork shares tabulated
H_MAX_DAYS = 3650


def table(window_h: int, alpha: float, model: dict) -> np.ndarray:
    """log P(window) at every fork share in FORK, the honest chain holding 1 - alpha."""
    w = window_h * 3600
    out = np.empty(FORK.size)
    for i, a in enumerate(FORK):
        out[i] = 0.0 if a <= 0 else log_failure(w, a, F, honest=1 - alpha, **model)
    return np.minimum(out, 0.0)


def failure_over(h_days: float, alpha: float, tau: float, c: float, logp: np.ndarray,
                 blocks_per_day: float) -> float:
    """Union bound over divergence points of age up to h_days, integrated hour by hour."""
    ages = (np.arange(int(math.ceil(h_days * 24))) + 0.5) / 24
    ages = ages[ages <= h_days]
    share = alpha + c * (1 - alpha) * (1 - np.exp(-tau * ages))
    lp = np.interp(share, FORK, logp)
    return float(min(1.0, blocks_per_day / 24 * np.exp(lp).sum()))


def longest(alpha, tau, c, logp, blocks_per_day, eps) -> float:
    if failure_over(1 / 24, alpha, tau, c, logp, blocks_per_day) > eps:
        return 0.0
    if failure_over(H_MAX_DAYS, alpha, tau, c, logp, blocks_per_day) <= eps:
        return math.inf
    lo, hi = 1 / 24, float(H_MAX_DAYS)
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        if failure_over(mid, alpha, tau, c, logp, blocks_per_day) <= eps:
            lo = mid
        else:
            hi = mid
    return lo


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1) & (s.blend_hops == 3)
          & (s.blend_delay_max == 3)]
    growth = float(s.growth_per_f.iloc[0])
    models = {"random, specification": dict(growth=growth), "worst, 10 s": dict(delta=10)}
    keys = [(wh, a, name) for wh in WINDOWS_H for a in ALPHAS for name in models]
    logs = Parallel(n_jobs=-2)(delayed(table)(wh, a, models[name]) for wh, a, name in keys)
    rows = []
    for (wh, a, name), logp in zip(keys, logs):
        rate = 1 / (10 + 1 / (1 - (1 - F) ** (1 - a))) if name.startswith("worst") else \
            growth * (1 - (1 - F) ** (1 - a))
        bpd = 86400 * rate                                       # divergence points per day
        for tau in TAUS:
            for c in CS:
                row = dict(model=name, window_h=wh, alpha=round(a, 4), tau_per_day=tau, c=c)
                for eps in EPS:
                    row[f"h_days_{eps:.0e}"] = longest(a, tau, c, logp, bpd, eps)
                rows.append(row)
    t = pd.DataFrame(rows)
    out = HERE / "runs" / "b5"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "recovery_sweep.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 500):
        print(t[(t.window_h == 4) & (t.model == "random, specification")].round(3)
              .to_string(index=False))


if __name__ == "__main__":
    main()
