"""CHECK.md, item 4: an independent search for counterexamples to the reduction of GENESIS 7.1 as repaired
by attempts A and B, with every chain deriving its own epoch states as the specification derives them.

Written from the specification and GENESIS's definitions only; it shares no code with either attempt.

Model (small parameters):
  - Slots 1..now; genesis in slot 0. Epoch e = [eE, (e+1)E), E = L1 + G; cut-off c_e = eE + L1.
  - Epoch state of epoch ep for a chain (protocol 205-249): snapshot = the chain's last block below the
    epoch's predecessor's first slot (REVIEW's A4: the root reads blocks below that slot); nonce = eta of
    the chain's last block below c_(ep-1); D = the inference (inference 77-87, integers, truncation
    toward zero, beta = 2/3, PRECISION = 1000) applied to D of epoch ep - 1 and to the distinct occupied
    slots of [sl_(ep-1), sl_(ep-1) + PERIOD), PERIOD = L1, from the chain's blocks in the window and the
    uncles they reference that lie in the window.
  - eta_B = H(eta_parent, rho, slot), rho = H(slot, note) (protocol 192, leadership 185).
  - Lottery: a party of stake v wins slot t under state (snap, eta, D) iff
    H(snap, eta, t, party) < 1 - (1 - f)^(v/D).  A block is valid iff its maker wins its slot under the
    state its own chain derives.  The coalition is one party.
  - Honest nodes extend their longest chain (a tie keeps the current one), reference up to 4 uncles whose
    parent lies on the chain at most W slots back, and receive every honest block within Delta + 1 slots
    (visible from slot t + d, 1 <= d <= Delta + 1: A2).  B_imm of honest nodes stays at genesis.
  - The coalition knows every block at once.  Live: private branches extended at its wins, new branches
    from recent blocks, and (optionally) publication of a private tip to the honest nodes.  After the
    run (withheld blocks, so building them late changes nothing): crossing attacks (Y from an honest
    block D_Y = c_e - u, u in [2, 2K - 2 - G] when that range is not empty, X from a late block of Y,
    X past sl(D_Y) + K, below sl(D) + K), forks from 2 slots before each cut-off, dense forks from blocks
    of the honest chain and from blocks of the crossing branches.
  - J holds every block, B_imm = genesis, and runs one pass of the Bootstrap rule (fork choice 116-140)
    from several starts and orders.

Checked, for every choice of H (every honest block of greatest length with slot <= now - Delta - 1),
on runs where S holds:
  - every pass that ends outside G meets B's events (E_d*, E_r*, E_g) and A's events (E_d, E_r', E_g),
    in the literal form (all chains) and in a sharp form (tips only, X != Y);
  - the first exit from G after the last H-tip visit, classified as GENESIS 7.1 Steps 1 and 2 and the
    repairs classify it; in the crossing case whether GENESIS's witness X is made under H's states;
  - the structural claims the bounds need: 3.1 (honest blocks under H's states); B 5.3 (E_r* witnesses
    under H's states, tip <= now - 1); B 7.1 (E_d* witnesses: Y and X's window under H's states);
    GENESIS 6.1 for every E_d witness (X's window under H's states); the extension of 6.3's first case and
    of 7.2's second bound (the added slots derive H's states on the extended chain), for E_d* witnesses
    and for E_d witnesses whose divergence block lies after D_Y.
Usage: python c4_sim.py [runs_per_gap] > out_c4_sim.txt
"""
from __future__ import annotations

import bisect
import math
import os
import random
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

sys.dont_write_bytecode = True
MASK = (1 << 64) - 1
TWO64 = float(1 << 64)


def mix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & MASK
    return x ^ (x >> 31)


def hh(*args) -> int:
    v = 0x5DEECE66D
    for a in args:
        v = mix64(v ^ (a & MASK))
    return v


