"""Data-only multi-epoch certificates (`Cryptarchia/Prob/CertGen.lean`, `CertSpec.lean`).

A certificate states the numbers a search chose: the band family's breakpoints, the potential's
parameters `c z s κ d τ` and contractions `lp`, `lpi`, the estimate's band, the settlement
parameters and the bounds. Lean computes the rest (the bands, the automaton tables and their
bounds, the potential's expectations) and the kernel checks it. This module mirrors those
computations exactly, so the generator knows every check passes before it writes a file:

- `Data.lean`: the family (`FamSpec`), the configuration (`FamCfg`), and each index's seeds and
  bounds, computed at elaboration time, with its check;
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


# ---- the records' fields, each with a line comment

def record(fields):
    """the fields of a `where` record, `(name, value, comment)`, with aligned line comments; a long
    field's comment goes on the line above it"""
    short = [len(f"  {n} := {v}") for n, v, _ in fields if len(f"  {n} := {v}") <= 80]
    w = max(short) if short else 0
    out = ""
    for n, v, c in fields:
        line = f"  {n} := {v}"
        out += f"  -- {c}\n{line}\n" if len(line) > 80 else line.ljust(w) + f"  -- {c}\n"
    return out


def fam_fields(beta, K, ys):
    return [("η", "1 / 10 ^ 70", "the lottery threshold's approximation error"),
            ("ζ", "1 / 10 ^ 16", "the largest note's share of the stake"),
            ("β", qQ(beta), "the adversary's share of the participating stake"),
            ("d", "13", "significant digits of the bands' fields"),
            ("dy", "12", "significant digits of the adversarial exponent's bound"),
            ("K", str(K), "the members"),
            ("ys", "[" + ", ".join(qQ(y) for y in ys) + "]", "the breakpoints: member k has honest exponent in [ys k, ys (k + 1)]")]


def tq_fields(T):
    return [("ℓlo", qQ(T['llo']), "the estimate's band, below: ℓlo ≤ λ V / D"),
            ("ℓhi", qQ(T['lhi']), "and above: λ V / D ≤ ℓhi"),
            ("μ", qQ(T['mu']), "the canonical chain's loss of honestly won slots (`ChainQuality`)"),
            ("β", qQ(T['beta']), "the adversary's share of the participating stake"),
            ("δ", qQ(T['delta']), "the estimate's relative band per epoch"),
            ("η", "1 / 10 ^ 70", "the lottery threshold's approximation error"),
            ("ζ", "1 / 10 ^ 16", "the largest note's share of the stake")]


POT = [("κ", "the weight of the cold potential's second term"),
       ("lp", "the potential's contraction per phase"),
       ("lpi", "its contraction per phase inside an epoch")]


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


def write_params(cfg, fam, T, par_type, par_fields, sub, ns, name, closed=False):
    """`Params.lean`: every number the search chose, each with a line comment"""
    D = cfg['Delta']; K = len(fam)
    beta = Fr(cfg['beta']).limit_denominator(1000)
    ys = [m['ylo'] for m in fam] + [fam[-1]['yhi']]
    c, z, s, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'd', 'tau'])
    pot = [("Δ", str(D), "the network delay, in slots"),
           ("c", qQ(c), "the potential's base for the reach"),
           ("z", qQ(z), "the potential's base for the margin, when cold"),
           ("s", qQ(s), "the weight of the cold potential's first term"),
           ("d", qQ(d), "the base of the cold potential's second term"),
           ("τ", qQ(tau), "the span term's base per slot")]
    lib = "CertClosed" if closed else "CertSpec"
    txt = (imports([f"public import Cryptarchia.Prob.{lib}\n"]) + f"""
/-!
# {name}: the chosen numbers

Generated by `tools/certgen/emitF.py`. Every number of the certificate that a search chose; Lean
computes the rest (`Data.lean`, the main file) and the kernel checks it.
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

/-- The band family. -/
def S : FamSpec where
{record(fam_fields(beta, K, ys))}
/-- The potential's parameters. -/
def pot : PotCfg where
{record(pot)}
/-- The certificate's other chosen numbers. -/
def par : {par_type} where
{record(par_fields)}
/-- The estimate's band: `λV/D ∈ [ℓlo, ℓhi]`, μ = {T['mu']}, β = {T['beta']}, δ = {T['delta']}. -/
def Tq : TBandQ where
{record(tq_fields(T))}
end {ns}
""")
    open(f"{sub}/Params.lean", "w").write(txt)


