"""Phase B7: an epoch nonce that resists grinding (PLAN.md, B7).

    python scripts/b7_nonce.py      # needs runs/a1 and runs/b2; writes runs/b7/*.csv

minimum.csv: the nonce taken from the smallest contribution of each of m sub-windows of the window
before the cut-off (src/finality_sim/nonce.py), for B6's three delay models. The window runs from
the epoch's start to its cut-off, 6 floor(k/f) slots, at each k of B5 and at k = 1620. G_min, the
nonces reachable at the cut-off, is sampled 100,000 times a point with 20,000 near slots. The
decisions before the cut-off add to it, estimated, not bounded: c_last is the hindsight count of
the last sub-window's reachable minima (20,000 windows a point), from the coalition attempting
only the honest blocks that held the running minimum (lo) or any honest block (hi), each removed
with the chance `displacement` gives the model; the factor per nonce is nonce.estimate, and each
factor F gives R_2 = F^2, read as B6 reads its factors.

m is set per k by the prediction channel: p_disp is the chance of holding a sub-window's minimum
with every honest block below the coalition's own attempted, at a third under the worst case, the
largest of the table; m_life is the fewest sub-windows that keep p_disp^m times the epochs in ten
years at or below 1e-9, and m, used throughout, the fewest with notes frozen one epoch earlier,
when a prediction needs every minimum of two windows: p_disp^(2m).

budget.csv: today's hash-chain nonce under B6's bounds with B = 2^b nonces evaluated an epoch, b from
1 to 64, at 30 % and a third, on the specification's Blend under random delay and in the worst case
at 10 s: the factors and the depths at 1e-9 for one and two nonces.

recovery.csv: B6's recovery horizon on the specification's Blend under random delay and in the
worst case at 10 s, every freed key for sale, at k = 2160, 1620 and 1080 and each one's longest
window, with phi(u) <= u F and phi_2(u) <= u F^2 in place of B6's bounds, F the larger estimate.
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
from finality_sim.nonce import (displacement, estimate, last_sub_window, min_rule_choices, own_share,
                                predicted_share)

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b7"
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
KS = (2160, 1620, 1080, 432, 216, 120)
EPS = 1e-9
SAMPLES = 100_000
LAST_SAMPLES = 20_000
NEAR = 20_000
BUDGETS = (1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64)
YEARS = 10
RECOVERY_KS = (2160, 1620, 1080)
RECOVERY_MODELS = ("random, specification", "worst, 10 s")


def models() -> dict[str, tuple[dict, float]]:
    """Each delay model's keywords for finality_sim.nonce and its orphan share."""
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    out = {}
    for name, (h, d) in {"random, testnet": (1, 1), "random, specification": (3, 3)}.items():
        r = s[(s.blend_hops == h) & (s.blend_delay_max == d)].iloc[0]
        out[name] = (dict(growth=float(r.growth_per_f)), float(r.orphan_share))
    return out | {"worst, 10 s": (dict(delta=10), 0.0)}


def depth_reader(kw: dict, alpha: float, log_ub: dict):
    """The depth at which the attack's own chance is at most exp(log_eps), as B6 reads it."""
    if "growth" in kw:
        q = alpha / (alpha + (1 - alpha) * kw["growth"])
        return lambda log_eps: strict_depth(q, log_eps)
    return lambda log_eps: ub_depth(log_ub[(round(alpha, 4), kw["delta"])], log_eps)


def epochs(k: int) -> float:
    return YEARS * 365.25 * 86400 / (10 * math.floor(k / F))


def sub_windows(k: int, p_disp: float) -> tuple[int, int]:
    """(m_life, m): the fewest sub-windows that keep a right prediction over ten years at or below
    EPS, needing every minimum of one window, and of two."""
    life = math.log(EPS / epochs(k)) / math.log(p_disp)
    return math.ceil(life), math.ceil(life / 2)


