"""Data-only multi-epoch certificates (`Cryptarchia/Prob/CertGen.lean`, `CertSpec.lean`).

A certificate states the numbers a search chose: the band family's breakpoints, the potential's
parameters `c z s κ d τ` and contractions `lp`, `lpi`, the estimate's band, the settlement
parameters and the bounds. Lean computes the rest (the bands, the automaton tables and their
bounds, the potential's expectations) and the kernel checks it. This module mirrors those
computations exactly, so the generator knows every check passes before it writes a file:

- `Fam.lean`: the family (`FamSpec`) and the configuration (`FamCfg`);
- `I<i>.lean`: index `i`'s seeds and bounds, computed at elaboration time, and its check;
- `NAME.lean`: the main checks and, at the specification, the finality theorem.
"""
import os
from fractions import Fraction as Fr
from certnum import rup
from gen import lean_q as q
from cert2 import check_cert
from certE import EL, PERIOD, tband_derived, check_class
import emitZ, powq
from emitZ import fill, keys, g_floor, seed_ok, check_sol, check_pre, boundz, M as MZ, SZ, H, solve_seeds, seeds_chain


def qQ(x):
    x = Fr(x)
    return f"({x.numerator} : ℚ)" if x.denominator == 1 else f"({x.numerator} / {x.denominator} : ℚ)"


ETA_ZETA = "(1 / 10 ^ 70) (1 / 10 ^ 16)"
HEAD = "set_option maxRecDepth 100000\nset_option maxHeartbeats 0\n"
SEC = "@[expose] public section\n"


def is_sw(i): return i in (0, 1, 2, 17)
def is_one(i): return i not in (2, 17)


# ---- the index computations of `FamCfg` (`CertGen.lean`), with its fixed solver settings

PAD = 2 ** 8


def bound_q(B, D, X, v):
    return Fr(boundz(B, D, X, SZ, lambda q_, a, u: v[(q_, a, u)]), MZ(X, D) * SZ)


def index_data(i, famZ, D, Dl, X):
    """`postSeeds`, `preSeeds`, `eInList`, `eEOf`, `swSeeds`, `eSOf`; every check of `idxChk` run"""
    lo = g_floor(X, SZ)
    floor = [lo(0, a, True) for a in range(3)]
    out = dict(eE=Fr(0), eS=Fr(0), eIn=[])
    if is_sw(i):
        vs = solve_seeds(famZ, D, Dl, X, SZ, lo, H, PAD, 3, 200, floor)
        tab = fill(famZ, D, Dl, X, SZ, lo, vs)
        assert all(seed_ok(B, D, Dl, X, SZ, lo, tab) and check_sol(B, D, Dl, X, SZ, tab) for B in famZ), ('switch', i)
        out['eS'] = max([Fr(0)] + [rup(bound_q(B, D, X, tab), 13) for B in famZ])
    if is_one(i):
        post = seeds_chain(D, Dl, X, SZ, lo, H, PAD, 3, 2, 200, famZ, floor)
        posts = [fill([B], D, Dl, X, SZ, lo, t) for B, t in zip(famZ, post)]
        vmax = {key: max([0] + [p[key] for p in posts]) for key in keys(Dl)}
        vlo = lambda q_, a, u: vmax[(q_, a, u)]
        pre = [solve_seeds([B], D, Dl, X, SZ, vlo, H, PAD, 0, 200, [vmax[(0, a, True)] for a in range(3)]) for B in famZ]
        pres = [fill([B], D, Dl, X, SZ, vlo, t) for B, t in zip(famZ, pre)]
        assert all(seed_ok(B, D, Dl, X, SZ, lo, po) and check_sol(B, D, Dl, X, SZ, po) for B, po in zip(famZ, posts)), ('post', i)
        assert all(seed_ok(B, D, Dl, X, SZ, vlo, pr) and check_pre(B, D, Dl, X, SZ, vmax, pr) for B, pr in zip(famZ, pres)), ('pre', i)
        out['eIn'] = [rup(bound_q(B, D, X, po), 13) for B, po in zip(famZ, posts)]
        out['eE'] = max([Fr(0)] + [rup(bound_q(B, D, X, pr), 13) for B, pr in zip(famZ, pres)])
    return out


