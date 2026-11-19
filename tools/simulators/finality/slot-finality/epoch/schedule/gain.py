"""What a coalition of 30 % gains in blocks by choosing among nonces, at the epochs of SCHEDULE.md (5).

The computation of ../s11_gain.py (REVIEW.md 10.6), imported, at other epoch lengths: the law of the
number of nonces at a cut-off is the finality study's `today_choices.sample`, with the arguments and the
seed of s11, and does not read the epoch's length (Assumed, as in REVIEW.md 10.6).
Usage: python gain.py > out_gain.txt   (with the finality study's interpreter)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.dont_write_bytecode = True
import numpy as np                       # noqa: E402
import s11_gain as g                     # noqa: E402

EPOCHS_H = (180.0, 100.0, 40.0, 35.0, 30.0)

if __name__ == "__main__":
    table = g.log2_tail_table()
    a, h = g.rates(0.30)
    print("a coalition of 30 %; gain in its blocks, mean over all cut-offs, by the most nonces it evaluates at a cut-off")
    for delta in (10, 15):
        lg, lm, lm0, zs = g.sample(2_000_000, a, h, delta, 8000, 6000, 4242, table)
        n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
        print(f"\nevery honest block {delta} slots late")
        print(" epoch (h) | slots | blocks by share | gain at 2^8, 2^16, 2^40 nonces: % (blocks an epoch) | at 2^16: blocks a year")
        for hours in EPOCHS_H:
            n_slots = int(round(hours * 3600))
            curve, mean = g.gain_curve(a, n_slots)
            cells, at16 = [], None
            for cap in (8, 16, 40):
                v = float(np.interp(np.minimum(n0, cap), g.GRID, curve).mean())
                cells.append(f"{100 * v:+.3f} % ({v * mean:+.1f})")
                if cap == 16:
                    at16 = v
            print(f" {hours:9.2f} | {n_slots:6d} | {mean:7.0f} | " + ", ".join(cells) + f" | {at16 * mean * g.YEAR / n_slots:7.0f}")
