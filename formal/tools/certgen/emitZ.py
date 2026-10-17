"""Integer tables for the multi-epoch certificates (`Cryptarchia/Prob/AutoZ.lean`,
`Cryptarchia/Prob/AutoFill.lean`).

A certificate states no tables: the kernel computes each table's three entries at
`(0, a, true)` (its seeds) by Newton's method (`seedsZ`, `solveSeedsZ`), fills in the rest
(`fillZ`, `fillAllZ`) and checks the seeds (`seedOKZ`). This module gives the integer data
(bands over a common denominator, `x`, `θ`, `g` over theirs, tables at scale `SZ = 2^64`) and
mirrors those computations exactly, so the generator knows every check passes before it
writes a file.
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


def check_bound(B, D, X, S, v, e):
    return Fr(boundz(B, D, X, S, lambda q, a, u: v[(q, a, u)])) <= Fr(e) * M(X, D) * S


def keys(Dl):
    return [(q, a, u) for q in range(Dl) for a in range(3) for u in (False, True)]


def tops(V):
    """a table's seeds: its entries at (0, a, true), rounded up to the scale"""
    return [cdiv(Fr(V[(0, a, True)]).numerator * SZ, Fr(V[(0, a, True)]).denominator) for a in range(3)]


def up_table(V, Dl):
    return {key: cdiv(Fr(V[key]).numerator * SZ, Fr(V[key]).denominator) for key in keys(Dl)}


# ---- the seed computations of AutoFill.lean

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


def ein_list(famZ, D, Dl, X, S, d, seeds):
    """`eInListQ`: each member's post-switch bound, rounded up to d significant digits"""
    from certnum import rup
    out = []
    for B, t in zip(famZ, seeds):
        po = fill([B], D, Dl, X, S, g_floor(X, S), t)
        out.append(rup(Fr(boundz(B, D, X, S, lambda q, a, u: po[(q, a, u)]), M(X, D) * S), d))
    return out


def seed_ok(B, D, Dl, X, S, lo, v):
    """`seedOKZ`"""
    m = M(X, D); w = lambda q, a, u: v[(q, a, u)]
    return all(lo(0, a, True) <= v[(0, a, True)] and stepz(B, D, Dl, X, S, w, 0, a, True) <= v[(0, a, True)] * m
               for a in range(3))


# the solver's settings, tried in turn: Newton steps for the first member and for each later
# one, the pad, and the steps of the recursion allowed after them. The solver runs at
# elaboration time (`eval%`), so these cost the kernel nothing.
SOLVE = [(3, 2, 2 ** 8, 200), (4, 3, 2 ** 16, 400)]
H = 2 ** 32


# ---- one index

