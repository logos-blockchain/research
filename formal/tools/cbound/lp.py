"""The best table witness for the failed-check term, as a linear program.

For a fixed `λ`, the Lean check of `proto.py` is linear in the unknowns: the table `V` on the box,
each box state's automaton table `v[q, a]`, and its terminal entries `g2[b]` for two or more
adversarial slots. Each `slot4` bound is the largest of 8 linear forms (one per choice of `amax`
or `alo`, `hhi` or `hlo`, `hahi` or `halo`), so `v ≥ slot4(...)` and `autoBound ≤ ...` are 8
linear constraints each. The program also asks for what the pessimizations use:

* `V` nondecreasing in the reach and in the margin (so `H = B` in a burst only raises `V`);
* the crossing's credit nonnegative (`V` without the crossing at least `V` with it);
* `V ≥ 1` on warm states (a warm margin is a failed check).

`λ` is found by bisection; every feasible point is a witness that passes the checks exactly as
written. Several members are checked against one `V` by stacking their constraints.

Usage: python3 lp.py BETA DELTA DEPTH [R] [M] [MEMBERS: all|worst]
"""
import sys, os, time
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proto  # noqa: E402

AX = proto.AX
CAP = 2  # the automaton tracks min(A, CAP) (`acap` in `Prob/Auto.lean` has CAP = 2)


def combos(B):
    """the 8 coefficient vectors of `slot4` on `(F00, F01, F10, F11)`"""
    out = []
    for A1 in (B['amax'], B['alo']):
        for A2 in (B['hhi'], B['hlo']):
            for A3 in (B['hahi'], B['halo']):
                out.append((1 - A1 - A2 + A3, A1 - A3, A2 - A3, A3))
    return out


