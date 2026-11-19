"""What each candidate schedule costs, at K = 36,000 slots and phi = 689 (SCHEDULE.md, 2 and 5).

Each row is computed with the review's cost function (../s09_epoch.py, costs): the least share of the
inferred stake that must build for phase 1 and phase 3 to be final in time at 15 s, the targets that
meet two nonces, cut-offs a year, new stake's wait, the longest time with no correction, and, for a
learning rate of 1 and one step from the fixed point, the noise of D, the chance of missing the floor,
the floor at 1e-9 and the chance that the noise passes 1.094 (for another learning rate see chain.py).
Each row also gives whether phase 3 meets J (at least 2K - 1 slots, GENESIS 7.1), the expected blocks
an epoch, the proof-of-work rate rho that keeps EPOCH_POW_DISTRIBUTION_RATE_DEN * EXPECTED_BLOCKS_PER_EPOCH
= 4,320,000 (today's 200 * 21,600, so the reward of a claim does not change), and the gain of choosing
among nonces by the square-root rule of REVIEW.md 10.6 (0.70 % times sqrt(180 h / E), at 10 s).
Usage: python costs.py > out_costs.txt   (run from any folder, with the finality study's interpreter)
"""
import math
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.dont_write_bytecode = True
from s09_epoch import costs              # noqa: E402

K, PHI = 36000, 689
G_STAR, W_B = 46910, 17268               # the largest G* and w_B over the K row (REVIEW.md 5.9, 9.4)
NAME = "10 h (#533)"
SCHEDULES = (   # (L1, L2, L3, window, label)
    (194400, 194400, 259200, 388800, "today: 54 + 54 + 72 h"),
    (3 * K, 3 * K, 4 * K, 6 * K, "3K, 3K, 4K"),
    (3 * K, 3 * K, 3 * K, 6 * K, "3K, 3K, 3K"),
    (3 * K, 0, 4 * K, 3 * K, "no buffer: 3K, 4K"),
    (3 * K, 0, 3 * K, 3 * K, "no buffer: 3K, 3K (the specification)"),
    (7 * K // 2, 0, 3 * K // 2, 7 * K // 2, "no buffer: 3.5K, 1.5K"),
    (2 * K, 0, 2 * K, 2 * K, "no buffer: 2K, 2K"),
    (3 * K // 2, 0, 2 * K, 3 * K // 2, "no buffer: 1.5K, 2K"),
    (3 * K // 2, 0, 3 * K // 2, 3 * K // 2, "no buffer: 1.5K, 1.5K"),
    (K, K, K, 2 * K, "K, K, K"),
    (G_STAR, W_B, 2 * K - 1, G_STAR + W_B, "buffer kept, the least that suffices with J: G*, w_B, 2K - 1"),
)

print("epoch = L1 + L2 + L3 (h) | window (h) | least share phase 1, phase 3 (15 s) | two nonces | cut-offs a year | new stake waits (h) | "
      "no correction for (h) | beta = 1: sd of D | P(miss floor at K) | floor at 1e-9 | P(> 1.094) an epoch | wins 30 % gives up to deflate | "
      "blocks an epoch")
for l1, l2, l3, p, label in SCHEDULES:
    costs(NAME, K, PHI, l1, l2, l3, p, label)
print()
print("epoch (h) | phase 3 meets J (>= 2K - 1 = 71,999 slots) | expected blocks an epoch | rho | gain of choosing among nonces, 10 s")
for l1, l2, l3, p, label in SCHEDULES:
    E = l1 + l2 + l3
    rho = Fraction(E, 30) / 4_320_000
    print(f"{E / 3600:7.2f} | {'yes' if l3 >= 2 * K - 1 else 'no'} ({l3}) | {E / 30:9.2f} | {rho} | "
          f"{0.70 * math.sqrt(180 * 3600 / E):.2f} %   [{label}]")
