"""Bounds on the least epoch, and the other figures that rest on the necessary values of statements
5.5 and 9.2 (REVIEW.md, statements 5.5, 5.9, 9.2, 10.2 and 10.3, and sections 0 and 11).

1. The margin over K that 5.5 (3) makes necessary: G - K >= 611.28 / x - 1 slots.
2. For each state of the K row (5.9): the necessary gap, that is the least gap at which the lower
   bound of 5.5 (1) (every win counted) or of 5.5 (2) (only blocks of the chain count) falls to
   1e-9; the necessary span of 9.2, ceil(611.28 / x); and beside them G* (5.4) and w_B (9.4, read
   from out_08_buffer.txt). The state with a tenth of the honest stake offline is read twice:
   (a) once the inference has corrected, x = 0.63 / 0.93; (b) before it corrects, x = 0.63.
3. The bounds of 10.2 over the states the K row requires: no epoch shorter than
   E_nec = max(P, G_nec + w_nec) + G_nec keeps the rules, and E_suf = max(P, G* + w_B) + G* does,
   with the window shortened to phases 1 and 2 or kept at 108 h.
4. A node's own draw of the lottery at the use slot (5.10): each waiting phase needs G* + d.
5. New stake's wait with a late snapshot: phase 1, the buffer and the gap of 72 h.
6. A second computation of the necessary gaps and of G*: binomial tails summed term by term in log
   space, without scipy.stats.binom.
Usage: python s14_bracket.py > out_14_bracket.txt   (after s08_buffer.py)
"""
import math
import os

import numpy as np
from scipy.special import gammaln

from common import CASES, EPS, F, GAP, H, PERIOD, least_gap, least_int, lower_chain, lower_wins, p_of

HERE = os.path.dirname(os.path.abspath(__file__))
C = math.log(1 / EPS) / -math.log1p(-F)        # ln(1/eps) / ln(1/(1 - f)) = 611.28 slots

# (state, share x of the inferred stake that builds, delay d, buffer of out_08_buffer.txt)
NONE = ("no disturbance, 10 s", 0.7, 10, "30 %, no disturbance, 10 s")
LATE = ("every block T_M = 15 s late", 0.7, 15, "30 %, every honest block 15 s late")
OFF_A = ("a tenth of the honest stake offline, 10 s", 0.63 / 0.93, 10, "30 %, a tenth of the honest stake offline, 10 s")
OFF_B = ("a tenth offline, before the inference corrects, 10 s", 0.63, 10,
         "30 %, a tenth of the honest stake offline before the inference corrects, 10 s")
DEFL = ("deflated inference, 10 s", 1.0, 10, "30 %, deflated inference, 10 s")
LATE_OFF_A = ("15 s and a tenth of the honest stake offline", 0.63 / 0.93, 15, "30 %, 15 s and a tenth of the honest stake offline")
LATE_OFF_B = ("15 s and a tenth offline, before the inference corrects", 0.63, 15,
              "30 %, 15 s and a tenth of the honest stake offline before the inference corrects")
LATE_DEFL = ("15 s and a deflated inference", 1.0, 15, "30 %, 15 s and a deflated inference")
OFF_DEFL = ("a tenth offline and a deflated inference, 10 s", 1.0, 10,
            "30 %, a tenth of the honest stake offline and a deflated inference, 10 s")

ROWS = {   # one disturbance at a time for the latest #533, two together for the base
    ("10 h (#533)", "a"): (NONE, LATE, OFF_A, DEFL),
    ("10 h (#533)", "b"): (NONE, LATE, OFF_B, DEFL),
    ("18 h (base)", "a"): (NONE, LATE, OFF_A, DEFL, LATE_OFF_A, LATE_DEFL, OFF_DEFL),
    ("18 h (base)", "b"): (NONE, LATE, OFF_B, DEFL, LATE_OFF_B, LATE_DEFL, OFF_DEFL),
}
READING = {"a": "the inference corrected", "b": "before the inference corrects"}