def derived(dats):
    """`eOf`, `lrOf`, `bOf`"""
    e = [d['eE'] if is_one(i) else d['eS'] for i, d in enumerate(dats)]
    return e, max(dats[0]['eS'], dats[0]['eE']), max(dats[1]['eS'], dats[1]['eE'], Fr(1))


# ---- the files

def imports(lines, ext=False): return "module\n\n" + "".join(lines) + (emitZ_ext() if ext else "")


# Imports, as `lake shake` computes them: the modules whose `norm_num` and `simp` extensions the
# main file's proofs use. After changing the emitted proofs, rerun `lake shake CryptarchiaCerts`.
EXT = """import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
"""


def emitZ_ext(): return EXT


def write_fam(cfg, fam, sub, ns, name):
    D = cfg['Delta']; K = len(fam)
    beta = Fr(cfg['beta']).limit_denominator(1000)
    ys = [m['ylo'] for m in fam] + [fam[-1]['yhi']]
    c, z, s, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'd', 'tau'])
    txt = (imports(["public import Cryptarchia.Prob.CertSpec\n", "meta import Cryptarchia.Prob.CertSpec\n"]) + f"""
/-!
# {name}: the band family and the potential

Generated by `tools/certgen/emitF.py`. Member `k` of the family has honest exponent in
`[ys k, ys (k + 1)]` and adversarial exponent at most `β / (1 - β)` times the upper end; Lean
computes its band (`memberOfQ`) and the kernel checks it (`famOK`).
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

{HEAD}
/-- The band family: {K} members, β = {beta}. -/
def S : FamSpec := ⟨1 / 10 ^ 70, 1 / 10 ^ 16, {qQ(beta)}, 13, 12, {K},
  [{", ".join(qQ(y) for y in ys)}]⟩

/-- The family's integer bands (computed once), `Δ = {D}` and the potential's `c z s d τ`. -/
def F : FamCfg := ⟨S, eval% S.famZList S.DZ, eval% S.DZ, {D}, {qQ(c)}, {qQ(z)}, {qQ(s)}, {qQ(d)}, {qQ(tau)}⟩

theorem famOK : F.S.chk F.famZ F.D = true := by decide +kernel

theorem dOK : 0 < F.D := by decide +kernel

end {ns}
""")
    open(f"{sub}/Fam.lean", "w").write(txt)


def write_index(i, sub, ns, name):
    lines = []
    if is_one(i):
        lines += [f"def post{i} : List (List ℤ) := eval% F.postSeeds {i}\n",
                  f"def pre{i} : List (List ℤ) := eval% F.preSeeds {i} post{i}\n"]
        one = f"post{i}, pre{i}, eval% F.eInList {i} post{i}, eval% F.eEOf {i} post{i} pre{i}"
    else:
        one = "[], [], [], 0"
    if is_sw(i):
        lines.append(f"def vs{i} : List ℤ := eval% F.swSeeds {i}\n")
        sw = f"vs{i}, eval% F.eSOf {i} vs{i}"
    else:
        sw = "[], 0"
    txt = (imports([f"public import {ns}.Fam\n", f"meta import {ns}.Fam\n"]) + f"""
/-! # {name}: phase index {i}, its tables' seeds and bounds computed at elaboration time -/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

{HEAD}
{"".join(lines)}
def dat{i} : IdxData := ⟨{one}, {sw}⟩

theorem chk{i} : F.idxChk {i} dat{i} = true := by decide +kernel

end {ns}
""")
    open(f"{sub}/I{i}.lean", "w").write(txt)


