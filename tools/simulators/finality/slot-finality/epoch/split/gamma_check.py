"""Checks of the independent review of gamma = 3/4 (beta = 1/2, 4K + 2K), mean path.

1. The longest halt whose worst start keeps S/D within 2.097: exact rule from D right, and printed rule from rest.
2. After a 48-hour halt: the blocks a 30 % coalition is expected to displace at 15 s over all epochs after the halt, at the worst
   start and averaged over starts, with and without gamma (exact rule from D right; c15 from the study's wait bound via exposure.py).
3. Withholding by a 30 % coalition at beta 1/2 over four windows, printed rule from rest, to four decimals; and beta 1 with gamma.
Usage: <finality study's python> -B gamma_check.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from exposure import F, c15, q  # noqa: E402

K = 36000
P, E = 4 * K, 216000
FH = 0.033
FIX = math.log1p(-FH) / math.log1p(-F)


def run(u, h, b, g, fh, d0, epochs=12):
    """Halt of h slots from slot u (epoch 0 starts at 0). Returns [(slots after the halt in the epoch, S/D during it)], peak."""
    d, segs = d0, []
    for e in range(epochs):
        a, z = e * E, e * E + P
        lost = max(0, min(z, u + h) - max(a, u))
        n = (P - lost) * float(q(1 / d))
        end = a + E
        if end > u + h:
            segs.append((end - max(a, u + h), 1 / d))
        d = max(d * ((1 - b) + b * n / (P * fh)), g * d)
    return segs


def worst(h, b, g, fh, d0, starts=2000):
    return max(max(r for _, r in run((i + 0.5) / starts * E, h, b, g, fh, d0)) for i in range(starts))


print("1. longest halt with the worst start within 2.097 (beta 1/2, gamma 3/4)")
for label, fh, d0 in (("exact rule, D right", F, 1.0), ("printed rule, from rest", FH, 1 / FIX)):
    lo, hi = 100 * 3600, 130 * 3600
    while hi - lo > 60:
        mid = (lo + hi) // 2
        if worst(mid, 0.5, 0.75, fh, d0) <= 2.097:
            lo = mid
        else:
            hi = mid
    print(f"   {label}: {lo / 3600:.2f} h (worst at 125 h: {worst(125 * 3600, 0.5, 0.75, fh, d0):.3f};"
          f" at 160 h: {worst(160 * 3600, 0.5, 0.75, fh, d0):.3f})")

print("2. after a 48-hour halt: blocks displaced at 15 s over all later epochs, worst start and mean over starts (exact rule)")
base = float(c15(1.0))
for label, g in (("beta 1/2 alone", 0.0), ("beta 1/2, gamma 3/4", 0.75)):
    sums = []
    for i in range(480):
        tot = 0.0
        for slots, r in run((i + 0.5) / 480 * E, 48 * 3600, 0.5, g, F, 1.0):
            if r > 1:
                tot += slots * float(q(min(r, 100))) * max(0.0, min(1.0, float(c15(min(r, 3.0)))) - base)
        sums.append(tot)
    print(f"   {label}: worst start {max(sums):.3g}, mean over starts {sum(sums) / len(sums):.3g}")

print("3. withholding by 30 %, printed rule from rest: S/D after each of four windows")
for label, b, g in (("beta 1/2, gamma 3/4", 0.5, 0.75), ("beta 1, gamma 3/4", 1.0, 0.75)):
    d, row = 1 / FIX, []
    for _ in range(4):
        d = max(d * ((1 - b) + b * float(q(0.7 / d)) / FH), g * d)
        row.append(1 / d)
    print(f"   {label}: " + " ".join(f"{x:.4f}" for x in row))
print(f"   withholding at rest, then two windows without blocks: {(1 / (0.7 / FIX)) / 0.75 ** 2:.3f} printed, {(1 / 0.7) / 0.75 ** 2:.3f} exact")

print("4. finality at mean rates after the stake halves just after a cut-off (printed rule from rest, blocks 10 s late, floor 689)")
d0 = (1 / FIX) / 0.5                              # D over the new stake until the first correction
d1 = max(d0 * (0.5 + 0.5 * float(q(1 / d0)) / FH), 0.75 * d0)
for label, x in (("before the first correction", 1 / d0), ("after it, beta 1/2 and gamma 3/4", 1 / d1)):
    p = float(q(x))
    print(f"   {label}: S/D {x:.4f}, {689 / (p / (1 + 10 * p)) / 3600:.1f} h")