def index_lines(i):
    """index `i`'s seeds and bounds, computed at elaboration time, and its check"""
    lines = [f"/-! ### Index {i} -/\n\n"]
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
    lines += [f"def dat{i} : IdxData := ⟨{one}, {sw}⟩\n",
              f"theorem chk{i} : F.idxChk {i} dat{i} = true := by decide +kernel\n"]
    return "".join(lines)


def write_data(sub, ns, name):
    """`Data.lean`: the family's integer bands and each index's seeds and bounds, computed at
    elaboration time, with the kernel's checks"""
    cfg_f = [("toPotCfg", "pot", "the potential's parameters"),
             ("S", "S", "the band family"),
             ("famZL", "eval% S.famZList S.DZ", "the members' integer bands, computed once"),
             ("D", "eval% S.DZ", "their common denominator")]
    txt = (imports([f"public import {ns}.Params\n", f"meta import {ns}.Params\n"]) + f"""
/-!
# {name}: the computed data

Generated by `tools/certgen/emitF.py`. The band family: Lean computes each member's band from its
breakpoints (`memberOfQ`) and the kernel checks it (`famOK`). The phase indices: each index's tables
are given by their seeds, which Lean computes at elaboration time (`eval%`), with the bounds they
give; the kernel checks each index (`chk<i>`, `FamCfg.idxChk`).
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

{HEAD}
/-- The family's integer bands and the potential's parameters. -/
def F : FamCfg where
{record(cfg_f)}
theorem famOK : F.S.chk F.famZ F.D = true := by decide +kernel

theorem dOK : 0 < F.D := by decide +kernel

/-! ## The phase indices -/

""" + "\n".join(index_lines(i) for i in range(19)) + f"""
end {ns}
""")
    open(f"{sub}/Data.lean", "w").write(txt)


def check_all(cfg, T, fam, B, P):
    """every index's data, the expectations and contractions derived from them, and the main checks,
    mirrored; returns the indices' data, the expectations, and the contractions"""
    from cert2 import lp_exact
    D = cfg['Delta']
    Dz, famZ = emitZ.fam_z(fam)
    args = tuple(Fr(cfg[v]) for v in ['c', 'z', 's', 'd', 'tau'])
    dats = [index_data(i, famZ, Dz, D, emitZ.ph_z(i, *args)) for i in range(19)]
    e, lr, b = derived(dats)
    for i in range(19):
        assert e[i] <= P['e'][i], ('e', i)
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    # the contractions (`lpOf`, `lpiOf`)
    lp = lp_exact(B, D, c, z, s, kap, d, e)
    eik = [[dats[i]['eIn'][k] if is_one(i) else Fr(0) for i in range(19)] for k in range(len(fam))]
    lpi = max([Fr(0)] + [lp_exact({'slo': P['patk'][k], 'elo': Fr(1)}, D, c, z, s, kap, d, eik[k])
                         for k in range(len(fam))])
    ok, oks = check_cert(B, D, c, z, s, kap, d, tau, lp, lr, b, e)
    assert ok, [j for j, o in enumerate(oks) if not o]
    assert 0 < lpi <= lp
    for k in range(len(fam)):
        assert check_class(D, c, z, s, kap, d, lpi, eik[k], P['patk'][k])[0], ('class', k)
    return dats, e, lr, b, lp, lpi


