"""Phase C3: the largest tolerable adversary share under each fork-choice rule (PLAN.md C3).

    python scripts/c3_ghost.py        # writes runs/c3/regions.csv

The slot lottery's wins are Poisson at lambda = -ln(1 - f) per slot (E5's rate), split between the
honest side and the adversary by stake.
"""

import math
import pathlib

import pandas as pd

from finality_sim.ghost import RULES, max_share

F = 1 / 30
DELAYS_S = (1, 2, 3, 5, 8, 10, 15, 20, 30)
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "c3"

rows = [dict(rule=name, **{f"{d} s": max_share(rule, -math.log(1 - F), d) for d in DELAYS_S})
        for name, rule in RULES.items()]
OUT.mkdir(parents=True, exist_ok=True)
t = pd.DataFrame(rows)
t.to_csv(OUT / "regions.csv", index=False)
print("largest adversary stake share, f = 1/30, worst-case delay Delta (s)")
print(t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