def minimum(name: str, kw: dict, orphan: float, alpha: float, k: int, m: int, seed: int) -> dict:
    window = 6 * math.floor(k / F)
    g, deep = min_rule_choices(F, alpha, window, SAMPLES, seed, sub_windows=m, near_slots=NEAR, **kw)
    if deep > 0:
        raise ValueError("a fork reached past the near slots")
    any_block, records = last_sub_window(F, alpha, window // m, LAST_SAMPLES, seed + 1, orphan=orphan,
                                         **kw)
    own = own_share(F, alpha, **kw)
    coin = displacement(F, alpha, orphan=orphan, **kw)
    p_disp = predicted_share(own, coin)
    return dict(model=name, alpha=round(alpha, 4), k=k, sub_windows=m, sub_slots=window // m,
                own=own, coin=coin, p_disp=p_disp, mean_g=g.mean(),
                se_g=g.std() / math.sqrt(g.size), p_choice=float(np.mean(g > 1)),
                p999_g=float(np.percentile(g, 99.9)), max_g=g.max(),
                c_last_lo=records.mean(), se_last_lo=records.std() / math.sqrt(records.size),
                c_last_hi=any_block.mean(), se_last_hi=any_block.std() / math.sqrt(any_block.size),
                factor_lo=estimate(g.mean(), records.mean(), p_disp),
                factor_hi=estimate(g.mean(), any_block.mean(), p_disp))


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
    # the prediction channel at its strongest: a third under the worst case
    p_star = max(predicted_share(own_share(F, a, **kw), displacement(F, a, orphan=o, **kw))
                 for kw, o in ms.values() for a in ALPHAS)
    ms_of = {k: sub_windows(k, p_star) for k in KS}

    pts = [(n, a, k) for n in ms for a in ALPHAS for k in KS]
    rows = Parallel(n_jobs=-2)(delayed(minimum)(n, ms[n][0], ms[n][1], a, k, ms_of[k][1],
                                                7919 * list(ms).index(n) + 104729 * ALPHAS.index(a) + k)
                               for n, a, k in pts)
    for (n, a, k), r in zip(pts, rows):
        at = depth_reader(ms[n][0], a, log_ub)
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_two_cutoff"] = at(math.log(EPS / r["mean_g"] ** 2))
        r["depth_two_lo"] = at(math.log(EPS / r["factor_lo"] ** 2))
        r["depth_two_hi"] = at(math.log(EPS / r["factor_hi"] ** 2))
        r["p_disp_star"] = p_star
        r["m_life"], r["m"] = ms_of[k]
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "minimum.csv", index=False)
    with pd.option_context("display.width", 300):
        print(f"p_disp at a third under the worst case = {p_star:.4f}; m per k = {ms_of}")
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    worst = {(r["model"], r["alpha"], r["k"]): r["factor_hi"] for r in rows}
    rjobs = [(n, a, k, max(WINDOWS_H[k]), tau) for n in RECOVERY_MODELS for a in (0.25, 0.30, 1 / 3)
             for k in RECOVERY_KS for tau in TAUS]
    rec = Parallel(n_jobs=-2)(delayed(horizons)(n, ms[n][0], a, k, w, tau, 1.0,
                                                curve(worst[(n, round(a, 4), k)]),
                                                curve(worst[(n, round(a, 4), k)] ** 2))
                              for n, a, k, w, tau in rjobs)
    r = pd.DataFrame(rec).rename(columns={"h_days_ground": "h_days_minimum"})
    r.to_csv(OUT / "recovery.csv", index=False)
    print(r.round(1).to_string(index=False), end="\n\n")

    bpts = [(n, a, b) for n in ("random, specification", "worst, 10 s") for a in (0.30, 1 / 3)
            for b in BUDGETS]
    brows = Parallel(n_jobs=-2)(delayed(budget)(n, ms[n][0], a, b) for n, a, b in bpts)
    for (n, a, _), r in zip(bpts, brows):
        at = depth_reader(ms[n][0], a, log_ub)
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
