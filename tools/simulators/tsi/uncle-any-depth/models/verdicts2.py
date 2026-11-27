"""Follow-up to verdicts.py: the wrong-reference attack with an uncle that stays private, faster chain growth, and the
number of blocks one attacker block makes a node fetch."""
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    import verdicts, option_ab
from verdicts import *

def attack2(opt, seeds=12, share=3, slots=700, n=12, held=3, right=False):
    """X is a sibling of a tip, handed to `held` honest nodes outside the broadcast (so nobody selects it). A is a later sibling
    of the tip, sent to all, whose reference names X at the wrong slot (or at the right one)."""
    worst = []; over = 0
    for sd in range(seeds):
        net = mk(opt, P(k=12, n=n), sd); r = random.Random(sd + 99); X = None; gaps = []; honest = range(share, n)
        for t in range(slots):
            step_once(net, share)
            if r.random() < net.p.f * share / n:
                c = max((net.N[i].c for i in honest), key=lambda c: c.h)
                if c.parent is None or c.slot >= net.slot: continue
                b = Block(next(net.ids), c.parent, net.slot, c.h); b.maker = 0; net.all[b.id] = b
                if X is None:
                    X = b
                    for i in range(share, share + held): net.N[i].on_block(X)
                else:
                    b.entries = [(X.id, X.slot - (0 if right else 1))]; b.forged = True; X = None
                    for i in range(n): net.q.append((net.slot + 1, i, b))
            if t > 100: gaps.append(common_prefix(net, honest)[1])
        worst.append(max(gaps)); over += common_prefix(net, honest)[1] > 12
    w = sorted(worst)
    return f"{opt:10s} worst divergence: median {w[len(w)//2]}, max {w[-1]} blocks; more than k apart at the end in {over} of {seeds}"

def fast(opt, growth, what, seeds=10):
    """The chain grows `growth` times faster than the target (the stake rose and the estimate lags); ages and windows stay."""
    ok = 0; lag = []
    for s in range(seeds):
        p = P(k=12, f=1/5); p.f = growth / 5; net = mk(opt, p, s); net.N[11].up = False
        for _ in range(300): net.step()
        net.N[11].up = True
        for _ in range(240): net.step()
        best = max(net.N[i].c.h for i in range(11)); lag.append(best - net.N[11].c.h); ok += common_prefix(net, range(12))[1] <= 4
    return f"{opt:10s} growth x{growth}: node that syncs is on the chain 240 slots later in {ok} of {seeds}, behind by {min(lag)} to {max(lag)} blocks (k = 12)"

def layers(wins, siblings=4):
    """One attacker block at the last of `wins` wins; every block references `siblings` distinct blocks made from the win before."""
    GEN2 = Block(0, None, 0, 0); ids = itertools.count(1); main = [GEN2]; sl = 0
    for _ in range(wins * 4 + 4): sl += 5; main.append(Block(next(ids), main[-1], sl, main[-1].h + 1))
    T = {b.id: b for b in main}; prev = []; p = P(k=12)
    def valid(u, A):
        Xb = T[u[0]]; G = lca(Xb, A); return Xb is not G and u[1] == Xb.slot < A.slot and A.slot - G.slot <= p.w
    for j in range(wins):
        par = main[4 * j + 3]; cnt = siblings ** (wins - 1 - j); cur = []
        for m in range(cnt):
            b = Block(next(ids), par, par.slot + 2, par.h + 1); b.entries = [(x.id, x.slot) for x in prev[m * siblings:(m + 1) * siblings]]
            T[b.id] = b; cur.append(b); assert all(valid(u, b) for u in b.entries)
        prev = cur
    A = prev[0]; need = set(); st = [A]
    while st:
        for u in st.pop().entries:
            if u[0] not in need: need.add(u[0]); st.append(T[u[0]])
    return len(A.entries), len(need)

if __name__ == "__main__":
    for right in (False, True):
        for held in (1, 3, 4, 5, 6, 8):
            print("reference", "right" if right else "wrong", "| uncle held by", held, "of 9 honest nodes")
            for opt in ("drafted", "wrong=bad", "age"): print("   ", attack2(opt, held=held, right=right))
    for g in (1.0, 1.25, 1.5, 2.0):
        for opt in ("drafted", "age"): print(fast(opt, g, None))
    for w in (2, 4, 6, 8): print(f"{w} wins: blocks to fetch for the last block, drafted {layers(w)[0]}, with references of uncles checked as well {layers(w)[1]}")
