module

public import Cryptarchia.Prob.PowQ
public import Cryptarchia.Prob.Final3E
import Mathlib.Algebra.Order.Floor.Extended
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

/-!
# Certificates from their data

A multi-epoch certificate is the data a search chose: the band family's breakpoints, the
potential's parameters and the settlement parameters. Everything else is computed, and the
results checked by the kernel; this file holds the generic constructions, so that a certificate
states no proofs of its own.

* `FamSpec`: the band family from its breakpoints, with one check per member (`FamSpec.chk`)
  giving `Member.OK`, `Band.Prod`, the weakest band below it, and its integer bands.
* `FamCfg`, `IdxData`: one phase index's tables, given by seeds computed at elaboration time,
  and the bounds they give; `idxChk` checks them, and `idx_sw`, `idx_one` give what `Cert2E`
  needs from them.
* `Cert2.ofQ`, `Cert2E.ofCfg`, `Cert3E.ofCfg`: the certificates from the data and the checks.
  The potential's expectations `e i`, `lr` and `b` are the tables' bounds (`eOf`, `lrOf`, `bOf`).
-/

@[expose] public section

namespace Cryptarchia.Prob

/-! ## Band families from their breakpoints -/

/-- A band family: member `k` has honest exponent in `[ys k, ys (k + 1)]` (`memberOfQ`). -/
structure FamSpec where
  η : ℚ
  ζ : ℚ
  β : ℚ
  d : ℕ
  dy : ℕ
  K : ℕ
  ys : List ℚ

namespace FamSpec

variable (S : FamSpec)

def mQ (k : Fin S.K) : MemberQ := memberOfQ S.η S.ζ S.β S.d S.dy S.ys k.val

noncomputable def mem (k : Fin S.K) : Member := (S.mQ k).toMember

noncomputable def fam (k : Fin S.K) : Band := (S.mQ k).B.toBand

def famQ (k : Fin S.K) : BandQ := (S.mQ k).B.toQ

/-- Two bands' weakest combination: the larger upper and the smaller lower bounds. -/
def weak2 (H b : BandR) : BandR :=
  ⟨max H.hhi b.hhi, min H.hlo b.hlo, max H.amax b.amax, max H.hahi b.hahi, min H.slo b.slo, min H.hnlo b.hnlo,
    min H.elo b.elo, min H.alo b.alo, min H.halo b.halo⟩

/-- **The weakest band**, weaker than every member's. -/
def weakest : BandR :=
  match (List.finRange S.K).map fun k => (S.mQ k).B with
  | [] => ⟨0, 0, 0, 0, 0, 0, 0, 0, 0⟩
  | b :: bs => bs.foldl weak2 b

/-- The common denominator of the members' `slot4` fields. -/
def DZ : ℤ :=
  ((List.finRange S.K).foldl (fun m k => let b := (S.mQ k).B;
    [b.hhi, b.hlo, b.amax, b.hahi, b.alo, b.halo].foldl (fun m q => Nat.lcm m q.den) m) 1 : ℕ)

/-- The members' integer bands over `D`, listed: computed once, at elaboration time. -/
def famZList (D : ℤ) : List (List ℤ) := (List.finRange S.K).map fun k => (S.mQ k).B.toZList D

/-- Each member's crossing bound. -/
def patQ (Δ : ℕ) (k : Fin S.K) : ℚ := rdnQ 13 ((S.mQ k).B.slo * (S.mQ k).B.elo ^ Δ)

/-- **Every member's checks**: its numeric conditions, the weakest band below it, and its integer
band `famZ k` over `D`. -/
def chk (famZ : Fin S.K → BandZ) (D : ℤ) : Bool :=
  (List.finRange S.K).all fun k => (S.mQ k).chk S.η S.ζ && S.weakest.weakerQ (S.mQ k).B &&
    decide ((famZ k).Rep D (S.famQ k))

section Chk

variable {S} {famZ : Fin S.K → BandZ} {D : ℤ} (h : S.chk famZ D = true)
include h

theorem chk_k (k : Fin S.K) : ((S.mQ k).chk S.η S.ζ && S.weakest.weakerQ (S.mQ k).B &&
    decide ((famZ k).Rep D (S.famQ k))) = true :=
  List.all_eq_true.1 h k (List.mem_finRange k)

theorem ok (k : Fin S.K) : (S.mem k).OK S.η S.ζ := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_OK this.1.1

theorem prod (k : Fin S.K) : (S.fam k).Prod := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_prod this.1.1

