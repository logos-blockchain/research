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
import os, math
from fractions import Fraction as Fr
from certnum import rup, rdn
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


def fam_fields(K):
    return [("η", "Tq.η", "the lottery threshold's approximation error"),
            ("ζ", "Tq.ζ", "the largest note's share of the stake"),
            ("β", "Tq.β", "the adversary's share of the participating stake"),
            ("d", "13", "significant digits of the bands' fields"),
            ("dy", "12", "significant digits of the adversarial exponent's bound"),
            ("K", str(K), "the members"),
            ("ys", f"eval% geomYs Tq.ylo Tq.Yh {K} 12", "the breakpoints: [ylo, Yh] split geometrically")]


def tq_args(T):
    """`TBandQ.ofDrift`'s arguments beyond the configuration, each with a line comment"""
    return [(qQ(T['mu']), "μ: the canonical chain's loss of honestly won slots (`ChainQuality`)"),
            (qQ(T['beta']), "β: the adversary's share of the participating stake"),
            (qQ(T['delta']), "δ: the estimate's relative band per epoch"),
            ("(1 / 10 ^ 70)", "η: the lottery threshold's approximation error"),
            ("(1 / 10 ^ 16)", "ζ: the largest note's share of the stake"),
            ("par.ρ par.Hmin", "the stake drift and the least honest stake"),
            ("8 30", "8 digits, 30 rounds")]


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


# ---- the lesser settlement parameters, by rule (`SpecData.derive`)

EPS = Fr(1, 100)     # each lesser term at most this share of the main terms


def least(P, lo, hi):
    """`leastTrue`: the least n in [lo, hi] with P n, by binary search"""
    while lo < hi:
        mid = (lo + hi) // 2
        if P(mid): hi = mid
        else: lo = mid + 1
    return lo


def tilt(d, n, m, p):
    """`tilt`: the best tilt (m + 1)(1 - p) / ((n - m - 1) p), rounded down to d digits"""
    den = (n - m - 1) * p
    return rdn((m + 1) * (1 - p) / den, d) if den != 0 else Fr(0)


def argmin(f, lo, m):
    """`argmin`: the first n in [lo, lo + m) minimizing f"""
    best = lo
    for i in range(m):
        if f(lo + i) < f(best): best = lo + i
    return best


def tmin(f, lo, hi, n=64):
    """`tmin`: a minimizer of f on [lo, hi] by ternary search"""
    for _ in range(n):
        if hi <= lo + 2: return argmin(f, lo, hi + 1 - lo)
        m1, m2 = lo + (hi - lo) // 3, hi - (hi - lo) // 3
        if f(m1) <= f(m2): hi = m2
        else: lo = m1
    return lo


def nb_spec(D, G, Tg): return (EL - PERIOD - D - 3 - G + D) // (Tg + D)


def spec_rules(cfg, B, e, lr, b, lpi, eps):
    """`SpecData.derive`'s rules: `Lw` and `J` minimizing the main terms, the window at its best tilt `x`; `G'`, `G`, `r` each the least making
    its term at most `eps` times these; `T` minimizing the slow-growth term at its best tilt `yy`"""
    D, k, N = cfg['Delta'], cfg['k'], cfg['N']
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    up = lambda base, n: powq.pow_up(14, base, n)
    dn = lambda base, n: powq.pow_dn(14, base, n)
    stat = 1 + (b - 1) / (1 - lr)
    span = lambda Lw, J: (N + 1) * up(e[17], J + 1) / dn(tau, Lw + 1)
    fail = lambda J: (N + 1) * up(lpi, J) * e[2] * stat
    x_of = lambda Lw: max(Fr(1), tilt(5, Lw, k, 1 - B['elo']))
    win = lambda Lw: (N + 1) * up(1 + (x_of(Lw) - 1) * (1 - B['elo']), Lw) / dn(x_of(Lw), k + 1)
    J_of = lambda Lw: tmin(lambda j: span(Lw, j) + fail(j), 1, 2 ** 15)
    Lw = tmin(lambda L: span(L, J_of(L)) + fail(J_of(L)) + win(L), k + 2, math.floor((k + 1) / (1 - B['elo'])))
    J = J_of(Lw)
    m0 = span(Lw, J) + fail(J) + win(Lw)
    Gp = least(lambda n: (N + 1) * up(1 - B['hlo'], n) <= eps * m0, 1, 2 ** 14)
    mG = least(lambda n: (N + 1) * up(1 - (1 - B['hhi']) ** D, n) <= eps * m0, 1, 2 ** 10)
    G = max(2 * D, D * mG + D)
    r = least(lambda n: (N + G + 1) * stat / dn(c, n + 1) <= eps * m0, 0, 2 ** 12)
    def yy_of(Tg):
        v = tilt(4, nb_spec(D, G, Tg), k + r - 1, 1 - (1 - B['hlo']) ** Tg)
        return v if 0 < v < 1 else Fr(1)
    grow = lambda Tg: up(1 + (yy_of(Tg) - 1) * (1 - (1 - B['hlo']) ** Tg), nb_spec(D, G, Tg)) / dn(yy_of(Tg), k + r)
    Tg = argmin(grow, 1, 64)
    return dict(Lw=Lw, J=J, x=x_of(Lw), G=G, Gp=Gp, r=r, T=Tg, yy=yy_of(Tg))


