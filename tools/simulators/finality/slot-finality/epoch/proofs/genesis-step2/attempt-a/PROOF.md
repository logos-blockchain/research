# GENESIS 7.3 when the gap is only s + K − 1 slots

Date: 2026-11-19.

GENESIS 7.3 proves that a node that bootstraps under the Bootstrap rule ends on the honest chain. Among its hypotheses is $`2K \le G + 1`$, where $`G`$ is the gap from the cut-off to the next epoch. This document asks whether the conclusion still holds when that hypothesis is replaced by $`s + K \le G + 1`$. It proves that it does, with GENESIS's bound unchanged: the extra failure term is 0. The one step that used $`2K \le G + 1`$ is repaired with a different witness of the same event. Section 5 states what a fork's own epoch state can be when $`G + 1 < 2K`$. The proof does not need it.

## 0. Result in brief

- **Proved, with no extra term (4.1).** In the model of GENESIS section 3, with $`s \le K - 1`$ and $`s + K \le G + 1`$, the bound of GENESIS 7.3 holds term for term. The extra term is 0 in every state of the $`K`$ row, for both schedules, and whatever nonce and inferred stake a fork derives after its density window. (Proved, given GENESIS A6.)
- **The only use of $`2K \le G + 1`$ (2.3).** Step 2 of GENESIS 7.1 uses it to put a bad fork $`X`$ under $`H`$'s epoch states, so that $`X`$ and $`H`$ witness $`E_r`$. Every other step needs $`s + K \le G + 1`$, $`K \le G + 1`$ or $`G \ge K`$. GENESIS 6.2 and 6.3 list $`2K \le G + 1`$ as a hypothesis, but their proofs do not use it. The claim of the question is confirmed. (Proved.)
- **The repair (3.2, 3.3).** Without $`E_r`$ and $`E_g`$, every chain of $`\mathcal G`$ left $`H`$ less than $`K`$ slots before the switch. Suppose a chain $`Y`$ of $`\mathcal G`$ left $`H`$ at least $`K`$ slots before the switch. Then $`Y`$ is dominant and ends before the switch. Its blocks lie less than $`K \le G + 1`$ slots after $`D_Y`$, so they are under $`H`$'s states. So $`Y`$ and $`H`$ witness $`E_r`$. A fork that beats $`Y`$ by length shares $`H`$'s blocks up to $`D_Y`$ or up to its divergence block from $`Y`$, so it is not bad. The blocks of $`X`$ that lie under a state of its own are never read. (Proved.)
- **Numbers (4.2).** Of the terms of 7.3, only $`P_1(G + 1 - s)`$ reads $`G`$. Against 30 % it is at most $`2.9\cdot10^{-20}`$ at $`G`$ = 52,199 and $`3.2\cdot10^{-21}`$ at 54,000, in place of at most $`6.3\cdot10^{-33}`$ at GENESIS's gap. No total changes in its first four digits. Per divergence slot, forks with no honest block in the window, together with $`U(K-2)`$, meet $`10^{-9}`$ in every state, the worst being $`9.20\cdot10^{-10}`$. The bound for every fork does not meet it in any state ($`1.35\cdot10^{-7}`$ to $`4.34\cdot10^{-5}`$), as in GENESIS. (Computed, `out_2_terms.txt`.)
- **A fork's own state (5).** When $`G + 1 < 2K`$, the fork $`X`$ of Step 2 can derive its own nonce and its own $`D`$ for the epoch after $`D_Y`$'s, but never its own snapshot. This happens only if $`D_Y`$ lies 2 to $`2K - 2 - G`$ slots before a cut-off. Always $`D_X \ge (1 - \beta)D`$. Under REVIEW's count law, $`D_X \ge 0.70\,D_H`$ except with chance $`10^{-9}`$. The coalition can choose $`X`$'s nonce among at least $`2^A`$ candidates, where $`A`$ is its number of wins between $`D_Y`$ and the cut-off. $`A`$ averages 200 when $`D_Y`$ lies earliest. So a model of the best of $`M \le 2^{64}`$ nonces would not bound the choice. 4.1 needs neither bound. (Proved; Computed, `out_3_inference.txt`.)
- **Checks (6).** Random and targeted executions with $`G + 1 < 2K`$ produced 2,851 replacements of a chain of $`\mathcal G`$ by a bad fork in a comparison by length. In every one, $`Y`$ and $`H`$ witnessed $`E_r'`$. In 856 of them $`X`$ held blocks under a state that $`H`$ does not derive, so GENESIS's witness $`(X, H)`$ would have failed. (Computed, `out_4_checks.txt`.)
- **For the schedule.** The repaired argument asks of the Lottery Constants Finalization phase only $`G \ge s + K - 1`$ = 52,199 slots (14.50 h), not $`2K - 1`$ = 71,999 (20.00 h). Schedule (ii), with 54,000 slots, meets it. If $`s`$ is raised to the window that the bound for every fork needs at $`10^{-9}`$ against 30 % at 10 slots, the phase needs 57,335 slots for one divergence slot and 69,180 for a year of history. (Proved, 4.1; Computed, `out_2_terms.txt` lines 11–12.)

## 1. Setting

### 1.1 Texts

| Short name | Text | Version |
| --- | --- | --- |
| GENESIS | `tools/simulators/finality/slot-finality/epoch/proofs/genesis/GENESIS.md` of the research worktree `fast-finalization-slots`, with `common_g.py` and the cached curves `.cache/` | as read 2026-11-19 |
| REVIEW | `.../slot-finality/epoch/REVIEW.md` of the same worktree | as read 2026-11-19 |
| protocol, inference, fork choice, bootstrap, leadership | `docs/blockchain/raw/cryptarchia-v1-protocol.md`, `cryptarchia-total-stake-inference.md`, `fork-choice.md`, `cryptarchia-v1-bootstr-sync.md`, `cryptarchia-proof-of-leadership.md` of logos-lips | `83596b6e` (branch Bedrock-RFC-Shorter-Epoch; protocol 1.5.0, two phases of $`2K`$) |

