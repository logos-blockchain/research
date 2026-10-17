module

public import Cryptarchia.Prob.AutoE
public import Cryptarchia.Prob.Cold2
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

A certificate checks its automaton tables (`AutoSol`, `PreSol`, the domination by `vmax`,
`autoBound ≤ e`) by `decide +kernel`, in integer arithmetic. A band's `slot4` fields are
integers over a common denominator `D` (`BandZ.Rep`, against the rational fields `BandQ`), a
phase expectation's `x`, `θ`, `g` integers over their own denominators (`PhZ.Rep`, against
the rational `xgNQ`), and a table integers over a scale `S` (`castZ`). A recursion step and a
phase bound are then integers exactly proportional to the real ones (`stepZ_cast`,
`autoBoundZ_cast`), so an integer comparison gives the real one (`stepZ_le`, `autoBoundZ_le`),
and the kernel evaluates it with its arbitrary-precision `Nat` arithmetic. This adds no axioms.

A table refers back to itself only through the three entries `v 0 a true`, the state just
after an honest success; every other entry is one recursion step from the next row. `fillZ`
computes the table from those three entries (`top`), row by row from `q = Δ - 1` down, each
step rounded up to the scale and floored at `lo`; `fillAllZ` does the same with the step's
maximum over several bands. A certificate gives only the three entries per table.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-- The fields of a band that `slot4` reads, over `ℚ`. -/
structure BandQ where
  hhi : ℚ
  hlo : ℚ
  amax : ℚ
  hahi : ℚ
  alo : ℚ
  halo : ℚ

/-- `B` has the values of `b` in the fields `slot4` reads. -/
structure BandQ.Agrees (b : BandQ) (B : Band) : Prop where
  hhi : B.hhi = b.hhi
  hlo : B.hlo = b.hlo
  amax : B.amax = b.amax
  hahi : B.hahi = b.hahi
  alo : B.alo = b.alo
  halo : B.halo = b.halo

/-! ## Tables -/

/-- A terminal table over `ℚ`, cast to `ℝ`. -/
noncomputable def castG (g : Fin 3 → Bool → Bool → ℚ) : Fin 3 → Bool → Bool → ℝ := fun a b u => g a b u

/-- `gtab` over `ℚ`. -/
def gtabQ (t0 t1 t2 : Bool → Bool → ℚ) : Fin 3 → Bool → Bool → ℚ := fun a b u =>
  if a.val = 0 then t0 b u else if a.val = 1 then t1 b u else t2 b u

