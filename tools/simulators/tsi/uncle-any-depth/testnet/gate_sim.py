"""Effect of the adoption rule on a network that spreads blocks as the testnet does: half of the producers reach only about 9 % of the
nodes by broadcast, 15 % of the nodes hear broadcasts late. Compares: no gate (signed headers travel in the block, as today, but any
depth) with the gate (a chain is followed only once every referenced block is held; missing ones are fetched from random peers)."""
import heapq, random, sys, statistics as st, itertools

class Blk:
    __slots__ = ("id", "par", "slot", "h", "refs", "maker", "born")
    def __init__(s, i, par, slot, refs, maker): s.id, s.par, s.slot, s.refs, s.maker = i, par, slot, refs, maker; s.h = par.h + 1 if par else 0; s.born = slot

def run(gate, seed, n=60, rate=0.054, T=40000, W=2880, U=4, ask=3, attempt=1.0, bad=0.5, reach_bad=0.09, slow=0.15, TM=15, gate_any=True):
    r = random.Random(seed); G = Blk(0, None, 0, (), -1); ids = itertools.count(1); allb = {0: G}
    goodsend = [r.random() >= bad for _ in range(n)]; slown = [r.random() < slow for _ in range(n)]
    tree = [{0: 0.0} for _ in range(n)]; tip = [G] * n; kids = [dict() for _ in range(n)]; wait = [dict() for _ in range(n)]; heard = [dict() for _ in range(n)]
    ev = []; seq = itertools.count()
    push = lambda t, k, *a: heapq.heappush(ev, (t, next(seq), k, a))
    need = [dict() for _ in range(n)]                    # block id -> time first needed
    adopt = {}
    def anc(b):
        while b is not None: yield b; b = b.par
    def lca(a, b):
        while a is not b:
            if a.h >= b.h: a = a.par
            else: b = b.par
        return a
    def missing(i, b):
        g = lca(b, tip[i]); out = []; x = b
        while x is not g: out += [u for u in x.refs if u not in tree[i]]; x = x.par
        return out
    def consider(t, i):
        # longest adoptable tip among the known ones
        cand = sorted((b for b in leaves[i].values() if b.h > tip[i].h), key=lambda b: (-b.h, b.id))
        for b in cand:
            x = b
            while x.h > tip[i].h:
                m = missing(i, x) if gate else []
                if not m:
                    tip[i] = x; adopt.setdefault(x.id, {})[i] = t; break
                for u in m:
                    if u not in need[i]: need[i][u] = t; push(t + attempt, "fetch", i, u)
                x = x.par
    leaves = [dict() for _ in range(n)]
    def add(t, i, b):
        if b.id in tree[i]: return
        if b.par.id not in tree[i]:
            wait[i].setdefault(b.par.id, []).append(b)
            if b.par.id not in need[i]: need[i][b.par.id] = t; push(t + attempt, "fetch", i, b.par.id)
            return
        tree[i][b.id] = t; leaves[i].pop(b.par.id, None); leaves[i][b.id] = b
        if len(leaves[i]) > 60:
            for k in [k for k, x in leaves[i].items() if x.h < tip[i].h - 30]: leaves[i].pop(k)
        need[i].pop(b.id, None)
        for c in wait[i].pop(b.id, []): add(t, i, c)
        consider(t, i)
    def select(i, par, slot):
        on = set(); occ = set(); x = par
        while x is not None and x.slot >= slot - W - 400: on.add(x.id); occ.add(x.slot); occ |= {allb[u].slot for u in x.refs}; x = x.par
        c = []
        for k, tt in list(tree[i].items())[-400:]:
            b = allb[k]
            if b.id in on or b.slot < slot - W or b.slot >= slot or b.slot in occ or tt + TM > slot: continue
            g = b
            while g.id not in on and g.par is not None and g.slot >= slot - W: g = g.par
            if g.id in on and slot - g.slot <= W: c.append((g.slot, b.slot, b.id))
        c.sort(); out = []; sl = set()
        for _, s_, k in c:
            if len(out) < U and s_ not in sl: sl.add(s_); out.append(k)
        return tuple(out)
    t = 0.0
    while True:
        t += r.expovariate(rate)
        if t >= T: break
        push(t, "win", r.randrange(n))
    waits = []
    while ev:
        t, _, k, a = heapq.heappop(ev)
        if t > T + 600: break
        if k == "win":
            i = a[0]; par = tip[i]; s = int(t)
            if s <= par.slot: continue
            b = Blk(next(ids), par, s, select(i, par, s), i); allb[b.id] = b; add(t, i, b)
            p = 0.95 if goodsend[i] else reach_bad
            for j in range(n):
                if j != i and r.random() < p:
                    push(t + (r.expovariate(1 / 90) if slown[j] else r.lognormvariate(0.8, 0.7)), "recv", j, b)
        elif k == "recv": add(t, *a)
        elif k == "fetch":
            i, u = a
            if u in tree[i] or u not in need[i]: need[i].pop(u, None); continue
            ps = r.sample([j for j in range(n) if j != i], min(ask, n - 1))
            src = next((j for j in ps if u in tree[j]), None)
            if src is None: push(t + attempt, "fetch", i, u); continue
            waits.append(t - need[i].get(u, t)); chain = []
            x = allb[u]
            while x.id not in tree[i]: chain.append(x); x = x.par
            for x in reversed(chain): push(t + 0.3, "recv", i, x)
            push(t + 2.0, "fetch", i, u)
    best = max(tip, key=lambda b: b.h); on = {x.id for x in anc(best)}
    blocks = [b for b in allb.values() if 2000 < b.slot < T - 3000]; can = [b for b in blocks if b.id in on]
    cs = {b.slot for b in can}; cnt = cs | {allb[u].slot for b in can for u in b.refs}
    occ = {b.slot for b in blocks}
    def spread(sel, q):
        v = []
        for b in sel:
            a_ = sorted(x - b.slot for x in adopt.get(b.id, {}).values()); v.append(a_[int(q * n) - 1] if len(a_) >= int(q * n) else 999)
        return st.median(v) if v else float("nan")
    w = [b for b in can if b.refs]; wo = [b for b in can if not b.refs]
    return dict(orphans=1 - len(can) / len(blocks), refs=sum(len(b.refs) for b in can) / len(can), withref=len(w) / len(can), counted=len(cnt & occ) / len(occ),
                half=spread(can, .5), half_ref=spread(w, .5), half_no=spread(wo, .5), wait=st.median(waits) if waits else 0, wait90=sorted(waits)[int(.9 * len(waits))] if waits else 0)
def mean(gate, seeds=4, **kw):
    R = [run(gate, s, **kw) for s in range(seeds)]
    return {k: round(sum(x[k] for x in R) / len(R), 3) for k in R[0]}
if __name__ == "__main__":
    for kw in (dict(), dict(attempt=3.0), dict(ask=1), dict(attempt=10.0, ask=1), dict(bad=0.0, rate=1 / 30), dict(bad=0.0, rate=1 / 30, attempt=3.0)):
        for g in (False, True): print("gate" if g else "none", kw, mean(g, **kw), flush=True)