# ---- the files

def dec_up(x, sig):
    """`x > 0` rounded up to `sig` significant digits, and as a Lean literal (scientific below 10⁻³)."""
    x = Fr(x)
    e = math.floor(math.log10(x)) - sig + 1
    up = lambda e: -((-x) // (Fr(10) ** e))
    while up(e) >= 10 ** sig: e += 1
    while up(e - 1) < 10 ** sig: e -= 1
    n = up(e)
    d = str(n).rstrip('0')
    e10 = e + len(str(n)) - 1
    if e10 < -3:
        lit = d[0] + ('.' + d[1:] if d[1:] else '') + f"e{e10}"
    else:
        v = Fr(n) * Fr(10) ** e
        k = max(0, -e)
        lit = f"{v.numerator * 10 ** k // v.denominator:0{k + 1}d}"
        lit = (lit[:-k] + '.' + lit[-k:]).rstrip('0').rstrip('.') if k else lit
    return Fr(n) * Fr(10) ** e, lit


def imports(lines): return "module\n\n" + "".join(lines)




def write_params(cfg, fam, T, par_type, par_fields, sub, ns, name, closed=False):
    """`Params.lean`: every number the search chose, each with a line comment; the estimate's band and
    the breakpoints by rule"""
    D = cfg['Delta']; K = len(fam)
    c, z, s, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'd', 'tau'])
    pot = [("Δ", str(D), "the network delay, in slots"),
           ("c", qQ(c), "the potential's base for the reach"),
           ("z", qQ(z), "the potential's base for the margin, when cold"),
           ("s", qQ(s), "the weight of the cold potential's first term"),
           ("d", qQ(d), "the base of the cold potential's second term"),
           ("τ", qQ(tau), "the span term's base per slot")]
    lib = "CertClosed" if closed else "CertSpec"
    args = tq_args(T)
    w = max(len(v) for v, _ in args)
    tq = "".join(f"    {v.ljust(w)}  -- {cm}\n" for v, cm in args)
    txt = (imports([f"public import Cryptarchia.Prob.{lib}\n", f"meta import Cryptarchia.Prob.{lib}\n"]) + f"""
/-!
# {name}: the chosen numbers

Generated by `tools/certgen/emitF.py`. Every number of the certificate that a search chose, and the
rules for the estimate's band and the band family's breakpoints; Lean computes the rest (`Data.lean`,
the main file) and the kernel checks it.
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

/-- The potential's parameters. -/
def pot : PotCfg where
{record(pot)}
/-- The certificate's other chosen numbers. -/
def par : {par_type} where
{record(par_fields)}
/-- The estimate's band `λV/D ∈ [ℓlo, ℓhi]`: the least that the stake drift allows
(`TBandQ.ofDrift`). -/
def Tq : TBandQ :=
  eval% TBandQ.ofDrift {"(Config.specK par.k0)" if closed else "Config.spec"}
{tq}
/-- The band family: {K} members over the estimate's band. -/
def S : FamSpec where
{record(fam_fields(K))}
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
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    ns = f"Cryptarchia.Prob.Certs.{name}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    for old in os.listdir(sub):
        if old.endswith('.lean'): os.remove(f"{sub}/{old}")
    dats, e, lr, b, lp, lpi = check_all(cfg, T, fam, B, P)
    rl = spec_rules(cfg, B, e, lr, b, lpi, EPS)
    Lw, J, x, G, Gp, r, Tg, yy = (rl[v] for v in ['Lw', 'J', 'x', 'G', 'Gp', 'r', 'T', 'yy'])
    assert D + 1 <= G
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
        ("ε", qQ(EPS), "each lesser term (long phases, long empty runs, large reach) at most this share of the main ones"),
        ("ρ", qQ(T['rho']), "the stake drift per epoch (`StakeDrift`)"),
        ("Hmin", qQ(T['hmin']), "the least honest online stake (`MinStake`)")]
    write_params(cfg, fam, T, "SpecData", spec_fields, sub, ns, name)
    write_data(sub, ns, name)
    txt = (imports([f"public import {ns}.Data\n", f"meta import {ns}.Data\n"]) + f"""
/-!
# Multi-epoch finality certificate: β = {beta}, Δ = {D}, k = {k}, {K} members

Generated by `tools/certgen/emitF.py`. The specification's parameters (f = 1/30, k = {k}) are
`Config.spec`'s. The certificate is the data below; Lean computes the rest and the kernel checks it
(`CertGen.lean`, `CertSpec.lean`):

- the chosen numbers: the potential's parameters and the other numbers `par`, with the estimate's
  band and the band family by rule (`Params.lean`);
- each phase index's tables (`Data.lean`);
- the derived numbers `der` (`SpecData.derive`): the contractions, the settlement parameters by rule,
  and the bounds on settlement, on leaving the band in one epoch and on a finality violation;
- the checks of the potential (`mainOK`) and of every numeric condition (`finOK`).
-/

{SEC}
namespace {ns}

open Cryptarchia Cryptarchia.Prob

universe u

{HEAD}
/-- The phase indices' data. -/
def dat : Fin 19 → IdxData := ![{", ".join(f"dat{i}" for i in range(19))}]

theorem idxOK : ∀ i : Fin 19, F.idxChk i (dat i) = true := by
  intro i; fin_cases i
  exacts [{", ".join(f"chk{i}" for i in range(19))}]

/-- The derived numbers (`SpecData.derive`), computed at elaboration time: the contractions from the
tables' bounds; the settlement parameters by their rules (Lw = {Lw}, J = {J}, G = {G}, G' = {Gp},
r = {r}, T = {Tg}) and tilts; the slots and epochs covered; and the bounds on settlement
({float(tgt):.2e}), on leaving the band in one epoch ({float(bx):.3e}) and on a finality violation
({float(fin):.2e}). The kernel checks every condition on them (`mainOK`, `finOK`). -/
def der : SpecDerived := eval% par.derive F F.S.weakest dat Tq

