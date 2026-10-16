import Mathlib

/-!
# The block reward

Block Rewards 1.3.0 (RFC-480 §6). The reward of block `t` is

  `R_t = A_t · I_max · S_cap · Δ_t + (1 - A_t) · R̄_t`,

with the emission rate factor `A_t = min(1, max(0, (α_d δ_t + α_a γ_t + I_min) / I_max))`, the
stake deviation `δ_t = (D_0,target - D_0,t) / D_0,target`, the annualized pooling rate
`γ_t = (1/Δ_t)(1/T) ∑ D_1,τ / D_1,target`, and the average pooled reward `R̄_t = (1/T) ∑ D_1,τ`
over the last `T = 120` blocks.

The real-valued definitions (`emissionFactor`, `reward`) take the parameters of the table;
`block_reward` is the integer reference (`aNumerator`, `release`, `payout`). Results:

* **`aNumerator_eq`**: `A_t' = A_SCALE · A_t` exactly: the integer numerator *is* the emission
  rate factor, `FEE_AVG_NUMERATOR = 10,512` and `A_SCALE = 1.2·10⁸` being the exact constants;
* **`release_eq`**, **`payout_eq`**: the release is `min(⌊A_t · I_max S_cap Δ_t⌋, B_{t-1})` and
  the payout `⌊(1 - A_t) R̄_t⌋`, with `I_max S_cap Δ_t = 62,500/657` (`max_release_eq`);
* `reward_floor`: when the reserve does not bind, the integer reward is within `2` of `R_t`;
* `release_le`: at most `95` LGO leave the reserve per block, so at most `99,864,000` per year,
  within `I_max · S_cap = 10⁸` (`annual_release_le`), and the reserve `B_0 = 10⁹` lasts at least
  `Y = 10` years (`reserve_lasts`);
* `intermediates_lt`, `outputs_lt`: with fees in `uint64`, every product of `block_reward`
  stays below `2^101` (in fact `2^98`) and both results fit in `uint64`, as the specification
  states.
-/

namespace TokenEconomics

noncomputable section

/-! ## Parameters -/

/-- `S_cap`: 10 billion LGO. -/
def S_CAP : ℝ := 10 ^ 10
/-- Blocks per year: one every 30 seconds. -/
def BLOCKS_PER_YEAR : ℕ := 365 * 2880
/-- `Δ_t`: the fraction of a year in one block. -/
def DELTA : ℝ := 1 / BLOCKS_PER_YEAR
/-- `T`: the look-back window. -/
def T : ℕ := 120
def I_MAX : ℝ := 1 / 100
def I_MIN : ℝ := 0
def D0_TARGET : ℝ := 3 * 10 ^ 9
def D1_TARGET : ℝ := 10 ^ 10
def ALPHA_D : ℝ := 1 / 4
def ALPHA_A : ℝ := 1
/-- `Y`: the lifetime of the reserve at the maximum release rate. -/
def Y : ℝ := 10

/-- `B_0 = I_max · S_cap · Y`. -/
def B0 : ℝ := I_MAX * S_CAP * Y

/-- `δ_t`. -/
def stakeDeviation (D0 : ℝ) : ℝ := (D0_TARGET - D0) / D0_TARGET

/-- `γ_t`, for `S = ∑ D_1,τ` over the window. -/
def poolingRate (S : ℝ) : ℝ := (1 / DELTA) * (1 / T) * (S / D1_TARGET)

/-- `A_t`. -/
def emissionFactor (D0 S : ℝ) : ℝ :=
  min 1 (max 0 ((ALPHA_D * stakeDeviation D0 + ALPHA_A * poolingRate S + I_MIN) / I_MAX))

/-- `R̄_t`. -/
def avgPooled (S : ℝ) : ℝ := S / T

/-- `I_max · S_cap · Δ_t`: the maximum reserve release of a block. -/
def maxRelease : ℝ := I_MAX * S_CAP * DELTA

/-- `R_t`. -/
def reward (D0 S : ℝ) : ℝ :=
  emissionFactor D0 S * maxRelease + (1 - emissionFactor D0 S) * avgPooled S

/-! ## The integer reference -/

def A_SCALE : ℕ := 120_000_000
def STAKE_TARGET : ℕ := 3_000_000_000
def FEE_AVG_NUMERATOR : ℕ := 10_512
def WINDOW : ℕ := 120
def RELEASE_NUMERATOR : ℕ := 62_500
def RELEASE_DENOMINATOR : ℕ := 657

