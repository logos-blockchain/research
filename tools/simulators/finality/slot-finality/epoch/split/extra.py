"""4K + 2K with beta 1/2 beside today and the old branch (3K + 3K, beta 3/4): the remaining figures of the RFC.

1. E[c15(S/D)], the displacement chance per block after 10 h at 15 s against 30 %, averaged over the stationary noise of D
   (exact rule, every win counted), with exposure.py of this folder and its curve of the study's wait bound.
2. Steady growth with new stake at epoch boundaries (mean path, exact rule): the daily growth at which the steady S/D reaches
   1.094 (K's limit at 15 s), and D's lag behind the stake in hours.
3. A 30 % coalition withholds one whole window (D at the fixed point before): S/D after it (mean path, exact rule).
Usage: <finality study's python> -B extra.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
from exposure import F, c15, q, stationary  # noqa: E402

CASES = (("today, window 108 h, epoch 180 h, beta 1", 388800, 648000, 1.0),
         ("3K + 3K, beta 3/4", 108000, 216000, 0.75),
         ("4K + 2K, beta 1", 144000, 216000, 1.0),
         ("4K + 2K, beta 1/2", 144000, 216000, 0.5))

print("1. E[c15(S/D)] over the stationary noise of D (exact rule): c15(1) = %.3e" % float(c15(1.0)))
for name, P, E, b in CASES:
    X, pi = stationary(P, b, 1.0)
    print(f"   {name}: {float(np.sum(pi * c15(1 / X))):.3e}")


def steady(E, b, g, epochs=600):
    d, k = 1.0, (1 + g) ** (E / 86400)
    for _ in range(epochs):
        d = d * ((1 - b) + b * float(q(1 / d)) / F) / k
    return 1 / d


print("2. steady growth: the daily growth at which the steady S/D reaches 1.094, and the lag of D in hours")
for name, P, E, b in CASES:
    lo, hi = 0.0, 0.2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if steady(E, b, mid) < 1.094 else (lo, mid)
    g = lo
    print(f"   {name}: {100 * g:.2f} % a day (lag {24 * math.log(steady(E, b, g)) / math.log1p(g):.0f} h); "
          f"at 1 % a day S/D {steady(E, b, 0.01):.3f}, lag {24 * math.log(steady(E, b, 0.01)) / math.log1p(0.01):.0f} h")

print("3. a 30 % coalition withholds one whole window: S/D after it")
for name, P, E, b in CASES:
    print(f"   {name}: {1 / ((1 - b) + b * float(q(0.7)) / F):.3f}")
