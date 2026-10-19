import TokenEconomics

/-!
Checks of the integer reference against values computed by hand from the specification, in
units of `10⁻⁹` LGO. Every `#guard` fails the file if it does not hold:

  lake env lean TokenEconomicsTest/Spec.lean
-/

open TokenEconomics

-- No stake, no fees: `A_t = 1`, the reserve releases its maximum
-- `⌊62,500·10⁹/657⌋ = 95,129,375,951` per block.
#guard blockReward 0 (List.replicate 120 0) (10 ^ 18) = (95_129_375_951, 0)
-- The release is capped at the reserve.
#guard blockReward 0 (List.replicate 120 0) 40 = (40, 0)
-- Stake at target, no fees: `A_t = 0`, nothing is released.
#guard blockReward (3 * 10 ^ 18) (List.replicate 120 0) (10 ^ 18) = (0, 0)
-- Stake well above target with pooled fees of 1,200 LGO a block: `A_t = 0`, the payout is the
-- average pooled fee.
#guard blockReward (5 * 10 ^ 18) (List.replicate 120 (1_200 * 10 ^ 9)) (10 ^ 18) = (0, 1_200 * 10 ^ 9)
-- The same fees at 4·10¹⁸ of stake push `A_t` back to 1: the pooling rate term outweighs the
-- stake surplus, and the pool keeps the fees.
#guard blockReward (4 * 10 ^ 18) (List.replicate 120 (1_200 * 10 ^ 9)) (10 ^ 18) = (95_129_375_951, 0)
-- Halfway: `A_t' = 6·10¹⁶`, half the release and half the average.
#guard aNumerator 2_940_000_000_000_000_000 0 = 60_000_000_000_000_000
#guard blockReward 2_940_000_000_000_000_000 (List.replicate 120 0) (10 ^ 18) = (47_564_687_975, 0)
-- The leader receives 40% rounded down, the Blend service the rest.
#guard leaderShare 95_129_375_951 = 38_051_750_380 ∧ blendShare 95_129_375_951 = 57_077_625_571
-- The base fee is unchanged at the target, and never falls below 1.
#guard updateBaseFee 1_000 Mantle.G_TARGET = 1_000
#guard updateBaseFee 1 0 = 1
#guard updateBaseFee 8 0 = 7
-- A full average lifts a fee of 1 to 2: the rounding unit.
#guard updateBaseFee 1 Mantle.G_MAX = 2
-- The smoothed average.
#guard updateGAvg 1_000 2_000 = 1_100
