"""Phase K, K.5: the block rate with k counted in slots (RATE.md, "Counted in slots").

    python scripts/k5_rate.py      # needs runs/c1; writes runs/k5/rate.csv (about a minute)

At f = 1/30, 1/20 and 1/15, against 25 %, 30 % and a third, at eps = 1e-9:

- worst case, Delta = 10 s: B2's upper bound, computed here at D = f * Delta, since the port counts
  time in expected block intervals (b2_settlement.upper fixes f = 1/30); its depth on the clock
  Delta + 1/p_h of the honest chain the coalition withholds from (SETTLEMENT.md B2), and the wait
  slots.worst_needed bounds at that f;
- random delay, the specification's Blend: B5's closed form at C1's growth for the block interval
  (runs/c1/summary.csv, 3 hops of up to 3 rounds), on C1's clock, the interval over
  (1 - alpha) * growth, and the wait slots.wait_needed gives at that growth and f.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import MIN_PROB, MIN_STATES, alphabet_for
from finality_sim.lcbounds import slot_pdf, ub_curve
from finality_sim.private_race import strict_depth
from finality_sim.recovery import occupancy
from finality_sim.slots import wait_needed, worst_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k5"
INTERVALS = (30, 20, 15)
ALPHAS = (0.25, 0.30, 1 / 3)
DELTA_S = 10
EPS = 1e-9
FLOOR = 1e-14
K_MAX = 60_000


def worst(alpha: float, interval: int) -> dict:
    f = 1 / interval
    d = f * DELTA_S
    a = alphabet_for(alpha, d)
    ub = ub_curve(K_MAX, slot_pdf(1 - alpha, d, a), a, max(MIN_STATES, a + 1), MIN_PROB, FLOOR)
    log_ub = np.log(np.minimum(ub, 1.0))
    depth = int(np.argmax(ub <= EPS)) + 1
    clock = DELTA_S + 1 / occupancy(f, 1 - alpha)
    wait = worst_needed(alpha, EPS, DELTA_S, log_ub, f)
    return dict(alpha=alpha, interval=interval, D=d, worst_depth=depth, worst_clock_s=clock,
                worst_depth_h=depth * clock / 3600, worst_wait=wait, worst_wait_h=wait / 3600)


def main() -> None:
    c1 = pd.read_csv(HERE / "runs" / "c1" / "summary.csv")
    rows = Parallel(n_jobs=4)(delayed(worst)(a, i) for i in INTERVALS for a in ALPHAS)
    for r in rows:
        alpha, interval = r["alpha"], r["interval"]
        f = 1 / interval
        g = float(c1[(c1.hops == 3) & (c1.delta_max == 3) & (c1.interval == interval)]
                  .growth_per_f.iloc[0])
        q = alpha / (alpha + (1 - alpha) * g)
        depth = strict_depth(q, math.log(EPS), lead=True)
        clock = interval / ((1 - alpha) * g)
        wait = wait_needed(alpha, EPS, g, f)
        r.update(growth=g, random_depth=depth, random_clock_s=clock,
                 random_depth_h=depth * clock / 3600, random_wait=wait, random_wait_h=wait / 3600)
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rate.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
