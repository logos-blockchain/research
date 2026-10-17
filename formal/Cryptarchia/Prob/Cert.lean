module

public import Mathlib.Basic.Real.Basic
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
# Tools for numeric certificates

Large powers `β^n` (with `n` up to about `10^5`) are bounded by processing the bits
of `n` from the top: `β^(2m + b) = (β^m)^2 · β^b`, rounding the intermediate bound
to a short rational at each step (`pow_bit_le`, `pow_bit_ge`). Every rounding step
is a small `norm_num` goal.
-/

@[expose] public section

namespace Cryptarchia.Prob

theorem pow_bit_le {β P P' : ℝ} {m : ℕ} (hβ : 0 ≤ β) (h : β ^ m ≤ P) (b : ℕ)
    (h' : P ^ 2 * β ^ b ≤ P') : β ^ (2 * m + b) ≤ P' := by
  have h0 : 0 ≤ β ^ m := pow_nonneg hβ m
  calc β ^ (2 * m + b) = (β ^ m) ^ 2 * β ^ b := by rw [pow_add, mul_comm 2 m, pow_mul]
    _ ≤ P ^ 2 * β ^ b := by
        apply mul_le_mul_of_nonneg_right _ (pow_nonneg hβ b)
        exact pow_le_pow_left₀ h0 h 2
    _ ≤ P' := h'

theorem pow_bit_ge {β P P' : ℝ} {m : ℕ} (hβ : 0 ≤ β) (hP : 0 ≤ P) (h : P ≤ β ^ m) (b : ℕ)
    (h' : P' ≤ P ^ 2 * β ^ b) : P' ≤ β ^ (2 * m + b) := by
  calc P' ≤ P ^ 2 * β ^ b := h'
    _ ≤ (β ^ m) ^ 2 * β ^ b := by
        apply mul_le_mul_of_nonneg_right _ (pow_nonneg hβ b)
        exact pow_le_pow_left₀ hP h 2
    _ = β ^ (2 * m + b) := by rw [pow_add, mul_comm 2 m, pow_mul]

theorem pow_one_le {β P : ℝ} (h : β ≤ P) : β ^ 1 ≤ P := by rwa [pow_one]

theorem pow_one_ge {β P : ℝ} (h : P ≤ β) : P ≤ β ^ 1 := by rwa [pow_one]

end Cryptarchia.Prob
