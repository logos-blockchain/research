"""Option C: the finality floor and its consequences at a window of 36 hours.

The derivation of the specification's Finality Floor (all of the inferred stake builds, every block
T_M = 15 slots late, chance at most 1e-9), at K = 129,600 slots (36 h), beside K = 64,800 (18 h),
and for the ten-hour variant at K = 54,000 (15 h) beside K = 36,000 (10 h).

The floor is computed twice: in whole numbers (exact), and in floating point as the specification
prints it. Usage: python3 floor_c.py
"""
from math import exp, lgamma, log

T_M, EPS_NUM, EPS_DEN = 15, 1, 10 ** 9
F_NUM, F_DEN = 1, 30


def short_exact(n, k):
    """10^9 * P(Bin(k - n T_M, 1/30) < n) as a pair (numerator, denominator), exact."""
    m = k - n * T_M
    if m < n:
        return 1, 1
    a, b = F_NUM, F_DEN - F_NUM
    term, total = b ** m, 0
    for i in range(n):
        total += term
        term = term * (m - i) * a // ((i + 1) * b)
    return total, F_DEN ** m


def floor_exact(k):
    lo, hi = 0, k // (T_M + 1)
    while lo < hi:  # the chance grows with n, so the largest n that passes is found by bisection
        mid = (lo + hi + 1) // 2
        num, den = short_exact(mid, k)
        if num * EPS_DEN <= den * EPS_NUM:
            lo = mid
        else:
            hi = mid - 1
    return lo


def short_float(n, k, f=1 / 30):
    m = k - n * T_M
    if m < n:
        return 1.0
    return sum(exp(lgamma(m + 1) - lgamma(i + 1) - lgamma(m - i + 1) + i * log(f) + (m - i) * log(1 - f))
               for i in range(n))


def floor_float(k):
    n = 0
    while short_float(n + 1, k) <= 1e-9:
        n += 1
    return n


def share_every_win(blocks, slots):
    """The share of the inferred stake whose wins, at mean rates, number `blocks` in `slots`."""
    return log(1 - blocks / slots) / log(29 / 30)


def share_chain_blocks(blocks, slots, delay):
    """The same, counting only blocks of a chain whose every block is `delay` slots late."""
    p = 1 / (slots / blocks - delay)
    return log(1 - p) / log(29 / 30)


def hours_for(blocks, share, delay):
    """Mean time for `blocks` blocks while `share` of the inferred stake builds, each `delay` late."""
    p = 1 - (29 / 30) ** share
    return blocks * (delay + 1 / p) / 3600


if __name__ == "__main__":
    for k in (64_800, 129_600, 36_000, 54_000):
        fe = floor_exact(k)
        ff = floor_float(k)
        n0, d0 = short_exact(fe, k)
        n1, d1 = short_exact(fe + 1, k)
        print(f"K = {k} slots ({k / 3600:.0f} h): floor exact {fe}, as printed {ff}, "
              f"P(N < {fe}) = {n0 / d0:.4e}, P(N < {fe + 1}) = {n1 / d1:.4e}, "
              f"floor / K = {fe / k:.5f}, mean blocks at 15 s = {k / (T_M + 30):.0f}")
        for name, slots in (("54 h", 194_400), ("72 h", 259_200), ("3K", 3 * k), ("4K", 4 * k)):
            print(f"    floor met within {name}: every win {100 * share_every_win(fe, slots):.1f} %, "
                  f"chain blocks at 15 s {100 * share_chain_blocks(fe, slots, 15):.1f} % of the inferred stake")
        for share, who in ((2 / 3, "a third withholds"), (0.7, "30 % withholds")):
            print(f"    {who}: {hours_for(fe, share, 10):.1f} h at 10 s, {hours_for(fe, share, 15):.1f} h at 15 s, "
                  f"{hours_for(fe, share, 5.5068):.1f} h on the specification's Blend")
        print(f"    all stake builds: {hours_for(fe, 1.0, 15):.1f} h at 15 s for the floor's count, "
              f"blocks in K on the specification's Blend {k / (5.5068 + 30):.0f}")
    print(f"depth rule, 2,160 blocks on the specification's Blend: {hours_for(2160, 1.0, 5.5068):.1f} h, "
          f"at 15 s {hours_for(2160, 1.0, 15):.1f} h, while a third withholds on Blend {hours_for(2160, 2 / 3, 5.5068):.1f} h")
