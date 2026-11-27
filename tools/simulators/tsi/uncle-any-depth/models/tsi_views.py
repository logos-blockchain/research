"""Does the Total Stake Inference differ between nodes, or between competing chains, under the drafted rule?

Toy network of adopt.py with the drafted adoption rule and the epoch schedule of the specification (k = 12, f = 1/5, so
k/f = 60 slots: epoch 600, counted window 360, gap until the first use 240). The last node is blind: it never receives a
fork block and never downloads an uncle, it only copies blocks 3 deep on a peer's chain.
"""
import contextlib, io, sys
with contextlib.redirect_stdout(io.StringIO()):
    import adopt, adopt2
from adopt import *
from adopt2 import N2, Net2, common_prefix

KF = 60; EPOCH, WINDOW = 10 * KF, 6 * KF

class NV(N2):
    def __init__(s, p, i): super().__init__(p, i); s.held = {0}; s.imm_anc = {0}
    def on_block(s, b, online=True):
        ok = super().on_block(b)
        if ok: s.held.add(b.id)
        return ok
    def prune(s):                                            # same rule as Node.prune, without walking the settled chain
        x = s.imm
        while x.id not in s.imm_anc: s.imm_anc.add(x.id); x = x.parent
        for i in [i for i, b in s.T.items() if i not in s.imm_anc and not s.step8(b)]: del s.T[i]
    def leaves(s):
        par = {b.parent.id for b in s.T.values() if b.parent is not None}
        return [b for b in s.T.values() if b.id not in par]

class NetV(Net2):
    def __init__(s, p, seed, **kw):
        super().__init__(p, seed, "drafted", **kw); s.N = [NV(p, i) for i in range(p.n)]
        for n in s.N: n.rule = "drafted"
        s.blind = p.n - 1
    def send(s, i, b):
        for j in range(s.p.n):
            if j == s.blind: continue
            s.q.append((s.slot if j == i else s.slot + 1 + s.r.choice(s.delay), j, b))
    def uncles(s, j):
        if j == s.blind:
            if s.slot % 5 == 0:
                src = s.N[s.r.randrange(s.p.n - 1)]; x = src.c
                for _ in range(3): x = x.parent or x
                for b in reversed([b for b in anc(x) if b.id not in s.N[j].T]): s.N[j].on_block(b)
            return
        super().uncles(j)

def counted(tip, ep, keep=lambda A, u: True):
    """|occupied slots| of the window of epoch ep on the chain of tip: the drafted formula, with an optional filter."""
    lo, hi = ep * EPOCH, ep * EPOCH + WINDOW; out = set()
    for A in anc(tip):
        if A.parent is None or not lo <= A.slot < hi: continue
        out.add(A.slot)
        out |= {u[1] for u in A.entries if lo <= u[1] < hi and keep(A, u)}
    return len(out)

def run(seed, epochs=4, n=8, delay=(0, 1, 2, 3)):
    net = NetV(P(k=12, n=n), seed, delay=delay); net.N[net.blind].up = True
    r = dict(nodes=0, multi=0, leaves=0, eq_leaves=0, eq_nodes=0, boundaries=0, blind_eq=0, blind_lag=[], blind_unseen=[], seen_rel=[], deep_eq=0, mid=[], blind_prefix=0)
    real = NV.select
    while net.slot < epochs * EPOCH:
        # the blind node does not propose
        net.N[net.blind].up = True
        net.step()
        if net.slot % EPOCH == 0:
            ep = net.slot // EPOCH - 1; r["boundaries"] += 1; vals = []
            for i, nd in enumerate(net.N):
                cs = {counted(t, ep) for t in nd.leaves()}
                r["nodes"] += 1; r["leaves"] += len(nd.leaves()); r["multi"] += len(nd.leaves()) > 1; r["eq_leaves"] += len(cs) == 1
                vals.append(counted(nd.c, ep))
            r["eq_nodes"] += len(set(vals)) == 1
            b = net.N[net.blind]; full = counted(b.c, ep); best = max(nd.c.h for nd in net.N[:-1])
            r["blind_eq"] += full == vals[0]; r["blind_lag"].append(best - b.c.h)
            r["blind_prefix"] += b.c in set(anc(max((nd.c for nd in net.N[:-1]), key=lambda c: c.h)))
            ent = [(A, u) for A in anc(b.c) if ep * EPOCH <= A.slot < ep * EPOCH + WINDOW for u in A.entries]
            r["blind_unseen"].append((sum(u[0] not in b.held for _, u in ent), len(ent)))
            r["seen_rel"].append(counted(b.c, ep, lambda A, u: u[0] in b.held) / full - 1)
            r["deep_eq"] += counted(b.c, ep, lambda A, u: u[0] in b.held or b.c.h - A.h >= net.p.k) == full
        elif net.slot % EPOCH < WINDOW and net.slot % 7 == 0:
            for nd in net.N[:-1]:
                cs = [counted(t, net.slot // EPOCH) for t in nd.leaves() if t.h >= nd.c.h]          # tips as high as its own
                if len(cs) > 1: r["mid"].append(max(cs) - min(cs))
    return r

if __name__ == "__main__":
    tot = None
    for s in range(int(sys.argv[1]) if len(sys.argv) > 1 else 5):
        r = run(s)
        if tot is None: tot = r
        else:
            for k_, v in r.items(): tot[k_] = tot[k_] + v
    t = tot
    print(f"epoch boundaries {t['boundaries']}; node views {t['nodes']}, of which with competing chains {t['multi']} (chains compared {t['leaves']})")
    print(f"  all chains of a view give one count: {t['eq_leaves']} of {t['nodes']}; all nodes (blind one included) give one count: {t['eq_nodes']} of {t['boundaries']}")
    un = sum(a for a, _ in t['blind_unseen']); al = sum(b for _, b in t['blind_unseen'])
    print(f"  blind node: {un} of {al} counted references name a block it never held; its chain is a prefix of the longest one in {t['blind_prefix']} of {t['boundaries']}, behind by {min(t['blind_lag'])} to {max(t['blind_lag'])} blocks")
    print(f"  blind node, count equal to the others': {t['blind_eq']} of {t['boundaries']}")
    print(f"  if only held uncles counted: off by {100*min(t['seen_rel']):.1f} % to {100*max(t['seen_rel']):.1f} %; if held or k deep: equal in {t['deep_eq']} of {t['boundaries']}")
    print(f"while the window is open: competing chains of one view differ by up to {max(t['mid'])} slots, and differ in {sum(m > 0 for m in t['mid'])} of {len(t['mid'])} comparisons")
