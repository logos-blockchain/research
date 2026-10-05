import StochasticRecurrence.MeanField

/-!
# The critical threshold at `f = 1/30` (eq. `eq:Dc_numerical`)

The paper states `D_c/W ≈ 0.121` for `f = 1/30`. The certified bracket here is
`0.119 < D_c/W < 0.1205`; numerically `D_c/W = 0.11960…`. So the paper's figure is
slightly high, but the conclusion it supports is unchanged: the estimate can
undershoot the true stake by a factor of about 8 and still be in the
contractive region.
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

/-- **`D_c/W` at `f = 1/30`**: `0.119 < D_c/W < 0.1205` (the paper says `≈ 0.121`). -/
theorem Dc_ratio {h W Dc : ℝ} (H : Hyp (1 / 30) h W) (hW : 0 < W)
    (hc : IsCritical (1 / 30) h W Dc) : (0.119 : ℝ) < Dc / W ∧ Dc / W < 0.1205 := by
  obtain ⟨hDc, hg⟩ := hc
  rw [gderiv_eq_one_iff H.h_pos] at hg
  have hmono := q_strictMonoOn (f := 1 / 30) (by norm_num) (by norm_num)
  have hu : 0 < W / Dc := div_pos hW hDc
  have h1 : 2000 / 241 < W / Dc := by
    by_contra hle; push Not at hle
    have := hmono.monotoneOn (Set.mem_Ici.mpr hu.le) (Set.mem_Ici.mpr (by norm_num)) hle
    linarith [q_lo]
  have h2 : W / Dc < 1000 / 119 := by
    by_contra hle; push Not at hle
    have := hmono.monotoneOn (Set.mem_Ici.mpr (by norm_num)) (Set.mem_Ici.mpr hu.le) hle
    linarith [q_hi]
  have e : Dc / W = 1 / (W / Dc) := by field_simp
  rw [e]
  constructor
  · rw [lt_div_iff₀ hu]; nlinarith
  · rw [div_lt_iff₀ hu]; nlinarith

end SRE
