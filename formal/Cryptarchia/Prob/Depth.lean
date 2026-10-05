import Cryptarchia.Prob.Potential

/-!
# Honest depth over blocks

Honest depth `hD a b` (Def. 6 of Gaži–Ren–Russell: the greedy count of honest
slots more than `Δ` apart in `(a, b]`) is monotone in `b` (`hD_mono`) and
superadditive across a gap of `Δ` slots (`hD_super`). So over blocks of `T` slots
separated by gaps of `Δ`, it is at least the number of blocks with an honest
success (`hD_blocks`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ : ℕ} {w : CStr}

/-- Monotone in the right end, and a window of at most `Δ + 1` slots adds at most one. -/
theorem hD_mono_aux (a : ℕ) : ∀ b, (∀ b' ≤ b, hD Δ w a b' ≤ hD Δ w a b) ∧
    (∀ d ≤ Δ + 1, hD Δ w a b ≤ hD Δ w a (b - d) + 1) := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    -- the window property at `b`
    have hL : ∀ d ≤ Δ + 1, hD Δ w a b ≤ hD Δ w a (b - d) + 1 := by
      intro d hd
      rcases Nat.eq_zero_or_pos d with rfl | hd0
      · simp
      unfold hD
      by_cases hb : b ≤ a
      · simp only [hb, ↓reduceDIte]; omega
      · simp only [hb, ↓reduceDIte]
        by_cases hw : (w b).1 = 0
        · simp only [hw, ↓reduceIte]
          have := (ih (b - 1) (by omega)).2 (d - 1) (by omega)
          rw [show b - 1 - (d - 1) = b - d by omega] at this
          conv_rhs => rw [← hD.eq_def]
          exact this
        · simp only [hw, ↓reduceIte]
          have hm := (ih (b - d) (by omega)).1 (b - Δ - 1) (by omega)
          conv_rhs => rw [← hD.eq_def]
          omega
    refine ⟨?_, hL⟩
    intro b' hb'
    rcases Nat.eq_or_lt_of_le hb' with rfl | hlt
    · exact le_rfl
    · -- `b' ≤ b - 1 < b`
      have h1 := (ih (b - 1) (by omega)).1 b' (by omega)
      have h2 : hD Δ w a (b - 1) ≤ hD Δ w a b := by
        conv_rhs => unfold hD
        by_cases hb : b ≤ a
        · have : hD Δ w a (b - 1) = 0 := by unfold hD; simp [show b - 1 ≤ a by omega]
          simp [hb, this]
        · simp only [hb, ↓reduceDIte]
          by_cases hw : (w b).1 = 0
          · simp only [hw, ↓reduceIte, le_refl]
          · simp only [hw, ↓reduceIte]
            have := (ih (b - 1) (by omega)).2 Δ (by omega)
            rw [show b - 1 - Δ = b - Δ - 1 by omega] at this
            exact this
      omega

theorem hD_mono {a b b' : ℕ} (h : b' ≤ b) : hD Δ w a b' ≤ hD Δ w a b := (hD_mono_aux a b).1 b' h

/-- **Superadditivity across a gap of `Δ` slots.** -/
theorem hD_super {a m : ℕ} (ham : a ≤ m) : ∀ b, m + Δ ≤ b →
    hD Δ w a m + hD Δ w (m + Δ) b ≤ hD Δ w a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro hb
    by_cases hbm : b ≤ m + Δ
    · have : b = m + Δ := by omega
      subst this
      have h0 : hD Δ w (m + Δ) (m + Δ) = 0 := by unfold hD; simp
      rw [h0, add_zero]; exact hD_mono (by omega)
    · conv_lhs => arg 2; unfold hD
      conv_rhs => unfold hD
      have hb1 : ¬ b ≤ m + Δ := hbm
      have hb2 : ¬ b ≤ a := by omega
      simp only [hb1, hb2, ↓reduceDIte]
      by_cases hw : (w b).1 = 0
      · simp only [hw, ↓reduceIte]
        exact ih (b - 1) (by omega) (by omega)
      · simp only [hw, ↓reduceIte]
        by_cases hc : m + Δ ≤ b - Δ - 1
        · have := ih (b - Δ - 1) (by omega) hc
          omega
        · have h0 : hD Δ w (m + Δ) (b - Δ - 1) = 0 := by unfold hD; simp [show b - Δ - 1 ≤ m + Δ by omega]
          rw [h0]
          have := hD_mono (Δ := Δ) (w := w) (a := a) (show m ≤ b - Δ - 1 by omega)
          omega

/-- An honest success in block `i`: some slot among the first `T` after `y + i Lb`. -/
def blockHon (w : CStr) (y Lb T i : ℕ) : Prop := ∃ j, y + i * Lb < j ∧ j ≤ y + i * Lb + T ∧ (w j).1 ≠ 0

/-- **Honest depth over blocks.** With blocks of `T` slots followed by gaps of `Δ`
(`Lb = T + Δ`), honest depth over the first `n` blocks is at least the number of
blocks with an honest success. -/
theorem hD_blocks {y T Lb : ℕ} (hLb : Lb = T + Δ) [DecidablePred fun i => blockHon w y Lb T i] :
    ∀ n, ((Finset.range (n + 1)).filter fun i => blockHon w y Lb T i).card ≤
      hD Δ w y (y + n * Lb + T) := by
  intro n
  induction n with
  | zero =>
    simp only [zero_add, Finset.range_one, Finset.filter_singleton, zero_mul, add_zero]
    split_ifs with hh
    · obtain ⟨j, h1, h2, h3⟩ := hh
      simp only [Finset.card_singleton]
      exact one_le_hD _ ⟨j, by simpa using h1, by simpa using h2, h3⟩
    · simp
  | succ n ih =>
    rw [Finset.range_add_one, Finset.filter_insert]
    have hsup := hD_super (Δ := Δ) (w := w) (a := y) (m := y + n * Lb + T) (by omega)
      (y + (n + 1) * Lb + T) (by rw [hLb]; ring_nf; omega)
    have hstart : y + n * Lb + T + Δ = y + (n + 1) * Lb := by rw [hLb]; ring
    rw [hstart] at hsup
    split_ifs with hh
    · have hnot : n + 1 ∉ (Finset.range (n + 1)).filter fun i => blockHon w y Lb T i := by simp
      rw [Finset.card_insert_of_notMem hnot]
      have h1 : 1 ≤ hD Δ w (y + (n + 1) * Lb) (y + (n + 1) * Lb + T) := by
        obtain ⟨j, h1, h2, h3⟩ := hh
        exact one_le_hD _ ⟨j, h1, h2, h3⟩
      omega
    · omega

end Cryptarchia.Prob