def emit(cfg, T, fam, B, P, name, out_dir, target=None):
    """write a certificate at the specification: `Params.lean`, `Data.lean`, `NAME.lean`; its bounds are derived
    (`SpecData.derive`), and `target` is only compared with them"""
    D = cfg['Delta']; K = len(fam); N = cfg['N']; k = cfg['k']
    G, Gp, J, Lw, r, Tg = cfg['G'], cfg['Gp'], cfg['J'], cfg['Lw'], cfg['r'], cfg['T']
    x, yy = Fr(cfg['x']), Fr(cfg['yy'])
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    ns = f"Cryptarchia.Prob.Certs.{name}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    for old in os.listdir(sub):
        if old.endswith('.lean'): os.remove(f"{sub}/{old}")
    dats, e, lr, b, lp, lpi = check_all(cfg, T, fam, B, P)
    # the derived numbers (`SpecData.derive`)
    M = N + G + Gp + D + 2
    Ne = M // EL + 1
    nb = (EL - PERIOD - D - 3 - G + D) // (Tg + D)
    ne = (N + 2) // EL
    tgt = rup(powq.settle_q(powq.D_POW, D, B, e[17], tau, lp, e[2], b, lr, c, lpi, x, yy, k, ne, nb, G, N, G, Gp,
                            J, Lw, r, Tg), 2)
    dv = tband_derived(T)
    bx = rup(powq.band_q(powq.D_POW, powq.N_EXP, dv, T['delta'], PERIOD), 4)
    fin = rup(tgt + Ne * bx, 2)
    if target is not None and tgt > target: print(name, 'derived settlement bound', float(tgt), 'above', float(target))
    assert M // EL < Ne and Lw + G < EL and PERIOD + G + 2 <= EL
    beta = T['beta']
    spec_fields = [("κ", qQ(kap), POT[0][1]),
        ("N", N, "the horizon: executions up to slot N"),
        ("G", G, "the phase cut: longer phases count as failures"),
        ("G'", Gp, "the longest empty run"),
        ("J", J, "the phases of a span"),
        ("Lw", Lw, "the slots of a span, and of a crowded window"),
        ("r", r, "the reach bound"),
        ("T", Tg, "the growth block, in slots"),
        ("x", qQ(x), "the crowded-window tilt"),
        ("yy", qQ(yy), "the slow-growth tilt"),
        ("ρ", qQ(T['rho']), "the stake drift per epoch (`StakeDrift`)"),
        ("Hmin", qQ(T['hmin']), "the least honest online stake (`MinStake`)")]
    write_params(cfg, fam, T, "SpecData", spec_fields, sub, ns, name)
    write_data(sub, ns, name)
    txt = (imports([f"public import {ns}.Data\n"], ext=True) + f"""
/-!
# Multi-epoch finality certificate: β = {beta}, Δ = {D}, k = {k}, {K} members

Generated by `tools/certgen/emitF.py`. The specification's parameters (f = 1/30, k = {k}) are
`Config.spec`'s. The certificate is the data below; Lean computes the rest and the kernel checks it
(`CertGen.lean`, `CertSpec.lean`):

- the chosen numbers: the band family, the potential's parameters, the other numbers `par` and the
  estimate's band `Tq` (`Params.lean`);
- each phase index's tables (`Data.lean`);
- the derived numbers `der` (`SpecData.derive`): the contractions, and the bounds on settlement, on
  leaving the band in one epoch and on a finality violation;
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

/-- The derived numbers: the slots and epochs covered, the contractions from the tables' bounds, and the
bounds on settlement ({float(tgt):.2e}), on leaving the band in one epoch ({float(bx):.3e}) and on a
finality violation ({float(fin):.2e}). -/
def der : SpecDerived := par.derive F F.S.weakest dat Tq

theorem derNe : der.Ne = {Ne} := by decide +kernel

theorem derFin : der.fin = {qQ(fin)} := by decide +kernel

theorem mainOK : F.mainChk F.S.weakest par.κ der.lp der.lpi dat = true := by decide +kernel

theorem finOK : FamCfg.finChkSpec F F.S.weakest dat Tq par der = true := by decide +kernel

/-- **Finality, certified.** f = 1/30, k = {k}, Δ = {D} slots, executions up to slot {N}. Under the
execution model (`Model`), if the genesis estimate is the genesis stake, the adversary holds at most
{float(beta)} of the participating stake, the canonical chain counts at least {float(1 - T['mu'])} of
each window's honestly won slots, stake drifts by at most a factor {float(T['rho'])} per epoch and
honest online stake is at least {T['hmin']}, a finality violation has probability at most
{float(fin):.2e}. -/
theorem finality {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) (hc : E.c = Config.spec) (hΔ : E.Δ = {D})
    (es : Ω → List Event) (hM : Model μ O E es) (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ {N})
    (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} {Ne})
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} {Ne})
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal {q(fin)} := by
  have h := FamCfg.finality_spec F par der mainOK famOK dOK rfl idxOK rfl Tq finOK hc hΔ es hM hN hG
    (fun ω => by simpa [Tq] using hS ω) (fun ω => by simpa [Tq, derNe] using hQ ω)
    (fun ω => by simpa [par, derNe] using hD ω) (fun ω => by simpa [par] using hH ω)
  rw [derFin] at h
  simpa using h

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
    return fin, tgt, bx


# ---- closed-form certificates (`CertClosed.lean`)

def closed_derive(cfg, T, B, dats, lp, lpi, cl):
    """`ClosedData.derive`: the closed form's derived numbers, from the tables' bounds"""
    import emitC
    from certnum import rdn
    D = cfg['Delta']; m = emitC.M_DIV
    G, g, j, w, rho, Tg, x, yy, k0 = cl['G'], cl['g'], cl['j'], cl['w'], cl['rho'], cl['Tg'], cl['x'], cl['yy'], cl['k0']
    e, lr, b = derived(dats)
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    hhi, hlo, elo = B['hhi'], B['hlo'], B['elo']
    up = lambda base, n: powq.pow_up(14, base, n)
    dn = lambda base, n: powq.pow_dn(14, base, n)
    stat = 1 + (b - 1) / (1 - lr)
    nb = 120 * m // (Tg + D)
    nb0 = (3 + G + (Tg + D) - 1) // (Tg + D) + 1
    bs = 1 + (yy - 1) * (1 - (1 - hhi) ** Tg if 1 <= yy else 1 - (1 - hlo) ** Tg)
    C = dict(A1=up(rup(1 - (1 - hhi) ** D, 14), G // D), q2=up(rup(1 - hlo, 14), g),
             A3=rup(e[17] / tau, 14), q3=rup(up(e[17], j) / dn(tau, w), 14),
             A4=rup(up(lp / lpi, G) * e[2] * stat, 14), q4=up(lpi, j),
             A5=rup(1 / x, 14), q5=rup(up(1 + (x - 1) * (1 - elo), w) / dn(x, m), 14),
             A6=rup(stat / c, 14), q6=rup(1 / dn(c, rho), 14),
             A7=rup((1 / rdn(bs, 14)) ** nb0 * (1 / yy) ** m, 14), q7=rup(up(rup(bs, 14), nb) / dn(yy, m + rho), 14))
    dv = tband_derived(T); delta = T['delta']
    a1 = dv['ylo'] * dv['clo'] * delta ** 2 / 2; a2 = dv['ylo'] * dv['clo'] * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    Cs = [rup(1 / (1 - a), 10) for a in (a1, a2)]
    Qs = [dn(1 + rdn(180 * m * a, 8) / 4096, 4096) for a in (a1, a2)]
    t0 = k0 // m
    qi = [C[f'q{i}'] for i in range(2, 8)]
    Ai = [Fr(1)] + [C[f'A{i}'] for i in range(3, 8)]
    qs = rup(max(qi), 6)
    qb = rup(max(1 / Qs[0], 1 / Qs[1]), 6)
    As = sum(rup(A_ * (q_ / qs) ** t0, 6) for A_, q_ in zip(Ai, qi))
    Ab = sum(rup(Cb * ((1 / Qb) / qb) ** t0, 6) for Cb, Qb in zip(Cs, Qs))
    # every condition of `closedChk`
    assert e[17] / tau <= C['A3'] and bs > 0 and 0 < lpi and m * t0 <= k0
    for a, Cb, Qb in ((a1, Cs[0], Qs[0]), (a2, Cs[1], Qs[1])):
        assert 0 <= a <= 1 - 1 / Cb and 0 < Qb <= dn(1 + 180 * m * a / 4096, 4096)
    assert sum(A_ * (q_ ** t0 / qs ** t0) for A_, q_ in zip(Ai, qi)) <= As
    assert sum(Cb * ((1 / Qb) ** t0 / qb ** t0) for Cb, Qb in zip(Cs, Qs)) <= Ab
    return dict(lp=lp, lpi=lpi, nb=nb, nb0=nb0, C=C, Cs=Cs, Qs=Qs, t0=t0, qs=qs, As=As, qb=qb, Ab=Ab)


def emit_closed(cfg, T, fam, B, P, name, out_dir, cl):
    """write a closed-form certificate: `Params.lean`, `Data.lean`, `NAME.lean`"""
    import emitC
    D = cfg['Delta']; K = len(fam)
    kap = Fr(cfg['kap'])
    ns = f"Cryptarchia.Prob.Certs.{name}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    for old in os.listdir(sub):
        if old.endswith('.lean'): os.remove(f"{sub}/{old}")
    dats, e, lr, b, lp, lpi = check_all(cfg, T, fam, B, P)
    m_ = emitC.M_DIV
    cl = dict(cl, G=cfg['G'])
    q_ = closed_derive(cfg, T, B, dats, lp, lpi, cl)
    C = q_['C']
    beta = T['beta']
    par_f = [("κ", qQ(kap), POT[0][1]),
        ("G", cl['G'], "the phase cut: longer phases count as failures"),
        ("g", cl['g'], f"the longest empty run, per t = k / {m_}"),
        ("j", cl['j'], "the phases of a span, per t"),
        ("w", cl['w'], "the slots of a span, and of a crowded window, per t"),
        ("ρr", cl['rho'], "the reach bound, per t"),
        ("T", cl['Tg'], "the growth block, in slots"),
        ("m", m_, "the depth per t"),
        ("k0", cl['k0'], "the least depth"),
        ("x", qQ(cl['x']), "the crowded-window tilt"),
        ("yy", qQ(cl['yy']), "the slow-growth tilt"),
        ("ρ", qQ(T['rho']), "the stake drift per epoch (`StakeDrift`)"),
        ("Hmin", qQ(T['hmin']), "the least honest online stake (`MinStake`)")]
    write_params(cfg, fam, T, "ClosedData", par_f, sub, ns, name, closed=True)
    write_data(sub, ns, name)
    k0, g, G = cl['k0'], cl['g'], cl['G']
    hyps = f"""(E : Env) {{k : ℕ}} (hc : E.c = Config.specK k) (hk : {k0} ≤ k) (hΔ : E.Δ = {D}) (es : Ω → List Event)
    (hM : Model μ O E es) {{N : ℕ}} (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} (N / (300 * k) + 2))
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])})"""
    txt = (imports([f"public import {ns}.Data\n", "public import Cryptarchia.Prob.CertClosed\n"],
                   ext=True) + f"""