def index_z(i, fam, Dl, P, args, sbound=None):
    """the integer data of index i: the solver settings under which the kernel's tables pass
    every check and lie below the planned ones (so the planned bounds hold); raises if none"""
    D, famZ = fam_z(fam)
    X = ph_z(i, *args)
    S = SZ
    lo = g_floor(X, S)
    floor = [lo(0, a, True) for a in range(3)]
    out = dict(X=X)
    if 'vs' in P and i in P['vs']:
        cap = tops(P['vs'][i])
        for n, _, pad, kk in SOLVE:
            top = solve_seeds(famZ, D, Dl, X, S, lo, H, pad, n, kk, floor)
            vs = fill(famZ, D, Dl, X, S, lo, top)
            if all(
                    seed_ok(B, D, Dl, X, S, lo, vs) and check_sol(B, D, Dl, X, S, vs) and
                    check_bound(B, D, X, S, vs, sbound) for B in famZ):
                break
        else:
            raise AssertionError(('switch', i))
        out['vs'] = dict(n=n, pad=pad, k=kk)
    if 'post' in P and i in P['post']:
        caps = [tops(V) for V in P['post'][i]]
        for n, n1, pad, kk in SOLVE:
            sd = seeds_chain(D, Dl, X, S, lo, H, pad, n, n1, kk, famZ, floor)
            posts = [fill([B], D, Dl, X, S, lo, t) for B, t in zip(famZ, sd)]
            vmax = {key: max([0] + [p[key] for p in posts]) for key in keys(Dl)}
            vlo = lambda q, a, u: vmax[(q, a, u)]
            # the pre-switch seeds: vmax's own, or after Newton steps
            for npre in (0, 1, 2):
                pts = [solve_seeds([B], D, Dl, X, S, vlo, H, pad, npre, kk, [vmax[(0, a, True)] for a in range(3)]) for B in famZ]
                pres = [fill([B], D, Dl, X, S, vlo, t) for B, t in zip(famZ, pts)]
                if all(seed_ok(B, D, Dl, X, S, vlo, pr) and check_pre(B, D, Dl, X, S, vmax, pr) and
                       check_bound(B, D, X, S, pr, P['e'][i]) for B, pr in zip(famZ, pres)):
                    break
            else:
                continue
            # the in-epoch bounds the kernel computes, below the planned ones (so the class
            # conditions planned with them hold)
            ein = ein_list(famZ, D, Dl, X, S, 13, sd)
            if all(seed_ok(B, D, Dl, X, S, lo, po) and check_sol(B, D, Dl, X, S, po) and
                   check_bound(B, D, X, S, po, ein[k]) and ein[k] <= P['eIn'][i][k]
                   for k, (B, po) in enumerate(zip(famZ, posts))):
                break
        else:
            raise AssertionError(('one-switch', i))
        out['post'] = dict(n=n, n1=n1, pad=pad, npre=npre, k=kk)
        out['eIn'] = ein
    return out


# ---- Lean text

def zl(n): return f"({n} : ℤ)" if n < 0 else str(n)


def fam_z_lean(fam):
    """`famQ`, `famA`, `DZ`, `famZ`, `famR` for Fam.lean"""
    D, famZ = fam_z(fam)
    K = len(fam)
    def fm(name, typ, items):
        return f"def {name} : {typ} := fun k =>\n  match k.val with\n" + "".join(
            f"  | {j} => {it}\n" if j < K - 1 else f"  | _ => {it}\n" for j, it in enumerate(items))
    s = "/-- The members' `slot4` fields over `ℚ`. -/\n" + fm("famQ", f"Fin {K} → BandQ", [f"f{k}Q" for k in range(K)])
    s += f"\ntheorem famA : ∀ k, (famQ k).Agrees (fam k) := fun k => by\n  fin_cases k; exacts [{', '.join(f'f{k}A' for k in range(K))}]\n"
    s += f"\n/-- The members' `slot4` fields' common denominator. -/\ndef DZ : ℤ := {D}\n\ntheorem DZ_pos : 0 < DZ := by decide\n"
    s += "\n/-- The members' `slot4` fields over the integers, times `DZ`. -/\n" + fm(
        "famZ", f"Fin {K} → BandZ", ["⟨" + ", ".join(zl(B[kk]) for kk in QKEYS) + "⟩" for B in famZ])
    s += "\ntheorem famR : ∀ k, (famZ k).Rep DZ (famQ k) := by decide +kernel\n"
    return s


