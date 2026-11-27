"""4K + 2K: beta 1/2 alone, beta 1/2 with a floor D' >= 3/4 D, and beta 1 with that floor (mean path, exact rule, review's rules.py).

Per rule: S/D after an empty window; worst S/D after a halt of 6, 12, 24, 36, 48 h and the blocks displaced after it at 15 s and 10 s;
S/D after a 30 % coalition withholds one window, and over four windows of withholding; S/D after the stake doubles (each correction);
D/S after it halves; launch at 30 % building; the daily growth at which the steady S/D reaches 1.094.
Usage: <finality study's python> -B floor_half.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from exposure import F, q  # noqa: E402
from rules import K, halt_stats, rise, upd  # noqa: E402

P, E = 4 * K, 216000
RULES = (("beta 1/2", 0.5, 0.0), ("beta 1/2, floor 3/4", 0.5, 0.75), ("beta 1, floor 3/4", 1.0, 0.75))


def growth(b, fl):
    def steady(g):
        d, k = 1.0, (1 + g) ** (E / 86400)
        for _ in range(600):
            d = upd(d, P * float(q(1 / d)), P, b, fl) / k
        return 1 / d
    lo, hi = 0.0, 0.2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if steady(mid) < 1.094 else (lo, mid)
    return lo


for name, b, fl in RULES:
    empty = 1 / max(1 - b, fl)
    hs = [halt_stats(P, b, fl, h) for h in (6, 12, 24, 36, 48)]
    d, wh = 1.0, []
    for _ in range(4):
        d = upd(d, P * float(q(0.7 / d)), P, b, fl)
        wh.append(1 / d)
    up = rise(P, b, fl, 2.0)
    dn = [1 / v for v in rise(P, b, fl, 0.5)]
    gen = rise(P, b, fl, 0.3, 7)
    print(f"{name}: empty window S/D {empty:.2f}")
    print("   worst S/D after a halt of 6, 12, 24, 36, 48 h: " + " ".join("%.2f" % x[0] for x in hs))
    print("   blocks displaced after it, 15 s: " + " ".join("%.0e" % x[1] for x in hs) + " | 10 s: " + " ".join("%.0e" % x[2] for x in hs))
    print("   a 30 % coalition withholds 1 to 4 windows, S/D: " + " ".join("%.3f" % v for v in wh))
    print("   doubling, S/D after each correction: " + " ".join("%.3f" % v for v in up[1:])
          + " | halving, D/S: " + " ".join("%.2f" % v for v in dn[1:]))
    print("   launch at 30 %: " + " ".join("%.2f" % v for v in gen) + f" | daily growth held at 15 s: {100 * growth(b, fl):.2f} %")
