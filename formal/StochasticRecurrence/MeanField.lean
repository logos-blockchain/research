import StochasticRecurrence.Concentration

/-!
# §2.3 The mean-field map: derivative, critical point, contraction

With `A = -log(1-f)` (eq. `eq:c_def`) and `u = W/D`:

* `hasDerivAt_g`: `g'(D) = 1 - hf + h q(W/D)`, `q(u) = 1 - (1 + Au)e^{-Au}`
  (eqs. `eq:gprime1`–`eq:q_def`);
* `q_strictMonoOn`, `q_nonneg`: `q` is strictly increasing and nonnegative on
  `[0, ∞)` (eqs. `eq:qprime`, `eq:q_positive`), so `g' ≥ 1 - hf > 0` and `g'` is
  decreasing in `D`;
* `exists_unique_critical`: there is exactly one `D_c > 0` with `g'(D_c) = 1`
  (eq. `eq:Dc_definition`);
* `critical_lambert`, `lambert_unique`: `z = 1 + A W/D_c` is the unique `z > 1` with
  `z e^{-z} = (1-f)/e`, and `D_c = W A/(z - 1)`. That is, `-z = 𝒲₋₁(-(1-f)/e)`
  (eqs. `eq:z_equation`–`eq:Dc_formula`; Mathlib has no Lambert `W`, so the branch
  is pinned down by this characterisation);
* `contraction`: if `D_c < a` then `g` is `L_g`-Lipschitz on `[a, b]` with
  `L_g = g'(a) ∈ (0, 1)` (eqs. `eq:contractive_region`–`eq:Lg_less_1`);
* `theorem_2_1`: Theorem 2.1 as stated, under `h < 1/f` and `D_min > D_c`.
-/

open Real Set Filter Topology

namespace SRE

/-- `A = -log(1 - f)` (eq. `eq:c_def`). -/
noncomputable def Acoef (f : ℝ) : ℝ := -Real.log (1 - f)

/-- `q(u) = 1 - (1 + Au)e^{-Au}` (eq. `eq:q_def`). -/
noncomputable def q (f u : ℝ) : ℝ := 1 - (1 + Acoef f * u) * exp (-(Acoef f * u))

/-- `g'(D) = 1 - hf + h q(W/D)` (eq. `eq:gprime_q`). -/
noncomputable def gderiv (f h W D : ℝ) : ℝ := 1 - h * f + h * q f (W / D)

variable {f h W : ℝ}

theorem Acoef_pos (hf0 : 0 < f) (hf1 : f < 1) : 0 < Acoef f := by
  unfold Acoef
  have := Real.log_neg (by linarith) (by linarith : 1 - f < 1)
  linarith

/-- `(1-f)^u = e^{-Au}` (eq. `eq:exp_form`). -/
theorem rpow_eq_exp (hf1 : f < 1) (u : ℝ) : (1 - f) ^ u = exp (-(Acoef f * u)) := by
  rw [Real.rpow_def_of_pos (by linarith)]; unfold Acoef; ring_nf

/-- `(1 + x)e^{-x}` is strictly decreasing on `[0, ∞)`. -/
theorem psi_strictAnti {x y : ℝ} (hx : 0 ≤ x) (hxy : x < y) :
    (1 + y) * exp (-y) < (1 + x) * exp (-x) := by
  have e : y - x + 1 < exp (y - x) := add_one_lt_exp (by linarith)
  rw [show exp (-x) = exp (y - x) * exp (-y) by rw [← Real.exp_add]; ring_nf]
  have := exp_pos (-y)
  have : (1 + y) < (1 + x) * exp (y - x) := by nlinarith
  nlinarith

theorem psi_le_one {x : ℝ} : (1 + x) * exp (-x) ≤ 1 := by
  have h1 : x + 1 ≤ exp x := add_one_le_exp x
  have : exp x * exp (-x) = 1 := by rw [← Real.exp_add]; simp
  nlinarith [exp_pos (-x)]

theorem q_zero : q f 0 = 0 := by simp [q]

theorem q_strictMonoOn (hf0 : 0 < f) (hf1 : f < 1) : StrictMonoOn (q f) (Ici 0) := by
  intro u hu v _ huv
  have hA := Acoef_pos hf0 hf1
  unfold q
  have := psi_strictAnti (mul_nonneg hA.le (mem_Ici.mp hu)) (mul_lt_mul_of_pos_left huv hA)
  linarith