theorem elo (k : Fin S.K) : 0 ≤ (S.fam k).elo := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_elo this.1.1

theorem weak (k : Fin S.K) : S.weakest.toBand.Weaker (S.fam k) := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact BandR.weaker_of this.1.2

theorem rep (k : Fin S.K) : (famZ k).Rep D (S.famQ k) := by
  have := chk_k h k; simp only [Bool.and_eq_true, decide_eq_true_eq] at this; exact this.2

end Chk

theorem agrees (k : Fin S.K) : (S.famQ k).Agrees (S.fam k) := (S.mQ k).B.agrees

theorem pat_le (Δ : ℕ) (k : Fin S.K) : ((S.patQ Δ k : ℚ) : ℝ) ≤ (S.fam k).slo * (S.fam k).elo ^ Δ :=
  patQ_le Δ (S.mQ k).B 13

theorem hfam (k : Fin S.K) : (S.mem k).B = S.fam k := rfl

/-- **Consecutive members chain.** -/
theorem chained {n : ℕ} (hK : S.K = n + 1) :
    Chained (S.mem (hK ▸ 0)) (List.ofFn fun k : Fin n => S.mem (hK ▸ k.succ)) := by
  obtain ⟨η, ζ, β, d, dy, K, ys⟩ := S
  simp only at hK
  subst hK
  simpa only [mem, mQ, Fin.val_zero, Fin.val_succ, Nat.zero_add] using chained_memberOfQ η ζ β d dy ys n 0

end FamSpec

/-! ## One phase index, from its seeds -/

/-- What a certificate's index checks depend on: the band family, its integer bands over `D`
(listed, as computed once at elaboration time), `Δ`, and the potential's parameters. -/
structure FamCfg where
  S : FamSpec
  famZL : List (List ℤ)
  D : ℤ
  Δ : ℕ
  c : ℚ
  z : ℚ
  s : ℚ
  d : ℚ
  τ : ℚ

/-- One index's data, computed at elaboration time: each member's post- and pre-switch seeds,
in-epoch bound and the largest pre-switch bound, and the switching table's seeds and largest
bound. -/
structure IdxData where
  post : List (List ℤ)
  pre : List (List ℤ)
  eIn : List ℚ
  eE : ℚ
  vs : List ℤ
  eS : ℚ

namespace FamCfg

variable (F : FamCfg)

def famZ (k : Fin F.S.K) : BandZ := BandZ.ofList (F.famZL.getD k.val [])

def famL : List BandZ := (List.finRange F.S.K).map F.famZ

/-- Phase expectation `i` over the integers. -/
def X (i : ℕ) : PhZ := PhZ.ofQ (xgNQ F.c F.z F.s F.d F.τ i)

/-- The terminal table's entries at `(0, a, true)`, where the seeds start. -/
def floor (i : ℕ) : List ℤ := [gFloorZ (F.X i) SZ 0 0 true, gFloorZ (F.X i) SZ 0 1 true, gFloorZ (F.X i) SZ 0 2 true]

/-- The solver's settings: differences of `2 ^ 32`, a pad of `2 ^ 8`, three Newton steps for the first
member and two for each later one, then up to 200 steps of the recursion. -/
def postSeeds (i : ℕ) : List (List ℤ) :=
  seedsZ F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (2 ^ 32) (2 ^ 8) 3 2 200 F.famL (F.floor i)

def preSeeds (i : ℕ) (post : List (List ℤ)) : List (List ℤ) :=
  preSeedsZ F.famL F.D F.Δ (F.X i) SZ (2 ^ 32) (2 ^ 8) 0 200 post

def swSeeds (i : ℕ) : List ℤ :=
  solveSeedsZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (2 ^ 32) (2 ^ 8) 3 200 (F.floor i)

