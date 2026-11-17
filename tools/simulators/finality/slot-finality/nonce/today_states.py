# For RFC-532 and RFC-533: TODAY's nonce (hash chain, 2^64 evaluated, both
# ends of the grinding bound, an attack that meets two nonces) in each disturbance and each pair:
#   15      every honest block up to 15 s late (else 10 s)
#   off     a tenth of the honest stake offline, inference corrected: alpha' = s / (s + 0.9 (1 - s))
#   defl    the inferred stake equals the honest stake online: every rate times 1 / (1 - alpha')
# For each state and share: the pair factor (grinding.pair_bounds at the state's f, share, delay) and
# the wait bound (waitbound.wait_curve with scale). Printed: the wait at 30 %, the chance times
# factor at 18 h and 10 h, and the largest share 18 h and 10 h prove (crossing of 1e-9, log-linear
# between shares 0.01 apart).
# Usage: python today_states.py > today_states.out
import math
import os
import sys
import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
F, EPS, FLOOR = 1 / 30, 1e-9, 1e-45
STATES = {"10 s (no disturbance)": (10, False, False), "15 s": (15, False, False),
          "off, 10 s": (10, True, False), "defl, 10 s": (10, False, True),
          "15 s + off": (15, True, False), "15 s + defl": (15, False, True),
          "off + defl, 10 s": (10, True, True)}
SHARES = [round(0.17 + 0.01 * i, 2) for i in range(17)]


def run(name, s):
    from finality_sim.grinding import factors, pair_bounds
    from finality_sim.waitbound import wait_curve
    delta, off, defl = STATES[name]
    a = s / (s + 0.9 * (1 - s)) if off else s
    scale = 1 / (1 - a) if defl else 1.0
    f = 1 - (1 - F) ** scale
    ts, lo, up, lo2, up2 = pair_bounds(f, a, budget_bits=64, depths=4000, floor=100, per_bit=4, delta=delta)
    flo, fhi = factors(ts, lo2, up2, EPS)
    c = wait_curve(2_500_000, a, delta, F, floor=FLOOR, scale=scale)
    def at(h):
        return float(c[h * 3600 - 1]) if c.size >= h * 3600 else FLOOR
    def wait(fac):
        hit = np.nonzero(c <= EPS / fac)[0]
        return (hit[0] + 1) / 3600 if hit.size else float("nan")
    return name, s, a, flo, fhi, wait(1.0), wait(flo), wait(fhi), at(18), at(10)


def cross(ss, logs):
    """largest share with log10(chance * factor) <= -9"""
    best = None
    for i in range(len(ss) - 1):
        y0, y1 = logs[i] + 9, logs[i + 1] + 9
        if y0 <= 0 < y1:
            best = ss[i] + (ss[i + 1] - ss[i]) * (-y0) / (y1 - y0)
    if best is None:
        return "> %.2f" % ss[-1] if logs[-1] + 9 <= 0 else "< %.2f" % ss[0]
    return "%.3f" % best


if __name__ == "__main__":
    jobs = [(n, s) for n in STATES for s in SHARES]
    res = Parallel(n_jobs=13)(delayed(run)(*j) for j in jobs)
    print("state | share | share of active stake | pair factor lo-hi | wait unground (h) | wait today's nonce lo-hi (h) | chance at 18 h, 10 h (unground)")
    for name, s, a, flo, fhi, w1, wlo, whi, c18, c10 in res:
        if s in (0.27, 0.30):
            print(f"{name:22s} | {s:.2f} | {a:.4f} | {flo:.3g}-{fhi:.3g} | {w1:6.2f} | {wlo:6.2f}-{whi:6.2f} | {c18:.2e}, {c10:.2e}")
    print("largest share proven (today's nonce: hi end - lo end of the factor; unground)")
    for n in STATES:
        rows = [r for r in res if r[0] == n]
        ss = [r[1] for r in rows]
        for hh, k in ((18, 8), (10, 9)):
            lo = [math.log10(r[k] * r[3]) for r in rows]
            hi = [math.log10(r[k] * r[4]) for r in rows]
            un = [math.log10(r[k]) for r in rows]
            print(f"{n:22s} | K = {hh:2d} h | today {cross(ss, hi)}-{cross(ss, lo)} | unground {cross(ss, un)}")
