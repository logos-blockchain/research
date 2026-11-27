"""Property checks of the drafted uncle rules on random block trees.

Draft rule. X is a valid uncle of A when, with G = common_ancestor(X, A):
  X != G;  entry.slot == sl_X;  sl_X < sl_A;  sl_A - sl_G <= w;
  every block after G up to X is valid, its own uncles not checked.
Retention. A node keeps each valid block whose slot > sl_Bimm - w.
"""
import random
from dataclasses import dataclass, field

@dataclass
class B:
    id: int; parent: int; slot: int; h: int
    uncles: list = field(default_factory=list)     # [(id, slot)]

class Tree:
    def __init__(self): self.b = {0: B(0, -1, 0, 0)}
    def add(self, i, parent, slot):
        p = self.b[parent]; assert slot > p.slot
        self.b[i] = B(i, parent, slot, p.h + 1); return self.b[i]
    def anc(self, i):
        while i != -1:
            yield i; i = self.b[i].parent
    def lca(self, x, y):
        sx = set(self.anc(x))
        for a in self.anc(y):
            if a in sx: return a
    def at_depth(self, tip, d):
        i = tip
        for _ in range(d):
            if self.b[i].parent == -1: return i
            i = self.b[i].parent
        return i

def rand_tree(n, rng, p_stale=0.35, gap=(0, 1, 1, 2, 3, 5)):
    t = Tree(); slot = 0; order = [0]
    for i in range(1, n):
        slot += rng.choice(gap)
        cands = [c for c in order if t.b[c].slot < slot]
        if not cands: slot += 1; cands = order
        par = rng.choice(cands[-12:]) if rng.random() < p_stale else max(cands, key=lambda c: (t.b[c].h, -c))
        if t.b[par].slot >= slot: slot = t.b[par].slot + 1
        t.add(i, par, slot); order.append(i)
    return t

def window_ok(t, x, a, w):
    g = t.lca(x, a)
    return x != g and t.b[x].slot < t.b[a].slot and t.b[a].slot - t.b[g].slot <= w

# ---- 1. retention holds every block a check reads ---------------------------------------------
def retention(trials=400, seed=1):
    rng = random.Random(seed); cases = deep = 0
    for _ in range(trials):
        t = rand_tree(70, rng); w = rng.choice([1, 3, 6, 12, 25]); k = rng.choice([1, 2, 3, 5, 8])
        tip = rng.choice(list(t.b)); imm = t.at_depth(tip, k); s_imm = t.b[imm].slot
        for a in t.b:
            if a == imm or imm not in set(t.anc(a)): continue       # step 8: A descends from B_imm
            for x in t.b:
                if not window_ok(t, x, a, w): continue
                g = t.lca(x, a); cases += 1
                g_kept = t.b[g].slot > s_imm - w
                assert g_kept, (t.b[g], s_imm, w)
                if imm not in set(t.anc(g)): deep += 1               # G lies below B_imm
                y = x
                while y != g:
                    assert t.b[y].slot > s_imm - w
                    y = t.b[y].parent
    print(f"retention: {cases} (A, X) pairs, {deep} with the fork point below B_imm, none needs a block outside the kept range")

# mutation: keeping only slot > s_imm - w + 1 must fail somewhere
def retention_tight(seed=2):
    rng = random.Random(seed)
    for _ in range(4000):
        t = rand_tree(40, rng); w = rng.choice([3, 6, 12]); k = rng.choice([1, 2, 3])
        tip = rng.choice(list(t.b)); imm = t.at_depth(tip, k); s_imm = t.b[imm].slot
        for a in t.b:
            if a == imm or imm not in set(t.anc(a)): continue
            for x in t.b:
                if window_ok(t, x, a, w) and not (t.b[t.lca(x, a)].slot > s_imm - w + 1):
                    print("retention bound is tight: a fork point sits at the first kept slot", t.b[t.lca(x, a)].slot, "with s_imm - w =", s_imm - w); return
    print("retention bound NOT tight in the sample")

# ---- 2. epoch state: the branch of X and the chain of A agree ----------------------------------
def epoch_state(q=3):
    E, last = 10 * q, 4 * q
    def agree(w):
        for sA in range(E + 2, 3 * E):
            for sG in range(max(0, sA - w), sA):
                for sX in range(sG + 1, sA):
                    e = sX // E
                    if e == 0: continue
                    cut = e * E - last                    # blocks with slot < cut fix the epoch state of epoch e
                    # the chains agree up to G; a branch block or a chain block after G may sit at sG + 1
                    if sG + 1 < cut and sG + 1 < sX: return False, (sA, sG, sX, e)
        return True, None
    best = max(w for w in range(1, 2 * E) if agree(w)[0])
    print(f"epoch state: q = {q}, 4q = {last}: the states agree for every w <= {best} (= 4q + {best - last}); w = {best+1} fails at (sA, sG, sX, epoch) = {agree(best+1)[1]}")

retention(); retention_tight()
for q in (2, 3, 5): epoch_state(q)
