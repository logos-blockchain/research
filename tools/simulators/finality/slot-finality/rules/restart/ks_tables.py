# From the stored curves: the largest share each K holds under each worst-case
# condition (held_worst on B5's grid, as K.7's holds.csv), the waits at 0.25 / 0.30 / a third, and
# the restart path (the private race, as in private_race.py, then the share
# the study's bound holds at that equivalent wait).
# Usage: python ks_tables.py   (reads ks_curves.npy and ks_factors.csv of ../../nonce/data,
# which ks_curves.py there writes)
import math
import os
import sys

import numpy as np
from joblib import Parallel, delayed
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "..", "nonce", "data")
SRC = os.path.join(HERE, "..", "..", "..", "src")
sys.path.insert(0, DIR)
from ks_common import EPS, F, GRID, HOURS, KS, T_OFF, WGRID, add_src, fmt_share, held_worst  # noqa: E402

FR = 1.10 ** 2            # the resisting nonce: slots.md §4 "at most 1.10" per nonce, two nonces
curves = np.load(f"{DIR}/ks_curves.npy").astype(np.float64)   # [case, alpha, T-1]
CASES = {"10 s": 0, "10 s deflated": 1, "12 s": 2, "15 s": 3}
fac = np.genfromtxt(f"{DIR}/ks_factors.csv", delimiter=",", names=True)
assert np.allclose(fac["alpha"], WGRID)
ln = {key: np.interp(GRID, WGRID, np.log(fac[key])) for key in ("factor_lo", "factor_hi", "pair_lo", "pair_hi")}

CONDS = [
    ("10 s, nonce not ground", "10 s", 0.0),
    ("10 s, resisting nonce", "10 s", math.log(FR)),
    ("10 s, deflated, not ground", "10 s deflated", 0.0),
    ("10 s, deflated, resisting nonce", "10 s deflated", math.log(FR)),
    ("10 s, today's nonce, one ground (upper)", "10 s", ln["factor_hi"]),
    ("10 s, today's nonce, two ground (upper)", "10 s", ln["pair_hi"]),
    ("12 s, nonce not ground", "12 s", 0.0),
    ("15 s, nonce not ground", "15 s", 0.0),
]


def held_at(T, case, lnr):
    logs = curves[CASES[case], :, T - 1]
    return held_worst(logs, EPS, lnr)


print("largest share held at 1e-9 (study's bound, K.7 reading); columns K =", HOURS)
for name, case, lnr in CONDS:
    print(f"  {name:42s} " + " | ".join(fmt_share(held_at(KS[h], case, lnr)) for h in HOURS))


# waits at 0.25, 0.30, a third, with the study's bound (need), factors at exactly those shares
def need(alpha, delta, eps, scale=1.0):
    add_src(SRC)
    from finality_sim.waitbound import wait_curve, wait_needed
    return wait_needed(wait_curve(1_500_000, alpha, delta, F, floor=eps / 10, scale=scale), eps)


idx = {a: int(np.argmin(np.abs(WGRID - a))) for a in (0.25, 0.30, 1 / 3)}
jobs = []
for a in (0.25, 0.30, 1 / 3):
    i = idx[a]
    dfl = 1 / (1 - a)
    jobs += [
        ("10 s, nonce not ground", a, (a, 10, EPS)),
        ("10 s, resisting nonce", a, (a, 10, EPS / FR)),
        ("10 s, deflated, not ground", a, (a, 10, EPS, dfl)),
        ("10 s, deflated, resisting nonce", a, (a, 10, EPS / FR, dfl)),
        ("10 s, one ground, lower", a, (a, 10, EPS / fac["factor_lo"][i])),
        ("10 s, one ground, upper", a, (a, 10, EPS / fac["factor_hi"][i])),
        ("10 s, two ground, lower", a, (a, 10, EPS / fac["pair_lo"][i])),
        ("10 s, two ground, upper", a, (a, 10, EPS / fac["pair_hi"][i])),
        ("12 s, nonce not ground", a, (a, 12, EPS)),
        ("15 s, nonce not ground", a, (a, 15, EPS)),
    ]
ws = Parallel(n_jobs=14)(delayed(need)(*args) for _, _, args in jobs)
print()
print("wait at 1e-9, hours (study's bound): 0.25 / 0.30 / a third")
table = {}
for (name, a, _), w in zip(jobs, ws):
    table.setdefault(name, {})[a] = w
for name, d in table.items():
    print(f"  {name:36s} " + " / ".join(f"{d[a] / 3600:.2f}" if d[a] > 0 else "past" for a in (0.25, 0.30, 1 / 3)))


# the restart path: the private race, as in private_race.py
DELTA = 10


def p_share(a):
    return 1 - (1 - F) ** a


def log_chance(alpha, t_attacker, t_honest):
    pa, ph = p_share(alpha), p_share(1 - alpha)
    mean_h = t_honest / (DELTA + 1 / ph)
    ns = np.arange(max(1, int(mean_h * 0.1)), int(mean_h * 1.6))
    sf_h = stats.nbinom.cdf(t_honest - ns * DELTA - ns, ns, ph)
    pmf_h = sf_h - np.append(sf_h[1:], 0.0)
    log_sf_a = stats.binom.logsf(ns - 1, t_attacker, pa)
    with np.errstate(divide="ignore"):
        terms = np.log(np.maximum(pmf_h, 1e-320)) + log_sf_a
    m = terms.max()
    return m + np.log(np.exp(terms - m).sum())


def equivalent(alpha, K):
    frozen = log_chance(alpha, K, K - T_OFF)
    lo, hi = K - 12000, K
    while hi - lo > 5:
        mid = (lo + hi) // 2
        if log_chance(alpha, mid, mid) > frozen:
            lo = mid
        else:
            hi = mid
    return hi


print()
print("restart path: alpha used, equivalent wait (h), share held at that wait")
for name, case, lnr in (CONDS[5], CONDS[1], CONDS[3]):
    cells = []
    for h in HOURS:
        K = KS[h]
        a0 = held_at(K, case, lnr)
        a_use = 1 / 3 if a0 == math.inf else a0
        if a_use != a_use:
            cells.append("n/a")
            continue
        Tq = equivalent(a_use, K)
        a1 = held_at(Tq, case, lnr)
        cells.append(f"{h} h: a={a_use:.3f} -> {Tq / 3600:.2f} h -> {fmt_share(a1)}")
    print(f"  {name}: " + "; ".join(cells))