def postTop (dat : IdxData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (dat.post.getD k.val [])

def preTop (dat : IdxData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (dat.pre.getD k.val [])

def eIn (dat : IdxData) (k : Fin F.S.K) : ℚ := dat.eIn.getD k.val 0

/-- A table's bound over the integers, as a rational. -/
def boundQ (B : BandZ) (i : ℕ) (v : ℕ → Fin 3 → Bool → ℤ) : ℚ :=
  (autoBoundZ B F.D (F.X i) SZ v : ℚ) / ((F.X i).M F.D * SZ : ℤ)

/-- The members' in-epoch bounds, rounded up to 13 digits. -/
def eInList (i : ℕ) (post : List (List ℤ)) : List ℚ := eInListQ F.famL F.D F.Δ (F.X i) SZ 13 post

/-- The largest pre-switch bound, rounded up to 13 digits. -/
def eEOf (i : ℕ) (post pre : List (List ℤ)) : ℚ :=
  let vm := vmaxListZ F.famL F.D F.Δ (F.X i) SZ post
  (List.zipWith (fun B t => rupQ 13 (F.boundQ B i (tabZ (fillRowsZ [B] F.D F.Δ (F.X i) SZ (tabZ vm) (seedL t) 0 F.Δ))))
    F.famL pre).foldl max 0

/-- The switching table's largest bound, rounded up to 13 digits. -/
def eSOf (i : ℕ) (vs : List ℤ) : ℚ :=
  let v := tabZ (fillRowsZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (seedL vs) 0 F.Δ)
  (F.famL.map fun B => rupQ 13 (F.boundQ B i v)).foldl max 0

/-- The indices with a switching table, and with one-switch tables. -/
def isSw (i : ℕ) : Bool := i == 0 || i == 1 || i == 2 || i == 17

def isOne (i : ℕ) : Bool := !(i == 2 || i == 17)

/-- **Every check of index `i`.** -/
def idxChk (i : ℕ) (dat : IdxData) : Bool :=
  decide ((F.X i).Rep (xgNQ F.c F.z F.s F.d F.τ i).1 (xgNQ F.c F.z F.s F.d F.τ i).2.1 (xgNQ F.c F.z F.s F.d F.τ i).2.2) &&
    (!isSw i || (List.finRange F.S.K).all (chkSwF F.famZ F.D F.Δ (F.X i) SZ (seedL dat.vs) fun _ => dat.eS)) &&
    (!isOne i || (List.finRange F.S.K).all (chkOneF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) (F.preTop dat) (F.eIn dat) dat.eE))

/-- The tables, over `ℝ`. -/
noncomputable def vsR (i : ℕ) (dat : IdxData) : ℕ → Fin 3 → Bool → ℝ :=
  castT (castZ SZ (fillAllZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (seedL dat.vs)))

noncomputable def vpostR (i : ℕ) (dat : IdxData) (k : Fin F.S.K) : ℕ → Fin 3 → Bool → ℝ :=
  castT (castZ SZ (postF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) k))

noncomputable def vpreR (i : ℕ) (dat : IdxData) (k : Fin F.S.K) : ℕ → Fin 3 → Bool → ℝ :=
  castT (castZ SZ (preF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) (F.preTop dat) k))

noncomputable def vmaxR (i : ℕ) (dat : IdxData) : ℕ → Fin 3 → Bool → ℝ :=
  castT (castZ SZ (vmaxF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat)))

/-- `xg` at the potential's parameters, over `ℝ`. -/
noncomputable abbrev xgR (i : Fin 19) := xg F.c F.z F.s F.d F.τ i

section Sound

variable {F} (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) {i : Fin 19} {dat : IdxData}
  (h : F.idxChk i dat = true)
include hS hD h

theorem idx_rep : (F.X i).Rep (xgNQ F.c F.z F.s F.d F.τ i).1 (xgNQ F.c F.z F.s F.d F.τ i).2.1
    (xgNQ F.c F.z F.s F.d F.τ i).2.2 := by
  simp only [idxChk, Bool.and_eq_true, decide_eq_true_eq] at h; exact h.1.1

/-- **A switching index's table** solves every member's recursion within its bound. -/
theorem idx_sw (hi : isSw i = true) :
    (∀ k, AutoSol (F.S.fam k) F.Δ (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat)) ∧
      ∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat) ≤ dat.eS := by
  have hX := idx_rep hS hD h
  simp only [idxChk, hi, Bool.not_true, Bool.false_or, Bool.and_eq_true] at h
  have := switchF_sound (eS := fun _ => dat.eS) (F.S.rep hS) F.S.agrees hD hX SZ_pos h.1.2
  rw [xgR, xg_ofQ rfl rfl rfl rfl rfl i]
  exact this

/-- **A one-switch index's tables** solve every member's recursions within their bounds. -/
theorem idx_one (hi : isOne i = true) :
    AutoSolE F.S.fam F.Δ (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpreR i dat) (F.vpostR i dat) (F.vmaxR i dat) ∧
      (∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpostR i dat k) ≤ F.eIn dat k) ∧
      ∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpreR i dat k) ≤ dat.eE := by
  have hX := idx_rep hS hD h
  simp only [idxChk, hi, Bool.not_true, Bool.false_or, Bool.and_eq_true] at h
  have := oneSwitchF_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos h.2
  rw [xgR, xg_ofQ rfl rfl rfl rfl rfl i]
  exact this

