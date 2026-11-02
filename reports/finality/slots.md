# Slot-based finality for Cryptarchia

Counted in slots, a Cryptarchia block is final once `K` slots have passed since its slot, a fixed time whatever the chain does. This report reads that rule alone: what `K` must be, the floor and the epoch nonce it needs, and what else it changes. The specification counts `k = 2160` blocks instead, which take 21 hours on its Blend and 30 to 33 hours while 30 % to a third of the stake withholds its blocks.

The figures are the finality study's, read in slots in its notes (`SLOTS.md`, phase K). The study's report reads the other routes beside this one. Specifications are read at `logos-lips` `47a73cdc`, the node at `logos-blockchain` `4e0405d51`. One slot is one second and `f = 1/30` unless stated.

## 1. Summary

Finality counted in slots is recommended at `K = ⌊k/f⌋` = 64,800 slots, 18 hours, with a floor of `φ` = 1,019 occupied slots and the epoch nonce of §4. `B_imm`, the latest immutable block, then passes a block once it is `K` slots old and `φ` occupied slots follow it. Against a third of the stake at `ε = 1e-9`, under a worst-case delay of 10 s, the wait that holds is 10.2 hours, and 12.5 after the adversary has deflated the inferred stake.

| parameter | recommended | what sets it |
| --- | --- | --- |
| the window `K` | 64,800 slots, 18 hours | `⌊k/f⌋` at `k = 2160`; it holds a third at 10 s with a factor of `8.4·10^6` to spare, `1.2·10^4` after a deflated inference (§3) |
| the floor `φ` | 1,019 occupied slots, in the depth form | the `ε` lower tail of what the honest chain makes in `K` while a third withholds, under the worst case at 10 s (§5) |
| the epoch nonce | the smallest contributions of 25 sub-windows, each bound to its parent's, passed through a sequential delay that spans the last sub-window | with today's nonce no `K` below 25.9 hours holds a third at 10 s (§4) |
| the inference's correction | uncapped | a cap lengthens a split's protection and a fall's stall alike, and the depth form gains nothing from it (§7) |
| the block rate | `f = 1/30`, as today | under the worst case a faster rate needs a longer `K` (§9) |

**What it gives.**

- Every block is final 18 hours after its slot. The floor delays that only on a sparse chain: under random delay a block made as the active stake halves is still fixed at 18 hours on average.
- Against a third at 10 s the chance of displacement after 18 hours is `1.2·10^-16` without grinding, and `8.4·10^-14` after a deflated inference. Without grinding `K` holds a third up to 15 s of worst-case delay.
- Both branches of a fork have one divergence age, so every node holding both decides alike under the Bootstrap rule (§8).
- A race lasts at most `K`, so the grinding bounds cover every target while `K` is at most 72 hours (§4).

**What it needs.**

- The epoch nonce of §4. With today's hash-chain nonce an adversary that withholds its wins chooses among leader schedules, and a third at 10 s then needs a wait of 26 to 42 hours.
- The floor. Without it an eclipse or a split fixes a fork after `K` slots, whatever stake made it, a block the node made itself included (§5).

**What it leaves.**

- A node cut off with a third of the stake fixes the fork it is shown after 1.05 days on average, and one cut off with a tenth after 3.5 (§5).
- No floor separates a partition at a third. At 18 hours the floor holds back a cut-off side only up to 0.385 of the stake, the adversary's included, so a split the adversary signs on waits for operators (§6).
- At 20 s of worst-case delay 18 hours does not hold a third: the wait is 33.5 hours without grinding (§3).

Three specification candidates follow (§10): `B_imm` counted in slots with the floor, the epoch nonce, and a Bootstrap density window sized for `(α, ε)`. §11 lists what is open.

## 2. The rule and the models

`B_imm` is the latest block of the node's chain that is at least `K` slots old and that `φ` occupied slots follow. The Online rule ignores a fork that diverges before `B_imm`, so a rollback reaches `K` slots back, and further only while the floor holds `B_imm` back. The Bootstrap rule compares such a fork by its density. Commit, fork pruning and rule 8 of Block Header Validation read `B_imm` as they do today (`SLOTS.md` K.0).