theorem q_monotoneOn (hf0 : 0 < f) (hf1 : f < 1) : MonotoneOn (q f) (Ici 0) :=
  (q_strictMonoOn hf0 hf1).monotoneOn

theorem q_nonneg (u : ℝ) : 0 ≤ q f u := by
  unfold q; linarith [psi_le_one (x := Acoef f * u)]

theorem q_continuous : Continuous (q f) := by
  unfold q; fun_prop

/-- **The derivative of `g`** (eqs. `eq:gprime1`–`eq:gprime_q`). -/
theorem hasDerivAt_g (hf1 : f < 1) {D : ℝ} (hD : 0 < D) :
    HasDerivAt (g f h W) (gderiv f h W D) D := by
  have hg : g f h W = fun D => D - h * D * (f - 1 + exp (-(Acoef f * (W * D⁻¹)))) := by
    funext D; unfold g φ; rw [rpow_eq_exp hf1, div_eq_mul_inv]; ring
  have h1 : HasDerivAt (fun D => -(Acoef f * (W * D⁻¹))) (-(Acoef f * (W * (-(D ^ 2)⁻¹)))) D :=
    (((hasDerivAt_inv hD.ne').const_mul W).const_mul (Acoef f)).neg
  have h3 := ((hasDerivAt_id D).const_mul h).mul (h1.exp.const_add (f - 1))
  have h4 := (hasDerivAt_id D).sub h3
  rw [hg]
  convert h4 using 1
  · funext x; simp only [id, Pi.sub_apply, Pi.mul_apply]
  · unfold gderiv q
    simp only [id, div_eq_mul_inv]
    field_simp
    ring

/-- `g' ≥ 1 - hf > 0` (eq. `eq:gprime_positive`). -/
theorem gderiv_pos (H : Hyp f h W) (D : ℝ) : 0 < gderiv f h W D := by
  unfold gderiv
  have := mul_nonneg H.h_pos.le (q_nonneg (f := f) (W / D))
  linarith [H.hf_lt]

/-- `g'` is decreasing in `D > 0`. -/
theorem gderiv_anti (H : Hyp f h W) {D D' : ℝ} (hD : 0 < D) (hDD' : D ≤ D') :
    gderiv f h W D' ≤ gderiv f h W D := by
  unfold gderiv
  have hm := q_monotoneOn H.f_pos H.f_lt_one
    (mem_Ici.mpr (div_nonneg H.W_nonneg (hD.trans_le hDD').le))
    (mem_Ici.mpr (div_nonneg H.W_nonneg hD.le))
    (div_le_div_of_nonneg_left H.W_nonneg hD hDD')
  nlinarith [H.h_pos]

/-- `D_c` is critical: `D_c > 0` and `g'(D_c) = 1` (eq. `eq:Dc_definition`). -/
def IsCritical (f h W Dc : ℝ) : Prop := 0 < Dc ∧ gderiv f h W Dc = 1

/-- `g'(D_c) = 1 ⟺ q(W/D_c) = f` (eq. `eq:Dc_equation2`). -/
theorem gderiv_eq_one_iff (hh : 0 < h) (D : ℝ) : gderiv f h W D = 1 ↔ q f (W / D) = f := by
  unfold gderiv
  constructor
  · intro e
    have : h * (q f (W / D) - f) = 0 := by linarith
    rcases mul_eq_zero.mp this with h0 | h0
    · linarith
    · linarith
  · intro e; rw [e]; ring

/-- `q(u) → 1` as `u → ∞`, so `q` takes every value in `[0, 1)`. -/
theorem exists_q_gt (hf0 : 0 < f) (hf1 : f < 1) : ∃ M, 0 < M ∧ f < q f M := by
  have hA := Acoef_pos hf0 hf1
  have hlim : Tendsto (fun x : ℝ => (1 + x) * exp (-x)) atTop (𝓝 0) := by
    have h0 := Real.tendsto_pow_mul_exp_neg_atTop_nhds_zero 0
    have h1 := Real.tendsto_pow_mul_exp_neg_atTop_nhds_zero 1
    simpa [add_mul] using h0.add h1
  obtain ⟨x, hx, hx0⟩ :=
    ((hlim.eventually (gt_mem_nhds (by linarith : (0 : ℝ) < 1 - f))).and
      (eventually_gt_atTop 0)).exists
  refine ⟨x / Acoef f, div_pos hx0 hA, ?_⟩
  unfold q
  rw [mul_div_cancel₀ _ hA.ne']
  linarith

/-- **The critical point exists and is unique.** -/
theorem exists_unique_critical (H : Hyp f h W) (hW : 0 < W) : ∃! Dc, IsCritical f h W Dc := by
  obtain ⟨M, hM, hfM⟩ := exists_q_gt H.f_pos H.f_lt_one
  obtain ⟨u, ⟨hu0, _⟩, hu⟩ := intermediate_value_Icc hM.le q_continuous.continuousOn
    (show f ∈ Icc (q f 0) (q f M) from ⟨by rw [q_zero]; exact H.f_pos.le, hfM.le⟩)
  have hupos : 0 < u := lt_of_le_of_ne hu0 (by rintro rfl; rw [q_zero] at hu; linarith [H.f_pos])
  refine ⟨W / u, ⟨div_pos hW hupos, ?_⟩, ?_⟩
  · rw [gderiv_eq_one_iff H.h_pos, div_div_cancel₀ hW.ne']; exact hu
  · rintro Dc ⟨hDc, hc⟩
    rw [gderiv_eq_one_iff H.h_pos] at hc
    have := (q_strictMonoOn H.f_pos H.f_lt_one).injOn
      (mem_Ici.mpr (div_pos hW hDc).le) (mem_Ici.mpr hupos.le) (hc.trans hu.symm)
    rw [← this, div_div_cancel₀ hW.ne']

/-- **The Lambert-W form of `D_c`** (eqs. `eq:z_def`–`eq:Dc_formula`): with
`z = 1 + A W/D_c`, `z > 1`, `z e^{-z} = (1-f)/e`, and `D_c = W A/(z - 1)`. -/
theorem critical_lambert (H : Hyp f h W) (hW : 0 < W) {Dc : ℝ} (hc : IsCritical f h W Dc) :
    1 < 1 + Acoef f * (W / Dc) ∧
    (1 + Acoef f * (W / Dc)) * exp (-(1 + Acoef f * (W / Dc))) = (1 - f) / exp 1 ∧
    Dc = W * Acoef f / ((1 + Acoef f * (W / Dc)) - 1) := by
  obtain ⟨hDc, hg⟩ := hc
  rw [gderiv_eq_one_iff H.h_pos] at hg
  have hA := Acoef_pos H.f_pos H.f_lt_one
  have hu : 0 < W / Dc := div_pos hW hDc
  refine ⟨by nlinarith, ?_, ?_⟩
  · unfold q at hg
    rw [show -(1 + Acoef f * (W / Dc)) = -(Acoef f * (W / Dc)) + -1 by ring, Real.exp_add,
      Real.exp_neg 1, ← mul_assoc, ← div_eq_mul_inv]
    congr 1; linarith
  · field_simp; ring

/-- `z e^{-z} = c` has at most one solution `z ≥ 1`: the `-1` branch `𝒲₋₁` of the
Lambert `W` function. -/
theorem lambert_unique {z₁ z₂ : ℝ} (h₁ : 1 ≤ z₁) (h₂ : 1 ≤ z₂)
    (h : z₁ * exp (-z₁) = z₂ * exp (-z₂)) : z₁ = z₂ := by
  have key : ∀ {a b : ℝ}, 1 ≤ a → a < b → b * exp (-b) < a * exp (-a) := by
    intro a b ha hab
    have := psi_strictAnti (x := a - 1) (y := b - 1) (by linarith) (by linarith)
    have e : ∀ t : ℝ, exp (-(t - 1)) = exp (-t) * exp 1 := by
      intro t; rw [← Real.exp_add]; ring_nf
    rw [e, e] at this
    simp only [add_sub_cancel] at this
    nlinarith [exp_pos 1]
  rcases lt_trichotomy z₁ z₂ with hlt | heq | hgt
  · exact absurd h (key h₁ hlt).ne'
  · exact heq
  · exact absurd h (key h₂ hgt).ne

/-- **Contraction** (eqs. `eq:contractive_region`–`eq:Lg_less_1`): if `D_c < a` then
on `[a, b]`, `0 < g' ≤ g'(a) < 1`, so `g` is `g'(a)`-Lipschitz there. -/
theorem contraction (H : Hyp f h W) (hW : 0 < W) {Dc a b : ℝ} (hc : IsCritical f h W Dc)
    (ha : Dc < a) :
    LipOn (g f h W) a b (gderiv f h W a) ∧ 0 < gderiv f h W a ∧ gderiv f h W a < 1 := by
  obtain ⟨hDc, hg⟩ := hc
  have hapos : 0 < a := hDc.trans ha
  refine ⟨?_, gderiv_pos H a, ?_⟩
  · intro x y hx _ hy _
    have hderiv : ∀ z ∈ Icc (min x y) (max x y),
        HasDerivWithinAt (g f h W) (gderiv f h W z) (Icc (min x y) (max x y)) z := by
      intro z hz
      exact (hasDerivAt_g H.f_lt_one (lt_of_lt_of_le hapos (le_trans (le_min hx hy) hz.1)))
        |>.hasDerivWithinAt
    have hbound : ∀ z ∈ Icc (min x y) (max x y), ‖gderiv f h W z‖ ≤ gderiv f h W a := by
      intro z hz
      have hz : a ≤ z := le_trans (le_min hx hy) hz.1
      rw [Real.norm_eq_abs, abs_of_pos (gderiv_pos H z)]
      exact gderiv_anti H hapos hz
    have := (convex_Icc (min x y) (max x y)).norm_image_sub_le_of_norm_hasDerivWithin_le
      hderiv hbound (⟨min_le_right x y, le_max_right x y⟩ : y ∈ Icc (min x y) (max x y))
      (⟨min_le_left x y, le_max_left x y⟩ : x ∈ Icc (min x y) (max x y))
    simpa [Real.norm_eq_abs] using this
  · have hlt : gderiv f h W a < gderiv f h W Dc := by
      unfold gderiv
      have := q_strictMonoOn H.f_pos H.f_lt_one (mem_Ici.mpr (div_pos hW hapos).le)
        (mem_Ici.mpr (div_pos hW hDc).le) (div_lt_div_of_pos_left hW hDc ha)
      nlinarith [H.h_pos]
    linarith

/-- **Theorem 2.1** as stated in the paper. Assume `0 < f < 1`, `0 < h < 1/f`
(eq. `eq:h_condition`), `W, D₀ > 0`, and `D_min > D_c` (eq. `eq:contractive_assumption`)
for the critical point `D_c`. Then there is `L_g < 1` such that for every `T ≥ 1`,
with `K = h² D_max² / (1 - L_g²) · L / 4`:

1. `E[(D_ℓ - d_ℓ)²] ≤ K/T` for `ℓ ≤ L`;
2. `P(sup_{ℓ≤L} |D_ℓ - d_ℓ| ≥ δ) ≤ (L+1)K/(Tδ²)`, so `sup_{ℓ≤L}|D_ℓ - d_ℓ| = O_P(T^{-1/2})`;
3. `|m_ℓ - d_ℓ| ≤ √(K/T) = O(T^{-1/2})`. -/
theorem theorem_2_1 (H : Hyp f h W) (hW : 0 < W) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Dc : ℝ}
    (hc : IsCritical f h W Dc) (hmin : Dc < Dmin f h D₀ L) :
    ∃ Lg, 0 ≤ Lg ∧ Lg < 1 ∧ ∀ T : ℕ, 0 < T →
      let K := (h * Dmax f h D₀ L) ^ 2 / (1 - Lg ^ 2) * L / 4
      (∀ ℓ ≤ L, kChain f h T W L D₀ (fun ks => (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2)
          ≤ K / T) ∧
      (∀ δ > 0, kProb f h T W L D₀
          (fun ks => ∃ ℓ ≤ L, δ ≤ |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ|)
          ≤ (L + 1) * K / (T * δ ^ 2)) ∧
      (∀ ℓ ≤ L, |kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) - mf f h W D₀ ℓ|
          ≤ √(K / T)) := by
  obtain ⟨hLip, hpos, hlt⟩ := contraction (b := Dmax f h D₀ L) H hW hc hmin
  refine ⟨_, hpos.le, hlt, fun T hT => ?_⟩
  intro K
  have hK : Kc f h D₀ L (gderiv f h W (Dmin f h D₀ L)) ≤ K := Kc_le_contractive hpos.le hlt
  have hT' : (0 : ℝ) < T := by exact_mod_cast hT
  obtain ⟨c1, c2, c3⟩ := concentration (T := T) H hT hD₀ hpos.le hLip
  refine ⟨fun ℓ hℓ => (c1 ℓ hℓ).trans (by gcongr), fun δ hδ => (c2 δ hδ).trans (by gcongr),
    fun ℓ hℓ => (c3 ℓ hℓ).trans (Real.sqrt_le_sqrt (by gcongr))⟩

end SRE
