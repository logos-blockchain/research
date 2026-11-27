"""How soon after its slot does a peer follow a block, among the peers that follow it at all within 600 s?

A delay near the broadcast time means the peer got the block on the broadcasting channel. A much later one means that it
fetched it, or came back from another branch. `first_with` is when the scanner first saw the block on the peer's own chain, and
`last_without` the scan before it, so the true time lies between the two.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import load
s = load("sample")
spread = load("spread")
def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]
for k, ids in s.items():
    up, lo, n, never, gap = [], [], 0, 0, []
    per_block = []
    for i in ids:
        d = spread[i]
        u = []
        for p in d["peers"]:
            if not p["seen"]: continue
            n += 1
            if p["first_with"] is None: never += 1; continue
            t1 = (p["first_with"] - d["slot_ms"]) / 1000
            t0 = (p["last_without"] - d["slot_ms"]) / 1000 if p["last_without"] else None
            up.append(t1); u.append(t1)
            if t0 is not None: lo.append(t0); gap.append(t1 - t0)
        if u: per_block.append(u)
    print(f"{k}: {len(ids)} blocks, {n} (block, peer) pairs, {never} never within 600 s; scan interval median {q(gap,.5):.1f} s, 90 % {q(gap,.9):.1f} s")
    if not up: continue
    for T in (5, 10, 15, 20, 30, 60, 120, 300):
        print(f"    among the peers that followed it: by {T:3d} s {sum(t <= T for t in up)/len(up):.3f}   (certainly later than {T} s: {sum(t > T for t in lo)/max(1,len(lo)):.3f})")