theorem derNe : der.Ne = {Ne} := by decide +kernel

theorem derFin : der.fin = {qQ(fin)} := by decide +kernel

theorem mainOK : F.mainChk F.S.weakest par.κ der.lp der.lpi dat = true := by decide +kernel

theorem finOK : FamCfg.finChkSpec F F.S.weakest dat Tq par der = true := by decide +kernel

/-- **Finality, certified** (`Claim.Finality`): f = 1/30, k = {k}, Δ = {D} slots, executions up to
slot {N}; the adversary holds at most {float(beta)} of the participating stake, stakes are at most
10³⁰, the canonical chain counts at least {float(1 - T['mu'])} of each window's honestly won slots,
stake drifts by at most a factor {float(T['rho'])} per epoch and honest online stake is at least
{T['hmin']}; a finality violation has probability at most {float(fin):.2e}. -/
theorem finality :
    Claim.Finality.{{u}} (k := {k}) (Δ := {D}) (N := {N}) (β := {q(beta)}) (Smax := 10 ^ 30) (μ := {q(T['mu'])})
      (ρ := {q(T['rho'])}) (Hmin := {q(T['hmin'])}) (ε := {q(fin)}) := by
  intro Ω _ μ _ O E es hM hc hΔ hN hG hS hQ hD hH
  have hT : Tq.β = {qQ(beta)} ∧ Tq.ζ = 1 / 10 ^ 16 ∧ Tq.μ = {qQ(T['mu'])} := by decide +kernel
  have h := FamCfg.finality_spec F par der mainOK famOK dOK rfl idxOK rfl Tq finOK (by rw [hc]; rfl) hΔ es hM hN
    (Smax := 10 ^ 30) (by rw [hT.2.1]; decide +kernel) (by rw [derNe]; decide +kernel) hG
    (fun ω => by rw [hT.1]; simpa using hS ω) (fun ω => by rw [hT.2.2]; simpa [par] using hQ ω)
    (fun ω => by simpa [par] using hD ω) (fun ω => by simpa [par] using hH ω)
  rw [derFin] at h
  simpa using h

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
    return fin, tgt, bx


