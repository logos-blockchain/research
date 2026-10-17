module

public import Cryptarchia.Prob.AutoQ
public import Cryptarchia.Prob.Cold2E
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
# Automaton checks over the integers, with computed tables

The checks of `AutoQ`, in integer arithmetic. A band's `slot4` fields are integers over a
common denominator `D` (`BandZ.Rep`), a phase expectation's `x`, `θ`, `g` integers over
their own denominators (`PhZ.Rep`), and a table integers over a scale `S`. Every check is
then a comparison of integers, exactly equivalent to the rational one (`stepZ_cast`,
`slot4Z_cast`), and the kernel evaluates it with its arbitrary-precision `Nat` arithmetic,
without the normalization of rationals.

A table checked by `autoSolZ` or `preSolZ` refers back to itself only through the three
entries `v 0 a true`, the state just after an honest success; every other entry is one
recursion step from the next row. `fillZ` computes the table from those three entries
(`top`), row by row from `q = Δ - 1` down, each step rounded up to the scale and floored at
`lo`; `fillAllZ` does the same with the step's maximum over several bands. A certificate
gives only the three entries per table. The tables are then checked as before, so neither
needs a soundness theorem: a wrong entry makes a check fail.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-- The fields of a band that `slot4` reads, as integers over a common denominator. -/
structure BandZ where
  hhi : ℤ
  hlo : ℤ
  amax : ℤ
  hahi : ℤ
  alo : ℤ
  halo : ℤ

/-- `B / D` has the values of `b`. -/
structure BandZ.Rep (B : BandZ) (D : ℤ) (b : BandQ) : Prop where
  hhi : b.hhi = (B.hhi : ℚ) / D
  hlo : b.hlo = (B.hlo : ℚ) / D
  amax : b.amax = (B.amax : ℚ) / D
  hahi : b.hahi = (B.hahi : ℚ) / D
  alo : b.alo = (B.alo : ℚ) / D
  halo : b.halo = (B.halo : ℚ) / D

instance (B : BandZ) (D : ℤ) (b : BandQ) : Decidable (B.Rep D b) :=
  decidable_of_iff (b.hhi = (B.hhi : ℚ) / D ∧ b.hlo = (B.hlo : ℚ) / D ∧ b.amax = (B.amax : ℚ) / D ∧
      b.hahi = (B.hahi : ℚ) / D ∧ b.alo = (B.alo : ℚ) / D ∧ b.halo = (B.halo : ℚ) / D)
    ⟨fun ⟨h1, h2, h3, h4, h5, h6⟩ => ⟨h1, h2, h3, h4, h5, h6⟩,
      fun h => ⟨h.hhi, h.hlo, h.amax, h.hahi, h.alo, h.halo⟩⟩

/-- `slot4`, times `D`, over the integers. -/
def slot4Z (B : BandZ) (D : ℤ) (F : Bool → Bool → ℤ) : ℤ :=
  F false false * D + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

theorem slot4Z_cast {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) (F : Bool → Bool → ℤ)
    {c : ℚ} (hc : 0 < c) : (slot4Z B D F : ℚ) = D * c * slot4Q b (fun h a => (F h a : ℚ) / c) := by
  have hD' : (0 : ℚ) < D := by exact_mod_cast hD
  have e1 : ∀ x y : ℤ, ((x : ℚ) / c ≤ (y : ℚ) / c ↔ x ≤ y) := fun x y => by
    rw [div_le_div_iff_of_pos_right hc, Int.cast_le]
  have e2 : ∀ x y z w : ℤ, ((x : ℚ) / c + (y : ℚ) / c ≤ (z : ℚ) / c + (w : ℚ) / c ↔ x + y ≤ z + w) :=
    fun x y z w => by
      rw [← add_div, ← add_div, div_le_div_iff_of_pos_right hc, ← Int.cast_add, ← Int.cast_add, Int.cast_le]
  unfold slot4Z slot4Q
  simp only [e1, e2, hR.hhi, hR.hlo, hR.amax, hR.hahi, hR.alo, hR.halo]
  split_ifs <;> push_cast <;> field_simp

/-- A phase expectation's numbers over the integers: `x = xn / xd`, `θ = θn / θd`,
`g = gn / gd`. -/
structure PhZ where
  xn : ℤ
  xd : ℤ
  θn : ℤ
  θd : ℤ
  gn : Fin 3 → Bool → Bool → ℤ
  gd : ℤ

