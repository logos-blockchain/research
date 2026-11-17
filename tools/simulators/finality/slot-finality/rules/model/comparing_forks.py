"""The model runs behind RFC-532's "Comparing forks". The fences are read from the checkout, so
this runs the rules as now printed.

The Bootstrap rule visits the forks in a fixed order, so the count of cases that depend on the
order of visits is taken twice: on the rule without that order, which is the count the RFC
prints, and on the rule as printed, where it must be zero.

Usage: SPEC_ROOT=<checkout> python3 comparing_forks.py
"""
import itertools
import os
import random
import subprocess
import sys

sys.setrecursionlimit(100000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from model import *

K, PHI, S_GEN, W = 64800, 1019, 16200, 360
R = Rules(K, PHI, S_GEN, W)


def spaced(start, end, step):
    return list(range(start, end + 1, step))


def on(n, first, a="fork", b="honest"):
    return a if is_ancestor(first, n.c_loc) else b


print("HEAD", subprocess.run(["git", "-C", WT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
      "| worktree dirty:", bool(subprocess.run(["git", "-C", WT, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()))

print("\n--- D: same blocks, two delivery orders, Bootstrap rule")
g = Block(None, 0, tag="G")
D = Block(g, 1000, tag="D")
F = chain_up(D, spaced(1020, 1000 + S_GEN, 20), tag="F")
A = chain_up(D, spaced(1200, 1000 + S_GEN, 200) + spaced(1000 + S_GEN + 10, 1000 + K + 500, 40), tag="A")
X, Y = Node(R, g), Node(R, g)
for b in [D] + F + A:
    assert X.on_block(b) == "ok"
for b in [D] + A + F:
    assert Y.on_block(b) == "ok"
print(" X (F then A) on", on(X, A[0], "A", "F"), "| Y (A then F) on", on(Y, A[0], "A", "F"), "| same T:", X.T == Y.T)
X.switch_to_online(True)
Y.switch_to_online(True)
print(" after the switch: X B_imm past D", X.B_imm.height > D.height, "A in T", A[-1] in X.T, "F in T", F[-1] in X.T,
      "| Y B_imm past D", Y.B_imm.height > D.height, "A in T", A[-1] in Y.T, "F in T", F[-1] in Y.T)

print("\n--- E: incomplete pruning, restart under the Bootstrap rule")
g = Block(None, 0, tag="G")
pre = chain_up(g, spaced(30, 30000, 30))
Dv = pre[-1]
L = chain_up(Dv, spaced(Dv.slot + 5, Dv.slot + 8000, 5), tag="left")
M_ = chain_up(Dv, spaced(Dv.slot + 30, Dv.slot + 140000, 30), tag="main")
n = Node(R, g, rule="ONLINE", step8="ancestor", prune="incomplete")
for b in pre + L + M_:
    assert n.on_block(b) == "ok"
print(" B_imm", n.B_imm, "left in T", L[-1] in n.T, "left descends", is_ancestor(n.B_imm, L[-1]))
n.rule = "BOOTSTRAP"
print(" fork block:", n.on_block(Block(M_[-3], M_[-3].slot + 1, tag="x")), "c_loc on", on(n, L[0], "left", "main"),
      "B_imm ancestor of c_loc:", is_ancestor(n.B_imm, n.c_loc))
try:
    n.switch_to_online(True)
    print(" switch ok, B_imm", n.B_imm)
except NotOnChain as e:
    print(" switch raises:", e)


def setup(H_slots, F_slots, sl_D=100000):
    g = Block(None, 0, tag="G")
    pre = chain_up(g, spaced(30, sl_D, 30))
    D = pre[-1]
    return g, pre, D, chain_up(D, H_slots(D.slot), tag="H"), chain_up(D, F_slots(D.slot), tag="F")


class PairOnline(Node):
    """Candidate: the Online rule uses the Bootstrap pair test too, on every block."""

    def on_block(self, b):
        if b in self.T:
            return "known"
        err = self.valid_header(b)
        if err:
            return err
        Tp = self.T | {b}
        c = b if b.parent is self.c_loc else self.c_loc
        c2 = self.r.bootstrap_fork_choice(c, tips(Tp), self.r.K, self.r.s_gen, self.B_imm)
        if self.rule == "ONLINE":
            Tp, self.B_imm = self.r.commit(Tp, c2, self.B_imm)
        self.T, self.c_loc = Tp, c2
        return "ok"


H7 = lambda d: spaced(d + 45, d + 45855, 45)
F7 = lambda d: [d + 89 * (i + 1) for i in range(1020)]

print("\n--- B7, both delivery orders, as printed")
for label, order in (("fork first", lambda p, H, F: p + F[:-1] + H), ("honest first", lambda p, H, F: p + H + F[:-1])):
    g, pre, D, H, F = setup(H7, F7)
    n = Node(R, g)
    for b in order(pre, H, F):
        assert n.on_block(b) == "ok"
    pick = on(n, F[0])
    n.switch_to_online(True)
    surv = F[-2] in n.T
    r = n.on_block(F[-1])
    print(f" {label}: Bootstrap picked {pick}; F survives switch {surv}; next F block {r}: on {on(n, F[0])}, B_imm past D {n.B_imm.height > D.height}, H in T {H[-1] in n.T}")

print("\n--- RFC claim: pruning the fork at the switch does not hold (fork delivered again)")
g, pre, D, H, F = setup(H7, F7)
n = Node(R, g)
for b in pre + F[:-1] + H:
    n.on_block(b)
n.switch_to_online(True)
n.T = prune_blocks(F[-2], D, n.T)
print(" pruned, F in T:", F[-2] in n.T, "D in T:", D in n.T, "B_imm at or below D:", n.B_imm.height <= D.height)
res = [n.on_block(b) for b in F]
print(" delivered again: all ok", all(x == "ok" for x in res), "on", on(n, F[0]), "B_imm past D", n.B_imm.height > D.height, "H in T", H[-1] in n.T)

print("\n--- Candidate rule change: the Online rule also uses the pair test")
cases = {
    "B2 child younger than K": (lambda d: spaced(d + 30, d + K + 10, 30), lambda d: [d + 5 + 100 * i for i in range(10)] + spaced(d + 16300, d + K + 40, 20)),
    "B3 floor": (lambda d: spaced(d + 20, d + S_GEN, 20) + spaced(d + S_GEN + 1000, d + 70000, 2000), lambda d: [d + 100 * (i + 1) for i in range(10)] + spaced(d + 16300, d + 70020, 40)),
    "B5 lag, rate 1/60": (lambda d: spaced(d + 45, d + K - 32800, 45), lambda d: spaced(d + 60, d + K + 200, 60)),
    "B7 lag, a third": (H7, F7),
}
for name, (hs, fs) in cases.items():
    out = []
    for cls in (Node, PairOnline):
        g, pre, D, H, F = setup(hs, fs)
        n = cls(R, g)
        for b in pre + F[:-1] + H:
            n.on_block(b)
        pick = on(n, F[0])
        n.switch_to_online(True)
        n.on_block(F[-1])
        out.append(f"{cls.__name__}: Bootstrap {pick}, then on {on(n, F[0])}, past D {n.B_imm.height > D.height}")
    print(f" {name}: " + " | ".join(out))
# G3: Online node, 12.5 h eclipse
out = []
for cls in (Node, PairOnline):
    g, pre, D, H, F = setup(H7, F7)
    n = cls(R, g, rule="ONLINE")
    for b in pre + H + F:
        n.on_block(b)
    out.append(f"{cls.__name__}: on {on(n, F[0])}, past D {n.B_imm.height > D.height}")
print(" G3 eclipse 12.5 h: " + " | ".join(out))
# its cost: a denser fork that died, and a live chain
out = []
for cls in (Node, PairOnline):
    g = Block(None, 0, tag="G")
    pre = chain_up(g, spaced(30, 100000, 30))
    D = pre[-1]
    S = chain_up(D, spaced(D.slot + 30, D.slot + S_GEN, 30), tag="S")  # dense, then dies
    Live = chain_up(D, spaced(D.slot + 60, D.slot + 200000, 60), tag="L")  # sparser in the window, keeps going
    n = cls(R, g, rule="ONLINE")
    for b in pre + S + Live:
        r = n.on_block(b)
    out.append(f"{cls.__name__}: on {on(n, S[0], 'dead', 'live')}, last block {r}, B_imm past D {n.B_imm.height > D.height}")
print(" dense fork that dies, live chain 3,333 blocks: " + " | ".join(out))

print("\n--- Order of comparison figures (RFC 'Comparing forks')")
rng = random.Random(7)
Rs = Rules(40, 5, 10, 10, unordered=True)   # the Bootstrap test, visiting forks as listed
Rp = Rules(40, 5, 10, 10)                   # the rule as printed, with its fixed order
Ms = master_rules(6, 10)
asym_b = asym_m = pairs = cases_n = order_b = order_m = order_p = 0
for seed in range(4000):
    Block.counter = 0
    r = Block(None, 0)
    bl = [r]
    for i in range(rng.randint(6, 40)):
        p = bl[rng.randrange(max(0, len(bl) - 12), len(bl))]
        bl.append(Block(p, p.slot + rng.randint(1, 14)))
    ts = tips(set(bl))
    for x, y in itertools.combinations(ts, 2):
        pairs += 1
        p1, p2 = Rs.bootstrap_fork_choice(x, [x, y], 40, 10, r), Rs.bootstrap_fork_choice(y, [y, x], 40, 10, r)
        q1, q2 = Ms["bootstrap_fork_choice"](x, [x, y], 6, 10), Ms["bootstrap_fork_choice"](y, [y, x], 6, 10)
        dx, dy = common_prefix_depth(x, y)
        if p1 is not p2:
            age = grandparent(x, dx).slot + 40 <= max(x.slot, y.slot)
            tie = (density(x, dx, 10) == density(y, dy, 10)) if age else (dx == dy)
            asym_b += not tie
        if q1 is not q2:
            asym_m += not (dx == dy or density(x, dx, 10) == density(y, dy, 10))
    if 3 <= len(ts) <= 6:
        for local in ts:
            cases_n += 1
            order_b += len({Rs.bootstrap_fork_choice(local, list(pm), 40, 10, r) for pm in itertools.permutations(ts)}) > 1
            order_m += len({Ms["bootstrap_fork_choice"](local, list(pm), 6, 10) for pm in itertools.permutations(ts)}) > 1
            order_p += len({Rp.bootstrap_fork_choice(local, list(pm), 40, 10, r) for pm in itertools.permutations(ts)}) > 1
print(f" pairs {pairs}: not-a-tie disagreement branch={asym_b} base={asym_m}; cases {cases_n}: order-dependent "
      f"without the fixed order={order_b} base={order_m} as printed={order_p}")

print("\n--- With a strict pairwise winner, is the result fixed under every delivery order? (small trees, K=40)")
from random_trees import delivery, universe


class Shortcut(Node):
    """The on_block split of 9b8881de, for comparison: no Bootstrap comparison when a block extends c_loc."""

    def on_block(self, b):
        if b in self.T:
            return "known"
        err = self.valid_header(b)
        if err:
            return err
        Tp = self.T | {b}
        c2 = b if b.parent is self.c_loc else self.r.bootstrap_fork_choice(self.c_loc, tips(Tp), self.r.K, self.r.s_gen, self.B_imm)
        self.T, self.c_loc = Tp, c2
        return "ok"


def winner(r, ts):
    for x in ts:
        if all(y is x or (r.bootstrap_fork_choice(x, [x, y], r.K, r.s_gen, ROOT) is x and r.bootstrap_fork_choice(y, [y, x], r.K, r.s_gen, ROOT) is x) for y in ts):
            return x
    return None


rng = random.Random(11)
stats = {"trees": 0, "with-winner": 0, "printed-misses": 0, "shortcut-misses": 0, "no-winner": 0, "no-winner-split": 0}
rs = Rules(40, 5, 10, 10)
for seed in range(1500):
    ROOT = Block(None, 0)
    blocks = universe(rng, ROOT, rng.randint(8, 60), rng.choice([1, 2, 4, 8]), rng.choice([0.2, 0.5]), 40, 10)
    for b in blocks:
        b.uncles = []
    stats["trees"] += 1
    w = winner(rs, tips(set(blocks)))
    finals, finals_s = [], []
    for _ in range(4):
        order = delivery(rng, blocks, ROOT)
        a, s = Node(rs, ROOT), Shortcut(rs, ROOT)
        for b in order:
            a.on_block(b)
            s.on_block(b)
        finals.append(a.c_loc)
        finals_s.append(s.c_loc)
    if w is not None:
        stats["with-winner"] += 1
        stats["printed-misses"] += any(f is not w for f in finals)
        stats["shortcut-misses"] += any(f is not w for f in finals_s)
    else:
        stats["no-winner"] += 1
        stats["no-winner-split"] += len(set(finals)) > 1
print(" ", stats)
