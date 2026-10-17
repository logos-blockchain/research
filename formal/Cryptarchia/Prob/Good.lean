module

public import Cryptarchia.Proof.FinalE
public import Cryptarchia.Prob.Cold
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
# The good event from the absence of five bad events

On a full sampled history `h` (length `M`), with the greedy phase ends, the good
event `GoodLS` and the growth condition `GrowthS` of the settlement theorem hold
unless one of five bad events happens (`good_of`):

* **long phase**: some phase starting by `N` lasts more than `G` slots;
* **cold failure**: some anchored failure (`accH`);
* **crowded window**: more than `k` occupied slots in a window of `Lw` slots;
* **large reach**: the reach bound exceeds `r` at a phase end;
* **slow growth**: honest depth over an epoch's last phase is at most `k + r`.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ M N W : ℕ}

/-- A phase that starts by `N` ends within `G` slots. -/
theorem phase_short {w : CStr} {G : ℕ} (hNG : N + G < M)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ w m) {j : ℕ} (hj : gend Δ M w j ≤ N) :
    gend Δ M w (j + 1) ≤ gend Δ M w j + G := by
  obtain ⟨m, h1, h2, h3⟩ := hq _ hj
  rw [gend_succ]
  exact le_trans (nextE_le_of_quiet h1 (by omega) h3) h2

theorem gend_pidx_M {w : CStr} : gend Δ M w (pidx Δ M w M) = M :=
  gend_pidx_of_end (Or.inr (Or.inl rfl))

end Cryptarchia.Prob
