"""The retained share gamma = 3/4 beside beta = 1/2 at 4K + 2K: what it changes, under the rule as printed (f truncated to 0.033).

The next estimate is max(D((1 - beta) + beta N / (P f_hat)), gamma D) on the mean path, with N = P q(S/D).
1. Closed forms: S/D after one and after two windows without an occupied slot, from D right before, with and without gamma;
   the least gamma that keeps two such windows within 2.097, and the room for D below the total active stake that 3/4 leaves.
2. Launch with 30 % of the genesis D building: S/D after each window, with and without gamma.
3. A real fall of the stake to 0.5 and to 0.3 just after a cut-off: D over its fixed point at each correction, with and without gamma,
   and today's one-step correction for the fall to 0.3.
4. A coalition that withholds its blocks first keeps D on the honest stake (0.7); a window without blocks then follows: S/D.
The halts at any time of the epoch and the blocks displaced after them are in floor_half.py (exact rule).
Usage: <finality study's python> -B floor.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from exposure import F, q  # noqa: E402

FH, P, BETA, GAMMA = 0.033, 144000, 0.5, 0.75
FIX = math.log1p(-FH) / math.log1p(-F)          # S/D at the printed rule's fixed point


def step(d, s, gamma):
    """One correction: D over the total active stake d, stake that builds s (same unit)."""
    return max(d * ((1 - BETA) + BETA * float(q(s / d)) / FH), gamma * d)


print("1. closed forms, D right before")
for g in (0.0, GAMMA):
    one = 1 / max(1 - BETA, g)
    print(f"   gamma {g}: one window without blocks {one:.3f}, two {one * one:.3f}")
print(f"   least gamma with (1/gamma)^2 <= 2.097: {1 / math.sqrt(2.097):.4f}; room for D below the stake at 3/4: "
      f"one window {100 * (1 - (1 / GAMMA) / 2.097):.1f} %, two windows {100 * (1 - (1 / GAMMA) ** 2 / 2.097):.1f} %")

print("2. launch, 30 % of the genesis D building: S/D after each window")
for g in (0.0, GAMMA):
    d, row = 1.0, []
    for _ in range(6):
        row.append(0.3 / d)
        d = step(d, 0.3, g)
    print(f"   gamma {g}: " + " ".join(f"{x:.3f}" for x in row))

print("3. a real fall of the stake just after a cut-off: D over its fixed point at each correction (from D at rest)")
for m in (0.5, 0.3):
    for g in (0.0, GAMMA):
        d, row = 1 / FIX, []
        for _ in range(5):
            d = step(d, m, g)
            row.append(d / m * FIX)
        print(f"   to {m}, gamma {g}: " + " ".join(f"{x:.3f}" for x in row))
print("   today (beta 1, one correction 252 h after the change), to 0.3: "
      f"{(1 / FIX) * float(q(0.3 * FIX)) / FH / 0.3 * FIX:.4f}")

print("4. withholding first, then a window without blocks: S/D")
for g in (0.0, GAMMA):
    print(f"   gamma {g}: {(1 / 0.7) / max(1 - BETA, g):.3f}")
