# The Bootstrap theorem without $`2K \le G + 1`$

Date: 2026-11-19.

GENESIS proves that a node joining under the Bootstrap rule ends on the honest chain (its theorem 7.3), under $`s \le K - 1`$ and $`2K \le G + 1`$. This document asks whether the conclusion holds when $`2K \le G + 1`$ is replaced by $`s + K \le G + 1`$. It proves that it does, with the same terms and no extra term, and that $`G \ge K - 1`$ is enough.

## 0. Result in brief

- **The answer (7.4).** GENESIS 7.3 holds with $`s \le K - 1`$ and $`s + K \le G + 1`$. Its terms are unchanged, and there is no extra failure term. (Proved, given GENESIS's model, A1–A6 and S.)
- **A stronger form (7.5).** It holds for every gap $`G \ge K - 1`$. The only terms that read $`G`$ are $`P_1(G + 1 - s)`$ and, over a history, $`P_1(G + 2 - s - g)`$. (Proved, given the same model.)
- **Why the crossing case needs no bound (5.2 to 5.4).** In the crossing case of GENESIS 7.1 Step 2, a bad chain $`X`$ replaces a chain $`Y \in \mathcal G`$ by length, and $`X`$ leaves the reference chain $`H`$ where $`Y`$ does, at $`D_Y`$. $`X`$ is bad only if its tip lies $`K`$ or more slots after $`D_Y`$, so $`sl_{D_Y} \le \text{now} - K`$. Then $`Y`$ and $`H`$ are already two dominant chains that share no block from slot $`\text{now} - K + 1`$ on. $`Y`$ is not bad, so it is made under $`H`$'s epoch states. That is GENESIS's event $`E_r`$, with chance at most $`U(K - 2)`$. No block of $`X`$ after its divergence from $`Y`$ is read, so the epoch state that $`X`$ derives from its own blocks enters no bound. (Proved.)
- **The audit (3.1).** GENESIS uses $`2K \le G + 1`$ only in Step 2 of 7.1, and through it in the first bound of 7.2. Its other statements need at most $`s + K \le G + 2`$ (6.1 to 6.3 and 8.1) or $`G \ge K - 1`$ (3.1). The claim of the question is confirmed. One defect that does not depend on $`G`$ was found: the second bound of GENESIS 7.2 takes $`H`$'s states for slots that GENESIS 4.2 does not cover when the divergence block lies after $`D_Y`$ (3.2). That case also lies in $`E_r`$, so GENESIS's figures stand, and 7.3 below proves the bound without it. (Proved.)
- **What a fork's own state can differ in (4.1 to 4.3).** On a chain that leaves $`H`$ in epoch $`e`$, the snapshot of epoch $`e + 1`$ is $`H`$'s. The nonce and the inferred total stake $`D`$ of epoch $`e + 1`$ can differ. In the crossing case the fork holds at most $`2K - G - 3`$ slots of the observation window after $`D_Y`$: 19,798 at schedule (i) and 17,997 at (ii). At (ii) its $`D`$ can fall to 0.717 of $`H`$'s at $`\beta = 2/3`$ and to 0.789 at $`\beta = 1/2`$, at the $`10^{-9}`$ quantiles. That raises a 30 % coalition's chance per slot by up to 39 % and 27 %. Its nonce can take up to about $`2^{182}`$ values. None of this enters a bound. (Proved; Computed, `out_02_fork_state.txt`.)
- **The numbers (8).** At $`K`$ = 36,000 and $`s`$ = 16,200, every term equals GENESIS's except $`P_1(G + 1 - s)`$. That term is at most $`2.8\cdot10^{-20}`$ at (i) and $`3.2\cdot10^{-21}`$ at (ii) in every state of the $`K`$ row. The totals meet $`10^{-9}`$ exactly where GENESIS's do. The part from forks without honest blocks meets it in every state (at most $`9.0\cdot10^{-10}`$), and so does $`U(K - 2)`$ (at most $`2.5\cdot10^{-10}`$). The bound for every fork meets it in no state (at least $`1.35\cdot10^{-7}`$). (Computed, `out_01_terms.txt`.)
- **A check (6.3).** On 138,438 passes of the Bootstrap rule over random executions, every pass that ended outside $`\mathcal G`$ met one of the three events of the reduction. In 61 passes only the new witness of $`E_r`$ covered it. All 1,750 crossing events had that witness. (Computed, `out_03_reduction_check.txt`.)

## 1. Setting

### 1.1 Texts

| Short name | Text | Version |
| --- | --- | --- |
| GENESIS | `tools/simulators/finality/slot-finality/epoch/proofs/genesis/GENESIS.md` in the worktree `fast-finalization-slots`, and its scripts and cached curves | dated 2026-11-18, read 2026-11-19 |
| REVIEW | `tools/simulators/finality/slot-finality/epoch/REVIEW.md` in the same worktree | read 2026-11-19 |
| protocol, leadership, inference, fork choice, bootstrap | `docs/blockchain/raw/` of logos-lips: `cryptarchia-v1-protocol.md`, `cryptarchia-proof-of-leadership.md`, `cryptarchia-total-stake-inference.md`, `fork-choice.md`, `cryptarchia-v1-bootstr-sync.md` | branch Bedrock-RFC-Shorter-Epoch at `83596b6e` |

Line numbers of the specification are those of the files at `83596b6e`. At the lines GENESIS cites for the rules used here (fork choice 78, 113–140; protocol 432, 435, 453, 484–486; bootstrap 247) they agree with GENESIS's. (Cited.)

### 1.2 Symbols

GENESIS's symbols and definitions are kept: $`f`$, $`K`$, $`s = s_{gen}`$, $`\Delta`$, $`\alpha`$, $`p_h`$, $`p_a`$, $`A(I)`$, $`N(I)`$, $`d(t)`$, $`C[0{:}t]`$, $`U`$, $`U_{\Delta+1}`$, $`P_1`$, `now`, $`H`$, dominant, $`D_Z`$, bad, $`\mathcal G`$, holds, $`E_d`$, $`E_r`$, $`E_g`$. A statement of GENESIS is cited as "GENESIS x.y". The symbols below are this document's.

| Symbol | Meaning | Value |
| --- | --- | --- |
| $`E`$ | epoch length | $`4K`$ at `83596b6e` (protocol 159); 108,000 at (ii) |
| $`L_1`$ | snapshot phase: the slots from an epoch's first slot to its cut-off | $`2K`$ at `83596b6e` (protocol 154); 54,000 at (ii) |
| $`G`$ | gap from the cut-off to the next epoch, $`E - L_1`$ | $`2K`$ at `83596b6e` (protocol 155); 52,199 at (i); 54,000 at (ii) |
| $`sl_e`$, $`c_e`$ | first slot and cut-off of epoch $`e`$; $`c_e = sl_e + L_1`$ | |
| $`P`$ | `PERIOD`: the observation window is $`[sl_e, sl_e + P)`$, with $`P \le L_1`$ | $`2K`$ at `83596b6e` (inference 56); 54,000 at (ii) |
| $`\beta`$ | the inference's learning rate | 2/3 at `83596b6e` (inference 55); 1/2 for comparison |
| $`\hat f`$ | `truncate(f * PRECISION) / PRECISION` (inference 77) | 33/1000 |
| $`E_r^*`$ | the event of 5.1 | |
| $`E_d^*(\sigma)`$ | the event of 6.1 | |

Two schedules are evaluated. Schedule (i) has $`G`$ = 52,199, the least gap with $`s + K \le G + 1`$; its snapshot phase is left open. Schedule (ii) has $`L_1 = P = G`$ = 54,000, two phases of $`1.5K`$.

### 1.3 Labels

The labels are GENESIS's (GENESIS 1.3): Proved, Computed, Cited, Assumed, Estimate. A slot lasts one second.

## 2. What is used

**2.1 (Cited). From GENESIS.** The model of GENESIS 3 (A1 to A6 and S), the definitions of GENESIS 2.3, and the statements GENESIS 2.4, 3.1, 4.1 to 4.4, 5.1 to 5.4, 6.1 to 6.3, 7.1 (Steps 0, 1 and 3), 7.2 and 8.1 are used as stated, under the conditions on $`G`$ that 3.1 below lists. $`E_r`$ is the event that two chains of $`\mathcal D_\text{now}`$, made under $`H`$'s states, share no block with a slot of at least $`\text{now} - K + 1`$ (GENESIS 7.1). A chain of $`\mathcal D_\text{now}`$ is made by slot `now` and is at least as long as every chain that ends in an honest block made by slot $`\text{now} - \Delta - 1`$ (GENESIS 3, A6). A chain is made under $`H`$'s states when each of its blocks is honest or a coalition block in a slot that the coalition wins under $`H`$'s states (GENESIS 4.3).

**2.2 (Cited). The epoch state.**

- The epoch state of epoch $`ep`$ is $`(\mathbb C_\text{LEAD}, \eta, D)`$ (protocol 163).
- $`\mathbb C_\text{LEAD}^{ep}`$ is the commitment root at the first slot of epoch $`ep - 1`$ (protocol 225).
- $`\eta^{ep}`$ is $`\eta_{B'}`$, with $`B'`$ the last block before the cut-off of epoch $`ep - 1`$ (protocol 197, 229). $`\eta_B`$ hashes the parent's value, the block's contribution $`\rho_\text{LEAD}`$ and its slot (protocol 192). $`\rho_\text{LEAD} = \text{hash}(\text{NONCE\_CONTRIB\_V1} \| sl \| noteID \| sk)`$ (leadership 185).
- $`D^{ep}`$ is the inference applied to $`D^{ep-1}`$ and to the number $`N`$ of distinct occupied slots of the window of epoch $`ep - 1`$. A slot counts if it holds a block of the chain in the window, or an uncle that such a block references and whose slot lies in the window (protocol 233–247). A block outside the window contributes nothing (protocol 241). An uncle's slot lies before the slot of the block that references it (protocol 332).
- The inference returns $`\max(D'', 1)`$, computed in integers from $`D`$, $`N`$, $`P`$, $`f_p = 33`$ and $`\beta`$ = `beta.num / beta.den` (inference 77–87).
- The lottery of a slot reads the slot, $`\eta`$, the constants $`t_0`$ and $`t_1`$ computed from $`D`$, the root $`ledger_\text{AGED}`$ of the snapshot, and the latest root $`ledger_\text{LATEST}`$ of the chain that the block extends (leadership 137–154, 180–184). $`ledger_\text{LATEST}`$ is a property of the chain, not of the epoch state.
- **(Assumed: REVIEW's A4, as in GENESIS 4.2.)** The commitment root at a slot reads only blocks with smaller slots (REVIEW 4.3).

## 3. Where GENESIS reads $`G`$

**3.1 (Proved). The audit.** Each statement of GENESIS that reads $`G`$, and the condition its proof needs.

| GENESIS | What the proof reads | Needs | GENESIS states |
| --- | --- | --- | --- |
| 3.1 | the state of slot $`t`$ reads blocks below a cut-off of at most $`t - G`$; S covers slots up to $`t - K`$ | $`G \ge K - 1`$ | $`G \ge K`$ |
| 4.2 | the span $`(sl_D, sl_D + G + 1]`$ stays in two epochs | $`G < E`$ | $`G < E`$ |
| 6.1 | $`Y`$'s blocks up to $`sl_{D_Y} + K - 1`$; $`X`$'s window up to $`sl_D + s \le sl_{D_Y} + K - 1 + s`$ | $`s + K \le G + 2`$ | $`s + K \le G + 1`$ |
| 6.2 | 6.1 | as 6.1 | $`2K \le G + 1`$ |
| 6.3, first case | $`X`$'s window as in 6.1; the extension's slots, below $`b \le sl_{D_Y} + K - 1`$ when $`D`$ lies after $`D_Y`$, and below $`b \le \sigma + G + 1`$ otherwise | $`s + K \le G + 2`$ | $`2K \le G + 1`$ |
| 6.3, second and third cases | $`Y`$ alone, and the term $`P_1(G + 1 - s)`$ | $`K \le G + 2`$ | $`2K \le G + 1`$ |
| 7.1, Step 2 | $`X`$'s blocks up to $`sl_{D_Y} + 2K - 2`$ | $`2K \le G + 3`$ | $`2K \le G + 1`$ |
| 7.2, first bound | $`E_r`$'s chains made under $`H`$'s states, from Step 2 | as Step 2 | as 7.1 |
| 7.2, second bound | an extension over $`(e, \text{now}]`$ with $`\text{now} \le \sigma + G`$ | not covered when $`D`$ lies after $`D_Y`$ (3.2) | as 7.1 |
| 8.1 | the terms $`P_1(G + 2 - s - g)`$ | as 6.3 | as 7.1 |

So $`2K \le G + 1`$ is used in Step 2 of GENESIS 7.1 alone, and in the first bound of GENESIS 7.2 through it. Every other use needs at most $`s + K \le G + 2`$ or $`G \ge K - 1`$.

*Proof.* GENESIS 3.1: a slot $`t`$ of epoch $`ep`$ reads blocks with slots below the cut-off $`c_{ep-1}`$, and the root at the first slot of epoch $`ep - 1`$, which is earlier (2.2). Epoch $`ep`$ starts at $`c_{ep-1} + G \le t`$, so these blocks have slots of at most $`t - G - 1`$. S fixes the blocks with slots up to $`t - K`$, so $`t - G - 1 \le t - K`$ suffices.
GENESIS 6.1: $`Y`$ is not bad, so its blocks after $`D_Y`$ have slots in $`(sl_{D_Y}, sl_{D_Y} + K - 1]`$. This lies in the span $`(sl_{D_Y}, sl_{D_Y} + G + 1]`$ of GENESIS 4.2 when $`K \le G + 2`$. $`D`$ is $`D_Y`$, an ancestor of it, or a block of $`Y`$ after it, so $`sl_D \le sl_{D_Y} + K - 1`$ and $`X`$'s window ends at most at $`sl_{D_Y} + K - 1 + s`$. That lies in the span when $`s + K \le G + 2`$, which also gives $`K \le G + 2`$.
GENESIS 6.3, first case: the extension starts with $`X[0{:}e]`$, whose window 6.1 covers. $`b`$ is the slot of a block of $`Y`$, so $`b \le sl_Y \le sl_{D_Y} + K - 1`$. If $`D`$ lies after $`D_Y`$, the extension leaves $`H`$ at $`D_Y`$ and its added blocks lie in $`(e, b) \subset (sl_{D_Y}, sl_{D_Y} + K - 1]`$, which needs $`K \le G + 2`$. If $`D`$ is $`D_Y`$ or an ancestor of it, the extension leaves $`H`$ at $`D`$ or later, and the case's condition $`b \le \sigma + G + 1`$ puts its added blocks in the span. The second case reads $`Y`$ alone, made under $`H`$'s states when $`K \le G + 2`$, and the lottery of $`H`$. The third case reads the same.
GENESIS 7.1, Step 2: $`sl_X < sl_D + K`$, $`sl_D \le sl_Y`$ and $`sl_Y \le sl_{D_Y} + K - 1`$, so $`X`$'s blocks have slots of at most $`sl_{D_Y} + 2K - 2`$. They lie in the span when $`2K - 2 \le G + 1`$.
GENESIS 7.2 and 8.1: the first bound bounds the event of Step 2; the second is 3.2; 8.1 applies the cases of 6.3 at the edge of a cell. ∎

**3.2 (Proved). The second bound of GENESIS 7.2 has a gap that does not depend on $`G`$.** GENESIS 7.2 extends $`X[0{:}e]`$ by withheld blocks in the slots of $`(e, \text{now}]`$, where $`\text{now} + 1 \le \sigma + G + 1`$. It takes them as made under $`H`$'s states because "these slots lie within $`G + 1`$ of $`D`$". By GENESIS 4.2 that gives the extension the states of $`Y`$ on $`(\sigma, \sigma + G + 1]`$. $`Y`$ is guaranteed $`H`$'s states only up to $`sl_{D_Y} + G + 1`$. If $`D`$ lies after $`D_Y`$ on $`Y`$ and $`\text{now} > sl_{D_Y} + G + 1`$, the slots of $`(sl_{D_Y} + G + 1, \text{now}]`$ are covered by neither. Nothing in the argument relates $`K`$ and $`G`$ here.

The case is harmless. Then $`sl_{D_Y} < \sigma \le \text{now} - K`$, so $`Y`$ is a chain of $`\mathcal G`$ that left $`H`$ at a slot of at most $`\text{now} - K`$. That is $`E_r^*`$ (5.1) if $`Y`$ does not contain $`H`$, and $`E_g`$ otherwise (5.2). Both are in GENESIS's bound. 7.3 proves the second bound with the case removed. ∎

## 4. What a fork's own epoch state can differ in

**4.1 (Proved). Which parts can differ.** Let a chain $`Z`$ share exactly the blocks up to a block $`A`$ with $`H`$, and let $`A`$ lie in epoch $`e`$.

1. For every slot of epoch $`e`$, $`Z`$ derives $`H`$'s state.
2. For epoch $`e + 1`$: $`\mathbb C_\text{LEAD}^{e+1}`$ is always $`H`$'s. $`\eta^{e+1}`$ is $`H`$'s if $`sl_A \ge c_e - 1`$, and can differ otherwise. $`D^{e+1}`$ is $`H`$'s if $`sl_A \ge sl_e + P - 1`$. Otherwise $`Z`$'s count is at least $`N_0`$, the number of distinct occupied slots of $`[sl_e, sl_A]`$ that the blocks of $`Z`$ up to $`A`$ in the window and the uncles they reference give.
3. If $`2K \le E + 2`$ and every block of $`Z`$ after $`A`$ has a slot of at most $`sl_A + 2K - 2`$, then no block of $`Z`$ lies in epoch $`e + 2`$ or later.
4. If, in addition, a block of $`Z`$ lies in epoch $`e + 1`$, then at most $`2K - G - 3`$ slots of $`[sl_e, c_e)`$ lie after $`A`$.

*Proof.* (1) The state of epoch $`e`$ reads blocks below $`c_{e-1} < sl_e \le sl_A`$ (2.2), which $`Z`$ and $`H`$ share.
(2) The snapshot is the root at $`sl_e \le sl_A`$. It reads blocks with slots below $`sl_e`$ (REVIEW's A4), and these are shared. It would be shared also if it read the block of slot $`sl_e`$, since $`Z`$'s own blocks have slots above $`sl_A \ge sl_e`$. $`\eta^{e+1}`$ is $`\eta_{B'}`$, with $`B'`$ the chain's last block below $`c_e`$. If $`sl_A \ge c_e - 1`$, $`Z`$'s blocks after $`A`$ have slots of at least $`c_e`$, so $`B'`$ is shared. Otherwise $`Z`$ can hold blocks in $`(sl_A, c_e)`$, and then $`B'`$ is one of them. If $`sl_A \ge sl_e + P - 1`$, $`Z`$'s blocks after $`A`$ lie after the window and contribute nothing (protocol 241), so the counts agree. Otherwise the blocks of $`Z`$ in $`[sl_e, sl_A]`$ are shared, and so are the uncles they reference. Those uncles have slots below their referencing blocks (protocol 332), so in $`[sl_e, sl_A]`$. So $`Z`$'s count contains these $`N_0`$ slots.
(3) Epoch $`e + 2`$ starts at $`sl_e + 2E`$, and $`sl_A \le sl_e + E - 1`$. So $`sl_A + 2K - 2 \le sl_e + E + 2K - 3 < sl_e + 2E`$ when $`2K \le E + 2`$.
(4) Epoch $`e + 1`$ starts at $`c_e + G`$. A block of $`Z`$ there has a slot of at least $`c_e + G`$ and at most $`sl_A + 2K - 2`$. So $`c_e - 1 - sl_A \le 2K - G - 3`$. ∎

The crossing chain $`X`$ of GENESIS 7.1 Step 2 meets the hypotheses of (3) and (4) with $`A = D_Y`$ (3.1). Schedule (ii) has $`2K \le E + 2`$, and schedule (i) has it for every snapshot phase of at least 19,799 slots.

**4.2 (Proved). How far $`D`$ can fall.** For integers $`D \ge 1`$, $`0 \le N \le P`$ and $`\beta \le 2/3`$, the inference returns $`\max(D'', 1)`$ with

$$
x - 1.002 < D'' < x + 0.002, \qquad x = D\Big((1 - \beta) + \beta\,\frac{N}{P \hat f}\Big).
$$

$`x`$ grows with $`N`$. So in case (2) of 4.1, $`D_Z^{e+1} > D^e\big((1 - \beta) + \beta N_0/(P\hat f)\big) - 1.002`$, while $`H`$'s count is $`N_0`$ plus the slots that $`H`$'s blocks after $`A`$ in the window, and their uncles, add.

*Proof.* Write $`e_p = 33P`$, $`m = 1000N`$ and $`v = 1000D(e_p - m)/e_p = 1000D(1 - N/(P\hat f))`$. Integer division truncates toward zero. So `slot_activation_error_p` is $`v - \theta_1`$ and `correction_p` is $`\beta(v - \theta_1) - \theta_2`$, with $`|\theta_1|, |\theta_2| < 1`$. Then `tse_p - correction_p` is $`z = 1000x + \beta\theta_1 + \theta_2`$. Since $`1000x \ge 1000D(1 - \beta) \ge 333`$, $`z > 0`$, and the last division is a floor: $`z/1000 - 1 < D'' \le z/1000`$. With $`|\beta\theta_1 + \theta_2| < 1 + \beta \le 2`$ this gives the bounds. ∎

`s02_fork_state.py` runs the algorithm as printed on 200,000 random inputs. The largest distance from $`x`$ is 1.0000 at both values of $`\beta`$ (`out_02_fork_state.txt`, line 1). (Computed.)

**4.3 (Computed). The values in the crossing case.** By 4.1 (4) the fork holds at most $`2K - G - 3`$ slots of the window after $`D_Y`$, and the rest of the window is shared. The table takes the inference at its fixed point, where $`H`$'s count has mean $`P\hat f`$ and $`D_H^{e+1}`$ equals $`D^e`$ on average (REVIEW 7.4), and a fork that adds no occupied slot after $`D_Y`$. "Means" puts the counts at their means. "Quantiles" puts the shared count at its $`10^{-9}`$ lower quantile and $`H`$'s count after $`D_Y`$ at its $`10^{-9}`$ upper quantile, with counts binomial as in REVIEW 7.3. The last column is the coalition's chance per slot under the fork's $`D`$, for a coalition of 30 % of $`D_H`$, against $`p_a`$ = 0.010119 (`out_02_fork_state.txt`, lines 3–18).

| Schedule | $`P`$ | slots after $`D_Y`$, at most | $`\beta`$ | $`D_X/D_H`$, means | $`D_X/D_H`$, quantiles | chance per slot, quantiles |
| --- | --- | --- | --- | --- | --- | --- |
| (i) | 54,000 | 19,798 | 1/2 | 0.8167 | 0.7706 | $`1.30\,p_a`$ |
| (i) | 54,000 | 19,798 | 2/3 | 0.7556 | 0.6931 | $`1.44\,p_a`$ |
| (i) | 72,000 | 19,798 | 1/2 | 0.8625 | 0.8267 | $`1.21\,p_a`$ |
| (i) | 72,000 | 19,798 | 2/3 | 0.8167 | 0.7675 | $`1.30\,p_a`$ |
| (ii) | 54,000 | 17,997 | 1/2 | 0.8334 | 0.7886 | $`1.27\,p_a`$ |
| (ii) | 54,000 | 17,997 | 2/3 | 0.7778 | 0.7168 | $`1.39\,p_a`$ |

The coalition wins about 200 slots at (i) and 182 at (ii) in the slots after $`D_Y`$ (same lines). Each of these wins is a win under the shared state of epoch $`e`$, so any subset of them, in slot order, makes a valid chain, and each subset gives its own last block $`B'`$. So the fork's nonce of epoch $`e + 1`$ can take up to about $`2^{200}`$ or $`2^{182}`$ values, and a coalition that chooses among them is limited by computation, not by its wins.

**4.4 (Proved). None of this is used.** A direct treatment of the crossing case would have to bound how fast $`X`$ grows over up to $`2K - G - 3`$ slots of epoch $`e + 1`$ under a lowered $`D`$ and a nonce chosen among many. 5.4 shows that the case lies in $`E_r`$, so no bound below reads the fork's state of epoch $`e + 1`$. Truncating $`X`$ at $`sl_{D_Y} + G + 1`$ would keep it under $`H`$'s states, but the truncated chain can be shorter than a dominant chain by the coalition's wins in up to $`2K - G - 3`$ slots, so it does not witness $`E_r`$ by itself. ∎

## 5. The crossing case lies in $`E_r`$

**5.1 (Definition).** $`E_r^*`$ is the event that some chain $`Z \in \mathcal G`$ of $`J`$'s block tree does not contain $`H`$ and has $`sl_{D_Z} \le \text{now} - K`$.

**5.2 (Proved). The lemma.** On S, if neither $`E_r^*`$ nor $`E_g`$ occurs, every chain $`Z \in \mathcal G`$ has $`sl_{D_Z} > \text{now} - K`$.

*Proof.* If $`Z`$ contains $`H`$, $`D_Z`$ is $`H`$'s last block, and GENESIS 7.1 Step 0 shows that its slot exceeds $`\text{now} - K`$ unless $`E_g`$ occurs. If $`Z`$ does not contain $`H`$, $`sl_{D_Z} \le \text{now} - K`$ is $`E_r^*`$. ∎

**5.3 (Proved, given A6). $`E_r^*`$ lies in $`E_r`$, with chance at most $`U(K - 2)`$.** Let $`K \le G + 2`$. Every outcome of $`E_r^*`$ is an outcome of $`E_r`$. $`P(E_r^*) \le U(K - 2)`$, and $`E_r^*`$ lies in the event that GENESIS 7.2 bounds by $`U_{\Delta+1}(K - 1)`$.

*Proof.* Let $`Z`$ witness $`E_r^*`$. $`Z`$ is not bad, so its blocks after $`D_Z`$ have slots in $`(sl_{D_Z}, sl_{D_Z} + K - 1]`$. $`Z`$ and $`H`$ share exactly the blocks up to $`D_Z`$, and $`K \le G + 2`$ puts these slots in the span of GENESIS 4.2. By GENESIS 4.3, $`Z`$ is made under $`H`$'s states. Its tip has a slot of at most $`sl_{D_Z} + K - 1 \le \text{now} - 1`$. $`Z`$ is dominant, so $`\text{len}(Z) \ge d(\text{now} - \Delta - 1)`$. $`H`$ ends in a slot of at most $`\text{now} - \Delta - 1`$ and has length $`d(\text{now} - \Delta - 1)`$. The two chains share no block with a slot of at least $`\ell = \text{now} - K + 1`$, since $`sl_{D_Z} \le \text{now} - K`$. So $`Z`$ and $`H`$ witness $`E_r`$. Both are made by slot $`\text{now} - 1`$, so A6 at slot `now` gives $`\mu_\ell \ge 0`$ at slot $`\text{now} - 1 = \ell + K - 2`$, with chance at most $`U(K - 2)`$. At delay $`\Delta + 1`$ and slot $`\text{now} + 1`$, both are made by slot `now` and are at least as long as every chain that ends in an honest block made by slot $`(\text{now} + 1) - (\Delta + 1) - 1`$. So A6 at that delay gives $`\mu_\ell \ge 0`$ at slot `now`, the event of GENESIS 7.2's second bound. ∎

**5.4 (Proved). The crossing case.** In GENESIS 7.1 Step 2, let `c_max` be $`Y \in \mathcal G`$, let $`Y`$ not contain $`H`$, let $`X`$ replace $`Y`$ by length, let $`D = D(X, Y)`$ lie after $`D_Y`$ on $`Y`$, and let $`X`$ be bad. Then $`Y`$ witnesses $`E_r^*`$.

*Proof.* $`X`$ contains $`D`$, hence $`D_Y`$ and the block of $`Y`$ after $`D_Y`$, which is not a block of $`H`$. So $`D_X = D_Y`$. $`X`$ is bad, so $`sl_{D_Y} + K \le sl_X`$. A valid block has a slot of at most `now` (protocol 435), so $`sl_{D_Y} \le \text{now} - K`$. ∎

The proof reads no block of $`X`$ after $`D`$. GENESIS's proof took $`X`$ and $`H`$ as the witnesses of $`E_r`$, which needs $`X`$ made under $`H`$'s states, and so the span $`2K \le G + 3`$ (3.1).

## 6. The reduction

**6.1 (Definition).** $`E_d^*(\sigma)`$ is the event that some chains $`X`$ and $`Y \in \mathcal G`$ of $`J`$'s block tree have their last common block $`D`$ in slot $`\sigma`$, that $`D`$ is a block of $`H`$ and a strict ancestor of $`D_Y`$, and that $`X`$ has at least as many blocks as $`Y`$ in $`(\sigma, \sigma + s]`$. Then $`D_X = D`$: $`Y`$ holds the block of $`H`$ after $`D`$, and $`X`$ does not. $`E_d^*(\sigma)`$ is part of GENESIS's $`E_d(\sigma)`$.

**6.2 (Proved). The reduction.** On S, $`J`$ holds unless $`E_d^*(\sigma)`$ occurs for some slot $`\sigma`$ from $`J`$'s starting block to $`\text{now} - K`$, or $`E_r^*`$ occurs, or $`E_g`$ occurs. This needs no condition on $`G`$ or $`s`$.

*Proof.* Assume that none of them occurs. GENESIS's Steps 0 and 3 are unchanged. Steps 1 and 2 become:

*Step 1. After the last $`H`$-tip is visited, `c_max` lies in $`\mathcal G`$.* GENESIS's proof applies, except that its comparison by density now gives $`E_d^*`$. There the `c_max` before the visit, $`Y_0`$, is at least as dense as the $`H`$-tip $`h' \in \mathcal G`$, with $`D = D(Y_0, h')`$ and $`sl_D + K \le \text{now}`$. $`D_{h'}`$ is $`H`$'s last block, whose slot exceeds $`\text{now} - K`$ by Step 0. So $`D`$ precedes it on $`h'`$: $`D`$ is a block of $`H`$ and a strict ancestor of $`D_{h'}`$. That is $`E_d^*(sl_D)`$.

*Step 2. A visit keeps `c_max` in $`\mathcal G`$.* Let `c_max` be $`Y \in \mathcal G`$, visit $`X`$, and let $`D = D(X, Y)`$. By 5.2, $`sl_{D_Y} > \text{now} - K`$.

- If $`X`$ does not replace $`Y`$, nothing changes.
- A replacement by density means that $`X`$ is strictly denser than $`Y`$ and $`sl_D + K \le \text{now}`$. Then $`sl_D \le \text{now} - K < sl_{D_Y}`$. $`D`$ is a block of $`Y`$ with a smaller slot than $`D_Y`$, so it is a strict ancestor of $`D_Y`$ and a block of $`H`$. That is $`E_d^*(sl_D)`$.
- A replacement by length makes $`X`$ longer than $`Y`$, hence dominant, with $`sl_D + K > sl_X`$. If $`D`$ is $`D_Y`$ or an ancestor of it, $`D`$ is a block of $`H`$ on $`X`$, so $`sl_{D_X} \ge sl_D > sl_X - K`$ and $`X`$ is not bad. Otherwise $`D`$ lies after $`D_Y`$ on $`Y`$. If $`Y`$ contains $`H`$, so does $`X`$, and Step 0 puts $`X`$ in $`\mathcal G`$. If not, $`D_X = D_Y`$ as in 5.4, so $`sl_{D_X} > \text{now} - K \ge sl_X - K`$, and $`X`$ is not bad.

In every case the new `c_max` lies in $`\mathcal G`$. ∎

The invariant is GENESIS's. The difference is 5.2: outside $`E_r^*`$ and $`E_g`$, every chain of $`\mathcal G`$ left $`H`$ after $`\text{now} - K`$, so a chain that leaves $`Y`$ after $`D_Y`$ is not bad.

**6.3 (Computed). A check on random executions.** `s03_reduction_check.py` draws executions with honest nodes that extend a longest chain they hold, honest blocks delivered within $`\Delta + 1`$ slots, and a coalition that makes forks at random. In five of its eight settings the coalition also runs the crossing case of 5.4 on purpose: a withheld branch $`Y`$ from an honest block, and a second branch $`X`$ from a block of $`Y`$. In two of these, $`Y`$ holds no block in the $`s`$ slots after its divergence, so that it stays longer than $`H`$ without being denser in the window. $`J`$'s tree holds every honest block and most coalition blocks. Each pass starts at a random tip and visits the tips in a random order with the Bootstrap test. For every choice of $`H`$, the script checks the reduction with the events restricted to tips, which is the sharper form, since the pass compares only tips. Over 138,438 passes, 55,780 ended outside $`\mathcal G`$. Each of them met $`E_d^*`$, $`E_r^*`$ or $`E_g`$, and 61 met only $`E_r^*`$. Step 0 held in all 23,072 cases without $`E_g`$. All 1,750 crossing events had $`Y`$ as a witness of $`E_r^*`$ (`out_03_reduction_check.txt`, lines 1–9). The check has no epochs. The reduction reads no epoch state, so it loses nothing for 6.2; it does not check section 7. (Computed.)

## 7. The bounds and the theorems

**7.1 (Proved). GENESIS 6.1 for $`E_d^*`$.** On S, let $`X`$ and $`Y \in \mathcal G`$ be chains of $`J`$'s block tree whose last common block $`D`$ is a block of $`H`$ and a strict ancestor of $`D_Y`$. Let $`e = sl_D + s \le \text{now}`$, $`s \le G + 1`$ and $`K \le G + 2`$. If $`X`$ has at least as many blocks as $`Y`$ in $`(sl_D, e]`$, then

$$
A((t_g, b)) \ge N((t_g + \Delta,\ b - \Delta - 2]),
$$

with $`g`$ the last honest block of $`X[0{:}e]`$ and $`b`$ that of GENESIS 5.4 for $`Y`$. If $`X`$ has no honest block in $`(sl_D, e]`$, then $`t_g \le sl_D`$.

*Proof.* GENESIS's proof needs that GENESIS 5.4 applies to $`Y`$ and GENESIS 5.3 to $`X[0{:}e]`$. $`Y`$ is not bad, so its blocks after $`D_Y`$ lie in $`(sl_{D_Y}, sl_{D_Y} + K - 1]`$. With $`K \le G + 2`$ that is in the span of GENESIS 4.2 for $`Y`$ and $`H`$, so $`Y`$ is made under $`H`$'s states and GENESIS 5.4 applies. $`X`$ leaves $`H`$ at $`D`$ (6.1). Its blocks after $`D`$ in $`X[0{:}e]`$ lie in $`(sl_D, sl_D + s]`$, which $`s \le G + 1`$ puts in the span of GENESIS 4.2 for $`X`$ and $`H`$. By GENESIS 4.3, with $`H`$ in the place of $`Y`$, each of them is honest or a coalition block in a slot that the coalition wins under $`H`$'s states, and GENESIS 5.3 applies. The rest of GENESIS's proof is unchanged. ∎

**7.2 (Proved, given A6). GENESIS 6.2, 6.3 and 8.1 for $`E_d^*`$.** Let $`s \le K - 1`$ and $`K - 1 \le G < E`$, and fix a slot $`\sigma \le \text{now} - K`$. The part of $`E_d^*(\sigma)`$ in which $`X`$ has no honest block in $`(\sigma, \sigma + s]`$ has chance at most $`P_1(s)`$. Moreover

$$
P(E_d^*(\sigma)) \le U(s - 1) + P_1(K - s) + P_1(G + 1 - s),
$$

and the cells of GENESIS 8.1 bound the union over a history as GENESIS 8.1 states, with $`E_d^*`$ in the place of $`E_d`$.

*Proof.* $`K - 1 \le G`$ gives $`K \le G + 2`$, and with $`s \le K - 1`$ it gives $`s \le G + 1`$, so 7.1 applies. GENESIS's proofs of 6.2, 6.3 and 8.1 then hold with 7.1 in the place of GENESIS 6.1, after one change. In the first case of GENESIS 6.3, $`Y`$ has an honest block in slot $`b \le \sigma + G + 1`$. The extension $`\tilde X`$ of $`X[0{:}e]`$ leaves $`H`$ at $`D`$, and its added blocks lie in $`(e, b) \subset (\sigma, \sigma + G + 1]`$. By GENESIS 4.2 with $`H`$ they are wins under $`H`$'s states. $`Y[0{:}b-1]`$ is made under $`H`$'s states, as in 7.1. The second and third cases read $`Y`$ alone, which is made under $`H`$'s states, and the lottery of $`H`$. GENESIS 8.1 applies the same cases with the edge of a cell in the place of $`\sigma`$. ∎

**7.3 (Proved, given A6). The second bound of GENESIS 7.2.** Let $`s \le K - 1`$ and $`K - 1 \le G < E`$. $`E_r^*`$, together with the parts of $`E_d^*(\sigma)`$, at every $`\sigma \le \text{now} - K`$, in which $`Y`$ has no honest block after $`\sigma + s`$ and $`\text{now} + 1 \le \sigma + G + 1`$, has chance at most $`U_{\Delta+1}(K - 1)`$.

*Proof.* For $`E_r^*`$ this is 5.3. In the other parts, extend $`X[0{:}e]`$ as GENESIS 7.2 does, by a withheld block in each slot of $`(e, \text{now}]`$ that the coalition wins under $`H`$'s states. The extension $`\tilde X`$ leaves $`H`$ at $`D`$, and its added blocks lie in $`(\sigma, \sigma + G]`$. By GENESIS 4.2 with $`H`$ they are valid wins under $`H`$'s states. $`Y`$'s blocks after $`e`$ are coalition blocks in distinct slots of $`(e, \text{now}]`$ that the coalition wins under $`H`$'s states (7.1). So

$$
\text{len}(\tilde X) \ge \text{len}(X[0{:}e]) + A((e, \text{now}]) \ge \text{len}(Y[0{:}e]) + A((e, \text{now}]) \ge \text{len}(Y) \ge d(\text{now} - \Delta - 1).
$$

$`\tilde X`$ and $`Y`$ are made by slot `now` under $`H`$'s states, and each is at least as long as every chain that ends in an honest block made by slot $`\text{now} - \Delta - 1`$. They share no block with a slot of at least $`\sigma + 1`$, hence none with a slot of at least $`\text{now} - K + 1`$. By A6 at delay $`\Delta + 1`$ and slot $`\text{now} + 1`$, $`\mu_{\text{now} - K + 1} \ge 0`$ at slot `now` at that delay. 5.3 gives the same event for $`E_r^*`$. Its chance is at most $`U_{\Delta+1}(K - 1)`$. ∎

The divergence blocks that GENESIS's $`E_d`$ admits beyond $`E_d^*`$ lie at or after $`D_Y`$, and the gap of 3.2 is among them. With $`\sigma \le \text{now} - K`$ they have $`sl_{D_Y} \le \text{now} - K`$, so they lie in $`E_r^*`$ or $`E_g`$ (5.2).

**7.4 (Proved, given A6). The theorem with $`s + K \le G + 1`$.** In the model of GENESIS 3, with $`s \le K - 1`$ and $`s + K \le G + 1`$,

$$
P(\text{S holds and } J \text{ does not hold}) \le P\Big(\bigcup_\sigma E_d^*(\sigma)\Big) + U(K - 2) + (1 - p_h)^{K - 2\Delta - 1},
$$

where the union is over the slots from $`J`$'s starting block to $`\text{now} - K`$. $`P(\bigcup_\sigma E_d^*(\sigma)) \le \sum_\sigma P(E_d^*(\sigma))`$, and $`P(E_d^*(\sigma)) \le U(s - 1) + P_1(K - s) + P_1(G + 1 - s)`$. The part with no honest block of $`X`$ in the window is at most $`P_1(s)`$. $`U(K - 2)`$ and the terms $`P_1(K - s)`$ may together be replaced by $`U_{\Delta+1}(K - 1)`$. The cells of GENESIS 8.1 apply. If $`J`$ holds, GENESIS 2.4 applies. These are the terms of GENESIS 7.3, and there is no extra term.

*Proof.* $`s + K \le G + 1`$ gives $`K - 1 \le G`$. A schedule has $`E = L_1 + G`$ with $`L_1 \ge 1`$, so $`G < E`$. GENESIS 3.1 holds with $`G \ge K - 1`$ (3.1). 6.2 gives the three events. 5.3 bounds $`E_r^*`$ by $`U(K - 2)`$, and GENESIS 7.2 bounds $`E_g`$. 7.2 bounds $`E_d^*`$, and 7.3 gives the replacement. ∎

**7.5 (Proved, given A6). The theorem for every gap of at least $`K - 1`$.** The statement of 7.4 holds with $`s \le K - 1`$ and $`G \ge K - 1`$ in place of $`s \le K - 1`$ and $`s + K \le G + 1`$.

*Proof.* The proof of 7.4 used $`s + K \le G + 1`$ only to obtain $`K - 1 \le G`$. ∎

At $`G = K - 1`$ the term $`P_1(G + 1 - s)`$ equals $`P_1(K - s)`$.

## 8. The numbers

**8.1 (Computed). The terms at the two schedules.** $`K`$ = 36,000, $`s`$ = 16,200, and the states of the $`K`$ row with REVIEW 5.9's mapping, against 30 % (GENESIS 10.4's list; Assumed: the mapping). The extra term of 7.4 and 7.5 is 0 in every row. The last column is the bound for every fork per divergence slot with its once-terms, the smaller of $`U(s - 1) + P_1(K - s) + P_1(G + 1 - s) + U(K - 2)`$ and $`U(s - 1) + P_1(G + 1 - s) + U_{\Delta+1}(K - 1)`$, as GENESIS's `g07_states.py` forms it; it is the same at both schedules. (`out_01_terms.txt`, lines 4–6, 14–16, 24–26, 34–36, 44–46.)

| State | $`P_1(s)`$ | $`U(s - 1)`$ | $`P_1(K - s)`$ | $`U(K - 2)`$ | $`U_{\Delta+1}(K - 1)`$ | $`P_1(G + 1 - s)`$, (i) | $`P_1(G + 1 - s)`$, (ii) | every fork |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no disturbance | $`2.055\cdot10^{-13}`$ | $`1.349\cdot10^{-7}`$ | $`3.95\cdot10^{-16}`$ | $`8.28\cdot10^{-16}`$ | $`1.35\cdot10^{-14}`$ | $`2.7\cdot10^{-28}`$ | $`1.2\cdot10^{-29}`$ | $`1.349\cdot10^{-7}`$ |
| every block $`T_M`$ late | $`2.564\cdot10^{-10}`$ | $`4.341\cdot10^{-5}`$ | $`2.30\cdot10^{-12}`$ | $`2.51\cdot10^{-10}`$ | $`2.08\cdot10^{-9}`$ | $`1.6\cdot10^{-21}`$ | $`1.6\cdot10^{-22}`$ | $`4.341\cdot10^{-5}`$ |
| a tenth offline, inference corrected | $`5.205\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ | $`5.55\cdot10^{-12}`$ | $`2.01\cdot10^{-11}`$ | $`1.80\cdot10^{-10}`$ | $`8.4\cdot10^{-21}`$ | $`8.9\cdot10^{-22}`$ | $`1.285\cdot10^{-5}`$ |
| a tenth offline, before the correction | $`8.995\cdot10^{-10}`$ | $`1.285\cdot10^{-5}`$ | $`1.08\cdot10^{-11}`$ | $`2.08\cdot10^{-11}`$ | $`1.51\cdot10^{-10}`$ | $`2.8\cdot10^{-20}`$ | $`3.2\cdot10^{-21}`$ | $`1.285\cdot10^{-5}`$ |
| $`D`$ equals the honest stake online | $`8.523\cdot10^{-15}`$ | $`4.506\cdot10^{-7}`$ | $`8.04\cdot10^{-18}`$ | $`9.90\cdot10^{-15}`$ | $`7.26\cdot10^{-13}`$ | $`2.2\cdot10^{-31}`$ | $`7.1\cdot10^{-33}`$ | $`4.506\cdot10^{-7}`$ |

- Every column but the two of $`P_1(G + 1 - s)`$ equals GENESIS's `out_07_states.txt`, lines 2, 6, 10, 14 and 18. At GENESIS's $`G`$ the script returns GENESIS's $`P_1(G + 1 - s)`$ (`out_01_terms.txt`, lines 7, 17, 27, 37, 47).
- Against $`10^{-9}`$ nothing changes. The part from forks without honest blocks meets it in every state, the closest being $`9.0\cdot10^{-10}`$. $`U(K - 2)`$ meets it in every state, the closest being $`2.5\cdot10^{-10}`$. $`U_{\Delta+1}(K - 1)`$ misses it in the first disturbance, $`2.1\cdot10^{-9}`$. The bound for every fork misses it in every state.
- Under 7.4, schedule (i) admits no window above $`s_{gen}`$, since $`s \le G + 1 - K`$ = 16,200. Under 7.5 the least window for every fork at $`10^{-9}`$ per divergence slot is 21,336 slots without disturbance, none in the first disturbance, 30,509 and 30,494 with a tenth offline (30,508 and 30,492 at (ii)), and 23,062 with $`D`$ equal to the honest stake online. These are GENESIS 10.4's figures at $`K`$ = 36,000, except one and two slots more at (i) in the two states with a tenth offline (`out_01_terms.txt`, lines 5–6, 15–16, 25–26, 35–36, 45–46).
- Over a history the cells of GENESIS 8.1 give the same figures at both schedules as at GENESIS's $`G`$. Without disturbance they are $`8.39\cdot10^{-11}`$ for a day and $`3.06\cdot10^{-8}`$ for a year for forks without honest blocks, and $`3.024\cdot10^{-5}`$ and $`1.104\cdot10^{-2}`$ for every fork (`out_01_terms.txt`, lines 10–11; GENESIS's `out_04_union.txt`, lines 5 and 7). The first disturbance gives GENESIS's figures as well (lines 20–21; GENESIS's lines 16 and 18), and the other states are at lines 30–31, 40–41 and 50–51.
- At $`G = K - 1`$ the term $`P_1(G + 1 - s) = P_1(K - s)`$ is at most $`1.1\cdot10^{-11}`$ at $`s_{gen}`$, and the bound for every fork per divergence slot is unchanged (lines 9, 19, 29, 39, 49).

