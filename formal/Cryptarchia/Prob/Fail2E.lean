module

public import Cryptarchia.Prob.Cold2
public import Cryptarchia.Prob.Fail2
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
# One check, with one band member per epoch

As `Fail2.lean`, for kernels whose band changes only at epoch boundaries. Phase
expectations are bounded only for phases cut at `G` slots, so the potential `ΦfE`
counts a check only if every phase from the anchor on has at most `G` slots
(`noLong`); the long-phase term of the settlement bound pays for the rest. The
reach part before the anchor and the checked phase use bounds valid for any phase
(`hR0`, `hR1`, `hC2`); the contraction between anchor and check uses the truncated
bounds (`hE`, through `ex_post2G`).
-/

@[expose] public section

namespace Cryptarchia.Prob

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

end Cryptarchia.Prob