end Sound

/-! ## The potential's expectations from the tables -/

/-- `e i`: the one-switch bound, or the switching one for indices 2 and 17. -/
def eOf (dat : Fin 19 → IdxData) (i : Fin 19) : ℚ := if isOne i then (dat i).eE else (dat i).eS

def lrOf (dat : Fin 19 → IdxData) : ℚ := max (dat 0).eS (dat 0).eE

def bOf (dat : Fin 19 → IdxData) : ℚ := max (max (dat 1).eS (dat 1).eE) 1

end FamCfg

/-! ## The certificates -/

/-- The basic conditions of `Cert2`, the class conditions and the reach recursion, over `ℚ`. -/
def cert2ChkQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ) : Bool :=
  decide (1 ≤ c) && decide (1 ≤ z) && decide (1 ≤ s) && decide (0 ≤ κ) && decide (0 < d) && decide (d ≤ 1) &&
    decide (s + κ ≤ z) && decide (1 ≤ τ) && decide (0 ≤ lp) && decide (lp < 1) && decide (0 ≤ lr) && decide (lr < 1) &&
    decide (1 ≤ b) && decide (0 ≤ Bq.elo) && decide (0 < Δ) && decide (1 ≤ e 17) && decide (e 0 ≤ lr) && decide (e 1 ≤ b) &&
    classOKQ c z s κ d lp e (Bq.slo * Bq.elo ^ Δ)

/-- The conditions `cert2ChkQ` checks, by name. -/
structure Cert2FactsQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ) : Prop where
  hc : 1 ≤ c
  hz : 1 ≤ z
  hs : 1 ≤ s
  hκ : 0 ≤ κ
  hd0 : 0 < d
  hd1 : d ≤ 1
  hsz : s + κ ≤ z
  hτ : 1 ≤ τ
  hlp0 : 0 ≤ lp
  hlp : lp < 1
  hlr0 : 0 ≤ lr
  hlr1 : lr < 1
  hb1 : 1 ≤ b
  helo : 0 ≤ Bq.elo
  hΔ : 0 < Δ
  he17 : 1 ≤ e 17
  hlr : e 0 ≤ lr
  hb : e 1 ≤ b
  w1 : e 0 ≤ lp
  w0 : e 1 - (1 - (s + κ) * z⁻¹) * (Bq.slo * Bq.elo ^ Δ) ≤ lp
  m1r0 : s * (e 3 - lp) + κ * (e 7 - lp) ≤ 0
  m1r1 : s * c * (e 4 - lp) + κ * d * (e 8 - lp) ≤ 0
  m1r2 : s * c ^ 2 * (e 4 - lp) + κ * d ^ 2 * (e 9 - lp) ≤ 0
  m1r3a : e 4 ≤ lp
  m1r3 : s * c ^ 3 * (e 4 - lp) + κ * d ^ 3 * max (e 10 - lp) 0 + κ * e 15 ≤ 0
  m2r0 : s * (e 5 - lp) + κ * (e 11 - lp) ≤ 0
  m2r1 : s * c * (e 6 - lp) + κ * d * (e 12 - lp) ≤ 0
  m2r2 : s * c ^ 2 * (e 6 - lp) + κ * d ^ 2 * (e 13 - lp) ≤ 0
  m2r3a : e 6 ≤ lp
  m2r3 : s * c ^ 3 * (e 6 - lp) + κ * d ^ 3 * max (e 14 - lp) 0 + κ * e 16 ≤ 0

