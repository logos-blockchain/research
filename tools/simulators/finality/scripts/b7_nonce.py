"""Phase B7: an epoch nonce that resists grinding (PLAN.md, B7).

    python scripts/b7_nonce.py      # needs runs/a1 and runs/b2; writes runs/b7/*.csv

minimum.csv: the nonce taken from the smallest contribution of each of m sub-windows of the window
before the cut-off (src/finality_sim/nonce.py), for B6's three delay models. The window runs from
the epoch's start to its cut-off, 6 floor(k/f) slots, at each k of B5 and at k = 1620; m = 22, the
fewest sub-windows that keep p_own^m at or below 1e-9 at every share and model of the table. G_min,
the nonces reachable at the cut-off, is sampled 100,000 times a point with 20,000 near slots.
Decisions the coalition takes before the cut-off add to it. Their factor per nonce is estimated,
not bounded: G_min (1 + p_own) for the last sub-window's smallest coalition contribution published
or discarded; G_min / (1 - p_own) for any of its contributions there; and that times
1 + (p_own / (1 - p_own))^2 for the earlier sub-windows. Each factor F gives R_2 = F^2, read as B6
reads its factors.

p_own is the chance that the coalition holds a long sub-window's smallest contribution without
displacing an honest block; p_disp the chance when it races every honest block below its own from
the block's parent, a race from one block behind won with (p_own / (1 - p_own))^2:
p_own (1 - p_own) / (1 - p_own - p_own^2). m_life is the fewest sub-windows that keep p_disp^m at or
below 1e-9 over ten years of epochs, and m_early the fewest with notes frozen one epoch earlier,
when a prediction needs every minimum of two windows: p_disp^(2m).

budget.csv: today's hash-chain nonce under B6's bounds with B = 2^b nonces evaluated an epoch, b from
1 to 64, at 30 % and a third, on the specification's Blend under random delay and in the worst case
at 10 s: the factors and the depths at 1e-9 for one and two nonces.

recovery.csv: B6's recovery horizon on the specification's Blend under random delay, every freed key
for sale, at k = 2160, 1620 and 1080 and each one's longest window, with phi(u) <= u F and
phi_2(u) <= u F^2 in place of B6's bounds, F the largest of the estimates above.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b6_grinding import TAUS, WINDOWS_H, horizons, strict_depth, ub_depth
from finality_sim.grinding import PER_BIT, factors, pair_bounds
from finality_sim.nonce import min_rule_choices, own_share

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b7"
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
KS = (2160, 1620, 1080, 432, 216, 120)
EPS = 1e-9
SAMPLES = 100_000
NEAR = 20_000
BUDGETS = (1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64)
YEARS = 10
RECOVERY_KS = (2160, 1620, 1080)


def models() -> dict[str, dict]:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    g = {"random, testnet": (1, 1), "random, specification": (3, 3)}
    return {name: dict(growth=float(s[(s.blend_hops == h) & (s.blend_delay_max == d)].growth_per_f.iloc[0]))
            for name, (h, d) in g.items()} | {"worst, 10 s": dict(delta=10)}


def depth_reader(kw: dict, alpha: float, log_ub: dict):
    """The depth at which the attack's own chance is at most exp(log_eps), as B6 reads it."""
    if "growth" in kw:
        q = alpha / (alpha + (1 - alpha) * kw["growth"])
        return lambda log_eps: strict_depth(q, log_eps)
    return lambda log_eps: ub_depth(log_ub[(round(alpha, 4), kw["delta"])], log_eps)


def minimum(name: str, kw: dict, alpha: float, k: int, m: int, seed: int) -> dict:
    g, deep = min_rule_choices(F, alpha, 6 * math.floor(k / F), SAMPLES, seed, sub_windows=m,
                               near_slots=NEAR, **kw)
    if deep > 0:
        raise ValueError("a fork reached past the near slots")
    return dict(model=name, alpha=round(alpha, 4), k=k, sub_windows=m,
                sub_slots=6 * math.floor(k / F) // m, own=own_share(F, alpha, **kw), mean_g=g.mean(),
                se_g=g.std() / math.sqrt(g.size), p_choice=float(np.mean(g > 1)),
                p999_g=float(np.percentile(g, 99.9)), max_g=g.max())


def displaced(own: float) -> float:
    """The chance of holding a sub-window's smallest contribution when every honest block below the
    coalition's own is raced from its parent."""
    return own * (1 - own) / (1 - own - own ** 2)


