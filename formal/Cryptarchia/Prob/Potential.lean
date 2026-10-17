module

public import Cryptarchia.Settle.Phases
public import Mathlib.Basic.Real.Basic
import Cryptarchia.Settle.Reduce
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Ring.Star
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.Int.Star
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
import Mathlib.Topology.Sheaves.Init

/-!
# A potential for the reach and margin bounds

The settlement bound process (`step`, `Settle/Phases.lean`) moves the pair
`(ρ, μ)` (reach bound, margin bound) once per phase. We follow it with the
potential

  `V(ρ, μ) = c^ρ · z^min(μ, 0)`,    `c, z ≥ 1`.

Started from margin = reach, the process is always either **warm** (`μ = ρ ≥ 0`)
or **cold** (`μ < 0`) (`inv_step`). Over one phase with `A` adversarial slots,
`B` = "some honest success", and `X` = "the phase is a crossing" (one honest
leader, alone, no adversarial slot), the potential changes by at most:

* warm, `ρ ≥ 1`:  factor `c^(A - B)`                         (`warm_pos`)
* warm, `ρ = 0`:  to at most `c^A - X·(1 - 1/z)`             (`warm_zero`)
* cold:           factor `(c z)^A - [A = 0 ∧ B]·(1 - 1/z)`    (`cold_step`)

and a margin that is not cold at the next phase costs at most `V · z^A`
(`fail_le`). These are the only properties of the recurrences the probability
bound uses. Only `B` enters, not the honest depth itself: honest depth is at least
one in a phase with an honest success.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ : ℕ} {w : CStr}

/-! ## Honest depth facts -/

theorem hD_zero_of {a : ℕ} : ∀ b, (∀ i, a < i → i ≤ b → (w i).1 = 0) → hD Δ w a b = 0 := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro h
    unfold hD
    by_cases hb : b ≤ a
    · simp only [hb, ↓reduceDIte]
    · simp only [hb, ↓reduceDIte, h b (by omega) le_rfl, ↓reduceIte]
      exact ih (b - 1) (by omega) fun i h1 h2 => h i h1 (by omega)

theorem one_le_hD {a : ℕ} : ∀ b, (∃ i, a < i ∧ i ≤ b ∧ (w i).1 ≠ 0) → 1 ≤ hD Δ w a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    rintro ⟨i, h1, h2, h3⟩
    unfold hD
    have hb : ¬ b ≤ a := by omega
    simp only [hb, ↓reduceDIte]
    by_cases hw : (w b).1 = 0
    · simp only [hw, ↓reduceIte]
      have hib : i ≠ b := by rintro rfl; exact h3 hw
      exact ih (b - 1) (by omega) ⟨i, h1, by omega, h3⟩
    · simp only [hw, ↓reduceIte]; omega

/-- Slots with no honest success at the end do not change honest depth. -/
theorem hD_skip {a s : ℕ} (hs : a ≤ s) : ∀ b, s ≤ b → (∀ i, s < i → i ≤ b → (w i).1 = 0) →
    hD Δ w a b = hD Δ w a s := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro hsb h
    rcases Nat.eq_or_lt_of_le hsb with rfl | hlt
    · rfl
    · conv_lhs => unfold hD
      have hb : ¬ b ≤ a := by omega
      simp only [hb, ↓reduceDIte, h b hlt le_rfl, ↓reduceIte]
      exact ih (b - 1) (by omega) (by omega) fun i h1 h2 => h i h1 (by omega)

/-- A crossing phase has honest depth exactly one. -/
theorem hD_of_cross {ℓ a b : ℕ} (hX : Cross w ℓ a b) : hD Δ w a b = 1 := by
  obtain ⟨-, s, h1, h2, -, h4, h5⟩ := hX
  rw [hD_skip (Δ := Δ) (show a ≤ s by omega) b h2 fun i hi1 hi2 => h5 i (by omega) hi2 (by omega)]
  unfold hD
  have hb : ¬ s ≤ a := by omega
  have hw : (w s).1 ≠ 0 := by omega
  simp only [hb, ↓reduceDIte, hw, ↓reduceIte]
  rw [hD_zero_of (s - Δ - 1) fun i hi1 hi2 => h5 i hi1 (by omega) (by omega)]

/-- Some slot of `(a, b]` has an honest success. -/
def HonIn (w : CStr) (a b : ℕ) : Prop := ∃ i, a < i ∧ i ≤ b ∧ (w i).1 ≠ 0

theorem hD_ge_ind {a b : ℕ} [Decidable (HonIn w a b)] :
    (if HonIn w a b then 1 else 0 : ℤ) ≤ (hD Δ w a b : ℤ) := by
  split_ifs with h
  · exact_mod_cast one_le_hD b h
  · positivity

