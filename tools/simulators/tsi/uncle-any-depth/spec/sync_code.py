"""Run the drafted listening, download and uncle pseudocode on a small network (with the stop at the window).
Usage: python3 sync_code.py <cryptarchia-v1-bootstr-sync.md>"""
import re, sys
from dataclasses import dataclass, field
from typing import Optional, List, Callable
W, f = 4, 0.1                                       # W/f = 40 slots in these toy trees
doc = open(sys.argv[1]).read()
bl = re.findall(r"```python\n(.*?)```", doc, re.S)
src = "\n".join(next(b for b in bl if k in b) for k in ("def listen_and_process_new_blocks", "def download_blocks", "def download_missing_uncles"))
src = src.replace("block.height ≤ local_tree.latest_immutable_block().height", "False")
class ForkChoice: pass
class InvalidBlock(Exception): pass
class ParentNotFound(Exception): pass
@dataclass(frozen=True)
class Ref: block_id: str; slot: int
@dataclass
class Block:
    id: str; parent_block: Optional[str]; slot: int; uncles: list = field(default_factory=list); bad: bool = False
@dataclass
class KnownBlocks: local_tip: str; latest_immutable_block: str; additional_blocks: list
@dataclass
class DownloadBlocksRequest: target_block: str; known_blocks: KnownBlocks
BlockId = str
class Tree:
    k = 100
    def __init__(s, bs): s.t = {b.id: b for b in bs}; s.c = max(bs, key=lambda b: b.slot).id; s.n = 0
    def chain(s, i):
        out = []
        while i: out.append(s.t[i]); i = s.t[i].parent_block
        return out                                   # tip first
    def has(s, i): return i in s.t
    def common_ancestor(s, a, b):
        ca = {x.id for x in s.chain(a)}
        return next(x for x in s.chain(b) if x.id in ca)
    def best_tip(s): return s.t[max(s.t, key=lambda i: len(s.chain(i)))]
    def latest_immutable_block(s): return s.t["G"]
    def ok(s, i): return all(u.block_id in s.t for d, b in enumerate(s.chain(i)) if d < s.k for u in b.uncles)
    def on_block(s, b, *a):
        if b.id in s.t: return
        if b.bad: raise InvalidBlock
        if b.parent_block not in s.t: raise ParentNotFound
        s.t[b.id] = b
        for i in s.t:
            if len(s.chain(i)) > len(s.chain(s.c)) and s.ok(i): s.c = i
    def missing_uncles(s):
        return [(b, u) for i in list(s.t) if len(s.chain(i)) > len(s.chain(s.c)) for d, b in enumerate(s.chain(i)) if d < s.k for u in b.uncles if u.block_id not in s.t]
NET = {}; REQ = []; SENT = []
def nchain(i):
    out = []
    while i: out.append(i); i = NET[i].parent_block
    return out[::-1]
class Resp:
    def __init__(s, ids): s.ids = ids; SENT.extend(ids)
    def blocks(s): return [NET[i] for i in s.ids]
def select_peers(): return []
FROM_IMM = [False]                                   # provider lacks the requester's chain: starts from B_imm
def send_request_to_peers(peers, req):
    REQ.append(req.target_block)
    if req.target_block not in NET: return None
    c = nchain(req.target_block); k = req.known_blocks
    lca = max((max((c.index(y) for y in nchain(x) if y in c), default=-1) for x in ([k.latest_immutable_block] if FROM_IMM[0] else [k.local_tip, k.latest_immutable_block] + k.additional_blocks) if x in NET), default=-1)
    return Resp(c[lca + 1:])
exec(src, globals())
def net(*bs):
    NET.clear(); REQ.clear(); SENT.clear()
    for b in bs: NET[b.id] = b
def run(tree, *incoming):
    global listen_for_new_blocks
    listen_for_new_blocks = lambda: incoming
    listen_and_process_new_blocks(ForkChoice(), tree); return tree
G, A1, A2 = Block("G", None, 0), Block("A1", "G", 10), Block("A2", "A1", 20)
Z = Ref("Z", 5)
X1, X2 = Block("X1", "A1", 14, [Z]), Block("X2", "X1", 17, [Z])
A3, A4 = Block("A3", "A2", 30, [Ref("X2", 17)]), Block("A4", "A3", 40)
net(G, A1, A2, X1, X2, A3, A4); t = run(Tree([G, A1, A2]), A3)
print("1. uncle at depth 2:", t.c == "A3", "requests", REQ, "streamed", SENT, "| its own uncles not requested:", "Z" not in REQ)
net(G, A1, A2, X1, X2, A3, A4); t = run(Tree([G, A1, A2]), A4)
print("2. block arrives as a missing ancestor:", t.c == "A4", REQ)
net(G, A1, A2, A3, A4); t = run(Tree([G, A1, A2]), A3)
print("3. uncle nobody serves: the block is in the tree, the chain is not adopted:", t.has("A3") and t.c == "A2", REQ)
net(G, A1, A2, X1, Block("X2", "X1", 17, bad=True), A3); t = run(Tree([G, A1, A2]), A3)
print("4. invalid uncle: not adopted:", t.c == "A2")
long = [Block(f"F{i}", f"F{i-1}" if i else "G", 11 + i) for i in range(30)]
X = Block("XF", "F28", 60); AF = Block("AF", "F29", 70, [Ref("XF", 60)])
net(G, A1, A2, *long, X, AF); t = run(Tree([G, A1, A2] + long), AF)
print("5. uncle off a 30-block fork: blocks streamed", len(SENT), "adopted:", t.c == "AF")

# 6. The fork point of the uncle lies outside the window (70 - 10 > 40): the download stops before adding any block.
Y1, Y2 = Block("Y1", "A1", 50), Block("Y2", "Y1", 60)
B70 = Block("B70", "A2", 70, [Ref("Y2", 60)])
net(G, A1, A2, Y1, Y2, B70); t = run(Tree([G, A1, A2]), B70)
print("6. fork point outside the window: streamed", SENT, "added none:", not t.has("Y1") and not t.has("Y2"), "| not adopted:", t.c == "A2")
# 7. The provider lacks the requester's chain and streams from B_imm: blocks of A's chain are skipped, the honest uncle arrives.
FROM_IMM[0] = True
net(G, A1, A2, X1, X2, A3, A4); t = run(Tree([G, A1, A2]), A3)
print("7. stream from B_imm: streamed", SENT, "adopted:", t.c == "A3")
FROM_IMM[0] = False
# 8. The entry claims slot 13, below X1 (slot 14) on the way to X2: the download stops before X1.
A3w = Block("A3", "A2", 30, [Ref("X2", 13)])
net(G, A1, A2, X1, X2, A3w); t = run(Tree([G, A1, A2]), A3w)
print("8. entry with a slot below the branch: added none:", not t.has("X1") and not t.has("X2"))
