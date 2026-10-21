"""Phase K.2: the largest share a finality window of K slots holds (SLOTS.md K.2).

    python scripts/k2_holds.py      # needs runs/a1, runs/b2, runs/b6, runs/g7, runs/h2; writes runs/k2/

K is read at ⌊k/f⌋ and 3⌊k/f⌋ slots for k = 2160, 1620, 1080, 432, 216 and 120: the time k blocks
take at the full rate with no forks, and the specification's slot parameter s. A K holds a share
at 1e-9 when the chance against a wait of K slots (src/finality_sim/slots.py), multiplied by a
factor R for grinding, is at most 1e-9.

- Random delay: the private race in B4's model at A1's growth on testnet's Blend and the
  specification's (slots.wait_logfail); the largest share by bisection, as B6's held_random.
- Worst case at 1, 10 and 20 s: the bound of slots.worst_logbound at T = K, on B5's grid of shares
  (0.05 to 1/3 in steps of 0.005), from B2's upper bound computed here at every depth up to 7,000
  (ub_grid.parquet); linear in the share between grid points, as B5's held_worst.

The factors: today's nonce, one and two ground nonces, are B6's upper ends at 1e-9 (factor_hi,
pair_hi), recomputed here on B6's grids with B6's own settings (factors.csv) and interpolated in
log over shares as B6 does; the script checks that they return B6's shares.csv for k in blocks.
The nonce of §3.1 under H.2's delay carries H.2's bound at one delay evaluator,
gmin_bound + blind_bound + multi_bound at a margin of 10 minutes and the sub-windows of k = 2160
(runs/h2/formation.csv), squared for two nonces; H.2 computes it at 30 % and a third on the
specification's Blend and at 10 s, so its column takes the third's factor at every share up to a
third, where the factor is largest, and reads no share above a third.

A deflated inference (FURTHER.md G7) raises every lottery threshold by 1/(1 − α): per slot the
honest stake wins at f and the coalition at occupancy(f, α/(1 − α)). Under the worst case Δ stays
fixed in slots, so B2's curve is read at the delay Δ/(1 − α) at the old rates, as G7 reads it,
with the renewal and lead laws at the raised rates. Under random delay, in the convention's model
both rates rise by 1/(1 − α) and the race keeps its ratio, so a wait of K slots after a
deflation is a wait of K/(1 − α) at the old rates; on the engine G7's deflated arm measured the
growth of the chain then (runs/g7/engine.csv, one copy released at the slot).

holds.csv: the largest share each K holds, per model and case. waits.csv: for k = 2160, the wait
against 30 % and a third in each case, beside both candidate K, at 10 s, at 1 and 20 s, and on
the specification's Blend under random delay; and the largest factor each candidate absorbs.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import upper
from b5_what_k_holds import GRID, held_worst, max_alpha
from b6_grinding import RANDOM_TOP, held_random as b6_held_random, point
from finality_sim.recovery import occupancy
from finality_sim.slots import lead_law, rates, wait_logfail, wait_needed, worst_logbound, worst_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k2"
F = 1 / 30
EPS = 1e-9
KS = (2160, 1620, 1080, 432, 216, 120)
DELAYS = (1, 10, 20)
DEPTH_CAP = 7_000
UB_FLOOR = 1e-45
JOBS = 6
WGRID = np.append(np.round(np.arange(0.05, 1 / 3, 0.01), 4), 1 / 3)       # B6's worst-case grid
RGRID = {m: np.round(np.arange(0.05, top + 1e-9, 0.01), 4) for m, top in RANDOM_TOP.items()}


def windows() -> list[tuple[int, str, int]]:
    """(k, reading, K) for both readings of K at every k."""
    return [(k, r, (1 if r == "⌊k/f⌋" else 3) * math.floor(k / F)) for k in KS
            for r in ("⌊k/f⌋", "3⌊k/f⌋")]


def growths() -> dict[str, float]:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    return {"random, testnet": float(s[(s.blend_hops == 1) & (s.blend_delay_max == 1)].growth_per_f.iloc[0]),
            "random, specification": float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)]
                                           .growth_per_f.iloc[0])}


def curve(alpha: float, delay_s: float) -> np.ndarray:
    """log of B2's upper bound at depths 1 .. DEPTH_CAP, or until it is at most UB_FLOOR."""
    with np.errstate(divide="ignore"):
        return np.log(np.minimum(upper(alpha, delay_s, DEPTH_CAP, floor=UB_FLOOR), 1.0))