- **`K`, the window.** 64,800 slots at `k = 2160`: `⌊k/f⌋`, the time 2,160 blocks take at the full rate with no forks. The specification's own slot parameter `s = 3⌊k/f⌋`, 194,400 slots or 54 hours, is read beside it.
- **An occupied slot.** A slot holding a block of the chain or an uncle the chain references, each slot counted once, as `density_over_slots` of the stake inference counts them.
- **`φ`, the floor.** In its depth form `B_imm` passes a block only once `φ` occupied slots follow it. In its density form, which §5 reads beside it, `B_imm` passes a block only once the `K` slots after it hold `φ` blocks.

**The adversary** holds a share `α` of the stake. The design must hold against a third, and 30 % is read as the loosest share. A rule fails when a block it has fixed is displaced, and `ε = 1e-9` is the chance allowed per block.

**Two delay models.**

- **Random delay.** Blend's mixing delays, measured in the per-node engine of the total-stake inference (TSI) study: 1,000 nodes, a degree-6 peering graph and geographic links. The specification's Blend, 3 hops of up to 3 rounds, orphans 18 % of blocks and delivers a block to every node within 10.2 s at the 99th percentile. Only the private attack is played, with honest relays.
- **Worst case.** An adversary delivers every honest block as late as a bound `Δ` allows, taken at `Δ = 10` s, a chosen bound at about that 99th percentile. The bounds of Gaži, Ren and Russell apply ("Practical Settlement Bounds for Longest-Chain Consensus", ePrint 2022/1571, revision 2025-05-02), and they hold against every attack within `Δ`. Their code is ported and checked against their Table 1 and against the original run in Octave.

`K` binds every node, so it must hold under the worst case. The random-delay figures show what an honest Blend gives.

## 3. What `K` must be

Against a third at 10 s the wait that holds `ε` is 10.1 hours with a nonce that is not ground, 10.2 with the nonce of §4, and 12.5 with it after a deflated inference. `K = ⌊k/f⌋`, 18 hours, holds all three. After a deflation the chance at 18 hours is `8.4·10^-14`, about `10^4` times below `ε` with the nonce's factor counted (`SLOTS.md` K.7).

**A wait does not stretch.** While the adversary withholds, the honest chain grows from the honest stake alone: under the worst case one block per `Δ + 1/p_h` slots, where `p_h` is the honest stake's chance to win a slot. A wait of `K` slots must cover that pace and the runs in which the blocks come late. Gaži, Ren and Russell's Lemma 10 keeps the prefix up to a slot in every dominant chain once their margin stays negative. Their Markov chain, frozen at the phase in which the wait passes, therefore bounds a wait directly. It runs on the 1 s slot lottery, where a phase also holds the slot of its first honest block. That gives the adversary one slot more per phase than continuous time, and costs 10 % against a third at 10 s.

The wait that holds `ε = 1e-9` with a nonce that is not ground, in hours (`SLOTS.md` K.1, K.7):

| adversary | random delay, the specification's Blend | worst case at 10 s |
| --- | --- | --- |
| 10 % | 0.45 | 0.8 |
| 20 % | 1.04 | 1.9 |
| 25 % | 1.70 | 3.2 |
| 30 % | 3.09 | 5.9 |
| a third | 5.10 | 10.1 |

**What each `K` absorbs.** A grinding factor multiplies the chance against one leader schedule, so a `K` holds while the chance after it, times the factor, stays at most `ε`. At 10 s (`SLOTS.md` K.7):

| `K` | hours | a third: chance after `K` / factor absorbed | a third after a deflated inference | 30 % |
| --- | --- | --- | --- | --- |
| `⌊k/f⌋` = 64,800 slots | 18 | `1.2·10^-16` / `8.4·10^6` | `8.4·10^-14` / `1.2·10^4` | `9.4·10^-28` / `1.1·10^18` |
| `3⌊k/f⌋` = 194,400 slots | 54 | `3.2·10^-48` / `3.2·10^38` | `8.0·10^-40` / `1.2·10^30` | below `10^-55` / above `10^46` |

- **The nonce of §4 leaves a factor of at most 1.10 per nonce against a third,** plus a term per delay evaluator, which 18 hours absorbs. Today's hash-chain nonce reaches `10^28` against a third with two ground nonces, which only 54 hours absorbs.
- **The least `K` that holds.** Against a third at 10 s it is 10.1 hours without grinding, 10.2 with the nonce of §4 and 12.5 with it after a deflation. Against 30 % it is 5.9, 6.0 and 6.4.
- **The delay.** 18 hours holds a third without grinding up to 15 s of worst-case delay, where the wait is 17.4 hours, and not at 20 s, where it is 33.5. At 20 s only 54 hours holds a third, and only without grinding or a deflation. At 1 s the wait is 4.7 hours.
- **Under random delay** 18 hours holds 0.390 of the stake without grinding, and at least a third with the nonce of §4 (`SLOTS.md` K.2). The worst case is the binding model.

