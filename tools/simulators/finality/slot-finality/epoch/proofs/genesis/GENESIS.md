# The conclusion of Ouroboros Genesis, Theorem 2, for the Bootstrap rule

Date: 2026-11-18.

This document asks whether a node that bootstraps under the specification's Bootstrap rule ends on the honest chain, as Theorem 2 of Ouroboros Genesis concludes for its protocol. The paper's hypotheses fail at the specification's delays (REVIEW.md, 8.5), so the paper's theorem cannot be applied. This document gives a new argument with explicit constants. It proves a reduction for the specification's rules, a sharp bound for the long-range fork that the density comparison exists for, and a bound for forks that hold honest blocks. It states what remains open.

## 0. Result in brief

- **The target (2.3).** A joining node holds, when it switches to the Online rule, a chain that is at least as long as the honest chain and that left the honest chain less than $`K`$ slots before its own tip. Then `commit` fixes only blocks of the honest chain, and the node is an honest node of the Online rule's model from then on. (Proved, 2.4. 7.3 bounds the chance that the node does not hold, given A6.)
- **The reduction (7.1).** In the model of section 3, and while the Online rule keeps its own guarantee, the joining node misses the target only if, for some divergence block $`D`$ of its history, a fork is at least as dense as a dominant chain in the $`s_{gen}`$ slots after $`D`$, or two dominant chains differ on a slot $`K - 1`$ or more slots before the switch, or honest stake wins no slot in the $`K - 2\Delta - 1`$ slots that end $`\Delta + 1`$ slots before the switch, which has a chance below $`10^{-353}`$. This needs $`s_{gen} \le K - 1`$ and $`2K \le G + 1`$. It does not need $`2s_{gen} \le K`$. (Proved.)
- **Forks with no honest block in the window (6.2).** This is the long-range attack. Per divergence slot the chance is at most $`2.1\cdot10^{-13}`$ against 30 % at $`\Delta`$ = 10 slots, $`2.6\cdot10^{-10}`$ at 15 slots, $`1.3\cdot10^{-8}`$ against a third at 10 slots and $`3.2\cdot10^{-6}`$ at 15 slots. RFC-532's single-window figures, $`6.0\cdot10^{-14}`$ and $`3.9\cdot10^{-9}`$, are reproduced as one of the three terms. (Proved; Computed, `out_02_window.txt`.)
- **Every fork (6.3).** Per divergence slot the chance is at most the settlement bound at a wait of $`s_{gen} - 1`$ slots, plus two terms that are negligible at $`s_{gen}`$: $`1.35\cdot10^{-7}`$, $`4.3\cdot10^{-5}`$, $`8.3\cdot10^{-5}`$ and $`4.1\cdot10^{-3}`$ in the same four settings. (Proved, given A6: a reading of GRR's definitions that costs one slot, and the study's construction that its bound $`U`$ covers the margin at every slot. Computed, `out_03_settle.txt`.)
- **The second bound counts a real attack (6.4).** In GRR's model, where ties are broken for the coalition, a split of the honest nodes that lasts through the window leaves a fork that wins the density comparison. The finality study's estimate of the attack that makes such splits puts their chance at about $`4.7\cdot10^{-11}`$, $`3.0\cdot10^{-8}`$, $`8.6\cdot10^{-7}`$ and $`7.5\cdot10^{-5}`$ per divergence slot. These estimates lie 55 to 2,900 times below the bound of 6.3, so that bound may be loose by as much. (Proved: the construction. Estimate: the chances.)
- **A history (8.2).** A node that syncs from genesis compares forks at every divergence block of the history. Over a year of history the bounds are $`3.1\cdot10^{-8}`$ for forks without honest blocks and $`1.1\cdot10^{-2}`$ for every fork against 30 % at 10 slots. (Proved, given A6 for every fork; Computed, `out_04_union.txt`.)
- **Keys bought later (9).** The specification does not stop a coalition from signing old slots with keys of notes that were honest then. With enough such keys the density comparison fails for every window length. Against 30 % at 10 slots, keys of a further 4.8 % of the window's stake lift the bound above $`10^{-9}`$, and 26.6 % give the fork the mean rate of the honest chain's guaranteed growth under the worst-case delay. No bound here holds without assumption A3. (Cited, 4.5; Proved, 9.1; Computed, `out_05_keys.txt`.)
- **Whether $`s_{gen}`$ and $`K`$ suffice (11).** Against forks without honest blocks, $`s_{gen}`$ = 16,200 slots meets $`10^{-9}`$ per divergence slot against 30 % at both delays, and not against a third. Against every fork, these bounds do not reach $`10^{-9}`$ in any of the four settings. They would with a window of 21,336 slots against 30 % at 10 slots, and 33,729 at 15 slots, and over a year of history with 33,181 and 51,560 slots. At 10 slots both fit within $`K`$ = 36,000 under the reduction of 7.1, which needs $`s_{gen} \le K - 1`$ only. At 15 slots the bounds of this document do not reach $`10^{-9}`$ at $`K`$ = 36,000 for any window, and they do at $`K`$ = 64,800. (Computed, `out_03_settle.txt`, `out_04_union.txt`.)

## 1. Setting

### 1.1 Texts