theorem cert2ChkQ.facts {Bq : BandR} {Δ : ℕ} {c z s κ d τ lp lr b : ℚ} {e : Fin 19 → ℚ}
    (h : cert2ChkQ Bq Δ c z s κ d τ lp lr b e = true) : Cert2FactsQ Bq Δ c z s κ d τ lp lr b e := by
  simp only [cert2ChkQ, classOKQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨hc, hz⟩, hs⟩, hκ⟩, hd0⟩, hd1⟩, hsz⟩, hτ⟩, hlp0⟩, hlp⟩, hlr0⟩, hlr1⟩, hb1⟩, helo⟩, hΔ⟩, he17⟩, hlr⟩, hb⟩, ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨w1, w0⟩, m1r0⟩, m1r1⟩, m1r2⟩, m1r3a⟩, m1r3⟩, m2r0⟩, m2r1⟩, m2r2⟩, m2r3a⟩, m2r3⟩⟩ := h
  exact ⟨hc, hz, hs, hκ, hd0, hd1, hsz, hτ, hlp0, hlp, hlr0, hlr1, hb1, helo, hΔ, he17, hlr, hb, w1, w0, m1r0, m1r1, m1r2, m1r3a, m1r3, m2r0, m2r1, m2r2, m2r3a, m2r3⟩

/-- **The potential certificate** from its numbers, with an empty family (`Cert2E` gives the
phase bounds). -/
noncomputable def Cert2.ofQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ)
    (h : cert2ChkQ Bq Δ c z s κ d τ lp lr b e = true) : Cert2 Bq.toBand Δ where
  c := c
  z := z
  s := s
  κ := κ
  d := d
  τ := τ
  lp := lp
  lr := lr
  b := b
  v := fun _ _ _ _ => 0
  e := fun i => e i
  hc := by exact_mod_cast (cert2ChkQ.facts h).hc
  hz := by exact_mod_cast (cert2ChkQ.facts h).hz
  hs := by exact_mod_cast (cert2ChkQ.facts h).hs
  hκ := by exact_mod_cast (cert2ChkQ.facts h).hκ
  hd0 := by exact_mod_cast (cert2ChkQ.facts h).hd0
  hd1 := by exact_mod_cast (cert2ChkQ.facts h).hd1
  hsz := by exact_mod_cast (cert2ChkQ.facts h).hsz
  hτ := by exact_mod_cast (cert2ChkQ.facts h).hτ
  hlp0 := by exact_mod_cast (cert2ChkQ.facts h).hlp0
  hlp := by exact_mod_cast (cert2ChkQ.facts h).hlp
  hlr0 := by exact_mod_cast (cert2ChkQ.facts h).hlr0
  hlr1 := by exact_mod_cast (cert2ChkQ.facts h).hlr1
  hb1 := by exact_mod_cast (cert2ChkQ.facts h).hb1
  helo := by simp only [BandR.toBand_elo]; exact_mod_cast (cert2ChkQ.facts h).helo
  hΔ := (cert2ChkQ.facts h).hΔ
  Bs := []
  weak := fun _ hB => by simp at hB
  sol := fun _ _ hB => by simp at hB
  he := fun _ _ hB => by simp at hB
  he17 := by exact_mod_cast (cert2ChkQ.facts h).he17
  hlr := by exact_mod_cast (cert2ChkQ.facts h).hlr
  hb := by exact_mod_cast (cert2ChkQ.facts h).hb
  w1 := by exact_mod_cast (cert2ChkQ.facts h).w1
  w0 := by simp only [BandR.toBand_slo, BandR.toBand_elo]; exact_mod_cast (cert2ChkQ.facts h).w0
  m1r0 := by exact_mod_cast (cert2ChkQ.facts h).m1r0
  m1r1 := by exact_mod_cast (cert2ChkQ.facts h).m1r1
  m1r2 := by exact_mod_cast (cert2ChkQ.facts h).m1r2
  m1r3a := by exact_mod_cast (cert2ChkQ.facts h).m1r3a
  m1r3 := by exact_mod_cast (cert2ChkQ.facts h).m1r3
  m2r0 := by exact_mod_cast (cert2ChkQ.facts h).m2r0
  m2r1 := by exact_mod_cast (cert2ChkQ.facts h).m2r1
  m2r2 := by exact_mod_cast (cert2ChkQ.facts h).m2r2
  m2r3a := by exact_mod_cast (cert2ChkQ.facts h).m2r3a
  m2r3 := by exact_mod_cast (cert2ChkQ.facts h).m2r3

namespace FamCfg

variable (F : FamCfg)

theorem isOne_of {i : Fin 19} (h2 : i ≠ 2) (h17 : i ≠ 17) : isOne i = true := by
  revert h2 h17; revert i; decide

theorem isSw_of {i : Fin 19} (hi : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) : isSw i = true := by
  rcases hi with rfl | rfl | rfl | rfl <;> rfl

/-- Each member's in-epoch bounds, by index (`0` where there is no one-switch table). -/
def eiQ (dat : Fin 19 → IdxData) (k : Fin F.S.K) (i : Fin 19) : ℚ := if isOne i then F.eIn (dat i) k else 0

