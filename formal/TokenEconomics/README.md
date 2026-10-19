# Token economics (Lean 4 + Mathlib)

A machine-checked version, at `tl/program_notes` 35e3c1c, of Block Rewards 1.3.0, the Cryptoeconomics Overview 1.4.1 and the Execution Market 1.3.1 as modified by [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) and [logos-lips#481](https://github.com/logos-co/logos-lips/pull/481), and of Block Execution, which ties them to Mantle (`../Mantle`).

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build TokenEconomics`; `lake env lean TokenEconomicsTest/Axioms.lean` prints the axioms; `lake env lean TokenEconomicsTest/Spec.lean` checks the integer reference on hand-computed values; `lake env lean TokenEconomicsTest/Projection.lean` reproduces the supply projection.

## The model

Tokens are counted in units of `10⁻⁹` LGO, as `TokenValue` does: `S_cap = 10¹⁹`, `B_0 = 10¹⁸`. The block reward is given twice: as the real-valued equation of the specification (`emissionFactor`, `reward`, with the parameter table) and as the integer reference `block_reward` (`aNumerator`, `release`, `payout`). The reward state (`RewardState`) is the reserve, the rewards pool, the pending Blend share and the window of pooled fees. `executeBlock` runs the five steps of Block Execution on a Mantle state and a reward state.

## Results

| Specification | Lean | Statement |
|---|---|---|
| *Deterministic Implementation*: `A_t' = A_t · 12·10¹⁶`, `FEE_AVG_NUMERATOR = 10,512` | **`aNumerator_eq`** | the integer numerator equals `A_SCALE · A_t` exactly, for the parameters of the table |
| `ι_t = min(⌊…⌋, B_{t-1})`, `π_t = ⌊…⌋` | **`release_eq`**, **`payout_eq`**, `maxRelease_eq` | the release is `min(⌊A_t I_max S_cap Δ_t⌋, B)`, the payout `⌊(1 - A_t) R̄_t⌋`, with `I_max S_cap Δ_t = 62,500·10⁹/657` |
| `R_t = ι_t + π_t` | `reward_floor` | within 2 of the real `R_t` when the reserve does not bind |
| "the pooled fees of a block never exceed the maximum supply of `10**19`, so every product stays below `2**127`", results in `uint64` | **`intermediates_lt`**, `intermediates_lt_spec`, `payout_product_le`, `outputs_lt` | below `2^127` for fees up to `10¹⁹`; in fact for any `uint64` stake and fees, the largest product (the payout's) stays below `2^108`, because it is non-zero only when `10,512 ∑ D_1 < A_SCALE + D_0` |
| release capped at `I_max` of `S_cap` per year; reserve for `Y = 10` years | `release_le`, `annual_release_le`, `reserve_lasts` | at most `95,129,375,951` units per block, `10¹⁷ - 308,800` per year |
| regimes `A_t → 1`, `A_t → 0` | `regime_release`, `regime_pool` | |
| "every pooled fee is paid out at most once … so the pool never goes below zero" | **`poolInv_rewardStep`**, **`payout_le_pool`** | `120 · pool ≥ ∑ᵢ i · window[i]` holds at genesis and after every block and Blend return, so `pool + pooled_fees ≥ payout` |
| *Pool Accounting*: the controlled total is constant | `rewardStep_conserves` | `reserve' + pool' + pending' + leader_share = reserve + pool + pending + pooled_fees` |
| 40% to the leader rounded down, the rest to Blend | `leaderShare_le`, `leaderShare_add_blendShare`, `blendShare_ge` | |
| Blend reward of epoch `e` paid from `blend_rewards_pending` in `e + 2` | **`blendSchedule_pending`** | the pending share is exactly the Blend shares of the two unpaid epochs, so it covers the payment |
| *Base Fee Update Rule* | `constants_eq`, `updateGAvg_eq`, **`updateBaseFee_eq`** | the integer rules are the floor and ceiling of the real rules |
| rounding up keeps 1 as the floor; down makes 0 absorbing | **`updateBaseFee_pos`**, `floor_absorbing` | |
| "up to about `±12.5%`" per block | `updateBaseFee_fixed`, `updateBaseFee_ge`, `updateBaseFee_le`, `updateBaseFee_lower`, `updateBaseFee_upper`, `increase_above_eighth` | a full average multiplies the fee by `(9 G_target + 1)/(8 G_target)`, as `G_max = 2 G_target + 1` |
| *Annex*: net circulating growth after 10 years | **`net_growth_le`**, `net_growth_ten_years` | for any stake and fees, at most `MAX_RELEASE` units per block, below `10%` of `S_cap` over 10 years; the reserve is never exhausted |
| *Annex*: "a net circulating growth of about 0.25% per year" once settled | **`steady_growth`**, **`steady_quarter`** | with constant stake and fees `D`, the supply grows by `A (m - D)` per block; at the target stake with fees at `0.5%` a year, `A = 1/2` and the growth is `0.25%` a year exactly |
| *Annex*: "`A_t` averages about one half" despite the stake noise | **`clip_symmetric`** | a noise with a symmetric law leaves a clipped factor of `1/2` at `1/2` on average |
| *Annex*: "`3.25%` without that noise" | **`noiseFree_growth`** | without noise, the scenario's growth over 10 years is in `(3.246%, 3.248%)` of `S_cap` in the continuous model, `3.250%` simulated |
| *Annex*: 20 runs, mean `3.00%`, `2.81%` to `3.18%`; `3.10%` with half the noise, `2.94%` with twice | `TokenEconomicsTest/Projection.lean` (`Simulation.lean`, tested, not proven) | 20 runs of the annex's scenario: mean `3.02%`, `2.78%` to `3.31%`; `3.10%` and `2.94%` at half and twice the noise |
| "No token is ever minted: the maximum supply is fixed at genesis" | **`executeBlock_total`**, **`executeChain_total`** | the tokens of notes, withdrawn declarations, the PoW pool and its pending refill, the reserve, the pool and the pending Blend share never increase over a block, nor over any chain of blocks |
| Mantle, *Arithmetic*: "no token value exceeds the maximum supply of `10^19` units, which a `TokenValue` holds" | **`executeChain_tokenValue`**, `maxSupply_lt` | from a state of at most `10¹⁹` units, every unspent note, the PoW pool, the reserve, the pool and the pending Blend share stay at most `10¹⁹ < 2^64` along any chain |
| Block Execution step 1: "at the first block of an epoch, also credit the pow reward pool with its refill" | `executeBlock` | the model credits the fees diverted during the previous epoch at that step |

## Differences from the specification

None. The three differences reported against 9e14358 are resolved by the revision of 2026-10-19: the Execution Market says "up to about `±12.5%`", Block Execution names the step that refills the proof of work pool, and the annex states the growth without the stake noise (`3.25%`) and at half and twice the noise (`3.10%`, `2.94%`), the values the model gives.

Confirmed as stated: the integer reference is the reward equation (to the floor) in units of `10⁻⁹` LGO, the `int128` bound, the pool never goes below zero, the Blend share is always available when paid, the supply is fixed at Genesis and fits a `TokenValue`; at steady state the growth is `0.25%` a year.

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