| Short name | Text | Version |
| --- | --- | --- |
| protocol | `docs/blockchain/raw/cryptarchia-v1-protocol.md` | `7f3cf149` (latest #533, $`K`$ = 36,000) and `ded1d4c6` (base, $`K`$ = 64,800) |
| fork choice | `docs/blockchain/raw/fork-choice.md` | identical at both commits (`out_01_setting.txt`, line 16) |
| bootstrap | `docs/blockchain/raw/cryptarchia-v1-bootstr-sync.md` | identical at both commits |
| leadership | `docs/blockchain/raw/cryptarchia-proof-of-leadership.md` | identical at both commits |
| the paper | "Ouroboros Genesis: Composable Proof-of-Stake Blockchains with Dynamic Availability", Badertscher, Gaži, Kiayias, Russell, Zikas | full version of 22 February 2019, ePrint 2018/378: Theorem 1 (§4.2), Theorem 2 (§4.3), Lemma 1 and Corollary 1 (§4.4). The CCS 2018 version numbers them Theorem 4.3, Theorem 4.4, Lemma 4.5 and Corollary 4.6. |
| GRR | "Practical Settlement Bounds for Longest-Chain Consensus", Gaži, Ren, Russell, ePrint 2022/1571 (CRYPTO 2023) | the copy in `dual-finality-2026-11-17/paper/` (`grr.txt`): §2.1, §2.2, Definitions 4, 5 and 10–12, Lemma 10, Theorem 2, §4.7 |
| the study | the finality study, package `finality_sim` | `waitbound.wait_curve` (its bound $`U`$), stored runs `runs/k1/worst.csv` and `runs/k7/worst.csv` |
| Cardano | Ouroboros Consensus, "Cardano Genesis" design page, `docs/website/contents/references/miscellaneous/genesis_design.md` of the repository `IntersectMBO/ouroboros-consensus` | read 2026-11-18 |

Line numbers of the specification are those that `git show <commit>:<path>` prints, at `7f3cf149` unless stated. The texts of the paper read here are the CCS version and the full version's §4.2 to §4.4 and Appendix E; line numbers of the full text are those of a plain-text extract of the full version, which is not copied here. The proof of Theorem 2 is at its lines 1615–1678.

### 1.2 Symbols

The specification's symbols are kept. The others are this document's.

| Symbol | Meaning | Value |
| --- | --- | --- |
| $`f`$, $`k`$ | slot activation coefficient, security parameter (protocol 102, 103) | 1/30, 2,160 |
| $`K`$ | finality window (protocol 104; base 103) | 36,000 or 64,800 slots |
| $`s`$ | $`s_{gen} = \lfloor k/(4f) \rfloor`$, the density window (fork choice 80) | 16,200 slots |
| $`E`$, $`G`$ | epoch length; gap from the cut-off to the next epoch (protocol 155, 159) | 648,000; 259,200 slots |
| $`\Delta`$ | worst-case delivery delay in slots: 10, or $`T_M`$ = 15 in the first disturbance of the $`K`$ row | 10, 15 |
| $`\alpha`$ | the coalition's share of the total active stake, counted while all honest stake is online | 3/10; 1/3 for comparison |
| $`p_h`$, $`p_a`$ | $`1-(1-f)^{1-\alpha}`$, $`1-(1-f)^{\alpha}`$ | `out_01_setting.txt`, lines 28–31 |
| $`A(I)`$ | the number of slots of a set $`I`$ that the coalition wins | |
| $`N(I)`$ | the largest number of slots of $`I`$ won by honest stake with pairwise gaps of at least $`\Delta + 1`$ (5.2) | |
| $`d(t)`$ | the largest length of an honest block with a slot of at most $`t`$; $`d(t) = 0`$ for $`t \le 0`$ | |
| $`C[0{:}t]`$ | the chain that ends in the last block of $`C`$ with a slot of at most $`t`$ | |
| $`U(w)`$ | the study's settlement bound for a wait of $`w`$ slots (A6) | `out_03_settle.txt` |
| $`U_{\Delta+1}(w)`$ | the same bound at a delay of $`\Delta + 1`$ slots (A6) | `out_03_settle.txt` |
| $`P_1(x)`$ | the bound of 6.2 for a window of $`x`$ slots | `out_02_window.txt` |

A chain is named by its last block. Its length is its number of blocks after genesis. Intervals of slots are written $`(a, b] = \{a+1, \dots, b\}`$ and $`(a, b) = \{a+1, \dots, b-1\}`$.

### 1.3 Labels and conventions

Every numbered statement carries one label, as in REVIEW.md, section 2.

- **Proved.** The definitions, the statement and a complete argument are in this text.
- **Computed.** A script in this folder evaluates a formula that is proved or cited. The file and its lines are named.
- **Cited.** A statement of the specification, a paper or a stored run of the study, with its place.
- **Assumed.** Named as an assumption: a model, or a reading of a text that is not the text's own statement.
- **Estimate.** A number that no statement here bounds. It is given to place a bound, never in its stead.

A slot lasts one second, so 3,600 slots are an hour. A coalition's share is a share of the total active stake, counted while all of the honest stake is online (protocol 104).

## 2. The target

**2.1 (Cited). What the paper concludes.** Theorem 2 considers the protocol with the rule `maxvalid-bg`, with every honest party online from the start. Under the conditions of Theorem 1 and $`k > 192\Delta/(\epsilon\beta)`$, $`R/6 \ge s = k/(4f) \ge 48\Delta/(\epsilon\beta f)`$, it concludes that common prefix, chain growth, chain quality and existential chain quality hold as in Theorem 1, except for an additional error (its display (5)). Lemma 1 adds that a party that joins later adopts its synchronizing chain, the first chain that an alert party with no stake, receiving the same messages, would adopt. Corollary 1 concludes that the guarantees then hold with parties that join and leave.

The proof of Theorem 2 (full version, §4.3) compares a chain held by an alert party with a candidate that forks from it by more than $`k`$ blocks. It reads two windows of $`s`$ slots after their last common block. It shows that a candidate at least as dense in the first window yields a common-prefix violation of parameter $`k\beta/64`$ blocks. That is 33.75 blocks at $`k`$ = 2,160 and $`\beta = 1`$.

**2.2 (Cited). The specification's bootstrap.** A node that starts from genesis, from a checkpoint, after more than $`T_\text{offline}`$ offline, or after a stop under the Bootstrap rule, uses the Bootstrap rule (bootstrap 121–136). It runs the rule on every block it processes (protocol 482–486). It keeps the rule for the Prolonged Bootstrap Period of 24 hours (bootstrap 111, 194–200), then runs a last round that fetches every peer's tip (bootstrap 204–245). "When the round ends, the node switches the fork choice rule to the Online rule and runs Commit on $`c_{loc}`$ before it processes any further block" (bootstrap 247). Under the Bootstrap rule $`B_\text{imm}`$ does not move (protocol 127). The rule compares two chains by length when their divergence block is less than $`K`$ slots older than the later tip, and by density in the $`s`$ slots after it otherwise (4.1).

**2.3 (Definitions).** Let $`J`$ be the joining node, and let `now` be the slot of its switch to the Online rule.

- The **reference chain** $`H`$ is the longest chain that ends in an honest block made in a slot of at most $`\text{now} - \Delta - 1`$. So $`\text{len}(H) = d(\text{now} - \Delta - 1)`$.
- A chain $`Z`$ is **dominant** if $`\text{len}(Z) \ge d(\text{now} - \Delta - 1)`$.
- $`D_Z`$ is the last block that $`Z`$ shares with $`H`$. $`Z`$ is **bad** if $`sl_{D_Z} + K \le sl_Z`$.
- $`\mathcal G`$ is the set of chains in $`J`$'s block tree that are dominant and not bad.
- $`J`$ **holds** if its $`c_{loc}`$ at the switch lies in $`\mathcal G`$.

**2.4 (Proved). What holding gives.** Suppose that $`J`$ holds.

1. The `commit` of the switch makes immutable only blocks of $`H`$ with slots of at most $`\text{now} - K`$.
2. Every chain that has the same blocks as $`H`$ in the slots up to $`\text{now} - K`$ contains $`J`$'s new $`B_\text{imm}`$. So while the Online rule keeps every honest node's local chain in that set, which S states up to the switch and the $`K`$ row is sized to keep afterwards, $`J`$ is an honest node of the model of section 3, and the guarantees that the $`K`$ row gives honest nodes cover it.

*Proof.* (1) By REVIEW.md 3.6, `commit` on a tip $`O`$ makes a block $`X`$ after the old $`B_\text{imm}`$ immutable only if $`X`$ is on $`O`$ and $`sl_X + K \le sl_O`$. A valid block has a slot of at most `now` (protocol 435), so $`sl_X \le \text{now} - K`$. $`O`$ is not bad, so $`sl_X \le sl_O - K < sl_{D_O}`$. Slots increase along a chain (protocol 432), so $`X`$ is $`D_O`$ or an ancestor of it, hence a block of $`H`$. The old $`B_\text{imm}`$ is a block of $`H`$ by A5. (2) The new $`B_\text{imm}`$ is a block of $`H`$ with a slot of at most $`\text{now} - K`$, so a chain with $`H`$'s blocks in those slots contains it, and so does $`H`$, the chain of an honest block of length $`d(\text{now} - \Delta - 1)`$. $`J`$ holds a dominant chain, processes blocks under the Online rule, and receives honest blocks within $`\Delta`$ (A2), which is all that section 3 asks of an honest node. ∎

This is the analogue of Lemma 1 and Corollary 1 of the paper. The paper's party adopts the alert party's chain exactly. Here $`J`$ may hold a short fork of it, which the Online rule treats as it treats an honest node's fork.

**2.5 (Proved, by 7.1 to 7.3). What the density comparison must give, and what $`K`$ gives.** The proof of 7.1 splits the failures of $`J`$ in two.

- **The density comparison** must exclude, for every divergence block $`D`$ of $`J`$'s history with $`sl_D \le \text{now} - K`$, a fork at least as dense as a chain of $`\mathcal G`$ in the window $`(sl_D, sl_D + s]`$. This is event $`E_d(sl_D)`$ of 7.1. Its chance is the subject of sections 6 and 8.
- **The window $`K`$** must exclude two dominant chains that differ on a slot $`K - 1`$ or more slots before the switch, event $`E_r`$, and must keep the Online rule's guarantee S. Both are the settlement that sizes $`K`$ (protocol 104). $`E_r`$ costs $`U(K-2)`$ (7.2).

The two do not overlap. The density window bounds what a fork does right after its divergence. $`K`$ bounds how long two branches can both stay viable.

## 3. The model

Every statement below holds in this model. (All Assumed, except where marked.)

- **A1. The lottery.** Fix the epoch states of the reference chain $`H`$. For each slot $`t`$, let $`h_t = 1`$ if honest stake wins slot $`t`$ under them, and $`a_t = 1`$ if the coalition does. The pairs $`(h_t, a_t)`$ are independent over $`t`$, $`h_t`$ and $`a_t`$ are independent, $`P(h_t = 1) \ge (1 - \delta)\,p_h`$ and $`P(a_t = 1) \le p_a`$. Here $`\delta`$ is the relative shortfall of the circuit's second-order threshold for one note that holds all honest stake: $`9.4\cdot10^{-5}`$ against 30 %, $`8.6\cdot10^{-5}`$ against a third, and $`1.9\cdot10^{-4}`$ when $`D`$ equals the honest stake online (leadership 199–212, 260–281; `out_02_window.txt` lines 12, 23, 34, 45; `out_07_states.txt` line 20). Statement 4.4 proves the bound on $`a_t`$ from the circuit. The computations use $`p_h`$. With $`(1 - \delta)\,p_h`$, $`P_1(s)`$ rises by at most 0.9 % in the settings of 6.2 and by at most 2.0 % in the states of 10.4 (`out_02_window.txt` lines 12, 23, 34, 45; `out_07_states.txt` lines 4, 8, 12, 16, 20). Independence of tickets of different notes is assumed, as in REVIEW.md 5.2.
- **A2. Delivery.** An honest block made in slot $`t`$, with its ancestors, is held by every honest node before slot $`t + \Delta + 1`$ begins. This is the worst case of the $`K`$ row (protocol 104) and the convention of REVIEW.md 5.2 (M2). An honest leader extends its $`c_{loc}`$. At its switch, $`J`$ holds $`H`$: it receives honest blocks within $`\Delta`$ while it listens for new blocks, and the last round fetches the tips of its peers (bootstrap 204–245). Peers prune forks that diverged before their $`B_\text{imm}`$ (protocol 518–520), so $`J`$ need not hold every honest block, and no proof uses it.
- **A3. Keys.** In each epoch's stake distribution, the notes whose secret keys the coalition holds at any time up to $`J`$'s switch carry at most a share $`\alpha`$ of the stake. Section 9 shows that the specification does not enforce this.
- **A4. The nonce.** Each epoch nonce is unbiased, as each disturbance of the $`K`$ row takes it (protocol 104).
- **A5. The start.** $`J`$'s $`B_\text{imm}`$ when it starts is a block of $`H`$: genesis, a checkpoint on the honest chain, or a block that S kept.
- **A6. The settlement lemma (a reading of GRR).** GRR's model has one characteristic string for all chains (GRR §2.1), and the margin $`\mu_\ell`$ of a string is defined from it alone (GRR Definition 11). Read at one slot: if two chains made by slot $`t - 1`$, each at least as long as every chain ending in an honest block made by slot $`t - \Delta - 1`$, share no block with a slot of at least $`\ell`$, then $`\mu_\ell \ge 0`$ at slot $`t - 1`$. This is not Lemma 10, whose hypothesis is a block made in slot $`\ell`$. It is the statement of the paragraph before Lemma 10 (`grr.txt` 867–872, 880–881). The last honest block of each chain heads a chain of non-negative reach in a public tree, because the blocks after it are coalition blocks in distinct coalition slots (GRR's axioms S3 and S4, Definition 10). Two such chains with no common block from slot $`\ell`$ on witness $`\mu_\ell \ge 0`$ (GRR Definitions 4 and 11). The reading costs one slot. GRR's set $`\mathcal D_t`$ is measured against honest chains made by slot $`t - \Delta - 1`$ and admits blocks made in slot $`t`$, while dominance in a tree for the first $`t`$ symbols reads labels up to $`t - \Delta`$ (GRR §2.2, Definition 5; `grr.txt` 265–266, 377–386). So both chains are taken to end before slot $`t`$. The chance that $`\mu_\ell \ge 0`$ at some slot of at least $`\ell + w`$ is at most $`U(w)`$, the study's bound (`waitbound.wait_curve`, slots). That this bound covers every slot of a phase, not only its end, is the study's construction, not a statement of GRR (Cited: `waitbound.py`, docstring lines 9–29; not checked here). $`U_{\Delta+1}`$ is the same bound at a delay of $`\Delta + 1`$ slots. It applies to the same execution, because an execution that meets A2 with $`\Delta`$ meets it with $`\Delta + 1`$. Chains made by the coalition in a later slot than they name are simulated, as usual, by chains made in their own slots and withheld; honest nodes behave the same.
- **S. The Online rule's guarantee.** At every slot $`t`$ from $`J`$'s starting block to the switch: every honest block of length $`d(t - \Delta - 1)`$ made by slot $`t - \Delta - 1`$ descends from the $`B_\text{imm}`$ of every honest node at slot $`t`$; and the local chain $`c_{loc}`$ of every honest node at slot $`t`$ has the same blocks as $`H`$ in the slots up to $`t - K`$. This is what the $`K`$ row bounds by $`\varepsilon`$ per block (Cited: protocol 104). A shorter honest block, such as one that lost a race of $`\Delta`$ slots, need not descend from $`B_\text{imm}`$. The theorems below hold on S, as Theorem 2 of the paper holds except for the errors of Theorem 1.

**3.1 (Proved). Honest blocks follow one lottery.** On S, the local chain of an honest node at slot $`t`$ derives for slot $`t`$ the epoch state that $`H`$ derives. So every honest block is made under $`H`$'s epoch states.

*Proof.* The epoch state of slot $`t`$ reads only blocks with slots below the cut-off of the previous epoch (REVIEW.md 4.3, with its assumption A4 on the commitment root). That cut-off is at most $`t - G \le t - K`$, because the next epoch starts $`G`$ slots after a cut-off (protocol 155) and $`G \ge K`$. By S the chain and $`H`$ have the same blocks in these slots. ∎

## 4. Facts of the specification and of the lottery

