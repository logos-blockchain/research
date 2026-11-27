# The split of 60 hours

Date: 2026-11-27.

This note supports the logos-lips RFC "Cryptarchia: Shorten the epoch to 60 hours", on the branch `Bedrock-RFC-Shorter-Epoch`. The RFC sets two phases of $`4K`$ and $`2K`$ slots, with $`K`$ = 36,000. The stake inference reads a window of $`4K`$ and learns at `beta` = 1/2. Section 1 gives the source of each figure of the RFC's Discussion. Section 2 corrects `../schedule/SCHEDULE.md` and `../REVIEW.md`. Section 3 lists the files of this folder and says how to rerun them.

Conventions:

- "Line n" is a line of the output that the same row or sentence names. A file without a folder is in this folder.
- The states of the $`K`$ row are those of REVIEW.md 5.9. The second reading is REVIEW.md 5.9's reading of the second disturbance before the inference corrects. In it 63 % of $`D`$ builds.
- $`S/D`$ is the stake that builds over the inferred stake $`D`$.
- `c15(r)` and `c10(r)` are the chances that a coalition of 30 % displaces a block after $`K`$ slots at $`S/D = r`$, with every block 15 or 10 slots late. They come from the study's wait bound, through `displace.py`.
- "Today" is the specification of 180 hours: phases of 54, 54 and 72 hours, a window of 108 hours and `beta` = 1.

## 1. Where each figure of the RFC comes from

The rows follow the RFC's sections in order. A closed form is a source when the row gives it.

### 1.1 What 60 hours hold

| Figure | Source |
| --- | --- |
| 13.80 % and 10.20 % today | `../schedule/out_costs.txt`, line 2: the least building share for phase 1 (54 h) and phase 3 (72 h), at 15 s. |
| 19.02 % for the snapshot phase | `../schedule/out_costs.txt`, line 5: the least share for a phase of 40 h. The share depends only on the phase's length. |
| 41.35 % for the last phase | `../schedule/out_costs.txt`, line 8: the least share for a phase of 20 h. |
| 63 %, with every block 10 s late | REVIEW.md 5.9, second reading: $`x`$ = 0.63, the second disturbance alone, at the baseline delay of 10 slots. |
| about 47,600 slots, 13.2 hours | `out_r3_final.txt`, line 14: 47,599, the least gap at `1e-9` that counts a coalition's private lead, second reading. The cost of 2.6, at most one $`d`$ of 15 slots, is not in it. 47,614/3,600 still rounds to 13.2. The law of the lead matters a little: other laws built from SURVIVAL's $`M`$ give 47,546 to 47,671 slots, by the independent check of 2026-11-27. All round to 13.2 hours. |
| 20 hours is 1.5 times that | 72,000/47,599 = 1.51. |
| at most $`f^2`$, about 0.11 % | REVIEW.md 5.5 (4): at $`G = K`$ the chance is at most $`p^2`$, and $`p \le f`$. $`f^2`$ = 1/900. |
| $`2K - 1`$ | REVIEW.md 10.1, rule J, after GENESIS 7.1. |
| $`K - 1`$ | `../proofs/genesis-step2/STEP2.md`. |
| $`6 s_{gen}`$ = 27 hours | $`s_{gen}`$ = 16,200 slots (REVIEW.md 1.2), so $`6 s_{gen}`$ = 97,200 slots. |
| delays above two slots | REVIEW.md 8.5: the theorem's hypotheses hold for $`\Delta \le 2`$. |
| about 26 hours after the cut-off | `out_betacost.txt`, line 10: 95,194 slots at $`S/D`$ = 0.3 and 15 s, which is 26.4 h. |
| 6 hours after their first use | 26.4 h − 20 h. |
| $`3 \cdot 10^{-15}`$ | `out_genesis_u.txt`, line 2: the chance after 72,000 slots at $`S/D`$ = 0.3 and 15 s. |

