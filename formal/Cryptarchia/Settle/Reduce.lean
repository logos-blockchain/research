import Cryptarchia.Settle.Mono

/-!
# Reducing the bound process to a Markov chain

The numeric evaluation (`model/cryptarchia_bound.py`) computes the law of a
simpler process than `bnd`. These lemmas show that process dominates `bnd`, so
the numbers bound the probability of the right event.

* `step_cases`: the phase step in closed form (the chain the script iterates).
* `reach_indep`: the reach bound does not depend on `ℓ`.
* `bnd_from`: from any phase `k0` on, `bnd` is at most the process restarted at
  `k0` from state `(ρ, ρ)` with `ρ` the reach bound there (margin credited
  nothing before `k0`).
* `run_ell`: once phases start at or after `ℓ`, the crossing test does not
  depend on `ℓ`.
-/

namespace Cryptarchia.Settle

open Finset

variable {Δ : ℕ} {w : CStr}

open Classical in
/-- **The phase step in closed form**, for a state with margin at most reach. -/
theorem step_cases (ℓ e0 e1 : ℕ) (b : ℤ × ℤ) (hb : b.2 ≤ b.1) :
    step Δ w ℓ e0 e1 b =
      (max (b.1 + (advCnt w e0 e1 : ℤ) - (hD Δ w e0 e1 : ℤ)) (advCnt w e0 e1 : ℤ),
       if b.2 < -(advCnt w e0 e1 : ℤ) then b.2 + (advCnt w e0 e1 : ℤ) - (hD Δ w e0 e1 : ℤ)
       else if Cross w ℓ e0 e1 then b.1 - (hD Δ w e0 e1 : ℤ)
       else max (b.1 + (advCnt w e0 e1 : ℤ) - (hD Δ w e0 e1 : ℤ)) (advCnt w e0 e1 : ℤ)) := by
  simp only [step]
  set A : ℤ := (advCnt w e0 e1 : ℤ)
  set H : ℤ := (hD Δ w e0 e1 : ℤ)
  have hA : 0 ≤ A := by simp only [A]; positivity
  have h1 := le_max_left (b.1 + A - H) A
  congr 1
  by_cases hx : Cross w ℓ e0 e1
  · have hA0 : A = 0 := by simp only [A]; exact_mod_cast hx.1
    by_cases hc : b.2 < -A <;> simp only [hc, hx, if_true, if_false] <;> omega
  · by_cases hc : b.2 < -A <;> simp only [hc, hx, if_true, if_false] <;> omega

