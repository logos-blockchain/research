# The epoch of 40 hours

Date: 2026-11-19.

This note states the epoch schedule that the logos-lips branch `Bedrock-RFC-Shorter-Epoch` specifies at a finality window $`K`$ of 36,000 slots (10 hours), and the analysis behind it that `../REVIEW.md` does not contain: why the Buffer phase can go, the condition on the last phase, the learning rate of the stake inference, and what each schedule costs. Statements carry the labels of REVIEW.md, section 2. Line numbers of the specification are those of commit `7f3cf149`, as in REVIEW.md 1.1. Section 7 lists the files.

## 1. The schedule

The epoch has two phases (Cited: the branch's `cryptarchia-v1-protocol.md`, Epoch Schedule and Epoch State Pseudocode; `cryptarchia-total-stake-inference.md`, Parameters and variables):

| Phase | Length |
| --- | --- |
| Stake Distribution Snapshot | $`2K`$ = 72,000 slots, 20 hours |
| Lottery Constants Finalization | $`2K`$ = 72,000 slots, 20 hours |

- The epoch nonce $`\eta`$ and the inferred total stake $`D`$ are read at slot $`2K`$ of the epoch, the cut-off.
- The observation window `PERIOD` is $`2K`$: the first phase.
- The learning rate `beta` of the stake inference is 2/3, held as the ratio of two integers.
- The epoch lasts $`4K`$ = 144,000 slots.

REVIEW.md numbers the phases of the schedule with a Buffer phase: phase 1, phase 2 (the Buffer phase) and phase 3. Here phase 1 is the Stake Distribution Snapshot phase and phase 3 the Lottery Constants Finalization phase, in the same sense.

## 2. The rules it keeps

The rules are those of REVIEW.md 10.1, with B replaced by section 3. A phase of $`G^*`$ = 46,910 slots suffices to keep its value final in time in every state of the $`K`$ row (REVIEW.md 5.9). No phase shorter than 37,718 slots does when every win is counted, or 46,894 when only blocks of the chain count (REVIEW.md 5.9).

- S and L. Each phase lasts 72,000 slots, more than $`G^*`$. Each value is final in time while at least 41.35 % of the inferred stake builds blocks, every block 15 slots late (Computed: `out_costs.txt`, the row of 40 hours). The worst state of the $`K`$ row has 70 % building.
- J. Phase 3 lasts at least $`2K - 1`$ = 71,999 slots, as GENESIS 7.1 needs for a joining node under the Bootstrap rule (Cited: REVIEW.md 10.1, GENESIS 7.1). 72,000 meets it (Proved).
- I. The window ends at the cut-off and lies in phase 1 (Cited, section 1).
- The epoch is at least $`2K`$, so a race of $`K`$ slots meets at most two nonces (Proved from REVIEW.md 6.2).
- The bound $`R \ge 6s_{gen}`$ of Theorem 2 of Ouroboros Genesis is met: 144,000 slots against 97,200 (Computed). The theorem does not cover the specification's delays (REVIEW.md 8.5).
- Phase 1 holds an honest block, the condition of section 3: 72,000 slots against the 17,268 that suffice in every state of the $`K`$ row (Cited: REVIEW.md 9.4, SURVIVAL 8.1).

## 3. The Buffer phase is not needed for the nonce

**3.1 (Cited). The threat.** The lottery ticket of a note is a hash of $`\eta`$, the slot, the note and its secret key (leadership 180). A coalition that knows $`\eta^{ep}`$ while it can still choose the notes of $`\mathbb{C}_\text{LEAD}^{ep}`$ can grind them (protocol 155, 173, 177). The Buffer phase was there so that an honest leader contributes to the nonce after the snapshot is final (protocol 154 at `7f3cf149`).

**3.2 (Cited). Facts used.**

- $`\eta_B`$ is a hash of the parent's value, of the block's contribution $`\rho`$ and of its slot (protocol 192).
- $`\rho`$ is a hash of the slot, the note and its secret key (leadership 185). It does not depend on the parent, on $`\eta`$, or on the block's transactions.
- A header names its parent and is signed under a key that the proof of leadership binds (protocol 300, 445–454). The block ID commits to the parent and to the body (protocol 280–284, 426–430). Slots increase along a chain (protocol 432).
- Only a block's own $`\rho`$ enters $`\eta`$. Uncles add no nonce input.

**3.3 (Proved). An honest block after the snapshot slot suffices.** Let $`s_0`$ be the snapshot slot and $`sl_\text{cut}`$ the cut-off. Suppose that the final chain holds an honest block $`H`$ of the chain itself, with $`s_0 \le sl_H < sl_\text{cut}`$. Then the coalition fixed every note of the final snapshot before it could compute $`\eta^{ep}`$. Assumptions: A4 of REVIEW.md (the snapshot reads only blocks below $`s_0`$), a final chain (REVIEW.md 9.3), and that $`\rho_H`$ cannot be predicted without the honest key (the random oracle of SURVIVAL A1).

*Proof.* Every block with a slot below $`s_0`$ precedes $`H`$ on the chain, so it is an ancestor of $`H`$. The leader of $`H`$ built it on its own local chain, so those blocks were published with their bodies before $`H`$ existed. $`H`$ cannot be moved to another parent, because the parent is signed. The last block before the cut-off is $`H`$ or a descendant of it, so $`\eta^{ep}`$ is a function of $`\eta_H`$, which hashes $`\rho_H`$. ∎

The coalition keeps only the choice that the $`K`$ row already names: withholding or forking its own blocks between $`H`$ and the cut-off (Cited: protocol 104).

**3.4 (Proved). The honest block need not follow the snapshot's finality.** A change of the snapshot needs a fork that diverges before $`s_0`$. That fork holds no block of the abandoned branch, and so none of its honest contributions. Private forks from before $`s_0`$, short reorganisations around $`s_0`$ and withholding all reduce to one event: the final chain holds no honest block in $`[s_0, sl_\text{cut})`$. An honest block below $`s_0`$ does not suffice, since the coalition can append later blocks below $`s_0`$ with fresh notes.

**3.5 (Proved). What the snapshot's finality still does.** If two forks that diverge before $`s_0`$ both survived past the cut-off, the coalition could choose between two pairs of snapshot and nonce. That needs a block more than $`L_1`$ slots old to be still mutable, so phase 1 of at least $`G^*`$ excludes it.

**3.6. The rule.** Without a Buffer phase, phase 1 of $`\max(G^*, w_B)`$ slots suffices, with $`w_B`$ = 17,268 the span that keeps an honest block in every state of the $`K`$ row (Proved, 3.3 to 3.5, with REVIEW.md 9.4). For the honest block at least 903 slots are necessary (Proved, REVIEW.md 9.2), and for 3.5 the necessary values of section 2.

**3.7 (Proved). What the Buffer phase gave instead.** The window must end at the cut-off, because $`D`$ is read there with $`\eta`$, and must lie in one epoch, because the rule treats every counted slot as drawn under the estimate of that epoch (protocol 233–247; REVIEW.md 7.4). So without a Buffer phase the window is at most phase 1. The Buffer phase gave the window its length.

**Not proved.** The assumptions of SURVIVAL (A1 to A5), the existence of a final chain, and A4 of REVIEW.md.

## 4. The stake inference: window and learning rate

**4.1 (Assumed). The standard.** $`K`$ holds 30 % at 15 s only while the true active stake stays within 1.094 times $`D`$ (Cited: RFC-533 61). The standard taken here: the noise of $`D`$ alone passes that limit with a chance of at most $`10^{-9}`$ per epoch.

**4.2 (Computed). With a learning rate of 1.** One step from the fixed point, under the rule the specification prints, the chance is at most $`10^{-9}`$ for every window of at least 113,038 slots (31.40 hours). It first falls below at 112,433 slots and rises above again in between, because the count is an integer (`out_chain.txt`, part 1). At a window of 20 hours it is $`8.0\cdot10^{-7}`$.

**4.3 (Cited). Two forms of the rule.** The rule the specification prints truncates $`f`$ to 33 thousandths, so it settles where slots are occupied at 0.033 and $`D`$ is 1.03 % above the stake that builds (REVIEW.md 7.4). A rule that computes with $`f`$ exactly settles at $`f`$, with $`D`$ equal to that stake. The limit of 4.1 is then 9.4 % above the fixed point in place of 10.5 %.

**4.4 (Computed). The chance per epoch that the noise passes 1.094, by learning rate.** The stationary law of the chain of `chain.py`, beside importance sampling of the rule in integers (`simulate.py`):

| Window | `beta` | Rule as printed: chain | Rule as printed: sampled | Exact rule: chain | Exact rule: sampled |
| --- | --- | --- | --- | --- | --- |
| 20 h | 1 | $`8.3\cdot10^{-7}`$ | $`8.4\cdot10^{-7}`$ | $`7.2\cdot10^{-6}`$ | $`7.2\cdot10^{-6}`$ |
| 20 h | 3/4 | $`1.9\cdot10^{-10}`$ | | $`7.6\cdot10^{-9}`$ | |
| 20 h | **2/3** | $`3.0\cdot10^{-12}`$ | $`3.0\cdot10^{-12}`$ | $`2.5\cdot10^{-10}`$ | $`2.5\cdot10^{-10}`$ |
| 20 h | 1/2 | $`1.1\cdot10^{-17}`$ | $`1.2\cdot10^{-17}`$ | $`9.5\cdot10^{-15}`$ | $`9.7\cdot10^{-15}`$ |
| 15 h | 1 | $`1.7\cdot10^{-5}`$ | $`1.7\cdot10^{-5}`$ | $`8.6\cdot10^{-5}`$ | $`8.7\cdot10^{-5}`$ |
| 15 h | 2/3 | $`1.3\cdot10^{-9}`$ | | $`3.6\cdot10^{-8}`$ | |
| 15 h | 1/2 | $`1.1\cdot10^{-13}`$ | $`1.1\cdot10^{-13}`$ | $`1.7\cdot10^{-11}`$ | $`1.7\cdot10^{-11}`$ |

The chain reads a tail by summing the grid cells beyond the limit, which runs up to 2 % low; importance sampling does not. Sources: `out_chain.txt`, part 2; `out_simulate_branch_20h.txt`, `out_simulate_529_20h.txt`, `out_simulate_branch_15h.txt`, `out_simulate_529_15h.txt`, part B. Plain Monte Carlo of the same rules agrees with the chain on the mean, the sd and the share of epochs above 1.03 to 1.06 (part A of the 20-hour outputs).

**4.5. The choice.** `beta` = 2/3 is the largest of 1, 3/4 and 2/3 that meets the standard under both forms of the rule at a window of $`2K`$ (Computed, 4.4). The sd of $`D/S`$ is then 1.43 % (`out_chain.txt`, part 2).

**4.6 (Computed). What a learning rate of 2/3 costs.** At the schedule of section 1, by simulation of the rule in integers (`out_simulate_*_20h.txt`, parts C and D; both forms agree to 0.1 point):

- A change of the stake that builds, just after a cut-off, is first used 60 hours later. After the stake halves, $`D`$ is 34 % off at 60 hours, 12 % at 100 hours and 4 % at 140 hours. After a change of a tenth, it is 3.8 % off at 60 hours and 1.6 % at 100 hours.
- After the active stake doubles just after a cut-off, $`S/D`$ stays above 1.094 until the second correction, 100 hours later: 1.204 at 60 hours and 1.055 at 100 hours under the rule as printed. With a learning rate of 1 it would stay above until the first correction, 60 hours later, and today until 252 hours.
- A coalition of 30 % of the total active stake that withholds every block brings $`D`$ to within 15 %, 5 % and 2 % of where the rule settles on the honest stake, after one, two and three windows. Each window costs it 729 wins.

**4.7 (Computed). The floor premise.** The mean chance that fewer than 689 blocks follow a block within $`K`$ slots, every block 15 slots late, over the stationary law: $`5.6\cdot10^{-8}`$ under the rule as printed and $`1.2\cdot10^{-8}`$ under the exact rule. At its fixed point with no noise the exact rule gives $`9.8\cdot10^{-10}`$, and the rule as printed $`5.6\cdot10^{-9}`$ (`out_chain.txt`, part 3). Missing the floor delays finality past $`K`$ and never makes a block immutable early (Cited: RFC-533 131).

**Not proved.** The count model (every win counted, REVIEW.md 7.3) and the limit 1.094, which is cited.

## 5. What each schedule costs

`out_costs.txt` gives every column for ten schedules; the gain of choosing among nonces is from `out_gain.txt`. For the schedule of section 1 (Computed):

| | Today | 40 hours |
| --- | --- | --- |
| Phases | 54, 54, 72 h | 20, 20 h |
| Least building share for phase 1, phase 3 (15 s) | 13.80 %, 10.20 % | 41.35 %, 41.35 % |
| Targets that meet two nonces | 5.56 % | 25.00 % |
| Gain of a coalition of 30 % that chooses among at most $`2^{16}`$ nonces, 10 s and 15 s | 0.70 %, 0.82 % | 1.49 %, 1.75 % |
| New stake waits | 180 to 360 h | 40 to 80 h |
| Longest time with no correction of $`D`$ | 252 h | 60 h |
| Blocks an epoch | 21,600 | 4,800 |

Of the schedules in `out_costs.txt`, "no buffer: 3.5K, 1.5K", "no buffer: 1.5K, 1.5K" and "K, K, K" fail J, and "K, K, K" also fails S and L.

## 6. Blend's reward lottery

The lottery's threshold reads the cover messages of an epoch. A core node's chance of a base reward in an epoch, at 3,000 and 10,000 core nodes, is 1.00 and 0.89 at 180 hours, and 0.81 and 0.03 at 40 hours. It falls below a half from 16,384 core nodes at 180 hours and from 4,096 at 40 hours (Computed: `out_lottery.txt`).

## 7. Files

All files are in `slot-finality/epoch/schedule/`. Run each script in this folder with the finality study's interpreter and redirect its output.

| Script | What it computes | Output |
| --- | --- | --- |
| `chain.py` | the windows of 4.2; the stationary law by window, learning rate and form of the rule; the floor premise | `out_chain.txt` (20 minutes) |
| `simulate.py <branch\|529> [A B C D]` | the rule in integers: plain Monte Carlo (A), importance sampling (B), the response to a change of stake (C), a deflation (D); settings WINDOW, EPOCH_H, GAP_H, BETAS | `out_simulate_branch_20h.txt`, `out_simulate_529_20h.txt` (defaults); `out_simulate_branch_15h.txt`, `out_simulate_529_15h.txt` (WINDOW=54000 EPOCH_H=35 GAP_H=20 BETAS=1,1/2, parts B C D) |
| `costs.py` | the costs of ten schedules with `../s09_epoch.py`, whether phase 3 meets J, and the proof-of-work rate that keeps the reward of a claim | `out_costs.txt` |
| `gain.py` | the gain of choosing among nonces with `../s11_gain.py`, at 180, 100, 40, 35 and 30 hours | `out_gain.txt` |
| `lottery.py` | Blend's reward lottery by the length of the epoch | `out_lottery.txt` |