/-- `X` has the values `x`, `θ`, `g`, with positive denominators. -/
structure PhZ.Rep (X : PhZ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) : Prop where
  xd : 0 < X.xd
  θd : 0 < X.θd
  gd : 0 < X.gd
  x : x = (X.xn : ℚ) / X.xd
  θ : θ = (X.θn : ℚ) / X.θd
  g : ∀ a b u, g a b u = (X.gn a b u : ℚ) / X.gd

instance (X : PhZ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) : Decidable (X.Rep x θ g) :=
  decidable_of_iff (0 < X.xd ∧ 0 < X.θd ∧ 0 < X.gd ∧ x = (X.xn : ℚ) / X.xd ∧ θ = (X.θn : ℚ) / X.θd ∧
      ∀ a b u, g a b u = (X.gn a b u : ℚ) / X.gd)
    ⟨fun ⟨h1, h2, h3, h4, h5, h6⟩ => ⟨h1, h2, h3, h4, h5, h6⟩,
      fun h => ⟨h.xd, h.θd, h.gd, h.x, h.θ, h.g⟩⟩

/-- The scale of a step over the integers, apart from the table's: `θd · D · xd · gd`. -/
def PhZ.M (X : PhZ) (D : ℤ) : ℤ := X.θd * D * X.xd * X.gd

