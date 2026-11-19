"""What a coalition of 30 % gains in blocks by choosing among nonces, by the length of the epoch
(REVIEW.md, statement 10.6).

The model is the one behind RFC-532's "What grinding gives besides" (published run
slot-finality/nonce/mean_gain.py of the finality study): at each cut-off the coalition holds n
nonces, keeps the one that gives it the most slots in the epoch the nonce governs, and its slots
under each nonce are an independent Binomial(N, a) draw, N the slots of the epoch.
  - The law of n is sampled by the study's `today_choices.sample`, imported read-only, with the
    arguments and the seed of mean_gain.py. It does not read N.
  - E[max of n Binomial(N, a)] is computed from the binomial law, as mean_gain.py does.
At N = 648,000 the script must return the published figures (+0.698 % and +0.821 % at a budget of
2^16 nonces). The other rows change N only.
Assumed, not derived here: that the law of n does not depend on the epoch's length.
The epochs are the schedules of out_09_epoch.txt, part C, 10-hour case, read from that file in hours.
Usage: python s11_gain.py > out_11_gain.txt     (the caches go to .cache beside this script; after s09)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for var in ("NUMBA_CACHE_DIR", "TMPDIR", "JOBLIB_TEMP_FOLDER"):
    os.environ.setdefault(var, os.path.join(HERE, ".cache"))
os.environ.setdefault("NUMBA_NUM_THREADS", "6")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "nonce"))

import numpy as np                                     # noqa: E402
from scipy import stats                                # noqa: E402
from model import rates                                # noqa: E402
from today_choices import log2_tail_table, sample      # noqa: E402

GRID = np.arange(0, 40.01, 0.25)                       # log2 of the number of nonces
YEAR = 365.25 * 86400


def schedules():
    """The epochs, in hours, of part C of the 10-hour case in out_09_epoch.txt."""
    out, case, part = [], None, None
    for line in open(os.path.join(HERE, "out_09_epoch.txt")):
        if line.startswith("==="):
            case = "10 h" if "10 h" in line else "other"
        elif re.match(r"^[A-C]\. ", line):
            part = line[0]
        m = re.match(r"^\s+(\d+\.\d+) = ", line)
        if m and case == "10 h" and part == "C":
            out.append(float(m.group(1)))
    return tuple(out)


EPOCHS_H = schedules()


def gain_curve(a, n_slots):
    mean = n_slots * a
    ks = np.arange(int(mean - 12 * mean ** 0.5), int(mean + 40 * mean ** 0.5) + 1)
    ks = ks[ks >= 0]
    lsf = np.log1p(-stats.binom.sf(ks, n_slots, a))
    out = []
    for b in GRID:
        cdf = np.exp(2.0 ** b * lsf)
        pm = np.diff(np.concatenate(([0.0], cdf)))
        out.append(float((pm * ks).sum()) / mean - 1)
    return np.array(out), mean


if __name__ == "__main__":
    table = log2_tail_table()
    alpha = 0.30
    a, h = rates(alpha)
    print("a coalition of 30 %; gain in its blocks, mean over all cut-offs, by the most nonces it evaluates at a cut-off")
    for delta in (10, 15):
        lg, lm, lm0, zs = sample(2_000_000, a, h, delta, 8000, 6000, 4242, table)
        n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
        any_ = float(np.mean(n0 >= 1 - 1e-9))
        print(f"\nevery honest block {delta} slots late; cut-offs with a choice: {100 * any_:.1f} %")
        print(" epoch (h) | slots | blocks by share | gain at 2^8, 2^16, 2^40 nonces: % (blocks an epoch) | at 2^16: blocks a year | sqrt rule 0.70 % or 0.82 % times sqrt(180 h / epoch)")
        base = None
        for hours in EPOCHS_H:
            n_slots = int(round(hours * 3600))
            g, mean = gain_curve(a, n_slots)
            cells, at16 = [], None
            for cap in (8, 16, 40):
                v = float(np.interp(np.minimum(n0, cap), GRID, g).mean())
                cells.append(f"{100 * v:+.3f} % ({v * mean:+.1f})")
                if cap == 16:
                    at16 = v
            if base is None:
                base = at16
            rule = 100 * base * (EPOCHS_H[0] / hours) ** 0.5
            print(f" {hours:9.2f} | {n_slots:6d} | {mean:7.0f} | " + ", ".join(cells)
                  + f" | {at16 * mean * YEAR / n_slots:7.0f} | {rule:.3f} %")
