"""select_rules.py, the drafted condition (branch by broadcast or referenced) at W = 240 and p = 0.7, with three kinds of wait."""
"""Selection rules compared on the real testnet tree, with persistent nodes.

N nodes of equal stake. A losing branch of two or more blocks is held, whole, by a random set of nodes of the size the scanner saw
on it. Each of them got each block of the branch on the broadcasting channel with probability p, otherwise by a download.
The first block of a branch is also held by other nodes, as fitted from the references of the real chain (Beta draw per block).
The proposer of each canonical block is a random node. A referenced block and its branch are then held by everybody (downloads).

Rules for a candidate X of a proposer that holds X and its branch:
  any      no condition
  all      every block of the branch received by broadcast                                  (the draft)
  all+ref  every block of the branch received by broadcast, or referenced on the proposer's chain
  self     X received by broadcast
Usage: select_rules.py [seeds]
"""
import sys, os, io, contextlib, random, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import json, window_real as wr
    from hold_fit import *
    F = load("forks")["forks"]
aff = {f["point"]: f["res"]["affected"] / max(1, f["res"]["peers"]) for f in F if f.get("res")}
N, U = 150, 4
PARENT = {b["id"]: b["parent"] for b in off}

def branch_ids(i):
    out = [i]
    while PARENT.get(out[-1]) in PARENT: out.append(PARENT[out[-1]])
    return out                                       # X first, then its ancestors down to the first fork block
BR = {b["id"]: branch_ids(b["id"]) for b in off}

def run(args):
    Wb, rule, p, lo, hi, seed, lag, kind = args
    rng = random.Random(seed); wslots = Wb * 30
    memb, direct, cast = {}, {}, {}
    def members(f):
        if f not in memb:
            r = random.Random(f"{seed}-{f}"); x = r.betavariate(a, b_)
            x = max(x, aff.get(FP[f][0], 0.0)) if len_branch[f] >= 2 else 0.0
            memb[f] = frozenset(n for n in range(N) if r.random() < x)
        return memb[f]
    def first_holders(f):                            # nodes that got the first fork block by broadcast, outside the branch
        if f not in direct:
            r = random.Random(f"{seed}-d-{f}"); x = r.betavariate(a, b_)
            direct[f] = frozenset(n for n in range(N) if r.random() < x)
        return direct[f]
    def got_cast(i, n):
        f = first[i]
        if i not in cast:
            r = random.Random(f"{seed}-c-{i}")
            cast[i] = frozenset(n for n in members(f) if r.random() < p)
        return n in cast[i] or (i == f and n in first_holders(f))
    public = set(); refd = set()                     # held by everybody; referenced on the chain
    def holds(i, n):
        f = first[i]
        return i in public or n in members(f) or (i == f and n in first_holders(f))
    def ok(i, n):
        if not holds(i, n): return False
        if rule == "any": return True
        if rule == "self": return got_cast(i, n)
        if rule == "all": return all(got_cast(y, n) for y in BR[i])
        return all(got_cast(y, n) or y in refd for y in BR[i])
    cand = sorted(((VM(b) + lag if kind == "receipt" else max(VM(b), b["slot"] + lag), b) for b in off if lo - 20000 <= b["slot"] < hi), key=lambda t: t[0])
    chain_occ = set(); counted = set(); pool = []; j = 0; nref = collections.Counter()
    for i in main:
        A = B[i]
        if A["slot"] < lo - 20000: continue
        if A["slot"] >= hi: break
        while j < len(cand) and cand[j][0] <= A["slot"]: pool.append(cand[j][1]); j += 1
        n = rng.randrange(N); keep = []; sel = []
        for b in pool:
            G = B[FP[b["id"]][0]]
            if A["slot"] - G["slot"] > wslots: continue
            if b["slot"] in chain_occ or b["slot"] in counted: continue
            keep.append(b)
            if pos[G["id"]] >= pos[i] or b["slot"] >= A["slot"]: continue
            if not ok(b["id"], n): continue
            sel.append((G["slot"], b["slot"], b["id"]))
        sel.sort(); sl = set(); m = 0
        for _, s, x in sel:
            if m == U: break
            if s in sl: continue
            sl.add(s); m += 1; refd.add(x); public.update(BR[x])
        counted |= sl; nref[m] += 1; pool = keep; chain_occ.add(A["slot"])
    can, o = span(lo, hi); cs = {b["slot"] for b in can}; occs = cs | {b["slot"] for b in o}
    return args, len((cs | counted) & occs) / len(occs)

if __name__ == "__main__":
    from multiprocessing import Pool
    per = {"last 7 days": (lo7, HI - 400), "7-14 days ago": (HI - 14 * 86400 + 3600, HI - 7 * 86400)}
    arms = {"no wait": (0, "receipt"), "15 s after receipt": (15, "receipt"), "15 slots after the uncle's slot": (15, "slot")}
    jobs = [(240, "all+ref", 0.7, lo, hi, sd, lag, kind) for lo, hi in per.values() for lag, kind in arms.values() for sd in range(6)]
    with Pool(10) as P: res = P.map(run, jobs, chunksize=1)
    t = collections.defaultdict(list)
    for a, v in res: t[(a[3], a[6], a[7])].append(v)
    import statistics as st
    for name, (lo, hi) in per.items():
        for arm, (lag, kind) in arms.items():
            x = t[(lo, lag, kind)]; print(f"{name:14s} {arm:32s} {st.mean(x):.4f} +- {st.stdev(x) / len(x) ** .5:.4f}")