/-- `a_numerator = min(max(STAKE_TARGET - stake + FEE_AVG_NUMERATOR * sum_fees, 0), A_SCALE)`;
in `ℕ`, truncated subtraction is the `max(·, 0)`. -/
def aNumerator (stake sumFees : ℕ) : ℕ :=
  min (STAKE_TARGET + FEE_AVG_NUMERATOR * sumFees - stake) A_SCALE

/-- The release of `block_reward`, capped at the reserve. -/
def release (stake sumFees reserve : ℕ) : ℕ :=
  min (RELEASE_NUMERATOR * aNumerator stake sumFees / (RELEASE_DENOMINATOR * A_SCALE)) reserve

/-- The payout of `block_reward`. -/
def payout (stake sumFees : ℕ) : ℕ :=
  (A_SCALE - aNumerator stake sumFees) * sumFees / (WINDOW * A_SCALE)

/-- `block_reward(total_stake, pooled_fees_window, reserve)`. -/
def blockReward (stake : ℕ) (window : List ℕ) (reserve : ℕ) : ℕ × ℕ :=
  (release stake window.sum reserve, payout stake window.sum)

/-! ## The integer reference computes the reward equation -/

theorem maxRelease_eq : maxRelease = (RELEASE_NUMERATOR : ℝ) / RELEASE_DENOMINATOR := by
  simp only [maxRelease, I_MAX, S_CAP, DELTA, BLOCKS_PER_YEAR, RELEASE_NUMERATOR,
    RELEASE_DENOMINATOR]
  norm_num

/-- The two terms of the emission rate factor, over `I_max`, are `(3·10⁹ - D_0)/(12·10⁷)` and
`10,512 ∑ D_1 / (12·10⁷)`. -/
theorem inner_eq (D0 S : ℝ) :
    (ALPHA_D * stakeDeviation D0 + ALPHA_A * poolingRate S + I_MIN) / I_MAX =
      ((STAKE_TARGET : ℝ) - D0 + FEE_AVG_NUMERATOR * S) / A_SCALE := by
  simp only [ALPHA_D, stakeDeviation, D0_TARGET, ALPHA_A, poolingRate, DELTA, BLOCKS_PER_YEAR, T,
    D1_TARGET, I_MIN, I_MAX, STAKE_TARGET, FEE_AVG_NUMERATOR, A_SCALE]
  push_cast
  ring

theorem cast_tsub (a b : ℕ) : ((a - b : ℕ) : ℝ) = max ((a : ℝ) - b) 0 := by
  rcases le_total b a with h | h
  · rw [Nat.cast_sub h, max_eq_left (by simp [h])]
  · rw [Nat.sub_eq_zero_of_le h, max_eq_right (by simp [h])]
    simp

