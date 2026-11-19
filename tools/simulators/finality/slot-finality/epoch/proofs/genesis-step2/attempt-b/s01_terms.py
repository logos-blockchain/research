"""PROOF.md, section 8: the terms of the bound of 7.3 at the two schedules, in the states of the K row.

For each state of REVIEW.md 5.9 (GENESIS g07_states.py's list, against 30 %), at K = 36,000 and
s = s_gen = 16,200:
  - the terms that do not read G: P1(s) (GENESIS 6.2), U(s - 1), P1(K - s) (6.3), U(K - 2) and
    U_(Delta + 1)(K - 1) (7.2); they must equal GENESIS's out_07_states.txt;
  - per gap G: the only term that reads G, P1(G + 1 - s) (6.3, case b > sigma + G + 1), and the
    every-fork total per divergence slot, min(U(s-1) + P1(K-s) + P1(G+1-s) + U(K-2),
    U(s-1) + P1(G+1-s) + U_(Delta+1)(K-1)), as GENESIS's g07 forms it; the extra term of PROOF.md 7.4
    and 7.5 is 0;
  - the least window s for 1e-9 per divergence slot, every fork, under s <= K - 1 (7.5) and under
    s + K <= G + 1 as well (7.4);
  - the history bounds of GENESIS 8.1 at s_gen over a day and a year (cells), at each G.
P1 is the closed form Window.p1 for single values and Window.p1_curve (forward pass) for curves; the
script prints their largest relative difference at three windows.
Usage: python s01_terms.py > out_01_terms.txt
"""
import math

import numpy as np

from common_b import (EPS, H, K, REFERENCE_G, S, SCHEDULES, STATES, YEAR, U_at, Window, load_U,
                      p_of)

X_MAX = 72_001                    # P1 curve up to the largest G + 1 read from the curve
SPANS = {"1 day": 24 * H, "1 year": YEAR}


def least(values: np.ndarray, lo: int, hi: int):
    """The least index s in [lo, hi] with values[s] <= EPS, or None."""
    hit = np.nonzero(values[lo:hi + 1] <= EPS)[0]
    return int(hit[0]) + lo if hit.size else None


def fmt_least(v):
    return f"{v} slots ({v / H:.2f} h)" if v is not None else "none"


if __name__ == "__main__":
    print(f"K = {K}, s = {S}; schedules: " + "; ".join(f"{n}: G = {g}" for n, g, _ in SCHEDULES)
          + "; reference gaps: " + "; ".join(f"{n}: G = {g}" for n, g in REFERENCE_G))
    for name, xh, xa, d, (alpha, scale) in STATES:
        ph, pa = p_of(xh), p_of(xa)
        w = Window(pa, ph, d)
        u = load_U(alpha, d, scale)
        u1 = load_U(alpha, d + 1, scale)
        p1c = w.p1_curve(X_MAX)
        chk = max(abs(p1c[x] / w.p1(x) - 1) for x in (S, K - S, 36_000))
        p1s, us, near = w.p1(S), U_at(u, S - 1), w.p1(K - S)
        uk2, uk1 = U_at(u, K - 2), U_at(u1, K - 1)
        print(f"\n{name}: p_h = {ph:.6f}, p_a = {pa:.6f}, Delta = {d} "
              f"(forward pass against closed form at {S}, {K - S}, 36000: largest relative difference {chk:.1e})")
        print(f"  terms that do not read G: P1(s) = {p1s:.3e}; U(s - 1) = {us:.3e}; P1(K - s) = {near:.2e}; "
              f"U(K - 2) = {uk2:.2e}; U_{d + 1}(K - 1) = {uk1:.2e}")
        sv = np.arange(K)                                              # candidate windows s
        Us = np.where(sv >= 2, u[np.clip(sv - 2, 0, None)], 1.0)          # U(s - 1)
        nears = np.where(K - sv >= 1, p1c[np.clip(K - sv, 0, X_MAX)], 1.0)  # P1(K - s)
        for gname, G, _ in SCHEDULES + [(n, g, None) for n, g in REFERENCE_G]:
            far = w.p1(G + 1 - S)
            tot_a = us + near + far + uk2
            tot_b = us + far + uk1
            line = (f"  G = {G} [{gname}]: P1(G + 1 - s) = P1({G + 1 - S}) = {far:.1e}; extra term 0; "
                    f"every fork per divergence slot: (A) {tot_a:.3e}, (B) {tot_b:.3e}, total {min(tot_a, tot_b):.3e}")
            if G + 1 <= X_MAX:
                fars = np.where(G + 1 - sv >= 1, p1c[np.clip(G + 1 - sv, 0, X_MAX)], 1.0)
                tot = np.minimum(Us + nears + fars + uk2, Us + fars + uk1)
                l74 = least(tot, 2_000, K - 1)
                l73 = least(tot, 2_000, min(K - 1, G + 1 - K))
                line += (f"; least window for 1e-9, every fork: s <= K - 1 (7.5) {fmt_least(l74)}, "
                         f"s + K <= G + 1 (7.4, s <= {min(K - 1, G + 1 - K)}) {fmt_least(l73)}")
            print(line)
        # the history (GENESIS 8.1) at s_gen, cells of g slots, for each schedule's G
        g = np.arange(1, S + 1)
        P1 = lambda x: np.where(x >= 1, p1c[np.clip(x, 0, X_MAX)], 1.0)          # noqa: E731
        Ug = np.where(S - g >= 1, u[np.clip(S - g, 1, None) - 1], 1.0)          # U(s - g)
        for span_name, L in SPANS.items():
            cells = np.ceil(L / g)
            v1 = cells * P1(S - g + 1)
            parts = [f"no honest block <= {v1.min():.2e} (g = {g[np.argmin(v1)]})"]
            for gname, G, _ in SCHEDULES + [(n, gg, None) for n, gg in REFERENCE_G if gg + 2 <= X_MAX]:
                base = Ug + P1(G + 2 - S - g)
                vb = cells * base
                va = cells * (base + P1(K - S - g + 1))
                tot = min(va.min() + uk2, vb.min() + uk1)
                parts.append(f"G = {G}: every fork, cells {vb.min():.3e} (g = {g[np.argmin(vb)]}), total {min(1.0, tot):.3e}")
            print(f"  history of {span_name}: " + "; ".join(parts))
