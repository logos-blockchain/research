"""The switch to the Online rule with `commit` and without it, at K = 64,800, phi = 1,019 and
s_gen = 16,200.

A fork that is sparse in the density window but longer overall loses under the Bootstrap rule.
With `commit` at the switch the fork is pruned, and its next block is refused. Without `commit`
its next block makes it win by length, and `B_imm` passes the divergence block.

Usage: SPEC_ROOT=<checkout> python3 switch.py
"""
import os
import sys

sys.setrecursionlimit(100000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *

K, PHI, S_GEN, W = 64800, 1019, 16200, 360
R = Rules(K, PHI, S_GEN, W)


def spaced(start, end, step):
    return list(range(start, end + 1, step))


def feed(node, blocks):
    for b in blocks:
        res = node.on_block(b)
        if res not in ("ok", "known"):
            print("   feed rejected", b, res)
            return res
    return "ok"


def banner(s):
    print("\n=== " + s)


banner("B1. Switch: rejected fork, divergence child older than K (the RFC's case)")


def setup(H_slots, F_slots, sl_D=100000):
    g = Block(None, 0, tag="G")
    pre = chain_up(g, spaced(30, sl_D, 30))
    D = pre[-1]
    H = chain_up(D, H_slots(D.slot), tag="H")
    F = chain_up(D, F_slots(D.slot), tag="F")
    return g, pre, D, H, F


H_s = lambda d: spaced(d + 30, d + 70000, 30)  # 2333 blocks, 540 in s_gen
F_s = lambda d: [d + 100 * (i + 1) for i in range(10)] + spaced(d + 16300, d + 70000 + 20, 20)  # 10 in s_gen, longer overall
for run_commit in (True, False):
    g, pre, D, H, F = setup(H_s, F_s)
    n = Node(R, g)
    feed(n, pre + H + F[:-1])
    print(f" run_commit={run_commit}: bootstrap picked", "H" if is_ancestor(H[0], n.c_loc) else "F",
          f" len H={len(H)} len F={len(F)-1} density H={density(H[-1], len(H), S_GEN)} F={density(F[-2], len(F)-1, S_GEN)}")
    n.switch_to_online(run_commit)
    print("   after switch B_imm", n.B_imm, " past D:", n.B_imm.height > D.height, " F tip in T:", F[-2] in n.T)
    r = n.on_block(F[-1])
    print("   next F block:", r, " c_loc on", "H" if is_ancestor(H[0], n.c_loc) else "F", " B_imm", n.B_imm,
          " H still in T:", H[-1] in n.T)
