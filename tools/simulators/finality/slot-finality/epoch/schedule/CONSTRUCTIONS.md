# Epoch constructions and the learning rate

Date: 2026-11-20.

This note compares three constructions of the epoch at a finality window $`K`$ of 36,000 slots (10 hours). The first is the one the logos-lips branch `Bedrock-RFC-Shorter-Epoch` specifies at `b6dfd7e6`, $`3K + 3K`$. The other two keep a Buffer phase: $`2K + 2K + 2K`$ and $`2.5K + K + 2K`$. The note also derives the learning rate `beta` of the stake inference for each. The rules, the method and the labels are those of SCHEDULE.md, and REVIEW.md, section 2, defines the labels. Section 7 lists the files.

## 1. What the protocol reads of a schedule

**1.1 (Cited).** The protocol reads three things of epoch $`ep - 1`$, whose first slot is $`s_0`$ (protocol at `b4c987d8`, the base: 149–159, 197, 225–237; at `b6dfd7e6`: 150–159, 197, 225–237):

- the snapshot of the note commitments, at $`s_0`$;
- the cut-off, the first slot of the Lottery Constants Finalization phase, where $`\eta^{ep}`$ and $`D^{ep}`$ are read;
- the window of the inference, the first `PERIOD` slots of the epoch, which ends at the cut-off (REVIEW.md 10.1, I).

**1.1a (Cited).** The other specifications at `b6dfd7e6` read the epoch's length, its boundaries, `PERIOD`, or the cut-off as an event:

- Proof of work fixes `difficulty_blend` for epoch $`N`$ at the snapshot that fixes epoch $`N`$'s nonce, from the blocks of epoch $`N - 2`$ (proof-of-work 114, 218). Blend (697) and the genesis block (325) read the same value.
- SDP takes its snapshot at the start of an epoch (bedrock-service-declaration-protocol 131). Proof of work refills its pool at each epoch boundary (183).
- Blend, proof of work and block rewards read the epoch's length, and the inference reads `PERIOD`.

None reads the boundary between the first two phases. A reader of the cut-off reads blocks that are older than the cut-off by at least $`c \ge G^*`$, so its value is final in time in every construction here.

**1.2 (Proved from 1.1 and 1.1a).** Nothing reads the boundary between the Stake Distribution Snapshot phase and the Buffer phase. A schedule of phases $`L_1 + L_2 + L_3`$ therefore runs exactly as the two-phase schedule $`(L_1 + L_2) + L_3`$ with the same window. $`2K + 2K + 2K`$ runs as $`4K + 2K`$, and also as $`3K + K + 2K`$. $`2.5K + K + 2K`$ runs as $`3.5K + 2K`$.

**1.3 (Cited).** The split of the slots before the cut-off decides only which argument covers the nonce:

- B of REVIEW.md 10.1, which is the Buffer phase's own text. Phase 1 lets the snapshot finalize, which needs $`L_1 \ge G^*`$. Phase 2 then holds an honest block, which needs $`L_2 \ge w_B`$.
- SCHEDULE.md 3.6, with no Buffer phase. The chain holds an honest block between the snapshot slot and the cut-off, and $`L_1 + L_2 \ge \max(G^*, w_B)`$.

Every construction here meets both (section 2). As protocols they differ only in three things: the epoch $`E`$; the cut-off $`c = L_1 + L_2`$, which is also the window; and the learning rate.

| Construction | Epoch $`E`$ | Cut-off and window $`c`$ | Phase 3, $`E - c`$ |
| --- | --- | --- | --- |
| $`3K + 3K`$ | $`6K`$, 60 h | $`3K`$, 30 h | $`3K`$, 30 h |
| $`2K + 2K + 2K`$ | $`6K`$, 60 h | $`4K`$, 40 h | $`2K`$, 20 h |
| $`2.5K + K + 2K`$ | $`5.5K`$, 55 h | $`3.5K`$, 35 h | $`2K`$, 20 h |

**1.4 (Proved).** In an epoch of $`6K`$, J asks for a phase 3 of at least $`2K - 1`$ slots, so the cut-off is at most $`4K + 1`$. The window of $`2K + 2K + 2K`$ is one slot shorter than the longest that J allows at that epoch.

## 2. The rules each keeps

