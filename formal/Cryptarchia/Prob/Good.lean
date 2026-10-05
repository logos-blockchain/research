import Cryptarchia.Proof.FinalE
import Cryptarchia.Prob.Reach
import Cryptarchia.Prob.Blocks
import Cryptarchia.Prob.Depth

/-!
# The good event from the absence of five bad events

On a full sampled history `h` (length `M`), with the greedy phase ends, the good
event `GoodLS` and the growth condition `GrowthS` of the settlement theorem hold
unless one of five bad events happens (`good_of`):

* **long phase**: some phase starting by `N` lasts more than `G` slots;
* **cold failure**: some anchored failure (`accH`);
* **crowded window**: more than `k` occupied slots in a window of `Lw` slots;
* **large reach**: the reach bound exceeds `r` at a phase end;
* **slow growth**: honest depth over an epoch's last phase is at most `k + r`.
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ M N W : ℕ}

/-- A phase that starts by `N` ends within `G` slots. -/
theorem phase_short {w : CStr} {G : ℕ} (hNG : N + G < M)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ w m) {j : ℕ} (hj : gend Δ M w j ≤ N) :
    gend Δ M w (j + 1) ≤ gend Δ M w j + G := by
  obtain ⟨m, h1, h2, h3⟩ := hq _ hj
  rw [gend_succ]
  exact le_trans (nextE_le_of_quiet h1 (by omega) h3) h2

/-- **The cold condition.** -/
theorem cold_of_noFail {w : CStr} {G Lw : ℕ} (hNG : N + G < M) (hW : W + 2 * G ≤ Lw) (hGL : G ≤ Lw)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ w m)
    (hfail : ∀ k0 k, k0 ≤ k → gend Δ M w k ≤ N → failK Δ M N W w k0 k = 0)
    {t k : ℕ} (h1 : Lw < t) (h2 : t ≤ N) (h3 : gend Δ M w k + 1 ≤ t) (h4 : t ≤ gend Δ M w (k + 1)) :
    (bnd Δ w (t - Lw) (gend Δ M w) k).2 < -(advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) : ℤ) := by
  classical
  have hekN : gend Δ M w k ≤ N := by omega
  have hshort := phase_short (Δ := Δ) hNG hq hekN
  obtain ⟨k0, hk0⟩ : ∃ k0, pidx Δ M w (t - Lw) = k0 := ⟨_, rfl⟩
  -- the anchor is at most `k`
  have hk0k : k0 ≤ k := by rw [← hk0]; exact pidx_le_of (by omega)
  have hle0 : t - Lw ≤ gend Δ M w k0 := by rw [← hk0]; exact le_gend_pidx _
  -- the anchor is at most `G` past `t - Lw`
  have hk0pos : 1 ≤ k0 := by
    by_contra h0
    have : k0 = 0 := by omega
    rw [this, gend_zero] at hle0
    omega
  have hprev : gend Δ M w (k0 - 1) < t - Lw := gend_lt_of_lt_pidx (by omega)
  have hshort0 := phase_short (Δ := Δ) hNG hq (j := k0 - 1) (by omega)
  rw [show k0 - 1 + 1 = k0 by omega] at hshort0
  -- not cold would be a failure
  by_contra hnc
  push Not at hnc
  have hrun : ¬ (runFrom (Δ := Δ) (w := w) 0 (gend Δ M w) k0
      ((bnd Δ w 0 (gend Δ M w) k0).1, (bnd Δ w 0 (gend Δ M w) k0).1) (k - k0)).2 <
      -(advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) : ℤ) := by
    intro hc
    have := cold_of_run (Δ := Δ) (w := w) (t - Lw) (gend Δ M w) gend_mono hk0k hle0 hc
    omega
  push Not at hrun
  have hf := hfail k0 k hk0k hekN
  unfold failK at hf
  rw [if_pos ⟨by omega, by omega, hrun⟩] at hf
  norm_num at hf

theorem gend_pidx_M {w : CStr} : gend Δ M w (pidx Δ M w M) = M :=
  gend_pidx_of_end (Or.inr (Or.inl rfl))

/-- **The good event and the growth condition, from the absence of the bad events.** -/
theorem good_of (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) {h : List Out} (hlen : h.length = M)
    {G Lw r : ℕ} (hNG : N + G < M) (hW : W + 2 * G ≤ Lw) (hGL : G ≤ Lw)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m)
    (hfail : ∀ k0 ≤ N, accH Δ M N W k0 h = 0)
    (hwin : ∀ t ≤ N, occCnt (strOf h) (t - Lw) t ≤ E.c.k)
    (hreach : ∀ j0, gend Δ M (strOf h) j0 ≤ N + G → (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1 ≤ r)
    (hdepth : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N →
      E.c.k + r < hD Δ (strOf h) (E.c.cut ep + G) (E.c.fix ep - Δ - 1)) :
    GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧ GrowthS E (strOf h) (gend Δ M (strOf h)) N r G := by
  set w := strOf h with hw
  have hfail' : ∀ k0 k, k0 ≤ k → gend Δ M w k ≤ N → failK Δ M N W w k0 k = 0 := by
    intro k0 k hk hkN
    have hk0N : k0 ≤ N := le_trans hk (le_trans (le_gend k) hkN)
    have hacc := hfail k0 hk0N
    unfold accH acc at hacc
    rw [hlen] at hacc
    have hkJ : k < pidx Δ M w M := by
      by_contra hc; push Not at hc
      have := gend_strictMono.monotone (f := gend Δ M w) hc
      rw [gend_pidx_M] at this; omega
    have hnn : ∀ i ∈ Finset.Ico k0 (pidx Δ M w M), 0 ≤ failK Δ M N W w k0 i := fun i _ => by
      unfold failK; split_ifs <;> norm_num
    exact (Finset.sum_eq_zero_iff_of_nonneg hnn).1 hacc k (Finset.mem_Ico.2 ⟨hk, hkJ⟩)
  refine ⟨⟨gend_zero, gend_mono, ?_, gend_unb, ?_, ?_⟩, ?_⟩
  · intro k hk; rw [hΔ]; exact gend_quiet k (by omega)
  · intro t k h1 h2 h3 h4
    rw [hΔ]
    exact cold_of_noFail hNG hW hGL hq hfail' h1 h2 h3 h4
  · exact hwin
  · intro ep hep hfix
    have hcf := (hsane.fix_ok ep hep).1
    obtain ⟨j, hj⟩ : ∃ j, pidx Δ M w (E.c.cut ep - 2) = j := ⟨_, rfl⟩
    have hge : E.c.cut ep - 2 ≤ gend Δ M w j := by rw [← hj]; exact le_gend_pidx _
    have hle : gend Δ M w j ≤ E.c.cut ep - 2 + G := by
      rcases Nat.eq_zero_or_pos j with h0 | hpos
      · rw [h0, gend_zero]; omega
      · have hprev : gend Δ M w (j - 1) < E.c.cut ep - 2 := gend_lt_of_lt_pidx (by omega)
        have := phase_short (Δ := Δ) hNG hq (j := j - 1) (by omega)
        rw [show j - 1 + 1 = j by omega] at this
        omega
    refine ⟨j, hge, by omega, ?_, ?_⟩
    · rw [hΔ]; exact hreach j (by omega)
    · rw [hΔ]; exact hdepth ep hep hfix

end Cryptarchia.Prob
