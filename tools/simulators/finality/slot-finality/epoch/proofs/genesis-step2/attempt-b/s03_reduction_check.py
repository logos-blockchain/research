"""PROOF.md, 6.3: a check of the reduction 6.2 on random executions.

The check supports the proof. It does not replace it. It has no epochs: every block is a win of one
lottery. The reduction 6.2 reads no epoch state, so this is no loss for it; the bounds of section 7,
which read epoch states, are not checked here.

Model (slots 1..T, now = T). In each slot honest stake wins with chance ph and the coalition with
chance pa, independently. There are n honest nodes. The leader of an honest win extends a longest
chain among the blocks it holds with smaller slots, ties at random. A node holds an honest block from
1 to delta + 1 slots after its slot (A2), and a coalition block when the coalition releases it to that
node, or never. In each slot it wins the coalition makes one to three blocks: on one of its private
branches (on a block of it, often its longest one), on the longest block of the tree, or on a random
block, each with a slot below the current slot.
J's block tree: every honest block and a random subset of the coalition's blocks, closed under
ancestors. B_imm is genesis (A5). The pass: c_max starts at a random tip, the tips are visited in a
random order, and each visit applies the Bootstrap test (fork choice 123-139) with K and s.

For every choice of H (every honest block of length d(now - delta - 1) with a slot of at most
now - delta - 1), with the events E_d* and E_r* of PROOF.md 5 and 6 restricted to tips (the pass
compares only tips, so the restriction makes the check sharper):
  (1) GENESIS 7.1 Step 0: without E_g, the slot of H's last block exceeds now - K;
  (2) the reduction 6.2: if the final c_max is not in G, then E_d*(sigma) for some sigma <= now - K,
      or E_r*, or E_g; each event is counted where it holds, and so are the failures that only E_r*
      covers, which a reduction without E_r* would miss;
  (3) statement 5.4 at work: at every replacement by length of a c_max Y in G by a bad chain X whose
      last common block with Y lies after D_Y on Y, with Y not containing H (the crossing case of
      GENESIS 7.1 Step 2), E_r* holds with Y as its witness.
Usage: python s03_reduction_check.py > out_03_reduction_check.txt
"""
import random
import sys