def tdiv(a: int, b: int) -> int:
    """Integer division truncating toward zero (Rust's i128 /)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


class Cfg:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.E = self.L1 + self.G
        self.PERIOD = self.L1
        self.f_p = int(self.f * 1000)

    def short(self):
        return (f"K={self.K} s={self.s} Delta={self.Delta} L1={self.L1} G={self.G} E={self.E} f={self.f} "
                f"alpha={self.alpha} nh={self.nh} now={self.now} pub={self.p_pub} quiet={self.p_quiet} "
                f"focused={self.focused} sigma0={self.sigma0}")


class Run:
    def __init__(self, cfg: Cfg, seed: int):
        self.c = cfg
        self.seed = seed
        self.rng = random.Random(seed)
        self.parent = [-1]
        self.slot = [0]
        self.maker = [-1]
        self.length = [0]
        self.anc = [1]
        self.eta = [hh(seed, 1)]
        self.unc = [()]
        self.cids = [[0]]
        self.csl = [[0]]
        self.virtual = [False]
        self.memo = {}
        nh = cfg.nh
        hs = [(1 - cfg.alpha) / nh] * nh
        self.stake = [x * 1000.0 for x in hs] + [cfg.alpha * 1000.0]
        self.A = nh
        self.D0 = 1000
        self.honest = []
        self.cross = []          # (D_Y, Y, D, X) of the crossing attempts

    # --- blocks -------------------------------------------------------------------------------------
    def add(self, p, t, m, unc=(), virtual=False):
        i = len(self.parent)
        self.parent.append(p)
        self.slot.append(t)
        self.maker.append(m)
        self.length.append(self.length[p] + 1)
        self.anc.append(self.anc[p] | (1 << i))
        self.eta.append(hh(self.eta[p], hh(t, m, 99), t))
        self.unc.append(tuple(unc))
        self.cids.append(self.cids[p] + [i])
        self.csl.append(self.csl[p] + [t])
        self.virtual.append(virtual)
        return i

    def last_below(self, b, x):
        """The chain's last block with slot < x (genesis has slot 0); -1 if x <= 0."""
        if x <= 0:
            return -1
        k = bisect.bisect_left(self.csl[b], x) - 1
        return self.cids[b][k]

    def last_at_most(self, b, x):
        return self.last_below(b, x + 1)

    def count(self, b, lo, hi):
        """Blocks of the chain of b with slots in (lo, hi] (fork choice: density)."""
        cs = self.csl[b]
        return bisect.bisect_right(cs, hi) - bisect.bisect_right(cs, lo)

    def lca(self, x, y):
        return (self.anc[x] & self.anc[y]).bit_length() - 1

    def isanc(self, a, b):
        """a is b or an ancestor of b."""
        return (self.anc[b] >> a) & 1 == 1

    # --- epoch state --------------------------------------------------------------------------------
    def infer(self, D, N):
        c = self.c
        tse = D * 1000
        exp_ = c.PERIOD * c.f_p
        diff = exp_ - N * 1000
        err = tdiv(tse * diff, exp_)
        corr = tdiv(2 * err, 3)
        return max(tdiv(tse - corr, 1000), 1)

    def window_count(self, bp, lo, hi):
        occ = set()
        cs, ci = self.csl[bp], self.cids[bp]
        k0 = bisect.bisect_left(cs, lo)
        k1 = bisect.bisect_left(cs, hi)
        for k in range(max(k0, 1), k1):          # genesis is not a lottery win
            occ.add(cs[k])
            for u in self.unc[ci[k]]:
                su = self.slot[u]
                if lo <= su < hi:
                    occ.add(su)
        return len(occ)

    def state(self, b, ep):
        """(snapshot, nonce, D) of epoch ep as the chain of b derives it."""
        if ep == 0:
            return (-1, self.eta[0], self.D0)
        c = self.c
        cut = (ep - 1) * c.E + c.L1
        bp = self.last_below(b, cut)
        key = (bp, ep)
        r = self.memo.get(key)
        if r is not None:
            return r
        sl0 = (ep - 1) * c.E
        snap = self.last_below(bp, sl0)
        Dp = self.state(bp, ep - 1)[2]
        N = self.window_count(bp, sl0, sl0 + c.PERIOD)
        r = (snap, self.eta[bp], self.infer(Dp, N))
        self.memo[key] = r
        return r

    def wins(self, party, t, st):
        snap, eta, D = st
        thr = -math.expm1((self.stake[party] / D) * math.log1p(-self.c.f))
        return hh(snap, eta, t, party, 4242) / TWO64 < thr

    def ep(self, t):
        return t // self.c.E

    # --- the execution ------------------------------------------------------------------------------
    def deliver(self, V, tips, j, b):
        if b in V:
            return
        for x in reversed(self.cids[b]):
            if x in V:
                break
            V.add(x)
        if self.length[b] > self.length[tips[j]]:
            tips[j] = b

    def pick_uncles(self, V, p, t, recent):
        c = self.c
        out = []
        for u in recent:
            if len(out) >= 4:
                break
            if u not in V or self.slot[u] >= t or self.isanc(u, p):
                continue
            q = self.parent[u]
            if q < 0 or not self.isanc(q, p) or self.slot[q] < t - c.W:
                continue
            # not referenced already by a block of the chain after the uncle's parent
            dup = False
            for x in reversed(self.cids[p]):
                if self.slot[x] <= self.slot[q]:
                    break
                if u in self.unc[x]:
                    dup = True
                    break
            if not dup:
                out.append(u)
        return out

    def simulate(self):
        c, rng = self.c, self.rng
        nh, A = c.nh, self.A
        V = [{0} for _ in range(nh)]
        tips = [0] * nh
        self.cl = [[0] * (c.now + 1) for _ in range(nh)]
        deliv = defaultdict(list)
        priv = []
        for t in range(1, c.now + 1):
            for (j, b) in deliv.pop(t, ()):
                self.deliver(V[j], tips, j, b)
            for j in range(nh):
                self.cl[j][t] = tips[j]
            e = self.ep(t)
            recent = [b for b in range(len(self.parent) - 1, 0, -1) if self.slot[b] >= t - c.W - 1][::-1]
            for j in range(nh):
                p = tips[j]
                if self.wins(j, t, self.state(p, e)):
                    b = self.add(p, t, j, self.pick_uncles(V[j], p, t, recent))
                    self.honest.append(b)
                    V[j].add(b)
                    tips[j] = b
                    for k in range(nh):
                        if k != j:
                            deliv[t + rng.randint(1, c.Delta + 1)].append((k, b))
            # the coalition, live (none in the focused mode, where only the crossing branches are built)
            if c.focused:
                continue
            newp = []
            for p in priv:
                if rng.random() < 0.85 and self.wins(A, t, self.state(p, e)):
                    newp.append(self.add(p, t, A))
                    if rng.random() < 0.25:
                        newp.append(p)
                else:
                    newp.append(p)
            if rng.random() < 0.35:
                cands = [b for b in range(len(self.parent)) if t - 3 * c.K <= self.slot[b] < t]
                if cands:
                    q = rng.choice(cands)
                    if self.wins(A, t, self.state(q, e)):
                        newp.append(self.add(q, t, A))
            priv = newp[-10:]
            if c.p_pub > 0 and priv and rng.random() < c.p_pub:
                b = rng.choice(priv)
                for k in range(nh):
                    deliv[t + rng.randint(1, c.Delta + 1)].append((k, b))
        self.retro()

    def grow(self, base, lo, hi, skip=None, take=1.0):
        """Extend base by a coalition block in each slot of [lo, hi] it wins on the growing chain."""
        cur = base
        rng = self.rng
        for t in range(lo, hi + 1):
            if skip is not None and skip[0] <= t <= skip[1]:
                continue
            if self.wins(self.A, t, self.state(cur, self.ep(t))) and rng.random() < take:
                cur = self.add(cur, t, self.A)
        return cur

    def retro(self):
        """Withheld branches built after the run (the coalition could have built them in time)."""
        c, rng = self.c, self.rng
        lim = c.now - c.Delta - 1
        cand = [b for b in self.honest if self.slot[b] <= lim] or [0]
        lm = max(self.length[b] for b in cand)
        proxy = min(b for b in cand if self.length[b] == lm)          # a stand-in for H
        n_real = len(self.parent)
        # crossing attempts
        umax = max(2, 2 * c.K - 2 - c.G)
        for _ in range(c.n_cross):
            u = rng.randint(2, umax)
            if c.focused:
                opts = [c.sigma0]
                s0 = c.sigma0
                DY = self.last_at_most(proxy, s0)
                sDY = self.slot[DY]
                quiet = rng.random() < c.p_quiet
                Y = self.grow(DY, sDY + 1, min(sDY + c.K - 1, c.now - 1),
                              skip=(sDY + 1, sDY + c.s) if quiet else None)
                if Y == DY:
                    continue
                ys = [x for x in self.cids[Y] if self.slot[x] > sDY]
                late = [x for x in ys if self.slot[x] >= sDY + c.G + 3 - c.K]
                D = rng.choice(late) if late and rng.random() < 0.7 else rng.choice(ys)
                X = self.grow(D, self.slot[D] + 1, min(self.slot[D] + c.K - 1, c.now))
                self.cross.append((DY, Y, D, X))
                continue
            # an epoch whose c_e - u lies within a few K of now - K
            opts = []
            e = 0
            while e * c.E + c.L1 - u <= c.now:
                s0 = e * c.E + c.L1 - u
                if 1 <= s0 <= c.now - c.K and s0 >= c.now - c.K - c.cross_slack:
                    opts.append(s0)
                e += 1
            if not opts:
                s0 = rng.randint(1, max(1, c.now - c.K))
            else:
                s0 = rng.choice(opts)
            DY = self.last_at_most(proxy, s0)
            sDY = self.slot[DY]
            quiet = rng.random() < c.p_quiet
            Y = self.grow(DY, sDY + 1, min(sDY + c.K - 1, c.now - 1),
                          skip=(sDY + 1, sDY + c.s) if quiet else None)
            if Y == DY:
                continue
            ys = [x for x in self.cids[Y] if self.slot[x] > sDY]
            late = [x for x in ys if self.slot[x] >= sDY + c.G + 3 - c.K]
            D = rng.choice(late) if late and rng.random() < 0.7 else rng.choice(ys)
            X = self.grow(D, self.slot[D] + 1, min(self.slot[D] + c.K - 1, c.now))
            self.cross.append((DY, Y, D, X))
            # a dense fork from a block of Y after D_Y (an E_d witness whose D lies after D_Y)
            D2 = rng.choice(ys)
            self.grow(D2, self.slot[D2] + 1, min(self.slot[D2] + c.s + rng.randint(0, c.K), c.now))
        if c.focused:
            self.n_tree = len(self.parent)
            return
        # forks from 2 slots before each cut-off
        e = 0
        while e * c.E + c.L1 - 2 <= c.now:
            ce = e * c.E + c.L1
            if ce - 2 >= 1 and rng.random() < 0.8:
                D = self.last_at_most(proxy, ce - 2)
                self.grow(D, self.slot[D] + 1, min(self.slot[D] + rng.randint(c.s, 2 * c.K), c.now), take=0.9)
            e += 1
        # dense forks from blocks of the honest chain
        hb = [x for x in self.cids[proxy] if self.slot[x] <= c.now - c.K]
        for _ in range(c.n_dense):
            if not hb:
                break
            D = rng.choice(hb)
            self.grow(D, self.slot[D] + 1, min(self.slot[D] + c.s + rng.randint(0, c.K), c.now))
        self.n_tree = len(self.parent)

    # --- the Bootstrap pass -------------------------------------------------------------------------
    def bpass(self, start, order):
        c = self.c
        cm = start
        trace = []
        for x in order:
            D = self.lca(cm, x)
            sd = self.slot[D]
            top = max(self.slot[cm], self.slot[x])
            if sd + c.K > top:
                kind = "len"
                rep = self.length[x] > self.length[cm]
            else:
                kind = "den"
                rep = self.count(x, sd, sd + c.s) > self.count(cm, sd, sd + c.s)
            trace.append((x, cm, D, kind, rep))
            if rep:
                cm = x
        return cm, trace


