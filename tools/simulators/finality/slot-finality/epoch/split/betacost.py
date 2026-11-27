"""What a lower beta costs: genesis (D starts at all distributed tokens), a real fall of stake, growth; and what it protects. 4K+2K unless said."""
import math
import os
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))      # slot-finality/epoch, for common.py
sys.dont_write_bytecode = True
import common
from exposure import E, F, K, c15, q
from scipy.stats import binom

PHI = 689
BS = (1.0, 15 / 16, 7 / 8, 3 / 4, 2 / 3, 1 / 2, 3 / 8)


def S(n, L, p, d):
    m = L - n * d
    return 1.0 if m < n else float(binom.cdf(n - 1, m, p))


print("genesis: D0 = all distributed tokens, a share s of them builds; S/D by epoch 0, 1, 2, ...")
for s in (0.1, 0.3, 0.5):
    print(f" s = {s}: G* at 15 s, one value final with 1e-9: {common.least_gap(K, PHI, s, 15)} slots; chance not final by 2K, 3K, 4K (15 s): "
          + ", ".join("%.1e" % S(PHI + 1, n * K, common.p_of(s), 15) for n in (2, 3, 4)))
    for b in BS:
        d, row = 1.0, []
        for _ in range(7):
            row.append(s / d)
            d = d * ((1 - b) + b * float(q(s / d)) / F)
        print(f"   beta {b:.4f}: " + " ".join(f"{r:.3f}" for r in row))
print("\na real fall of stake to m just after a cut-off (4K+2K: used from 80, 140, 200, 260 h): D/S, and finality of the floor at mean rates (h, 10 s)")
for m in (0.7, 0.5, 0.3):
    for b in BS:
        d, row = 1.0, []
        for _ in range(5):
            x = m / d
            p = common.p_of(x)
            rate = p / (1 + p * 10)
            row.append("%.2f (%.1f h)" % (d / m, max(10.0, PHI / rate / 3600)))
            d = d * ((1 - b) + b * float(q(m / d)) / F)
        print(f"   to {m}: beta {b:.4f}: " + " ".join(row))
print("\nsteady growth (new stake), S/D at 1, 2, 3, 5, 10 % a day")
for b in BS:
    row = []
    for g in (0.01, 0.02, 0.03, 0.05, 0.10):
        d, k = 1.0, (1 + g) ** (E / 86400)
        for _ in range(800):
            d = d * ((1 - b) + b * float(q(1 / d)) / F) / k
        row.append("%.3f" % (1 / d))
    print(f"   beta {b:.4f}: " + " ".join(row))
print("\nlost blocks: hours of a total halt inside one window that take S/D to 1.094 (15 s), 1.6 (12 s), 2.097 (10 s); the largest S/D after one empty window")
for name, P in (("2K+4K", 2 * K), ("3K+3K", 3 * K), ("4K+2K", 4 * K), ("today, window 108 h", 388800)):
    for b in ((1.0,) if "today" in name else BS):
        h = []
        for lim in (1.094, 1.6, 2.097):
            y = (1 - 1 / lim) / b
            h.append("%.1f h" % (y * P / 3600) if y <= 1 else "never")
        print(f"   {name} beta {b:.4f}: " + ", ".join(h) + f"; {1 / (1 - b):.2f}" if b < 1 else f"   {name} beta {b:.4f}: " + ", ".join(h) + "; unbounded")