/-- `xgN` over `ℚ`. -/
def xgNQ (c z s d τ : ℚ) : ℕ → ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)
  | 0 => (c, 1, gtabQ (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1))
  | 1 => (c, 1, fun _ _ _ => 1)
  | 2 => (z, 1, gtabQ (fun b _ => if b then 1 else 0) (fun _ _ => 1) (fun _ _ => 1))
  | 3 => (c, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  | 4 => (c, 1, gtabQ (fun b _ => if b then (c * z)⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  | 5 => (c * z, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then s⁻¹ else 1))
  | 6 => (c * z, 1, gtabQ (fun b _ => if b then (c * z)⁻¹ else 1) (fun b _ => if b then (c * z)⁻¹ else 1)
      (fun b _ => if b then s⁻¹ else 1))
  | 7 => (d * z, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 8 => (d * z, 1, gtabQ (fun b _ => if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 9 => (d * z, 1, gtabQ (fun b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 10 => (d * z, 1, gtabQ (fun b u => if u then 0 else if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 11 => (d * z, 1, fun _ b _ => if b then z⁻¹ else 1)
  | 12 => (d * z, 1, fun _ b _ => if b then (d * z)⁻¹ else 1)
  | 13 => (d * z, 1, fun _ b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1)
  | 14 => (d * z, 1, fun _ b u => if u then 0 else if b then (d * z)⁻¹ else 1)
  | 15 => (z, 1, gtabQ (fun _ u => if u then z⁻¹ else 0) (fun _ _ => 0) (fun _ _ => 0))
  | 16 => (z, 1, fun _ _ u => if u then z⁻¹ else 0)
  | 17 => (1, τ, fun _ _ _ => 1)
  | _ => (1, 1, fun _ _ _ => 1)

/-- A triple over `ℚ`, cast to `ℝ`. -/
noncomputable def castX (p : ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)) : ℝ × ℝ × (Fin 3 → Bool → Bool → ℝ) :=
  ((p.1 : ℝ), (p.2.1 : ℝ), castG p.2.2)

theorem xgN_ofQ (c z s d τ : ℚ) (i : ℕ) :
    xgN (c : ℝ) z s d τ i = castX (xgNQ c z s d τ i) := by
  rcases i with _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | i <;>
    refine Prod.ext ?_ (Prod.ext ?_ ?_) <;> simp only [xgN, xgNQ, castX] <;> (try funext a b u) <;>
    (try simp only [castG, gtab, gtabQ]) <;> (try split_ifs) <;> push_cast <;> rfl

/-- `xg` at rational parameters, given as real literals. -/
theorem xg_ofQ {c z s d τ : ℚ} {c' z' s' d' τ' : ℝ} (hc : (c : ℝ) = c') (hz : (z : ℝ) = z')
    (hs : (s : ℝ) = s') (hd : (d : ℝ) = d') (hτ : (τ : ℝ) = τ') (i : Fin 19) :
    xg c' z' s' d' τ' i = castX (xgNQ c z s d τ i.val) := by
  subst hc hz hs hd hτ; exact xgN_ofQ c z s d τ i.val

/-! ## Over the integers -/

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

theorem slot4Z_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D)
    (F : Bool → Bool → ℤ) {c : ℝ} (hc : 0 < c) : (slot4Z B D F : ℝ) = D * c * slot4 Bb (fun h a => (F h a : ℝ) / c) := by
  have hD' : (0 : ℝ) < D := by exact_mod_cast hD
  have e1 : ∀ x y : ℤ, ((x : ℝ) / c ≤ (y : ℝ) / c ↔ x ≤ y) := fun x y => by
    rw [div_le_div_iff_of_pos_right hc, Int.cast_le]
  have e2 : ∀ x y z w : ℤ, ((x : ℝ) / c + (y : ℝ) / c ≤ (z : ℝ) / c + (w : ℝ) / c ↔ x + y ≤ z + w) :=
    fun x y z w => by
      rw [← add_div, ← add_div, div_le_div_iff_of_pos_right hc, ← Int.cast_add, ← Int.cast_add, Int.cast_le]
  unfold slot4Z slot4
  simp only [e1, e2, hA.hhi, hA.hlo, hA.amax, hA.hahi, hA.alo, hA.halo, hR.hhi, hR.hlo, hR.amax, hR.hahi, hR.alo,
    hR.halo]
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

/-- A table of integers at scale `S`, over `ℝ`. -/
noncomputable def castZ (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℝ := fun q a u => (v q a u : ℝ) / S

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

theorem stepZ_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D)
    {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) (Δ : ℕ)
    (w : ℕ → Fin 3 → Bool → ℤ) (q : ℕ) (a : Fin 3) (u : Bool) :
    (stepZ B D Δ X S w q a u : ℝ) = (X.M D : ℝ) * S * stepR Bb Δ x θ (castG g) (castZ S w) q a u := by
  have hxd : (0 : ℝ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℝ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  unfold stepZ stepR
  rw [Int.cast_mul, slot4Z_cast hR hA hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then w 0 (acap (a.val + if aa then 1 else 0)) true * X.gd
        else if q + 1 = Δ then X.gn (acap (a.val + if aa then 1 else 0)) true u * S
          else w (q + 1) (acap (a.val + if aa then 1 else 0)) u * X.gd) : ℤ) : ℝ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then (x : ℝ) else 1) *
        (if hh then castZ S w 0 (acap (a.val + if aa then 1 else 0)) true
          else if q + 1 = Δ then castG g (acap (a.val + if aa then 1 else 0)) true u
            else castZ S w (q + 1) (acap (a.val + if aa then 1 else 0)) u)) := by
    funext hh aa
    simp only [castZ, castG, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-- `autoBound`, times `M · S`, over the integers. -/
def autoBoundZ (B : BandZ) (D : ℤ) (X : PhZ) (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℤ :=
  X.θn * slot4Z B D (fun hh aa => (if aa then X.xn else X.xd) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false * X.gd else X.gn (acap (if aa then 1 else 0)) false false * S))

theorem autoBoundZ_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb)
    (hD : 0 < D) {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S)
    (v : ℕ → Fin 3 → Bool → ℤ) :
    (autoBoundZ B D X S v : ℝ) = (X.M D : ℝ) * S * autoBound Bb x θ (castG g) (castZ S v) := by
  have hxd : (0 : ℝ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℝ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  unfold autoBoundZ autoBound
  rw [Int.cast_mul, slot4Z_cast hR hA hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then v 0 (acap (if aa then 1 else 0)) false * X.gd
        else X.gn (acap (if aa then 1 else 0)) false false * S) : ℤ) : ℝ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then (x : ℝ) else 1) *
        (if hh then castZ S v 0 (acap (if aa then 1 else 0)) false else castG g (acap (if aa then 1 else 0)) false false)) := by
    funext hh aa
    simp only [castZ, castG, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-! ## The checks -/

section Checks

variable {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D) {X : PhZ}
  {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S)
include hR hA hD hX hS

/-- The recursion over the integers at a state gives it over `ℝ`. -/
theorem stepZ_le {Δ : ℕ} {w : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} {a : Fin 3} {u : Bool}
    (h : stepZ B D Δ X S w q a u ≤ w q a u * X.M D) : stepR Bb Δ x θ (castG g) (castZ S w) q a u ≤ castZ S w q a u := by
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have h2 : (stepZ B D Δ X S w q a u : ℝ) ≤ (w q a u : ℝ) * X.M D := by exact_mod_cast h
  rw [stepZ_cast hR hA hD hX hS] at h2
  rw [castZ, le_div_iff₀ hS']
  nlinarith [mul_pos hM hS']

/-- A phase bound over the integers gives it over `ℝ`. -/
theorem autoBoundZ_le {v : ℕ → Fin 3 → Bool → ℤ} {e : ℚ} (h : (autoBoundZ B D X S v : ℚ) ≤ e * (X.M D * S : ℤ)) :
    autoBound Bb x θ (castG g) (castZ S v) ≤ e := by
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have h2 : (autoBoundZ B D X S v : ℝ) ≤ (e : ℝ) * (X.M D * S : ℤ) := by exact_mod_cast h
  rw [autoBoundZ_cast hR hA hD hX hS] at h2
  push_cast at h2
  nlinarith [mul_pos hM hS']

end Checks

theorem castZ_le {S : ℤ} (hS : 0 < S) {v w : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} {a : Fin 3} {u : Bool}
    (h : v q a u ≤ w q a u) : castZ S v q a u ≤ castZ S w q a u :=
  div_le_div_of_nonneg_right (by exact_mod_cast h) (by exact_mod_cast hS.le)

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

theorem ClassOK.ofQ {c z s κ d lp pat : ℚ} {e : Fin 19 → ℚ} {c' z' s' κ' d' lp' pat' : ℝ}
    {e' : Fin 19 → ℝ} (hc : c' = c) (hz : z' = z) (hs : s' = s) (hκ : κ' = κ) (hd : d' = d) (hlp : lp' = lp)
    (he : ∀ i, e' i = e i) (hpat : pat' = pat)
    (h : classOKQ c z s κ d lp e pat = true) : ClassOK c' z' s' κ' d' lp' e' pat' := by
  simp only [classOKQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩, h10⟩, h11⟩, h12⟩ := h
  subst hc hz hs hκ hd hlp hpat
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [he] <;>
    exact_mod_cast ‹_›

end Cryptarchia.Prob
