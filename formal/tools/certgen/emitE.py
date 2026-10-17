"""Emit a multi-epoch certificate (`Cert2E`, Prob/Final2E.lean) as Lean files.

Layout (`formal/Cryptarchia/Prob/Certs/<name>/`):
* `Fam.lean`   the members' bands `f k`, the weakest band `B`, the family `fam`;
* `I<i>.lean`  index i's tables, by their entries at (0, a, true), and their checks
               (switching tables for 0, 1, 2, 17; one-switch tables for the others);
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
from emit_gen import member_band
from certE import SIDX, EIDX, EL, PERIOD, tband_derived
import planE
import emitZ

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
FAM_IMPORTS = """public import Cryptarchia.Prob.FamQ
"""
MAIN_IMPORTS = """import Cryptarchia.Prob.Cert
public import Cryptarchia.Prob.PowQ
import Cryptarchia.Prob.ExpBound
public import Cryptarchia.Prob.Finality
import Mathlib.Algebra.Order.Ring.Star
"""
# the closed form's proofs also use these
CLOSED_IMPORTS = """import Mathlib.RingTheory.WittVector.IsPoly
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


def kmatch(name, typ, items, default):
    s = f"noncomputable def {name} : {typ} := fun k =>\n  match k.val with\n"
    for j, it in enumerate(items):
        s += f"  | {j} => {it}\n" if j < len(items) - 1 else f"  | _ => {it}\n"
    return s


