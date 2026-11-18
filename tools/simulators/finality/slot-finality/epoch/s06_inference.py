"""The noise of the stake inference by the length of its observation window, and what it costs the
finality floor (REVIEW.md, section 7).

Part 1 runs the update rule as cryptarchia-total-stake-inference.md prints it (lines 68-88 on the
10-hour branch), in integers with division that truncates toward zero, and compares it with the
closed form D' = D N / (P f^), f^ = 33/1000 (statement 7.2).
Part 2 gives the fixed point and the one-step mean and variance from the binomial law
(statement 7.4), and the standard deviation by window length (7.5).
Part 3 iterates the rule to its stationary law by sampling (7.4).
Part 4 gives the chance that the whole stake misses the floor at K, and the floor that the
specification's derivation returns, when the lottery runs at the rate the inference sets, noise
included (7.6).
Part 5 gives the chance per epoch that the noise alone puts the true active stake further above the
inferred stake than the limits RFC-533 and RFC-532 state for a delay of 15 s (7.7). A chance below
the range of double precision is summed term by term in log space.
Part 6 gives the wins a coalition gives up to deflate the inference (7.8).
Usage: python s06_inference.py > out_06_inference.txt
"""
import math
import random
from fractions import Fraction

import numpy as np
from scipy.special import gammaln
from scipy.stats import binom

from common import CASES, F, H, PERIOD, T_M, U, p_of

PRECISION = 1000          # `const PRECISION: u64 = 1e3`
BETA = 1.0                # learning rate, Parameters and variables
F_HAT = Fraction(33, 1000)  # truncate(f * PRECISION) / PRECISION


def tdiv(a: int, b: int) -> int:
    """Integer division that truncates toward zero, as on i128."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def total_stake_inference(density: int, total_stake_estimate: int, period: int) -> int:
    """The specification's algorithm; `density` stands for density_over_slots(tip, epoch_slot, PERIOD)."""
    beta_p = int(BETA * PRECISION)
    f_p = int(F * PRECISION)
    tse_p = total_stake_estimate * PRECISION
    measured_density_p = density * PRECISION
    expected_density_p = period * f_p
    density_diff_p = expected_density_p - measured_density_p
    slot_activation_error_p = tdiv(tse_p * density_diff_p, expected_density_p)
    correction_p = tdiv(beta_p * slot_activation_error_p, PRECISION)
    new_total_stake_estimate = tdiv(tse_p - correction_p, PRECISION)
    return max(new_total_stake_estimate, 1)


def rate(r):
    """Chance per slot that a slot is occupied when the stake that builds is r times the inferred stake."""
    return -np.expm1(r * math.log1p(-F))


def miss(n, K, r):
    """P(fewer than n blocks in K slots) at the rate of r, every block T_M late (blocks_short)."""
    m = K - n * T_M
    return binom.cdf(n - 1, m, rate(r))


def noise_average(n, K, period, f_hat, r_star):
    """E over N ~ Bin(P, f^) of miss(n, K, r* P f^ / N): one step of the rule from its fixed point."""
    mean = period * f_hat
    sd = math.sqrt(period * f_hat * (1 - f_hat))
    ns = np.arange(max(1, int(mean - 14 * sd)), int(mean + 14 * sd) + 1)
    w = binom.pmf(ns, period, f_hat)
    return float(np.sum(w * miss(n, K, r_star * mean / ns)))


def lower_tail(k, n, p):
    """P(Bin(n, p) <= k) as text; summed in log space when it is below the range of double precision."""
    v = float(binom.cdf(k, n, p))
    if v > 0:
        return f"{v:.3e}"
    i = np.arange(0, k + 1, dtype=np.float64)
    terms = gammaln(n + 1.0) - gammaln(i + 1.0) - gammaln(n - i + 1.0) + i * math.log(p) + (n - i) * math.log1p(-p)
    top = terms.max()
    log10v = (top + math.log(np.exp(terms - top).sum())) / math.log(10)
    e = math.floor(log10v)
    return f"{10 ** (log10v - e):.3f}e{e}"


def floor_with_noise(K, period, f_hat, r_star, eps=1e-9):
    lo, hi = 0, K // (T_M + 1) + 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if noise_average(mid, K, period, f_hat, r_star) <= eps:
            lo = mid
        else:
            hi = mid
    return lo


