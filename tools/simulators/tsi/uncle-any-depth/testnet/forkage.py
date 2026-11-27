"""The forks of the last 7 days: the slots from fork point to orphan, the orphans by depth, the branches by duration, the
fewest canonical blocks in 4k/f - W/f slots, and the canonical chain's references to blocks the scanner never got."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from window_real import *
lo, hi = HI - 7 * 86400, HI - 800
o = [b for b in off if lo <= b["slot"] < hi]
age = [b["slot"] - B[FP[b["id"]][0]]["slot"] for b in o]
print("last 7 days, orphans:", len(o), "| slots from the fork point to the orphan's own slot: share within", {w: round(sum(x < w * 30 for x in age) / len(age), 3) for w in (12, 24, 48, 96, 144, 288, 576)})
d = collections.Counter("1" if FP[b["id"]][1] == 1 else "2" if FP[b["id"]][1] == 2 else "3+" for b in o); print("depth shares", {k: round(v / len(o), 3) for k, v in d.items()})
# branch families
fam = {}
for b in o: fam.setdefault(first[b["id"]], []).append(b)
L = sorted(((sub_end[f] - B[B[f]["parent"]]["slot"], len(v)) for f, v in fam.items()), reverse=True)
print("branches", len(L), "longest (slots from fork point to last block, blocks):", L[:8])
for w in (360, 720, 1440, 2880, 4320, 8640): print("  orphans in branches that last longer than", w, "slots:", round(sum(n for s, n in L if s > w) / len(o), 3))
# is the growth assumption of the TSI answer met?
cs = [B[i]["slot"] for i in main]
import bisect
for k, name in ((1000, "testnet k = 1000"), (2160, "k = 2160")):
    gap = 4 * k * 30; mins = []
    for W in (12, 96, 288):
        n = gap - W * 30
        m = min(bisect.bisect_left(cs, s + n) - bisect.bisect_left(cs, s) for s in range(cs[0], cs[-1] - n, 600))
        mins.append((W, n, m))
    print(name, "fewest canonical blocks in 4k/f - W/f slots (W, slots, blocks):", mins, "needed", k)
# longest losing branch against k, and how far peers stay behind
print("deepest fork block in 14 days:", max(FP[b["id"]][1] for b in off))
# references of the canonical chain and how many name a block the scanner never got
ref = [b for b in B.values() if any(r in MAIN for r in b["uncle_in"] or [])]
for nm, a, z in (("last 7 days", lo, hi), ("14 days", LO, HI)):
    r = [b for b in ref if a <= b["slot"] < z]; print(nm, "uncles referenced by the canonical chain", len(r), "never obtained as a block by the scanner", sum(bool(b.get("header_only")) for b in r), round(sum(bool(b.get("header_only")) for b in r) / len(r), 3))
    can = [i for i in main if a <= B[i]["slot"] < z]; R = collections.defaultdict(list)
    for b in r:
        for x in b["uncle_in"]:
            if x in MAIN: R[x].append(b)
    print("   canonical blocks with a reference", round(len(R) / len(can), 3), "with a reference to such a block", round(sum(any(u.get("header_only") for u in v) for v in R.values()) / len(can), 4))