## 9. What remains assumed or unproved

1. **GENESIS's model.** A1 to A6 and S, with the open points of GENESIS 12: A6 is a reading of GRR, and that $`U`$ bounds the margin at every slot rests on the study's clock. A3 (keys) is not enforced by the specification. A4 (an unbiased nonce) is needed for $`H`$'s nonce only; no bound here reads the nonce of a fork. S is cited from the $`K`$ row. This document adds no assumption to the model.
2. **REVIEW's A4 on the commitment root,** used through GENESIS 4.2 and in 4.1 for the snapshot.
3. **The states of the $`K`$ row** use REVIEW 5.9's mapping.
4. **The check of 6.3** has no epochs and checks no bound of section 7.
5. **Schedule (i)'s snapshot phase** is not given. 4.3 evaluates it at 54,000 and 72,000 slots. No bound depends on it. 4.1 (3) needs a snapshot phase of at least 19,799 slots at (i).
6. **The quantiles of 4.3** take the counts as binomial at the inference's fixed point (REVIEW 7.3). They size what a direct treatment would face and enter no bound.
7. **Not examined here.** Whether S, the $`K`$ row's guarantee, holds at the shorter epochs of (i) and (ii): the noise of a shorter observation window (REVIEW 7.5 to 7.7), and whether a snapshot phase holds an honest leader's block (protocol 157). These belong to the $`K`$ row and to REVIEW, not to the reduction.

## 10. Files

All files are in this folder. The scripts run with the finality study's interpreter. They import GENESIS's `common_g.py` read-only, write no bytecode, keep numba's cache in `.cache/numba`, and read GENESIS's cached curves of $`U`$ with `np.load`.

| File | Content | Statements |
| --- | --- | --- |
| `common_b.py` | constants, schedules, the states of the $`K`$ row, the read-only loader of $`U`$ | 8 |
| `s01_terms.py`, `out_01_terms.txt` | the terms of 7.4 and 7.5 per state and gap, least windows, the cells over a day and a year | 8.1 |
| `s02_fork_state.py`, `out_02_fork_state.txt` | the inference as printed against its closed form; the fork's free slots, $`D_X/D_H`$, the coalition's chance, its wins | 4.2, 4.3 |
| `s03_reduction_check.py`, `out_03_reduction_check.txt` | random executions and passes of the Bootstrap rule; the reduction, Step 0 and the crossing events | 6.3 |

Each script names its usage in its first lines.
