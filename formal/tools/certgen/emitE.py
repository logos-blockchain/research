"""Emit a multi-epoch certificate (`Cert2E`, Prob/Final2E.lean) as Lean files.

Layout (`formal/Cryptarchia/Prob/Certs/<name>/`):
* `Fam.lean`   the members' bands `f k`, the weakest band `B`, the family `fam`;
* `I<i>.lean`  index i's tables and their proofs (switching tables for 0, 1, 2, 17;
               one-switch tables for the others);
* `<name>.lean` (one level up) the potential `P`, the certificate `C`, the numbers
               (`eps_le`) and the certified theorem.
Usage: python3 emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [all|main|emit] [MU]
(`main` and `emit` reuse the saved plan `res_<NAME>.pkl`: `main` writes the main file,
`emit` every file.)
"""
import sys, os, json, math
from fractions import Fraction as Fr
from gen import lean_q as q, chain
from certnum import rup, rdn, flog10
from certE import SIDX, EIDX, EL, PERIOD, tband_derived
import planE

def qQ(x):
    x = Fr(x)
    if x.denominator == 1: return f"({x.numerator} : ℚ)"
    return f"({x.numerator} / {x.denominator} : ℚ)"


BANDKEYS = ['hhi', 'hlo', 'amax', 'hahi', 'slo', 'hnlo', 'elo', 'alo', 'halo']
WEAKKEYS = ['hhi', 'hlo', 'amax', 'hahi', 'slo', 'hnlo', 'elo', 'alo', 'halo']
HEAD = "set_option maxRecDepth 100000\nset_option maxHeartbeats 0\n"
SEC = "@[expose] public section\n"
# Imports, as `lake shake` computes them. `EXT` are the modules whose `norm_num` and
# `simp` extensions the proofs use; every generated file imports them. After changing the
# proofs a generator emits, rerun `lake shake CryptarchiaCerts` and update these lists.
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
FAM_IMPORTS = """public import Cryptarchia.Prob.AutoQ
public import Cryptarchia.Prob.Stake
"""
MAIN_IMPORTS = """import Cryptarchia.Prob.Cert
import Cryptarchia.Prob.ExpBound
import Cryptarchia.Prob.FinalInd
public import Cryptarchia.Prob.Pick
public import Cryptarchia.Prob.Final3E
import Mathlib.Algebra.Order.Ring.Star
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.ReduceModChar
"""


def band_def(name, B, doc):
    return (f"/-- {doc} -/\nnoncomputable def {name} : Band where\n" +
            "".join(f"  {k} := {q(B[k])}\n" for k in BANDKEYS))


OKFIELDS = ['ylo0', 'le', 'yhi', 'ahi0', 'ahi', 'eLoH', 'eLoA', 'eHi', 'pos1', 'hhi', 'hlo', 'amax', 'amax1', 'slo',
            'hnlo', 'elo']
QKEYS = ['hhi', 'hlo', 'amax', 'hahi', 'alo', 'halo']


def bandq_def(k, B):
    """The member's `slot4` fields over ℚ, and their agreement with the band."""
    return (f"def f{k}Q : BandQ := ⟨" + ", ".join(qQ(B[kk]) for kk in QKEYS) + "⟩\n\n"
            f"theorem f{k}A : f{k}Q.Agrees f{k} :=\n  ⟨" +
            ", ".join(f"by norm_num [f{k}, f{k}Q]" for _ in QKEYS) + "⟩\n")


def vdef(name, V, D):
    """A table over ℚ (`{name}Q`, listed by (q, a, u)) and its cast to ℝ (`{name}`)."""
    vals = [qQ(V[(qq, a, u)]) for qq in range(D) for a in range(3) for u in (False, True)]
    s = f"def {name}Q : ℕ → Fin 3 → Bool → ℚ := tabL\n  [" + ",\n   ".join(vals) + "]\n\n"
    s += f"noncomputable def {name} : ℕ → Fin 3 → Bool → ℝ := castT {name}Q\n"
    return s


def kmatch(name, typ, items, default):
    s = f"noncomputable def {name} : {typ} := fun k =>\n  match k.val with\n"
    for j, it in enumerate(items):
        s += f"  | {j} => {it}\n" if j < len(items) - 1 else f"  | _ => {it}\n"
    return s


