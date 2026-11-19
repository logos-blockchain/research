"""PROOF.md, section 6: random executions with G + 1 < 2K, checking statement 3.2 (Step 2 with the
witness (Y, H)) and the reduction 3.3 on every pass of the Bootstrap rule. A check supports a proof; it
does not replace it.

An execution: slots 1..T, honest nodes that extend the longest chain they hold and receive honest blocks
within Delta slots (GENESIS A2), a coalition that makes 1-3 blocks per won slot on chains of its choice,
some withheld, and keeps a private branch from an honest block near a cut-off (to make the forks of
Step 2 frequent). Every won slot is taken as valid on every chain: the checks below are of the
deterministic statements, and "under H's states" is tested on the inputs of the epoch state: a block of
chain Z in slot t is under H's states if Z and H hold the same blocks below the cut-off that the state of
t's epoch reads (statement 2.2).
J's tree is all blocks, or all honest blocks with a random ancestor-closed share of the coalition's;
now = T. The pass of the Bootstrap rule (fork choice 117-139) runs from a random tip over the tips in a
random order. Checked:
  (1) every transition of c_max from G (dominant and not bad) to outside G is either a density
      replacement with sl_D <= now - K (E_d), or a length replacement in which X contains H and E_g
      holds, or a length replacement with D after D_Y on Y, Y not containing H, X bad, and (Y, H) a
      witness of E_r': sl_{D_Y} <= now - K, sl_Y <= now - 1, len(Y) >= d(now - Delta - 1), and every
      block of Y under H's states. Counted: such cases, and those in which X has a block NOT under H's
      states (where GENESIS's witness (X, H) fails);
  (2) at the end of every pass: c_max in G, or E_d(sigma) for some sigma <= now - K, or E_r' (with H as
      one chain), or E_g.
Usage: python t4_checks.py > out_4_checks.txt
"""
import random


def run_execution(rng, T, n_nodes, ph, pa, delta, cut_offs, private_from):
    blocks = {0: (None, 0, True, 0)}
    known = [{0: 0} for _ in range(n_nodes)]
    nid = 1
    private_tip = None

    def anc(b):
        while b is not None:
            yield b
            b = blocks[b][0]

    def learn(n, b, t):
        for x in anc(b):
            if x not in known[n] or known[n][x] > t:
                known[n][x] = t

    for t in range(1, T + 1):
        h_win = rng.random() < ph
        a_win = rng.random() < pa
        if a_win:
            k = rng.randint(1, 3)
            for j in range(k):
                cands = [b for b, v in blocks.items() if v[1] < t]
                r = rng.random()
                if private_tip is not None and r < 0.45:
                    par = private_tip
                elif r < 0.7:
                    par = max(cands, key=lambda b: (blocks[b][3], rng.random()))
                else:
                    par = rng.choice(cands)
                blocks[nid] = (par, t, False, blocks[par][3] + 1)
                if par == private_tip and j == 0:
                    private_tip = nid
                for n in range(n_nodes):
                    if rng.random() < 0.5:
                        learn(n, nid, t + rng.randint(0, 3 * delta))
                nid += 1
        if h_win:
            leader = rng.randrange(n_nodes)
            view = [b for b, s0 in known[leader].items() if s0 <= t and blocks[b][1] < t]
            best = max(blocks[b][3] for b in view)
            par = rng.choice([b for b in view if blocks[b][3] == best])
            blocks[nid] = (par, t, True, blocks[par][3] + 1)
            for n in range(n_nodes):
                learn(n, nid, t if n == leader else t + rng.randint(1, delta + 1))
            nid += 1
        # start a private branch from the latest honest block, at a chosen slot near a cut-off
        if t in private_from:
            hon = [b for b, v in blocks.items() if v[2] and v[1] <= t]
            private_tip = max(hon, key=lambda b: (blocks[b][1], rng.random()))
    return blocks


