import Cryptarchia.Prob.Auto

/-!
# A two-term potential

`V2(ρ, μ) = c^ρ` when warm, and `z^μ · (s c^ρ + κ d^ρ)` when cold (`0 < d ≤ 1`). The
second term gives cold states with a small reach bound extra weight, which is
where the single-term potential is loosest. This file gives the potential after one
phase in closed form (`V2_stay`, `V2_rewarm`, `V2_warm_step`) and the honest-depth
facts the class bounds use (`hD_le_honCnt`, `min_hD_le`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ : ℕ} {w : CStr}

/-- The potential. -/
noncomputable def V2 (c z s κ d : ℝ) (st : ℤ × ℤ) : ℝ :=
  if st.2 < 0 then z ^ st.2 * (s * c ^ st.1 + κ * d ^ st.1) else c ^ st.1

variable {c z s κ d : ℝ}

theorem V2_warm {st : ℤ × ℤ} (h : 0 ≤ st.2) : V2 c z s κ d st = c ^ st.1 := by
  unfold V2; rw [if_neg (by omega)]

theorem V2_cold {st : ℤ × ℤ} (h : st.2 < 0) : V2 c z s κ d st = z ^ st.2 * (s * c ^ st.1 + κ * d ^ st.1) := by
  unfold V2; rw [if_pos h]

theorem V2_pos (hc : 0 < c) (hz : 0 < z) (hs : 0 < s) (hκ : 0 ≤ κ) (hd : 0 < d) (st : ℤ × ℤ) :
    0 < V2 c z s κ d st := by
  unfold V2; split_ifs <;> positivity

/-- Honest depth counts some of the honest slots. -/
theorem hD_le_honCnt {a : ℕ} : ∀ b, hD Δ w a b ≤ honCnt w a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    unfold hD
    by_cases hb : b ≤ a
    · simp only [hb, ↓reduceDIte, Nat.zero_le]
    · simp only [hb, ↓reduceDIte]
      have hsplit := honCnt_succ (w := w) (a := a) (b := b - 1) (by omega)
      rw [show b - 1 + 1 = b by omega] at hsplit
      by_cases hw : (w b).1 = 0
      · simp only [hw, ↓reduceIte]
        have := ih (b - 1) (by omega)
        rw [hsplit]; simp [hw]; exact this
      · simp only [hw, ↓reduceIte]
        have h1 := ih (b - Δ - 1) (by omega)
        have h2 : honCnt w a (b - Δ - 1) ≤ honCnt w a (b - 1) := by
          unfold honCnt
          apply Finset.card_le_card
          intro j hj; simp only [Finset.mem_filter, Finset.mem_Ioc] at hj ⊢; exact ⟨⟨hj.1.1, by omega⟩, hj.2⟩
        rw [hsplit]; simp [hw]; omega

theorem honIn_iff_honCnt {a b : ℕ} : HonIn w a b ↔ 1 ≤ honCnt w a b := by
  unfold HonIn honCnt
  constructor
  · rintro ⟨i, h1, h2, h3⟩; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨h1, h2⟩, h3⟩⟩
  · intro h
    obtain ⟨i, hi⟩ := Finset.card_pos.1 h
    simp only [Finset.mem_filter, Finset.mem_Ioc] at hi
    exact ⟨i, hi.1.1, hi.1.2, hi.2⟩

/-- `min(H, 2) ≤ B + U2`, and `H ≤ 1` without two honest slots. -/
theorem min_hD_le {a b : ℕ} : min (hD Δ w a b) 2 ≤
    (if 1 ≤ honCnt w a b then 1 else 0) + (if 2 ≤ honCnt w a b then 1 else 0) := by
  have := hD_le_honCnt (Δ := Δ) (w := w) (a := a) b
  split_ifs <;> omega

/-! ## The potential after one phase -/

/-- **Staying cold.** -/
theorem V2_stay {ℓ a b : ℕ} {st : ℤ × ℤ} (hm : st.2 ≤ st.1) (hcold : st.2 < -(advCnt w a b : ℤ)) :
    V2 c z s κ d (step Δ w ℓ a b st) =
      z ^ (st.2 + advCnt w a b - hD Δ w a b) *
        (s * c ^ (max (st.1 + advCnt w a b - hD Δ w a b) (advCnt w a b)) +
          κ * d ^ (max (st.1 + advCnt w a b - hD Δ w a b) (advCnt w a b))) := by
  classical
  rw [step_cases ℓ a b st hm, if_pos hcold]
  have hH : (0 : ℤ) ≤ hD Δ w a b := by positivity
  rw [V2_cold (by simp; omega)]

