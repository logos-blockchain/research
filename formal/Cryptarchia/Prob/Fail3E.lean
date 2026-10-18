module

public import Cryptarchia.Prob.Cold2
import Cryptarchia.Settle.Mono
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic

/-!
# A failed check is rare

A failed check at phase `k`, anchored at phase `k0` (`failC`), under a kernel
with one band member per epoch. Phase expectations are bounded only for phases cut at `G`
slots, so a check counts only if every phase from the anchor on has at most `G` slots
(`NoLong`); the long-phase term of the settlement bound pays for the rest. The reach part
before the anchor and the checked phase use bounds valid for any phase, the contraction
between anchor and check the truncated ones (`PhaseBounds`).

A phase that starts more than `G` slots before the next boundary stays in one member, so a
smaller in-epoch contraction `lpi` applies (`InEpoch`; `ex_cross_truncIn` for the crossing
pattern). Phases that start within `G` slots of a boundary (`Sw`) pay the ratio `lp / lpi`.
Within a check's window of `L` slots there are at most `Ccap` such slots, so the potential
`ΦfF` carries a weight `(lp / lpi)^c`, with `c` the switching slots left in the window
(`swCnt`); a failed check counts only if the check is within `L` slots of its anchor (the
span term pays for the rest). Before the anchor the potential is the reach potential `Φr2`
(`phiR2_pre`). `fail_checkF` bounds the expected count for any failed-check potential (`FailPot`:
nonnegative, at most the reach potential on warm states, paying for a check, contracting by `lp` and
`lpi`); `FailPot.ofV2` is the certificate's two-term potential, and `fail_checkE3` the bound with it.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-!
## Failed checks and spans

Fix a check at phase `k` and anchor the bound process at phase `k0 ≤ k`. The check
**fails** if the next phase is not empty and the margin is not cold for it (`failC`). A
span of phases from `k0` to `k1` weighs `τ` per slot (`spanH`); its expectation is at most
`e 17 ^ (k1 - k0)` (`span_bound'`).
-/

section

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

theorem failC_nonneg (Hc k0 k : ℕ) (w : CStr) : 0 ≤ failC Δ M Hc k0 k w := by
  unfold failC; split_ifs <;> norm_num

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
  have he17 : 0 ≤ P.e 17 := by
    have := h17 h hpe hlM
    refine le_trans (ExPh_nonneg _ _ (fun y => ?_) _) this
    rw [WP17]; positivity
  by_cases h1 : j < k0
  · -- constant until the anchor
    refine (ExPh_le_first hlM fun h' hf => ?_).trans (le_of_eq (show P.e 17 ^ (k1 - k0) = _ by
      unfold Ψs; rw [hj, if_pos h1]))
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
  · push Not at h1
    by_cases h2 : j < k1
    · -- one more phase of the span
      have hk0j : gend Δ M (strOf h) k0 ≤ h.length := by rw [← hej]; exact gend_strictMono.monotone h1
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Ψs Δ M P k0 k1) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.e 17 ^ (k1 - (j + 1)) *
            P.τ ^ (h.length - gend Δ M (strOf h) k0) * WP P 17 h.length h') h := by
        refine ExPh_mono_first hlM fun h' hf => ?_
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
      refine ExPh_le_first hlM fun h' hf => ?_
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

end

/-!
## The reach bound stays small

`reach_tail2'`: at any fixed phase index `j0`, `E[c^ρ] ≤ 1 + (b - 1) / (1 - λr)`, where `ρ`
is the reach bound there, through the potential `Φr2` (`phiR2_step`).
-/

section

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
/-- `c^ρ` at phase `j0`, once the history has reached it. -/
noncomputable def reachH2 (c : ℝ) (j0 : ℕ) (h : List Out) : ℝ :=
  if j0 ≤ pidx Δ M (strOf h) h.length then c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1 else 0

