"""A block that an attacker hands to one node only: does the node's next proposal name it, under each selection rule?

Runs the drafted Uncle Selection on a tree of 200 blocks with one planted block, for a target that got every other block by broadcast.
The attacker picks the parent of its block. Also the two-block form: the parent Y is handed to the target alone, the child X is broadcast.
Usage: planted.py <cryptarchia-v1-protocol.md>
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
class Block: id: int; parent: "Block"; slot: int; uncles: list = field(default_factory=list); cast: bool = True
W_SLOTS, MAX_UNCLES, T_M = 7200, 4, 15
T = set(); IDX = {}
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
broadcast = lambda Y: Y.cast
def valid_uncle(u, A):
    X = IDX.get(u.block_id)
    if X is None: return False
    G = fork_point(X, A); return X is not G and u.slot == X.slot < A.slot and A.slot - G.slot <= W_SLOTS
RULES = {"any block held": "True", "X by broadcast": "broadcast(X)", "whole branch by broadcast (draft)": "all(broadcast(Y) for Y in branch(X, B))",
         "branch by broadcast or referenced": "all(broadcast(Y) or block_id(Y) in referenced for Y in branch(X, B))"}
cond = re.search(r"and all\(broadcast\(Y\).*?\)\)", code).group(0)
rng = random.Random(5)
for name, c in RULES.items():
    src = code.replace(cond, "and " + c)
    if "referenced" in c and "referenced =" not in src:
        src = src.replace("    return {X for X in T if", "    referenced = {u.block_id for A in ancestors(B) for u in A.uncles}\n\n    return {X for X in T if")
    exec(src, globals()); hits1 = hits2 = 0; runs = 100
    for _ in range(runs):
        for two in (False, True):
            T.clear(); IDX.clear(); g = Block(0, None, 0); T.add(g); IDX[0] = g; tip = g; nid = 1; slot = 0; used = set()
            for _ in range(150):
                slot += 1 + int(rng.expovariate(1 / 30)); b = Block(nid, tip, slot); nid += 1; T.add(b); IDX[b.id] = b; used.add(slot)
                if rng.random() < .3 and tip.parent is not None:            # an honest fork block, broadcast to all
                    s = tip.slot + 2
                    if s not in used: x = Block(nid, tip.parent, s); nid += 1; T.add(x); IDX[x.id] = x
                tip = b
            chain = ancestors(tip)[::-1]; par = chain[-60]; s = par.slot + 7
            while s in used: s += 1
            if two:
                y = Block(nid, par, s, cast=False); nid += 1; s2 = s + 5
                while s2 in used: s2 += 1
                p = Block(nid, y, s2); nid += 1; T.add(y); IDX[y.id] = y
            else: p = Block(nid, par, s, cast=False); nid += 1
            T.add(p); IDX[p.id] = p
            # proposals of the target: the honest backlog older than the planted block has been referenced before
            for a in chain[1:]:
                a.uncles = []
            old = sorted((x for x in T if x not in chain and x is not p and x.cast and not (two and x is p)), key=lambda x: x.slot)
            for a in chain[-120:]:
                for x in list(old):
                    if len(a.uncles) < 4 and x.slot < a.slot and fork_point(x, tip).slot < a.slot: a.uncles.append(UncleReference(x.id, x.slot)); old.remove(x)
            B = Block(nid, tip, tip.slot + 20)
            named = {u.block_id for u in select_uncles(B)}
            hit = p.id in named or (two and y.id in named)
            if two: hits2 += hit
            else: hits1 += hit
    print(f"{name:36s}: the proposal names the planted block in {hits1} of {runs} runs; with a withheld parent in {hits2} of {runs}")
