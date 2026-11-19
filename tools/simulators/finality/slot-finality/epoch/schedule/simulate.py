"""Simulations of the stake inference with a learning rate below 1 (SCHEDULE.md, 4).

By default the schedule of 40 hours: a window of 2K = 72,000 slots, phase 3 of 20 hours. The settings
WINDOW (slots), EPOCH_H and GAP_H (hours) and BETAS (comma-separated ratios) change them.

Two forms of the update, both in integers:
  branch  the algorithm that cryptarchia-total-stake-inference.md prints on the branch
          Bedrock-RFC-Shorter-Epoch, with beta the ratio of the integers beta.num and beta.den:
              f_p = 33; tse_p = D * 1000; expected = PERIOD * f_p
              diff = expected - N * 1000; error = (tse_p * diff) / expected
              correction = (beta.num * error) / beta.den; D' = max((tse_p - correction) / 1000, 1)
          with division that truncates toward zero. It settles where slots are occupied at 0.033.
  529     the algorithm of logos-lips #529 (exact, one division), beta = beta_n / beta_d, f = 1 / 30:
              D' = min(max(floor(D * ((beta_d - beta_n) * f_n * PERIOD + beta_n * f_d * N)
                                 / (beta_d * f_n * PERIOD)), 1), 2^64 - 1)
          It settles where slots are occupied at f.
N, the occupied slots of the window, is Binomial(PERIOD, 1 - (1 - f)^(S / D)) for the stake S that
builds (review 7.3: every win counted). S is 10^8 units: int64 holds every intermediate, and the
rounding of the rule is below one unit (review 7.2).

Parts:
  A. steady state: sd of D/S and the share of epochs with S/D above several levels, by plain
     Monte Carlo, beside the exact Markov chain of chain.py;
  B. the share of epochs with S/D > 1.094 (the limit at which K holds 30 % at 15 s), by importance
     sampling along the most likely path, each run weighted by its likelihood ratio;
  C. the response to a step change of S, in hours, beside today's schedule;
  D. a deflation: 30 % of the total active stake withholds every block for several windows.
Usage: python simulate.py <branch|529> [A|B|C|D ...] > out_simulate_<rule>_<window in hours>.txt
"""
import math
import os
import sys
import time
from fractions import Fraction

import numpy as np
from scipy.stats import binom

F = Fraction(1, 30)
FF = float(F)
S0 = 10 ** 8
K = 36000
H = 3600
LIMIT = 1.094
P30 = int(os.environ.get("WINDOW", 2 * K))       # the window in slots
EPOCH_H = int(os.environ.get("EPOCH_H", 40))     # the epoch in hours
GAP_H = int(os.environ.get("GAP_H", 20))         # phase 3 in hours
RNG = np.random.default_rng(20261118)
RULE = sys.argv[1] if len(sys.argv) > 1 else "branch"
F_HAT = 0.033 if RULE == "branch" else FF          # the rate of occupied slots the rule settles at
X_STAR = math.log1p(-FF) / math.log1p(-F_HAT)       # D / S at the fixed point
BETAS = {"branch": (1.0, 2 / 3, 0.5), "529": (Fraction(1), Fraction(2, 3), Fraction(1, 2))}[RULE]
if os.environ.get("BETAS"):
    BETAS = tuple((Fraction(b) if RULE == "529" else float(Fraction(b))) for b in os.environ["BETAS"].split(","))