def read_buffers():
    out, name = {}, None
    for line in open(os.path.join(HERE, "out_08_buffer.txt")):
        if ": coalition's share" in line:
            name = line.split(": coalition's share")[0]
        elif line.strip().startswith("w_B =") and name is not None:
            out[name] = int(line.split("=")[1].split("slots")[0])
    return out


def g_nec(K, phi, x, d=None):
    """The least gap at which the lower bound of 5.5 (1), or of 5.5 (2) if d is given, is at most 1e-9."""
    p = p_of(x)
    if d is None:
        return least_int(lambda G: lower_wins(G, K, phi, p), K, 40_000_000)
    return least_int(lambda G: lower_chain(G, K, phi, p, d), K, 40_000_000)


def w_nec(x):
    """The least span with (1 - f)^(x w) <= 1e-9 (9.2)."""
    return math.ceil(C / x)


def hours(slots):
    return f"{slots:7d} slots, {slots / H:6.2f} h"


# --- the second computation (part 6) ------------------------------------------------------------
def log_cdf(k, m, p):
    """ln P(Bin(m, p) <= k), the pmf terms summed in log space."""
    if k < 0:
        return -math.inf
    if k >= m:
        return 0.0
    i = np.arange(0, k + 1, dtype=np.float64)
    terms = gammaln(m + 1.0) - gammaln(i + 1.0) - gammaln(m - i + 1.0) + i * math.log(p) + (m - i) * math.log1p(-p)
    top = terms.max()
    return float(top + math.log(np.exp(terms - top).sum()))


def wins_2(G, K, phi, p):
    if G < K:
        return 1.0
    a = 1.0 if G < phi else math.exp(log_cdf(phi - 1, G, p))
    return max(a, math.exp((G - K + 1) * math.log1p(-p)))


def chain_2(G, K, phi, p, d):
    if G < K:
        return 1.0
    m = G + 1 - phi * d
    a = 1.0 if m < phi + 1 else math.exp(log_cdf(phi, m, p))
    return max(a, math.exp((G - K + 1) * math.log1p(-p)))


def upper_2(G, K, phi, p, d):
    """The bound of 5.4: S(phi + 1; G, p, d) + R(G - K - 2d + 1; p)."""
    m = G - (phi + 1) * d
    s = 1.0 if m < phi + 1 else math.exp(log_cdf(phi, m, p))
    r_m = G - K - 2 * d + 1
    r = 1.0 if r_m <= 0 else math.exp(r_m * math.log1p(-p)) + r_m * p * math.exp((r_m - 1) * math.log1p(-p))
    return min(1.0, s + r)


def bisect(fn, lo, hi=40_000_000):
    while lo < hi:
        mid = (lo + hi) // 2
        if fn(mid) <= EPS:
            hi = mid
        else:
            lo = mid + 1
    return lo


