module

public import Cryptarchia.Prob.Tail
public import Mathlib.MeasureTheory.Measure.MeasureSpaceDef
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
import Mathlib.Topology.Sheaves.Init

/-!
# Probabilistic finality

The lottery string of an execution, cut to its first `M` slots and with honest
leader counts capped at two, is a list of outcomes (`slots`). The good event
`GoodLS` and the growth condition `GrowthS` see the string only through that list
(`good_congr`). So if the law of the list is (at most) that of a kernel within a
band, the deterministic finality theorem `final_bimm_epochs` and the bound
`settle_bound` give probabilistic finality (`final_bimm_prob`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- A slot of a characteristic string as an outcome, capping honest leaders at two. -/
def enc (p : ℕ × Bool) : Out := ⟨if p.1 = 0 then 0 else if p.1 = 1 then 1 else 2, p.2⟩

/-- **The first `M` slots of a characteristic string.** -/
def slots (w : CStr) (M : ℕ) : List Out := (List.range M).map fun i => enc (w (i + 1))

theorem slots_length (w : CStr) (M : ℕ) : (slots w M).length = M := by simp [slots]

variable {Δ M : ℕ}

/-- Strings that agree up to the horizon have the same phase ends. -/
theorem gend_congr_all {w w' : CStr} (h : SimOn w w' 0 M) : ∀ k, gend Δ M w k = gend Δ M w' k := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih =>
    by_cases hk : gend Δ M w (k + 1) ≤ M
    · exact gend_congr (h.mono le_rfl le_rfl) (k + 1) hk
    · rw [gend_succ, gend_succ, ← ih]
      by_cases hm : gend Δ M w k < M
      · have := nextE_le (Δ := Δ) (w := w) hm
        rw [gend_succ] at hk; omega
      · push Not at hm
        rw [nextE_of_ge hm, nextE_of_ge hm]

/-- **The good event sees the string only up to the horizon.** -/
theorem good_congr (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) {w w' : CStr} (h : SimOn w w' 0 M)
    {N Lw r G : ℕ} (hNM : N + G < M)
    (hg : GoodLS E w N Lw (gend Δ M w) ∧ GrowthS E w (gend Δ M w) N r G) :
    GoodLS E w' N Lw (gend Δ M w') ∧ GrowthS E w' (gend Δ M w') N r G := by
  have he : gend Δ M w = gend Δ M w' := funext (gend_congr_all h)
  rw [← he]
  obtain ⟨⟨h0, hmono, hq, hunb, hcold, hwin⟩, hgr⟩ := hg
  refine ⟨⟨h0, hmono, ?_, hunb, ?_, ?_⟩, ?_⟩
  · intro k hk
    have := hq k hk
    rw [hΔ] at this ⊢
    exact (quiet_congr (h.mono (Nat.zero_le _) (by omega))).1 this
  · intro t k h1 h2 h3 h4
    have := hcold t k h1 h2 h3 h4
    have hk1 : gend Δ M w (k + 1) ≤ M := by
      rw [gend_succ]; exact nextE_le (by omega)
    rw [hΔ] at this ⊢
    rw [← bnd_congr gend_mono k (h.mono le_rfl (by have := gend_mono (Δ := Δ) (M := M) (w := w) k; omega)),
      ← advCnt_congr (h.mono (Nat.zero_le _) hk1)]
    exact this
  · intro t ht
    rw [← occCnt_congr (h.mono (Nat.zero_le _) (by omega))]
    exact hwin t ht
  · intro ep hep hfix
    obtain ⟨j, h1, h2, h3, h4⟩ := hgr ep hep hfix
    have hcf := (hsane.fix_ok ep hep).1
    refine ⟨j, h1, h2, ?_, ?_⟩
    · rw [hΔ] at h3 ⊢
      rw [← bnd_congr gend_mono j (h.mono le_rfl (by omega))]
      exact h3
    · rw [hΔ] at h4 ⊢
      rw [← hD_congr (h.mono (Nat.zero_le _) (by unfold Config.fix at hfix ⊢; omega))]
      exact h4

/-- The lottery string of an execution. -/
noncomputable abbrev lotStr (E : Env) (es : List Event) : CStr := lotStrS E (σE E es) (lateAt E es)

/-- **A finality violation**: a block an honest node had as `B_imm` is missing from
an honest node's chain at a later point where both are online. -/
def Unsafe (E : Env) (es : List Event) : Prop :=
  ∃ n n' i j, n ≤ n' ∧ n' ≤ es.length ∧ i ∈ E.nodes ∧ j ∈ E.nodes ∧
    E.online i (wAt E es n').now = true ∧ E.online j (wAt E es n').now = true ∧
    ((wAt E es n).node i).bimm ∉ chainIds (wAt E es n').st ((wAt E es n').node j).cloc

end Cryptarchia.Prob
