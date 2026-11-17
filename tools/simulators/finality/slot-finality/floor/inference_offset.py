# The floor against the rate the stake inference steers to.
# The inference stores f at three decimals (f_p = truncate(f * 1000) / 1000 = 0.033), so with every
# win counted it settles where slots are occupied at 0.033 a slot, 1 % below f = 1/30.
# The specification's formula with the win chance p in place of f.
from math import exp, lgamma, log

f = 1 / 30


def blocks_short(n, K, delay, p):
    slots = K - n * delay
    if slots < n:
        return 1.0
    return sum(exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1) + i * log(p) + (slots - i) * log(1 - p))
               for i in range(n))


def floor(K, delay, p, eps=1e-9):
    n = 0
    while blocks_short(n + 1, K, delay, p) <= eps:
        n += 1
    return n


for K, phi in ((64800, 1291), (36000, 689)):
    print(f"K = {K}, floor {phi}, every block 15 s late")
    for name, p in (("f = 1/30", f), ("0.033, where the inference settles", 0.033),
                    ("f with the estimate 1 % high", 1 - (1 - f) ** (1 / 1.01)),
                    ("f with the estimate 2 % high", 1 - (1 - f) ** (1 / 1.02)),
                    ("0.033 with the estimate 1 % high", 1 - (1 - 0.033) ** (1 / 1.01)),
                    ("0.033 with the estimate 2 % high", 1 - (1 - 0.033) ** (1 / 1.02))):
        print(f"  win chance {name}: missed with chance {blocks_short(phi, K, 15, p):.2g}; the floor at this rate would be {floor(K, 15, p)}; "
              f"at 10 s the chance is {blocks_short(phi, K, 10, p):.2g}")
