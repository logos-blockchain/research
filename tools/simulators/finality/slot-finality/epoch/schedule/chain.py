"""The stake inference's noise and the floor premise, by exact iteration of a Markov chain (SCHEDULE.md, 4).

Model (REVIEW.md 7.3): over a window of P slots the count of occupied slots is
    N ~ Binomial(P, 1 - (1 - f)^(S / D)),
for the stake S that builds and the inferred stake D. The rule with learning rate beta, in closed form
(REVIEW.md 7.2, rounding below one unit of stake ignored), is
    D' = D * ((1 - beta) + beta * N / (P * f_hat)),
where f_hat is the rate of occupied slots the rule settles at: 0.033 for the rule the specification
prints (f truncated to thousandths), 1/30 for an exact rule (logos-lips #529). The chain runs on a grid
of x = D / S from the fixed point to its stationary law. Prints:
  1. with beta = 1, one step from the fixed point, the windows at which P(S/D' > 1.094) <= 1e-9: the
     first window, and the window from which it holds for every longer one (the tail saw-tooths,
     because N is an integer);
  2. the stationary P(S/D > 1.094) and the sd of D/S, by window, learning rate and rule;
  3. the stationary mean chance that fewer than 689 blocks follow a block within K = 36,000 slots,
     every block 15 slots late (Finality Floor's formula at the current D/S), and the largest floor
     whose mean chance is at most 1e-9.
1.094 is the largest true active stake over the inferred stake at which K = 10 hours holds 30 % at
15 s (RFC-533). Usage: python chain.py > out_chain.txt   (about 20 minutes)
"""
import math

import numpy as np
from scipy.stats import binom

F = 1 / 30
LIMIT = 1.094
K, PHI, T_M = 36000, 689, 15
RULES = (("specification (f_hat = 0.033)", 0.033), ("exact (f_hat = 1/30)", F))


def r_star(f_hat):
    """S / D at the fixed point."""
    return math.log1p(-f_hat) / math.log1p(-F)


def one_step_tail(P, f_hat=0.033):
    return float(binom.cdf(math.ceil(r_star(f_hat) * P * f_hat / LIMIT) - 1, P, f_hat))


def stationary(P, beta, f_hat, n_grid=6000, lo=0.80, hi=1.25, iters=400):
    xs = np.linspace(lo, hi, n_grid)
    dx = xs[1] - xs[0]
    pi = np.zeros(n_grid)
    pi[np.argmin(abs(xs - 1 / r_star(f_hat)))] = 1.0
    T = np.zeros((n_grid, n_grid))
    for i, x in enumerate(xs):
        q = -math.expm1(math.log1p(-F) / x)
        mean, sd = P * q, math.sqrt(P * q * (1 - q))
        ns = np.arange(max(0, int(mean - 12 * sd)), int(mean + 12 * sd) + 1)
        xp = x * ((1 - beta) + beta * ns / (P * f_hat))
        j = np.clip(np.rint((xp - lo) / dx).astype(int), 0, n_grid - 1)
        np.add.at(T[i], j, binom.pmf(ns, P, q))
    for _ in range(iters):
        pi = pi @ T
    return xs, pi


def mean_miss(n, xs, pi):
    m = pi > 1e-16
    p = -np.expm1(np.log1p(-F) / xs[m])
    return float((pi[m] * binom.cdf(n - 1, K - n * T_M, p)).sum())


def main():
    print("1. beta = 1, one step from the fixed point (specification's rule): P(S/D' > 1.094) by window")
    ok = [P for P in range(100_000, 135_001) if one_step_tail(P) <= 1e-9]
    bad = [P for P in range(100_000, 135_001) if one_step_tail(P) > 1e-9]
    print(f"   first window with a tail <= 1e-9: {ok[0]} slots ({ok[0] / 3600:.2f} h); holds for every window from "
          f"{bad[-1] + 1} slots ({(bad[-1] + 1) / 3600:.2f} h), scanned to 135,000")
    for P in (54000, 72000, 108000, 216000):
        print(f"   window {P / 3600:5.1f} h: {one_step_tail(P):.3e}")
    print()
    print("2. stationary law: P(S/D > 1.094) per epoch and the sd of D/S")
    laws = {}
    for P in (54000, 72000):
        for name, fh in RULES:
            for beta in (1.0, 0.75, 2 / 3, 0.6, 0.5):
                xs, pi = stationary(P, beta, fh)
                laws[(P, fh, beta)] = (xs, pi)
                mean = (pi * xs).sum()
                sd = math.sqrt((pi * (xs - mean) ** 2).sum()) / mean
                print(f"   window {P / 3600:.0f} h, {name}, beta {beta:.4f}: {pi[(1 / xs) > LIMIT].sum():.3e} | sd {100 * sd:.3f} %",
                      flush=True)
    print()
    print(f"3. floor premise: mean chance of fewer than {PHI} blocks within K, and the largest floor at 1e-9")
    for name, fh in RULES:
        p_fix = -math.expm1(math.log1p(-F) * r_star(fh))
        n = PHI
        while binom.cdf(n - 1, K - n * T_M, p_fix) > 1e-9:
            n -= 1
        print(f"   {name}, at the fixed point, no noise: {binom.cdf(PHI - 1, K - PHI * T_M, p_fix):.3e}; floor {n}")
        for P, beta in ((72000, 2 / 3), (54000, 0.5), (54000, 1.0), (72000, 1.0)):
            xs, pi = laws[(P, fh, beta)]
            n = PHI
            while mean_miss(n, xs, pi) > 1e-9:
                n -= 1
            print(f"   {name}, window {P / 3600:.0f} h, beta {beta:.4f}: {mean_miss(PHI, xs, pi):.3e}; floor {n}")


if __name__ == "__main__":
    main()
