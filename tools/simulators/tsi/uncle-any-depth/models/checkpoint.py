"""A node that starts from a checkpoint: how long until it follows the honest chain, by checkpoint depth.

The drafted chain maintenance of adopt2.py (N2, rule "drafted"). The provider is an honest node. The new node holds the
checkpoint block only: no block before it, no fork of it. Two ways to pick the checkpoint:

  depth   the block m blocks below the tip of the provider's chain
  slots   the highest block at least W/f slots before the provider's B_imm (the k-deep block)

Usage: checkpoint.py
"""
import random, statistics as st
from adopt2 import *


class Cp(N2):
    """A node whose tree starts at the checkpoint. Blocks before it do not exist for it."""
    def __init__(s, p, i, cp):
        super().__init__(p, i)
        s.cp = cp; s.T = {cp.id: cp}; s.imm = s.c = cp

    def step8(s, b):
        # a block that does not descend from the checkpoint has no parent in T; on_block already refuses it
        return super().step8(b)

    def valid(s, u, A):
        return super().valid(u, A)

    def commit(s):
        x = s.c
        for _ in range(s.p.k):
            if x is s.cp or x.parent is None: break
            x = x.parent
        if x.h > s.imm.h: s.imm = x
        s.prune()

    def choose(s):
        # Bootstrap rule as plain longest adoptable chain, any fork depth (every fork here is short)
        s.top = s.tops_cp(); best = s.c
        for b in s.T.values():
            if b.h > best.h and s.chain_bad(b) == []: best = b
        s.c = best; s.top = None
        # B_imm stays at the checkpoint under the Bootstrap rule

    def tops_cp(s):
        top = {}
        for b in sorted(s.T.values(), key=lambda b: -b.h):
            top[b.id] = max(top.get(b.id, 0), b.h); x = b.parent
            if x is not None and x.id in s.T: top[x.id] = max(top.get(x.id, 0), top[b.id])
        return top

    def missing(s):
        s.top = s.tops_cp(); out = []
        tips = {i for i in s.T} - {b.parent.id for b in s.T.values() if b.parent is not None}
        for i in tips:
            x = s.T[i]
            if x.h > s.c.h: out += s.chain_bad(x, only_missing=True) or []
        s.top = None
        return {u[0] for _, u in out}


def run(k, W, pick, seed, f=1 / 5, n=10, warm=None):
    p = P(k=k, W=W, f=f, n=n)
    net = Net2(p, seed, delay=(0, 1, 2, 4, 8))             # many forks
    need = int((k + 4 * W + 40) / f)
    for _ in range(warm or need + int(4 * k / f)): net.step()
    prov = net.N[0]; chain = list(anc(prov.c))              # tip first
    kdeep = chain[k]
    if pick[0] == "depth":
        cp = chain[pick[1]]
    else:
        cp = next(b for b in chain if b.slot <= kdeep.slot - p.w + pick[1])
    new = Cp(p, n, cp)
    net.N.append(new); p2 = P(k=k, W=W, f=f, n=n + 1)       # the new node takes part as a listener
    net.p.n = n + 1
    # it never proposes: proposals come from nodes 0..n-1 only
    t0 = net.slot; h0 = chain[0].h; cp_depth = chain[0].h - cp.h
    # Initial block download: the provider's chain, parent first
    for b in reversed(chain[: cp_depth]): new.on_block(b)
    follow = None
    entries = sum(len(b.entries) for b in chain[: cp_depth])
    outside = [(b, u) for b in chain[: cp_depth] for u in b.entries if u[0] in net.all and lca(net.all[u[0]], b).h < cp.h]
    behind0 = None
    for t in range(4 * p.w + int(40 / f)):
        # uncles: several tries per slot
        for _ in range(3):
            for bid in list(new.missing()):
                for x in net.ask(n, bid) or []:
                    if x.parent is None or (x.parent.id not in new.T): continue
                    new.on_block(x)
        if behind0 is None: behind0 = prov.c.h - new.c.h
        if prov.c.h - new.c.h <= 2 and follow is None:
            follow = net.slot - t0; break
        # one slot of the honest network; the new node gets every block
        before = set(net.all)
        net.p.n = n
        net.step()
        net.p.n = n + 1
        for b in list(anc(prov.c))[:40][::-1]:
            if b.id not in new.T and b.parent is not None and b.parent.id in new.T: new.on_block(b)
        new.choose()
    return dict(depth=cp_depth, slots=kdeep.slot - cp.slot, entries=entries, outside=len(outside), behind0=behind0, follow=follow)


if __name__ == "__main__":
    f = 1 / 5
    for k, W in ((12, 12), (30, 12), (60, 24), (40, 40)):
        w = int(W / f)
        for name, pick in (("exactly k deep", ("depth", k)), ("W/f slots before the k-deep block", ("slots", 0))):
            rs = [run(k, W, pick, sd, f) for sd in range(8)]
            fol = [r["follow"] for r in rs]
            print(f"k={k} W={W} (window {w} slots) checkpoint {name:36s}: entries with the fork point before it "
                  f"{[r['outside'] for r in rs]}, blocks behind after the download {[r['behind0'] for r in rs]}, "
                  f"slots until it follows {fol} (median {st.median([x if x is not None else 10**6 for x in fol])})")
