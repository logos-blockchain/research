"""Epoch constructions beside 3K + 3K: 2K + 2K + 2K and 2.5K + K + 2K (CONSTRUCTIONS.md, 1 to 3).

The protocol reads three slots of an epoch: the snapshot at its first slot, the cut-off at which eta and D are
read (the start of the Lottery Constants Finalization phase), and the window of the inference, the first PERIOD
slots, which ends at the cut-off. A three-phase schedule L1 + L2 + L3 therefore runs as the two-phase schedule
(L1 + L2) + L3 with the same window; the split of the slots before the cut-off only decides which argument
covers the nonce (SCHEDULE.md, 3). Each construction is printed in both forms.

Part 1 prints, for each schedule, the columns of costs.py (the review's cost function, ../s09_epoch.py, costs),
then whether it keeps the rules of SCHEDULE.md 2: S and L (phase 1 and phase 3 at least G* = 46,910), J (phase 3
at least 2K - 1), the honest block (B: phase 2 at least w_B = 17,268 with the Buffer phase; with none, phase 1 at
least max(G*, w_B), SCHEDULE.md 3.6), the expected blocks an epoch N_b, and the proof-of-work rate
rho = EPOCH_POW_DISTRIBUTION_RATE_NUM / EPOCH_POW_DISTRIBUTION_RATE_DEN at which the pool pays out 1/4,320,000 of
itself per expected block, rho / N_b = 1/4,320,000 (today's 1/200 and 21,600), so the reward of a claim does not change.
Part 2 prints the gain of choosing among nonces with ../s11_gain.py, as gain.py, at 60, 55 and 50 hours.
Usage: python constructions.py > out_constructions.txt   (with the finality study's interpreter)
"""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.dont_write_bytecode = True
import numpy as np                       # noqa: E402
import s11_gain as g                     # noqa: E402
from s09_epoch import costs              # noqa: E402

K, PHI = 36000, 689
G_STAR, W_B = 46910, 17268               # the largest G* and w_B over the K row (REVIEW.md 5.9, 9.4)
NAME = "10 h (#533)"
SCHEDULES = (   # (L1, L2, L3, window, label)
    (194400, 194400, 259200, 388800, "today: 54 + 54 + 72 h"),
    (3 * K, 0, 3 * K, 3 * K, "no buffer: 3K, 3K (the specification)"),
    (2 * K, 2 * K, 2 * K, 4 * K, "2K, 2K, 2K"),
    (3 * K, K, 2 * K, 4 * K, "3K, K, 2K (the protocol of 2K, 2K, 2K)"),
    (4 * K, 0, 2 * K, 4 * K, "no buffer: 4K, 2K (the protocol of 2K, 2K, 2K)"),
    (5 * K // 2, K, 2 * K, 7 * K // 2, "2.5K, K, 2K"),
    (7 * K // 2, 0, 2 * K, 7 * K // 2, "no buffer: 3.5K, 2K (the protocol of 2.5K, K, 2K)"),
    (2 * K, K, 2 * K, 3 * K, "2K, K, 2K"),
)


def honest_block(l1, l2):
    """B with a Buffer phase; SCHEDULE.md 3.6 without one."""
    if l2:
        return f"phase 2 {l2} >= w_B {W_B}: {'yes' if l2 >= W_B else 'no'}"
    return f"phase 1 {l1} >= max(G*, w_B) {max(G_STAR, W_B)}: {'yes' if l1 >= max(G_STAR, W_B) else 'no'}"


def part_1():
    print("1. costs (columns of costs.py)")
    print("epoch = L1 + L2 + L3 (h) | window (h) | least share phase 1, phase 3 (15 s) | two nonces | cut-offs a year | new stake waits (h) | "
          "no correction for (h) | beta = 1: sd of D | P(miss floor at K) | floor at 1e-9 | P(> 1.094) an epoch | wins 30 % gives up to deflate | "
          "blocks an epoch")
    for l1, l2, l3, p, label in SCHEDULES:
        costs(NAME, K, PHI, l1, l2, l3, p, label)
    print()
    print("epoch (h) | cut-off (slots) | S: phase 1 >= G* | L: phase 3 >= G* | J: phase 3 >= 2K - 1 = 71,999 | honest block | "
          "expected blocks an epoch N_b | rho = NUM / DEN | rho / N_b")
    for l1, l2, l3, p, label in SCHEDULES:
        E = l1 + l2 + l3
        n_b = Fraction(E, 30)
        rho = n_b / 4_320_000
        print(f"{E / 3600:7.2f} | {l1 + l2:6d} | {'yes' if l1 >= G_STAR else 'no'} | {'yes' if l3 >= G_STAR else 'no'} | "
              f"{'yes' if l3 >= 2 * K - 1 else 'no'} ({l3 - (2 * K - 1):+d}) | {honest_block(l1, l2)} | {float(n_b):8.1f} | "
              f"{rho.numerator} / {rho.denominator} | {rho / n_b}   [{label}]")


def part_2(epochs_h=(60.0, 55.0, 50.0)):
    print()
    print("2. a coalition of 30 %; gain in its blocks by choosing among nonces, mean over all cut-offs (../s11_gain.py, as gain.py)")
    table = g.log2_tail_table()
    a, h = g.rates(0.30)
    for delta in (10, 15):
        lg, lm, lm0, zs = g.sample(2_000_000, a, h, delta, 8000, 6000, 4242, table)
        n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
        print(f"every honest block {delta} slots late")
        print(" epoch (h) | slots | blocks by share | gain at 2^8, 2^16, 2^40 nonces: % (blocks an epoch) | at 2^16: blocks a year")
        for hours in epochs_h:
            n_slots = int(round(hours * 3600))
            curve, mean = g.gain_curve(a, n_slots)
            cells, at16 = [], None
            for cap in (8, 16, 40):
                v = float(np.interp(np.minimum(n0, cap), g.GRID, curve).mean())
                cells.append(f"{100 * v:+.3f} % ({v * mean:+.1f})")
                if cap == 16:
                    at16 = v
            print(f" {hours:9.2f} | {n_slots:6d} | {mean:7.0f} | " + ", ".join(cells) + f" | {at16 * mean * g.YEAR / n_slots:7.0f}")


if __name__ == "__main__":
    part_1()
    part_2()
