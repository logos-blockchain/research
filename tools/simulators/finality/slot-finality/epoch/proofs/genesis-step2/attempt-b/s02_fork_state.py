"""PROOF.md, 4.2 and 4.3: how far a fork's own epoch state can differ from H's in the crossing case.

None of these numbers enters a bound of PROOF.md (5.4 puts the case inside E_r*); they size what a
direct treatment of the crossing case would have had to bound.

(a) The inference as printed (inference 77-87, beta = num/den) against its closed form
    D' = D((1 - beta) + beta N / (PERIOD f_hat)), f_hat = 33/1000, on random inputs (statement 4.2).
(b) Per schedule: the free part of the observation window, at most 2K - G - 3 slots after D_Y
    (statement 4.1 (4)); the ratio D_X / D_H of the next epoch's inferred stake when the fork adds no
    occupied slot in the free part: at the means (N_H = PERIOD f_hat, the inference's fixed point,
    REVIEW.md 7.4), and with the shared count at its 1e-9 lower quantile and H's count in the free part
    at its 1e-9 upper quantile; the coalition's share of D_X, 0.3 D_H / D_X, and its chance per slot;
    the coalition's expected wins in the free part (the fork's nonce can take 2^wins values).
Usage: python s02_fork_state.py > out_02_fork_state.txt
"""
import math
import random
from fractions import Fraction

from scipy import stats

from common_b import F, F_HAT, K, SCHEDULES

BETAS = (Fraction(1, 2), Fraction(2, 3))
ALPHA = 0.3


def trunc_div(a: int, b: int) -> int:
    """Integer division that truncates toward zero, as Rust's i128 division does."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def infer_printed(D: int, N: int, P: int, beta: Fraction) -> int:
    """inference 77-87 with PRECISION = 1000 and f_p = truncate(f * 1000) = 33."""
    f_p = 33
    tse_p = D * 1000
    measured = N * 1000
    expected = P * f_p
    diff = expected - measured
    err = trunc_div(tse_p * diff, expected)
    corr = trunc_div(beta.numerator * err, beta.denominator)
    return max(trunc_div(tse_p - corr, 1000), 1)


def infer_closed(D: float, N: int, P: int, beta: Fraction) -> float:
    b = float(beta)
    return D * ((1 - b) + b * N / (P * F_HAT))


if __name__ == "__main__":
    rng = random.Random(5)
    worst = {b: 0.0 for b in BETAS}
    for _ in range(200_000):
        P = rng.choice((18_000, 36_000, 54_000, 72_000))
        D = rng.randint(10 ** 3, 10 ** 12)
        N = rng.randint(0, P)
        for b in BETAS:
            v = infer_printed(D, N, P, b)
            c = infer_closed(D, N, P, b)
            if c >= 1:
                worst[b] = max(worst[b], abs(v - c))
    print("(a) the inference as printed against D((1 - beta) + beta N / (PERIOD f_hat)), 200,000 random inputs "
          "with D in [1e3, 1e12]: largest distance " + ", ".join(f"beta = {b}: {worst[b]:.4f}" for b in BETAS))
    pa = -math.expm1(ALPHA * math.log1p(-F))
    print(f"\n(b) K = {K}; the coalition's chance per slot under H's states p_a = {pa:.6f}")
    cases = []
    for name, G, period in SCHEDULES:
        for P in ((period,) if period else (54_000, 72_000)):
            cases.append((name, G, P))
    for name, G, P in cases:
        free = 2 * K - G - 3
        shared = P - free
        lo0 = stats.binom.ppf(1e-9, shared, F_HAT)          # 1e-9 lower quantile of the shared count
        hi_free = stats.binom.isf(1e-9, free, F_HAT)        # 1e-9 upper quantile of H's count in the free part
        wins = free * pa
        print(f"  {name}, G = {G}, PERIOD = {P}: free part at most {free} slots, shared part at least {shared} "
              f"({100 * shared / P:.1f} % of the window); the coalition's expected wins in the free part {wins:.0f} "
              f"(the fork's nonce can take up to 2^{wins:.0f} values)")
        for b in BETAS:
            bf = float(b)
            mean_ratio = ((1 - bf) + bf * shared / P) / 1.0
            x_lo = (1 - bf) + bf * lo0 / (P * F_HAT)
            h_hi = (1 - bf) + bf * (lo0 + hi_free) / (P * F_HAT)
            q_ratio = x_lo / h_hi
            for label, r in (("at the means", mean_ratio), ("at the 1e-9 quantiles", q_ratio)):
                share = ALPHA / r
                p_x = -math.expm1(share * math.log1p(-F))
                print(f"    beta = {b}, {label}: D_X / D_H >= {r:.4f}; the coalition's share of D_X <= {share:.4f}, "
                      f"its chance per slot <= {p_x:.6f} ({p_x / pa:.3f} times p_a)")
