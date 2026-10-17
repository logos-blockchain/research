module

public import Cryptarchia.Prob.Burst
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Ring.Star
import Mathlib.Algebra.Order.Star.Real
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
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.ENatToNat
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.Monotonicity.Lemmas
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
import Mathlib.Tactic.Polynomial.Basic
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Presheaf
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Phase expectations through a small automaton

A sharper version of `phase_upper`. Over one phase, we bound

  `E[θ^L · x^A · g(min(A, 2), B, U2)]`

for any nonnegative table `g`, where `A` counts adversarial slots, `B` says the phase
has an honest success, and `U2` says it has at least two slots with honest successes.
During a burst the automaton tracks the slots since the last honest success (`q`),
`min(A, 2)` and `U2`; a solution `v` of its recursion (`AutoSol`) bounds the rest of
the phase from every state (`phase_autoT`, `AutoE.lean`). Each step is bounded for every
next-slot distribution in the band (`slot_sum4`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

variable {κ : Kern} {B : Band}

/-- **One slot, four outcome classes.** `F h a` is the value after a slot with
(`h`) or without an honest success and with (`a`) or without an adversarial one. -/
theorem slot_sum4 {l : List Out} (hB : κ.BandAt B l) (F : Bool → Bool → ℝ) :
    ∑ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv ≤
      F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
        (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
        (F true true - F true false - F false true + F false false) *
          (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
  set c1 := F false true - F false false
  set c2 := F true false - F false false
  set c3 := F true true - F true false - F false true + F false false
  have hsplit : ∀ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv =
      κ.p l o * F false false + c1 * (if o.adv = true then κ.p l o else 0) +
        c2 * (if o.hon ≠ 0 then κ.p l o else 0) + c3 * (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) := by
    intro o
    by_cases h1 : o.hon ≠ 0 <;> by_cases h2 : o.adv = true <;> simp [h1, h2, c1, c2, c3] <;> ring
  simp only [hsplit, Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.sum_mul, κ.sum_one, one_mul]
  have e1 : ∑ o, (if o.adv = true then κ.p l o else 0) = κ.pr l (fun o => o.adv = true) := rfl
  have e2 : ∑ o, (if o.hon ≠ 0 then κ.p l o else 0) = κ.pr l (fun o => o.hon ≠ 0) := rfl
  have e3 : ∑ o, (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) =
      κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) := rfl
  rw [e1, e2, e3]
  have ha := hB.amax
  have ha0 := pr_nonneg (κ := κ) l (fun o => o.adv = true)
  have hh := hB.hhi
  have hlo := hB.hlo
  have hha := hB.hahi
  have hha0 := pr_nonneg (κ := κ) l (fun o => o.hon ≠ 0 ∧ o.adv = true)
  have t1 : c1 * κ.pr l (fun o => o.adv = true) ≤
      c1 * (if F false false ≤ F false true then B.amax else B.alo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left ha (by simp only [c1]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.alo) (by simp only [c1]; linarith)
  have t2 : c2 * κ.pr l (fun o => o.hon ≠ 0) ≤
      c2 * (if F false false ≤ F true false then B.hhi else B.hlo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hh (by simp only [c2]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left hlo (by simp only [c2]; linarith)
  have t3 : c3 * κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤
      c3 * (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hha (by simp only [c3]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.halo) (by simp only [c3]; linarith)
  linarith

/-- The bound `slot_sum4` gives, as a function. -/
noncomputable def slot4 (B : Band) (F : Bool → Bool → ℝ) : ℝ :=
  F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

/-! ## The phase summary -/

/-- Honest slots in `(a, b]`. -/
def honCnt (w : CStr) (a b : ℕ) : ℕ := ((Finset.Ioc a b).filter (fun j => (w j).1 ≠ 0)).card

/-- `min(A, 2)`. -/
def acap (n : ℕ) : Fin 3 := ⟨min n 2, by omega⟩

/-- The weight of a history for a phase that started at `m`, with table `g`. -/
noncomputable def Wt2 (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
    g (acap (advCnt (strOf h) m h.length)) (decide (1 ≤ honCnt (strOf h) m h.length))
      (decide (2 ≤ honCnt (strOf h) m h.length))

/-- A solution of the automaton recursion for adversary factor `x`, tilt `θ` and
terminal table `g`: `v q a u2` bounds the rest of a burst `q` slots after its last
honest success, with `min(A, 2) = a` and `U2 = u2` so far. -/
structure AutoSol (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (v : ℕ → Fin 3 → Bool → ℝ) : Prop where
  /-- a run cut by the horizon is covered -/
  term : ∀ q < Δ, ∀ a u2, g a true u2 ≤ v q a u2
  /-- the recursion -/
  step : ∀ q < Δ, ∀ a u2, θ * slot4 B (fun hh aa =>
    (if aa then x else 1) *
      (if hh then v 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u2
          else v (q + 1) (acap (a.val + if aa then 1 else 0)) u2)) ≤ v q a u2

variable {Δ M : ℕ}

theorem honCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    honCnt w a (b + 1) = honCnt w a b + (if (w (b + 1)).1 ≠ 0 then 1 else 0) := by
  unfold honCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem honCnt_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : honCnt w a b = honCnt w' a b := by
  unfold honCnt
  congr 1
  apply Finset.filter_congr
  intro j hj
  rw [Finset.mem_Ioc] at hj
  exact not_congr (h j hj.1 hj.2).1

theorem honCnt_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    honCnt (strOf (x ++ [o])) m (x.length + 1) = honCnt (strOf x) m x.length + (if o.hon ≠ 0 then 1 else 0) := by
  rw [honCnt_succ _ hm, honCnt_congr (strOf_sim x [o] m), strOf_last]
  congr 1
  simp only [Out.toPair, ne_eq]
  by_cases h : o.hon = 0
  · simp [h]
  · have : ¬ (o.hon.val = 0) := fun h' => h (Fin.ext h')
    simp [h, this]

theorem acap_add (n : ℕ) (b : ℕ) (hb : b ≤ 1) : acap (n + b) = acap ((acap n).val + b) := by
  unfold acap; ext; simp; omega

theorem Wt2_snoc {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} {m : ℕ} (h : List Out) (o : Out) (hm : m ≤ h.length) :
    Wt2 x θ g m (h ++ [o]) =
      θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * (θ * (if o.adv then x else 1)) *
        g (acap ((acap (advCnt (strOf h) m h.length)).val + if o.adv then 1 else 0))
          (decide (1 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0))
          (decide (2 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0)) := by
  unfold Wt2
  simp only [List.length_append, List.length_singleton]
  rw [advCnt_snoc h o hm, honCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega,
    pow_succ, ← acap_add _ _ (by split_ifs <;> norm_num)]
  by_cases ha : o.adv = true
  · simp only [ha, ↓reduceIte, pow_succ]; ring
  · simp only [ha, Bool.false_eq_true, ↓reduceIte, add_zero, mul_one]; ring

/-- The bound for one phase from its start. -/
noncomputable def autoBound (B : Band) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (v : ℕ → Fin 3 → Bool → ℝ) : ℝ :=
  θ * slot4 B (fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false))

end Cryptarchia.Prob
