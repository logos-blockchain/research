"""Phase B5: the recovery horizon H against stake turnover (PLAN.md B5, H6).

    python scripts/b5_recovery_sweep.py      # needs runs/a1; writes runs/b5/recovery_sweep.csv

Automatic recovery (SETTLEMENT.md B5) compares a fork that diverges within H by its density in
the W slots after the divergence. Cryptarchia has no forward security, so whoever holds the key of
a note that was eligible at the divergence and has been spent since can sign for it on the fork,
where the note is still unspent. A share mu(a) = 1 - exp(-tau a) of the stake moves within an age
a, for a turnover rate tau per day. An adversary holding alpha that obtains a fraction c of the
freed keys signs the fork with alpha + c (1 - alpha) mu(a), while the honest chain kept 1 - alpha.

Over the horizon, the chance is at most the sum over divergence points, one per canonical honest
block, of the window's failure at the age of each point (src/finality_sim/recovery.py), capped at
one, integrated over ages on a grid of 6 minutes. The sweep reports the longest H that keeps it
at or below eps. Delay: random (the specification's Blend, A1's growth) and a worst case of 10 s.
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
STEP_DAYS = 1 / 240                                      # the age grid of the sum, 6 minutes


def table(window_h: int, alpha: float, model: dict) -> np.ndarray:
    """log P(window) at every fork share in FORK, the honest chain holding 1 - alpha."""
    w = int(round(window_h * 3600))
    out = np.empty(FORK.size)
    for i, a in enumerate(FORK):
        out[i] = 0.0 if a <= 0 else log_failure(w, a, F, honest=1 - alpha, **model)
    return np.minimum(out, 0.0)


def canonical_rate(alpha: float, growth: float | None = None, delta: int | None = None) -> float:
    """Canonical honest blocks per slot, the divergence points: under random delay the honest wins
    thinned by A1's growth; under a worst case of delta slots, one per delta slots and the wait
    for the next honest win."""
    win = 1 - (1 - F) ** (1 - alpha)
    return growth * win if growth is not None else 1 / (delta + 1 / win)


def accumulated(alpha: float, tau: float, c: float, logp: np.ndarray,
                blocks_per_day: float) -> np.ndarray:
    """The union bound over divergence points of age up to i STEP_DAYS, i = 0 .. H_MAX_DAYS /
    STEP_DAYS: the chance per window at each point's fork share, by the midpoint rule."""
    ages = (np.arange(int(round(H_MAX_DAYS / STEP_DAYS))) + 0.5) * STEP_DAYS
    share = alpha + c * (1 - alpha) * (1 - np.exp(-tau * ages))
    per_step = blocks_per_day * STEP_DAYS * np.exp(np.interp(share, FORK, logp))
    return np.concatenate(([0.0], np.cumsum(per_step)))


def at(acc: np.ndarray, age):
    """``accumulated`` at any age in days, linear between its grid points."""
    x = np.clip(np.asarray(age, float) / STEP_DAYS, 0.0, acc.size - 1.0)
    i = np.minimum(x.astype(int), acc.size - 2)
    return acc[i] + (x - i) * (acc[i + 1] - acc[i])


def longest_h(chance, eps: float) -> float:
    """The longest horizon in days whose chance stays at or below eps: 0 if one hour exceeds it,
    inf if H_MAX_DAYS does not."""
    if chance(1 / 24) > eps:
        return 0.0
    if chance(H_MAX_DAYS) <= eps:
        return math.inf
    lo, hi = 1 / 24, float(H_MAX_DAYS)
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if chance(mid) <= eps else (lo, mid)
    return lo


def longest(alpha, tau, c, logp, blocks_per_day, eps) -> float:
    acc = accumulated(alpha, tau, c, logp, blocks_per_day)
    return longest_h(lambda h: min(1.0, float(at(acc, h))), eps)


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
        bpd = 86400 * canonical_rate(a, **models[name])          # divergence points per day
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
