# CHECK: attempts A and B on weakening $`2K \le G + 1`$ in GENESIS 7.3

Date: 2026-11-19.

Read in full: GENESIS.md; REVIEW.md sections 3, 4, 5.9 and 7; PROOF.md of attempt A and of attempt B; the specification at `83596b6e` (protocol: Epoch Schedule, Epoch State Pseudocode, block validation steps 5 and 6, `on_block`; fork choice 111–141; inference 53–88; leadership 137–185). The attempts' scripts were read, not run. Every figure below comes from the scripts of this folder.

## 0. Verdicts

- **A: confirmed.** GENESIS 7.3 holds with $`s \le K - 1`$ and $`s + K \le G + 1`$, term for term, with no extra term. One slip: PROOF.md line 12 says "at most $`2.9\cdot10^{-20}`$", a second rounding of $`2.8466\cdot10^{-20}`$ (5). It is harmless.
- **B: confirmed.** GENESIS 7.3 holds for every gap with $`K - 1 \le G < E`$ and $`s \le K - 1`$, with no extra term. One slip: PROOF.md line 14 says "at most $`2.8\cdot10^{-20}`$", 1.7 % below the computed bound $`2.8466\cdot10^{-20}`$ (5). It is harmless.
- So A's condition is not needed. A's theorem is B's 7.4, a special case of B's 7.5.
- Both theorems bound $`P(\text{S holds and } J \text{ does not hold})`$, as GENESIS 7.3 does. B 7.5 does not show that a gap of $`K - 1`$ is safe, because S itself is not established at such gaps (2, "What 7.5 does not give").
- GENESIS: the gap in 7.2's second bound is real, also under $`2K \le G + 1`$, and harmless. The reported gap in 6.3's first case is an omitted step whose conclusion holds (3).

## 1. The shared repair (Confirmed)

**The witness.** In GENESIS 7.1 Step 2, let `c_max` be $`Y \in \mathcal G`$, let $`Y`$ not contain $`H`$, let $`X`$ replace $`Y`$ by length, let $`D = D(X, Y)`$ lie strictly after $`D_Y`$ on $`Y`$, and let $`X`$ be bad.