class Program:
    def __init__(self, box, D, x):
        self.box, self.D, self.x = box, D, x
        self.op = proto.Operator(box, D, x)
        n = box.n
        self.n = n
        # variables: V[0:n], v[n + (s * D + q) * 3 + a], g2[n + 3 D n + 2 s + b]
        self.nv = n + (CAP + 1) * D * n + 2 * n

    def iv(self, s, q, a):
        return self.n + (s * self.D + q) * (CAP + 1) + a

    def ig2(self, s, b):
        return self.n + (CAP + 1) * self.D * self.n + 2 * s + b

    def lin_V(self, key):
        """the linear form V(next state for `key`) at every box state: (column, coefficient)"""
        idx, fac = self.op.nxt[key]
        return idx, fac

    def g_terms(self, s, a, b):
        """terminal entry g(a, b) at state `s` as a list of (column, coefficient)"""
        x = self.x
        if a < CAP:
            idx, fac = self.lin_V((a, b, False))
            return [(int(idx[s]), fac[s] / x ** a)]
        return [(self.ig2(s, b), 1.0)]

    def build(self, bands, lam):
        """inequality rows `A_ub · z ≤ 0` (and the normalization) for every band in `bands`"""
        box, D, x, n = self.box, self.D, self.x, self.n
        rows, cols, vals = [], [], []
        r = [0]

        def add(terms):
            for c, v in terms:
                rows.append(r[0]); cols.append(c); vals.append(v)
            r[0] += 1

        # g2[b] ≥ V(next(A, b)) / x^A for A ≥ 2 (shared by all bands)
        for b in (0, 1):
            for A in range(CAP, AX + 1):
                idx, fac = self.lin_V((A, b, False))
                for s in range(n):
                    add([(int(idx[s]), fac[s] / x ** A), (self.ig2(s, b), -1.0)])
        # monotonicity: V(ρ, μ) ≤ V(ρ + 1, μ), V(ρ, μ) ≤ V(ρ, μ + 1), cold ≤ warm
        R, M, nc = box.R, box.M, box.nc
        ci = lambda rr, m: rr * M + (m + M)
        for rr in range(R + 1):
            for m in range(-M, 0):
                if rr < R:
                    add([(ci(rr, m), 1.0), (ci(rr + 1, m), -1.0)])
                if m < -1:
                    add([(ci(rr, m), 1.0), (ci(rr, m + 1), -1.0)])
                else:
                    add([(ci(rr, m), 1.0), (nc + rr, -1.0)])
            if rr < R:
                add([(nc + rr, 1.0), (nc + rr + 1, -1.0)])
        # the crossing's credit is nonnegative
        i0, f0 = self.lin_V((0, 1, False))
        i1, f1 = self.lin_V((0, 1, True))
        for s in range(n):
            add([(int(i1[s]), f1[s]), (int(i0[s]), -f0[s])])
        nshared = r[0]
        for B in bands:
            # automaton tables are per band: offset their columns
            k = bands.index(B)
            off = k * ((CAP + 1) * D * n)
            iv = lambda s, q, a: self.iv(s, q, a) + off
            cmb = combos(B)
            pat = B['slo'] * B['elo'] ** D
            for s in range(n):
                for q in range(D):
                    for a in range(CAP + 1):
                        a1 = min(a + 1, CAP)
                        # v ≥ g(a, true)
                        add([(c, v) for c, v in self.g_terms(s, a, 1)] + [(iv(s, q, a), -1.0)])
                        # v ≥ slot4(F00, F01, F10, F11)
                        F00 = self.g_terms(s, a, 1) if q + 1 == D else [(iv(s, q + 1, a), 1.0)]
                        F01 = [(c, x * v) for c, v in (self.g_terms(s, a1, 1) if q + 1 == D else [(iv(s, q + 1, a1), 1.0)])]
                        F10 = [(iv(s, 0, a), 1.0)]
                        F11 = [(iv(s, 0, a1), x)]
                        for w in cmb:
                            t = [(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] + \
                                [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11]
                            add(t + [(iv(s, q, a), -1.0)])
                # the phase: autoBound - pat · (V(no crossing) - V(crossing)) ≤ λ V(s)
                F00 = self.g_terms(s, 0, 0)
                F01 = [(c, x * v) for c, v in self.g_terms(s, 1, 0)]
                F10 = [(iv(s, 0, 0), 1.0)]
                F11 = [(iv(s, 0, 1), x)]
                cr = [(int(i0[s]), -pat * f0[s]), (int(i1[s]), pat * f1[s])]
                for w in cmb:
                    t = [(c, w[0] * v) for c, v in F00] + [(c, w[1] * v) for c, v in F01] + \
                        [(c, w[2] * v) for c, v in F10] + [(c, w[3] * v) for c, v in F11]
                    add(t + cr + [(s, -lam)])
        nvar = n + len(bands) * (CAP + 1) * D * n + 2 * n
        # g2 columns sit after all bands' automaton tables
        shift = (len(bands) - 1) * (CAP + 1) * D * n
        cols = [c + shift if c >= n + (CAP + 1) * D * n else c for c in cols]
        A = sp.csr_matrix((vals, (rows, cols)), shape=(r[0], nvar))
        return A, nvar

    def feasible(self, bands, lam):
        A, nvar = self.build(bands, lam)
        n, nc = self.n, self.box.nc
        b = np.zeros(A.shape[0])
        # V ≥ 1 on warm states; everything nonnegative; minimize V on warm states over ce^ρ
        lo = np.zeros(nvar)
        lo[nc:n] = 1.0
        cost = np.zeros(nvar)
        cost[nc:n] = 1.0 / (1.9 ** np.arange(self.box.R + 1))
        res = linprog(cost, A_ub=A, b_ub=b, bounds=list(zip(lo, [None] * nvar)), method='highs')
        return res.status == 0, (res.x[:n] if res.status == 0 else None)


def best_lambda(prog, bands, lo=0.990, hi=0.9985, tol=2e-6):
    best = None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        t = time.time()
        ok, V = prog.feasible(bands, mid)
        print(f"  λ = {mid:.6f}: {'feasible' if ok else 'infeasible'} ({time.time() - t:.0f}s)", flush=True)
        if ok:
            hi, best = mid, V
        else:
            lo = mid
    return hi, best


if __name__ == "__main__":
    import certE
    beta, delta, k = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    R = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    M = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    which = sys.argv[6] if len(sys.argv) > 6 else 'worst'
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(13, 100))
    fam = certE.epoch_members(T, 32)
    # tails: warm reach grows by 1.9 per unit, cold margin shrinks by 1.9 per unit (the best tail
    # contractions); the automaton's factor per adversarial slot x = 2.6, which with its min(A, 2)
    # counter comes within 5e-5 of the true rate (x = 1.9 loses 5e-4)
    box = proto.Box(R, M, 1.9, 1.0, 1.9)
    prog = Program(box, 11, 2.6)
    bands = [proto.fband(m['B']) for m in fam] if which == 'all' else [proto.fband(fam[0]['B'])]
    lam, V = best_lambda(prog, bands)
    print(f"best λ = {lam:.6f}  (box R = {R}, M = {M}, {len(bands)} band(s))")
    if V is not None:
        np.save(os.environ.get("WITNESS_OUT", f"V_R{R}_M{M}.npy"), V)
        lams = [np.max(prog.op.apply(V, proto.fband(m['B'])) / V) for m in fam]
        print("checked with the operator, all members: max λ =", f"{max(lams):.6f}", "at member", int(np.argmax(lams)))
