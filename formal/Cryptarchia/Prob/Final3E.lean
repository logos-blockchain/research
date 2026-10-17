module

public import Cryptarchia.Prob.Final2E
public import Cryptarchia.Prob.Tail3E
import Cryptarchia.Prob.ROEpoch
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
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Probabilistic finality over many epochs, with an in-epoch contraction

`Cert3E` adds to a `Cert2E` an in-epoch contraction `lpi`: for each member, phase bounds
`ei k` from its own tables (`vpost`, no switch) and a crossing bound `pat0 k` from its own
band, meeting the class conditions with `lpi`. Phases that start more than `G` slots before an epoch boundary use them; the
others pay `(lp / lpi)` each, at most `G` times per check window (`swCnt_noSw_le`,
for `Lw + G < EL`). `final_bimm_ro_epoch3_ok` is `final_bimm_ro_epoch_ok` with the
failed-checks term `lpi^J · (lp/lpi)^G · e₂ · stat`.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

variable {B : Band} {Δ M : ℕ} {κ : Kern}

/-- **A certificate with an in-epoch contraction.** -/
structure Cert3E (B : Band) (Δ : ℕ) {K : ℕ} (fam : Fin K → Band) (EL G : ℕ) where
  C : Cert2E B Δ fam EL G
  lpi : ℝ
  ei : Fin K → Fin 19 → ℝ
  pat0 : Fin K → ℝ
  hcl : ∀ k, ClassOK C.P.c C.P.z C.P.s C.P.κ C.P.d lpi (ei k) (pat0 k)
  hlpi0 : 0 < lpi
  hlpi : lpi ≤ C.P.lp
  hpat : ∀ k, pat0 k ≤ (fam k).slo * (fam k).elo ^ Δ
  helo : ∀ k, 0 ≤ (fam k).elo
  heIn : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ k, autoBound (fam k) (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).1
    (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.1 (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.2 (C.vpost i k) ≤ ei k i

/-- **At most `G` switching slots in a window** of `L` slots, if `L + G < EL`: they lie
within `G` slots before the window's only boundary. -/
theorem swCnt_noSw_le {EL G L : ℕ} (hEL : 0 < EL) (hL : L + G < EL) (t : ℕ) :
    swCnt (fun s => ¬ NoSw EL G s) t (t + L) ≤ G := by
  classical
  unfold swCnt
  have key : ∀ a b, (a + 1) % EL = 0 → (b + 1) % EL = 0 → a < b → EL ≤ b - a := by
    intro a b ha hb hab
    have h3 : EL ∣ (b + 1) - (a + 1) := Nat.dvd_sub (Nat.dvd_of_mod_eq_zero hb) (Nat.dvd_of_mod_eq_zero ha)
    rw [show (b + 1) - (a + 1) = b - a by omega] at h3
    exact Nat.le_of_dvd (by omega) h3
  by_cases hex : ∃ s, t ≤ s ∧ s < t + L ∧ ¬ NoSw EL G s
  · obtain ⟨s0, hs0a, hs0b, hn0⟩ := hex
    unfold NoSw at hn0; push Not at hn0
    obtain ⟨j0, hj0a, hj0b, hj0c⟩ := hn0
    refine le_trans (Finset.card_le_card (t := Finset.Ico (j0 - G) j0) ?_) (by rw [Nat.card_Ico]; omega)
    intro s hs
    simp only [Finset.mem_filter, Finset.mem_Ico] at hs
    obtain ⟨⟨hsa, hsb⟩, hn⟩ := hs
    unfold NoSw at hn; push Not at hn
    obtain ⟨j, hja, hjb, hjc⟩ := hn
    have hjj : j = j0 := by
      rcases lt_trichotomy j j0 with h | h | h
      · have := key j j0 hjc hj0c h; omega
      · exact h
      · have := key j0 j hj0c hjc h; omega
    subst hjj
    rw [Finset.mem_Ico]; omega
  · refine le_trans (Finset.card_le_card (t := ∅) ?_) (by simp)
    intro s hs
    simp only [Finset.mem_filter, Finset.mem_Ico] at hs
    exact absurd ⟨s, hs.1.1, hs.1.2, hs.2⟩ hex

section Derive

variable {K EL G : ℕ} {fam : Fin K → Band} (D : Cert3E B Δ fam EL G) (hκ : κ.EpochFam EL fam)
include D hκ

/-- **The phase bounds** of the certificate. -/
theorem Cert3E.bounds : PhaseBounds κ M G D.C.P :=
  ⟨D.C.anyPhase hκ 0 (by decide) D.C.heS0, D.C.anyPhase hκ 1 (by decide) D.C.heS1,
    D.C.anyPhase hκ 2 (by decide) D.C.heS2, D.C.anyPhase hκ 17 (by decide) D.C.heS17, D.C.truncPhase hκ⟩

/-- **The in-epoch contraction**: a phase that starts more than `G` slots before an epoch
boundary meets the starting member's class conditions, through its crossing bound and
own-table phase bounds. -/
theorem Cert3E.inEpoch {Lw : ℕ} (hLw : Lw + G < EL) :
    InEpoch κ M G D.C.P D.lpi (fun t => ¬ NoSw EL G t) Lw G := by
  refine ⟨D.hlpi0, D.hlpi, swCnt_noSw_le (by omega) hLw, fun h hpe hlM hnb => ?_⟩
  obtain ⟨mem, hband, hmem⟩ := hκ
  have hG1 : 1 ≤ G := by have := D.C.hG; have := D.C.P.hΔ; omega
  refine ⟨D.ei (mem h), D.pat0 (mem h), D.hcl (mem h),
    ex_cross_truncIn mem hband hmem (D.hpat (mem h)) D.helo D.C.P.hΔ hlM D.C.hG (not_not.1 hnb), fun i h2 h17 => ?_⟩
  have hx := xg_nonneg D.C.P i
  exact phase_autoIn (D.C.solE i h2 h17).post (xg_g_nonneg D.C.P i) mem hband hmem hx.1 hx.2 hG1
    (D.heIn i h2 h17 (mem h)) D.C.P.hΔ (start_of_pe hpe (by omega)) (by omega) (not_not.1 hnb)

end Derive

end Cryptarchia.Prob