def tdiv(a, b):
    return np.sign(a) * (np.abs(a) // b)


def step(D, N, P, beta):
    if RULE == "branch":
        b = Fraction(beta).limit_denominator(10 ** 6)
        tse_p = D * 1000
        error = tdiv(tse_p * (P * 33 - N * 1000), P * 33)
        return np.maximum(tdiv(tse_p - tdiv(b.numerator * error, b.denominator), 1000), 1)
    b = Fraction(beta)
    num = D * ((b.denominator - b.numerator) * F.numerator * P + b.numerator * F.denominator * N)
    return np.clip(num // (b.denominator * F.numerator * P), 1, 2 ** 63 - 1)


def q_of(D, S):
    return -np.expm1(np.log1p(-FF) * (S / D))


def draw(D, S, P):
    return RNG.binomial(P, q_of(D, S))


def settled(M, P, beta, S=S0, epochs=30):
    D = np.full(M, round(S * X_STAR), dtype=np.int64)
    for _ in range(epochs):
        D = step(D, draw(D, S, P), P, beta)
    return D


def part_a(M=400_000, keep=40):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chain
    print(f"A. [{RULE}] steady state at a window of {P30} slots ({P30 / H:g} h): {M} chains settled 30 epochs, then {keep} epochs kept")
    for beta in BETAS:
        D = settled(M, P30, beta)
        samples = []
        for _ in range(keep):
            D = step(D, draw(D, S0, P30), P30, beta)
            samples.append(D.copy())
        x = np.concatenate(samples) / S0
        xs, pi = chain.stationary(P30, float(beta), F_HAT)
        mc_mean, ch_mean = x.mean(), (pi * xs).sum()
        sd_c = math.sqrt((pi * (xs - ch_mean) ** 2).sum()) / ch_mean
        row = [f"beta {beta}: mean D/S {mc_mean:.5f} (chain {ch_mean:.5f}), sd {100 * x.std() / mc_mean:.3f} % (chain {100 * sd_c:.3f} %)"]
        for lv in (1.03, 1.04, 1.05, 1.06, LIMIT):
            row.append(f"P(S/D > {lv}) {float((1 / x > lv).mean()):.3e} (chain {float(pi[(1 / xs) > lv].sum()):.3e})")
        print("   " + " | ".join(row))


def part_b(M=1_000_000, tilt_steps=6, batches=4):
    print(f"B. [{RULE}] P(S/D > {LIMIT}) at a window of {P30 / H:g} h by importance sampling: {batches} batches of {M} runs")
    sigma1 = math.sqrt((1 - F_HAT) / (P30 * F_HAT))
    target = math.log(X_STAR * LIMIT)
    c = (-math.log1p(-FF)) * (1 - F_HAT) / (F_HAT * X_STAR)
    for beta in BETAS:
        bf = float(beta)
        a = 1 - bf * c
        w2 = sum(a ** (2 * j) for j in range(tilt_steps))
        z = [target * a ** j / (bf * sigma1 * w2) for j in range(tilt_steps)][::-1]
        est = []
        for _ in range(batches):
            D = settled(M, P30, beta)
            logw = np.zeros(M)
            for zj in z:
                q = q_of(D, S0)
                qt = np.clip(q - zj * np.sqrt(q * (1 - q) / P30), 1e-9, 1 - 1e-9)
                N = RNG.binomial(P30, qt)
                logw += binom.logpmf(N, P30, q) - binom.logpmf(N, P30, qt)
                D = step(D, N, P30, beta)
            est.append(float(np.mean(np.where(S0 / D > LIMIT, np.exp(logw), 0.0))))
        e = np.array(est)
        print(f"   beta {beta}: {e.mean():.3e} (batches {', '.join(f'{v:.2e}' for v in e)}; relative sd of the mean "
              f"{e.std(ddof=1) / e.mean() / math.sqrt(batches):.1%})")


def part_c(M=200_000, beta_low=None):
    beta_low = beta_low or BETAS[1]
    print(f"C. [{RULE}] response to a step change of the stake that builds; the change falls just after a cut-off. "
          "Mean of |D/S - fixed point| / fixed point (99th percentile) by hours after the change")
    cases = ((f"{EPOCH_H} h, beta {beta_low}", P30, beta_low, EPOCH_H * H, GAP_H * H), (f"{EPOCH_H} h, beta 1", P30, BETAS[0], EPOCH_H * H, GAP_H * H),
             ("today, 180 h, beta 1", 6 * 64800, BETAS[0], 180 * H, 72 * H))
    for factor in (0.5, 0.9, 1.1, 2.0):
        print(f"   stake that builds times {factor}:")
        for name, P, beta, E, L3 in cases:
            D = settled(M, P, beta, epochs=20)
            S1 = round(S0 * factor)
            out = [f"0 h {np.mean(np.abs(D / S1 - X_STAR) / X_STAR):.3f}"]
            t = E + L3
            for _ in range(5):
                D = step(D, draw(D, S1, P), P, beta)
                err = np.abs(D / S1 - X_STAR) / X_STAR
                out.append(f"{t / H:.0f} h {err.mean():.4f} ({np.quantile(err, 0.99):.4f})")
                t += E
            print(f"     {name}: " + ", ".join(out))


def part_d(M=200_000, windows=6, beta_low=None):
    beta_low = beta_low or BETAS[1]
    print(f"D. [{RULE}] deflation: 30 % of the total active stake withholds every block; D over the honest stake after each window")
    for name, P, beta in ((f"{EPOCH_H} h, beta {beta_low}", P30, beta_low), (f"{EPOCH_H} h, beta 1", P30, BETAS[0]), ("today, 180 h, beta 1", 6 * 64800, BETAS[0])):
        D = settled(M, P, beta, epochs=20)
        honest = round(0.7 * S0)
        out = [f"start {np.mean(D / honest):.3f}"]
        for n in range(windows):
            D = step(D, draw(D, honest, P), P, beta)
            out.append(f"{n + 1}: {np.mean(D / honest):.3f}")
        lost = -math.expm1(0.3 * math.log1p(-FF)) * P
        print(f"   {name}: " + ", ".join(out) + f"   (wins given up per window {lost:.0f}; the fixed point is {X_STAR:.4f})")


if __name__ == "__main__":
    for p in sys.argv[2:] or ["A", "B", "C", "D"]:
        t0 = time.time()
        {"A": part_a, "B": part_b, "C": part_c, "D": part_d}[p]()
        print(f"   ({time.time() - t0:.0f} s)")
