module

import Cryptarchia.Proof.Recur
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
public import Cryptarchia.Prob.TSIRO

/-!
# Two links for the multi-epoch theorem

`recur_of`: the stake estimate's update (`Recur`) from statements about the canonical
chain. `inB0_of_genesis`: genesis in band for every execution, from the genesis state.
The multi-epoch theorem is `finality_tight` (`Prob/FinalTight`), restated from plain
assumptions as `finality` (`Prob/Finality`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory
open scoped ENNReal

/-- **`Recur` from the canonical chain.** If the canonical prefixes are consistent and
the canonical chain's occupied-slot count in epoch `e`'s window lies between `(1 - μ)`
times the honest occupied slots and all occupied slots plus genesis, the estimate's
update satisfies `Recur` (part 1, `cs_succ_D`). -/
theorem recur_of {E : Env} {es : List Event} {O : Oracle} (hA : Assm E) {Tb : TBand} (X : ℕ → Out) {e : ℕ}
    (hcons : 1 ≤ e → prefixBelow (CP (E.withO O) es (e + 1)) (E.c.cut e) = CP (E.withO O) es e)
    (hlo : (1 - Tb.μ) * hcnt E X e ≤ (occupied E.c (CP (E.withO O) es (e + 1)) e : ℝ))
    (hhi : (occupied E.c (CP (E.withO O) es (e + 1)) e : ℝ) ≤ wcnt E X e + 1) :
    Recur E Tb (σE (E.withO O) es) X e := by
  refine ⟨occupied E.c (CP (E.withO O) es (e + 1)) e, ?_, hlo, hhi⟩
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  have h1 : σE (E.withO O) es ((e + 1) * E.c.epochLength) = CS (E.withO O) es (e + 1) := by
    show CS (E.withO O) es ((e + 1) * E.c.epochLength / E.c.epochLength) = _
    rw [Nat.mul_div_cancel _ hEL]
  have h0 : σE (E.withO O) es (e * E.c.epochLength) = CS (E.withO O) es e := by
    show CS (E.withO O) es (e * E.c.epochLength / E.c.epochLength) = _
    rw [Nat.mul_div_cancel _ hEL]
  rw [h1, h0]
  exact cs_succ_D (hA.withO O) hcons

/-- **Genesis in band, for every execution**: the first epoch runs under the genesis
state, whatever the oracle and the execution. -/
theorem inB0_of_genesis {E : Env} {Tb : TBand} {o : Oracle} {es : List Event}
    (h0 : InB E Tb (fun _ => es0 E) 0) : InB E Tb (σE (E.withO o) es) 0 := by
  intro i h1 h2
  rw [zero_add, one_mul] at h2
  rw [σE_epoch0 (E.withO o) es (by exact h2), es0_withO]
  exact h0 i h1 (by rw [zero_add, one_mul]; exact h2)

end Cryptarchia.Prob
