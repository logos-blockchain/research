import StochasticRecurrence.MeanField

/-!
# Appendix B: the average

* `traj_prod`: `D_ℓ = D_0 ∏_{r<ℓ} (1 - h(f - 1 + k_r/T))`;
* `E_step`: `⟨D_{ℓ+1}⟩ = (1 + h(1-f))⟨D_ℓ⟩ - h⟨D_ℓ (1 - φ(W/D_ℓ))⟩`;
* `jensen`: `D ↦ D(1 - φ(W/D))` is convex (tangent-line form), so
  `⟨D_ℓ(1 - φ(W/D_ℓ))⟩ ≥ ⟨D_ℓ⟩(1 - φ(W/⟨D_ℓ⟩))`; this is the appendix's last inequality;
* `E_step_le_g`: hence `⟨D_{ℓ+1}⟩ ≤ g(⟨D_ℓ⟩)`. So the saddle-point equation
  (eq. `eq:MF`) holds as an inequality for every finite `T`, not as an equality;
* `mean_le_mf`: since `g` is increasing, `⟨D_ℓ⟩ ≤ d_ℓ` for every `T` and `ℓ ≤ L`.
  The mean-field recursion bounds the mean estimate from above.
-/

open Finset Set

namespace SRE

variable {f h W : ℝ} {T : ℕ}

/-- The product formula of Appendix B. -/
theorem traj_prod (D₀ : ℝ) (ks : ℕ → ℕ) (ℓ : ℕ) :
    Dtraj f h T D₀ ks ℓ = D₀ * ∏ r ∈ range ℓ, (1 - h * (f - 1 + ks r / T)) := by
  induction ℓ with
  | zero => simp [traj]
  | succ ℓ ih =>
    have ih' : traj (step f h T) D₀ ks ℓ = _ := ih
    simp only [traj, step_eq]; rw [ih', prod_range_succ]; ring

/-- The mean after one more step. -/
theorem E_step (hT : 0 < T) {L ℓ : ℕ} (hℓ : ℓ < L) (D₀ : ℝ) :
    kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks (ℓ + 1))
      = (1 + h * (1 - f)) * kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ)
        - h * kChain f h T W L D₀
            (fun ks => Dtraj f h T D₀ ks ℓ * pEmpty f W (Dtraj f h T D₀ ks ℓ)) := by
  have hpath : (fun ks => Dtraj f h T D₀ ks (ℓ + 1))
      = fun ks => Dtraj f h T D₀ ks ℓ * (1 + h * (1 - f))
          + Dtraj f h T D₀ ks ℓ * ((ks ℓ : ℝ) / T) * (-h) := by
    funext ks; simp only [traj, step_eq]; ring
  have htower := E_tower (f := f) (h := h) (T := T) (W := W)
    (fun x k => x * ((k : ℝ) / T)) L D₀ ℓ hℓ
  have hmean : ∀ x : ℝ, binExp T (pEmpty f W x) (fun k => x * ((k : ℝ) / T))
      = x * pEmpty f W x := by
    intro x
    rw [show (fun k : ℕ => x * ((k : ℝ) / T)) = fun k : ℕ => (k : ℝ) / T * x from by funext; ring,
      binExp_mul_const, binExp_mean hT.ne']
    ring
  simp only [hmean] at htower
  rw [hpath, E_add, E_mul_const, E_mul_const, htower]
  ring

/-- The tangent-line inequality for `F(x) = x·e^{-c/x}`, `c ≥ 0`, on `x > 0`:
`F(x) ≥ F(m) + e^{-c/m}(1 + c/m)(x - m)`. So `F` is convex. -/
theorem tangent_le {c x m : ℝ} (hx : 0 < x) (hm : 0 < m) :
    m * Real.exp (-(c / m)) + Real.exp (-(c / m)) * (1 + c / m) * (x - m)
      ≤ x * Real.exp (-(c / x)) := by
  have ht := Real.add_one_le_exp (c / m - c / x)
  have he : Real.exp (-(c / x)) = Real.exp (-(c / m)) * Real.exp (c / m - c / x) := by
    rw [← Real.exp_add]; ring_nf
  rw [he]
  have hE := Real.exp_pos (-(c / m))
  have : m + (1 + c / m) * (x - m) = x * (c / m - c / x + 1) := by field_simp; ring
  nlinarith [mul_le_mul_of_nonneg_left ht (mul_pos hx hE).le]

theorem pEmpty_eq_exp (hf1 : f < 1) (D : ℝ) :
    pEmpty f W D = Real.exp (-(Acoef f * W / D)) := by
  rw [pEmpty_eq, rpow_eq_exp hf1]; ring_nf

/-- **Jensen** (the last inequality of Appendix B):
`⟨D_ℓ (1 - φ(W/D_ℓ))⟩ ≥ ⟨D_ℓ⟩ (1 - φ(W/⟨D_ℓ⟩))`. -/
theorem jensen (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) (L ℓ : ℕ) :
    let m := kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ)
    m * pEmpty f W m
      ≤ kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ * pEmpty f W (Dtraj f h T D₀ ks ℓ)) := by
  intro m
  have hm : 0 < m := by
    have : kChain f h T W L D₀ (fun _ => D₀ * (1 - h * f) ^ ℓ) ≤ m :=
      E_mono H hT L D₀ hD₀ _ _ fun ks hb => (traj_bounds H hT hD₀ hb ℓ).1
    rw [E_const] at this
    exact lt_of_lt_of_le (mul_pos hD₀ (pow_pos (by linarith [H.hf_lt]) _)) this
  set c := Acoef f * W
  set s := Real.exp (-(c / m)) * (1 + c / m)
  calc m * pEmpty f W m
      = kChain f h T W L D₀ (fun ks => (m * pEmpty f W m + Dtraj f h T D₀ ks ℓ * s) + (-m * s)) := by
        rw [E_add, E_const, E_add, E_const, E_mul_const]; ring
    _ ≤ _ := by
        refine E_mono H hT L D₀ hD₀ _ _ fun ks hb => ?_
        have hx := traj_pos H hT hD₀ hb ℓ
        have := tangent_le (c := c) hx hm
        simp only [pEmpty_eq_exp H.f_lt_one, mul_div_assoc] at this ⊢
        simp only [s, c, mul_div_assoc] at this ⊢
        linarith

