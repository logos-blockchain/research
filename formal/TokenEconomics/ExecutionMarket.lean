import Mantle.Gas

/-!
# The execution market

Execution Market 1.3.1, *Base Fee Update Rule*: the smoothed average
`G_avg[s] = ⌊(G[s] + 9 G_avg[s-1]) / 10⌋` and the base fee
`b[s+1] = ⌈b[s] (7 G_target + G_avg[s]) / (8 G_target)⌉`, with `G_target = 1,596,241` and
`G_max = 3,192,483` (`Mantle.limit_eq`).

* `constants_eq`: `BASE_FEE_NUMERATOR = 7 G_target`, `BASE_FEE_DENOMINATOR = 8 G_target`;
* `updateGAvg_eq`, `updateBaseFee_eq`: the integer rules are the floor and the ceiling of the
  real rules `G_avg = (1-q) G + q G_avg`, `b' = b (1 + φ (G_avg - G_target)/G_target)` with
  `q = 9/10`, `φ = 1/8`;
* `updateGAvg_le`: blocks within `G_max` keep the average within `G_max`;
* **`updateBaseFee_pos`**: rounding up keeps the base fee at least `1`, while rounding down
  would make `0` absorbing (`floor_absorbing`);
* `updateBaseFee_fixed`, `updateBaseFee_ge`, `updateBaseFee_le`: the fee is unchanged at the
  target, rises above it and falls below it;
* `updateBaseFee_lower`, `updateBaseFee_upper`: a step changes the fee by at most `-12.5%` and
  `+12.5% + 1/(8 G_target)` of it, plus the rounding unit: `G_max = 2 G_target + 1`, so a full
  average lifts it slightly more than 12.5% (`increase_above_eighth`).
-/

namespace TokenEconomics

open Mantle

def EMA_DENOMINATOR : ℕ := 10
def EMA_PREV_WEIGHT : ℕ := 9
def BASE_FEE_NUMERATOR : ℕ := 11_173_687
def BASE_FEE_DENOMINATOR : ℕ := 12_769_928

def ceilDiv (a b : ℕ) : ℕ := (a + b - 1) / b

/-- `update_g_avg(prev_g_avg, block_gas_used)`. -/
def updateGAvg (prev used : ℕ) : ℕ := (used + EMA_PREV_WEIGHT * prev) / EMA_DENOMINATOR

/-- `update_base_fee(base_fee, g_avg)`. -/
def updateBaseFee (b gAvg : ℕ) : ℕ := ceilDiv (b * (BASE_FEE_NUMERATOR + gAvg)) BASE_FEE_DENOMINATOR

theorem constants_eq : BASE_FEE_NUMERATOR = 7 * G_TARGET ∧ BASE_FEE_DENOMINATOR = 8 * G_TARGET ∧
    G_MAX = 2 * G_TARGET + 1 := by decide

/-- `⌈a / b⌉ = (a + b - 1) / b`. -/
theorem natCeil_div (a b : ℕ) (hb : 0 < b) : ⌈(a : ℝ) / b⌉₊ = (a + b - 1) / b := by
  have hbr : (0 : ℝ) < b := by exact_mod_cast hb
  have hq := Nat.div_add_mod (a + b - 1) b
  have hr := Nat.mod_lt (a + b - 1) hb
  rw [Nat.mul_comm] at hq
  apply le_antisymm
  · apply Nat.ceil_le.2
    rw [div_le_iff₀ hbr]
    have : a ≤ (a + b - 1) / b * b := by omega
    exact_mod_cast this
  · have h := Nat.le_ceil ((a : ℝ) / b)
    rw [div_le_iff₀ hbr] at h
    have h' : a ≤ ⌈(a : ℝ) / b⌉₊ * b := by exact_mod_cast h
    by_contra hc
    push Not at hc
    have : (⌈(a : ℝ) / b⌉₊ + 1) * b ≤ (a + b - 1) / b * b := Nat.mul_le_mul_right _ hc
    rw [Nat.add_mul, Nat.one_mul] at this
    omega

/-- The integer average is the floor of `(1 - q) G + q G_avg`. -/
theorem updateGAvg_eq (prev used : ℕ) :
    updateGAvg prev used = ⌊(1 - 9 / 10 : ℝ) * used + 9 / 10 * prev⌋₊ := by
  rw [updateGAvg, show (1 - 9 / 10 : ℝ) * used + 9 / 10 * prev =
    ((used + EMA_PREV_WEIGHT * prev : ℕ) : ℝ) / (EMA_DENOMINATOR : ℕ) by
      simp only [EMA_PREV_WEIGHT, EMA_DENOMINATOR]; push_cast; ring,
    Nat.floor_div_eq_div]

