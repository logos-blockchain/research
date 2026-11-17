# Review 3, checks 4 and 6: the early-depth chance and large-deviation sanity figures.
import sys
import numpy as np
from scipy import stats
sys.path.insert(0, ".")
from model import rates

K = 2160
print("check 4: P(2160 gaps <= T), by exact convolution-free identity and by sampling")
for alpha, delta in ((1 / 3, 10), (0.01, 10), (0.01, 0), (0.01, 2), (0.0, 0)):
    a, h = rates(alpha)
    for hh in (18, 10):
        T = hh * 3600
        c = stats.nbinom.cdf(T - K * delta - K, K, h)
        # P(tau <= T) = P(at least K honest wins in the T - K*delta live slots) (each gap removes delta slots)
        alt = stats.binom.sf(K - 1, T - K * delta, h) if T - K * delta > 0 else 0.0
        print(f"alpha {alpha:.3f} delta {delta:2d} {hh} h: nbinom.cdf {c:.3e} | binomial identity {alt:.3e}")
rng = np.random.default_rng(5)
a, h = rates(0.01)
tau = K * 2 + K + rng.negative_binomial(K, h, 2_000_000)
print("sampled P(tau <= 18 h), 1 %, delta 2:", (tau <= 64800).mean(), "formula", stats.nbinom.cdf(64800 - K * 2 - K, K, h))

print("\ncheck 6: largest single term (a lower estimate, log10)")
for alpha, delta in ((1 / 3, 10), (0.25, 10)):
    a, h = rates(alpha)
    fs = np.arange(0, int(8 * K / h))
    ts = K * delta + K + fs
    term = stats.nbinom.logpmf(fs, K, h) + stats.binom.logsf(K, ts, a)      # W >= 2161, no lead before, none after
    i = term.argmax()
    print(f"DEPTH alpha {alpha:.3f} delta {delta}: max term {term[i] / np.log(10):.2f} at tau = {ts[i]} slots ({ts[i] / 3600:.1f} h); "
          f"sum over tau {np.logaddexp.reduce(term) / np.log(10):.2f}")
    for hh in (18, 10):
        T = hh * 3600
        ms = np.arange(1, 3000)
        # W >= m and at most m - 1 honest blocks in T slots (m gaps take more than T)
        term = stats.binom.logsf(ms - 1, T, a) + stats.nbinom.logsf(T - ms * (delta + 1), ms, h)
        i = term.argmax()
        print(f"SLOT {hh} h alpha {alpha:.3f} delta {delta}: max term {term[i] / np.log(10):.2f} at {ms[i]} blocks; sum {np.logaddexp.reduce(term) / np.log(10):.2f}")