# ------------------------------------------------------------------------------------------------------
# analysis of one run for one choice of H
# ------------------------------------------------------------------------------------------------------
def analyse(run: Run, h: int, stats: dict, viol: list, examples: dict, max_ext=6):
    c = run.c
    now, K, s, Dl = c.now, c.K, c.s, c.Delta
    n = run.n_tree
    tree = range(n)
    # S: every honest node's chain at every slot agrees with H in the slots up to t - K
    for j in range(c.nh):
        for t in range(K + 1, now + 1):
            if run.last_at_most(run.cl[j][t], t - K) != run.last_at_most(h, t - K):
                stats["H choices without S"] += 1
                return
    stats["H choices with S"] += 1
    Hst = {}

    def hstate(t):
        e = run.ep(t)
        if e not in Hst:
            Hst[e] = run.state(h, e)
        return Hst[e]

    underH = [True] * n
    for b in range(1, n):
        underH[b] = run.wins(run.maker[b], run.slot[b], hstate(run.slot[b]))
    allH = [True] * n
    for b in range(1, n):
        allH[b] = allH[run.parent[b]] and underH[b]
    # 3.1: honest blocks under H's states (their chain derives H's state)
    for b in run.honest:
        stats["3.1 honest blocks"] += 1
        if run.state(run.parent[b], run.ep(run.slot[b])) != hstate(run.slot[b]):
            stats["3.1 VIOLATIONS"] += 1
    lenH = run.length[h]
    DZ = [run.lca(b, h) for b in tree]
    contH = [run.isanc(h, b) for b in tree]
    inG = [run.length[b] >= lenH and run.slot[DZ[b]] + K > run.slot[b] for b in tree]
    children = [0] * n
    for b in range(1, n):
        children[run.parent[b]] += 1
    tips = [b for b in tree if children[b] == 0]
    Glist = [b for b in tree if inG[b]]
    Gtips = [b for b in tips if inG[b]]
    # E_g: honest stake wins no slot of [now - K + Dl + 1, now - Dl - 1] under H's states
    Eg = not any(run.wins(j, t, hstate(t)) for t in range(now - K + Dl + 1, now - Dl) for j in range(c.nh))
    # Step 0: every dominant chain containing H lies in G unless E_g
    for b in tree:
        if contH[b] and run.length[b] >= lenH:
            stats["Step 0 checks"] += 1
            if not inG[b] and not Eg:
                stats["Step 0 VIOLATIONS"] += 1
    # E_r* (B): a chain of G not containing H that left H at a slot <= now - K
    ErS = [Z for Z in Glist if not contH[Z] and run.slot[DZ[Z]] <= now - K]
    ErS_tips = [Z for Z in ErS if children[Z] == 0]
    for Z in ErS:
        stats["B 5.3: E_r* witnesses"] += 1
        if not allH[Z] or run.slot[Z] > now - 1:
            stats["B 5.3 VIOLATIONS (witness not under H's states or tip > now - 1)"] += 1
    # E_r' (A): two chains under H's states, tips <= now - 1, length >= len(H), sharing no block from now - K + 1
    cands = [b for b in tree if run.slot[b] <= now - 1 and run.length[b] >= lenH and allH[b]]
    Erp = False
    for i in range(len(cands)):
        for k in range(i + 1, len(cands)):
            if run.slot[run.lca(cands[i], cands[k])] <= now - K:
                Erp = True
                break
        if Erp:
            break
    # GENESIS's E_r as written (chains made by slot now)
    cands2 = [b for b in tree if run.length[b] >= lenH and allH[b]]
    Er_lit = any(run.slot[run.lca(cands2[i], cands2[k])] <= now - K
                 for i in range(len(cands2)) for k in range(i + 1, len(cands2)))
    # E_d and E_d*: literal (X any chain, Y in G) and sharp (X, Y tips, X != Y)
    Ed = Eds = EdS = EdsS = False
    w_star, w_gen_after = [], []
    for Y in Glist:
        DY = DZ[Y]
        for X in tree:
            D = run.lca(X, Y)
            sig = run.slot[D]
            if sig > now - K:
                continue
            if run.count(X, sig, sig + s) < run.count(Y, sig, sig + s):
                continue
            star = D != DY and run.isanc(D, DY)                 # D a block of H strictly before D_Y
            sharp = children[X] == 0 and children[Y] == 0 and X != Y
            Ed = True
            EdS = EdS or sharp
            if star:
                Eds = True
                EdsS = EdsS or sharp
                w_star.append((X, Y, D))
            elif run.isanc(DY, D):
                w_gen_after.append((X, Y, D))
    # structural claims on the witnesses
    for (X, Y, D) in w_star:
        stats["B 7.1: E_d* witnesses"] += 1
        sig = run.slot[D]
        win_ok = all(underH[b] for b in run.cids[X] if sig < run.slot[b] <= sig + s)
        if not allH[Y] or not win_ok:
            stats["B 7.1 VIOLATIONS (Y or X's window not under H's states)"] += 1
    for (X, Y, D) in w_gen_after:
        stats["GENESIS 6.1 on E_d witnesses with D at/after D_Y"] += 1
        DY = DZ[Y]
        if not ((not contH[Y] and run.slot[DY] <= now - K) or (contH[Y] and Eg)):
            stats["  ... E_d witness with D at/after D_Y outside E_r* and E_g VIOLATION (B 7.3 remark)"] += 1
        sig = run.slot[D]
        if not all(underH[b] for b in run.cids[X] if sig < run.slot[b] <= sig + s):
            stats["  ... X's window not under H's states (6.1 needs s + K <= G + 2)"] += 1
    # the extensions of 6.3 (first case) and of 7.2 (second bound)
    rng = run.rng

    def extension(X, sig, lo, hi):
        """Extend X[0:sig+s] by a coalition block in each slot of [lo, hi] that the coalition wins under
        H's states; return (all added slots derive H's state, all added blocks valid, final length)."""
        cur = run.last_at_most(X, sig + s)
        same = valid = True
        first_bad = None
        for t in range(lo, hi + 1):
            if not run.wins(run.A, t, hstate(t)):
                continue
            st = run.state(cur, run.ep(t))
            if st != hstate(t):
                same = False
                if first_bad is None:
                    first_bad = (t, run.ep(t), st, hstate(t))
            if not run.wins(run.A, t, st):
                valid = False
            cur = run.add(cur, t, run.A, virtual=True)
        extension.first_bad = first_bad
        return same, valid, run.length[cur]

    for label, ws in (("E_d*", w_star), ("E_d with D after D_Y", w_gen_after)):
        sample = ws if len(ws) <= max_ext else rng.sample(ws, max_ext)
        for (X, Y, D) in sample:
            sig = run.slot[D]
            e = sig + s
            hon = [b for b in run.cids[Y] if run.slot[b] > e and run.maker[b] < run.A and run.maker[b] >= 0]
            b_ = run.slot[hon[0]] if hon else now + 1
            if hon and b_ <= sig + c.G + 1:                       # 6.3, first case
                same, valid, ln = extension(X, sig, e + 1, b_ - 1)
                stats[f"6.3 case 1 extension, {label}"] += 1
                if not same:
                    stats[f"  ... 6.3 case 1, {label}: an added slot not under H's states"] += 1
                if ln < run.length[run.last_at_most(Y, b_ - 1)]:
                    stats[f"  ... 6.3 case 1, {label}: extension shorter than Y[0:b-1]"] += 1
            elif not hon and now <= sig + c.G:                     # 7.2, second bound (6.3 third case)
                same, valid, ln = extension(X, sig, e + 1, now)
                stats[f"7.2 second-bound extension, {label}"] += 1
                if not same:
                    stats[f"  ... 7.2 second bound, {label}: an added slot not under H's states"] += 1
                    key = f"7.2 second bound, {label}"
                    if key not in examples:
                        t_, e_, st_, hs_ = extension.first_bad
                        DY = DZ[Y]
                        examples[key] = (f"seed {run.seed} [{c.short()}]: H = block {h} (slot {run.slot[h]}); Y = block {Y} "
                                         f"(slot {run.slot[Y]}, D_Y slot {run.slot[DY]}); X = block {X} (slot {run.slot[X]}); "
                                         f"D slot {sig}; Y has no honest block after {e}; now = {now} <= sigma + G = {sig + c.G}; "
                                         f"added slot {t_} (epoch {e_}, > sl(D_Y) + G + 1 = {run.slot[DY] + c.G + 1}) derives "
                                         f"(snapshot, nonce, D) = {st_[0]}, {st_[1] % 10**6}..., {st_[2]} on the extension and "
                                         f"{hs_[0]}, {hs_[1] % 10**6}..., {hs_[2]} on H; E_r* {bool(ErS)}, E_g {Eg}")
                if not valid:
                    stats[f"  ... 7.2 second bound, {label}: an added block invalid on its own chain"] += 1
                if ln < lenH:
                    stats[f"  ... 7.2 second bound, {label}: extension shorter than H"] += 1
    # passes
    Htips = [b for b in tips if contH[b]]
    order_sets = []
    for k in range(c.n_pass):
        start = rng.choice(tips)
        if k == 1 and ErS_tips:
            start = rng.choice(ErS_tips)
        order = tips[:]
        rng.shuffle(order)
        if k == 2:
            order.sort(key=lambda b: hh(b, run.seed, 5))         # by "block ID"
        if k in (1, 3):
            order = [b for b in order if contH[b]] + [b for b in order if not contH[b]]
        order_sets.append((start, order))
    covB = Eg or bool(ErS) or Eds
    covA = Eg or Erp or Ed
    covBs = Eg or bool(ErS_tips) or EdsS
    covAs = Eg or Erp or EdS
    for (start, order) in order_sets:
        stats["passes"] += 1
        cm, trace = run.bpass(start, order)
        if not inG[cm]:
            stats["passes ending outside G"] += 1
            stats["  ... with E_g"] += Eg
            stats["  ... with E_r*"] += bool(ErS)
            stats["  ... with E_d*"] += Eds
            stats["  ... with E_r'"] += Erp
            stats["  ... with E_d"] += Ed
            stats["  ... with E_r as GENESIS writes it"] += Er_lit
            stats["  ... B covered only by E_r*"] += bool(ErS) and not Eg and not Eds
            stats["  ... A covered only by E_r'"] += Erp and not Eg and not Ed
            stats["  ... A covered only by E_r', sharp form"] += Erp and not Eg and not EdS
            stats["  ... B covered only by E_r*, sharp form"] += bool(ErS_tips) and not Eg and not EdsS
            if not covB:
                stats["  ... B's events MISS (violation)"] += 1
            if not covA:
                stats["  ... A's events MISS (violation)"] += 1
            if not covBs:
                stats["  ... B's events, sharp form, MISS"] += 1
            if not covAs:
                stats["  ... A's events, sharp form, MISS"] += 1
            if (not covB or not covA) and len(viol) < 5:
                viol.append(f"seed {run.seed} [{c.short()}] H = block {h} (slot {run.slot[h]}, len {lenH}); start {start}; "
                            f"final {cm} (slot {run.slot[cm]}, len {run.length[cm]}, D_Z slot {run.slot[DZ[cm]]}); "
                            f"E_g {Eg} E_r* {bool(ErS)} E_d* {Eds} E_r' {Erp} E_d {Ed}")
        # classify the first exit from G at or after the last H-tip visit
        last = max((i for i, tr in enumerate(trace) if contH[tr[0]]), default=None)
        if last is None:
            stats["  passes without an H-tip (A2 fails)"] += 1
            continue
        x, y0, D, kind, rep = trace[last]
        after = x if rep else y0
        if not inG[after]:
            if rep:
                key = "Step 1: H-tip adopted, outside G" + (" (E_g)" if Eg else " VIOLATION")
            elif kind == "den":
                if run.isanc(D, h) and D != h and run.slot[D] <= now - K:
                    key = "Step 1: kept by density -> E_d*(sl_D)"
                else:
                    key = "Step 1: kept by density, D at/after H's tip" + (" (E_g)" if Eg else " VIOLATION")
            else:
                key = "Step 1: kept by length, outside G" + (" (E_g)" if Eg else " VIOLATION")
            stats[key] += 1
            continue
        for (x, y, D, kind, rep) in trace[last + 1:]:
            if not rep:
                continue
            if inG[x]:
                continue
            DY = DZ[y]
            if kind == "den":
                if D != DY and run.isanc(D, DY) and run.slot[D] <= now - K:
                    stats["Step 2: density -> E_d*(sl_D)"] += 1
                elif not contH[y] and run.slot[DY] <= now - K:
                    stats["Step 2: density, D at/after D_Y -> E_r* by Y (B 5.2)"] += 1
                elif contH[y] and Eg:
                    stats["Step 2: density, D at/after D_Y, Y contains H -> E_g"] += 1
                else:
                    stats["Step 2: density, D at/after D_Y VIOLATION"] += 1
            elif contH[x]:
                stats["Step 2: length, X contains H" + (" (E_g)" if Eg else " VIOLATION")] += 1
            elif D != DY and run.isanc(DY, D) and not contH[y]:
                okB = (not contH[y]) and run.slot[DY] <= now - K and inG[y]
                okA = okB and allH[y] and run.slot[y] <= now - 1
                stats["Step 2: crossing (D after D_Y, X bad)"] += 1
                if not okB:
                    stats["  ... crossing: Y not an E_r* witness VIOLATION"] += 1
                if not okA:
                    stats["  ... crossing: (Y, H) not an E_r' witness VIOLATION"] += 1
                if not allH[x]:
                    stats["  ... crossing: GENESIS's witness X not under H's states"] += 1
                    if "crossing" not in examples:
                        bad = [b for b in run.cids[x] if not underH[b]]
                        b0 = bad[0]
                        pre = [b for b in run.cids[x] if run.slot[DY] < run.slot[b] < (run.ep(run.slot[DY]) * c.E + c.L1)]
                        examples["crossing"] = (f"seed {run.seed} [{c.short()}]: H = block {h} (slot {run.slot[h]}); "
                                                f"Y = block {y} (slot {run.slot[y]}, len {run.length[y]}), D_Y slot {run.slot[DY]} "
                                                f"(cut-off {run.ep(run.slot[DY]) * c.E + c.L1}); D slot {run.slot[D]}; "
                                                f"X = block {x} (slot {run.slot[x]}, len {run.length[x]}); X's blocks before the "
                                                f"cut-off after D_Y at slots {[run.slot[b] for b in pre]}; X's block in slot "
                                                f"{run.slot[b0]} (epoch {run.ep(run.slot[b0])}) is a coalition win on X but not "
                                                f"under H's states; Y witnesses E_r*: {okB}, (Y, H) witnesses E_r': {okA}")
            else:
                stats["Step 2: other exit VIOLATION"] += 1
            break


