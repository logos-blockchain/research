# What grinding gives a coalition in practice, beyond a higher chance against a final block: the
# expected gain in its own wins when it keeps the best of n nonces.
#   - over a whole epoch (648,000 slots): more blocks, so more leader rewards and fees;
#   - over one hour: a stretch in which it leads far more often than its share.
# Exact: E[max of n Binomial(N, a)] from the binomial law.
# Usage: python practice.py > practice.out
import numpy as np
from scipy import stats
from model import rates

for alpha in (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3):
    a, h = rates(alpha)
    who = "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"
    for label, N in (("epoch, 648,000 slots", 648_000), ("one hour, 3,600 slots", 3600)):
        mean = N * a
        ks = np.arange(int(mean - 12 * (mean ** 0.5)), int(mean + 40 * (mean ** 0.5)) + 1)
        ks = ks[ks >= 0]
        sf = stats.binom.sf(ks, N, a)
        row = []
        for b in (0, 3, 8, 16, 24, 40):
            n = 2.0 ** b
            cdf = np.exp(n * np.log1p(-sf))
            pm = np.diff(np.concatenate(([0.0], cdf)))
            row.append(float((pm * ks).sum()) / mean - 1)
        print(f"{who:8s} | {label:22s} | mean wins {mean:8.1f} | gain with the best of 1, 8, 2^8, 2^16, 2^24, 2^40 nonces: "
              + ", ".join(f"{100 * r:+.1f} %" for r in row))