### 1.2 Why the Buffer phase can go

| Figure | Source |
| --- | --- |
| about 65,000 slots, 18 hours | `out_r2_repair.txt`, line 4: 64,750, the least phase on the commit route for a total of `1e-9` on a grid of 250 slots, second reading. It is the largest of the five states (lines 1 to 5). The RFC rounds it up, since the cost of 2.6 is not in it. |
| 144,000 | $`4K`$. |
| 17,709 | REVIEW.md 9.4 (`../out_08_buffer.txt`, line 149): $`w_B`$ in the second reading. The first reading needs 17,268 (line 142). 2.8 covers a span that starts at the epoch's first slot. |
| 971 | REVIEW.md 9.2 (`../out_14_bracket.txt`, line 12), second reading. The first reading gives 903 (line 9). |

### 1.3 The split of 60 hours

The rows give `2K + 4K`, `3K + 3K` and `4K + 2K` in that order.

| Row | Figures | Source |
| --- | --- | --- |
| a halt within one window takes $`S/D`$ past 1.094 | 3.4, 5.2, 6.9 h | `out_betacost.txt`, lines 65, 72 and 79. Closed form: a halt in one window that takes $`S/D`$ past $`L`$ lasts $`(1 - 1/L)/\beta`$ times the window. |
| income a coalition of 30 % gives up | 5.0, 28.7, 52.5 % | `out_printed.txt`, part 4. With $`D`$ on the honest stake the coalition's stake wins $`q(0.3/0.7)/q(0.3)`$ = 1.4255 times as often a slot, so it keeps 1.4255 times the last phase's share of the epoch. `out_genesis_u.txt`, line 5, gives 14, 36 and 57 % at 10 s: it uses the chain's growth rate with every block 10 s late, not the coalition's win rate. The RFC uses the win rate. |
| a change is first corrected | 100, 90, 80 h later | The last phase plus one epoch. |
| the nonce is known before the epoch by | 40, 30, 20 h | The last phase. |
| the last phase is final in time down to | 19.02, 26.05, 41.35 % | `../schedule/out_costs.txt`, lines 5, 6 and 8: phases of 40, 30 and 20 h. |
| a halt the last phase absorbs | 26.8, 16.8, 6.8 h | (last phase − 47,599)/3,600, with 47,599 from `out_r3_final.txt`, line 14. |

### 1.4 The stake inference

| Figure | Source |
| --- | --- |
| 40 hours in place of 108 | $`4K`$ = 144,000 slots. Today `PERIOD` is 388,800 slots (REVIEW.md 1.2). |
| $`D' = D \cdot ((1 - \beta) + \beta N/(P f))`$ | REVIEW.md 7.2, with `beta` held as a ratio. |
| $`(1 - \beta) \cdot D`$ | The rule at $`N = 0`$. |
| $`1/(1 - \beta y)`$ | The rule at $`N = (1 - y) P f`$. |
| 2.097 at 10 s | `out_displace.txt`, line 27: at $`S/D`$ = 2.097 and 10 s the wait at `1e-9` is 9.994 h. `../../floor/out_least_waits_edges.txt`, line 8, gives the same edge. |
| 1.094 at 15 s | `out_displace.txt`, line 11: at 1.094 and 15 s the wait is 9.999 h. |
| at most twice $`D`$ | $`1/(1 - 1/2)`$ = 2 (`out_betacost.txt`, line 79). |
| 4.6 % of room | 1 − 2/2.097. |
| `2·10^-12` and `5·10^-9` | `out_printed.txt`, part 8: the stationary chance that $`S/D`$ exceeds 2.097/2 at a window of $`4K`$ and `beta` = 1/2, `2.24e-12` under the rule as printed and `5.17e-09` under the exact rule. |
| 2.86 times $`D`$ | 2/0.7. A coalition that withholds keeps $`D`$ on the honest stake, 0.7 of the total, and a window without blocks then halves $`D`$. |