/-- The step is monotone in the state (for states with margin at most reach). -/
theorem step_mono (ℓ e0 e1 : ℕ) {b b' : ℤ × ℤ} (h1 : b.1 ≤ b'.1) (h2 : b.2 ≤ b'.2)
    (hb : b.2 ≤ b.1) (hb' : b'.2 ≤ b'.1) :
    (step Δ w ℓ e0 e1 b).1 ≤ (step Δ w ℓ e0 e1 b').1 ∧
      (step Δ w ℓ e0 e1 b).2 ≤ (step Δ w ℓ e0 e1 b').2 := by
  classical
  rw [step_cases ℓ e0 e1 b hb, step_cases ℓ e0 e1 b' hb']
  simp only
  set A : ℤ := (advCnt w e0 e1 : ℤ)
  set H : ℤ := (hD Δ w e0 e1 : ℤ)
  have hA : 0 ≤ A := by simp only [A]; positivity
  refine ⟨max_le_max (by omega) le_rfl, ?_⟩
  have m1 := le_max_left (b.1 + A - H) A
  have m2 := le_max_left (b'.1 + A - H) A
  have m3 : max (b.1 + A - H) A ≤ max (b'.1 + A - H) A := max_le_max (by omega) le_rfl
  by_cases hc' : b'.2 < -A
  · have hc : b.2 < -A := by omega
    rw [if_pos hc, if_pos hc']; omega
  · rw [if_neg hc']
    by_cases hx : Cross w ℓ e0 e1
    · have hA0 : A = 0 := by simp only [A]; exact_mod_cast hx.1
      by_cases hc : b.2 < -A <;> simp only [hc, hx, if_true, if_false] <;> omega
    · by_cases hc : b.2 < -A <;> simp only [hc, hx, if_true, if_false] <;> omega

/-- The bound process restarted at phase `k0` from state `b0`. -/
noncomputable def runFrom (ℓ : ℕ) (e : ℕ → ℕ) (k0 : ℕ) (b0 : ℤ × ℤ) : ℕ → ℤ × ℤ
  | 0 => b0
  | j + 1 => step Δ w ℓ (e (k0 + j)) (e (k0 + j + 1)) (runFrom ℓ e k0 b0 j)

theorem runFrom_le (ℓ : ℕ) (e : ℕ → ℕ) (k0 : ℕ) {b0 : ℤ × ℤ} (hb : b0.2 ≤ b0.1) :
    ∀ j, (runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j).2 ≤ (runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j).1 := by
  intro j
  cases j with
  | zero => exact hb
  | succ j => simp only [runFrom, step]; exact min_le_left _ _

theorem bnd_eq_runFrom (ℓ : ℕ) (e : ℕ → ℕ) (k0 : ℕ) :
    ∀ j, bnd Δ w ℓ e (k0 + j) = runFrom (Δ := Δ) (w := w) ℓ e k0 (bnd Δ w ℓ e k0) j := by
  intro j
  induction j with
  | zero => rfl
  | succ j ih => rw [← Nat.add_assoc, bnd, runFrom, ih]

/-- **The reach bound does not depend on `ℓ`.** -/
theorem reach_indep (ℓ ℓ' : ℕ) (e : ℕ → ℕ) : ∀ k, (bnd Δ w ℓ e k).1 = (bnd Δ w ℓ' e k).1 := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih => simp only [bnd, step]; rw [ih]

/-- **Restart with margin = reach.** From any phase `k0` on, the bound process is
at most the one restarted at `k0` from `(ρ, ρ)`, `ρ` the reach bound at `k0`. -/
theorem bnd_from (ℓ : ℕ) (e : ℕ → ℕ) (k0 : ℕ) :
    ∀ j, (bnd Δ w ℓ e (k0 + j)).1 ≤
        (runFrom (Δ := Δ) (w := w) ℓ e k0 ((bnd Δ w ℓ e k0).1, (bnd Δ w ℓ e k0).1) j).1 ∧
      (bnd Δ w ℓ e (k0 + j)).2 ≤
        (runFrom (Δ := Δ) (w := w) ℓ e k0 ((bnd Δ w ℓ e k0).1, (bnd Δ w ℓ e k0).1) j).2 := by
  intro j
  induction j with
  | zero => exact ⟨le_rfl, bnd_le ℓ e k0⟩
  | succ j ih =>
    rw [← Nat.add_assoc]
    simp only [bnd, runFrom]
    exact step_mono ℓ _ _ ih.1 ih.2 (bnd_le ℓ e (k0 + j)) (runFrom_le ℓ e k0 le_rfl j)

/-- **Crossings after `ℓ`.** If phase `k0` starts at or after `ℓ`, the restarted
process does not depend on `ℓ`. -/
theorem run_ell (ℓ : ℕ) (e : ℕ → ℕ) (hmono : ∀ k, e k ≤ e (k + 1)) (k0 : ℕ) (hℓ : ℓ ≤ e k0)
    (b0 : ℤ × ℤ) : ∀ j, runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j = runFrom (Δ := Δ) (w := w) 0 e k0 b0 j := by
  have hmono' : ∀ a b, a ≤ b → e a ≤ e b := fun a b hab => by
    induction b with
    | zero => rw [Nat.le_zero.1 hab]
    | succ b ih =>
      rcases Nat.eq_or_lt_of_le hab with h | h
      · rw [h]
      · exact le_trans (ih (by omega)) (hmono b)
  intro j
  induction j with
  | zero => rfl
  | succ j ih =>
    simp only [runFrom]; rw [ih]
    unfold step
    have hx : Cross w ℓ (e (k0 + j)) (e (k0 + j + 1)) ↔ Cross w 0 (e (k0 + j)) (e (k0 + j + 1)) := by
      have := hmono' k0 (k0 + j) (by omega)
      constructor
      · rintro ⟨hA, s, h1, h2, -, h4, h5⟩; exact ⟨hA, s, h1, h2, Nat.zero_le _, h4, h5⟩
      · rintro ⟨hA, s, h1, h2, -, h4, h5⟩; exact ⟨hA, s, h1, h2, by omega, h4, h5⟩
    rw [show Cross w ℓ (e (k0 + j)) (e (k0 + j + 1)) = Cross w 0 (e (k0 + j)) (e (k0 + j + 1)) from
      propext hx]

/-- **The cold test reduces to the restarted chain.** If phase `k0` starts at or
after `ℓ` and the chain restarted there from the reach bound (with crossings
credited from `k0` on) is cold at phase `k`, then so is `bnd`. -/
theorem cold_of_run (ℓ : ℕ) (e : ℕ → ℕ) (hmono : ∀ k, e k ≤ e (k + 1)) {k0 k : ℕ} (hk : k0 ≤ k)
    (hℓ : ℓ ≤ e k0)
    (hc : (runFrom (Δ := Δ) (w := w) 0 e k0 ((bnd Δ w 0 e k0).1, (bnd Δ w 0 e k0).1) (k - k0)).2 <
      -(advCnt w (e k) (e (k + 1)) : ℤ)) :
    (bnd Δ w ℓ e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ) := by
  have h := (bnd_from (Δ := Δ) (w := w) ℓ e k0 (k - k0)).2
  rw [Nat.add_sub_cancel' hk, reach_indep ℓ 0 e k0,
    run_ell ℓ e hmono k0 hℓ] at h
  exact lt_of_le_of_lt h hc

/-- **The cold condition of `GoodL` from a window of phases.** For a time `t` in
phase `k + 1`: if the `k - k0` phases before it and itself span at most `Lw`
slots, and the chain restarted at `k0` is cold, the cold condition holds at `t`. -/
theorem cold_of_window (e : ℕ → ℕ) (hmono : ∀ k, e k ≤ e (k + 1)) {Lw t k k0 : ℕ} (hk : k0 ≤ k)
    (ht : t ≤ e (k + 1)) (hW : e (k + 1) ≤ e k0 + Lw)
    (hc : (runFrom (Δ := Δ) (w := w) 0 e k0 ((bnd Δ w 0 e k0).1, (bnd Δ w 0 e k0).1) (k - k0)).2 <
      -(advCnt w (e k) (e (k + 1)) : ℤ)) :
    (bnd Δ w (t - Lw) e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ) :=
  cold_of_run (t - Lw) e hmono hk (by omega) hc

end Cryptarchia.Settle