def emit_all(cfg, T, fam, B, P, Ts, name, out_dir, target, closed=None):
    D = cfg['Delta']; K = len(fam)
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    C_, Z_, S_, K_, Dd_, TAU_ = (q(v) for v in (c, z, s, kap, d, tau))
    args = f"{C_} {Z_} {S_} {Dd_} {TAU_}"
    sub = f"{out_dir}/{name}"
    os.makedirs(sub, exist_ok=True)
    ns = f"Cryptarchia.Prob.Certs.{name}"
    pre = f"namespace {ns}\n\nopen Cryptarchia Cryptarchia.Prob\n\n{HEAD}\n"
    # ---- Fam.lean: the members from their breakpoints (`FamQ.lean`); the kernel computes and
    # checks every band
    ys = [m['ylo'] for m in fam] + [fam[-1]['yhi']]
    beta = Fr(cfg['beta']).limit_denominator(1000)
    for m in fam:
        assert m['ahi'] == rup(beta / (1 - beta) * m['yhi'], 12) and m['B'] == member_band(m['ylo'], m['yhi'], m['ahi'])
    Dfam, _ = emitZ.fam_z(fam)
    MQ = f"memberOfQ (1 / 10 ^ 70) (1 / 10 ^ 16) {qQ(beta)} 13 12 ysF"
    L = ["module\n\n" + FAM_IMPORTS + "meta import Cryptarchia.Prob.FamQ\n" + EXT,
         f"/-!\n# {name}: the band family\n\nGenerated by `tools/certgen/emitE.py`. Member `k` has honest exponent in\n"
         f"`[ysF k, ysF (k + 1)]` and adversarial exponent at most `β / (1 - β)` times the upper end; the kernel\n"
         f"computes its band (`memberOfQ`, `FamQ.lean`) and checks it.\n-/\n", SEC, pre]
    L.append("/-- The members' breakpoints. -/\ndef ysF : List ℚ :=\n  [" + ", ".join(qQ(y) for y in ys) + "]\n")
    L.append(f"""/-- Member `k` over `ℚ`. -/
def famM (k : Fin {K}) : MemberQ := {MQ} k.val

noncomputable def mem (k : Fin {K}) : Member := (famM k).toMember

noncomputable def fam (k : Fin {K}) : Band := (famM k).B.toBand
""")
    L.append(band_def("B", B, "The weakest band: weaker than every member."))
    L.append("def Bq : BandR := ⟨" + ", ".join(qQ(B[kk]) for kk in BANDKEYS) + "⟩\n\n"
             "theorem B_eq : B = Bq.toBand := by\n  simp only [B, Bq, BandR.toBand]; norm_num\n")
    L.append(f"""/-- Every member's numeric conditions, and the weakest band below it. -/
theorem chkM : ∀ k, ((famM k).chk (1 / 10 ^ 70) (1 / 10 ^ 16) && Bq.weakerQ (famM k).B) = true := by
  decide +kernel

theorem chkM1 (k : Fin {K}) : (famM k).chk (1 / 10 ^ 70) (1 / 10 ^ 16) = true := by
  have h := chkM k; simp only [Bool.and_eq_true] at h; exact h.1

theorem weak (k : Fin {K}) : B.Weaker (fam k) := by
  have h := chkM k; simp only [Bool.and_eq_true] at h; rw [B_eq]; exact BandR.weaker_of h.2

theorem prod (k : Fin {K}) : (fam k).Prod := memberOfQ_prod (chkM1 k)

theorem elo (k : Fin {K}) : 0 ≤ (fam k).elo := memberOfQ_elo (chkM1 k)

theorem ok (k : Fin {K}) : (mem k).OK (1 / 10 ^ 70) (1 / 10 ^ 16) := by
  have h := memberOfQ_OK (chkM1 k); push_cast at h; exact h

/-- The members' `slot4` fields over `ℚ`. -/
def famQ (k : Fin {K}) : BandQ := (famM k).B.toQ

theorem famA (k : Fin {K}) : (famQ k).Agrees (fam k) := (famM k).B.agrees

/-- The members' `slot4` fields' common denominator. -/
def DZ : ℤ := {Dfam}

theorem DZ_pos : 0 < DZ := by decide

/-- The members' `slot4` fields over the integers, times `DZ`, computed once at elaboration time
(the index files read them); `famR` checks them against the bands. -/
def famZL : List (List ℤ) := eval% (List.finRange {K}).map fun k => (famM k).B.toZList DZ

def famZ (k : Fin {K}) : BandZ := BandZ.ofList (famZL.getD k.val [])

theorem famR : ∀ k, (famZ k).Rep DZ (famQ k) := by decide +kernel

/-- Each member's crossing bound. -/
def PatKQ (k : Fin {K}) : ℚ := rdnQ 13 ((famM k).B.slo * (famM k).B.elo ^ {D})

theorem patm (k : Fin {K}) : ((PatKQ k : ℚ) : ℝ) ≤ (fam k).slo * (fam k).elo ^ {D} := patQ_le {D} (famM k).B 13
""")
    for k in range(K):
        assert rdn(fam[k]['B']['slo'] * fam[k]['B']['elo'] ** D, 13) == P['patk'][k]
    L.append(f"end {ns}\n")
    open(f"{sub}/Fam.lean", "w").write("\n".join(L))
    argsQ = " ".join(qQ(v) for v in (c, z, s, d, tau))
    # ---- I<i>.lean: one file per index, so that Lake checks the indices in parallel. Each
    # table is given by its entries at (0, a, true); Lean computes the rest and checks it in
    # integer arithmetic (`AutoZ.lean`, mirrored in `emitZ.py`).
    for old in os.listdir(sub):
        if old.endswith('.lean') and old != 'Fam.lean': os.remove(f"{sub}/{old}")
    for i in range(19):
        L = ["module\n\npublic import " + ns + ".Fam\nmeta import " + ns + ".Fam\n" + EXT, f"/-! # {name}: tables for index {i} -/\n", SEC, pre]
        xgs = f"(xg {args} {i}).1 (xg {args} {i}).2.1 (xg {args} {i}).2.2"
        L.append(f"theorem xgQ{i} : xg {args} {i} = castX (xgNQ {argsQ} {i}) :=\n"
                 f"  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) {i}\n")
        # the tables from their entries at (0, a, true), in integer arithmetic (`AutoZ.lean`);
        # `index_z` runs every check first
        sb = {0: P['lr'], 1: P['b'], 2: P['e'][2], 17: P['e'][17]}.get(i)
        data = emitZ.index_z(i, fam, D, P, (c, z, s, d, tau), sb)
        L.append(emitZ.index_lean(i, K, D, xgs, argsQ, data, P, q, qQ, sb))
        L.append(f"end {ns}\n")
        open(f"{sub}/I{i}.lean", "w").write("\n".join(L))
    # ---- main file
    emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, args, closed=closed)


def emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, args, closed=None):
    D = cfg['Delta']; K = len(fam); N = cfg['N']; k = cfg['k']
    G0 = cfg['G']
    ELHYP = f"{G0 + 1} < EL" if closed else f"EL = {EL}"
    GELPRF = "hEL" if closed else "by rw [hEL]; norm_num"
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
    if closed:
        L.append(f"""/-!
# Closed-form finality certificate: β = {cfg['beta']}, Δ = {D}, every k ≥ {closed['k0']}, {K} members

Generated by `tools/certgen/emitC.py`. Later epochs' states lie in one of
{K} members (honest exponent ranges covering `[(1-β)ℓlo, ℓhi]`, `ℓlo = {float(T['llo']):.6f}`,
`ℓhi = {float(T['lhi']):.6f}`, full withholding). The automaton certificates do not depend on
the depth; the settlement parameters grow linearly in `k / 20`, and `finality_closed` bounds a
finality violation by a sum of geometric terms in `k / 20`, for every depth `k ≥ {closed['k0']}`
and every horizon `N`.
-/
""")
    else:
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
    L.append("/-- Each member's in-epoch phase bounds, from the index files (none for 2 and 17). -/\n" +
             f"def EiKQ : Fin {K} → Fin 19 → ℚ := fun k i =>\n  match i.val with\n" +
             "".join(f"  | {i} => eIn{i} k\n" for i in EIDX) + "  | _ => 0\n\n" +
             f"noncomputable def EiK : Fin {K} → Fin 19 → ℝ := fun k i => EiKQ k i\n\n" +
             f"noncomputable def PatK : Fin {K} → ℝ := fun k => PatKQ k\n")
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
    solS = ", ".join(f"solS{i} k" for i in SIDX)
    hes = "".join(f"  heS{i} := heS{i}\n" for i in SIDX)
    bul_solE = "".join(f"    · exact solE{i}\n" if i in EIDX else ("    · exact absurd rfl h2\n" if i == 2 else "    · exact absurd rfl h17\n")
                       for i in range(19))
    bul_heE = "".join(f"    · exact heEall{i}\n" if i in EIDX else ("    · exact absurd rfl h2\n" if i == 2 else "    · exact absurd rfl h17\n")
                      for i in range(19))
    L.append(f"""/-- **The multi-epoch certificate.** -/
noncomputable def C (EL : ℕ) (hEL : {ELHYP}) : Cert2E B {D} fam EL {G} where
  P := P
  weakF := weak
  hG := by norm_num
  hGEL := {GELPRF}
  vs := vsF
  solS := by
    intro i hi k
    rcases hi with rfl | rfl | rfl | rfl
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
    LPIQ = qQ(P['lpi'])
    L.append(f"""/-- The class conditions for every member, over `ℚ`. -/
theorem chkCls : ∀ k, classOKQ {qQ(c)} {qQ(z)} {qQ(s)} {qQ(kap)} {qQ(d)} {LPIQ} (EiKQ k) (PatKQ k) = true := by
  decide +kernel

theorem cls : ∀ k, ClassOK P {LPI} (EiK k) (PatK k) := fun k =>
  ClassOK.ofQ (by norm_num [P]) (by norm_num [P]) (by norm_num [P]) (by norm_num [P]) (by norm_num [P])
    (by norm_num) (fun _ => rfl) rfl (chkCls k)
""")
    def heIn_bullet(i):
        if i == 2: return "    · exact absurd rfl h2\n"
        if i == 17: return "    · exact absurd rfl h17\n"
        return f"    · exact heIn{i}\n"
    bul_heIn = "".join(heIn_bullet(i) for i in range(19))
    L.append(f"""/-- **The certificate with an in-epoch contraction.** -/
noncomputable def D3 (EL : ℕ) (hEL : {ELHYP}) : Cert3E B {D} fam EL {G} where
  C := C EL hEL
  lpi := {LPI}
  ei := EiK
  pat0 := PatK
  hcl := cls
  hlpi0 := by norm_num
  hlpi := by show {LPI} ≤ {LP}; norm_num
  hpat := patm
  helo := elo
  heIn := by
    intro i h2 h17
    fin_cases i
{bul_heIn}""")
    if closed:
        from emitC import closed_section
        L.append(emit_tsi(cfg, T, D, K, cfg['N'] + cfg['G'] + cfg['Gp'] + D + 2, '0', cfg['Gp'], cfg['J'], cfg['Lw'], cfg['r'], cfg['T'], Fr(cfg['x']), Fr(cfg['yy']), cfg['G'], Fr(1), closed=closed))
        L[0] = L[0].replace("public import Cryptarchia.Prob.Finality\n", "public import Cryptarchia.Prob.Finality\npublic import Cryptarchia.Prob.Closed\n")
        L[0] = L[0].replace("import Mathlib.Algebra.Order.Ring.Star\n", "import Mathlib.Algebra.Order.Ring.Star\n" + CLOSED_IMPORTS)
        L.append(closed_section(cfg, T, fam, B, P, D, K, closed)[0])
        L.append(f"end {ns}\n")
        open(f"{out_dir}/{name}.lean", "w").write("\n".join(L))
        return
    # ---- the numbers: the settlement bound computed by the kernel (`settleEps3E_le_Q`), below the target
    import powq
    tgt = q(target)
    sq = powq.settle_q(powq.D_POW, D, B, es[17], tau, lp, es[2], b, lr, c, P['lpi'], x, yy, k, nEp, nbD, G, N, G, Gp,
                       J, Lw, r, Tg)
    assert sq <= target, (float(sq), float(target))
    eqs = " ".join(f"(by rw [show {lhs} = ({rhs} : ℝ) from rfl]; norm_num)" for lhs, rhs in
                   [("P.e 17", e[17]), ("P.τ", TAU_), ("P.lp", LP), ("P.e 2", e[2]), ("P.b", q(b)), ("P.lr", q(lr)),
                    ("P.c", C_)])
    L.append(f"""/-- **The numbers**, computed by the kernel. -/
theorem eps_le (E : Env) (hc : E.c = Config.spec) :
    settleEps3E E B P {LPI} {G} {N} {G} {Gp} {J} {Lw} {r} {Tg} {q(x)} {q(yy)} ≤ {tgt} := by
  have hk : E.c.k = {k} := by rw [hc]; rfl
  have hnEp : nEp E {N} = {nEp} := by
    unfold nEp; rw [hc]; norm_num [Config.spec, Config.epochLength, Config.kf]
  have hnbD : nbD E {D} {G} {Tg} = {nbD} := by
    unfold nbD growLen; rw [hc]; norm_num [Config.spec, Config.epochLength, Config.kf, Config.nonceOffset, Config.s]
  have h := settleEps3E_le_Q (d := {powq.D_POW}) (e17 := {qQ(es[17])}) (τ := {qQ(tau)}) (lp := {qQ(lp)})
    (e2 := {qQ(es[2])}) (b := {qQ(b)}) (lr := {qQ(lr)}) (c := {qQ(c)}) (lpi := {LPIQ}) (x := {qQ(x)}) (yy := {qQ(yy)})
    (k := {k}) (ne := {nEp}) (nb := {nbD}) (Ccap := {G}) (N := {N}) (G := {G}) (G' := {Gp}) (J := {J}) (Lw := {Lw})
    (r := {r}) (T := {Tg}) P Bq B_eq
    {eqs} hk hnEp hnbD (by decide +kernel)
  push_cast at h
  refine h.trans ?_
  refine (Rat.cast_le (K := ℝ) |>.2 (show settleEps3EQ {powq.D_POW} {D} Bq {qQ(es[17])} {qQ(tau)} {qQ(lp)} {qQ(es[2])} {qQ(b)} {qQ(lr)} {qQ(c)} {LPIQ}
    {qQ(x)} {qQ(yy)} {k} {nEp} {nbD} {G} {N} {G} {Gp} {J} {Lw} {r} {Tg} ≤ {qQ(target)} by decide +kernel)).trans_eq ?_
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
    prod pick
    (G' := {Gp}) (J := {J}) (Lw := {Lw}) (r := {r}) (T := {Tg}) (x := {q(x)}) (yy := {q(yy)})
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by rw [hEL]; norm_num)).trans
    (add_le_add (ENNReal.ofReal_le_ofReal (eps_le E hc)) le_rfl)

""")
    L.append(emit_tsi(cfg, T, D, K, M, tgt, Gp, J, Lw, r, Tg, x, yy, G, target))
    L.append(f"end {ns}\n")
    open(f"{out_dir}/{name}.lean", "w").write("\n".join(L))


def emit_tsi(cfg, T, D, K, M, tgt, Gp, J, Lw, r, Tg, x, yy, G, tgt_q, closed=None):
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
    # the kernel's bound (`bandEps_le_Q`), below BX
    import powq
    assert n == powq.N_EXP and powq.band_q(powq.D_POW, n, dv, delta, PERIOD) <= BX
    Ne = M // EL + 1
    FINAL = rup(tgt_q + Ne * BX, 2)
    tb = f"⟨{q(T['llo'])}, {q(T['lhi'])}, {q(T['mu'])}, {q(beta)}, {q(delta)}, 1 / 10 ^ 70, 1 / 10 ^ 16⟩"
    simpsT = "Tb, TBand.Yh, TBand.Ya, TBand.ylo, TBand.clo, TBand.chi, errHi, errLo"
    fieldsT = ['lo_pos', 'hi0', 'μ0', 'μ1', 'β0', 'β1', 'δ0', 'δ1', 'η0', 'ζ0', 'Yh_le', 'Ya_le', 'eHi', 'eLoH', 'eLoA', 'clo0']
    s = f"""/-- The estimate's band: `λV/D ∈ [ℓlo, ℓhi]`, μ = {float(T['mu'])}, β = {float(beta)}, δ = {float(delta)}. -/
noncomputable def Tb : TBand := {tb}

theorem TbOK : Tb.OK where
""" + "".join(f"  {f} := by norm_num [{simpsT}]\n" for f in fieldsT) + f"""
/-- **The estimate leaves its band in one epoch with probability at most `{float(BX):.3e}`.** -/
def TbQ : TBandQ := ⟨{qQ(T['llo'])}, {qQ(T['lhi'])}, {qQ(T['mu'])}, {qQ(beta)}, {qQ(delta)}, 1 / 10 ^ 70, 1 / 10 ^ 16⟩

theorem Tb_eq : Tb = TbQ.toTBand := by
  simp only [Tb, TbQ, TBandQ.toTBand]; norm_num

theorem band_le : bandEps Tb {PERIOD} ≤ {q(BX)} := by
  rw [Tb_eq]
  refine (bandEps_le_Q (d := {powq.D_POW}) (n := {n}) (T := TbQ) (P := {PERIOD}) (by decide +kernel)).trans ?_
  refine (Rat.cast_le (K := ℝ) |>.2 (show bandEpsQ {powq.D_POW} {n} TbQ {PERIOD} ≤ {qQ(BX)} by decide +kernel)).trans_eq ?_
  norm_num

theorem lot : LotConsts Config.spec (1 / 10 ^ 70) where
  p_pos := by norm_num [Config.spec]
  t0_pos := by norm_num [Config.spec]
  t1_le := by norm_num [Config.spec]
  a1_le := by unfold lam0; norm_num [Config.spec]
  a1_near := by unfold lam0; rw [abs_le]; constructor <;> norm_num [Config.spec]

theorem chainM : Chained (mem 0) (List.ofFn fun k : Fin {K - 1} => mem k.succ) := by
  simpa only [mem, famM, Fin.val_zero, Fin.val_succ, Nat.zero_add] using chained_memberOfQ (1 / 10 ^ 70) (1 / 10 ^ 16) {qQ(beta)} 13 12 ysF {K - 1} 0

theorem covM : ∀ y, Tb.ylo ≤ y → y ≤ Tb.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi :=
  cover_of_chain chainM
    (by simp only [mem, famM, MemberQ.toMember_ylo, memberOfQ_ylo, ysF]; norm_num [Tb, TBand.ylo])
    (by simp only [mem, famM, MemberQ.toMember_yhi, memberOfQ_yhi, ysF]; norm_num [Tb, TBand.Yh])

theorem advM : ∀ k, Tb.β * (mem k).yhi ≤ (1 - Tb.β) * (mem k).ahi := fun k =>
  memberOfQ_adv (by norm_num) (by norm_num [Tb])

/-- **Finality, certified.** f = 1/30, k = 2160, Δ = {D} slots, executions up to slot
{cfg['N']} ({Ne} epochs). Under the execution model (`Model`), if the genesis estimate is
the genesis stake, the adversary holds at most {float(beta)} of the participating stake, the
canonical chain counts at least {float(1 - T['mu'])} of each window's honestly won slots,
stake drifts by at most a factor {float(T['rho'])} per epoch and honest online stake is at
least {T['hmin']}, a finality violation has probability at most {float(FINAL):.2e}. -/
theorem finality {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) (hc : E.c = Config.spec) (hΔ : E.Δ = {D})
    (es : Ω → List Event) (hM : Model μ O E es) (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ {cfg['N']})
    (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} {Ne})
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} {Ne})
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal {q(FINAL)} := by
  have hEL : E.c.epochLength = {EL} := by rw [hc]; rfl
  have hP : E.c.period = {PERIOD} := by rw [hc]; rfl
  have hb := Prob.finality (M := {M}) (Ne := {Ne}) es hM hN hΔ (D3 E.c.epochLength hEL)
    prod
    (G' := {Gp}) (J := {J}) (Lw := {Lw}) (r := {r}) (T := {Tg}) (x := {q(x)}) (yy := {q(yy)})
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B])
    (by rw [hEL]; norm_num) (by rw [hEL, hc]; norm_num [Config.spec, Config.nonceOffset, Config.s, Config.kf])
    (by rw [hc]; exact lot) TbOK (by rw [hc]; rfl) (by rw [hc]; norm_num [Config.spec])
    (by rw [hc]; norm_num [Config.spec, Config.period, Config.kf])
    (by rw [hP]; norm_num) (by rw [hP, hEL]; norm_num) (by rw [hEL]; norm_num)
    (mem := mem) (fun k => by fin_cases k <;> rfl)
    ok covM advM
    (ρ := {q(T['rho'])}) (Hmin := {q(T['hmin'])}) (by norm_num) (by norm_num)
    (by rw [hc]; unfold lam0 Kc; norm_num [Tb, TBand.clo, TBand.Yh, TBand.ylo, errHi, Config.spec, Config.period,
      Config.kf, Config.t0Const, Config.p])
    (by rw [hc]; unfold lam0 Kc; norm_num [Tb, TBand.chi, TBand.Yh, TBand.Ya, errLo, Config.spec, Config.period,
      Config.kf, Config.t0Const, Config.p])
    (by rw [hc]; unfold lam0; norm_num [Tb, Config.spec, Config.t0Const, Config.p])
    (by rw [hc]; unfold lam0; norm_num [Tb, Config.spec, Config.t0Const, Config.p])
    hG hS hQ hD hH
  rw [hP] at hb
  have h1 := ENNReal.ofReal_le_ofReal (eps_le E hc)
  have h2 := ENNReal.ofReal_le_ofReal band_le
  refine hb.trans ((add_le_add h1 (mul_le_mul_right h2 _)).trans ?_)
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add (by positivity) (by positivity)]
  exact ENNReal.ofReal_le_ofReal (by norm_num)

"""
    if closed:
        # the closed-form certificate keeps the band, the lottery constants and the members
        s = s[:s.index("theorem band_le")] + s[s.index("theorem lot :"):s.index("/-- **Finality, certified.**")]
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
    # the settlement parameters, optimized against the exact terms (`optnum`)
    import optnum
    cand, _ = optnum.optimize(cfg, B, P)
    cfg = dict(cfg, **cand)
    _, Ts, _ = planE.terms(cfg, B, P)
    tot = sum(Ts)
    # the settlement bound's target: the planned total, rounded up to two significant digits
    target = rup(tot, 2)
    if mode == 'main':
        C_, Z_, S_, K_, Dd_, TAU_ = (q(Fr(cfg[v])) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
        emit_main(cfg, T, fam, B, P, Ts, name, out_dir, target, f"{C_} {Z_} {S_} {Dd_} {TAU_}")
    else:
        emit_all(cfg, T, fam, B, P, Ts, name, out_dir, target)
    json.dump(dict(cfg, target=str(target)), open(f"cfgE_{name}.json", "w"), indent=1)
    print(name, 'target', target)