/-!
# Closed-form finality certificate: β = {beta}, Δ = {D}, every k ≥ {k0}, {K} members

Generated by `tools/certgen/emitF.py`. The specification's parameters (f = 1/30, any depth `k`) are
`Config.specK k`'s. The certificate is the data below; Lean computes the rest and the kernel checks
it (`CertGen.lean`, `CertClosed.lean`); the chosen numbers are in `Params.lean`, the computed index data
in `Data.lean`. The settlement parameters grow linearly in `t = k / {m_}`, and
`finality_closed` bounds a finality violation by `par.epsC der N k`, a sum of geometric terms in `t`,
for every depth `k ≥ {k0}` and every horizon `N`; the derived numbers `der` are computed from the chosen
ones (`ClosedData.derive`).
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

/-- The derived numbers: the contractions from the tables' bounds, the growth blocks, each settlement
term's constant and rate, the band's terms, and the short form's rates. -/
def der : ClosedDerived := par.derive F F.S.weakest dat Tq

theorem derNb : der.nb = {q_['nb']} ∧ der.nb0 = {q_['nb0']} := by decide +kernel

theorem mainOK : F.mainChk F.S.weakest par.κ der.lp der.lpi dat = true := by decide +kernel

theorem closedOK : FamCfg.closedChk F F.S.weakest dat Tq par der = true := by decide +kernel

