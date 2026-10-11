"""Integer tables for the multi-epoch certificates (`Cryptarchia/Prob/AutoZ.lean`).

A certificate states each automaton table by its three entries at `(0, a, true)`; Lean
computes the rest (`fillZ`, `fillAllZ`) and checks it in integer arithmetic. This module
gives the integer data (bands over a common denominator, `x`, `θ`, `g` over theirs, tables
at scale `SZ = 2^64`) and mirrors `AutoZ.lean`'s computations exactly, so the generator
knows every check passes before it writes a file.
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


# ---- one index

def index_z(i, fam, Dl, P, args):
    """the integer data of index i, every check run; raises if one fails"""
    D, famZ = fam_z(fam)
    X = ph_z(i, *args)
    S = SZ
    out = dict(X=X)
    if 'vs' in P and i in P['vs']:
        top = tops(P['vs'][i])
        vs = fill(famZ, D, Dl, X, S, lambda q, a, u: 0, top)
        for k, B in enumerate(famZ):
            assert check_sol(B, D, Dl, X, S, vs), ('switch', i, k)
            assert check_bound(B, D, X, S, vs, P['eS'][i][k]), ('switch bound', i, k)
        out['vsTop'] = top
    if 'post' in P and i in P['post']:
        vmax = up_table(P['vmax'][i], Dl)
        posts, pres = [], []
        for k, B in enumerate(famZ):
            pt = tops(P['post'][i][k]); pr = tops(P['pre'][i][k])
            post = fill([B], D, Dl, X, S, g_floor(X, S), pt)
            pre = fill([B], D, Dl, X, S, lambda q, a, u: vmax[(q, a, u)], pr)
            assert check_sol(B, D, Dl, X, S, post), ('post', i, k)
            assert all(post[key] <= vmax[key] for key in keys(Dl)), ('vmax', i, k)
            assert check_pre(B, D, Dl, X, S, vmax, pre), ('pre', i, k)
            assert check_bound(B, D, X, S, post, P['eIn'][i][k]), ('in bound', i, k)
            assert check_bound(B, D, X, S, pre, P['e'][i]), ('pre bound', i, k)
            posts.append(pt); pres.append(pr)
        out.update(vmax=[vmax[key] for key in keys(Dl)], postTop=posts, preTop=pres)
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


def index_lean(i, K, Dl, xgs, xgsQ, data, P, qR, qQ):
    """the body of I<i>.lean: `xgs` the real `x θ g` text, `xgsQ` the rational triple's text"""
    X = data['X']
    gl = [X['gn'][(a, b, u)] for a in range(3) for b in (False, True) for u in (False, True)]
    L = [f"""/-- Phase expectation {i} over the integers. -/
def X{i} : PhZ := ⟨{zl(X['xn'])}, {X['xd']}, {zl(X['tn'])}, {X['td']},
  fun a b u => [{', '.join(zl(v) for v in gl)}].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  {X['gd']}⟩

theorem X{i}R : X{i}.Rep {xgsQ} := by decide +kernel
"""]
    def tm(name, rows):
        return f"def {name} : Fin {K} → Fin 3 → ℤ := fun k =>\n  match k.val with\n" + "".join(
            (f"  | {j} => " if j < K - 1 else "  | _ => ") + "![" + ", ".join(zl(v) for v in r) + "]\n" for j, r in enumerate(rows))
    def qm(name, vals):
        return f"def {name} : Fin {K} → ℚ := fun k =>\n  match k.val with\n" + "".join(
            (f"  | {j} => " if j < K - 1 else "  | _ => ") + qQ(v) + "\n" for j, v in enumerate(vals))
    if 'vsTop' in data:
        L.append(f"""/-- The switching table, from its entries at `(0, a, true)`. -/
def vs{i}Z : ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ ((List.finRange {K}).map famZ) DZ {Dl} X{i} SZ (fun _ _ _ => 0) ![{', '.join(zl(v) for v in data['vsTop'])}]

{qm(f'eS{i}', P['eS'][i])}
theorem chkS{i} : ∀ k, (autoSolZ (famZ k) DZ {Dl} X{i} SZ vs{i}Z &&
    decide ((autoBoundZ (famZ k) DZ X{i} SZ vs{i}Z : ℚ) ≤ eS{i} k * (X{i}.M DZ * SZ : ℤ))) = true := by
  decide +kernel

noncomputable def vs{i} : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vs{i}Z)
""")
        for k in range(K):
            e = P['eS'][i][k]
            L.append(f"theorem solS{i}_{k} : AutoSol (fam {k}) {Dl} {xgs} vs{i} := by\n  rw [xgQ{i}]; exact (switchZ_sound famR famA DZ_pos X{i}R SZ_pos chkS{i}).1 {k}\n")
            L.append(f"theorem heS{i}_{k} : autoBound (fam {k}) {xgs} vs{i} ≤ {qR(e)} := by\n"
                     f"  rw [xgQ{i}]; have h := (switchZ_sound famR famA DZ_pos X{i}R SZ_pos chkS{i}).2 {k}; rw [show eS{i} {k} = {qQ(e)} from rfl] at h; exact h.trans_eq (by push_cast; ring)\n")
    if 'postTop' in data:
        vm = data['vmax']
        L.append(f"""/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax{i}Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [{', '.join(zl(v) for v in vm)}]

/-- Each member's post-switch table at `(0, a, true)`. -/
{tm(f'postTop{i}', data['postTop'])}
/-- Each member's pre-switch table at `(0, a, true)`. -/
{tm(f'preTop{i}', data['preTop'])}
/-- Each member's in-epoch phase bound. -/
{qm(f'eIn{i}', P['eIn'][i])}
def post{i}Z (k : Fin {K}) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ {Dl} X{i} SZ (gFloorZ X{i} SZ) (postTop{i} k)
def pre{i}Z (k : Fin {K}) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ {Dl} X{i} SZ vmax{i}Z (preTop{i} k)

/-- Every check of member `k`, as one Boolean. -/
def chkE{i}Q (k : Fin {K}) : Bool :=
  autoSolZ (famZ k) DZ {Dl} X{i} SZ (post{i}Z k) && leTabZ {Dl} (post{i}Z k) vmax{i}Z &&
    preSolZ (famZ k) DZ {Dl} X{i} SZ vmax{i}Z (pre{i}Z k) &&
    decide ((autoBoundZ (famZ k) DZ X{i} SZ (post{i}Z k) : ℚ) ≤ eIn{i} k * (X{i}.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X{i} SZ (pre{i}Z k) : ℚ) ≤ {qQ(P['e'][i])} * (X{i}.M DZ * SZ : ℤ))

""" + "".join(f"theorem chkE{i}_{k} : chkE{i}Q {k} = true := by decide +kernel\n" for k in range(K)) + f"""
theorem chkE{i} : ∀ k, chkE{i}Q k = true := fun k => by
  fin_cases k; exacts [{', '.join(f'chkE{i}_{k}' for k in range(K))}]

noncomputable def vmax{i} : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax{i}Z)
noncomputable def vpreI{i} : Fin {K} → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre{i}Z k))
noncomputable def vpostI{i} : Fin {K} → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post{i}Z k))

theorem solE{i} : AutoSolE fam {Dl} {xgs} vpreI{i} vpostI{i} vmax{i} := by
  rw [xgQ{i}]; exact (oneSwitchZ_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).1

theorem heEall{i} : ∀ k, autoBound (fam k) {xgs} (vpreI{i} k) ≤ {qR(P['e'][i])} := by
  rw [xgQ{i}]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).2.2 k).trans_eq (by push_cast; ring)
""")
        for k in range(K):
            e = P['eIn'][i][k]
            L.append(f"theorem heIn{i}_{k} : autoBound (fam {k}) {xgs} (vpostI{i} {k}) ≤ {qR(e)} := by\n"
                     f"  rw [xgQ{i}]; have h := (oneSwitchZ_sound famR famA DZ_pos X{i}R SZ_pos chkE{i}).2.1 {k}; rw [show eIn{i} {k} = {qQ(e)} from rfl] at h; exact h.trans_eq (by push_cast; ring)\n")
    return "\n".join(L)
