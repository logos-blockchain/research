"""PROOF.md, section 5: what a fork's own epoch state can be (not used by theorem 4.2).

(a) the inference (inference 77-87) with beta = num/den, run as printed in integers on random inputs,
    against the closed form D' = D((1 - beta) + beta N / (P f_hat)) of statement 5.2: the largest
    distance, and that the last division never sees a negative numerator;
(b) the floor D' >= (1 - beta) D - 1.002 for any count N >= 0;
(c) the deficit of statement 5.3: a fork X that shares H's blocks up to slot sigma_0 = c_e - u counts
    at least the slots H counts up to sigma_0; under the count model of REVIEW.md 7.3 (every won slot
    counted, independent slots of chance q = f_hat, the inference's fixed point), the ratio
    R = D_X / D_H of the next epoch is at least
        R_min = ((1 - beta) P f_hat + beta S0) / ((1 - beta) P f_hat + beta (S0 + n)),
    S0 ~ Bin(P - u + 1 - 359, q), n ~ Bin(u - 1 + 359, q) independent (the 359 slots before sigma_0 that
    an uncle referenced after sigma_0 can occupy are moved to n). Printed: E[R_min] to first order and its
    lower 1e-9 quantile, for u up to 2K - 2 - G, beta in {1/2, 2/3}, P in {54,000, 72,000}; beside them the
    coalition's share of D_X, 0.3 / R, and its chance per slot 1 - (1 - f)^(0.3 / R) (no disturbance);
(d) the nonce: the coalition's wins A in (sigma_0, c_e), Bin(u - 1, p_a) under H's states; every subset
    of them is a chain from D_Y with its own nonce, so a fork can choose among at least 2^A nonces:
    the mean of A, and the chance that A >= 16, 40, 64.
Usage: python t3_inference.py > out_3_inference.txt
"""
import math
import random
from fractions import Fraction

import numpy as np
from scipy import optimize, stats

from common_s import F, F_HAT, K, S, p_of

W_BACK = 359          # an uncle's slot is at least its referencer's slot - W f^-1 + 1 (protocol 330-332)


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def infer_int(D, N, P, num, den):
    tse_p = D * 1000
    expected = P * 33
    diff = expected - N * 1000
    err = tdiv(tse_p * diff, expected)
    corr = tdiv(num * err, den)
    z = tse_p - corr
    return max(tdiv(z, 1000), 1), z


def closed(D, N, P, num, den):
    """the closed form in exact rationals (f_hat = 33/1000)"""
    b = Fraction(num, den)
    return Fraction(D) * ((1 - b) + b * Fraction(1000 * N, 33 * P))


def part_a():
    print("(a) the inference in integers against the closed form D((1 - beta) + beta N/(P f_hat)), evaluated in exact rationals")
    rng = random.Random(7)
    for num, den in ((1, 2), (2, 3), (1, 1)):
        worst, neg = 0.0, 0
        for _ in range(200_000):
            P = rng.choice((54_000, 72_000, rng.randrange(1_000, 400_000)))
            D = rng.choice((rng.randrange(1, 10 ** 4), rng.randrange(1, 10 ** 12), rng.randrange(1, 10 ** 15)))
            N = rng.randrange(0, P + 1) if rng.random() < 0.3 else int(P * F_HAT * rng.uniform(0, 2))
            N = min(N, P)
            out, z = infer_int(D, N, P, num, den)
            neg += z < 0
            c = closed(D, N, P, num, den)
            if c >= 1:                                     # the max(., 1) clamp aside
                worst = max(worst, float(abs(out - c)))
        print(f"  beta = {num}/{den}: largest |D' - closed form| over 200,000 inputs = {worst:.6f}; "
              f"inputs with a negative numerator before the last division: {neg}")


def part_b():
    print("\n(b) the floor at N = 0: D' / D")
    for num, den in ((1, 2), (2, 3)):
        for D in (10 ** 6, 10 ** 12):
            out, _ = infer_int(D, 0, 54_000, num, den)
            print(f"  beta = {num}/{den}, D = {D}: D' = {out}, D'/D = {out / D:.6f} (1 - beta = {1 - num / den:.6f})")


def quantile_rmin(P, u, beta, q, eps=1e-9):
    a = (1 - beta) * P * F_HAT
    m0 = P - u + 1 - W_BACK
    m1 = u - 1 + W_BACK
    s0 = np.arange(0, m0 + 1)
    w0 = stats.binom.pmf(s0, m0, q)
    keep = w0 > 1e-30
    s0, w0 = s0[keep], w0[keep]

    def cdf(rho):                                          # P(R_min <= rho)
        thr = (1 - rho) * (a + beta * s0) / (rho * beta)
        return float(np.sum(w0 * stats.binom.sf(np.ceil(thr) - 1, m1, q)))
    lo, hi = 1e-3, 1.0
    if cdf(hi - 1e-12) < eps:
        return 1.0
    return optimize.brentq(lambda r: math.log(max(cdf(r), 1e-300)) - math.log(eps), lo, hi - 1e-12, xtol=1e-7)


def part_c():
    q = F_HAT
    pa0 = p_of(0.3)
    print("\n(c) the ratio R = D_X/D_H of the epoch after D_Y's, X with no block and no new uncle slot after sigma_0 = c_e - u "
          f"(q = f_hat = {q}; the no-disturbance coalition: 0.3 of D_H, p_a = {pa0:.6f})")
    for gname, G in (("(i) G = 52,199", S + K - 1), ("(ii) G = 54,000", 54_000)):
        umax = 2 * K - 2 - G
        for P in (54_000, 72_000):
            for num, den in ((1, 2), (2, 3)):
                beta = num / den
                rows = []
                for u in (2, 2_000, 6_000, 10_000, 14_000, umax):
                    span = 2 * K - 1 - G - u
                    mean = 1 - beta * (u - 1 + W_BACK) / P          # first order, E[S0 + n] = qP
                    r9 = quantile_rmin(P, u, beta, q)
                    share = 0.3 / r9
                    rows.append(f"u = {u} (own-state stretch {span}): E ~ {mean:.4f}, 1e-9 quantile {r9:.4f}, "
                                f"coalition {share:.3f} of D_X, p_a {p_of(share):.5f}")
                print(f"  {gname}, P = {P}, beta = {num}/{den}:")
                for r in rows:
                    print("    " + r)


def part_d():
    print("\n(d) the coalition's choice of the fork's nonce: A = its wins in (sigma_0, c_e) under H's states, M >= 2^A candidates")
    for name, xa in (("no disturbance (0.3 of D)", 0.3), ("D equals the honest stake online (0.3/0.7 of D)", 0.3 / 0.7)):
        pa = p_of(xa)
        for gname, G in (("(i)", S + K - 1), ("(ii)", 54_000)):
            umax = 2 * K - 2 - G
            out = []
            for u in (2_000, 6_000, 10_000, umax):
                m = u - 1
                out.append(f"u = {u}: E[A] = {m * pa:.1f}, P(A >= 16) = {stats.binom.sf(15, m, pa):.3f}, "
                           f"P(A >= 40) = {stats.binom.sf(39, m, pa):.3f}, P(A >= 64) = {stats.binom.sf(63, m, pa):.3f}")
            print(f"  {name}, {gname}: " + "; ".join(out))
        print(f"  {name}: E[A] reaches 16, 40, 64 at u = " +
              ", ".join(str(1 + math.ceil(b / pa)) for b in (16, 40, 64)))


if __name__ == "__main__":
    part_a()
    part_b()
    part_c()
    part_d()