**4.1 (Cited). The Bootstrap test.** For the current choice `c_max` and a fork `c_fork`, let $`D`$ be their last common block (fork choice 78, 123–125) and $`sl_\text{top}`$ the later of their tips' slots (126). If $`sl_D + K > sl_\text{top}`$, `c_fork` replaces `c_max` only if it has strictly more blocks after $`D`$ (127–132). Otherwise it replaces it only if it has strictly more blocks with slots in $`(sl_D, sl_D + s]`$ (133–139). The count takes only blocks of the chain; uncle references give no weight (fork choice 100; protocol 390). Forks that do not descend from $`B_\text{imm}`$ are ignored (fork choice 119). The forks are visited in order of block ID (118), each against the current `c_max`. The Online rule takes the strictly longer chain among forks that descend from $`B_\text{imm}`$ (fork choice 148–159).

Since both chains contain $`D`$, the density test compares $`\text{len}(C[0{:}sl_D + s])`$ of the two chains.

**4.2 (Proved). One epoch state after a divergence.** Let two chains share exactly the blocks up to a block $`D`$. For every slot $`t`$ with $`sl_D < t \le sl_D + G + 1`$, both chains derive the epoch state of $`t`$ from blocks they share. This extends REVIEW.md 8.4 (b) from $`2s_{gen}`$ to any span up to $`G + 1`$, with the same assumption A4 of the review on the commitment root.

*Proof.* Let $`D`$ lie in epoch $`e`$, with cut-off $`c_e`$, so that epoch $`e + 1`$ starts at $`c_e + G`$ and epoch $`e + 2`$ at $`c_e + G + E`$ (protocol 153–159). The state of epoch $`e`$ reads blocks below the cut-off of epoch $`e - 1`$, which is before $`D`$ (REVIEW.md 4.3 and its A4); it is shared. The state of epoch $`e + 1`$ reads blocks with slots below $`c_e`$ and the root at the start of epoch $`e`$.
Case $`sl_D \ge c_e - 1`$: the blocks the chains do not share have slots above $`sl_D \ge c_e - 1`$, so the state of epoch $`e + 1`$ is shared. Since $`D`$ lies in epoch $`e`$, $`sl_D \le c_e + G - 1`$, so every $`t \le sl_D + G + 1 \le c_e + 2G < c_e + G + E`$ lies in epoch $`e`$ or $`e + 1`$; here $`G < E`$.
Case $`sl_D \le c_e - 2`$: every $`t \le c_e - 2 + G + 1 = c_e + G - 1`$ lies in epoch $`e`$. ∎

$`G + 1`$ = 259,201 slots, against $`s`$ = 16,200 and $`2K`$ = 72,000 or 129,600 (`out_01_setting.txt`, lines 20–24).

**4.3 (Proved). What a chain's blocks in a window can be.** Let $`X`$ and $`Y`$ share exactly the blocks up to $`D`$, and let $`Y`$'s epoch states agree with $`H`$'s for the slots in question. Every block of $`X`$ with a slot in $`(sl_D, sl_D + G + 1]`$ is an honest block, or a coalition block in a slot that the coalition wins under $`H`$'s states. Two blocks of one chain never share a slot. So $`X`$ has at most $`A(I)`$ coalition blocks in any set of slots $`I \subseteq (sl_D, sl_D + G + 1]`$.

*Proof.* A block needs a Proof of Leadership for its slot under the epoch state its chain derives (protocol 453; leadership 137–146). By 4.2 that state is $`Y`$'s, hence $`H`$'s. A block that is not honest was made by the coalition. By A3 its note's key is one the coalition holds, so the slot is one the coalition wins. Slots increase along a chain (protocol 432). ∎

This is all the coalition can count in a density comparison. Uncles carry no weight (4.1). A slot it did not win cannot hold a block of its chain. An honest block on its fork counts as an honest win, and section 6 treats it.

**4.4 (Proved). The coalition's chance per slot.** A note of value $`v`$ wins when its ticket falls below $`v(t_0 + t_1 v)`$ with $`t_0 = -\ln(1-f)\,P/D`$ and $`t_1 = -\ln^2(1-f)\,P/(2D^2)`$, $`P`$ the field's order (leadership 180–184, 199–223). With an ideal hash, the note wins with chance $`q(v) = a v - (a v)^2/2`$, where $`a = -\ln(1 - f)/D`$. Since $`1 - e^{-x} \ge x - x^2/2`$ for $`x \ge 0`$, $`1 - q(v) \ge e^{-a v}`$. For notes of total value $`V`$, the chance that at least one wins is $`1 - \prod (1 - q(v_i)) \le 1 - e^{-aV} = 1 - (1-f)^{V/D}`$. With $`V/D = \alpha`$ this is $`p_a`$. (The rounding of $`t_0`$ and $`t_1`$ to integers is ignored.) ∎

**4.5 (Cited; consequence Proved). Old keys sign old slots.** The leadership proof shows that a note of the snapshot is unspent in the ledger of the chain it extends, and that $`\text{hash}(\text{LEAD\_V1} \| \eta \| sl \| noteID \| sk)`$ falls below the threshold (leadership 145–149, 177–184). The block is signed with a one-time key that the proof binds (leadership 189–193). Version 1.1.0 removed "the protection against adaptive adversary", and "there is no leader note evolution mechanism anymore" (leadership 28, 68). So whoever holds a note's secret key can prove, for every slot of every epoch whose snapshot holds the note, on every chain on which the note is unspent. A note that its owner spent on $`H`$ after a block $`D`$ is unspent on a fork from $`D`$. The finality study notes the same: "Cryptarchia has no forward security" (`SETTLEMENT.md`, B5, rule 6). Section 9 gives what fails without A3.

## 5. Chain lengths in the model

**5.1 (Proved). Honest depth.** On S, a block made by an honest leader in slot $`t`$ has length at least $`d(t - \Delta - 1) + 1`$.

*Proof.* By A2 the leader holds, before slot $`t`$, every honest block made by slot $`t - \Delta - 1`$ and its ancestors. By S those of length $`d(t - \Delta - 1)`$ descend from its $`B_\text{imm}`$. Under the Online rule $`c_{loc}`$ is a longest tip among those that descend from $`B_\text{imm}`$: a block that extends $`c_{loc}`$ becomes $`c_{loc}`$ and is at least as long as every other tip, and every other block makes the rule visit every tip and keep a longest one (protocol 484–486; fork choice 148–159). So $`\text{len}(c_{loc}) \ge d(t - \Delta - 1)`$, and the leader extends $`c_{loc}`$ (A2). ∎

**5.2 (Proved). Honest growth.** For a set of slots $`I`$, let $`N(I)`$ be the largest number of slots of $`I`$ won by honest stake whose pairwise gaps are at least $`\Delta + 1`$. Then:

1. For an interval, the greedy choice attains $`N(I)`$: take the first honest slot, then the first honest slot more than $`\Delta`$ slots later, and so on.
2. If all of $`I_1`$ precedes all of $`I_2`$ by at least $`\Delta + 1`$ slots, $`N(I_1 \cup I_2 \cup J) \ge N(I_1) + N(I_2)`$ for any $`J`$; and $`N`$ grows with its set.
3. On S, for $`t_1 < t_2`$: $`d(t_2) - d(t_1) \ge N((t_1 + \Delta, t_2])`$.
4. Under A1 with $`P(h_t = 1) = p_h`$, for an interval of $`m`$ slots, $`P(N \ge n) = P(\mathrm{Bin}(m - (n-1)\Delta, p_h) \ge n)`$ for $`n \ge 1`$.

*Proof.* (1) Let $`g_1 < g_2 < \dots`$ be the greedy choice and $`o_1 < o_2 < \dots`$ an optimal one. By induction $`g_i \le o_i`$: $`g_1`$ is the first honest slot, and if $`g_i \le o_i`$, then $`o_{i+1} \ge o_i + \Delta + 1 \ge g_i + \Delta + 1`$ is a candidate for $`g_{i+1}`$. So the greedy choice is at least as long. (2) The union of separated sets is separated; a larger set allows the same choice. (3) Let $`u_1 < \dots < u_m`$ be a choice in $`(t_1 + \Delta, t_2]`$. By 5.1, $`d(u_1) \ge d(u_1 - \Delta - 1) + 1 \ge d(t_1) + 1`$, and $`d(u_{i+1}) \ge d(u_{i+1} - \Delta - 1) + 1 \ge d(u_i) + 1`$. $`d`$ does not decrease, so $`d(t_2) \ge d(t_1) + m`$. (4) Number the slots $`1, \dots, m`$. The greedy times are $`T_1 = W_1`$ and $`T_{i} = T_{i-1} + \Delta + W_i`$, where $`W_i`$ is the wait for the next honest slot. As in REVIEW.md 5.3 Step 3, the $`W_i`$ are independent and geometric with parameter $`p_h`$, and their sum is the trial of the $`n`$-th success in one sequence of independent trials. $`N \ge n`$ iff $`T_n \le m`$ iff $`W_1 + \dots + W_n \le m - (n-1)\Delta`$ iff that sequence has $`n`$ successes in its first $`m - (n-1)\Delta`$ trials. ∎

The formula is the one the study uses (`recovery.honest_logpmf`), with its interval starting $`\Delta`$ slots later. `out_06_checks.txt`, lines 2–5, checks it against a slot-by-slot computation. (Computed.)

**5.3 (Proved). An upper bound for any chain.** Let $`X`$ be a chain, $`e`$ a slot, and $`g`$ the last honest block of $`X[0{:}e]`$ (genesis is honest), in slot $`t_g`$. If the coalition blocks of $`X[0{:}e]`$ after $`g`$ lie in slots that 4.3 covers, then

$$
\text{len}(X[0{:}e]) \le d(t_g) + A((t_g, e]).
$$

*Proof.* $`\text{len}(g) \le d(t_g)`$ by the definition of $`d`$. The blocks of $`X[0{:}e]`$ after $`g`$ are coalition blocks with distinct slots in $`(t_g, e]`$; by 4.3 there are at most $`A((t_g, e])`$. ∎

**5.4 (Proved). A lower bound for a dominant chain.** On S, let $`Y`$ be dominant at `now` with all its blocks under $`H`$'s epoch states, and $`e \le \text{now}`$. Let $`b`$ be the slot of $`Y`$'s first honest block after $`e`$, or $`\text{now} + 1`$ if there is none. Then

$$
\text{len}(Y[0{:}e]) \ge d(b - \Delta - 2) - A((e, b)).
$$

*Proof.* If $`Y`$ has an honest block in slot $`b \le \text{now}`$, an honest leader made it on $`Y[0{:}b-1]`$, so $`\text{len}(Y[0{:}b-1]) \ge d(b - \Delta - 1)`$ by 5.1. Otherwise $`\text{len}(Y) \ge d(\text{now} - \Delta - 1) = d(b - \Delta - 2)`$ by dominance. In both cases the blocks of $`Y`$ in $`(e, b)`$ are coalition blocks with distinct slots, at most $`A((e, b))`$. Removing them leaves $`Y[0{:}e]`$. $`d`$ does not decrease. ∎

`out_06_checks.txt`, lines 23–26, checks 5.1, 5.2 (3), 5.3 and 5.4 on random executions with a randomised coalition, with no violation. (Computed.)

## 6. One divergence block

