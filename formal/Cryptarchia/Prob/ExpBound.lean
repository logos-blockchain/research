import Mathlib.Analysis.SpecialFunctions.Exp

/-!
# A rational upper bound on `exp (-a)`

`exp (-a) ≤ 1 / (1 + a/n)^n`, from `1 + x ≤ exp x`. A certificate bounds `(1 + a₀/n)^n`
from below by a repeated-squaring chain and gets `exp (-a) ≤ 1 / Q` for `a ≥ a₀`.
-/

namespace Cryptarchia.Prob

open Real

theorem exp_neg_le_of {a a0 Q : ℝ} (n : ℕ) (hn : 0 < n) (h0 : 0 ≤ a0) (ha : a0 ≤ a)
    (hQ0 : 0 < Q) (hQ : Q ≤ (1 + a0 / n) ^ n) : exp (-a) ≤ 1 / Q := by
  have hn' : (0 : ℝ) < n := by exact_mod_cast hn
  have h1 : (1 + a0 / n) ^ n ≤ exp a0 := by
    have := add_one_le_exp (a0 / n)
    calc (1 + a0 / n) ^ n ≤ exp (a0 / n) ^ n :=
          pow_le_pow_left₀ (by positivity) (by linarith) n
      _ = exp a0 := by rw [← exp_nat_mul]; congr 1; field_simp
  have h2 : exp (-a) ≤ exp (-a0) := exp_le_exp.2 (by linarith)
  rw [exp_neg a0] at h2
  exact h2.trans (by rw [one_div]; exact inv_anti₀ hQ0 (hQ.trans h1))

end Cryptarchia.Prob