def deflated(alpha: float) -> tuple[float, float]:
    """The honest stake's and the coalition's slot occupancy once every threshold is raised by
    1/(1 − α)."""
    return occupancy(F, 1.0), occupancy(F, alpha / (1 - alpha))


def worst_log(alpha: float, delta: int, K: int, log_ub: np.ndarray, deflate: bool) -> float:
    p_h, p_a = deflated(alpha) if deflate else (occupancy(F, 1 - alpha), occupancy(F, alpha))
    return worst_logbound(K, alpha, delta, log_ub, F, lead_law(p_a, p_h, delta), p_h, p_a)[0]


def held_random(K: int, g: float, lnr=None, top: float = 0.5, scale=None) -> float:
    """The largest share whose chance against a wait of K slots, times R, stays at or below EPS;
    ``top`` when it holds there. ``scale(a)`` stretches the wait, for the deflated race."""
    def ok(a: float) -> bool:
        x, y = rates(a, g, F)
        if x >= y:
            return False
        t = K if scale is None else K * scale(a)
        extra = 0.0 if lnr is None else float(lnr(a))
        return wait_logfail(t, a, g, F) + extra <= math.log(EPS)
    if ok(top):
        return top
    lo, hi = 0.0, top
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo


def h2_factor(model: str, alpha: float, k: int = 2160, margin: int = 10) -> float:
    """H.2's bound on the factor per nonce at one delay evaluator."""
    f = pd.read_csv(HERE / "runs" / "h2" / "formation.csv")
    r = f[(f.model == model) & np.isclose(f.alpha, round(alpha, 4)) & (f.k == k)
          & (f.margin == margin)].iloc[0]
    return float(r.gmin_bound + r.blind_bound + r.multi_bound)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gs = growths()

    # B6's factors on B6's grids, with B6's settings
    fpts = [(m, dict(growth=g), a, dict(per_bit=4, depths=32_000, floor=200 if a >= 0.38 else 100))
            for m, g in gs.items() for a in RGRID[m]]
    fpts += [(f"worst, {d} s", dict(delta=d), a, dict(per_bit=4)) for d in DELAYS for a in WGRID]
    frows = Parallel(n_jobs=JOBS)(delayed(point)(kw, a, **opt) for _, kw, a, opt in fpts)
    fac = pd.DataFrame([dict(model=m, alpha=a, factor_lo=r["factor_lo_1e-09"], factor_hi=r["factor_hi_1e-09"],
                             pair_lo=r["pair_lo_1e-09"], pair_hi=r["pair_hi_1e-09"])
                        for (m, _, a, _), r in zip(fpts, frows)])
    fac.to_csv(OUT / "factors.csv", index=False, float_format="%.17g")

    def lnr_curve(model: str, key: str):
        f = fac[fac.model == model].sort_values("alpha")
        xs, ys = f.alpha.to_numpy(), np.log(f[key].to_numpy())
        return lambda a: np.interp(a, xs, ys)

    # check: B6's shares for k in blocks come back from these factors
    b6 = pd.read_csv(HERE / "runs" / "b6" / "shares.csv")
    for m, g in gs.items():
        for k in (2160, 1080, 432):
            for col, key in (("held_one", "factor_hi"), ("held_two", "pair_hi")):
                got = b6_held_random(RGRID[m], np.log(fac[fac.model == m].sort_values("alpha")[key].to_numpy()),
                                     g, k)
                want = float(b6[(b6.model == m) & (b6.k == k)][col].iloc[0])
                if abs(got - want) > 1e-9:
                    raise ValueError(f"B6's shares not reproduced: {m} k={k} {col} {got} {want}")

    # B2's upper bound on B5's grid, at the old rates and at the deflated delay
    cpts = [(a, d, dfl) for d in DELAYS for a in GRID for dfl in (False, True)]
    logs = Parallel(n_jobs=JOBS)(delayed(curve)(float(a), d / (1 - a) if dfl else float(d))
                                 for a, d, dfl in cpts)
    pd.DataFrame([dict(alpha=a, delay_s=d, deflated=dfl, depth=i + 1, log_ub=v)
                  for (a, d, dfl), lg in zip(cpts, logs) for i, v in enumerate(lg)]).to_parquet(
        OUT / "ub_grid.parquet")
    log_ub = {(round(float(a), 4), d, dfl): lg for (a, d, dfl), lg in zip(cpts, logs)}

    wins = windows()
    rows = []
    # random delay
    for m, g in gs.items():
        top = RANDOM_TOP[m]
        one, two = lnr_curve(m, "factor_hi"), lnr_curve(m, "pair_hi")
        jobs = []
        for k, rd, K in wins:
            jobs += [(m, k, rd, K, "without", dict()), (m, k, rd, K, "one", dict(lnr=one, top=top)),
                     (m, k, rd, K, "two", dict(lnr=two, top=top)),
                     (m, k, rd, K, "deflated", dict(scale=lambda a: 1 / (1 - a)))]
            if m == "random, specification":
                f2 = 2 * math.log(h2_factor(m, 1 / 3))
                jobs.append((m, k, rd, K, "nonce §3.1", dict(lnr=lambda a, f2=f2: f2, top=1 / 3)))
        res = Parallel(n_jobs=JOBS)(delayed(held_random)(K, g, **kw) for _, _, _, K, _, kw in jobs)
        for (mm, k, rd, K, case, kw), v in zip(jobs, res):
            rows.append(dict(model=mm, k=k, reading=rd, K=K, case=case, held=v,
                             top=kw.get("top", math.nan)))
    # worst case
    for d in DELAYS:
        model = f"worst, {d} s"
        one = np.interp(GRID, WGRID, np.log(fac[fac.model == model].sort_values("alpha").factor_hi))
        two = np.interp(GRID, WGRID, np.log(fac[fac.model == model].sort_values("alpha").pair_hi))
        pts = [(K, float(a), dfl) for _, _, K in wins for a in GRID for dfl in (False, True)]
        vals = Parallel(n_jobs=JOBS)(delayed(worst_log)(a, d, K, log_ub[(round(a, 4), d, dfl)], dfl)
                                     for K, a, dfl in pts)
        table = {(K, round(a, 4), dfl): v for (K, a, dfl), v in zip(pts, vals)}
        for k, rd, K in wins:
            base = np.array([table[(K, round(float(a), 4), False)] for a in GRID])
            dfl = np.array([table[(K, round(float(a), 4), True)] for a in GRID])
            cases = {"without": held_worst(base, EPS), "one": held_worst(base, EPS, one),
                     "two": held_worst(base, EPS, two), "deflated": held_worst(dfl, EPS)}
            if d == 10:
                cases["nonce §3.1"] = held_worst(base, EPS, 2 * math.log(h2_factor(model, 1 / 3)))
            for case, v in cases.items():
                rows.append(dict(model=model, k=k, reading=rd, K=K, case=case, held=v, top=1 / 3))
    h = pd.DataFrame(rows)
    h.to_csv(OUT / "holds.csv", index=False)
    with pd.option_context("display.max_rows", 500, "display.width", 200):
        print(h.pivot_table(index=["model", "k", "reading"], columns="case", values="held").to_string(
            float_format=lambda v: f"{v:.3f}"), end="\n\n")

    # waits at k = 2160 against 30 % and a third
    b2 = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    b6g = pd.read_csv(HERE / "runs" / "b6" / "grinding.csv")
    b6d = pd.read_csv(HERE / "runs" / "b6" / "delays.csv")
    eng = pd.read_csv(HERE / "runs" / "g7" / "engine.csv")
    cand = (math.floor(2160 / F), 3 * math.floor(2160 / F))
    wrows = []
    for d in DELAYS:
        model = f"worst, {d} s"
        for alpha in (0.30, 1 / 3):
            c = b2[np.isclose(b2.adv, alpha) & (b2.delay_s == d)].sort_values("depth")
            lu = np.log(np.minimum(c.ub.to_numpy(), 1.0))
            src = b6d[np.isclose(b6d.alpha, round(alpha, 4)) & (b6d.delay_s == d) & (b6d.budget_bits == 64)].iloc[0]
            cases = [("without", 1.0), ("one ground nonce, lower end", src["factor_lo_1e-09"]),
                     ("one ground nonce, upper end", src["factor_hi_1e-09"]),
                     ("two ground nonces, lower end", src["pair_lo_1e-09"]),
                     ("two ground nonces, upper end", src["pair_hi_1e-09"])]
            if d == 10:
                cases.append(("nonce §3.1, two nonces at H.2's bound", h2_factor(model, alpha) ** 2))
            for case, r in cases:
                t = worst_needed(alpha, EPS / r, d, lu, F)
                wrows.append(dict(model=model, alpha=alpha, case=case, factor=r, wait_slots=t))
            p_h, p_a = deflated(alpha)
            ldf = log_ub[(round(alpha, 4), d, True)]
            dcases = [("deflated", 1.0)]
            if d == 10:
                dcases.append(("deflated, nonce §3.1 at H.2's bound at the old rates",
                               h2_factor(model, alpha) ** 2))
            for case, r in dcases:
                t = worst_needed(alpha, EPS / r, d, ldf, F, p_h=p_h, p_a=p_a)
                wrows.append(dict(model=model, alpha=alpha, case=case, factor=r, wait_slots=t))
    m = "random, specification"
    g = gs[m]
    for alpha in (0.30, 1 / 3):
        src = b6g[(b6g.model == m) & np.isclose(b6g.alpha, round(alpha, 4))].iloc[0]
        cases = [("without", 1.0), ("one ground nonce, lower end", src["factor_lo_1e-09"]),
                 ("one ground nonce, upper end", src["factor_hi_1e-09"]),
                 ("two ground nonces, lower end", src["pair_lo_1e-09"]),
                 ("two ground nonces, upper end", src["pair_hi_1e-09"]),
                 ("nonce §3.1, two nonces at H.2's bound", h2_factor(m, alpha) ** 2)]
        for case, r in cases:
            wrows.append(dict(model=m, alpha=alpha, case=case, factor=r,
                              wait_slots=wait_needed(alpha, EPS / r, g, F)))
        lam = -math.log(1 - F)
        t = wait_needed(alpha, EPS, g, F)
        wrows.append(dict(model=m, alpha=alpha, case="deflated, the convention's model", factor=1.0,
                          wait_slots=math.ceil(t * (1 - alpha))))
        gd = float(eng[np.isclose(eng.alpha, round(alpha, 4)) & (eng.arm == "deflated") & (eng.copies == 1)
                       & (~eng.next_round)].growth.iloc[0])
        wrows.append(dict(model=m, alpha=alpha, case="deflated, the engine's growth", factor=1.0,
                          wait_slots=wait_needed(alpha, EPS, g, F, a=alpha * lam / (1 - alpha), h=gd * lam)))
    w = pd.DataFrame(wrows)
    w["wait_h"] = w.wait_slots / 3600
    for K in cand:
        w[f"holds_{K}"] = (w.wait_slots >= 0) & (w.wait_slots <= K)
    w.to_csv(OUT / "waits.csv", index=False)
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(w.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    # the largest factor each candidate K absorbs at 10 s
    arows = []
    for alpha in (0.30, 1 / 3):
        c = b2[np.isclose(b2.adv, alpha) & (b2.delay_s == 10)].sort_values("depth")
        lu = np.log(np.minimum(c.ub.to_numpy(), 1.0))
        p_h, p_a = deflated(alpha)
        for K in cand:
            normal = worst_log(alpha, 10, K, lu, False)
            dfl = worst_log(alpha, 10, K, log_ub[(round(alpha, 4), 10, True)], True)
            arows.append(dict(alpha=alpha, K=K, absorbs=math.exp(math.log(EPS) - normal),
                              absorbs_deflated=math.exp(math.log(EPS) - dfl)))
    a = pd.DataFrame(arows)
    a.to_csv(OUT / "absorbs.csv", index=False)
    print(a.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
