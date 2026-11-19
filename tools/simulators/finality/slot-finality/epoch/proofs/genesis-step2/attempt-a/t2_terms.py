"""PROOF.md, section 4: the terms of theorem 4.2 (GENESIS 7.3 with s + K <= G + 1) in each state of the
K row, against a coalition of 30 %, for the two schedules and, for comparison, GENESIS's gap.

Per state and gap G it prints (K = 36,000, s = 16,200):
  P1(s) (GENESIS 6.2); U(s - 1), P1(K - s), P1(G + 1 - s) (GENESIS 6.3); U(K - 2), U_(Delta + 1)(K - 1)
  (GENESIS 7.2); E_g = (1 - p_h)^(K - 2 Delta - 1); the extra term of the weaker condition, which is 0
  (PROOF.md 3.3); the totals per divergence slot:
    long-range part   P1(s) + U(K - 2) + E_g,
    every fork        min(U(s - 1) + P1(K - s) + P1(G + 1 - s) + U(K - 2),
                          U(s - 1) + P1(G + 1 - s) + U_(Delta + 1)(K - 1)) + E_g;
  and over histories of a day, 30 days and a year, the cells of GENESIS 8.1 with this G.
It also prints the least s at which the every-fork bound meets 1e-9 per divergence slot and over a year,
and the least G that the condition s + K <= G + 1 then asks for.
U is read from GENESIS's cached curves; P1 from Window.p1_curve (forward pass), checked against the
closed form Window.p1 at the gaps' windows.
Usage: python t2_terms.py > out_2_terms.txt
"""
import math

import numpy as np

from common_s import (EPS, GENESIS_G, H, K, S, STATES, T_MAX, U_at, U_curve, cg, p_of)

GAPS = [("(i) G = 52,199", S + K - 1), ("(ii) G = 54,000", 54_000), ("GENESIS G = 259,200", GENESIS_G)]
SPANS = {"1 day": 24 * H, "30 days": 30 * 24 * H, "1 year": 365 * 24 * H}
X_MAX = 54_001


def cells(p1c, U, U1, s, G, span):
    """GENESIS 8.1 with gap G: (no-honest part, every-fork total) over a history of `span` divergence slots."""
    g = np.arange(1, s + 1)
    n = np.ceil(span / g)
    P1 = lambda x: np.where(x >= 1, p1c[np.clip(x, 0, len(p1c) - 1)], 1.0)    # noqa: E731
    Uw = lambda w: np.where(w >= 1, U[np.clip(w, 1, None) - 1], 1.0)            # noqa: E731
    nh = float(min(1.0, (n * P1(s - g + 1)).min()))
    far = np.where(G + 2 - s - g < len(p1c), P1(G + 2 - s - g), 0.0)           # beyond the curve: below 1e-31
    base = Uw(s - g) + far
    part = float((n * base).min())
    tot_a = float((n * (base + P1(K - s - g + 1))).min()) + U_at(U, K - 2)
    tot_b = part + U_at(U1, K - 1)
    return nh, float(min(1.0, tot_a, tot_b))


if __name__ == "__main__":
    print(f"K = {K}, s = {S}; coalition 30 % of the total active stake; the states of REVIEW.md 5.9 (GENESIS g07_states.py)")
    for name, xh, xa, d, (alpha, scale) in STATES:
        ph, pa = p_of(xh), p_of(xa)
        w = cg.Window(pa, ph, d)
        p1c = w.p1_curve(X_MAX)
        U = U_curve(alpha, d, scale)
        U1 = U_curve(alpha, d + 1, scale)
        lg_eg = (K - 2 * d - 1) * math.log1p(-ph) / math.log(10)     # log10 E_g; E_g underflows a double
        eg = 10.0 ** lg_eg
        p1s, us, p1ks = w.p1(S), U_at(U, S - 1), w.p1(K - S)
        uk2, uk1 = U_at(U, K - 2), U_at(U1, K - 1)
        print(f"\n{name}: p_h = {ph:.6f}, p_a = {pa:.6f}, Delta = {d}")
        print(f"  P1(s) = {p1s:.3e}; U(s - 1) = {us:.3e}; P1(K - s) = {p1ks:.2e}; U(K - 2) = {uk2:.2e}; "
              f"U_{d + 1}(K - 1) = {uk1:.2e}; E_g = (1 - p_h)^(K - 2 Delta - 1) = 10^{lg_eg:.0f}")
        chk = max(abs(p1c[x] / w.p1(x) - 1) for x in (S, K - S, 36_000, 37_801))
        print(f"  forward pass against the closed form at s, K - s, 36,000 and 37,801: largest relative difference {chk:.1e}")
        for gname, G in GAPS:
            far = w.p1(G + 1 - S)
            lr = p1s + uk2 + eg
            every = min(us + p1ks + far + uk2, us + far + uk1) + eg
            print(f"  {gname}: P1(G + 1 - s) = P1({G + 1 - S}) = {far:.2e}; extra term 0; per divergence slot: "
                  f"long-range part {lr:.3e} ({'meets' if lr <= EPS else 'misses'} 1e-9), every fork {every:.3e} "
                  f"({'meets' if every <= EPS else 'misses'} 1e-9)")
            if G <= X_MAX:
                out = []
                for sname, span in SPANS.items():
                    nh, tot = cells(p1c, U, U1, S, G, span)
                    out.append(f"{sname}: no honest block {nh:.2e}, every fork {tot:.3e}")
                print("    histories: " + "; ".join(out))
        # least s for 1e-9, every fork, with the s-dependent terms other than t = now, and the gap it asks for
        for sname, span in (("one divergence slot", 1), ("1 year", SPANS["1 year"])):
            found = None
            for s in range(10_000, 80_000, 1):
                g = np.arange(1, s + 1)
                n = np.ceil(span / g)
                Uw = np.where(s - g >= 1, U[np.clip(s - g, 1, None) - 1], 1.0)
                if float((n * Uw).min()) <= EPS:
                    found = s
                    break
            if found:
                print(f"  every fork, {sname}: the cells' U-part alone meets 1e-9 first at s = {found} ({found / H:.2f} h), "
                      f"which s + K <= G + 1 admits from G = {found + K - 1} on, and s <= K - 1 admits: {found <= K - 1}")