def emit_all(cfg, T, fam, B, P, Ts, name, out_dir, target):
    D = cfg['Delta']; K = len(fam)
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    C_, Z_, S_, K_, Dd_, TAU_ = (q(v) for v in (c, z, s, kap, d, tau))
    args = f"{C_} {Z_} {S_} {Dd_} {TAU_}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    ns = f"Cryptarchia.Prob.Certs.{name}"
    pre = f"namespace {ns}\n\nopen Cryptarchia Cryptarchia.Prob\n\n{HEAD}\n"
    # ---- Fam.lean
    L = ["module\n\n" + FAM_IMPORTS + EXT,
         f"/-!\n# {name}: the band family\n\nGenerated by `tools/certgen/emitE.py`.\n-/\n", SEC, pre]
    for k, m in enumerate(fam):
        L.append(band_def(f"f{k}", m['B'], f"Member {k}: honest exponent in [{float(m['ylo']):.6f}, {float(m['yhi']):.6f}], adversary ≤ {float(m['ahi']):.6f}."))
    L.append(band_def("B", B, "The weakest band: weaker than every member."))
    L.append(kmatch("fam", f"Fin {K} → Band", [f"f{k}" for k in range(K)], None))
    for k in range(K):
        L.append(f"theorem weak{k} : B.Weaker f{k} :=\n  ⟨" + ", ".join(f"by norm_num [B, f{k}]" for _ in WEAKKEYS) + "⟩\n")
        L.append(f"theorem prod{k} : f{k}.Prod :=\n  ⟨" + ", ".join(f"by norm_num [f{k}]" for _ in range(5)) + "⟩\n")
        L.append(f"theorem patm{k} : {q(P['patk'][k])} ≤ f{k}.slo * f{k}.elo ^ {D} := by norm_num [f{k}]\n")
        L.append(f"theorem elo{k} : 0 ≤ f{k}.elo := by norm_num [f{k}]\n")
        L.append(bandq_def(k, fam[k]['B']))
        m = fam[k]
        L.append(f"/-- Member {k} with its exponent range. -/\nnoncomputable def m{k} : Member := ⟨{q(m['ylo'])}, {q(m['yhi'])}, {q(m['ahi'])}, f{k}⟩\n")
        L.append(f"theorem ok{k} : m{k}.OK (1 / 10 ^ 70) (1 / 10 ^ 16) where\n" +
                 "".join(f"  {fl} := by norm_num [m{k}, f{k}, errLo, errHi, Elo, Ehi]\n" for fl in OKFIELDS))
    L.append(kmatch("mem", f"Fin {K} → Member", [f"m{k}" for k in range(K)], None))
    L.append(f"end {ns}\n")
    open(f"{sub}/Fam.lean", "w").write("\n".join(L))
    argsQ = " ".join(qQ(v) for v in (c, z, s, d, tau))
    dk = "(by decide +kernel)"
    def bnd(k, i, tab, e):
        return (f"  rw [xgQ{i}]\n  exact autoBound_le_ofQ f{k}A (v := {tab}Q) (e := {qQ(e)}) (by norm_num) {dk}\n")
    # ---- I<i>.lean: one file per index. The kernel checks a file's declarations one at
    # a time, so separate files are what lets the checks run in parallel. Every check is
    # a rational computation (`AutoQ.lean`), evaluated by the kernel.
    for old in os.listdir(sub):
        if old.endswith('.lean') and old != 'Fam.lean': os.remove(f"{sub}/{old}")
    for i in range(19):
        L = ["module\n\npublic import " + ns + ".Fam\n" + EXT, f"/-! # {name}: tables for index {i} -/\n", SEC, pre]
        xgs = f"(xg {args} {i}).1 (xg {args} {i}).2.1 (xg {args} {i}).2.2"
        L.append(f"theorem xgQ{i} : xg {args} {i} = castX (xgNQ {argsQ} {i}) :=\n"
                 f"  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) {i}\n")
        if i in SIDX:
            L.append(vdef(f"vs{i}", P['vs'][i], D))
            for k in range(K):
                L.append(f"theorem solS{i}_{k} : AutoSol f{k} {D} {xgs} vs{i} := by\n"
                         f"  rw [xgQ{i}]\n  exact autoSol_ofQ f{k}A (v := vs{i}Q) {dk}\n")
                L.append(f"theorem heS{i}_{k} : autoBound f{k} {xgs} vs{i} ≤ {q(P['eS'][i][k])} := by\n" +
                         bnd(k, i, f"vs{i}", P['eS'][i][k]))
        if i in EIDX:
            L.append(vdef(f"vmax{i}", P['vmax'][i], D))
            for k in range(K):
                L.append(vdef(f"post{i}_{k}", P['post'][i][k], D))
                L.append(vdef(f"pre{i}_{k}", P['pre'][i][k], D))
                L.append(f"theorem postS{i}_{k} : AutoSol f{k} {D} {xgs} post{i}_{k} := by\n"
                         f"  rw [xgQ{i}]\n  exact autoSol_ofQ f{k}A (v := post{i}_{k}Q) {dk}\n")
                L.append(f"theorem maxp{i}_{k} : ∀ q < {D}, ∀ a u, post{i}_{k} q a u ≤ vmax{i} q a u :=\n"
                         f"  leTab_ofQ (v := post{i}_{k}Q) (w := vmax{i}Q) {dk}\n")
                L.append(f"theorem preS{i}_{k} : PreSol f{k} {D} {xgs} vmax{i} pre{i}_{k} := by\n"
                         f"  rw [xgQ{i}]\n  exact preSol_ofQ f{k}A (vmax := vmax{i}Q) (vpre := pre{i}_{k}Q) {dk}\n")
                L.append(f"theorem heE{i}_{k} : autoBound f{k} {xgs} pre{i}_{k} ≤ {q(P['eE'][i][k])} := by\n" +
                         bnd(k, i, f"pre{i}_{k}", P['eE'][i][k]))
            L.append(kmatch(f"vpreI{i}", f"Fin {K} → ℕ → Fin 3 → Bool → ℝ", [f"pre{i}_{k}" for k in range(K)], None))
            L.append(kmatch(f"vpostI{i}", f"Fin {K} → ℕ → Fin 3 → Bool → ℝ", [f"post{i}_{k}" for k in range(K)], None))
            ks = lambda pfx: ", ".join(f"{pfx}{i}_{k}" for k in range(K))
            L.append(f"theorem solE{i} : AutoSolE fam {D} {xgs} vpreI{i} vpostI{i} vmax{i} :=\n"
                     f"  AutoSolE.mk' (fun k => by fin_cases k; exacts [{ks('postS')}])\n"
                     f"    (fun k => by fin_cases k; exacts [{ks('maxp')}])\n"
                     f"    (fun k => by fin_cases k; exacts [{ks('preS')}])\n")
            for k in range(K):
                L.append(f"theorem heIn{i}_{k} : autoBound f{k} {xgs} post{i}_{k} ≤ {q(P['eIn'][i][k])} := by\n" +
                         bnd(k, i, f"post{i}_{k}", P['eIn'][i][k]))
            e_i = P['e'][i]
            L.append(f"theorem heEall{i} : ∀ k, autoBound (fam k) {xgs} (vpreI{i} k) ≤ {q(e_i)} := fun k => by\n"
                     f"  fin_cases k\n  exacts [" + ", ".join(f"(heE{i}_{k}).trans (by norm_num)" for k in range(K)) + "]\n")
        L.append(f"end {ns}\n")
        open(f"{sub}/I{i}.lean", "w").write("\n".join(L))
    # ---- main file
    emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, args)


def emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, args):
    D = cfg['Delta']; K = len(fam); N = cfg['N']; k = cfg['k']
    G, Gp, J, Lw, r, Tg = cfg['G'], cfg['Gp'], cfg['J'], cfg['Lw'], cfg['r'], cfg['T']
    x, yy = Fr(cfg['x']), Fr(cfg['yy'])
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    C_, Z_, S_, K_, Dd_, TAU_ = (q(v) for v in (c, z, s, kap, d, tau))
    ns = f"Cryptarchia.Prob.Certs.{name}"
    es = P['e']; lp, lr, b = P['lp'], P['lr'], P['b']
    e = [q(v) for v in es]; LP = q(lp)
    ch, Ts2, aux = planE.terms(cfg, B, P)
    tot = sum(Ts2)
    assert tot <= target, (float(tot), float(target))
    M = N + G + Gp + D + 2
    nbD, nEp = aux['nbD'], aux['nEp']
    L = ["module\n\n" + "".join(f"public import {ns}.I{i}\n" for i in range(19)) +
         MAIN_IMPORTS + EXT]
    L.append(f"""/-!
# Multi-epoch finality certificate: β = {cfg['beta']}, Δ = {D}, k = {k}, {K} members

Generated by `tools/certgen/emitE.py`. Later epochs' states lie in one of
{K} members (honest exponent ranges covering `[(1-β)ℓlo, ℓhi]`, `ℓlo = {float(T['llo']):.6f}`,
`ℓhi = {float(T['lhi']):.6f}`, full withholding). The certificate bounds settlement up to
slot {N} by `{target}`, whatever member each epoch runs under.
-/
""")
    L.append(SEC)
    L.append(f"namespace {ns}\n\nopen Cryptarchia Cryptarchia.Prob\n\n{HEAD}\n")
    def fmatch(nm, typ, items, dflt):
        s = f"noncomputable def {nm} : {typ} := fun i =>\n  match i.val with\n"
        for (ii, it) in items: s += f"  | {ii} => {it}\n"
        s += f"  | _ => {dflt}\n"
        return s
    L.append(fmatch("vsF", "Fin 19 → ℕ → Fin 3 → Bool → ℝ", [(i, f"vs{i}") for i in SIDX], "fun _ _ _ => 0"))
    L.append(fmatch("vpreF", f"Fin 19 → Fin {K} → ℕ → Fin 3 → Bool → ℝ", [(i, f"vpreI{i}") for i in EIDX], "fun _ _ _ _ => 0"))
    L.append(fmatch("vpostF", f"Fin 19 → Fin {K} → ℕ → Fin 3 → Bool → ℝ", [(i, f"vpostI{i}") for i in EIDX], "fun _ _ _ _ => 0"))
    L.append(fmatch("vmaxF", "Fin 19 → ℕ → Fin 3 → Bool → ℝ", [(i, f"vmax{i}") for i in EIDX], "fun _ _ _ => 0"))
    L.append(fmatch("Ev", "Fin 19 → ℝ", [(i, e[i]) for i in range(18)], e[18]))
    s_ = f"noncomputable def EiK : Fin {K} → Fin 19 → ℝ := fun k i =>\n  match k.val, i.val with\n"
    for kk in range(K):
        for i in range(19):
            s_ += f"  | {kk}, {i} => {q(P['eik'][kk][i])}\n"
    s_ += "  | _, _ => 0\n"
    L.append(s_)
    L.append(kmatch("PatK", f"Fin {K} → ℝ", [q(P['patk'][kk]) for kk in range(K)], None))
    conds = {
        'he17': f"1 ≤ {e[17]}", 'hlr': f"{e[0]} ≤ {q(lr)}", 'hb': f"{e[1]} ≤ {q(b)}", 'w1': f"{e[0]} ≤ {LP}",
        'w0': f"{e[1]} - (1 - ({S_} + {K_}) * {Z_}⁻¹) * (B.slo * B.elo ^ {D}) ≤ {LP}",
        'm1r0': f"{S_} * ({e[3]} - {LP}) + {K_} * ({e[7]} - {LP}) ≤ 0",
        'm1r1': f"{S_} * {C_} * ({e[4]} - {LP}) + {K_} * {Dd_} * ({e[8]} - {LP}) ≤ 0",
        'm1r2': f"{S_} * {C_} ^ 2 * ({e[4]} - {LP}) + {K_} * {Dd_} ^ 2 * ({e[9]} - {LP}) ≤ 0",
        'm1r3a': f"{e[4]} ≤ {LP}",
        'm1r3': f"{S_} * {C_} ^ 3 * ({e[4]} - {LP}) + {K_} * {Dd_} ^ 3 * max ({e[10]} - {LP}) 0 + {K_} * {e[15]} ≤ 0",
        'm2r0': f"{S_} * ({e[5]} - {LP}) + {K_} * ({e[11]} - {LP}) ≤ 0",
        'm2r1': f"{S_} * {C_} * ({e[6]} - {LP}) + {K_} * {Dd_} * ({e[12]} - {LP}) ≤ 0",
        'm2r2': f"{S_} * {C_} ^ 2 * ({e[6]} - {LP}) + {K_} * {Dd_} ^ 2 * ({e[13]} - {LP}) ≤ 0",
        'm2r3a': f"{e[6]} ≤ {LP}",
        'm2r3': f"{S_} * {C_} ^ 3 * ({e[6]} - {LP}) + {K_} * {Dd_} ^ 3 * max ({e[14]} - {LP}) 0 + {K_} * {e[16]} ≤ 0"}
    cl = "".join(f"  {kk} := by show {v}; norm_num [B]\n" for kk, v in conds.items())
    L.append(f"""/-- The potential certificate. Its family is empty: the phase bounds come from the
multi-epoch tables of `C`. -/
noncomputable def P : Cert2 B {D} where
  c := {C_}
  z := {Z_}
  s := {S_}
  κ := {K_}
  d := {Dd_}
  τ := {TAU_}
  lp := {LP}
  lr := {q(lr)}
  b := {q(b)}
  Bs := []
  weak := fun B' hB' => by simp at hB'
  v := fun _ _ _ _ => 0
  e := Ev
  hc := by norm_num
  hz := by norm_num
  hs := by norm_num
  hκ := by norm_num
  hd0 := by norm_num
  hd1 := by norm_num
  hsz := by norm_num
  hτ := by norm_num
  hlp0 := by norm_num
  hlp := by norm_num
  hlr0 := by norm_num
  hlr1 := by norm_num
  hb1 := by norm_num
  helo := by norm_num [B]
  hΔ := by norm_num
  sol := fun i B' hB' => by simp at hB'
  he := fun i B' hB' => by simp at hB'
{cl}""")
    def kx(pfx, i): return ", ".join(f"{pfx}{i}_{kk}" for kk in range(K))
    solS = ", ".join(kx('solS', i) for i in SIDX)
    bnd = {0: 'P.lr', 1: 'P.b', 2: 'P.e 2', 17: 'P.e 17'}
    hes = ""
    for i in SIDX:
        hes += f"  heS{i} := fun k => by\n    fin_cases k\n    exacts [" + ", ".join(
            f"(heS{i}_{kk}).trans (by show _ ≤ {bnd[i]}; norm_num [P, Ev])" for kk in range(K)) + "]\n"
    bul_solE = "".join(f"    · exact solE{i}\n" if i in EIDX else ("    · exact absurd rfl h2\n" if i == 2 else "    · exact absurd rfl h17\n")
                       for i in range(19))
    bul_heE = "".join(f"    · exact heEall{i}\n" if i in EIDX else ("    · exact absurd rfl h2\n" if i == 2 else "    · exact absurd rfl h17\n")
                      for i in range(19))
    L.append(f"""/-- **The multi-epoch certificate.** -/
noncomputable def C (EL : ℕ) (hEL : EL = {EL}) : Cert2E B {D} fam EL {G} where
  P := P
  weakF := fun k => by fin_cases k; exacts [{", ".join(f"weak{kk}" for kk in range(K))}]
  hG := by norm_num
  hGEL := by rw [hEL]; norm_num
  vs := vsF
  solS := by
    intro i hi k
    rcases hi with rfl | rfl | rfl | rfl <;> fin_cases k
    exacts [{solS}]
{hes}  vpre := vpreF
  vpost := vpostF
  vmax := vmaxF
  solE := by
    intro i h2 h17
    fin_cases i
{bul_solE}  heE := by
    intro i h2 h17
    fin_cases i
{bul_heE}""")
    LPI = q(P['lpi'])
    for kk in range(K):
        ei = [q(v) for v in P['eik'][kk]]; PAT = q(P['patk'][kk])
        condsI = {
            'w1': f"{ei[0]} ≤ {LPI}",
            'w0': f"{ei[1]} - (1 - ({S_} + {K_}) * {Z_}⁻¹) * {PAT} ≤ {LPI}",
            'm1r0': f"{S_} * ({ei[3]} - {LPI}) + {K_} * ({ei[7]} - {LPI}) ≤ 0",
            'm1r1': f"{S_} * {C_} * ({ei[4]} - {LPI}) + {K_} * {Dd_} * ({ei[8]} - {LPI}) ≤ 0",
            'm1r2': f"{S_} * {C_} ^ 2 * ({ei[4]} - {LPI}) + {K_} * {Dd_} ^ 2 * ({ei[9]} - {LPI}) ≤ 0",
            'm1r3a': f"{ei[4]} ≤ {LPI}",
            'm1r3': f"{S_} * {C_} ^ 3 * ({ei[4]} - {LPI}) + {K_} * {Dd_} ^ 3 * max ({ei[10]} - {LPI}) 0 + {K_} * {ei[15]} ≤ 0",
            'm2r0': f"{S_} * ({ei[5]} - {LPI}) + {K_} * ({ei[11]} - {LPI}) ≤ 0",
            'm2r1': f"{S_} * {C_} * ({ei[6]} - {LPI}) + {K_} * {Dd_} * ({ei[12]} - {LPI}) ≤ 0",
            'm2r2': f"{S_} * {C_} ^ 2 * ({ei[6]} - {LPI}) + {K_} * {Dd_} ^ 2 * ({ei[13]} - {LPI}) ≤ 0",
            'm2r3a': f"{ei[6]} ≤ {LPI}",
            'm2r3': f"{S_} * {C_} ^ 3 * ({ei[6]} - {LPI}) + {K_} * {Dd_} ^ 3 * max ({ei[14]} - {LPI}) 0 + {K_} * {ei[16]} ≤ 0"}
        L.append(f"theorem cls{kk} : ClassOK P {LPI} (EiK {kk}) (PatK {kk}) where\n" +
                 "".join(f"  {f} := by show {v}; norm_num\n" for f, v in condsI.items()))
    def heIn_bullet(i):
        if i == 2: return "    · exact absurd rfl h2\n"
        if i == 17: return "    · exact absurd rfl h17\n"
        return f"    · exact fun k => by fin_cases k; exacts [{', '.join(f'heIn{i}_{kk}' for kk in range(K))}]\n"
    bul_heIn = "".join(heIn_bullet(i) for i in range(19))
    L.append(f"""/-- **The certificate with an in-epoch contraction.** -/
noncomputable def D3 (EL : ℕ) (hEL : EL = {EL}) : Cert3E B {D} fam EL {G} where
  C := C EL hEL
  lpi := {LPI}
  ei := EiK
  pat0 := PatK
  hcl := fun k => by fin_cases k; exacts [{", ".join(f"cls{kk}" for kk in range(K))}]
  hlpi0 := by norm_num
  hlpi := by show {LPI} ≤ {LP}; norm_num
  hpat := fun k => by fin_cases k; exacts [{", ".join(f"patm{kk}" for kk in range(K))}]
  helo := fun k => by fin_cases k; exacts [{", ".join(f"elo{kk}" for kk in range(K))}]
  heIn := by
    intro i h2 h17
    fin_cases i
{bul_heIn}""")
    # ---- the numbers
    def lines(key): return "\n".join(ch[key][0])
    def hyp(key): return ch[key][2]
    def U(key): return q(ch[key][1])
    base1 = ch['long'][3]; base2 = ch['empty'][3]; base3 = ch['win_a'][3]; base5 = ch['grow_a'][3]
    STAT = f"(1 + ({q(b)} - 1) / (1 - {q(lr)}))"
    tgt = q(target)
    L.append(f"""/-- **The numbers.** -/
theorem eps_le (E : Env) (hc : E.c = Config.spec) :
    settleEps3E E B P {LPI} {G} {N} {G} {Gp} {J} {Lw} {r} {Tg} {q(x)} {q(yy)} ≤ {tgt} := by
  have hk : E.c.k = {k} := by rw [hc]; rfl
  have hnEp : nEp E {N} = {nEp} := by
    unfold nEp; rw [hc]; norm_num [Config.spec, Config.epochLength, Config.kf]
  have hnbD : nbD E {D} {G} {Tg} = {nbD} := by
    unfold nbD growLen; rw [hc]; norm_num [Config.spec, Config.epochLength, Config.kf, Config.nonceOffset, Config.s]
  have p17 : P.e 17 = {e[17]} := rfl
  have p2 : P.e 2 = {e[2]} := rfl
  have pτ : P.τ = {TAU_} := rfl
  have plp : P.lp = {LP} := rfl
  have plr : P.lr = {q(lr)} := rfl
  have pb : P.b = {q(b)} := rfl
  have pc : P.c = {C_} := rfl
  unfold settleEps3E PT
  rw [hk, hnEp, hnbD, p17, p2, pτ, plp, plr, pb, pc]
  simp only [B]
{lines('long')}
  have e1 : (1 - (1 - {q(B['hhi'])}) ^ {D}) ^ ({G} / {D}) ≤ {U('long')} := by
    have hb : (0 : ℝ) ≤ 1 - (1 - {q(B['hhi'])}) ^ {D} := by norm_num
    have hb' : 1 - (1 - {q(B['hhi'])}) ^ {D} ≤ {q(base1)} := by norm_num
    rw [show ({G} / {D} : ℕ) = {G // D} by norm_num]
    exact (pow_le_pow_left₀ hb hb' _).trans {hyp('long')}
{lines('empty')}
  have e2 : (1 - {q(B['hlo'])}) ^ {Gp} ≤ {U('empty')} := by
    have hb : (0 : ℝ) ≤ 1 - {q(B['hlo'])} := by norm_num
    have hb' : 1 - {q(B['hlo'])} ≤ {q(base2)} := by norm_num
    exact (pow_le_pow_left₀ hb hb' _).trans {hyp('empty')}
{lines('span_a')}
{lines('span_b')}
  have e3 : {e[17]} ^ ({J} + 1) / {TAU_} ^ ({Lw} + 1) ≤ {U('span_a')} / {U('span_b')} := by
    rw [show ({J} + 1 : ℕ) = {J + 1} by norm_num, show ({Lw} + 1 : ℕ) = {Lw + 1} by norm_num]
    exact div_le_div₀ (by norm_num) {hyp('span_a')} (by norm_num) {hyp('span_b')}
{lines('fail')}
{lines('ratio')}
  have e4 : {LPI} ^ {J} * ({LP} / {LPI}) ^ {G} * {e[2]} * {STAT} ≤ {U('fail')} * {U('ratio')} * {e[2]} * {STAT} := by
    rw [show ({LP} / {LPI} : ℝ) = {q(lp / P['lpi'])} by norm_num]
    apply mul_le_mul_of_nonneg_right _ (by norm_num)
    apply mul_le_mul_of_nonneg_right _ (by norm_num)
    exact mul_le_mul {hyp('fail')} {hyp('ratio')} (by positivity) (by norm_num)
{lines('win_a')}
{lines('win_b')}
  have e5 : (1 + ({q(x)} - 1) * (1 - {q(B['elo'])})) ^ {Lw} / {q(x)} ^ ({k} + 1) ≤ {U('win_a')} / {U('win_b')} := by
    rw [show (1 + ({q(x)} - 1) * (1 - {q(B['elo'])}) : ℝ) = {q(base3)} by norm_num,
      show ({k} + 1 : ℕ) = {k + 1} by norm_num]
    exact div_le_div₀ (by norm_num) {hyp('win_a')} (by norm_num) {hyp('win_b')}
{lines('reach')}
  have e6 : {STAT} / {C_} ^ ({r} + 1) ≤ {STAT} / {U('reach')} := by
    rw [show ({r} + 1 : ℕ) = {r + 1} by norm_num]
    exact div_le_div_of_nonneg_left (by norm_num) (by norm_num) {hyp('reach')}
{lines('grow_a')}
{lines('grow_b')}
  have e7 : (1 + ({q(yy)} - 1) * (if (1 : ℝ) ≤ {q(yy)} then 1 - (1 - {q(B['hhi'])}) ^ {Tg}
      else 1 - (1 - {q(B['hlo'])}) ^ {Tg})) ^ {nbD} / {q(yy)} ^ ({k} + {r}) ≤ {U('grow_a')} / {U('grow_b')} := by
    rw [if_neg (by norm_num), show ({k} + {r} : ℕ) = {k + r} by norm_num]
    have hb : (0 : ℝ) ≤ 1 + ({q(yy)} - 1) * (1 - (1 - {q(B['hlo'])}) ^ {Tg}) := by norm_num
    have hb' : 1 + ({q(yy)} - 1) * (1 - (1 - {q(B['hlo'])}) ^ {Tg}) ≤ {q(base5)} := by norm_num
    exact div_le_div₀ (by norm_num) ((pow_le_pow_left₀ hb hb' _).trans {hyp('grow_a')}) (by norm_num) {hyp('grow_b')}
  have f1 := mul_le_mul_of_nonneg_left e1 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + (({Gp} : ℕ) : ℝ) + 1)
  have f2 := mul_le_mul_of_nonneg_left e2 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + 1)
  have f3 := mul_le_mul_of_nonneg_left e3 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + (({Gp} : ℕ) : ℝ) + 1)
  have f4 := mul_le_mul_of_nonneg_left e4 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + (({Gp} : ℕ) : ℝ) + 1)
  have f5 := mul_le_mul_of_nonneg_left e5 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + 1)
  have f6 := mul_le_mul_of_nonneg_left e6 (by norm_num : (0 : ℝ) ≤ (({N} : ℕ) : ℝ) + (({G} : ℕ) : ℝ) + 1)
  have f7 := mul_le_mul_of_nonneg_left e7 (by norm_num : (0 : ℝ) ≤ (({nEp} : ℕ) : ℝ))
  refine le_trans (add_le_add (add_le_add (add_le_add (add_le_add (add_le_add (add_le_add f1 f2) f3) f4) f5) f6) f7) ?_
  norm_num
""")
    L.append(f"""/-- **Certified multi-epoch finality from a random oracle.** β = {cfg['beta']}, Δ = {D},
k = {k}, executions up to slot {N}. Random-oracle tickets, fresh lotteries, Δ-delivery;
`pick` assigns each epoch and state a member. A finality violation has probability at most
`{target}` plus the probability that some slot's state is outside its member's band. -/
theorem certified {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) (hc : E.c = Config.spec) (hΔ : E.Δ = {D})
    (hA : Assm E) (es : Ω → List Event) (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ {N})
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω)) (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω)) (pick : ℕ → EpochState → Fin {K}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal {tgt} +
      μ {{ω | ∃ n < {M}, ¬ SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1))))
        E (n + 1)
        (σE (E.withO (O ω)) (es ω) (n + 1))}} := by
  have hEL : E.c.epochLength = {EL} := by rw [hc]; rfl
  refine (final_bimm_ro_epoch3_ok (M := {M}) hA es hNF hdel hO hσm hfresh hΔ (D3 E.c.epochLength hEL)
    (fun k => by fin_cases k; exacts [{", ".join(f"prod{kk}" for kk in range(K))}]) pick
    (G' := {Gp}) (J := {J}) (Lw := {Lw}) (r := {r}) (T := {Tg}) (x := {q(x)}) (yy := {q(yy)})
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by rw [hEL]; norm_num)).trans
    (add_le_add (ENNReal.ofReal_le_ofReal (eps_le E hc)) le_rfl)

""")
    L.append(emit_tsi(cfg, T, D, K, M, tgt, Gp, J, Lw, r, Tg, x, yy, G))
    L.append(f"end {ns}\n")
    open(f"{out_dir}/{name}.lean", "w").write("\n".join(L))


