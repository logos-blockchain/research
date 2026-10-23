"""Phase K.7: a bound for a wait of T slots in the model of Gaži, Ren and Russell (SLOTS.md K.7).

    python scripts/k7_wait.py      # needs runs/a1, runs/k1, runs/k2, runs/b6, runs/h2, runs/g3;
                                   # writes runs/k7/ (about 40 minutes on 12 cores)

The bound of finality_sim.waitbound: LCanalysis's chain frozen at the phase in which the wait
passes, each phase costed by its wait for the next success, rounded up to a slot, and its span,
charged h·Δ. On the slot lottery the chain runs at Δ + 1 slots and −ln(1 − f) successes a slot
(waitbound.wait_curve, slots); B2 reads the paper's model at Δ and f, the continuous reading.

- worst.csv: the wait at 1e-6 and 1e-9 for α from 5 % to a third and Δ from 1 to 20 s, on slots
  and in the continuous reading, beside K.1's bound, which reads B2 continuously, and the attack's
  estimate (runs/k1/worst.csv).
- checks.csv: at four points, the wait with half-slot levels, with twice the states, and with the
  spans charged at the depth they add, which is not a bound and brackets what h·Δ costs.
- played.csv: the continuous reading beside its chain played with true lengths in continuous time,
  and the bound on slots beside the paper's attack against a wait on the per-slot lottery, whose
  standard error is the spread of 16 runs' rates (the gates' runs, more targets).
- holds.csv, waits.csv, absorbs.csv: K.2's worst-case readings under the bound, with K.2's
  factors (runs/k2/factors.csv; runs/b6/delays.csv; runs/h2/formation.csv through
  k2_holds.h2_factor). A deflated inference raises both shares' rates by 1/(1 − α) with the shares
  unchanged (wait_curve's scale), read in slots. holds.csv reads B5's grid
  of shares, linear between grid points (b5_what_k_holds.held_worst).
- rate.csv: at f = 1/30, 1/20 and 1/15, 10 s, against 25 %, 30 % and a third (RATE.md, K.5).
- blend.csv: G3's Blend settings at their worst-case delay against 30 % and a third (K.5).
- floor.csv: K.3's floor at the least K against a third at 10 s under the bound.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b5_what_k_holds import GRID, held_worst
from k2_holds import WGRID, h2_factor, windows
from k3_splits import growth, models
from finality_sim.floor import chain_rate, floor_for, log_short, provisional_share
from finality_sim.grr_attack import _symbols_timed, occupancy
from finality_sim.waitbound import (alphabet_for, attack_longest, play_chain, steps, wait_curve,
                                    wait_needed)

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k7"
F = 1 / 30
EPSS = (1e-6, 1e-9)
EPS = 1e-9
ADV = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
DELAYS_S = (1, 2, 3, 5, 8, 10, 15, 20)
K2_DELAYS = (1, 10, 20)
JOBS = 12
GRID_FLOOR = 1e-50              # past every factor K.2 applies, up to 1e37
GRID_T = 3 * math.floor(2160 / F)
WAIT_T = 1_500_000
WAIT_FLOOR = 1e-50
CHECKS = ((1 / 3, 10), (1 / 3, 20), (0.10, 10), (1 / 3, 1))
PLAYED = ((1 / 3, 10), (0.25, 5), (1 / 3, 1))
PLAYED_WAITS = (900, 1_800, 3_600, 7_200)
INTERVALS = (30, 20, 15)


def need(alpha: float, delta_s: float, eps: float, f: float = F, t_max: int = WAIT_T,
         scale: float = 1.0) -> int:
    """The least wait, in slots, whose bound on slots is at most ``eps``; -1 past ``t_max``."""
    return wait_needed(wait_curve(t_max, alpha, delta_s, f, floor=eps / 10, scale=scale), eps)


def worst_row(alpha: float, delta_s: int) -> dict:
    row = dict(alpha=alpha, delta_s=delta_s)
    for name, slots in (("", True), ("cont_", False)):
        c = wait_curve(WAIT_T, alpha, delta_s, floor=1e-12, slots=slots)
        for eps in EPSS:
            t = wait_needed(c, eps)
            row[f"{name}wait_{eps:g}"] = t
            row[f"{name}wait_h_{eps:g}"] = t / 3600 if t > 0 else math.nan
    return row


def check_row(alpha: float, delta_s: int, kind: str) -> dict:
    a = alphabet_for(alpha, F * delta_s)
    kw, unit = {}, 1.0
    if kind == "half-slot levels":
        kw, unit = dict(unit=0.5), 0.5
    elif kind == "spans at the depth they add":
        kw = dict(body="d")
    elif kind == "twice the states":
        kw = dict(states=2 * max(30, a + 1))
    c = wait_curve(int(WAIT_T / unit), alpha, delta_s, floor=1e-10, **kw)
    return dict(alpha=alpha, delta_s=delta_s, kind=kind,
                **{f"wait_h_{e:g}": wait_needed(c, e) * unit / 3600 for e in EPSS})


def played_row(alpha: float, delta_s: int) -> list[dict]:
    waits = np.array(PLAYED_WAITS, float)
    curve = wait_curve(int(waits[-1]) + 10, alpha, delta_s)
    cont = wait_curve(int(waits[-1]) + 10, alpha, delta_s, slots=False)
    fails = np.zeros(waits.size)
    total = 0
    for seed in range(16):
        hs, ds, as_, ends = steps(4_000_000, (1 - alpha) * F, alpha * F, delta_s, seed)
        f, done = play_chain(hs, ds, as_, ends, waits, 40_000, 200, 20_000.0, 1_000 + seed)
        fails += f
        total += done
    per_run = []
    n = 0
    for seed in range(16):
        d_sym, a_sym, t_sym = _symbols_timed(3_000_000, occupancy(F, 1 - alpha),
                                             occupancy(F, alpha), delta_s, 2_000 + seed)
        longest = attack_longest(d_sym, a_sym, t_sym, 2_000, 60)
        scored = longest[longest > -2]
        n += scored.size
        per_run.append([(scored >= t).mean() for t in waits])
    per_run = np.array(per_run)
    rows = []
    for i, t in enumerate(waits):
        rate = fails[i] / total
        rows.append(dict(alpha=alpha, delta_s=delta_s, wait=int(t), bound=curve[int(t) - 1],
                         continuous=cont[int(t) - 1], chain=rate,
                         chain_se=math.sqrt(rate * (1 - rate) / total), chain_targets=total,
                         attack=per_run[:, i].mean(),
                         attack_se=per_run[:, i].std(ddof=1) / math.sqrt(len(per_run)),
                         attack_targets=n))
    return rows


def grid_logs(alpha: float, delta_s: int, deflate: bool) -> np.ndarray:
    """log of the bound at waits 1..GRID_T, the floor's log past the curve's end."""
    c = wait_curve(GRID_T, alpha, delta_s, floor=GRID_FLOOR, scale=1 / (1 - alpha) if deflate else 1.0)
    out = np.full(GRID_T, math.log(GRID_FLOOR))
    with np.errstate(divide="ignore"):
        out[:c.size] = np.log(np.maximum(c, 1e-300))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    par = Parallel(n_jobs=JOBS)

    # the wait over the grid of K.1
    rows = par(delayed(worst_row)(a, d) for a in ADV for d in DELAYS_S)
    w = pd.DataFrame(rows)
    k1 = pd.read_csv(HERE / "runs" / "k1" / "worst.csv")
    for eps in EPSS:
        k = k1[np.isclose(k1.eps, eps)]
        key = [(round(a, 4), d) for a, d in zip(k.alpha, k.delay_s)]
        look = dict(zip(key, k.wait_h))
        est = dict(zip(key, k.lb_h_estimate))
        mark = dict(zip(key, k.lb_extrapolated))
        w[f"k1_h_{eps:g}"] = [look[(round(a, 4), d)] for a, d in zip(w.alpha, w.delta_s)]
        w[f"attack_h_{eps:g}"] = [est[(round(a, 4), d)] for a, d in zip(w.alpha, w.delta_s)]
        w[f"attack_extrapolated_{eps:g}"] = [mark[(round(a, 4), d)] for a, d in zip(w.alpha, w.delta_s)]
        w[f"k1_over_k7_{eps:g}"] = w[f"k1_h_{eps:g}"] / w[f"cont_wait_h_{eps:g}"]
        w[f"slots_over_cont_{eps:g}"] = w[f"wait_h_{eps:g}"] / w[f"cont_wait_h_{eps:g}"]
    w.to_csv(OUT / "worst.csv", index=False)
    print(w.round(3).to_string(index=False), end="\n\n")

    kinds = ("the bound", "half-slot levels", "twice the states", "spans at the depth they add")
    c = pd.DataFrame(par(delayed(check_row)(a, d, k) for a, d in CHECKS for k in kinds))
    c.to_csv(OUT / "checks.csv", index=False)
    print(c.round(3).to_string(index=False), end="\n\n")

    p = pd.DataFrame([r for rows in par(delayed(played_row)(a, d) for a, d in PLAYED) for r in rows])
    p.to_csv(OUT / "played.csv", index=False)
    print(p.to_string(index=False), end="\n\n")

    # K.2 under the bound: the curves on B5's grid, at the old rates and deflated
    pts = [(float(a), d, dfl) for d in K2_DELAYS for a in GRID for dfl in (False, True)]
    logs = par(delayed(grid_logs)(a, d, dfl) for a, d, dfl in pts)
    table = {(round(a, 4), d, dfl): lg for (a, d, dfl), lg in zip(pts, logs)}
    fac = pd.read_csv(HERE / "runs" / "k2" / "factors.csv")
    hrows = []
    for d in K2_DELAYS:
        model = f"worst, {d} s"
        f = fac[fac.model == model].sort_values("alpha")
        one = np.interp(GRID, WGRID, np.log(f.factor_hi))
        two = np.interp(GRID, WGRID, np.log(f.pair_hi))
        for k, rd, K in windows():
            base = np.array([table[(round(float(a), 4), d, False)][K - 1] for a in GRID])
            dfl = np.array([table[(round(float(a), 4), d, True)][K - 1] for a in GRID])
            cases = {"without": held_worst(base, EPS), "one": held_worst(base, EPS, one),
                     "two": held_worst(base, EPS, two), "deflated": held_worst(dfl, EPS)}
            if d == 10:
                cases["nonce §3.1"] = held_worst(base, EPS, 2 * math.log(h2_factor(model, 1 / 3)))
            for case, v in cases.items():
                hrows.append(dict(model=model, k=k, reading=rd, K=K, case=case, held=v))
    h = pd.DataFrame(hrows)
    h.to_csv(OUT / "holds.csv", index=False)
    with pd.option_context("display.max_rows", 500, "display.width", 200):
        print(h.pivot_table(index=["model", "k", "reading"], columns="case", values="held").to_string(
            float_format=lambda v: f"{v:.3f}"), end="\n\n")

    # the waits at k = 2160 against 30 % and a third
    b6d = pd.read_csv(HERE / "runs" / "b6" / "delays.csv")
    jobs = []
    for d in K2_DELAYS:
        model = f"worst, {d} s"
        for alpha in (0.30, 1 / 3):
            src = b6d[np.isclose(b6d.alpha, round(alpha, 4)) & (b6d.delay_s == d)
                      & (b6d.budget_bits == 64)].iloc[0]
            cases = [("without", 1.0, False), ("one ground nonce, lower end", src["factor_lo_1e-09"], False),
                     ("one ground nonce, upper end", src["factor_hi_1e-09"], False),
                     ("two ground nonces, lower end", src["pair_lo_1e-09"], False),
                     ("two ground nonces, upper end", src["pair_hi_1e-09"], False),
                     ("deflated", 1.0, True)]
            if d == 10:
                r2 = h2_factor(model, alpha) ** 2
                cases += [("nonce §3.1, two nonces at H.2's bound", r2, False),
                          ("deflated, nonce §3.1 at H.2's bound at the old rates", r2, True)]
            jobs += [(model, d, alpha, case, r, dfl) for case, r, dfl in cases]
    waits = par(delayed(need)(alpha, d, EPS / r, scale=1 / (1 - alpha) if dfl else 1.0)
                for _, d, alpha, _, r, dfl in jobs)
    wt = pd.DataFrame([dict(model=m, alpha=a, case=cs, factor=r, wait_slots=t)
                       for (m, _, a, cs, r, _), t in zip(jobs, waits)])
    wt["wait_h"] = np.where(wt.wait_slots > 0, wt.wait_slots / 3600, np.nan)
    for K in (math.floor(2160 / F), 3 * math.floor(2160 / F)):
        wt[f"holds_{K}"] = (wt.wait_slots > 0) & (wt.wait_slots <= K)
    k2w = pd.read_csv(HERE / "runs" / "k2" / "waits.csv")
    look = {(m, round(a, 4), cs): v for m, a, cs, v in zip(k2w.model, k2w.alpha, k2w.case, k2w.wait_h)}
    wt["k1_wait_h"] = [look.get((m, round(a, 4), cs), math.nan)
                       for m, a, cs in zip(wt.model, wt.alpha, wt.case)]
    wt.to_csv(OUT / "waits.csv", index=False)
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(wt.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    # the chance after each candidate at 10 s, and the largest factor it absorbs
    arows = []
    for alpha in (0.30, 1 / 3):
        plain = wait_curve(GRID_T, alpha, 10, floor=1e-55)
        dfl = wait_curve(GRID_T, alpha, 10, floor=1e-55, scale=1 / (1 - alpha))
        for K in (math.floor(2160 / F), 3 * math.floor(2160 / F)):
            cp = plain[K - 1] if plain.size >= K else math.nan
            cd = dfl[K - 1] if dfl.size >= K else math.nan
            arows.append(dict(alpha=alpha, K=K, chance=cp, below_1e55=plain.size < K,
                              absorbs=EPS / cp if cp == cp else math.nan,
                              chance_deflated=cd, below_1e55_deflated=dfl.size < K,
                              absorbs_deflated=EPS / cd if cd == cd else math.nan))
    a = pd.DataFrame(arows)
    a.to_csv(OUT / "absorbs.csv", index=False)
    print(a.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    # K.5: the block rate, at 10 s
    k5r = pd.read_csv(HERE / "runs" / "k5" / "rate.csv")
    rjobs = [(a, i) for i in INTERVALS for a in (0.25, 0.30, 1 / 3)]
    rw = par(delayed(need)(a, 10, EPS, 1 / i) for a, i in rjobs)
    rate = pd.DataFrame([dict(alpha=a, interval=i, wait=t, wait_h=t / 3600) for (a, i), t in zip(rjobs, rw)])
    look = {(round(a, 4), i): v for a, i, v in zip(k5r.alpha, k5r.interval, k5r.worst_wait_h)}
    rate["k1_wait_h"] = [look[(round(a, 4), i)] for a, i in zip(rate.alpha, rate.interval)]
    rate.to_csv(OUT / "rate.csv", index=False)
    print(rate.round(3).to_string(index=False), end="\n\n")

    # K.5: G3's Blend settings
    k5b = pd.read_csv(HERE / "runs" / "k5" / "blend.csv")
    bl = k5b[np.isfinite(k5b.worst_depth)].copy()
    bw = par(delayed(need)(float(a), int(d), EPS) for a, d in zip(bl.alpha, bl.delta_s))
    bl["k7_wait_h"] = [t / 3600 for t in bw]
    bl.to_csv(OUT / "blend.csv", index=False)
    print(bl.round(3).to_string(index=False), end="\n\n")

    # K.3's floor at the least K against a third at 10 s
    least = need(1 / 3, 10, EPS)
    g = growth()
    frows = []
    for alpha in (0.25, 0.30, 1 / 3):
        for mname, kw in models(g).items():
            phi = floor_for(least, alpha, EPS, F, **kw)
            prov = provisional_share(least, phi, EPS)
            frows.append(dict(window="K.7's least against a third at 10 s", slots=least,
                              hours=least / 3600, alpha=alpha, model=mname, phi=phi,
                              expected=least * chain_rate(1.0 - alpha, F, **kw),
                              log10_wait_full=log_short(least, phi, 1.0, F, **kw) / math.log(10),
                              log10_wait_attacked=log_short(least, phi, 1.0 - alpha, F, **kw) / math.log(10),
                              provisional_share=prov, provisional_honest=prov - alpha))
    fl = pd.DataFrame(frows)
    fl.to_csv(OUT / "floor.csv", index=False)
    print(fl.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
