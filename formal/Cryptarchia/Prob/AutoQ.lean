module

public import Cryptarchia.Prob.CertE
public import Cryptarchia.Prob.Cold2
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
# Automaton checks by evaluation

Rational versions of the checks a generated certificate makes on its tables
(`AutoSol`, `PreSol`, the domination `post ≤ vmax`, and `autoBound ≤ e`), as Boolean
functions, each with its soundness theorem. A certificate states its tables over `ℚ`
(cast to `ℝ` by `castT`) and proves each check by `decide +kernel`: the kernel
evaluates it with its arbitrary-precision arithmetic, instead of `norm_num` over `ℝ`
case by case. This adds no axioms.
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

/-- `slot4` over `ℚ`. -/
def slot4Q (B : BandQ) (F : Bool → Bool → ℚ) : ℚ :=
  F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

theorem slot4_ofQ {b : BandQ} {B : Band} (h : b.Agrees B) (F : Bool → Bool → ℚ) :
    slot4 B (fun hh aa => (F hh aa : ℝ)) = (slot4Q b F : ℝ) := by
  have e1 : ((F false false : ℝ) ≤ F false true) ↔ F false false ≤ F false true := Rat.cast_le
  have e2 : ((F false false : ℝ) ≤ F true false) ↔ F false false ≤ F true false := Rat.cast_le
  have e3 : ((F true false : ℝ) + F false true ≤ F true true + F false false) ↔
      F true false + F false true ≤ F true true + F false false := by
    rw [← Rat.cast_add, ← Rat.cast_add, Rat.cast_le]
  unfold slot4 slot4Q
  rw [h.hhi, h.hlo, h.amax, h.hahi, h.alo, h.halo]
  simp only [e1, e2, e3]
  split_ifs <;> push_cast <;> ring

/-! ## Tables -/

/-- A table over `ℚ`, cast to `ℝ`. -/
noncomputable def castT (v : ℕ → Fin 3 → Bool → ℚ) : ℕ → Fin 3 → Bool → ℝ := fun q a u => v q a u

/-- A terminal table over `ℚ`, cast to `ℝ`. -/
noncomputable def castG (g : Fin 3 → Bool → Bool → ℚ) : Fin 3 → Bool → Bool → ℝ := fun a b u => g a b u

/-- A table from its values listed by `(q, a, u)` in lexicographic order; `0` beyond. -/
def tabL (l : List ℚ) : ℕ → Fin 3 → Bool → ℚ := fun q a u =>
  l.getD (6 * q + 2 * a.val + if u then 1 else 0) 0

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

/-! ## The checks -/

/-- A predicate on the six `(a, u)` states. -/
def all6 (p : Fin 3 → Bool → Bool) : Bool :=
  p 0 false && p 0 true && p 1 false && p 1 true && p 2 false && p 2 true

/-- A predicate on every state with `q < Δ`. -/
def allQ (Δ : ℕ) (p : ℕ → Fin 3 → Bool → Bool) : Bool := (List.range Δ).all fun q => all6 (p q)

theorem allQ_sound {Δ : ℕ} {p : ℕ → Fin 3 → Bool → Bool} (h : allQ Δ p = true) :
    ∀ q < Δ, ∀ a u, p q a u = true := by
  intro q hq a u
  have h6 := List.all_eq_true.1 h q (List.mem_range.2 hq)
  simp only [all6, Bool.and_eq_true] at h6
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩ := h6
  fin_cases a <;> cases u <;> assumption

/-- The left side of the recursion step at state `(q, a, u)`, for successor table `w`. -/
def stepQ (B : BandQ) (Δ : ℕ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) (w : ℕ → Fin 3 → Bool → ℚ)
    (q : ℕ) (a : Fin 3) (u : Bool) : ℚ :=
  θ * slot4Q B (fun hh aa => (if aa then x else 1) *
    (if hh then w 0 (acap (a.val + if aa then 1 else 0)) true
      else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u
        else w (q + 1) (acap (a.val + if aa then 1 else 0)) u))

