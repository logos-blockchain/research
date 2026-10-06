"""Phase B6: what grinding the epoch nonce costs in settlement depth and in recovery horizon.

    python scripts/b6_grinding.py      # needs runs/a1, runs/b2 and runs/b5; writes runs/b6/*.csv

The coalition picks each epoch's schedule among G nonces and evaluates at most B = 2^64 of them
(src/finality_sim/grinding.py). An attack that succeeds with probability u against one schedule
then succeeds with phi(u) <= E[min(1, u min(G, B))], and one whose schedule spans two epochs with
phi_2(u). To hold eps, the chance against one schedule must fall by the factor R = eps / u*, where
phi(u*) = eps; R_2 likewise for phi_2. Each lies between the values the two bounds give. The depth
that holds eps / R is read off the attack's own chance at depth:

- random delay: the private race in closed form (scripts/b5_what_k_holds.py), at the canonical
  growth A1 measured;
- worst case of Delta: B2's upper bound (runs/b2/ub.parquet).

grinding.csv holds both factors and both depths for three delay models. delays.csv holds the
worst case at every share and delay of B2, and with B = 2^40 for a quarter and a third. race_h is
how long the two-epoch depth takes at the canonical rate while the coalition withholds
(b5_recovery_sweep.canonical_rate). shares.csv gives the largest share each k holds at 1e-9:
without grinding, as B5 finds it, and with one and two ground nonces. Under random delay ln R is
interpolated over shares 0.05 to 0.43 in steps of 0.01; in the worst case over shares 0.05 to 1/3
in steps of 0.01, onto B5's grid of B2's bound (runs/b5/worst_logs.csv).

recovery.csv: SETTLEMENT.md B5's recovery horizon with every epoch's nonce ground, for k = 2160,
216 and 120, the epoch 10 floor(k/f) slots long and the window at most 4 floor(k/f) slots (rule 5).
A divergence point within one window of its epoch's end has a window that reaches the next epoch,
whose nonce is fixed before the point, so its chance meets both nonces. Over a horizon the chance
is at most the sum over epochs of the upper bound on phi at the sum of the chances of the epoch's
other points against honest nonces, and of the upper bound on phi_2 at that of these points
(b5_recovery_sweep.accumulated). The horizon is the shortest over 48 phases of the epoch
boundaries.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import ADV, DELAYS_S, F
from b5_recovery_sweep import accumulated, at, canonical_rate, longest_h, table
from b5_what_k_holds import GRID, KS, held_worst, log_strict, max_alpha
from finality_sim.grinding import PER_BIT, factors, pair_bounds, tail

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b6"
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
EPS = (1e-6, 1e-9)
BUDGET_BITS = 64
TAUS = (1.25e-3, 2.43e-3)                                   # Bitcoin's yearly and monthly turnover
CS = (0.1, 1.0)
WINDOWS_H = {2160: (4, 8), 216: (4, 7.2), 120: (4,)}        # 4 floor(k/f) slots: 72, 7.2, 4 h
PHASES = 48


def point(kw: dict, alpha: float, budget_bits: int = BUDGET_BITS, per_bit: int = PER_BIT,
          depths: int = 4000) -> dict:
    ts, lower, upper, lower2, upper2 = pair_bounds(F, alpha, budget_bits=budget_bits,
                                                   depths=depths, per_bit=per_bit, **kw)
    p = tail(F, alpha, np.array([0.0, float(budget_bits)]), depths=depths, **kw)
    row = dict(alpha=round(alpha, 4), budget_bits=budget_bits, p_choice=p[0], p_over_budget=p[1])
    for eps in EPS:
        e = f"{eps:.0e}"
        row[f"factor_lo_{e}"], row[f"factor_hi_{e}"] = factors(ts, lower, upper, eps)
        row[f"pair_lo_{e}"], row[f"pair_hi_{e}"] = factors(ts, lower2, upper2, eps)
    row["budget_binds_1e-09"] = bool(row["factor_hi_1e-09"] * 2.0 ** -budget_bits > 1e-9)
    return row | dict(_upper=upper, _upper2=upper2)


def strict_depth(q: float, log_eps: float) -> float:
    """The smallest depth at which the private race's closed form is at most exp(log_eps)."""
    if q >= 0.5:
        return math.inf
    lo, hi = 0, 1
    while log_strict(q, hi + 1) > log_eps:
        lo, hi = hi, 2 * hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if log_strict(q, mid + 1) > log_eps else (lo, mid)
    return float(hi)


