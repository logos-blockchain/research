import Cryptarchia.Prob.Cold2E
import Cryptarchia.Prob.Fail2

/-!
# One check, with one band member per epoch

As `Fail2.lean`, for kernels whose band changes only at epoch boundaries. Phase
expectations are bounded only for phases cut at `G` slots, so the potential `ΦfE`
counts a check only if every phase from the anchor on has at most `G` slots
(`noLong`); the long-phase term of the settlement bound pays for the rest. The
reach part before the anchor and the checked phase use bounds valid for any phase
(`hR0`, `hR1`, `hC2`); the contraction between anchor and check uses the truncated
bounds (`hE`, through `ex_post2G`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
/-- Every phase from `k0` to `j` has at most `G` slots. -/
def NoLong (G k0 j : ℕ) (w : CStr) : Prop := ∀ i, k0 ≤ i → i < j → gend Δ M w (i + 1) ≤ gend Δ M w i + G

variable (Δ M) in
open Classical in
/-- A failed check at phase `k`, anchored at `k0`, counted only without long phases. -/
noncomputable def failHE (G Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if NoLong Δ M G k0 k (strOf h) then failH Δ M Hc k0 k h else 0

variable (Δ M) in
open Classical in
/-- **The potential.** -/
noncomputable def ΦfE (P : Cert2 B Δ) (G Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then
    P.lp ^ (k - k0) * P.e 2 * (P.lr ^ (k0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (k0 - pidx Δ M (strOf h) h.length), P.lr ^ i)
  else if pidx Δ M (strOf h) h.length ≤ k then
    (if h.length ≤ Hc ∧ NoLong Δ M G k0 (pidx Δ M (strOf h) h.length) (strOf h) then
      P.lp ^ (k - pidx Δ M (strOf h) h.length) * P.e 2 *
      V2 P.c P.z P.s P.κ P.d (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) else 0)
  else failHE Δ M G Hc k0 k h

theorem noLong_self (G k0 : ℕ) (w : CStr) : NoLong Δ M G k0 k0 w := fun i h1 h2 => absurd h2 (by omega)

section NextL

variable {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h')
include hpe hlM hf

theorem noLong_stable {G k0 j : ℕ} (hj : j ≤ pidx Δ M (strOf h) h.length) :
    NoLong Δ M G k0 j (strOf h') ↔ NoLong Δ M G k0 j (strOf h) := by
  unfold NoLong
  constructor
  · intro H i h1 h2
    have := H i h1 h2
    rwa [next_gend hpe hlM hf (by omega : i + 1 ≤ _), next_gend hpe hlM hf (by omega : i ≤ _)] at this
  · intro H i h1 h2
    rw [next_gend hpe hlM hf (by omega : i + 1 ≤ _), next_gend hpe hlM hf (by omega : i ≤ _)]
    exact H i h1 h2

theorem noLong_next {G k0 : ℕ} (hk0 : k0 ≤ pidx Δ M (strOf h) h.length) :
    NoLong Δ M G k0 (pidx Δ M (strOf h) h.length + 1) (strOf h') ↔
      NoLong Δ M G k0 (pidx Δ M (strOf h) h.length) (strOf h) ∧ h'.length ≤ h.length + G := by
  constructor
  · intro H
    refine ⟨(noLong_stable hpe hlM hf le_rfl).1 fun i h1 h2 => H i h1 (by omega), ?_⟩
    have := H (pidx Δ M (strOf h) h.length) hk0 (by omega)
    rwa [next_gend_last hpe hlM hf, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe] at this
  · rintro ⟨H, hl⟩ i h1 h2
    rcases Nat.lt_or_ge i (pidx Δ M (strOf h) h.length) with hi | hi
    · exact (noLong_stable hpe hlM hf le_rfl).2 H i h1 hi
    · have hie : i = pidx Δ M (strOf h) h.length := by omega
      rw [hie, next_gend_last hpe hlM hf, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe]
      exact hl

end NextL

/-- **The potential is a supermartingale over phases.** -/
theorem phiFE_step (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hC2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ}
    (hk0 : k0 ≤ k) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 k) h ≤ ΦfE Δ M P G Hc k0 k h := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have he2 : 0 ≤ P.e 2 := le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _)
    (hC2 [] (pe_nil hM) (by simpa using hM))
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
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 k) h ≤
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
      have hval : ΦfE Δ M P G Hc k0 k h' ≤ P.lp ^ (k - k0) * P.e 2 *
          (P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) := by
        unfold ΦfE
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
    have hval : ΦfE Δ M P G Hc k0 k h = P.lp ^ (k - k0) * P.e 2 *
        (P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i) := by
      unfold ΦfE; rw [hj, if_pos hjk, hn, hρ]
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
      have h2 := hR0 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      nlinarith [mul_nonneg hbl hlrn]
    · have h2 := hR1 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    by_cases hjk2 : j ≤ k
    · by_cases hHl : h.length ≤ Hc ∧ NoLong Δ M G k0 j (strOf h)
      · obtain ⟨st, hst⟩ : ∃ st, rf Δ M (strOf h) k0 (j - k0) = st := ⟨_, rfl⟩
        have hinv : Inv st := by rw [← hst]; exact rf_inv _ k0 _
        have hval : ΦfE Δ M P G Hc k0 k h = P.lp ^ (k - j) * P.e 2 * V2 P.c P.z P.s P.κ P.d st := by
          unfold ΦfE; rw [hj, if_neg (by omega), if_pos hjk2, if_pos hHl, hst]
        have hVs : 0 ≤ V2 P.c P.z P.s P.κ P.d st :=
          (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 st).le
        by_cases hjeq : j = k
        · -- the check
          subst hjeq
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 j) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => V2 P.c P.z P.s P.κ P.d st * WP P 2 h.length h') h := by
            apply ExPh_mono_on
            intro o t ht hk hend
            have hf := reach o t ht hk hend
            generalize hh' : h ++ [o] ++ t = h' at hf ⊢
            have hp' := next_pidx hpe hlM hf
            rw [hj] at hp'
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj, hst] at hfn
            have hnl' : NoLong Δ M G k0 j (strOf h') :=
              (noLong_stable hpe hlM hf (by rw [hj])).2 hHl.2
            unfold ΦfE failHE failH
            rw [hp', if_neg (by omega), if_neg (by omega), if_pos hnl', if_pos (by omega), hfn]
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
          have := mul_le_mul_of_nonneg_left (hC2 h hpe hlM) hVs
          linarith
        · -- between the anchor and the check
          have hjk3 : j < k := by omega
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 k) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
                (fun h' => P.lp ^ (k - (j + 1)) * P.e 2 * truncG h.length G (postB2 P st h.length) h') h := by
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
            have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
            rw [hj] at hnn
            unfold ΦfE
            rw [hp', if_neg (by omega), if_pos (by omega)]
            split_ifs with hc
            · have hl : h'.length ≤ h.length + G := (hnn.1 hc.2).2
              rw [hrs]
              unfold truncG; rw [if_pos hl]
              exact mul_le_mul_of_nonneg_left hpost (by positivity)
            · refine mul_nonneg (by positivity) ?_
              unfold truncG; split_ifs
              · exact hpb
              · exact le_rfl
          refine hle.trans ?_
          rw [ExPh_mul_const, hval]
          have := ex_post2G (κ := κ) P hW hG hE hinv hpe (by omega : h.length + Δ + 1 ≤ M)
          have hpow : P.lp ^ (k - j) = P.lp ^ (k - (j + 1)) * P.lp := by
            rw [← pow_succ, show k - (j + 1) + 1 = k - j by omega]
          rw [hpow]
          have := mul_le_mul_of_nonneg_left this (by positivity : (0 : ℝ) ≤ P.lp ^ (k - (j + 1)) * P.e 2)
          linarith
      · -- past the horizon: nothing more
        have hval : ΦfE Δ M P G Hc k0 k h = 0 := by
          unfold ΦfE; rw [hj, if_neg (by omega), if_pos hjk2, if_neg hHl]
        rw [hval]
        have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 k) h ≤
            ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => 0) h := by
          apply ExPh_mono_on
          intro o t ht hk hend
          have hf := reach o t ht hk hend
          generalize hh' : h ++ [o] ++ t = h' at hf ⊢
          have hp' := next_pidx hpe hlM hf
          rw [hj] at hp'
          unfold ΦfE
          rw [hp', if_neg (by omega)]
          by_cases hj' : j + 1 ≤ k
          · rw [if_pos hj']
            have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
            rw [hj] at hnn
            rw [if_neg (fun hc => hHl ⟨by have := hf.lt; omega, (hnn.1 hc.2).1⟩)]
          · rw [if_neg hj']
            have hjeq : j = k := by omega
            unfold failHE
            by_cases hnl : NoLong Δ M G k0 k (strOf h')
            · rw [if_pos hnl]
              have hnl0 : NoLong Δ M G k0 j (strOf h) := by
                rw [hjeq]; exact (noLong_stable hpe hlM hf (by rw [hj]; omega)).1 hnl
              unfold failH
              rw [hp', if_pos (by omega)]
              have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
              rw [hj] at hfn
              rw [← hjeq, hfn, if_neg (fun hc => hHl ⟨hc.1, hnl0⟩)]
            · rw [if_neg hnl]
        exact hle.trans (le_of_eq (ExPh_const _ _ _ _))
    · -- after the check: the failure is fixed
      push Not at hjk2
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE Δ M P G Hc k0 k) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => ΦfE Δ M P G Hc k0 k h) h := by
        apply ExPh_mono_on
        intro o t ht hk hend
        have hf := reach o t ht hk hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have hst' := noLong_stable (G := G) (k0 := k0) (j := k) hpe hlM hf (by rw [hj]; omega)
        have e1 : ΦfE Δ M P G Hc k0 k h' =
            (if NoLong Δ M G k0 k (strOf h) then failC Δ M Hc k0 k (strOf h') else 0) := by
          unfold ΦfE failHE failH; rw [hp', if_neg (by omega), if_neg (by omega)]
          by_cases hn : NoLong Δ M G k0 k (strOf h)
          · rw [if_pos (hst'.2 hn), if_pos hn, if_pos (by omega)]
          · rw [if_neg (fun h'' => hn (hst'.1 h'')), if_neg hn]
        have e2 : ΦfE Δ M P G Hc k0 k h =
            (if NoLong Δ M G k0 k (strOf h) then failC Δ M Hc k0 k (strOf h) else 0) := by
          unfold ΦfE failHE failH; rw [hj, if_neg (by omega), if_neg (by omega)]
          by_cases hn : NoLong Δ M G k0 k (strOf h)
          · rw [if_pos hn, if_pos hn, if_pos (by omega)]
          · rw [if_neg hn, if_neg hn]
        rw [e1, e2, next_failC_old hpe hlM hf (by rw [hj]; exact hjk2) (by omega)]
      exact hle.trans (le_of_eq (ExPh_const _ _ _ _))


theorem failHE_le_phi (P : Cert2 B Δ) (he2 : 0 ≤ P.e 2) {G Hc k0 k : ℕ} (hk0 : k0 ≤ k) (h : List Out) :
    failHE Δ M G Hc k0 k h ≤ ΦfE Δ M P G Hc k0 k h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hlp := P.hlp0
  by_cases h1 : pidx Δ M (strOf h) h.length < k0
  · have hf : failHE Δ M G Hc k0 k h = 0 := by
      unfold failHE failH; split_ifs <;> first | rfl | omega
    rw [hf]; unfold ΦfE; rw [if_pos h1]
    apply mul_nonneg (by positivity)
    apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · by_cases h2 : pidx Δ M (strOf h) h.length ≤ k
    · have hf : failHE Δ M G Hc k0 k h = 0 := by
        unfold failHE failH; split_ifs <;> first | rfl | omega
      rw [hf]; unfold ΦfE; rw [if_neg h1, if_pos h2]
      split_ifs
      · exact mul_nonneg (by positivity) (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le
      · exact le_rfl
    · unfold ΦfE; rw [if_neg h1, if_neg h2]

/-- **A failed check is rare**, with one band member per epoch. -/
theorem fail_checkE (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hC2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ} (hk0 : k0 ≤ k) :
    Ex κ M (failHE Δ M G Hc k0 k) [] ≤ P.lp ^ (k - k0) * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have he2 : 0 ≤ P.e 2 := le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _)
    (hC2 [] (pe_nil hM) (by simpa using hM))
  have hF : 0 ≤ P.lp ^ (k - k0) * P.e 2 := mul_nonneg (pow_nonneg P.hlp0 _) he2
  calc Ex κ M (failHE Δ M G Hc k0 k) [] ≤ Ex κ M (ΦfE Δ M P G Hc k0 k) [] :=
        Ex_mono M (failHE_le_phi P he2 hk0) []
    _ ≤ ΦfE Δ M P G Hc k0 k [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := ΦfE Δ M P G Hc k0 k) (M := M)
          (fun h hpe hlM => phiFE_step P hW hG hR0 hR1 hC2 hE hHc hk0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
        unfold ΦfE
        rw [hp0]
        by_cases hk : 0 < k0
        · rw [if_pos hk, hb0, zpow_zero, mul_one, Nat.sub_zero]
          exact mul_le_mul_of_nonneg_left (geom_mix P.hlr0 P.hlr1 P.hb1 k0) hF
        · have : k0 = 0 := by omega
          subst this
          rw [if_neg (by omega), if_pos (Nat.zero_le _), if_pos ⟨by simp, noLong_self G 0 _⟩]
          unfold rf rho0
          simp only [runFrom, Nat.sub_zero, Nat.sub_self]
          rw [hb0, V2_warm (show (0 : ℤ) ≤ ((0 : ℤ), (0 : ℤ)).2 from le_rfl), zpow_zero, mul_one]
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
          calc P.lp ^ (k - 0) * P.e 2 = P.lp ^ (k - 0) * P.e 2 * 1 := by ring
            _ ≤ _ := mul_le_mul_of_nonneg_left (by linarith) hF

end Cryptarchia.Prob
