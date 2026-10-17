"""Mirrors of the integer automaton computations (`Cryptarchia/Prob/AutoZ.lean`,
`Cryptarchia/Prob/AutoFill.lean`).

A certificate states no tables: Lean computes each table's three entries at `(0, a, true)` (its
seeds) by Newton's method at elaboration time (`seedsZ`, `solveSeedsZ`), fills in the rest (`fillZ`,
`fillAllZ`) and the kernel checks the seeds (`seedOKZ`). This module gives the integer data (bands
over a common denominator, `x`, `θ`, `g` over theirs, tables at scale `SZ = 2^64`) and mirrors those
computations exactly, so the generator knows every check passes before it writes a file (`emitF`).
"""
import math
from fractions import Fraction as Fr
from cert2 import xg_exact

SZ = 2 ** 64
QKEYS = ['hhi', 'hlo', 'amax', 'hahi', 'alo', 'halo']


def lcm(xs):
    out = 1
    for x in xs: out = out * x // math.gcd(out, x)
    return out


def cdiv(n, m):
    """`cdivZ`: n / m rounded up (m > 0)."""
    return -((-n) // m)


def acap(n): return min(n, 2)


# ---- data

def fam_z(fam):
    """the members' `slot4` fields as integers over their common denominator"""
    D = lcm([Fr(m['B'][k]).denominator for m in fam for k in QKEYS])
    return D, [{k: int(Fr(m['B'][k]) * D) for k in QKEYS} for m in fam]


def ph_z(i, c, z, s, d, tau):
    """phase expectation `i`'s numbers: x = xn/xd, θ = θn/θd, g = gn/gd"""
    x, th, g = xg_exact(i, c, z, s, d, tau)
    x, th = Fr(x), Fr(th)
    gs = {(a, b, u): Fr(g(a, b, u)) for a in range(3) for b in (False, True) for u in (False, True)}
    gd = lcm([v.denominator for v in gs.values()])
    return dict(xn=x.numerator, xd=x.denominator, tn=th.numerator, td=th.denominator,
                gn={k: int(v * gd) for k, v in gs.items()}, gd=gd)


def M(X, D):
    return X['td'] * D * X['xd'] * X['gd']


# ---- the computations of AutoZ.lean

def slot4z(B, D, F):
    ff, ft, tf, tt = F(False, False), F(False, True), F(True, False), F(True, True)
    return (ff * D + (ft - ff) * (B['amax'] if ff <= ft else B['alo']) +
            (tf - ff) * (B['hhi'] if ff <= tf else B['hlo']) +
            (tt - tf - ft + ff) * (B['hahi'] if tf + ft <= tt + ff else B['halo']))


def stepz(B, D, Dl, X, S, w, q, a, u):
    def F(hh, aa):
        a2 = acap(a + (1 if aa else 0))
        if hh: nxt = w(0, a2, True) * X['gd']
        elif q + 1 == Dl: nxt = X['gn'][(a2, True, u)] * S
        else: nxt = w(q + 1, a2, u) * X['gd']
        return (X['xn'] if aa else X['xd']) * nxt
    return X['tn'] * slot4z(B, D, F)


def boundz(B, D, X, S, v):
    def F(hh, aa):
        a2 = acap(1 if aa else 0)
        nxt = v(0, a2, False) * X['gd'] if hh else X['gn'][(a2, False, False)] * S
        return (X['xn'] if aa else X['xd']) * nxt
    return X['tn'] * slot4z(B, D, F)


def fill(Bs, D, Dl, X, S, lo, top):
    """`fillAllZ`: the table as a dict (q, a, u) -> int"""
    m = M(X, D)
    v = {}
    for q in reversed(range(Dl)):
        w = lambda qq, aa, uu: top[aa] if qq == 0 else v[(qq, aa, uu)]
        for a in range(3):
            for u in (False, True):
                if q == 0 and u:
                    v[(q, a, u)] = top[a]; continue
                best = lo(q, a, u)
                for B in Bs:
                    s = cdiv(stepz(B, D, Dl, X, S, w, q, a, u), m)
                    if best <= s: best = s
                v[(q, a, u)] = best
    return v


def g_floor(X, S):
    return lambda q, a, u: cdiv(X['gn'][(a, True, u)] * S, X['gd'])


def check_sol(B, D, Dl, X, S, v):
    m = M(X, D); w = lambda q, a, u: v[(q, a, u)]
    return all(X['gn'][(a, True, u)] * S <= v[(q, a, u)] * X['gd'] and stepz(B, D, Dl, X, S, w, q, a, u) <= v[(q, a, u)] * m
               for q in range(Dl) for a in range(3) for u in (False, True))


def check_pre(B, D, Dl, X, S, vmax, v):
    m = M(X, D); w = lambda q, a, u: v[(q, a, u)]
    return all(vmax[(q, a, u)] <= v[(q, a, u)] and stepz(B, D, Dl, X, S, w, q, a, u) <= v[(q, a, u)] * m
               for q in range(Dl) for a in range(3) for u in (False, True))


def keys(Dl):
    return [(q, a, u) for q in range(Dl) for a in range(3) for u in (False, True)]


def seed_step(Bs, D, Dl, X, S, lo, t):
    """`seedStepZ`: the step at (0, a, true) for the table with seeds t, its maximum over
    the bands, rounded up, floored at lo"""
    v = fill(Bs, D, Dl, X, S, lo, t)
    w = lambda qq, aa, uu: t[aa] if qq == 0 else v[(qq, aa, uu)]
    m = M(X, D)
    out = []
    for a in range(3):
        best = lo(0, a, True)
        for B in Bs: best = max(best, cdiv(stepz(B, D, Dl, X, S, w, 0, a, True), m))
        out.append(best)
    return out


def det3(a, b, c, d, e, f, g, h, i):
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def newton(Bs, D, Dl, X, S, lo, h, t):
    """`newtonZ`"""
    F = lambda tt: seed_step(Bs, D, Dl, X, S, lo, tt)
    f = F(t)
    t0, t1, t2 = t
    g0, g1, g2 = F([t0 + h, t1, t2]), F([t0, t1 + h, t2]), F([t0, t1, t2 + h])
    d = lambda g, i: g[i] - f[i]
    r = lambda i: h * f[i] - (d(g0, i) * t0 + d(g1, i) * t1 + d(g2, i) * t2)
    A = [[h - d(g0, 0), -d(g1, 0), -d(g2, 0)], [-d(g0, 1), h - d(g1, 1), -d(g2, 1)], [-d(g0, 2), -d(g1, 2), h - d(g2, 2)]]
    m = det3(*A[0], *A[1], *A[2])
    if m <= 0: return list(t)
    R = [r(0), r(1), r(2)]
    col = lambda j: [[R[i] if jj == j else A[i][jj] for jj in range(3)] for i in range(3)]
    return [cdiv(det3(*col(j)[0], *col(j)[1], *col(j)[2]), m) for j in range(3)]


def solve_seeds(Bs, D, Dl, X, S, lo, h, pad, n, k, t):
    """`solveSeedsZ`"""
    N = lambda tt: [max(lo(0, a, True), v + pad) for a, v in enumerate(newton(Bs, D, Dl, X, S, lo, h, tt))]
    x = list(t)
    for _ in range(n): x = N(x)
    for _ in range(k):
        y = seed_step(Bs, D, Dl, X, S, lo, x)
        if all(a <= b for a, b in zip(y, x)): break
        x = [max(a, b) for a, b in zip(x, y)]
    return x


def seeds_chain(D, Dl, X, S, lo, h, pad, n, n1, k, famZ, t):
    """`seedsZ`"""
    out = []
    for j, B in enumerate(famZ):
        t = solve_seeds([B], D, Dl, X, S, lo, h, pad, n if j == 0 else n1, k, t)
        out.append(t)
    return out


def seed_ok(B, D, Dl, X, S, lo, v):
    """`seedOKZ`"""
    m = M(X, D); w = lambda q, a, u: v[(q, a, u)]
    return all(lo(0, a, True) <= v[(0, a, True)] and stepz(B, D, Dl, X, S, w, 0, a, True) <= v[(0, a, True)] * m
               for a in range(3))


H = 2 ** 32
