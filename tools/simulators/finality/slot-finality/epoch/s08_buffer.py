"""The buffer: how long a span must be so that the chain keeps at least one honest block of it
(REVIEW.md, section 9).

REVIEW.md proves the reduction: if the final chain holds no honest block with a slot in a span of w
slots, then a branch of the coalition's own blocks that leaves the chain at an honest block at or
before the span's start is still held by an honest node after the span's end. Summed over the slots
that can hold that honest block,
    P(no honest block of the span stays)  <=  h * sum_{t >= 0} survival(w + t),
with h the chance that a slot holds an honest block and survival(T) the chance that such a branch
can still be published T slots after its fork point.

survival(T) is NOT derived here. It is the finality study's `branch_survival` (package finality_sim,
module formation, lines 390-405), under the study's worst-case delay model, read-only. The script
evaluates it on a grid, interpolates its logarithm, and reports the least w that keeps the bound at
most 1e-9. The states are those of the K row of the specification, with a coalition of 30 % of the
total active stake:
  - no disturbance: every honest block 10 slots late;
  - every honest block T_M = 15 slots late;
  - a tenth of the honest stake offline, the inference corrected: the coalition holds 0.3 / 0.93 of
    the stake that is still active;
  - a deflated inference: the inferred stake is the honest stake only, so the lottery's coefficient
    is 1 - (1 - f)^(1 / 0.7).
The coefficient is that of the stake that is online: a share s of it wins a slot with chance
1 - (1 - coefficient)^s. With a tenth of the honest stake offline and a deflated inference, the stake
online is 0.93 of the total and the inferred stake 0.63, so the coefficient is 1 - (1 - f)^(0.93 / 0.63)
and the honest stake online wins with chance f.
A coalition of a third is added for comparison with the earlier study. The last two states read a
tenth of the honest stake offline before the inference corrects: the inferred stake is still the
total, so the coefficient of the stake online is 1 - (1 - f)^0.93.
Usage: python s08_buffer.py > out_08_buffer.txt     (the caches go to .cache beside this script)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for var in ("NUMBA_CACHE_DIR", "TMPDIR", "JOBLIB_TEMP_FOLDER"):
    os.environ.setdefault(var, os.path.join(HERE, ".cache"))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

import numpy as np                                   # noqa: E402
from finality_sim.formation import branch_survival   # noqa: E402

from common import EPS, F, H                         # noqa: E402

STEP = 900                 # grid step, slots
T_MAX = 14 * H             # grid end
F_DEFLATED = -math.expm1(math.log1p(-F) / 0.7)

F_DEFLATED_OFF = -math.expm1(math.log1p(-F) * 0.93 / 0.63)   # stake online 0.93, inferred stake 0.63
F_OFF_UNCORRECTED = -math.expm1(math.log1p(-F) * 0.93)       # stake online 0.93, inferred stake 1

STATES = (
    ("30 %, no disturbance, 10 s", 0.30, 10, F),
    ("30 %, every honest block 15 s late", 0.30, 15, F),
    ("30 %, a tenth of the honest stake offline, 10 s", 0.30 / 0.93, 10, F),
    ("30 %, deflated inference, 10 s", 0.30, 10, F_DEFLATED),
    ("30 %, 15 s and a tenth of the honest stake offline", 0.30 / 0.93, 15, F),
    ("30 %, 15 s and a deflated inference", 0.30, 15, F_DEFLATED),
    ("30 %, a tenth of the honest stake offline and a deflated inference, 10 s", 0.30 / 0.93, 10, F_DEFLATED_OFF),
    ("a third, 10 s", 1 / 3, 10, F),
    ("a third, 15 s", 1 / 3, 15, F),
    ("30 %, a tenth of the honest stake offline before the inference corrects, 10 s", 0.30 / 0.93, 10, F_OFF_UNCORRECTED),
    ("30 %, 15 s and a tenth of the honest stake offline before the inference corrects", 0.30 / 0.93, 15, F_OFF_UNCORRECTED),
)

def least_w(f, a, delta, step):
    """w_B computed as below, on a grid of `step` slots; the tail's decay is read over the last hour."""
    grid = np.arange(step, T_MAX + 1, step)
    logs = np.log(np.array([branch_survival(f, a, int(t), delta=delta) for t in grid]))
    slots = np.arange(step, T_MAX + 1)
    every = np.exp(np.interp(slots, grid, logs))
    tail = np.cumsum(every[::-1])[::-1]
    k = H // step
    tail = tail + every[-1] / (-math.expm1((logs[-1] - logs[-1 - k]) / (k * step)))
    h = -math.expm1((1 - a) * math.log1p(-f))
    return int(slots[np.argmax(h * tail <= EPS)])


if __name__ == "__main__":
    found = {}
    grid = np.arange(STEP, T_MAX + 1, STEP)
    print("survival(T): the study's chance that a branch from an honest block can still be published T slots later")
    print("bound(w) = h * sum_{t >= 0} survival(w + t); w_B = the least w with bound(w) <= 1e-9")
    print(f"necessary in every case: an honest win in the span, (1 - f)^((1 - a) w) <= 1e-9, w >= {math.log(1 / EPS) / (-math.log1p(-F)) / 0.7:.1f} slots at a = 0.3")
    for name, a, delta, f in STATES:
        h = -math.expm1((1 - a) * math.log1p(-f))
        surv = np.array([branch_survival(f, a, int(t), delta=delta) for t in grid])
        logs = np.log(surv)
        slots = np.arange(STEP, T_MAX + 1)
        every = np.exp(np.interp(slots, grid, logs))          # survival at every slot, log-linear
        tail = np.cumsum(every[::-1])[::-1]                   # sum_{t >= 0} survival(w + t), to the grid end
        decay = (logs[-1] - logs[-5]) / (4 * STEP)            # per slot, at the grid end
        tail = tail + every[-1] / (-math.expm1(decay))        # the rest, a geometric series
        bound = h * tail
        w_b = int(slots[np.argmax(bound <= EPS)])
        print(f"\n{name}: coalition's share of the active stake {a:.4f}, lottery coefficient {f:.5f}, h = {h:.5f}")
        for hours in (1, 2, 3, 4, 5, 6, 8, 10):
            i = hours * H - STEP
            print(f"  w = {hours:2d} h: survival {every[i]:.3e}, bound {bound[i]:.3e}, bound / survival {bound[i] / every[i]:5.1f}")
        print(f"  w_B = {w_b} slots = {w_b / H:.2f} h; survival there {every[w_b - STEP]:.3e}")
        found[name] = w_b
    print(f"\nthe same w_B on a grid of 150 slots in place of {STEP}")
    for name, a, delta, f in STATES:
        fine = least_w(f, a, delta, 150)
        print(f"  {name}: {fine} slots ({fine - found[name]:+d})")