def check_all(cfg, T, fam, B, P):
    """every index's data and the main checks, mirrored; returns the indices' data and the derived
    expectations"""
    D = cfg['Delta']
    Dz, famZ = emitZ.fam_z(fam)
    args = tuple(Fr(cfg[v]) for v in ['c', 'z', 's', 'd', 'tau'])
    dats = [index_data(i, famZ, Dz, D, emitZ.ph_z(i, *args)) for i in range(19)]
    e, lr, b = derived(dats)
    # below the planned values, so the planned contractions and targets hold
    for i in range(19):
        assert e[i] <= P['e'][i], ('e', i)
        if is_one(i): assert all(x <= y for x, y in zip(dats[i]['eIn'], P['eIn'][i])), ('eIn', i)
    assert lr <= P['lr'] and b <= P['b']
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    ok, oks = check_cert(B, D, c, z, s, kap, d, tau, P['lp'], lr, b, e)
    assert ok, [j for j, o in enumerate(oks) if not o]
    for k, m in enumerate(fam):
        ek = [dats[i]['eIn'][k] if is_one(i) else Fr(0) for i in range(19)]
        assert check_class(D, c, z, s, kap, d, P['lpi'], ek, P['patk'][k])[0], ('class', k)
    return dats, e, lr, b


def emit(cfg, T, fam, B, P, name, out_dir, target):
    """write a certificate at the specification: `Fam.lean`, `I<i>.lean`, `NAME.lean`"""
    D = cfg['Delta']; K = len(fam); N = cfg['N']; k = cfg['k']
    G, Gp, J, Lw, r, Tg = cfg['G'], cfg['Gp'], cfg['J'], cfg['Lw'], cfg['r'], cfg['T']
    x, yy = Fr(cfg['x']), Fr(cfg['yy'])
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    ns = f"Cryptarchia.Prob.Certs.{name}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    for old in os.listdir(sub):
        if old.endswith('.lean'): os.remove(f"{sub}/{old}")
    dats, e, lr, b = check_all(cfg, T, fam, B, P)
    # the settlement and band bounds, below their targets
    M = N + G + Gp + D + 2
    Ne = M // EL + 1
    nb = (EL - PERIOD - D - 3 - G + D) // (Tg + D)
    ne = (N + 2) // EL
    sq = powq.settle_q(powq.D_POW, D, B, e[17], tau, P['lp'], e[2], b, lr, c, P['lpi'], x, yy, k, ne, nb, G, N, G, Gp,
                       J, Lw, r, Tg)
    assert sq <= target, (float(sq), float(target))
    dv = tband_derived(T)
    from gen import chain
    from certnum import rdn
    # the band's bound: 1 / Q per term, Q from `exp (-a) ≤ 1 / (1 + a / n) ^ n` with `a` rounded down
    n = powq.N_EXP
    m = (PERIOD - 1) * dv['ylo'] * dv['clo']
    a1 = m * T['delta'] ** 2 / 2; a2 = m * T['delta'] ** 2 * (Fr(1, 2) - Fr(2, 9) * T['delta'])
    Qs = [chain(1 + rdn(a, 8) / n, n, False, name='bq')[1] for a in (a1, a2)]
    BX = rup(1 / Qs[0] + 1 / Qs[1], 4)
    assert powq.band_q(powq.D_POW, n, dv, T['delta'], PERIOD) <= BX
    FINAL = rup(target + Ne * BX, 2)
    assert M // EL < Ne and N + G + Gp + D + 2 <= M and Lw + G < EL and PERIOD + G + 2 <= EL
    write_fam(cfg, fam, sub, ns, name)
    for i in range(19): write_index(i, sub, ns, name)
    beta = T['beta']
    tq = f"⟨{qQ(T['llo'])}, {qQ(T['lhi'])}, {qQ(T['mu'])}, {qQ(beta)}, {qQ(T['delta'])}, {ETA_ZETA.replace(') (', '), (')}⟩"
    txt = (imports([f"public import {ns}.I{i}\n" for i in range(19)], ext=True) + f"""
/-!
# Multi-epoch finality certificate: β = {beta}, Δ = {D}, k = {k}, {K} members

Generated by `tools/certgen/emitF.py`. The certificate is the data below; Lean computes the rest
and the kernel checks it (`CertGen.lean`, `CertSpec.lean`):

- the band family and the potential's parameters (`Fam.lean`), and each phase index's tables
  (`I<i>.lean`);
- the chosen numbers `par`: the potential's `κ`, contractions `lp` and `lpi`, the settlement
  parameters and the bounds on settlement (`{float(target):.2e}`), on leaving the band in one epoch
  (`{float(BX):.3e}`) and on a finality violation; and the estimate's band `Tq`;
- the checks of the potential (`mainOK`) and of every numeric condition (`finOK`).
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

{HEAD}
/-- The phase indices' data. -/
def dat : Fin 19 → IdxData := ![{", ".join(f"dat{i}" for i in range(19))}]

theorem idxOK : ∀ i : Fin 19, F.idxChk i (dat i) = true := by
  intro i; fin_cases i
  exacts [{", ".join(f"chk{i}" for i in range(19))}]

/-- The certificate's chosen numbers. -/
def par : SpecData where
  κ := {qQ(kap)}
  lp := {qQ(P['lp'])}
  lpi := {qQ(P['lpi'])}
  N := {N}
  M := {M}
  Ne := {Ne}
  G := {G}
  G' := {Gp}
  J := {J}
  Lw := {Lw}
  r := {r}
  T := {Tg}
  x := {qQ(x)}
  yy := {qQ(yy)}
  ρ := {qQ(T['rho'])}
  Hmin := {qQ(T['hmin'])}
  tgt := {qQ(target)}
  bx := {qQ(BX)}
  fin := {qQ(FINAL)}

/-- The estimate's band: `λV/D ∈ [ℓlo, ℓhi]`, μ = {T['mu']}, β = {beta}, δ = {T['delta']}. -/
def Tq : TBandQ := {tq}

theorem mainOK : F.mainChk F.S.weakest par.κ par.lp par.lpi dat = true := by decide +kernel

theorem finOK : FamCfg.finChkSpec F F.S.weakest dat Tq par = true := by decide +kernel

/-- **Finality, certified.** f = 1/30, k = {k}, Δ = {D} slots, executions up to slot {N}. Under the
execution model (`Model`), if the genesis estimate is the genesis stake, the adversary holds at most
{float(beta)} of the participating stake, the canonical chain counts at least {float(1 - T['mu'])} of
each window's honestly won slots, stake drifts by at most a factor {float(T['rho'])} per epoch and
honest online stake is at least {T['hmin']}, a finality violation has probability at most
{float(FINAL):.2e}. -/
theorem finality {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) (hc : E.c = Config.spec) (hΔ : E.Δ = {D})
    (es : Ω → List Event) (hM : Model μ O E es) (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ {N})
    (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} {Ne})
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} {Ne})
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal {q(FINAL)} := by
  have h := FamCfg.finality_spec F par mainOK famOK dOK rfl idxOK rfl Tq finOK hc hΔ es hM hN hG
    (fun ω => by simpa [Tq] using hS ω) (fun ω => by simpa [Tq, par] using hQ ω)
    (fun ω => by simpa [par] using hD ω) (fun ω => by simpa [par] using hH ω)
  simpa [par] using h

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
    return FINAL


# ---- closed-form certificates (`CertClosed.lean`)

def closed_data(cfg, T, B, P, dats, cl):
    """the closed form's chosen numbers, as `emitC.closed_section` sets them, every check of
    `closedChk` mirrored"""
    import emitC
    from certnum import rdn
    D = cfg['Delta']; G = cfg['G']; m = emitC.M_DIV
    j, w, g, rho, Tg, x, yy, k0 = cl['j'], cl['w'], cl['g'], cl['rho'], cl['Tg'], cl['x'], cl['yy'], cl['k0']
    e, lr, b = derived(dats)
    e17, e2, lp, lpi = e[17], e[2], P['lp'], P['lpi']
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    hhi, hlo, elo = B['hhi'], B['hlo'], B['elo']
    nb = 120 * m // (Tg + D)
    assert 120 * m == nb * (Tg + D)
    nb0 = -(-(3 + G) // (Tg + D)) + 1
    # the constants, as `emitC` computes them (from the planned bounds)
    consts, Qs, _, _, Cs, short = emitC.closed_consts(cfg, T, B, P, D, cl)
    d = powq.D_POW
    up, dn = (lambda xx, n: powq.pow_up(d, xx, n)), (lambda xx, n: powq.pow_dn(d, xx, n))
    STAT = 1 + (b - 1) / (1 - lr)
    bs = 1 + (yy - 1) * (1 - (1 - hhi) ** Tg if 1 <= yy else 1 - (1 - hlo) ** Tg)
    C = consts
    assert up(1 - (1 - hhi) ** D, G // D) <= C['A1'] and up(1 - hlo, g) <= C['q2']
    assert e17 / tau <= C['A3'] and up(e17, j) / dn(tau, w) <= C['q3']
    assert up(lp / lpi, G) * e2 * STAT <= C['A4'] and up(lpi, j) <= C['q4']
    assert 1 / x <= C['A5'] and up(1 + (x - 1) * (1 - elo), w) / dn(x, m) <= C['q5']
    assert STAT / c <= C['A6'] and 1 / dn(c, rho) <= C['q6']
    assert bs > 0 and (1 / bs) ** nb0 * (1 / yy) ** m <= C['A7'] and up(bs, nb) / dn(yy, m + rho) <= C['q7']
    dv = tband_derived(T); delta = T['delta']
    a1 = dv['ylo'] * dv['clo'] * delta ** 2 / 2; a2 = dv['ylo'] * dv['clo'] * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    for a, Cb, Qb in ((a1, Cs[0], Qs[0]), (a2, Cs[1], Qs[1])):
        assert 0 <= a <= 1 - 1 / Cb and 0 < Qb <= dn(1 + 180 * m * a / 4096, 4096)
    t0 = short['t0']
    qi = [C['q2'], C['q3'], C['q4'], C['q5'], C['q6'], C['q7']]
    Ai = [1, C['A3'], C['A4'], C['A5'], C['A6'], C['A7']]
    assert sum(A_ * (q_ ** t0 / short['qs'] ** t0) for A_, q_ in zip(Ai, qi)) <= short['As']
    assert sum(Cb * ((1 / Qb) ** t0 / short['qb'] ** t0) for Cb, Qb in zip(Cs, Qs)) <= short['Ab']
    assert m * t0 <= k0
    return dict(G=G, g=g, j=j, w=w, rho=rho, T=Tg, m=m, nb=nb, nb0=nb0, k0=k0, x=x, yy=yy, C=C, Cs=Cs, Qs=Qs,
                short=short)


def emit_closed(cfg, T, fam, B, P, name, out_dir, cl):
    """write a closed-form certificate: `Fam.lean`, `I<i>.lean`, `NAME.lean`"""
    D = cfg['Delta']; K = len(fam)
    kap = Fr(cfg['kap'])
    ns = f"Cryptarchia.Prob.Certs.{name}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    for old in os.listdir(sub):
        if old.endswith('.lean'): os.remove(f"{sub}/{old}")
    dats, e, lr, b = check_all(cfg, T, fam, B, P)
    cd = closed_data(cfg, T, B, P, dats, cl)
    C, sh = cd['C'], cd['short']
    write_fam(cfg, fam, sub, ns, name)
    for i in range(19): write_index(i, sub, ns, name)
    beta = T['beta']
    tq = f"⟨{qQ(T['llo'])}, {qQ(T['lhi'])}, {qQ(T['mu'])}, {qQ(beta)}, {qQ(T['delta'])}, (1 / 10 ^ 70), (1 / 10 ^ 16)⟩"
    flds = [("κ", qQ(kap)), ("lp", qQ(P['lp'])), ("lpi", qQ(P['lpi'])), ("G", cd['G']), ("g", cd['g']), ("j", cd['j']),
            ("w", cd['w']), ("ρr", cd['rho']), ("T", cd['T']), ("m", cd['m']), ("nb", cd['nb']), ("nb0", cd['nb0']),
            ("k0", cd['k0']), ("x", qQ(cd['x'])), ("yy", qQ(cd['yy'])), ("ρ", qQ(T['rho'])), ("Hmin", qQ(T['hmin']))]
    flds += [(kk, qQ(C[kk])) for kk in ['A1', 'q2', 'A3', 'q3', 'A4', 'q4', 'A5', 'q5', 'A6', 'q6', 'A7', 'q7']]
    flds += [("C1", qQ(cd['Cs'][0])), ("Q1", qQ(cd['Qs'][0])), ("C2", qQ(cd['Cs'][1])), ("Q2", qQ(cd['Qs'][1])),
             ("t0", sh['t0']), ("qs", qQ(sh['qs'])), ("As", qQ(sh['As'])), ("qb", qQ(sh['qb'])), ("Ab", qQ(sh['Ab']))]
    par = "".join(f"  {kk} := {v}\n" for kk, v in flds)
    k0, g, G = cd['k0'], cd['g'], cd['G']
    hyps = f"""(E : Env) {{k : ℕ}} (hc : E.c = Config.specK k) (hk : {k0} ≤ k) (hΔ : E.Δ = {D}) (es : Ω → List Event)
    (hM : Model μ O E es) {{N : ℕ}} (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} (N / (300 * k) + 2))
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])})"""
    txt = (imports([f"public import {ns}.I{i}\n" for i in range(19)] + ["public import Cryptarchia.Prob.CertClosed\n"],
                   ext=True) + f"""