What one window of lost blocks does. The rows give today, `3K + 3K` at 3/4, `4K + 2K` at 1 and `4K + 2K` at 1/2 in that order.

| Row | Figures | Source |
| --- | --- | --- |
| $`S/D`$ after a window without blocks | unbounded, 4, unbounded, 2 | $`1/(1 - \beta)`$. `out_betacost.txt`, lines 81, 70, 74 and 79. |
| a halt takes $`S/D`$ past 2.097 from | 56.5 h, 20.9 h, 20.9 h, never | The same lines. |
| a halt takes $`S/D`$ past 1.094 from | 9.3, 3.4, 3.4, 6.9 h | The same lines. |
| largest $`S/D`$ after a halt of 24 h | 1.29, 2.50, 2.50, 1.43 | `out_halt.txt`, lines 134, 33, 34 and 39. |
| $`S/D`$ after a coalition of 30 % withholds one window, under the specification's rule | 1.41, 1.27, 1.41, 1.16 | `out_printed.txt`, part 3, from $`D`$ at rest. The exact rule gives 1.42, 1.29, 1.42 and 1.17 (`out_extra.txt`, lines 12 to 15). |

| Figure | Source |
| --- | --- |
| a halt of up to 56 hours | `out_betacost.txt`, line 81: 56.5 h. |
| its floor of one unit | REVIEW.md 7.2: the rule returns at least 1. |
| two windows need a halt of at least 100 hours | window, last phase and window: 40 + 20 + 40 h. |
| 4 times $`D`$ | $`(1/(1 - 1/2))^2`$. |
| 0.83 % and 0.87 % | `out_split_chain.txt`, lines 7 and 1, the rule as printed. |
| about $`2 \cdot 10^{-33}`$ | `out_split_chain.txt`, line 7: `1.914e-33`. `out_simulate_branch_4k2k.txt`, line 7, gives `1.980e-33` by importance sampling. |
| $`2.21 \cdot 10^{-10}`$ under the specification's rule, the same today | `out_printed.txt`, part 1: `2.209e-10` at 60 hours and `2.210e-10` today. |
| $`2.53 \cdot 10^{-10}`$ under an exact rule | `out_extra.txt`, lines 5 and 2: `2.525e-10` and `2.527e-10`. |
| $`2.50 \cdot 10^{-10}`$ with $`D`$ exact | `out_extra.txt`, line 1: `c15(1)` = `2.504e-10`. |
| 1.03 % above | `out_split_chain.txt`, line 7: mean $`D/S`$ 1.01027. REVIEW.md 7.4. |
| 0.13 % at Blend's design delays | `out_forkloss2.txt`, line 2: 3 hops uniform to 3 s, mean 9.3 s, loss 0.1315 %. Its last gossip leg has a mean of 1.21 s and an sd of 0.26 s. They come from `out_gossip.txt`: the mean distance, line 1, and 0.36/√2, line 2. |
| 0.26 % at 15 s | `out_forkloss2.txt`, line 5: mean 15.0 s, loss 0.2574 %. |
| about 7 % at 15 s | `out_forkloss3.txt`, line 8: 6.753 %. `out_forkloss.txt`, line 15: 6.98 % where each leader breaks ties at random. |
| about $`7.5 \cdot 10^{-10}`$ | `out_exposure.txt`, line 1: `c15(1.076)` = `7.515e-10`. 1.076 is 1/0.929, the $`D/S`$ of `out_forkloss.txt`, line 15, where each leader breaks ties at random (loss 6.98 %). At 6.753 % $`D/S`$ is 0.9313 (`out_forkloss3.txt`, line 8), so `c15` is lower there. The independent check puts 6.8 % at $`S/D`$ 1.074 under the exact rule (`7.3e-10`) and 1.063 under the rule as printed (about `6.2e-10`), so `7.5e-10` is the upper value. |

