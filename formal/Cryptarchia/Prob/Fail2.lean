import Cryptarchia.Prob.Cold2

/-!
# One check, anchored `J` phases back

Fix a check at phase `k` and anchor the bound process `J` phases before it, at
`k0 = k - J`. The check **fails** if the next phase is not empty and the margin is
not cold for it (`failC`). `fail_check`: the probability of a failed check is at most

  `λp^J · m_z · (1 + (b - 1) / (1 - λr))`,

with `m_z = e 2` the bound on `E[z^A ; the phase is not empty]`. The potential
(`Φf`) tracks `c^ρ` (the reach bound) before the anchor and `λp^(J - j) V2` from the
anchor to the check.
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
open Classical in
/-- A failed check at phase `k`, anchored at `k0`, within the horizon `Hc`. -/
noncomputable def failC (Hc k0 k : ℕ) (w : CStr) : ℝ :=
  if gend Δ M w k ≤ Hc ∧ -(advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) : ℤ) ≤ (rf Δ M w k0 (k - k0)).2 ∧
    (1 ≤ advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) ∨ 1 ≤ honCnt w (gend Δ M w k) (gend Δ M w (k + 1)))
  then 1 else 0

variable (Δ M) in
/-- The failed check, once the history has completed phase `k + 1`. -/
noncomputable def failH (Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if k < pidx Δ M (strOf h) h.length then failC Δ M Hc k0 k (strOf h) else 0

variable (Δ M) in
/-- **The potential.** -/
noncomputable def Φf (P : Cert2 B Δ) (Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then
    P.lp ^ (k - k0) * P.e 2 * (P.lr ^ (k0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (k0 - pidx Δ M (strOf h) h.length), P.lr ^ i)
  else if pidx Δ M (strOf h) h.length ≤ k then
    (if h.length ≤ Hc then P.lp ^ (k - pidx Δ M (strOf h) h.length) * P.e 2 *
      V2 P.c P.z P.s P.κ P.d (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) else 0)
  else failH Δ M Hc k0 k h

theorem failC_nonneg (Hc k0 k : ℕ) (w : CStr) : 0 ≤ failC Δ M Hc k0 k w := by
  unfold failC; split_ifs <;> norm_num

theorem e_nonneg (P : Cert2 B Δ) (hB : κ.Fam P.Bs) (hM : 0 < M) (i : Fin 19) (hi : i ≠ 17) : 0 ≤ P.e i := by
  have := ex_WP (κ := κ) (M := M) P hB i (pe_nil hM) (by simpa using hM)
  refine le_trans ?_ this
  exact ExPh_nonneg _ _ (fun y => WP_nonneg P i 0 y hi) _

section NextF

variable {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h')
include hpe hlM hf

theorem next_failC_old {Hc k0 k : ℕ} (hk : k < pidx Δ M (strOf h) h.length) (hk0 : k0 ≤ k) :
    failC Δ M Hc k0 k (strOf h') = failC Δ M Hc k0 k (strOf h) := by
  unfold failC
  have hsim := next_sim hpe hlM hf
  rw [next_gend hpe hlM hf (by omega : k ≤ _), next_gend hpe hlM hf (by omega : k + 1 ≤ _),
    next_rf hpe hlM hf (k0 := k0) (n := k - k0) (by omega),
    advCnt_congr (hsim.mono (Nat.zero_le _) (gend_le_len hpe hlM hf (by omega))),
    honCnt_congr (hsim.mono (Nat.zero_le _) (gend_le_len hpe hlM hf (by omega)))]

theorem next_failC_new {Hc k0 : ℕ} (hk0 : k0 ≤ pidx Δ M (strOf h) h.length) :
    failC Δ M Hc k0 (pidx Δ M (strOf h) h.length) (strOf h') =
      (by classical exact if h.length ≤ Hc ∧ -(advCnt (strOf h') h.length h'.length : ℤ) ≤
          (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)).2 ∧
          (1 ≤ advCnt (strOf h') h.length h'.length ∨ 1 ≤ honCnt (strOf h') h.length h'.length) then 1 else 0) := by
  unfold failC
  rw [next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe, next_gend_last hpe hlM hf,
    next_rf hpe hlM hf (k0 := k0) (n := _ - k0) (by omega)]

end NextF

theorem WP_val' (P : Cert2 B Δ) (i : Fin 19) (hi : i ≠ 17) (m : ℕ) (h : List Out) {A nh : ℕ}
    (hA : advCnt (strOf h) m h.length = A) (hn : honCnt (strOf h) m h.length = nh) :
    WP P i m h = (xg P.c P.z P.s P.d P.τ i).1 ^ A *
      (xg P.c P.z P.s P.d P.τ i).2.2 (acap A) (decide (1 ≤ nh)) (decide (2 ≤ nh)) := by
  rw [WP_val P i m h hi, hA, hn]

/-- **The potential is a supermartingale over phases.** -/
theorem phiF_step (P : Cert2 B Δ) (hB : κ.Fam P.Bs) {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ}
    (hk0 : k0 ≤ k) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 k) h ≤ Φf Δ M P Hc k0 k h := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have he2 : 0 ≤ P.e 2 := e_nonneg P hB hM 2 (by decide)
  have hlp := P.hlp0
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have reach : ∀ (o : Out) (t : List Out), t.length ≤ M - h.length - 1 →
      (∀ k' < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k')) →
      (PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) → FirstPE Δ M h (h ++ [o] ++ t) :=
    fun o t ht hk hend => firstPE_of_reached hlM o t ht hk hend
  have hF : 0 ≤ P.lp ^ (k - k0) * P.e 2 := by positivity
  by_cases hjk : j < k0
  · -- before the anchor
    obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, k0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 k) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.lp ^ (k - k0) * P.e 2 * (P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i)) h := by
      apply ExPh_mono_on
      intro o t ht hk hend
      have hf := reach o t ht hk hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
      have hρ'0 : 0 ≤ ρ' := by rw [← hρ']; exact bnd_fst_nonneg _
      have hcr : P.c ^ ρ' ≤ (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') := by
        have := c_pow_reach (Δ := Δ) (w := strOf h') (ℓ := 0) (a := h.length) (b := h'.length) P.hc
          (st := bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j) (by rw [hρ]; exact hρ0) (bnd_le 0 _ j)
        rw [← hρ', hbs]
        rw [hρ] at this
        obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h') h.length h'.length = A := ⟨_, rfl⟩
        obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h') h.length h'.length = nh := ⟨_, rfl⟩
        have hiff : HonIn (strOf h') h.length h'.length ↔ 1 ≤ nh := by rw [← hnh]; exact honIn_iff_honCnt
        rw [hA] at this
        by_cases h1 : 1 ≤ ρ
        · rw [if_pos h1] at this
          rw [if_pos h1, WP_val' P 0 (by decide) h.length h' hA hnh, xg_0]
          refine this.trans (le_of_eq ?_)
          simp only [xgN, gtab]
          by_cases hb : HonIn (strOf h') h.length h'.length
          · rw [if_pos hb, zpow_sub₀ hc0.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
            simp [hiff.1 hb]
          · rw [if_neg hb]; simp [show ¬ 1 ≤ nh from fun h'' => hb (hiff.2 h'')]
        · rw [if_neg h1] at this
          rw [if_neg h1, WP_val' P 1 (by decide) h.length h' hA hnh, xg_1]
          refine this.trans (le_of_eq ?_)
          simp [xgN]
      have hval : Φf Δ M P Hc k0 k h' ≤ P.lp ^ (k - k0) * P.e 2 *
          (P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) := by
        unfold Φf
        rw [hp']
        by_cases hjk' : j + 1 < k0
        · rw [if_pos hjk', show k0 - (j + 1) = n - 1 by omega, hρ']
        · rw [if_neg hjk', if_pos (by omega), show n - 1 = 0 by omega]
          simp only [pow_zero, one_mul, Finset.range_zero, Finset.sum_empty, mul_zero, add_zero]
          have hk0' : k0 = j + 1 := by omega
          split_ifs
          · rw [show k - (j + 1) = k - k0 by omega, show j + 1 - k0 = 0 by omega]
            apply mul_le_mul_of_nonneg_left _ hF
            unfold rf rho0
            simp only [runFrom]
            rw [hk0', hρ', V2_warm (show (0 : ℤ) ≤ (ρ', ρ').2 from hρ'0)]
          · exact mul_nonneg hF (zpow_nonneg hc0.le _)
      refine hval.trans ?_
      apply mul_le_mul_of_nonneg_left _ hF
      have := mul_le_mul_of_nonneg_left hcr (pow_nonneg P.hlr0 (n - 1))
      linarith
    refine hle.trans ?_
    have hS : ∑ i ∈ Finset.range n, P.lr ^ i = ∑ i ∈ Finset.range (n - 1), P.lr ^ i + P.lr ^ (n - 1) := by
      rw [show n = (n - 1) + 1 by omega, Finset.sum_range_succ, Nat.add_sub_cancel]
    have hval : Φf Δ M P Hc k0 k h = P.lp ^ (k - k0) * P.e 2 *
        (P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i) := by
      unfold Φf; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_mul_const]
    apply mul_le_mul_of_nonneg_left _ hF
    rw [ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have h2 := (ex_WP (κ := κ) P hB 0 hpe hlM).trans P.hlr
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      nlinarith [mul_nonneg hbl hlrn]
    · have h2 := (ex_WP (κ := κ) P hB 1 hpe hlM).trans P.hb
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    by_cases hjk2 : j ≤ k
    · by_cases hHl : h.length ≤ Hc
      · obtain ⟨st, hst⟩ : ∃ st, rf Δ M (strOf h) k0 (j - k0) = st := ⟨_, rfl⟩
        have hinv : Inv st := by rw [← hst]; exact rf_inv _ k0 _
        have hval : Φf Δ M P Hc k0 k h = P.lp ^ (k - j) * P.e 2 * V2 P.c P.z P.s P.κ P.d st := by
          unfold Φf; rw [hj, if_neg (by omega), if_pos hjk2, if_pos hHl, hst]
        have hVs : 0 ≤ V2 P.c P.z P.s P.κ P.d st :=
          (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 st).le
        by_cases hjeq : j = k
        · -- the check
          subst hjeq
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 j) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => V2 P.c P.z P.s P.κ P.d st * WP P 2 h.length h') h := by
            apply ExPh_mono_on
            intro o t ht hk hend
            have hf := reach o t ht hk hend
            generalize hh' : h ++ [o] ++ t = h' at hf ⊢
            have hp' := next_pidx hpe hlM hf
            rw [hj] at hp'
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj, hst] at hfn
            unfold Φf failH
            rw [hp', if_neg (by omega), if_neg (by omega), if_pos (by omega), hfn]
            obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h') h.length h'.length = A := ⟨_, rfl⟩
            obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h') h.length h'.length = nh := ⟨_, rfl⟩
            rw [hA, hnh, WP_val' P 2 (by decide) h.length h' hA hnh, xg_2]
            simp only [xgN]
            have hg : 0 ≤ gtab (fun b _ => if b then (1 : ℝ) else 0) (fun _ _ => 1) (fun _ _ => 1) (acap A)
                (decide (1 ≤ nh)) (decide (2 ≤ nh)) := by
              unfold gtab; split_ifs <;> simp only [decide_eq_true_eq] <;> (try split_ifs) <;> norm_num
            by_cases hcond : h.length ≤ Hc ∧ -(A : ℤ) ≤ st.2 ∧ (1 ≤ A ∨ 1 ≤ nh)
            · rw [if_pos hcond]
              have hg1 : gtab (fun b _ => if b then (1 : ℝ) else 0) (fun _ _ => 1) (fun _ _ => 1) (acap A)
                  (decide (1 ≤ nh)) (decide (2 ≤ nh)) = 1 := by
                unfold gtab
                rcases hcond.2.2 with h1 | h1
                · have := acap_pos h1; simp only [this, ↓reduceIte]; split_ifs <;> rfl
                · by_cases ha0 : (acap A).val = 0
                  · simp [ha0, h1]
                  · simp only [ha0, ↓reduceIte]; split_ifs <;> rfl
              rw [hg1, mul_one]
              have hfl := fail_le2 P.hc P.hz P.hs P.hκ P.hd0 hinv A
              rw [if_pos hcond.2.1, zpow_natCast] at hfl
              exact hfl
            · rw [if_neg hcond]
              exact mul_nonneg hVs (mul_nonneg (pow_nonneg hz0.le _) hg)
          refine hle.trans ?_
          rw [ExPh_mul_const, hval, Nat.sub_self, pow_zero, one_mul]
          have := mul_le_mul_of_nonneg_left (ex_WP (κ := κ) P hB 2 hpe hlM) hVs
          linarith
        · -- between the anchor and the check
          have hjk3 : j < k := by omega
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 k) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
                (fun h' => P.lp ^ (k - (j + 1)) * P.e 2 * postB2 P st h.length h') h := by
            apply ExPh_mono_on
            intro o t ht hk hend
            have hf := reach o t ht hk hend
            generalize hh' : h ++ [o] ++ t = h' at hf ⊢
            have hp' := next_pidx hpe hlM hf
            have hrs := next_rf_succ hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj] at hp' hrs
            rw [hst] at hrs
            have hpost := post2_le (Δ := Δ) P hinv h.length h' hf.lt.le
            have hpb : 0 ≤ postB2 P st h.length h' := le_trans (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le hpost
            unfold Φf
            rw [hp', if_neg (by omega), if_pos (by omega)]
            split_ifs
            · rw [hrs]; exact mul_le_mul_of_nonneg_left hpost (by positivity)
            · positivity
          refine hle.trans ?_
          rw [ExPh_mul_const, hval]
          have := ex_post2 (κ := κ) P hB hinv hpe (by omega : h.length + Δ + 1 ≤ M)
          have hpow : P.lp ^ (k - j) = P.lp ^ (k - (j + 1)) * P.lp := by
            rw [← pow_succ, show k - (j + 1) + 1 = k - j by omega]
          rw [hpow]
          have := mul_le_mul_of_nonneg_left this (by positivity : (0 : ℝ) ≤ P.lp ^ (k - (j + 1)) * P.e 2)
          linarith
      · -- past the horizon: nothing more
        have hval : Φf Δ M P Hc k0 k h = 0 := by
          unfold Φf; rw [hj, if_neg (by omega), if_pos hjk2, if_neg hHl]
        rw [hval]
        have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 k) h ≤
            ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => 0) h := by
          apply ExPh_mono_on
          intro o t ht hk hend
          have hf := reach o t ht hk hend
          generalize hh' : h ++ [o] ++ t = h' at hf ⊢
          have hp' := next_pidx hpe hlM hf
          rw [hj] at hp'
          unfold Φf
          rw [hp', if_neg (by omega)]
          by_cases hj' : j + 1 ≤ k
          · rw [if_pos hj', if_neg (by have := hf.lt; omega)]
          · rw [if_neg hj']
            unfold failH
            rw [hp', if_pos (by omega)]
            have hjeq : j = k := by omega
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj] at hfn
            rw [← hjeq, hfn, if_neg (fun hc => hHl hc.1)]
        exact hle.trans (le_of_eq (ExPh_const _ _ _ _))
    · -- after the check: the failure is fixed
      push Not at hjk2
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φf Δ M P Hc k0 k) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => Φf Δ M P Hc k0 k h) h := by
        apply ExPh_mono_on
        intro o t ht hk hend
        have hf := reach o t ht hk hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have e1 : Φf Δ M P Hc k0 k h' = failC Δ M Hc k0 k (strOf h') := by
          unfold Φf failH; rw [hp', if_neg (by omega), if_neg (by omega), if_pos (by omega)]
        have e2 : Φf Δ M P Hc k0 k h = failC Δ M Hc k0 k (strOf h) := by
          unfold Φf failH; rw [hj, if_neg (by omega), if_neg (by omega), if_pos (by omega)]
        rw [e1, e2, next_failC_old hpe hlM hf (by rw [hj]; exact hjk2) (by omega)]
      exact hle.trans (le_of_eq (ExPh_const _ _ _ _))

theorem failH_le_phi (P : Cert2 B Δ) (hB : κ.Fam P.Bs) (hM : 0 < M) {Hc k0 k : ℕ} (hk0 : k0 ≤ k) (h : List Out) :
    failH Δ M Hc k0 k h ≤ Φf Δ M P Hc k0 k h := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have he2 : 0 ≤ P.e 2 := e_nonneg P hB hM 2 (by decide)
  have hlp := P.hlp0
  unfold Φf failH
  by_cases h1 : pidx Δ M (strOf h) h.length < k0
  · rw [if_pos h1, if_neg (by omega)]
    apply mul_nonneg (by positivity)
    apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · rw [if_neg h1]
    by_cases h2 : pidx Δ M (strOf h) h.length ≤ k
    · rw [if_pos h2, if_neg (by omega)]
      split_ifs
      · exact mul_nonneg (by positivity) (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le
      · exact le_rfl
    · rw [if_neg h2, if_pos (by omega)]

/-- **A failed check is rare.** -/
theorem fail_check (P : Cert2 B Δ) (hB : κ.Fam P.Bs) {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ}
    (hk0 : k0 ≤ k) :
    Ex κ M (failH Δ M Hc k0 k) [] ≤ P.lp ^ (k - k0) * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have he2 : 0 ≤ P.e 2 := e_nonneg P hB hM 2 (by decide)
  have hF : 0 ≤ P.lp ^ (k - k0) * P.e 2 := mul_nonneg (pow_nonneg P.hlp0 _) he2
  calc Ex κ M (failH Δ M Hc k0 k) [] ≤ Ex κ M (Φf Δ M P Hc k0 k) [] :=
        Ex_mono M (failH_le_phi P hB hM hk0) []
    _ ≤ Φf Δ M P Hc k0 k [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Φf Δ M P Hc k0 k) (M := M)
          (fun h hpe hlM => phiF_step P hB hHc hk0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
        unfold Φf
        rw [hp0]
        by_cases hk : 0 < k0
        · rw [if_pos hk, hb0, zpow_zero, mul_one, Nat.sub_zero]
          exact mul_le_mul_of_nonneg_left (geom_mix P.hlr0 P.hlr1 P.hb1 k0) hF
        · have : k0 = 0 := by omega
          subst this
          rw [if_neg (by omega), if_pos (Nat.zero_le _), if_pos (by simp)]
          unfold rf rho0
          simp only [runFrom, Nat.sub_zero, Nat.sub_self]
          rw [hb0, V2_warm (show (0 : ℤ) ≤ ((0 : ℤ), (0 : ℤ)).2 from le_rfl), zpow_zero, mul_one]
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
          calc P.lp ^ (k - 0) * P.e 2 = P.lp ^ (k - 0) * P.e 2 * 1 := by ring
            _ ≤ _ := mul_le_mul_of_nonneg_left (by linarith) hF

/-! ## Spans of phases -/

variable (Δ M) in
/-- `τ` to the slots spanned by phases `k0 .. k1`, once they are complete. -/
noncomputable def spanH (τ : ℝ) (k0 k1 : ℕ) (h : List Out) : ℝ :=
  if k1 ≤ pidx Δ M (strOf h) h.length then
    τ ^ (gend Δ M (strOf h) k1 - gend Δ M (strOf h) k0) else 0

variable (Δ M) in
/-- The potential for spans. -/
noncomputable def Ψs (P : Cert2 B Δ) (k0 k1 : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then P.e 17 ^ (k1 - k0)
  else if pidx Δ M (strOf h) h.length ≤ k1 then
    P.e 17 ^ (k1 - pidx Δ M (strOf h) h.length) * P.τ ^ (h.length - gend Δ M (strOf h) k0)
  else P.τ ^ (gend Δ M (strOf h) k1 - gend Δ M (strOf h) k0)

theorem WP17 (P : Cert2 B Δ) (m : ℕ) (h : List Out) : WP P 17 m h = P.τ ^ (h.length - m) := by
  unfold WP Wt2; rw [xg_17]; simp [xgN]

theorem psiS_step (P : Cert2 B Δ)
    (h17 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 17 h.length) h ≤ P.e 17)
    {k0 k1 : ℕ} (hk : k0 ≤ k1) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Ψs Δ M P k0 k1) h ≤ Ψs Δ M P k0 k1 h := by
  classical
  have hτ0 : 0 ≤ P.τ := by linarith [P.hτ]
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have hej : gend Δ M (strOf h) j = h.length := by rw [← hj]; exact gend_pidx_pe hpe
  have reach : ∀ (o : Out) (t : List Out), t.length ≤ M - h.length - 1 →
      (∀ k' < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k')) →
      (PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) → FirstPE Δ M h (h ++ [o] ++ t) :=
    fun o t ht hk hend => firstPE_of_reached hlM o t ht hk hend
  have he17 : 0 ≤ P.e 17 := by
    have := h17 h hpe hlM
    refine le_trans (ExPh_nonneg _ _ (fun y => ?_) _) this
    rw [WP17]; positivity
  by_cases h1 : j < k0
  · -- constant until the anchor
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Ψs Δ M P k0 k1) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => P.e 17 ^ (k1 - k0)) h := by
      apply ExPh_mono_on
      intro o t ht hk' hend
      have hf := reach o t ht hk' hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      rw [hj] at hp'
      unfold Ψs
      rw [hp']
      by_cases h2 : j + 1 < k0
      · rw [if_pos h2]
      · have hk0 : k0 = j + 1 := by omega
        have hl := next_gend_last hpe hlM hf
        rw [hj] at hl
        rw [if_neg h2, if_pos (by omega), hk0, hl, Nat.sub_self, pow_zero, mul_one]
    refine hle.trans (le_of_eq ?_)
    rw [ExPh_const]; unfold Ψs; rw [hj, if_pos h1]
  · push Not at h1
    by_cases h2 : j < k1
    · -- one more phase of the span
      have hk0j : gend Δ M (strOf h) k0 ≤ h.length := by rw [← hej]; exact gend_strictMono.monotone h1
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Ψs Δ M P k0 k1) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.e 17 ^ (k1 - (j + 1)) *
            P.τ ^ (h.length - gend Δ M (strOf h) k0) * WP P 17 h.length h') h := by
        apply ExPh_mono_on
        intro o t ht hk' hend
        have hf := reach o t ht hk' hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have hg0 := next_gend hpe hlM hf (i := k0) (by rw [hj]; exact h1)
        unfold Ψs
        rw [hp', if_neg (by omega), if_pos (by omega), hg0, WP17, mul_assoc, ← pow_add]
        apply le_of_eq; congr 2; have := hf.lt; omega
      refine hle.trans ?_
      rw [ExPh_mul_const]
      have := mul_le_mul_of_nonneg_left (h17 h hpe hlM)
        (by positivity : (0 : ℝ) ≤ P.e 17 ^ (k1 - (j + 1)) * P.τ ^ (h.length - gend Δ M (strOf h) k0))
      refine this.trans (le_of_eq ?_)
      unfold Ψs
      rw [hj, if_neg (by omega), if_pos (by omega), show k1 - j = (k1 - (j + 1)) + 1 by omega, pow_succ]
      ring
    · -- the span is complete
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Ψs Δ M P k0 k1) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => Ψs Δ M P k0 k1 h) h := by
        apply ExPh_mono_on
        intro o t ht hk' hend
        have hf := reach o t ht hk' hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have hg0 := next_gend hpe hlM hf (i := k0) (by rw [hj]; omega)
        have hg1 := next_gend hpe hlM hf (i := k1) (by rw [hj]; omega)
        unfold Ψs
        rw [hp', hj, if_neg (by omega), if_neg (by omega), if_neg (by omega), hg0, hg1]
        by_cases h3 : j ≤ k1
        · have hjk : j = k1 := by omega
          rw [if_pos h3, hjk, Nat.sub_self, pow_zero, one_mul, ← hjk, hej]
        · rw [if_neg h3]
      exact hle.trans (le_of_eq (ExPh_const _ _ _ _))

/-- **Long spans are rare.** -/
theorem span_bound' (P : Cert2 B Δ)
    (h17 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 17 h.length) h ≤ P.e 17)
    (hM : 0 < M) {k0 k1 : ℕ} (hk : k0 ≤ k1) :
    Ex κ M (spanH Δ M P.τ k0 k1) [] ≤ P.e 17 ^ (k1 - k0) := by
  have hτ0 : 0 ≤ P.τ := by linarith [P.hτ]
  have he17 : 0 ≤ P.e 17 := by
    have := h17 [] (pe_nil hM) (by simpa using hM)
    refine le_trans (ExPh_nonneg _ _ (fun y => ?_) _) this
    rw [WP17]; positivity
  calc Ex κ M (spanH Δ M P.τ k0 k1) [] ≤ Ex κ M (Ψs Δ M P k0 k1) [] := by
        apply Ex_mono_len
        intro h hlen
        simp only [List.nil_append]
        unfold spanH Ψs
        by_cases h1 : k1 ≤ pidx Δ M (strOf h) h.length
        · rw [if_pos h1]
          by_cases h2 : pidx Δ M (strOf h) h.length < k0
          · omega
          · rw [if_neg h2]
            by_cases h3 : pidx Δ M (strOf h) h.length ≤ k1
            · have hjk : pidx Δ M (strOf h) h.length = k1 := by omega
              rw [if_pos h3, hjk, Nat.sub_self, pow_zero, one_mul]
              have hg : gend Δ M (strOf h) (pidx Δ M (strOf h) h.length) = h.length := by
                rw [hlen]; exact gend_pidx_of_end (Or.inr (Or.inl rfl))
              rw [hjk] at hg; rw [hg]
            · rw [if_neg h3]
        · rw [if_neg h1]
          split_ifs <;> positivity
    _ ≤ Ψs Δ M P k0 k1 [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Ψs Δ M P k0 k1) (M := M)
          (fun h hpe hlM => psiS_step P h17 hk hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := by
        unfold Ψs
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        rw [hp0]
        by_cases h0 : 0 < k0
        · rw [if_pos h0]
        · have : k0 = 0 := by omega
          subst this
          rw [if_neg (by omega), if_pos (Nat.zero_le _)]
          simp [gend_zero]

theorem span_bound (P : Cert2 B Δ) (hB : κ.Fam P.Bs) (hM : 0 < M) {k0 k1 : ℕ} (hk : k0 ≤ k1) :
    Ex κ M (spanH Δ M P.τ k0 k1) [] ≤ P.e 17 ^ (k1 - k0) :=
  span_bound' P (fun h hpe hlM => ex_WP (κ := κ) P hB 17 hpe hlM) hM hk

end Cryptarchia.Prob
