"""What a halt of block production, or a share of the stake offline for a while, does to D, by split and beta (mean path, exact rule).

During a halt no slot is occupied (or only those of the stake still online). Afterwards all stake is back. S = 1 throughout.
For a start slot u of the halt (uniform in the epoch) and a length h, the counts of the windows it touches give D of the following epochs.
Reported over 120 start times: the largest S/D an epoch gets, its mean over start times and its worst case, the hours with S/D above 1.094 (15 s)
and above 2.097 (10 s), and the sum over the blocks made of the displacement chance at 15 s and at 10 s (log-extrapolated past the curves' ends).
"""
import math
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
sys.dont_write_bytecode = True
import numpy as np

from exposure import E, F, K, c10, c15, q

C15 = lambda r: min(1.0, float(c15(r)))
C10 = lambda r: min(1.0, float(c10(r)))


def path(P, b, u, h, online, epochs=10, cap=None):
    """D over the epochs; the halt covers [u, u + h) in slots from the start of epoch 0; `online` is the share of stake still building then."""
    d = 1.0
    segs = []                                  # (hours, S/D) of full-stake time after the halt, by epoch
    for e in range(epochs):
        a, z = e * E, e * E + P                # window
        lo, hi = max(a, u), min(z, u + h)
        halted = max(0, hi - lo)
        n = (P - halted) * float(q(1 / d)) + halted * float(q(online / d))
        lo2, hi2 = max(a, u), min(a + E, u + h)
        run = E - max(0, hi2 - lo2)            # slots of the epoch with the full stake
        before = max(0, min(a + E, u) - a) if u > a else 0
        after = run - before
        if after > 0 and (e * E + E) > u + h:
            segs.append((after / 3600, 1 / d))
        nd = d * ((1 - b) + b * n / (P * F))
        if cap is not None:
            nd = max(nd, cap * d)
        d = max(nd, 1e-9)
    return segs


def stats(P, b, hours, online=0.0, cap=None, starts=120):
    worst, peaks, t15, t10, s15, s10 = 0.0, [], 0.0, 0.0, 0.0, 0.0
    for i in range(starts):
        u = (i + 0.5) / starts * E
        segs = path(P, b, u, hours * 3600, online, cap=cap)
        pk = max(r for _, r in segs)
        peaks.append(pk)
        worst = max(worst, pk)
        for h, r in segs:
            blocks = h * 3600 * float(q(min(r, 200)))
            t15 += h * (r > 1.094)
            t10 += h * (r > 2.097)
            s15 += blocks * max(0.0, C15(min(r, 3.0)) - 2.5e-10) if r > 1.0 else 0.0
            s10 += blocks * max(0.0, C10(min(r, 4.0)) - 8.3e-16) if r > 1.0 else 0.0
    n = starts
    return worst, float(np.mean(peaks)), t15 / n, t10 / n, s15 / n, s10 / n


if __name__ == "__main__":
    confs = [("2K+4K", 2 * K, (1.0, 3 / 5)), ("3K+3K", 3 * K, (1.0, 4 / 5, 3 / 4)), ("4K+2K", 4 * K, (1.0, 15 / 16, 7 / 8, 3 / 4, 2 / 3, 1 / 2))]
    for online in (0.0, 0.5):
        for hours in (6, 12, 24, 36, 48):
            print(f"\n{'everyone halts' if online == 0 else 'half of the stake is offline'} for {hours} h, at a uniform time: worst S/D, mean peak S/D, "
                  f"h above 1.094, h above 2.097, displaced (15 s), displaced (10 s)")
            for name, P, bs in confs:
                for b in bs:
                    w, m, t15, t10, s15, s10 = stats(P, b, hours, online)
                    print(f"   {name} beta {b:.4f}: {w:10.2f} | {m:8.2f} | {t15:6.1f} | {t10:6.1f} | {s15:.1e} | {s10:.1e}")
    print("\ntoday's schedule (window 108 h of 180 h, beta 1), everyone halts for 12, 24, 36, 48 h: worst S/D")
    for hours in (12, 24, 36, 48, 108):
        P, b = 388800, 1.0
        n = max(0, P - hours * 3600) / P
        print(f"   {hours} h: {1 / max(n, 1e-9):.2f}")