What a learning rate of 1/2 costs. The rows give today, then `4K + 2K` at 1/2.

| Row | Figures | Source |
| --- | --- | --- |
| a change is first corrected | 252 h, 80 h | The last phase plus one epoch: 72 + 180 h and 20 + 60 h. |
| after the stake halves, $`D`$ is off by | 0.8 % at 252 h; 50, 25, 13 % at 80, 140, 200 h | `out_printed.txt`, part 7, the mean path: 1.0084; 1.5042, 1.2549, 1.1292. `out_simulate_branch_4k2k.txt`, lines 13 and 11, gives the mean error with the noise: 1.2 % today, and the same 50, 25 and 13 %. |
| after it falls by a tenth | 0.2 %; 5.6, 2.9, 1.5 % | `out_printed.txt`, part 7: 1.0017; 1.0564, 1.0286, 1.0146. |
| after the stake doubles, $`S/D`$ stays above 1.094 until | the correction at 252 h; the third correction, at 200 h | `out_printed.txt`, part 7: $`D`$ over its fixed point is 0.7418, 0.8680 and 0.9327, so $`S/D`$ is 1.334, 1.140 and 1.061 after one, two and three corrections. |
| a coalition of 30 % withholds every block | one window, withholding 3,894 wins; within 22, 11, 6 and 3 %, withholding 1,442, 1,692, 1,854 and 1,948 wins | `out_printed.txt`, part 5, wins from $`D`$ at rest. `out_simulate_branch_4k2k.txt`, lines 30 and 28: $`D`$ over the honest stake is 1.229, 1.121, 1.067 and 1.039, against the fixed point 1.0103. The simulation's "wins given up per window" is the first window from $`D`$ equal to the stake, not each window. |
| daily growth that $`K`$ holds at 15 s | 1.32 %, 2.03 % | `out_printed.txt`, part 2, the rule as printed. The exact rule gives 1.18 % and 1.82 % (`out_extra.txt`, lines 7 and 10). |
| noise of $`D`$ | 0.87 %, 0.83 % | `out_split_chain.txt`, lines 1 and 7. |
| a chain misses the floor of 689 | $`1.4 \cdot 10^{-8}`$, $`1.3 \cdot 10^{-8}`$ | `out_split_chain.txt`, lines 1 and 7. |

| Figure | Source |
| --- | --- |
| 13.3 hours, then 10.5 hours | `out_betacost.txt`, line 40. Line 35 gives 13.3 h at `beta` = 1. |
| 0.46, 0.63, 0.76 and 0.86; 0.98 at `beta` = 1 | `out_printed.txt`, part 6, the rule as printed. The exact rule gives 0.46, 0.63, 0.77, 0.87 and 0.99 (`out_betacost.txt`, lines 16 and 11). |
| $`2.5 \cdot 10^{-9}`$ with $`f`$ exact | `out_split_chain.txt`, line 8: `2.513e-09`. |

### 1.5 The epoch nonce

| Figure | Source |
| --- | --- |
| 48.7 and 146 cut-offs a year | `../schedule/out_costs.txt`, lines 2 and 6. |
| 5.6 % and 16.7 % of targets | `../schedule/out_costs.txt`, lines 2 and 6. They are $`K/E`$ (REVIEW.md 6.2). |
| 0.70 %, 0.82 %; 1.21 %, 1.43 % | `../schedule/out_gain.txt`, lines 5, 14, 7 and 16, at $`2^{16}`$ nonces. |
| 2,230 and 3,870 blocks a year | `../schedule/out_gain.txt`, lines 5 and 7. |
| 24.7 to 27.9 % | `../../nonce/today_states.out`, lines 18 to 24: the shares that 10 hours prove with today's nonce, from 0.247 at 15 s to 0.279 with no disturbance. REVIEW.md 1.4, item 6, cites the same from RFC-533. |

