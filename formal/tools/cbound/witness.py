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
* more than `R + M + 1` adversarial slots in a phase always end warm past the box, where one more
  slot multiplies `V` by `cw ≤ x`, so the terminal table's `min(A, 2) = 2` entry is the largest of
  `V(next) / x^A` over `2 ≤ A ≤ R + M + 1`.

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
        self.AX = R + M + 1

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
    def __init__(self, tab, D, x):
        assert tab.cw <= x
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

    def solve(self, members, weakest, lam, lamb, objective="warm"):
        """a table passing every member's check at `lam` and the weakest band's at `lamb`"""
        t, D, x, m, n, AX = self.t, self.D, self.x, self.m, self.t.n, self.t.AX
        bands = list(members) + [weakest]
        lams = [lam] * len(members) + [lamb]
        nb = len(bands)
        base_v = n
        base_g2 = n + nb * (CAP + 1) * D * m
        nvar = base_g2 + 2 * m
        iv = lambda k, s, q, a: base_v + ((k * m + s) * D + q) * (CAP + 1) + a
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
        # shape conditions on the box: monotone; margin growth at least zc; warm ≥ zc · (margin -1)
        Rb, Mb, nc = t.R, t.M, t.nc
        ci = lambda r, mm: r * Mb + (mm + Mb)
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
        # each band's automaton and phase bound
        for k, (B, lk) in enumerate(zip(bands, lams)):
            cm = combos(B)
            pat = B['slo'] * B['elo'] ** D
            for s in range(m):
                for q in range(D):
                    for a in range(CAP + 1):
                        a1 = min(a + 1, CAP)
                        add(g(s, a, 1) + [(iv(k, s, q, a), -1.0)])
                        F00 = g(s, a, 1) if q + 1 == D else [(iv(k, s, q + 1, a), 1.0)]
                        F01 = [(c, x * v) for c, v in (g(s, a1, 1) if q + 1 == D else [(iv(k, s, q + 1, a1), 1.0)])]
                        F10, F11 = [(iv(k, s, 0, a), 1.0)], [(iv(k, s, 0, a1), x)]
                        for w in cm:
                            add([(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] +
                                [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11] +
                                [(iv(k, s, q, a), -1.0)])
                F00 = g(s, 0, 0)
                F01 = [(c, x * v) for c, v in g(s, 1, 0)]
                F10, F11 = [(iv(k, s, 0, 0), 1.0)], [(iv(k, s, 0, 1), x)]
                cr = [(c, -pat * v) for c, v in lin((0, 1, False), s)] + [(c, pat * v) for c, v in lin((0, 1, True), s)]
                si, sf = int(self.self_[0][s]), float(self.self_[1][s])
                for w in cm:
                    add([(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] +
                        [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11] + cr + [(si, -lk * sf)])
        A = sp.csr_matrix((Vv, (R, C)), shape=(row[0], nvar))
        lo = np.zeros(nvar)
        lo[nc:n] = 1.0
        cost = np.zeros(nvar)
        cost[nc:n] = 1.0 / (t.cw ** np.arange(Rb + 1))
        res = linprog(cost, A_ub=A, b_ub=np.zeros(row[0]), bounds=list(zip(lo, [None] * nvar)), method='highs')
        return (res.x[:n] if res.status == 0 else None)

    def best(self, fam_bands, weakest, lamb, lo=0.9960, hi=0.9985, tol=1e-5, start=(0,), log=print):
        """the least in-epoch `λ` by bisection, with constraint generation over the members"""
        active = list(start)
        V = None
        while True:
            l, h = lo, hi
            Vb = None
            while h - l > tol:
                mid = (l + h) / 2
                t0 = time.time()
                Vm = self.solve([fam_bands[i] for i in active], weakest, mid, lamb)
                log(f"  members {active}, λ = {mid:.6f}: {'feasible' if Vm is not None else 'infeasible'} ({time.time() - t0:.0f}s)")
                if Vm is not None:
                    h, Vb = mid, Vm
                else:
                    l = mid
            if Vb is None:
                return None, None, active
            rat = np.array([np.max(self.apply(Vb, B)) for B in fam_bands])
            worst = int(np.argmax(rat))
            log(f"members {active}: λ = {h:.6f}; all members max {rat[worst]:.6f} at {worst}; weakest {np.max(self.apply(Vb, weakest)):.6f}")
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