theorem honIn_of_cross {ℓ a b : ℕ} (hX : Cross w ℓ a b) : HonIn w a b := by
  obtain ⟨-, s, h1, h2, -, h4, -⟩ := hX
  exact ⟨s, h1, h2, by omega⟩

/-! ## The potential -/

/-- Warm (margin = reach ≥ 0) or cold (margin < 0), reach nonnegative. -/
def Inv (st : ℤ × ℤ) : Prop := 0 ≤ st.1 ∧ (st.2 = st.1 ∨ st.2 < 0) ∧ st.2 ≤ st.1

variable {c z s : ℝ}

theorem inv_start {ρ : ℤ} (h : 0 ≤ ρ) : Inv (ρ, ρ) := ⟨h, Or.inl rfl, le_rfl⟩

open Classical in
theorem inv_step {ℓ a b : ℕ} {st : ℤ × ℤ} (h : Inv st) : Inv (step Δ w ℓ a b st) := by
  obtain ⟨h0, h1, h2⟩ := h
  rw [step_cases ℓ a b st h2]
  set A : ℤ := (advCnt w a b : ℤ)
  set H : ℤ := (hD Δ w a b : ℤ)
  have hA : 0 ≤ A := by positivity
  have hH : 0 ≤ H := by positivity
  refine ⟨le_trans hA (le_max_right _ _), ?_, ?_⟩
  · by_cases hc : st.2 < -A
    · rw [if_pos hc]; right; omega
    · rw [if_neg hc]
      by_cases hx : Cross w ℓ a b
      · rw [if_pos hx]
        rcases h1 with h1 | h1
        · by_cases hρ : st.1 - H < 0
          · right; exact hρ
          · left
            have hA0 : A = 0 := by simp only [A]; exact_mod_cast hx.1
            rw [hA0]; omega
        · have hA0 : A = 0 := by simp only [A]; exact_mod_cast hx.1
          omega
      · rw [if_neg hx]; left; rfl
  · have := le_max_left (st.1 + A - H) A
    by_cases hc : st.2 < -A
    · rw [if_pos hc]; omega
    · rw [if_neg hc]
      by_cases hx : Cross w ℓ a b
      · rw [if_pos hx]
        have hA0 : A = 0 := by simp only [A]; exact_mod_cast hx.1
        have := le_max_left (st.1 + A - H) A
        omega
      · rw [if_neg hx]

/-- The reach bound after a phase: `ρ' ≤ ρ + A - B` from a positive reach, and
`ρ' = A` from zero. -/
theorem reach_step {ℓ a b : ℕ} [Decidable (HonIn w a b)] {st : ℤ × ℤ} (h0 : 0 ≤ st.1) (hm : st.2 ≤ st.1) :
    (step Δ w ℓ a b st).1 ≤
      (if 1 ≤ st.1 then st.1 + advCnt w a b - (if HonIn w a b then 1 else 0) else advCnt w a b) := by
  classical
  rw [step_cases ℓ a b st hm]
  simp only
  have hB := hD_ge_ind (Δ := Δ) (w := w) (a := a) (b := b)
  have hA : (0 : ℤ) ≤ advCnt w a b := by positivity
  have hH : (0 : ℤ) ≤ hD Δ w a b := by positivity
  by_cases h1 : 1 ≤ st.1
  · rw [if_pos h1]
    by_cases hb : HonIn w a b
    · rw [if_pos hb] at hB ⊢; apply max_le <;> omega
    · rw [if_neg hb] at hB ⊢; apply max_le <;> omega
  · rw [if_neg h1]; apply max_le <;> omega

theorem c_pow_reach (hc : 1 ≤ c) {ℓ a b : ℕ} [Decidable (HonIn w a b)] {st : ℤ × ℤ} (h0 : 0 ≤ st.1)
    (hm : st.2 ≤ st.1) :
    c ^ (step Δ w ℓ a b st).1 ≤
      (if 1 ≤ st.1 then c ^ st.1 * c ^ ((advCnt w a b : ℤ) - (if HonIn w a b then 1 else 0))
        else c ^ (advCnt w a b : ℤ)) := by
  have h := reach_step (Δ := Δ) (w := w) (ℓ := ℓ) (a := a) (b := b) h0 hm
  have hc0 : 0 < c := by linarith
  by_cases h1 : 1 ≤ st.1
  · rw [if_pos h1] at h ⊢
    rw [← zpow_add₀ hc0.ne']
    apply zpow_le_zpow_right₀ hc
    linarith
  · rw [if_neg h1] at h ⊢
    exact zpow_le_zpow_right₀ hc h

end Cryptarchia.Prob