def ub_depth(log_ub: np.ndarray, log_eps: float) -> float:
    """The smallest depth at which B2's upper bound is at most exp(log_eps)."""
    hit = np.nonzero(log_ub <= log_eps)[0]
    if not hit.size:
        raise ValueError("B2's upper bound stops above the chance asked for")
    return float(hit[0] + 1)


def depths_for(row: dict, depth_at) -> dict:
    """Depth at 1e-9 without grinding, and with one and two ground nonces at both factor ends."""
    out = {"depth_1e-09": depth_at(math.log(1e-9))}
    for name, key in (("ground", "factor"), ("ground2", "pair")):
        for side in ("lo", "hi"):
            out[f"{name}_{side}_1e-09"] = depth_at(math.log(1e-9 / row[f"{key}_{side}_1e-09"]))
    return out


def held_random(grid: np.ndarray, lnr: np.ndarray, g: float, k: int, eps: float = 1e-9) -> float:
    """The largest share the private race lets k hold, the chance against one schedule held to
    eps / R; the top of the grid when it holds there."""
    def ok(a):
        q = a / (a + (1 - a) * g)
        return q < 0.5 and log_strict(q, k + 1) + np.interp(a, grid, lnr) <= math.log(eps)
    if ok(grid[-1]):
        return float(grid[-1])
    lo, hi = 0.0, float(grid[-1])
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo


