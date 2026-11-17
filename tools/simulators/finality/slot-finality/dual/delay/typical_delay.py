"""What if 15 s is the largest delay and the typical delay is about 6 s?

The floor is a count over about 1,300 blocks, so only the MEAN delay per block matters for it: the
sum of 1,300 delays spreads by a few minutes at most, against 18 hours. A delay that is 6 s with
chance 1 - q and 15 s with chance q has mean 6 + 9q. Rows: the mean delay per block.
The floor stays 1,291 (K = 64,800), sized with no stake withholding and every block 15 s late.
"""
import sys

sys.path.insert(0, "..")
from timing import H, cdf, p_of, quantile  # noqa: E402

K, N, EPS, TH = 64800, 1291, 1e-9, 1 / 3


def bis(fn, lo, hi):
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fn(mid) else (lo, mid)
    return lo


def miss(n, share, D):
    return 1 - cdf(n, K, p_of(share), D)


def floor_for(D):
    n = 0
    while miss(n + 1, 1.0, D) <= EPS:
        n += 1
    return n


print(f"{'mean delay':>10s} {'share at 15 s':>13s} {'blocks in K':>11s} | missing before late (1e-9 / 1e-3 / half) | a third withholds: median / latest | 0.2: median / latest | floor if sized at this delay")
for D in (6, 6.9, 7, 8.25, 10, 12, 15):
    q = (D - 6) / 9
    g = p_of(1) / (1 + p_of(1) * D)
    m = [bis(lambda a: miss(N, 1 - a, D) <= e, 0.0, 1.0) if miss(N, 1.0, D) <= e else 0.0 for e in (EPS, 1e-3, 0.5)]
    t3 = [max(K, quantile(N, x, p_of(1 - TH), D)) / H for x in (0.5, 1 - EPS)]
    t2 = [max(K, quantile(N, x, p_of(0.8), D)) / H for x in (0.5, 1 - EPS)]
    print(f"{D:10.2f} {100 * q:12.0f}% {g * K:11.0f} | {100 * m[0]:5.1f} % / {100 * m[1]:5.1f} % / {100 * m[2]:5.1f} % | {t3[0]:5.1f} / {t3[1]:5.1f} h | {t2[0]:5.1f} / {t2[1]:5.1f} h | {floor_for(D)}")

# How much the spread of the delays adds: two-point delay, 6 s or 15 s, share q at 15 s.
# Sum of n delays = 6n + 9 * Binomial(n, q); its standard deviation in slots:
import math
for q in (0.1, 0.25, 0.5):
    print(f"q = {q}: the sum of {N} delays has a standard deviation of {9 * math.sqrt(N * q * (1 - q)):.0f} slots; "
          f"the lottery's own spread over {N} blocks is {math.sqrt(N * (1 - p_of(1))) / p_of(1):.0f} slots")