Computed: `out_constructions.txt`, part 1, with $`G^*`$ = 46,910 and $`w_B`$ = 17,268, the largest values over the $`K`$ row (REVIEW.md 5.9, 9.4). A share is the least share of $`D`$ that must build for the value to be final in time, with every block 15 slots late.

| Construction | Snapshot: final in time at | Phase 3: final in time at | J: phase 3 less $`2K - 1`$ | Honest block |
| --- | --- | --- | --- | --- |
| $`3K + 3K`$ | 26.05 % (cut-off $`3K`$) | 26.05 % | +36,001 slots | phase 1: 108,000 ≥ 46,910 |
| $`2K + 2K + 2K`$ | 41.35 % (phase 1, $`2K`$); 19.02 % (cut-off $`4K`$) | 41.35 % | +1 slot | phase 2: 72,000 ≥ 17,268 |
| $`2.5K + K + 2K`$ | 31.96 % (phase 1, $`2.5K`$); 21.98 % (cut-off $`3.5K`$) | 41.35 % | +1 slot | phase 2: 36,000 ≥ 17,268 |

- The worst state of the $`K`$ row has 70 % of $`D`$ building. Every construction keeps S and L in every state.
- A phase 3 of $`2K`$ meets J's $`2K - 1`$ with one slot to spare, for every $`K`$. J is a condition of GENESIS's argument, not a proven necessity (REVIEW.md 10.1). The weaker condition $`K - 1`$ in `../proofs/genesis-step2/STEP2.md` has not been reviewed. Under it the margin would be 36,001 slots.
- Each epoch is at least $`2K`$ and at least $`6s_{gen}`$ = 97,200 slots (SCHEDULE.md 2).
- Under B the snapshot's share for $`2K + 2K + 2K`$ is 41.35 %. The same protocol written as $`3K + K + 2K`$ gives 26.05 %. Phase 3 stays at 41.35 % either way, and the 70 % of the $`K`$ row bounds every share (`out_constructions.txt`, part 1).

## 3. What does not depend on the learning rate

Computed: `out_constructions.txt`, parts 1 and 2. The gain is that of `gain.py` and REVIEW.md 10.6.

| | $`3K + 3K`$ | $`2K + 2K + 2K`$ | $`2.5K + K + 2K`$ |
| --- | --- | --- | --- |
| Targets that meet two nonces | 16.67 % | 16.67 % | 18.18 % |
| Gain of a coalition of 30 % that chooses among at most $`2^{16}`$ nonces, 10 s and 15 s | 1.21 %, 1.43 % | 1.21 %, 1.43 % | 1.27 %, 1.49 % |
| New stake waits | 60 to 120 h | 60 to 120 h | 55 to 110 h |
| First use of a correction after a change, $`E + L_3`$ | 90 h | 80 h | 75 h |
| Wins a coalition of 30 % gives up per window it withholds | 1,093 | 1,457 | 1,275 |
| Expected blocks an epoch | 7,200 | 7,200 | 6,600 |
| Proof-of-work rate $`\rho`$ = `NUM`/`DEN` that keeps the reward of a claim | 1/600 | 1/600 | 11/7200 |
| Share of the epoch in which the next epoch's nonce is known (phase 3) | 50 % (30 h) | 33 % (20 h) | 36 % (20 h) |

- Proof of work holds $`\rho`$ as `EPOCH_POW_DISTRIBUTION_RATE_NUM` / `EPOCH_POW_DISTRIBUTION_RATE_DEN` (proof-of-work 139–140, Cited). Each rate pays out 1/4,320,000 of the pool per expected block. At 55 hours, `NUM` = 11 and `DEN` = 7,200 do that exactly. The sentence at proof-of-work 159, which states the product `DEN` · `EXPECTED_BLOCKS_PER_EPOCH`, would then need `NUM` in its product.
- (Assumed: Blend's randomness of the next epoch, $`R_{e+1}`$, is the next epoch's nonce. Blend 992–994 says only that the consensus provides one value per epoch.) The nonce of epoch $`e + 1`$ is known from the cut-off of epoch $`e`$, so throughout phase 3. Blend 1025 says that a dishonest node that knows the randomness early can hold back messages whose tokens might win a premium reward for the receiving node (Cited).

## 4. The learning rate: noise