if __name__ == "__main__":
    f_hat = float(F_HAT)
    r_star = math.log1p(-f_hat) / math.log1p(-F)

    print("1. the update rule as printed, against D' = D N / (P f^), f^ = 33/1000")
    rnd = random.Random(94)
    worst = Fraction(0)
    for _ in range(200_000):
        period = rnd.choice((PERIOD, 3 * U, U, 36_000, 1000, 97))
        expected = period * 33                     # in thousandths of a slot
        D = rnd.choice((rnd.randrange(1, 10 ** 4), rnd.randrange(1, 10 ** 12), rnd.randrange(1, 10 ** 19)))
        N = rnd.randrange(0, min(period, 3 * expected // 1000 + 2) + 1)
        got = total_stake_inference(N, D, period)
        closed = Fraction(D * N * 1000, expected)
        if closed >= 1:
            worst = max(worst, abs(got - closed))
            assert closed - Fraction(1001, 1000) < got <= closed + Fraction(1, 1000)
        else:
            assert got == 1
    print(f"   200000 random (D, N, P): D N/(P f^) - 1.001 < D' <= D N/(P f^) + 0.001 whenever D N/(P f^) >= 1, and D' = 1 below; largest gap {float(worst):.6f}")
    print(f"   expected_density_p / PRECISION at PERIOD = {PERIOD}: {PERIOD * 33 / 1000:.1f} occupied slots; f^ = {f_hat}")

    print("\n2. the fixed point and one step of the rule")
    print(f"   r* = ln(1 - f^)/ln(1 - f) = {r_star:.6f}: the rule settles where the stake that builds is r* of the inferred stake,")
    print(f"   so the inferred stake is {100 * (1 / r_star - 1):.3f} % above it and slots are occupied at f^ = {f_hat}, {100 * (1 - f_hat / F):.2f} % below f")
    for period in (PERIOD, U):
        for q in (f_hat, F, 0.02):
            ns = np.arange(0, period + 1)
            w = binom.pmf(ns, period, q)
            ratio = ns / (period * f_hat)
            mean = float(np.sum(w * ratio))
            var = float(np.sum(w * (ratio - mean) ** 2))
            print(f"   P = {period:6d}, q = {q:.5f}: E[D'/D] = {mean:.8f} (q/f^ = {q / f_hat:.8f}); "
                  f"Var[D'/D] = {var:.6e} (q(1-q)/(P f^2) = {q * (1 - q) / (period * f_hat ** 2):.6e})")
    print("   standard deviation of D'/D at the fixed point, sqrt((1 - f^)/(P f^)), by window length:")
    print("   window (h) | slots | expected occupied slots | sd, f^ = 0.033 | sd, f = 1/30 exact | 1/sqrt(120 h) (the earlier study)")
    windows = (108, 72, 54, 36, 27, 18, 14.2, 10)
    for hours in windows:
        P = int(round(hours * H))
        print(f"   {hours:10.1f} | {P:6d} | {P * f_hat:9.1f} | {100 * math.sqrt((1 - f_hat) / (P * f_hat)):.3f} % | "
              f"{100 * math.sqrt((1 - F) / (P * F)):.3f} % | {100 / math.sqrt(120 * hours):.3f} %")

    print("\n3. the rule iterated: r' = r P f^ / N, N ~ Bin(P, 1 - (1 - f)^r); 200000 chains, 40 epochs, the last 30 kept")
    rng = np.random.default_rng(94)
    for hours in (108, 54, 18, 10):
        P = int(round(hours * H))
        r = np.full(200_000, r_star)
        kept = []
        for epoch in range(40):
            n = rng.binomial(P, rate(r))
            r = r * P * f_hat / n
            if epoch >= 10:
                kept.append(r / r_star)
        kept = np.concatenate(kept)
        print(f"   window {hours:5.1f} h: mean of r/r* = {kept.mean():.6f}, sd = {100 * kept.std():.3f} % "
              f"(one step from the fixed point: {100 * math.sqrt((1 - f_hat) / (P * f_hat)):.3f} %)")

    print("\n4. the floor and the rate the inference sets")
    for name, (K, phi) in CASES.items():
        print(f"   {name}: K = {K}, phi = {phi}")
        print(f"     premise of Finality Floor, rate f: P(fewer than phi blocks in K) = {float(miss(phi, K, 1.0)):.3e}")
        print(f"     at the fixed point, rate f^, no noise: {float(miss(phi, K, r_star)):.3e}; the derivation at that rate gives "
              f"{max(n for n in range(phi - 40, phi + 1) if float(miss(n, K, r_star)) <= 1e-9)}")
        print(f"     an inferred stake 2 % above the stake that builds: {float(miss(phi, K, 1 / 1.02)):.3e}")
        print("     window (h) | P(miss) with noise, rule as printed | floor at 1e-9 | P(miss) with noise, rule computing with f exactly | floor at 1e-9")
        for hours in windows:
            P = int(round(hours * H))
            a = noise_average(phi, K, P, f_hat, r_star)
            fa = floor_with_noise(K, P, f_hat, r_star)
            b = noise_average(phi, K, P, F, 1.0)
            fb = floor_with_noise(K, P, F, 1.0)
            print(f"     {hours:10.1f} | {a:.3e} | {fa:5d} ({fa - phi:+d}) | {b:.3e} | {fb:5d} ({fb - phi:+d})")

    print("\n5. the chance per epoch that noise alone leaves the true active stake above a limit times the inferred stake")
    print("   (one step from the fixed point; limits at 15 s against 30 %: 1.094 at 10 h, RFC-533 line 61; 1.593 at 18 h, RFC-532 line 74)")
    print("   window (h) | P(true / inferred > 1.094) | P(true / inferred > 1.593)")
    for hours in windows:
        P = int(round(hours * H))
        cells = []
        for limit in (1.094, 1.593):
            # r' = r* P f^ / N > limit  <=>  N < r* P f^ / limit
            bound = r_star * P * f_hat / limit
            cells.append(lower_tail(math.ceil(bound) - 1, P, f_hat))
        print(f"   {hours:10.1f} | " + " | ".join(cells))

    print("\n6. blocks a coalition of 30 % gives up to deflate the inference: its wins of one window, (1 - (1 - f)^0.3) P")
    for hours in windows:
        P = int(round(hours * H))
        print(f"   window {hours:5.1f} h: {p_of(0.3) * P:7.0f} wins of 30 %; {p_of(1 / 3) * P:7.0f} of a third")
