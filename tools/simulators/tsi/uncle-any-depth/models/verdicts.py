"""Three ways to treat a reference, on the toy network.

drafted   undecided or wrong: the chain is not followed until the block is k deep; the block stays in T
wrong=bad undecided as drafted; a node that holds the uncle and sees that the reference is wrong drops the block for good
age       a block waits outside T until its uncles are held and right; a block older than k/f slots is taken as it is
"""
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import adopt, adopt2, option_ab
from adopt import *
from adopt2 import N2, Net2, common_prefix
from option_ab import NA, NetA

class NH(N2):                                                 # wrong=bad
    def __init__(s, p, i): super().__init__(p, i); s.bad = set()
    def wrong(s, u, b):
        X = s.T.get(u[0]); return X is not None and not s.valid(u, b)
    def drop(s, b):
        dead = {b.id}
        for x in sorted(s.T.values(), key=lambda x: x.h):
            if x.parent is not None and x.parent.id in dead: dead.add(x.id)
        if any(x.id in dead for x in anc(s.c)):
            x = s.c
            while x.id in dead: x = x.parent
            s.c = x
        s.bad |= dead
        for i in dead: s.T.pop(i, None)
    def on_block(s, b, online=True):
        if b.id in s.bad or (b.parent is not None and b.parent.id in s.bad): s.bad.add(b.id); return False
        new = b.id not in s.T; ok = super().on_block(b)
        if new and ok:
            for x in [x for x in s.T.values() if any(u[0] == b.id for u in x.entries)] + [b]:
                if x.id in s.T and any(s.wrong(u, x) for u in x.entries) and s.c is not x: s.drop(x)
            s.choose()
        return ok and b.id in s.T

class NetH(Net2):
    def __init__(s, p, seed, **kw): super().__init__(p, seed, "drafted", **kw); s.N = [NH(p, i) for i in range(p.n)]

class NG(NA):                                                 # age
    now = 0; AGE = 60
    def verdict(s, b): return "valid" if s.now - b.slot >= s.AGE else super().verdict(b)
class NetG(NetA):
    def __init__(s, p, seed, **kw): super().__init__(p, seed, **kw); s.N = [NG(p, i) for i in range(p.n)]
    def step(s, propose=True):
        for n in s.N: n.now = s.slot + 1
        super().step(propose)

def mk(opt, p, s, **kw): return {"drafted": lambda: Net2(p, s, "drafted", **kw), "wrong=bad": lambda: NetH(p, s, **kw), "age": lambda: NetG(p, s, **kw)}[opt]()

def attack(opt, seeds=10, share=3, slots=700, n=12, held=6):
    """Nodes 0..share-1 collude. On a win they first make X and give it only to `held` honest nodes; on the next win they
    make A beside the current tip, with a reference to X at the wrong slot, and send A to everybody."""
    worst = []; final = []; stuck = 0
    for sd in range(seeds):
        net = mk(opt, P(k=12, n=n), sd); r = random.Random(sd + 99); X = None; gaps = []; honest = range(share, n)
        orig = net.r.random
        for t in range(slots):
            net.slot += 0
            # colluders do not propose through Net.step: take them down for the honest part of the step
            for i in range(share): net.N[i].up = True
            cut = net.p.f
            real_up = [net.N[i].up for i in range(n)]
            for i in range(share): net.N[i].mute = True
            step_once(net, share)
            if r.random() < net.p.f * share / n:
                c = net.N[share].c if X is None else max((net.N[i].c for i in honest), key=lambda c: c.h)
                if X is None:
                    X = Block(next(net.ids), c, net.slot, c.h + 1) if c.slot < net.slot else None
                    if X is not None:
                        X.maker = 0; net.all[X.id] = X
                        for i in range(share, share + held): net.q.append((net.slot + 1, i, X))
                elif c.parent is not None and c.slot < net.slot:
                    A = Block(next(net.ids), c.parent, net.slot, c.h); A.maker = 0; A.entries = [(X.id, X.slot - 1)]; A.forged = True
                    net.all[A.id] = A
                    for i in range(n): net.q.append((net.slot + 1, i, A))
                    X = None
            if t > 100: gaps.append(common_prefix(net, honest)[1])
        worst.append(max(gaps)); final.append(common_prefix(net, honest)[1])
    return f"{opt:10s} worst divergence of honest nodes: median {sorted(worst)[len(worst)//2]}, max {max(worst)} blocks; at the end {sorted(final)}"

def step_once(net, share):
    """Net.step, but only honest nodes propose (colluders relay nothing and serve nothing)."""
    net.slot += 1
    for nd in net.N:
        if hasattr(nd, "now"): nd.now = net.slot
    due = [m for m in net.q if m[0] <= net.slot]; net.q = [m for m in net.q if m[0] > net.slot]; net.r.shuffle(due)
    for _, j, b in due: net.deliver(j, b, b.maker)
    for j in range(net.p.n): net.uncles(j)
    for i in range(share, net.p.n):
        nd = net.N[i]
        if net.r.random() < net.p.f / net.p.n:
            par = nd.c; b = Block(next(net.ids), par, net.slot, par.h + 1); b.maker = i; b.entries = nd.select(net.slot, par, net.slot)
            net.all[b.id] = b; net.send(i, b)

if __name__ == "__main__":
    import sys
    option_ab.mk = lambda opt, p, s, **kw: mk(opt, p, s, **kw)
    for opt in ("drafted", "wrong=bad", "age"):
        print(opt)
        for f in (option_ab.honest, option_ab.fresh, option_ab.rejoin, option_ab.lost): print("   ", f(opt))
    for held in (3, 5, 6): 
        print("wrong reference, uncle given to", held, "of 9 honest nodes")
        for opt in ("drafted", "wrong=bad", "age"): print("   ", attack(opt, held=held))
