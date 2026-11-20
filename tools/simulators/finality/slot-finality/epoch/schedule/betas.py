"""The learning rate beta of the stake inference, for the constructions of CONSTRUCTIONS.md (4 and 5).

Windows: 3K = 108,000 slots (30 h), the window of 3K + 3K; 3.5K = 126,000 (35 h), that of 2.5K + K + 2K;
4K = 144,000 (40 h), that of 2K + 2K + 2K. Learning rates: 1, 7/8, 5/6, 4/5, 3/4, 2/3. Two forms of the rule,
as in chain.py and simulate.py: as the specification prints it (f truncated to 0.033) and exact (#529).
  1. The stationary chance per epoch that S/D passes 1.094 and the sd of D/S (chain.py's chain), and the floor
     premise: the mean chance that fewer than 689 blocks follow a block within K, every block 15 slots late,
     and the largest floor whose mean chance is at most 1e-9 (chain.py's mean_miss).
  2. The response to a step change of the stake that builds, just after a cut-off, by the rule in integers
     (simulate.py's two forms, 200,000 runs, 20 epochs to settle): the mean of |D/S - fixed point| / fixed
     point after each of the first four corrections, and, for a rise, the share of runs with S/D above 1.094.
     The k-th correction is first used L3 + k E after the change.
  3. A deflation (as simulate.py part D): 30 % of the total active stake withholds every block; the mean of
     D over the honest stake after each window, and the wins it gives up per window.
  4. A stake that builds and grows steadily, by the mean of the rule with no noise and no rounding, in two
     models. New stake: a note leads only from the epoch after the one whose first slot finds it in the
     note set (protocol 173), so the stake that builds is constant within an epoch and rises at each
     boundary. Coming online: stake that is already eligible joins slot by slot, the count of a window sums
     the chance of each slot under the stake of that slot, and the largest S/D of an epoch is at its end.
     Printed: at 1 % a day, the largest S/D of an epoch over S/D at the fixed point, and that ratio as
     hours of growth (the lag of D); and the largest growth a day at which that S/D stays at most 1.094.
Usage: python betas.py > out_betas.txt   (part 1 runs in 7 processes; about 10 minutes)
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import math                                   # noqa: E402
import sys                                    # noqa: E402
import time                                   # noqa: E402
from concurrent.futures import ProcessPoolExecutor   # noqa: E402
from fractions import Fraction                # noqa: E402

import numpy as np                            # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import chain                                  # noqa: E402

F = Fraction(1, 30)
FF = float(F)
K, PHI, H = 36000, 689, 3600
LIMIT = 1.094
S0 = 10 ** 8
BETAS = (Fraction(1), Fraction(7, 8), Fraction(5, 6), Fraction(4, 5), Fraction(3, 4), Fraction(2, 3))
RULES = (("printed", 0.033), ("exact", FF))
WINDOWS = (3 * K, 7 * K // 2, 4 * K)
CONSTRUCTIONS = (   # (label, E, L3, window)
    ("3K + 3K", 6 * K, 3 * K, 3 * K),
    ("2K + 2K + 2K", 6 * K, 2 * K, 4 * K),
    ("2.5K + K + 2K", 11 * K // 2, 2 * K, 7 * K // 2),
)
TODAY = ("today, 54 + 54 + 72 h", 648000, 259200, 388800)


def x_star(fh):
    """D / S at the fixed point."""
    return math.log1p(-FF) / math.log1p(-fh)


def tdiv(a, b):
    return np.sign(a) * (np.abs(a) // b)


def step(rule, D, N, P, beta):
    """simulate.py's step: the branch's printed rule, or #529's exact rule, in integers."""
    if rule == "printed":
        tse_p = D * 1000
        error = tdiv(tse_p * (P * 33 - N * 1000), P * 33)
        return np.maximum(tdiv(tse_p - tdiv(beta.numerator * error, beta.denominator), 1000), 1)
    num = D * ((beta.denominator - beta.numerator) * F.numerator * P + beta.numerator * F.denominator * N)
    return np.clip(num // (beta.denominator * F.numerator * P), 1, 2 ** 63 - 1)


def q_of(D, S):
    return -np.expm1(np.log1p(-FF) * (S / D))


def chain_cell(args):
    P, rule, fh, beta = args
    xs, pi = chain.stationary(P, float(beta), fh)
    mean = float((pi * xs).sum())
    sd = math.sqrt(float((pi * (xs - mean) ** 2).sum())) / mean
    tail = float(pi[(1 / xs) > LIMIT].sum())
    miss = chain.mean_miss(PHI, xs, pi)
    n = PHI
    while chain.mean_miss(n, xs, pi) > 1e-9:
        n -= 1
    return P, rule, beta, tail, sd, miss, n


def part_1():
    print("1. stationary law: P(S/D > 1.094) an epoch | sd of D/S | P(fewer than 689 blocks within K) | floor at 1e-9")
    cells = [(P, rule, fh, beta) for P in WINDOWS for rule, fh in RULES for beta in BETAS]
    with ProcessPoolExecutor(max_workers=7) as ex:
        out = list(ex.map(chain_cell, cells))
    for P, rule, beta, tail, sd, miss, n in out:
        print(f"   window {P / H:g} h, {rule:7s}, beta {str(beta):>4s}: {tail:.3e} | sd {100 * sd:.3f} % | {miss:.3e} | {n}")


def settle(rule, P, beta, M, rng, epochs=20):
    D = np.full(M, round(S0 * x_star(dict(RULES)[rule])), dtype=np.int64)
    for _ in range(epochs):
        D = step(rule, D, rng.binomial(P, q_of(D, S0)), P, beta)
    return D


def part_2(M=200_000):
    rng = np.random.default_rng(20261120)
    print()
    print("2. response to a step change of the stake that builds, just after a cut-off: mean |D/S - x*| / x* after corrections 1 to 4; "
          "for a rise, the share of runs with S/D > 1.094 after corrections 1 to 3")
    for label, E, L3, P in CONSTRUCTIONS + (TODAY,):
        times = ", ".join(f"{(L3 + k * E) / H:g}" for k in range(1, 5))
        print(f"   {label}: epoch {E / H:g} h, window {P / H:g} h, phase 3 {L3 / H:g} h; corrections first used at {times} h")
        for beta in (BETAS if label != TODAY[0] else (Fraction(1),)):
            for rule, fh in RULES:
                xs = x_star(fh)
                cells = []
                for factor in (0.5, 0.9, 1.1, 2.0):
                    D = settle(rule, P, beta, M, rng)
                    S1 = round(S0 * factor)
                    errs, above = [], []
                    for _ in range(4):
                        D = step(rule, D, rng.binomial(P, q_of(D, S1)), P, beta)
                        errs.append(float(np.mean(np.abs(D / S1 - xs) / xs)))
                        above.append(float(np.mean(S1 / D > LIMIT)))
                    cell = f"x{factor}: " + " ".join(f"{e:.4f}" for e in errs)
                    if factor > 1:
                        cell += " [>1.094: " + " ".join(f"{a:.4f}" for a in above[:3]) + "]"
                    cells.append(cell)
                print(f"     beta {str(beta):>4s}, {rule:7s} | " + " | ".join(cells))


def part_3(M=200_000, windows=4):
    rng = np.random.default_rng(20261121)
    print()
    print("3. deflation: 30 % of the total active stake withholds every block; mean D over the honest stake after windows 1 to 4")
    for label, E, L3, P in CONSTRUCTIONS + (TODAY,):
        lost = -math.expm1(0.3 * math.log1p(-FF)) * P
        print(f"   {label}: window {P / H:g} h, wins given up per window {lost:.0f}")
        for beta in (BETAS if label != TODAY[0] else (Fraction(1),)):
            row = []
            for rule, fh in RULES:
                D = settle(rule, P, beta, M, rng)
                honest = round(0.7 * S0)
                vals = []
                for _ in range(windows):
                    D = step(rule, D, rng.binomial(P, q_of(D, honest)), P, beta)
                    vals.append(float(np.mean(D / honest)))
                row.append(f"{rule} (x* {x_star(fh):.4f}): " + " ".join(f"{v:.3f}" for v in vals))
            print(f"     beta {str(beta):>4s} | " + " | ".join(row))


def end_ratio(E, P, beta, fh, g_day, model, epochs=60):
    """The largest S/D of an epoch, once the mean of the rule has settled under a growth of g_day a day."""
    gam = math.log1p(g_day) / 86400.0
    online = model == "online"
    w = np.exp(gam * np.arange(P)) if online else np.ones(P)   # S over the window, over S at the epoch's first slot
    d = x_star(fh)                                 # D of the epoch over S at its first slot
    for _ in range(epochs):
        N = float((-np.expm1(math.log1p(-FF) * w / d)).sum())
        end = (math.exp(gam * E) if online else 1.0) / d
        d = d * ((1 - float(beta)) + float(beta) * N / (P * fh)) * math.exp(-gam * E)
    return end


def part_4():
    print()
    print("4. a stake that builds and grows steadily (mean of the rule, no noise): at 1 % a day, the largest S/D of an epoch "
          "over S/D at x*, and as hours of growth; the largest growth a day with that S/D at most 1.094")
    for label, E, L3, P in CONSTRUCTIONS + (TODAY,):
        print(f"   {label}: epoch {E / H:g} h, window {P / H:g} h")
        for beta in (BETAS if label != TODAY[0] else (Fraction(1),)):
            for model, name in (("new", "new stake"), ("online", "coming online")):
                row = []
                for rule, fh in RULES:
                    g1 = 0.01
                    ratio = end_ratio(E, P, beta, fh, g1, model) * x_star(fh)
                    lag = math.log(ratio) / (math.log1p(g1) / 24)
                    lo, hi = 0.0, 0.2
                    for _ in range(30):
                        mid = (lo + hi) / 2
                        lo, hi = (mid, hi) if end_ratio(E, P, beta, fh, mid, model) <= LIMIT else (lo, mid)
                    row.append(f"{rule}: {ratio:.4f} = {lag:.1f} h; largest {100 * lo:.2f} % a day")
                print(f"     beta {str(beta):>4s}, {name:13s} | " + " | ".join(row))


if __name__ == "__main__":
    for part in (sys.argv[1:] or ["1", "2", "3", "4"]):
        t0 = time.time()
        {"1": part_1, "2": part_2, "3": part_3, "4": part_4}[part]()
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