Line numbers are those that `git show 83596b6e:<path>` prints. GENESIS cites `7f3cf149`. The fork choice, bootstrap and leadership texts are identical at the two commits. The protocol differs in its revision table, the $`K`$ row, the Epoch Schedule and the Epoch State Pseudocode. The inference differs in `beta`, `PERIOD` and the correction step. From line 156 on, the protocol's lines keep the numbers that GENESIS cites, and their texts differ only at lines 157, 159, 229, 231, 235 and 237 (`out_1_schedule.txt` (a), lines 27–31). GENESIS's statements are cited by their numbers, for example GENESIS 7.1.

### 1.2 Symbols

GENESIS's symbols and definitions are kept: $`f, k, K`$, $`s = s_{gen}`$, $`\Delta`$, $`\alpha`$, $`p_h, p_a`$, $`A(I)`$, $`N(I)`$, $`d(t)`$, $`U(w)`$, $`U_{\Delta+1}(w)`$, $`P_1(x)`$ (GENESIS 1.2); $`J`$, now, $`H`$, dominant, $`D_Z`$, bad, $`\mathcal G`$, holds (GENESIS 2.3); A1–A6 and S (GENESIS 3); $`E_d(\sigma)`$ and $`E_g`$ (GENESIS 7.1). The others are this document's.

| Symbol | Meaning | Value |
| --- | --- | --- |
| $`P`$ | the snapshot phase: the cut-off's offset into the epoch, and `PERIOD`, the inference's window | 72,000 at `83596b6e`; 54,000 in schedule (ii) |
| $`G`$ | the Lottery Constants Finalization phase: the gap from the cut-off to the next epoch | 72,000 at `83596b6e`; 52,199 in (i); 54,000 in (ii) |
| $`E`$ | the epoch, $`P + G`$ | |
| $`c_e`$ | the cut-off of epoch $`e`$, slot $`eE + P`$; epoch $`e + 1`$ starts at $`c_e + G`$ | |
| $`\sigma_0, u`$ | the slot of $`D_Y`$; $`u = c_e - \sigma_0`$ for $`D_Y`$ in epoch $`e`$ | |
| $`\beta, \hat f`$ | the inference's learning rate, a ratio of integers; $`\hat f`$ = 33/1000 | 2/3 at `83596b6e`; 1/2 and 2/3 here |
| $`E_r'`$ | two chains, made under $`H`$'s states, each with no block after slot $`\text{now} - 1`$ and at least $`d(\text{now} - \Delta - 1)`$ blocks long, that share no block with a slot of at least $`\text{now} - K + 1`$ | |
| $`m(Y, D)`$ | for two blocks $`D`$ and $`D_Y`$ of a chain $`Y`$, the one that is an ancestor of the other, or both if they are equal | |