1. $`X`$ contains $`D`$, hence $`D_Y`$ and the block of $`Y`$ after $`D_Y`$. That block is not on $`H`$, because $`D_Y`$ is $`Y`$'s last block on $`H`$. So $`D_X = D_Y`$.
2. $`X`$ is bad, so $`sl_{D_Y} + K \le sl_X \le \text{now}`$ (validation step 6: a block's slot has elapsed). So $`sl_{D_Y} \le \text{now} - K`$.
3. $`Y`$ is not bad, so its blocks after $`D_Y`$ have slots in $`(sl_{D_Y}, sl_{D_Y} + K - 1]`$. This lies in GENESIS 4.2's span for $`(Y, H)`$ if and only if $`K \le G + 2`$. Then by 4.3, with $`H`$ in the place of $`Y`$, each block of $`Y`$ is honest or a coalition win under $`H`$'s states.
4. $`Y`$ is dominant. $`H`$ has length $`d(\text{now} - \Delta - 1)`$ and ends in an honest block in a slot of at most $`\text{now} - \Delta - 1`$. So both are at least as long as every chain that ends in an honest block made by slot $`\text{now} - \Delta - 1`$.
5. Both are made by slot $`\text{now} - 1`$: $`sl_Y \le sl_{D_Y} + K - 1 \le \text{now} - 1`$.
6. They share exactly the blocks up to $`D_Y`$, all in slots of at most $`\text{now} - K`$.

So $`(Y, H)`$ is a witness of $`E_r`$ as GENESIS 7.1 defines it. It also meets A6 at slot `now` with $`\ell = \text{now} - K + 1`$, giving $`\mu_\ell \ge 0`$ at slot $`\ell + K - 2`$: $`U(K - 2)`$. At delay $`\Delta + 1`$ and slot $`\text{now} + 1`$ it gives $`U_{\Delta+1}(K - 1)`$. No block of $`X`$ after $`D`$ is read.

**Every case lands in an event** (A 3.3 and B 6.2 use the same cases):

- Step 1, the $`H`$-tip $`h'`$ adopted: $`h'`$ contains $`H`$, so Step 0 puts it in $`\mathcal G`$ unless $`E_g`$.
- Step 1, $`Y_0`$ kept by density: $`E_d(sl_D)`$. $`D`$ lies on $`H`$ strictly before $`H`$'s tip, so it is also $`E_d^*(sl_D)`$, unless $`H`$'s tip has a slot of at most $`\text{now} - K`$, which is $`E_g`$.
- Step 1, $`Y_0`$ kept by length: $`D_{Y_0} = D`$, so $`Y_0`$ is not bad; or $`Y_0`$ contains $`H`$ and Step 0 applies.
- Step 2, by density: $`E_d(sl_D)`$. With $`D`$ strictly before $`D_Y`$ it is $`E_d^*(sl_D)`$. Otherwise $`sl_{D_Y} \le sl_D \le \text{now} - K`$: $`E_r^*`$ if $`Y`$ does not contain $`H`$, $`E_g`$ if it does.
- Step 2, by length, $`D`$ at or before $`D_Y`$: $`sl_{D_X} \ge sl_D > sl_X - K`$, so $`X`$ is not bad.
- Step 2, by length, $`D`$ after $`D_Y`$: if $`Y`$ contains $`H`$, so does $`X`$ (Step 0). Otherwise $`X`$ is not bad, or it is the witness above.

The search of 4 classified 1,153,464 first exits from $`\mathcal G`$ after the last $`H`$-tip visit by these cases. None was left unexplained.

**The inequalities.** Each attempt's condition is correct. B's are exact; A's, like GENESIS's, are one slot stronger than needed.

| Requirement | Exact (B) | A and GENESIS | Search (4): failures seen at |
| --- | --- | --- | --- |
| GENESIS 3.1: blocks read have slots of at most $`t - G - 1`$, S covers $`t - K`$ | $`G \ge K - 1`$ | $`G \ge K`$ | $`G = K - 2`$ and $`K - 3`$ only |
| $`Y`$, or a witness of $`E_r^*`$, under $`H`$'s states | $`K \le G + 2`$ | $`K \le G + 1`$ | $`G = K - 3`$ only |
| GENESIS 6.1 with $`D`$ after $`D_Y`$: $`X`$'s window reaches $`sl_{D_Y} + K - 1 + s`$ | $`s + K \le G + 2`$ | $`s + K \le G + 1`$ | $`G`$ up to $`2K - 4`$, with $`s = K - 1`$ |
| GENESIS's own witness $`X`$: slots up to $`sl_{D_Y} + 2K - 2`$ | $`2K \le G + 3`$ | $`2K \le G + 1`$ | $`G`$ up to $`2K - 6`$ (possible to $`2K - 4`$) |

**A remark on GENESIS.** $`E_r`$ as 7.1 writes it admits chains made by slot `now`. A6 at slot `now` needs chains made by slot $`\text{now} - 1`$. So 7.2's "$`P(E_r) \le U(K - 2)`$" holds for the Step 2 witness, which is how 7.2's text argues it, not for $`E_r`$ as written. A's $`E_r'`$ and B's $`E_r^*`$ end by slot $`\text{now} - 1`$, so their $`U(K - 2)`$ is direct.

## 2. B's stronger claim (Confirmed)

- **The reduction, B 6.2,** is combinatorial and reads no epoch state. The cases of 1 cover it.
- **What $`E_d^*`$ leaves out.** A divergence block at or after $`D_Y`$ with $`\sigma \le \text{now} - K`$ gives $`sl_{D_Y} \le \text{now} - K`$. Then $`Y`$ witnesses $`E_r^*`$ if it does not contain $`H`$, and Step 0 gives $`E_g`$ if it does. The search found 104,568,120 such $`E_d`$ witnesses. None lay outside $`E_r^* \cup E_g`$.
- **B 7.1.** $`D`$ lies on $`H`$ strictly before $`D_Y`$, so $`D_X = D`$. $`X`$'s window $`(\sigma, \sigma + s]`$ lies in 4.2's span for $`(X, H)`$ if and only if $`s \le G + 1`$. $`Y`$'s blocks lie in it if and only if $`K \le G + 2`$. The rest of GENESIS 6.1 is unchanged.
- **B 7.2.** GENESIS 6.2 (a)–(c) read only $`H`$'s lottery. In 6.3's first case, $`\tilde X`$ shares $`H`$'s blocks up to $`D`$ or a later block, and its added slots lie below $`b \le \sigma + G + 1`$. The second and third cases read $`Y`$ alone. $`P_1(G + 1 - s)`$ is a bound on $`H`$'s lottery with no condition on $`G`$. 8.1 applies the same cases at the edge of a cell.
- **B 7.3.** The added slots lie in $`(\sigma + s, \text{now}] \subseteq (\sigma, \sigma + G]`$, within 4.2's span for $`(\tilde X, H)`$. $`E_r^*`$ is bounded by B 5.3.
- **GENESIS 3.1 with $`G \ge K - 1`$.** A slot $`t`$ of epoch $`ep`$ reads blocks below $`c_{ep-1} \le t - G`$, so in slots of at most $`t - G - 1 \le t - K`$.
- **Every use of the gap in GENESIS,** re-read: 3.1; 4.2, which needs $`G < E`$; 4.3; 6.1 ($`Y`$'s blocks, $`X`$'s window); 6.2 through 6.1; 6.3 (the split at $`b \le \sigma + G + 1`$, the extension, $`Y`$ alone); 7.1 Step 2; 7.2's second bound ($`\text{now} \le \sigma + G`$, the extension); 8.1 (the same at the edge of a cell); 6.4 and 9.2, which 7.3 does not use. B's audit, its 3.1, lists them all. There is no other.
- **A condition both use:** 4.2 needs the observation window inside the snapshot phase. B states $`P \le L_1`$; A sets PERIOD equal to the snapshot phase. It holds at `83596b6e` and in schedule (ii). Schedule (i) leaves the snapshot phase open.
- **What 7.5 does not give.** B 7.5 is conditioned on S, which the $`K`$ row supplies. REVIEW 4.6 shows that for $`G < K`$ the nonce and $`D`$ are never final when first used. At $`K`$ = 36,000, REVIEW 5.9 finds a necessary gap of at least 36,611 slots in every state, and a sufficient one of up to 46,910 (the first disturbance). So 7.5 shows only that the reduction asks for no more than $`G \ge K - 1`$. B's 9.7 says the same.
- **At $`G`$ = 46,910,** REVIEW 5.9's gap for the first disturbance, B's theorem applies and A's does not ($`s + K = 52{,}200 > G + 1`$). The term that reads $`G`$ is at most $`1.8\cdot10^{-17}`$, and no total changes (5).

## 3. The gaps in GENESIS

**(a) 7.2's second bound (Confirmed: B 3.2, A 3.4 (3)).** The extension of $`X[0{:}e]`$ through $`(e, \text{now}]`$ is put under $`H`$'s states because its slots lie "within $`G + 1`$ of $`D`$". By 4.2 that gives $`Y`$'s states. These equal $`H`$'s only up to $`sl_{D_Y} + G + 1`$. With $`D`$ after $`D_Y`$ and $`\text{now} > sl_{D_Y} + G + 1`$, the step fails.

- The search found 3,211 such extensions, of 454,011 checked, with an added slot whose state is not $`H`$'s. They occur at every $`G \ge K`$. At $`G = K - 1`$ the case is empty.
- At $`K`$ = 12 and $`G`$ = 23, 24 and 36, where $`2K \le G + 1`$ holds, it found 14, 34 and 7 (`out_c4_extra.txt`).
- Example, seed 12180036681, $`K`$ = 12, $`G`$ = 18: $`D_Y`$ in slot 106, $`D`$ in slot 116, now = 128 $`\le \sigma + G`$ = 134. The added slot 127 lies after $`sl_{D_Y} + G + 1`$ = 125. There the extension derives a nonce other than $`H`$'s ($`D`$ is 293 on both).
- Every such case lay in $`E_r^*`$ or $`E_g`$. None of the 29,593 extensions of $`E_d^*`$ witnesses failed.
- Effect: none on GENESIS's figures. $`E_r^*`$ lies in the event of $`U_{\Delta+1}(K - 1)`$ (B 5.3), and $`E_g`$ is in the total. A's and B's fixes are correct.

**(b) 6.3's first case (Corrected: an omitted step, not a false one).** The added slots lie below $`b \le sl_Y \le sl_{D_Y} + K - 1 \le sl_{D_Y} + G + 1`$ under GENESIS's hypotheses, since $`K \le G + 2`$ suffices. So "hence $`H`$'s" holds, though GENESIS does not say why. A's 3.4 (2) supplies the step. The search found no failure in 1,957,677 such extensions, 13,047 of them with $`D`$ after $`D_Y`$, also at the negative controls.

## 4. Counterexample search (Confirmed: no violation)

`c4_sim.py` is written from the specification and GENESIS's definitions. It shares no code with either attempt.

- **Epoch states.** Every chain derives its own state for each epoch. The snapshot is the chain below the previous epoch's first slot (REVIEW A4). The nonce is $`\eta`$ of the last block before the cut-off. $`D`$ comes from the inference in integers (truncation toward zero, $`\beta`$ = 2/3), over the distinct occupied slots of the snapshot phase, uncles included.
- **The lottery.** A party of stake $`v`$ wins slot $`t`$ when a hash of the state, $`t`$ and the party falls below $`1 - (1 - f)^{v/D}`$. A block is valid only under its own chain's state.
- **Honest nodes.** One to three. Each holds the longest chain, a tie keeping the current one, and references uncles. Each receives honest blocks within $`\Delta + 1`$ slots.
- **The coalition.** Live private branches, and occasional publication. After the run, withheld branches: crossing forks from $`D_Y = c_e - u`$ with $`u \in [2, 2K - 2 - G]`$, $`u`$ = 2 in half of them, with $`Y`$ quiet in its window in some; forks from 2 slots before every cut-off; dense forks.
- **The joining node.** $`J`$ holds every block, starts from genesis, and runs the Bootstrap pass from four starts and orders. One of them starts at a witness of $`E_r^*`$ and visits the $`H`$-tips first.
- **What is tested.** Each choice of $`H`$ on which S holds, with $`K`$ = 10, 12 and 16, $`G`$ from $`K - 1`$ to $`2K - 2`$ (41 gaps, 12,000 runs each), and negative controls at $`G = K - 3`$ and $`K - 2`$.

| Count, $`K - 1 \le G \le 2K - 2`$ | Value |
| --- | --- |
| runs (in the focused crossing mode) | 456,000 (205,755) |
| choices of $`H`$ with S / without S, excluded | 388,474 / 140,681 |
| passes / ending outside $`\mathcal G`$ | 1,553,896 / 1,150,294 |
| passes outside $`\mathcal G`$ that B's events miss / that A's miss (also with tips only) | 0 / 0 |
| passes covered by $`E_r^*`$ alone (tips only, $`X \ne Y`$) | 2,428 |
| crossing exits / $`Y`$ not a witness of $`E_r^*`$, or $`(Y, H)`$ not one of $`E_r'`$ | 104,044 / 0 |
| crossing exits in which GENESIS's witness $`X`$ has a block not under $`H`$'s states | 2,091 |
| honest blocks off $`H`$'s states (3.1) | 0 of 18,386,705 |
| witnesses of $`E_r^*`$ not under $`H`$'s states (B 5.3) | 0 of 2,592,696 |
| witnesses of $`E_d^*`$ with $`Y`$ or $`X`$'s window off $`H`$'s states (B 7.1) | 0 of 305,499,097 |
| witnesses of $`E_d`$ with $`D`$ at or after $`D_Y`$ and $`X`$'s window off $`H`$'s states (GENESIS 6.1) | 10,127 of 104,568,120 |

- **Negative controls** (72,000 runs, 183,007 passes outside $`\mathcal G`$): no pass escaped the events, since the reduction is combinatorial. But 3.1 failed for 31 honest blocks, at $`G = K - 2`$ and $`K - 3`$. B 5.3 failed 1,918 times, $`(Y, H)`$ failed as a witness of $`E_r'`$ 154 times, and B 7.1 failed 40,471 times, all at $`G = K - 3`$. So the bounds need what B states, and no less.
- **Example crossing,** seed 12181037444, $`K`$ = 12, $`G`$ = 18: $`D_Y`$ in slot 105, cut-off 108, $`D`$ in slot 115, $`X`$ in slot 126 with length 39 against $`Y`$'s 36. $`X`$'s block in slot 126, the first slot of the next epoch, is a win on $`X`$ but not under $`H`$'s states. Here $`H`$, not $`X`$, has a block between $`D_Y`$ and the cut-off, so $`X`$'s nonce differs. $`Y`$ witnesses $`E_r^*`$ and $`E_r'`$.
- **Replay:** `c4_sim.replay(K, G, seed)` replays any run.

## 5. The numbers (Confirmed, with two rounding slips)

GENESIS's `Window.p1` (closed form, checked against the forward pass) and its cached curves of $`U`$, in g07's states (REVIEW 5.9's mapping); $`K`$ = 36,000, $`s`$ = 16,200 (`out_c5_terms.txt`):

| State | $`P_1(s)`$ | $`U(s-1)`$ | $`U(K-2)`$ | $`U_{\Delta+1}(K-1)`$ | $`P_1(G+1-s)`$ at $`G`$ = 35,999 / 46,910 / 52,199 / 54,000 |
| --- | --- | --- | --- | --- | --- |
| no disturbance | 2.0552e-13 | 1.3493e-7 | 8.2847e-16 | 1.3482e-14 | 3.9493e-16 / 2.4938e-24 / 2.7097e-28 / 1.2140e-29 |
| every block $`T_M`$ late | 2.5638e-10 | 4.3411e-5 | 2.5075e-10 | 2.0824e-9 | 2.2980e-12 / 1.5397e-18 / 1.6038e-21 / 1.5512e-22 |
| a tenth offline, corrected | 5.2045e-10 | 1.2848e-5 | 2.0131e-11 | 1.7972e-10 | 5.5479e-12 / 6.2875e-18 / 8.4499e-21 / 8.9138e-22 |
| a tenth offline, before the correction | 8.9950e-10 | 1.2851e-5 | 2.0801e-11 | 1.5087e-10 | 1.0826e-11 / 1.7723e-17 / 2.8466e-20 / 3.1907e-21 |
| $`D`$ = honest stake online | 8.5233e-15 | 4.5061e-7 | 9.8981e-15 | 7.2613e-13 | 8.0400e-18 / 5.8775e-27 / 2.2460e-31 / 7.0545e-33 |

- **The other terms.** All of them equal A's and B's tables, and GENESIS's `out_07_states.txt`.
- **The totals per divergence slot** are the same at all four gaps to five digits. Without honest blocks, $`P_1(s) + U(K-2)`$: 2.0635e-13, 5.0712e-10, 5.4058e-10, 9.2030e-10 and 1.8421e-14. For every fork: 1.3493e-7 to 4.3411e-5.
- **The second-digit differences.** Both attempts call the same closed form at the same arguments, and agree with this recomputation to every digit they print. A prints three digits, B two, each rounded correctly: 8.45 and 8.4 (from 8.4499), 2.85 and 2.8 (2.8466), 2.25 and 2.2 (2.2460), 1.55 and 1.6 (1.5512). The figures 8.5e-21, 2.9e-20 and 2.3e-31 come only from rounding A's three digits a second time.
- **Where the double rounding matters.** A rounds twice once, in PROOF.md line 12: "at most $`2.9\cdot10^{-20}`$". As upper bounds, A's 2.9e-20 holds and B's "at most 2.8e-20" (PROOF.md line 14) does not. No conclusion depends on this.
- **The floor of $`P_1`$.** At $`G`$ = 259,200, $`P_1(G+1-s)`$ sits in all five states at the floor of the computation, the mass placed at infinity (7.2e-39, 2.2e-35, 6.3e-33, 2.1e-33, 5.1e-36). At $`G`$ = 72,000 it does in two states. GENESIS marks it "≤". A's table (its GENESIS column) and B's output print it as a value.
- **A's 4.3: confirmed.** At $`G`$ = 57,335 the bound for every fork is 9.9978e-10 at $`s`$ = 21,336, against 1.0007e-9 at 21,335. At $`G`$ = 69,180 the bound over a year is 9.9948e-10 at $`s`$ = 33,181, against 1.0004e-9 at 33,180.
- **The same windows under B.** With $`G \ge K - 1`$ they meet $`10^{-9}`$ from $`G`$ = 37,486 (one divergence slot) and $`G`$ = 55,834 (a year). The term $`P_1(G + 1 - s)`$, or $`P_1(G + 2 - s - g)`$ in the cells, then limits them. The margins are only 2e-13 and 5e-13, so these least gaps move with small changes of the window.
- **Least windows under B,** per divergence slot for every fork: 21,339, none, none, none and 23,068 at $`G = K - 1`$. At $`G`$ = 52,199: 21,336, none, 30,509, 30,494 and 23,062, as B reports.

## 6. A fork's own epoch state (Confirmed: no contradiction with the theorem)

- Both say that nothing here enters a bound, and nothing does.
- The stretch of the fork's own state is $`2K - 3 - G`$ slots at most: 19,798 in (i) and 17,997 in (ii). A's 5.1 (3) and B's 4.1 (4) agree.
- The coalition's expected wins in the free part are 200 and 182, so up to about $`2^{200}`$ and $`2^{182}`$ nonce candidates. A's 5.4 and B's 4.3 agree.
- B's 4.2 bound on the inference holds for $`\beta \le 2/3`$: the numerator before the last division is greater than 333 − 2.
- The search confirms that GENESIS's witness can carry blocks under a state of its own, so A's 5.5 is realizable. The example in 4 shows a second route besides A's: $`H`$'s own block between $`D_Y`$ and the cut-off. A's 5.1 (2) allows it.
- The quantile tables of $`D_X/D_H`$ (A 5.3, B 4.3) were not recomputed.

## 7. What was not checked

- A6, the reading of GRR at one slot, and the study's clock behind $`U`$. Both attempts and GENESIS take them as given.
- S at gaps below REVIEW 5.9's values. Also A1's independence and A4 when a window straddles more cut-offs, as it does at shorter epochs.
- The search tests the reduction and what the bounds need of the epoch states, structurally. It computes no GRR margin and no probability.
- The attempts' own check scripts were not rerun.

## 8. Files

| File | Content |
| --- | --- |
| `c5_terms.py`, `out_c5_terms.txt` | item 5: every term in the five states at the six gaps, the totals, the least windows, A's 4.3 and the least gaps under B |
| `c4_sim.py`, `out_c4_sim.txt` | item 4: the search, per $`(K, G)`$, with examples; `replay(K, G, seed)` |
| `c4_table.py`, `out_c4_table.txt` | item 4: one line per $`(K, G)`$ |
| `c4_extra.py`, `out_c4_extra.txt` | item 3: the gap of 7.2's second bound at $`G \ge 2K - 1`$ |

Interpreter: the finality study's `.venv`. GENESIS's folder is read only: no bytecode, numba's cache in `.cache/numba`, and the curves loaded with `np.load`.