theorem PhZ.M_pos {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {D : ℤ} (hD : 0 < D) :
    0 < X.M D := by
  unfold PhZ.M; have := hX.xd; have := hX.θd; have := hX.gd; positivity

/-- The tables' scale: `2⁶⁴`. -/
def SZ : ℤ := 18446744073709551616

theorem SZ_pos : 0 < SZ := by decide

/-- A table of integers at scale `S`, over `ℚ`. -/
def castZ (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℚ := fun q a u => (v q a u : ℚ) / S

/-- A table from its integers listed by `(q, a, u)` in lexicographic order; `0` beyond. -/
def tabZ (l : List ℤ) : ℕ → Fin 3 → Bool → ℤ := fun q a u =>
  l.getD (6 * q + 2 * a.val + if u then 1 else 0) 0

/-- The left side of the recursion step, times `M · S`, for a successor table `w` at scale `S`. -/
def stepZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (w : ℕ → Fin 3 → Bool → ℤ) (q : ℕ) (a : Fin 3)
    (u : Bool) : ℤ :=
  X.θn * slot4Z B D (fun hh aa => (if aa then X.xn else X.xd) *
    (if hh then w 0 (acap (a.val + if aa then 1 else 0)) true * X.gd
      else if q + 1 = Δ then X.gn (acap (a.val + if aa then 1 else 0)) true u * S
        else w (q + 1) (acap (a.val + if aa then 1 else 0)) u * X.gd))

theorem stepZ_cast {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) (Δ : ℕ)
    (w : ℕ → Fin 3 → Bool → ℤ) (q : ℕ) (a : Fin 3) (u : Bool) :
    (stepZ B D Δ X S w q a u : ℚ) = (X.M D : ℚ) * S * stepQ b Δ x θ g (castZ S w) q a u := by
  have hxd : (0 : ℚ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℚ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℚ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  unfold stepZ stepQ
  rw [Int.cast_mul, slot4Z_cast hR hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then w 0 (acap (a.val + if aa then 1 else 0)) true * X.gd
        else if q + 1 = Δ then X.gn (acap (a.val + if aa then 1 else 0)) true u * S
          else w (q + 1) (acap (a.val + if aa then 1 else 0)) u * X.gd) : ℤ) : ℚ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then x else 1) *
        (if hh then castZ S w 0 (acap (a.val + if aa then 1 else 0)) true
          else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u
            else castZ S w (q + 1) (acap (a.val + if aa then 1 else 0)) u)) := by
    funext hh aa
    simp only [castZ, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-- `autoBound`, times `M · S`, over the integers. -/
def autoBoundZ (B : BandZ) (D : ℤ) (X : PhZ) (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℤ :=
  X.θn * slot4Z B D (fun hh aa => (if aa then X.xn else X.xd) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false * X.gd else X.gn (acap (if aa then 1 else 0)) false false * S))

theorem autoBoundZ_cast {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) (v : ℕ → Fin 3 → Bool → ℤ) :
    (autoBoundZ B D X S v : ℚ) = (X.M D : ℚ) * S * autoBoundQ b x θ g (castZ S v) := by
  have hxd : (0 : ℚ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℚ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℚ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  unfold autoBoundZ autoBoundQ
  rw [Int.cast_mul, slot4Z_cast hR hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then v 0 (acap (if aa then 1 else 0)) false * X.gd
        else X.gn (acap (if aa then 1 else 0)) false false * S) : ℤ) : ℚ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then x else 1) *
        (if hh then castZ S v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false)) := by
    funext hh aa
    simp only [castZ, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-! ## The checks -/

theorem allQ_mono {Δ : ℕ} {p p' : ℕ → Fin 3 → Bool → Bool}
    (h : ∀ q < Δ, ∀ a u, p q a u = true → p' q a u = true) (hp : allQ Δ p = true) : allQ Δ p' = true := by
  unfold allQ at hp ⊢
  rw [List.all_eq_true] at hp ⊢
  intro q hq
  have h6 := hp q hq
  have hq' := List.mem_range.1 hq
  simp only [all6, Bool.and_eq_true] at h6 ⊢
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩ := h6
  exact ⟨⟨⟨⟨⟨h q hq' _ _ h1, h q hq' _ _ h2⟩, h q hq' _ _ h3⟩, h q hq' _ _ h4⟩, h q hq' _ _ h5⟩, h q hq' _ _ h6⟩

/-- `AutoSol` over the integers. -/
def autoSolZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  allQ Δ fun q a u => decide (X.gn a true u * S ≤ v q a u * X.gd) && decide (stepZ B D Δ X S v q a u ≤ v q a u * X.M D)

theorem autoSolZ_sound {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ} {v : ℕ → Fin 3 → Bool → ℤ}
    (h : autoSolZ B D Δ X S v = true) : autoSolQ b Δ x θ g (castZ S v) = true := by
  have hgd : (0 : ℚ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  have hM : (0 : ℚ) < X.M D := by exact_mod_cast X.M_pos hX hD
  refine allQ_mono (fun q _ a u hp => ?_) h
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hp ⊢
  refine ⟨?_, ?_⟩
  · rw [hX.g, castZ, div_le_div_iff₀ hgd hS']; exact_mod_cast hp.1
  · have e := stepZ_cast hR hD hX hS Δ v q a u
    have h2 : (stepZ B D Δ X S v q a u : ℚ) ≤ (v q a u : ℚ) * X.M D := by exact_mod_cast hp.2
    rw [e] at h2
    rw [castZ, le_div_iff₀ hS']
    nlinarith [mul_pos hM hS']

/-- `PreSol` over the integers. -/
def preSolZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (vmax vpre : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  allQ Δ fun q a u => decide (vmax q a u ≤ vpre q a u) && decide (stepZ B D Δ X S vpre q a u ≤ vpre q a u * X.M D)

theorem preSolZ_sound {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ} {vmax vpre : ℕ → Fin 3 → Bool → ℤ}
    (h : preSolZ B D Δ X S vmax vpre = true) : preSolQ b Δ x θ g (castZ S vmax) (castZ S vpre) = true := by
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  have hM : (0 : ℚ) < X.M D := by exact_mod_cast X.M_pos hX hD
  refine allQ_mono (fun q _ a u hp => ?_) h
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hp ⊢
  refine ⟨?_, ?_⟩
  · simp only [castZ]; exact div_le_div_of_nonneg_right (by exact_mod_cast hp.1) hS'.le
  · have e := stepZ_cast hR hD hX hS Δ vpre q a u
    have h2 : (stepZ B D Δ X S vpre q a u : ℚ) ≤ (vpre q a u : ℚ) * X.M D := by exact_mod_cast hp.2
    rw [e] at h2
    rw [castZ, le_div_iff₀ hS']
    nlinarith [mul_pos hM hS']

/-- Domination `v ≤ w` below `Δ`, over the integers. -/
def leTabZ (Δ : ℕ) (v w : ℕ → Fin 3 → Bool → ℤ) : Bool := allQ Δ fun q a u => decide (v q a u ≤ w q a u)

theorem leTabZ_sound {Δ : ℕ} {S : ℤ} (hS : 0 < S) {v w : ℕ → Fin 3 → Bool → ℤ} (h : leTabZ Δ v w = true) :
    leTabQ Δ (castZ S v) (castZ S w) = true := by
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  refine allQ_mono (fun q _ a u hp => ?_) h
  simp only [decide_eq_true_eq] at hp ⊢
  simp only [castZ]; exact div_le_div_of_nonneg_right (by exact_mod_cast hp) hS'.le

theorem autoBoundZ_sound {B : BandZ} {D : ℤ} {b : BandQ} (hR : B.Rep D b) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {v : ℕ → Fin 3 → Bool → ℤ} {e : ℚ}
    (h : decide ((autoBoundZ B D X S v : ℚ) ≤ e * (X.M D * S : ℤ)) = true) :
    decide (autoBoundQ b x θ g (castZ S v) ≤ e) = true := by
  have hS' : (0 : ℚ) < S := by exact_mod_cast hS
  have hM : (0 : ℚ) < X.M D := by exact_mod_cast X.M_pos hX hD
  simp only [decide_eq_true_eq] at h ⊢
  rw [autoBoundZ_cast hR hD hX hS] at h
  push_cast at h
  have hMS := mul_pos hM hS'
  nlinarith

/-! ## Tables by backward recursion -/

/-- `n / m` rounded up, for `0 < m`. -/
def cdivZ (n m : ℤ) : ℤ := -((-n) / m)

/-- The row at `q` from the row at `q + 1` (`nxt`, six entries by `(a, u)`): the step's maximum
over the bands `Bs`, rounded up to the scale, floored at `lo`; `top a` at `(0, a, true)`. -/
def fillRowZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (top : Fin 3 → ℤ)
    (q : ℕ) (nxt : List ℤ) : List ℤ :=
  let w : ℕ → Fin 3 → Bool → ℤ := fun q' a u =>
    if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0
  let f : Fin 3 → Bool → ℤ := fun a u =>
    if q = 0 ∧ u = true then top a else
      Bs.foldl (fun m B => let s := cdivZ (stepZ B D Δ X S w q a u) (X.M D); if m ≤ s then s else m) (lo q a u)
  [f 0 false, f 0 true, f 1 false, f 1 true, f 2 false, f 2 true]

/-- The rows `q, …, q + n - 1`, listed by `(q, a, u)`. -/
def fillRowsZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (top : Fin 3 → ℤ) : ℕ → ℕ → List ℤ
  | _, 0 => []
  | q, n + 1 =>
    let r := fillRowsZ Bs D Δ X S lo top (q + 1) n
    fillRowZ Bs D Δ X S lo top q r ++ r

/-- The table for the bands `Bs` with entries `top a` at `(0, a, true)`, floored at `lo`. -/
def fillAllZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (top : Fin 3 → ℤ) : ℕ → Fin 3 → Bool → ℤ :=
  tabZ (fillRowsZ Bs D Δ X S lo top 0 Δ)

/-- The table for one band. -/
def fillZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (top : Fin 3 → ℤ) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ [B] D Δ X S lo top

/-- The terminal table `g` at scale `S`, rounded up: the floor of a post-switch table. -/
def gFloorZ (X : PhZ) (S : ℤ) : ℕ → Fin 3 → Bool → ℤ := fun _ a u => cdivZ (X.gn a true u * S) X.gd

/-! ## A whole index, for a family of bands -/

/-- **The one-switch tables of an index, for the whole family**, from the integer checks
for each member `k`: the post-switch table solves the member's recursion and lies below
`vmax`, the pre-switch table solves it above `vmax`, and both phase bounds hold. -/
theorem oneSwitchZ_sound {K : ℕ} {famZ : Fin K → BandZ} {D : ℤ} {famQ : Fin K → BandQ} {fam : Fin K → Band}
    (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ}
    {post pre : Fin K → ℕ → Fin 3 → Bool → ℤ} {vmax : ℕ → Fin 3 → Bool → ℤ} {eIn : Fin K → ℚ} {eE : ℚ}
    (h : ∀ k, (autoSolZ (famZ k) D Δ X S (post k) && leTabZ Δ (post k) vmax &&
      preSolZ (famZ k) D Δ X S vmax (pre k) &&
      decide ((autoBoundZ (famZ k) D X S (post k) : ℚ) ≤ eIn k * (X.M D * S : ℤ)) &&
      decide ((autoBoundZ (famZ k) D X S (pre k) : ℚ) ≤ eE * (X.M D * S : ℤ))) = true) :
    AutoSolE fam Δ x θ (castG g) (fun k => castT (castZ S (pre k))) (fun k => castT (castZ S (post k)))
        (castT (castZ S vmax)) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castT (castZ S (post k))) ≤ eIn k) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castT (castZ S (pre k))) ≤ eE) := by
  have hk : ∀ k, _ := fun k => h k
  simp only [Bool.and_eq_true] at hk
  refine ⟨AutoSolE.mk' (fun k => autoSol_ofQ (hA k) (autoSolZ_sound (hR k) hD hX hS (hk k).1.1.1.1))
    (fun k => leTab_ofQ (leTabZ_sound hS (hk k).1.1.1.2))
    (fun k => preSol_ofQ (hA k) (preSolZ_sound (hR k) hD hX hS (hk k).1.1.2)), fun k => ?_, fun k => ?_⟩
  · exact autoBound_le_ofQ (hA k) rfl (autoBoundZ_sound (hR k) hD hX hS (hk k).1.2)
  · exact autoBound_le_ofQ (hA k) rfl (autoBoundZ_sound (hR k) hD hX hS (hk k).2)

/-- **A switching table of an index, for the whole family**: it solves every member's
recursion, with each member's phase bound. -/
theorem switchZ_sound {K : ℕ} {famZ : Fin K → BandZ} {D : ℤ} {famQ : Fin K → BandQ} {fam : Fin K → Band}
    (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D) {X : PhZ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ}
    {vs : ℕ → Fin 3 → Bool → ℤ} {eS : Fin K → ℚ}
    (h : ∀ k, (autoSolZ (famZ k) D Δ X S vs &&
      decide ((autoBoundZ (famZ k) D X S vs : ℚ) ≤ eS k * (X.M D * S : ℤ))) = true) :
    (∀ k, AutoSol (fam k) Δ x θ (castG g) (castT (castZ S vs))) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castT (castZ S vs)) ≤ eS k) := by
  have hk : ∀ k, _ := fun k => h k
  simp only [Bool.and_eq_true] at hk
  exact ⟨fun k => autoSol_ofQ (hA k) (autoSolZ_sound (hR k) hD hX hS (hk k).1),
    fun k => autoBound_le_ofQ (hA k) rfl (autoBoundZ_sound (hR k) hD hX hS (hk k).2)⟩

/-! ## The class conditions -/

/-- `ClassOK` as a check over `ℚ`, at the potential's parameters `c z s κ d`. -/
def classOKQ (c z s κ d lp : ℚ) (e : Fin 19 → ℚ) (pat : ℚ) : Bool :=
  decide (e 0 ≤ lp) && decide (e 1 - (1 - (s + κ) * z⁻¹) * pat ≤ lp) &&
    decide (s * (e 3 - lp) + κ * (e 7 - lp) ≤ 0) && decide (s * c * (e 4 - lp) + κ * d * (e 8 - lp) ≤ 0) &&
    decide (s * c ^ 2 * (e 4 - lp) + κ * d ^ 2 * (e 9 - lp) ≤ 0) && decide (e 4 ≤ lp) &&
    decide (s * c ^ 3 * (e 4 - lp) + κ * d ^ 3 * max (e 10 - lp) 0 + κ * e 15 ≤ 0) &&
    decide (s * (e 5 - lp) + κ * (e 11 - lp) ≤ 0) && decide (s * c * (e 6 - lp) + κ * d * (e 12 - lp) ≤ 0) &&
    decide (s * c ^ 2 * (e 6 - lp) + κ * d ^ 2 * (e 13 - lp) ≤ 0) && decide (e 6 ≤ lp) &&
    decide (s * c ^ 3 * (e 6 - lp) + κ * d ^ 3 * max (e 14 - lp) 0 + κ * e 16 ≤ 0)

theorem ClassOK.ofQ {B : Band} {Δ : ℕ} {P : Cert2 B Δ} {c z s κ d lp pat : ℚ} {e : Fin 19 → ℚ}
    {lp' pat' : ℝ} {e' : Fin 19 → ℝ} (hc : P.c = c) (hz : P.z = z) (hs : P.s = s) (hκ : P.κ = κ)
    (hd : P.d = d) (hlp : lp' = lp) (he : ∀ i, e' i = e i) (hpat : pat' = pat)
    (h : classOKQ c z s κ d lp e pat = true) : ClassOK P lp' e' pat' := by
  simp only [classOKQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩, h10⟩, h11⟩, h12⟩ := h
  subst hlp hpat
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [he, hc, hz, hs, hκ, hd] <;>
    exact_mod_cast ‹_›

end Cryptarchia.Prob
