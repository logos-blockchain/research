import MiningOnboarding.Model

/-!
# §10 Small-growth approximations, as two-sided bounds

The report expands `A(T; M)` for small `ε = (M + P_L) T / S₀`:

  `A(T; M) = (M P_L T² / 2S₀) [1 - (2M + P_L) T / 3S₀ + O(ε²)]`.

Here the `O(ε²)` is replaced by inequalities. With `r = P_L/(M + P_L) ∈ [0, 1]` and
`y = (M + P_L) t / S₀`, `A = S₀ [1 + r y - (1 + y)^r]`, and the Taylor remainders of
`(1 + y)^r` have a definite sign for `y ≥ 0`. So, for every `t ≥ 0` (not only small `ε`):

* `A_le_quadratic`: `A(t; M) ≤ M P_L t² / 2S₀`;
* `quadratic_correction_le_A`: `(M P_L t² / 2S₀) [1 - (2M + P_L) t / 3S₀] ≤ A(t; M)`;
* `Stot_div_S0`: `S_tot(t)/S₀ = 1 + ε`, so `ε ≪ 1` is `S_tot ≈ S₀`.

Consequences for a tokenless, all-locked newcomer (`a = 0`, `β = 0`), at fixed `M`:

* `unlocked_le_quadratic`: `b(T) ≤ m P_L T² / 2S₀`;
* `m0_le_of_qualifies`: the leading estimate `m₀(T) = 2 K_B S₀ / (P_L T²)` (`m0`) is a
  **lower bound** on the required rate: `b(T) ≥ K_B` forces `m ≥ m₀(T)`;
* `qualifies_of_ge`: if `δ = (2M + P_L) T / 3S₀ < 1` then `m ≥ m₀(T)/(1 - δ)` suffices
  for `b(T) ≥ K_B`.

So `m₀ ≤ m_req(T; M) ≤ m₀/(1 - δ)`. For equal newcomers, `M = N m/γ`; substituting
`m ≈ m₀` gives `δ ≈ 4 N K_B/(3γ P_L T) + P_L T/(3S₀)`, so `1/(1 - δ) ≈ 1 + δ` is the
report's first-corrected formula to first order. That formula itself is not proven here.
-/

open Real Set

namespace Onboarding

/-! ## Sign-definite Taylor remainders of `(1 + y)^p` -/

/-- A function vanishing at `0` with nonnegative derivative on `(0, ∞)`, differentiable on
`[0, ∞)`, is nonnegative on `[0, ∞)`. -/
theorem nonneg_of_hasDerivAt {f f' : ℝ → ℝ} (hd : ∀ y ≥ 0, HasDerivAt f (f' y) y)
    (h' : ∀ y > 0, 0 ≤ f' y) (h0 : f 0 = 0) : ∀ y ≥ 0, 0 ≤ f y := by
  have hmono : MonotoneOn f (Ici 0) := by
    refine monotoneOn_of_deriv_nonneg (convex_Ici 0)
      (fun y hy => (hd y hy).continuousAt.continuousWithinAt) ?_ ?_
    · rw [interior_Ici]
      exact fun y hy => (hd y (le_of_lt hy)).differentiableAt.differentiableWithinAt
    · rw [interior_Ici]; intro y hy; rw [(hd y (le_of_lt hy)).deriv]; exact h' y hy
  intro y hy
  rw [← h0]; exact hmono (mem_Ici.mpr le_rfl) hy hy

