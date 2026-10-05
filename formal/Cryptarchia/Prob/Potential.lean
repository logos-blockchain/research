import Cryptarchia.Prob.Phases

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

/-- The potential of a state `(ρ, μ)`: `c^ρ` when warm, `s · c^ρ · z^μ` when cold. -/
noncomputable def V (c z s : ℝ) (st : ℤ × ℤ) : ℝ := c ^ st.1 * (if st.2 < 0 then s * z ^ st.2 else 1)

/-- Warm (margin = reach ≥ 0) or cold (margin < 0), reach nonnegative. -/
def Inv (st : ℤ × ℤ) : Prop := 0 ≤ st.1 ∧ (st.2 = st.1 ∨ st.2 < 0) ∧ st.2 ≤ st.1

variable {c z s : ℝ}

theorem V_pos (hc : 0 < c) (hz : 0 < z) (hs : 0 < s) (st : ℤ × ℤ) : 0 < V c z s st := by
  unfold V; split_ifs <;> positivity

theorem V_warm {st : ℤ × ℤ} (h : 0 ≤ st.2) : V c z s st = c ^ st.1 := by
  unfold V; rw [if_neg (by omega), mul_one]

theorem V_cold {st : ℤ × ℤ} (h : st.2 < 0) : V c z s st = s * c ^ st.1 * z ^ st.2 := by
  unfold V; rw [if_pos h]; ring

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

/-- **Warm, positive reach.** -/
theorem warm_pos (hc : 1 ≤ c) {ℓ a b : ℕ} [Decidable (HonIn w a b)] {ρ : ℤ} (hρ : 1 ≤ ρ) :
    V c z s (step Δ w ℓ a b (ρ, ρ)) ≤
      V c z s (ρ, ρ) * c ^ ((advCnt w a b : ℤ) - (if HonIn w a b then 1 else 0)) := by
  classical
  have hinv := inv_step (Δ := Δ) (w := w) (ℓ := ℓ) (a := a) (b := b) (inv_start (by omega : (0 : ℤ) ≤ ρ))
  have hr := c_pow_reach (Δ := Δ) (w := w) (ℓ := ℓ) (a := a) (b := b) hc (st := (ρ, ρ))
    (by simp; omega) (by simp)
  simp only [show (1 : ℤ) ≤ (ρ, ρ).1 from hρ, ↓reduceIte] at hr
  rw [V_warm (show (0 : ℤ) ≤ (ρ, ρ).2 by simp; omega)]
  -- after a warm phase from a positive reach, the margin stays nonnegative
  have hw : 0 ≤ (step Δ w ℓ a b (ρ, ρ)).2 := by
    rw [step_cases ℓ a b (ρ, ρ) (by simp)]
    simp only
    have hA : (0 : ℤ) ≤ advCnt w a b := by positivity
    rw [if_neg (by simp; omega)]
    by_cases hx : Cross w ℓ a b
    · rw [if_pos hx, hD_of_cross hx]; simp; omega
    · rw [if_neg hx]; exact le_trans hA (le_max_right _ _)
  rw [V_warm hw]
  exact hr

/-- **Warm, zero reach.** A crossing makes the margin negative. -/
theorem warm_zero {ℓ a b : ℕ} [Decidable (Cross w ℓ a b)] :
    V c z s (step Δ w ℓ a b (0, 0)) ≤
      c ^ (advCnt w a b : ℤ) - (if Cross w ℓ a b then 1 - s * z⁻¹ else 0) := by
  classical
  rw [step_cases ℓ a b (0, 0) le_rfl]
  simp only
  have hA : (0 : ℤ) ≤ advCnt w a b := by positivity
  have hH : (0 : ℤ) ≤ hD Δ w a b := by positivity
  rw [if_neg (by omega)]
  by_cases hx : Cross w ℓ a b
  · rw [if_pos hx, if_pos hx]
    have hA0 : advCnt w a b = 0 := hx.1
    have hH1 : hD Δ w a b = 1 := hD_of_cross hx
    simp only [hA0, hH1, Nat.cast_zero, Nat.cast_one, zero_add, zero_sub]
    unfold V
    simp [zpow_neg, zpow_one]
  · rw [if_neg hx, if_neg hx, sub_zero]
    have hmax : max ((0 : ℤ) + advCnt w a b - hD Δ w a b) (advCnt w a b) = advCnt w a b := by
      apply max_eq_right; omega
    rw [hmax, V_warm (by simpa using hA)]