def make_cfg(cfgd, seed):
    """The configuration of the run with this seed (the random choices depend on the seed only)."""
    rng = random.Random(seed ^ 0xABCDEF)
    cfg = Cfg(**cfgd, alpha=rng.choice((0.2, 0.3, 0.45, 0.55)), nh=rng.choice((2, 3)),
              f=rng.choice((0.25, 0.4)),
              Delta=rng.choice((1, 2)), s=rng.choice((3, 5, cfgd["K"] - 1)),
              L1=rng.choice((cfgd["K"], 2 * cfgd["K"])),
              p_pub=rng.choice((0.0, 0.0, 0.05)), p_quiet=rng.choice((0.0, 0.5)),
              now=0, W=4, n_cross=6, n_dense=6, cross_slack=2 * cfgd["K"], n_pass=4)
    cfg.focused = rng.random() < 0.45
    cfg.sigma0 = 0
    if cfg.focused:
        u = 2 if rng.random() < 0.5 else rng.randint(2, max(2, 2 * cfg.K - 2 - cfg.G))
        cfg.sigma0 = rng.choice((2, 3, 4)) * cfg.E + cfg.L1 - u
        if rng.random() < 0.5:
            rr = rng.randint(0, cfg.Delta + 1)
        else:                                          # far enough for X to reach the next epoch
            rr = rng.randint(0, max(0, u + cfg.G - cfg.K + 2))
        cfg.now = cfg.sigma0 + cfg.K + rr
        cfg.p_quiet = rng.choice((0.0, 0.5, 1.0))
        cfg.alpha = rng.choice((0.45, 0.55, 0.65))
        cfg.nh = rng.choice((1, 1, 2, 3))
        cfg.__init__(**cfg.__dict__)
    else:
        cfg.now = rng.randint(3 * cfg.E, 5 * cfg.E)
    return cfg


