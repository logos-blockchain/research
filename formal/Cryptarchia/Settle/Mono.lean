import Cryptarchia.Settle.Phases

/-!
# The bounds are monotone in adversarial slots

With the same honest successes, a string with fewer adversarial slots has smaller
reach and margin bounds (`bnd_mono`) and fewer occupied slots. So a good event
checked on the lottery's string (every adversarial win) implies the good event
on any string whose adversarial slots are among them.
-/

namespace Cryptarchia.Settle

open Finset

variable {Δ : ℕ} {w w' : CStr}

/-- Up to slot `N`, `w'` has the same honest successes as `w`; after `N`, `w`
has none; and `w'` has at least `w`'s adversarial slots. -/
def AdvLe (N : ℕ) (w w' : CStr) : Prop :=
  (∀ i, 1 ≤ i → i ≤ N → (w i).1 = (w' i).1) ∧ (∀ i, N < i → (w i).1 = 0) ∧
    (∀ i, (w i).2 = true → (w' i).2 = true)

/-- The weak form: equal honest successes up to `N`, adversarial slots included. -/
def AdvLeW (N : ℕ) (w w' : CStr) : Prop :=
  (∀ i, 1 ≤ i → i ≤ N → (w i).1 = (w' i).1) ∧ (∀ i, (w i).2 = true → (w' i).2 = true)

variable {N : ℕ}

theorem AdvLe.weak (h : AdvLe N w w') : AdvLeW N w w' := ⟨h.1, h.2.2⟩

theorem AdvLeW.refl (w : CStr) : AdvLeW N w w := ⟨fun _ _ _ => rfl, fun _ h => h⟩

theorem AdvLeW.trans {w'' : CStr} {N' : ℕ} (h : AdvLeW N w w') (h' : AdvLeW N' w' w'') (hN : N ≤ N') :
    AdvLeW N w w'' :=
  ⟨fun i h1 h2 => (h.1 i h1 h2).trans (h'.1 i h1 (by omega)), fun i hi => h'.2 i (h.2 i hi)⟩

theorem advCnt_le (h : AdvLeW N w w') (a b : ℕ) : advCnt w a b ≤ advCnt w' a b := by
  unfold advCnt
  apply card_le_card
  intro j hj
  simp only [mem_filter] at hj ⊢
  exact ⟨hj.1, h.2 j hj.2⟩

theorem occCnt_le (h : AdvLeW N w w') {a b : ℕ} (hb : b ≤ N) : occCnt w a b ≤ occCnt w' a b := by
  unfold occCnt
  apply card_le_card
  intro j hj
  simp only [mem_filter, mem_Ioc] at hj ⊢
  refine ⟨hj.1, ?_⟩
  rcases hj.2 with h1 | h2
  · left; rw [← h.1 j (by omega) (by omega)]; exact h1
  · right; exact h.2 j h2

theorem hD_eq (h : AdvLeW N w w') (a : ℕ) : ∀ b, b ≤ N → hD Δ w a b = hD Δ w' a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro hbN
    conv_lhs => rw [hD]
    conv_rhs => rw [hD]
    by_cases hb : b ≤ a
    · rw [dif_pos hb, dif_pos hb]
    rw [dif_neg hb, dif_neg hb, h.1 b (by omega) hbN]
    split
    · exact ih _ (by omega) (by omega)
    · rw [ih _ (by omega) (by omega)]

theorem quiet_of (h : AdvLe N w w') (m : ℕ) : Quiet Δ w' m → Quiet Δ w m := by
  unfold Quiet
  intro hq j h1 h2 h3
  by_cases hjN : j ≤ N
  · rw [h.1 j h3 hjN]; exact hq j h1 h2 h3
  · exact h.2.1 j (by omega)

theorem quiet_of_le (h : AdvLeW N w w') {m : ℕ} (hm : m ≤ N) : Quiet Δ w' m → Quiet Δ w m := by
  unfold Quiet
  intro hq j h1 h2 h3
  rw [h.1 j h3 (by omega)]; exact hq j h1 h2 h3

theorem cross_of (h : AdvLeW N w w') {ℓ a b : ℕ} (hbN : b ≤ N) (hc : Cross w' ℓ a b) : Cross w ℓ a b := by
  obtain ⟨hA, s, h1, h2, h3, h4, h5⟩ := hc
  refine ⟨Nat.eq_zero_of_le_zero (hA ▸ advCnt_le h a b), s, h1, h2, h3,
    by rw [h.1 s (by omega) (by omega)]; exact h4, ?_⟩
  intro i hi1 hi2 hne; rw [h.1 i (by omega) (by omega)]; exact h5 i hi1 hi2 hne

/-- The margin bound never exceeds the reach bound. -/
theorem bnd_le (ℓ : ℕ) (e : ℕ → ℕ) : ∀ k, (bnd Δ w ℓ e k).2 ≤ (bnd Δ w ℓ e k).1 := by
  intro k
  cases k with
  | zero => simp [bnd]
  | succ k => simp only [bnd, step]; exact min_le_left _ _

open Classical in
/-- **Monotonicity of the bound process.** -/
theorem bnd_mono (h : AdvLeW N w w') (ℓ : ℕ) (e : ℕ → ℕ) (hmono : ∀ k, e k ≤ e (k + 1)) :
    ∀ k, e k ≤ N → (bnd Δ w ℓ e k).1 ≤ (bnd Δ w' ℓ e k).1 ∧ (bnd Δ w ℓ e k).2 ≤ (bnd Δ w' ℓ e k).2 := by
  intro k
  induction k with
  | zero => intro _; simp [bnd]
  | succ k ih =>
    intro hkN
    obtain ⟨h1, h2⟩ := ih (le_trans (hmono k) hkN)
    have hle := bnd_le (Δ := Δ) (w := w) ℓ e k
    have hle' := bnd_le (Δ := Δ) (w := w') ℓ e k
    have hA := advCnt_le h (e k) (e (k + 1))
    have hH := hD_eq (Δ := Δ) h (e k) (e (k + 1)) hkN
    simp only [bnd, step]
    set b := bnd Δ w ℓ e k
    set b' := bnd Δ w' ℓ e k
    set A : ℤ := (advCnt w (e k) (e (k + 1)) : ℤ)
    set A' : ℤ := (advCnt w' (e k) (e (k + 1)) : ℤ)
    set H : ℤ := (hD Δ w (e k) (e (k + 1)) : ℤ)
    have hAA : A ≤ A' := by simp only [A, A']; exact_mod_cast hA
    have hHH : (hD Δ w' (e k) (e (k + 1)) : ℤ) = H := by simp only [H]; rw [hH]
    rw [hHH]
    have hρ : max (b.1 + A - H) A ≤ max (b'.1 + A' - H) A' := max_le_max (by omega) hAA
    refine ⟨hρ, ?_⟩
    apply le_min (le_trans (min_le_left _ _) hρ)
    apply le_min
    · -- the cold branch
      by_cases hc' : b'.2 < -A'
      · rw [if_pos hc']
        have hc : b.2 < -A := by omega
        refine le_trans (min_le_right _ _) (le_trans (min_le_left _ _) ?_)
        rw [if_pos hc]; omega
      · rw [if_neg hc']; exact le_trans (min_le_left _ _) hρ
    · -- the crossing branch
      by_cases hx' : Cross w' ℓ (e k) (e (k + 1))
      · rw [if_pos hx']
        refine le_trans (min_le_right _ _) (le_trans (min_le_right _ _) ?_)
        rw [if_pos (cross_of h hkN hx')]; omega
      · rw [if_neg hx']; exact le_trans (min_le_left _ _) hρ

end Cryptarchia.Settle
