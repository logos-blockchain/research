"""Load the testnet block tree (14 days up to 2026-11-24) and find the canonical chain."""
import gzip, json, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
def load(name):
    """A file of data/: name.json.gz or name.json."""
    p = os.path.join(HERE, "data", name)
    return json.load(gzip.open(p + ".json.gz") if os.path.exists(p + ".json.gz") else open(p + ".json"))
_d = load("tree")
B = {b["id"]: b for b in _d["blocks"]}
LO = min(b["slot"] for b in B.values()); HI = max(b["slot"] for b in B.values())
tip = max((b for b in B.values() if not b.get("header_only")), key=lambda b: (b["height"], -b["slot"]))
main = []; x = tip["id"]
while x in B: main.append(x); x = B[x]["parent"]
main.reverse(); MAIN = set(main)
def settled(b): return b["slot"] <= tip["slot"] - 400
FP = {}                                     # fork point and depth of every block off the chain
def fork(i):
    path = []; x = i
    while x in B and x not in MAIN and x not in FP: path.append(x); x = B[x]["parent"]
    if x in FP: g, d = FP[x]
    elif x in MAIN: g, d = x, 0
    else: g, d = None, None
    for y in reversed(path):
        if g is None: FP[y] = (None, None)
        else: d += 1; FP[y] = (g, d)
    return FP.get(i, (i, 0))
for i in list(B):
    if i not in MAIN: fork(i)
