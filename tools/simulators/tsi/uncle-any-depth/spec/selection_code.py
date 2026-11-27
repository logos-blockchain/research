"""Run the pseudocode of the drafted Uncle Selection on random trees and compare it with a brute-force oracle.

Usage: python3 selection_code.py <cryptarchia-v1-protocol.md>
"""
import re, sys, random
from dataclasses import dataclass, field
from typing import Set

doc = open(sys.argv[1]).read()
sec = doc[doc.index("#### Uncle Selection"):doc.index("### Block Header Validation")]
code = "\n".join(re.findall(r"```python\n(.*?)```", sec, re.S))

@dataclass(frozen=True)
class UncleReference:
    block_id: int
    slot: int

@dataclass(eq=False)
class Block:
    id: int
    parent: "Block"
    slot: int
    uncles: list = field(default_factory=list)
    cast: set = field(default_factory=set)

W_SLOTS, MAX_UNCLES, T_M = 12, 4, 3 if 'T_M' in code else 0
T = set()
block_id = lambda X: X.id
def ancestors(B):
    out = []
    x = B
    while x is not None: out.append(x); x = x.parent
    return out
def fork_point(X, A):
    a = set(ancestors(A))
    return next(y for y in ancestors(X) if y in a)
def branch(X, A):
    g = fork_point(X, A); out = []; y = X
    while y is not g: out.append(y); y = y.parent
    return out
CUR = 0                                                  # the proposing node
broadcast = lambda Y: CUR in Y.cast
def by_id(i): return next((b for b in T if b.id == i), None)
def valid_uncle(u, A):                                   # the four rules; every block of T is valid here
    X = by_id(u.block_id)
    if X is None: return False
    G = fork_point(X, A)
    return X is not G and u.slot == X.slot < A.slot and A.slot - G.slot <= W_SLOTS
exec(code, globals())

def oracle(B):
    chain = set(ancestors(B)); refd = {u.block_id for a in chain for u in a.uncles}; occ = {a.slot for a in chain} | {u.slot for a in chain for u in a.uncles}
    c = []
    for X in T:
        if X in chain or X.slot >= B.slot or X.slot in occ or X.slot > B.slot - T_M: continue
        g = X; ok = True
        while g not in chain: ok &= (CUR in g.cast) or g.id in refd; g = g.parent
        if B.slot - g.slot <= W_SLOTS and ok: c.append((g.slot, X.slot, X.id))
    c.sort(); out, seen = [], set()
    for _, sl, i in c:
        if len(out) < MAX_UNCLES and sl not in seen: seen.add(sl); out.append((i, sl))
    return out

rng = random.Random(11); n_sel = deep = capped = uncast = via = 0
for trial in range(300):
    T.clear(); g = Block(0, None, 0); T.add(g); nid = 1; slot = 0
    for _ in range(45):
        slot += rng.choice((0, 1, 1, 2, 3))
        pars = sorted((b for b in T if b.slot < slot), key=lambda b: b.id)
        if not pars: continue
        par = rng.choice(pars[-9:])
        CUR = rng.randrange(5)
        B = Block(nid, par, slot, cast={n for n in range(5) if rng.random() > 0.3}); nid += 1
        sel = select_uncles(B)
        assert [(u.block_id, u.slot) for u in sel] == oracle(B), trial
        assert all(valid_uncle(u, B) for u in sel) and len(sel) <= MAX_UNCLES and len({u.slot for u in sel}) == len(sel)
        n_sel += len(sel); deep += sum(1 for u in sel if by_id(u.block_id).parent not in ancestors(B)); capped += len(sel) == MAX_UNCLES
        uncast += sum(1 for b in T if CUR not in b.cast)
        via += sum(1 for u in sel if not all(CUR in y.cast for y in branch(by_id(u.block_id), B)))
        B.uncles = sel; T.add(B)
print(f"pseudocode = oracle on 300 trees: {n_sel} entries selected, {deep} of them deeper than the first fork block, {capped} blocks at the cap; unbroadcast blocks present in {uncast} checks; {via} entries only the new condition admits")