**What is shown, and what is not.**

- The worst-case wait is the bound of Gaži, Ren and Russell's chain, each phase's span charged at its longest and the slot lottery's extra slot counted. Half-slot levels shorten it by under 1 %, and twice the states change it by under 0.2 %.
- It lies above the paper's attack played against a wait on the slot lottery, which against a third succeeds 0.26 to 0.82 times as often as the bound allows.
- The deflated wait with the nonce of §4 takes that nonce's factor at the old rates, where its bound is derived.
- Delivery later than `Δ`, one block in a hundred under honest mixing on the specification's Blend, lies outside the bound.

## 4. The epoch nonce

`K` = 18 hours rests on an epoch nonce that resists grinding. With today's nonce no `K` below 25.9 hours holds a third at 10 s.

**Today's nonce can be ground.** The nonce of the next epoch is the hash chain at the last block before a cut-off slot, `6⌊k/f⌋` slots into the epoch. An adversary that withholds its wins chooses which of them end the chain there, and can fork away the last honest blocks. Each choice is a different leader schedule. Against a third at 10 s one ground nonce needs a wait of 25.9–26.7 hours, and two need 38.3–42.0. Against 30 % they need 13.6–14.1 and 16.1–18.7 hours. At 20 s one ground nonce needs 92.8–95.5 hours against a third. The ranges span two bounds on the factor, and neither end is an attack (`SLOTS.md` K.7; `SETTLEMENT.md` B6).

**A race lasts at most `K`.** The Online rule ignores a fork that diverges before `B_imm`, so a race against a target lasts at most `K` slots. A target meets two ground nonces only past its epoch's cut-off and within `K` slots of the epoch's end: 10 % of targets at 18 hours. While `K` is at most `4⌊k/f⌋` slots, 72 hours with the epoch at its length, no target meets a nonce its own private chain set, so the grinding bounds cover every target (`SLOTS.md` K.4).

**The recommended nonce** combines three changes (`SETTLEMENT.md` B7; `DESIGNS.md` H.2):

1. **The smallest contributions.** The window before the cut-off is split into 25 sub-windows at `k = 2160`, each of 15,552 slots, about 290 blocks. The nonce is taken from each sub-window's smallest contribution among its canonical blocks. A withheld block changes the nonce only if it holds a sub-window's minimum, and at the cut-off the adversary reaches 1.06 nonces on average against a third.
2. **A contribution bound to its parent's.** The minima are taken over `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`, which every node derives from public values. `ρ_LEAD` stays the win tag it is today, so the proof of leadership is unchanged. A value of the adversary's branch exists only once the block the branch forks from does.
3. **A sequential delay that spans the last sub-window.** The hash of the minima, fixed at the cut-off, passes through sequential squarings in a class group of a 1,024-bit discriminant, and the output is hashed into the nonce. The delay lasts the sub-window and a margin of ten minutes: 4.5 hours on the adversary's hardware at `k = 2160`. A Wesolowski proof of one group element is published before the nonce is first used, and is verified in 2–4 ms.

**What it leaves.** Without the delay the adversary could compute, from the start of the last sub-window, the nonce each of its decisions gives. With the delay those decisions are blind. The factor per nonce is then 1.009–1.011 against a third, sampled. Under the worst case at 10 s it is at most 1.10 as a bound, plus `1.6·10^-6` for each delay evaluator the adversary runs. Against a third at 10 s the guaranteed wait is 10.2 hours, against 10.1 for a nonce that cannot be ground.

**What it costs.** A hard fork. Sub-windows of at least 54 hours in all, which the epoch at its length gives with 108. A sequential computation of about a day once an epoch, by whoever first needs the nonce: at a speed ratio of 5 between the honest hardware and the adversary's, 22 hours at `k = 2160`, `1.7·10^10` squarings of one core. The documented ratio is 3 to 5, and the `4⌊k/f⌋` slots before the nonce is first used hold a ratio of 15 to 16.

