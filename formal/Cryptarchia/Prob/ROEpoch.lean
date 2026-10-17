module

public import Cryptarchia.Prob.WorstE
public import Cryptarchia.Prob.RO

/-!
# Epochs and what is known before a slot

A slot's epoch state depends only on its epoch (`σE`), so consecutive slots of one epoch
run under the same state (`σE_succ`). What is known before a slot (`hist`) grows with
the slot (`hist_mono`) and knows the slot's epoch state (`measurable_hist_σ`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Settle
open scoped ENNReal

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env}

/-- Consecutive slots of one epoch run under the same epoch state. -/
theorem σE_succ (E : Env) (es : List Event) {n : ℕ} (h : (n + 2) % E.c.epochLength ≠ 0) :
    σE E es (n + 2) = σE E es (n + 1) := by
  unfold σE Config.epochOf
  congr 1
  rw [show n + 2 = (n + 1) + 1 by omega, Nat.succ_div, if_neg (fun hd => h (Nat.mod_eq_zero_of_dvd hd)), add_zero]

/-- Consecutive slots of one epoch have the same epoch index. -/
theorem div_succ_of_mod {EL n : ℕ} (h : (n + 2) % EL ≠ 0) : (n + 2) / EL = (n + 1) / EL := by
  rw [show n + 2 = (n + 1) + 1 by omega, Nat.succ_div, if_neg (fun hd => h (Nat.mod_eq_zero_of_dvd hd)), add_zero]

theorem hist_mono (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) {j n : ℕ} (h : j ≤ n) : hist O σ j ≤ hist O σ n :=
  sup_le_sup (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)
    (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)

/-- Slot `n`'s epoch state is known before slot `n`'s tickets are drawn. -/
theorem measurable_hist_σ (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) (n : ℕ) :
    Measurable[hist O σ n] fun ω => σ ω n :=
  (comap_measurable (fun ω => σ ω n)).mono
    (le_sup_of_le_right (le_iSup₂_of_le n (Finset.mem_range.2 (Nat.lt_succ_self n)) le_rfl)) le_rfl

end Cryptarchia.Prob
