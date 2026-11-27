"""Fit how many proposers hold a fork block (from which orphans the real chain referenced), then replay the drafted rule with it."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from window_real import *
from math import lgamma, log, exp
cslots = {B[i]["slot"] for i in main}
lo7, hi7 = HI - 7 * 86400, HI - 800
o1 = [b for b in off if FP[b["id"]][1] == 1 and lo7 <= b["slot"] < hi7 and b["slot"] not in cslots]
obs = []                                              # (trials before success, success?)
for b in o1:
    R = set(b["uncle_in"] or []); j = pos[b["parent"]] + 1; n = 0; s = 0
    while j < len(main) and B[main[j]]["slot"] - B[b["parent"]]["slot"] <= 360:
        if B[main[j]]["slot"] > b["slot"]:
            n += 1
            if main[j] in R: s = 1; break
        j += 1
    if n: obs.append((n, s))
cnt = collections.Counter(obs)
lb = lambda a, b: lgamma(a) + lgamma(b) - lgamma(a + b)
def ll(a, b):
    return sum(c * ((lb(a + 1, b + n - 1) if s else lb(a, b + n)) - lb(a, b)) for (n, s), c in cnt.items())
best = max(((ll(a, b), a, b) for a in [x * 0.05 for x in range(1, 60)] for b in [x * 0.5 for x in range(1, 80)]), key=lambda t: t[0])
_, a, b_ = best
print(f"last 7 days: {len(o1)} single-depth orphans, {sum(s for _, s in obs)} referenced; fitted Beta({a:.2f}, {b_:.1f}): mean holding share {a/(a+b_):.3f}")
pn = lambda n: 1 - exp(lb(a, b_ + n) - lb(a, b_))
print("share referenced by the n-th following canonical block, model:", {n: round(pn(n), 2) for n in (1, 2, 5, 10, 20, 40, 80, 120)})
def hold_single(seed):
    r = random.Random(seed); H = {}
    def h(b):
        if b["id"] not in H:
            # a block of a branch of 3 or more blocks was on the chain of many peers: half of the proposers hold it
            f = first[b["id"]]; H[b["id"]] = 0.5 if len_branch[f] >= 3 else r.betavariate(a, b_)
        return H[b["id"]]
    return h
len_branch = collections.Counter()
for b in off: len_branch[first[b["id"]]] = max(len_branch[first[b["id"]]], FP[b["id"]][1])
VM = lambda b: (sub_end[first[b["id"]]] if len_branch[first[b["id"]]] >= 3 else b["slot"]) + 10
if __name__ == "__main__":
    for name, lo, hi in (("last 24 h", HI - 86400 - 400, HI - 400), ("last 7 days", lo7, HI - 400), ("7 to 14 days ago", HI - 14 * 86400 + 3600, HI - 7 * 86400)):
        x, c, occ = actual(lo, hi); print(f"{name}: canonical alone {c:.3f}, with the actual references {x:.3f} of the occupied slots")
        for label, depth, Ws in (("today's rule, first fork block", 1, [12, 96, 288]), ("any depth", None, [12, 24, 48, 96, 144, 288])):
            for W in Ws:
                v = [run(W * 30, VM, depth, lo=lo, hi=hi, hold=hold_single(s), seed=s)[0] for s in range(3)]
                print(f"   {label:32s} W = {W:3d}: {sum(v)/3:.3f}")