variable (Δ M) in
/-- The potential. -/
noncomputable def Φr2 (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < j0 then
    P.lr ^ (j0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (j0 - pidx Δ M (strOf h) h.length), P.lr ^ i
  else P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1

theorem phiR2_step (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (j0 : ℕ) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr2 Δ M P j0) h ≤ Φr2 Δ M P j0 h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  by_cases hjk : j < j0
  · obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, j0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr2 Δ M P j0) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) h := by
      refine ExPh_mono_first hlM fun h' hf => ?_
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
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
      have hval : Φr2 Δ M P j0 h' ≤ P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i := by
        unfold Φr2
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
    have hval : Φr2 Δ M P j0 h = P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i := by
      unfold Φr2; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have h2 := hR0 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
      nlinarith [mul_nonneg hbl hlrn]
    · have h2 := hR1 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    refine ExPh_le_first hlM fun h' hf => ?_
    have hp' := next_pidx hpe hlM hf
    have hb := next_bnd hpe hlM hf (i := j0) (by rw [hj]; exact hjk)
    rw [hj] at hp'
    unfold Φr2
    rw [hp', hj, if_neg (by omega), if_neg (by omega), hb]

/-- Before the anchor `j0`, a function at most `F · Φr2` at the next phase end
contracts as `Φr2` does. -/
theorem phiR2_pre (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (j0 : ℕ) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) {F : ℝ} (hF : 0 ≤ F) {Φ : List Out → ℝ}
    (hΦ : ∀ h', FirstPE Δ M h h' → Φ h' ≤ F * Φr2 Δ M P j0 h') :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) Φ h ≤ F * Φr2 Δ M P j0 h := by
  refine (ExPh_mono_first hlM hΦ).trans ?_
  rw [ExPh_mul_const]; exact mul_le_mul_of_nonneg_left (phiR2_step P hR0 hR1 j0 hpe hlM) hF

