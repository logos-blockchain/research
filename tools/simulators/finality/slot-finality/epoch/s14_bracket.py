"""Bounds on the least epoch, and the other figures that rest on the necessary values of statements
5.5 and 9.2 (REVIEW.md, statements 5.5, 5.9, 9.2, 10.2 and 10.3, and sections 0, 11 and 12).

1. The margin over K that 5.5 (3) makes necessary: G - K >= 611.28 / x - 1 slots.
2. For each state of the K row (5.9): the necessary gap, that is the least gap at which the lower
   bound of 5.5 (1) (every win counted) or of 5.5 (2) (only blocks of the chain count) falls to
   1e-9; the necessary span of 9.2, ceil(611.28 / x); and beside them G* (5.4) and w_B (9.4, with the
   proved survival law, read from the last part of out_08_buffer.txt). The state with a tenth of the
   honest stake offline is read twice:
   (a) once the inference has corrected, x = 0.63 / 0.93; (b) before it corrects, x = 0.63.
3. The bounds of 10.2 over the states the K row requires: no epoch shorter than
   E_nec = max(P, G_nec + w_nec) + G_nec keeps the rules S, B, L and I, and
   E_suf = max(P, G* + w_B) + max(G*, 2 K - 1) keeps them and gives phase 3 the 2 K - 1 slots that
   the argument of proofs/genesis/GENESIS.md (7.1, 7.3) for the Bootstrap rule needs (10.1, rule J),
   with the window shortened to phases 1 and 2 or kept at 108 h. The condition enters E_suf only: it
   is a condition of that argument, not a proven necessity.
4. A node's own draw of the lottery at the use slot (5.10): each waiting phase needs G* + d, and
   phase 3 at least 2 K - 1.
5. New stake's wait with a late snapshot: phase 1, the buffer and the gap of 72 h.
6. A second computation of the necessary gaps and of G*: binomial tails summed term by term in log
   space, without scipy.stats.binom.
7. GENESIS's bounds at a phase 3 of 2 K - 1 slots, for a coalition of 30 % at delays of 10 and 15
   slots. The bound of GENESIS 6.3 and the cells of 8.1 have one term that reads the gap G,
   P1(G + 1 - s) or P1(G + 2 - s - g). GENESIS computes them at today's G = 259,200. This part
   computes them, with GENESIS's own code and its cached settlement curves (read only), at
   G = 2 K - 1 and at today's G: the bound for every fork per divergence slot and over a year at
   s = s_gen, and the least windows per divergence slot and over a year, from the cells alone and
   from the total at that K with s <= K - 1. The search follows proofs/genesis/g04_union.py.
Usage: python s14_bracket.py > out_14_bracket.txt   (after s08_buffer.py, and after proofs/genesis/g03_settle.py,
       whose settlement curves part 7 reads from proofs/genesis/.cache)
"""
import math
import os
import re
import sys

import numpy as np
from scipy.special import gammaln

from common import CASES, EPS, F, GAP, H, PERIOD, least_gap, least_int, lower_chain, lower_wins, p_of

HERE = os.path.dirname(os.path.abspath(__file__))
GENESIS_DIR = os.path.join(HERE, "proofs", "genesis")
C = math.log(1 / EPS) / -math.log1p(-F)        # ln(1/eps) / ln(1/(1 - f)) = 611.28 slots


def j_min(K):
    """The least phase 3 of GENESIS's argument for the Bootstrap rule: 2 K <= G + 1 (GENESIS 7.1, 7.3)."""
    return 2 * K - 1

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
    """w_B per state with the proved survival law, from the last part of out_08_buffer.txt."""
    out = {}
    for line in open(os.path.join(HERE, "out_08_buffer.txt")):
        m = re.match(r"\s+(.+?): proved w_B = (\d+) slots", line)
        if m:
            out[m.group(1)] = int(m.group(2))
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


# --- GENESIS at a phase 3 of 2 K - 1 slots (part 7) ---------------------------------------------
def least_window(fn, lo, hi, step=10):
    """The least s in [lo, hi] with fn(s) <= EPS: a scan in steps, then slot by slot (as g04_union.least)."""
    prev = lo
    for s in range(lo, hi + 1, step):
        if fn(s) <= EPS:
            for s2 in range(max(lo, prev), s + 1):
                if fn(s2) <= EPS:
                    return s2
        prev = s
    return None