/-- The integer base fee is the ceiling of `b (1 + φ (G_avg - G_target) / G_target)`. -/
theorem updateBaseFee_eq (b gAvg : ℕ) :
    updateBaseFee b gAvg =
      ⌈(b : ℝ) * (1 + 1 / 8 * ((gAvg : ℝ) - G_TARGET) / G_TARGET)⌉₊ := by
  have hG : (G_TARGET : ℝ) ≠ 0 := by simp [G_TARGET]
  rw [show (b : ℝ) * (1 + 1 / 8 * ((gAvg : ℝ) - G_TARGET) / G_TARGET) =
    ((b * (BASE_FEE_NUMERATOR + gAvg) : ℕ) : ℝ) / (BASE_FEE_DENOMINATOR : ℕ) by
      simp only [BASE_FEE_NUMERATOR, BASE_FEE_DENOMINATOR, G_TARGET] at hG ⊢
      push_cast
      field_simp
      ring]
  rw [updateBaseFee, ceilDiv, natCeil_div _ _ (by decide)]

/-- Blocks within `G_max` keep the smoothed average within `G_max`. -/
theorem updateGAvg_le {prev used : ℕ} (hp : prev ≤ G_MAX) (hu : used ≤ G_MAX) :
    updateGAvg prev used ≤ G_MAX := by
  unfold updateGAvg EMA_PREV_WEIGHT EMA_DENOMINATOR
  omega

/-- **Rounding up keeps the base fee at least `1`.** -/
theorem updateBaseFee_pos {b : ℕ} (hb : 1 ≤ b) (gAvg : ℕ) : 1 ≤ updateBaseFee b gAvg := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR
  have : 11_173_687 ≤ b * (11_173_687 + gAvg) := by nlinarith
  omega

/-- Rounding the base fee down instead would send `1` to `0` below the target, and `0` is
absorbing: execution would become free for good. -/
theorem floor_absorbing {gAvg : ℕ} (hg : gAvg < G_TARGET) (g' : ℕ) :
    1 * (BASE_FEE_NUMERATOR + gAvg) / BASE_FEE_DENOMINATOR = 0 ∧
      0 * (BASE_FEE_NUMERATOR + g') / BASE_FEE_DENOMINATOR = 0 := by
  simp only [G_TARGET] at hg
  simp only [BASE_FEE_NUMERATOR, BASE_FEE_DENOMINATOR, one_mul, zero_mul, Nat.zero_div,
    and_true]
  omega

/-- At the target the fee is unchanged. -/
theorem updateBaseFee_fixed (b : ℕ) : updateBaseFee b G_TARGET = b := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR G_TARGET
  omega

/-- Above the target the fee does not fall. -/
theorem updateBaseFee_ge {b gAvg : ℕ} (hg : G_TARGET ≤ gAvg) : b ≤ updateBaseFee b gAvg := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR
  simp only [G_TARGET] at hg
  have : b * 12_769_928 ≤ b * (11_173_687 + gAvg) := Nat.mul_le_mul_left _ (by omega)
  omega

/-- Below the target the fee does not rise. -/
theorem updateBaseFee_le {b gAvg : ℕ} (hg : gAvg ≤ G_TARGET) : updateBaseFee b gAvg ≤ b := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR
  simp only [G_TARGET] at hg
  have : b * (11_173_687 + gAvg) ≤ b * 12_769_928 := Nat.mul_le_mul_left _ (by omega)
  omega

/-- A step lowers the fee by at most 12.5%: `b' ≥ 7b/8`. -/
theorem updateBaseFee_lower (b gAvg : ℕ) : 7 * b ≤ 8 * updateBaseFee b gAvg := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR
  have h1 : b * 11_173_687 ≤ b * (11_173_687 + gAvg) := Nat.mul_le_mul_left _ (by omega)
  have h2 := Nat.div_add_mod (b * (11_173_687 + gAvg) + 12_769_928 - 1) 12_769_928
  have h3 := Nat.mod_lt (b * (11_173_687 + gAvg) + 12_769_928 - 1) (show 12_769_928 > 0 by omega)
  omega

/-- A step raises the fee by at most `12.5% + 1/(8 G_target)` of it, plus the rounding unit,
when the average is within `G_max`. -/
theorem updateBaseFee_upper {b gAvg : ℕ} (hg : gAvg ≤ G_MAX) :
    8 * G_TARGET * updateBaseFee b gAvg < 9 * G_TARGET * b + b + 8 * G_TARGET := by
  unfold updateBaseFee ceilDiv BASE_FEE_NUMERATOR BASE_FEE_DENOMINATOR
  simp only [G_MAX] at hg
  simp only [G_TARGET]
  have h1 : b * (11_173_687 + gAvg) ≤ b * (11_173_687 + 3_192_483) :=
    Nat.mul_le_mul_left _ (by omega)
  have h2 := Nat.div_mul_le_self (b * (11_173_687 + gAvg) + 12_769_928 - 1) 12_769_928
  omega

/-- With the average at `G_max`, the fee rises by slightly more than 12.5%, since
`G_max = 2 G_target + 1`: at `b = 8 G_target` it reaches `9 G_target + 1`. -/
theorem increase_above_eighth :
    updateBaseFee (8 * G_TARGET) G_MAX = 9 * G_TARGET + 1 := by decide

end TokenEconomics
