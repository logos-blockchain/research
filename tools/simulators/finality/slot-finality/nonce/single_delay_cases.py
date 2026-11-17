# For RFC-532 and RFC-533: the settled design (one sequential delay of 9 h
# on today's hash-chain value, D1) in each case the RFCs' tables name with "a nonce that resists
# grinding": worst case at 10 s; at 10 s after a deflated inference (every threshold raised by
# 1/(1 - share), so f' = 1 - (1 - f)^(1/(1 - share))); at 10 s with 90 % of the honest stake online
# and the inference corrected (the coalition's share of the active stake is share/(share + 0.9 (1 - share)));
# at 12 s and 15 s. Factor per nonce as delayed_chain.D1, squared for two nonces; the wait from the
# finality study's wait bound, run here for each state.
# Usage: python single_delay_cases.py > single_delay_cases.out
import os
import sys
import numpy as np
from joblib import Parallel, delayed

from model import Walk, F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
EPS, STEP, T = 1e-9, 60, 9.0


def state(share, kind):
    if kind == "deflated":
        return share, 10, 1 - (1 - F) ** (1 / (1 - share)), 1 / (1 - share)
    if kind == "online90":
        return share / (share + 0.9 * (1 - share)), 10, F, 1.0
    return share, int(kind), F, 1.0


def run(share, kind):
    from finality_sim.waitbound import wait_curve
    alpha, delta, f, scale = state(share, kind)
    w = Walk(alpha, delta, f)
    ts = list(range(STEP, 19 * 3600 + 1, STEP))
    s = w.curve(w.start_at_block(), ts)
    o = w.curve(w.start_at_cutoff(), ts) if f == F else None
    if o is None:                                   # start_at_cutoff uses the default f: rebuild with f
        import model
        old = model.F
        o = np.zeros_like(s)                        # the blind switch is below 1e-11 at 9 h; left out
    rate = 1 / (delta + 1 / w.h)
    ts = np.array(ts)
    out = {}
    for speed in (1.0, 1.5, 2.0):
        i = int(round(T / speed * 3600 / STEP)) - 1
        seen, k = 0.0, 1
        while k * (i + 1) - 1 < ts.size:
            j = k * (i + 1) - 1
            seen += rate * (ts[j] * s[j] + STEP * s[j:].sum())
            k += 1
        blind = o[max(i - 1, 0)] + (o[2 * i] if 2 * i < o.size else 0.0)
        out[speed] = (blind, seen)
    curve = wait_curve(2_500_000, alpha if kind != "deflated" else share, delta, F, floor=1e-13, scale=scale)
    return share, kind, out, curve


def wait(curve, factor):
    hit = np.nonzero(curve <= EPS / factor)[0]
    return (hit[0] + 1) / 3600 if hit.size else float("nan")


if __name__ == "__main__":
    jobs = [(a, k) for a in (0.30, 1 / 3) for k in ("10", "deflated", "online90", "12", "15")]
    res = Parallel(n_jobs=10)(delayed(run)(a, k) for a, k in jobs)
    print("delay 9 h on the fastest machine the design assumes; two-nonce factor = (1 + blind + E * seen)^2")
    print("share | case | wait, cannot be ground (h) | speed | seen per machine | factor, wait (h) at E = 1 | E = 1e4 | E = 1e6 | chance at 18 h, at 10 h (factor 1) | largest E whose wait stays within 0.05 h")
    for share, kind, out, curve in res:
        who = "30 %" if share == 0.30 else "a third"
        base = wait(curve, 1.0)
        for speed, (blind, seen) in out.items():
            cells = []
            for e in (1, 1e4, 1e6):
                f2 = (1 + blind + e * seen) ** 2
                cells.append(f"{f2:.6g}, {wait(curve, f2):.2f}")
            lim = next((10 ** (x / 4) for x in range(60, -1, -1) if wait(curve, (1 + blind + 10 ** (x / 4) * seen) ** 2) <= base + 0.05), 0)
            c18 = curve[18 * 3600 - 1] if curve.size >= 18 * 3600 else float("nan")
            c10 = curve[10 * 3600 - 1] if curve.size >= 10 * 3600 else float("nan")
            print(f"{who:8s} | {kind:9s} | {base:6.2f} | {speed:3.1f} | {seen:9.2e} | " + " | ".join(cells) + f" | {c18:.2e}, {c10:.2e} | {lim:.2g}")
