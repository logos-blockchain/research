"""Adoption rules compared: 'chain' = fewer than k descendants on the chain, every block after B_imm;
'drafted' = blocks after the common ancestor with c_loc that have no descendant in T k or more blocks higher."""
import sys
from adopt import *

class N2(Node):
    rule = "drafted"
    def tops(s):
        top = {}
        for b in sorted(s.T.values(), key=lambda b: -b.h):
            top[b.id] = max(top.get(b.id, 0), b.h); x = b.parent
            if x is not None: top[x.id] = max(top.get(x.id, 0), top[b.id])
        return top
    def chain_bad(s, b, only_missing=False):
        if s.rule == "chain": return Node.chain_bad(s, b, only_missing)
        if lca(b, s.imm) is not s.imm: return None
        stop = lca(b, s.c); out = []; top = s.top if getattr(s, "top", None) else s.tops()
        x = b
        while x is not stop:
            if top.get(x.id, x.h) - x.h < s.p.k:
                out += [(x, u) for u in x.entries if (u[0] not in s.T if only_missing else not s.valid(u, x))]
            x = x.parent
        return out
    def choose(s):
        s.top = s.tops(); best = s.c
        for b in s.T.values():
            if b.h > best.h and s.depth(s.c, b) <= s.p.k and s.chain_bad(b) == []: best = b
        s.c = best; s.commit(); s.top = None
    def missing(s):
        s.top = s.tops(); out = []
        tips = {i for i in s.T} - {b.parent.id for b in s.T.values() if b.parent is not None}
        for i in tips:
            x = s.T[i]
            if x.h > s.c.h and s.depth(s.c, x) <= s.p.k: out += s.chain_bad(x, only_missing=True) or []
        s.top = None
        return {u[0] for _, u in out}
class Net2(Net):
    def __init__(s, p, seed, rule="drafted", **kw):
        super().__init__(p, seed, **kw); s.N = [N2(p, i) for i in range(p.n)]
        for n in s.N: n.rule = rule

def capture(rule, k=40, seed=1):
    """A node cut off at its tip t receives the honest chain H in full, then a fork F without entries, then H's uncles."""
    r = random.Random(seed); p = P(k=k); n = N2(p, 0); n.rule = rule
    ids = itertools.count(1); sl = 0; tip = GEN
    for _ in range(50): sl += 5; tip = Block(next(ids), tip, sl, tip.h + 1); n.on_block(tip)
    t = tip; H = []; X = {}; x = t; s1 = sl
    for j in range(5 * k):
        s1 += 5; par = x; x = Block(next(ids), par, s1, par.h + 1)
        if r.random() < 0.1 and H: 
            u = Block(next(ids), H[-1].parent, H[-1].slot + 1, H[-1].h); X[u.id] = u; x.entries = [(u.id, u.slot)]
        H.append(x)
    F = []; x = t; s2 = sl
    for j in range(3 * k): s2 += 8; x = Block(next(ids), x, s2, x.h + 1); F.append(x)
    for b in H: n.on_block(b)
    a = n.c
    for b in F: n.on_block(b)
    for u in X.values():
        if n.step8(u) and u.parent.id in n.T: n.on_block(u)
    n.choose()
    on = "H" if n.c in H else "F" if n.c in F else "old tip"
    return f"after H: {'H+' + str(H.index(a)+1) if a in H else 'old tip'}; after F and the uncles: {on}, B_imm on {'H' if n.imm in H else 'F' if n.imm in F else 'the old chain'}"

def lost(rule, k, seeds=10):
    stuck = 0
    for s in range(seeds):
        net = Net2(P(k=k, n=10), s, rule)
        for _ in range(250): net.step()
        for n in net.N: n.T = {b.id: b for b in anc(n.c)}        # every node restarts and loses its forks
        h0 = max(n.c.h for n in net.N)
        for _ in range(120): net.step()
        stuck += max(n.c.h for n in net.N) < h0 + 10
    return f"chain halted in {stuck} of {seeds} runs"

def general(rule):
    out = []
    for k, W in ((12, 12), (10, 12), (4, 12), (12, 0)):
        g = []
        for s in range(5):
            net = Net2(P(k=k, W=W), s, rule)
            for _ in range(600): net.step()
            g.append(common_prefix(net, range(net.p.n))[1])
        out.append(f"k={k} W={W}: {max(g)}")
    return "largest divergence at the end " + ", ".join(out)
def rejoin(rule, k=12, seeds=6):
    ok = 0
    for s in range(seeds):
        net = Net2(P(k=k), s, rule)
        for _ in range(150): net.step()
        net.cut = {11}; h0 = net.N[0].c.h
        while net.N[0].c.h < h0 + 4 * k: net.step()
        net.cut = None
        for _ in range(60): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"rejoined in {ok} of {seeds}"
def fresh(rule, k=12, seeds=6):
    ok = 0
    for s in range(seeds):
        net = Net2(P(k=k), s, rule); net.N[11].up = False
        for _ in range(400): net.step()
        net.N[11].up = True
        for _ in range(60): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"fresh node on the chain in {ok} of {seeds}"
def forged(rule, seeds=6):
    bad = 0; g = []
    for s in range(seeds):
        net = Net2(P(k=12), s, rule, forge={0, 1, 2}); net.N[11].up = False
        for t in range(600):
            if t == 300: net.N[11].up = True
            net.step()
        bad += sum(b.forged for i in range(3, 12) for b in anc(net.N[i].c)); g.append(common_prefix(net, range(3, 12))[1])
    return f"forged blocks on honest chains {bad}, divergence at most {max(g)}"
if __name__ == "__main__":
    for rule in ("chain", "drafted"):
        print("rule:", rule)
        for sd in (1, 2, 3): print("  captured?", capture(rule, seed=sd))
        for k in (12, 60): print(f"  lost forks, k = {k}:", lost(rule, k))
        print("  ", general(rule)); print("  ", rejoin(rule)); print("  ", fresh(rule)); print("  ", forged(rule))
