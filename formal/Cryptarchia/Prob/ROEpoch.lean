module

public import Cryptarchia.Prob.WorstE
public import Cryptarchia.Prob.RO
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

/-!
# The lottery law over many epochs

Under a random oracle, fresh lotteries and Δ-delivery (`Prob/RO.lean`), suppose every
epoch state a slot can run under is within the band of a member of a family, chosen
by a fixed rule from the state (`pick`). A slot's epoch state depends only on its
epoch (`σE`), so the member is the same for all slots of an epoch and known before
each of them. `lottery_law_epoch` then bounds every event about the lottery string
that is closed under adding adversarial slots by a kernel that keeps one member per
epoch (`Kern.EpochFam`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Settle
open scoped ENNReal

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env}

/-- Consecutive slots of one epoch run under the same epoch state. -/
theorem σE_succ (E : Env) (es : List Event) {n : ℕ} (h : (n + 2) % E.c.epochLength ≠ 0) :
    σE E es (n + 2) = σE E es (n + 1) := by
  unfold σE Config.epochOf
  congr 1
  rw [show n + 2 = (n + 1) + 1 by omega, Nat.succ_div, if_neg (fun hd => h (Nat.mod_eq_zero_of_dvd hd)), add_zero]

/-- Consecutive slots of one epoch have the same epoch index. -/
theorem div_succ_of_mod {EL n : ℕ} (h : (n + 2) % EL ≠ 0) : (n + 2) / EL = (n + 1) / EL := by
  rw [show n + 2 = (n + 1) + 1 by omega, Nat.succ_div, if_neg (fun hd => h (Nat.mod_eq_zero_of_dvd hd)), add_zero]

theorem hist_mono (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) {j n : ℕ} (h : j ≤ n) : hist O σ j ≤ hist O σ n :=
  sup_le_sup (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)
    (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)

end Cryptarchia.Prob