**6.1 (Proved). What a lost comparison implies.** On S, let $`X`$ and $`Y`$ be chains in $`J`$'s block tree with last common block $`D`$, let $`Y \in \mathcal G`$, let $`e = sl_D + s \le \text{now}`$, and let $`s + K \le G + 1`$. If $`X`$ has at least as many blocks as $`Y`$ in $`(sl_D, e]`$, then

$$
A((t_g, b)) \ge N((t_g + \Delta,\ b - \Delta - 2]),
$$

where $`g`$ is the last honest block of $`X[0{:}e]`$ and $`b`$ is that of 5.4 for $`Y`$. If $`X`$ has no honest block in $`(sl_D, e]`$, then $`t_g \le sl_D`$.

*Proof.* $`Y`$ is not bad, so its blocks after $`D_Y`$ have slots below $`sl_{D_Y} + K \le sl_{D_Y} + G + 1`$; by 4.2 with $`H`$, they are under $`H`$'s epoch states, and 5.4 applies to $`Y`$. The blocks of $`X[0{:}e]`$ after $`g`$ are blocks of $`Y`$ (up to $`D`$) or lie in $`(sl_D, sl_D + s]`$. These slots are below $`sl_{D_Y} + K + s \le sl_{D_Y} + G + 1`$, because $`D`$ is $`D_Y`$, an ancestor of it, or a block of $`Y`$ after it, whose slot is below $`sl_{D_Y} + K`$. So by 4.2 with $`H`$, $`Y`$'s epoch states agree with $`H`$'s on the window, and by 4.3 with $`Y`$, 5.3 applies to $`X`$. Both chains contain $`D`$, so the hypothesis reads $`\text{len}(X[0{:}e]) \ge \text{len}(Y[0{:}e])`$ (4.1). Then

$$
d(b - \Delta - 2) - A((e, b)) \le \text{len}(Y[0{:}e]) \le \text{len}(X[0{:}e]) \le d(t_g) + A((t_g, e]).
$$

So $`d(b - \Delta - 2) - d(t_g) \le A((t_g, b))`$, and 5.2 (3) bounds the left side below by $`N((t_g + \Delta, b - \Delta - 2])`$ (which is 0 if the interval is empty). The last sentence holds because $`g`$ is then on the common prefix. ∎

The check of `out_06_checks.txt`, lines 27–28, finds the inequality in every one of 370,488 pairs in which a chain was at least as long as an honest node's chain up to a slot. (Computed.)

**6.2 (Proved; Computed). Forks with no honest block in the window.** Fix a slot $`\sigma \le \text{now} - K`$, with $`s \le K - 1`$ and $`2K \le G + 1`$. The chance that some $`X`$ with no honest block in $`(\sigma, \sigma + s]`$ and some $`Y \in \mathcal G`$ with last common block in slot $`\sigma`$ have $`X`$ at least as dense as $`Y`$ is at most $`P_1(s)`$, where

$$
P_1(x) = P(M_\text{pre} + Z_x + M^+_\text{post} \ge 0),
$$

$$
M_\text{pre} = \max_{a \le \sigma} \big[A((a, \sigma]) - N((a + \Delta, \sigma])\big], \quad Z_x = A((\sigma, \sigma + x]) - N((\sigma + \Delta, \sigma + x]),
$$

$$
M_\text{post} = \max_{b > \sigma + x} \big[A((\sigma + x, b)) - N((\sigma + x + \Delta,\ b - \Delta - 2])\big].
$$

Let $`\tau_x`$ be the number of slots from the last slot of the greedy choice of 5.2 (1) in $`(\sigma + \Delta, \sigma + x]`$ to $`\sigma + x`$, and $`\tau_x = \Delta + 1`$ if that choice has no slot in $`(\sigma + x - \Delta - 1, \sigma + x]`$. Let $`A_m`$ be the number of the first $`m`$ slots after $`\sigma + x`$ that the coalition wins. Then $`M^+_\text{post} = \max(M_\text{post}, 1 + A_{\Delta - \tau_x})`$ if $`\tau_x \le \Delta`$, and $`M^+_\text{post} = M_\text{post}`$ otherwise.

*Proof.* (a) *Reduction.* By 6.1 the event implies that for some $`a \le \sigma`$ and $`b > \sigma + s`$, $`A((a, b)) \ge N((a + \Delta, b - \Delta - 2])`$. Split $`(a, b)`$ at $`\sigma`$ and $`\sigma + s`$. If $`b \ge \sigma + s + \Delta + 2`$, the three intervals $`(a + \Delta, \sigma]`$, $`(\sigma + \Delta, \sigma + s]`$ and $`(\sigma + s + \Delta, b - \Delta - 2]`$ lie in $`(a + \Delta, b - \Delta - 2]`$ and are separated by at least $`\Delta + 1`$ slots, so by 5.2 (2) the difference $`A - N`$ is at most $`M_\text{pre} + Z_s + M_\text{post}`$. If $`\sigma + s < b \le \sigma + s + \Delta + 1`$, put $`j = \sigma + s + \Delta + 2 - b`$, so that $`1 \le j \le \Delta + 1`$. The intervals $`(a + \Delta, \sigma]`$ and $`(\sigma + \Delta, \sigma + s - j]`$ lie in $`(a + \Delta, b - \Delta - 2]`$ and are separated. The greedy choice in $`(\sigma + \Delta, \sigma + s]`$ has at most one slot after $`\sigma + s - j`$, and it has one exactly when $`\tau_s < j`$. So $`A - N`$ is at most $`M_\text{pre} + Z_s + 1\{\tau_s < j\} + A_{\Delta + 1 - j}`$. For $`j \le \tau_s`$ the last two terms are $`A_{\Delta + 1 - j} \le M_\text{post}`$, as $`M_\text{post} \ge A((\sigma + s, b'))`$ for every $`b' \le \sigma + s + 2\Delta + 2`$, where its honest interval is empty. For $`j > \tau_s`$ they are at most $`1 + A_{\Delta - \tau_s}`$. So $`A - N`$ is at most $`M_\text{pre} + Z_s + M^+_\text{post}`$. $`M_\text{pre}`$ reads the slots up to $`\sigma`$, $`(Z_s, \tau_s)`$ the window, and $`M^+_\text{post}`$, given $`\tau_s`$, the slots after the window. So the three are independent given $`\tau_s`$ (A1). The event grows with each $`a_t`$ and shrinks with each $`h_t`$, so A1's bound on $`a_t`$ lets the computation use $`P(a_t = 1) = p_a`$; it uses $`P(h_t = 1) = p_h`$, and A1 states what the circuit's shortfall adds.

(b) *The laws.* $`Z_x`$ is $`\mathrm{Bin}(x, p_a)`$ minus an independent $`N`$ over $`x - \Delta`$ slots (5.2 (4)). For $`M_\text{pre}`$, put $`u = \sigma - a`$ and $`v = u - \Delta`$. For $`u < \Delta`$ the bracket is at most its value at $`u = \Delta`$. For $`v \ge 0`$ it is $`Y_v`$, where $`Y_0 = A`$ of the last $`\Delta`$ slots, $`\sim \mathrm{Bin}(\Delta, p_a)`$, and $`Y_{v+1} = Y_v + a' - \eta`$: $`a'`$ is the coalition indicator of the slot $`v + \Delta + 1`$ back, and $`\eta = 1`$ if the slot $`v + 1`$ back is honest and the greedy count from the right takes it (5.2 (1)), after which the next $`\Delta`$ slots are not taken. Each step reads one new coalition indicator and one new honest indicator of distinct slots, so $`M_\text{pre} = \max_v Y_v`$ for a Markov chain on (value, slots left before the next slot can be taken). $`M_\text{post}`$ is the same chain started at $`\mathrm{Bin}(2\Delta + 1, p_a)`$: with $`u = b - \sigma - x - 1`$ and $`v = u - 2\Delta - 1`$, the coalition count runs over the first $`2\Delta + 1 + v`$ slots after $`\sigma + x`$ and the honest count over $`v`$ slots that start $`\Delta`$ slots in. Given $`A_m = i`$ with $`m \le \Delta`$, $`M_\text{post} = i + J + W`$, where $`J \sim \mathrm{Bin}(2\Delta + 1 - m, p_a)`$ and $`W`$ is the maximum of the chain started at value 0 with no slot left, and $`J`$ and $`W`$ are independent. This gives the law of $`M^+_\text{post}`$ given $`\tau_x`$: $`A_m + \max(J + W, 1)`$ with $`m = \Delta - \tau_x`$. The honest count of the window runs over its last $`m' = x - \Delta`$ slots. With $`T_n`$ the slot of its $`n`$-th greedy pick, counted from the start of those slots, no later pick fits after $`T_n = m' - t`$ for $`t \le \Delta`$. So $`P(N = n, \tau_x = t) = P(T_n = m' - t) = p_h\,P(\mathrm{Bin}(m' - t - (n-1)\Delta - 1, p_h) = n - 1)`$ for $`t \le \Delta`$ and $`n \ge 1`$. By 5.2 (4), $`P(N = n, \tau_x \ge \Delta + 1) = P(T_n \le m' - \Delta - 1) - P(T_{n+1} \le m') = (1 - p_h)\,P(\mathrm{Bin}(m' - n\Delta - 1, p_h) = n)`$. The coalition's count of the window is independent of both.

(c) *The tail of the maximum.* Let $`\varphi(y, c)`$ be the chance that the chain, started at value $`y < m`$ with $`c`$ slots left, ever reaches $`m`$. Group the steps in cycles: a geometric wait for a taken honest slot, then $`\Delta`$ untaken slots. The cycle's increment $`\xi = \mathrm{Bin}(W + \Delta, p_a) - 1`$, with $`W`$ geometric($`p_h`$), is independent from cycle to cycle. Within a cycle the value never exceeds its value at the cycle's end plus one. With $`J \sim \mathrm{Bin}(c, p_a)`$ the coalition count of the $`c`$ slots left, $`\max_v Y_v \le y + J + 1 + \max_n S_n`$, where $`S_n`$ sums $`n`$ cycle increments. Lundberg's inequality, $`P(\max_n S_n \ge z) \le e^{-\theta^* z}`$ with $`\theta^* > 0`$ the root of $`E[e^{\theta\xi}] = 1`$, gives

$$
\varphi(y, c) \le e^{-\theta^*(m - y - 1)}\,(1 - p_a + p_a e^{\theta^*})^c .
$$

The root exists when $`E[\xi] = p_a(1/p_h + \Delta) - 1 < 0`$, which holds for $`\Delta`$ below 56 slots against 30 % and 44 against a third (`out_01_setting.txt`, lines 41–43). The script solves the hitting problem exactly on the strip $`m - 400 \le y \le m - 1`$, with this bound as the value below it. The chain leaves the strip with chance 1, and its hitting chance is the expected value at exit, so a larger value below gives a larger solution: the solution bounds $`\varphi`$. Averaging over $`Y_0`$ gives tails $`T(m) \ge P(\max Y \ge m)`$. Distributions with these tails, the excess placed at $`+\infty`$, dominate $`M_\text{pre}`$ and $`M^+_\text{post}`$ given $`\tau_x`$, and the event of (a) grows with both. So the sum, over the joint law of $`(Z_x, \tau_x)`$, of the chance that $`M_\text{pre} + M^+_\text{post} \ge -Z_x`$ bounds $`P_1(x)`$. ∎