theorem Φr2_nonneg (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : 0 ≤ Φr2 Δ M P j0 h := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  unfold Φr2; split_ifs
  · apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · exact zpow_nonneg hc0.le _

theorem reachH2_le_phi (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : reachH2 Δ M P.c j0 h ≤ Φr2 Δ M P j0 h := by
  unfold reachH2
  split_ifs with h1
  · unfold Φr2; rw [if_neg (by omega)]
  · exact Φr2_nonneg P j0 h

/-- The potential at genesis. -/
theorem Φr2_nil_le (P : Cert2 B Δ) (j0 : ℕ) : Φr2 Δ M P j0 [] ≤ 1 + (P.b - 1) / (1 - P.lr) := by
  have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
    apply Nat.eq_zero_of_le_zero
    exact pidx_le_of (by simp [gend_zero])
  unfold Φr2
  rw [hp0]
  have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
  split_ifs with h1
  · rw [hb0, zpow_zero, mul_one, Nat.sub_zero]
    exact geom_mix P.hlr0 P.hlr1 P.hb1 j0
  · have hj : j0 = 0 := by omega
    subst hj
    rw [hb0, zpow_zero]
    have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
    linarith

/-- **The reach bound at any phase has a uniform exponential moment.** -/
theorem reach_tail2' (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hM : 0 < M) (j0 : ℕ) :
    Ex κ M (reachH2 Δ M P.c j0) [] ≤ 1 + (P.b - 1) / (1 - P.lr) := by
  calc Ex κ M (reachH2 Δ M P.c j0) [] ≤ Ex κ M (Φr2 Δ M P j0) [] := Ex_mono M (reachH2_le_phi P j0) []
    _ ≤ Φr2 Δ M P j0 [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Φr2 Δ M P j0) (M := M)
          (fun h hpe hlM => phiR2_step P hR0 hR1 j0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := Φr2_nil_le P j0

end

section

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
/-- Every phase from `k0` to `j` has at most `G` slots. -/
def NoLong (G k0 j : ℕ) (w : CStr) : Prop := ∀ i, k0 ≤ i → i < j → gend Δ M w (i + 1) ≤ gend Δ M w i + G

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

end

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

/-! ## The crossing pattern inside an epoch -/

/-- No epoch boundary within `G` slots after `t`. -/
def NoSw (EL G t : ℕ) : Prop := ∀ j, t < j → j ≤ t + G → (j + 1) % EL ≠ 0

theorem mem_pat {EL K : ℕ} {mem : List Out → Fin K} (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    {G : ℕ} {l : List Out} (hnb : NoSw EL G l.length) (o1 : Out) : ∀ i, i + 1 ≤ G → mem (l ++ pat o1 i) = mem l
  | 0, _ => by
    show mem (l ++ [o1]) = mem l
    exact hmem l o1 (hnb (l.length + 1) (by omega) (by omega))
  | i + 1, hi => by
    rw [← pat_snoc, ← List.append_assoc]
    have hlen : (l ++ pat o1 i).length = l.length + 1 + i := by simp [pat]; omega
    rw [hmem _ _ (by rw [hlen, show l.length + 1 + i + 2 = (l.length + 2 + i) + 1 by omega]; exact hnb (l.length + 2 + i) (by omega) (by omega)),
      mem_pat hmem hnb o1 i (by omega)]

/-- **The crossing pattern inside an epoch**: at least the member's own pattern. -/
theorem ex_cross_truncIn {EL K : ℕ} {fam : Fin K → Band} (mem : List Out → Fin K)
    (hband : ∀ h, κ.BandAt (fam (mem h)) h) (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    {pat0 : ℝ} {h : List Out} (hpat : pat0 ≤ (fam (mem h)).slo * (fam (mem h)).elo ^ Δ) (helo : ∀ k, 0 ≤ (fam k).elo)
    (hΔ : 0 < Δ) (hlM : h.length + Δ + 1 ≤ M) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hnb : NoSw EL G h.length) :
    pat0 ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h := by
  refine le_trans hpat (ex_cross_trunc (helo (mem h)) hΔ hlM hG (hband h).slo fun i hi => ?_)
  have := (hband (h ++ pat ⟨1, false⟩ i)).elo
  rwa [mem_pat hmem hnb ⟨1, false⟩ i (by omega)] at this

/-! ## The potential with an in-epoch contraction -/

open Classical in
/-- The slots in `[t, T)` satisfying `Sw` (within `G` slots before an epoch boundary). -/
noncomputable def swCnt (Sw : ℕ → Prop) (t T : ℕ) : ℕ := ((Finset.Ico t T).filter Sw).card

theorem swCnt_anti (Sw : ℕ → Prop) {t t' T : ℕ} (h : t ≤ t') : swCnt Sw t' T ≤ swCnt Sw t T := by
  classical
  unfold swCnt
  exact Finset.card_le_card (Finset.filter_subset_filter _ (Finset.Ico_subset_Ico_left h))

theorem swCnt_succ_pos (Sw : ℕ → Prop) {t T : ℕ} (hs : Sw t) (ht : t < T) :
    swCnt Sw t T = swCnt Sw (t + 1) T + 1 := by
  classical
  unfold swCnt
  rw [← Finset.insert_Ico_add_one_left_eq_Ico ht, Finset.filter_insert, if_pos hs,
    Finset.card_insert_of_notMem (by simp)]

/-! ## The phase bounds -/

/-- **Phase bounds** under `κ` up to the horizon `M`: those of the reach recursion (`lr`,
`b`), of a check (`e 2`) and of a span (`e 17`) for any phase, and the others for phases
cut at `G` slots. -/
structure PhaseBounds (κ : Kern) (M G : ℕ) (P : Cert2 B Δ) : Prop where
  r0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr
  r1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b
  c2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2
  s17 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 17 h.length) h ≤ P.e 17
  cut : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i

theorem PhaseBounds.e2_nonneg {G : ℕ} {P : Cert2 B Δ} (hb : PhaseBounds κ M G P) (hM : 0 < M) : 0 ≤ P.e 2 :=
  le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _) (hb.c2 [] (pe_nil hM) (by simpa using hM))

/-- **An in-epoch contraction** `lpi ≤ lp`: a phase that starts at a slot outside `Sw`
meets the class conditions with `lpi`, through phase bounds `e` and a crossing bound
`pat` of its own; any `L` slots hold at most `Ccap` slots of `Sw`. -/
structure InEpoch (κ : Kern) (M G : ℕ) (P : Cert2 B Δ) (lpi : ℝ) (Sw : ℕ → Prop) (L Ccap : ℕ) : Prop where
  pos : 0 < lpi
  le_lp : lpi ≤ P.lp
  cap : ∀ t, swCnt Sw t (t + L) ≤ Ccap
  cls : ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length → ∃ (e : Fin 19 → ℝ) (pat : ℝ),
    ClassOK P.c P.z P.s P.κ P.d lpi e pat ∧
    pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h ∧
    ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i

/-- **A potential for failed checks.** A function `V` of the reach and margin bounds: nonnegative,
at most the reach potential `c^ρ` on warm states (where a check starts), paying for a check whose
margin catches up with `z^A`, with a pointwise bound `post` after a phase whose expectation contracts
by `lp` over any phase cut at `G` slots and by `lpi` over one that starts outside `Sw`. -/
structure FailPot (κ : Kern) (M G : ℕ) (P : Cert2 B Δ) (Sw : ℕ → Prop) where
  V : ℤ × ℤ → ℝ
  post : ℤ × ℤ → ℕ → List Out → ℝ
  lp : ℝ
  lpi : ℝ
  hlpi : 0 < lpi
  hle : lpi ≤ lp
  nonneg : ∀ st, 0 ≤ V st
  warm : ∀ ρ : ℤ, 0 ≤ ρ → V (ρ, ρ) ≤ P.c ^ ρ
  fail : ∀ st, Inv st → ∀ A : ℕ, -(A : ℤ) ≤ st.2 → 1 ≤ V st * P.z ^ A
  post_le : ∀ st, Inv st → ∀ (m : ℕ) (h : List Out), m ≤ h.length →
    V (step Δ (strOf h) 0 m h.length st) ≤ post st m h
  ex : ∀ st, Inv st → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M →
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (post st h.length)) h ≤ lp * V st
  exIn : ∀ st, Inv st → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length →
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (post st h.length)) h ≤ lpi * V st

