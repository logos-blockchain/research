"""Phase E2: the paper's empirical settlement procedure on the DAG and on the chain (PLAN.md E2).

    python scripts/e2_fit.py          # needs runs/e2/race.csv and runs/c4/race.csv

Areon's §5.6: fit P(d) = A exp(-rho d) to the share of targets the attack displaces at depth d,
and read d*(eps) = ln(A / eps) / rho. The fit uses the depths whose share lies in [1e-4, 1e-1]
and rests on at least 10 successes; a point with fewer than three such depths gets no fit. The
same procedure is applied to the chain's race of C4 (the constant lotteries), so that both are
extrapolated alike. Times divide the depth by the honest chain's or DAG's growth.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent.parent
EPS = (1e-3, 1e-6, 1e-9)
CHAIN = {"constant": 1 / 30, "constant, 20 s": 1 / 20, "constant, 15 s": 1 / 15}


def fit(succ: np.ndarray, scored: int) -> tuple[float, float, int]:
    p = succ / scored
    k = np.arange(1, succ.size + 1)
    ok = (p >= 1e-4) & (p <= 1e-1) & (succ >= 10)
    if ok.sum() < 3:
        return math.nan, math.nan, int(ok.sum())
    slope, icpt = np.polyfit(k[ok], np.log(p[ok]), 1)
    return math.exp(icpt), -slope, int(ok.sum())


def rows_for(g: pd.DataFrame, kmax: int, per_slot: float) -> dict:
    tot = g.sum(numeric_only=True)
    succ = np.array([tot[f"s{k}"] for k in range(1, kmax + 1)], dtype=float)
    a, rho, n = fit(succ, int(tot.scored))
    row = dict(A=a, rho=rho, fit_points=n, slots_per_unit=1 / per_slot)
    for eps in EPS:
        d = math.log(a / eps) / rho if n >= 3 else math.nan
        row[f"depth_{eps:.0e}"] = d
        row[f"minutes_{eps:.0e}"] = d / per_slot / 60
    return row


def main() -> None:
    out = []
    r = pd.read_csv(HERE / "runs" / "e2" / "race.csv")
    r = r[r.horizon == "since the fork"]
    for (f, blend, alpha), g in r.groupby(["f", "blend", "alpha"], sort=False):
        out.append(dict(structure="DAG", f=f, blend=blend, alpha=alpha,
                        **rows_for(g, 60, g.layers_per_slot.mean())))
    c = pd.read_csv(HERE / "runs" / "c4" / "race.csv")
    c = c[c.curve.isin(list(CHAIN))]
    kmax = max(int(x[1:]) for x in c.columns if x.startswith("s") and x[1:].isdigit())
    for (curve, blend, alpha), g in c.groupby(["curve", "blend", "alpha"], sort=False):
        out.append(dict(structure="chain", f=CHAIN[curve], blend=blend, alpha=alpha,
                        **rows_for(g, kmax, g.honest_per_f.mean() / 30)))
    t = pd.DataFrame(out)
    t.to_csv(HERE / "runs" / "e2" / "fit.csv", index=False)
    with pd.option_context("display.width", 220, "display.max_rows", 200):
        print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
