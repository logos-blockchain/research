"""4K+2K: beta against a floor on D's fall, by what each protects and costs (mean path, exact rule). Floors: D' >= phi * D."""
import math
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
sys.dont_write_bytecode = True
import numpy as np
from exposure import E, F, K, c10, c15, q

C15 = lambda r: min(1.0, float(c15(min(r, 3.0))))
C10 = lambda r: min(1.0, float(c10(min(r, 4.0))))


def upd(d, n, P, b, fl):
    return max(d * ((1 - b) + b * n / (P * F)), fl * d, 1e-9)


def halt(P, b, fl, u, h, online, epochs=12):
    d, segs = 1.0, []
    for e in range(epochs):
        a, z = e * E, e * E + P
        lost = max(0, min(z, u + h) - max(a, u))
        n = (P - lost) * float(q(1 / d)) + lost * float(q(online / d))
        end = a + E
        if end > u + h:
            after = end - max(a, u + h)
            segs.append((after / 3600, 1 / d))
        d = upd(d, n, P, b, fl)
    return segs


def halt_stats(P, b, fl, hours, online=0.0, starts=240):
    w, s15, s10 = 0.0, 0.0, 0.0
    for i in range(starts):
        for h, r in halt(P, b, fl, (i + 0.5) / starts * E, hours * 3600, online):
            w = max(w, r)
            if r > 1:
                blocks = h * 3600 * float(q(min(r, 100)))
                s15 += blocks * max(0.0, C15(r) - C15(1.0))
                s10 += blocks * max(0.0, C10(r) - C10(1.0))
    return w, s15 / starts, s10 / starts


def rise(P, b, fl, m, epochs=4):
    d, row = 1.0, []
    for _ in range(epochs):
        row.append(m / d)
        d = upd(d, P * float(q(m / d)), P, b, fl)
    return row


RULES = [("beta 1", 1.0, 0.0), ("beta 15/16", 15 / 16, 0.0), ("beta 7/8", 7 / 8, 0.0), ("beta 3/4", 3 / 4, 0.0), ("beta 2/3", 2 / 3, 0.0),
         ("beta 1/2", 1 / 2, 0.0), ("beta 1, floor 1/2", 1.0, 0.5), ("beta 1, floor 3/4", 1.0, 0.75), ("beta 3/4, floor 3/4", 0.75, 0.75)]

if __name__ == "__main__":
    for name, P in (("4K+2K", 4 * K), ("3K+3K", 3 * K)):
        print("==", name)
        for lab, b, fl in RULES:
            empty = 1 / max(1 - b, fl) if max(1 - b, fl) > 0 else float("inf")
            hs = [halt_stats(P, b, fl, h) for h in (6, 12, 24, 36, 48)]
            of = halt_stats(P, b, fl, 48, 0.5)
            wd = 1 / max((1 - b) + b * float(q(0.7)) / F, fl)
            up = rise(P, b, fl, 2.0)
            dn = [1 / v for v in rise(P, b, fl, 0.5)]
            gen = rise(P, b, fl, 0.3, 7)
            ge = next((i for i, v in enumerate(gen) if v >= 0.9), 99)
            print(f"{lab:20s}: empty window S/D {empty:.2f} | worst S/D after a halt of 6, 12, 24, 36, 48 h: " + " ".join("%.2f" % x[0] for x in hs)
                  + " | displaced 15 s: " + " ".join("%.0e" % x[1] for x in hs) + " | 10 s: " + " ".join("%.0e" % x[2] for x in hs)
                  + f" | half offline 48 h: {of[0]:.2f} {of[1]:.0e} {of[2]:.0e} | 30 % withholds a window: {wd:.3f} ({C15(wd):.1e}) | doubles: "
                  + " ".join("%.3f" % v for v in up[1:]) + " | halves, D/S: " + " ".join("%.2f" % v for v in dn[1:])
                  + f" | genesis 30 %: " + " ".join("%.2f" % v for v in gen) + f" (S/D >= 0.9 from epoch {ge})")