def genesis_at_gap():
    """Part 7: the bounds of GENESIS 6.3 and 8.1 for every fork at G = 2 K - 1 and at today's G."""
    sys.path.insert(0, GENESIS_DIR)
    from common_g import GAP as G_TODAY, S_GEN as S, YEAR, U_at, Window, p_of as p_g, settle_cached
    t_max = 160_000                                   # the length of the cached curves (g04_union.T_MAX)
    spans = (("one divergence slot", 1), ("1 year", YEAR))
    names = ("every fork at s_gen, one divergence slot", "every fork at s_gen, 1 year",
             "least window, one divergence slot, cells alone", "least window, one divergence slot, total at K",
             "least window, 1 year, cells alone", "least window, 1 year, total at K")
    rows, diffs = [], []
    for d in (10, 15):
        w = Window(p_g(0.3), p_g(0.7), d)
        u, u1 = settle_cached(0.3, d, t_max), settle_cached(0.3, d + 1, t_max)
        p1c = w.p1_curve(G_TODAY + 1)

        def P1(x):
            return np.where(x >= 1, p1c[np.clip(x, 0, G_TODAY + 1)], 1.0)

        def U(x):
            return np.where(x >= 1, u[np.clip(x, 1, None) - 1], 1.0)

        def every(s, span, gap, K=None):
            """The cells of 8.1 (2) for every fork; with K, the smaller total of g04_union (A or B)."""
            g = np.arange(1, s + 1)
            cells = np.ceil(span / g)
            base = U(s - g) + P1(gap + 2 - s - g)
            part = float(min(1.0, (cells * base).min()))
            if K is None:
                return part
            tot_a = float((cells * (base + P1(K - s - g + 1))).min()) + U_at(u, K - 2)
            return float(min(1.0, tot_a, part + U_at(u1, K - 1)))

        for K, _ in CASES.values():
            vals = {}
            for gap in (j_min(K), G_TODAY):
                v = [float(P1(np.array(gap + 1 - S))), every(S, 1, gap), every(S, YEAR, gap)]
                for _, span in spans:
                    v.append(least_window(lambda s: every(s, span, gap), 2_000, t_max - 1))
                    v.append(least_window(lambda s: every(s, span, gap, K), 2_000, K - 1))
                vals[gap] = v
            a, b = vals[j_min(K)], vals[G_TODAY]
            fmt = lambda x: "none" if x is None else (f"{x:.3e}" if isinstance(x, float) else str(x))   # noqa: E731
            here = [(n, fmt(x), fmt(y)) for n, x, y in zip(names, a[1:], b[1:]) if fmt(x) != fmt(y)]
            diffs += [f"Delta = {d}, K = {K}, {n}: {x} (today {y})" for n, x, y in here]
            rows.append(f"   Delta = {d}, K = {K}, G = {j_min(K)} (today {G_TODAY}): P1(G + 1 - s) = {a[0]:.2e} (today {b[0]:.2e}); "
                        f"every fork at s = {S}: one divergence slot {a[1]:.3e} (today {b[1]:.3e}), 1 year {a[2]:.3e} (today {b[2]:.3e})")
            rows.append(f"      least windows, cells alone: one divergence slot {fmt(a[3])} (today {fmt(b[3])}), 1 year {fmt(a[5])} "
                        f"(today {fmt(b[5])}); total at K with s <= K - 1: one divergence slot {fmt(a[4])} (today {fmt(b[4])}), "
                        f"1 year {fmt(a[6])} (today {fmt(b[6])}) | {'equal' if not here else 'differs'}")
    return rows, diffs


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
        g3 = max(gs, j_min(K))
        print(f"   {name}, a tenth offline read {READING[reading]} | gap {gw} ({gw / H:.2f} h); {gc} ({gc / H:.2f} h); "
              f"span {wn}; G* {gs} ({gs / H:.2f} h); w_B {wb} ({wb / H:.2f} h); phase 3 that suffices {g3} ({g3 / H:.2f} h), "
              f"{g3 - gs} ({(g3 - gs) / H:.2f} h) more than G*")
        for label, window in (("window shortened to phases 1 and 2", 0), ("window kept at 108 h", PERIOD)):
            e_w = max(window, gw + wn) + gw
            e_c = max(window, gc + wn) + gc
            e_s = max(window, gs + wb) + g3
            print(f"      {label}: no shorter than {hours(e_w)}; {hours(e_c)} | suffices {hours(e_s)}")

    print("\n4. a node's own draw of the lottery at the use slot (5.10): each waiting phase G* + d, phase 3 at least 2 K - 1")
    for (name, reading), row in ROWS.items():
        if reading != "a":
            continue
        K = CASES[name][0]
        g_own = max(seen[(name, s[0])][2] + seen[(name, s[0])][5] for s in row)
        g3 = max(g_own, j_min(K))
        wb = largest[(name, reading)][4]
        print(f"   {name}: phase 1 {hours(g_own)}; phase 3 {hours(g3)}; epoch, window shortened {hours(g_own + wb + g3)}, "
              f"window kept {hours(max(PERIOD, g_own + wb) + g3)}")

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

    print("\n7. GENESIS 6.3 and 8.1 at a phase 3 of 2 K - 1 slots, a coalition of 30 %: the terms that read the gap G, "
          "at G = 2 K - 1 and at today's G (GENESIS's code and cached curves, read only)")
    rows, diffs = genesis_at_gap()
    for r in rows:
        print(r)
    print("   every bound and window at G = 2 K - 1 equals today's" if not diffs else
          "   at G = 2 K - 1 every bound and window equals today's except: " + "; ".join(diffs))