/-!
# Closed-form finality certificate: β = {beta}, Δ = {D}, every k ≥ {k0}, {K} members

Generated by `tools/certgen/emitF.py`. The certificate is the data below; Lean computes the rest
and the kernel checks it (`CertGen.lean`, `CertClosed.lean`). The settlement parameters grow
linearly in `t = k / {cd['m']}`, and `finality_closed` bounds a finality violation by `par.epsC N k`, a
sum of geometric terms in `t`, for every depth `k ≥ {k0}` and every horizon `N`.
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

{HEAD}
/-- The phase indices' data. -/
def dat : Fin 19 → IdxData := ![{", ".join(f"dat{i}" for i in range(19))}]

theorem idxOK : ∀ i : Fin 19, F.idxChk i (dat i) = true := by
  intro i; fin_cases i
  exacts [{", ".join(f"chk{i}" for i in range(19))}]

/-- The certificate's chosen numbers. -/
def par : ClosedData where
{par}
/-- The estimate's band: `λV/D ∈ [ℓlo, ℓhi]`, μ = {T['mu']}, β = {beta}, δ = {T['delta']}. -/
def Tq : TBandQ := {tq}

theorem mainOK : F.mainChk F.S.weakest par.κ par.lp par.lpi dat = true := by decide +kernel

