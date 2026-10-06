"""Phase B6: what grinding the epoch nonce costs in settlement depth and in recovery horizon.

    python scripts/b6_grinding.py      # needs runs/a1, runs/b2 and runs/e2; writes runs/b6/*.csv

The coalition picks the next epoch's schedule among G nonces and evaluates at most B = 2^64 of them
(src/finality_sim/grinding.py). An attack that succeeds with probability u against one schedule
then succeeds with phi(u) <= E[min(1, u min(G, B))]. To hold eps, the chance against one schedule
must fall to u*, where phi(u*) = eps, and the factor R = eps / u* lies between the values the two
bounds on phi give. The depth that holds eps grows by ln R / rho, rho being the attack's decay per
block: the §5.6 fit of the chain's race under random delay (runs/e2/fit.csv), and B2's upper bound
between its two deepest computed depths under a worst case of Delta (runs/b2/curves.csv).
delays.csv repeats the worst case at every share and delay B2 computed, and with B = 2^40 beside
2^64 for a quarter and a third. shares.csv gives the largest share each k holds at 1e-9 with
grinding, read as SETTLEMENT.md B5 reads it without: under random delay the private race in closed
form (scripts/b5_what_k_holds.py) with ln R interpolated over shares 0.05 to 0.43 on a grid of a
quarter bit, and in the worst case B2's upper bound plus ln R / rho, its log interpolated linearly
in the share.

recovery.csv: the divergence points of each epoch of a recovery horizon H share a nonce the
coalition ground. If the chance over an epoch's divergence points is U_e against an honest nonce,
the chance over H becomes at most the sum over epochs of phi(U_e), with the upper bound on phi in
its place; the horizon must keep that at eps. The setting is SETTLEMENT.md B5's: windows of 4 and
8 hours, and Bitcoin's turnover rates.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b5_recovery_sweep import FORK, longest, table
from b5_what_k_holds import KS, log_strict, max_alpha
from finality_sim.grinding import PER_BIT, bounds, factors, tail

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b6"
F = 1 / 30
K = 2160
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
EPS = (1e-6, 1e-9)
BUDGET_BITS = 64
EPOCH_DAYS = 10 * K / F / 86400                           # 10 floor(k/f) slots of 1 s
TAUS = (1.25e-3, 2.43e-3)                                 # Bitcoin's yearly and monthly turnover
CS = (0.1, 1.0)
WINDOWS_H = (4, 8)
H_MAX_DAYS = 3650


def b2_upper(b2, b2d, alpha: float, delay: int) -> tuple[float, float]:
    """B2's upper-bound depth at 1e-9 and its decay per block between the two deepest depths."""
    c = b2[np.isclose(b2.adv, alpha, atol=1e-3) & (b2.delay_s == delay)].sort_values("depth").tail(2)
    rho = math.log(c.ub.iloc[0] / c.ub.iloc[1]) / (c.depth.iloc[1] - c.depth.iloc[0])
    d = b2d[np.isclose(b2d.adv, alpha, atol=1e-3) & (b2d.delay_s == delay) & (b2d.eps == 1e-9)]
    return float(d.ub_depth.iloc[0]), rho


def point(model: str, kw: dict, alpha: float, budget_bits: int = BUDGET_BITS, per_bit: int = PER_BIT,
          depths: int = 4000) -> dict:
    ts, lower, upper, p_choice = bounds(F, alpha, budget_bits=budget_bits, depths=depths,
                                        per_bit=per_bit, **kw)
    row = dict(model=model, alpha=round(alpha, 4), budget_bits=budget_bits, p_choice=p_choice,
               p_over_budget=float(tail(F, alpha, np.array([float(budget_bits)]), depths=depths,
                                        **kw)[0]))
    for eps in EPS:
        row[f"factor_lo_{eps:.0e}"], row[f"factor_hi_{eps:.0e}"] = factors(ts, lower, upper, eps)
    row["budget_binds_1e-09"] = bool(row["factor_hi_1e-09"] * 2.0 ** -budget_bits > 1e-9)
    return row | dict(_ts=ts, _upper=upper)


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


def held_worst(alphas: np.ndarray, depth: np.ndarray, k: int) -> float:
    """SETTLEMENT.md B5's reading: log depth linear in the share between B2's shares; nan past
    the grid at either end (below 0.05, or at least 1/3)."""
    logd = np.log(depth)
    if logd[0] > math.log(k) or logd[-1] <= math.log(k):
        return math.nan if logd[0] > math.log(k) else math.inf
    i = int(np.nonzero(logd > math.log(k))[0][0])
    return float(alphas[i - 1] + (math.log(k) - logd[i - 1]) * (alphas[i] - alphas[i - 1])
                 / (logd[i] - logd[i - 1]))


def phi_upper(u: float, ts: np.ndarray, upper: np.ndarray) -> float:
    """The upper bound at the grid point with the next larger u: phi rises with u."""
    if u <= 0.0:
        return 0.0
    i = int(math.floor(-math.log2(u) * PER_BIT))
    return float(upper[min(max(i, 0), ts.size - 1)])