**4.1 (Computed). The chance per epoch that the noise of $`D`$ passes 1.094.** A cell marked with an asterisk gives importance sampling of the rule in integers (`simulate.py`, part B). Every other cell gives the stationary law of `chain.py`'s chain (`out_betas.txt`, part 1). The chain agrees with every sampled value within 2 %.

| `beta` | 30 h, rule as printed | 30 h, exact rule | 35 h, rule as printed | 35 h, exact rule | 40 h, rule as printed | 40 h, exact rule |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | $`2.2\cdot10^{-9}`$* | $`5.4\cdot10^{-8}`$* | $`1.2\cdot10^{-10}`$* | $`4.7\cdot10^{-9}`$* | $`6.2\cdot10^{-12}`$* | $`4.2\cdot10^{-10}`$* |
| 7/8 | $`1.1\cdot10^{-11}`$* | $`6.9\cdot10^{-10}`$* | $`2.4\cdot10^{-13}`$* | $`3.0\cdot10^{-11}`$* | $`5.4\cdot10^{-15}`$* | $`1.3\cdot10^{-12}`$* |
| 5/6 | $`1.3\cdot10^{-12}`$* | $`1.2\cdot10^{-10}`$* | $`2.0\cdot10^{-14}`$ | $`3.9\cdot10^{-12}`$ | $`3.1\cdot10^{-16}`$ | $`1.3\cdot10^{-13}`$ |
| 4/5 | $`2.0\cdot10^{-13}`$ | $`2.6\cdot10^{-11}`$ | $`2.2\cdot10^{-15}`$ | $`6.6\cdot10^{-13}`$ | $`2.6\cdot10^{-17}`$ | $`1.7\cdot10^{-14}`$ |
| 3/4 | $`8.8\cdot10^{-15}`$* | $`2.1\cdot10^{-12}`$* | $`6.0\cdot10^{-17}`$ | $`3.4\cdot10^{-14}`$ | $`4.2\cdot10^{-19}`$ | $`5.8\cdot10^{-16}`$ |
| 2/3 | $`1.7\cdot10^{-17}`$ | $`1.3\cdot10^{-14}`$ | $`4.3\cdot10^{-20}`$ | $`9.4\cdot10^{-17}`$ | $`1.1\cdot10^{-22}`$ | $`6.9\cdot10^{-19}`$ |

The sampled values are in `out_simulate_branch_40h.txt`, `out_simulate_529_40h.txt`, `out_simulate_branch_35h.txt`, `out_simulate_529_35h.txt`, `out_simulate_branch_30h_betas.txt`, `out_simulate_529_30h_betas.txt`, and, for 30 hours at 1 and 3/4, `out_simulate_branch_30h.txt` and `out_simulate_529_30h.txt`. At 40 hours, plain Monte Carlo agrees with the chain on the mean, the sd and the share of epochs above 1.03 to 1.06 (part A).

**4.2 (Computed). The largest rate that meets the standard of SCHEDULE.md 4.1 under both forms.** The exact rule binds at every window.

