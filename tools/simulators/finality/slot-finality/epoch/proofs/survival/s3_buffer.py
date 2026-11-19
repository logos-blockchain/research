"""The buffer w_B with the proved survival law (SURVIVAL.md, sections 8 and 9.3).

bound(w) = h * sum_{T >= w} Qhat(T) (Theorem 8.1), the sum taken slot by slot up to T_END and bounded by
Lemma 6.7 beyond it; w_B is the least w with bound(w) <= 1e-9. Beside it: the same with Q (no tie
argument, Corollary 6.2), with Q1 (the strict lead), and the review's w_B from the study's law
(out_08_buffer.txt of the review, read only). Part 2: the bound at two hours (the review's finding 4).
Part 3: w_B under the circuit's threshold: Qhat evaluated with the honest chance lowered by the
circuit's largest relative error, 0.0444 % (leadership 281; Lemma 6.8), and the factor h kept, because
2.3 bounds the chance of an honest block at s_0 by h only. Part 4: the instance of Proposition 9.3, in which an adversary reaches
the survival event with a chance of at least (1 - c) (Qhat(T) - Qhat(T_MAX)), against the study's law.
Usage: python s3_buffer.py > out_3_buffer.txt
"""
import math
import sys

import numpy as np

from sv_common import EPS, F, H, STATES, STUDY_SRC, chernoff, least_w, max_law, rates, study_params, survival_curves

sys.path.insert(0, STUDY_SRC)
from finality_sim.formation import branch_survival   # noqa: E402

T_END = 20 * H
DELTA_LOT = 4.44e-4           # largest relative error of the circuit's order-2 threshold, leadership 281
T_MAX = 35_000                # Proposition 9.3 needs T_MAX < K = 36,000 (latest #533)
N_NODES = 10 ** 9             # honest nodes of equal stake in the instance of Proposition 9.3


def hours(w):
    return f"{w:6d} slots ({w / H:5.2f} h)"


if __name__ == "__main__":
    print(f"1. w_B = the least w with h * sum_(T >= w) survival(T) <= {EPS:g}; slot by slot to T = {T_END} ({T_END // H} h), Lemma 6.7 beyond")
    curves = {}
    for key, label, xh, xa, d, old, old_line in STATES:
        h, a = rates(xh, xa)
        law = max_law(h, a, d)
        res = survival_curves(h, a, d, T_END, law=law, lower=True)
        th, rho, lam, C = chernoff(h, a, d)
        curves[key] = (h, a, d, res, C, lam, law)
        w_h, S_h, tail = least_w(h, res["Qhat"], d, C, lam)
        w_q, _, _ = least_w(h, res["Q"], d, C, lam)
        w_1, _, _ = least_w(h, res["Q1"], d, C, lam)
        print(f"   {label}: h = {h:.6f} | w_B(Qhat) = {hours(w_h)} | the review's w_B = {hours(old)} (its out_08 line {old_line}) | "
              f"change {w_h - old:+d} slots | w_B(Q) = {hours(w_q)} | w_B(Q1) = {hours(w_1)} | "
              f"bound at w_B {h * S_h[w_h]:.3e} | tail beyond {T_END // H} h {tail:.1e}")

    print("\n2. the bound at w = 2 h, h * sum_(T >= 7200) Qhat(T), against the review's figure from the study's law")
    for key, review in (("none", "7.081e-06 (out_08 line 7)"), ("late", "2.452e-04 (out_08 line 18)")):
        h, a, d, res, C, lam, _ = curves[key]
        _, S_h, _ = least_w(h, res["Qhat"], d, C, lam)
        print(f"   {[s[1] for s in STATES if s[0] == key][0]}: {h * S_h[2 * H]:.3e}; the review: {review}")

    print(f"\n3. w_B under the circuit's threshold: h * sum Qhat, Qhat at the honest chance h (1 - {DELTA_LOT}) and the coalition's a (Lemmas 2.3 and 6.8)")
    for key, label, xh, xa, d, old, _ in STATES:
        h, a, d, res, C, lam, _ = curves[key]
        w_h, _, _ = least_w(h, res["Qhat"], d, C, lam)
        h2 = h * (1 - DELTA_LOT)
        res2 = survival_curves(h2, a, d, T_END)
        th2, rho2, lam2, C2 = chernoff(h2, a, d)
        w2, _, _ = least_w(h, res2["Qhat"], d, C2, lam2)
        print(f"   {label}: {hours(w2)}, {w2 - w_h:+d} slots")

    print(f"\n4. Proposition 9.3: n = {N_NODES:.0e} honest nodes of equal stake, T_max = {T_MAX}: "
          f"c = (T_max + 1) d n p_n^2 / h^2; the adversary's chance >= (1 - c) (Qhat_low(T) - Qhat_up(T_max))")
    for key, label, xh, xa, d, old, _ in STATES:
        h, a, d, res, C, lam, _ = curves[key]
        fp, al = study_params(xh, xa)
        p_n = -math.expm1((xh / N_NODES) * math.log1p(-F))
        c = (T_MAX + 1) * d * N_NODES * p_n ** 2 / h ** 2
        cells = []
        for hr in (2, 3, 4):
            T = hr * H
            low = (1 - c) * (res["Qhat_low"][T] - res["Qhat"][T_MAX])
            st = branch_survival(fp, al, T, delta=d)
            cells.append(f"T = {hr} h: adversary >= {low:.4e}, study {st:.4e}, ratio {low / st:.4f}")
        print(f"   {label}: c = {c:.2e}, Qhat(T_max) = {res['Qhat'][T_MAX]:.1e} | " + " | ".join(cells))
