# The settled design (one sequential delay on today's hash-chain value) in the state
# "worst case at 15 s after a deflated inference" (every threshold raised by 1/(1 - share), so
# f' = 1 - (1 - f)^(1/(1 - share))), for a third against a 36 h window and 30 % against a 15 h window.
# Factor per nonce as delayed_chain.D1: 1 + blind + E * seen; squared for two nonces. Unlike
# single_delay_cases.py, the blind switch is computed here at the deflated rate.
#  (1) the 9 h delay: seen per machine, two-nonce factor and wait at E = 1, 1e4, 1e6, speeds 1, 1.5, 2;
#  (2) the shortest delay (steps of 0.5 h) whose two-nonce factor keeps the wait within the window.
# Usage: python deflated_delay.py > deflated_delay.out
import math
import os
import sys
import numpy as np
from joblib import Parallel, delayed
import model
from model import Walk, F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
EPS, STEP, HMAX = 1e-9, 60, 66


class WalkF(Walk):
    def __init__(self, alpha, delta, f):
        super().__init__(alpha, delta, f, lo=900, hi=400)
        self.f = f

    def start_at_cutoff(self):
        step = model.gap_wins_pmf(self.alpha, self.delta, self.f)
        back = model.alltime_max_pmf(step)
        age = model.age_pmf(self.alpha, self.delta, self.f)
        p = np.zeros((self.delta + 1, self.n))
        for m, pm in enumerate(age):
            if pm < 1e-30:
                break
            wins = np.array([math.comb(m, j) * self.a ** j * (1 - self.a) ** (m - j) for j in range(min(m, 80) + 1)])
            lead = np.convolve(wins, back)
            k = min(lead.size, self.hi)
            p[max(self.delta - m, 0), self.lo:self.lo + k] += pm * lead[:k]
        return p


def run(share, delta):
    from finality_sim.waitbound import wait_curve
    f = 1 - (1 - F) ** (1 / (1 - share))
    w = WalkF(share, delta, f)
    ts = list(range(STEP, HMAX * 3600 + 1, STEP))
    s = w.curve(w.start_at_block(), ts)
    o = w.curve(w.start_at_cutoff(), ts)
    curve = wait_curve(2_500_000, share, delta, F, floor=1e-13, scale=1 / (1 - share))
    return share, delta, np.array(ts), s, o, 1 / (delta + 1 / w.h), curve


def parts(ts, s, o, rate, hours):
    i = int(round(hours * 3600 / STEP)) - 1
    seen, k = 0.0, 1
    while k * (i + 1) - 1 < ts.size:
        j = k * (i + 1) - 1
        seen += rate * (ts[j] * s[j] + STEP * s[j:].sum())
        k += 1
    blind = o[max(i - 1, 0)] + (o[2 * i] if 2 * i < o.size else 0.0)
    return blind, seen


def wait(curve, factor):
    hit = np.nonzero(curve <= EPS / factor)[0]
    return (hit[0] + 1) / 3600 if hit.size else float("nan")


if __name__ == "__main__":
    res = Parallel(n_jobs=2)(delayed(run)(a, d) for a, d in ((1 / 3, 15), (0.30, 15)))
    for share, delta, ts, s, o, rate, curve in res:
        who = "30 %" if share == 0.30 else "a third"
        window = 15 if share == 0.30 else 36
        base = wait(curve, 1.0)
        room = EPS / curve[window * 3600 - 1]
        print(f"\n{who}, {delta} s, deflated: wait that cannot be ground {base:.2f} h; window {window} h absorbs a two-nonce factor of {room:.4g} (per nonce {room ** 0.5:.4g})")
        print("survival of a branch after 9, 12, 18, 24 h: " + ", ".join(f"{s[h * 60 - 1]:.2e}" for h in (9, 12, 18, 24))
              + "; a choice still open after: " + ", ".join(f"{o[h * 60 - 1]:.2e}" for h in (9, 12, 18, 24)))
        print("(1) the 9 h delay | speed | blind | seen per machine | two-nonce factor, wait (h) at E = 1 | 1e4 | 1e6")
        for speed in (1.0, 1.5, 2.0):
            blind, seen = parts(ts, s, o, rate, 9.0 / speed)
            cells = [f"{(1 + blind + e * seen) ** 2:.6g}, {wait(curve, (1 + blind + e * seen) ** 2):.2f}" for e in (1, 1e4, 1e6)]
            print(f"   {speed:3.1f} | {blind:.2e} | {seen:.2e} | " + " | ".join(cells))
        print(f"(2) shortest delay on the fastest machine the design assumes (h) that keeps the wait within {window} h | speed | E = 1 | 1e4 | 1e6")
        for speed in (1.0, 1.5, 2.0):
            row = []
            for e in (1, 1e4, 1e6):
                t = next((h / 2 for h in range(2, 2 * HMAX // 2) if (lambda b, sn: (1 + b + e * sn) ** 2 <= room)(*parts(ts, s, o, rate, h / 2 / speed))), float("nan"))
                row.append(t)
            print(f"   {speed:3.1f} | " + " | ".join(f"{t:5.1f}" for t in row))
        print("    factor by delay at speed 1 (delay h: blind, seen, two-nonce factor at E = 1e6, wait): "
              + "; ".join(f"{t}: {b:.1e}, {sn:.1e}, {(1 + b + 1e6 * sn) ** 2:.4g}, {wait(curve, (1 + b + 1e6 * sn) ** 2):.2f}"
                          for t in (9, 12, 14, 18, 24) for b, sn in [parts(ts, s, o, rate, t)]))