# ---- closed-form certificates (`CertClosed.lean`)

def closed_rules(cfg, B, e, lr, b, lpi, cl):
    """`ClosedData.derive`'s rules, at the horizon `N1` and depth `k1`: `w`, `j` minimizing the main terms
    (the window at its best tilt `x`); `g`, `ρr` each the least making its term at most `ε` times these,
    and `G` against them decayed to `t1 + t1 / 4`; `T` minimizing the slow-growth rate at its best tilt `yy`"""
    D, m, N1, eps = cfg['Delta'], cl['m'], cl['N1'], cl['eps']
    t1 = cl['k1'] // m
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    up = lambda base, n: powq.pow_up(14, base, n)
    dn = lambda base, n: powq.pow_dn(14, base, n)
    stat = 1 + (b - 1) / (1 - lr)
    at1 = lambda A, r: (N1 + 1) * A * up(r, t1)
    x_of = lambda w: max(Fr(1), tilt(5, w, m - 1, 1 - B['elo']))
    span = lambda w, j: at1(e[17] / tau, up(e[17], j) / dn(tau, w))
    fail = lambda j: at1(e[2] * stat, up(lpi, j))
    win = lambda w: at1(1 / x_of(w), up(1 + (x_of(w) - 1) * (1 - B['elo']), w) / dn(x_of(w), m))
    j_of = lambda w: tmin(lambda j: span(w, j) + fail(j), 1, 2 ** 12)
    w = tmin(lambda w: span(w, j_of(w)) + fail(j_of(w)) + win(w), m + 1, math.floor(Fr(m) / (1 - B['elo'])))
    j = j_of(w)
    m0 = span(w, j) + fail(j) + win(w)
    m2 = m0 * up(up(e[17], j) / dn(tau, w), t1 // 4)
    mG = least(lambda n: (N1 + 1) * up(1 - (1 - B['hhi']) ** D, n) <= eps * m2, 1, 2 ** 10)
    G = max(2 * D, D * mG + D)
    g = least(lambda n: at1(Fr(1), up(1 - B['hlo'], n)) <= eps * m0, 1, 2 ** 10)
    rho = least(lambda n: at1(stat / c, 1 / dn(c, n)) <= eps * m0, 0, 2 ** 8)
    def yy_of(Tg):
        v = tilt(4, 120 * m // (Tg + D), m + rho - 1, 1 - (1 - B['hlo']) ** Tg)
        return v if 0 < v < 1 else Fr(1)
    rate = lambda Tg: up(1 + (yy_of(Tg) - 1) * (1 - (1 - B['hlo']) ** Tg), 120 * m // (Tg + D)) / dn(yy_of(Tg), m + rho)
    Tg = argmin(rate, 1, 64)
    return dict(G=G, g=g, j=j, w=w, rho=rho, Tg=Tg, x=x_of(w), yy=yy_of(Tg))


def closed_derive(cfg, T, B, dats, lp, lpi, cl):
    """`ClosedData.derive`: the closed form's derived numbers, from the tables' bounds"""
    import emitC
    from certnum import rdn
    D = cfg['Delta']; m = cl['m']
    e, lr, b = derived(dats)
    cl = dict(cl, **closed_rules(cfg, B, e, lr, b, lpi, cl))
    G, g, j, w, rho, Tg, x, yy, k0 = cl['G'], cl['g'], cl['j'], cl['w'], cl['rho'], cl['Tg'], cl['x'], cl['yy'], cl['k0']
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
    return dict(cl=cl, lp=lp, lpi=lpi, nb=nb, nb0=nb0, C=C, Cs=Cs, Qs=Qs, t0=t0, qs=qs, As=As, qb=qb, Ab=Ab)


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
    m_ = cl['m']
    q_ = closed_derive(cfg, T, B, dats, lp, lpi, cl)
    cl = q_['cl']
    C = q_['C']
    beta = T['beta']
    par_f = [("κ", qQ(kap), POT[0][1]),
        ("m", m_, "the depth per step of t = k / m"),
        ("k0", cl['k0'], "the least depth"),
        ("N1", cl['N1'], "the horizon the settlement parameters are fitted at"),
        ("k1", cl['k1'], "and the depth"),
        ("ε", qQ(cl['eps']), "each lesser term (long phases, long empty runs, large reach) at most this share of the main ones"),
        ("ρ", qQ(T['rho']), "the stake drift per epoch (`StakeDrift`)"),
        ("Hmin", qQ(T['hmin']), "the least honest online stake (`MinStake`)")]
    write_params(cfg, fam, T, "ClosedData", par_f, sub, ns, name, closed=True)
    write_data(sub, ns, name)
    k0, g, G = cl['k0'], cl['g'], cl['G']
    A1u, A1s = dec_up(C['A1'], 2)
    Asu, Ass = dec_up(q_['As'], 4)
    qsu, qss = dec_up(q_['qs'], 6)
    Abu, Abs = dec_up(q_['Ab'], 4)
    qbu, qbs = dec_up(q_['qb'], 6)
    claim = (f"(β := {q(beta)}) (Smax := 10 ^ 30) (μ := {q(T['mu'])})\n      (ρ := {q(T['rho'])}) "
             f"(Hmin := {q(T['hmin'])})")
    txt = (imports([f"public import {ns}.Data\n", f"meta import {ns}.Data\n", "public import Cryptarchia.Prob.CertClosed\n"]) + f"""
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

universe u

{HEAD}
/-- The phase indices' data. -/
def dat : Fin 19 → IdxData := ![{", ".join(f"dat{i}" for i in range(19))}]

theorem idxOK : ∀ i : Fin 19, F.idxChk i (dat i) = true := by
  intro i; fin_cases i
  exacts [{", ".join(f"chk{i}" for i in range(19))}]

/-- The derived numbers (`ClosedData.derive`), computed at elaboration time: the contractions from the
tables' bounds, the settlement parameters by their rules (G = {cl['G']}, and per t: g = {cl['g']}, j = {cl['j']},
w = {cl['w']}, ρr = {cl['rho']}; T = {cl['Tg']}) and the tilts, the growth blocks, each settlement term's constant
and rate, the band's terms, and the short form's rates. The kernel checks every condition on them (`closedOK`). -/
def der : ClosedDerived := eval% par.derive F F.S.weakest dat Tq

theorem derLen : der.nb = {q_['nb']} ∧ der.nb0 = {q_['nb0']} ∧ der.G = {cl['G']} ∧ der.g = {cl['g']} ∧ der.w = {cl['w']} ∧
    der.T = {cl['Tg']} := by decide +kernel

theorem mainOK : F.mainChk F.S.weakest par.κ der.lp der.lpi dat = true := by decide +kernel

theorem closedOK : FamCfg.closedChk F F.S.weakest dat Tq par der = true := by decide +kernel

theorem hTq : Tq.β = {qQ(beta)} ∧ Tq.ζ = 1 / 10 ^ 16 ∧ Tq.μ = {qQ(T['mu'])} := by decide +kernel

/-- **Finality in closed form** (`Claim.Finality`): f = 1/30, Δ = {D} slots, any depth `k ≥ {k0}` and
any horizon `N`; the adversary holds at most {float(beta)} of the participating stake, stakes are at
most 10³⁰, the canonical chain counts at least {float(1 - T['mu'])} of each window's honestly won
slots, stake drifts by at most a factor {float(T['rho'])} per epoch and honest online stake is at
least {T['hmin']}; a finality violation has probability at most `par.epsC der N k`. -/
theorem finality_closed (k N : ℕ) (hk : {k0} ≤ k) :
    Claim.Finality.{{u}} (k := k) (Δ := {D}) (N := N) {claim} (ε := par.epsC der N k) := by
  intro Ω _ μ _ O E es hM hc hΔ hN hG hS hQ hD hH
  exact FamCfg.finality_closed_gen F par der mainOK famOK dOK rfl idxOK rfl Tq closedOK
    (fun k hk => by obtain ⟨h1, h2, h3, -, -, h6⟩ := derLen; simp only [par, h1, h2, h3, h6, F, pot] at hk ⊢; omega)
    (fun k hk => by obtain ⟨-, -, h3, -, h5, -⟩ := derLen; simp only [par, h3, h5] at hk ⊢; omega)
    (fun k hk => by obtain ⟨-, -, h3, h4, -, -⟩ := derLen; simp only [par, h3, h4, F, pot] at hk ⊢; omega) E hc hk hΔ es hM hN
    (Smax := 10 ^ 30) (by rw [hTq.2.1]; decide +kernel) hG
    (fun ω => by rw [hTq.1]; simpa using hS ω) (fun ω => by rw [hTq.2.2]; simpa using hQ ω)
    (fun ω => by simpa [par] using hD ω) (fun ω => by simpa [par] using hH ω)

/-- **Finality in closed form, short** (`Claim.Finality`): with `t = k / {m_}` and `Ne = N / (300 k) + 2`
epochs, a finality violation has probability at most
`(N + {g} t + {G + 2}) · ({A1s} + {Ass} · {qss}ᵗ) + Ne · {Abs} · {qbs}ᵗ`: settlement at rate {qss} per {m_}
blocks of depth, the estimate's band at rate {qbs}. -/
theorem finality_closed_short (k N : ℕ) (hk : {k0} ≤ k) :
    Claim.Finality.{{u}} (k := k) (Δ := {D}) (N := N) {claim}
      (ε := ((N : ℝ) + {g} * ((k / {m_} : ℕ) : ℝ) + {G + 2}) * ({A1s} + {Ass} * {qss} ^ (k / {m_})) +
        ((N / (300 * k) + 2 : ℕ) : ℝ) * ({Abs} * {qbs} ^ (k / {m_}))) := by
  refine (finality_closed k N hk).mono ((FamCfg.epsC_le_short par der closedOK N hk).trans ?_)
  obtain ⟨-, -, hG, hg, -, -⟩ := derLen
  have hv : der.A1 ≤ {qQ(A1u)} ∧ der.As ≤ {qQ(Asu)} ∧ der.qs ≤ {qQ(qsu)} ∧ der.Ab ≤ {qQ(Abu)} ∧
      der.qb ≤ {qQ(qbu)} ∧ 0 ≤ der.As ∧ 0 ≤ der.qs ∧ 0 ≤ der.Ab ∧ 0 ≤ der.qb := by decide +kernel
  obtain ⟨h1, h2, h3, h4, h5, h6, h7, h8, h9⟩ := hv
  have c : ∀ {{x y : ℚ}}, x ≤ y → (x : ℝ) ≤ y := fun h => by exact_mod_cast h
  have c0 : ∀ {{x : ℚ}}, 0 ≤ x → (0 : ℝ) ≤ x := fun h => by exact_mod_cast h
  set t := k / {m_}
  have hA : (der.A1 : ℝ) + der.As * (der.qs : ℝ) ^ t ≤ {A1s} + {Ass} * {qss} ^ t := by
    have := c h1; have := c h2; have := c h3; norm_num at *
    gcongr
  have hB : (der.Ab : ℝ) * (der.qb : ℝ) ^ t ≤ {Abs} * {qbs} ^ t := by
    have := c h4; have := c h5; norm_num at *
    gcongr
  unfold ClosedData.epsShort
  simp only [par, hG, hg] at *
  push_cast
  gcongr

end {ns}
""")
    open(f"{out_dir}/{name}.lean", "w").write(txt)
    return q_