theorem stepQ_cast {b : BandQ} {B : Band} (hB : b.Agrees B) (Δ : ℕ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ)
    (w : ℕ → Fin 3 → Bool → ℚ) (q : ℕ) (a : Fin 3) (u : Bool) :
    (θ : ℝ) * slot4 B (fun hh aa => (if aa then (x : ℝ) else 1) *
      (if hh then castT w 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then castG g (acap (a.val + if aa then 1 else 0)) true u
          else castT w (q + 1) (acap (a.val + if aa then 1 else 0)) u)) = (stepQ b Δ x θ g w q a u : ℝ) := by
  unfold stepQ
  rw [Rat.cast_mul, ← slot4_ofQ hB]
  congr 2
  funext hh aa
  simp only [castT, castG]
  split_ifs <;> push_cast <;> ring

/-- `AutoSol` as a check. -/
def autoSolQ (B : BandQ) (Δ : ℕ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) (v : ℕ → Fin 3 → Bool → ℚ) : Bool :=
  allQ Δ fun q a u => decide (g a true u ≤ v q a u) && decide (stepQ B Δ x θ g v q a u ≤ v q a u)

theorem autoSol_ofQ {b : BandQ} {B : Band} (hB : b.Agrees B) {Δ : ℕ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} {v : ℕ → Fin 3 → Bool → ℚ} (h : autoSolQ b Δ x θ g v = true) :
    AutoSol B Δ x θ (castG g) (castT v) where
  term q hq a u := by
    have := allQ_sound h q hq a u
    simp only [Bool.and_eq_true, decide_eq_true_eq] at this
    exact Rat.cast_le.2 this.1
  step q hq a u := by
    have := allQ_sound h q hq a u
    simp only [Bool.and_eq_true, decide_eq_true_eq] at this
    rw [stepQ_cast hB]
    exact Rat.cast_le.2 this.2

/-- `PreSol` as a check. -/
def preSolQ (B : BandQ) (Δ : ℕ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) (vmax vpre : ℕ → Fin 3 → Bool → ℚ) : Bool :=
  allQ Δ fun q a u => decide (vmax q a u ≤ vpre q a u) && decide (stepQ B Δ x θ g vpre q a u ≤ vpre q a u)

theorem preSol_ofQ {b : BandQ} {B : Band} (hB : b.Agrees B) {Δ : ℕ} {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} {vmax vpre : ℕ → Fin 3 → Bool → ℚ} (h : preSolQ b Δ x θ g vmax vpre = true) :
    PreSol B Δ x θ (castG g) (castT vmax) (castT vpre) where
  dom q hq a u := by
    have := allQ_sound h q hq a u
    simp only [Bool.and_eq_true, decide_eq_true_eq] at this
    exact Rat.cast_le.2 this.1
  step q hq a u := by
    have := allQ_sound h q hq a u
    simp only [Bool.and_eq_true, decide_eq_true_eq] at this
    rw [stepQ_cast hB]
    exact Rat.cast_le.2 this.2

/-- Domination `v ≤ w` below `Δ` as a check. -/
def leTabQ (Δ : ℕ) (v w : ℕ → Fin 3 → Bool → ℚ) : Bool := allQ Δ fun q a u => decide (v q a u ≤ w q a u)

theorem leTab_ofQ {Δ : ℕ} {v w : ℕ → Fin 3 → Bool → ℚ} (h : leTabQ Δ v w = true) :
    ∀ q < Δ, ∀ a u, castT v q a u ≤ castT w q a u := fun q hq a u =>
  Rat.cast_le.2 (of_decide_eq_true (allQ_sound h q hq a u))

/-- `autoBound` over `ℚ`. -/
def autoBoundQ (B : BandQ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) (v : ℕ → Fin 3 → Bool → ℚ) : ℚ :=
  θ * slot4Q B (fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false))

theorem autoBound_le_ofQ {b : BandQ} {B : Band} (hB : b.Agrees B) {x θ : ℚ}
    {g : Fin 3 → Bool → Bool → ℚ} {v : ℕ → Fin 3 → Bool → ℚ} {e : ℚ} {e' : ℝ} (he : (e : ℝ) = e')
    (h : decide (autoBoundQ b x θ g v ≤ e) = true) : autoBound B x θ (castG g) (castT v) ≤ e' := by
  rw [← he]
  have hc : autoBound B x θ (castG g) (castT v) = (autoBoundQ b x θ g v : ℝ) := by
    unfold autoBound autoBoundQ
    rw [Rat.cast_mul, ← slot4_ofQ hB]
    congr 2
    funext hh aa
    simp only [castT, castG]
    split_ifs <;> push_cast <;> ring
  rw [hc]
  exact Rat.cast_le.2 (of_decide_eq_true h)

end Cryptarchia.Prob
