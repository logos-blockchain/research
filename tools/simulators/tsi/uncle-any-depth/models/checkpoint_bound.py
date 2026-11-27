"""Which checkpoints let a new node check every entry it has to check?

Random block trees. P is a provider's tip, I = its k-deep block, C a block of its chain below I.
A block A after C on that chain is checked when it has no descendant on the chain k or more blocks higher, that is when it
comes after I. An entry of A can name X with fork point G when X is off the chain, sl_X < sl_A and sl_A - sl_G <= w.
The node that starts at C cannot obtain X when G lies before C.

Rule: sl_C + w <= sl_I.  Checks that it is enough, and how far it can be weakened.
"""
import random
from rules import rand_tree   # prints its own checks on import

def run(slack, trials=600, seed=3):
    rng = random.Random(seed); pairs = bad = 0; ex = None
    for _ in range(trials):
        t = rand_tree(60, rng); w = rng.choice([1, 3, 6, 12, 25]); k = rng.choice([1, 2, 3, 5, 8])
        tip = max(t.b, key=lambda c: t.b[c].h); chain = list(t.anc(tip))
        if len(chain) <= k: continue
        I = chain[k]; checked = chain[:k]
        for C in chain[k:]:
            if not t.b[C].slot + w <= t.b[I].slot + slack: continue
            for A in checked:
                for X in t.b:
                    if X in chain or t.b[X].slot >= t.b[A].slot: continue
                    G = t.lca(X, A)
                    if t.b[A].slot - t.b[G].slot > w: continue
                    pairs += 1
                    if t.b[G].slot < t.b[C].slot: bad += 1; ex = (w, k, t.b[C].slot, t.b[I].slot, t.b[A].slot, t.b[G].slot)
    print(f"sl_C + w <= sl_I + {slack}: {pairs} checked entries, {bad} with the fork point before the checkpoint", ("e.g. (w, k, C, I, A, G) = %s" % (ex,)) if bad else "")

for s in (0, 1, 2, 3): run(s)
# The drafted rule: C exactly k blocks deep (C = I)
rng = random.Random(4); pairs = bad = 0
for _ in range(600):
    t = rand_tree(60, rng); w = rng.choice([1, 3, 6, 12, 25]); k = rng.choice([1, 2, 3, 5, 8])
    tip = max(t.b, key=lambda c: t.b[c].h); chain = list(t.anc(tip))
    if len(chain) <= k: continue
    C = chain[k]
    for A in chain[:k]:
        for X in t.b:
            if X in chain or t.b[X].slot >= t.b[A].slot: continue
            G = t.lca(X, A)
            if t.b[A].slot - t.b[G].slot > w: continue
            pairs += 1; bad += t.b[G].slot < t.b[C].slot
print(f"checkpoint exactly k blocks deep: {pairs} checked entries, {bad} with the fork point before the checkpoint")
