"""A table witness for the failed-check term, with the conditions that make it valid at every state.

`V(ρ, μ)` is tabulated on a box (`0 ≤ ρ ≤ R`; `μ` warm, i.e. `μ = ρ`, or cold with `-M ≤ μ ≤ -1`) and
extended geometrically: past `ρ = R` every value grows by `cw` per unit of reach (warm and cold
alike), and below `μ = -M` cold values shrink by `zc` per unit of margin. Each check is the Lean
bound on one phase (`proto.py`: the per-slot automaton with `slot4`, the `min(A, 2)` counter with
factor `x^A`, the crossing's pattern credit) against `λ · V(state)`.

The extension makes the infinitely many states outside the box follow from finitely many checks:

* past `ρ = R`, the phase step shifts the reach and keeps its distance from the box (a burst has
  honest depth at least 1, which the bound takes as exactly 1), and every value scales by `cw`, so
  the row `ρ = R + 1` stands for every larger reach;
* below `μ = -M`, a deeper cold state's outcomes are its representative's shifted down, which costs
  at least `zc` per unit when `V` grows by at least `zc` per unit of margin (`V(ρ, ν) ≥ zc V(ρ, ν - 1)`,
  and the warm value at least `zc` times the margin `-1` value), so the column `μ = -M - 1` stands
  for every deeper margin;
* more than `R + M + 2` adversarial slots in a phase always end warm past the box, where one more
  slot multiplies `V` by `cw ≤ x`, so the terminal table's `min(A, 2) = 2` entry is the largest of
  `V(next) / x^A` over `2 ≤ A ≤ R + M + 2`; a deeper state that catches up with more slots than its
  representative is covered by that entry when `x ≥ cw · zc` and warm values grow by at most `cw`
  per unit of reach.

The program also asks for `V` nondecreasing in reach and margin (so honest depth 1 in a burst only
raises `V`), the crossing's credit nonnegative, and `V ≥ 1` on warm states. Members of the band
family are checked at the in-epoch contraction `λ`, and the family's weakest band (which bounds a
phase that crosses an epoch boundary) at `λb`.

Usage: python3 witness.py BETA DELTA DEPTH [R] [M] [X] [CW] [ZC] [LAMBDA_B]
"""
import sys, os, time
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from fractions import Fraction as Fr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certgen"))
import certE  # noqa: E402

CAP = 2


class Table:
    """the box, its variables, and the check states (the box, the row `ρ = R + 1`, the column `μ = -M - 1`)"""

    def __init__(self, R, M, cw, zc):
        self.R, self.M, self.cw, self.zc = R, M, cw, zc
        self.cold = [(r, m) for r in range(R + 1) for m in range(-M, 0)]
        self.nc = len(self.cold)
        self.n = self.nc + R + 1   # variables: cold box entries, then warm (ρ, ρ), ρ ≤ R
        chk = list(self.cold) + [(r, r) for r in range(R + 1)]
        chk += [(R + 1, m) for m in range(-M, 0)] + [(R + 1, R + 1)]          # the row past the box
        chk += [(r, -M - 1) for r in range(R + 2)]                              # the column below it
        self.chk = np.array(chk)
        self.AX = R + M + 2   # as `TabQ.AX`

    def lookup(self, rho, mu):
        """`V(ρ, μ)` as (variable index, factor) for arrays of states with `μ ≤ ρ`"""
        R, M = self.R, self.M
        warm = mu >= 0
        fac = self.cw ** np.maximum(rho - R, 0).astype(float)
        fac = fac * np.where(~warm & (mu < -M), self.zc ** (mu + M).astype(float), 1.0)
        r = np.minimum(rho, R)
        m = np.maximum(mu, -M)
        idx = np.where(warm, self.nc + r, r * M + (m + M))
        return idx, fac


def step(rho, mu, A, H, X):
    rp = np.maximum(rho + A - H, A)
    mp = np.where(mu < -A, mu + A - H, (rho - H) if X else rp)
    return rp, np.minimum(mp, rp)


def combos(B):
    return [(1 - a1 - a2 + a3, a1 - a3, a2 - a3, a3)
            for a1 in (B['amax'], B['alo']) for a2 in (B['hhi'], B['hlo']) for a3 in (B['hahi'], B['halo'])]


