"""Mutations of adopt.py: each rule, when broken, must show up."""
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import adopt
from adopt import *

def rejoin(runs=6, k=12):
    ok = 0
    for s in range(runs):
        net = Net(P(k=k, n=12), s)
        for _ in range(150): net.step()
        net.cut = {11}; h0 = net.N[0].c.h
        while net.N[0].c.h < h0 + 4 * k: net.step()
        net.cut = None
        for _ in range(60): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"rejoined in {ok} of {runs}"
orig_bad, orig8 = Node.chain_bad, Node.step8

print("baseline:", rejoin())
def all_blocks(s, b, only_missing=False):               # mutation: check every block after B_imm of the cut-off node, not only the last k
    out = []
    for A in anc(b):
        if A is s.imm: return out
        out += [(A, u) for u in A.entries if (u[0] not in s.T if only_missing else not s.valid(u, A))]
    return None
Node.chain_bad = all_blocks
print("entries of all blocks after B_imm must be valid:", rejoin())
Node.chain_bad = orig_bad

def strict8(s, b): return lca(b, s.imm) is s.imm        # mutation: forks below B_imm are not admitted and are pruned
Node.step8 = strict8
def deep():
    miss = tot = 0
    for s in range(6):
        net = Net(P(k=4, W=12), s, delay=(0, 1, 4, 8))
        for _ in range(500):
            net.step()
            if net.slot % 50 == 0:
                for n in net.N:
                    for A in net.all.values():
                        if A is n.imm or n.imm not in set(anc(A)): continue
                        for u in A.entries:
                            X = net.all.get(u[0])
                            if X is None: continue
                            G = lca(X, A)
                            if X is G or not (u[1] == X.slot < A.slot and A.slot - G.slot <= n.p.w): continue
                            tot += 1; miss += not n.step8(X)
    return f"{miss} of {tot} valid entries name a block the node can no longer hold"
print("step 8 and pruning at B_imm:", deep())
def div(k):
    out = []
    for s in range(6):
        net = Net(P(k=k, W=12), s, delay=(0, 1, 4, 8))
        for _ in range(700): net.step()
        out.append(common_prefix(net, range(net.p.n))[1])
    return out
print("  divergence after 700 slots, k = 4:", div(4))
Node.step8 = orig8
print("  divergence after 700 slots, k = 4, drafted step 8:", div(4))

def nofetch(s, j): pass
orig_u = Net.uncles; Net.uncles = nofetch
def fresh():
    ok = 0
    for s in range(6):
        net = Net(P(k=60), s); net.N[11].up = False
        for _ in range(250): net.step()
        net.N[11].up = True
        for _ in range(60): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"a fresh node is on the chain in {ok} of 6 runs"
print("no uncle downloads:", fresh()); Net.uncles = orig_u; print("with uncle downloads:", fresh())

def restart(keep, k=300):
    behind = []
    for s in range(10):
        net = Net(P(k=k, n=10, f=1/3), s, delay=(0, 2, 5))
        for _ in range(120): net.step()
        for n in net.N:
            if not keep: n.T = {b.id: b for b in anc(n.c)}
        net.q = []
        for _ in range(60): net.step()
        behind.append(common_prefix(net, range(net.p.n))[1])
    return f"divergence 60 slots after a coordinated restart: {behind}"
print("block tree kept:", restart(True)); print("own chain only:", restart(False))