def horizon(alpha, tau, c, logp, bpd, eps, ts=None, upper=None) -> float:
    if ts is None:
        return longest(alpha, tau, c, logp, bpd, eps)

    def chance(h):
        """b5_recovery_sweep.failure_over, hour by hour, with each epoch's sum ground."""
        ages = (np.arange(int(math.ceil(h * 24))) + 0.5) / 24
        ages = ages[ages <= h]
        share = alpha + c * (1 - alpha) * (1 - np.exp(-tau * ages))
        per_hour = bpd / 24 * np.exp(np.interp(share, FORK, logp))
        per_epoch = np.bincount((ages // EPOCH_DAYS).astype(int), weights=per_hour)
        return min(1.0, sum(phi_upper(x, ts, upper) for x in per_epoch))

    if chance(1 / 24) > eps:
        return 0.0
    if chance(H_MAX_DAYS) <= eps:
        return math.inf
    lo, hi = 1 / 24, float(H_MAX_DAYS)
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if chance(mid) <= eps else (lo, mid)
    return lo


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    growth = {"random, testnet": float(s[(s.blend_hops == 1) & (s.blend_delay_max == 1)].growth_per_f.iloc[0]),
              "random, specification": float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)]
                                             .growth_per_f.iloc[0])}
    models = {name: dict(growth=g) for name, g in growth.items()} | {"worst, 10 s": dict(delta=10)}
    pts = [(m, a) for m in models for a in ALPHAS]
    rows = Parallel(n_jobs=-2)(delayed(point)(m, models[m], a) for m, a in pts)
    curves = {(r["model"], r["alpha"]): (r.pop("_ts"), r.pop("_upper")) for r in rows}
    t = pd.DataFrame(rows)

    fit = pd.read_csv(HERE / "runs" / "e2" / "fit.csv")
    fit = fit[(fit.structure == "chain") & np.isclose(fit.f, F)]
    b2 = pd.read_csv(HERE / "runs" / "b2" / "curves.csv")
    b2d = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    depth, rho = [], []
    for _, r in t.iterrows():
        if r.model.startswith("random"):
            x = fit[(fit.blend == r.model.split(", ")[1]) & np.isclose(fit.alpha, r.alpha, atol=1e-3)]
            depth.append(float(x["depth_1e-09"].iloc[0]) if len(x) else math.nan)
            rho.append(float(x.rho.iloc[0]) if len(x) else math.nan)
        else:
            x, y = b2_upper(b2, b2d, r.alpha, 10)
            depth.append(x)
            rho.append(y)
    t["depth_1e-09"], t["rho"] = depth, rho
    for side in ("lo", "hi"):
        t[f"extra_{side}_1e-09"] = np.log(t[f"factor_{side}_1e-09"]) / t.rho
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "grinding.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.3g}"), end="\n\n")

    delays = sorted(b2.delay_s.unique())
    shares = sorted(b2.adv.unique())
    dpts = [(a, int(d), BUDGET_BITS) for a in shares for d in delays] + \
        [(a, int(d), 40) for a in (0.25, 1 / 3) for d in delays]
    drows = Parallel(n_jobs=-2)(delayed(point)("worst", dict(delta=d), a, b) for a, d, b in dpts)
    for (a, d, _), r in zip(dpts, drows):
        r.pop("_ts"), r.pop("_upper")
        r["delay_s"] = d
        r["depth_1e-09"], r["rho"] = b2_upper(b2, b2d, a, d)
        for side in ("lo", "hi"):
            r[f"ground_{side}_1e-09"] = r["depth_1e-09"] + math.log(r[f"factor_{side}_1e-09"]) / r["rho"]
    d = pd.DataFrame(drows)
    d.to_csv(OUT / "delays.csv", index=False)
    with pd.option_context("display.width", 250):
        print(d.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    grid = np.round(np.arange(0.05, 0.4301, 0.01), 4)       # walks at 0.43 last up to 30,000 blocks
    gpts = [(m, a) for m in growth for a in grid]
    grows = Parallel(n_jobs=-2)(delayed(point)(m, models[m], a, per_bit=4, depths=32_000)
                                for m, a in gpts)
    held = []
    for m, g in growth.items():
        lnr = np.log([r["factor_hi_1e-09"] for (mm, _), r in zip(gpts, grows) if mm == m])
        for k in KS:
            held.append(dict(model=m, k=k, held=held_random(grid, lnr, g, k),
                             held_without=max_alpha(k, g, 1e-9)))
    w = d[d.budget_bits == BUDGET_BITS]
    for delay, g in w.groupby("delay_s"):
        g = g.sort_values("alpha")
        for k in KS:
            held.append(dict(model=f"worst, {delay} s", k=k,
                             held=held_worst(g.alpha.to_numpy(), g["ground_hi_1e-09"].to_numpy(), k),
                             held_without=held_worst(g.alpha.to_numpy(), g["depth_1e-09"].to_numpy(), k)))
    h = pd.DataFrame(held)
    h.to_csv(OUT / "shares.csv", index=False)
    print(h.to_string(index=False), end="\n\n")

    rec = []
    for model in ("random, specification", "worst, 10 s"):
        kw = models[model]
        for alpha in (0.10, 0.20, 0.25):
            rate = (1 / (10 + 1 / (1 - (1 - F) ** (1 - alpha))) if "delta" in kw
                    else kw["growth"] * (1 - (1 - F) ** (1 - alpha)))
            ts, upper = curves[(model, round(alpha, 4))]
            for wh in WINDOWS_H:
                logp = table(wh, alpha, kw)
                for tau in TAUS:
                    for c in CS:
                        rec.append(dict(model=model, alpha=alpha, window_h=wh, tau_per_day=tau, c=c,
                                        h_days=horizon(alpha, tau, c, logp, 86400 * rate, 1e-9),
                                        h_days_ground=horizon(alpha, tau, c, logp, 86400 * rate,
                                                              1e-9, ts, upper)))
    r = pd.DataFrame(rec)
    r.to_csv(OUT / "recovery.csv", index=False)
    with pd.option_context("display.max_rows", 200):
        print(r.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