theorem hasDerivAt_one_add_rpow {y : ℝ} (hy : 0 ≤ y) (p : ℝ) :
    HasDerivAt (fun y => (1 + y) ^ p) (p * (1 + y) ^ (p - 1)) y := by
  have := ((hasDerivAt_id' y).const_add 1).rpow_const (p := p) (Or.inl (by positivity))
  convert this using 1; ring

/-- Bernoulli's inequality for a nonpositive exponent: `1 + p y ≤ (1 + y)^p`. -/
theorem one_add_mul_le_rpow_of_nonpos {p y : ℝ} (hp : p ≤ 0) (hy : 0 ≤ y) :
    1 + p * y ≤ (1 + y) ^ p := by
  rw [rpow_def_of_pos (by linarith)]
  have hlog : log (1 + y) ≤ y := by have := log_le_sub_one_of_pos (by linarith : 0 < 1 + y); linarith
  have := add_one_le_exp (log (1 + y) * p)
  nlinarith

/-- Second-order upper bound for a nonpositive exponent:
`(1 + y)^q ≤ 1 + q y + q(q-1)/2 · y²`. -/
theorem rpow_le_taylor2_of_nonpos {q : ℝ} (hq : q ≤ 0) :
    ∀ y ≥ 0, (1 + y) ^ q ≤ 1 + q * y + q * (q - 1) / 2 * y ^ 2 := by
  have := nonneg_of_hasDerivAt
    (f := fun y => 1 + q * y + q * (q - 1) / 2 * y ^ 2 - (1 + y) ^ q)
    (f' := fun y => q + q * (q - 1) * y - q * (1 + y) ^ (q - 1))
    (fun y hy => by
      have h1 := hasDerivAt_one_add_rpow hy q
      have h2 : HasDerivAt (fun y => 1 + q * y + q * (q - 1) / 2 * y ^ 2)
          (q + q * (q - 1) * y) y := by
        convert (((hasDerivAt_id' y).const_mul q).const_add 1).add
          ((hasDerivAt_pow 2 y).const_mul (q * (q - 1) / 2)) using 1
        push_cast; ring
      convert h2.sub h1 using 1)
    (fun y hy => by
      have := one_add_mul_le_rpow_of_nonpos (by linarith : q - 1 ≤ 0) hy.le
      nlinarith)
    (by simp)
  intro y hy; have := this y hy; linarith

/-- Second-order lower bound: `1 + r y + r(r-1)/2 · y² ≤ (1 + y)^r` for `0 ≤ r ≤ 1`. -/
theorem taylor2_le_rpow {r : ℝ} (hr0 : 0 ≤ r) (hr1 : r ≤ 1) :
    ∀ y ≥ 0, 1 + r * y + r * (r - 1) / 2 * y ^ 2 ≤ (1 + y) ^ r := by
  have := nonneg_of_hasDerivAt
    (f := fun y => (1 + y) ^ r - (1 + r * y + r * (r - 1) / 2 * y ^ 2))
    (f' := fun y => r * (1 + y) ^ (r - 1) - (r + r * (r - 1) * y))
    (fun y hy => by
      have h1 := hasDerivAt_one_add_rpow hy r
      have h2 : HasDerivAt (fun y => 1 + r * y + r * (r - 1) / 2 * y ^ 2)
          (r + r * (r - 1) * y) y := by
        convert (((hasDerivAt_id' y).const_mul r).const_add 1).add
          ((hasDerivAt_pow 2 y).const_mul (r * (r - 1) / 2)) using 1
        push_cast; ring
      exact h1.sub h2)
    (fun y hy => by
      have := one_add_mul_le_rpow_of_nonpos (by linarith : r - 1 ≤ 0) hy.le
      nlinarith)
    (by simp)
  intro y hy; have := this y hy; linarith

/-- Third-order upper bound:
`(1 + y)^r ≤ 1 + r y + r(r-1)/2 · y² + r(r-1)(r-2)/6 · y³` for `0 ≤ r ≤ 1`. -/
theorem rpow_le_taylor3 {r : ℝ} (hr0 : 0 ≤ r) (hr1 : r ≤ 1) :
    ∀ y ≥ 0, (1 + y) ^ r ≤
      1 + r * y + r * (r - 1) / 2 * y ^ 2 + r * (r - 1) * (r - 2) / 6 * y ^ 3 := by
  have := nonneg_of_hasDerivAt
    (f := fun y => 1 + r * y + r * (r - 1) / 2 * y ^ 2 + r * (r - 1) * (r - 2) / 6 * y ^ 3
      - (1 + y) ^ r)
    (f' := fun y => r + r * (r - 1) * y + r * (r - 1) * (r - 2) / 2 * y ^ 2
      - r * (1 + y) ^ (r - 1))
    (fun y hy => by
      have h1 := hasDerivAt_one_add_rpow hy r
      have h2 : HasDerivAt
          (fun y => 1 + r * y + r * (r - 1) / 2 * y ^ 2 + r * (r - 1) * (r - 2) / 6 * y ^ 3)
          (r + r * (r - 1) * y + r * (r - 1) * (r - 2) / 2 * y ^ 2) y := by
        convert ((((hasDerivAt_id' y).const_mul r).const_add 1).add
          ((hasDerivAt_pow 2 y).const_mul (r * (r - 1) / 2))).add
          ((hasDerivAt_pow 3 y).const_mul (r * (r - 1) * (r - 2) / 6)) using 1
        push_cast; ring
      exact h2.sub h1)
    (fun y hy => by
      have := rpow_le_taylor2_of_nonpos (by linarith : r - 1 ≤ 0) y hy.le
      have : 0 ≤ r * (1 + (r - 1) * y + (r - 1) * (r - 1 - 1) / 2 * y ^ 2
          - (1 + y) ^ (r - 1)) := mul_nonneg hr0 (by linarith)
      linarith)
    (by simp)
  intro y hy; have := this y hy; linarith

/-! ## Bounds on `A(t; M)` -/

variable {S0 PL M t : ℝ}

/-- `S_tot(t)/S₀ = 1 + ε` with `ε = (M + P_L) t / S₀`. -/
theorem Stot_div_S0 (hS0 : 0 < S0) : Stot S0 PL M t / S0 = 1 + (M + PL) * t / S0 :=
  (g_base hS0).symm

/-- `A(t; M) ≤ M P_L t² / 2S₀` for every `t ≥ 0`: the leading term of the small-growth
expansion is an upper bound. -/
theorem A_le_quadratic (hS0 : 0 < S0) (hM : 0 ≤ M) (hPL : 0 ≤ PL) (hMP : 0 < M + PL)
    (ht : 0 ≤ t) : A S0 PL M t ≤ M * PL * t ^ 2 / (2 * S0) := by
  have hy : 0 ≤ (M + PL) * t / S0 := by positivity
  have h := taylor2_le_rpow (r := PL / (M + PL)) (by positivity)
    (by rw [div_le_one hMP]; linarith) _ hy
  have e1 : S0 * (PL / (M + PL) * ((M + PL) * t / S0)) = PL * t := by field_simp
  have e2 : S0 * (PL / (M + PL) * (PL / (M + PL) - 1) / 2 * ((M + PL) * t / S0) ^ 2)
      = -(M * PL * t ^ 2 / (2 * S0)) := by field_simp; ring
  have := mul_le_mul_of_nonneg_left h hS0.le
  unfold A g
  nlinarith

/-- `(M P_L t² / 2S₀) [1 - (2M + P_L) t / 3S₀] ≤ A(t; M)` for every `t ≥ 0`: the
first-corrected expansion is a lower bound. -/
theorem quadratic_correction_le_A (hS0 : 0 < S0) (hM : 0 ≤ M) (hPL : 0 ≤ PL)
    (hMP : 0 < M + PL) (ht : 0 ≤ t) :
    M * PL * t ^ 2 / (2 * S0) * (1 - (2 * M + PL) * t / (3 * S0)) ≤ A S0 PL M t := by
  have hy : 0 ≤ (M + PL) * t / S0 := by positivity
  have h := rpow_le_taylor3 (r := PL / (M + PL)) (by positivity)
    (by rw [div_le_one hMP]; linarith) _ hy
  have e1 : S0 * (PL / (M + PL) * ((M + PL) * t / S0)) = PL * t := by field_simp
  have e2 : S0 * (PL / (M + PL) * (PL / (M + PL) - 1) / 2 * ((M + PL) * t / S0) ^ 2
      + PL / (M + PL) * (PL / (M + PL) - 1) * (PL / (M + PL) - 2) / 6
        * ((M + PL) * t / S0) ^ 3)
      = -(M * PL * t ^ 2 / (2 * S0) * (1 - (2 * M + PL) * t / (3 * S0))) := by
    field_simp; ring
  have := mul_le_mul_of_nonneg_left h hS0.le
  unfold A g
  nlinarith

/-! ## Consequences for the required mining rate -/

/-- Leading estimate of the required mining rate, `m₀(T) = 2 K_B S₀ / (P_L T²)`. -/
noncomputable def m0 (S0 PL KB T : ℝ) : ℝ := 2 * KB * S0 / (PL * T ^ 2)

/-- An all-locked tokenless newcomer has `b(T) ≤ m P_L T² / 2S₀`. -/
theorem unlocked_le_quadratic (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 ≤ PL) (ht : 0 ≤ t)
    {m : ℝ} (hm : 0 ≤ m) : unlocked S0 PL M 0 0 m t ≤ m * PL * t ^ 2 / (2 * S0) := by
  have h := A_le_quadratic hS0 hM.le hPL (by linarith) ht
  have := mul_le_mul_of_nonneg_left h (div_nonneg hm hM.le)
  have e : m / M * (M * PL * t ^ 2 / (2 * S0)) = m * PL * t ^ 2 / (2 * S0) := by
    field_simp
  simp only [unlocked, zero_mul, zero_add]; linarith

/-- The leading estimate `m₀(T)` underestimates the required rate: an all-locked tokenless
newcomer that qualifies by `T` (`b(T) ≥ K_B`) has `m ≥ m₀(T)`. -/
theorem m0_le_of_qualifies (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) {T KB m : ℝ}
    (hT : 0 < T) (hm : 0 ≤ m) (hq : KB ≤ unlocked S0 PL M 0 0 m T) : m0 S0 PL KB T ≤ m := by
  have := unlocked_le_quadratic hS0 hM hPL.le hT.le hm
  unfold m0
  rw [div_le_iff₀ (by positivity)]
  have : KB ≤ m * PL * T ^ 2 / (2 * S0) := by linarith
  rw [le_div_iff₀ (by positivity)] at this
  linarith

/-- A sufficient rate: if `δ = (2M + P_L) T / 3S₀ < 1` and `m ≥ m₀(T)/(1 - δ)`, an
all-locked tokenless newcomer qualifies by `T`. -/
theorem qualifies_of_ge (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 < PL) {T KB m : ℝ}
    (hT : 0 < T) (hKB : 0 ≤ KB) (hδ : (2 * M + PL) * T / (3 * S0) < 1)
    (hm : m0 S0 PL KB T / (1 - (2 * M + PL) * T / (3 * S0)) ≤ m) :
    KB ≤ unlocked S0 PL M 0 0 m T := by
  set δ := (2 * M + PL) * T / (3 * S0)
  have h1δ : 0 < 1 - δ := by linarith
  have hm0 : 0 ≤ m0 S0 PL KB T := by unfold m0; positivity
  have hm' : m0 S0 PL KB T ≤ m * (1 - δ) := by rwa [div_le_iff₀ h1δ] at hm
  have hmnn : 0 ≤ m := by
    by_contra h; have := not_le.mp h; nlinarith
  have hA := quadratic_correction_le_A hS0 hM.le hPL.le (by linarith) hT.le
  have := mul_le_mul_of_nonneg_left hA (div_nonneg hmnn hM.le)
  have e : m / M * (M * PL * T ^ 2 / (2 * S0) * (1 - δ))
      = m * (1 - δ) * (PL * T ^ 2 / (2 * S0)) := by field_simp
  have hKB' : KB = m0 S0 PL KB T * (PL * T ^ 2 / (2 * S0)) := by
    unfold m0; field_simp
  have := mul_le_mul_of_nonneg_right hm' (by positivity : 0 ≤ PL * T ^ 2 / (2 * S0))
  simp only [unlocked, zero_mul, zero_add]
  linarith

end Onboarding
