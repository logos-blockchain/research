"""Toy network that runs the drafted chain maintenance: adoptable chains, step 8, pruning, uncle downloads.

No cryptography: a lottery win is a coin flip. Every node follows the same rules, except `forge` nodes, which put
entries that name blocks nobody has (or the wrong slot) into their own blocks.
"""
import random, itertools, sys
from dataclasses import dataclass, field

@dataclass(eq=False)
class Block:
    id: int; parent: "Block"; slot: int; h: int; entries: list = field(default_factory=list); forged: bool = False

class P:                                    # parameters
    def __init__(s, k=12, f=1/5, W=12, U=4, n=12): s.k, s.f, s.w, s.U, s.n = k, f, int(W / f), U, n

GEN = Block(0, None, 0, 0)

def anc(b):
    while b is not None: yield b; b = b.parent
def lca(a, b):
    while a is not b:
        if a.h >= b.h: a = a.parent
        else: b = b.parent
    return a

class Node:
    def __init__(s, p, i): s.p, s.i = p, i; s.T = {0: GEN}; s.imm = s.c = GEN; s.up = True; s.cast = {}; s.unres = 0
    def valid(s, u, A):
        X = s.T.get(u[0])
        if X is None: return False
        G = lca(X, A)
        return X is not G and u[1] == X.slot < A.slot and A.slot - G.slot <= s.p.w
    def chain_bad(s, b, only_missing=False):
        out = []; d = 0
        for A in anc(b):
            if A is s.imm: return out
            if d < s.p.k: out += [(A, u) for u in A.entries if (u[0] not in s.T if only_missing else not s.valid(u, A))]
            d += 1
        return None                          # does not contain B_imm
    def adoptable(s, b): r = s.chain_bad(b); return r == [] 
    def step8(s, b):
        g = lca(b, s.imm); return g is s.imm or g.slot > s.imm.slot - s.p.w
    def on_block(s, b, online=True):
        if b.id in s.T: return True
        if b.parent.id not in s.T or b.slot <= b.parent.slot or not s.step8(b): return False
        s.T[b.id] = b; s.choose(); return True
    def choose(s):
        best = s.c
        for b in s.T.values():               # longest adoptable chain, first seen wins ties; forks deeper than k ignored
            if b.h > best.h and s.depth(s.c, b) <= s.p.k and s.adoptable(b): best = b
        s.c = best; s.commit()
    def depth(s, a, b): return a.h - lca(a, b).h
    def commit(s):
        x = s.c
        for _ in range(s.p.k):
            if x.parent is None: break
            x = x.parent
        if x.h > s.imm.h: s.imm = x
        s.prune()
    def prune(s):
        for i in [i for i, b in s.T.items() if not s.step8(b) and lca(b, s.imm) is not b]: del s.T[i]
    def best(s):
        b = s.c
        for x in s.T.values():
            if x.h > b.h and s.depth(s.c, x) <= s.p.k: b = x
        return b
    def missing(s):
        out = []
        for x in s.T.values():
            if x.h > s.c.h and s.depth(s.c, x) <= s.p.k:
                m = s.chain_bad(x, only_missing=True)
                if m: out += m
        return {u[0] for _, u in out}
    def select(s, slot, par, now):
        occ = {a.slot for a in anc(par)} | {u[1] for a in anc(par) for u in a.entries}
        on = set(a.id for a in anc(par)); c = []
        for X in s.T.values():
            if X.id in on or X.slot >= slot or X.slot in occ: continue
            g = X; ok = True
            while g.id not in on: ok &= s.cast.get(g.id, 10**9) + 2 <= now; g = g.parent
            if slot - g.slot <= s.p.w and ok: c.append((g.slot, X.slot, X.id))
        c.sort(); out, sl = [], set()
        for _, t, i in c:
            if len(out) < s.p.U and t not in sl: sl.add(t); out.append((i, t))
        return out

class Net:
    def __init__(s, p, seed, forge=(), delay=(0, 1, 2)):
        s.p, s.r = p, random.Random(seed); s.N = [Node(p, i) for i in range(p.n)]; s.ids = itertools.count(1)
        s.q = []; s.slot = 0; s.forge = set(forge); s.all = {0: GEN}; s.delay = delay; s.cut = None; s.adopt = {}
    def linked(s, a, b): return s.N[a].up and s.N[b].up and (s.cut is None or (a in s.cut) == (b in s.cut))
    def send(s, i, b):
        for j in range(s.p.n):
            if j == i: s.q.append((s.slot, j, b)) ; continue
            s.q.append((s.slot + 1 + s.r.choice(s.delay), j, b))
    def ask(s, j, bid):                      # download from up to 4 random linked peers, with the branch
        peers = [a for a in range(s.p.n) if a != j and s.linked(a, j)]
        for a in s.r.sample(peers, min(4, len(peers))):
            if bid in s.N[a].T: return [b for b in reversed(list(anc(s.N[a].T[bid]))) if b.id not in s.N[j].T]
        return None
    def deliver(s, j, b, src):
        n = s.N[j]; n.cast.setdefault(b.id, s.slot)
        if n.on_block(b): return
        if b.parent.id not in n.T:           # orphan: download ancestors
            got = s.ask(j, b.id) or (s.ask(j, b.parent.id) or []) + [b]
            for x in got:
                if not n.on_block(x): break
    def uncles(s, j):
        n = s.N[j]
        for bid in list(n.missing()):
            for x in s.ask(j, bid) or []:
                if not n.on_block(x): break
    def step(s, propose=True):
        s.slot += 1
        due = [m for m in s.q if m[0] <= s.slot]; s.q = [m for m in s.q if m[0] > s.slot]
        s.r.shuffle(due)
        for _, j, b in due:
            if s.N[j].up and (s.cut is None or b.maker in (None,) or (b.maker in s.cut) == (j in s.cut)): s.deliver(j, b, b.maker)
        for j in range(s.p.n):
            if s.N[j].up: s.uncles(j)
        if propose:
            for i in range(s.p.n):
                n = s.N[i]
                if n.up and s.r.random() < s.p.f / s.p.n:
                    par = n.c; b = Block(next(s.ids), par, s.slot, par.h + 1)
                    b.maker = i; b.entries = n.select(s.slot, par, s.slot)
                    if i in s.forge:
                        b.entries = [(10**6 + b.id * 4 + z, max(0, s.slot - 1 - z)) for z in range(s.p.U)]; b.forged = True
                    s.all[b.id] = b; s.send(i, b)
    def check(s):
        for n in s.N:
            if n.up: assert n.chain_bad(n.c) == [], "c_loc not adoptable"