/-- **Rewarming.** -/
theorem V2_rewarm {ℓ a b : ℕ} {st : ℤ × ℤ} (hm : st.2 ≤ st.1) (hneg : st.2 < 0)
    (hwarm : -(advCnt w a b : ℤ) ≤ st.2) :
    V2 c z s κ d (step Δ w ℓ a b st) = c ^ (max (st.1 + advCnt w a b - hD Δ w a b) (advCnt w a b)) := by
  classical
  have hA1 : 1 ≤ advCnt w a b := by omega
  have hx : ¬ Cross w ℓ a b := fun hx => by have := hx.1; omega
  rw [step_cases ℓ a b st hm, if_neg (by omega), if_neg hx]
  rw [V2_warm (show (0 : ℤ) ≤ _ from le_trans (by positivity) (le_max_right _ _))]

/-- **A warm phase from a positive reach** stays warm. -/
theorem V2_warm_step (hc : 1 ≤ c) {ℓ a b : ℕ} [Decidable (HonIn w a b)] {ρ : ℤ} (hρ : 1 ≤ ρ) :
    V2 c z s κ d (step Δ w ℓ a b (ρ, ρ)) ≤
      c ^ ρ * c ^ ((advCnt w a b : ℤ) - (if HonIn w a b then 1 else 0)) := by
  classical
  have hr := c_pow_reach (Δ := Δ) (w := w) (ℓ := ℓ) (a := a) (b := b) hc (st := (ρ, ρ))
    (by simp; omega) (by simp)
  simp only [show (1 : ℤ) ≤ (ρ, ρ).1 from hρ, ↓reduceIte] at hr
  have hw : 0 ≤ (step Δ w ℓ a b (ρ, ρ)).2 := by
    rw [step_cases ℓ a b (ρ, ρ) (by simp)]
    simp only
    have hA : (0 : ℤ) ≤ advCnt w a b := by positivity
    rw [if_neg (by simp; omega)]
    by_cases hx : Cross w ℓ a b
    · rw [if_pos hx, hD_of_cross hx]; simp; omega
    · rw [if_neg hx]; exact le_trans hA (le_max_right _ _)
  rw [V2_warm hw]
  exact hr

/-- **A warm phase from zero reach.** A crossing makes the margin negative. -/
theorem V2_warm_zero {ℓ a b : ℕ} [Decidable (Cross w ℓ a b)] :
    V2 c z s κ d (step Δ w ℓ a b (0, 0)) ≤
      c ^ (advCnt w a b : ℤ) - (if Cross w ℓ a b then 1 - (s + κ) * z⁻¹ else 0) := by
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
    rw [V2_cold (by norm_num)]
    simp [zpow_neg, zpow_one]; ring_nf; exact le_refl _
  · rw [if_neg hx, if_neg hx, sub_zero]
    have hmax : max ((0 : ℤ) + advCnt w a b - hD Δ w a b) (advCnt w a b) = advCnt w a b := by
      apply max_eq_right; omega
    rw [hmax, V2_warm (by simpa using hA)]

/-- The failure indicator is paid for by the potential. -/
theorem fail_le2 (hc : 1 ≤ c) (hz : 1 ≤ z) (hs : 1 ≤ s) (hκ : 0 ≤ κ) (hd : 0 < d) {st : ℤ × ℤ}
    (hst : Inv st) (A : ℕ) :
    (if -(A : ℤ) ≤ st.2 then (1 : ℝ) else 0) ≤ V2 c z s κ d st * z ^ (A : ℤ) := by
  have hz0 : 0 < z := by linarith
  have hc0 : 0 < c := by linarith
  have hs0 : 0 < s := by linarith
  split_ifs with h
  · obtain ⟨h0, h1, h2⟩ := hst
    rcases le_or_gt 0 st.2 with hμ | hμ
    · rw [V2_warm hμ]
      calc (1 : ℝ) ≤ c ^ st.1 * 1 := by rw [mul_one]; exact one_le_zpow₀ hc h0
        _ ≤ c ^ st.1 * z ^ (A : ℤ) := mul_le_mul_of_nonneg_left (one_le_zpow₀ hz (by positivity))
            (by positivity)
    · rw [V2_cold hμ]
      have h1 : (1 : ℝ) ≤ s * c ^ st.1 + κ * d ^ st.1 := by
        have := one_le_zpow₀ hc h0
        have : 0 ≤ κ * d ^ st.1 := by positivity
        nlinarith
      calc (1 : ℝ) ≤ 1 * (z ^ st.2 * z ^ (A : ℤ)) := by
            rw [one_mul, ← zpow_add₀ hz0.ne']; exact one_le_zpow₀ hz (by omega)
        _ ≤ (s * c ^ st.1 + κ * d ^ st.1) * (z ^ st.2 * z ^ (A : ℤ)) :=
            mul_le_mul_of_nonneg_right h1 (by positivity)
        _ = z ^ st.2 * (s * c ^ st.1 + κ * d ^ st.1) * z ^ (A : ℤ) := by ring
  · have := V2_pos hc0 hz0 hs0 hκ hd st; positivity

end Cryptarchia.Prob