### 1.6 New stake and the other readers of the epoch

| Figure | Source |
| --- | --- |
| 60 to 120 hours; 180 to 360 | One to two epochs. `../schedule/out_costs.txt`, lines 6 and 2. |
| 7,200 expected blocks | 216,000 slots times $`f`$. |
| $`\rho`$ = 1/600 | `../schedule/out_costs.txt`, line 19. |
| 43,200,000 | 600 · 10 · 7,200. Today 200 · 10 · 21,600. |
| 21.6 % a year | $`1 - (1 - 1/600)^{146}`$. Today $`1 - (1 - 1/200)^{48.7}`$. |
| 216,000 rounds; 1/3 of today's quota; 3 times as often | One round a slot. 216,000/648,000. 180 h/60 h. |
| about 111 MB | $`(216000 + 30) \cdot (1 + 130/30) \cdot 3 \cdot 32`$ = 110,607,360 bytes, the RFC's Details, section 4. |
| 0.19 and 0.89 per epoch | `../schedule/out_lottery.txt`, lines 6 and 2, at 10,000 core nodes. |
| 0.48 over 180 hours | $`1 - (1 - 0.1936)^3`$. |
| 8,192 and 16,384; 262,144 and 972,000 | `../schedule/out_lottery.txt`, lines 6 and 2. |
| 60 hours in place of 180; 20 hours in place of 72 | The epoch; the last phase. |
| 7,200 blocks in place of 21,600 | `../schedule/out_costs.txt`, lines 6 and 2. |
| $`\Delta_t`$ = 1/146 and $`f`$ = 7200 | 146 epochs a year; 7,200 blocks an epoch. |
| a factor of 2; 12.5 %; $`6k/f`$; 648,000 | Values of the specifications, unchanged by the RFC. |

### 1.7 Alternatives

| Row | Figure | Source |
| --- | --- | --- |
| Today | 56 h | `out_betacost.txt`, line 81: 56.5 h. |
| Today | 360 h, 252 h | Two epochs. 72 + 180 h. |
| `3K`, `3K`, `4K` | a 60-hour window; 19.02 % | `../schedule/out_costs.txt`, line 3. |
| `3K`, `3K`, `4K` | 31.4 h | $`(1 - 1/2.097) \cdot 60`$ h. |
| `3K + 3K`, 3/4 | 26.05 %; 30 hours | `../schedule/out_costs.txt`, line 6; the last phase. |
| `3K + 3K`, 3/4 | 20.9 h; 28.7 % against 52.5 % | `out_betacost.txt`, line 70; `out_printed.txt`, part 4. |
| `4K + 2K`, 1 | 80 h; 4.01 %; 20.9 h | 20 + 60 h; `out_printed.txt`, part 2, the rule as printed; `out_betacost.txt`, line 74. |
| `4K + 2K`, 1, a fall of at most a quarter | 4/3; one step; 12 % at 140 h | `out_rules.txt`, line 9: an empty window gives 1.33; after a doubling 1.017 and then 1.000; after a halving $`D/S`$ is 1.50, 1.12 and 1.00. |
| `2K + 2K` | 40 to 80 h; 41.35 %; 25 %; 4,800 blocks | `../schedule/out_costs.txt`, line 8. |
| `2K + 2K` | about 7,000; 1.48 % | 72,000 − 65,000, with 65,000 as in 1.2; `../schedule/out_gain.txt`, line 8. |
| `1.5K + 2K` | 54,000 | 1.5 · 36,000. |
| `K`, `K`, `K` | 0.11 % | $`f^2`$, as in 1.1. |
| $`\rho`$ at 1/200 | 3 times; 51.9 % | 600/200; $`1 - (1 - 1/200)^{146}`$. |

## 2. Corrections to SCHEDULE.md and REVIEW.md

These corrections come from the review of `4K + 2K` of 2026-11-25.