/-- **Finality in closed form.** f = 1/30, Δ = {D} slots, any depth `k ≥ {k0}` and any horizon `N`.
Under the execution model (`Model`), if the genesis estimate is the genesis stake, the adversary
holds at most {float(beta)} of the participating stake, the canonical chain counts at least
{float(1 - T['mu'])} of each window's honestly won slots, stake drifts by at most a factor
{float(T['rho'])} per epoch and honest online stake is at least {T['hmin']}, a finality violation has
probability at most `par.epsC der N k`. -/
theorem finality_closed {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} {hyps} :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal (par.epsC der N k) :=
  FamCfg.finality_closed_gen F par der mainOK famOK dOK rfl idxOK rfl Tq closedOK
    (fun k hk => by simp only [par, derNb.1, derNb.2, F, pot] at hk ⊢; omega) (fun k hk => by simp only [par] at hk ⊢; omega)
    (fun k hk => by simp only [par, F, pot] at hk ⊢; omega) E hc hk hΔ es hM hN hG
    (fun ω => by simpa [Tq] using hS ω) (fun ω => by simpa [Tq] using hQ ω) (fun ω => by simpa [par] using hD ω)
    (fun ω => by simpa [par] using hH ω)

/-- **Finality in closed form, short**: with `t = k / {m_}` and `Ne = N / (300 k) + 2` epochs, a
finality violation has probability at most
`(N + {g} t + {G + 2}) · ({float(C['A1']):.2g} + {float(q_['As']):.4g} · {float(q_['qs']):.6f}ᵗ) + Ne · {float(q_['Ab']):.4g} · {float(q_['qb']):.6f}ᵗ`:
settlement at rate {float(q_['qs']):.4f} per {m_} blocks of depth, the estimate's band at rate {float(q_['qb']):.4f}. -/
theorem finality_closed_short {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} {hyps} :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal (par.epsShort der N k) :=
  (finality_closed E hc hk hΔ es hM hN hG hS hQ hD hH).trans
    (ENNReal.ofReal_le_ofReal (FamCfg.epsC_le_short par der closedOK N hk))

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
    return q_