def index_lean(i, K, Dl, xgs, argsQ, data, P, qR, qQ, sbound=None):
    """the body of I<i>.lean: `xgs` the real `x θ g` text, `argsQ` the rational parameters of `xgNQ`"""
    L = [f"""/-- Phase expectation {i} over the integers. -/
def X{i} : PhZ := PhZ.ofQ (xgNQ {argsQ} {i})

theorem X{i}R : X{i}.Rep (xgNQ {argsQ} {i}).1 (xgNQ {argsQ} {i}).2.1 (xgNQ {argsQ} {i}).2.2 := by decide +kernel
"""]
    fl = f"gFloorZ X{i} SZ"
    floor = f"[{fl} 0 0 true, {fl} 0 1 true, {fl} 0 2 true]"
    def qm(name, vals):
        return f"def {name} : Fin {K} → ℚ := fun k =>\n  match k.val with\n" + "".join(
            (f"  | {j} => " if j < K - 1 else "  | _ => ") + qQ(v) + "\n" for j, v in enumerate(vals))
    if 'vs' in data:
        n, pad, kk = data['vs']['n'], data['vs']['pad'], data['vs']['k']
        tab = f"fillAllZ ((List.finRange {K}).map famZ) DZ {Dl} X{i} SZ ({fl}) vsTop{i}"
        L.append(f"""/-- The switching table's seeds, by Newton's method at elaboration time. -/
def vsTop{i} : Fin 3 → ℤ :=
  seedL (eval% solveSeedsZ ((List.finRange {K}).map famZ) DZ {Dl} X{i} SZ ({fl}) (2 ^ {H.bit_length() - 1}) (2 ^ {pad.bit_length() - 1}) {n} {kk} {floor})

theorem chkS{i} : (List.finRange {K}).all (chkSwF famZ DZ {Dl} X{i} SZ vsTop{i} fun _ => {qQ(sbound)}) = true := by
  decide +kernel

noncomputable def vs{i} : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ ({tab}))

theorem solS{i} : ∀ k, AutoSol (fam k) {Dl} {xgs} vs{i} := by
  rw [xgQ{i}]; exact (switchF_sound famR famA DZ_pos X{i}R SZ_pos chkS{i}).1

theorem heS{i} : ∀ k, autoBound (fam k) {xgs} vs{i} ≤ {qR(sbound)} := by
  rw [xgQ{i}]
  exact fun k => ((switchF_sound famR famA DZ_pos X{i}R SZ_pos chkS{i}).2 k).trans_eq (by push_cast; ring)
""")
    if 'post' in data:
        n, n1, pad, npre, kk = (data['post'][v] for v in ('n', 'n1', 'pad', 'npre', 'k'))
        vm = f"vmaxF famZ DZ {Dl} X{i} SZ postTop{i}"
        H_, P_ = f"(2 ^ {H.bit_length() - 1})", f"(2 ^ {pad.bit_length() - 1})"
        L.append(f"""/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd{i} : List (List ℤ) :=
  eval% seedsZ DZ {Dl} X{i} SZ ({fl}) {H_} {P_} {n} {n1} {kk} ((List.finRange {K}).map famZ) {floor}

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd{i} : List (List ℤ) := eval% preSeedsZ ((List.finRange {K}).map famZ) DZ {Dl} X{i} SZ {H_} {P_} {npre} {kk} sd{i}

def postTop{i} (k : Fin {K}) : Fin 3 → ℤ := seedL (sd{i}.getD k.val [])
def preTop{i} (k : Fin {K}) : Fin 3 → ℤ := seedL (psd{i}.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL{i} : List ℚ := eval% eInListQ ((List.finRange {K}).map famZ) DZ {Dl} X{i} SZ 13 sd{i}

def eIn{i} (k : Fin {K}) : ℚ := eInL{i}.getD k.val 0

theorem chkE{i} : (List.finRange {K}).all (chkOneF famZ DZ {Dl} X{i} SZ postTop{i} preTop{i} eIn{i} {qQ(P['e'][i])}) = true := by
  decide +kernel

noncomputable def vmax{i} : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ ({vm}))
noncomputable def vpreI{i} : Fin {K} → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ {Dl} X{i} SZ postTop{i} preTop{i} k))
noncomputable def vpostI{i} : Fin {K} → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ {Dl} X{i} SZ postTop{i} k))

theorem solE{i} : AutoSolE fam {Dl} {xgs} vpreI{i} vpostI{i} vmax{i} := by
  rw [xgQ{i}]; exact (oneSwitchF_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).1

theorem heEall{i} : ∀ k, autoBound (fam k) {xgs} (vpreI{i} k) ≤ {qR(P['e'][i])} := by
  rw [xgQ{i}]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).2.2 k).trans_eq (by push_cast; ring)

theorem heIn{i} : ∀ k, autoBound (fam k) {xgs} (vpostI{i} k) ≤ (eIn{i} k : ℝ) := by
  rw [xgQ{i}]; exact (oneSwitchF_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).2.1
""")
    return "\n".join(L)