/-- **Cold.** With `1 ≤ s ≤ z`: a phase with an honest success earns `1/s`, and one
with no adversarial slot earns `1/z`. -/
theorem cold_step (hc : 1 ≤ c) (hz : 1 ≤ z) (hs : 1 ≤ s) (hsz : s ≤ z) {ℓ a b : ℕ} [Decidable (HonIn w a b)]
    {st : ℤ × ℤ} (h0 : 0 ≤ st.1) (hneg : st.2 < 0) (hm : st.2 ≤ st.1) :
    V c z s (step Δ w ℓ a b st) ≤
      V c z s st * ((c * z) ^ (advCnt w a b : ℤ) * (if HonIn w a b then s⁻¹ else 1) -
        (if advCnt w a b = 0 ∧ HonIn w a b then s⁻¹ - z⁻¹ else 0)) := by
  classical
  have hc0 : 0 < c := by linarith
  have hz0 : 0 < z := by linarith
  have hs0 : 0 < s := by linarith
  have hB := hD_ge_ind (Δ := Δ) (w := w) (a := a) (b := b)
  have hzs : z⁻¹ ≤ s⁻¹ := inv_anti₀ hs0 hsz
  have hs1 : s⁻¹ ≤ 1 := inv_le_one_of_one_le₀ hs
  rw [V_cold hneg]
  rw [step_cases ℓ a b st hm]
  set A : ℤ := (advCnt w a b : ℤ) with hAdef
  set H : ℤ := (hD Δ w a b : ℤ) with hHdef
  have hA : 0 ≤ A := by positivity
  have hρ' : max (st.1 + A - H) A ≤ st.1 + A := by apply max_le <;> omega
  have hcA : c ^ max (st.1 + A - H) A ≤ c ^ st.1 * c ^ A := by
    rw [← zpow_add₀ hc0.ne']; exact zpow_le_zpow_right₀ hc hρ'
  have hczA : (c * z) ^ A = c ^ A * z ^ A := mul_zpow c z A
  by_cases hcold : st.2 < -A
  · -- stays cold
    rw [if_pos hcold, V_cold (show st.2 + A - H < 0 by omega)]
    have h2 : z ^ (st.2 + A - H) = z ^ st.2 * z ^ A * z ^ (-H) := by
      rw [← zpow_add₀ hz0.ne', ← zpow_add₀ hz0.ne']; ring_nf
    rw [h2]
    -- the factor `z^(-H)`
    have hzH : z ^ (-H) ≤ (if HonIn w a b then s⁻¹ else 1) -
        (if advCnt w a b = 0 ∧ HonIn w a b then s⁻¹ - z⁻¹ else 0) * (z ^ A)⁻¹ := by
      by_cases hb : HonIn w a b
      · have hH1 : (1 : ℤ) ≤ H := by simpa [hb] using hB
        have hzH1 : z ^ (-H) ≤ z⁻¹ := by
          rw [← zpow_neg_one]; exact zpow_le_zpow_right₀ hz (by omega)
        rw [if_pos hb]
        by_cases ha : advCnt w a b = 0
        · rw [if_pos ⟨ha, hb⟩]
          have : A = 0 := by simp [hAdef, ha]
          rw [this, zpow_zero, inv_one, mul_one]; linarith
        · rw [if_neg (fun h => ha h.1), zero_mul, sub_zero]; linarith
      · rw [if_neg hb, if_neg (fun h => hb h.2), zero_mul, sub_zero]
        exact zpow_le_one_of_nonpos₀ hz (by omega)
    have hzA : 0 < z ^ A := zpow_pos hz0 A
    calc s * c ^ max (st.1 + A - H) A * (z ^ st.2 * z ^ A * z ^ (-H))
        ≤ s * (c ^ st.1 * c ^ A) * (z ^ st.2 * z ^ A * ((if HonIn w a b then s⁻¹ else 1) -
            (if advCnt w a b = 0 ∧ HonIn w a b then s⁻¹ - z⁻¹ else 0) * (z ^ A)⁻¹)) := by
          apply mul_le_mul (mul_le_mul_of_nonneg_left hcA hs0.le) _ (by positivity) (by positivity)
          exact mul_le_mul_of_nonneg_left hzH (by positivity)
      _ = s * c ^ st.1 * z ^ st.2 * ((c * z) ^ A * (if HonIn w a b then s⁻¹ else 1) -
            (if advCnt w a b = 0 ∧ HonIn w a b then s⁻¹ - z⁻¹ else 0) * c ^ A) := by
          rw [hczA]; field_simp
      _ ≤ _ := by
          apply mul_le_mul_of_nonneg_left _ (by positivity)
          by_cases hh : advCnt w a b = 0 ∧ HonIn w a b
          · have : A = 0 := by simp [hAdef, hh.1]
            rw [if_pos hh, this, zpow_zero]; simp
          · rw [if_neg hh]; simp
  · -- rewarms: not a crossing (it needs `A = 0`); the margin becomes the reach
    rw [if_neg hcold]
    have hA1 : 1 ≤ A := by omega
    have hx : ¬ Cross w ℓ a b := by
      intro hx; have : A = 0 := by simp only [hAdef]; exact_mod_cast hx.1
      omega
    rw [if_neg hx, V_warm (le_trans (by omega) (le_max_right _ _))]
    have hnA : ¬ (advCnt w a b = 0 ∧ HonIn w a b) := by
      rintro ⟨h, -⟩; have : A = 0 := by simp only [hAdef]; exact_mod_cast h
      omega
    rw [if_neg hnA, sub_zero]
    -- `c^ρ' ≤ c^ρ c^A ≤ s c^ρ z^μ · (c z)^A / s`, as `z^(μ + A) ≥ 1`
    have h2 : (1 : ℝ) ≤ z ^ st.2 * z ^ A := by
      rw [← zpow_add₀ hz0.ne']; exact one_le_zpow₀ hz (by omega)
    have hy : s⁻¹ ≤ (if HonIn w a b then s⁻¹ else 1) := by split_ifs <;> linarith
    calc c ^ max (st.1 + A - H) A ≤ c ^ st.1 * c ^ A := hcA
      _ ≤ c ^ st.1 * c ^ A * (z ^ st.2 * z ^ A) := le_mul_of_one_le_right (by positivity) h2
      _ = s * c ^ st.1 * z ^ st.2 * ((c * z) ^ A * s⁻¹) := by rw [hczA]; field_simp
      _ ≤ s * c ^ st.1 * z ^ st.2 * ((c * z) ^ A * (if HonIn w a b then s⁻¹ else 1)) := by
          apply mul_le_mul_of_nonneg_left _ (by positivity)
          exact mul_le_mul_of_nonneg_left hy (by positivity)

/-- A margin that is not cold at the next phase is paid for by the potential. -/
theorem fail_le (hc : 1 ≤ c) (hz : 1 ≤ z) (hs : 1 ≤ s) {st : ℤ × ℤ} (hst : Inv st) (A : ℕ) :
    (if -(A : ℤ) ≤ st.2 then (1 : ℝ) else 0) ≤ V c z s st * z ^ (A : ℤ) := by
  have hz0 : 0 < z := by linarith
  have hc0 : 0 < c := by linarith
  have hs0 : 0 < s := by linarith
  split_ifs with h
  · obtain ⟨h0, h1, h2⟩ := hst
    rcases le_or_gt 0 st.2 with hμ | hμ
    · rw [V_warm hμ]
      calc (1 : ℝ) ≤ c ^ st.1 * 1 := by rw [mul_one]; exact one_le_zpow₀ hc h0
        _ ≤ c ^ st.1 * z ^ (A : ℤ) := mul_le_mul_of_nonneg_left (one_le_zpow₀ hz (by positivity))
            (by positivity)
    · rw [V_cold hμ]
      calc (1 : ℝ) ≤ 1 * 1 * (z ^ st.2 * z ^ (A : ℤ)) := by
            rw [one_mul, one_mul, ← zpow_add₀ hz0.ne']; exact one_le_zpow₀ hz (by omega)
        _ ≤ s * c ^ st.1 * (z ^ st.2 * z ^ (A : ℤ)) := by
            apply mul_le_mul_of_nonneg_right _ (by positivity)
            exact mul_le_mul hs (one_le_zpow₀ hc h0) zero_le_one hs0.le
        _ = s * c ^ st.1 * z ^ st.2 * z ^ (A : ℤ) := by ring
  · have := V_pos hc0 hz0 hs0 st; positivity

end Cryptarchia.Prob