**What is open.** The sequentiality assumption itself, the number of delay evaluators an adversary runs, and the formal write-up of the proof. The discrete logarithm in the class group of a 1,024-bit discriminant costs `2^91.4` to `2^101.4` operations, with the class group up to 1.6 times that: two hundred thousand to three hundred million machines of `10^18` operations a second within the delay. 2,048 bits give `2^139.4` and `2^149.4`. [`grinding.md`](grinding.md) reviews every approach to grinding side by side.

## 5. The floor

A floor of 1,019 occupied slots, in its depth form, keeps a node cut off with a third of the stake from fixing the fork it is shown for 1.05 days on average. It never stalls finality.

**What the window alone fixes.** A node fixes its chain once a block the rest of the network lacks is `K` slots old, whatever stake made it. An eclipsed node fixes the chain it is shown, or the chain it makes itself, `K` slots after that chain's first block: 0.75 days at 18 hours, for every share from a tenth up. A side of a partition fixes its fork after `K` slots, whatever its share. A node that receives no blocks for `K` slots would see `B_imm` reach its own tip (`SLOTS.md` K.3).

**Its size.** `φ` is the `ε` lower tail of the blocks the honest chain makes in `K` slots while a third withholds. Under the worst case at 10 s that chain makes 1,184 blocks on average in 18 hours, and its lower tail is 1,019. Under random delay the tail is 1,022, and a protocol takes the lower, so the chain reaches the floor under both models. A chain nobody withholds from falls below it with chance `2·10^-96`, and the chain a third withholds from with chance at most `ε`. When it does, finality waits for the next block that reaches the floor (`SLOTS.md` K.3).

**Counted as the stake inference counts.** The inference counts occupied slots, and with one uncle a block it recovers the honest stake at 0.998–1.001 under Blend (`reports/tsi/README.md` §3.2a). Every canonical block occupies its own slot, so on every path the count of occupied slots is at least the count of blocks, and a floor sized on blocks keeps its liveness. A side cut off from the rest, at its fastest, holds one block per slot it occupies, so it counts the same either way. Under random delay a floor on occupied slots could stand a fifth higher, at 1,225. Under the worst case no larger lower bound on the count is derived, and the floor stays at 1,019 (`SLOTS.md` K.9).

**The two forms at 18 hours.** The days a side cut off from the rest takes to fix its fork, at its fastest (`SLOTS.md` K.8, K.9):

| the side's share of the stake | depth form, mean | depth form, earliest at `ε` | density form, at the earliest |
| --- | --- | --- | --- |
| 0.1 | 3.49 | 2.87 | 8.25 |
| 0.2 | 1.75 | 1.44 | 8.25 |
| 0.25 | 1.40 | 1.15 | 8.25 |
| 0.3 | 1.17 | 0.96 | 8.25 |
| a third | 1.05 | 0.87 | 8.25 |

- **Both forms hold back past `K` a side of up to 0.385 of the stake.** A side of 0.4 passes them within a day: after 0.88 days under the depth form and 0.75 under the density form.
- **The depth form never stalls.** Under random delay a block made as the active stake halves is fixed after 0.75 days on average, counted on occupied slots, and after 0.83 counted on blocks. A fall to 40 % delays it to 0.88 days, and 1.04 on blocks.
- **The density form holds a sparse side back until its inferred stake corrects,** 8.25 days at the earliest. But it stalls finality whenever the active stake falls below 0.562 under random delay, counted on occupied slots, or below 0.665 counted on blocks. Without a cap on the inference's correction the stall lasts until the first correction, 11.25 days at the latest.
- **Against today's rule** the depth form's 1.05 and 3.5 days for a third and a tenth are about half of the 2.2 and 7.4 days that 2,160 blocks give.

**When the protection ends.** Every floor holds only until a sparse chain's inferred stake corrects. A side keeps the thresholds set before the split for at least `4⌊k/f⌋` slots, 3 days, and has corrected in full 7.5 to 15 days after it. From then every chain, the adversary's fork included, fills its slots at `f` and reaches either form of the floor (`SLOTS.md` K.3).

**What is shown, and what is not.** A side of a partition grows at most one block per slot it occupies, and the floor's figures rest on it. An adversary that orphans a run of honest blocks at once leaves one countable uncle, the run's first block (`reports/tsi/README.md` §6.6), so under the worst case the count of occupied slots is bounded below only by the count of blocks.

## 6. Partitions

No floor separates a partition at a third. From a fifth to 30 % of the stake a floor separates one only over windows of 0.88 days or more, so at 18 hours a split the adversary signs on waits for operators.