def run_attack(rng, n_nodes, ph, pa, delta, K, P, G):
    """The structure of Step 2: honest nodes see only honest blocks. The coalition takes the honest block D_Y
    latest at sigma_0 = c_e - u (epoch e = 1, u uniform in [2, 2K - 2 - G]) and builds, withheld, a branch Y
    from it with a block in each slot it wins up to a random end before sl_{D_Y} + K. Then it picks D among
    the last three blocks of Y and builds a branch X from D with a block in each slot it wins in
    (sl_D, sl_D + K); X can thus reach past sl_{D_Y} + G + 1. now = sl_D + K - 1. Returns
    (blocks, now, Y tip, X tip)."""
    E = P + G
    c_e = E + P
    u = rng.randint(2, 2 * K - 2 - G)
    sigma = c_e - u
    T = sigma + 2 * K + 5
    blocks = {0: (None, 0, True, 0)}
    known = [{0: 0} for _ in range(n_nodes)]
    nid = 1
    y_tip = y_end = None
    y_blocks = []
    a_wins = []

    def anc(b):
        while b is not None:
            yield b
            b = blocks[b][0]

    def learn(n, b, t):
        for x in anc(b):
            if x not in known[n] or known[n][x] > t:
                known[n][x] = t

    for t in range(1, T + 1):
        if rng.random() < pa:
            a_wins.append(t)
            if y_tip is not None and t <= y_end:
                blocks[nid] = (y_tip, t, False, blocks[y_tip][3] + 1)
                y_tip = nid
                y_blocks.append(nid)
                nid += 1
        if rng.random() < ph:
            leader = rng.randrange(n_nodes)
            view = [b for b, s0 in known[leader].items() if s0 <= t and blocks[b][1] < t]
            best = max(blocks[b][3] for b in view)
            par = rng.choice([b for b in view if blocks[b][3] == best])
            blocks[nid] = (par, t, True, blocks[par][3] + 1)
            for n in range(n_nodes):
                learn(n, nid, t if n == leader else t + rng.randint(1, delta + 1))
            nid += 1
        if t == sigma:
            hon = [b for b, v in blocks.items() if v[2]]
            d_y = max(hon, key=lambda b: (blocks[b][3], blocks[b][1]))
            y_tip = d_y
            y_end = blocks[d_y][1] + K - 1 - rng.randint(0, K // 3)
    if not y_blocks:
        return blocks, T, None, None
    d = rng.choice(y_blocks[-3:])
    sd = blocks[d][1]
    now = min(sd + K - 1, T)
    x_tip = d
    for t in a_wins:
        if sd < t <= now:
            blocks[nid] = (x_tip, t, False, blocks[x_tip][3] + 1)
            x_tip = nid
            nid += 1
    # J's tree holds only blocks with slots up to now
    blocks = {k: v for k, v in blocks.items() if v[1] <= now}
    return blocks, now, (y_tip if y_tip in blocks else None), (x_tip if x_tip in blocks else None)


class Tree:
    def __init__(self, blocks, keep):
        self.b = {k: v for k, v in blocks.items() if k in keep}
        self.children = {k: [] for k in self.b}
        for k, (par, *_r) in self.b.items():
            if par is not None:
                self.children[par].append(k)
        self.tips = [k for k, c in self.children.items() if not c]
        self._anc = {}

    def anc(self, x):
        if x not in self._anc:
            out = []
            y = x
            while y is not None:
                out.append(y)
                y = self.b[y][0]
            self._anc[x] = out
        return self._anc[x]

    def ancset(self, x):
        return set(self.anc(x))

    def last_common(self, x, y):
        sx = self.ancset(x)
        for z in self.anc(y):
            if z in sx:
                return z
        return 0

    def slot(self, x):
        return self.b[x][1]

    def length(self, x):
        return self.b[x][3]

    def count_window(self, x, lo, hi):
        """blocks of the chain of x with slots in (lo, hi]"""
        return sum(1 for z in self.anc(x) if lo < self.b[z][1] <= hi)


def check(seed, n_exec, T, n_nodes, ph, pa, delta, K, s, P, G, n_orders=6, attack=False):
    E = P + G
    cut_offs = [e * E + P for e in range(T // E + 2)] if T else []
    rng = random.Random(seed)
    stats = dict(passes=0, trans=0, dens=0, len_eg=0, len_r=0, len_r_x_own=0, viol=0,
                 final_out=0, final_ed=0, final_er=0, final_eg=0, final_viol=0)

    for _ in range(n_exec):
        y_start = None
        if attack:
            blocks, now, y_start, _x = run_attack(rng, n_nodes, ph, pa, delta, K, P, G)
            T = now
        else:
            private_from = {c - rng.randint(2, 2 * K - 2 - G) for c in cut_offs if 0 < c < T}
            blocks = run_execution(rng, T, n_nodes, ph, pa, delta, cut_offs, private_from)
            now = T
        # J's tree: everything, or the honest blocks with a random ancestor-closed share of the coalition's
        if attack or rng.random() < 0.5:
            keep = set(blocks)
        else:
            keep = set()
            for k in sorted(blocks):
                par, sl, hon, ln = blocks[k]
                if (par is None or par in keep) and (hon or rng.random() < 0.7):
                    keep.add(k)
            # J holds H (A2): add every honest block's ancestors
            for k, v in blocks.items():
                if v[2]:
                    y = k
                    while y is not None and y not in keep:
                        keep.add(y)
                        y = blocks[y][0]
        tr = Tree(blocks, keep)
        d = [0] * (T + 2)
        for k, (par, sl, hon, ln) in blocks.items():
            if hon and sl >= 1:
                d[sl] = max(d[sl], ln)
        for t in range(1, T + 2):
            d[t] = max(d[t], d[t - 1])
        dstar = d[now - delta - 1]
        hcands = [k for k, v in blocks.items() if v[2] and v[1] <= now - delta - 1 and v[3] == dstar]
        h_tip = rng.choice(hcands)
        Hs = tr.ancset(h_tip)
        h_blocks_sorted = sorted((tr.slot(z), z) for z in Hs)
        eg = not any(v[2] and now - K + delta + 1 <= v[1] <= now - delta - 1 for v in blocks.values())

        def D_of(z):
            for y in tr.anc(z):
                if y in Hs:
                    return y
            return 0

        def contains_H(z):
            return h_tip in tr.ancset(z)

        def dominant(z):
            return tr.length(z) >= dstar

        def bad(z):
            return tr.slot(D_of(z)) + K <= tr.slot(z)

        def in_G(z):
            return dominant(z) and not bad(z)

        def under_H(z):
            """every block of z after D_z reads, for its slot's epoch state, the blocks H holds below the cut-off"""
            dz = D_of(z)
            zs = sorted((tr.slot(y), y) for y in tr.anc(z))
            for y in tr.anc(z):
                if y == dz:
                    break
                ep = tr.slot(y) // E
                if ep == 0:
                    continue
                c = (ep - 1) * E + P
                if {b for sl, b in zs if sl < c} != {b for sl, b in h_blocks_sorted if sl < c}:
                    return False
            return True

        def ed_any():
            g_tips = [y for y in tr.tips if in_G(y)]
            for y in g_tips:
                for x in tr.tips:
                    if x == y:
                        continue
                    dd = tr.last_common(x, y)
                    sd = tr.slot(dd)
                    if sd <= now - K and tr.count_window(x, sd, sd + s) >= tr.count_window(y, sd, sd + s):
                        return True
            return False

        def er_any():
            for z in tr.b:
                if z in Hs:
                    continue
                dz = D_of(z)
                if (tr.slot(dz) <= now - K and tr.slot(z) <= now - 1 and tr.length(z) >= dstar and under_H(z)):
                    return True
            return False

        for _o in range(n_orders):
            stats["passes"] += 1
            order = tr.tips[:]
            rng.shuffle(order)
            c_max = y_start if (attack and y_start in tr.tips and _o % 2 == 0) else rng.choice(tr.tips)
            for x in order:
                y = c_max
                if x == y:
                    continue
                dd = tr.last_common(x, y)
                sd = tr.slot(dd)
                top = max(tr.slot(x), tr.slot(y))
                if sd + K > top:
                    rep = tr.length(x) > tr.length(y)
                    kind = "len"
                else:
                    rep = tr.count_window(x, sd, sd + s) > tr.count_window(y, sd, sd + s)
                    kind = "dens"
                if rep:
                    if in_G(y) and not in_G(x):
                        stats["trans"] += 1
                        if kind == "dens":
                            stats["dens"] += 1
                            if sd > now - K:
                                stats["viol"] += 1
                        else:
                            dy = D_of(y)
                            after_dy = dd != dy and dy in tr.ancset(dd)
                            if contains_H(x):
                                stats["len_eg"] += 1
                                if not eg:
                                    stats["viol"] += 1
                            elif after_dy and not contains_H(y) and bad(x):
                                stats["len_r"] += 1
                                ok = (tr.slot(dy) <= now - K and tr.slot(y) <= now - 1 and tr.length(y) >= dstar
                                      and under_H(y) and D_of(x) == dy)
                                if not ok:
                                    stats["viol"] += 1
                                if not under_H(x):
                                    stats["len_r_x_own"] += 1
                            else:
                                stats["viol"] += 1
                    c_max = x
            if not in_G(c_max):
                stats["final_out"] += 1
                e1, e2 = ed_any(), er_any()
                stats["final_ed"] += e1
                stats["final_er"] += e2
                stats["final_eg"] += eg
                if not (e1 or e2 or eg):
                    stats["final_viol"] += 1
    return stats


if __name__ == "__main__":
    print("random executions, G + 1 < 2K (the weaker condition s + K <= G + 1 holds); Bootstrap passes in random orders")
    configs = [
        # seed, executions, T, nodes, p_h, p_a, Delta, K, s, P, G
        (1, 150, 260, 4, 0.22, 0.20, 2, 30, 10, 30, 39),
        (2, 150, 260, 4, 0.22, 0.24, 2, 30, 10, 36, 45),
        (3, 150, 300, 4, 0.25, 0.25, 3, 36, 12, 40, 47),
        (4, 150, 300, 3, 0.20, 0.28, 2, 40, 12, 44, 51),
    ]
    attack_configs = [
        # seed, executions, nodes, p_h, p_a, Delta, K, s, P, G
        (11, 400, 3, 0.10, 0.50, 2, 30, 10, 30, 39),
        (12, 400, 3, 0.12, 0.55, 2, 40, 12, 44, 51),
        (13, 400, 4, 0.10, 0.60, 3, 36, 12, 40, 47),
    ]
    runs = [(c, False) for c in configs] + [((a[0], a[1], None) + a[2:], True) for a in attack_configs]
    total = {}
    for cfg, attack in runs:
        seed, n_exec, T, nn, ph, pa, dl, K, s, P, G = cfg
        assert s <= K - 1 and s + K <= G + 1 < 2 * K
        st = check(seed, n_exec, T, nn, ph, pa, dl, K, s, P, G, attack=attack)
        what = ("targeted executions of the structure of Step 2 (D_Y within 2K - 2 - G slots before a cut-off), "
                "the pass started at Y in half of the passes" if attack else f"T = {T}")
        print(f"\n{what}, {nn} honest nodes, p_h = {ph}, p_a = {pa}, Delta = {dl}, K = {K}, s = {s}, P = {P}, G = {G} "
              f"(s + K = {s + K} <= G + 1 = {G + 1} < 2K = {2 * K}); {n_exec} executions, {st['passes']} passes")
        print(f"  (1) transitions of c_max out of G: {st['trans']}: by density with sl_D <= now - K: {st['dens']}; by length "
              f"with X containing H and E_g: {st['len_eg']}; by length with D after D_Y and X bad, (Y, H) witnessing E_r': "
              f"{st['len_r']}, of which X has a block not under H's states: {st['len_r_x_own']}; violations: {st['viol']}")
        print(f"  (2) passes ending outside G: {st['final_out']}; with E_d: {st['final_ed']}, with E_r': {st['final_er']}, "
              f"with E_g: {st['final_eg']}; with none of the three: {st['final_viol']}")
        for key, val in st.items():
            total[key] = total.get(key, 0) + val
    print(f"\nall runs: {total['passes']} passes; transitions out of G {total['trans']} = density {total['dens']} + length with "
          f"E_g {total['len_eg']} + length with (Y, H) witnessing E_r' {total['len_r']} (X with a block not under H's states: "
          f"{total['len_r_x_own']}); violations {total['viol']}; passes ending outside G {total['final_out']}, with none of "
          f"E_d, E_r', E_g: {total['final_viol']}")
