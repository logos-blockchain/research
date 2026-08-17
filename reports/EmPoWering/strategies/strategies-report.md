# Which strategy pays — five ways to participate in EmPoWering

Five participation strategies, simulated together on one honest chain for 120 epochs (about
two and a half years), competing for the same claim flow, the same leadership lottery and the
same service pool. A hundred nodes in each group. No Blend network, no propagation delay, no
adversary, no churn.

| # | strategy | mines | lottery | services |
| --- | --- | --- | --- | --- |
| 1 | miner | yes | no | no |
| 2 | miner and staker | yes | on what it mines | no |
| 3 | miner, staker and service provider | yes | yes | on reaching the bond |
| 4 | stakeholder | no | on initial stake | no |
| 5 | stakeholder and service provider | no | yes | yes |

Groups 4 and 5 are each endowed with 5% of launch supply, drawn once from a Pareto
distribution and reused between them. Groups 1 to 3 start with nothing and are given a Pareto
hashrate distribution floored at a measured Raspberry Pi 5, likewise drawn once and shared.
The paired draws are what make this a comparison of strategies rather than of luck.

Regenerate everything here with:

```
python3 -m empowering_sim.plots_strategies --out figures/strategies --epochs 120 --nodes 100
```

---

## 1. The result

![where a median node's income comes from](figures/strategy_composition.png)

| strategy | median node, LGO | against a plain stakeholder |
| --- | --- | --- |
| miner | 50,055 | 0.29× |
| miner and staker | 52,519 | 0.30× |
| stakeholder | 173,573 | 1.00× |
| miner, staker and service provider | 776,483 | **4.47×** |
| stakeholder and service provider | 905,542 | **5.22×** |

Three things fall out of that table, and only the first is obvious.

**Service provision dominates, by a factor of five.** Adding a service declaration to a plain
stake multiplies a node's income more than fivefold. Nothing else on the chain comes close.

**Staking on top of mining is worth almost nothing — three percent.** A miner who stakes
everything it mines earns 52,519 against a pure miner's 50,055. The reason is arithmetic: what
a miner accumulates over two and a half years is small against 5% of supply, so its share of
the lottery is correspondingly small. The two curves are visually indistinguishable in §2.

**Mining is the weakest of the five.** A miner earns less than a third of what a stakeholder
earns, and it is the only strategy that pays for its income in electricity.

### Why service provision wins, and it is structural

The service reward carries **no stake term at all**. `blend-protocol.md` splits the service
income across providers holding a valid activity proof — `R = I / (B + P)` — and stake appears
nowhere in that formula. It is a binary admission gate and nothing more. So the stream is
**flat per provider**: a node at the bare minimum bond earns exactly what a whale earns.

That is not a parameter anyone chose badly. It is what the mechanism is: paying a service by
the provider rather than by the capital behind it. But it means the marginal value of holding
more than the bond is zero for the largest reward stream on the chain, and the marginal value
of *reaching* the bond is the entire per-provider share.

---

## 2. Dispersion — and the strategy that erases it

![accumulated reward per node](figures/strategy_per_node.png)

The rank curves say more than the medians do.

| strategy | p10 | median | p90 | max ÷ min |
| --- | --- | --- | --- | --- |
| miner | 25,933 | 50,055 | 152,848 | 22.7× |
| miner and staker | 26,954 | 52,519 | 161,333 | 22.6× |
| stakeholder | 105,845 | 173,573 | 747,785 | **113.3×** |
| miner, staker and service | 736,251 | 776,483 | 894,908 | **1.8×** |
| stakeholder and service | 838,027 | 905,542 | 1,491,706 | 13.8× |

**The two service curves are nearly flat and the stakeholder curve is not.** A plain
stakeholder's reward spans a hundred-and-thirteenfold range, because leadership income is
strictly proportional to stake and the stake draw is Pareto — the top tenth of that group
holds 57.7% of it. The miner-staker-service curve spans **1.8×** across a hundred nodes whose
hashrates differ by 22.6×.

So **service provision is the only stream on the chain that compresses inequality**, and it
compresses it almost completely. Every other stream — mining, leadership — pays in proportion
to what you brought, and therefore preserves whatever distribution you started with. A flat
per-provider payment does the opposite.

That is the most consequential property in this report, and it cuts both ways. It is exactly
what one would want from an on-ramp. It is also a standing invitation to split one large
operator into many bonded identities, which §5 returns to.

---

## 3. What the proof-of-work reward actually looks like

![proof-of-work reward per block and per epoch](figures/pow_distributions.png)

Per block the reward is the arrival process at a fixed price: the reward per claim is frozen
for the whole epoch, so the shape is the Poisson claim count and nothing else. Median 8.4 LGO
a block against a target of ten claims at the opening reward.

Per epoch the picture carries the reward's decay as well, which is why it is not the same
distribution rescaled: the spread runs from about 250,000 LGO down through 140,000 across the
run as the endowment drains.

Neither distribution has a tail worth worrying about. The per-block variance is what a
thermostat holding ten claims a block produces, and the retarget was independently gated to
hold that rate to within half a percent across a three-hundredfold change in the field.

---

## 4. Electricity, and why it does not change the answer

Miners pay for their income and stakeholders do not. Netting it out, at the Pi 5's measured
rate and a whole-platform basis at 20 cents a kilowatt-hour:

| strategy | median electricity, 120 epochs | break-even token price |
| --- | --- | --- |
| miner | $83.28 | $1.7 × 10⁻³ /LGO |
| miner and staker | $83.28 | $1.6 × 10⁻³ /LGO |
| miner, staker and service | $83.28 | $1.1 × 10⁻⁴ /LGO |

Mining stops paying only if a token is worth less than about a sixth of a cent. Above that,
electricity is a rounding error against the reward, and **the ordering in §1 is unchanged**.
This is the one place the study's answer is robust rather than delicate.

It is worth being clear what that means: mining is not weak because it is expensive. It is
weak because it pays little.

---

## 5. The floor that turns the largest stream off

The service stream does not taper. Below **32 unique providers** the specification says rewards
*"are not calculated"* at all and nodes must bypass the Blend network entirely.

| nodes per group | providers | outcome |
| --- | --- | --- |
| 10 | 20 | **no service reward at all** |
| 20 | 40 | pays, 30,828 LGO per provider |
| 40 | 80 | pays, 15,414 LGO per provider |
| 100 | 200 | pays, 6,166 LGO per provider |

At ten nodes a group the dominant strategy in this report simply does not exist, and strategies
3 and 5 collapse onto 2 and 4. A study run at small group sizes would conclude that staking
wins — correctly for that chain, and misleadingly for this one.

Note also the shape of the payoff: the per-provider reward is the pool divided by the provider
count, so **each additional provider dilutes every other one**. Between 20 and 100 nodes a
group, the per-provider reward falls fivefold. Service provision pays enormously *and* is
congestible, and the two facts are the same fact.

---

## 6. The launch transient

The chain does not open in its steady state, and the reason is a decision recorded in
`docs/CONTRADICTIONS.md` rather than a modelling choice. The stake estimate is seeded at the
total distributed at genesis — 10¹⁰ LGO — against a target of 3×10⁹, so the deviation is
strongly negative and the emission factor clamps to **zero**. The chain opens on pure fee
recycling.

It corrects quickly. The lottery is calibrated against the estimate, so an estimate ten times
the truth makes the difficulty ten times too hard: the first epoch yields **2,160 blocks
instead of 21,600**, and that shortfall is precisely the signal the estimator corrects on. One
epoch, one order of magnitude, and the emission factor rises to one.

The consequence for this report is small but should be stated: the first two epochs pay
almost nothing from the block reward, and no service provider is bonded yet in any case. By
epoch 2 the mechanism is in the regime the rest of this report describes.

---

## 7. What would change these conclusions

Ranked by how much.

**Whether a locked service bond still carries leadership weight.** Not stated anywhere. The
simulator counts it, which is the favourable reading for strategies 3 and 5. If a bond is
removed from the lottery, a service provider trades its leader income for its service income
rather than adding one to the other — which would cut strategy 5 by roughly its leader share
and leave the ordering intact but narrow the gap.

**Who receives the emission.** `block-rewards.md` calibrates `I_max` so that "the APY for
validation is ~3.33%", which requires validators to receive the whole emission;
`overview-cryptoeconomics.md` gives leaders 0.4 of the block reward with Blend taking 0.6.
Both cannot hold. This report takes the stated 0.4. Under the other reading every leadership
figure here rises by two and a half times, which would roughly double a plain stakeholder's
income and narrow service provision's lead from 5.2× to about 2×.

**The minimal-Hamming doubling is not modelled.** Providers at minimal distance earn twice the
base share. Every provider here earns the base share, so the service groups' dispersion is
understated — the flatness in §2 is the floor of the flatness, not the whole of it.

**The bond itself is a decision, not a reading.** `min_stake.stake_threshold` is UNSET in the
specification. This study uses 1,000 LGO, the figure the static minimum stake analysis derives
— though that analysis assumed a supply a hundred times smaller than the one that governs. At
100,000 LGO instead, reaching the bond takes 86,401 claims rather than 865, and strategy 3
would not reach it inside this run at all.

---

## 8. What this says about the mechanism

The mechanism's stated purpose is to let someone with no stake mine their way into the
stake-based system. On these numbers it does that, but not in the way the design describes.

**Mining is not the reward. Reaching the bond is.** A miner who never declares a service earns
a third of what a stakeholder earns. The same miner, having crossed a 1,000 LGO threshold —
about 865 claims, a matter of days at a percent of the field — earns four and a half times what
that stakeholder earns. The entire value of the on-ramp is on the far side of a threshold that
costs almost nothing to cross, and almost none of it is in the mining reward itself.

**And the on-ramp's value is capped by a queue, not by money.** The endowment can fund fifty
thousand bonds at this threshold, which is not the binding constraint. What binds is that each
provider dilutes the others: the stream is a fixed pool divided by however many show up.
