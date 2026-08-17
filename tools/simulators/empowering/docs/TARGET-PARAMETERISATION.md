# Parameterising by outcome instead of by rate

A design note on the proposal to make the mechanism's controlling values **how many nodes we want to onboard** and **how long we want that to take**, with everything else derived.

## The short answer

It works, the inversion is exact and closed-form, and it is a better way to state the design. It also exposes one term the current parameterisation hides and which turns out to be worth 4.5×. One part of the intuition does not survive: the difficulty cannot be the controller for onboarding, and cannot be made into one without retargeting it on something else.

## The inversion

Three outcomes map one-to-one onto three parameters. Each is a closed form — no search, no fitting.

| you state | it determines | how |
| --- | --- | --- |
| `nodes_to_onboard` | `genesis_pool` | `genesis_pool = nodes_to_onboard * min_stake / conversion_efficiency` |
| `bootstrap_years` | `distribution_rate` | `distribution_rate = 1 - remaining_fraction ** (1 / bootstrap_epochs)` |
| `steady_reward` (a transaction bundle) | `pow_share` | `pow_share = bundle * target_claims_per_block / (txs_per_block * avg_tx_fee)` |

The first follows from the pool being the only source of a miner's first tokens; the second from the pool's decay being geometric at exactly `distribution_rate`; the third from the fee-funded steady state being the refill spread over an epoch's claims.

Checked against the current settings: `genesis_pool` of 50M LGO onboards 25,950 nodes at the good conversion efficiency and 5,700 at the bad one, which is what the elevation study measured. `distribution_rate = 1/200` corresponds to 90% of the pool spent in 9.4 years.

## What it exposes: conversion efficiency

The first inversion has a term the current parameterisation never asks about. The pool does not convert into bonds cleanly — most of what it pays out lands in balances that never reach the threshold. The elevation study measured **11.4%** when bonded miners keep mining and **51.9%** when they retire.

So the budget for a stated onboarding target is not one number but a range:

| nodes to onboard | at 51.9% efficiency | at 11.4% efficiency |
| --- | --- | --- |
| 1,000 | 1.9M LGO | 8.8M LGO |
| 10,000 | 19.3M LGO | 87.7M LGO |
| 50,000 | 96.3M LGO | 438.6M LGO |

**This is the strongest argument for the reparameterisation.** Under the current scheme you set `genesis_pool = 0.5%` of supply and discover the outcome afterwards; under the proposed one you state the outcome and are immediately asked what the conversion efficiency is — which is an unspecified behaviour worth a factor of four and a half in the budget. At 10,000 nodes it is the difference between 0.19% and 0.88% of supply.

## What it constrains: a floor under `bootstrap_years`

The within-epoch drain is closed by construction only while `target_claims_per_block / distribution_rate > max_block_txs`. That caps the distribution rate at about 1/102, and therefore puts a **floor of 4.82 years** under any bootstrap period at the specified claim target.

| bootstrap | `distribution_rate` | `T / rho` | drain-safe |
| --- | --- | --- | --- |
| 2.00 yr | 1/43 | 428 | **no** |
| 4.85 yr | 1/103 | 1,030 | yes |
| 9.40 yr | 1/199 | 1,992 | yes — current |
| 20.0 yr | 1/423 | 4,232 | yes |

A shorter bootstrap needs `target_claims_per_block` raised in step, and that thins the self-funding margin one for one. This is the second thing the reparameterisation makes visible at the moment of choosing rather than afterwards: state "two years" and you are told immediately that it costs you the margin.

## What it says about `pow_share`

Setting the steady reward to a transaction bundle inverts cleanly, and the answer is that the current share is about four times larger than the stated goal needs.

| inscription | bundle | `pow_share` needed | against the current 10% |
| --- | --- | --- | --- |
| 256 B | 7,763 base units | **2.32%** | 0.23× |
| 512 B | 9,555 | 2.85% | 0.29× |
| 1024 B | 13,139 | 3.93% | 0.39× |

One caveat: this holds at one traffic level. The fee-funded steady state scales with `txs_per_block`, so a share that exactly covers a bundle at 600 transactions covers ten bundles at 6,000. If the goal is that a claim covers a bundle *whatever the traffic*, the reward has to be **defined** as the bundle and the pool left to absorb the difference — which is a mechanism change rather than a re-parameterisation, and the only version that delivers the goal as stated.

## What does not survive: the difficulty as the onboarding controller

The proposal has the difficulty controlling the network to meet the bootstrap target. It cannot, and this is worth being plain about because the rest of the proposal is sound.

The difficulty controller targets the **claim count**, and it holds it there against a 380-fold change in load — that is measured, in the report's §1.3. It therefore controls neither how much value flows out of the pool, which is fixed by `distribution_rate` and the claim count, nor how many nodes reach the bond, which depends on how the claims are distributed among miners. All it decides is *who* gets the claims, by pricing out slow hardware.

To make the difficulty an onboarding controller it would have to retarget on something else — the number of *distinct* claimants, or the elevation rate itself — which is a different mechanism with its own sybil surface, since distinct-claimant counts are forgeable in a way that a claim count is not.

**The honest version of the intuition:** `distribution_rate` is the bootstrap clock, `genesis_pool` is the bootstrap budget, and the difficulty is what stops either from depending on how much hardware turns up. That last property is what makes the first two mean anything — without it, the clock and the budget would both move with adoption.

## What would have to change

Little, and most of it is presentation:

1. **A `targets.py` that inverts the three closed forms.** Trivial; they are the formulas above.
2. **The config takes targets and derives the parameters.** A presentation change, not a model change — the simulator computes the same things afterwards.
3. **Conversion efficiency becomes an explicit input**, because the first inversion cannot be stated without it. This is the substantive part: it forces a currently-invisible behaviour into the parameter set.
4. **Only if the steady-state goal is to hold at every traffic level**: the reward gains a floor at the bundle. That one is a mechanism change and should be taken on its own merits.

## Is it easier to reason about?

Yes, and for a reason worth naming. The current parameters are dimensionless rates and shares whose consequences only appear after a simulation: nobody can defend `distribution_rate = 1/200` directly. The proposed ones are outcomes a designer can hold an opinion about — *"ten thousand nodes onboarded within five years, and afterwards a claim pays for a transfer and a 256-byte inscription"* is a sentence that can be argued with, priced, and checked against.

The cost is that two of the three inversions carry a constraint the rate-based form let you ignore: the conversion efficiency, and the drain-safety floor. That is not really a cost.