**A floor is a quorum.** The adversary signs on both sides of a partition. A floor separates the sides only if it lies above what a side of `(1 + α)/2` of the stake makes at its fastest, and below what the honest chain makes while the adversary withholds. At a third the two are equal. Below a third the gap between them is small, and under the worst case the honest chain also loses blocks to delay while the side loses none, so only long windows separate them (`SLOTS.md` K.3, K.9).

The least window, in days, at which a floor separates the sides of every partition:

| adversary | random delay, counted on occupied slots | worst case at 1 s | worst case at 5 s | worst case at 10 s |
| --- | --- | --- | --- | --- |
| 20 % | 0.88 | 1.04 | 2.63 | 28.4 |
| 25 % | 2.24 | 2.91 | 17.5 | none |
| 30 % | 14.2 | 28.4 | none | none |
| a third | none | none | none | none |

- **The worst-case columns count blocks.** Under the worst case no lower bound on the honest chain's occupied slots beyond its blocks is derived. Counted on blocks under random delay, the window is 516 days against a quarter, and none exists against 30 %.
- **At 18 hours** the floor of 1,019 holds back a side of at most 0.385 of the stake. With a third of the stake signing on it, that side's honest part is at most 0.052. The floor protects against an eclipse, and against a cut-off side the adversary does not sign on, but not against a partition the adversary signs on.

**What the floor leaves to operators.** A partition at a third. Below a third, every split that no floor separates at 18 hours. Any split that outlasts the inference's correction. The only separator the study found is a one-off round of anonymous-seat votes, cast when a node holds two chains that diverge before `B_imm`: 2,271 seats separate a quarter and 14,966 separate 30 % while Blend's relays deliver the votes, and none separates a third (`DESIGNS.md` H.1; `SLOTS.md` K.3, K.5).

## 7. The stake inference

A deflated inference lengthens the wait against a third at 10 s by 23 %, and 18 hours still holds it. The inference's correction is recommended uncapped.

**The deflation.** The inference corrects its estimate in full each epoch from the occupied slots of an observation period, the first `6⌊k/f⌋` slots of the epoch before. An adversary that withholds every block for one period, 4.5 days at `k = 2160`, lowers the estimate by its share. Every lottery threshold then rises by `1/(1 − α)` for the next epoch, and the honest stake alone fills slots at `f` (`FURTHER.md` G7).

- **Under the worst case the delay weighs more.** `Δ` stays fixed in slots while the chain speeds up. Against a third at 10 s the wait grows from 10.1 to 12.4 hours, and to 12.5 with the nonce of §4. The chance after 18 hours is then `8.4·10^-14`.
- **At short delays and under random delay it shortens the wait.** Against a third at 1 s the wait falls from 4.7 to 3.4 hours. Under random delay it falls from 5.1 to 3.4 hours in the convention's model, and to 4.2 at the engine's deflated growth (`SLOTS.md` K.2, K.7).

**A cap on the correction.** A cap `c` bounds each correction: `D' ≥ (1 − c)·D`. It prices the deflation. But the inference reads a side cut off from the rest as stake that left, and stake that left as a side cut off, so a cap lengthens the density form's protection and its stall after a genuine fall alike. At 18 hours (`SLOTS.md` K.8):

| cap an epoch | density form: a side of 0.3 held back (days) | density form: finality stalls after the active stake halves (days) | depth form: a side of 0.3 held back (days) | a third's deflation: periods withheld | a third's deflation: days withheld |
| --- | --- | --- | --- | --- | --- |
| none | 8.25 | 11.25 | 1.17 | 1 | 4.5 |
| 20 % | 15.75 | 18.75 | 1.17 | 2 | 9.0 |
| 10 % | 23.25 | 26.25 | 1.17 | 4 | 18.0 |
| 5 % | 38.25 | 48.75 | 1.17 | 8 | 36.0 |
| 2 % | 98.25 | 116 | 1.17 | 21 | 94.5 |

- **No cap separates a split from a fall.** At 18 hours the protection against a side of 0.3 lasts 0.73 to 0.89 times the stall after a fall to half, whatever the cap. Each needs the estimate to fall by a set ratio, and the cap sets only how many corrections that takes.
- **The depth form gains nothing from a cap at 18 hours.** A side of a tenth or more makes its `φ + 1` blocks before the first correction.
- **A capped chain stays slow.** After a fall to half the chain fills its slots within 5 % of `f` again after 10.5 days without a cap, 100 at 5 % and 243 at 2 %.