/-- **The certificate's potential `V2` as a failed-check potential**, contracting by `lp` over any
phase (the class conditions `P.cls`) and by `lpi` in an epoch (`InEpoch`). -/
noncomputable def FailPot.ofV2 (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hb : PhaseBounds κ M G P) {lpi : ℝ} {Sw : ℕ → Prop} {L Ccap : ℕ} (hI : InEpoch κ M G P lpi Sw L Ccap) :
    FailPot κ M G P Sw where
  V := V2 P.c P.z P.s P.κ P.d
  post := postB2 P
  lp := P.lp
  lpi := lpi
  hlpi := hI.pos
  hle := hI.le_lp
  nonneg st := (V2_pos (by linarith [P.hc]) (by linarith [P.hz]) (by linarith [P.hs]) P.hκ P.hd0 st).le
  warm ρ hρ := by rw [V2_warm (show (0 : ℤ) ≤ (ρ, ρ).2 from hρ)]
  fail st hst A hA := by
    have h := fail_le2 P.hc P.hz P.hs P.hκ P.hd0 hst A
    rw [if_pos hA, zpow_natCast] at h
    exact h
  post_le st hst m h hm := post2_le P hst m h hm
  ex st hst h hpe hlM := ex_post2G_at (κ := κ) P hW hG hst hpe hlM
    (fun i h2 h17 => hb.cut i h2 h17 h hpe (by omega))
  exIn st hst h hpe hlM hsw := by
    obtain ⟨ei, pat0, hcl, hX, hEi⟩ := hI.cls h hpe hlM hsw
    exact ex_post2G_gen (κ := κ) P hcl hst hlM hX hEi

