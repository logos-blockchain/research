# Token economics (Lean 4 + Mathlib)

A machine-checked version of Block Rewards 1.3.0, the Cryptoeconomics Overview 1.4.1 and the Execution Market 1.3.1 as modified by [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) and [logos-lips#481](https://github.com/logos-co/logos-lips/pull/481), and of Block Execution, which ties them to Mantle (`../Mantle`).

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build TokenEconomics`; `lake env lean TokenEconomicsTest/Axioms.lean` prints the axioms; `lake env lean TokenEconomicsTest/Spec.lean` checks the integer reference on hand-computed values; `lake env lean TokenEconomicsTest/Projection.lean` reproduces the supply projection.

## The model

The block reward is given twice: as the real-valued equation of the specification (`emissionFactor`, `reward`, with the parameter table) and as the integer reference `block_reward` (`aNumerator`, `release`, `payout`). The reward state (`RewardState`) is the reserve, the rewards pool, the pending Blend share and the window of pooled fees. `executeBlock` runs the five steps of Block Execution on a Mantle state and a reward state.

## Results

| Specification | Lean | Statement |
|---|---|---|
| *Deterministic Implementation*: `A_t' = A_t · 12·10⁷`, `FEE_AVG_NUMERATOR = 10,512` | **`aNumerator_eq`** | the integer numerator equals `A_SCALE · A_t` exactly, for the parameters of the table |
| `ι_t = min(⌊…⌋, B_{t-1})`, `π_t = ⌊…⌋` | **`release_eq`**, **`payout_eq`**, `maxRelease_eq` | the release is `min(⌊A_t I_max S_cap Δ_t⌋, B)`, the payout `⌊(1 - A_t) R̄_t⌋`, with `I_max S_cap Δ_t = 62,500/657` |
| `R_t = ι_t + π_t` | `reward_floor` | within 2 of the real `R_t` when the reserve does not bind |
| "every product stays below `2**101`", results in `uint64` | **`intermediates_lt`**, `outputs_lt` | for a window of 120 `uint64` fees; the largest product is below `2^98` |
| release capped at `I_max` of `S_cap` per year; reserve for `Y = 10` years | `release_le`, `annual_release_le`, `reserve_lasts` | at most 95 LGO per block, 99,864,000 per year |
| regimes `A_t → 1`, `A_t → 0` | `regime_release`, `regime_pool` | |
| "every pooled fee is paid out at most once … so the pool never goes below zero" | **`poolInv_rewardStep`**, **`payout_le_pool`** | `120 · pool ≥ ∑ᵢ i · window[i]` holds at genesis and after every block and Blend return, so `pool + pooled_fees ≥ payout` |
| *Pool Accounting*: the controlled total is constant | `rewardStep_conserves` | `reserve' + pool' + pending' + leader_share = reserve + pool + pending + pooled_fees` |
| 40% to the leader rounded down, the rest to Blend | `leaderShare_le`, `leaderShare_add_blendShare`, `blendShare_ge` | |
| Blend reward of epoch `e` paid from `blend_rewards_pending` in `e + 2` | **`blendSchedule_pending`** | the pending share is exactly the Blend shares of the two unpaid epochs, so it covers the payment |
| *Base Fee Update Rule* | `constants_eq`, `updateGAvg_eq`, **`updateBaseFee_eq`** | the integer rules are the floor and ceiling of the real rules |
| rounding up keeps 1 as the floor; down makes 0 absorbing | **`updateBaseFee_pos`**, `floor_absorbing` | |
| `±12.5%` per block | `updateBaseFee_fixed`, `updateBaseFee_ge`, `updateBaseFee_le`, `updateBaseFee_lower`, `updateBaseFee_upper` | |
| *Annex*: net circulating growth after 10 years | **`net_growth_le`**, `net_growth_ten_years` | for any stake and fees, at most 95 LGO per block, `9.99%` of `S_cap` over 10 years; the reserve is never exhausted |
| *Annex*: "a net circulating growth of about 0.25% per year" once settled | **`steady_growth`**, **`steady_quarter`** | with constant stake and fees `D`, the supply grows by `A (m - D)` per block; at the target stake with fees at `0.5%` a year, `A = 1/2` and the growth is `0.25%` a year exactly |
| *Annex*: "`A_t` averages about one half" despite the stake noise | **`clip_symmetric`** | a noise with a symmetric law leaves a clipped factor of `1/2` at `1/2` on average |
| *Annex*: the scenario | **`noiseFree_growth`** | without noise, the scenario's growth over 10 years is in `(3.246%, 3.248%)` of `S_cap` |
| *Annex*: 20 runs, mean `3.00%`, `2.81%` to `3.18%` | `TokenEconomicsTest/Projection.lean` (`Simulation.lean`, tested, not proven) | 20 runs of the annex's scenario: mean `3.02%`, `2.78%` to `3.31%`; without noise `3.250%` |
| "No token is ever minted: the maximum supply is fixed at genesis" | **`executeBlock_total`**, **`executeChain_total`** | the tokens of notes, withdrawn declarations, the PoW pool and its pending refill, the reserve, the pool and the pending Blend share never increase over a block, nor over any chain of blocks |

## Differences from the specification

1. **The base fee can rise by slightly more than 12.5%.** `G_max = 3,192,483 = 2 G_target + 1` because `G_target` is rounded down, so a full average multiplies the fee by `(9 G_target + 1)/(8 G_target)` (`increase_above_eighth`), before the rounding unit (which alone takes a fee of 1 to 2). Negligible, but "up to ±12.5%" is not exact.
2. **The proof of work refill.** `get_pow_pool_refill(e)` sums the diverted fees of the previous epoch; Block Execution does not say in which step the pool receives it. The model credits it at the first block of the next epoch (`powPending`); the total is the same at any step.
3. **The projection's 3% is the effect of its noise.** Without noise, the scenario of the annex grows the circulating supply by `3.247%` after 10 years (`noiseFree_growth`), above all 20 of the annex's runs (at most `3.18%`). The stake noise (25 units of `A_t` per unit of deviation) pulls `A_t` toward one half during the transition, which lowers the growth by about a quarter of a point; the simulator reproduces the annex's mean (`3.02%`) and shows the result moving with the noise level (`3.10%` at half the noise, `2.94%` at twice). The projection depends on the assumed noise of the inferred stake, which the annex states but does not discuss.

Confirmed as stated: the integer reference is the reward equation (to the floor), the `int128` bound, the pool never goes below zero, the Blend share is always available when paid, and the supply is fixed at Genesis; at steady state the growth is `0.25%` a year.

## Not formalized

- The stochastic runs of the projection are reproduced by simulation, not proven; the simulator steps by half-days (equal fees within a day, the annex's third scenario).
- The Storage Markets fee update and the Blend reward computation (the Blend notes of an epoch are an input, with their total at most the Blend reward).
- The KPI inference of the total stake (the stake is an input of each block).

## Layout

| File | Contents |
|---|---|
| `BlockReward.lean` | the reward equation and its integer reference |
| `Pools.lean` | reserve, pool, pending Blend share, leader share, Blend epochs |
| `ExecutionMarket.lean` | the EMA and the base fee |
| `Supply.lean` | Block Execution and the fixed supply |
| `Projection.lean` | the supply projection: universal bound, steady state, symmetric noise, the noise-free scenario |
| `Simulation.lean` | a simulator of the projection (`Float`) |