**2.1 SCHEDULE.md 3.4.** "All reduce to one event" holds for grinding only. A coalition can choose between two snapshots without that event.

- A coalition wins a slot just before $`s_0`$. It makes two blocks of that one win, with the same $`\rho`$ and two bodies that create different notes. No rule forbids two blocks of one win.
- It sends each block first to one half of the honest stake. A tie keeps each half on the block it holds.
- It keeps both branches alive. It matches each honest block of one branch within $`\Delta`$, by an honest win or a win of its own on the other branch.
- When the last honest block before the cut-off is public, it knows the nonce of each branch, and it picks one.

3.3 still holds on each branch, so the coalition cannot grind its notes. 2.2 gives the condition that ends the choice.

**2.2 SCHEDULE.md 3.5.** The end time of 3.5 is wrong.

- The choice between snapshots opens at the last honest block of the final chain before the cut-off.
- It closes when the split is lost, or when a block of the epoch becomes immutable at an honest node.
- So the snapshot must be final at every honest node before the last honest block of the phase.
- In the states of the $`K`$ row a block of the epoch becomes immutable between 36,000 and 47,028 slots after $`s_0`$, except with `1e-9` (2.7). In the second reading the bound is 47,599.
- The last honest block before the cut-off lies at most 17,268 slots before it, except with `1e-9` (REVIEW.md 9.4), and at most 17,709 in the second reading.

**2.3 SCHEDULE.md 3.6.** 46,910 is not proved. Two bounds prove the condition of 2.2.

- The commit route of `r2_repair.py`. The snapshot is final by a slot $`s_0 + g`$, and the final chain holds an honest block in the last $`L_1 - g`$ slots of the phase. The script takes the least sum of the two chances over $`g`$. It does not use the study's settlement bound $`U`$. The least $`L_1`$ for a total of `1e-9`, on a grid of 250 slots, is 55,750, 63,000, 61,500, 64,750 and 50,250 slots in the five states (`out_r2_repair.txt`, lines 1 to 5). The largest is 64,750, in the second reading.
- A sum with each term at `1e-9`, so with a total of `2e-9`: 47,028 + 17,268 = 64,296 slots, and 47,599 + 17,709 = 65,308 in the second reading. The first term is the least gap of 2.7, and the second is $`w_B`$ (REVIEW.md 9.4).

The settlement route of `r2_repair.py` gives shorter phases. It rests on $`U`$, which this folder does not check. A phase 1 of 144,000 slots meets both bounds.

**2.4 SCHEDULE.md 3.7.** The window need only end at or before the cut-off. $`D`$ is read at the cut-off, and REVIEW.md 4.2 and 4.3 need only that every slot of the window is before the read slot. The rest of 3.7 stands.

**2.5 SCHEDULE.md 4.1.** The standard of 4.1 does not track the risk, and it no longer sets `beta`.

- 4.1 bounds the chance per epoch that the noise of $`D`$ takes $`S/D`$ past 1.094.
- $`K`$ is sized by the chance per block that a coalition of 30 % displaces a block. Averaged over the noise of $`D`$, that chance is `2.566e-10` at `4K + 2K` with `beta` = 1 and `2.525e-10` with `beta` = 1/2 under the exact rule, against `2.504e-10` with $`D`$ exact (`out_extra.txt`, lines 4, 5 and 1). Under the rule as printed it is `2.243e-10` and `2.209e-10` (`out_printed.txt`, part 1).
- Between the same two rates, the chance of 4.1 falls from `4.2e-10` to `1.2e-27` under the exact rule (`out_split_chain.txt`, lines 6 and 8).
- The bound on lost blocks sets `beta`. One window without blocks takes $`S/D`$ to $`1/(1 - \beta)`$. $`K`$ holds 30 % at 10 s only up to 2.097 (`out_displace.txt`, line 27). So `beta` must not exceed $`1 - 1/2.097`$ = 0.523.
- At `beta` = 1/2 a window without blocks takes $`S/D`$ to 2 (`out_betacost.txt`, line 79).