def common_prefix(net, nodes):
    tips = [net.N[i].c for i in nodes]; x = tips[0]
    for t in tips[1:]: x = lca(x, t)
    return x, max(t.h for t in tips) - x.h

GEN.maker = None
def scenario(name, fn, runs=6):
    print(name); 
    for r in fn(runs): print("   ", r)

def honest(runs):
    for k, W in ((12, 12), (10, 12), (4, 12), (12, 0)):
        bad = deep = ent = 0; gaps = []
        for s in range(runs):
            net = Net(P(k=k, W=W), s)
            for _ in range(700): net.step(); net.check()
            x, gap = common_prefix(net, range(net.p.n)); gaps.append(gap)
            ch = list(anc(net.N[0].c)); ent += sum(len(b.entries) for b in ch)
            deep += sum(1 for b in ch for u in b.entries if u[0] in net.all and net.all[u[0]].parent not in set(anc(b)))
        yield f"k={k:2d} W={W:2d} (window {int(W*5)} slots): divergence at the end at most {max(gaps)} blocks in {runs} runs; {ent} entries on the chains, {deep} deeper than the first fork block"

def cutoff(runs):
    for hours, k in (("long", 12),):
        ok = 0; need = []
        for s in range(runs):
            net = Net(P(k=k, n=12), s)
            for _ in range(150): net.step()
            net.cut = {11}; h0 = net.N[0].c.h
            while net.N[0].c.h < h0 + 4 * k: net.step()          # peers move 4k blocks on; the node keeps running
            net.cut = None; t0 = net.slot
            for _ in range(60):
                net.step(); net.check()
            x, gap = common_prefix(net, range(12)); ok += gap <= 3
        yield f"a node cut off while its peers add {4*k} blocks (k = {k}), never restarted: rejoined in {ok} of {runs} runs"

def fresh(runs):
    ok = 0; fetched = []
    for s in range(runs):
        net = Net(P(k=12), s); net.N[11].up = False
        for _ in range(500): net.step()
        net.N[11].up = True
        for _ in range(60): net.step(); net.check()
        x, gap = common_prefix(net, range(12)); ok += gap <= 3
        fetched.append(sum(1 for b in net.N[11].T.values() if b not in set(anc(net.N[11].c))))
    yield f"a node that starts from genesis after 500 slots: on the same chain in {ok} of {runs} runs; fork blocks it ended up holding {fetched}"

def forged(runs):
    worst = 0; on_chain = 0; gaps = []
    for s in range(runs):
        net = Net(P(k=12), s, forge={0, 1, 2}); net.N[11].up = False
        for t in range(700):
            if t == 350: net.N[11].up = True
            net.step(); net.check()
        x, gap = common_prefix(net, range(3, 12)); gaps.append(gap)
        on_chain += sum(b.forged for b in anc(net.N[5].c)) + sum(b.forged for b in anc(net.N[11].c))
    yield f"a quarter of the wins forge their entries: forged blocks on honest chains {on_chain}, honest divergence at most {max(gaps)} blocks; the node that joined in the middle included"

def restart(runs):
    for keep in (True, False):
        ok = 0
        for s in range(runs):
            net = Net(P(k=12, n=10), s)
            for _ in range(300): net.step()
            for n in net.N:                                      # every node restarts; blocks of the last slots still in flight are lost
                if not keep:
                    chain = {b.id: b for b in anc(n.c)}; n.T = chain
            net.q = []
            tips = {n.c.id for n in net.N}
            for _ in range(80): net.step()
            x, gap = common_prefix(net, range(net.p.n)); ok += gap <= 3
        yield f"every node restarts at once, {'the block tree kept' if keep else 'only the own chain kept'}: one chain again in {ok} of {runs} runs"

def deepfork(runs):
    """Every entry of every block that descends from a node's B_imm names a block the node can hold."""
    n_pairs = below = 0
    for s in range(runs):
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
                            n_pairs += 1; assert n.step8(X), "valid entry names a block step 8 rejects"
                            if lca(X, n.imm) is not n.imm: below += 1
    yield f"{n_pairs} (node, block, entry) triples, {below} with the fork point below B_imm: step 8 admits every uncle"

if __name__ == "__main__":
  scenario("1. honest network", honest); scenario("2. cut off for longer than k blocks", cutoff); scenario("3. fresh node", fresh)
  scenario("4. forged entries", forged); scenario("5. coordinated restart", restart); scenario("6. uncles around the latest immutable block", deepfork)