## 8. What else reads `K`

Every rule that waits for finality then waits a fixed time, and each fits at 18 hours (`MAPPING.md` §7; `SLOTS.md` K.3, K.4).

| what | counted in slots | at 18 hours |
| --- | --- | --- |
| `B_imm` and the node's LIB | trail the clock by `K` slots, more while the floor holds them back, stepping through the chain's blocks as each becomes `K` slots old | every block is final 18 hours after its slot, later on a sparse chain |
| the largest rollback | `K` slots, more while the floor holds `B_imm` back | 18 hours on a chain that meets the floor |
| the offline grace period | a node offline longer than `T_offline`, 20 minutes, takes the Bootstrap rule, which freezes `B_imm` | `K` is 54 times `T_offline`, as today |
| the epoch's phases | each phase that waits for finality lasts at least `K`: the snapshot phase, `s` slots, and the lottery constants' lead, `4⌊k/f⌋` | three and four windows long |
| the uncle window | `W·f⁻¹`, 360 slots, stays within `K` | holds |
| the wallet's leader-claim reservations | expire after `K` slots | 18 hours |

**The Bootstrap rule** decides a fork that diverges before `B_imm` by its density.

- Both branches of a fork have one divergence age, so every node holding both chains decides alike. The rule can no longer split the nodes that run it after a split.
- A fork that diverges before `B_imm` is at least `K` slots old, so both chains hold the whole density window whenever it fits in `K`.
- The window must be sized for `(α, ε)`. Today's `s_gen = ⌊k/4f⌋` is 4.5 hours at `k = 2160` and 15 minutes at testnet's `k = 120`, short of the 4.8–4.9 hours a window needs against a third at `1e-9`.
- With the epoch at its length a fork's own nonce and inferred stake take effect 72 hours after its divergence, which caps the window.
- A node whose chain was sparse over the window does not compare, and leaves the split to operators (§6). The density form of the floor is the same test applied to `B_imm`.

**`B_imm` must not move on time alone.** A node that receives no blocks for `K` slots would see `B_imm` reach its own tip, and would come back fixed on whatever tip it held. The floor keeps `B_imm` from passing a block that `φ` occupied slots do not follow, and the Bootstrap rule taken after `T_offline` freezes it.

## 9. The block rate and the delay

Under the worst case a faster block rate needs a longer `K`, so faster blocks are not recommended. A fixed delay costs more block intervals as blocks speed up. The wait that holds `ε = 1e-9`, in hours (`SLOTS.md` K.7; `RATE.md`):

| mean block interval | a quarter, worst case at 10 s | 30 %, worst case at 10 s | a third, worst case at 10 s | a quarter, random delay | a third, random delay |
| --- | --- | --- | --- | --- | --- |
| 30 s, as today | 3.2 | 5.9 | 10.1 | 1.7 | 5.1 |
| 20 s | 3.3 | 6.6 | 12.5 | 1.5 | 5.7 |
| 15 s | 4.2 | 9.5 | 20.4 | 1.4 | 6.2 |

At 15 s blocks 18 hours would no longer hold a third under the worst case.

**Blend's setting sets the delay.** The wait against a third at each Blend setting, at its worst-case delay, beside random delay, in hours (`SLOTS.md` K.7):

| hops | rounds | worst-case delay `Δ` | random delay | worst case |
| --- | --- | --- | --- | --- |
| 1 | 1 | 2 s | 2.9 | 5.1 |
| 1 | 2 | 3 s | 3.1 | 5.5 |
| 1 | 3 | 4 s | 3.3 | 5.9 |
| 1 | 5 | 6 s | 3.6 | 7.0 |
| 1 | 8 | 9 s | 4.3 | 9.2 |
| 1 | 12 | 13 s | 5.7 | 13.8 |
| 3 | 1 | 5 s | 3.9 | 6.4 |
| 3 | 2 | 8 s | 4.7 | 8.4 |
| 3 | 3 | 11 s | 5.1 | 11.2 |
| 3 | 5 | 16 s | 8.0 | 19.6 |
| 3 | 8 | 24 s | 11.6 | 62.7 |

- **Without grinding 18 hours holds a third at every setting whose worst-case delay is 13 s or less,** the specification's setting at 11 s, its 99th percentile rounded up, included, and not at 16 s or 24 s.
- **Hostile relays lengthen the random-delay wait** against a third: relays that hold every block to the sender's deadline by 27 % with one copy, and relays that drop what they carry by 56 % with two copies and 73 % with one (`FURTHER.md` G6). The worst case covers every delay within `Δ`, and none beyond it.

