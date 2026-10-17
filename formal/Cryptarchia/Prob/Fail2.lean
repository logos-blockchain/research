module

public import Cryptarchia.Prob.Cold2
import Cryptarchia.Settle.Mono
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Tactic.Polynomial.Basic
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.BitVec

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

@[expose] public section

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

end Cryptarchia.Prob