**2.6 REVIEW.md 5.3.** Delays that vary up to $`d`$ cost one $`d`$. Step 2 of 5.3 rests on M2: the next block of the chain is in the first marked slot after $`s + d`$. When delays vary up to $`d`$, the chain can keep a block made up to $`d`$ slots after that marked slot, so $`s_i \le \tau_i`$ fails. Heights still grow. The bound of 5.4 then holds with $`G - d`$ in place of $`G`$, as in 5.10.

**2.7 REVIEW.md 5.4, 5.9 and 10.2.** $`G^*`$ leaves out a coalition's private lead.

- 5.4 holds in $`M(p, d)`$, which has no coalition.
- A coalition can hold a private chain whose blocks all lie before the cut-off. It releases the chain when an honest block reaches its height. The first $`L`$ blocks of the gap then leave the chain, where $`L`$ is its lead at the cut-off.
- `r3_final.py` bounds the chance against such a coalition. At its first use a node's chain holds at least $`N(G - 2\Delta) - M_{pre}`$ blocks of the gap. $`N(m)`$ is the greedy count of honest wins with gaps of at least $`\Delta + 1`$ in $`m`$ slots, and $`M_{pre}`$ is the coalition's lead (`walk.py`).
- The floor part is $`\Pr[N(G - 2\Delta) - M_{pre} \le \phi]`$.
- The age part is $`\Pr[M_{pre} + M_{post} + 1 \ge N(y_0 - \Delta)] + \Pr[M_{pre} \ge N(z_0 - 2\Delta)]`$, for any $`y_0 + z_0 = G - K + 1`$.
- The least $`G`$ at `1e-9` rises from 43,460, 46,910, 44,667 and 47,483 to 43,547, 47,028, 44,779 and 47,599 slots. That is 87 to 118 slots more (`out_r3_final.txt`, lines 11 to 14).
- With $`D`$ equal to the honest stake online it rises from 36,726 to 39,375 (line 15). The script's split of the age part is loose in that state.
- The largest value is 47,028 slots, and 47,599 in the second reading. It replaces $`G^*`$ in REVIEW.md 5.9 and 10.2, in SCHEDULE.md 2 and 3.6, and in `../proofs/genesis-step2/STEP2.md` 1.2. Phases of $`2K`$ and $`4K`$ exceed it.

**2.8 SCHEDULE.md 3.6 and REVIEW.md 9.4.** A span that starts at $`s_0`$ breaks assumption A2 of `../proofs/survival/SURVIVAL.md`. The last honest block before $`s_0`$ lies in the previous epoch, under another $`D`$ and another nonce. Another bound covers that span at a cost of at most 1.2 times: at most `3.2e-10` at $`w_B`$, and at most `7e-26` at 46,910 slots. Both stay below `1e-9`, so no length changes. The review of 2026-11-25 computed these chances. This folder does not recompute them.

## 3. Files and how to rerun them

Run each script with the finality study's interpreter, from any folder. It finds its imports and inputs from its own location, and prints its result.

    cd tools/simulators/finality
    .venv/bin/python -B slot-finality/epoch/split/run_all.py

`run_all.py` reruns every script in the order of the table and stores each output as `out_<name>.txt` beside it.

- `displace.py` runs first. `exposure.py` reads `out_displace.txt`, and `halt.py`, `betacost.py`, `rules.py` and `extra.py` import `exposure.py`.
- `r2_repair.py` reads the curves $`U`$ that `../proofs/genesis/g07_states.py` caches in `../proofs/genesis/.cache`. `run_all.py` runs `g07_states.py` first when a curve is missing, and discards its output.
- `displace.py` and `genesis_u.py` cache in `.cache` beside them. Git ignores it.
- Times are those of one run on a machine with 14 cores.