## 10. Specification candidates

1. **`B_imm` counted in slots, with a floor.** `B_imm` is the latest block of the node's chain that is at least `K = ⌊k/f⌋` = 64,800 slots old and that `φ` = 1,019 occupied slots follow: distinct slots holding a block of its chain or an uncle that chain references, as `density_over_slots` of the stake inference counts them. The Online rule ignores a fork that diverges before it. The inference's correction stays uncapped.
2. **The epoch nonce from the smallest contributions** of 25 sub-windows, taken over a contribution bound to its parent's, `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`, and passed through a sequential delay that spans the last sub-window, with a proof published before the nonce is first used.
3. **The Bootstrap rule's density window** sized for `(α, ε)` rather than tied to `k`. The window bears on testnet, which runs `k = 120`.

**How the parameters bind each other.**

- `φ` is the `ε` lower tail of the blocks the honest chain makes in `K` slots while a coalition of `α_max` withholds, under the worst case at `Δ`. A change to `K`, `α_max`, `ε` or `Δ` changes `φ`.
- `K` must hold the worst case at the chosen `f`. A faster block rate needs a longer `K` (§9).
- `K` is at most `s = 3⌊k/f⌋`. The snapshot phase lasts `s` slots and waits for finality, so a larger `K` needs longer epoch phases. Past `4⌊k/f⌋` slots, targets within `K − 4⌊k/f⌋` slots before a cut-off would also race into an epoch whose nonce their private chain set, which no grinding bound covers.
- The uncle window, `W·f⁻¹` slots, and the Bootstrap rule's density window each fit within `K`.
- The nonce's sub-windows span at least 54 hours in all, and its delay spans the last sub-window and a margin.

## 11. Open questions

- **A worst-case bound for the count of occupied slots.** Under the worst case the floor stays at the count of blocks, since no larger lower bound on the honest chain's occupied slots is derived. Such a bound would raise the floor by up to a fifth, and let it separate partitions under the worst case as it does under random delay (§5, §6; `SLOTS.md` K.9).
- **An eclipse of a day.** Under the floor a node cut off with a third of the stake fixes the fork it is shown after 1.05 days, and one cut off with a tenth after 3.5. How long an eclipse an adversary can hold against a node is open.
- **Delay past 15 s.** 18 hours holds a third without grinding up to 15 s of worst-case delay, and not at 20 s. Delivery later than `Δ`, one block in a hundred under honest mixing on the specification's Blend, lies outside the bound.
- **The delay function.** Its sequentiality assumption, the number of delay evaluators an adversary runs, and the formal write-up of the proof (§4).
- **Recovery in a partition.** No density test tells a third's withheld fork from an honest third. Whether any local test can, and what a node should do when its own chain was sparse over the window, is open (§6).
- **Blend's relays.** The share of the relays an adversary can run, which the service declaration prices, not its stake (§9).

## 12. Reproducing the figures

```
cd tools/simulators/finality
make install          # a virtualenv with the TSI engine and the study's package
make test             # every gate
make mutations        # each gate fails on its registered mutation
make all              # every run, phase K's included
make tables           # every table of the notes, from runs/
make check-tables     # each table appears verbatim in a note
```

Phase K has its own targets. `make k1` gives the waits (`finality_sim.slots`), `make k2` what each `K` holds with grinding and a deflated inference, `make k3` eclipses, splits and the floor (`finality_sim.floor`), and `make k5` the nonce's coverage and the other notes read in slots (`finality_sim.slotmap`). `make k7` bounds a wait in the model of Gaži, Ren and Russell on the slot lottery (`finality_sim.waitbound`; it needs `make a1`, `make k1`, `make k2`, `make k5`, `make b6` and `make designs`), `make k8` caps the inference's correction (`finality_sim.cap`), and `make k9` reads the floor on occupied slots. The nonce's bound comes from `make designs` (H.2), and the deflation from `make further` (G7).

The notes carry each result with its gate: `SLOTS.md` (phase K), `DESIGNS.md` (H.1, H.2), `SETTLEMENT.md` (B6, B7), `FURTHER.md` (G6, G7), `MAPPING.md` §7 and `RATE.md`. The study's report reads every route, this one among them: [`README.md`](README.md).