/-- **The mean-field map bounds the mean from above, one step**:
`⟨D_{ℓ+1}⟩ ≤ g(⟨D_ℓ⟩)` for every `T`. -/
theorem E_step_le_g (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L ℓ : ℕ} (hℓ : ℓ < L) :
    kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks (ℓ + 1))
      ≤ g f h W (kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ)) := by
  rw [E_step hT hℓ]
  have hj := jensen H hT hD₀ L ℓ
  simp only at hj
  have hg : ∀ m, g f h W m = (1 + h * (1 - f)) * m - h * (m * pEmpty f W m) := by
    intro m; unfold g pEmpty; ring
  rw [hg]
  nlinarith [H.h_pos]

/-- `g` is increasing on `(0, ∞)` (`g' > 0`). -/
theorem g_monotoneOn (H : Hyp f h W) : MonotoneOn (g f h W) (Ioi 0) := by
  have hd : ∀ x ∈ Ioi (0 : ℝ), HasDerivAt (g f h W) (gderiv f h W x) x :=
    fun x hx => hasDerivAt_g H.f_lt_one hx
  refine monotoneOn_of_deriv_nonneg (convex_Ioi 0)
    (fun x hx => (hd x hx).continuousAt.continuousWithinAt)
    (fun x hx => (hd x (interior_subset hx)).differentiableAt.differentiableWithinAt)
    (fun x hx => ?_)
  rw [(hd x (interior_subset hx)).deriv]
  exact (gderiv_pos H x).le

/-- **The mean estimate never exceeds the mean-field recursion:**
`⟨D_ℓ⟩ ≤ d_ℓ` for every `T ≥ 1` and `ℓ ≤ L`. -/
theorem mean_le_mf (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} :
    ∀ ℓ ≤ L, kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) ≤ mf f h W D₀ ℓ := by
  intro ℓ
  induction ℓ with
  | zero => intro _; simp only [traj, mf]; rw [E_const]
  | succ ℓ ih =>
    intro hℓ
    have hm : 0 < kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) := by
      have : kChain f h T W L D₀ (fun _ => D₀ * (1 - h * f) ^ ℓ)
          ≤ kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) :=
        E_mono H hT L D₀ hD₀ _ _ fun ks hb => (traj_bounds H hT hD₀ hb ℓ).1
      rw [E_const] at this
      exact lt_of_lt_of_le (mul_pos hD₀ (pow_pos (by linarith [H.hf_lt]) _)) this
    exact (E_step_le_g H hT hD₀ (by omega)).trans
      (g_monotoneOn H hm (hm.trans_le (ih (by omega))) (ih (by omega)))

end SRE
