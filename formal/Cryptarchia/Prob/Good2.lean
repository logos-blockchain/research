import Cryptarchia.Prob.Fail2
import Cryptarchia.Prob.Good

/-!
# The cold condition from rare spans and rare failed checks

`cold_of_checks`: on a full history, if every run of `G'` slots before `N` has an
occupied slot, no `J + 1` consecutive phases (up to `Hc = N + G'`) span more than
`Lw` slots, and no check before a nonempty phase fails (anchored `J` phases back),
then the cold condition of `GoodLS` holds at every slot. A check before an empty
phase needs no test: an empty phase leaves a margin that is not cold not cold
(`margin_empty`), so a failure there shows up at the end of the empty run.
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ M : ℕ}

/-- An empty phase leaves a nonnegative margin nonnegative. -/
theorem margin_empty {w : CStr} {ℓ a b : ℕ} {st : ℤ × ℤ} (hm : st.2 ≤ st.1) (h0 : 0 ≤ st.2)
    (hA : advCnt w a b = 0) (hH : honCnt w a b = 0) : 0 ≤ (step Δ w ℓ a b st).2 := by
  classical
  have hD0 : hD Δ w a b = 0 := by
    have := hD_le_honCnt (Δ := Δ) (w := w) (a := a) b; omega
  have hx : ¬ Cross w ℓ a b := fun hx => by
    have := honIn_of_cross hx; rw [honIn_iff_honCnt] at this; omega
  rw [step_cases ℓ a b st hm, hA, hD0]
  simp only [Nat.cast_zero, neg_zero, add_zero, sub_zero]
  rw [if_neg (by omega), if_neg hx]
  exact le_trans h0 (le_trans hm (le_max_left _ _))

