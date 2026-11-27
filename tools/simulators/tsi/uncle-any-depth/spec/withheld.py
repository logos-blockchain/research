"""Blocks of an attacker that only one node holds: does that node's proposal differ from everyone else's?

Runs the drafted Uncle Selection (the code of the document) on the view of the target and on the view of another node, same parent.
X is an attacker's fork block, Y its parent (also the attacker's, a second win). Orphans that cannot be completed are abandoned, as
the sync specification allows ("may retry ... before abandoning") and as the node does (one try).

  planted             X handed to the target in a download, never broadcast                              1 win
  withheld parent     X broadcast to all, Y handed to the target only                                    2 wins
  late parent         the same, then Y broadcast to all (the others have abandoned X)                    2 wins
  referenced parent   the same, then a block of the attacker on the chain references Y                   3 wins
  withheld tx         X broadcast to all, only the target could resolve a transaction of X               1 win
Usage: withheld.py <cryptarchia-v1-protocol.md>
"""
import re, sys, random
from dataclasses import dataclass, field
from typing import Set
doc = open(sys.argv[1]).read()
sec = doc[doc.index("#### Uncle Selection"):doc.index("### Block Header Validation")]
code = "\n".join(re.findall(r"```python\n(.*?)```", sec, re.S))
@dataclass(frozen=True)
class UncleReference: block_id: int; slot: int
@dataclass(eq=False)
class Block: id: int; parent: "Block"; slot: int; uncles: list = field(default_factory=list)
W_SLOTS, MAX_UNCLES, T_M = 7200, 4, 15
T = set(); CAST = set()                         # the view of the node whose proposal is computed
block_id = lambda X: X.id
def ancestors(B):
    out = []; x = B
    while x is not None: out.append(x); x = x.parent
    return out
def fork_point(X, A):
    a = set(ancestors(A)); return next(y for y in ancestors(X) if y in a)
def branch(X, A):
    g = fork_point(X, A); out = []; y = X
    while y is not g: out.append(y); y = y.parent
    return out
broadcast = lambda Y: Y in CAST
def valid_uncle(u, A):
    X = next((b for b in T if b.id == u.block_id), None)
    if X is None: return False
    G = fork_point(X, A); return X is not G and u.slot == X.slot < A.slot and A.slot - G.slot <= W_SLOTS
good = "all(broadcast(Y) or block_id(Y) in referenced for Y in branch(X, B))"
assert code.count(good) == 1
RULES = {"1 (drafted now)": good, "2 (whole branch)": "all(broadcast(Y) for Y in branch(X, B))",
         "3 (any block held)": "(broadcast(X) or X.id not in OWN)"}
OWN = set()
CASES = ("planted", "withheld parent", "late parent", "referenced parent", "withheld tx")
rng = random.Random(9); runs = 100
print(f"{'':20s}" + "".join(f"{c:>20s}" for c in CASES))
for rn, rc in RULES.items():
    exec(code.replace(good, rc), globals()); row = []
    for case in CASES:
        hit = 0
        for _ in range(runs):
            g = Block(0, None, 0); base = {g}; tip = g; nid = 1; slot = 0; used = {0}
            for _ in range(60):
                slot += 1 + int(rng.expovariate(1 / 30)); b = Block(nid, tip, slot); nid += 1; base.add(b); used.add(slot); tip = b
            chain = ancestors(tip)[::-1]; par = chain[-30]; s = par.slot + 3
            while s in used: s += 1
            Y = Block(nid, par, s); nid += 1; used.add(s)
            s2 = s + 5
            while s2 in used: s2 += 1
            two = case in ("withheld parent", "late parent", "referenced parent")
            X = Block(nid, Y if two else par, s2); nid += 1
            if case == "referenced parent":            # the attacker's canonical block, above the fork point
                next(a for a in chain if a.slot > s2).uncles.append(UncleReference(Y.id, Y.slot))
            B = Block(nid, tip, tip.slot + 20)
            view_t = base | ({X, Y} if two else {X}); view_o = base | ({Y} if case in ("late parent", "referenced parent") else set())
            cast_t = set(base) | {X}; cast_o = set(base) | {X}
            if case == "planted": cast_t = set(base)
            if case == "late parent": cast_t |= {Y}; cast_o |= {Y}
            T, CAST = view_t, cast_t; mine = [u.block_id for u in select_uncles(B)]
            T, CAST = view_o, cast_o; others = [u.block_id for u in select_uncles(B)]
            hit += mine != others
        row.append(hit)
    print(f"{rn:20s}" + "".join(f"{str(h) + ' of ' + str(runs):>20s}" for h in row))