if __name__ == "__main__":
    buffers = read_buffers()

    print(f"1. the margin over K that 5.5 (3) makes necessary: G - K >= {C:.2f} / x - 1 slots")
    for x in (1.0, 0.7):
        print(f"   x = {100 * x:5.1f} %: {C / x - 1:.2f} slots, so G - K >= {math.ceil(C / x - 1)}")

    print("\n2. each state of the K row: necessary gap (5.5 (1) every win counted; 5.5 (2) chain blocks only), "
          "G* (5.4), necessary span (9.2), w_B (9.4)")
    seen = {}
    for (name, reading), row in ROWS.items():
        K, phi = CASES[name]
        print(f"   {name}, K = {K}, phi = {phi}; a tenth offline read {READING[reading]}")
        for state, x, d, key in row:
            if (name, state) in seen:
                continue
            gw, gc, gs = g_nec(K, phi, x), g_nec(K, phi, x, d), least_gap(K, phi, x, d)
            seen[(name, state)] = (gw, gc, gs, w_nec(x), buffers[key], d)
            print(f"     {state}: x = {100 * x:6.2f} %, d = {d} | every win {hours(gw)} | chain only {hours(gc)} | "
                  f"G* {hours(gs)} | span {w_nec(x)} slots | w_B {hours(buffers[key])}")

    print("\n3. bounds on the least epoch over the states the K row requires (10.2)")
    print("   case | largest: necessary gap (every win; chain only), necessary span, G*, w_B")
    print("        | no shorter epoch keeps the rules (every win; chain only) | this epoch suffices")
    largest = {}
    for (name, reading), row in ROWS.items():
        K, phi = CASES[name]
        vals = [seen[(name, s[0])] for s in row]
        gw, gc, gs = max(v[0] for v in vals), max(v[1] for v in vals), max(v[2] for v in vals)
        wn, wb = max(v[3] for v in vals), max(v[4] for v in vals)
        largest[(name, reading)] = (gw, gc, gs, wn, wb)
        print(f"   {name}, a tenth offline read {READING[reading]} | gap {gw} ({gw / H:.2f} h); {gc} ({gc / H:.2f} h); "
              f"span {wn}; G* {gs} ({gs / H:.2f} h); w_B {wb} ({wb / H:.2f} h)")
        for label, window in (("window shortened to phases 1 and 2", 0), ("window kept at 108 h", PERIOD)):
            e_w = max(window, gw + wn) + gw
            e_c = max(window, gc + wn) + gc
            e_s = max(window, gs + wb) + gs
            print(f"      {label}: no shorter than {hours(e_w)}; {hours(e_c)} | suffices {hours(e_s)}")

    print("\n4. a node's own draw of the lottery at the use slot (5.10): each waiting phase G* + d")
    for (name, reading), row in ROWS.items():
        if reading != "a":
            continue
        g_own = max(seen[(name, s[0])][2] + seen[(name, s[0])][5] for s in row)
        wb = largest[(name, reading)][4]
        print(f"   {name}: phase {hours(g_own)}; epoch, window shortened {hours(2 * g_own + wb)}, "
              f"window kept {hours(max(PERIOD, g_own + wb) + g_own)}")

    print(f"\n5. new stake's wait with a late snapshot: phase 1 + buffer + gap of {GAP} slots ({GAP / H:g} h), latest #533")
    K, phi = CASES["10 h (#533)"]
    g1, w15 = least_gap(K, phi, 1.0, 15), buffers["30 %, every honest block 15 s late"]
    print(f"   all of the inferred stake builds, 15 s: G* {g1} + w_B {w15} + gap = {hours(g1 + w15 + GAP)}")
    for reading in ("a", "b"):
        gw, gc, gs, wn, wb = largest[("10 h (#533)", reading)]
        print(f"   every state of the K row, a tenth offline read {READING[reading]}: G* {gs} + w_B {wb} + gap = {hours(gs + wb + GAP)}; "
              f"necessary: {gw} + {wn} + gap = {hours(gw + wn + GAP)} (every win), {gc} + {wn} + gap = {hours(gc + wn + GAP)} (chain only)")

    print("\n6. the necessary gaps and G* again, with binomial tails summed in log space (no scipy.stats.binom)")
    agree = True
    for (name, state), (gw, gc, gs, wn, wb, d) in seen.items():
        K, phi = CASES[name]
        x = next(s[1] for row in ROWS.values() for s in row if s[0] == state)
        p = p_of(x)
        gw2 = bisect(lambda G: wins_2(G, K, phi, p), K)
        gc2 = bisect(lambda G: chain_2(G, K, phi, p, d), K)
        gs2 = bisect(lambda G: upper_2(G, K, phi, p, d), K)
        same = (gw2, gc2, gs2) == (gw, gc, gs)
        agree &= same
        print(f"   {name}, {state}: every win {gw2}, chain only {gc2}, G* {gs2} | {'equal' if same else 'DIFFERENT'}")
    print("   every value equal" if agree else "   A VALUE DIFFERS")