/-- **The integer numerator is the emission rate factor**: `A_t' = A_SCALE · A_t`. -/
theorem aNumerator_eq (stake sumFees : ℕ) :
    (aNumerator stake sumFees : ℝ) = A_SCALE * emissionFactor stake sumFees := by
  have hA : (0 : ℝ) < A_SCALE := by simp [A_SCALE]
  rw [emissionFactor, inner_eq, aNumerator, Nat.cast_min, cast_tsub]
  push_cast
  rw [mul_min_of_nonneg _ _ hA.le, mul_max_of_nonneg _ _ hA.le, mul_one, mul_zero,
    mul_div_cancel₀ _ hA.ne', min_comm, max_comm]
  congr 2
  ring

theorem aNumerator_le (stake sumFees : ℕ) : aNumerator stake sumFees ≤ A_SCALE :=
  min_le_right _ _

theorem emissionFactor_eq (stake sumFees : ℕ) :
    emissionFactor stake sumFees = (aNumerator stake sumFees : ℝ) / A_SCALE := by
  rw [aNumerator_eq]; field_simp [A_SCALE]

theorem floor_div (a b : ℕ) : ⌊(a : ℝ) / b⌋₊ = a / b := Nat.floor_div_eq_div a b

/-- **The release is the floor of `A_t · I_max S_cap Δ_t`, capped at the reserve.** -/
theorem release_eq (stake sumFees reserve : ℕ) :
    release stake sumFees reserve =
      min ⌊emissionFactor stake sumFees * maxRelease⌋₊ reserve := by
  rw [release, emissionFactor_eq, maxRelease_eq,
    show (aNumerator stake sumFees : ℝ) / A_SCALE * (RELEASE_NUMERATOR / RELEASE_DENOMINATOR) =
      ((RELEASE_NUMERATOR * aNumerator stake sumFees : ℕ) : ℝ) /
        ((RELEASE_DENOMINATOR * A_SCALE : ℕ) : ℝ) by push_cast; ring, floor_div]

/-- **The payout is the floor of `(1 - A_t) R̄_t`.** -/
theorem payout_eq (stake sumFees : ℕ) :
    payout stake sumFees = ⌊(1 - emissionFactor stake sumFees) * avgPooled sumFees⌋₊ := by
  have hA : (A_SCALE : ℝ) ≠ 0 := by simp [A_SCALE]
  rw [payout, emissionFactor_eq, avgPooled,
    show (1 - (aNumerator stake sumFees : ℝ) / A_SCALE) * ((sumFees : ℝ) / T) =
      (((A_SCALE - aNumerator stake sumFees) * sumFees : ℕ) : ℝ) / ((WINDOW * A_SCALE : ℕ) : ℝ) by
        rw [Nat.cast_mul, Nat.cast_sub (aNumerator_le _ _)]
        simp only [T, WINDOW]
        field_simp
        push_cast
        ring, floor_div]

/-- When the reserve does not bind, the integer reward is within `2` of `R_t`. -/
theorem reward_floor (stake sumFees reserve : ℕ)
    (h : ⌊emissionFactor stake sumFees * maxRelease⌋₊ ≤ reserve) :
    (release stake sumFees reserve + payout stake sumFees : ℝ) ≤ reward stake sumFees ∧
      reward stake sumFees < release stake sumFees reserve + payout stake sumFees + 2 := by
  have hA0 : 0 ≤ emissionFactor stake sumFees := by
    rw [emissionFactor_eq]; positivity
  have hA1 : emissionFactor stake sumFees ≤ 1 := by
    rw [emissionFactor_eq, div_le_one (by simp [A_SCALE])]
    exact_mod_cast aNumerator_le _ _
  have hm : 0 ≤ maxRelease := by rw [maxRelease_eq]; positivity
  have hp : 0 ≤ avgPooled sumFees := by unfold avgPooled; positivity
  rw [release_eq, min_eq_left h, payout_eq, reward]
  have e1 := Nat.floor_le (mul_nonneg hA0 hm)
  have e2 := Nat.floor_le (mul_nonneg (sub_nonneg.2 hA1) hp)
  have e3 := Nat.lt_floor_add_one (emissionFactor stake sumFees * maxRelease)
  have e4 := Nat.lt_floor_add_one ((1 - emissionFactor stake sumFees) * avgPooled sumFees)
  constructor <;> linarith

/-! ## Bounds -/

/-- At most `⌊62,500/657⌋ = 95` LGO leave the reserve per block. -/
theorem release_le (stake sumFees reserve : ℕ) : release stake sumFees reserve ≤ 95 := by
  unfold release
  refine (min_le_left _ _).trans ?_
  calc RELEASE_NUMERATOR * aNumerator stake sumFees / (RELEASE_DENOMINATOR * A_SCALE)
      ≤ RELEASE_NUMERATOR * A_SCALE / (RELEASE_DENOMINATOR * A_SCALE) :=
        Nat.div_le_div_right (Nat.mul_le_mul_left _ (aNumerator_le _ _))
    _ = 95 := by decide

theorem release_le_reserve (stake sumFees reserve : ℕ) :
    release stake sumFees reserve ≤ reserve := min_le_right _ _

/-- The release over a year stays within `I_max · S_cap = 10⁸` LGO. -/
theorem annual_release_le : 95 * BLOCKS_PER_YEAR ≤ 100_000_000 := by decide

/-- At the maximum release rate the reserve `B_0 = 10⁹` lasts at least `Y = 10` years. -/
theorem reserve_lasts : B0 = 1_000_000_000 ∧ 10 * (95 * BLOCKS_PER_YEAR) < 1_000_000_000 := by
  refine ⟨by norm_num [B0, I_MAX, S_CAP, Y], by decide⟩

/-- The payout of a block is at most a `1/120` share of the pooled fees of the window. -/
theorem payout_le (stake sumFees : ℕ) : WINDOW * payout stake sumFees ≤ sumFees := by
  unfold payout
  have h1 : (A_SCALE - aNumerator stake sumFees) * sumFees ≤ A_SCALE * sumFees :=
    Nat.mul_le_mul_right _ (Nat.sub_le _ _)
  have h2 := Nat.div_mul_le_self ((A_SCALE - aNumerator stake sumFees) * sumFees)
    (WINDOW * A_SCALE)
  have hA : 0 < A_SCALE := by decide
  nlinarith [Nat.mul_le_mul_left WINDOW (Nat.div_le_div_right (c := WINDOW * A_SCALE) h1),
    Nat.mul_div_le (A_SCALE * sumFees) (WINDOW * A_SCALE),
    Nat.mul_div_mul_right sumFees WINDOW hA]

/-- **Every intermediate of `block_reward` stays below `2^101`**, for a window of `120` fees
in `uint64`. -/
theorem intermediates_lt {stake : ℕ} {window : List ℕ} (hl : window.length = WINDOW) (hw : ∀ x ∈ window, x < 2 ^ 64) :
    FEE_AVG_NUMERATOR * window.sum < 2 ^ 101 ∧
      STAKE_TARGET + FEE_AVG_NUMERATOR * window.sum < 2 ^ 101 ∧
      RELEASE_NUMERATOR * aNumerator stake window.sum < 2 ^ 101 ∧
      (A_SCALE - aNumerator stake window.sum) * window.sum < 2 ^ 98 := by
  have hsum : window.sum ≤ WINDOW * (2 ^ 64 - 1) := by
    have := List.sum_le_length_nsmul window (2 ^ 64 - 1) (fun x hx => by have := hw x hx; omega)
    simpa [hl] using this
  have ha := aNumerator_le stake window.sum
  simp only [WINDOW] at hsum
  refine ⟨by simp only [FEE_AVG_NUMERATOR]; omega, by simp only [STAKE_TARGET, FEE_AVG_NUMERATOR]; omega,
    by simp only [RELEASE_NUMERATOR, A_SCALE] at ha ⊢; omega, ?_⟩
  calc (A_SCALE - aNumerator stake window.sum) * window.sum ≤ A_SCALE * (120 * (2 ^ 64 - 1)) :=
        Nat.mul_le_mul (Nat.sub_le _ _) hsum
    _ < 2 ^ 98 := by decide

/-- **Both results of `block_reward` fit in a `uint64`.** -/
theorem outputs_lt {stake reserve : ℕ} {window : List ℕ} (hl : window.length = WINDOW)
    (hw : ∀ x ∈ window, x < 2 ^ 64) :
    (blockReward stake window reserve).1 < 2 ^ 64 ∧ (blockReward stake window reserve).2 < 2 ^ 64 := by
  have hsum : window.sum ≤ WINDOW * (2 ^ 64 - 1) := by
    have := List.sum_le_length_nsmul window (2 ^ 64 - 1) (fun x hx => by have := hw x hx; omega)
    simpa [hl] using this
  have hp := payout_le stake window.sum
  refine ⟨by simp only [blockReward]; have := release_le stake window.sum reserve; omega, ?_⟩
  simp only [blockReward]
  simp only [WINDOW] at hp hsum
  omega

/-! ## Regimes -/

/-- Far from the targets (`A_t = 1`): the reward is the reserve release alone, the pool keeping
the fees. -/
theorem regime_release {stake sumFees reserve : ℕ}
    (h : A_SCALE ≤ STAKE_TARGET + FEE_AVG_NUMERATOR * sumFees - stake) :
    payout stake sumFees = 0 ∧ release stake sumFees reserve = min 95 reserve := by
  have ha : aNumerator stake sumFees = A_SCALE := min_eq_right h
  refine ⟨by simp [payout, ha], ?_⟩
  simp only [release, ha]
  rfl

/-- At the targets (`A_t = 0`): no release, the reward is the average pooled fee paid back. -/
theorem regime_pool {stake sumFees reserve : ℕ}
    (h : STAKE_TARGET + FEE_AVG_NUMERATOR * sumFees ≤ stake) :
    release stake sumFees reserve = 0 ∧ payout stake sumFees = sumFees / WINDOW := by
  have ha : aNumerator stake sumFees = 0 := by simp [aNumerator, Nat.sub_eq_zero_of_le h]
  refine ⟨by simp [release, ha], ?_⟩
  simp only [payout, ha, Nat.sub_zero]
  rw [Nat.mul_comm, Nat.mul_div_mul_right _ _ (by decide : 0 < A_SCALE)]

end

end TokenEconomics