| Script | What it computes | Output | Time |
| --- | --- | --- | --- |
| `displace.py` | `c15`, `c10`, the same at 12 s, and at 10 s with a tenth of the honest stake offline, by $`S/D`$, from the study's wait bound; the wait at `1e-9` | `out_displace.txt` | 4 min, 4 workers |
| `exposure.py` | the chance per block over the noise of $`D`$, by split and `beta`; a step of the stake; a coalition that withholds one window; steady growth | `out_exposure.txt` | 35 s |
| `halt.py` | what a halt, or half of the stake offline, does to $`D`$, by split and `beta` | `out_halt.txt` | 1 s |
| `betacost.py` | genesis, a fall of the stake, growth, and the halt in one window that takes $`S/D`$ past 1.094, 1.6 and 2.097 | `out_betacost.txt` | 1 s |
| `rules.py` | `beta` against a bound on the fall of $`D`$, at `4K + 2K` and `3K + 3K` | `out_rules.txt` | 4 s |
| `genesis_u.py` | at genesis, the chance that a fork from before the first cut-off is alive at the first use; the income a coalition gives up | `out_genesis_u.txt` | 25 s |
| `forkloss.py` | the wins that $`D`$ does not count, by delay, with ties broken the same for all or at random | `out_forkloss.txt` | 14 s |
| `forkloss2.py` | the same with an arrival time per block and leader, Blend's delays among them | `out_forkloss2.txt` | 11 s |
| `forkloss3.py` | the same when deliveries are timed to keep the honest leaders split | `out_forkloss3.txt` | 4 s |
| `gossip.py` | the last gossip leg of the network that `forkloss2.py` takes. It imports `tools/simulators/tsi/tsi-sim-pernode/src`. | `out_gossip.txt` | 1 s |
| `walk.py` | the laws of the coalition's lead and of the honest count, which `r3_final.py` and `r2_repair.py` import | none | |
| `r3_final.py` | REVIEW.md 5.4 as printed, and the bound against a coalition with a lead (2.7) | `out_r3_final.txt` | 2 s |
| `r2_repair.py` | the condition of 2.2 at a phase 1 of 72,000, 108,000 and 144,000 slots, by the commit route and the settlement route, and the least phase by each | `out_r2_repair.txt` | 10 s |
| `split_chain.py` | the noise of $`D`$ and the floor premise at a window of $`4K`$, with `../schedule/chain.py` | `out_split_chain.txt` | 15 s |
| `extra.py` | the chance per block over the noise of $`D`$, the growth that $`K`$ holds, and a coalition that withholds one window, beside today and `3K + 3K` | `out_extra.txt` | 5 s |
| `printed.py` | the figures of the stake inference under the rule as printed: the chance per block over the noise, growth, one withheld window, the income a coalition gives up, the wins of a lasting deflation, the launch, the mean path after a step, and the room below the total active stake | `out_printed.txt` | 1 min |
| `../schedule/simulate.py` | the rule in integers at a window of $`4K`$: `WINDOW=144000 EPOCH_H=60 GAP_H=20 BETAS=1,1/2`, `branch A B C D` | `out_simulate_branch_4k2k.txt` | 31 s |

Each output was rerun here on 2026-11-27 and compared with the run that the RFC's figures came from.

- Every number matches. Only the lines that print a run's time differ, in `out_forkloss.txt`, `out_forkloss2.txt` and `out_simulate_branch_4k2k.txt`. The Monte Carlo runs use fixed seeds.
- The earlier `out_displace.txt` ended with a line from the shell that ran it. This run does not print it.
- `r3_final.py` and `r2_repair.py` had no stored output. Their figures match the review's write-up. The write-up gives the floor and age parts at $`G`$ = 72,000 rounded up, by at most 10 %.
- `gossip.py` gives the same output with the package of this branch as with that of the branch `tsi-cousins`, for which it was written.