theorem closedOK : FamCfg.closedChk F F.S.weakest dat Tq par = true := by decide +kernel

/-- **Finality in closed form.** f = 1/30, Δ = {D} slots, any depth `k ≥ {k0}` and any horizon `N`.
Under the execution model (`Model`), if the genesis estimate is the genesis stake, the adversary
holds at most {float(beta)} of the participating stake, the canonical chain counts at least
{float(1 - T['mu'])} of each window's honestly won slots, stake drifts by at most a factor
{float(T['rho'])} per epoch and honest online stake is at least {T['hmin']}, a finality violation has
probability at most `par.epsC N k`. -/
theorem finality_closed {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} {hyps} :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal (par.epsC N k) :=
  FamCfg.finality_closed_gen F par mainOK famOK dOK rfl idxOK rfl Tq closedOK
    (fun k hk => by simp only [par, F] at hk ⊢; omega) (fun k hk => by simp only [par] at hk ⊢; omega)
    (fun k hk => by simp only [par, F] at hk ⊢; omega) E hc hk hΔ es hM hN hG
    (fun ω => by simpa [Tq] using hS ω) (fun ω => by simpa [Tq] using hQ ω) (fun ω => by simpa [par] using hD ω)
    (fun ω => by simpa [par] using hH ω)

/-- **Finality in closed form, short**: with `t = k / {cd['m']}` and `Ne = N / (300 k) + 2` epochs, a
finality violation has probability at most
`(N + {g} t + {G + 2}) · ({float(C['A1']):.2g} + {float(sh['As']):.4g} · {float(sh['qs']):.6f}ᵗ) + Ne · {float(sh['Ab']):.4g} · {float(sh['qb']):.6f}ᵗ`:
settlement at rate {float(sh['qs']):.4f} per {cd['m']} blocks of depth, the estimate's band at rate {float(sh['qb']):.4f}. -/
theorem finality_closed_short {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} {hyps} :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal (par.epsShort N k) :=
  (finality_closed E hc hk hΔ es hM hN hG hS hQ hD hH).trans
    (ENNReal.ofReal_le_ofReal (FamCfg.epsC_le_short par closedOK N hk))

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
