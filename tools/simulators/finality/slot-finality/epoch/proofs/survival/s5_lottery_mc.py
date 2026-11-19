"""A Monte Carlo check of the recursion of section 7 at inflated rates (SURVIVAL.md, section 10.1).

The lottery of section 2 is sampled slot by slot, and the three events are read off each path:
  Q:    some t >= T has X(t) >= 0;
  Q1:   some t >= T has X(t) >= 1;
  Qhat: some count n has U_n >= 0 and sigma_(n+1) > T  (the event of Theorem 6.1).
Each path is followed until its lead X falls 60 below zero; Lemma 6.4 (2) bounds the chance of a
later return by exp(-60 theta*), below 1e-11 for these rates (printed). The frequencies are set against the recursion
of sv_common at the same rates. The check supports the computation; it does not replace the proofs.
Usage: python s5_lottery_mc.py > out_5_lottery_mc.txt
"""
import math

import numpy as np

from sv_common import max_law, survival_curves, theta_star

CASES = (   # f, x_h, x_a, d
    (0.20, 0.7, 0.3, 3),
    (0.15, 0.63 / 0.93, 0.3 / 0.93, 5),
)
N_PATHS = 400_000
TS = (10, 20, 40, 60, 80, 120, 160)
STOP = 60


def sample(h, a, d, n, rng, t_max=6000):
    """Per path: the last t with X(t) >= 0 (L0), with X(t) >= 1 (L1), and the largest T with the
    event of Qhat (Lh). X'(0) = 1 with the count of H0 pending at slot d (Lemma 6.5)."""
    x = np.ones(n, np.int64)
    phase = np.full(n, d, np.int64)
    flag = np.zeros(n, bool)
    L0 = np.zeros(n, np.int64)
    L1 = np.zeros(n, np.int64)
    Lh = np.full(n, -1, np.int64)
    alive = np.ones(n, bool)
    for t in range(1, t_max + 1):
        coal = rng.random(n) < a
        hon = rng.random(n) < h
        count = phase == 1
        start = (phase == 0) & hon
        phase = np.where(phase >= 2, phase - 1, phase)
        phase = np.where(count, 0, phase)
        phase = np.where(start, d, phase)
        x = x + coal - count
        # a count at slot t: the event of the previous count reaches t - 1; the flag becomes [X >= 0]
        Lh = np.where(count & flag, t - 1, Lh)
        flag = np.where(count, x >= 0, flag)
        if t >= d:
            L0 = np.where(x >= 0, t, L0)
            L1 = np.where(x >= 1, t, L1)
        alive &= x > -STOP
        if t % 100 == 0 and not alive.any():
            break
    Lh = np.where(flag, t_max + 1, Lh)     # a flag still set at the end counts as reaching every T
    return L0, L1, Lh, t


if __name__ == "__main__":
    rng = np.random.default_rng(20261118)
    for f, xh, xa, d in CASES:
        h = -math.expm1(xh * math.log1p(-f))
        a = -math.expm1(xa * math.log1p(-f))
        th = theta_star(h, a, d)
        law = max_law(h, a, d)
        res = survival_curves(h, a, d, max(TS), law=law)
        L0, L1, Lh, t_end = sample(h, a, d, N_PATHS, rng)
        print(f"f = {f}, x_h = {xh:.4f}, x_a = {xa:.4f}, d = {d}: h = {h:.5f}, a = {a:.5f}, theta* = {th:.4f}, "
              f"P(M >= {STOP}) <= exp(-theta* {STOP}) = {math.exp(-th * STOP):.1e}; {N_PATHS} paths, followed to slot {t_end}")
        print("   T | Qhat: frequency, recursion, z | Q1: frequency, recursion, z | Q: frequency, recursion, z")
        for T in TS:
            cells = []
            for name, L in (("Qhat", Lh), ("Q1", L1), ("Q", L0)):
                p_mc = float(np.mean(L >= T))
                p_rec = float(res[name][T])
                se = math.sqrt(max(0.0, p_rec * (1 - p_rec)) / N_PATHS)
                z = f"{(p_mc - p_rec) / se:+.2f}" if se > 1e-9 else "none (both are 1)"
                cells.append(f"{p_mc:.5f}, {p_rec:.5f}, {z}")
            print(f"   {T:3d} | " + " | ".join(cells))
