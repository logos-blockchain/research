module

public import Cryptarchia.Prob.Fail3E
import Cryptarchia.Settle.Mono
public import Cryptarchia.Prob.Tail
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
import Mathlib.Tactic.ENatToNat
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
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init

/-!
# The good event from the absence of the bad events

`cold_of_checks`: on a full history, if every run of `G'` slots before `N` has an
occupied slot, no `J + 1` consecutive phases (up to `Hc = N + G'`) span more than
`Lw` slots, and no check before a nonempty phase fails (anchored `J` phases back),
then the cold condition of `GoodLS` holds at every slot. A check before an empty
phase needs no test: an empty phase leaves a margin that is not cold not cold
(`margin_empty`), so a failure there shows up at the end of the empty run.

`good_of2`: the good event `GoodLS` and the growth condition `GrowthS` hold unless one of
the bad events happens: long phases, long empty runs (`occF`), long spans of `J + 1` phases,
failed checks, crowded windows, large reach, slow growth.
-/

@[expose] public section

namespace Cryptarchia.Prob

section

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

end

open Finset Settle

variable {B : Band} {Δ M N : ℕ} {κ : Kern}

/-- **The good event and the growth condition, from the absence of the bad events.** -/
theorem good_of2 (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) {h : List Out} (hlen : h.length = M)
    {G G' J Lw r : ℕ} (hNG : N + G < M) (hNG' : N + G' < M)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m)
    (hocc : ∀ y ≤ N, ∃ i, y < i ∧ i ≤ y + G' ∧ (1 ≤ (strOf h i).1 ∨ (strOf h i).2 = true))
    (hspan : ∀ k, gend Δ M (strOf h) k ≤ N + G' → gend Δ M (strOf h) (k + 1) - gend Δ M (strOf h) (k - J) ≤ Lw)
    (hfail : ∀ k ≤ N + G', J ≤ k → failC Δ M (N + G') (k - J) k (strOf h) = 0)
    (hwin : ∀ t ≤ N, occCnt (strOf h) (t - Lw) t ≤ E.c.k)
    (hreach : ∀ j0, gend Δ M (strOf h) j0 ≤ N + G → (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1 ≤ r)
    (hdepth : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N →
      E.c.k + r < hD Δ (strOf h) (E.c.cut ep + G) (E.c.fix ep - Δ - 1)) :
    GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧ GrowthS E (strOf h) (gend Δ M (strOf h)) N r G := by
  set w := strOf h with hw
  refine ⟨⟨gend_zero, gend_mono, ?_, gend_unb, ?_, ?_⟩, ?_⟩
  · intro k hk; rw [hΔ]; exact gend_quiet k (by omega)
  · intro t k h1 h2 h3 h4
    rw [hΔ]
    exact cold_of_checks hNG' hocc hspan hfail h1 h2 h3 h4
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

/-- All `G'` slots after `y` are empty. -/
noncomputable def occF (G' y : ℕ) (h : List Out) : ℝ := ∏ i ∈ Finset.range G', blockG occQ 1 0 y 1 1 i h

theorem occF_one {G' y : ℕ} {h : List Out}
    (hno : ¬ ∃ i, y < i ∧ i ≤ y + G' ∧ (1 ≤ (strOf h i).1 ∨ (strOf h i).2 = true)) : occF G' y h = 1 := by
  classical
  unfold occF
  apply Finset.prod_eq_one
  intro i hi
  rw [Finset.mem_range] at hi
  rw [blockG_cases, if_neg]
  rintro ⟨j, h1, h2, h3⟩
  apply hno
  refine ⟨j, by omega, by omega, ?_⟩
  exact (occQ_iff h (by omega)).1 h3

theorem spanH_nonneg (τ : ℝ) (hτ : 0 ≤ τ) (k0 k1 : ℕ) (h : List Out) : 0 ≤ spanH Δ M τ k0 k1 h := by
  unfold spanH; split_ifs <;> positivity

theorem pr_occ_ge (hB : κ.Within B) (l : List Out) : B.hlo ≤ κ.pr l occQ := by
  refine le_trans (hB.hlo l) ?_
  unfold Kern.pr
  refine Finset.sum_le_sum fun o _ => ?_
  by_cases h1 : o.hon ≠ 0
  · have h2 : occQ o := Or.inl h1
    simp only [h1, ne_eq, not_false_eq_true, ↓reduceIte, h2]; exact le_rfl
  · simp only [h1, ↓reduceIte]
    split_ifs
    · exact κ.nonneg l o
    · exact le_rfl

end Cryptarchia.Prob