def emit_tsi(cfg, T, D, K, M, tgt, Gp, J, Lw, r, Tg, x, yy, G):
    """the band constants, the band's probability, and the end-to-end theorem"""
    from certE import tband_derived, PERIOD
    beta, delta = T['beta'], T['delta']
    dv = tband_derived(T)
    m = (PERIOD - 1) * dv['ylo'] * dv['clo']
    a1 = m * delta ** 2 / 2; a2 = m * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    n = 4096
    out = []
    a0s, Qs, chains = [], [], []
    for idx, a in enumerate((a1, a2)):
        a0 = rdn(a, 8)
        base = 1 + a0 / n
        lines, Q, hyp = chain(base, n, False, name=f'bq{idx}')
        a0s.append(a0); Qs.append((Q, hyp, base)); chains.append("\n".join(lines))
    BX = rup(1 / Qs[0][0] + 1 / Qs[1][0], 4)
    Ne = M // EL + 1
    # consecutive member ranges: ⟨m0.yhi = m1.ylo, ⟨…, trivial⟩⟩
    def nest_(kk):
        if kk == K - 1: return "trivial"
        return f"⟨by norm_num [m{kk}, m{kk + 1}], {nest_(kk + 1)}⟩"
    nest = nest_(0)
    tb = f"⟨{q(T['llo'])}, {q(T['lhi'])}, {q(T['mu'])}, {q(beta)}, {q(delta)}, 1 / 10 ^ 70, 1 / 10 ^ 16⟩"
    simpsT = "Tb, TBand.Yh, TBand.Ya, TBand.ylo, TBand.clo, TBand.chi, errHi, errLo"
    fieldsT = ['lo_pos', 'hi0', 'μ0', 'μ1', 'β0', 'β1', 'δ0', 'δ1', 'η0', 'ζ0', 'Yh_le', 'Ya_le', 'eHi', 'eLoH', 'eLoA', 'clo0']
    s = f"""/-- The estimate's band: `λV/D ∈ [ℓlo, ℓhi]`, μ = {float(T['mu'])}, β = {float(beta)}, δ = {float(delta)}. -/
noncomputable def Tb : TBand := {tb}

theorem TbOK : Tb.OK where
""" + "".join(f"  {f} := by norm_num [{simpsT}]\n" for f in fieldsT) + f"""
/-- **The estimate leaves its band in one epoch with probability at most `{float(BX):.3e}`.** -/
theorem band_le : bandEps Tb {PERIOD} ≤ {q(BX)} := by
  unfold bandEps
{chains[0]}
{chains[1]}
  have x1 : Real.exp (-((({PERIOD} : ℕ) - 1 : ℝ) * (Tb.ylo * Tb.clo) * Tb.δ ^ 2 / 2)) ≤ 1 / {q(Qs[0][0])} :=
    exp_neg_le_of (a0 := {q(a0s[0])}) {n} (by norm_num) (by norm_num) (by norm_num [{simpsT}]) (by norm_num)
      (by rw [show (1 + {q(a0s[0])} / (({n} : ℕ) : ℝ)) = {q(Qs[0][2])} by norm_num]; exact {Qs[0][1]})
  have x2 : Real.exp (-((({PERIOD} : ℕ) - 1 : ℝ) * (Tb.ylo * Tb.clo) * Tb.δ ^ 2 * (1 / 2 - 2 / 9 * Tb.δ))) ≤
      1 / {q(Qs[1][0])} :=
    exp_neg_le_of (a0 := {q(a0s[1])}) {n} (by norm_num) (by norm_num) (by norm_num [{simpsT}]) (by norm_num)
      (by rw [show (1 + {q(a0s[1])} / (({n} : ℕ) : ℝ)) = {q(Qs[1][2])} by norm_num]; exact {Qs[1][1]})
  have : 1 / {q(Qs[0][0])} + 1 / {q(Qs[1][0])} ≤ {q(BX)} := by norm_num
  linarith

theorem lot : LotConsts Config.spec (1 / 10 ^ 70) where
  p_pos := by norm_num [Config.spec]
  t0_pos := by norm_num [Config.spec]
  t1_le := by norm_num [Config.spec]
  a1_le := by unfold lam0; norm_num [Config.spec]
  a1_near := by unfold lam0; rw [abs_le]; constructor <;> norm_num [Config.spec]

theorem chainM : Chained (mem 0) (List.ofFn fun k : Fin {K - 1} => mem k.succ) := by
  show Chained m0 [{", ".join(f"m{kk}" for kk in range(1, K))}]
  exact {nest}

theorem covM : ∀ y, Tb.ylo ≤ y → y ≤ Tb.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi :=
  cover_of_chain chainM (by show m0.ylo ≤ Tb.ylo; norm_num [m0, Tb, TBand.ylo])
    (by show Tb.Yh ≤ m{K - 1}.yhi; norm_num [m{K - 1}, Tb, TBand.Yh])

theorem advM : ∀ k, Tb.β * (mem k).yhi ≤ (1 - Tb.β) * (mem k).ahi := fun k => by
  fin_cases k
  exacts [{", ".join(f"by show Tb.β * m{kk}.yhi ≤ (1 - Tb.β) * m{kk}.ahi; norm_num [m{kk}, Tb]" for kk in range(K))}]

/-- **Certified multi-epoch finality from a random oracle and the stake estimate.**
β = {float(beta)}, Δ = {D}, k = 2160, executions up to slot {cfg['N']} ({Ne} epochs). Beyond the
random oracle, fresh lotteries and Δ-delivery, the hypotheses are those of
`final_bimm_ro_tsi6`: states satisfy `StateOK`, the genesis state is in band, the canonical
chain's occupied-slot count is at least `(1-μ)` times the honest occupied slots (`hlo`;
μ = {float(T['mu'])}, full withholding allowed), the stake path satisfies `StakePath`, the
honest nodes' online status changes only at epoch boundaries (`OnlineEpoch`), and some
honest node is online at every slot (`hlive`). Then a finality violation has probability
at most `{tgt} + {Ne} · {float(BX):.3e} + {Ne} · {tgt}`: the last term pays for the
canonical prefixes' consistency, epoch by epoch. -/
theorem certified_tsi {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) (hc : E.c = Config.spec) (hΔ : E.Δ = {D})
    (hA : Assm E) (es : Ω → List Event) (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ {cfg['N']})
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω)) (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    (hst : ∀ ω i, StateOK E Tb i (σE (E.withO (O ω)) (es ω) i))
    (h0 : InB E Tb (fun _ => es0 E) 0)
    (hlo : ∀ ω e, e + 1 < {Ne} → (1 - Tb.μ) *
      hcnt E (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e ≤
        (occupied E.c (CP (E.withO (O ω)) (es ω) (e + 1)) e : ℝ))
    (hpath : ∀ ω e, e + 1 < {Ne} → StakePath E Tb (σE (E.withO (O ω)) (es ω)) e)
    (hon : OnlineEpoch E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal {tgt} +
      ((({Ne} : ℕ) : ENNReal) * ENNReal.ofReal {q(BX)} + (({Ne} : ℕ) : ENNReal) * ENNReal.ofReal {tgt}) := by
  have hEL : E.c.epochLength = {EL} := by rw [hc]; rfl
  have hP : E.c.period = {PERIOD} := by rw [hc]; rfl
  refine (final_bimm_ro_tsi6 (M := {M}) (Ne := {Ne}) hA es hNF hdel hO hσm hfresh hΔ (D3 E.c.epochLength hEL)
    (fun k => by fin_cases k; exacts [{", ".join(f"prod{kk}" for kk in range(K))}])
    (G' := {Gp}) (J := {J}) (Lw := {Lw}) (r := {r}) (T := {Tg}) (x := {q(x)}) (yy := {q(yy)})
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by rw [hEL]; norm_num)
    (by rw [hEL, hc]; norm_num [Config.spec, Config.nonceOffset, Config.s, Config.kf]) (by norm_num [B])
    (by show (0 : ℝ) ≤ P.e 2; norm_num [P, Ev])
    (by rw [hc]; exact lot) TbOK (by rw [hc]; rfl) (by rw [hc]; norm_num [Config.spec])
    (by rw [hc]; norm_num [Config.spec, Config.period, Config.kf])
    (by rw [hP]; norm_num) (by rw [hP, hEL]; norm_num)
    hst h0 (by rw [hEL]; norm_num) hlo hpath hon hlive (mem := mem) (fun k => by fin_cases k <;> rfl)
    (fun k => by fin_cases k; exacts [{", ".join(f"ok{kk}" for kk in range(K))}]) covM advM).trans ?_
  rw [hP]
  have h1 := ENNReal.ofReal_le_ofReal (eps_le E hc)
  have h2 := ENNReal.ofReal_le_ofReal band_le
  exact add_le_add h1 (add_le_add (mul_le_mul_right h2 _) (mul_le_mul_right h1 _))

"""
    return s


if __name__ == "__main__":
    import pickle
    beta, D, delta, K, N = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    name, out_dir = sys.argv[6], sys.argv[7]
    mode = sys.argv[8] if len(sys.argv) > 8 else 'all'
    mu = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
    pk = f"res_{name}.pkl"
    if mode in ('main', 'emit') and os.path.exists(pk):
        res = pickle.load(open(pk, 'rb'))
    else:
        res = planE.make(beta, D, delta, K, N, mu=mu)
        pickle.dump(res, open(pk, 'wb'))
    cfg, T, fam, B, P, Ts = res
    tot = sum(Ts)
    texp = -flog10(tot) - 1
    target = Fr(1, 10 ** texp) if texp > 0 else Fr(1)
    while target < tot: texp -= 1; target = Fr(1, 10 ** texp)
    if mode == 'main':
        C_, Z_, S_, K_, Dd_, TAU_ = (q(Fr(cfg[v])) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
        emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, f"{C_} {Z_} {S_} {Dd_} {TAU_}")
    else:
        emit_all(cfg, T, fam, B, P, Ts, name, out_dir, target)
    json.dump(dict(cfg, target=str(target)), open(f"cfgE_{name}.json", "w"), indent=1)
    print(name, 'target', target)
