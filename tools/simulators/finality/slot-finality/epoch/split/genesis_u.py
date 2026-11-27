"""Genesis under 4K+2K with 30 % of the distributed tokens building (S/D = 0.3): the chance that a fork from before the cut-off of epoch 0 is
still alive when epoch 1 starts (wait 72,000 slots) and when the cut-off becomes final, for a coalition of 30 % of the building stake.
Also the price of holding D deflated (income a 30 % coalition gives up), by split."""
import math
import os
import sys

W = os.path.dirname(os.path.abspath(__file__))
os.environ["NUMBA_CACHE_DIR"] = os.path.join(W, ".cache", "numba")
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(W, "..", "..", "..", "src"))       # tools/simulators/finality/src
from finality_sim.waitbound import wait_curve

F = 1 / 30
for d in (10, 15):
    c = wait_curve(110000, 0.30, d, F, floor=0.0, scale=0.3)
    print(f"S/D 0.3, {d} s late: chance after 72,000 slots {c[71999]:.2e}; 95,194 slots {c[95193]:.2e}; 108,000 slots {c[107999]:.2e}")


def q(x):
    return -math.expm1(x * math.log1p(-F))


def rate(x, d):
    return q(x) / (1 + q(x) * d)


print("income a 30 % coalition gives up by withholding in every window and building in every last phase (reward per block):")
for d in (5.5, 10, 15):
    row = []
    for name, l3 in (("2K+4K", 4), ("3K+3K", 3), ("4K+2K", 2)):
        row.append(f"{name} {100 * (1 - rate(1 / 0.7, d) / rate(1.0, d) * l3 / 6):.0f} %")
    print(f"   blocks {d} s late: " + ", ".join(row))