def lookup(curve: np.ndarray, u) -> np.ndarray:
    """An upper bound on phi at u: the least upper bound on the grid at any u' >= u; phi rises."""
    hat = np.minimum.accumulate(curve)
    u = np.asarray(u, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        i = np.floor(-np.log2(np.where(u > 0, u, 1.0)) * PER_BIT)
    i = np.clip(i, 0, hat.size - 1).astype(int)
    return np.where(u > 0, hat[i], 0.0)


def ground_chance(acc, h, phase, epoch, window, upper, upper2) -> float:
    """The chance over ages [0, h] in days, epochs ending at ages phase + (j - 1) epoch."""
    j = np.arange(int(math.floor((h - phase) / epoch)) + 2)
    end = phase + (j - 1) * epoch
    lo, mid, hi = (np.clip(x, 0.0, h) for x in (end, end + window, end + epoch))
    spill, inside = at(acc, mid) - at(acc, lo), at(acc, hi) - at(acc, mid)
    return min(1.0, float(lookup(upper, inside).sum() + lookup(upper2, spill).sum()))


def horizons(model, kw, alpha, k, window_h, tau, c, upper, upper2) -> dict:
    logp = table(window_h, alpha, kw)
    acc = accumulated(alpha, tau, c, logp, 86400 * canonical_rate(alpha, **kw))
    epoch, window = 10 * math.floor(k / F) / 86400, window_h / 24
    ground = min(longest_h(lambda h: ground_chance(acc, h, p * epoch / PHASES, epoch, window,
                                                   upper, upper2), 1e-9)
                 for p in range(PHASES))
    return dict(model=model, alpha=alpha, k=k, window_h=window_h, tau_per_day=tau, c=c,
                h_days=longest_h(lambda h: min(1.0, float(at(acc, h))), 1e-9), h_days_ground=ground)


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    growth = {"random, testnet": float(s[(s.blend_hops == 1) & (s.blend_delay_max == 1)].growth_per_f.iloc[0]),
              "random, specification": float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)]
                                             .growth_per_f.iloc[0])}
    models = {name: dict(growth=g) for name, g in growth.items()} | {"worst, 10 s": dict(delta=10)}
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}

    def depth_at(kw: dict, alpha: float):
        if "growth" in kw:
            q = alpha / (alpha + (1 - alpha) * kw["growth"])
            return lambda log_eps: strict_depth(q, log_eps)
        return lambda log_eps: ub_depth(log_ub[(round(alpha, 4), kw["delta"])], log_eps)

    def race_h(kw, alpha, depth):
        return depth / canonical_rate(alpha, **kw) / 3600

    pts = [(m, a) for m in models for a in ALPHAS]
    rows = Parallel(n_jobs=-2)(delayed(point)(models[m], a) for m, a in pts)
    curves = {}
    for (m, a), r in zip(pts, rows):
        curves[(m, round(a, 4))] = (r.pop("_upper"), r.pop("_upper2"))
        r["model"] = m
        r.update(depths_for(r, depth_at(models[m], a)))
        r["race_h"] = race_h(models[m], a, r["ground2_hi_1e-09"])
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "grinding.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.3g}"), end="\n\n")

    dpts = [(a, d, BUDGET_BITS) for a in ADV for d in DELAYS_S] + \
        [(a, d, 40) for a in (0.25, 1 / 3) for d in DELAYS_S]
    drows = Parallel(n_jobs=-2)(delayed(point)(dict(delta=d), a, b) for a, d, b in dpts)
    for (a, d, _), r in zip(dpts, drows):
        r.pop("_upper"), r.pop("_upper2")
        kw = dict(delta=d)
        r["delay_s"] = d
        r.update(depths_for(r, depth_at(kw, a)))
        r["race_h"] = race_h(kw, a, r["ground2_hi_1e-09"])
    d = pd.DataFrame(drows)
    d.to_csv(OUT / "delays.csv", index=False)
    with pd.option_context("display.width", 250):
        print(d.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    held = []
    rgrid = np.round(np.arange(0.05, 0.4301, 0.01), 4)       # walks at 0.43 last up to 30,000 blocks
    rpts = [(m, a) for m in growth for a in rgrid]
    rrows = Parallel(n_jobs=-2)(delayed(point)(models[m], a, per_bit=4, depths=32_000) for m, a in rpts)
    for m, g in growth.items():
        rs = [r for (mm, _), r in zip(rpts, rrows) if mm == m]
        lnr = {key: np.log([r[f"{key}_hi_1e-09"] for r in rs]) for key in ("factor", "pair")}
        for k in KS:
            held.append(dict(model=m, k=k, held_without=max_alpha(k, g, 1e-9),
                             **{f"held_{n}": held_random(rgrid, lnr[key], g, k)
                                for n, key in (("one", "factor"), ("two", "pair"))}))
    wgrid = np.append(np.round(np.arange(0.05, 1 / 3, 0.01), 4), 1 / 3)
    wpts = [(dl, a) for dl in DELAYS_S for a in wgrid]
    wrows = Parallel(n_jobs=-2)(delayed(point)(dict(delta=dl), a, per_bit=4) for dl, a in wpts)
    logs = pd.read_csv(HERE / "runs" / "b5" / "worst_logs.csv", float_precision="round_trip")
    for dl in DELAYS_S:
        rs = [r for (x, _), r in zip(wpts, wrows) if x == dl]
        lnr = {key: np.interp(GRID, wgrid, np.log([r[f"{key}_hi_1e-09"] for r in rs]))
               for key in ("factor", "pair")}
        for k in KS:
            lg = logs[(logs.delay_s == dl) & (logs.k == k)].sort_values("alpha").log_ub.to_numpy()
            held.append(dict(model=f"worst, {dl} s", k=k, held_without=held_worst(lg, 1e-9),
                             held_one=held_worst(lg, 1e-9, lnr["factor"]),
                             held_two=held_worst(lg, 1e-9, lnr["pair"])))
    h = pd.DataFrame(held)
    h.to_csv(OUT / "shares.csv", index=False)
    print(h.to_string(index=False), end="\n\n")

    jobs = [(m, models[m], a, k, w, tau, c) for m in ("random, specification", "worst, 10 s")
            for a in (0.10, 0.20, 0.25) for k, ws in WINDOWS_H.items() for w in ws
            for tau in TAUS for c in CS]
    rec = Parallel(n_jobs=-2)(delayed(horizons)(m, kw, a, k, w, tau, c, *curves[(m, round(a, 4))])
                              for m, kw, a, k, w, tau, c in jobs)
    r = pd.DataFrame(rec)
    r.to_csv(OUT / "recovery.csv", index=False)
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(r.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