def run_execution(rng, T, n_nodes, ph, pa, delta, K=None, quiet=0):
    """With K given, the coalition also runs the scripted attack of the crossing case: from the
    longest honest block at a random slot t0 it extends a withheld branch P in each slot it wins in
    (t0 + quiet, t0 + L1]; from a block D of P it extends a second withheld branch Q up to sl_D + L2;
    L1 and L2 are drawn below K. P's tip is the Y of the crossing case and Q's tip its X. With quiet
    equal to s, P holds no block in the s slots after its divergence block, so that P can stay longer
    than the honest chain without being denser in the window, the case only E_r* covers; the
    coalition then makes no other block, so that no other fork wins a density comparison."""
    parent, slot, honest, length = [None], [0], [True], [0]
    held = [{0: 0} for _ in range(n_nodes)]          # node -> {block: slot from which it holds it}
    private = []                                     # the coalition's private branches (block lists)
    children = [[]]

    def new_block(par, t, hon):
        parent.append(par)
        slot.append(t)
        honest.append(hon)
        length.append(length[par] + 1)
        children.append([])
        children[par].append(len(parent) - 1)
        return len(parent) - 1

    def deliver(n, b, t):
        while b is not None:
            if b not in held[n] or held[n][b] > t:
                held[n][b] = t
            b = parent[b]

    attack = None
    if K is not None:
        t0 = rng.randint(max(2, T - 2 * K), T - K - 1)
        attack = dict(t0=t0, end_p=t0 + rng.randint(K // 2, K - 1), p=None, q=None, d=None, end_q=None,
                      split=rng.random())
    scripted = set()
    for t in range(1, T + 1):
        won = rng.random() < pa
        if attack is not None:
            a = attack
            if t == a["t0"]:
                hon = [b for b in range(len(parent)) if honest[b] and slot[b] < t]
                a["p"] = max(hon, key=lambda b: (length[b], rng.random()))
                a["p_blocks"] = [a["p"]]
            if won and a["p"] is not None and a["t0"] + quiet < t <= a["end_p"]:
                a["p"] = new_block(a["p"], t, False)
                a["p_blocks"].append(a["p"])
                scripted.add(a["p"])
            if a["p"] is not None and t == a["end_p"] + 1 and len(a["p_blocks"]) > 2:
                ok = [b for b in a["p_blocks"][1:] if slot[b] >= a["t0"] + a["split"] * (a["end_p"] - a["t0"])]
                a["d"] = ok[0] if ok else a["p_blocks"][-1]
                a["q"] = a["d"]
                a["end_q"] = slot[a["d"]] + rng.randint(K // 2, K - 1)
            if won and a["q"] is not None and t <= a["end_q"] and slot[a["q"]] < t:
                a["q"] = new_block(a["q"], t, False)
                scripted.add(a["q"])
        if won:
            for _ in range(rng.randint(1, 3) if attack is None else (0 if quiet else rng.randint(0, 2))):
                u = rng.random()
                cand = [b for b in range(len(parent)) if slot[b] < t]
                if u < 0.45:
                    if not private or rng.random() < 0.15:
                        start = rng.choice(cand)
                        private.append([start])
                    br = rng.choice(private)
                    ok = [b for b in br if slot[b] < t]
                    par = max(ok, key=lambda b: (length[b], rng.random())) if rng.random() < 0.7 else rng.choice(ok)
                    nb = new_block(par, t, False)
                    br.append(nb)
                elif u < 0.75:
                    par = max(cand, key=lambda b: (length[b], rng.random()))
                    nb = new_block(par, t, False)
                else:
                    par = rng.choice(cand)
                    nb = new_block(par, t, False)
                if rng.random() < 0.5:                   # released now or later, to some nodes
                    for n in range(n_nodes):
                        if rng.random() < 0.6:
                            deliver(n, nb, t + rng.randint(0, 4 * delta))
        if rng.random() < ph:
            leader = rng.randrange(n_nodes)
            view = [b for b, s0 in held[leader].items() if s0 <= t and slot[b] < t]
            best = max(length[b] for b in view)
            par = rng.choice([b for b in view if length[b] == best])
            hb = new_block(par, t, True)
            for n in range(n_nodes):
                deliver(n, hb, t if n == leader else t + rng.randint(1, delta + 1))
        # the coalition sometimes releases a private branch to every node
        if private and rng.random() < 0.02:
            br = rng.choice(private)
            for n in range(n_nodes):
                deliver(n, br[-1], t + 1)
    return parent, slot, honest, length, scripted


class Tree:
    """J's block tree: a subset of the blocks, closed under ancestors."""

    def __init__(self, parent, slot, honest, length, keep):
        self.parent, self.slot, self.honest, self.length = parent, slot, honest, length
        self.blocks = sorted(keep)
        has_child = set(parent[b] for b in self.blocks if parent[b] is not None)
        self.tips = [b for b in self.blocks if b not in has_child]
        self.anc = {}
        for b in self.blocks:                         # ancestor sets, including the block itself
            p = parent[b]
            self.anc[b] = (self.anc[p] if p is not None else frozenset()) | {b}

    def lca(self, x, y):
        a = self.anc[x]
        while y not in a:
            y = self.parent[y]
        return y

    def density(self, z, d, s):
        """Blocks of the chain of z with slots in (sl_d, sl_d + s] (fork choice 100: blocks only)."""
        lo, hi = self.slot[d], self.slot[d] + s
        c, b = 0, z
        while b is not None and self.slot[b] > lo:
            if self.slot[b] <= hi:
                c += 1
            b = self.parent[b]
        return c


def bootstrap_pass(tree, start, order, K, s, hook=None):
    c_max = start
    for c_fork in order:
        d = tree.lca(c_max, c_fork)
        sl_top = max(tree.slot[c_max], tree.slot[c_fork])
        if tree.slot[d] + K > sl_top:
            if tree.length[c_fork] > tree.length[c_max]:
                if hook:
                    hook(c_max, c_fork, d, "length")
                c_max = c_fork
        else:
            if tree.density(c_max, d, s) < tree.density(c_fork, d, s):
                if hook:
                    hook(c_max, c_fork, d, "density")
                c_max = c_fork
    return c_max


def check(seed, n_exec, T, K, s, delta, ph, pa, n_nodes=3, n_pass=6, attack=False, quiet=False):
    rng = random.Random(seed)
    st = dict(runs=0, hs=0, step0=0, step0_fail=0, fail=0, red_fail=0, by_ed=0, by_er=0, by_eg=0,
              only_er=0, crossing=0, crossing_fail=0, er_runs=0)
    for _ in range(n_exec):
        parent, slot, honest, length, scripted = run_execution(rng, T, n_nodes, ph, pa, delta,
                                                                K if attack else None, s if quiet else 0)
        nb = len(parent)
        keep = set()
        for b in range(nb):
            if honest[b] or b in scripted or rng.random() < 0.85:
                x = b
                while x is not None and x not in keep:
                    keep.add(x)
                    x = parent[x]
        tree = Tree(parent, slot, honest, length, keep)
        now = T
        dref = max(length[b] for b in range(nb) if honest[b] and slot[b] <= now - delta - 1)
        hon_wins = set(slot[b] for b in range(nb) if honest[b] and b != 0)
        e_g = not any(now - K + delta + 1 <= t <= now - delta - 1 for t in hon_wins)
        h_cands = [b for b in range(nb) if honest[b] and slot[b] <= now - delta - 1 and length[b] == dref]
        orders = []
        for _p in range(n_pass):
            start = rng.choice(tree.tips)
            order = tree.tips[:]
            rng.shuffle(order)
            orders.append((start, order))
        for h in h_cands:
            st["hs"] += 1
            Hanc = tree.anc[h]

            def d_of(z):                              # D_Z: the last block Z shares with H
                return tree.lca(z, h)

            def dominant(z):
                return length[z] >= dref

            def bad(z):
                return slot[d_of(z)] + K <= slot[z]

            def in_g(z):
                return dominant(z) and not bad(z)

            # (1) Step 0
            if not e_g:
                st["step0"] += 1
                if slot[h] <= now - K:
                    st["step0_fail"] += 1
            gtips = [z for z in tree.tips if in_g(z)]
            er_star = any(h not in tree.anc[z] and slot[d_of(z)] <= now - K for z in gtips)
            st["er_runs"] += er_star
            for start, order in orders:
                st["runs"] += 1
                crossings = []

                def hook(y, x, d, kind):
                    if kind != "length" or not in_g(y) or h in tree.anc[y]:
                        return
                    dy = d_of(y)
                    if d != dy and dy in tree.anc[d] and bad(x):   # D after D_Y on Y, X bad
                        crossings.append(y)

                final = bootstrap_pass(tree, start, order, K, s, hook)
                for y in crossings:
                    st["crossing"] += 1
                    if not (in_g(y) and h not in tree.anc[y] and slot[d_of(y)] <= now - K):
                        st["crossing_fail"] += 1
                if in_g(final):
                    continue
                st["fail"] += 1
                ed_star = False
                for y in gtips:
                    dy = d_of(y)
                    for x in tree.tips:
                        d = tree.lca(x, y)
                        if slot[d] > now - K or tree.density(x, d, s) < tree.density(y, d, s):
                            continue
                        if d != dy and d in Hanc and d in tree.anc[dy]:
                            ed_star = True
                            break
                    if ed_star:
                        break
                st["by_eg"] += e_g
                st["by_er"] += er_star
                st["by_ed"] += ed_star
                st["only_er"] += er_star and not ed_star and not e_g
                st["red_fail"] += not (e_g or er_star or ed_star)
    return st


if __name__ == "__main__":
    configs = [
        # (seed, executions, T, K, s, delta, ph, pa, scripted attack, quiet start of P)
        (1, 2000, 220, 50, 15, 2, 0.25, 0.20, False, False),
        (2, 2000, 260, 60, 20, 3, 0.25, 0.22, False, False),
        (3, 2000, 200, 40, 39, 2, 0.25, 0.20, False, False),
        (4, 3000, 220, 50, 15, 2, 0.15, 0.35, True, False),
        (5, 3000, 260, 60, 20, 3, 0.15, 0.35, True, False),
        (6, 3000, 200, 40, 10, 1, 0.20, 0.30, True, False),
        (7, 3000, 260, 60, 25, 2, 0.15, 0.50, True, True),
        (8, 3000, 300, 80, 30, 3, 0.15, 0.50, True, True),
    ]
    tot = {}
    for seed, n_exec, T, K, s, delta, ph, pa, attack, quiet in configs:
        st = check(seed, n_exec, T, K, s, delta, ph, pa, attack=attack, quiet=quiet)
        for k, v in st.items():
            tot[k] = tot.get(k, 0) + v
        kind = ("with the scripted attack, P quiet for s slots" if quiet else "with the scripted attack") \
            if attack else "without the scripted attack"
        print(f"seed {seed}: T = {T}, K = {K}, s = {s}, Delta = {delta}, p_h = {ph}, p_a = {pa}, "
              f"{kind}, {n_exec} executions: "
              f"{st['hs']} choices of H, {st['runs']} passes; Step 0 checks {st['step0']}, violations {st['step0_fail']}; "
              f"final c_max not in G: {st['fail']} (with E_g {st['by_eg']}, with E_r* {st['by_er']}, with E_d* {st['by_ed']}, "
              f"with E_r* only {st['only_er']}, with none {st['red_fail']}); crossing events {st['crossing']}, "
              f"without E_r* by Y {st['crossing_fail']}; choices of H with E_r* {st['er_runs']}")
        sys.stdout.flush()
    print(f"total: passes {tot['runs']}; Step 0 violations {tot['step0_fail']} of {tot['step0']}; final c_max not in G "
          f"{tot['fail']}: with E_g {tot['by_eg']}, with E_r* {tot['by_er']}, with E_d* {tot['by_ed']}, with E_r* only "
          f"{tot['only_er']}, with none {tot['red_fail']}; crossing events {tot['crossing']}, "
          f"without E_r* by Y {tot['crossing_fail']}")
