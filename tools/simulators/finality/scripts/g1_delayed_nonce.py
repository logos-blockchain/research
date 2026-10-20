"""Phase G1: the smallest contributions with a delayed nonce (PLAN.md, G1).

    python scripts/g1_delayed_nonce.py      # needs runs/a1, runs/b2, runs/b7; writes runs/g1/*.csv

With the nonce of B7 passed through a sequential delay that spans the last sub-window plus a margin
of T minutes on the coalition's hardware, a candidate's value reaches the coalition T after the
cut-off at the earliest, and counts only if the coalition can still publish a fork that reaches it
(src/finality_sim/formation.py).

open.csv: the chance that a choice is still open T minutes after the cut-off, for B6's delay models:
the law under random delay (formation.open_law), 400,000 windows a point under the worst case.
factor.csv: the factor per nonce, B7's G_min at the cut-off and, at margins of 5 to 30 minutes, the
values seen while reachable with B7's contributions, which the coalition knows ahead, formed at the
sub-window's start and the honest minima when their blocks arrive (formation.formation_counts,
20,000 windows a point with 20,000 near slots), and the depth at 1e-9 with two nonces read as B7
reads its factors, beside the unground depth and B7's estimate.
recovery.csv: B6's recovery horizon with the factor at T = 10 minutes, as B7 computes it for its
own factor.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b6_grinding import TAUS, WINDOWS_H, horizons
from b7_nonce import curve, depth_reader, models
from finality_sim.formation import formation_counts, open_law

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g1"
ALPHAS = (0.25, 0.30, 1 / 3)
KS = (2160, 1620, 1080)
MINUTES = (1, 2, 5, 10, 20, 30, 60)
MARGINS = (5, 10, 20, 30)
SAMPLES = 20_000
OPEN_SAMPLES = 400_000
EPS = 1e-9
JOBS = 4


def open_row(name: str, kw: dict, alpha: float, seed: int) -> list[dict]:
    if "growth" in kw:
        p = [open_law(F, alpha, 60 * t, kw["growth"]) for t in MINUTES]
        n = 0
    else:
        r = formation_counts(F, alpha, 6 * math.floor(2160 / F), 25, [60 * t for t in MINUTES], OPEN_SAMPLES,
                             seed, near_slots=6_000, level=0, **kw)
        p, n = list(r["open"].mean(axis=0)), OPEN_SAMPLES
    return [dict(model=name, alpha=round(alpha, 4), minutes=t, p_open=float(x), windows=n)
            for t, x in zip(MINUTES, p)]


def factor(name: str, kw: dict, alpha: float, k: int, m: int, seed: int) -> dict:
    window = 6 * math.floor(k / F)
    r = formation_counts(F, alpha, window, m, [60 * t for t in MARGINS], SAMPLES, seed, level=1, **kw)
    row = dict(model=name, alpha=round(alpha, 4), k=k, sub_windows=m, g_min=float(r["g"].mean()),
               crossing=float(r["cross"].mean()))
    for t, f, o in zip(MARGINS, r["per_win"].mean(axis=0), r["open_factor"].mean(axis=0)):
        row[f"factor_{t}"] = float(f)
        row[f"open_factor_{t}"] = float(o)
    return row


def main() -> None:
    ms = {n: kw for n, (kw, _) in models().items() if n != "random, testnet"}
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(n, a) for n in ms for a in ALPHAS]
    got = Parallel(n_jobs=JOBS)(delayed(open_row)(n, ms[n], a, 101 + int(a * 1000)) for n, a in jobs)
    op = pd.DataFrame([r for rows in got for r in rows])
    op.to_csv(OUT / "open.csv", index=False)
    print(op.pivot_table(index=["model", "alpha"], columns="minutes", values="p_open")
          .to_string(float_format=lambda v: f"{v:.2g}"))

    b7 = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}
    m_of = {k: int(b7[b7.k == k].sub_windows.iloc[0]) for k in KS}
    pts = [(n, a, k) for n in ms for a in ALPHAS[1:] for k in KS]
    out = Parallel(n_jobs=JOBS)(delayed(factor)(n, ms[n], a, k, m_of[k], 7919 * k + 31 * int(a * 1000))
                                for n, a, k in pts)
    for (n, a, k), r in zip(pts, out):
        at = depth_reader(ms[n], a, log_ub)
        x = b7[(b7.model == n) & (b7.alpha == round(a, 4)) & (b7.k == k)].iloc[0]
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_g_min"] = at(math.log(EPS / r["g_min"] ** 2))
        for t in MARGINS:
            r[f"depth_{t}"] = at(math.log(EPS / r[f"factor_{t}"] ** 2))
            r[f"depth_open_{t}"] = at(math.log(EPS / r[f"open_factor_{t}"] ** 2))
        r["depth_two_lo"], r["depth_two_hi"] = x.depth_two_lo, x.depth_two_hi
    t = pd.DataFrame(out)
    t.to_csv(OUT / "factor.csv", index=False)
    print()
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    # B6's recovery horizon with the factor that remains at a margin of 10 minutes, as B7 computes it
    f10 = {(r["model"], r["alpha"], r["k"]): r["factor_10"] for r in out}
    rjobs = [(n, a, k, max(WINDOWS_H[k]), tau) for n in ms for a in (0.30, 1 / 3) for k in KS
             for tau in TAUS]
    rec = Parallel(n_jobs=JOBS)(delayed(horizons)(n, ms[n], a, k, w, tau, 1.0,
                                                  curve(f10[(n, round(a, 4), k)]),
                                                  curve(f10[(n, round(a, 4), k)] ** 2))
                                for n, a, k, w, tau in rjobs)
    r = pd.DataFrame(rec).rename(columns={"h_days_ground": "h_days_delayed"})
    r.to_csv(OUT / "recovery.csv", index=False)
    print()
    print(r.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
