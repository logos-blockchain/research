"""The RFC's inference figures under the rule the specification prints (f truncated to 0.033), with corrections of the check.

1. E[c15(S/D)] over the stationary noise of D under the printed rule (exposure.py's chain with f_hat in the update).
2. Steady growth under the printed rule: the daily growth at which the steady S/D reaches 1.094, and D's lag.
3. One window withheld by a 30 % coalition, from D at rest: S/D after it.
4. The income a 30 % coalition gives up to keep D on the honest stake by withholding in every window: it builds only in the last
   phase, where its stake wins q(0.3 / 0.7) a slot in place of q(0.3) (win rate; blocks are not lost to forks in this count).
5. The wins a 30 % coalition withholds in each window of a lasting deflation at 4K + 2K, beta 1/2, from D at rest (printed rule).
6. Launch at 30 % of D building, printed rule: S/D after each window, beta 1/2 and 1.
7. The mean path after a step of the stake just after a cut-off (printed rule): D over its fixed point at each correction.
8. The room for D below the total active stake at beta 1/2 (4K window): the stationary chance that S/D exceeds 2.097/2, by
   ../schedule/chain.py, printed rule and exact rule.
Usage: <finality study's python> -B printed.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "schedule"))
sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
from scipy.stats import binom  # noqa: E402
from exposure import F, c15, q  # noqa: E402

FH = 0.033
CASES = (("today", 388800, 648000, 1.0), ("3K + 3K, 3/4", 108000, 216000, 0.75),
         ("4K + 2K, 1", 144000, 216000, 1.0), ("4K + 2K, 1/2", 144000, 216000, 0.5))
FIX = math.log1p(-FH) / math.log1p(-F)          # S/D at the printed rule's fixed point


def stationary(P, b, fh, n=4001):
    lo, hi = math.log(0.80), math.log(1.25)
    g = np.linspace(lo, hi, n)
    d = g[1] - g[0]
    X = np.exp(g)
    T = np.zeros((n, n))
    for i, x in enumerate(X):
        p = float(q(1 / x))
        m = P * p
        s = math.sqrt(m * (1 - p))
        ns = np.arange(max(0, int(m - 11 * s)), int(m + 11 * s) + 1)
        y = np.clip((np.log(x * ((1 - b) + b * ns / (P * fh))) - lo) / d, 0, n - 1.000001)
        j = y.astype(int)
        w = y - j
        pm = binom.pmf(ns, P, p)
        np.add.at(T[i], j, pm * (1 - w))
        np.add.at(T[i], j + 1, pm * w)
    pi = np.zeros(n)
    pi[np.argmin(abs(X - 1 / FIX if fh == FH else 1.0))] = 1
    for _ in range(200):
        pi = pi @ T
    return X, pi


print(f"fixed point of the printed rule: D/S = {1 / FIX:.5f}")
print("1. E[c15(S/D)] over the noise of D, printed rule | exact rule")
for name, P, E, b in CASES:
    out = []
    for fh in (FH, F):
        X, pi = stationary(P, b, fh)
        out.append(float(np.sum(pi * c15(1 / X))))
    print(f"   {name}: {out[0]:.3e} | {out[1]:.3e}")


def steady(E, b, g, fh, epochs=600):
    d, k = 1.0, (1 + g) ** (E / 86400)
    for _ in range(epochs):
        d = d * ((1 - b) + b * float(q(1 / d)) / fh) / k
    return 1 / d


print("2. daily growth at which the steady S/D reaches 1.094 (lag of D in hours), printed rule | exact rule")
for name, P, E, b in CASES:
    row = []
    for fh in (FH, F):
        lo, hi = 0.0, 0.2
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if steady(E, b, mid, fh) < 1.094 else (lo, mid)
        row.append(f"{100 * lo:.2f} % ({24 * math.log(steady(E, b, 0.01, fh) * (1 / FIX if fh == FH else 1)) / math.log1p(0.01):.0f} h)")
    print(f"   {name}: " + " | ".join(row))

print("3. a 30 % coalition withholds one window, D at rest before: S/D after it, printed rule | exact rule")
for name, P, E, b in CASES:
    pr = 1 / ((1 / FIX) * ((1 - b) + b * float(q(0.7 * FIX)) / FH))
    ex = 1 / ((1 - b) + b * float(q(0.7)) / F)
    print(f"   {name}: {pr:.3f} | {ex:.3f}")

print("4. income a 30 % coalition gives up to keep D on the honest stake (win rate, D exactly the honest stake)")
ratio = float(q(0.3 / 0.7)) / float(q(0.3))
print(f"   win rate in the last phase over the normal rate: {ratio:.4f}")
for name, l3 in (("2K + 4K", 4), ("3K + 3K", 3), ("4K + 2K", 2)):
    print(f"   {name}: {100 * (1 - ratio * l3 / 6):.1f} %")

print("5. wins withheld in each window of a lasting deflation at 4K + 2K, beta 1/2, printed rule, from D at rest")
P, b = 144000, 0.5
d = 1 / FIX                                      # D over the total active stake
wins = []
for _ in range(6):
    wins.append(P * float(q(0.3 / d)))
    n = P * float(q(0.7 / d))
    d = d * ((1 - b) + b * n / (P * FH))
print("   " + ", ".join(f"{x:.0f}" for x in wins) + f"; today's window (388,800) from rest: {388800 * float(q(0.3 * FIX)):.0f}")

print("6. launch, 30 % of D building, printed rule: S/D after each window")
for b in (0.5, 1.0):
    d, row = 1.0, []
    for _ in range(6):
        row.append(0.3 / d)
        d = d * ((1 - b) + b * float(q(0.3 / d)) / FH)
    print(f"   beta {b}: " + " ".join(f"{x:.3f}" for x in row))

print("7. mean path after a step just after a cut-off, printed rule: D over its fixed point at each correction")
for m in (0.5, 0.9, 2.0):
    for name, b in (("today", 1.0), ("4K + 2K, 1/2", 0.5)):
        d = (1 / FIX) / m                         # D over the new stake
        row = []
        for _ in range(4):
            d = d * ((1 - b) + b * float(q(1 / d)) / FH)
            row.append(d * FIX)
        print(f"   stake x{m}, {name}: " + " ".join(f"{x:.4f}" for x in row))

import chain  # noqa: E402
print("8. stationary chance that S/D exceeds 2.097/2 = 1.0485 at a window of 4K, beta 1/2")
for name, fh in chain.RULES:
    xs, pi = chain.stationary(144000, 0.5, fh)
    print(f"   {name}: {pi[(1 / xs) > 2.097 / 2].sum():.2e}")
