module

public import Cryptarchia.Proof.LotteryG
import Cryptarchia.Proof.Honest
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
# The lottery string of the first epoch

Within the first epoch every chain derives the genesis epoch state. The
**lottery string** records, for each slot, how many honest nodes hold a winning
note and whether the adversary does. It is a function of the lottery (the
tickets) alone, not of the adversary.

This is the first-epoch instance of `Proof/LotteryG.lean`, with every slot's
state the genesis one and every valid block in the tree:

* the settlement tree's honest successes at each slot are exactly the lottery's
  (given that honest staking notes stay unspent within the epoch);
* the tree's adversarial slots are among the adversary's lottery wins.

Hence the good event checked on the lottery string implies the execution's good
event, whatever the adversary does (`good_of_lottery`).
-/

@[expose] public section

namespace Cryptarchia

open Settle

variable (E : Env)

/-- The genesis epoch state. -/
def es0 : EpochState := epochState E.c E.L E.O E.G [genesisBlock] 0

variable {E} {es : List Event}

/-- Every chain of an execution derives the genesis epoch state for the first epoch. -/
theorem epochState_es0 {st : Store} (hS : StoreOK st) (hg : st genesisId = some genesisBlock)
    {b : ℕ} (hb : Rooted st b) : epochState E.c E.L E.O E.G (chainUp st b) 0 = es0 E := by
  rw [epochState_zero hS hb hS.rooted_gen]
  unfold es0
  congr 1
  unfold chainUp; rw [chain_genesis hg rfl]; rfl

end Cryptarchia
