"""Random block trees, random delivery orders, random switch times: check the invariants.

9,000 runs: 3,000 from genesis, 3,000 from a checkpoint, 3,000 after a restart under the Online
rule. Among the invariants is the note in Uncle Selection: a candidate whose parent is within the
uncle window is still in the block tree ("candidate-pruned").

Usage: SPEC_ROOT=<checkout> python3 random_trees.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *


def universe(rng, root, n, gap, fork_p, K, W_slots):
    """A random tree above root. Returns blocks in creation order (parents first)."""
    blocks = [root]
    top = root
    firsts = []  # blocks whose parent is on some chain and that started a fork
    slot = root.slot
    for _ in range(n):
        slot += rng.randint(1, gap)
        if rng.random() < fork_p:
            # build on a random recent block, sometimes very old
            depth = rng.choice([1, 2, 3, 5, 8, 13, 21, 34, 55])
            p = blocks[max(0, len(blocks) - depth)]
        else:
            p = top
        uncles = []
        # reference a first block of a fork when the rules allow it
        cands = [u for u in firsts if is_ancestor(u.parent, p) and not is_ancestor(u, p)
                 and u.parent.slot < u.slot < slot and slot - u.parent.slot <= W_slots]
        rng.shuffle(cands)
        uncles = cands[: rng.randint(0, 2)]
        s = max(slot, p.slot + 1)
        b = Block(p, s, uncles=uncles)
        slot = max(slot, s)
        if p is not top and p.parent is not None and p.parent is not MISSING:
            firsts.append(b)
        blocks.append(b)
        if b.height > top.height or (b.height == top.height and rng.random() < 0.3):
            top = b
    return blocks


def delivery(rng, blocks, root):
    """A random order in which each block follows its parent."""
    pending = [b for b in blocks if b is not root]
    children = {}
    for b in pending:
        children.setdefault(b.parent, []).append(b)
    ready = list(children.get(root, []))
    order = []
    while ready:
        i = rng.randrange(len(ready))
        # bias towards creation order, with some lag
        if rng.random() < 0.7:
            i = min(range(len(ready)), key=lambda j: ready[j].id)
        b = ready.pop(i)
        order.append(b)
        ready.extend(children.get(b, []))
    return order


def check(node, prev_imm, viol, r, seen, clock):
    if not is_ancestor(node.B_imm, node.c_loc):
        viol["imm-not-ancestor"] += 1
    if not is_ancestor(prev_imm, node.B_imm):
        viol["imm-moved-back"] += 1
    if node.c_loc not in tips(node.T):
        viol["c_loc-not-tip"] += 1
    for b in node.T:
        if not (is_ancestor(b, node.B_imm) or is_ancestor(node.B_imm, b)):
            viol["unpruned"] += 1
            break
    if node.B_imm is not prev_imm:
        # the move obeys the condition
        if not (node.B_imm.slot <= node.c_loc.slot - r.K and
                density_over_slots(node.c_loc, node.B_imm.slot + 1, node.c_loc.slot - node.B_imm.slot) >= r.phi):
            viol["move-breaks-condition"] += 1
    if node.rule == "ONLINE" and node.c_loc is not node.B_imm:
        # maximal: the next block fails the condition
        C = child_on_chain(node.B_imm, node.c_loc)
        if C.slot <= node.c_loc.slot - r.K and density_over_slots(node.c_loc, C.slot + 1, node.c_loc.slot - C.slot) >= r.phi:
            viol["commit-not-maximal"] += 1
        # monotone: walking from the tip finds the same block
        x = node.c_loc
        while x is not node.B_imm:
            ok = x.slot <= node.c_loc.slot - r.K and density_over_slots(node.c_loc, x.slot + 1, node.c_loc.slot - x.slot) >= r.phi
            if ok:
                viol["commit-not-monotone"] += 1
                break
            x = x.parent
    # Note in Uncle Selection: a candidate within the window is still in T, for the block being built
    build = clock + 1
    if node.rule == "ONLINE":
        for u in seen:
            p = u.parent
            if p is MISSING or p is None:
                continue
            if is_ancestor(p, node.c_loc) and not is_ancestor(u, node.c_loc) and build - p.slot <= r.W_slots:
                if u not in node.T:
                    viol["candidate-pruned"] += 1
                    break
        # the claim as worded: B_imm lies at least K behind the slot being built
        if node.B_imm.slot > build - r.K and node.B_imm.height > node.start_height:
            viol["imm-less-than-K-behind-build"] += 1


def run(seed, start, viol, stats):
    rng = random.Random(seed)
    K = rng.choice([8, 12, 20, 40])
    phi = rng.choice([0, 1, 2, 3, 5, K // 2])
    s_gen = max(1, K // 4)
    W_slots = rng.choice([1, 2, K // 4, K - 1])
    r = Rules(K, phi, s_gen, W_slots)
    Block.counter = 0
    if start == "genesis":
        root = Block(None, 0, tag="G")
        rule = "BOOTSTRAP"
    elif start == "checkpoint":
        root = Block(MISSING, 1000, tag="CP", height=500)
        rule = "BOOTSTRAP"
    else:  # restart within T_offline: the node comes up Online with its state
        root = Block(None, 0, tag="G")
        rule = "ONLINE"
    blocks = universe(rng, root, rng.randint(10, 90), rng.choice([1, 2, 4, 8]), rng.choice([0.05, 0.2, 0.5]), K, W_slots)
    order = delivery(rng, blocks, root)
    node = Node(r, root, rule=rule)
    node.start_height = root.height
    switch_at = rng.randint(0, len(order))
    seen, clock = [], root.slot
    for i, b in enumerate(order):
        if i == switch_at and node.rule == "BOOTSTRAP":
            prev = node.B_imm
            node.switch_to_online()
            check(node, prev, viol, r, seen, clock)
        prev = node.B_imm
        # step 8 agrees with is_ancestor on a pruned tree
        if b.parent in node.T:
            h = b.height > node.B_imm.height
            a = is_ancestor(node.B_imm, b)
            if h != a:
                viol["step8-height-vs-ancestor"] += 1
        res = node.on_block(b)
        stats[res] = stats.get(res, 0) + 1
        clock = max(clock, b.slot)
        if res == "ok":
            seen.append(b)
        check(node, prev, viol, r, seen, clock)
    if node.rule == "BOOTSTRAP":
        prev = node.B_imm
        node.switch_to_online()
        check(node, prev, viol, r, seen, clock)
    stats["moved"] = stats.get("moved", 0) + (node.B_imm is not root)


for start in ("genesis", "checkpoint", "restart") if __name__ == "__main__" else ():
    viol = {k: 0 for k in ("imm-not-ancestor", "imm-moved-back", "c_loc-not-tip", "unpruned", "move-breaks-condition",
                           "commit-not-maximal", "commit-not-monotone", "candidate-pruned", "imm-less-than-K-behind-build",
                           "step8-height-vs-ancestor", "exception")}
    stats = {}
    N = 3000
    for seed in range(N):
        try:
            run(seed, start, viol, stats)
        except (MissingHistory, NotOnChain) as e:
            viol["exception"] += 1
            print("EXC", start, seed, repr(e))
    print(start, "runs", N, "stats", stats)
    print("   violations", {k: v for k, v in viol.items() if v} or "none")
