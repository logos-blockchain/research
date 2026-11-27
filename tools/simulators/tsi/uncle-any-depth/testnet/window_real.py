"""What the drafted rule could count on the real testnet tree, by reference window, under three visibility assumptions."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import random, bisect
U = 4
pos = {i: n for n, i in enumerate(main)}
off = [b for b in B.values() if b["id"] not in MAIN and FP[b["id"]][0] is not None and b["slot"] <= HI - 400]
# last slot of the losing branch family: the fork group is everything hanging off the same fork point
grp_end = collections.defaultdict(int)
for b in off: grp_end[FP[b["id"]][0]] = max(grp_end[FP[b["id"]][0]], b["slot"])
kids = collections.defaultdict(list)
for b in off: kids[b["parent"]].append(b["id"])
sub_end = {}
def subtree_end(i):                          # last slot of the branch family that contains b (descend from the first fork block)
    st = [i]; e = B[i]["slot"]
    while st:
        x = st.pop(); e = max(e, B[x]["slot"]); st += kids[x]
    return e
first = {}                                   # first fork block of each branch
for b in off:
    x = b["id"]
    while B[x]["parent"] not in MAIN: x = B[x]["parent"]
    first[b["id"]] = x
for i in set(first.values()): sub_end[i] = subtree_end(i)
def span(sel_lo, sel_hi):
    can = [B[i] for i in main if sel_lo <= B[i]["slot"] < sel_hi]; o = [b for b in off if sel_lo <= b["slot"] < sel_hi]
    return can, o
def run(Wslots, vis, depth=None, lag=15, seed=0, hold=None, lo=None, hi=None):
    """vis(b) = slot from which a canonical proposer may hold b; hold = per-(orphan, proposer) probability or None."""
    rng = random.Random(seed); lo = LO if lo is None else lo; hi = HI if hi is None else hi
    cand = sorted(((vis(b) + lag, b) for b in off if lo - 20000 <= b["slot"] < hi), key=lambda t: t[0])
    occ = {B[i]["slot"] for i in main}; chain_occ = set(); counted = set(); used = 0; nref = collections.Counter()
    pool = []; j = 0
    for i in main:
        A = B[i]
        if A["slot"] < lo - 20000: continue
        if A["slot"] >= hi: break
        while j < len(cand) and cand[j][0] <= A["slot"]: pool.append(cand[j][1]); j += 1
        keep = []; sel = []
        for b in pool:
            G = B[FP[b["id"]][0]]
            if A["slot"] - G["slot"] > Wslots: continue            # out of the window for good
            if b["slot"] in chain_occ or b["slot"] in counted: continue
            keep.append(b)
            if pos[G["id"]] >= pos[i] or b["slot"] >= A["slot"]: continue
            if depth and FP[b["id"]][1] > depth: continue
            if hold is not None and rng.random() >= hold(b): continue
            sel.append((G["slot"], b["slot"], b["id"]))
        sel.sort(); sl = set(); n = 0
        for _, s, _ in sel:
            if n == U: break
            if s in sl: continue
            sl.add(s); n += 1
        counted |= sl; nref[n] += 1; pool = keep; chain_occ.add(A["slot"])
    can, o = span(lo, hi); cs = {b["slot"] for b in can}; occs = cs | {b["slot"] for b in o}
    return len((cs | counted) & occs) / len(occs), nref
def actual(lo, hi):
    can, o = span(lo, hi); cs = {b["slot"] for b in can}; occs = cs | {b["slot"] for b in o}
    ref = {b["slot"] for b in o if any(r in MAIN for r in (b["uncle_in"] or []))}
    return len(cs | ref) / len(occs), len(cs) / len(occs), len(occs) / (hi - lo)
V1 = lambda b: b["slot"] + 10                               # seen 10 s after its slot by everybody
V3 = lambda b: sub_end[first[b["id"]]] + 10                 # seen only when its branch has stopped growing
if __name__ == "__main__":
    periods = [("last 24 h", HI - 86400 - 400, HI - 400), ("last 7 days", HI - 7 * 86400, HI - 400), ("7 to 14 days ago", HI - 14 * 86400 + 3600, HI - 7 * 86400)]
    for name, lo, hi in periods:
        a, c, occ = actual(lo, hi)
        print(f"{name}: occupied {occ:.4f} per slot; canonical blocks alone cover {c:.3f} of the occupied slots; with the actual references {a:.3f}")
        for label, depth, Ws in (("today's rule (first fork block), W = 12", 1, [12]), ("any depth", None, [12, 24, 48, 96, 144, 288])):
            for W in Ws:
                v1, n1 = run(W * 30, V1, depth, lo=lo, hi=hi); v3, n3 = run(W * 30, V3, depth, lo=lo, hi=hi)
                print(f"   {label:40s} W = {W:3d}: counted share if seen at once {v1:.3f}, if seen only when the branch stops growing {v3:.3f}   (blocks with 4 references {n1[4]/sum(n1.values()):.2f} / {n3[4]/sum(n3.values()):.2f})")