/-- The bound process restarted at an anchor bounds the margin. -/
theorem bnd_le_rf {w : CStr} {ℓ k0 k : ℕ} (hk : k0 ≤ k) (hℓ : ℓ ≤ gend Δ M w k0) :
    (bnd Δ w ℓ (gend Δ M w) k).2 ≤ (rf Δ M w k0 (k - k0)).2 := by
  have h := (bnd_from (Δ := Δ) (w := w) ℓ (gend Δ M w) k0 (k - k0)).2
  rw [Nat.add_sub_cancel' hk, reach_indep ℓ 0 (gend Δ M w) k0, run_ell ℓ (gend Δ M w) gend_mono k0 hℓ] at h
  unfold rf rho0
  exact h

/-- **The cold condition from spans and checks.** -/
theorem cold_of_checks {w : CStr} {N G' J Lw : ℕ} (hNM : N + G' < M)
    (hocc : ∀ y ≤ N, ∃ i, y < i ∧ i ≤ y + G' ∧ (1 ≤ (w i).1 ∨ (w i).2 = true))
    (hspan : ∀ k, gend Δ M w k ≤ N + G' → gend Δ M w (k + 1) - gend Δ M w (k - J) ≤ Lw)
    (hfail : ∀ k ≤ N + G', J ≤ k → failC Δ M (N + G') (k - J) k w = 0)
    {t k : ℕ} (h1 : Lw < t) (h2 : t ≤ N) (h3 : gend Δ M w k + 1 ≤ t) (h4 : t ≤ gend Δ M w (k + 1)) :
    (bnd Δ w (t - Lw) (gend Δ M w) k).2 < -(advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) : ℤ) := by
  classical
  have hekN : gend Δ M w k ≤ N := by omega
  -- an occupied slot soon after the check, and its phase
  obtain ⟨i, hi1, hi2, hi3⟩ := hocc (gend Δ M w k) hekN
  have hpos : 0 < pidx Δ M w i := by
    by_contra h0; push Not at h0
    have := le_gend_pidx (Δ := Δ) (M := M) (w := w) i
    rw [show pidx Δ M w i = 0 by omega, gend_zero] at this; omega
  set p := pidx Δ M w i - 1 with hp
  have hp1 : gend Δ M w p < i := gend_lt_of_lt_pidx (by omega)
  have hp2 : i ≤ gend Δ M w (p + 1) := by
    have := le_gend_pidx (Δ := Δ) (M := M) (w := w) i
    rwa [show p + 1 = pidx Δ M w i by omega]
  have hpk : k ≤ p := by
    by_contra hlt; push Not at hlt
    have := gend_strictMono.monotone (f := gend Δ M w) (show p + 1 ≤ k by omega); omega
  have hpNE : 1 ≤ advCnt w (gend Δ M w p) (gend Δ M w (p + 1)) ∨ 1 ≤ honCnt w (gend Δ M w p) (gend Δ M w (p + 1)) := by
    rcases hi3 with h | h
    · right; unfold honCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨hp1, hp2⟩, by omega⟩⟩
    · left; unfold advCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨hp1, hp2⟩, h⟩⟩
  -- the first nonempty phase from `k` on
  have hex : ∃ q, k ≤ q ∧ (1 ≤ advCnt w (gend Δ M w q) (gend Δ M w (q + 1)) ∨
      1 ≤ honCnt w (gend Δ M w q) (gend Δ M w (q + 1))) := ⟨p, hpk, hpNE⟩
  set k' := Nat.find hex with hk'
  have hk'spec := Nat.find_spec hex
  have hk'k : k ≤ k' := hk'spec.1
  have hk'p : k' ≤ p := Nat.find_min' hex ⟨hpk, hpNE⟩
  have hmin : ∀ q, k ≤ q → q < k' → advCnt w (gend Δ M w q) (gend Δ M w (q + 1)) = 0 ∧
      honCnt w (gend Δ M w q) (gend Δ M w (q + 1)) = 0 := by
    intro q hq1 hq2
    have := Nat.find_min hex hq2
    push Not at this
    have := this hq1
    omega
  have hk'H : gend Δ M w k' ≤ N + G' := by
    have := gend_strictMono.monotone (f := gend Δ M w) hk'p; omega
  have hk'le : k' ≤ N + G' := le_trans (le_gend k') hk'H
  -- the span at `k'` puts the anchor after `t - Lw`
  have hsp := hspan k' hk'H
  have hmono1 : gend Δ M w (k + 1) ≤ gend Δ M w (k' + 1) := gend_strictMono.monotone (by omega)
  have hJ : J ≤ k' := by
    by_contra hlt; push Not at hlt
    rw [show k' - J = 0 by omega, gend_zero] at hsp; omega
  set k0 := k' - J with hk0
  have hk0le : gend Δ M w k0 ≤ gend Δ M w (k' + 1) := gend_strictMono.monotone (by omega)
  have hℓ : t - Lw ≤ gend Δ M w k0 := by omega
  -- the check at `k'` passes
  have hf := hfail k' hk'le hJ
  unfold failC at hf
  have hpass : (rf Δ M w k0 (k' - k0)).2 < -(advCnt w (gend Δ M w k') (gend Δ M w (k' + 1)) : ℤ) := by
    by_contra hc; push Not at hc
    rw [if_pos ⟨hk'H, hc, hk'spec.2⟩] at hf; norm_num at hf
  have hbk' := bnd_le_rf (Δ := Δ) (M := M) (w := w) (ℓ := t - Lw) (show k0 ≤ k' by omega) hℓ
  rcases Nat.eq_or_lt_of_le hk'k with heq | hlt
  · rw [heq]; exact lt_of_le_of_lt hbk' hpass
  · -- empty phases from `k` to `k'`: the margin was already negative at `k`
    have hA0 : advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) = 0 := (hmin k le_rfl hlt).1
    rw [hA0, Nat.cast_zero, neg_zero]
    by_contra hnn; push Not at hnn
    have hprop : ∀ q, k ≤ q → q ≤ k' → 0 ≤ (bnd Δ w (t - Lw) (gend Δ M w) q).2 := by
      intro q hq1 hq2
      induction q with
      | zero => have : k = 0 := by omega
                subst this; exact hnn
      | succ q ih =>
        rcases Nat.eq_or_lt_of_le hq1 with h | h
        · rw [← h]; exact hnn
        · have ih' := ih (by omega) (by omega)
          obtain ⟨ha, hh⟩ := hmin q (by omega) (by omega)
          simp only [bnd]
          exact margin_empty (bnd_le _ _ q) ih' ha hh
    have := hprop k' hk'k le_rfl
    have hA1 : (0 : ℤ) ≤ advCnt w (gend Δ M w k') (gend Δ M w (k' + 1)) := by positivity
    omega

end Cryptarchia.Prob