def estimates(g: float, own: float) -> tuple[float, float, float]:
    """The factor per nonce with the decisions before the cut-off: the last sub-window's smallest
    contribution, any contribution there, and the earlier sub-windows too."""
    every = g / (1 - own)
    return g * (1 + own), every, every * (1 + (own / (1 - own)) ** 2)


def curve(factor: float) -> np.ndarray:
    """phi(u) <= min(1, u factor) on B6's grid of u."""
    return np.minimum(1.0, 2.0 ** -(np.arange(256 * PER_BIT + 1) / PER_BIT) * factor)


def budget(name: str, kw: dict, alpha: float, bits: int) -> dict:
    ts, lower, upper, lower2, upper2 = pair_bounds(F, alpha, budget_bits=bits, **kw)
    row = dict(model=name, alpha=round(alpha, 4), budget_bits=bits)
    row["factor_lo"], row["factor_hi"] = factors(ts, lower, upper, EPS)
    row["pair_lo"], row["pair_hi"] = factors(ts, lower2, upper2, EPS)
    return row


def main() -> None:
    ms = models()
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}
    big_m = max(math.ceil(math.log(EPS) / math.log(own_share(F, a, **kw)))
                for kw in ms.values() for a in ALPHAS)

    pts = [(n, a, k) for n in ms for a in ALPHAS for k in KS]
    rows = Parallel(n_jobs=-2)(delayed(minimum)(n, ms[n], a, k, big_m,
                                                7919 * list(ms).index(n) + 104729 * ALPHAS.index(a) + k)
                               for n, a, k in pts)
    for (n, a, k), r in zip(pts, rows):
        at = depth_reader(ms[n], a, log_ub)
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_one_1e-09"] = at(math.log(EPS / r["mean_g"]))
        r["depth_two_1e-09"] = at(math.log(EPS / r["mean_g"] ** 2))
        for name, factor in zip(("last", "every", "earlier"), estimates(r["mean_g"], r["own"])):
            r[f"factor_{name}"] = factor
            r[f"depth_two_{name}"] = at(math.log(EPS / factor ** 2))
        epochs = YEARS * 365.25 * 86400 / (10 * math.floor(k / F))
        r["own_displaced"] = displaced(r["own"])
        life = math.log(EPS / epochs) / math.log(r["own_displaced"])
        r["m_epoch"] = math.ceil(math.log(EPS) / math.log(r["own"]))
        r["m_life"], r["m_early"] = math.ceil(life), math.ceil(life / 2)
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "minimum.csv", index=False)
    with pd.option_context("display.width", 250):
        print(f"M = {big_m}")
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    spec = "random, specification"
    worst = {(r["alpha"], r["k"]): r["factor_earlier"] for r in rows if r["model"] == spec}
    rjobs = [(a, k, max(WINDOWS_H[k]), tau) for a in (0.25, 0.30, 1 / 3) for k in RECOVERY_KS
             for tau in TAUS]
    rec = Parallel(n_jobs=-2)(delayed(horizons)(spec, ms[spec], a, k, w, tau, 1.0,
                                                curve(worst[(round(a, 4), k)]),
                                                curve(worst[(round(a, 4), k)] ** 2))
                              for a, k, w, tau in rjobs)
    r = pd.DataFrame(rec).rename(columns={"h_days_ground": "h_days_minimum"})
    r.to_csv(OUT / "recovery.csv", index=False)
    print(r.round(1).to_string(index=False), end="\n\n")

    bpts = [(n, a, b) for n in ("random, specification", "worst, 10 s") for a in (0.30, 1 / 3)
            for b in BUDGETS]
    brows = Parallel(n_jobs=-2)(delayed(budget)(n, ms[n], a, b) for n, a, b in bpts)
    for (n, a, _), r in zip(bpts, brows):
        at = depth_reader(ms[n], a, log_ub)
        r["depth_1e-09"] = at(math.log(EPS))
        for side in ("lo", "hi"):
            r[f"depth_one_{side}"] = at(math.log(EPS / r[f"factor_{side}"]))
            r[f"depth_two_{side}"] = at(math.log(EPS / r[f"pair_{side}"]))
    b = pd.DataFrame(brows)
    b.to_csv(OUT / "budget.csv", index=False)
    with pd.option_context("display.width", 250):
        print(b.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
