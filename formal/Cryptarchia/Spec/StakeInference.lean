import Cryptarchia.Spec.Params

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
