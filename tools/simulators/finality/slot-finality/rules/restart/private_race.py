# The restart path: a private race at delta = 10 in which the fork runs over K slots and the node's
# chain stopped T_offline = 1,200 slots earlier. "Behaves like" = the wait T whose race, with both
# sides running T slots, has the same chance. Another form of the model in ks_tables.py
# (log_chance / equivalent): the honest count is the renewal count with gaps delta + Geom(p_h), the
# fork's count is Bin(t, p_a), and the fork wins when it holds at least as many blocks.
import math

import numpy as np
from scipy import stats

F, DELTA, T_OFF = 1 / 30, 10, 1200


def p(share):
    return 1 - (1 - F) ** share


def log_chance(alpha, t_adv, t_hon):
    pa, ph = p(alpha), p(1 - alpha)
    mean = t_hon / (DELTA + 1 / ph)
    ns = np.arange(max(1, int(mean * 0.05)), int(mean * 1.8))
    # P(N >= n) = P(Bin(t_hon - n*DELTA, ph) >= n)
    ge = stats.binom.sf(ns - 1, np.maximum(t_hon - ns * DELTA, 0), ph)
    pmf = ge - np.append(ge[1:], 0.0)                       # P(N = n)
    log_a = stats.binom.logsf(ns - 1, t_adv, pa)            # log P(A >= n)
    with np.errstate(divide="ignore"):
        terms = np.log(np.maximum(pmf, 1e-320)) + log_a
    m = terms.max()
    return m + math.log(np.exp(terms - m).sum())


def equivalent(alpha, K, t_off=T_OFF):
    target = log_chance(alpha, K, K - t_off)
    lo, hi = K - 15000, K                                   # chance falls with T
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if log_chance(alpha, mid, mid) > target:
            lo = mid
        else:
            hi = mid
    return hi


for K, label in ((64800, "18 h"), (36000, "10 h")):
    for alpha in (0.272, 0.295, 0.298, 0.30, 0.323, 0.332, 1 / 3):
        T = equivalent(alpha, K)
        print(f"K {label}, alpha {alpha:.4f}: behaves like {T} slots = {T / 3600:.2f} h; the head start costs {(K - T) / 3600:.2f} h; "
              f"log10 chance of the race itself {log_chance(alpha, K, K - T_OFF) / math.log(10):.1f}")