/-- **The checks of the main file**: the potential's conditions, the in-epoch contraction, and
every member's class conditions. -/
def mainChk (Bq : BandR) (κ lp lpi : ℚ) (dat : Fin 19 → IdxData) : Bool :=
  cert2ChkQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) && decide (0 < lpi) &&
    decide (lpi ≤ lp) && (List.finRange F.S.K).all fun k => classOKQ F.c F.z F.s κ F.d lpi (F.eiQ dat k) (F.S.patQ F.Δ k)

section Certs

variable {F} {Bq : BandR} {κ lp lpi : ℚ} {dat : Fin 19 → IdxData} (hM : F.mainChk Bq κ lp lpi dat = true)
include hM

theorem mainChk_P : cert2ChkQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) = true := by
  simp only [mainChk, Bool.and_eq_true] at hM; exact hM.1.1.1

/-- **The potential certificate**, its expectations the tables' bounds. -/
noncomputable def cert2 : Cert2 Bq.toBand F.Δ :=
  Cert2.ofQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) (mainChk_P hM)

variable (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
  (hidx : ∀ i : Fin 19, F.idxChk i (dat i) = true)

/-- **The multi-epoch certificate** from the index checks. -/
noncomputable def cert2E (EL G : ℕ) (hG : F.Δ + 1 ≤ G) (hGEL : G + 1 < EL) : Cert2E Bq.toBand F.Δ F.S.fam EL G where
  P := cert2 hM
  weakF := fun k => hBq ▸ F.S.weak hS k
  hG := hG
  hGEL := hGEL
  vs := fun i => F.vsR i (dat i)
  solS := fun i hi k => (idx_sw hS hD (hidx i) (isSw_of hi)).1 k
  heS0 := fun k => ((idx_sw hS hD (hidx 0) rfl).2 k).trans (by
    show ((dat 0).eS : ℝ) ≤ ((max (dat 0).eS (dat 0).eE : ℚ) : ℝ); exact_mod_cast le_max_left _ _)
  heS1 := fun k => ((idx_sw hS hD (hidx 1) rfl).2 k).trans (by
    show ((dat 1).eS : ℝ) ≤ ((max (max (dat 1).eS (dat 1).eE) 1 : ℚ) : ℝ)
    exact_mod_cast (le_max_left _ _).trans (le_max_left _ _))
  heS2 := fun k => ((idx_sw hS hD (hidx 2) rfl).2 k).trans le_rfl
  heS17 := fun k => ((idx_sw hS hD (hidx 17) rfl).2 k).trans le_rfl
  vpre := fun i => F.vpreR i (dat i)
  vpost := fun i => F.vpostR i (dat i)
  vmax := fun i => F.vmaxR i (dat i)
  solE := fun i h2 h17 => (idx_one hS hD (hidx i) (isOne_of h2 h17)).1
  heE := fun i h2 h17 k => ((idx_one hS hD (hidx i) (isOne_of h2 h17)).2.2 k).trans (by
    show ((dat i).eE : ℝ) ≤ ((eOf dat i : ℚ) : ℝ); rw [eOf, if_pos (isOne_of h2 h17)])

/-- **The certificate with an in-epoch contraction.** -/
noncomputable def cert3E (EL G : ℕ) (hG : F.Δ + 1 ≤ G) (hGEL : G + 1 < EL) : Cert3E Bq.toBand F.Δ F.S.fam EL G where
  C := cert2E hM hS hD hBq hidx EL G hG hGEL
  lpi := lpi
  ei := fun k i => F.eiQ dat k i
  pat0 := fun k => F.S.patQ F.Δ k
  hcl := fun k => by
    simp only [mainChk, Bool.and_eq_true] at hM
    exact ClassOK.ofQ rfl rfl rfl rfl rfl rfl (fun _ => rfl) rfl (List.all_eq_true.1 hM.2 k (List.mem_finRange k))
  hlpi0 := by simp only [mainChk, Bool.and_eq_true, decide_eq_true_eq] at hM; exact_mod_cast hM.1.1.2
  hlpi := by
    show (lpi : ℝ) ≤ (lp : ℝ)
    simp only [mainChk, Bool.and_eq_true, decide_eq_true_eq] at hM; exact_mod_cast hM.1.2
  hpat := F.S.pat_le F.Δ
  helo := F.S.elo hS
  heIn := fun i h2 h17 k => ((idx_one hS hD (hidx i) (isOne_of h2 h17)).2.1 k).trans (by
    show ((F.eIn (dat i) k : ℚ) : ℝ) ≤ ((F.eiQ dat k i : ℚ) : ℝ); rw [eiQ, if_pos (isOne_of h2 h17)])

end Certs

end FamCfg

end Cryptarchia.Prob
