"""The chance that the whole stake misses the floor at K, with every block 15 s late, when the
lottery does not run at exactly f = 1/30: (a) the specification stores f at three decimals, so the
inference steers occupied slots to 0.033 a slot; (b) the inferred stake is 1 or 2 % above the stake
that builds for an epoch (the inference's noise is about 0.9 % an epoch). Specification's formula.
Also the floor that the same derivation gives at each rate."""
from math import exp, lgamma, log

EPS = 1e-9


def short(n, K, p, delta=15):
    slots = K - n * delta
    if slots < n:
        return 1.0
    return sum(exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1) + i * log(p) + (slots - i) * log(1 - p)) for i in range(n))


def floor(K, p, delta=15):
    n = 0
    while short(n + 1, K, p, delta) <= EPS:
        n += 1
    return n


f = 1 / 30
cases = [("f = 1/30, estimate exact", f), ("rate 0.033 a slot", 0.033)]
for hi in (1.01, 1.02, 1.03, 1.05):
    cases.append((f"f = 1/30, estimate {100 * (hi - 1):.0f} % high", 1 - (1 - f) ** (1 / hi)))
    cases.append((f"rate 0.033, estimate {100 * (hi - 1):.0f} % high", 1 - (1 - 0.033) ** (1 / hi)))
for K, phi in ((64800, 1291), (36000, 689)):
    print(f"\nK = {K}, floor {phi}, every block 15 s late, all stake building")
    for name, p in cases:
        print(f"  {name:34s} p = {p:.6f}  mean blocks {K * p / (1 + 15 * p):7.1f}  P(N < {phi}) = {short(phi, K, p):.2e}   floor by the same derivation at this rate: {floor(K, p)}")
    print(f"  at 10 s per block: rate 0.033: P = {short(phi, K, 0.033, 10):.1e}; estimate 2 % high: P = {short(phi, K, 1 - (1 - f) ** (1 / 1.02), 10):.1e}")
