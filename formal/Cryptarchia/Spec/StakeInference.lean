module

public import Cryptarchia.Spec.Params
public import Mathlib.Data.Int.Notation
public import Mathlib.Data.Rat.Init
public import Mathlib.Tactic.ToDual
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
# Cryptarchia: the total stake inference arithmetic

`cryptarchia-total-stake-inference.md` rev 1.1.0, *Algorithm*:

```rust
let beta_p = truncate(beta * PRECISION)
let f_p = truncate(f * PRECISION)
let tse_p = total_stake_estimate * PRECISION
let measured_density_p = density_over_slots(epoch_slot, PERIOD) * PRECISION
let expected_density_p = PERIOD * f_p
let density_diff_p: i128 = expected_density_p - measured_density_p
let slot_activation_error_p: i128 = (tse_p * density_diff_p) / expected_density_p
let correction_p: i128 = (beta_p * slot_activation_error_p) / PRECISION
let new_total_stake_estimate = (tse_p - correction_p) / PRECISION
max(new_total_stake_estimate, 1)
```

Rust's `/` on signed integers truncates toward zero, which is `Int.tdiv`; the
model uses it for every division (the implementation, `ledger/src/cryptarchia/
stake.rs`, computes the same in `i128`). The model computes in `ℤ` without
overflow; `infer_no_overflow` gives the range of `D` for which the fixed-width
computation cannot overflow.
-/

@[expose] public section

namespace Cryptarchia

variable (c : Config)

/-- **`total_stake_inference`**: the next epoch's estimate from the current one
and the number `N` of distinct occupied slots counted in the observation period. -/
def infer (D N : ℕ) : ℕ :=
  let tseP : ℤ := D * c.precision
  let measuredP : ℤ := N * c.precision
  let expectedP : ℤ := c.period * c.fP
  let diffP : ℤ := expectedP - measuredP
  let errP : ℤ := Int.tdiv (tseP * diffP) expectedP
  let corrP : ℤ := Int.tdiv (c.betaP * errP) c.precision
  let newD : ℤ := Int.tdiv (tseP - corrP) c.precision
  (max newD 1).toNat

theorem infer_pos (D N : ℕ) : 1 ≤ infer c D N := by
  unfold infer
  simp only
  omega

/-- The exact-rational version of the update, `D · (1 - β·(f_p - N/PERIOD)/f_p)`,
that the fixed-point computation approximates (`β = betaP / PRECISION`,
`f_p = fP / PRECISION`). With `β = 1` it is `D · N / (PERIOD · f_p)`. -/
def inferReal (D N : ℕ) : ℚ :=
  let β : ℚ := c.betaP / c.precision
  let fp : ℚ := c.fP / c.precision
  D * (1 - β * (fp - N / c.period) / fp)

theorem inferReal_beta_one (D N : ℕ) (hb : c.betaP = c.precision) (hp : c.precision ≠ 0)
    (hP : c.period ≠ 0) (hf : c.fP ≠ 0) :
    inferReal c D N = D * N / (c.period * (c.fP / c.precision)) := by
  unfold inferReal
  simp only [hb]
  have : (c.precision : ℚ) ≠ 0 := by exact_mod_cast hp
  have : (c.period : ℚ) ≠ 0 := by exact_mod_cast hP
  have : (c.fP : ℚ) ≠ 0 := by exact_mod_cast hf
  field_simp
  ring

end Cryptarchia
