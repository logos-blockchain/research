import Cryptarchia.Prob.Stake

/-!
# Tools for numeric certificates

Large powers `β^n` (with `n` up to about `10^5`) are bounded by processing the bits
of `n` from the top: `β^(2m + b) = (β^m)^2 · β^b`, rounding the intermediate bound
to a short rational at each step (`pow_bit_le`, `pow_bit_ge`). Every rounding step
is a small `norm_num` goal.
-/

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
