"""A simulation of the Online rule as printed, at inflated rates (SURVIVAL.md, section 10.2).

Honest nodes run on_block (protocol 470-494) with online_fork_choice (fork choice 148-159): a block
that extends c_loc becomes c_loc; otherwise the tips are visited in increasing block ID and a tip
replaces the running choice only when it is strictly longer. B_imm stays at the root, so the check of
A5 holds by construction, and commit is not run. A delivered block arrives with every block of its
chain that the node lacks. Slot 0 holds H0, an honest block on the root.

Part 1 stresses Lemmas 3.1 to 5.2 with random adversaries and random delivery within d. At the end of
every slot t >= d, for every honest node, it checks:
  (a) chain growth (Lemma 4.2): height(c_loc) >= height(H0) + N(t - d);
  (b) if c_loc is a pure branch (H0 followed by coalition blocks only): A(t) >= N(t - d) (Lemma 5.2 (1));
  (c) and then also X(t) >= 1 or U_(N(t-d)) >= 0 (Lemma 5.2 (2) with Lemma 5.3).
Part 2 runs the instance of Proposition 9.3: honest wins by fresh nodes that share one view, every
honest block d slots late, a target node without stake, and the adversary S* (deliver the private
branch first at every count with U_n >= 0). It counts the runs in which some honest node holds a pure
branch at some slot t >= T, against Qhat(T) of the recursion at the same rates.
The simulation supports the proofs; it does not replace them.
The seed is fixed, and a random parent is drawn from a list sorted by block ID, so that every run
prints the same output.
Usage: python s6_protocol_sim.py > out_6_protocol_sim.txt
"""
import math
import random

from sv_common import survival_curves


class Block:
    __slots__ = ("bid", "parent", "slot", "height", "honest", "pure")

    def __init__(self, bid, parent, slot, honest, pure):
        self.bid, self.parent, self.slot, self.honest, self.pure = bid, parent, slot, honest, pure
        self.height = 0 if parent is None else parent.height + 1


class Node:
    def __init__(self, root):
        self.T = {root}
        self.tips = {root}
        self.c_loc = root

    def on_block(self, B):
        if B in self.T:
            return
        self.T.add(B)
        self.tips.discard(B.parent)
        self.tips.add(B)
        if B.parent is self.c_loc:                          # protocol 486, second case
            self.c_loc = B
            return
        c_max = self.c_loc                                  # fork choice 148-159
        for c in sorted(self.tips, key=lambda b: b.bid):
            if c.height > c_max.height:                     # depth_max < depth_fork
                c_max = c
        self.c_loc = c_max

    def deliver(self, B):
        chain = []
        while B not in self.T:
            chain.append(B)
            B = B.parent
        for b in reversed(chain):
            self.on_block(b)


class Lottery:
    """The greedy d-isolated honest wins after slot 0 and the coalition's wins, slot by slot."""

    def __init__(self, d):
        self.d = d
        self.taus = [0]
        self.A = [0]           # A[t] = coalition wins in 1..t

    def add(self, t, honest_won, coal_won):
        if honest_won and t > self.taus[-1] + self.d:
            self.taus.append(t)
        self.A.append(self.A[-1] + coal_won)

    def N(self, u):
        return sum(1 for s in self.taus[1:] if s <= u)

    def U(self, n):
        if n == 0:
            return 0
        return self.A[self.taus[n] + self.d] - n


def new_id(rng):
    return rng.getrandbits(64)


def stress_run(rng, f, xh, xa, d, n_h, t_sim, strategy, delays, stats):
    root = Block(new_id(rng), None, -1, True, False)
    nodes = [Node(root) for _ in range(n_h + 1)]           # the last node holds no stake
    H0 = Block(new_id(rng), root, 0, True, True)
    pending = {}

    def schedule(slot, prio, j, B):
        pending.setdefault(slot, []).append((prio, rng.random(), j, B))

    def honest_delay():
        if delays == "max":
            return d
        if delays == "random":
            return rng.randint(0, d)
        return rng.choice((0, d, rng.randint(0, d)))

    nodes[0].deliver(H0)
    for j in range(1, n_h + 1):
        schedule(honest_delay(), 1, j, H0)
    for _, _, j, B in sorted(pending.pop(0, [])):
        nodes[j].deliver(B)
    p_node = -math.expm1((xh / n_h) * math.log1p(-f))
    a = -math.expm1(xa * math.log1p(-f))
    lot = Lottery(d)
    adv_blocks = [H0]
    private = H0                                           # the private branch's tip
    for t in range(1, t_sim + 1):
        winners = [i for i in range(n_h) if rng.random() < p_node]
        coal = rng.random() < a
        lot.add(t, bool(winners), coal)
        for i in winners:                                  # built on c_loc at the end of slot t - 1
            B = Block(new_id(rng), nodes[i].c_loc, t, True, False)
            nodes[i].deliver(B)
            for j in range(n_h + 1):
                if j != i:
                    schedule(t + honest_delay(), 1, j, B)
        if coal:
            if strategy == "random":
                known = [b for b in adv_blocks if b.slot < t] + [b for n in nodes for b in sorted(n.T, key=lambda b: b.bid)
                                                                 if t - 30 <= b.slot < t]
                for _ in range(rng.randint(1, 2)):
                    par = rng.choice(known)
                    B = Block(new_id(rng), par, t, False, par.pure)
                    adv_blocks.append(B)
                    for j in range(n_h + 1):
                        if rng.random() < 0.5:
                            schedule(t + rng.randint(0, 3 * d), rng.choice((0, 2)), j, B)
            B = Block(new_id(rng), private, t, False, private.pure)
            private = B
            adv_blocks.append(B)
        if strategy in ("random", "private") and rng.random() < 0.15:
            schedule(t, rng.choice((0, 2)), rng.randrange(n_h + 1), private)
        for _, _, j, B in sorted(pending.pop(t, [])):
            nodes[j].deliver(B)
        if t >= d:
            n = lot.N(t - d)
            x = lot.A[t] - n
            for node in nodes:
                stats["checks"] += 1
                if node.c_loc.height < 1 + n:
                    stats["growth"] += 1
                if node.c_loc.pure:
                    stats["pure"] += 1
                    if x < 0:
                        stats["lemma51"] += 1
                    if not (x >= 1 or lot.U(n) >= 0):
                        stats["lemma52"] += 1
                    if x == 0:
                        stats["ties"] += 1