def slot4(B, F00, F01, F10, F11):
    c1, c2, c3 = F01 - F00, F10 - F00, F11 - F10 - F01 + F00
    return (F00 + c1 * np.where(c1 >= 0, B['amax'], B['alo']) + c2 * np.where(c2 >= 0, B['hhi'], B['hlo'])
            + c3 * np.where(c3 >= 0, B['hahi'], B['halo']))


class Witness:
    def __init__(self, tab, D, x, zk=2.0):
        assert tab.cw * tab.zc <= x and tab.zc <= zk
        self.zk = zk
        self.t, self.D, self.x = tab, D, x
        rho, mu = tab.chk[:, 0], tab.chk[:, 1]
        self.m = len(tab.chk)
        self.self_ = tab.lookup(rho, mu)
        self.nxt = {}
        for A in range(tab.AX + 1):
            for H in (0, 1):
                self.nxt[(A, H, False)] = tab.lookup(*step(rho, mu, A, H, False))
        self.nxt[(0, 1, True)] = tab.lookup(*step(rho, mu, 0, 1, True))

    # ---- the operator, for checking a solution

    def apply(self, V, B):
        """the Lean bound on `E[V(next phase end)] / V(state)` at every check state"""
        D, x, AX = self.D, self.x, self.t.AX
        Vn = lambda key: V[self.nxt[key][0]] * self.nxt[key][1]
        g = np.zeros((3, 2, self.m))
        for b in (0, 1):
            g[0, b] = Vn((0, b, False))
            g[1, b] = Vn((1, b, False)) / x
            g[2, b] = np.max([Vn((A, b, False)) / x ** A for A in range(2, AX + 1)], axis=0)
        v = np.repeat(g[:, 1][None], D, axis=0)
        for _ in range(5000):
            vn = np.empty_like(v)
            for q in range(D):
                for a in range(3):
                    a1 = min(a + 1, 2)
                    nh0 = g[a, 1] if q + 1 == D else v[q + 1, a]
                    nh1 = g[a1, 1] if q + 1 == D else v[q + 1, a1]
                    vn[q, a] = np.maximum(g[a, 1], slot4(B, nh0, x * nh1, v[0, a], x * v[0, a1]))
            done = np.max(np.abs(vn - v) / np.maximum(v, 1e-300)) < 1e-14
            v = vn
            if done:
                break
        bound = slot4(B, g[0, 0], x * g[1, 0], v[0, 0], x * v[0, 1])
        bound = bound - B['slo'] * B['elo'] ** D * np.maximum(Vn((0, 1, False)) - Vn((0, 1, True)), 0)
        Vs = V[self.self_[0]] * self.self_[1]
        return bound / Vs

    # ---- the linear program

    def solve(self, members, weakest, lam, lamb, objective="warm", switch=False):
        A, lo, hi, cost, n = self.system(members, weakest, lam, lamb, switch)
        res = linprog(cost, A_ub=A, b_ub=np.zeros(A.shape[0]), bounds=list(zip(lo, hi)), method='highs')
        return (res.x[:n] if res.status == 0 else None)

    def solve_joint(self, groups, lam, lamb, gam):
        """one table per group of members, in one program, each passing its members' checks at `lam` and
        the boundary at `lamb`, with values within a factor `gam` of each other at every box entry"""
        blocks = [self.system(g, None, lam, lamb, True) for g in groups]
        n = blocks[0][4]
        offs = np.cumsum([0] + [b[0].shape[1] for b in blocks])
        A = sp.block_diag([b[0] for b in blocks], format='csr')
        rows, cols, vals = [], [], []
        r = 0
        for i in range(len(groups)):
            for j in range(len(groups)):
                if i != j:
                    for v in range(n):
                        rows += [r, r]; cols += [offs[i] + v, offs[j] + v]; vals += [1.0, -gam]; r += 1
        A = sp.vstack([A, sp.csr_matrix((vals, (rows, cols)), shape=(r, A.shape[1]))], format='csr')
        lo = np.concatenate([b[1] for b in blocks])
        hi = sum((list(b[2]) for b in blocks), [])
        cost = np.concatenate([b[3] for b in blocks])
        res = linprog(cost, A_ub=A, b_ub=np.zeros(A.shape[0]), bounds=list(zip(lo, hi)), method='highs')
        return ([res.x[o:o + n] for o in offs[:-1]] if res.status == 0 else None)

    def system(self, members, weakest, lam, lamb, switch=False):
        """a table passing every member's check at `lam`, and the boundary phases' at `lamb`: against the
        weakest band, or (`switch`) through the one-switch automaton over the members, as `AutoSolE`
        (each member's own table `vpost`, a table `vmax` above them, each member's `vpre` above `vmax`)"""
        t, D, x, m, n, AX = self.t, self.D, self.x, self.m, self.t.n, self.t.AX
        nm = len(members)
        bands = list(members) if switch else list(members) + [weakest]
        lams = [lam] * nm + ([] if switch else [lamb])
        nb = len(bands)
        tab = (CAP + 1) * D * m
        base_v = n
        base_max = n + nb * tab
        base_pre = base_max + (tab if switch else 0)
        base_g2 = base_pre + (nm * tab if switch else 0)
        nvar = base_g2 + 2 * m
        iv = lambda k, s, q, a: base_v + ((k * m + s) * D + q) * (CAP + 1) + a
        imx = lambda s, q, a: base_max + (s * D + q) * (CAP + 1) + a
        ipr = lambda k, s, q, a: base_pre + ((k * m + s) * D + q) * (CAP + 1) + a
        ig2 = lambda s, b: base_g2 + 2 * s + b
        R, C, Vv = [], [], []
        row = [0]

        def add(terms):
            for c, v in terms:
                R.append(row[0]); C.append(c); Vv.append(v)
            row[0] += 1

        def lin(key, s):
            idx, fac = self.nxt[key]
            return [(int(idx[s]), float(fac[s]))]

        def g(s, a, b):
            if a < CAP:
                return [(c, v / x ** a) for c, v in lin((a, b, False), s)]
            return [(ig2(s, b), 1.0)]

        # terminal entries for two or more adversarial slots
        for s in range(m):
            for b in (0, 1):
                for A in range(CAP, AX + 1):
                    add([(c, v / x ** A) for c, v in lin((A, b, False), s)] + [(ig2(s, b), -1.0)])
        # shape conditions on the box: monotone; margin growth at least zc; warm ≥ zc · (margin -1);
        # warm growth at most cw per unit of reach; cold values at least zk^(margin) (a check whose margin
        # catches up costs at most V · zk^A, `FailPot.fail`)
        Rb, Mb, nc = t.R, t.M, t.nc
        ci = lambda r, mm: r * Mb + (mm + Mb)
        for r in range(Rb):
            add([(nc + r + 1, 1.0), (nc + r, -t.cw)])
        for r in range(Rb + 1):
            for mm in range(-Mb, 0):
                if r < Rb:
                    add([(ci(r, mm), 1.0), (ci(r + 1, mm), -1.0)])
                if mm > -Mb:
                    add([(ci(r, mm - 1), t.zc), (ci(r, mm), -1.0)])
            add([(ci(r, -1), t.zc), (nc + r, -1.0)])
            if r < Rb:
                add([(nc + r, 1.0), (nc + r + 1, -1.0)])
        # the crossing's credit is nonnegative
        for s in range(m):
            add(lin((0, 1, True), s) + [(c, -v) for c, v in lin((0, 1, False), s)])

        def recursion(B, tv, s, q, a):
            """rows: table `tv` ≥ one step of band `B`'s recursion at (s, q, a)"""
            a1 = min(a + 1, CAP)
            F00 = g(s, a, 1) if q + 1 == D else [(tv(s, q + 1, a), 1.0)]
            F01 = [(c, x * v) for c, v in (g(s, a1, 1) if q + 1 == D else [(tv(s, q + 1, a1), 1.0)])]
            F10, F11 = [(tv(s, 0, a), 1.0)], [(tv(s, 0, a1), x)]
            for w in combos(B):
                add([(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] +
                    [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11] + [(tv(s, q, a), -1.0)])

        def phase(B, tv, s, lk, pat):
            """rows: band `B`'s phase bound with table `tv`, less the crossing's credit, at most `lk · V(s)`"""
            F00 = g(s, 0, 0)
            F01 = [(c, x * v) for c, v in g(s, 1, 0)]
            F10, F11 = [(tv(s, 0, 0), 1.0)], [(tv(s, 0, 1), x)]
            cr = [(c, -pat * v) for c, v in lin((0, 1, False), s)] + [(c, pat * v) for c, v in lin((0, 1, True), s)]
            si, sf = int(self.self_[0][s]), float(self.self_[1][s])
            for w in combos(B):
                add([(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] +
                    [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11] + cr + [(si, -lk * sf)])

        # each band's own table, its recursion, and its phase bound
        for k, (B, lk) in enumerate(zip(bands, lams)):
            tv = lambda s, q, a, k=k: iv(k, s, q, a)
            for s in range(m):
                for q in range(D):
                    for a in range(CAP + 1):
                        add(g(s, a, 1) + [(tv(s, q, a), -1.0)])
                        recursion(B, tv, s, q, a)
                phase(B, tv, s, lk, B['slo'] * B['elo'] ** D)
        if switch:
            # the one-switch automaton: vmax above every member's own table, each member's vpre above
            # vmax and its own recursion; the boundary phase's bound with vpre, against the family's
            # crossing bound
            pat_w = min(B['slo'] * B['elo'] ** D for B in members)
            for s in range(m):
                for q in range(D):
                    for a in range(CAP + 1):
                        for k in range(nm):
                            add([(iv(k, s, q, a), 1.0), (imx(s, q, a), -1.0)])
                            add([(imx(s, q, a), 1.0), (ipr(k, s, q, a), -1.0)])
            for k, B in enumerate(members):
                tv = lambda s, q, a, k=k: ipr(k, s, q, a)
                for s in range(m):
                    for q in range(D):
                        for a in range(CAP + 1):
                            recursion(B, tv, s, q, a)
                    phase(B, tv, s, lamb, pat_w)
        A = sp.csr_matrix((Vv, (R, C)), shape=(row[0], nvar))
        lo = np.zeros(nvar)
        lo[nc:n] = 1.0
        hi = [None] * nvar
        hi[nc] = 1.0   # V(0, 0) = 1, so warm values stay below c_r^ρ
        for r in range(Rb + 1):
            for mm in range(-Mb, 0):
                lo[ci(r, mm)] = self.zk ** mm
        cost = np.zeros(nvar)
        cost[nc:n] = 1.0 / (t.cw ** np.arange(Rb + 1))
        return A, lo, hi, cost, n

    def best(self, fam_bands, weakest, lamb, lo=0.9960, hi=0.9985, tol=1e-5, start=(0,), log=print, switch=False):
        """the least in-epoch `λ` by bisection, with constraint generation over the members"""
        active = list(start)
        V = None
        while True:
            l, h = lo, hi
            Vb = None
            while h - l > tol:
                mid = (l + h) / 2
                t0 = time.time()
                Vm = self.solve([fam_bands[i] for i in active], weakest, mid, lamb, switch=switch)
                log(f"  members {active}, λ = {mid:.6f}: {'feasible' if Vm is not None else 'infeasible'} ({time.time() - t0:.0f}s)")
                if Vm is not None:
                    h, Vb = mid, Vm
                else:
                    l = mid
            if Vb is None:
                return None, None, active
            rat = np.array([np.max(self.apply(Vb, B)) for B in fam_bands])
            worst = int(np.argmax(rat))
            wk = f"; weakest {np.max(self.apply(Vb, weakest)):.6f}" if weakest is not None else ""
            log(f"members {active}: λ = {h:.6f}; all members max {rat[worst]:.6f} at {worst}{wk}")
            if rat[worst] <= h + 2 * tol or worst in active:
                return h, Vb, active
            active.append(worst)
            lo = h


def fband(B):
    return {k: float(v) for k, v in B.items()}


def weakest_band(fam):
    keys_min = ['hlo', 'alo', 'halo', 'slo', 'hnlo', 'elo']
    keys_max = ['hhi', 'amax', 'hahi']
    out = {}
    for k in keys_min:
        out[k] = min(m[k] for m in fam)
    for k in keys_max:
        out[k] = max(m[k] for m in fam)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    beta, delta, k = float(a[0]), float(a[1]), int(a[2])
    R = int(a[3]) if len(a) > 3 else 12
    M = int(a[4]) if len(a) > 4 else 24
    x = float(a[5]) if len(a) > 5 else 2.6
    cw = float(a[6]) if len(a) > 6 else 1.9
    zc = float(a[7]) if len(a) > 7 else 1.9
    lamb = float(a[8]) if len(a) > 8 else 0.9985
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(13, 100))
    fam = [fband(m['B']) for m in certE.epoch_members(T, 32)]
    W = Witness(Table(R, M, cw, zc), 11, x)
    lam, V, act = W.best(fam, weakest_band(fam), lamb, log=lambda s: print(s, flush=True) if not s.startswith("  ") else None)
    print(f"λ = {lam}, weakest band at λb = {lamb}, binding members {act}")
    if V is not None and os.environ.get("WITNESS_OUT"):
        np.save(os.environ["WITNESS_OUT"], V)
