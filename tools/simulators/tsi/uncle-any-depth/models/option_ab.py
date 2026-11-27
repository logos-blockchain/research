"""Option A (a block enters T only once every uncle it names is held and valid) against option B (the drafted adoption rule).
Careful A: a missing uncle leaves the block undecided (retried every slot); only a provably bad entry condemns it for good.
A-skip: careful A, with the check skipped for a block that has k or more known descendants in the download queue (validity by depth)."""
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import adopt, adopt2
from adopt import *
from adopt2 import Net2, N2, common_prefix

class NA(Node):
    """Validity rule: the block waits outside T in `pend` until its uncles are held."""
    def __init__(s, p, i): super().__init__(p, i); s.pend = {}; s.bad = set()
    def adoptable(s, b): return lca(b, s.imm) is s.imm        # nothing left to check: every block in T was checked
    def chain_bad(s, b, only_missing=False): return [] if lca(b, s.imm) is s.imm else None
    def verdict(s, b):
        for u in b.entries:
            if u[0] not in s.T: return "undecided"
            if not s.valid(u, b): return "invalid"
        return "valid"
    def on_block(s, b, online=True):
        if b.id in s.T: return True
        if b.id in s.bad or b.parent.id in s.bad: s.bad.add(b.id); return False
        if b.parent.id not in s.T: 
            if b.parent.id in s.pend: s.pend[b.id] = b
            return False
        if b.slot <= b.parent.slot or not s.step8(b): return False
        v = s.verdict(b)
        if v == "invalid": s.bad.add(b.id); s.pend.pop(b.id, None); return False
        if v == "undecided": s.pend[b.id] = b; return False
        s.pend.pop(b.id, None); s.T[b.id] = b; s.choose()
        for c in sorted([c for c in s.pend.values() if c.parent is b], key=lambda c: c.h): s.on_block(c)
        return True
    def missing(s):
        return {u[0] for b in s.pend.values() if b.parent.id in s.T for u in b.entries if u[0] not in s.T}
    def retry(s):
        for b in sorted(s.pend.values(), key=lambda c: c.h):
            if b.id in s.pend and b.parent.id in s.T: s.on_block(b)

class NetA(Net):
    def __init__(s, p, seed, **kw): super().__init__(p, seed, **kw); s.N = [NA(p, i) for i in range(p.n)]
    def uncles(s, j): super().uncles(j); s.N[j].retry()
    def deliver(s, j, b, src):
        n = s.N[j]; n.cast.setdefault(b.id, s.slot)
        if n.on_block(b) or b.id in n.pend or b.id in n.bad: return
        got = s.ask(j, b.id) or (s.ask(j, b.parent.id) or []) + [b]
        for x in got: n.on_block(x)                          # blocks above an undecided block are queued

def mk(opt, p, s, **kw): return NetA(p, s, **kw) if opt == "A" else Net2(p, s, "drafted", **kw)

def honest(opt, seeds=5):
    g = []; stale = 0; tot = 0
    for s in range(seeds):
        net = mk(opt, P(k=12), s)
        for _ in range(600): net.step()
        g.append(common_prefix(net, range(net.p.n))[1])
    return f"honest network: divergence at most {max(g)}"
def rejoin(opt, k=12, seeds=10, away=4):
    ok = 0
    for s in range(seeds):
        net = mk(opt, P(k=k), s)
        for _ in range(150): net.step()
        net.cut = {11}; h0 = net.N[0].c.h
        while net.N[0].c.h < h0 + away * k: net.step()
        net.cut = None
        for _ in range(80): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"cut off for {away}k blocks, never restarted: rejoined in {ok} of {seeds}"
def fresh(opt, k=12, seeds=10):
    ok = 0
    for s in range(seeds):
        net = mk(opt, P(k=k), s); net.N[11].up = False
        for _ in range(400): net.step()
        net.N[11].up = True
        for _ in range(80): net.step()
        ok += common_prefix(net, range(12))[1] <= 3
    return f"node that syncs from genesis: on the chain in {ok} of {seeds}"
def lost(opt, k=12, seeds=10):
    """Half of the nodes saw an uncle and adopted the block that names it; then nobody can serve the uncle any more."""
    split = 0
    for s in range(seeds):
        net = mk(opt, P(k=k), s)
        for _ in range(200): net.step()
        par = net.N[0].c
        for n in net.N:                                      # common start
            for b in reversed(list(anc(par))):
                n.on_block(b) 
        g = par; X = Block(next(net.ids), g.parent, g.slot + 0, g.h); X.maker = 0
        X.slot = g.slot if g.slot > g.parent.slot else g.parent.slot + 1
        A = Block(next(net.ids), par, net.slot + 1, par.h + 1, [(X.id, X.slot)]); A.maker = 0
        net.all[X.id] = X; net.all[A.id] = A
        half = range(0, net.p.n // 2 + 2)
        for j in half: net.N[j].T[X.id] = X
        net.slot += 1
        for j in range(net.p.n): net.N[j].on_block(A)
        for j in half: net.N[j].T.pop(X.id, None)             # the uncle is gone everywhere
        for _ in range(40 * k): net.step()
        split += common_prefix(net, range(net.p.n))[1] > 2 * k
    return f"uncle seen by 8 of 12 nodes, then lost everywhere: network still split after about {8*k} blocks in {split} of {seeds}"
if __name__ == "__main__":
    for opt in ("A", "B"):
        print("option", opt)
        for f in (honest, fresh, rejoin, lost): print("   ", f(opt))