def instance_run(rng, h, a, d, t_sim, ts):
    """Proposition 9.3: one shared honest view V (fresh builders, every honest block d slots late),
    a target node without stake, and S*. Returns, for each T in ts, whether some honest node held a
    pure branch at some slot t >= T."""
    root = Block(new_id(rng), None, -1, True, False)
    V, target = Node(root), Node(root)
    H0 = Block(new_id(rng), root, 0, True, True)
    pending = {d: [H0]}
    lot = Lottery(d)
    private = H0
    last = -1
    for t in range(1, t_sim + 1):
        hon = rng.random() < h
        coal = rng.random() < a
        lot.add(t, hon, coal)
        if hon:
            B = Block(new_id(rng), V.c_loc, t, True, False)
            pending.setdefault(t + d, []).append(B)
        if coal:
            private = Block(new_id(rng), private, t, False, private.pure)
        count = len(lot.taus) - 1 >= 1 and lot.taus[-1] + d == t
        if count and lot.U(len(lot.taus) - 1) >= 0:        # S*: the private branch first
            target.deliver(private)
        for B in pending.pop(t, []):
            V.deliver(B)
            target.deliver(B)
        if t >= d and (target.c_loc.pure or V.c_loc.pure):
            last = t
        if t > max(ts) and (last >= max(ts) or lot.A[t] - lot.N(t - d) < -25):
            break                     # a later hit has a chance below exp(-25 theta*) (Lemma 6.4)
    return [last >= T for T in ts]


if __name__ == "__main__":
    rng = random.Random(20261118)
    f, xh, xa, d, n_h, t_sim = 0.25, 0.7, 0.3, 3, 4, 150
    print(f"1. stress runs: f = {f}, x_h = {xh}, x_a = {xa}, d = {d}, {n_h} honest nodes with stake and one without, {t_sim} slots a run")
    print("   strategy, delivery | runs | node-slot checks | (a) growth failures | pure c_loc seen | (b) failures | (c) failures | pure c_loc with X = 0")
    for strategy in ("random", "private", "none"):
        for delays in ("random", "max", "mixed"):
            stats = dict(checks=0, growth=0, pure=0, lemma51=0, lemma52=0, ties=0)
            runs = 1500
            for _ in range(runs):
                stress_run(rng, f, xh, xa, d, n_h, t_sim, strategy, delays, stats)
            print(f"   {strategy}, {delays} | {runs} | {stats['checks']} | {stats['growth']} | {stats['pure']} | "
                  f"{stats['lemma51']} | {stats['lemma52']} | {stats['ties']}")

    print("\n2. the instance of Proposition 9.3 against the recursion")
    TS = (10, 20, 40, 60, 80)
    for f2, xh2, xa2, d2 in ((0.2, 0.7, 0.3, 3), (0.15, 0.63 / 0.93, 0.3 / 0.93, 5)):
        h = -math.expm1(xh2 * math.log1p(-f2))
        a = -math.expm1(xa2 * math.log1p(-f2))
        res = survival_curves(h, a, d2, max(TS))
        runs = 20_000
        hits = [0] * len(TS)
        for _ in range(runs):
            for i, v in enumerate(instance_run(rng, h, a, d2, 20_000, TS)):
                hits[i] += v
        print(f"   f = {f2}, x_h = {xh2:.4f}, x_a = {xa2:.4f}, d = {d2}: h = {h:.5f}, a = {a:.5f}; {runs} runs, each followed "
              f"until the lead X falls below -25 after slot {max(TS)}, or a pure branch is held after slot {max(TS)}")
        for i, T in enumerate(TS):
            p = hits[i] / runs
            q = float(res["Qhat"][T])
            se = math.sqrt(max(q * (1 - q), 0.0) / runs)
            z = f"{(p - q) / se:+.2f}" if se > 1e-9 else "none (both are 1)"
            print(f"     T = {T:3d}: frequency {p:.4f}, Qhat {q:.4f}, z {z}")
