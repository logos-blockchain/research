# The mean gain in blocks over all epochs when a coalition keeps, at each cut-off, the nonce that
# gives it the most slots in the epoch the nonce governs. It weights the gain
# with n nonces (practice.py: the expected largest of n binomial draws over 648,000 slots) by how
# often a cut-off leaves n nonces (the sampler of today_choices.py, choices complete at the cut-off).
# Single epochs: the feedback of compound.py is not included. Budget: the most nonces evaluated.
# Usage: python mean_gain.py > mean_gain.out
import numpy as np
from scipy import stats
from model import rates
from today_choices import log2_tail_table, sample

N = 648_000
GRID = np.arange(0, 40.01, 0.25)                      # log2 of the number of nonces
table = log2_tail_table()

def gain_curve(a):
    mean = N * a
    ks = np.arange(int(mean - 12 * mean ** 0.5), int(mean + 40 * mean ** 0.5) + 1)
    ks = ks[ks >= 0]
    lsf = np.log1p(-stats.binom.sf(ks, N, a))
    out = []
    for b in GRID:
        cdf = np.exp(2.0 ** b * lsf)
        pm = np.diff(np.concatenate(([0.0], cdf)))
        out.append(float((pm * ks).sum()) / mean - 1)
    return np.array(out), mean

print("share | delay | blocks by share | epochs with a choice | mean gain over all epochs, budget 2^8, 2^16, 2^40 (blocks an epoch) | mean gain in the epochs with a choice, same budgets")
for alpha in (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3):
    a, h = rates(alpha)
    g, mean = gain_curve(a)
    who = "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"
    for delta in (10, 15):
        lg, lm, lm0, zs = sample(2_000_000, a, h, delta, 8000, 6000, 4242, table)
        n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
        any_ = float(np.mean(n0 >= 1 - 1e-9))
        alls, conds = [], []
        for cap in (8, 16, 40):
            gg = np.interp(np.minimum(n0, cap), GRID, g)
            alls.append(gg.mean())
            conds.append(gg[n0 >= 1 - 1e-9].mean())
        print(f"{who:8s} | {delta} s | {mean:7.0f} | {100 * any_:5.1f} % | "
              + ", ".join(f"{100 * v:+.3f} % ({v * mean:+.1f})" for v in alls) + " | "
              + ", ".join(f"{100 * v:+.2f} %" for v in conds), flush=True)
