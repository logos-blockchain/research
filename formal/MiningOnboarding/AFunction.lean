import MiningOnboarding.Model

/-!
# Appendix (`sec:A-analysis`): the function `A(t; M)`

`A(t; M) = S₀ + P_L t - S₀ (1 + k t)^r` with `k = (M + P_L)/S₀` and `r = P_L/(M + P_L)`.
Throughout, `S₀, P_L, M > 0` unless stated otherwise.

Dependence on `t`:
* `A_eq_bernoulli`: `A = S₀ [1 + r k t - (1 + k t)^r]` (§ "Consistency with the ODE system");
* `A_pos`, `A_lt`: `0 < A(t) < P_L t` for `t > 0`; `A_nonneg`, `A_le` for `t ≥ 0`;
* `hasDerivAt_A`: `A'(t) = P_L [1 - (1 + k t)^{r-1}]`;
* `A_strictMonoOn`: `A` is strictly increasing on `[0, ∞)`;
* `A_strictConvexOn`: `A` is strictly convex on `[0, ∞)` (the report's `A'' > 0`).

Dependence on `S₀` (fixed `t, M, P_L > 0`):
* `A_strictAntiOn_S0`: strictly decreasing on `(0, ∞)`;
* `A_lt_quad`: `A < M P_L t² / S₀`;
* `tendsto_A_S0_atTop`: `A → 0` as `S₀ → ∞`;
* `tendsto_A_S0_zero`: `A → P_L t` as `S₀ → 0⁺`.

Dependence on `M` (not in the report; it is what makes `m_min` well defined, see
`Qualification.lean`), for fixed `S₀, t, P_L > 0`:
* `g_strictAntiOn_M`: the growth factor of genesis stake, `g`, is strictly decreasing in `M`;
* `A_strictMonoOn_M`: `A(t; M)` is strictly increasing in `M` on `[0, ∞)`;
* `A_continuousOn_M`: `A(t; M)` is continuous in `M` on `(-P_L, ∞)`;
* `tendsto_A_M_atTop`: `A(t; M) → P_L t` as `M → ∞`.
-/

open Real Set Filter Topology

namespace Onboarding

variable {S0 PL M t : ℝ}

/-- `A = S₀ [1 + r y - (1 + y)^r]` with `y = (M + P_L) t / S₀`, `r = P_L/(M + P_L)`. -/
theorem A_eq_bernoulli (hS0 : S0 ≠ 0) (hMP : M + PL ≠ 0) :
    A S0 PL M t = S0 * (1 + PL / (M + PL) * ((M + PL) * t / S0)
      - (1 + (M + PL) * t / S0) ^ (PL / (M + PL))) := by
  unfold A g; field_simp

/-- The exponent `r = P_L/(M + P_L)` lies in `(0, 1)`. -/
theorem r_mem (hM : 0 < M) (hPL : 0 < PL) : 0 < PL / (M + PL) ∧ PL / (M + PL) < 1 :=
  ⟨by positivity, (div_lt_one (by linarith)).mpr (by linarith)⟩

/-- `A(t; M) > 0` for `t > 0` (concavity of `x ↦ x^r`). -/
theorem A_pos (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) : 0 < A S0 PL M t := by
  rw [A_eq_bernoulli hS0.ne' (by linarith)]
  have hy : 0 < (M + PL) * t / S0 := by positivity
  have := rpow_one_add_lt_one_add_mul_self (by linarith) hy.ne' (r_mem hM hPL).1 (r_mem hM hPL).2
  have := mul_pos hS0 (sub_pos.mpr this)
  linarith

theorem A_nonneg (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) (ht : 0 ≤ t) : 0 ≤ A S0 PL M t := by
  rcases ht.eq_or_lt with rfl | ht
  · simp [A_zero]
  · exact (A_pos hS0 hM hPL ht).le

/-- `g(t) > 1` for `t > 0`: genesis stake earns positive leadership income. -/
theorem one_lt_g (hS0 : 0 < S0) (hM : 0 ≤ M) (hPL : 0 < PL) (ht : 0 < t) : 1 < g S0 PL M t :=
  one_lt_rpow (by have : 0 < (M + PL) * t / S0 := by positivity
                  linarith) (by positivity)

/-- `A(t; M) < P_L t` for `t > 0` (leadership-income ceiling). -/
theorem A_lt (hS0 : 0 < S0) (hM : 0 ≤ M) (hPL : 0 < PL) (ht : 0 < t) : A S0 PL M t < PL * t := by
  rw [A_eq_interp]
  have := mul_pos hS0 (sub_pos.mpr (one_lt_g hS0 hM hPL ht))
  linarith

theorem A_le (hS0 : 0 < S0) (hM : 0 ≤ M) (hPL : 0 < PL) (ht : 0 ≤ t) : A S0 PL M t ≤ PL * t := by
  rcases ht.eq_or_lt with rfl | ht
  · simp [A_zero]
  · exact (A_lt hS0 hM hPL ht).le

/-! ## Dependence on `t` -/

/-- `A'(t) = P_L [1 - (1 + k t)^{r-1}]`. -/
theorem hasDerivAt_A (hS0 : 0 < S0) (hMP : 0 < M + PL) (hpos : 0 < Stot S0 PL M t) :
    HasDerivAt (A S0 PL M)
      (PL * (1 - (1 + (M + PL) * t / S0) ^ (PL / (M + PL) - 1))) t := by
  have hg := hasDerivAt_g hS0 hMP hpos
  have hlin : HasDerivAt (fun t => S0 + PL * t) PL t := by
    convert ((hasDerivAt_id' t).const_mul PL).const_add S0 using 1; ring
  have := hlin.sub (hg.const_mul S0)
  show HasDerivAt (fun t => S0 + PL * t - S0 * g S0 PL M t) _ t
  convert this using 1
  have hb : 0 < 1 + (M + PL) * t / S0 := by rw [g_base hS0]; exact div_pos hpos hS0
  rw [rpow_sub_one hb.ne', g, g_base hS0]
  rw [g_base hS0] at hb
  field_simp

/-- `(1 + k t)^{r-1} < 1` for `t > 0`, so `A' > 0`. -/
theorem deriv_A_pos (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) :
    0 < PL * (1 - (1 + (M + PL) * t / S0) ^ (PL / (M + PL) - 1)) := by
  have hy : 0 < (M + PL) * t / S0 := by positivity
  have := rpow_lt_one_of_one_lt_of_neg (x := 1 + (M + PL) * t / S0) (by linarith)
    (by linarith [(r_mem hM hPL).2] : PL / (M + PL) - 1 < 0)
  exact mul_pos hPL (by linarith)

theorem continuousOn_A (hS0 : 0 < S0) (hMP : 0 < M + PL) : ContinuousOn (A S0 PL M) (Ici 0) :=
  fun _ ht => (hasDerivAt_A hS0 hMP (Stot_pos hS0 hMP.le ht)).continuousAt.continuousWithinAt

/-- `A` is strictly increasing in `t` on `[0, ∞)`. -/
theorem A_strictMonoOn (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) :
    StrictMonoOn (A S0 PL M) (Ici 0) := by
  refine strictMonoOn_of_deriv_pos (convex_Ici 0) (continuousOn_A hS0 (by linarith)) ?_
  rw [interior_Ici]; intro t ht
  rw [(hasDerivAt_A hS0 (by linarith) (Stot_pos hS0 (by linarith) (le_of_lt ht))).deriv]
  exact deriv_A_pos hS0 hM hPL ht

/-- `A` is strictly convex in `t` on `[0, ∞)`: `A'` is strictly increasing. -/
theorem A_strictConvexOn (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) :
    StrictConvexOn ℝ (Ici 0) (A S0 PL M) := by
  refine StrictMonoOn.strictConvexOn_of_deriv (convex_Ici 0) (continuousOn_A hS0 (by linarith)) ?_
  rw [interior_Ici]
  intro u hu v hv huv
  have hu' : (0 : ℝ) < u := hu
  have hv' : (0 : ℝ) < v := hv
  rw [(hasDerivAt_A hS0 (by linarith) (Stot_pos hS0 (by linarith) hu'.le)).deriv,
    (hasDerivAt_A hS0 (by linarith) (Stot_pos hS0 (by linarith) hv'.le)).deriv]
  have hbu : 0 < 1 + (M + PL) * u / S0 := by positivity
  have hlt : 1 + (M + PL) * u / S0 < 1 + (M + PL) * v / S0 := by
    have := mul_lt_mul_of_pos_left huv (by linarith : (0 : ℝ) < M + PL)
    have := div_lt_div_of_pos_right this hS0
    linarith
  have := rpow_lt_rpow_of_neg hbu hlt (by linarith [(r_mem hM hPL).2] : PL / (M + PL) - 1 < 0)
  nlinarith

/-! ## Dependence on `S₀` -/

/-- `(1 + u)^{r-1} (1 + (1-r) u) > 1` for `u > 0`, `0 < r < 1`: Bernoulli's inequality
`(1 + u)^{1-r} < 1 + (1-r) u`. -/
theorem one_lt_rpow_mul (hu : 0 < u) {r : ℝ} (hr0 : 0 < r) (hr1 : r < 1) :
    1 < (1 + u) ^ (r - 1) * (1 + (1 - r) * u) := by
  have hb : 0 < 1 + u := by linarith
  have hB := rpow_one_add_lt_one_add_mul_self (by linarith) hu.ne' (p := 1 - r) (by linarith)
    (by linarith)
  have h1 : (1 + u) ^ (r - 1) * (1 + u) ^ (1 - r) = 1 := by
    rw [← rpow_add hb]; simp
  have hP := rpow_pos_of_pos hb (r - 1)
  nlinarith

/-- `S₀ ↦ A` has derivative `1 - (1 + u)^{r-1}(1 + (1-r)u)`, `u = (M + P_L) t / S₀`. -/
theorem hasDerivAt_A_S0 (hS0 : 0 < S0) (hMP : 0 < M + PL) (ht : 0 ≤ t) :
    HasDerivAt (fun x => A x PL M t)
      (1 - (1 + (M + PL) * t / S0) ^ (PL / (M + PL) - 1)
        * (1 + (1 - PL / (M + PL)) * ((M + PL) * t / S0))) S0 := by
  set c := (M + PL) * t
  set r := PL / (M + PL)
  have hb : 0 < 1 + c / S0 := by have : 0 ≤ c / S0 := by positivity
                                 linarith
  have hh : HasDerivAt (fun x => 1 + c / x) (-c / S0 ^ 2) S0 := by
    have := ((hasDerivAt_inv hS0.ne').const_mul c).const_add 1
    convert this using 1
    · funext x; simp [div_eq_mul_inv]
    · ring
  have hp := (hasDerivAt_id' S0).mul (hh.rpow_const (p := r) (Or.inl hb.ne'))
  have := ((hasDerivAt_id' S0).add_const (PL * t)).sub hp
  unfold A g
  convert this using 1
  have hQ : (1 + c / S0) ^ r = (1 + c / S0) * (1 + c / S0) ^ (r - 1) := by
    rw [rpow_sub_one hb.ne', mul_div_assoc', mul_div_cancel_left₀ _ hb.ne']
  rw [hQ]
  field_simp
  ring

/-- `A` is strictly decreasing in `S₀` on `(0, ∞)`. -/
theorem A_strictAntiOn_S0 (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) :
    StrictAntiOn (fun x => A x PL M t) (Ioi 0) := by
  have hMP : 0 < M + PL := by linarith
  refine strictAntiOn_of_deriv_neg (convex_Ioi 0)
    (fun x hx => (hasDerivAt_A_S0 hx hMP ht.le).continuousAt.continuousWithinAt) ?_
  rw [interior_Ioi]; intro x hx
  rw [(hasDerivAt_A_S0 hx hMP ht.le).deriv]
  have hx' : (0 : ℝ) < x := hx
  have hu : 0 < (M + PL) * t / x := by positivity
  have := one_lt_rpow_mul hu (r_mem hM hPL).1 (r_mem hM hPL).2
  linarith

/-- Quadratic upper bound `A < M P_L t² / S₀` for `t > 0`. -/
theorem A_lt_quad (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) :
    A S0 PL M t < M * PL * t ^ 2 / S0 := by
  have hMP : 0 < M + PL := by linarith
  rw [A_eq_bernoulli hS0.ne' hMP.ne']
  set u := (M + PL) * t / S0 with hu_def
  set r := PL / (M + PL) with hr_def
  have hu : 0 < u := by positivity
  obtain ⟨hr0, hr1⟩ := r_mem hM hPL
  have hb : 0 < 1 + u := by linarith
  have hq := rpow_one_add_lt_one_add_mul_self (by linarith) hu.ne' (p := 1 - r) (by linarith)
    (by linarith)
  have hPq : (1 + u) ^ r * (1 + u) ^ (1 - r) = 1 + u := by rw [← rpow_add hb]; simp
  have hP := rpow_pos_of_pos hb r
  have hQ := rpow_pos_of_pos hb (1 - r)
  set P := (1 + u) ^ r
  set Q := (1 + u) ^ (1 - r)
  set D := 1 + (1 - r) * u
  have hD : 0 < D := by have : 0 < (1 - r) * u := by nlinarith
                        linarith
  -- `(1 + r u - r(1-r)u²) D ≤ 1 + u < P D`.
  have h1 : (1 + r * u - r * (1 - r) * u ^ 2) * D ≤ 1 + u := by
    have : 0 ≤ r * (1 - r) ^ 2 * u ^ 3 := by
      have : 0 < 1 - r := by linarith
      positivity
    nlinarith
  have h2 : 1 + u < P * D := by nlinarith
  have h3 : 1 + r * u - r * (1 - r) * u ^ 2 < P := by
    by_contra h; have h := not_lt.mp h; nlinarith
  have hkey : S0 * (r * (1 - r) * u ^ 2) = M * PL * t ^ 2 / S0 := by
    rw [hu_def, hr_def]; field_simp; ring
  nlinarith

/-- `A → 0` as `S₀ → ∞`: an abundant incumbent stake leaves no leadership income for
mining-funded stake. -/
theorem tendsto_A_S0_atTop (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) :
    Tendsto (fun x => A x PL M t) atTop (𝓝 0) := by
  have hup : Tendsto (fun x => M * PL * t ^ 2 / x) atTop (𝓝 0) :=
    tendsto_const_nhds.div_atTop tendsto_id
  refine tendsto_of_tendsto_of_tendsto_of_le_of_le' tendsto_const_nhds hup ?_ ?_
  · filter_upwards [eventually_gt_atTop 0] with x hx using (A_pos hx hM hPL ht).le
  · filter_upwards [eventually_gt_atTop 0] with x hx using (A_lt_quad hx hM hPL ht).le

/-- `S₀ (1 + c/S₀)^r = S₀^{1-r} (S₀ + c)^r`. -/
theorem mul_rpow_eq (hx : 0 < x) {c : ℝ} (hc : 0 ≤ c) (r : ℝ) :
    x * (1 + c / x) ^ r = x ^ (1 - r) * (x + c) ^ r := by
  rw [show 1 + c / x = (x + c) / x by field_simp, div_rpow (by linarith) hx.le,
    rpow_sub hx, rpow_one]
  have := rpow_pos_of_pos hx r
  field_simp

/-- `A → P_L t` as `S₀ → 0⁺`: with no incumbent stake, mining-funded stake takes all
leadership income. -/
theorem tendsto_A_S0_zero (hM : 0 < M) (hPL : 0 < PL) (ht : 0 < t) :
    Tendsto (fun x => A x PL M t) (𝓝[>] 0) (𝓝 (PL * t)) := by
  set c := (M + PL) * t
  set r := PL / (M + PL)
  obtain ⟨hr0, hr1⟩ := r_mem hM hPL
  have hc : 0 < c := by positivity
  set F := fun x : ℝ => x + PL * t - x ^ (1 - r) * (x + c) ^ r
  have hF : ContinuousAt F 0 := by
    have h1 : ContinuousAt (fun x : ℝ => x ^ (1 - r)) 0 :=
      continuousAt_rpow_const _ _ (Or.inr (by linarith))
    have h2 : ContinuousAt (fun x : ℝ => (x + c) ^ r) 0 :=
      (continuousAt_id.add continuousAt_const).rpow_const (Or.inl (by show (0 : ℝ) + c ≠ 0; rw [zero_add]; exact hc.ne'))
    exact (continuousAt_id.add continuousAt_const).sub (h1.mul h2)
  have hF0 : F 0 = PL * t := by
    simp [F, zero_rpow (by linarith : (1 - r) ≠ 0)]
  have := hF.tendsto.mono_left (nhdsWithin_le_nhds (s := Ioi 0))
  rw [hF0] at this
  refine this.congr' ?_
  filter_upwards [self_mem_nhdsWithin] with x hx
  simp only [F, A, g]
  rw [mul_rpow_eq hx hc.le]

/-! ## Dependence on `M` -/

/-- `a ↦ log(1 + a x)/a` is strictly decreasing on `(0, ∞)` for `x > 0` (concavity of `log`). -/
theorem log_div_strictAnti {x a b : ℝ} (hx : 0 < x) (ha : 0 < a) (hab : a < b) :
    log (1 + b * x) / b < log (1 + a * x) / a := by
  have hb : 0 < b := ha.trans hab
  have := strictConcaveOn_log_Ioi.secant_strict_mono (a := 1) (x := 1 + a * x) (y := 1 + b * x)
    (by simp) (by simp only [mem_Ioi]; positivity) (by simp only [mem_Ioi]; positivity)
    (by have := mul_pos ha hx; linarith) (by have := mul_pos hb hx; linarith)
    (by nlinarith)
  simp only [log_one, sub_zero, add_sub_cancel_left] at this
  have e1 : log (1 + b * x) / b = x * (log (1 + b * x) / (b * x)) := by field_simp
  have e2 : log (1 + a * x) / a = x * (log (1 + a * x) / (a * x)) := by field_simp
  rw [e1, e2]
  exact mul_lt_mul_of_pos_left this hx

/-- `g = exp(P_L · log(1 + (M + P_L) t/S₀)/(M + P_L))`. -/
theorem g_eq_exp (hS0 : 0 < S0) (hMP : 0 < M + PL) (ht : 0 ≤ t) :
    g S0 PL M t = exp (PL * (log (1 + (M + PL) * (t / S0)) / (M + PL))) := by
  have hb : 0 < 1 + (M + PL) * t / S0 := by have : 0 ≤ (M + PL) * t / S0 := by positivity
                                            linarith
  rw [g, rpow_def_of_pos hb, mul_div_assoc]
  congr 1; ring

/-- The growth factor `g` of genesis stake is strictly decreasing in `M`: more mining-funded
stake competes for the same leadership pot. -/
theorem g_strictAntiOn_M (hS0 : 0 < S0) (hPL : 0 < PL) (ht : 0 < t) :
    StrictAntiOn (fun M => g S0 PL M t) (Ici 0) := by
  intro M1 hM1 M2 hM2 h12
  have hM1 : (0 : ℝ) ≤ M1 := hM1
  have hM2 : (0 : ℝ) ≤ M2 := hM2
  simp only
  rw [g_eq_exp hS0 (by linarith) ht.le, g_eq_exp hS0 (by linarith) ht.le]
  exact exp_lt_exp.mpr (mul_lt_mul_of_pos_left
    (log_div_strictAnti (by positivity) (by linarith) (by linarith)) hPL)

/-- `A(t; M)` is strictly increasing in `M` on `[0, ∞)` for `t > 0`. -/
theorem A_strictMonoOn_M (hS0 : 0 < S0) (hPL : 0 < PL) (ht : 0 < t) :
    StrictMonoOn (fun M => A S0 PL M t) (Ici 0) := by
  intro M1 hM1 M2 hM2 h12
  have := g_strictAntiOn_M hS0 hPL ht hM1 hM2 h12
  simp only [A_eq_interp] at this ⊢
  nlinarith

/-- `A(t; M)` is continuous in `M` on `(-P_L, ∞)`, for `t ≥ 0`. -/
theorem A_continuousOn_M (hS0 : 0 < S0) (ht : 0 ≤ t) :
    ContinuousOn (fun M => A S0 PL M t) (Ioi (-PL)) := by
  have hne : ∀ M ∈ Ioi (-PL), M + PL ≠ 0 := fun M hM => by
    have : -PL < M := hM; linarith
  have hexp : ContinuousOn (fun M => PL / (M + PL)) (Ioi (-PL)) :=
    continuousOn_const.div (continuousOn_id.add continuousOn_const) hne
  have hbase : ContinuousOn (fun M => 1 + (M + PL) * t / S0) (Ioi (-PL)) := by fun_prop
  have hpow := hbase.rpow hexp (fun M hM => Or.inl (by
    have : -PL < M := hM
    have : 0 ≤ (M + PL) * t / S0 := div_nonneg (mul_nonneg (by linarith) ht) hS0.le
    linarith))
  exact (continuousOn_const.add continuousOn_const).sub (continuousOn_const.mul hpow)

/-- `A(t; M) → P_L t` as `M → ∞`: the leadership-income ceiling is approached but, by
`A_lt`, never reached. -/
theorem tendsto_A_M_atTop (hS0 : 0 < S0) (hPL : 0 < PL) (ht : 0 < t) :
    Tendsto (fun M => A S0 PL M t) atTop (𝓝 (PL * t)) := by
  set x := t / S0
  have hx : 0 < x := by positivity
  -- `z = 1 + (M + P_L) x → ∞` and `log z / (z - 1) → 0`.
  have hz : Tendsto (fun M => 1 + (M + PL) * x) atTop atTop :=
    tendsto_atTop_add_const_left _ 1
      ((tendsto_atTop_add_const_right _ PL tendsto_id).atTop_mul_const hx)
  have hl := (tendsto_pow_log_div_mul_add_atTop 1 (-1) 1 one_ne_zero).comp hz
  have hexp : Tendsto (fun M => PL * (log (1 + (M + PL) * x) / (M + PL))) atTop (𝓝 0) := by
    have := (hl.const_mul (PL * x))
    rw [mul_zero] at this
    refine this.congr' ?_
    filter_upwards [eventually_gt_atTop 0] with M hM
    have : 0 < M + PL := by linarith
    simp only [Function.comp, pow_one]
    field_simp
    ring
  have hg : Tendsto (fun M => g S0 PL M t) atTop (𝓝 1) := by
    have := (continuous_exp.tendsto 0).comp hexp
    rw [exp_zero] at this
    refine this.congr' ?_
    filter_upwards [eventually_gt_atTop 0] with M hM
    exact (g_eq_exp hS0 (by linarith) ht.le).symm
  have := ((hg.sub_const 1).const_mul S0).const_sub (PL * t)
  simp only [sub_self, mul_zero, sub_zero] at this
  refine this.congr' (Eventually.of_forall fun M => ?_)
  simp [A_eq_interp]

end Onboarding
