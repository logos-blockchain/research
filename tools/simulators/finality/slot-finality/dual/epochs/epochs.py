"""The floor and the time to finality over several epochs, at mean rates.

Epoch: 10 * U slots, U = 64,800. The inferred stake D of epoch e + 1 is D of epoch e times the
occupied slots measured in the first 6 U slots of epoch e over the expected f * 6 U (beta = 1,
uncles count, so the measure is every lottery win of the stake that builds).
A stake b (as a share of the true stake) wins a slot with chance r = 1 - (1 - f)^(b / D).

Counts of occupied slots for the floor, three models:
  wins       every lottery win of the building stake counts (blocks lost to delay return as uncles)
  blocks 6   only chain blocks count, each 6 slots late:  rate r / (1 + 6 r)
  blocks 15  only chain blocks count, each 15 slots late: rate r / (1 + 15 r)
A block at slot t is final after the least T >= K with at least phi occupied slots in (t, t + T].
It is "late" if T > K. Depth rule: the least T with 2,160 chain blocks in (t, t + T].
Everything is a mean rate (a median, to a good approximation). No tails.

Usage: python epochs.py [K phi]      default 64800 1291; also 36000 689
"""
import sys

import numpy as np

f, U = 1 / 30, 64800
E, P = 10 * U, 6 * U
K = int(sys.argv[1]) if len(sys.argv) > 2 else 64800
PHI = int(sys.argv[2]) if len(sys.argv) > 2 else 1291
DT = 60
NE = 14                      # epochs simulated
T = np.arange(0, NE * E, DT)
EP = T // E
MODELS = (("wins", 0), ("blocks 6", 6), ("blocks 15", 15))


def run(build):
    """build: array over T of the building stake as a share of the true stake. Returns D per epoch
    and, per model, the cumulative count of occupied slots."""
    D = np.ones(NE + 1)
    r = np.zeros(T.size)
    for e in range(NE):
        m = EP == e
        r[m] = 1 - (1 - f) ** (build[m] / D[e])
        w = m & (T - e * E < P)
        D[e + 1] = D[e] * r[w].mean() / f
    cum = {name: np.concatenate(([0.0], np.cumsum(r / (1 + d * r) * DT))) for name, d in MODELS}
    return D, cum


def finality(cum, need, kmin):
    """Hours to finality for a block at each step: least T >= kmin with `need` counts after it."""
    target = cum[:-1] + need
    idx = np.searchsorted(cum, target, side="left")
    tt = (idx - np.arange(T.size)) * DT
    tt = np.maximum(tt, kmin).astype(float)
    tt[idx >= cum.size] = np.nan
    return tt


def stats(tt, lo=3, hi=NE - 3):
    m = (EP >= lo) & (EP < hi) & ~np.isnan(tt)
    late = tt[m] > K + DT
    # longest stretch of consecutive late steps
    best = cur = 0
    for x in late:
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return late.mean(), best * DT, tt[m].max() / 3600, tt[m][late].mean() / 3600 if late.any() else K / 3600, (tt[m].mean() - K) / 3600


def report(name, build, cost=None, lo=3, hi=NE - 3):
    D, cum = run(build)
    cells = []
    for mname, _ in MODELS:
        s = stats(finality(cum[mname], PHI, K), lo, hi)
        cells.append(f"{mname}: late {100 * s[0]:4.1f} % of the time, longest {s[1] / 86400:5.2f} d, mean when late {s[3]:5.1f} h, max {s[2]:5.1f} h, extra wait averaged over all time {60 * s[4]:5.1f} min")
    dep = []
    for mname in ("blocks 6", "blocks 15"):
        tt = finality(cum[mname], 2160, 0)
        m = (EP >= lo) & (EP < hi) & ~np.isnan(tt)
        dep.append(f"{mname}: {tt[m].min() / 3600:.1f} to {tt[m].max() / 3600:.1f} h")
    c = "" if cost is None else f" | withheld {100 * cost:.0f} % of the time"
    print(f"{name}{c}\n    D by epoch {lo}..{hi + 1}: " + " ".join(f"{x:.3f}" for x in D[lo:hi + 2])
          + f"   fastest lottery {1 / D[lo:hi + 2].min():.3f} x f when all stake builds"
          + "\n    floor " + "\n    floor ".join(cells) + "\n    depth 2,160: " + "; ".join(dep))
    return D, cum


def periodic(a, length):
    """Withholding in [a, a + length) of every epoch (in units of U, wrapping)."""
    x = (T % E) / U
    return ((x - a) % 10) < length


if __name__ == "__main__":
    print(f"K = {K}, floor {PHI}. Thresholds (building stake / D below which the floor is missed at mean rates): "
          + ", ".join(f"{n}: {np.log(1 - (lambda g: g / (1 - d * g))(PHI / K)) / np.log(1 - f):.3f}" for n, d in MODELS))
    for alpha, an in ((0.1, "a tenth"), (0.2, "a fifth"), (0.3, "30 %"), (1 / 3, "a third")):
        print(f"\n===== coalition of {an} =====")
        ones = np.ones(T.size)
        wh = T >= 3 * E + P
        report("S1 withholds for good, from the end of an observation window", ones - alpha * wh, lo=3, hi=8)
        wh = T >= 3 * E
        report("S1b withholds for good, from the start of an epoch", ones - alpha * wh, lo=3, hi=8)
        wh = periodic(6, 4)
        report("S2 withholds outside the observation windows only (last 4 U of each epoch)", ones - alpha * wh, wh.mean())
        wh = (EP % 2) == 1
        report("S3 withholds every second epoch", ones - alpha * wh, wh.mean())
        wh = periodic(0, 6)
        report("S5 withholds in every observation window, builds outside", ones - alpha * wh, wh.mean())
        # search: one interval per epoch, the same in every epoch
        best = {}
        for a in np.arange(0, 10, 0.5):
            for ln in np.arange(0.5, 10.01, 0.5):
                wh = periodic(a, ln)
                D, cum = run(ones - alpha * wh)
                for mname, _ in MODELS:
                    s = stats(finality(cum[mname], PHI, K))
                    key = mname
                    if key not in best or s[4] > best[key][5] + 1e-9:
                        best[key] = (s[0], a, ln, s[2], 1 / D[3:].min(), s[4])
        for mname, v in best.items():
            print(f"most delay from one interval per epoch [{mname}]: withhold from {v[1]:.1f} U for {v[2]:.1f} U -> extra wait averaged over all time {60 * v[5]:.1f} min, late {100 * v[0]:.1f} % of the time, "
                  f"max {v[3]:.1f} h, cost {10 * v[2]:.0f} % of the coalition's blocks, fastest lottery {v[4]:.3f} x f")
    print("\n===== stake that leaves for good (honest, no coalition) =====")
    for x in (0.1, 0.2, 0.3, 0.5):
        for label, t0 in (("at the start of an epoch", 3 * E), ("in the middle of an observation window", 3 * E + 3 * U),
                          ("at the end of an observation window", 3 * E + P)):
            report(f"L {x:.0%} leaves {label}", np.ones(T.size) - x * (T >= t0), lo=3, hi=8)
    print("\n===== stake that leaves and returns =====")
    for x in (0.1, 0.2, 0.3, 1 / 3, 0.48, 0.5):
        for label, t1 in (("at the start of an epoch", 7 * E), ("at the end of an observation window", 6 * E + P)):
            b = np.ones(T.size) - x * ((T >= 3 * E) & (T < t1))
            report(f"R {x:.0%} absent from the start of epoch 3, returns {label}", b, lo=3, hi=10)
