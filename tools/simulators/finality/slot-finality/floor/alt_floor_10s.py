# The alternative "a floor sized at 10 s only": how often the whole stake misses it at 15 s.
# The specification's formula with p = f.
from math import exp, lgamma, log

f = 1 / 30


def blocks_short(n, K, delay):
    slots = K - n * delay
    if slots < n:
        return 1.0
    return sum(exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1) + i * log(f) + (slots - i) * log(1 - f))
               for i in range(n))


def floor(K, delay, eps=1e-9):
    n = 0
    while blocks_short(n + 1, K, delay) <= eps:
        n += 1
    return n


for K in (64800, 36000):
    n10, n15 = floor(K, 10), floor(K, 15)
    print(f"K = {K}: floor at 10 s {n10} (P {blocks_short(n10, K, 10):.3g}), at 15 s {n15} (P {blocks_short(n15, K, 15):.3g}); "
          f"the 10 s floor is missed at 15 s with chance {blocks_short(n10, K, 15):.4g}, at 12 s {blocks_short(n10, K, 12):.3g}; "
          f"the 15 s floor is missed at 20 s with chance {blocks_short(n15, K, 20):.3g}")