**Computed.** `out_02_window.txt`:

| Setting | $`P(Z_s \ge 0)`$ | $`P_1(s)`$ | least $`x`$ with $`P_1(x) \le 10^{-9}`$ | lines |
| --- | --- | --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | $`6.016\cdot10^{-14}`$ | $`2.055\cdot10^{-13}`$ | 11,335 slots (3.15 h) | 7–10 |
| 30 %, $`\Delta`$ = 15 | $`6.951\cdot10^{-11}`$ | $`2.564\cdot10^{-10}`$ | 15,164 slots (4.21 h) | 18–21 |
| a third, $`\Delta`$ = 10 | $`3.863\cdot10^{-9}`$ | $`1.345\cdot10^{-8}`$ | 18,640 slots (5.18 h) | 29–32 |
| a third, $`\Delta`$ = 15 | $`8.650\cdot10^{-7}`$ | $`3.180\cdot10^{-6}`$ | 27,151 slots (7.54 h) | 40–43 |

- $`P(Z_s \ge 0)`$ is the single-window chance without the two maxima. It equals RFC-532's figures, $`6.0\cdot10^{-14}`$ and $`3.9\cdot10^{-9}`$ (Cited: RFC-532 309). The strict variant equals the study's $`4\cdot10^{-14}`$ (`out_02_window.txt`, line 7; Cited: `SETTLEMENT.md`, B5).
- The maxima cost a factor of 3.4 to 3.7 (lines 8, 19, 30, 41). They are the coalition's lead from before the divergence block and the coalition blocks that end $`Y`$'s part of the window. The term $`1 + A_{\Delta - \tau_x}`$ of $`M^+_\text{post}`$ adds 1.05 to 1.86 % to $`P_1(s)`$ (same lines).
- The tails of the maxima agree with a Monte Carlo, and to twelve digits with an exact forward computation (`out_06_checks.txt`, lines 8–15). $`P_1`$ agrees with a Monte Carlo of $`M_\text{pre} + Z_x + M^+_\text{post}`$ from slot bits at short windows (lines 18–20). At inflated rates, the event of 6.1 implied $`M_\text{pre} + Z_x + M^+_\text{post} \ge 0`$ in all 94,350 samples in which it held, while $`M_\text{pre} + Z_x + M_\text{post} < 0`$ in 452 of them (lines 30–31). The closed form of $`P_1`$ and a forward pass over the window's slots agree to $`7.5 \cdot 10^{-12}`$ relative (`out_04_union.txt` lines 3, 14, 25, 36). So the only loss in 6.2 is the split of 6.2 (a) and the coalition's best case of 6.1. (Computed.)

**6.3 (Proved, given A6; Computed). Every fork.** Fix a slot $`\sigma \le \text{now} - K`$, with $`s \le K - 1`$ and $`2K \le G + 1`$. The chance that some $`X`$ and some $`Y \in \mathcal G`$ with last common block in slot $`\sigma`$ have $`X`$ at least as dense as $`Y`$ is at most

$$
U(s - 1) + P_1(K - s) + P_1(G + 1 - s).
$$

*Proof.* Let $`D`$ be the block, $`e = \sigma + s`$, $`\ell = \sigma + 1`$, and $`b`$ as in 5.4 for $`Y`$.

Case: $`Y`$ has an honest block after $`e`$, and $`b \le \sigma + G + 1`$. Consider the execution with the same lottery and the same honest behaviour in which the coalition also makes, in each slot it wins, a withheld block on every chain whose tip has an earlier slot. Honest nodes never receive these blocks, so they act as before. In it, let $`\tilde X`$ extend $`X[0{:}e]`$ by one such block in each slot of $`(e, b)`$ that the coalition wins. These slots lie within $`G + 1`$ of $`D`$, so by 4.2 they are wins under $`Y`$'s, hence $`H`$'s, states. Then

$$
\text{len}(\tilde X) \ge \text{len}(X[0{:}e]) + A((e, b)) \ge \text{len}(Y[0{:}e]) + A((e, b)) \ge \text{len}(Y[0{:}b-1]) \ge d(b - \Delta - 1),
$$

using that $`Y`$'s blocks in $`(e, b)`$ are coalition blocks, and 5.1 (an honest leader built on $`Y[0{:}b-1]`$). So $`\tilde X`$ and $`Y[0{:}b-1]`$ are made by slot $`b - 1`$, and each is at least as long as every chain ending in an honest block made by slot $`b - \Delta - 1`$. They share no block with a slot of at least $`\ell`$, and $`b - 1 \ge e = \ell + s - 1`$. By A6 at slot $`b`$, $`\mu_\ell \ge 0`$ at slot $`b - 1`$. That event reads the lottery alone, which the two executions share, so the lost comparison in the first execution implies it, and its chance is at most $`U(s - 1)`$.

Case: $`b > \sigma + G + 1`$. Then $`Y`$ has no honest block in $`(e, \sigma + G + 1]`$. Apply 5.3 and 5.4 to $`Y`$ alone: with $`g'`$ the last honest block of $`Y[0{:}e]`$, $`d(b - \Delta - 2) - A((e, b)) \le \text{len}(Y[0{:}e]) \le d(t_{g'}) + A((t_{g'}, e])`$. As in 6.1 this gives $`A((t_{g'}, b)) \ge N((t_{g'} + \Delta, b - \Delta - 2])`$ with $`t_{g'} \le e`$ and $`b > e + (G + 1 - s)`$. As in 6.2 (a) with $`\sigma`$ replaced by $`e`$, its chance is at most $`P_1(G + 1 - s)`$.

Case: $`Y`$ has no honest block after $`e`$, and $`b = \text{now} + 1 \le \sigma + G + 1`$. Then $`Y`$ may hold a block of slot `now`, and the two chains cannot be taken to end before slot `now`. As in the second case, with $`b = \text{now} + 1 > e + (K - s)`$, since $`\text{now} \ge \sigma + K`$, its chance is at most $`P_1(K - s)`$. ∎

7.2 bounds this last case again, over every divergence slot at once.

**Computed.** `out_03_settle.txt`, lines 5, 8, 15, 18, 25, 28, 35, 38, and `out_02_window.txt`, lines 11, 22, 33, 44:

| Setting | $`U(s - 1)`$ | $`P_1(K - s)`$, $`K`$ = 36,000 | $`P_1(G + 1 - s)`$ | least $`s`$ with $`U(s - 1) \le 10^{-9}`$ |
| --- | --- | --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | $`1.349\cdot10^{-7}`$ | $`4.0\cdot10^{-16}`$ | $`\le 7.2\cdot10^{-39}`$ | 21,336 slots (5.93 h) |
| 30 %, $`\Delta`$ = 15 | $`4.341\cdot10^{-5}`$ | $`2.3\cdot10^{-12}`$ | $`\le 2.1\cdot10^{-35}`$ | 33,729 slots (9.37 h) |
| a third, $`\Delta`$ = 10 | $`8.263\cdot10^{-5}`$ | $`2.9\cdot10^{-10}`$ | $`\le 3.6\cdot10^{-30}`$ | 36,383 slots (10.11 h) |
| a third, $`\Delta`$ = 15 | $`4.133\cdot10^{-3}`$ | $`2.2\cdot10^{-7}`$ | $`\le 2.2\cdot10^{-26}`$ | 62,519 slots (17.37 h) |

- The least windows are one slot above the study's stored waits, because A6 costs one slot (`out_03_settle.txt`, lines 8, 18, 28, 38; Cited: `runs/k7/worst.csv`).
- At $`K`$ = 64,800, $`P_1(K - s)`$ is below $`2\cdot10^{-16}`$ in every setting (`out_02_window.txt`, lines 11, 22, 33, 44).
- With the terms that read $`K`$ (6.3 and 7.2), a window of 21,336 slots meets $`10^{-9}`$ against 30 % at 10 slots at either $`K`$. At 15 slots no window meets it at $`K`$ = 36,000, and 33,729 slots do at $`K`$ = 64,800 (`out_04_union.txt`, lines 10 and 21).

