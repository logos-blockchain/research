import Cryptarchia.Prob.Cold

/-!
# The reach bound stays small

`reach_tail`: at any fixed phase index `j0`, `E[c^ρ] ≤ 1 + b / (1 - λr)`, where `ρ`
is the reach bound there (`c^ρ` is the reach-only part of the cold potential).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
/-- `c^ρ` at phase `j0`, once the history has reached it. -/
noncomputable def reachH (c : ℝ) (j0 : ℕ) (h : List Out) : ℝ :=
  if j0 ≤ pidx Δ M (strOf h) h.length then c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1 else 0

variable (Δ M) in
/-- The potential. -/
noncomputable def Φr (P : ColdCert B Δ) (j0 : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < j0 then
    P.lr ^ (j0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (j0 - pidx Δ M (strOf h) h.length), P.lr ^ i
  else P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1

theorem phiR_step (hB : κ.Within B) (P : ColdCert B Δ) (j0 : ℕ) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr Δ M P j0) h ≤ Φr Δ M P j0 h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have reach : ∀ (o : Out) (t : List Out), t.length ≤ M - h.length - 1 →
      (∀ k < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k)) →
      (PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) → FirstPE Δ M h (h ++ [o] ++ t) :=
    fun o t ht hk hend => firstPE_of_reached hlM o t ht hk hend
  by_cases hjk : j < j0
  · obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, j0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr Δ M P j0) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * Wt P.c 1 P.c⁻¹ h.length h' else Wt P.c 1 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) h := by
      apply ExPh_mono_on
      intro o t ht hk hend
      have hf := reach o t ht hk hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
      have hcr : P.c ^ ρ' ≤
          (if 1 ≤ ρ then P.c ^ ρ * Wt P.c 1 P.c⁻¹ h.length h' else Wt P.c 1 1 h.length h') := by
        have := c_pow_reach (Δ := Δ) (w := strOf h') (ℓ := 0) (a := h.length) (b := h'.length) P.hc
          (st := bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j) (by rw [hρ]; exact hρ0) (bnd_le 0 _ j)
        rw [← hρ', hbs]
        rw [hρ] at this
        by_cases h1 : 1 ≤ ρ
        · rw [if_pos h1] at this
          rw [if_pos h1, wt_one]
          refine this.trans (le_of_eq ?_)
          split_ifs with hb
          · rw [zpow_sub₀ hc0.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
          · simp
        · rw [if_neg h1] at this
          rw [if_neg h1, wt_one]
          refine this.trans (le_of_eq ?_)
          rw [zpow_natCast]; simp
      have hval : Φr Δ M P j0 h' ≤ P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i := by
        unfold Φr
        rw [hp']
        by_cases hjk' : j + 1 < j0
        · rw [if_pos hjk', show j0 - (j + 1) = n - 1 by omega, hρ']
        · rw [if_neg hjk', show j0 = j + 1 by omega, show n - 1 = 0 by omega, hρ']
          simp
      refine hval.trans ?_
      have := mul_le_mul_of_nonneg_left hcr (pow_nonneg P.hlr0 (n - 1))
      linarith
    refine hle.trans ?_
    have hS : ∑ i ∈ Finset.range n, P.lr ^ i = ∑ i ∈ Finset.range (n - 1), P.lr ^ i + P.lr ^ (n - 1) := by
      rw [show n = (n - 1) + 1 by omega, Finset.sum_range_succ, Nat.add_sub_cancel]
    have hval : Φr Δ M P j0 h = P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i := by
      unfold Φr; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have := ex_wt (κ := κ) (y := P.c⁻¹) hB P.hΔ P.hc zero_le_one (inv_nonneg.mpr hc0.le) P.s4 hpe hlM
      have h2 := this.trans P.hlr
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
      nlinarith [mul_nonneg hbl hlrn]
    · have := ex_wt (κ := κ) (y := 1) hB P.hΔ P.hc zero_le_one zero_le_one P.s4 hpe hlM
      have h2 := this.trans P.hb
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr Δ M P j0) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => Φr Δ M P j0 h) h := by
      apply ExPh_mono_on
      intro o t ht hk hend
      have hf := reach o t ht hk hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      have hb := next_bnd hpe hlM hf (i := j0) (by rw [hj]; exact hjk)
      rw [hj] at hp'
      unfold Φr
      rw [hp', hj, if_neg (by omega), if_neg (by omega), hb]
    exact hle.trans (le_of_eq (ExPh_const _ _ _ _))

theorem reachH_le_phi (P : ColdCert B Δ) (j0 : ℕ) (h : List Out) : reachH Δ M P.c j0 h ≤ Φr Δ M P j0 h := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  unfold reachH Φr
  by_cases h1 : j0 ≤ pidx Δ M (strOf h) h.length
  · rw [if_pos h1, if_neg (by omega)]
  · rw [if_neg h1, if_pos (by omega)]
    apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)

/-- **The reach bound at any phase has a uniform exponential moment.** -/
theorem reach_tail (hB : κ.Within B) (P : ColdCert B Δ) (hM : 0 < M) (j0 : ℕ) :
    Ex κ M (reachH Δ M P.c j0) [] ≤ 1 + (P.b - 1) / (1 - P.lr) := by
  calc Ex κ M (reachH Δ M P.c j0) [] ≤ Ex κ M (Φr Δ M P j0) [] := Ex_mono M (reachH_le_phi P j0) []
    _ ≤ Φr Δ M P j0 [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Φr Δ M P j0) (M := M)
          (fun h hpe hlM => phiR_step hB P j0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ 1 + (P.b - 1) / (1 - P.lr) := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        unfold Φr
        rw [hp0]
        have hgeo := geom_le P.hlr0 P.hlr1 j0
        have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
        split_ifs with h1
        · rw [hb0, zpow_zero, mul_one, Nat.sub_zero]
          exact geom_mix P.hlr0 P.hlr1 P.hb1 j0
        · have hj : j0 = 0 := by omega
          subst hj
          rw [hb0, zpow_zero]
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
          linarith

end Cryptarchia.Prob
