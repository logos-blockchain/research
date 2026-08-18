# Parameterising by outcome instead of by rate

> **Revised after the fee correction.** This note was first written against a fee model that
> applied one price to both gas markets and so understated every fee by essentially its whole
> storage component. Two of the three inversions moved, and the first one changed *shape*
> rather than just value: the pool turns out to be self-sustaining, so a node target no longer
> sizes an endowment. The corrected version is below; the conclusion — that the
> reparameterisation is sound and worth doing — survives intact, and is if anything stronger.

A design note on the proposal to make the mechanism's controlling values **how many nodes we want to onboard** and **how long we want that to take**, with everything else derived.

## The short answer

It works, the inversion is exact and closed-form, and it is a better way to state the design. It also exposes one term the current parameterisation hides and which turns out to be worth 4.5×. One part of the intuition does not survive: the difficulty cannot be the controller for onboarding, and cannot be made into one without retargeting it on something else.

## The inversion

Three outcomes map one-to-one onto three parameters. Each is a closed form — no search, no fitting.

| you state | it determines | how |
| --- | --- | --- |
| `nodes_to_onboard` | the **time** it takes, not the endowment | `epochs = nodes_to_onboard * min_stake / (conversion_efficiency * epoch_refill)` |
| `bootstrap_years` | `distribution_rate` | `distribution_rate = 1 - remaining_fraction ** (1 / bootstrap_epochs)` |
| `steady_reward` (a transaction bundle) | `pow_share` | `pow_share = bundle * target_claims_per_block / (txs_per_block * avg_tx_fee)` |

The second follows from the pool's decay being geometric at exactly `distribution_rate`; the third from the fee-funded steady state being the refill spread over an epoch's claims. The first used to follow from the pool being the only source of a miner's first tokens — and that is the premise that broke.

Checked against the current settings: `distribution_rate = 1/200` corresponds to 90% of the endowment spent in 9.4 years, and the elevation study measures 23 bonds an epoch without retirement and 50 with.

## What changed: a node target buys time, not budget

The first inversion assumed the endowment is the only source of a miner's first tokens, so that `nodes_to_onboard` sized `genesis_pool`. With fees priced correctly that is false. The refill runs slightly ahead of what the pool pays, the pool holds its level indefinitely, and `epoch_refill / min_stake` = **268 bonds an epoch** are funded from fees alone, forever. There is no endowment large enough to be the binding constraint, because the endowment is not being consumed.

So a node target does not fix a budget. It fixes a **duration**, and the parameter it inverts onto is the schedule rather than the pool:

| nodes to onboard | bonded miners retire (50/epoch) | bonded miners keep mining (23/epoch) |
| --- | --- | --- |
| 1,000 | 20 epochs (0.4 yr) | 43 epochs (0.9 yr) |
| 10,000 | 200 epochs (4.1 yr) | 431 epochs (8.9 yr) |
| 50,000 | 1,001 epochs (20.6 yr) | 2,155 epochs (44.3 yr) |

**This is still the strongest argument for the reparameterisation, and now for a sharper reason.** The rate-based parameters cannot express an onboarding goal at all: `genesis_pool` sets a starting level that the mechanism then holds rather than spends. Stating the target forces the question of what actually limits the rate — and the answer is conversion efficiency, which is **8.9%** when bonded miners keep mining and **19.1%** when they retire. Nine-tenths of what the pool pays out lands in balances that never reach the bond. That is an unspecified behaviour worth a factor of two in the schedule, and nothing in the current parameterisation asks about it.

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

| inscription | `pow_share` needed | against the current 10% |
| --- | --- | --- |
| 256 B | **3.73%** | 0.37× |
| 512 B | 5.79% | 0.58× |
| 1024 B | **9.91%** | 0.99× |

The current 10% share is, to within a percent, *exactly* what a 1 kB bundle costs — which is the same fact the strategy report's §10 states from the other direction: the ceiling on the inscription is

| `max_inscription_bytes = (pow_share * txs_per_block / target_claims_per_block - 1) * transfer_tx_bytes` |
| --- |

= **1,035 bytes**, and it is independent of the storage price because the price appears on both sides and cancels. So this inversion is not free to choose: picking a target inscription *is* picking `pow_share`, and picking 1 kB pins it at essentially the value it already has, with 1% of headroom. **256 bytes at a 3.73% share is the version with real margin.**

One caveat: this holds at one traffic level. The fee-funded steady state scales with `txs_per_block`, so a share that exactly covers a bundle at 600 transactions covers ten bundles at 6,000. If the goal is that a claim covers a bundle *whatever the traffic*, the reward has to be **defined** as the bundle and the pool left to absorb the difference — which is a mechanism change rather than a re-parameterisation, and the only version that delivers the goal as stated.

## What does not survive: the difficulty as the onboarding controller

The proposal has the difficulty controlling the network to meet the bootstrap target. It cannot, and this is worth being plain about because the rest of the proposal is sound.

The difficulty controller targets the **claim count**, and it holds it there against a 380-fold change in load — that is measured, in the report's §1.3. It therefore controls neither how much value flows out of the pool, which is fixed by `distribution_rate` and the claim count, nor how many nodes reach the bond, which depends on how the claims are distributed among miners. All it decides is *who* gets the claims, by pricing out slow hardware.

To make the difficulty an onboarding controller it would have to retarget on something else — the number of *distinct* claimants, or the elevation rate itself — which is a different mechanism with its own sybil surface, since distinct-claimant counts are forgeable in a way that a claim count is not.

**The honest version of the intuition:** `distribution_rate` is the bootstrap clock, `genesis_pool` is the bootstrap budget, and the difficulty is what stops either from depending on how much hardware turns up. That last property is what makes the first two mean anything — without it, the clock and the budget would both move with adoption.

## What would have to change

Little, and most of it is presentation:

1. **A `targets.py` that inverts the three closed forms.** Trivial; they are the formulas above. Not yet built.
2. **The config takes targets and derives the parameters.** A presentation change, not a model change — the simulator computes the same things afterwards.
3. **Conversion efficiency becomes an explicit input**, because the first inversion cannot be stated without it. This is the substantive part: it forces a currently-invisible behaviour — worth a factor of two in the onboarding schedule — into the parameter set.
4. **Only if the steady-state goal is to hold at every traffic level**: the reward gains a floor at the bundle. That one is a mechanism change and should be taken on its own merits.

## Is it easier to reason about?

Yes, and for a reason worth naming. The current parameters are dimensionless rates and shares whose consequences only appear after a simulation: nobody can defend `distribution_rate = 1/200` directly. The proposed ones are outcomes a designer can hold an opinion about — *"ten thousand nodes onboarded within five years, and afterwards a claim pays for a transfer and a 256-byte inscription"* is a sentence that can be argued with, priced, and checked against.

The cost is that two of the three inversions carry a constraint the rate-based form let you ignore: the conversion efficiency, and the drain-safety floor. That is not really a cost.
