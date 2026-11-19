"""CHECK.md, item 5: the terms of GENESIS 7.3 recomputed with GENESIS's own code.

GENESIS's common_g.py is imported read-only (no bytecode, numba cache in this folder's .cache/numba). The settlement
curves U are read with np.load from GENESIS's .cache; a missing curve is an error, never a recomputation.
States: GENESIS g07_states.py's list (REVIEW 5.9's mapping), against 30 %, K = 36,000, s = 16,200.

Prints per state, with six significant digits:
  P1(s), U(s - 1), U(K - 2), U_(Delta+1)(K - 1), P1(K - s) and P1(G + 1 - s) for
  G = 35,999 (K - 1), 46,910, 52,199, 54,000, 72,000 and 259,200; the closed form (Window.p1) and the
  forward pass (Window.p1_curve) side by side; the floor of P1 (the mass Window places at infinity).
Then the totals per divergence slot, the least windows under B (s <= K - 1) and A (s <= G + 1 - K),
the check of A's 4.3 (57,335 and 69,180), and the least G that B's theorem asks for those windows.
Usage: python c5_terms.py > out_c5_terms.txt
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["NUMBA_CACHE_DIR"] = os.path.join(HERE, ".cache", "numba")
GEN = os.path.normpath(os.path.join(HERE, "..", "..", "genesis"))
sys.path.insert(0, GEN)

import numpy as np  # noqa: E402

import common_g as cg  # noqa: E402

K = 36_000
S = cg.S_GEN
T_MAX = 160_000
EPS = 1e-9
YEAR = cg.YEAR
GAPS = [35_999, 46_910, 52_199, 54_000, 72_000, 259_200]
X_MAX = 72_001
STATES = [
    ("no disturbance", 0.7, 0.3, 10, (0.3, 1.0)),
    ("every block T_M late", 0.7, 0.3, 15, (0.3, 1.0)),
    ("a tenth offline, inference corrected", 0.63 / 0.93, 0.3 / 0.93, 10, (0.3 / 0.93, 1.0)),
    ("a tenth offline, before the correction", 0.63, 0.3, 10, (0.3 / 0.93, 0.93)),
    ("D equals the honest stake online", 1.0, 0.3 / 0.7, 10, (0.3, 1 / 0.7)),
]


def load_U(alpha, delta, scale):
    name = os.path.join(GEN, ".cache", f"U_a{alpha:.6f}_d{delta}_t{T_MAX}_s{scale:.6f}.npy")
    if not os.path.exists(name):
        raise FileNotFoundError(name)
    return np.load(name)


def r2(v):
    return f"{v:.1e}"


def r3(v):
    return f"{v:.2e}"


if __name__ == "__main__":
    print(f"K = {K}, s = {S}, 1e-9 target; states of GENESIS g07_states.py (REVIEW 5.9)")
    for name, xh, xa, d, (alpha, scale) in STATES:
        ph, pa = cg.p_of(xh), cg.p_of(xa)
        w = cg.Window(pa, ph, d)
        u, u1 = load_U(alpha, d, scale), load_U(alpha, d + 1, scale)
        p1c = w.p1_curve(X_MAX)

        def P1(x):
            return w.p1(int(x)) if x >= 1 else 1.0

        def P1c(x):
            return float(p1c[x]) if 1 <= x <= X_MAX else (1.0 if x < 1 else float("nan"))

        p1s, us = P1(S), cg.U_at(u, S - 1)
        uk2, uk1 = cg.U_at(u, K - 2), cg.U_at(u1, K - 1)
        p1ks = P1(K - S)
        eg = (K - 2 * d - 1) * math.log10(1 - ph)
        print(f"\n{name}: p_h = {ph:.6f}, p_a = {pa:.6f}, Delta = {d}; floor of P1 (mass at infinity) {w.inf_mass:.3e}")
        print(f"  P1(s) = {p1s:.5e}  U(s-1) = {us:.5e}  U(K-2) = {uk2:.5e}  U_{d + 1}(K-1) = {uk1:.5e}  "
              f"P1(K-s) = {p1ks:.5e}  log10 E_g = {eg:.1f}")
        for G in GAPS:
            x = G + 1 - S
            cf = P1(x)
            fp = P1c(x)
            fps = f"{fp:.5e}" if not math.isnan(fp) else "beyond curve"
            print(f"  G = {G}: P1(G+1-s) = P1({x}): closed form {cf:.5e} (2 digits {r2(cf)}, 3 digits {r3(cf)}); forward pass {fps}")
        # totals per divergence slot
        for G in GAPS:
            far = P1(G + 1 - S)
            tot = min(us + p1ks + far + uk2, us + far + uk1)
            lr = p1s + uk2
            print(f"  G = {G}: no honest block P1(s) + U(K-2) = {lr:.4e}; every fork per divergence slot "
                  f"min(A, B) = {tot:.4e}")
        # least windows per divergence slot, as g07 forms the total, at each G (curve only for G + 1 <= X_MAX)
        sv = np.arange(K)
        Us = np.where(sv >= 2, u[np.clip(sv - 2, 0, None)], 1.0)
        nears = np.where(K - sv >= 1, p1c[np.clip(K - sv, 0, X_MAX)], 1.0)
        for G in [g for g in GAPS if g + 1 <= X_MAX]:
            fars = np.where(G + 1 - sv >= 1, p1c[np.clip(G + 1 - sv, 0, X_MAX)], 1.0)
            tot = np.minimum(Us + nears + fars + uk2, Us + fars + uk1)
            ok = np.nonzero(tot[2000:] <= EPS)[0]
            lB = int(ok[0]) + 2000 if ok.size else None
            capA = min(K - 1, G + 1 - K)
            okA = np.nonzero(tot[2000:capA + 1] <= EPS)[0] if capA >= 2000 else np.array([])
            lA = int(okA[0]) + 2000 if okA.size else None
            print(f"  G = {G}: least s with every-fork total <= 1e-9: under B (s <= K-1) {lB}; under A (s <= {capA}) {lA}")

        # A's 4.3: the windows 21,336 (one slot) and 33,181 (a year), cells as GENESIS g04 forms them
        def year_bound(s, G, span):
            g = np.arange(1, s + 1)
            cells = np.ceil(span / g)
            Ug = np.where(s - g >= 1, u[np.clip(s - g, 1, None) - 1], 1.0)
            xs = G + 2 - s - g
            far = np.where(xs >= 1, p1c[np.clip(xs, 0, X_MAX)], 1.0)
            far = np.where(xs > X_MAX, w.inf_mass, far)          # beyond the curve: P1 is at its floor
            xk = K - s - g + 1
            near = np.where(xk >= 1, p1c[np.clip(xk, 0, X_MAX)], 1.0)
            base = Ug + far
            ta = float((cells * (base + near)).min()) + uk2
            tb = float((cells * base).min()) + uk1
            return min(1.0, ta, tb)

        if name == "no disturbance":
            for s_need, span, label in ((21_336, 1, "one divergence slot"), (33_181, YEAR, "1 year")):
                Gs = s_need + K - 1
                vA = year_bound(s_need, Gs, span)
                vprev = year_bound(s_need - 1, Gs, span)
                # least G under B's theorem (G >= K - 1) at which the same window meets 1e-9
                lo = None
                for G in range(K - 1, Gs + 1, 50):
                    if year_bound(s_need, G, span) <= EPS:
                        for G2 in range(max(K - 1, G - 50), G + 1):
                            if year_bound(s_need, G2, span) <= EPS:
                                lo = G2
                                break
                        break
                print(f"  A 4.3, {label}: s = {s_need}: s + K - 1 = {Gs}; bound at G = {Gs}: {vA:.4e} "
                      f"(s - 1 = {s_need - 1}: {vprev:.4e}); least G with the bound <= 1e-9 under B (G >= K - 1): {lo}")