**6.4 (Proved: the construction, in GRR's model; Estimate: the chances). The second bound counts a real attack.** In GRR's model, suppose that at some slot $`t \ge \sigma + s + 1`$ the coalition holds two chains, made under $`H`$'s states, that share no block after a block $`D`$ in slot $`\sigma`$, and that are each at least as long as every honest block made by slot $`t`$. Then, with ties broken for the coalition as GRR's model allows, it can leave a fork that $`J`$ finds at least as dense as the honest chain at $`D`$. If $`J`$ switches after the fork holds $`\phi`$ occupied slots in the $`K`$ or more slots after a block $`X'`$ after $`D`$, the switch's `commit` fixes $`X'`$.

*Proof.* Let $`X`$ be the chain with at least as many blocks in $`(\sigma, \sigma + s]`$ and $`Y`$ the other. In GRR's model an honest leader extends the longest chain of a view that the coalition chooses; the view must contain the honest chains made $`\Delta + 1`$ slots before, and the coalition breaks ties (GRR §2.1). The specification gives no such tie-breaking: a tie keeps `c_max` (fork choice 130–131, 156–157), so an honest node that holds a chain on $`X`$'s side as long as $`Y`$ keeps it until $`Y`$'s branch is strictly longer. Every honest chain made by slot $`t`$ is at most as long as $`Y`$. So the coalition can give every honest leader from slot $`t`$ on a view in which $`Y`$'s branch is longest, and never show $`X`$'s coalition blocks. Honest blocks then extend $`Y`$'s branch only, which stays longer than every honest chain on $`X`$'s side. The honest chain then contains $`Y[0{:}\sigma + s]`$. The coalition extends $`X`$ in private with its own wins. After $`G + 1`$ slots $`X`$ derives its own epoch states, its inferred stake falls with its count of occupied slots (protocol 233–247), and its wins come no slower. Once $`X`$'s tip lies $`K`$ slots after a block $`X'`$ after $`D`$ with $`\phi`$ occupied slots between them, $`J`$, given $`X`$, compares it with the honest chain by density at $`D`$ (4.1), finds it at least as dense, and keeps it if it is strictly denser, or if it is `c_max` when the honest tips are visited; the pass starts at `c_local` (fork choice 117). The switch's `commit` then fixes $`X'`$ (REVIEW.md 3.6). ∎

So, in GRR's model, a settlement failure at a wait of $`s`$ slots can be turned into a lost density comparison. GRR's attack of §4.7 keeps two chains at or above the depth of the deepest honest block, which is the hypothesis of 6.4. The study gives, for that attack, the block depths at which its chance falls to $`10^{-6}`$ and $`10^{-9}`$ in GRR's model, computed at depths 20 to 120 and extended past them by a log-linear fit. It converts them to hours at $`\Delta + 1/p_h`$ seconds a block (Cited: `runs/k1/worst.csv`, columns `lb_depth` and `lb_h_estimate`, copied to `runs/k7/worst.csv`; all eight points used here are extended; `out_03_settle.txt`, lines 9–10, 19–20, 29–30, 39–40). A log-linear line through the two points, read at $`s`$ = 4.5 hours, gives about $`4.7\cdot10^{-11}`$, $`3.0\cdot10^{-8}`$, $`8.6\cdot10^{-7}`$ and $`7.5\cdot10^{-5}`$ in the four settings (`out_03_settle.txt`, lines 11, 21, 31, 41). For 30 % at 10 slots and a third at 15 slots, 4.5 hours lies outside the two points. (Estimate.) These estimates lie 55 to 2,900 times below $`U(s - 1)`$ (same lines), so the bound of 6.3 may be loose by as much. The true chance per divergence slot lies at or below the bound of 6.3; the estimate suggests that it lies above $`10^{-9}`$ at 15 slots and against a third.

## 7. The final pass and the switch

**7.1 (Proved). The reduction.** On S, let $`s \le K - 1`$ and $`2K \le G + 1`$. $`J`$ holds (2.3) unless one of these events occurs:

- $`E_d(\sigma)`$, for some slot $`\sigma`$ from $`J`$'s starting block to $`\text{now} - K`$: some chains $`X`$ and $`Y \in \mathcal G`$ of $`J`$'s block tree, with last common block in slot $`\sigma`$, have $`X`$ at least as dense as $`Y`$ in $`(\sigma, \sigma + s]`$;
- $`E_r`$: two chains of $`\mathcal D_\text{now}`$, made under $`H`$'s states, share no block with a slot of at least $`\text{now} - K + 1`$;
- $`E_g`$: honest stake wins no slot of $`[\text{now} - K + \Delta + 1, \text{now} - \Delta - 1]`$.

*Proof.* The chain $`c_{loc}`$ at the switch is the result of the pass of the Bootstrap rule at the last block processed (bootstrap 247; protocol 486). That pass starts at some chain and visits every tip of the tree that descends from $`J`$'s $`B_\text{imm}`$ (4.1), among them every tip whose chain contains $`H`$ (by A2 and A5); call these $`H`$-tips. Let $`D(X, Y)`$ be the last common block of two chains. Assume that none of the three events occurs.

*Step 0. Chains that contain $`H`$ and are dominant lie in $`\mathcal G`$.* For such a chain $`Z`$, $`D_Z`$ is $`H`$'s last block. No honest block is made in a slot from $`sl_{D_Z} + \Delta + 1`$ to $`\text{now} - \Delta - 1`$, since by 5.1 it would be longer than $`H`$, against the definition of $`H`$. Without $`E_g`$, therefore, $`sl_{D_Z} > \text{now} - K \ge sl_Z - K`$, so $`Z`$ is not bad. Every $`H`$-tip is dominant, since its length is at least $`\text{len}(H) = d(\text{now} - \Delta - 1)`$.

*Step 1. After the last $`H`$-tip is visited, `c_max` lies in $`\mathcal G`$.* Let $`h'`$ be that tip and $`Y_0`$ the `c_max` before it, with $`D = D(Y_0, h')`$. If $`h'`$ replaces $`Y_0`$, Step 0 applies. If not: in a comparison by density, $`Y_0`$ is at least as dense as $`h' \in \mathcal G`$, with $`sl_D + K \le \text{now}`$; that is $`E_d(sl_D)`$. In a comparison by length, $`\text{len}(Y_0) \ge \text{len}(h')`$, so $`Y_0`$ is dominant, and $`sl_D + K > sl_{Y_0}`$. If $`D`$ is a block of $`H`$ other than its last, then $`D_{Y_0} = D`$, because $`h'`$ continues with $`H`$'s next block and $`Y_0`$ does not; so $`Y_0`$ is not bad. Otherwise $`Y_0`$ contains $`H`$ and Step 0 applies to it.

*Step 2. A visit keeps `c_max` in $`\mathcal G`$.* Let `c_max` $`= Y \in \mathcal G`$, visit $`X`$, and let $`D = D(X, Y)`$. If $`X`$ does not replace $`Y`$, nothing changes. A replacement by density means $`X`$ strictly denser than $`Y \in \mathcal G`$ with $`sl_D + K \le \text{now}`$: that is $`E_d(sl_D)`$. A replacement by length makes $`X`$ longer than $`Y`$, hence dominant, with $`sl_D + K > sl_X`$. If $`D`$ is $`D_Y`$ or an ancestor of it, $`X`$ shares $`H`$'s blocks up to $`D`$, so $`sl_{D_X} \ge sl_D > sl_X - K`$ and $`X`$ is not bad. Otherwise $`D`$ lies after $`D_Y`$ on $`Y`$. If $`Y`$ contains $`H`$, so does $`X`$, and Step 0 applies. If not, $`D_X = D_Y`$, and $`X`$'s blocks after $`D_X`$ have slots below $`sl_D + K \le sl_Y + K < sl_{D_Y} + 2K`$, using that $`Y`$ is not bad. By 4.2 with $`2K \le G + 1`$ they are under $`H`$'s states. If $`X`$ were bad, $`X`$ and $`H`$ would be two chains of $`\mathcal D_\text{now}`$ that share no block with a slot of at least $`sl_{D_X} + 1`$, where $`sl_{D_X} + 1 \le sl_X - K + 1 \le \text{now} - K + 1`$: that is $`E_r`$.

*Step 3.* By Steps 1 and 2, the `c_max` at the end of the pass, which is $`c_{loc}`$ at the switch, lies in $`\mathcal G`$. ∎

The events are those of 2.5: $`E_d`$ is the density comparison's, $`E_r`$ and S are the window $`K`$'s, and $`E_g`$ is a long silence of the honest stake. The proof uses only one window after $`D`$, and the first honest block of $`Y`$ after it (5.4) in place of the paper's second window. So it needs $`s \le K - 1`$, not $`2s \le K`$.

**7.2 (Proved, given A6; Computed). The other two events.** $`P(E_r) \le U(K - 2)`$. The bad fork of $`E_r`$ is strictly longer than a dominant chain (7.1, Step 2). So, without a block of slot `now`, it is at least as long as $`d(\text{now} - \Delta - 1)`$, and so is $`H`$, which ends in a slot of at most $`\text{now} - \Delta - 1`$. By A6 at slot `now`, with $`\ell = sl_{D_X} + 1 \le \text{now} - K + 1`$, $`\mu_\ell \ge 0`$ at slot $`\text{now} - 1 \ge \ell + K - 2`$. $`P(E_g) \le (1 - p_h)^{K - 2\Delta - 1}`$ by A1, which is below $`10^{-353}`$ (`out_01_setting.txt`, lines 37–39).

The last case of 6.3 has a second bound, over every divergence slot at once. In that case, extend $`X[0{:}e]`$ as in the first case by a withheld block in each slot of $`(e, \text{now}]`$ that the coalition wins; these slots lie within $`G + 1`$ of $`D`$. This chain is at least as long as $`Y`$, as in the first case. The two chains are made by slot `now` under $`H`$'s states, each is at least as long as every chain ending in an honest block made by slot $`\text{now} - \Delta - 1`$, and they share no block with a slot of at least $`\sigma + 1 \le \text{now} - K + 1`$. $`E_r`$ gives two such chains too. An execution that meets A2 with $`\Delta`$ meets it with $`\Delta + 1`$. With delay $`\Delta + 1`$ these chains are made by slot $`(\text{now} + 1) - 1`$ and at least as long as every chain ending in an honest block made by slot $`(\text{now} + 1) - (\Delta + 1) - 1`$. By A6 at delay $`\Delta + 1`$ and slot $`\text{now} + 1`$, $`\mu_{\text{now} - K + 1} \ge 0`$ at slot `now`. So $`E_r`$ and the last case of 6.3 at every divergence slot together have chance at most $`U_{\Delta+1}(K - 1)`$.

| Setting | $`U(K-2)`$, $`K`$ = 36,000 | $`U_{\Delta+1}(K-1)`$, $`K`$ = 36,000 | $`U(K-2)`$, $`K`$ = 64,800 | $`U_{\Delta+1}(K-1)`$, $`K`$ = 64,800 |
| --- | --- | --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | $`8.3\cdot10^{-16}`$ | $`1.3\cdot10^{-14}`$ | $`9.4\cdot10^{-28}`$ | $`1.4\cdot10^{-25}`$ |
| 30 %, $`\Delta`$ = 15 | $`2.5\cdot10^{-10}`$ | $`2.1\cdot10^{-9}`$ | $`6.0\cdot10^{-18}`$ | $`2.7\cdot10^{-16}`$ |
| a third, $`\Delta`$ = 10 | $`1.2\cdot10^{-9}`$ | $`8.5\cdot10^{-9}`$ | $`1.2\cdot10^{-16}`$ | $`3.8\cdot10^{-15}`$ |
| a third, $`\Delta`$ = 15 | $`6.1\cdot10^{-6}`$ | $`2.4\cdot10^{-5}`$ | $`4.7\cdot10^{-10}`$ | $`5.4\cdot10^{-9}`$ |

(`out_03_settle.txt`, lines 6–7, 16–17, 26–27, 36–37.)

**7.3 (Proved, given A6). The theorem for the joining node.** In the model of section 3, with $`s \le K - 1`$ and $`2K \le G + 1`$,

$$
P(\text{S holds and } J \text{ does not hold}) \le P\Big(\bigcup_\sigma E_d(\sigma)\Big) + U(K - 2) + (1 - p_h)^{K - 2\Delta - 1},
$$

where the union is over slots from $`J`$'s starting block to $`\text{now} - K`$, and section 8 bounds it. $`P(\bigcup_\sigma E_d(\sigma)) \le \sum_\sigma P(E_d(\sigma))`$, and $`P(E_d(\sigma)) \le U(s - 1) + P_1(K - s) + P_1(G + 1 - s)`$ by 6.3. The part with no honest block of $`X`$ in the window is at most $`P_1(s)`$ by 6.2. By 7.2, $`U(K - 2)`$ and the terms $`P_1(K - s)`$ together may be replaced by $`U_{\Delta+1}(K - 1)`$. If $`J`$ holds, 2.4 applies.

*Proof.* 7.1, 7.2, 6.2 and 6.3. ∎

**7.4 (Proved). Uncles and the floor at the switch.** Uncles count in `commit`'s floor (protocol 322, 393) but not in the density comparison (4.1), so they do not enter 6.1 to 7.3. The floor does not replace the density comparison either. A fork made of coalition blocks reaches $`\phi`$ occupied slots after a block once its tip is far enough past it. At the coalition's mean rate under $`H`$'s states that takes about 68,090 slots (18.9 h) for $`\phi`$ = 689 and 127,583 (35.4 h) for 1,291 (`out_01_setting.txt`, lines 33–35), and a long-range attacker has the time. (The mean-rate figures are an estimate; the statement that the floor is met eventually is proved by the law of large numbers.)

## 8. All divergence blocks of a history

A node that syncs from genesis can be offered a fork at every block of the history. A naive union over divergence slots multiplies a bound by the number of slots, $`3.15\cdot10^7`$ a year. The events of nearby slots are nested, and that gives a better accounting.

**8.1 (Proved; the second bound given A6). Cells.** For integers $`g \ge 1`$ and $`c`$, let the cell be the slots $`(c - g, c]`$.

1. The union, over $`\sigma`$ in the cell, of the events of 6.2 has chance at most $`P_1(s - g + 1)`$.
2. The union, over $`\sigma`$ in the cell, of the events of 6.3 has chance at most $`U(s - g) + P_1(K - s - g + 1) + P_1(G + 2 - s - g)`$.

So if the divergence slots of $`J`$'s history span $`L`$ slots, the first term of 7.3, $`P(\bigcup_\sigma E_d(\sigma))`$, is at most $`\lceil L/g \rceil \big(U(s - g) + P_1(K - s - g + 1) + P_1(G + 2 - s - g)\big)`$ for every $`g`$, and the chance of its part from forks with no honest block in their window is at most $`\lceil L/g \rceil P_1(s - g + 1)`$. By 7.2, $`U(K - 2)`$ and the terms $`P_1(K - s - g + 1)`$ together may be replaced by $`U_{\Delta+1}(K - 1)`$.

*Proof.* (1) The event of 6.2 at $`\sigma`$ implies $`A((a, b)) \ge N((a + \Delta, b - \Delta - 2])`$ for some $`a \le \sigma \le c`$ and $`b > \sigma + s \ge c + (s - g + 1)`$. 6.2 (a) bounds this event for the window $`(c, c + s - g + 1]`$. (2) In the first case of 6.3 the two chains share no block with a slot of at least $`\sigma + 1`$, hence none with a slot of at least $`c + 1`$, at slot $`b - 1 \ge \sigma + s \ge (c + 1) + (s - g)`$. A6's event for $`\ell = c + 1`$ and $`w = s - g`$ contains all of them. In the second case, $`t_{g'} \le \sigma + s \le c + s`$ and $`b > \sigma + G + 1 \ge (c + s) + (G + 2 - s - g)`$, and 6.2 (a) applies with $`c + s`$ in place of $`\sigma`$. In the last case, $`b = \text{now} + 1 > \sigma + K \ge (c + s) + (K - s - g + 1)`$, and 6.2 (a) applies in the same way. ∎

**8.2 (Computed). The bounds over a history.** The least value over every cell width $`g`$ (`out_04_union.txt`). For every fork the table gives the cells. The terms that read $`K`$ change no figure of the table at either $`K`$ (the same lines):

| Setting | Part | one divergence slot | 1 day | 30 days | 1 year | lines |
| --- | --- | --- | --- | --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | no honest block in the window | $`2.1\cdot10^{-13}`$ | $`8.4\cdot10^{-11}`$ | $`2.5\cdot10^{-9}`$ | $`3.1\cdot10^{-8}`$ | 4–7 |
| | every fork | $`1.35\cdot10^{-7}`$ | $`3.0\cdot10^{-5}`$ | $`9.1\cdot10^{-4}`$ | $`1.1\cdot10^{-2}`$ | 4–7 |
| 30 %, $`\Delta`$ = 15 | no honest block in the window | $`2.6\cdot10^{-10}`$ | $`7.9\cdot10^{-8}`$ | $`2.4\cdot10^{-6}`$ | $`2.9\cdot10^{-5}`$ | 15–18 |
| | every fork | $`4.3\cdot10^{-5}`$ | $`6.2\cdot10^{-3}`$ | 0.19 | no bound | 15–18 |
| a third, $`\Delta`$ = 10 | no honest block in the window | $`1.3\cdot10^{-8}`$ | $`3.4\cdot10^{-6}`$ | $`1.0\cdot10^{-4}`$ | $`1.2\cdot10^{-3}`$ | 26–29 |
| | every fork | $`8.3\cdot10^{-5}`$ | $`1.1\cdot10^{-2}`$ | 0.33 | no bound | 26–29 |
| a third, $`\Delta`$ = 15 | no honest block in the window | $`3.2\cdot10^{-6}`$ | $`5.5\cdot10^{-4}`$ | $`1.7\cdot10^{-2}`$ | 0.20 | 37–40 |
| | every fork | $`4.1\cdot10^{-3}`$ | 0.32 | no bound | no bound | 37–40 |

The best cells are 576 to 1,350 slots wide for the first part and 1,041 to 3,086 for the second. The least window that keeps the bound at $`10^{-9}`$, the cells alone for every fork (lines 11–12, 22–23, 33–34, 44–45):

| Setting | over 1 day, no honest block / every fork | over 1 year, no honest block / every fork |
| --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | 14,778 (4.11 h) / 27,003 (7.50 h) | 18,167 (5.05 h) / 33,181 (9.22 h) |
| 30 %, $`\Delta`$ = 15 | 19,533 (5.43 h) / 41,876 (11.63 h) | 24,050 (6.68 h) / 51,560 (14.32 h) |
| a third, $`\Delta`$ = 10 | 23,837 (6.62 h) / 45,083 (12.52 h) | 29,415 (8.17 h) / 55,599 (15.44 h) |
| a third, $`\Delta`$ = 15 | 34,190 (9.50 h) / 75,736 (21.04 h) | 42,291 (11.75 h) / 93,673 (26.02 h) |

With the terms that read $`K`$, the windows for every fork are the same against 30 % at $`K`$ = 64,800, and against 30 % at 10 slots at $`K`$ = 36,000. At 15 slots no window meets $`10^{-9}`$ at $`K`$ = 36,000, because $`U_{16}(K - 1) = 2.1\cdot10^{-9}`$ and the terms $`P_1(K - s - g + 1)`$ grow as $`s`$ nears $`K`$ (same lines; 7.2).

A history that starts at a checkpoint or at the node's own $`B_\text{imm}`$ is shorter than one from genesis, and the bound scales with its length.

## 9. Keys acquired later

**9.1 (Proved). Without A3 the density comparison fails.** Suppose that the coalition holds the keys of notes of the window's stake distribution that carry a further share $`b`$ and are unspent on $`H`$ at $`D`$. By 4.5 it can sign blocks with them on a fork from $`D`$. By 4.4 it then wins each slot of the fork's window with chance up to $`1 - (1-f)^{\alpha + b}`$, and its fork can hold a block in each such slot. If the coalition keeps its own blocks off $`H`$ in the window, $`H`$'s count there is at most the number of slots won by the stake honest at the time, with chance $`1 - (1-f)^{1-\alpha}`$ per slot. If $`\alpha + b > 1 - \alpha`$, the fork is denser with a chance that tends to 1 as $`s`$ grows, by the law of large numbers, so no window suffices. Under the worst-case delay $`H`$ may hold only its guaranteed count $`N`$, whose rate is $`1/(\Delta + 1/p_h)`$ (5.2 (4)), and the fork matches that rate at a smaller $`b`$. ∎

Keys of notes that their owners have spent are worth nothing to them on $`H`$, so this needs no large outlay. The specification states no bound on such keys (4.5). A3 therefore stands as an assumption, and the bound on the keys an attacker can collect bounds how far back a history can be trusted. The study states the same constraint for its recovery horizon (Cited: `SETTLEMENT.md`, B5, rule 6).

**9.2 (Computed). The scale.** Within $`G + 1`$ slots of $`D`$ the fork derives $`H`$'s epoch states (4.2), and a note's ticket depends only on $`\eta`$, the slot, the note and its key (leadership 180). So an acquired note wins on the fork exactly the slots it won on $`H`$, where it was honest. The bound of 6.2 then takes, per slot, the coalition's own win $`a`$, the acquired stake's win $`b`$ and the win $`r`$ of the stake that stays honest, independent, with chances $`p(\alpha)`$, $`p(b)`$ and $`p(1 - \alpha - b)`$. The fork counts $`a \lor b`$, $`N`$ reads $`b \lor r`$, and the maxima stay at $`\alpha`$, because they count blocks made at their time (`out_05_keys.txt`):

| Setting | $`b`$ at which the bound reaches $`10^{-9}`$ | bound at $`b`$ = 0.05 | $`b`$ at which the fork's mean rate equals $`1/(\Delta + 1/p_h)`$ | lines |
| --- | --- | --- | --- | --- |
| 30 %, $`\Delta`$ = 10 | 0.0481 | $`1.4\cdot10^{-9}`$ | 0.2657 | 4–5 |
| 30 %, $`\Delta`$ = 15 | 0.0077 | $`8.4\cdot10^{-7}`$ | 0.2162 | 9–10 |
| a third, $`\Delta`$ = 10 | above $`10^{-9}`$ at 0 | $`1.0\cdot10^{-5}`$ | 0.2104 | 14–15 |
| a third, $`\Delta`$ = 15 | above $`10^{-9}`$ at 0 | $`9.3\cdot10^{-4}`$ | 0.1645 | 19–20 |

At the last column's $`b`$ the bound is about 0.56 to 0.60. With the acquired wins drawn independently of the honest ones, the first column would be 0.0393 and 0.0064 (lines 6, 11). Notes spent on $`H`$ inside the window win on the fork after they stop winning on $`H`$; that is the model of 12.7. With no delay the fork matches the honest stake at $`b = 1 - 2\alpha`$: 0.4 against 30 %.

## 10. Comparisons

**10.1 (Cited; Computed). The paper's hypotheses.** They hold only for $`\Delta \le 2`$ slots at these parameters (Cited: REVIEW.md 8.5 and its `out_07_genesis.txt`). The bounds here have no such limit. 6.2 needs the drift of 6.2 (c) to be negative, which holds for $`\Delta`$ below 56 slots against 30 % and 44 against a third (`out_01_setting.txt`, lines 41–43). 6.3 needs $`U`$, which the study computes for any delay. The structure of the argument follows the paper's.

| The paper's proof of Theorem 2 | This document |
| --- | --- |
| a candidate denser in the first window yields a common-prefix violation of $`k\beta/64`$ blocks | a fork with no honest block in the window: the exact bound $`P_1(s)`$ (6.2); any fork: settlement at a wait of $`s - 1`$ slots, $`U(s - 1)`$ (6.3) |
| a second window gives an honest block after the first ($`\exists`$CQ) | the first honest block of the dominant chain after the window, priced exactly by $`M_\text{post}`$ (5.4, 6.2) |
| both windows within the fork's age: $`2s \le k/(2f)`$; in the specification $`2s_{gen} \le K`$ | one window within the comparison's age: $`s \le K - 1`$ (7.1) |
| one stake distribution and nonce over both windows: $`2s \le R/3`$ | one epoch state for $`G + 1`$ slots after the divergence (4.2), used up to $`2K \le G + 1`$ |
| adaptive corruption handled by key-evolving signatures | not available: no key evolution (4.5); A3 assumed |

**10.2 (Cited; Computed). RFC-532 and the study.** RFC-532 gives, over one window at 10 s, $`6.0\cdot10^{-14}`$ for a fork of 30 % and $`3.9\cdot10^{-9}`$ for a third, and 4.8 to 4.9 hours for a third at $`10^{-9}`$, as "single-window estimates, not the study's bound" (Cited: RFC-532 309). They are $`P(Z_s \ge 0)`$ of 6.2 (`out_02_window.txt`, lines 7 and 29). With the coalition's lead before the window and its blocks after it, the bound is 3.4 times larger at 30 % and 3.5 times against a third, and a third needs 5.18 hours (lines 8, 30, 32). These figures cover forks with no honest block in the window only. RFC-532's "two windows within $`K`$" is the paper's condition; the reduction of 7.1 does not need it.

**10.3 (Cited). Cardano.** The implementation of Genesis in Ouroboros Consensus compares densities over $`S_{gen}`$ slots after the intersection and sets $`S_{gen} = S_{cg}`$, the chain-growth window $`3k/f`$, 129,600 slots at $`f`$ = 0.05, as "the most conservative assignment"; it states no probability bound, and lists smaller windows as follow-up work (Cited: Ouroboros Consensus, "Cardano Genesis", `docs/website/contents/references/miscellaneous/genesis_design.md`: Notation and Parameter Tuning for $`S_{gen} = S_{cg}`$; The Genesis Density Disconnection Component with CSJ for "the most conservative assignment"; Compatibility with the HardFork Combinator for $`S_{cg}`$ = 60·Kcp; Follow-Up Work for smaller windows; read 2026-11-18). That is twelve times the paper's $`k/(4f)`$ at Cardano's $`f`$. No later analysis of the density rule with sharper bounds was found. GRR bound settlement, not the density rule.

**10.4 (Computed). The states of the $`K`$ row, against 30 %.** With the mapping of REVIEW.md 5.9 (Assumed) (`out_07_states.txt`):

| State | $`P_1(s_{gen})`$ | $`U(s_{gen} - 1)`$ | least window, no honest block / every fork | every fork with the terms that read $`K`$, at $`K`$ = 36,000 | lines |
| --- | --- | --- | --- | --- | --- |
| no disturbance | $`2.1\cdot10^{-13}`$ | $`1.35\cdot10^{-7}`$ | 11,335 / 21,336 | 21,336 | 1–3 |
| every block $`T_M`$ late | $`2.6\cdot10^{-10}`$ | $`4.3\cdot10^{-5}`$ | 15,164 / 33,729 | none | 5–7 |
| a tenth of the honest stake offline, inference corrected | $`5.2\cdot10^{-10}`$ | $`1.3\cdot10^{-5}`$ | 15,684 / 30,215 | 30,508 | 9–11 |
| the same, before the correction | $`9.0\cdot10^{-10}`$ | $`1.3\cdot10^{-5}`$ | 16,114 / 30,249 | 30,492 | 13–15 |
| $`D`$ equals the honest stake online | $`8.5\cdot10^{-15}`$ | $`4.5\cdot10^{-7}`$ | 10,197 / 23,061 | 23,062 | 17–19 |

The worst state for forks without honest blocks is a tenth offline before the correction, $`9.0\cdot10^{-10}`$, just within $`10^{-9}`$, with a least window of 16,114 slots against $`s_{gen}`$ = 16,200. With the circuit's shortfall it is $`9.05\cdot10^{-10}`$ (line 16). The worst for every fork is the first disturbance. At $`K`$ = 64,800 the last column equals the windows for every fork (the same lines).

## 11. Whether $`s_{gen}`$ and $`K`$ suffice

By the bounds of this document, in the model of section 3 and on S:

- **Against the long-range fork** (no honest block in the window), $`s_{gen}`$ = 16,200 meets $`10^{-9}`$ per divergence slot against 30 % in every state of the $`K`$ row, the closest being $`9.0\cdot10^{-10}`$. It does not against a third: $`1.3\cdot10^{-8}`$ at 10 slots. (Computed, 6.2, 10.4.) Over a history at 30 % and 10 slots it meets $`10^{-9}`$ for a day ($`8.4\cdot10^{-11}`$) but not for 30 days ($`2.5\cdot10^{-9}`$); a year needs 18,167 slots at 10 and 24,050 at 15. (Computed, 8.2.)
- **Against every fork**, the bounds do not reach $`10^{-9}`$ in any setting: per divergence slot the bound is at least $`U(s_{gen} - 1) = 1.35\cdot10^{-7}`$. A window of 21,336 slots would meet it against 30 % with no disturbance, and 33,729 in the worst state of the $`K`$ row. Over a year the needs are 33,181 and 51,560 slots. (Computed, 6.3, 8.2, 10.4.) The estimate of 6.4 suggests that the true chance per divergence slot at 30 % and 10 slots is near $`5\cdot10^{-11}`$, below $`10^{-9}`$, but $`3\cdot10^{-8}`$ at 15 slots and $`9\cdot10^{-7}`$ against a third, above it. (Estimate.) So the density window is the weak point, and the weakness is a split that lasts the window (6.4).
- **$`K`$.** The reduction of 7.1 needs $`s \le K - 1`$ and $`2K \le G + 1`$. It costs $`U(K - 2)`$ for $`E_r`$: $`8.3\cdot10^{-16}`$ against 30 % at 10 slots and $`2.5\cdot10^{-10}`$ at 15 slots for $`K`$ = 36,000, and below $`10^{-17}`$ for 64,800. The case of 6.3 in which the dominant chain has no honest block after the window costs $`P_1(K - s)`$ per divergence slot: $`2.3\cdot10^{-12}`$ at 15 slots and $`s_{gen}`$, but large when $`s`$ nears $`K`$. Over every divergence slot at once, with $`E_r`$, it costs $`U_{\Delta+1}(K - 1)`$ instead: $`1.3\cdot10^{-14}`$ at 10 slots and $`2.1\cdot10^{-9}`$ at 15 slots for $`K`$ = 36,000 (6.3, 7.2). So $`K`$ = 36,000 admits the needs at 10 slots, 21,336 slots per divergence slot and 33,181 over a year. At 15 slots no window meets $`10^{-9}`$ at $`K`$ = 36,000 by these bounds. $`K`$ = 64,800 admits all the needs at 30 %. Against a third at 10 slots, $`U(K-2)`$ is $`1.2\cdot10^{-9}`$ at 36,000. The specification's rule $`2s_{gen} \le K`$ forbids all of these windows at $`K`$ = 36,000, and all but 21,336 at $`K`$ = 64,800, but this proof does not use that rule. (Proved, 7.1; Computed, `out_04_union.txt` lines 8–12, 19–23.)
- **All of it rests on A3**, which the specification does not enforce. Keys of 4.8 % more stake lift the long-range bound above $`10^{-9}`$ against 30 % at 10 slots. (Computed, 9.2.)

## 12. What is not proved here

1. **A6.** GRR state Lemma 10 for a block produced in slot $`\ell`$. A6 reads the margin for two chains that share no block from slot $`\ell`$ on, at one slot. 6.3, 7.2 and 8.1 (2) rest on it. A proof from GRR's definitions of reach and margin on public trees would close this half. The other half, that $`U(w)`$ bounds the margin at every slot from $`\ell + w`$ on, rests on the study's clock in `waitbound`, which this document does not check.
2. **A lower bound for forks with honest blocks.** 6.4 proves that a split lasting the window gives a lost comparison, but the chance of such a split is only estimated, by a log-linear line through two extended depths of the study's numerical evaluation of GRR's lower bound, converted to hours at the worst-case block interval. An exact computation of GRR's §4.7 attack against a wait in slots, as the study's `waitbound` does for the upper bound, would close it.
3. **The union over a history.** Cells bound it by $`\lceil L/g \rceil`$ times a window's bound. The true chance of a scan over a long history may be smaller by a constant factor.
4. **The nonce.** A4 is assumed, as in the $`K`$ row. A coalition that can choose among several nonces gains several draws of each window's lottery. That is not bounded here.
5. **S**, the Online rule's guarantee, is cited from the $`K`$ row, not derived. The theorems hold on S.
6. **A3** is an assumption that the specification does not enforce (section 9).
7. **The model.** Independent tickets, shares that hold over the whole history, honest notes that stay unspent in the windows, and a worst-case delay $`\Delta`$. $`J`$ needs an honest peer that delivers within $`\Delta`$ (A2): an eclipsed node is not covered, as RFC-532 accepts.
8. **The $`K`$ row's states** use REVIEW.md 5.9's mapping.
9. **The switch's floor.** 6.4 needs the fork to reach $`\phi`$ occupied slots past a block; the time it takes is an estimate at mean rates (7.4).
10. **The study's clock.** $`U(w)`$ bounds the margin at every slot from $`\ell + w`$ on only through the study's construction in `waitbound` (its phase clock, the weighting of the step that covers $`\ell`$, and the slot mapping). This document cites it and does not check it.
11. **Ties.** 6.4 uses GRR's tie-breaking. The specification keeps `c_max` on a tie, so the attack also needs $`Y`$'s branch to become strictly longer than every honest chain on $`X`$'s side, a race the coalition must win.
12. **The circuit's threshold.** Honest stake wins slightly less often than $`p_h`$ (A1). $`U`$ is computed at $`p_h`$, and the shortfall's effect on it is not computed.

## 13. Files

All files are in this folder. The scripts run with the finality study's interpreter and need `numpy`, `scipy` and `numba`; `g03`, `g04` and `g07` import `finality_sim.waitbound` and cache its curves, at delays $`\Delta`$ and $`\Delta + 1`$, in `.cache/`.

| File | Content | Statements |
| --- | --- | --- |
| `common_g.py` | constants; $`N`$ and the joint law of $`(N, \tau_x)`$; the circuit's shortfall; the strip bound on the maximum; $`P_1`$ in closed form and by a forward pass over the window's slots; the joint laws of a slot for 6.2 and 9.2; the wrapper of $`U`$ | 3, 5.2, 6.2, 6.3, 9.2 |
| `g01_setting.py`, `out_01_setting.txt` | the constants checked against the specification's text with `git show`; rates; the floor's time; $`E_g`$; the drift limit | 1, 6.2, 7.2, 7.4 |
| `g02_window.py`, `out_02_window.txt` | $`P(Z_s \ge 0)`$, $`P_1`$, the maxima's tails, least windows, the terms of 6.3, the circuit's shortfall | 3, 6.2, 6.3, 10.2 |
| `g03_settle.py`, `out_03_settle.txt` | $`U`$ and $`U_{\Delta+1}`$ at the waits read, the study's stored waits, the attack estimates | 6.3, 6.4, 7.2 |
| `g04_union.py`, `out_04_union.txt` | the cells over histories of a day, 30 days and a year, over every width; the terms that read $`K`$; least windows | 6.2, 6.3, 8.2, 11 |
| `g05_keys.py`, `out_05_keys.txt` | keys acquired later: identical tickets, and independent wins for comparison | 9.2 |
| `g06_checks.py`, `out_06_checks.txt` | checks: $`N`$; the maxima; $`P_1`$ by Monte Carlo; random executions; the step of 6.2 (a) path by path | 5, 6 |
| `g07_states.py`, `out_07_states.txt` | the states of the $`K`$ row | 3, 10.4 |

Each script names its usage in its first lines.