variable (Δ M) in
open Classical in
/-- A failed check at phase `k`, anchored at `k0`, counted only without long phases and
within `L` slots of the anchor. -/
noncomputable def failHE3 (G L Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then failH Δ M Hc k0 k h
  else 0

variable (Δ M) in
open Classical in
/-- **The potential.** Before the anchor the reach potential `Φr2`, times `lpi` per phase
and the full weight `(lp/lpi)^Ccap`; from the anchor on, `lpi` per remaining phase and the weight of
the switching slots left in the check's window, times the failed-check potential `F.V`. -/
noncomputable def ΦfF (P : Cert2 B Δ) {G : ℕ} {Sw : ℕ → Prop} (F : FailPot κ M G P Sw) (Ccap L Hc k0 k : ℕ)
    (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then F.lpi ^ (k - k0) * (F.lp / F.lpi) ^ Ccap * P.e 2 * Φr2 Δ M P k0 h
  else if pidx Δ M (strOf h) h.length ≤ k then
    (if h.length ≤ Hc ∧ NoLong Δ M G k0 (pidx Δ M (strOf h) h.length) (strOf h) ∧
        h.length ≤ gend Δ M (strOf h) k0 + L then
      F.lpi ^ (k - pidx Δ M (strOf h) h.length) * (F.lp / F.lpi) ^ swCnt Sw h.length (gend Δ M (strOf h) k0 + L) *
      P.e 2 * F.V (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) else 0)
  else failHE3 Δ M G L Hc k0 k h

/-- **The potential is a supermartingale over phases.** -/
theorem phiF_step (P : Cert2 B Δ) {G : ℕ} (hb : PhaseBounds κ M G P) {Sw : ℕ → Prop}
    (F : FailPot κ M G P Sw) {Ccap L : ℕ} (hcap : ∀ t, swCnt Sw t (t + L) ≤ Ccap)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ}
    (hk0 : k0 ≤ k) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfF Δ M P F Ccap L Hc k0 k) h ≤ ΦfF Δ M P F Ccap L Hc k0 k h := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have he2 := hb.e2_nonneg hM
  obtain ⟨hR0, hR1, hC2, -, -⟩ := hb
  have hlpi0 := F.hlpi
  have hRg1 : 1 ≤ F.lp / F.lpi := by rw [le_div_iff₀ hlpi0]; linarith [F.hle]
  have hRg0 : 0 ≤ F.lp / F.lpi := by linarith
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have hF : 0 ≤ F.lpi ^ (k - k0) * (F.lp / F.lpi) ^ Ccap * P.e 2 := by positivity
  by_cases hjk : j < k0
  · -- before the anchor
    refine (phiR2_pre P hR0 hR1 k0 hpe hlM hF fun h' hf => ?_).trans (le_of_eq ?_)
    · have hp' := next_pidx hpe hlM hf
      rw [hj] at hp'
      unfold ΦfF
      rw [hp']
      by_cases hjk' : j + 1 < k0
      · rw [if_pos hjk']
      · have hk0' : k0 = j + 1 := by omega
        have hbs := next_bnd_succ hpe hlM hf
        rw [hj] at hbs
        obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
        have hρ'0 : 0 ≤ ρ' := by rw [← hρ']; exact bnd_fst_nonneg _
        have hΦr : Φr2 Δ M P k0 h' = P.c ^ ρ' := by unfold Φr2; rw [hp', if_neg hjk', hk0', hρ']
        rw [if_neg hjk', if_pos (by omega), hΦr]
        have hcnt : swCnt Sw h'.length (gend Δ M (strOf h') k0 + L) ≤ Ccap := by
          have hg : gend Δ M (strOf h') k0 = h'.length := by rw [hk0', ← hp']; exact gend_pidx_pe hf.pe
          rw [hg]; exact hcap _
        split_ifs
        · refine le_trans (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right
            (mul_le_mul_of_nonneg_left (pow_le_pow_right₀ hRg1 hcnt) (pow_nonneg hlpi0.le _)) he2)
            (F.nonneg _)) ?_
          rw [show k - (j + 1) = k - k0 by omega, show j + 1 - k0 = 0 by omega]
          apply mul_le_mul_of_nonneg_left _ hF
          unfold rf rho0
          simp only [runFrom]
          rw [hk0', hρ']
          exact F.warm ρ' hρ'0
        · exact mul_nonneg hF (zpow_nonneg hc0.le _)
    · unfold ΦfF; rw [hj, if_pos hjk]
  · push Not at hjk
    have hgj : gend Δ M (strOf h) j = h.length := by rw [← hj]; exact gend_pidx_pe hpe
    obtain ⟨T0, hT0⟩ : ∃ T0, gend Δ M (strOf h) k0 + L = T0 := ⟨_, rfl⟩
    by_cases hjk2 : j ≤ k
    · by_cases hHl : h.length ≤ Hc ∧ NoLong Δ M G k0 j (strOf h) ∧ h.length ≤ T0
      · obtain ⟨st, hst⟩ : ∃ st, rf Δ M (strOf h) k0 (j - k0) = st := ⟨_, rfl⟩
        have hinv : Inv st := by rw [← hst]; exact rf_inv _ k0 _
        have hval : ΦfF Δ M P F Ccap L Hc k0 k h =
            F.lpi ^ (k - j) * (F.lp / F.lpi) ^ swCnt Sw h.length T0 * P.e 2 * F.V st := by
          unfold ΦfF; rw [hj, if_neg (by omega), if_pos hjk2, hT0, if_pos hHl, hst]
        have hVs : 0 ≤ F.V st :=
          F.nonneg st
        by_cases hjeq : j = k
        · -- the check
          subst hjeq
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfF Δ M P F Ccap L Hc k0 j) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => F.V st * WP P 2 h.length h') h := by
            refine ExPh_mono_first hlM fun h' hf => ?_
            have hp' := next_pidx hpe hlM hf
            rw [hj] at hp'
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj, hst] at hfn
            have hnl' : NoLong Δ M G k0 j (strOf h') :=
              (noLong_stable hpe hlM hf (by rw [hj])).2 hHl.2.1
            have hns' : gend Δ M (strOf h') j ≤ gend Δ M (strOf h') k0 + L := by
              rw [next_gend hpe hlM hf (show j ≤ _ by rw [hj]), next_gend hpe hlM hf (show k0 ≤ _ by rw [hj]; exact hjk),
                hgj, hT0]
              exact hHl.2.2
            unfold ΦfF failHE3 failH
            rw [hp', if_neg (by omega), if_neg (by omega), if_pos ⟨hnl', hns'⟩, if_pos (by omega), hfn]
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
              exact F.fail st hinv A hcond.2.1
            · rw [if_neg hcond]
              exact mul_nonneg hVs (mul_nonneg (pow_nonneg hz0.le _) hg)
          refine hle.trans ?_
          rw [ExPh_mul_const, hval, Nat.sub_self, pow_zero, one_mul]
          have hRc : 1 ≤ (F.lp / F.lpi) ^ swCnt Sw h.length T0 := one_le_pow₀ hRg1
          calc F.V st * ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h
              ≤ F.V st * P.e 2 := mul_le_mul_of_nonneg_left (hC2 h hpe hlM) hVs
            _ = 1 * (P.e 2 * F.V st) := by ring
            _ ≤ (F.lp / F.lpi) ^ swCnt Sw h.length T0 * (P.e 2 * F.V st) :=
                mul_le_mul_of_nonneg_right hRc (mul_nonneg he2 hVs)
            _ = _ := by ring
        · -- between the anchor and the check
          have hjk3 : j < k := by omega
          by_cases hT : h.length < T0
          · have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfF Δ M P F Ccap L Hc k0 k) h ≤
                ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
                  (fun h' => F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    truncG h.length G (F.post st h.length) h') h := by
              refine ExPh_mono_first hlM fun h' hf => ?_
              have hp' := next_pidx hpe hlM hf
              have hrs := next_rf_succ hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
              rw [hj] at hp' hrs
              rw [hst] at hrs
              have hpost := F.post_le st hinv h.length h' hf.lt.le
              have hpb : 0 ≤ F.post st h.length h' :=
                le_trans (F.nonneg _) hpost
              have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
              rw [hj] at hnn
              have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
                next_gend hpe hlM hf (by rw [hj]; exact hjk)
              have hcnt : swCnt Sw h'.length T0 ≤ swCnt Sw (h.length + 1) T0 :=
                swCnt_anti Sw (by have := hf.lt; omega)
              have hW0 : 0 ≤ F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 := by
                positivity
              unfold ΦfF
              rw [hp', if_neg (by omega), if_pos (by omega), hg0, hT0]
              split_ifs with hc
              · have hl : h'.length ≤ h.length + G := (hnn.1 hc.2.1).2
                rw [hrs]
                unfold truncG; rw [if_pos hl]
                exact mul_le_mul (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left
                  (pow_le_pow_right₀ hRg1 hcnt) (pow_nonneg hlpi0.le _)) he2) hpost
                  (F.nonneg _) hW0
              · refine mul_nonneg hW0 ?_
                unfold truncG; split_ifs
                · exact hpb
                · exact le_rfl
            refine hle.trans ?_
            rw [ExPh_mul_const, hval]
            have hw : 0 ≤ F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 := by
              positivity
            have hkj : k - j = k - (j + 1) + 1 := by omega
            by_cases hsw : Sw h.length
            · have hpost2 := F.ex st hinv h hpe (by omega : h.length + Δ + 1 ≤ M)
              have hc1 : swCnt Sw h.length T0 = swCnt Sw (h.length + 1) T0 + 1 := swCnt_succ_pos Sw hsw hT
              rw [hc1]
              calc F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (F.post st h.length)) h
                  ≤ F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    (F.lp * F.V st) := mul_le_mul_of_nonneg_left hpost2 hw
                _ = _ := by
                  obtain ⟨R, hR⟩ : ∃ R, F.lp / F.lpi = R := ⟨_, rfl⟩
                  have hlR : F.lp = F.lpi * R := by rw [← hR]; field_simp
                  rw [hR, hlR, hkj, pow_succ, pow_succ]; ring
            · have hpost2 := F.exIn st hinv h hpe (by omega : h.length + Δ + 1 ≤ M) hsw
              have hc1 : swCnt Sw (h.length + 1) T0 ≤ swCnt Sw h.length T0 := swCnt_anti Sw (by omega)
              calc F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (F.post st h.length)) h
                  ≤ F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    (F.lpi * F.V st) := mul_le_mul_of_nonneg_left hpost2 hw
                _ ≤ F.lpi ^ (k - (j + 1)) * (F.lp / F.lpi) ^ swCnt Sw h.length T0 * P.e 2 *
                    (F.lpi * F.V st) :=
                    mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left
                      (pow_le_pow_right₀ hRg1 hc1) (pow_nonneg hlpi0.le _)) he2) (mul_nonneg hlpi0.le hVs)
                _ = _ := by rw [hkj, pow_succ]; ring
          · -- the window is over: nothing more
            refine (ExPh_le_first (c := 0) hlM fun h' hf => ?_).trans (by rw [hval]; positivity)
            have hp' := next_pidx hpe hlM hf
            rw [hj] at hp'
            have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
              next_gend hpe hlM hf (by rw [hj]; exact hjk)
            unfold ΦfF
            rw [hp', if_neg (by omega), if_pos (by omega), hg0, hT0,
              if_neg (fun hc => by have := hf.lt; have := hc.2.2; omega)]
      · -- past the horizon: nothing more
        have hval : ΦfF Δ M P F Ccap L Hc k0 k h = 0 := by
          unfold ΦfF; rw [hj, if_neg (by omega), if_pos hjk2, hT0, if_neg hHl]
        rw [hval]
        refine ExPh_le_first hlM fun h' hf => ?_
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
          next_gend hpe hlM hf (by rw [hj]; exact hjk)
        unfold ΦfF
        rw [hp', if_neg (by omega)]
        by_cases hj' : j + 1 ≤ k
        · rw [if_pos hj']
          have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
          rw [hj] at hnn
          rw [hg0, hT0, if_neg (fun hc => hHl ⟨by have := hf.lt; omega, (hnn.1 hc.2.1).1,
            by have := hf.lt; have := hc.2.2; omega⟩)]
        · rw [if_neg hj']
          have hjeq : j = k := by omega
          unfold failHE3
          by_cases hnl : NoLong Δ M G k0 k (strOf h') ∧ gend Δ M (strOf h') k ≤ gend Δ M (strOf h') k0 + L
          · rw [if_pos hnl]
            have hnl0 : NoLong Δ M G k0 j (strOf h) := by
              rw [hjeq]; exact (noLong_stable hpe hlM hf (by rw [hj]; omega)).1 hnl.1
            have hsp : h.length ≤ T0 := by
              have h2 := hnl.2
              rw [next_gend hpe hlM hf (show k ≤ _ by rw [hj]; omega), hg0, ← hjeq, hgj, hT0] at h2
              exact h2
            unfold failH
            rw [hp', if_pos (by omega)]
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj] at hfn
            rw [← hjeq, hfn, if_neg (fun hc => hHl ⟨hc.1, hnl0, hsp⟩)]
          · rw [if_neg hnl]
    · -- after the check: the failure is fixed
      push Not at hjk2
      refine ExPh_le_first hlM fun h' hf => ?_
      have hp' := next_pidx hpe hlM hf
      rw [hj] at hp'
      have hst' := noLong_stable (G := G) (k0 := k0) (j := k) hpe hlM hf (by rw [hj]; omega)
      have hgk := next_gend hpe hlM hf (i := k) (by rw [hj]; omega)
      have hgk0 := next_gend hpe hlM hf (i := k0) (by rw [hj]; omega)
      have hC : (NoLong Δ M G k0 k (strOf h') ∧ gend Δ M (strOf h') k ≤ gend Δ M (strOf h') k0 + L) ↔
          (NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L) := by
        rw [hgk, hgk0]; exact and_congr_left fun _ => hst'
      have e1 : ΦfF Δ M P F Ccap L Hc k0 k h' =
          (if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then
            failC Δ M Hc k0 k (strOf h') else 0) := by
        unfold ΦfF failHE3 failH; rw [hp', if_neg (by omega), if_neg (by omega)]
        by_cases hn : NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L
        · rw [if_pos (hC.2 hn), if_pos hn, if_pos (by omega)]
        · rw [if_neg (fun h'' => hn (hC.1 h'')), if_neg hn]
      have e2 : ΦfF Δ M P F Ccap L Hc k0 k h =
          (if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then
            failC Δ M Hc k0 k (strOf h) else 0) := by
        unfold ΦfF failHE3 failH; rw [hj, if_neg (by omega), if_neg (by omega)]
        by_cases hn : NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L
        · rw [if_pos hn, if_pos hn, if_pos (by omega)]
        · rw [if_neg hn, if_neg hn]
      rw [e1, e2, next_failC_old hpe hlM hf (by rw [hj]; exact hjk2) (by omega)]

theorem failHE3_le_phi (P : Cert2 B Δ) (he2 : 0 ≤ P.e 2) {G : ℕ} {Sw : ℕ → Prop} (F : FailPot κ M G P Sw)
    {Ccap L Hc k0 k : ℕ} (hk0 : k0 ≤ k) (h : List Out) :
    failHE3 Δ M G L Hc k0 k h ≤ ΦfF Δ M P F Ccap L Hc k0 k h := by
  classical
  have hRg0 : 0 ≤ F.lp / F.lpi := div_nonneg (by linarith [F.hle, F.hlpi]) F.hlpi.le
  have hlpi0 := F.hlpi
  by_cases h1 : pidx Δ M (strOf h) h.length < k0
  · have hf : failHE3 Δ M G L Hc k0 k h = 0 := by
      unfold failHE3 failH; split_ifs <;> first | rfl | omega
    rw [hf]; unfold ΦfF; rw [if_pos h1]
    exact mul_nonneg (by positivity) (Φr2_nonneg P k0 h)
  · by_cases h2 : pidx Δ M (strOf h) h.length ≤ k
    · have hf : failHE3 Δ M G L Hc k0 k h = 0 := by
        unfold failHE3 failH; split_ifs <;> first | rfl | omega
      rw [hf]; unfold ΦfF; rw [if_neg h1, if_pos h2]
      split_ifs
      · exact mul_nonneg (by positivity) (F.nonneg _)
      · exact le_rfl
    · unfold ΦfF; rw [if_neg h1, if_neg h2]

/-- **A failed check is rare**, for any failed-check potential. -/
theorem fail_checkF (P : Cert2 B Δ) {G : ℕ} (hb : PhaseBounds κ M G P) {Sw : ℕ → Prop}
    (F : FailPot κ M G P Sw) {Ccap L : ℕ} (hcap : ∀ t, swCnt Sw t (t + L) ≤ Ccap)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ} (hk0 : k0 ≤ k) :
    Ex κ M (failHE3 Δ M G L Hc k0 k) [] ≤
      F.lpi ^ (k - k0) * (F.lp / F.lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have he2 := hb.e2_nonneg hM
  have hlpi0 := F.hlpi
  have hRg1 : 1 ≤ F.lp / F.lpi := by rw [le_div_iff₀ hlpi0]; linarith [F.hle]
  have hF : 0 ≤ F.lpi ^ (k - k0) * (F.lp / F.lpi) ^ Ccap * P.e 2 := by positivity
  calc Ex κ M (failHE3 Δ M G L Hc k0 k) [] ≤ Ex κ M (ΦfF Δ M P F Ccap L Hc k0 k) [] :=
        Ex_mono M (failHE3_le_phi P he2 F hk0) []
    _ ≤ ΦfF Δ M P F Ccap L Hc k0 k [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := ΦfF Δ M P F Ccap L Hc k0 k) (M := M)
          (fun h hpe hlM => phiF_step P hb F hcap hHc hk0 hpe hlM)
          (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
        unfold ΦfF
        rw [hp0]
        by_cases hk : 0 < k0
        · rw [if_pos hk]
          exact mul_le_mul_of_nonneg_left (Φr2_nil_le P k0) hF
        · have : k0 = 0 := by omega
          subst this
          have hg00 : gend Δ M (strOf ([] : List Out)) 0 = 0 := gend_zero
          rw [if_neg (by omega), if_pos (Nat.zero_le _), hg00,
            if_pos ⟨by simp, noLong_self G 0 _, by simp⟩]
          unfold rf rho0
          simp only [runFrom, Nat.sub_zero, Nat.sub_self]
          rw [hb0]
          have hV0 : F.V (0, 0) ≤ 1 := by simpa using F.warm 0 le_rfl
          have hcnt : swCnt Sw ([] : List Out).length (0 + L) ≤ Ccap := by simpa using hcap 0
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
          calc F.lpi ^ (k - 0) * (F.lp / F.lpi) ^ swCnt Sw ([] : List Out).length (0 + L) * P.e 2 * F.V (0, 0)
              ≤ F.lpi ^ (k - 0) * (F.lp / F.lpi) ^ Ccap * P.e 2 * 1 :=
                mul_le_mul (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left (pow_le_pow_right₀ hRg1 hcnt)
                  (pow_nonneg hlpi0.le _)) he2) hV0 (F.nonneg _) hF
            _ ≤ _ := mul_le_mul_of_nonneg_left (by linarith) hF

/-- **A failed check is rare**, with an in-epoch contraction (`V2` and `InEpoch`). -/
theorem fail_checkE3 (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hb : PhaseBounds κ M G P) {lpi : ℝ} {Sw : ℕ → Prop} {Ccap L : ℕ} (hI : InEpoch κ M G P lpi Sw L Ccap)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ} (hk0 : k0 ≤ k) :
    Ex κ M (failHE3 Δ M G L Hc k0 k) [] ≤
      lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) :=
  fail_checkF P hb (FailPot.ofV2 P hW hG hb hI) hI.cap hHc hk0

end Cryptarchia.Prob