def do_run(cfgd, seed, stats, viol, examples):
    cfg = make_cfg(cfgd, seed)
    stats["runs, focused mode"] += cfg.focused
    run = Run(cfg, seed)
    run.simulate()
    stats["runs"] += 1
    lim = cfg.now - cfg.Delta - 1
    cand = [b for b in run.honest if run.slot[b] <= lim] or [0]
    lm = max(run.length[b] for b in cand)
    Hs = [b for b in cand if run.length[b] == lm]
    stats["blocks"] += run.n_tree
    for h in Hs[:3]:
        analyse(run, h, stats, viol, examples)


def one_config(args):
    cfgd, runs, base_seed = args
    stats = defaultdict(int)
    viol = []
    examples = {}
    t0 = time.time()
    for r in range(runs):
        do_run(cfgd, base_seed * 1_000_003 + r, stats, viol, examples)
    return cfgd, dict(stats), viol, examples, time.time() - t0


def replay(K, G, seed):
    """Re-run one execution of the search (for example one quoted in out_c4_sim.txt) and return its
    counters and examples: python -c "import c4_sim; print(c4_sim.replay(12, 18, 12181037444))"."""
    stats, viol, examples = defaultdict(int), [], {}
    do_run({"K": K, "G": G}, seed, stats, viol, examples)
    return dict(stats), viol, examples


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    jobs = []
    for K in (10, 12, 16):
        for G in range(K - 3, 2 * K - 1):
            for part in range(4):
                jobs.append(({"K": K, "G": G}, runs // 4, K * 1000 + G * 10 + part))
    with Pool(min(14, os.cpu_count() or 1)) as pool:
        res = pool.map(one_config, jobs)
    agg = defaultdict(lambda: defaultdict(int))
    viols = defaultdict(list)
    exs = defaultdict(dict)
    secs = 0.0
    for cfgd, st, v, ex, dt in res:
        key = (cfgd["K"], cfgd["G"])
        for k, x in st.items():
            agg[key][k] += x
        viols[key].extend(v)
        for k, x in ex.items():
            exs[key].setdefault(k, x)
        secs += dt
    print(f"c4_sim.py: {runs} runs per (K, G); worker time {secs:.0f} s")
    keys = sorted(agg)
    order = None
    tot_in = defaultdict(int)
    tot_neg = defaultdict(int)
    for key in keys:
        K, G = key
        st = agg[key]
        tag = "in B's range (G >= K - 1)" if G >= K - 1 else "NEGATIVE CONTROL (G < K - 1)"
        print(f"\nK = {K}, G = {G}  [{tag}; A's condition s + K <= G + 1 holds only for s <= {G + 1 - K}]")
        for k in sorted(st):
            print(f"  {k}: {st[k]}")
        for v in viols[key]:
            print(f"  VIOLATION EXAMPLE: {v}")
        for k, x in sorted(exs[key].items()):
            print(f"  example, {k}: {x}")
        tgt = tot_in if G >= K - 1 else tot_neg
        for k, x in st.items():
            tgt[k] += x
    for name, tot in (("all gaps K - 1 <= G <= 2K - 2", tot_in), ("negative controls G = K - 3, K - 2", tot_neg)):
        print(f"\nTOTAL, {name}:")
        for k in sorted(tot):
            print(f"  {k}: {tot[k]}")


if __name__ == "__main__":
    main()
