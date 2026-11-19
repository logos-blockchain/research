"""GENESIS.md, section 10.4: the states of the K row, against 30 % (the mapping of REVIEW.md 5.9).

- no disturbance: shares 0.7 and 0.3 of D, Delta = 10;
- first disturbance: the same shares, Delta = T_M = 15;
- second disturbance, after the inference corrects: D = 0.93 of the total, shares 0.63/0.93 and
  0.3/0.93, Delta = 10; before it corrects: D = the total, shares 0.63 and 0.3;
- third disturbance: D = the honest stake online, shares 1 and 0.3/0.7, Delta = 10.
For U the study's wait_curve takes the coalition's share of the active stake and a scale on both
rates: 0.93 before the correction, 1/0.7 for the third disturbance (its docstring). U_(Delta + 1) is the
same curve at a delay of Delta + 1.
Prints, per state: P1(s_gen) (6.2), U(s_gen - 1), P1(K - s) and P1(G + 1 - s) (6.3), U(K - 2) and
U_(Delta + 1)(K - 1) (7.2) for both K; the least windows for 1e-9 per divergence slot: without honest
blocks (least x with P1(x) <= 1e-9), every fork with the cases other than t = now (least s with
U(s - 1) + P1(G + 1 - s) <= 1e-9), and every fork in total at each K (s <= K - 1, the smaller of
U(s - 1) + P1(K - s) + P1(G + 1 - s) + U(K - 2) and U(s - 1) + P1(G + 1 - s) + U_(Delta + 1)(K - 1));
and P1(s_gen) with the honest chance lowered by the circuit's shortfall delta (A1).
Usage: python g07_states.py > out_07_states.txt
"""
import numpy as np

from common_g import EPS, GAP, H, K_CASES, S_GEN, U_at, Window, p_of, settle_cached, shortfall

STATES = [
    # name, honest share of D, coalition share of D, Delta, (alpha, scale) for U
    ("no disturbance", 0.7, 0.3, 10, (0.3, 1.0)),
    ("every block T_M late", 0.7, 0.3, 15, (0.3, 1.0)),
    ("a tenth of the honest stake offline, inference corrected", 0.63 / 0.93, 0.3 / 0.93, 10, (0.3 / 0.93, 1.0)),
    ("a tenth of the honest stake offline, before the correction", 0.63, 0.3, 10, (0.3 / 0.93, 0.93)),
    ("D equals the honest stake online", 1.0, 0.3 / 0.7, 10, (0.3, 1 / 0.7)),
]
T_MAX = 160_000


def first(values, lo):
    """The least index s >= lo with values[s] <= EPS, or None."""
    hit = np.nonzero(values[lo:] <= EPS)[0]
    return int(hit[0]) + lo if hit.size else None


if __name__ == "__main__":
    for name, xh, xa, d, (alpha, scale) in STATES:
        ph, pa = p_of(xh), p_of(xa)
        w = Window(pa, ph, d)
        p1c = w.p1_curve(GAP + 1)
        c = settle_cached(alpha, d, T_MAX, scale)
        c1 = settle_cached(alpha, d + 1, T_MAX, scale)
        s = np.arange(GAP + 2)
        U = np.where(s >= 2, c[np.clip(s - 2, 0, T_MAX - 1)], 1.0)            # U(s - 1)
        far = p1c[np.clip(GAP + 1 - s, 0, GAP + 1)]                           # P1(G + 1 - s)
        cells = U + far
        lp = first(p1c, 2_000)
        lc = first(cells[:T_MAX], 2_000)
        ks, tots = [], []
        for K in K_CASES.values():
            near = np.where(K - s >= 1, p1c[np.clip(K - s, 0, GAP + 1)], 1.0)  # P1(K - s)
            tot = np.minimum(cells + near + U_at(c, K - 2), cells + U_at(c1, K - 1))
            lk = first(tot[:K], 2_000)
            ks.append(f"K = {K}: P1(K - s) = {p1c[K - S_GEN]:.2e}, U(K - 2) = {U_at(c, K - 2):.2e}, "
                      f"U_{d + 1}(K - 1) = {U_at(c1, K - 1):.2e}")
            tots.append(f"total at K = {K}: " + (f"{lk} slots ({lk / H:.2f} h)" if lk else "none with s <= K - 1"))
        dl = shortfall(xh)
        low = Window(pa, ph * (1 - dl), d).p1(S_GEN)
        print(f"{name}: p_h = {ph:.6f}, p_a = {pa:.6f}, Delta = {d}")
        print(f"  P1(s_gen) = {w.p1(S_GEN):.3e} (forward pass {p1c[S_GEN]:.3e}); U(s_gen - 1) = {U_at(c, S_GEN - 1):.3e}; "
              f"P1(G + 1 - s) <= {p1c[GAP + 1 - S_GEN]:.1e}; " + "; ".join(ks))
        print(f"  least window for 1e-9 per divergence slot: without honest blocks {lp} slots ({lp / H:.2f} h); every fork, "
              f"cases other than t = now, {lc} slots ({lc / H:.2f} h); " + "; ".join(tots))
        print(f"  the circuit's shortfall: delta = {dl:.2e}; P1(s_gen) at p_h (1 - delta) = {low:.3e} "
              f"({100 * (low / w.p1(S_GEN) - 1):+.2f} %)")