| Window | Of 1, 3/4 and 2/3 (the RFC's rule) | Of 1, 7/8, 5/6, 4/5, 3/4 and 2/3 | Its chance under the exact rule |
| --- | --- | --- | --- |
| 30 h ($`3K + 3K`$) | 3/4 | 7/8 | $`6.9\cdot10^{-10}`$ |
| 35 h ($`2.5K + K + 2K`$) | 3/4 | 7/8 | $`3.0\cdot10^{-11}`$ |
| 40 h ($`2K + 2K + 2K`$) | 1 | 1 | $`4.2\cdot10^{-10}`$ |

**4.3 (Computed). Noise and the floor premise at these rates** (`out_betas.txt`, part 1). The floor premise is the mean chance that fewer than 689 blocks follow a block within $`K`$, with every block 15 slots late (SCHEDULE.md 4.7).

| Window, `beta` | sd of $`D/S`$, exact rule | Floor premise, exact rule | Floor premise, rule as printed |
| --- | --- | --- | --- |
| 30 h, 3/4 (the branch) | 1.274 % | $`7.8\cdot10^{-9}`$ | $`3.7\cdot10^{-8}`$ |
| 30 h, 7/8 | 1.448 % | $`1.3\cdot10^{-8}`$ | $`5.9\cdot10^{-8}`$ |
| 35 h, 7/8 | 1.341 % | $`9.5\cdot10^{-9}`$ | $`4.4\cdot10^{-8}`$ |
| 40 h, 1 | 1.419 % | $`1.2\cdot10^{-8}`$ | $`5.4\cdot10^{-8}`$ |

## 5. The learning rate: response

**5.1 (Computed). The error of $`D`$ after each correction.** The rule is simulated in integers, with 200,000 runs (`out_betas.txt`, parts 2 and 3). The errors and the deflation depend on `beta`. They agree within 0.003 across the three windows, and the errors agree within 0.001 across the two forms of the rule. The share of runs above 1.094 also depends on the window's noise. At 7/8 under the exact rule it is 18.9 % at 30 hours, 17.0 % at 35 and 15.3 % at 40. Every value in the table is for a window of 30 hours. The errors are under the exact rule.

| `beta` | After the stake halves: error of $`D`$ at corrections 1, 2, 3 | After it doubles: runs with $`S/D`$ above 1.094 after correction 1, as printed and exact | Deflation by 30 %: $`D`$ over the honest stake after windows 1, 2, 3 (exact) |
| --- | --- | --- | --- |
| 1 | 2.0 %, 1.3 %, 1.3 % | 0, 0 | 1.005, 1.000, 1.000 |
| 7/8 | 13.2 %, 2.0 %, 1.2 % | 3.4 %, 18.9 % | 1.058, 1.008, 1.001 |
| 5/6 | 17.4 %, 3.1 %, 1.2 % | 57.9 %, 88.1 % | 1.076, 1.014, 1.002 |
| 4/5 | 20.7 %, 4.4 %, 1.3 % | 97.4 %, 99.8 % | 1.090, 1.019, 1.004 |
| 3/4 | 25.6 %, 6.7 %, 1.9 % | 100 %, 100 % | 1.111, 1.029, 1.008 |
| 2/3 | 33.9 %, 11.6 %, 4.0 % | 100 %, 100 % | 1.146, 1.050, 1.017 |

After a doubling, the share above 1.094 after correction 2 rounds to 0 at four decimals for every rate except 2/3, where it is 0.05 % and 0.85 %. Correction $`k`$ is first used $`L_3 + kE`$ after the change. That is 90, 150 and 210 hours for $`3K + 3K`$; 80, 140 and 200 for $`2K + 2K + 2K`$; and 75, 130 and 185 for $`2.5K + K + 2K`$.

**5.2 (Computed; the two models are Assumed). A stake that builds and grows steadily.** A note may lead only from the epoch after the one whose first slot finds it in the note set (protocol 173, Cited). So new stake raises the stake that builds only at epoch boundaries, and the stake stays constant within an epoch. Stake that is already eligible and comes online raises it within an epoch. The values are the mean of the rule with no noise (`out_betas.txt`, part 4). The lag is the largest $`S/D`$ of an epoch over $`S/D`$ at the fixed point, at 1 % a day, expressed as hours of growth. It is the same under both forms of the rule. The largest growth is the steepest at which that $`S/D`$ stays at most 1.094, under the exact rule.

| Construction, `beta` | New stake: lag | New stake: largest growth a day | Coming online: lag | Coming online: largest growth a day |
| --- | --- | --- | --- | --- |
| today, 1 | 183 h | 1.18 % | 309 h | 0.70 % |
| $`3K + 3K`$, 3/4 (the branch) | 81 h | 2.71 % | 126 h | 1.73 % |
| $`3K + 3K`$, 7/8 | 70 h | 3.15 % | 115 h | 1.90 % |
| $`3K + 3K`$, 1 (fails the standard) | 61 h | 3.59 % | 106 h | 2.05 % |
| $`2.5K + K + 2K`$, 7/8 | 64 h | 3.45 % | 101 h | 2.15 % |
| $`2K + 2K + 2K`$, 1 | 61 h | 3.59 % | 101 h | 2.16 % |

Each lag of part 4 is within one hour of a simple formula (Computed). For new stake the formula is $`1.02\,E/\beta`$. For stake coming online it is $`E(1 + 1.02/\beta) - c/2`$. The factor 1.02 is the inverse of the elasticity of the chance that a slot is occupied, $`1 - (1-f)^r`$, at $`r = 1`$. For new stake neither the window nor the cut-off enters. At the same epoch and rate, $`3K + 3K`$ and $`2K + 2K + 2K`$ lag alike.

**Not proved.** The count model (every win counted, REVIEW.md 7.3), the limit 1.094, which is cited, the two growth models of 5.2 and their use of the mean, to which the noise of 4.3 adds, and the reading of $`R_{e+1}`$ in section 3.

## 6. What this gives

- $`2K + 2K + 2K`$ keeps every rule of SCHEDULE.md 2 under both arguments for the nonce (1.3). It also keeps the base's structure of three phases.
  - Its window of 40 hours meets the standard with `beta` = 1, the base's value. The chance is $`4.2\cdot10^{-10}`$ under the exact rule, 2.4 times below $`10^{-9}`$. The branch's $`3K + 3K`$ at 3/4 is 480 times below it, at $`2.1\cdot10^{-12}`$.
  - Against $`3K + 3K`$ at 3/4, $`D`$ is corrected in one step, first used 80 hours after a change in place of 90. After a doubling, $`D`$ is back within 1.094 at 80 hours in place of 150.
  - The lag behind new stake falls from 81 to 61 hours, and behind stake coming online from 126 to 101.
  - The next epoch's nonce is known for a third of the epoch in place of a half.
  - The cost is in phase 3. Its values are final in time down to 41.35 % of $`D`$ building in place of 26.05 %, and it meets J with one slot to spare.
  - A deflation costs a coalition of 30 % one window of 1,457 wins in place of three windows of 1,093.
  - The floor premise rises from $`7.8\cdot10^{-9}`$ to $`1.2\cdot10^{-8}`$ under the exact rule.
- $`3K + 3K`$ meets the standard at 7/8 as well as at 3/4. At 7/8 the chance is $`6.9\cdot10^{-10}`$ under the exact rule, 1.45 times below $`10^{-9}`$.
  - 7/8 halves the error after a halving at the first correction, from 25.6 % to 13.2 %.
  - After a doubling, 81 % of runs are back within 1.094 at 90 hours under the exact rule, and 97 % under the rule as printed. At 3/4 none are.
  - The lag behind new stake falls from 81 to 70 hours.
- $`2.5K + K + 2K`$ shortens the epoch by 5 hours against $`2K + 2K + 2K`$, and costs the following.
  - A learning rate of 7/8.
  - The targets that meet two nonces rise from 16.67 % to 18.18 %.
  - The gain of a coalition of 30 % that chooses among nonces rises from 1.21 % to 1.27 % at 10 s, and from 1.43 % to 1.49 % at 15 s.
  - The proof-of-work rate needs a numerator of 11.

## 7. Files

All files are in `slot-finality/epoch/schedule/`. Run each script in this folder with the finality study's interpreter and redirect its output.

| Script | What it computes | Output |
| --- | --- | --- |
| `constructions.py` | the columns of `costs.py` and the rules of SCHEDULE.md 2 for each construction, in both forms of 1.2 and with $`3K + K + 2K`$ and $`2K + K + 2K`$; the proof-of-work rate as `NUM`/`DEN`; the gain of choosing among nonces at 60, 55 and 50 hours | `out_constructions.txt` |
| `betas.py` | the stationary law by window, learning rate and form of the rule, with the floor premise (part 1, 7 processes); the response to a step change (2) and to a deflation (3) in integers; the lag behind new stake and behind stake coming online (4) | `out_betas.txt` |
| `simulate.py <branch\|529> [A B]` | importance sampling (B) and plain Monte Carlo (A) of the rule in integers | `out_simulate_branch_40h.txt`, `out_simulate_529_40h.txt` (WINDOW=144000 EPOCH_H=60 GAP_H=20 BETAS=1,7/8, parts A B); `out_simulate_branch_35h.txt`, `out_simulate_529_35h.txt` (WINDOW=126000 EPOCH_H=55 GAP_H=20 BETAS=1,7/8, part B); `out_simulate_branch_30h_betas.txt`, `out_simulate_529_30h_betas.txt` (WINDOW=108000 EPOCH_H=60 GAP_H=30 BETAS=7/8,5/6, part B) |
