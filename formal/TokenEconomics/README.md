# Token economics (Lean 4 + Mathlib)

A machine-checked version, at `tl/program_notes` 35e3c1c, of Block Rewards 1.3.0, the Cryptoeconomics Overview 1.4.1 and the Execution Market 1.3.1 as modified by [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) and [logos-lips#481](https://github.com/logos-co/logos-lips/pull/481), and of Block Execution, which ties them to Mantle (`../Mantle`).

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build` builds the library and its tests: `TokenEconomicsTest/Axioms.lean` fails the build if any declaration of `TokenEconomics` uses a `sorry` or another axiom, `TokenEconomicsTest/Spec.lean` checks the integer reference on hand-computed values, and `TokenEconomicsTest/Projection.lean` reproduces the supply projection.

## The model

Tokens are counted in units of `10⁻⁹` LGO, as `TokenValue` does: `S_cap = 10¹⁹`, `B_0 = 10¹⁸`. The block reward is given twice: as the real-valued equation of the specification (`emissionFactor`, `reward`, with the parameter table) and as the integer reference `block_reward` (`aNumerator`, `release`, `payout`). The reward state (`RewardState`) is the reserve, the rewards pool, the pending Blend share and the window of pooled fees. `executeBlock` runs the five steps of Block Execution on a Mantle state and a reward state, steps 1 and 2 being `prepareBlock`; the Blend reward is paid only in the first block of an epoch, and the fees diverted to the proof of work pool wait in `powPending` until the epoch boundary. No Genesis state is built: the results hold from any state satisfying the invariants (`Inv`, `PoolInv`, `ChanInv`), Genesis being one by the specification. The "any chain" results also take the capacity `Cap` of the note sets of the last state, fewer than `2^31` commitments per set (half the specification's, see `../Mantle/README.md`), which a set reaches after about 52,000 blocks of gas-priced Operations at the limit.

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
| *Pool Accounting*: the movements are between stocks | `rewardStep_conserves`, `runRewards_conserves` | `reserve' + pool' + pending' + leader_share = reserve + pool + pending + pooled_fees`, for a block and for a run |
| 40% to the leader rounded down, the rest to Blend | `leaderShare_le`, `leaderShare_add_blendShare`, `blendShare_ge` | |
| Blend reward of epoch `e` paid from `blend_rewards_pending` in the first block of `e + 2` | **`runEpochs_pending`**, **`blend_payment_covered`** | along epochs of blocks (`rewardStep`), each epoch `e ≥ 2` first paying epoch `e - 2` (`payBlend`), the pending share is exactly the Blend rewards of the two unpaid epochs, so it covers the payment. `executeBlock` takes the Blend reward as an input and pays it only at an epoch start; it applies the same `payBlend` |
| *Base Fee Update Rule* | `constants_eq`, `updateGAvg_eq`, **`updateBaseFee_eq`** | the integer rules are the floor and ceiling of the real rules |
| rounding up keeps a positive fee positive; rounding down makes 0 absorbing | **`updateBaseFee_pos`**, `floor_absorbing` | the effective floor is 7 units, not 1 (difference 1 below) |
| "up to about `±12.5%`" per block | `updateBaseFee_fixed`, `updateBaseFee_ge`, `updateBaseFee_le`, `updateBaseFee_lower`, `updateBaseFee_upper`, `increase_above_eighth` | a full average multiplies the fee by `(9 G_target + 1)/(8 G_target)`, as `G_max = 2 G_target + 1` |
| *Annex*: the release over 10 years | **`reserve_drain_le`**, `reserve_drain_ten_years` | for any stake and fees, the reserve releases at most `MAX_RELEASE` units per block, below `10%` of `S_cap` over 10 years; it is never exhausted |
| *Annex*: net circulating growth | **`net_growth_le`**, `block_growth_exceeds_release` | from a state with an empty pool and nothing pending, as at Genesis, the leader shares and the pending Blend share of a run, less the fees pooled in it, are at most what the reserve released; block by block they are not: one block can pay out of the pool more than ten times `MAX_RELEASE`. The proof of work pool, which also drains into circulation, is not counted |
| *Annex*: "a net circulating growth of about 0.25% per year" once settled | **`steady_growth`**, **`steady_quarter`** | with constant stake and fees `D`, the supply grows by `A (m - D)` per block; at the target stake with fees at `0.5%` a year, `A = 1/2` and the growth is `0.25%` a year exactly |
| *Annex*: "`A_t` averages about one half" despite the stake noise | **`clip_symmetric`** | a noise with a symmetric law leaves a clipped factor of `1/2` at `1/2` on average |
| *Annex*: "`3.25%` without that noise" | **`noiseFree_growth`** | without noise, the scenario's growth over 10 years is in `(3.246%, 3.248%)` of `S_cap` in the continuous model, `3.250%` simulated |
| *Annex*: 20 runs, mean `3.00%`, `2.81%` to `3.18%`; `3.10%` with half the noise, `2.94%` with twice | `TokenEconomicsTest/Projection.lean` (`Simulation.lean`, tested, not proven) | 20 runs of the annex's scenario: mean `3.02%`, `2.78%` to `3.31%`; `3.10%` and `2.94%` at half and twice the noise |
| "No token is ever minted: the maximum supply is fixed at genesis" | **`executeBlock_total`**, **`executeChain_total`**, `prepareBlock_spec` | the tokens of notes, withdrawn declarations, the PoW pool and its pending refill, the reserve, the pool and the pending Blend share never increase over a block, nor over any chain of blocks satisfying `Cap` |
| Mantle, *Arithmetic*: "no token value exceeds the maximum supply of `10^19` units, which a `TokenValue` holds" | **`executeChain_tokenValue`**, `executeBlock_fees_le`, `applyTxs_fees_le`, `maxSupply_lt` | from a state of at most `10¹⁹` units, every unspent note, the notes of each withdrawn declaration, the PoW pool and its pending refill, the reserve, the pool and the pending Blend share stay at most `10¹⁹ < 2^64` along any chain satisfying `Cap`; the fees and tips of the transactions of a block are at most the tokens of the block state. The check on `tx_balance` never rejects such a transaction (`Mantle.balance_check_holds`) |
| Block Execution step 1: "at the first block of an epoch, also credit the pow reward pool with its refill and set the epoch PoW reward" | `prepareBlock` | the model credits the fees diverted during the previous epoch and sets `epoch_pow_reward = compute_epoch_pow_reward(pow_reward_pool)` |
| Block Construction: a note cannot be consumed by a later transaction of its block | **`fresh_not_provable_in_block`**, `recentRoots_in_block` | at the start of a transaction, a commitment its set did not hold when the previous block ended has no path under any `tx_cm_root` |
| Channels and the gas check along a chain | `ChanInv.executeBlock`, `ChanInv.executeChain`, `chanInv_of_none` | every block keeps the channels well formed, so `gas_check_holds` applies to every Operation of a chain starting without channels |

## Differences from the specification

The three differences reported against 9e14358 are resolved by the revision of 2026-10-19: the Execution Market says "up to about `±12.5%`", Block Execution names the step that refills the proof of work pool, and the annex states the growth without the stake noise (`3.25%`) and at half and twice the noise (`3.10%`, `2.94%`), the values the model gives. Found since:

1. **The base fee's effective floor is 7 units, not 1.** The Execution Market says rounding up "makes 1 the effective floor of the base fee and leaves the mechanism unchanged at every other price level, as the rounding error is at most one unit against an adjustment of up to `±12.5%`", and the Overview "keeps one unit as the effective floor of each price". But `⌈7b/8⌉ = b` for `b ≤ 7`: a fee of at most 7 units never falls, even on an empty chain (`updateBaseFee_sticky`), a fee of at least 7 never falls below 7 (`updateBaseFee_floor`), and above the target any fee rises by at least a unit (`updateBaseFee_ratchet`). Below 8 units the rounding outweighs the adjustment, so a small fee only ratchets up.
2. **The controlled total is not constant within an epoch.** Block Rewards counts `S_t + P_t + B_t + W_t + E_t`, "constant since every movement is between stocks", but the share of each block's fees diverted to the proof of work pool is in none of these stocks until the epoch boundary, when Proof of Work credits it from the epoch's blocks. The model needs a stock of its own for it (`powPending`, counted in `total`). The Overview's "each block credits a fixed share of the fees it collects to this pool" contradicts the epoch-boundary refill.
3. **The Execution Market's pooled fee is gross of the diverted share.** Its `R̂_pooled = ∑ g_t · b_exec` subtracts nothing, while its own principle, Block Rewards' `D_1` ("net of the share diverted") and the Overview route the fees net of it. The model pools the net amount.
4. **When the Blend reward of an epoch is paid.** The Overview's *Service Rewards Distribution Protocol* says the rewards of epoch `e - 1` are inserted when epoch `e` starts, while its *Blend Service and Consensus Leaders* and Service Reward Distribution pay epoch `e` in the first block of `e + 2`. The model follows `e + 2`.

Confirmed as stated: the integer reference is the reward equation (to the floor) in units of `10⁻⁹` LGO, the `int128` bound, the pool never goes below zero, the pending Blend share covers each payment, no token is minted and every token value fits a `TokenValue`; at steady state the growth is `0.25%` a year.

## Not formalized

- The stochastic runs of the projection are reproduced by simulation, not proven; the simulator steps by half-days (equal fees within a day, the annex's third scenario).
- The Storage Markets fee update and the Blend reward computation: the Blend reward of an epoch and its notes are inputs of `executeBlock`, the notes worth at most the reward and the reward at most the pending share (`runEpochs_pending` shows the schedule covers it).
- The KPI inference of the total stake (the stake is an input of each block), and the Genesis state.

## Layout

| File | Contents |
|---|---|
| `BlockReward.lean` | the reward equation and its integer reference |
| `Pools.lean` | reserve, pool, pending Blend share, leader share, Blend epochs |
| `ExecutionMarket.lean` | the EMA and the base fee, its effective floor |
| `Supply.lean` | Block Execution, the fixed supply, fresh notes, channels along a chain |
| `Projection.lean` | the supply projection: reserve drain, net growth, steady state, symmetric noise, the noise-free scenario |
| `Simulation.lean` | a simulator of the projection (`Float`) |
