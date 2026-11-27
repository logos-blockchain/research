"""What an honest proposal's uncle list tells about its proposer, by the kind of wait before a fork block is referenced.

N nodes, a random 8-regular gossip graph with lognormal links, Blend with 3 hops of 1 to 3 rounds each, f = 1/30, the drafted selection
(oldest fork point first, 4 at most, one per slot). For every canonical proposal: which other nodes, on the same parent at that slot,
would have written the same uncle list. Bits lost = log2(nodes on the parent / nodes with the same list). An observer is assumed to know
when every node received every block.

  none      referenced as soon as received on the broadcasting channel
  receipt   T_M after the node received it (the draft)
  slot      from T_M after the uncle's own slot
T_M = 3 (longest hop + 2)
"""
import sys, heapq, math, random
import numpy as np

LINK = 0.06
def graph(N, d, rng):
    while True:
        stubs = [i for i in range(N) for _ in range(d)]; rng.shuffle(stubs)
        E = {tuple(sorted((stubs[i], stubs[i + 1]))) for i in range(0, N * d, 2) if stubs[i] != stubs[i + 1]}
        adj = [[] for _ in range(N)]
        for a, b in E:
            w = rng.lognormvariate(math.log(LINK), 0.5) + 0.02
            adj[a].append((b, w)); adj[b].append((a, w))
        if all(len(x) >= d - 3 for x in adj): return adj

def flood(adj, src):
    N = len(adj); dist = [1e9] * N; dist[src] = 0; q = [(0.0, src)]
    while q:
        t, u = heapq.heappop(q)
        if t > dist[u]: continue
        for v, w in adj[u]:
            if t + w < dist[v]: dist[v] = t + w; heapq.heappush(q, (t + w, v))
    return np.array(dist)

class B:
    __slots__ = ("id", "parent", "slot", "h", "recv", "cast", "uncles", "who")

def run(seed, blocks, N=400, hop=(1, 3), f=1 / 30, TM=None):
    TM = 3 * (hop[1] + 2) if TM is None else TM
    rng = random.Random(seed); adj = graph(N, 8, rng); D = np.array([flood(adj, s) for s in range(N)])
    gen = B(); gen.id = 0; gen.parent = None; gen.slot = 0; gen.h = 0; gen.recv = np.zeros(N); gen.cast = np.zeros(N); gen.uncles = []; gen.who = 0
    allb = [gen]; recent = [gen]; slot = 0; W = 7200
    waits = ("none", "receipt", "slot"); lost = {w: [] for w in waits}; split = {w: 0 for w in waits}; par_bits = []; npro = 0
    def anc(x, lim):
        out = []
        while x is not None and x.slot >= lim: out.append(x); x = x.parent
        return out
    def elig(w, X, s):                       # per node
        if w == "none": return X.cast <= s
        if w == "receipt": return X.cast + TM <= s
        return (X.cast <= s) & (X.slot + TM <= s)
    def select(cands, chain_ids, occ):
        out, sl = [], set()
        for _, sx, i in cands:
            if len(out) == 4: break
            if sx in sl: continue
            sl.add(sx); out.append(i)
        return tuple(out)
    while len(allb) < blocks:
        slot += 1
        for _ in range(np.random.default_rng((seed, slot)).binomial(1, f)):
            n = rng.randrange(N); s = float(slot)
            recent = [b for b in recent if b.slot > slot - 1500 or b.id == 0] or recent
            # every node's preferred tip: highest block received; ties go to the first received
            best = None
            hs = np.array([b.h for b in recent]); R = np.array([b.recv for b in recent])      # blocks x nodes
            held = R <= s
            hm = np.where(held, hs[:, None], -1); top = hm.max(0)
            t = np.where((hm == top) & held, R, 1e18); tip = t.argmin(0)                       # index into recent, per node
            par = recent[tip[n]]; same = (tip == tip[n]); par_bits.append(math.log2(N / same.sum()))
            b = B(); b.id = len(allb); b.parent = par; b.slot = slot; b.h = par.h + 1; b.who = n
            chain = anc(par, slot - W - 200); ids = {x.id for x in chain}; occ = {x.slot for x in chain} | {u[1] for x in chain for u in x.uncles}
            C = []
            for X in recent:
                if X.id in ids or X.slot in occ or X.slot >= slot or X.id == 0: continue
                g = X; br = []
                while g is not None and g.id not in ids: br.append(g); g = g.parent
                if g is None or slot - g.slot > W: continue
                C.append((g.slot, X.slot, X.id, X, br))
            C.sort(key=lambda c: c[:3])
            npro += 1
            for w in waits:
                E = [np.logical_and.reduce([elig(w, y, s) for y in br]) for *_, br in C]
                if not E: lost[w].append(0.0); lst = (); 
                else:
                    M = np.array(E); lists = {}
                    key = [M[:, m].tobytes() for m in range(N)]; memo = {}
                    res = []
                    for m in range(N):
                        k = key[m]
                        if k not in memo: memo[k] = select([c[:3] for c, e in zip(C, M[:, m]) if e], ids, occ)
                        res.append(memo[k])
                    lst = res[n]; eq = sum(1 for m in range(N) if same[m] and res[m] == lst); tot = int(same.sum())
                    lost[w].append(math.log2(tot / eq)); split[w] += eq < tot
                if w == "slot": chosen = lst
            b.uncles = [(i, next(c[1] for c in C if c[2] == i)) for i in chosen]
            t_b = s + sum(rng.randint(*hop) for _ in range(3)) + sum(rng.random() * 0.5 for _ in range(3))
            ex = rng.randrange(N); b.cast = t_b + D[ex]; b.recv = b.cast.copy()
            b.recv[n] = s                                  # the proposer holds its own block at once; it counts as broadcast when it comes back
            allb.append(b); recent.append(b)
    return npro, lost, split, par_bits, np.mean([x.max() - x.min() for x in D])

def report(name, nb, seeds=4, **kw):
    L = {w: [] for w in ("none", "receipt", "slot")}; SP = {w: 0 for w in L}; P = []; n = 0; sp = []
    for seed in range(seeds):
        npro, lost, split, par, spread = run(seed, nb, **kw)
        n += npro; P += par; sp.append(spread)
        for w in L: L[w] += lost[w]; SP[w] += split[w]
    se = lambda k: 100 * math.sqrt(max(k, 1)) / n
    print(f"{name}: {n} proposals, gossip spread {np.mean(sp):.2f} s; the choice of the parent: {np.mean(P):.4f} bits a proposal")
    for w in L: print(f"   wait {w:8s}: uncle list differs between nodes in {100 * SP[w] / n:5.2f} +- {se(SP[w]):.2f} % of the proposals ({SP[w]}), {np.mean(L[w]):.5f} bits a proposal")

if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    report("sanity, wait 0 s in all three", 1500, 2, TM=0)
    report("hops of 1-3 s", nb)
    report("hops of 1-12 s", nb, hop=(1, 12))
    LINK = 0.25
    report("hops of 1-3 s, slow links", nb)
    report("hops of 1-12 s, slow links", nb, hop=(1, 12))
