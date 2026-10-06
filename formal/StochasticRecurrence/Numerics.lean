import StochasticRecurrence.MeanField

/-!
# The critical threshold at `f = 1/30` (eq. `eq:Dc_numerical`)

For `f = 1/30` the paper verifies `q(1/0.1205) < 1/30 < q(1/0.119)`
(eq. `eq:Dc_numerical_verification`, `Dc_numerical_verification`) and applies
Prop. (Bounds on the critical ratio) (`Dc_bounds`) to get `0.119 < D_c/W < 0.1205`
(eq. `eq:Dc_certified_bounds`, `Dc_ratio`). Numerically `D_c/W = 0.11960…`.
-/

open Real Finset

namespace SRE

/-- `0.0339 < A = -log(29/30) < 0.033902` (the log series to 4 terms). -/
theorem Acoef_bounds : (0.0339 : ℝ) < Acoef (1 / 30) ∧ Acoef (1 / 30) < 0.033902 := by
  have h := Real.abs_log_sub_add_sum_range_le (x := 1 / 30) (by norm_num [abs_of_pos]) 4
  simp only [sum_range_succ, sum_range_zero] at h
  norm_num [abs_of_pos] at h
  rw [abs_le] at h
  unfold Acoef
  norm_num
  constructor <;> linarith [h.1, h.2]

/-- `(1 + x)e^{-x}` is antitone on `[0, ∞)`. -/
theorem psi_anti {x y : ℝ} (hx : 0 ≤ x) (hxy : x ≤ y) :
    (1 + y) * exp (-y) ≤ (1 + x) * exp (-x) := by
  rcases hxy.lt_or_eq with h | h
  · exact (psi_strictAnti hx h).le
  · rw [h]

/-- The Taylor bound for `e^{-x}` with 5 terms, `0 ≤ x ≤ 1`. -/
theorem exp_neg_taylor {x : ℝ} (h0 : 0 ≤ x) (h1 : x ≤ 1) :
    |exp (-x) - (1 - x + x ^ 2 / 2 - x ^ 3 / 6 + x ^ 4 / 24)| ≤ x ^ 5 / 100 := by
  have := Real.exp_bound (x := -x) (by rw [abs_neg, abs_of_nonneg h0]; exact h1) (n := 5)
    (by norm_num)
  simp only [sum_range_succ, sum_range_zero, Nat.factorial, abs_neg, abs_of_nonneg h0] at this
  norm_num at this
  convert this using 2 <;> ring

/-- `q(1/0.1205) < 1/30`. -/
theorem q_lo : q (1 / 30) (2000 / 241) < 1 / 30 := by
  obtain ⟨_, hA⟩ := Acoef_bounds
  have hA0 := Acoef_pos (f := 1 / 30) (by norm_num) (by norm_num)
  set xh : ℝ := 0.033902 * (2000 / 241)
  have hx : Acoef (1 / 30) * (2000 / 241) ≤ xh := by
    apply mul_le_mul_of_nonneg_right hA.le (by norm_num)
  have hψ := psi_anti (by positivity) hx
  have ht := exp_neg_taylor (x := xh) (by norm_num [xh]) (by norm_num [xh])
  rw [abs_le] at ht
  unfold q
  have : (29 : ℝ) / 30 < (1 + xh) * exp (-xh) := by
    have hlow : (1 + xh) * ((1 - xh + xh ^ 2 / 2 - xh ^ 3 / 6 + xh ^ 4 / 24) - xh ^ 5 / 100)
        ≤ (1 + xh) * exp (-xh) :=
      mul_le_mul_of_nonneg_left (by linarith [ht.1]) (by norm_num [xh])
    refine lt_of_lt_of_le ?_ hlow
    norm_num [xh]
  linarith

/-- `q(1/0.119) > 1/30`. -/
theorem q_hi : 1 / 30 < q (1 / 30) (1000 / 119) := by
  obtain ⟨hA, _⟩ := Acoef_bounds
  set xl : ℝ := 0.0339 * (1000 / 119)
  have hx : xl ≤ Acoef (1 / 30) * (1000 / 119) := by
    apply mul_le_mul_of_nonneg_right hA.le (by norm_num)
  have hψ := psi_anti (by norm_num [xl]) hx
  have ht := exp_neg_taylor (x := xl) (by norm_num [xl]) (by norm_num [xl])
  rw [abs_le] at ht
  unfold q
  have : (1 + xl) * exp (-xl) < (29 : ℝ) / 30 := by
    have hup : (1 + xl) * exp (-xl)
        ≤ (1 + xl) * ((1 - xl + xl ^ 2 / 2 - xl ^ 3 / 6 + xl ^ 4 / 24) + xl ^ 5 / 100) :=
      mul_le_mul_of_nonneg_left (by linarith [ht.2]) (by norm_num [xl])
    refine lt_of_le_of_lt hup ?_
    norm_num [xl]
  linarith

/-- The numerical check of eq. `eq:Dc_numerical_verification`:
`q_{1/30}(1/0.1205) < 1/30 < q_{1/30}(1/0.119)`. -/
theorem Dc_numerical_verification :
    q (1 / 30) (1 / 0.1205) < 1 / 30 ∧ 1 / 30 < q (1 / 30) (1 / 0.119) := by
  rw [show (1 : ℝ) / 0.1205 = 2000 / 241 by norm_num, show (1 : ℝ) / 0.119 = 1000 / 119 by norm_num]
  exact ⟨q_lo, q_hi⟩

/-- **`D_c/W` at `f = 1/30`** (eq. `eq:Dc_certified_bounds`): `0.119 < D_c/W < 0.1205`,
by `Dc_bounds` with `a = 0.119`, `b = 0.1205`. -/
theorem Dc_ratio {h W Dc : ℝ} (H : Hyp (1 / 30) h W) (hW : 0 < W)
    (hc : IsCritical (1 / 30) h W Dc) : (0.119 : ℝ) < Dc / W ∧ Dc / W < 0.1205 :=
  Dc_bounds H hW hc (by norm_num) (by norm_num) Dc_numerical_verification.1
    Dc_numerical_verification.2

end SRE
