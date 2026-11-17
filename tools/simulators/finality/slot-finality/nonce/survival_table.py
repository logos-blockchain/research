# Branch survival and the open-choice chance, exact, from model.py, beside the finality study's
# branch_survival (formation.py) where it exists. Hours are on the coalition's clock.
# Usage: python survival_table.py > survival_table.out
import os
import sys
import numpy as np
from model import survival, open_after, clock, F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from finality_sim.formation import branch_survival   # noqa: E402

HOURS = (0.5, 1.0, 1.5, 2.0, 2.25, 3.0, 4.0, 4.49, 6.0, 9.0, 12.0)
np.save("survival_hours.npy", np.array(HOURS))
print("share | delay | T (h) | survival, this model | survival, study | open after cut-off | fork points in T")
res = {}
for alpha in (0.30, 1 / 3):
    for delta in (10, 15):
        ts = [int(round(h * 3600)) for h in HOURS]
        s = survival(alpha, delta, ts)
        o = open_after(alpha, delta, ts)
        res[(alpha, delta)] = (s, o)
        for hh, t, si, oi in zip(HOURS, ts, s, o):
            st = branch_survival(F, alpha, t, delta=delta)
            who = "30 %" if alpha == 0.30 else "a third"
            print(f"{who:8s} | {delta:2d} s | {hh:5.2f} | {si:9.3e} | {st:9.3e} | {oi:9.3e} | {t / clock(alpha, delta):6.0f}")
np.save("survival_table.npy", np.array([[res[(a, d)][0], res[(a, d)][1]] for a in (0.30, 1 / 3) for d in (10, 15)]))
