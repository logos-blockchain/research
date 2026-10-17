module

public import Cryptarchia.Prob.Reach2
public import Cryptarchia.Prob.Tail
public import Cryptarchia.Prob.Fail2
import Cryptarchia.Prob.Good
import Cryptarchia.Prob.Good2
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
# The probability that the good event fails, sharper

`settle_bound2`: under any kernel within the band, the probability that `GoodLS` or
`GrowthS` fails is at most `settleEps2`: long phases, long empty runs, long spans of
`J + 1` phases, failed checks, crowded windows, large reach, slow growth.
-/

@[expose] public section

namespace Cryptarchia.Prob

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
