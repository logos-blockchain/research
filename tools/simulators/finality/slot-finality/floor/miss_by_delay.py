# The chance that the whole stake misses the floor at K, by the delay of every block.
# The specification's formula with p = f.
from math import exp, lgamma, log

f = 1 / 30


def blocks_short(n, K, delay):
    slots = K - n * delay
    if slots < n:
        return 1.0
    return sum(exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1) + i * log(f) + (slots - i) * log(1 - f))
               for i in range(n))


for K, phi in ((64800, 1291), (36000, 689)):
    print(f"K = {K}, floor {phi}: " + ", ".join(f"{d} s: {blocks_short(phi, K, d):.2g}" for d in (10, 12, 14, 15, 16, 17, 18, 19, 20)))
