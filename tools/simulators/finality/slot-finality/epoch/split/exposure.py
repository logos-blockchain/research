"""The K row's own quantity, the displacement chance per block at 15 s against 30 %, by split and beta.

c(r): chance after 10 h at a lottery factor r = S/D (displace.py's output, the study's wait bound), interpolated in log.
1. Steady state: E[c(S/D)] over the stationary noise of D, with a share of the wins not counted.
2. A step of the stake by a factor m at a random time of the epoch: mean path of D (no noise), blocks made until D settles, and the mean
   number of blocks displaced, sum of c over the blocks made above the steady state.
3. A 30 % coalition withholds for one whole window, then returns for an epoch.
4. Steady growth: new stake joins at epoch boundaries.
"""
import math
import re
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

F, K, E = 1 / 30, 36000, 216000
LN = math.log1p(-F)
OUT = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "out_displace.txt")


def curve(delay, online):
    pts = []
    for line in open(OUT):
        m = re.match(r"share 0.30 delay (\d+) online ([\d.]+) factor ([\d.]+): chance after 10 h ([\d.e+-]+);", line)
        if m and int(m.group(1)) == delay and float(m.group(2)) == online:
            pts.append((float(m.group(3)), math.log(float(m.group(4)))))
    pts.sort()
    f = PchipInterpolator([p[0] for p in pts], [p[1] for p in pts], extrapolate=True)
    return lambda r: np.exp(f(r))


c15 = curve(15, 1.0)
c10 = curve(10, 1.0)


def q(r):
    return -np.expm1(LN * r)


def stationary(P, b, xs_, n=4001):
    from scipy.stats import binom
    cov = 1.0 if xs_ >= 1 else F / float(q(1 / xs_))
    lo, hi = math.log(0.80), math.log(1.25)
    g = np.linspace(lo, hi, n)
    d = g[1] - g[0]
    X = np.exp(g)
    T = np.zeros((n, n))
    for i, x in enumerate(X):
        p = cov * float(q(1 / x))
        m = P * p
        s = math.sqrt(m * (1 - p))
        ns = np.arange(max(0, int(m - 11 * s)), int(m + 11 * s) + 1)
        y = np.clip((np.log(x * ((1 - b) + b * ns / (P * F))) - lo) / d, 0, n - 1.000001)
        j = y.astype(int)
        w = y - j
        pm = binom.pmf(ns, P, p)
        np.add.at(T[i], j, pm * (1 - w))
        np.add.at(T[i], j + 1, pm * w)
    pi = np.zeros(n)
    pi[np.argmin(abs(X - xs_))] = 1
    for _ in range(200):
        pi = pi @ T
    return X, pi


SPLITS = [("2K+4K", 2 * K, (1.0, 2 / 3, 3 / 5)), ("3K+3K", 3 * K, (1.0, 7 / 8, 4 / 5, 3 / 4)), ("4K+2K", 4 * K, (1.0, 15 / 16, 7 / 8))]


def step_path(P, b, m, u, epochs=8):
    """Stake 1 -> m at slot u of epoch 0 (D = 1). Returns [(hours from the change, S/D)] segments until it settles."""
    segs = []
    d = 1.0
    # epoch 0: before u the stake is 1, after it m
    n_count = min(u, P) * float(q(1 / d)) + max(P - u, 0) * float(q(m / d))
    segs.append(((E - u) / 3600, m / d))
    d = d * ((1 - b) + b * n_count / (P * F))
    for _ in range(epochs):
        segs.append((E / 3600, m / d))
        d = d * ((1 - b) + b * float(q(m / d)) / F)
    return segs


def exposure(P, b, m, c):
    us = (np.arange(60) + 0.5) / 60 * E
    tot = tot_h = 0.0
    base = float(c(1.0))
    for u in us:
        for h, r in step_path(P, b, m, u):
            blocks = h * 3600 * float(q(r))
            tot += blocks * (float(c(r)) - base)
            tot_h += h * (r > 1.094)
    return tot / len(us), tot_h / len(us)


if __name__ == "__main__":
    print("c15(1) = %.3e, c15(1.094) = %.3e, c15(1.076) = %.3e, c15(1.05) = %.3e" % tuple(float(c15(v)) for v in (1, 1.094, 1.076, 1.05)))
    print("\n1. steady state at 15 s: mean displacement chance per block E[c15(S/D)]; D/S at the fixed point 1, 0.997, 0.99, 0.929")
    for name, P, bs in SPLITS:
        for b in bs:
            row = []
            for x in (1.0, 0.997, 0.99, 0.929):
                X, pi = stationary(P, b, x)
                row.append("%.3e" % float((pi * c15(1 / X)).sum()))
            X, pi = stationary(P, b, 0.997)
            print(f"   {name} beta {b:.4f}: {row}   P(S/D > 1.094) at 0.997: {float(pi[1 / X > 1.094].sum()):.1e}", flush=True)
    print("\n2. a step of the stake at a random time of the epoch, 15 s: blocks displaced in excess of the steady state (mean), hours with S/D > 1.094")
    for m in (1.1, 1.2, 1.5, 2.0):
        for name, P, bs in SPLITS:
            print(f"   x{m} {name}: " + "; ".join("beta %.4f: %.3e, %.1f h" % ((b,) + exposure(P, b, m, c15)) for b in bs))
    print("\n3. a 30 % coalition withholds one whole window (D at the fixed point before), then returns: S/D, c15, c10")
    for name, P, bs in SPLITS:
        row = []
        for b in bs:
            d = (1 - b) + b * float(q(0.7)) / F
            row.append(f"beta {b:.4f}: S/D {1 / d:.3f}, c15 {float(c15(1 / d)):.1e}, c10 {float(c10(1 / d)):.1e}")
        print(f"   {name} ({P / 3600:.0f} h, {P * float(q(0.3)):.0f} wins): " + "; ".join(row))
    print("   and after withholding exactly 729 wins (72,000 slots) in one window, whatever its length:")
    for name, P, bs in SPLITS:
        row = []
        for b in bs:
            y = 72000 / P
            d = (1 - b) + b * (y * float(q(0.7)) + (1 - y) * float(q(1.0))) / F
            row.append(f"beta {b:.4f}: S/D {1 / d:.3f}, c15 {float(c15(1 / d)):.1e}")
        print(f"   {name}: " + "; ".join(row))
    print("\n4. growth at 1, 2 and 3 % a day, new stake at epoch boundaries: steady S/D and c15")
    for name, P, bs in SPLITS:
        row = []
        for b in bs:
            vals = []
            for g in (0.01, 0.02, 0.03):
                d, k = 1.0, (1 + g) ** (E / 86400)
                for _ in range(400):
                    d = d * ((1 - b) + b * float(q(1 / d)) / F) / k
                vals.append("%.3f/%.1e" % (1 / d, float(c15(1 / d))))
            row.append(f"beta {b:.4f}: {vals}")
        print(f"   {name}: " + "; ".join(row))