$`E_r'`$ is GENESIS's $`E_r`$ with both chains ending before slot now, so $`E_r' \subseteq E_r`$. 3.4 bounds it directly.

The schedules of the question: (i) the least gap with $`s + K \le G + 1`$, $`G = s + K - 1`$ = 52,199, with a snapshot phase that the question leaves open; (ii) two phases of $`1.5K`$, $`P = G`$ = 54,000. The bound of 4.1 does not read $`P`$ or $`\beta`$.

### 1.3 Labels

As in GENESIS 1.3: every numbered statement is Proved, Computed, Cited or Assumed, and an Estimate is never a bound.

## 2. The schedule and the epoch state

**2.1 (Cited). What an epoch state reads.** For an epoch $`ep \ge 1`$, `compute_epoch_state` takes the snapshot as the commitment root at the first slot of epoch $`ep - 1`$ (protocol 225). It takes the nonce as $`\eta_{B'}`$ for the last block $`B'`$ before the cut-off of epoch $`ep - 1`$ (protocol 197, 229). It computes $`D^{ep}`$ from $`D^{ep-1}`$ and from the occupied slots of the chain in the snapshot phase of epoch $`ep - 1`$ (protocol 231–247; inference 56, 80). With REVIEW's assumption A4 on the commitment root, all three are functions of the chain's blocks with slots below $`c_{ep-1}`$ (REVIEW 4.3). Epoch $`ep`$ starts $`G`$ slots after $`c_{ep-1}`$ (protocol 154–159). GENESIS's schedule has the same form with $`P`$ = 388,800 and $`G`$ = 259,200, and so do (i) and (ii).

**2.2 (Proved). One epoch state for $`G + 1`$ slots after a divergence.** Let two chains share exactly the blocks up to a block $`D`$. For every slot $`t \le sl_D + G + 1`$, both chains derive the epoch state of $`t`$ from blocks they share. The span is the least possible: if $`sl_D = c_e - 2`$ and one chain has a block in slot $`c_e - 1`$, the state of slot $`c_e + G = sl_D + G + 2`$ reads that block. This is GENESIS 4.2 for every schedule of the form of 2.1.

*Proof.* Slots increase along a chain (protocol 432), so a chain's blocks with slots of at most $`sl_D`$ are $`D`$ and its ancestors, which both chains hold. Let $`t`$ lie in epoch $`ep`$ and $`D`$ in epoch $`e`$. The state of $`t`$ reads blocks with slots below $`c_{ep-1}`$, or none if $`ep = 0`$ (2.1). If $`ep \le e`$, then $`c_{ep-1} \le c_{e-1} = eE - G \le sl_D`$. If $`ep = e + 1`$ and $`sl_D \ge c_e - 1`$, then $`c_e \le sl_D + 1`$. In both cases the state reads only shared blocks. In the remaining cases $`t > sl_D + G + 1`$. If $`ep = e + 1`$ and $`sl_D \le c_e - 2`$, then $`t \ge c_e + G \ge sl_D + G + 2`$. If $`ep \ge e + 2`$, then $`t \ge (e + 2)E > sl_D + E \ge sl_D + G + 1`$, since $`(e + 1)E > sl_D`$ and $`P \ge 1`$. For the least span: the state of epoch $`e + 1`$ reads the nonce of the last block before $`c_e`$, which is the block in slot $`c_e - 1`$. ∎

`out_1_schedule.txt` (c): over every divergence slot of an epoch, the least span is $`G + 1`$ for (i) with $`P`$ = 54,000 and 72,000, for (ii) and for `83596b6e`, and it is attained only at $`c_e - 2`$. (d): `compute_epoch_state` written out, with the inference in integers, on random pairs of chains for four small schedules: 144,000 slot states up to $`\sigma_0 + G + 1`$ compared, none different. (Computed.)

**2.3 (Proved). Where GENESIS uses the gap.** GENESIS reads $`G`$ only in its 3.1 and its 4.2, which is 2.2 here. Each use of them needs:

| GENESIS | What the proof applies 2.2 to | Condition |
| --- | --- | --- |
| 3.1 | a state reads blocks below a cut-off at most $`t - G`$, which must be at most $`t - K`$ | $`G \ge K`$ |
| 6.1 | $`Y`$'s blocks after $`D_Y`$, below $`sl_{D_Y} + K`$; $`X`$'s window, below $`sl_{D_Y} + K + s`$ | $`K \le G + 1`$, $`s + K \le G + 1`$ |
| 6.2, 8.1 (1) | 6.1 | $`s + K \le G + 1`$ |
| 6.3, first case | the extension of $`X[0{:}e]`$ in the slots $`(e, b)`$ | the case's $`b \le \sigma + G + 1`$, and 3.4 (2) |
| 6.3, other cases; 8.1 (2) | 5.3 and 5.4 for $`Y`$ alone | $`K \le G + 1`$ |
| 7.1, Steps 0, 1 and 3 | nothing | none |
| 7.1, Step 2 | $`X`$'s blocks after $`D_Y`$, below $`sl_{D_Y} + 2K`$ | $`2K \le G + 1`$ |
| 7.2, $`E_r`$ | nothing beyond $`E_r`$'s definition | none |
| 7.2, the second bound | the extension of $`X[0{:}e]`$ in the slots $`(e, \text{now}]`$ | 3.4 (3) |

So only Step 2 of 7.1 uses $`2K \le G + 1`$. 6.2 and 6.3 list it among their hypotheses, but their proofs go through 6.1. GENESIS 6.4 and 9.2 also apply 2.2, but they are not used by 7.3. Two arguments justify the extension of $`X[0{:}e]`$ by "within $`G + 1`$ of $`D`$". That gives $`Y`$'s states. $`Y`$'s states equal $`H`$'s there only if $`D`$ is $`D_Y`$ or an ancestor of it, or if the slots lie at most $`sl_{D_Y} + G + 1`$. 3.4 (2) and (3) supply the missing step, under either condition on $`G`$.

*Proof.* By reading the proofs of GENESIS 3.1, 6.1–6.3, 7.1, 7.2 and 8.1 for the places where they apply GENESIS 4.2 or 3.1. ∎

## 3. The reduction under $`s + K \le G + 1`$

**3.1 (Proved). The chains of $`\mathcal G`$ lie under $`H`$'s states.** Let $`K \le G + 1`$. For every chain $`Z`$ of $`\mathcal G`$, every block of $`Z`$ after $`D_Z`$ was made under the epoch state that $`H`$ derives for its slot.

*Proof.* $`Z`$ is not bad, so its blocks after $`D_Z`$ have slots in $`(sl_{D_Z}, sl_{D_Z} + K) \subseteq (sl_{D_Z}, sl_{D_Z} + G + 1]`$. $`Z`$ and $`H`$ share exactly the blocks up to $`D_Z`$. 2.2 applies. ∎

**3.2 (Proved). Without $`E_r'`$ and $`E_g`$, every chain of $`\mathcal G`$ left $`H`$ less than $`K`$ slots before the switch.** On S, let $`K \le G + 1`$. If neither $`E_r'`$ nor $`E_g`$ occurs, then $`sl_{D_Z} > \text{now} - K`$ for every chain $`Z`$ of $`\mathcal G`$.

*Proof.* If $`Z`$ contains $`H`$, then $`D_Z`$ is $`H`$'s last block. Step 0 of GENESIS 7.1 shows $`sl_{D_Z} > \text{now} - K`$ when $`E_g`$ does not occur. Otherwise $`Z`$ and $`H`$ share exactly the blocks up to $`D_Z`$, and $`D_Z`$ is not $`H`$'s last block. Suppose $`sl_{D_Z} \le \text{now} - K`$. Then:

1. $`Z`$ is not bad, so $`sl_Z < sl_{D_Z} + K \le \text{now}`$, and $`Z`$ has no block after slot $`\text{now} - 1`$.
2. $`Z`$ is dominant: $`\text{len}(Z) \ge d(\text{now} - \Delta - 1)`$. $`H`$ ends in a block made by slot $`\text{now} - \Delta - 1`$, and $`\text{len}(H) = d(\text{now} - \Delta - 1)`$.
3. Both are made under $`H`$'s states (3.1).
4. They share no block with a slot above $`sl_{D_Z}`$, hence none with a slot of at least $`\text{now} - K + 1`$.

So $`Z`$ and $`H`$ witness $`E_r'`$, against the hypothesis. ∎

**3.3 (Proved). The reduction.** On S, let $`K \le G + 1`$. $`J`$ holds unless one of these occurs: $`E_d(\sigma)`$ for some slot $`\sigma`$ from $`J`$'s starting block to $`\text{now} - K`$; $`E_r'`$; $`E_g`$.

*Proof.* Steps 0, 1 and 3 are those of GENESIS 7.1. They read no condition on $`G`$. Assume that none of the three events occurs. Step 2 is replaced by Step 2′.

*Step 2′. A visit keeps `c_max` in $`\mathcal G`$.* Let `c_max` $`= Y \in \mathcal G`$, let the pass visit $`X`$, and let $`D = D(X, Y)`$. If $`X`$ does not replace $`Y`$, nothing changes. A replacement by density means that $`X`$ is strictly denser than $`Y`$ in $`(sl_D, sl_D + s]`$, with $`sl_D + K \le sl_\text{top} \le \text{now}`$ (fork choice 127, 133–139). That is $`E_d(sl_D)`$. A replacement by length makes $`X`$ longer than $`Y`$, hence dominant, with $`sl_D + K > sl_X`$ (fork choice 127–132). Let $`m = m(Y, D)`$. $`X`$ contains $`D`$, hence $`m`$. $`H`$ contains $`D_Y`$, hence $`m`$. So $`X`$ and $`H`$ share $`m`$, and $`sl_{D_X} \ge sl_m`$.

- If $`m = D`$, then $`sl_{D_X} \ge sl_D > sl_X - K`$.
- If $`m = D_Y`$, then $`sl_{D_X} \ge sl_{D_Y} > \text{now} - K \ge sl_X - K`$. The middle inequality is 3.2. The last holds because a valid block has a slot of at most now (protocol 435).

In both cases $`X`$ is not bad, so $`X \in \mathcal G`$. ∎

GENESIS's Step 2 splits the case $`m = D_Y`$ into "$`Y`$ contains $`H`$", which goes to Step 0, and "$`D_X = D_Y`$", which needs $`X`$ under $`H`$'s states. 3.2 covers both cases, and it reads only $`Y`$'s blocks, which lie less than $`K`$ slots after $`D_Y`$. $`X`$'s blocks may lie under a state that $`X`$ derives from its own blocks (5.1, 5.5). The proof never reads them.

**3.4 (Proved, given A6). The bounds of the three events under $`s + K \le G + 1`$.**

1. $`P(E_r') \le U(K - 2)`$.
2. GENESIS 6.1, 6.2 and 6.3 hold with $`s + K \le G + 1`$ in place of $`2K \le G + 1`$.
3. Let $`C_3(\sigma)`$ be the event of the last case of GENESIS 6.3 at $`\sigma`$. Then $`P\big(E_r' \cup \bigcup_\sigma C_3(\sigma)\big) \le U_{\Delta+1}(K - 1) + P(E_g)`$.

*Proof.* (1) Apply A6 at slot now with $`\ell = \text{now} - K + 1`$. The two chains of $`E_r'`$ are made by slot $`\text{now} - 1`$. Each is at least as long as every chain that ends in an honest block made by slot $`\text{now} - \Delta - 1`$. They share no block with a slot of at least $`\ell`$. So $`\mu_\ell \ge 0`$ at slot $`\text{now} - 1 = \ell + K - 2`$, whose chance is at most $`U(K - 2)`$.

(2) The proofs of 6.1 and 6.2 use the condition only through 6.1, as 2.3 states. In the first case of 6.3, $`Y`$ has an honest block in slot $`b`$ after $`e = \sigma + s`$, and $`b \le \sigma + G + 1`$. The extension $`\tilde X`$ needs every slot of $`(e, b)`$ to be under $`H`$'s states on $`\tilde X`$. Let $`m = m(Y, D)`$. As in 3.3, $`\tilde X`$ and $`H`$ share exactly the blocks up to a block at or after $`m`$, so by 2.2 their states agree at every slot up to $`sl_m + G + 1`$. If $`m = D`$, then $`sl_m = \sigma`$ and $`b \le \sigma + G + 1`$. If $`m = D_Y`$, then $`b`$ is the slot of a block of $`Y`$, so $`b \le sl_Y < sl_{D_Y} + K \le sl_{D_Y} + G + 1`$. In both cases the extension is valid and made under $`H`$'s states. The rest of the proof of 6.3 is unchanged.

(3) In $`C_3(\sigma)`$, $`Y`$ has no honest block after $`e`$, and $`\text{now} \le \sigma + G`$. Let $`m = m(Y, D)`$.

- If $`m = D`$, the extension $`\tilde X`$ of GENESIS 7.2 and $`H`$ share exactly the blocks up to a block at or after $`D`$. The extension's slots $`(e, \text{now}]`$ lie at most $`\sigma + G`$, so they are under $`H`$'s states by 2.2. $`Y`$ is under $`H`$'s states by 3.1. GENESIS 7.2's argument applies.
- If $`m = D_Y \ne D`$ and $`Y`$ does not contain $`H`$, then $`sl_{D_Y} \le \sigma \le \text{now} - K`$, and $`Y`$ and $`H`$ witness $`E_r'`$ as in 3.2.
- If $`m = D_Y \ne D`$ and $`Y`$ contains $`H`$, then $`H`$'s last block has a slot of at most $`\text{now} - K`$, and Step 0 of GENESIS 7.1 gives $`E_g`$.

The chains of $`E_r'`$ meet A6's hypothesis at delay $`\Delta + 1`$, slot $`\text{now} + 1`$ and $`\ell = \text{now} - K + 1`$, as in GENESIS 7.2, because an execution that meets A2 with $`\Delta`$ meets it with $`\Delta + 1`$. So $`E_r' \cup \bigcup_\sigma C_3(\sigma)`$ lies in the event that $`\mu_{\text{now} - K + 1} \ge 0`$ at slot now at delay $`\Delta + 1`$, or in $`E_g`$. ∎

## 4. The theorem

**4.1 (Proved, given A6). GENESIS 7.3 under $`s + K \le G + 1`$.** In the model of GENESIS section 3, with $`s \le K - 1`$ and $`s + K \le G + 1`$,

$$
P(\text{S holds and } J \text{ does not hold}) \le P\Big(\bigcup_\sigma E_d(\sigma)\Big) + U(K - 2) + (1 - p_h)^{K - 2\Delta - 1},
$$

where the union is over slots from $`J`$'s starting block to $`\text{now} - K`$.

- $`P(E_d(\sigma)) \le U(s - 1) + P_1(K - s) + P_1(G + 1 - s)`$ (GENESIS 6.3).
- The part with no honest block of $`X`$ in the window is at most $`P_1(s)`$ (GENESIS 6.2).
- $`U(K - 2)`$ and the terms $`P_1(K - s)`$ together may be replaced by $`U_{\Delta+1}(K - 1)`$ (3.4 (3)).
- Over a history, GENESIS 8.1 applies with this $`G`$.

This is GENESIS 7.3's bound. The extra term is 0. No term reads $`P`$, $`\beta`$, or the nonce and inferred stake of a fork after its window. If $`J`$ holds, GENESIS 2.4 applies.

*Proof.* $`s + K \le G + 1`$ gives $`K \le G + 1`$ and $`G \ge K`$, so GENESIS 3.1 holds. Then 3.3, 3.4, GENESIS 6.2, 6.3 and 8.1, and GENESIS 7.2 for $`P(E_g) \le (1 - p_h)^{K - 2\Delta - 1}`$. The event in 3.4 (3) contains $`E_g`$, whose term the bound already carries. ∎

**4.2 (Computed). The terms in the states of the $`K`$ row.** The states are mapped as in REVIEW 5.9 and GENESIS 10.4 (Assumed). Values are per divergence slot, against 30 % of the total active stake, with $`K`$ = 36,000 and $`s`$ = 16,200. "No honest block" is $`P_1(s) + U(K - 2) + (1 - p_h)^{K - 2\Delta - 1}`$. "Every fork" is $`\min\big(U(s - 1) + P_1(K - s) + P_1(G + 1 - s) + U(K - 2),\ U(s - 1) + P_1(G + 1 - s) + U_{\Delta+1}(K - 1)\big) + (1 - p_h)^{K - 2\Delta - 1}`$.

| State | $`P_1(s)`$ | $`U(s - 1)`$ | $`P_1(K - s)`$ | $`U(K - 2)`$ | $`U_{\Delta+1}(K - 1)`$ | $`P_1(G + 1 - s)`$: (i) / (ii) / GENESIS | extra | no honest block | every fork |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no disturbance | $`2.055\cdot10^{-13}`$ | $`1.349\cdot10^{-7}`$ | $`3.95\cdot10^{-16}`$ | $`8.28\cdot10^{-16}`$ | $`1.35\cdot10^{-14}`$ | $`2.71\cdot10^{-28}`$ / $`1.21\cdot10^{-29}`$ / $`7.18\cdot10^{-39}`$ | 0 | $`2.063\cdot10^{-13}`$ | $`1.349\cdot10^{-7}`$ |
| every block $`T_M`$ late | $`2.564\cdot10^{-10}`$ | $`4.341\cdot10^{-5}`$ | $`2.30\cdot10^{-12}`$ | $`2.51\cdot10^{-10}`$ | $`2.08\cdot10^{-9}`$ | $`1.60\cdot10^{-21}`$ / $`1.55\cdot10^{-22}`$ / $`2.14\cdot10^{-35}`$ | 0 | $`5.071\cdot10^{-10}`$ | $`4.341\cdot10^{-5}`$ |
| a tenth offline, inference corrected | $`5.205\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ | $`5.55\cdot10^{-12}`$ | $`2.01\cdot10^{-11}`$ | $`1.80\cdot10^{-10}`$ | $`8.45\cdot10^{-21}`$ / $`8.91\cdot10^{-22}`$ / $`6.28\cdot10^{-33}`$ | 0 | $`5.406\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ |
| a tenth offline, before the correction | $`8.995\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ | $`1.08\cdot10^{-11}`$ | $`2.08\cdot10^{-11}`$ | $`1.51\cdot10^{-10}`$ | $`2.85\cdot10^{-20}`$ / $`3.19\cdot10^{-21}`$ / $`2.10\cdot10^{-33}`$ | 0 | $`9.203\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ |
| $`D`$ equals the honest stake online | $`8.523\cdot10^{-15}`$ | $`4.506\cdot10^{-7}`$ | $`8.04\cdot10^{-18}`$ | $`9.90\cdot10^{-15}`$ | $`7.26\cdot10^{-13}`$ | $`2.25\cdot10^{-31}`$ / $`7.05\cdot10^{-33}`$ / $`5.10\cdot10^{-36}`$ | 0 | $`1.842\cdot10^{-14}`$ | $`4.506\cdot10^{-7}`$ |

$`(1 - p_h)^{K - 2\Delta - 1}`$ is $`10^{-371}`$, $`10^{-371}`$, $`10^{-359}`$, $`10^{-334}`$ and $`10^{-530}`$ in the five states. The last two columns are the same at the three gaps to the digits shown. (`out_2_terms.txt`, lines 4–10, 15–21, 26–32, 37–43, 48–54. The terms that do not read $`G`$ equal GENESIS's `out_07_states.txt`.)

- GENESIS's long-range figure meets $`10^{-9}`$ per divergence slot in every state, the closest being $`9.0\cdot10^{-10}`$. With $`U(K - 2)`$ and $`E_g`$ added, the worst is $`9.20\cdot10^{-10}`$ at both schedules. It still meets $`10^{-9}`$.
- The bound for every fork misses $`10^{-9}`$ in every state at both schedules, as it does in GENESIS.
- Over histories, nothing changes. Against 30 % at 10 slots, forks with no honest block are bounded by $`8.39\cdot10^{-11}`$ over a day, $`2.52\cdot10^{-9}`$ over 30 days and $`3.06\cdot10^{-8}`$ over a year, and every fork by $`3.0\cdot10^{-5}`$, $`9.1\cdot10^{-4}`$ and $`1.1\cdot10^{-2}`$. These are GENESIS 8.2's values (lines 7, 9; for the other states, lines 18–53).

**4.3 (Computed). The gap that a larger window would need.** The condition $`s + K \le G + 1`$ caps the density window at $`G + 1 - K`$: 16,200 slots in (i) and 18,001 in (ii). Within these caps, no $`s`$ brings the bound for every fork to $`10^{-9}`$, because $`U(s - 1) > 10^{-9}`$ for $`s \le`$ 21,335. In the state without a disturbance, the settlement part meets $`10^{-9}`$ at $`s`$ = 21,336 per divergence slot and at 33,181 over a year (GENESIS 8.2). $`s + K \le G + 1`$ then asks for $`G \ge`$ 57,335 and 69,180, both below $`2K - 1`$ = 71,999. At 15 slots, no window meets $`10^{-9}`$ at $`K`$ = 36,000 by these bounds, whatever $`G`$ (GENESIS 8.2). (`out_2_terms.txt`, lines 11–12, 22–23, 33–34, 44–45, 55–56.)

## 5. What a fork's own state can be

Nothing in this section is used by 4.1. It answers what changes when $`G + 1 < 2K`$ and why GENESIS's original witness fails.

**5.1 (Proved). Which parts of the state can differ.** Let $`X`$ and $`H`$ share exactly the blocks up to $`D_X`$, in slot $`\sigma_0`$ of epoch $`e`$. Let $`X`$'s blocks have slots of at most $`\sigma_0 + 2K - 2`$. That is the reach of Step 2's $`X`$, where $`D_X = D_Y`$, $`sl_X < sl_D + K`$ and $`sl_D < sl_{D_Y} + K`$. Let $`E \ge 2K - 2`$.

1. $`X`$ derives $`H`$'s state for every slot of epoch $`e`$, and of epoch $`e + 1`$ if $`\sigma_0 \ge c_e - 1`$. $`X`$ has no block in epoch $`e + 2`$.
2. If $`\sigma_0 \le c_e - 2`$, $`X`$'s state for epoch $`e + 1`$ has $`H`$'s snapshot, and it computes $`D`$ from $`H`$'s previous estimate $`D^e`$. Its nonce and its count of occupied slots can differ from $`H`$'s.
3. So $`X`$ has a block under a state of its own only if $`u = c_e - \sigma_0`$ lies in $`[2, 2K - 2 - G]`$. Those blocks lie in $`[c_e + G, \sigma_0 + 2K - 2]`$, a stretch of $`2K - 1 - G - u \le 2K - 3 - G`$ slots. That is at most 19,798 slots (5.50 h) in (i) and 17,997 slots (5.00 h) in (ii). For $`G \ge 2K - 3`$ there is no such $`u`$.

*Proof.* (1) 2.2 gives the first two clauses. For the third, $`(e + 2)E > \sigma_0 + E \ge \sigma_0 + 2K - 2`$. (2) The snapshot reads blocks below $`eE \le \sigma_0`$, which are shared. $`D^e`$ reads blocks below $`c_{e-1} < eE`$. The nonce reads blocks below $`c_e`$, and the count reads blocks in $`[eE, c_e)`$ (2.1). (3) By (1) and (2), such blocks lie in epoch $`e + 1`$ with $`\sigma_0 \le c_e - 2`$, so their slots are at least $`c_e + G`$ and at most $`\sigma_0 + 2K - 2 = c_e - u + 2K - 2`$. ∎

`out_1_schedule.txt` (d): in the small schedules, at the first epoch whose state differs, 6,376 pairs; the snapshot differs in none, the nonce in all, and $`D`$ in 74 to 79 %. (e) gives the ranges of (3). (Computed.)

**5.2 (Proved; Computed). The inference in closed form.** With $`\beta`$ = `beta.num`/`beta.den` in $`(0, 1]`$ and integer division that truncates toward zero, the algorithm of inference 77–87 returns $`\max(D'', 1)`$ with

$$
D\Big((1 - \beta) + \beta\frac{N}{P\hat f}\Big) - 1.002 < D'' < D\Big((1 - \beta) + \beta\frac{N}{P\hat f}\Big) + 0.002 .
$$

*Proof.* Write $`e = 33P`$, $`m = 1000N`$ and $`v = 1000D(e - m)/e`$. `slot_activation_error_p` is $`v - \theta`$, with $`0 \le \theta < 1`$ if $`v \ge 0`$ and $`-1 < \theta \le 0`$ if $`v < 0`$. `correction_p` is $`\beta(v - \theta) - \theta'`$ with $`|\theta'| < 1`$. So `tse_p − correction_p` is $`z = 1000D(1 - \beta(e - m)/e) + \beta\theta + \theta' = 1000D((1 - \beta) + \beta N/(P\hat f)) + \beta\theta + \theta'`$, since $`m/e = N/(P\hat f)`$. If $`v \ge 0`$, the correction is at most $`\beta v \le 1000\beta D`$, so $`z \ge 1000(1 - \beta)D \ge 0`$. If $`v < 0`$, the correction is at most 0, so $`z \ge 1000D`$. So the last division is a floor: $`z/1000 - 1 < D'' \le z/1000`$, and $`|\beta\theta + \theta'| < 2`$. ∎

`out_3_inference.txt` (a): the algorithm as printed, on 200,000 random inputs for each of $`\beta`$ = 1/2, 2/3 and 1, against the closed form in exact rationals. The largest distance is 0.999995, and no input gives a negative numerator. (Computed.)

**5.3 (Proved; Computed). How far $`X`$'s $`D`$ can fall below $`H`$'s.** In the setting of 5.1 (2), let $`S_0`$ be the number of occupied slots that $`H`$'s blocks up to $`D_X`$ count in the window, from their own slots and from the uncles they reference. Let $`n = N_H - S_0`$.

1. $`N_X \ge S_0`$ and $`N_H = S_0 + n`$, because $`X`$'s blocks up to $`D_X`$ are $`H`$'s, with the same uncle references.
2. $`D_X^{e+1} > (1 - \beta)D^e - 1.002`$ for every count. The floor is half of $`D^e`$ at $`\beta`$ = 1/2 and a third at 2/3.
3. Up to the rounding of 5.2, $`D_H^{e+1} - D_X^{e+1} \le \beta D^e n/(P\hat f)`$, and

$$
\frac{D_X^{e+1}}{D_H^{e+1}} \ge \frac{(1 - \beta)P\hat f + \beta S_0}{(1 - \beta)P\hat f + \beta(S_0 + n)} .
$$

4. Each slot that $`n`$ counts was won under $`H`$'s states, in $`(\sigma_0 - 359, c_e)`$. It holds a block of $`H`$ after $`\sigma_0`$, or an uncle that such a block references. An uncle's parent lies at most $`W f^{-1}`$ = 360 slots before the referencing block (protocol 332).

*Proof.* (1) holds as stated. (2) and (3) follow from 5.2 with $`N_X \ge 0`$, and with $`N_X \ge S_0`$ and the identity $`D^{e+1} = D^e((1 - \beta) + \beta N/(P\hat f))`$. (4) The uncle's slot exceeds its parent's, which is at least the referencing slot minus 360, and the referencing slot exceeds $`\sigma_0`$. ∎

Assume the count law of REVIEW 7.3 (Assumed): each slot is won and counted independently, with chance $`q`$, taken at the inference's fixed point $`q = \hat f`$. Then the right side of (3) is at least its value with $`S_0 \sim \mathrm{Bin}(P - u + 1 - 359, q)`$ and $`n \sim \mathrm{Bin}(u + 358, q)`$, independent. The bound grows with $`S_0`$ at a fixed $`S_0 + n`$, so moving the 359 slots before $`\sigma_0`$ into $`n`$ only lowers it. Its lower $`10^{-9}`$ quantile, with the coalition's share of $`D_X`$ against 30 % without a disturbance, is (`out_3_inference.txt` (c)):

| Schedule, $`P`$, $`\beta`$ | $`u`$ = 2 (own stretch 19,798 or 17,997 slots) | $`u`$ = 10,000 | largest $`u`$ (own stretch 1 slot) |
| --- | --- | --- | --- |
| (i), 54,000, 1/2 | 0.990 (share 0.303) | 0.875 (0.343) | 0.777 (0.386) |
| (i), 54,000, 2/3 | 0.986 (0.304) | 0.834 (0.360) | 0.705 (0.426) |
| (i), 72,000, 1/2 | 0.992 (0.302) | 0.906 (0.331) | 0.831 (0.361) |
| (i), 72,000, 2/3 | 0.990 (0.303) | 0.875 (0.343) | 0.776 (0.387) |
| (ii), 54,000, 1/2 | 0.990 (0.303) | 0.875 (0.343) | 0.795 (0.378) |
| (ii), 54,000, 2/3 | 0.986 (0.304) | 0.834 (0.360) | 0.728 (0.412) |

So $`D_X`$ falls at most 30 % below $`D_H`$ except with chance $`10^{-9}`$. The largest falls need $`D_Y`$ at its earliest slot, where $`X`$'s own-state stretch is a single slot. Where the stretch has 9,800 slots or more, $`D_X \ge 0.83\,D_H`$. Over every $`u`$, the coalition's chance per slot on $`X`$ rises from 0.0101 to at most 0.0143. (Computed, lines 12–68.)

**5.4 (Proved). The coalition's choice of $`X`$'s nonce.** In the setting of 5.1 (2), let $`A`$ be the number of slots in $`(\sigma_0, c_e)`$ that the coalition wins under $`H`$'s states. For every subset of these slots, the chain from $`D_X`$ with one coalition block in each slot of the subset is valid. Each slot lies within $`G + 1`$ of $`\sigma_0`$, so its state is $`H`$'s (2.2). These $`2^A`$ chains end in $`2^A`$ distinct sequences of slots and contributions. They give $`2^A`$ values of $`\eta_{B'}`$ for epoch $`e + 1`$ (protocol 192), all distinct unless zkHASH collides. With each nonce comes its count, and with it $`D_X^{e+1}`$. So the coalition can choose $`X`$'s state for epoch $`e + 1`$ among at least $`2^A`$ candidates. ∎

$`A \sim \mathrm{Bin}(u - 1, p_a)`$ under A1. Against 30 % without a disturbance, $`E[A]`$ is 20 at $`u`$ = 2,000, 61 at 6,000, 101 at 10,000 and 200 at 19,799. $`P(A \ge 64)`$ is 0.35 at $`u`$ = 6,000 and above 0.999 from 10,000 on. $`E[A]`$ reaches 16, 40 and 64 at $`u`$ = 1,583, 3,954 and 6,326. With $`D`$ equal to the honest stake online, it reaches them at 1,111, 2,775 and 4,438, and is 286 at 19,799 (`out_3_inference.txt`, lines 70–76). So a model in which the coalition takes the best of $`M`$ nonces, with $`M`$ = $`2^{16}`$, $`2^{40}`$ or $`2^{64}`$, understates its choice once $`D_Y`$ lies more than about 1,600, 4,000 or 6,300 slots before the cut-off. The bound of 4.1 needs no model of the choice. Its extra term is 0 for every $`M`$, and also when the coalition sets the nonce outright. (Computed.)

**5.5 (Proved). GENESIS's witness can fail.** Let $`G \le 2K - 4`$. The rules allow block trees in which Step 2's bad fork $`X`$ has a block that is not made under $`H`$'s states:

1. $`D_Y`$ is a block of $`H`$ in slot $`\sigma_0 = c_e - 2`$.
2. $`Y`$ continues from $`D_Y`$ with a block in slot $`c_e - 1`$ and later blocks, all below $`\sigma_0 + K`$.
3. $`D`$ is a block of $`Y`$ in a slot of at least $`\sigma_0 + G + 3 - K`$, which is below $`\sigma_0 + K`$ because $`G + 3 < 2K`$.
4. $`X`$ continues from $`D`$ with a block in slot $`c_e + G = \sigma_0 + G + 2 \le sl_D + K - 1`$, and its tip lies at least $`\sigma_0 + K`$.

On $`X`$, the nonce of epoch $`e + 1`$ is $`\eta`$ of $`Y`$'s block in slot $`c_e - 1`$. On $`H`$, it is $`\eta`$ of a block of $`H`$. These are different blocks, with different nonces unless zkHASH collides. So A6 does not apply to $`(X, H)`$, and GENESIS's Step 2 does not conclude $`E_r`$ from it. If $`Y \in \mathcal G`$, 3.2 concludes $`E_r'`$ from $`(Y, H)`$. Whether the coalition wins the slots that this tree needs is a matter of the lottery. The rules do not exclude it.

*Proof.* $`X`$'s block in slot $`c_e + G`$ lies in epoch $`e + 1`$. $`X`$'s last block before $`c_e`$ is $`Y`$'s block in slot $`c_e - 1`$, which $`H`$ does not hold. Apply 2.1. ∎

The targeted executions of 6 build such trees: 856 of the replacements there had $`X`$ with a block under a state of its own (`out_4_checks.txt`, lines 20, 24, 28). (Computed.)

## 6. Checks

**6.1 (Computed). Random executions with $`G + 1 < 2K`$.** `t4_checks.py` runs executions with honest nodes that extend the longest chain they hold and receive honest blocks within $`\Delta`$, and a coalition that makes one to three blocks per won slot and withholds some. Every won slot is taken as valid on every chain, so the checks test the deterministic statements. A block is "under $`H`$'s states" when its chain and $`H`$ hold the same blocks below the cut-off that its epoch's state reads (2.1). The pass of the Bootstrap rule runs from a random tip, or from $`Y`$, over the tips in random orders. Four configurations are random, with $`K`$ = 30 to 40, $`s`$ = 10 or 12 and $`G = s + K - 1`$ to $`s + K + 5`$. Three are targeted at the structure of Step 2. The targeted runs give $`D_Y`$ 2 to $`2K - 2 - G`$ slots before a cut-off, and fork $`X`$ from one of $`Y`$'s last three blocks.

- Transitions of `c_max` out of $`\mathcal G`$, over 10,800 passes: 4,539. By density with $`sl_D \le \text{now} - K`$: 1,664. By length, with $`X`$ containing $`H`$ and $`E_g`$: 24. By length, with $`D`$ after $`D_Y`$, $`X`$ bad and $`(Y, H)`$ a witness of $`E_r'`$: 2,851, of which 856 had a block of $`X`$ not under $`H`$'s states. Violations: 0.
- Passes that end outside $`\mathcal G`$: 8,614. In every one, $`E_d`$, $`E_r'`$ or $`E_g`$ held.

(Lines 4–29 per configuration, line 31 in total.)

The check supports 3.2 and 3.3. It does not replace them.

## 7. What remains assumed or unproved

1. **A6** (GENESIS 3, 12.1, 12.10): the reading of GRR at one slot, and the study's construction that $`U(w)`$ bounds the margin at every slot. 4.1 rests on it exactly as GENESIS 7.3 does. $`E_r'`$ uses it at the same slot and wait as GENESIS's $`E_r`$.
2. **S and A1–A5** (GENESIS 3), unchanged. A4, an unbiased nonce, is used for $`H`$'s nonces only. No fork's nonce or inferred stake after its window enters 4.1.
3. **REVIEW's A4**: `commitment_root_at_slot` reads only blocks below its slot. 2.1, 2.2 and 5.1 use it, as GENESIS 4.2 does.
4. **The count law of REVIEW 7.3** for the quantiles of 5.3. 5.3 (1)–(4) are proved without it.
5. **The states of the $`K`$ row** use REVIEW 5.9's mapping (GENESIS 10.4).
6. **GENESIS 12** is otherwise unchanged. Its item 4, the coalition's choice among nonces, concerns $`H`$'s nonces. 4.1 needs nothing about the nonces of forks.
7. **Not addressed:** whether the bound for every fork can reach $`10^{-9}`$ at $`s_{gen}`$. It cannot by these bounds, as in GENESIS (4.2, 4.3).
8. **The checks of 6** test the deterministic statements on small parameters. They draw no probability.

## 8. Files

All files are in this folder. `run_all.sh` regenerates every output with the finality study's interpreter. The scripts import GENESIS's `common_g.py` and read its cached curves without writing to its folder. Bytecode writing is off, and numba's cache is `.cache/numba` here.

| File | Content | Statements |
| --- | --- | --- |
| `common_s.py` | constants, schedules, the states of the $`K`$ row, `git show` of the specification, read-only access to GENESIS's code and curves | all |
| `t1_schedule.py`, `out_1_schedule.txt` | (a) the specification's lines, and the lines that differ from GENESIS's `7f3cf149`; (b) the schedules' conditions; (c) the least span of shared state; (d) `compute_epoch_state` written out on random pairs of chains; (e) the reach of Step 2's fork | 1.1, 2.2, 5.1 |
| `t2_terms.py`, `out_2_terms.txt` | the terms of 4.1 per state and gap, the totals, the histories, the least windows and the gaps they need | 4.2, 4.3 |
| `t3_inference.py`, `out_3_inference.txt` | (a) the integer inference against its closed form; (b) its floor; (c) the quantiles of $`D_X/D_H`$; (d) the number of nonce candidates | 5.2–5.4 |
| `t4_checks.py`, `out_4_checks.txt` | random and targeted executions, the Bootstrap pass, the witness of Step 2′ | 3.2, 3.3, 5.5, 6.1 |
