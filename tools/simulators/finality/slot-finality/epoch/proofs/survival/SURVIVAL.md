# Survival of a branch without honest blocks

Date: 2026-11-18.

This document proves the survival law that section 9 of the review of the epoch schedule takes from the finality study without proof. It then recomputes the buffer $`w_B`$ and the epochs that rest on it.

## 0. Result in brief

- **The theorem.** Take the model of section 2. The coalition may follow any strategy, and it schedules every delivery of an honest block within $`d`$ slots. Fix a slot $`s_0`$ and an integer $`T \ge d`$. The chance that slot $`s_0`$ holds an honest block $`H_0`$ and that some honest node holds, at some slot $`t \ge s_0 + T`$, a local chain whose blocks after $`H_0`$ are all the coalition's, is at most $`h\,\hat Q(T)`$, on the event that assumption A5 holds. Here $`h`$ is the chance that the honest stake that builds wins a slot. $`\hat Q(T)`$ is the chance of a lottery event (5.3): at some count $`n`$ of the greedy $`d`$-isolated honest wins after $`s_0`$, the coalition has won at least $`n`$ slots, and the next count comes after slot $`s_0 + T`$. A5 says that every honest block, and every block of its chain, that reaches an honest node during the period descends from that node's $`B_\text{imm}`$ or is $`B_\text{imm}`$. It is the guarantee that sizes $`K`$. (Proved, 6.1. Assumed, A1 to A5.)
- $`\hat Q`$ is computed exactly by a recursion over slots, from above and from below (Proved, 6.3 to 6.7; Computed, 7.1). $`\hat Q`$ is nearly attained: in an instance with many honest nodes an adversary reaches the event with a chance of at least $`(1 - c)(\hat Q(T) - \hat Q(35{,}000))`$, with $`c \le 5.43 \cdot 10^{-4}`$ and $`\hat Q(35{,}000) \le 4.0 \cdot 10^{-15}`$ (Proved, 9.3; Computed, `out_3_buffer.txt` lines 28–36).
- **The study's law is not an upper bound.** `branch_survival` lies below $`\hat Q`$ by a factor of 1.0623 to 1.1018 at every whole hour from 1 to 6 in every state (Computed, `out_2_survival.txt` line 83). It counts an honest block when it is made, not when every honest node must hold it, and it does not count a branch that an honest node keeps on a tie (Proved, 9.2). Each departure alone lowers it: the first by a factor of 1.015 to 1.032, the second by 1.054 to 1.095, at 1 to 6 hours in every state (Computed, `out_2_survival.txt` line 111).
- **The buffer.** $`w_B`$ grows by 45 to 69 slots in every state. Over the states of the latest #533 it is at most 17,268 slots (4.80 h) in place of 17,215 (4.78 h), and 17,709 slots (4.92 h) in place of 17,654 (4.90 h) when a tenth offline is read before the inference corrects. (Computed, `out_3_buffer.txt` lines 2–10.)
- **The epochs that suffice.** With the window shortened to phases 1 and 2: 37.83 h in place of 37.81 h, and 38.11 h in place of 38.09 h before the inference corrects. For the base: 66.81 h in place of 66.79 h, and 68.14 h in place of 68.12 h. With the window kept at 108 h the window and phase 3 decide, and 128.00 and 144.00 h do not change. Phase 3 lasts $`2K - 1`$ slots, as review 10.2 requires. (Computed, `out_4_epoch.txt` lines 9–20.)
- Not proved here: A5, the final chain of review 9.3, the reading of the lottery as a random oracle with an unbiased nonce (A1), the review's mapping of states to shares, and rounding in double precision (section 12).

## 1. Setting

### 1.1 Texts

Line numbers of the specification are those of `git show 7f3cf149:docs/blockchain/raw/<path>`, the latest #533 (review 1.1).

| Short name | Path | Used for |
| --- | --- | --- |
| protocol | `cryptarchia-v1-protocol.md` | constants, header validation, `on_block`, `commit` |
| fork choice | `fork-choice.md` | the Online rule |
| leadership | `cryptarchia-proof-of-leadership.md` | the lottery |
| review | `../../REVIEW.md` | its sections 1, 2, 3.7, 5.2, 5.3, 5.9, 9, 10, 11 and 12 |

The study's code is read at commit `0df6f2bb` of the worktree `fast-finalization-slots`, in `tools/simulators/finality/src/finality_sim/`: `formation.py` 390–405 (`branch_survival`), `grinding.py` 76–93 (`walk`), 96–120 (`_ladder`) and 123–134 (`_renewal`), `fork_bound.py` 76–85 (`blocks_pmf`), `nonce.py` 150–156 (`_rates`) and `recovery.py` 28–30 (`occupancy`).

### 1.2 Labels

The labels are those of review 2: Proved, Computed, Cited and Assumed. Every number of this text is printed by a script of this folder, and the text names the file and its lines. Probabilities are evaluated in double precision.

### 1.3 Conventions

- Slots are integers. A slot lasts one second (protocol 106).
- The *state of a node at slot $`t`$* is its state once it has processed every block delivered to it up to and including slot $`t`$.
- A leader of slot $`t`$ builds on its $`c_{loc}`$ in its state at slot $`t - 1`$.
- The *height* of a block is its number of ancestors. Header validation compares heights (protocol 441).
- A coalition's share is a share of the total active stake, counted while all of the honest stake is online (review 1.3). The shares $`x_h`$ and $`x_a`$ of this text are shares of the inferred total stake $`D`$.
- $`\mathrm{Bin}(m, p)`$ is a binomial variable. $`\mathrm{Geo}(r)`$ takes the values $`j = 0, 1, \dots`$ with chance $`(1 - r) r^j`$. $`[P]`$ is 1 when $`P`$ holds and 0 otherwise.

## 2. The model

The model extends $`M(p, d)`$ of review 5.2 in three ways. The coalition's wins are added. The delay $`d`$ is a bound within which the coalition schedules each delivery, not the exact delay of M2. The chain that each node holds follows from the Online rule as printed, in place of M2. With $`x = x_h`$, the honest marks of 2.2 are M1 and M4.

**2.1 (Cited). The lottery.** A note with secret key $`sk`$ and value $`v`$ wins slot $`sl`$ when $`\text{hash}(\text{LEAD\_V1} \| \eta \| sl \| noteID \| sk)`$ is below $`v(t_0 + t_1 v)`$ (leadership 180–184). $`t_0`$ and $`t_1`$ are computed from $`D`$, so that the chance is the second-order expansion of $`1 - (1-f)^{v/D}`$ (leadership 141, 199–212). The error is negative and at most 0.0444 % of the chance for a note of up to all of $`D`$ (leadership 254–281). A note may lead only if it was in the note set at the start of the previous epoch (protocol 173), so that its owner cannot fit it to $`\eta`$ (protocol 175–177).

**A1 (Assumed). Independent tickets.** The ticket hash acts as a random oracle. $`\eta`$ is fixed and unbiased during the period; the $`K`$ row takes the nonce as unbiased (protocol 104). Then tickets with different $`(sl, noteID)`$ are independent and uniform.

**A2 (Assumed). Fixed shares.** During the period $`D`$ and $`\eta`$ do not change. The honest stake that builds is a share $`x_h`$ of $`D`$, and the coalition's stake is a share $`x_a`$ of $`D`$.

**Lemma 2.2 (Proved). The marks.** Take the chance of a note as $`1 - (1-f)^{v/D}`$. Under A1 and A2 write $`\xi_t = 1`$ when some note of the honest stake that builds wins slot $`t`$, and $`\zeta_t = 1`$ when some note of the coalition wins it. Then the marks $`\xi_t`$ and $`\zeta_t`$ of all slots are independent, and

$$
\Pr[\xi_t = 1] = h = 1 - (1-f)^{x_h}, \qquad \Pr[\zeta_t = 1] = a = 1 - (1-f)^{x_a}.
$$

*Proof.* By A1 the events "note $`i`$ wins slot $`t`$" are independent over all pairs $`(i, t)`$. $`\xi_t`$ is a function of the events of the honest notes at slot $`t`$, and $`\zeta_t`$ of those of the coalition's notes. These are disjoint sets of independent events, so the marks are independent. A note of value $`v_i`$ loses with chance $`(1-f)^{v_i/D}`$. So $`\Pr[\xi_t = 0] = \prod_i (1-f)^{v_i/D} = (1-f)^{x_h}`$ by A2, and in the same way $`\Pr[\zeta_t = 0] = (1-f)^{x_a}`$. ∎

**Lemma 2.3 (Proved). The circuit's threshold.** Let each note's chance lie between $`1 - \delta`$ and 1 times $`1 - (1-f)^{v/D}`$, with $`\delta = 4.44 \cdot 10^{-4}`$ (2.1). Then the marks stay independent, $`(1 - \delta)h \le \Pr[\xi_t = 1] \le h`$, and $`\Pr[\zeta_t = 1] \le a`$.

*Proof.* Independence follows as in 2.2. Let $`p_i`$ be the chances of 2.2 and $`c_i \in [1 - \delta, 1]`$ the factors. The function $`g(c) = 1 - \prod_i (1 - c\,p_i)`$ is concave on $`[0, 1]`$, because its second derivative is $`-\sum_{i \ne j} p_i p_j \prod_{k \ne i, j} (1 - c\,p_k) \le 0`$. With $`g(0) = 0`$ this gives $`g(c) \ge c\,g(1)`$. The chance of $`\xi_t = 1`$ grows with each $`c_i`$, so it is at least $`g(1 - \delta) \ge (1 - \delta) h`$, and at most $`g(1) = h`$. For the coalition, $`c_i \le 1`$ gives at most $`a`$. ∎

**2.4 (Assumed). The coalition.** It holds the coalition's notes and knows their wins ahead of time. For each slot it wins, it may make any number of blocks of that slot, on any parent it holds, at any time from that slot on, or none. It sees every honest block when the block is made. It may deliver any block it holds to any honest node at any time. A block is valid at a node only from its own slot on (protocol 435).

**A3 (Assumed). Delivery.** Every honest block of slot $`s`$, with every block of its chain, is in the state of every honest node at slot $`s + d`$. The coalition chooses when, within that bound, and in which order. Source: the $`K`$ row's premise that every honest block is delivered at most $`\Delta`$ late, or at most $`T_M`$ late in its first disturbance (protocol 104). The chain comes with the block, because a node accepts a block only once the block's parent is in its tree (protocol 438). Clocks agree (protocol 599–601).

**A4 (Assumed). Honest nodes.** The honest nodes considered are online during the period. They run the Online rule: `on_block` (protocol 470–494) with `online_fork_choice` (fork choice 148–159). A leader of the honest stake builds a block in each slot it wins, on its $`c_{loc}`$ in its state at the slot before. Such a block is *honest*. It is valid at every honest node that holds its chain, subject to A5. The honest stake makes no other block, so every block that is not honest is the coalition's.

**A5 (Assumed). $`B_\text{imm}`$ stays below the honest blocks.** During the period, whenever an honest block, or a block of its chain, is delivered to an honest node, that node's $`B_\text{imm}`$ is an ancestor of the block or the block itself. Source: the guarantee that sizes $`K`$, a chance of at most $`\varepsilon`$ per block that a coalition displaces an immutable block (protocol 104), and the premise of the Online rule that nodes stay on the honest chain by rejecting forks that diverge before $`B_\text{imm}`$ (fork choice 71). The bounds below hold on the event that A5 holds. A failure of A5 is the event against which $`K`$ is sized, and it is not counted in them.

**2.5 (Cited). Chain rules.** A block's slot exceeds its parent's slot (protocol 432). So a chain holds at most one block in a slot, and slots increase along it. A node accepts a block only when the block's slot is at most the current slot (protocol 435). So every block in a node's state at slot $`t`$ has a slot of at most $`t`$.

**2.6 (Assumed). The states.** The review maps each state of the $`K`$ row to a building share and a delay (review 5.9, Assumed there). The coalition holds 30 % of the total active stake, and its share of $`D`$ follows in each state. `out_1_walk.txt`, lines 2–10, prints each state's $`x_h`$, $`x_a`$, $`d`$, $`h`$ and $`a`$.

| State | $`x_h`$ | $`x_a`$ | $`d`$ | Required by |
| --- | --- | --- | --- | --- |
| no disturbance | 0.7 | 0.3 | 10 | both cases |
| every honest block 15 s late | 0.7 | 0.3 | 15 | both cases |
| a tenth of the honest stake offline, after the inference corrects | 0.63/0.93 | 0.3/0.93 | 10 | both cases, first reading |
| a deflated inference | 1 | 0.3/0.7 | 10 | both cases |
| 15 s and a tenth offline, after the inference corrects | 0.63/0.93 | 0.3/0.93 | 15 | the base, first reading |
| 15 s and a deflated inference | 1 | 0.3/0.7 | 15 | the base |
| a tenth offline and a deflated inference | 1 | 0.3/0.63 | 10 | the base |
| a tenth offline before the inference corrects | 0.63 | 0.3 | 10 | both cases, second reading |
| 15 s and a tenth offline before the inference corrects | 0.63 | 0.3 | 15 | the base, second reading |

The latest #533 requires one disturbance at a time, and the base two together (review 5.9).

## 3. Two properties of the Online rule

**Lemma 3.1 (Proved).** At an honest node under A4:

1. every change of $`c_{loc}`$ raises its height, so the height of $`c_{loc}`$ never falls;
2. right after the node adds a block $`B`$ to its tree, its $`c_{loc}`$ is at least as high as $`B`$.

*Proof.* (1) `on_block` returns without a change at protocol 474, or sets $`c_{loc}'`$ by protocol 486. In the second case of 486, $`c_{loc}' = B`$ with $`\text{parent}(B) = c_{loc}`$, which is one block higher. In the third case, `online_fork_choice` starts from $`c_{max} = c_{loc}`$, and replaces $`c_{max}`$ only by a fork with `depth_max < depth_fork` (fork choice 149–158). These are the depths of the two tips below their divergence block (fork choice 82–88). So the test reads: the fork is higher than $`c_{max}`$. The result is $`c_{loc}`$ or a higher block. `commit` does not change $`c_{loc}`$ (protocol 500–522).

(2) $`B`$ was not in the tree $`T`$, or the call returns at 474. No block of $`T' = T \cup \{B\}`$ has $`B`$ as its parent, because every block of $`T`$ has its parent in $`T`$ (protocol 438). So $`B`$ is a tip of $`T'`$. $`B`$ passed step 8 of header validation, so it descends from $`B_\text{imm}`$ (protocol 441–442). In the second case of 486, $`c_{loc}' = B`$. In the third, `online_fork_choice` visits $`B`$, and $`B`$ passes its test `is_ancestor` (fork choice 151). After that visit $`c_{max}`$ is at least as high as $`B`$, and later visits only raise it. ∎

Part 1 is where the rule for ties acts: a fork that is only as high as $`c_{loc}`$ never replaces it.

## 4. Honest chain growth

**4.1 (Definitions).** Fix an honest block $`H_0`$ with slot $`s_0`$ and height $`\ell_0`$. Put $`\tau_0 = s_0`$. For $`i \ge 1`$, let $`\tau_i`$ be the first slot $`u > \tau_{i-1} + d`$ with $`\xi_u = 1`$. These are the *greedy $`d`$-isolated honest wins* after $`s_0`$. Let

$$
N(u) = |\{i \ge 1 : \tau_i \le u\}|, \qquad \sigma_i = \tau_i + d .
$$

Call $`\sigma_i`$ the *count* of the $`i`$-th win. Then $`\sigma_0 = s_0 + d`$, and for $`t \ge s_0 + d`$, $`\sigma_i \le t`$ exactly when $`i \le N(t - d)`$.

**Lemma 4.2 (Proved). Chain growth.** Assume A3 to A5. For every strategy of the coalition and every delivery schedule within $`d`$, every honest node's $`c_{loc}`$ in its state at a slot $`t \ge s_0 + d`$ has a height of at least $`\ell_0 + N(t - d)`$.

*Proof.* We show for every $`i \ge 0`$:
(a) some honest block of slot $`\tau_i`$ has a height of at least $`\ell_0 + i`$;
(b) at every slot $`t \ge \sigma_i`$, every honest node's $`c_{loc}`$ has a height of at least $`\ell_0 + i`$.

(a) gives (b). By A3 the block of (a) is in the node's state at slot $`\tau_i + d = \sigma_i`$. By A5 the node accepted it. By 3.1 (2) its $`c_{loc}`$ was at least as high right after, and by 3.1 (1) it stays so.

(a) holds for $`i = 0`$ with $`H_0`$. Let $`i \ge 1`$. As $`\xi_{\tau_i} = 1`$, a leader of the honest stake wins slot $`\tau_i`$. By A4 it builds a block on its $`c_{loc}`$ in its state at slot $`\tau_i - 1`$. As $`\tau_i - 1 \ge \tau_{i-1} + d = \sigma_{i-1}`$, (b) for $`i - 1`$ gives that $`c_{loc}`$ a height of at least $`\ell_0 + i - 1`$. So the new block has a height of at least $`\ell_0 + i`$. Its slot exceeds its parent's, by 2.5.

For $`t \ge s_0 + d`$ put $`i = N(t - d)`$. Then $`\sigma_i \le t`$ (4.1), and (b) gives the claim. ∎

## 5. From a held branch to the lottery

**5.1 (Definitions).** A chain is a *pure branch from $`H_0`$* when it contains $`H_0`$ and every block after $`H_0`$ on it is the coalition's. Let $`A(t) = |\{u : s_0 < u \le t,\ \zeta_u = 1\}|`$ be the number of slots the coalition wins after $`s_0`$. For $`t \ge s_0 + d`$ put

$$
X(t) = A(t) - N(t - d), \qquad U_n = A(\sigma_n) - n = X(\sigma_n) \quad (n \ge 0).
$$

$`X(t)`$ is the coalition's lead over the honest growth of 4.2. $`U_n`$ is that lead right after the $`n`$-th count. $`U_0 = A(s_0 + d) \ge 0`$.

**Lemma 5.2 (Proved). The pure branch and the tie.** Assume A3 to A5. Let an honest node hold, in its state at a slot $`t \ge s_0 + d`$, a $`c_{loc}`$ that is a pure branch from $`H_0`$ with $`m`$ blocks after $`H_0`$. Let $`n = N(t - d)`$. Then:

1. $`n \le m \le A(t)`$;
2. if $`m = n`$, then $`U_n \ge 0`$.

*Proof.* (1) The height of $`c_{loc}`$ is $`\ell_0 + m`$, and it is at least $`\ell_0 + n`$ by 4.2. The $`m`$ blocks after $`H_0`$ are the coalition's. They have distinct slots in $`(s_0, t]`$ (2.5), and the coalition won each of these slots, since each block carries a valid proof of leadership (protocol 444–455). So $`m \le A(t)`$.

(2) For $`n = 0`$, $`U_0 \ge 0`$. Let $`n \ge 1`$. Then $`\sigma_n \le t`$ (4.1). By 4.2, the node's $`c_{loc}`$ at slot $`\sigma_n`$ had a height of at least $`\ell_0 + N(\tau_n) = \ell_0 + n`$. At slot $`t`$ its height is $`\ell_0 + n`$. By 3.1 (1) the height stayed $`\ell_0 + n`$ in between, and $`c_{loc}`$ did not change, because every change raises the height. So the pure branch was already $`c_{loc}`$ at slot $`\sigma_n`$, and all its blocks have slots of at most $`\sigma_n`$ (2.5). Its $`n`$ blocks after $`H_0`$ lie in distinct slots of $`(s_0, \sigma_n]`$ that the coalition won. So $`A(\sigma_n) \ge n`$. ∎

**Lemma 5.3 (Proved). The event in counts.** For $`T \ge d`$, let $`E_T(H_0)`$ be the event that some honest node holds, in its state at some slot $`t \ge s_0 + T`$, a $`c_{loc}`$ that is a pure branch from $`H_0`$. Let

$$
\hat G_T = \{\text{some } n \ge 0 \text{ has } U_n \ge 0 \text{ and } \sigma_{n+1} > s_0 + T\}.
$$

Under A3 to A5, $`E_T(H_0) \subseteq \hat G_T`$.

*Proof.* Take such a slot $`t`$ and node, and put $`n = N(t - d)`$. Then $`\sigma_n \le t < \sigma_{n+1}`$ (4.1). If $`m = n`$, 5.2 (2) gives $`U_n \ge 0`$, and $`\sigma_{n+1} > t \ge s_0 + T`$. Otherwise $`m \ge n + 1`$, and 5.2 (1) gives $`X(t) \ge 1`$. On $`[\sigma_n, \sigma_{n+1} - 1]`$, $`N(u - d)`$ does not change and $`A`$ does not fall, so $`X(\sigma_{n+1} - 1) \ge X(t) \ge 1`$. At $`\sigma_{n+1}`$ one honest win is added to the count, so $`U_{n+1} = X(\sigma_{n+1} - 1) + \zeta_{\sigma_{n+1}} - 1 \ge 0`$. And $`\sigma_{n+2} > \sigma_{n+1} > t \ge s_0 + T`$. So $`n + 1`$ serves. ∎

## 6. The survival bound

**Theorem 6.1 (Proved). The survival bound.** Assume A1 to A5. Let $`s_0`$ be a slot and $`T \ge d`$ an integer. For every strategy of the coalition and every delivery schedule within $`d`$,

$$
\Pr[\text{some honest block } H_0 \text{ of slot } s_0 \text{ has } E_T(H_0), \text{ and A5 holds}] \le h\,\hat Q(T), \qquad \hat Q(T) = \Pr[\hat G_T] .
$$

$`\hat Q(T)`$ depends only on $`h`$, $`a`$, $`d`$ and $`T`$.

*Proof.* An honest block of slot $`s_0`$ needs $`\xi_{s_0} = 1`$. $`\hat G_T`$ is defined by the marks after slot $`s_0`$ alone, and not by which honest block of slot $`s_0`$ is $`H_0`$. By 5.3, whatever the coalition does, the event lies in $`\{\xi_{s_0} = 1\} \cap \hat G_T`$. By 2.2 these two events are independent, so the chance is at most $`h \Pr[\hat G_T]`$. By 2.2 and A2 the marks after $`s_0`$ have the same law for every $`s_0`$, so $`\Pr[\hat G_T]`$ depends only on $`h`$, $`a`$, $`d`$ and $`T`$. ∎

So $`\hat Q(T)`$ is the law $`\mathrm{survival}(T)`$ of review 9.3: for each honest block $`H_0`$, it bounds the chance that a branch with no honest block after $`H_0`$ is a local chain of an honest node at a slot at least $`T`$ after $`H_0`$. It covers every such slot, not one fixed slot.

**Corollary 6.2 (Proved). Two simpler laws.** Let $`Q(T)`$ be the chance that $`X(t) \ge 0`$ at some $`t \ge s_0 + T`$, and $`Q_1(T)`$ the chance that $`X(t) \ge 1`$ at some such $`t`$. Then $`Q_1(T) \le \hat Q(T) \le Q(T)`$.

*Proof.* If $`U_n \ge 0`$ and $`\sigma_{n+1} > s_0 + T`$, then $`t = \max(\sigma_n, s_0 + T)`$ lies in $`[\sigma_n, \sigma_{n+1} - 1]`$, and $`X(t) \ge X(\sigma_n) = U_n \ge 0`$. If $`X(t) \ge 1`$ with $`t \ge s_0 + T`$, the second half of the proof of 5.3 gives $`U_{n+1} \ge 0`$ and $`\sigma_{n+2} > s_0 + T`$. ∎

$`Q`$ is what 5.2 (1) gives without the tie argument of 5.2 (2). $`Q_1`$ asks for a strict lead.

From here on put $`s_0 = 0`$.

**Lemma 6.3 (Proved). Gaps, and the coalition's wins per gap.**

1. $`\tau_i - \tau_{i-1} = d + G_i`$, where $`G_1, G_2, \dots`$ are independent and $`\Pr[G_i = g] = h(1-h)^{g-1}`$ for $`g \ge 1`$.
2. For $`n \ge 1`$, $`A(\sigma_n) - A(\sigma_{n-1})`$ has the law of $`Y = \mathrm{Bin}(d + 1, a) + \mathrm{Geo}(r)`$, with independent terms and

$$
r = \frac{a(1-h)}{a(1-h) + h} .
$$

These increments are independent of each other and of the marks up to slot $`\sigma_{n-1}`$.

*Proof.* (1) $`G_i`$ is the place of the first 1 among the $`\xi_u`$ with $`u > \tau_{i-1} + d`$. For each slot $`v`$, whether $`\tau_{i-1} + d = v`$ is fixed by the marks up to $`v`$. The marks after $`v`$ are independent of that and of each other (2.2). So $`G_i`$ is geometric and independent of the earlier gaps. This is the argument of review 5.3, step 3.

(2) The slots of $`(\sigma_{n-1}, \sigma_n]`$ are the $`G_n`$ slots up to $`\tau_n`$, whose honest marks are $`0, \dots, 0, 1`$, and the $`d`$ slots after $`\tau_n`$. The coalition's marks are independent of the honest ones. On the $`d`$ last slots they give $`\mathrm{Bin}(d, a)`$. On the slot $`\tau_n`$ they give $`\mathrm{Bin}(1, a)`$. On the $`G_n - 1`$ slots before $`\tau_n`$ their sum has the generating function

$$
\sum_{m \ge 0} h(1-h)^m (1 - a + a s)^m = \frac{h}{1 - (1-h)(1 - a + a s)} = \frac{1 - r}{1 - r s},
$$

which is that of $`\mathrm{Geo}(r)`$. The three parts are independent, and $`\mathrm{Bin}(d, a) + \mathrm{Bin}(1, a) = \mathrm{Bin}(d + 1, a)`$. Independence across $`n`$ follows from the argument of (1) at the slot $`\sigma_{n-1}`$. ∎

**Lemma 6.4 (Proved). The all-time maximum.** Let $`Y_1, Y_2, \dots`$ be independent copies of $`Y`$, $`S_0 = 0`$, $`S_k = \sum_{j \le k} (Y_j - 1)`$ and $`M = \sup_{k \ge 0} S_k`$.

1. If $`\mathbb E[Y] < 1`$, then $`M`$ is finite. In every state $`\mathbb E[Y] - 1`$ lies between −0.4673 and −0.3509 (Computed, `out_1_walk.txt` lines 2–10).
2. Let $`\theta^* > 0`$ solve $`\mathbb E[e^{\theta (Y - 1)}] = 1`$. For $`0 < \theta \le \theta^*`$ and $`m \ge 0`$, $`\Pr[M \ge m] \le e^{-\theta m}`$.
3. Let $`\mathcal L`$ map the law of a variable $`W \ge 0`$ to the law of $`(W + Y - 1)^+`$, with $`Y`$ independent of $`W`$. Started at the law of 0, the iterates of $`\mathcal L`$ rise to the law of $`M`$. Started at a law $`\mu_0`$ that is stochastically at least the law of $`M`$, every iterate stays so. A start of that kind is $`\Pr[W \ge m] = e^{-\theta m}`$ with $`\theta \le \theta^*`$. So for every $`k`$ and $`m`$, $`\Pr[\mathcal L^k \delta_0 \ge m] \le \Pr[M \ge m] \le \Pr[\mathcal L^k \mu_0 \ge m]`$.

*Proof.* (1) By the strong law of large numbers $`S_k / k \to \mathbb E[Y] - 1 < 0`$, so $`S_k \to -\infty`$.

(2) $`\phi(\theta) = \log \mathbb E[e^{\theta(Y-1)}]`$ is convex, with $`\phi(0) = \phi(\theta^*) = 0`$, so $`\phi \le 0`$ on $`[0, \theta^*]`$. Then $`e^{\theta S_k}`$ is a nonnegative supermartingale that starts at 1. Ville's maximal inequality gives $`\Pr[\sup_k e^{\theta S_k} \ge e^{\theta m}] \le e^{-\theta m}`$.

(3) $`\mathcal L`$ keeps the stochastic order: couple $`W \le W'`$ and use one $`Y`$. Write $`M_k = \max_{0 \le j \le k} S_j`$. Then $`M_{k+1} = \max\big(0,\ (Y_1 - 1) + \max_{0 \le j \le k} (S_{j+1} - S_1)\big)`$. The inner maximum has the law of $`M_k`$ and is independent of $`Y_1`$. So the law of $`M_{k+1}`$ is $`\mathcal L`$ of the law of $`M_k`$, with $`M_0 = 0`$, and $`M_k`$ rises to $`M`$. In the same way $`M = \max\big(0,\ (Y_1 - 1) + M'\big)`$ with $`M' = \sup_{j \ge 0} (S_{j+1} - S_1)`$, which has the law of $`M`$ and is independent of $`Y_1`$. So the law of $`M`$ is a fixed point of $`\mathcal L`$. If $`\mu_0`$ is at least the law of $`M`$, then $`\mathcal L^k \mu_0`$ is at least $`\mathcal L^k`$ of the law of $`M`$, which is the law of $`M`$. By (2), $`\Pr[W \ge m] = e^{-\theta m}`$ is such a start. ∎

**Lemma 6.5 (Proved). A Markov chain over slots.** For $`t \ge 0`$ define:

- the phase $`k_t = \sigma_i - t`$ if $`\tau_i \le t < \sigma_i`$ for some $`i \ge 0`$, and $`k_t = 0`$ otherwise;
- $`X'(t) = 1 + A(t) - |\{i \ge 0 : \sigma_i \le t\}|`$, so that $`X'(t) = X(t)`$ for $`t \ge d`$;
- the flag $`F_t = [U_n \ge 0]`$ for the last count $`\sigma_n \le t`$, and $`F_t = 0`$ for $`t < d`$.

Then $`(X'(t), k_t, F_t)`$ is a Markov chain that starts at $`(1, d, 0)`$. With $`\zeta = \zeta_{t+1}`$ and $`\xi = \xi_{t+1}`$, it moves from $`(x, k, f)`$ at slot $`t`$ to:

- $`(x + \zeta,\ k - 1,\ f)`$ if $`k \ge 2`$;
- $`(x + \zeta - 1,\ 0,\ [x + \zeta - 1 \ge 0])`$ if $`k = 1`$;
- $`(x + \zeta,\ d\,\xi,\ f)`$ if $`k = 0`$.

*Proof.* At $`t = 0`$ the count of $`H_0`$ is pending at slot $`d`$. If $`k_t = k \ge 1`$, a count falls at slot $`t + k`$, and no greedy win can come before it, because $`\tau_{i+1} > \tau_i + d = \sigma_i`$. At the count $`X'`$ loses one, and the phase is 0 until the next honest win, which starts a new phase $`d`$. At a count, $`X'(\sigma_n) = 1 + A(\sigma_n) - (n + 1) = U_n`$, so the flag set there is $`[U_n \ge 0]`$, read after the coalition's mark of that slot. The marks of slot $`t + 1`$ are independent of the past (2.2), so the chain is Markov. ∎

**Lemma 6.6 (Proved). The chance from a state.** For $`T \ge d`$,

$$
\hat Q(T) = \mathbb E\big[F_T + (1 - F_T)\,\hat q(X(T), k_T)\big], \qquad \hat q(x, k) = \Pr[Z_k + M \ge 1 - x],
$$

with $`Z_k = \mathrm{Bin}(k, a)`$ for $`k \ge 1`$, $`Z_0 = Y`$, and $`Z_k`$ independent of $`M`$. In the same way $`Q(T) = \mathbb E[q_0(X(T), k_T)]`$ and $`Q_1(T) = \mathbb E[q_1(X(T), k_T)]`$, with $`q_c(x, k) = \Pr[R_k + M \ge c - x]`$, $`R_k = \mathrm{Bin}(k - 1, a)`$ for $`k \ge 1`$, and $`R_0 = \mathrm{Bin}(d, a) + \mathrm{Geo}(r)`$.

*Proof.* Let $`\sigma_{n_0}`$ be the last count at or before $`T`$. A count $`\sigma_n`$ has $`\sigma_{n+1} > T`$ exactly when $`n \ge n_0`$. So $`\hat G_T = \{F_T = 1\} \cup \{U_n \ge 0 \text{ for some } n > n_0\}`$. Let $`\sigma = \sigma_{n_0 + 1}`$. It is a stopping time, and $`U_{n_0+1} = X(T) + A(\sigma) - A(T) - 1`$.

The marks after $`T`$ are independent of the state at $`T`$ (2.2). In phase $`k \ge 1`$, $`\sigma = T + k`$, and $`A(\sigma) - A(T)`$ is $`\mathrm{Bin}(k, a)`$. In phase 0 no count is pending, so the next honest win is a greedy win. It comes $`G`$ slots after $`T`$, with $`G`$ geometric as in 6.3 (1), and $`\sigma`$ is $`d`$ slots after it. As in 6.3 (2), $`A(\sigma) - A(T)`$ then has the law of $`Y`$. After the count $`\sigma`$, the next greedy win is the first honest win after $`\sigma`$. So the process after $`\sigma`$ is a copy of the process after $`\sigma_0`$, independent of the marks up to $`\sigma`$, and by 6.3 (2) each further count changes $`U`$ by an independent copy of $`Y - 1`$. So the second event is $`\{U_{n_0+1} + M' \ge 0\}`$, where $`M'`$ has the law of $`M`$ and is independent of the state at $`T`$ and of $`A(\sigma) - A(T)`$. Given the state $`(x, k, 0)`$ at $`T`$, its chance is $`\Pr[x + Z_k - 1 + M \ge 0] = \hat q(x, k)`$.

For $`Q`$ and $`Q_1`$: $`X`$ does not fall on $`[T, \sigma - 1]`$, and on each later interval $`[\sigma_j, \sigma_{j+1} - 1]`$ it is largest at $`\sigma_{j+1} - 1`$. $`X(\sigma - 1) = X(T) + R`$, where $`R`$ counts the coalition's wins in $`(T, \sigma - 1]`$. These are $`k - 1`$ slots in phase $`k \ge 1`$. In phase 0 they are the $`G`$ slots to the next honest win and the $`d - 1`$ after it, which gives $`R_0`$ as in 6.3 (2). From $`\sigma - 1`$ on, the values $`X(\sigma_{j+1} - 1)`$ change by independent copies of $`Y - 1`$: the slots of $`[\sigma_j, \sigma_{j+1} - 1]`$ are the count's slot, the $`G`$ slots to the next honest win and the $`d - 1`$ after it. $`\sigma - 1 = \tau_{n_0+1} + d - 1`$ is a stopping time, since $`d \ge 1`$. So the chance of reaching $`c`$ from $`(x, k)`$ is $`\Pr[x + R_k + M \ge c]`$. ∎

**Lemma 6.7 (Proved). A closed-form tail.** For $`\theta > 0`$ let $`\rho \in (1 - h, 1)`$ solve $`\rho^d (\rho - 1 + h) = h e^{-\theta}`$, and put $`\lambda = (1 - a + a e^{\theta})\rho`$. If $`\lambda < 1`$, then for $`T \ge d`$

$$
\hat Q(T) \le Q(T) \le C \lambda^T, \qquad C = \frac{\rho^{-d}}{\min(1,\ e^{-\theta}/\rho)} .
$$

*Proof.* $`\rho`$ exists and is unique, because $`\rho^d(\rho - 1 + h)`$ rises on $`[1 - h, 1]`$ from 0 to $`h > h e^{-\theta}`$. Put $`e(0) = 1`$ and $`e(k) = e^{-\theta} \rho^{-k}`$ for $`1 \le k \le d`$. By 6.5,

$$
\mathbb E\big[e^{\theta X'(t+1)} e(k_{t+1}) \mid \text{the past}\big] = e^{\theta X'(t)} (1 - a + a e^{\theta}) (\Pi e)(k_t),
$$

with $`(\Pi e)(k) = e(k - 1)`$ for $`k \ge 2`$, $`(\Pi e)(1) = e^{-\theta} e(0)`$, and $`(\Pi e)(0) = h\,e(d) + (1 - h)\,e(0)`$. Substitution gives $`\Pi e = \rho e`$; the row $`k = 0`$ is the equation for $`\rho`$. So $`Z_t = e^{\theta X'(t)} e(k_t)`$ has $`\mathbb E[Z_{t+1} \mid \text{the past}] = \lambda Z_t \le Z_t`$, and $`\mathbb E[Z_T] = \lambda^T Z_0 = \lambda^T e^{\theta} e(d)`$. If $`X(t) \ge 0`$ for some $`t \ge T`$, then $`Z_t \ge e_{\min} = \min_k e(k) = \min(1, e^{-\theta}/\rho)`$, as $`e(k)`$ rises in $`k \ge 1`$. Ville's maximal inequality for the nonnegative supermartingale $`(Z_t)_{t \ge T}`$, given the past at $`T`$, gives $`Q(T) \le \mathbb E[Z_T] / e_{\min}`$, which is the claim. 6.2 gives $`\hat Q \le Q`$. ∎

`out_1_walk.txt`, lines 2–10, gives the best $`\theta`$ of each state, with $`\rho`$, $`\lambda`$ and $`C`$. $`\lambda^{3600}`$, the factor for one hour, is $`2.112 \cdot 10^{-3}`$ with no disturbance and $`9.828 \cdot 10^{-3}`$ when every honest block is 15 s late (lines 2–3).

**Lemma 6.8 (Proved). Monotonicity.** $`\hat Q(T)`$ does not fall when $`a`$ grows or when $`h`$ falls.

*Proof.* Couple the marks so that, slot by slot, there are more coalition wins or fewer honest wins. More coalition wins raise $`A`$ and leave the counts alone, so $`\hat G_T`$ grows. For the honest wins, $`N(u)`$ is the largest number of honest-won slots $`s_1 < s_2 < \dots`$ in $`(0, u]`$ with $`s_1 > d`$ and $`s_{j+1} > s_j + d`$. Indeed, for any such slots $`\tau_j \le s_j`$ by induction: $`\tau_1 \le s_1`$, and $`s_{j+1} > s_j + d \ge \tau_j + d`$ is honest-won, so $`\tau_{j+1} \le s_{j+1}`$. So more honest wins raise every $`N(u)`$ and make every $`\sigma_n = d + \min\{u : N(u) \ge n\}`$ earlier. An earlier $`\sigma_n`$ gives a smaller $`A(\sigma_n) - n`$, and makes $`\sigma_{n+1} > T`$ harder to meet. So $`\hat G_T`$ shrinks. ∎

By 2.3 and 6.8, the survival under the circuit's threshold is at most $`h\,\hat Q(T)`$, with $`\hat Q`$ evaluated at $`(1 - \delta) h`$ and $`a`$. The factor $`h`$ bounds the chance of an honest block at $`s_0`$ (2.3), and 6.8 bounds $`\hat Q`$.

## 7. Computation

**7.1 (Computed). Method.** `sv_common.py` evaluates 6.4 to 6.7.

- The law of $`M`$ is computed from below and from above by 6.4 (3), the start from above with $`\theta`$ just below $`\theta^*`$. Mass that leaves the kept support is dropped from below, and kept in a state above every level from above. The two agree to a relative $`9.5 \cdot 10^{-13}`$ or better for $`m \le 300`$ in every state (`out_1_walk.txt` lines 12–30).
- The chain of 6.5 runs slot by slot to 20 hours, with $`X`$ kept in the range printed with each state (`out_2_survival.txt`, for example line 2). From above, mass below the range is held at its bottom, and mass above it counts as the event. Holding mass at the bottom raises $`X`$ and the flag path by path, and $`\hat q`$ does not fall in $`x`$, so the result stays an upper bound. From below, mass that leaves the range counts as no event. In every row with $`T \le 6`$ h the two sides agree to 0.1 % (line 83).
- The sum of section 8 runs over $`T`$ slot by slot to 20 hours, and uses 6.7 beyond. The part beyond 20 hours is at most $`5.3 \cdot 10^{-25}`$ (`out_3_buffer.txt` lines 2–10).
- Rounding in double precision is not bounded (review 2).

**7.2 (Computed). Values.** With no disturbance, $`\hat Q`$ is $`3.8141 \cdot 10^{-4}`$ at 1 hour, $`1.0228 \cdot 10^{-9}`$ at 3 hours and $`3.5653 \cdot 10^{-15}`$ at 5 hours. When every honest block is 15 s late it is $`2.1228 \cdot 10^{-3}`$, $`1.2463 \cdot 10^{-7}`$ and $`9.4366 \cdot 10^{-12}`$. (`out_2_survival.txt` lines 3, 5, 7, 12, 14, 16.) Every state is in lines 2–82.

## 8. The buffer

**Theorem 8.1 (Proved). Review 9.3 with the proved law.** Assume a final chain as in review 9.3: a chain of which every block is in time immutable at every honest node (Assumed there). Assume also that it has blocks at slots as late as one likes, and an honest block at a slot of at most $`b`$. (The review writes $`a`$ for $`b`$.) Under A1 to A5 for the period, and for $`w \ge d`$,

$$
\Pr[\text{the final chain holds no honest block of a slot in } (b, b + w], \text{ and A5 holds}] \le h \sum_{j \ge 0} \hat Q(w + j) .
$$

*Proof.* Let $`H_0`$ be the last honest block of the final chain with a slot of at most $`b`$, and $`s_0 = b - j`$ its slot. We show that some honest node holds, in its state at some slot $`t \ge b + w`$, a $`c_{loc}`$ that is a pure branch from $`H_0`$. That is $`E_{w+j}(H_0)`$, since $`s_0 + w + j = b + w`$.

Case 1: the final chain has an honest block after $`H_0`$. Let $`H_1`$ be the first, and $`u`$ its slot. Then $`u > b + w`$, by the choice of $`H_0`$ and the hypothesis, and every block between $`H_0`$ and $`H_1`$ is the coalition's (review 9.3 (1), with A4). The leader of $`H_1`$ built it on its $`c_{loc}`$ in its state at slot $`u - 1 \ge b + w`$. That $`c_{loc}`$ is the parent of $`H_1`$, whose chain is a pure branch from $`H_0`$.

Case 2: it has none. Take a block $`Z`$ of the final chain with a slot of at least $`b + w`$. Some honest node makes $`Z`$ immutable. Then $`Z`$ is on that node's $`c_{loc}`$ (review 3.7) in its state at some slot $`t_Z \ge sl_Z`$ (2.5). Call that $`c_{loc}`$ $`C`$. If $`C`$ has no honest block after $`H_0`$, it is a pure branch from $`H_0`$. Otherwise let $`B`$ be the first honest block of $`C`$ after $`H_0`$. $`B`$ is not an ancestor of $`Z`$, because the final chain has no honest block after $`H_0`$. So $`B`$ comes after $`Z`$ on $`C`$, and $`sl_B > sl_Z \ge b + w`$. The leader of $`B`$ built it on the chain of its parent, in its state at slot $`sl_B - 1 \ge b + w`$, and that chain is a pure branch from $`H_0`$.

So the event lies in the union over $`j \ge 0`$ of the events that $`H_0`$ has slot $`b - j`$ and $`E_{w+j}(H_0)`$ holds. On A5, Theorem 6.1 bounds each of them by $`h\,\hat Q(w + j)`$. ∎

$`w_B`$ is the least $`w`$ at which the right-hand side is at most $`10^{-9}`$ (review 9.4).

**8.2 (Computed). The values.** `out_3_buffer.txt`, lines 2–10, gives $`w_B`$ with $`\hat Q`$, $`w_B`$ from the study's law as the review's `out_08_buffer.txt` gives it, and $`w_B`$ with $`Q`$ of 6.2. Lines 17–25 give $`w_B`$ under the circuit's threshold: the bound $`h \sum_j \hat Q(w + j)`$ with $`\hat Q`$ at the circuit's lowest honest chance $`(1 - \delta) h`$ (2.3, 6.8).

| State | Study's law | Proved law $`\hat Q`$ | Change | Circuit's threshold | Without the tie argument, $`Q`$ |
| --- | --- | --- | --- | --- | --- |
| no disturbance, 10 s | 12,242 (3.40 h) | 12,295 (3.42 h) | +53 | 12,313 | 12,468 |
| every honest block 15 s late | 16,579 (4.61 h) | 16,644 (4.62 h) | +65 | 16,670 | 16,860 |
| a tenth offline, after the inference corrects, 10 s | 17,215 (4.78 h) | 17,268 (4.80 h) | +53 | 17,297 | 17,477 |
| a deflated inference, 10 s | 11,126 (3.09 h) | 11,171 (3.10 h) | +45 | 11,188 | 11,317 |
| 15 s and a tenth offline, after (base) | 24,645 (6.85 h) | 24,713 (6.86 h) | +68 | 24,758 | 24,980 |
| 15 s and a deflated inference (base) | 18,081 (5.02 h) | 18,142 (5.04 h) | +61 | 18,173 | 18,345 |
| a tenth offline and a deflated inference, 10 s (base) | 16,452 (4.57 h) | 16,497 (4.58 h) | +45 | 16,528 | 16,676 |
| a tenth offline before the inference corrects, 10 s | 17,654 (4.90 h) | 17,709 (4.92 h) | +55 | 17,739 | 17,927 |
| 15 s and a tenth offline before it corrects (base) | 24,471 (6.80 h) | 24,540 (6.82 h) | +69 | 24,584 | 24,812 |

All values are slots. The first column is from the review's `out_08_buffer.txt` (its lines 14 to 124, named in each line of the output).

- The proved law moves every buffer by 45 to 69 slots, that is 45 to 69 seconds.
- The circuit's threshold adds 17 to 45 slots more (lines 17–25).
- The last column shows what the tie argument of 5.2 (2) is worth.
- The review's figure at two hours (its finding 4) becomes $`7.773 \cdot 10^{-6}`$ in place of $`7.081 \cdot 10^{-6}`$ with no disturbance, and $`2.677 \cdot 10^{-4}`$ in place of $`2.452 \cdot 10^{-4}`$ at 15 s (lines 13–14). Two hours are still not enough at $`10^{-9}`$.

## 9. The study's law

**9.1 (Cited; the reading is Proved). What `branch_survival` computes.** The function is `formation.py` 390–405. The review calls it with the coefficient $`f' = 1 - (1-f)^{x_h + x_a}`$ and the coalition's share $`\alpha = x_a / (x_h + x_a)`$ of the stake that wins (review `s08_buffer.py` 49–66). `out_1_walk.txt`, lines 33–41, prints $`f'`$ and $`\alpha`$ for each state.

- `_rates` (`nonce.py` 150–156, with `occupancy` of `recovery.py` 28–30) returns $`1 - (1 - f')^{\alpha}`$ and $`1 - (1 - f')^{1 - \alpha}`$, which are $`a`$ and $`h`$ of 2.2, and the dead time $`d`$.
- `walk` (`grinding.py` 76–93) returns `step`, the law of $`\mathrm{Bin}(d + 1, a) + \mathrm{Geo}(r)`$ cut where $`r^n`$ falls below $`10^{-40}`$. That is the law of $`Y`$ of 6.3 (2). It agrees with this folder's law of $`Y`$ to $`1.6 \cdot 10^{-15}`$ (`out_1_walk.txt` lines 33–41).
- `_ladder(step, 200)` (`grinding.py` 96–120) gives, by height, the first height above 0 that the walk with steps $`Y - 1`$ reaches from 0. It pushes the walk's remaining chance over the levels −200 to 0 until less than $`10^{-40}`$ is left, and drops paths that fall below −200.
- `_renewal` (`grinding.py` 123–134) gives $`\Pr[M = m] = (1 - \sum_j \ell_j)\,u_m`$, where $`\ell_j`$ are the ladder heights' chances and $`u_m`$ is the chance that some sum of ladder heights equals $`m`$: $`u_0 = 1`$, $`u_m = \sum_j \ell_j u_{m-j}`$. This is the all-time maximum as a geometric number of independent ladder heights. It agrees with 6.4 to $`2.0 \cdot 10^{-8}`$ (`out_1_walk.txt` lines 33–41).
- `after` (line 397) is the law of $`Y + M`$, and `up` (line 399) that of $`\mathrm{Bin}(T, a) + Y + M`$.
- `blocks_pmf(T)` (`fork_bound.py` 76–85) sets $`\Pr[N_T \ge n] = \Pr[\mathrm{NB}(n, h) \le T - n(d + 1)]`$, where $`\mathrm{NB}(n, h)`$ counts the failures before the $`n`$-th success. By 6.3 (1), $`\tau_n = n(d + 1) + \sum_{i \le n} (G_i - 1)`$, and the sum is $`\mathrm{NB}(n, h)`$. So $`N_T`$ has the law of $`N(T)`$ of 4.1.
- The function returns $`\sum_n \Pr[N_T = n] \Pr[\mathrm{up} \ge n + 1]`$ (lines 400–405).

So

$$
\texttt{branch\_survival}(T) = \Pr[\mathrm{Bin}(T, a) + Y + M \ge N(T) + 1],
$$

with the four terms independent. A recomputation from this formula with this folder's laws of $`Y`$ and $`M`$ agrees to $`1.2 \cdot 10^{-12}`$ (Computed, `out_2_survival.txt` lines 85–95).

**9.2 (Proved). Where it departs from Theorem 6.1.** $`\mathrm{Bin}(T, a)`$ has the law of $`A(T)`$ and is independent of the honest marks. $`N(T) - N(T - d)`$ is 1 in a phase $`k \ge 1`$ and 0 in phase 0 (6.5). So `branch_survival`(T) is the mean, over the state at $`T`$, of $`\Pr[X(T) - [k_T \ge 1] + Y + M \ge 1]`$ given that state. Set it against 6.6, case by case.

1. Phase 0 with $`F_T = 0`$. The study's chance is $`\Pr[X(T) + Y + M \ge 1] = \hat q(X(T), 0)`$. The two agree.
2. A phase $`k \ge 1`$. An isolated honest win of a slot $`\tau`$ in $`(T - d, T]`$ is pending. Every honest node must hold its block only from slot $`\tau + d > T`$ on (A3). The study subtracts that block at $`T`$, and then asks for a whole further gap: $`\Pr[X(T) - 1 + Y + M \ge 1]`$. Theorem 6.1 subtracts it at its count: $`\Pr[X(T) + \mathrm{Bin}(k, a) + M \ge 1]`$. Neither of $`Y - 1`$ and $`\mathrm{Bin}(k, a)`$ is stochastically larger than the other: $`\Pr[Y - 1 \ge 0] < 1 = \Pr[\mathrm{Bin}(k, a) \ge 0]`$, while for $`j > k`$, $`\Pr[\mathrm{Bin}(k, a) \ge j] = 0 < \Pr[Y - 1 \ge j]`$. So the formulas do not settle the sign of this case.
3. $`F_T = 1`$. At the last count the coalition had won as many slots as the count. An honest node that took its branch then keeps it on the tie (5.2 (2), 3.1), and the event holds. The study does not count this.

So the study counts an honest block when it is made, not when every honest node must hold it, and it does not count a branch kept on a tie. 9.4 measures the net effect.

**Proposition 9.3 (Proved). The law is attained.** Take the following instance of the model.

- The honest stake that builds is held by $`n`$ honest nodes, each with a share $`x_h / n`$ of $`D`$. One more honest node holds no stake. Call it the *target*.
- Before slot 0, every honest node holds the same chain $`C_0`$, with its $`B_\text{imm}`$ on it. The tip $`P`$ of $`C_0`$ has height $`\ell_0 - 1`$ and a slot of at most $`-d - 1`$. No honest block has a slot in $`[-d, -1]`$. $`H_0`$ is an honest block of slot 0 on $`P`$.
- Every honest block reaches every other honest node, the target included, with its chain, exactly $`d`$ slots after its slot. This meets A3.
- Strategy $`S^*`$. The coalition keeps one private chain that starts at $`H_0`$ and holds one block for each slot it wins after slot 0. At each count $`\sigma_n`$ with $`n \ge 1`$ and $`U_n \ge 0`$, it delivers that chain to the target. It delivers nothing else. Within a slot it delivers its chain first, then the honest blocks in the order of their slots, $`H_0`$ first among those of slot 0.

Let $`d \le T < T_{\max} < K`$, $`p_n = 1 - (1 - f)^{x_h / n}`$ and $`c_n = (T_{\max} + 1)\, d\, n\, p_n^2 / h^2`$. Then

$$
\Pr[\text{some honest node holds a pure branch from } H_0 \text{ at some slot in } [T, T_{\max}]] \ge (1 - c_n)\big(\hat Q(T) - \hat Q(T_{\max})\big).
$$

As $`n`$ grows, $`c_n \to 0`$. So no law below $`\hat Q(T) - \hat Q(K - 1)`$ bounds the event of review 9.3 in every instance of the model.

*Proof.* Let $`D_n`$ be the event that some honest node wins two slots $`u' < u \le u' + d`$ of $`[0, T_{\max}]`$.

Step 1: the honest blocks. Let $`m(v)`$ be the largest height among the blocks of $`C_0`$ and the honest blocks of slots from 0 to $`v`$. So $`m(v) = \ell_0 - 1`$ for $`v < 0`$. We show that off $`D_n`$, $`m(v) = \ell_0 + N(v)`$ for $`0 \le v \le T_{\max}`$. A leader of slot $`u \ge 1`$ builds on its $`c_{loc}`$ in its state at slot $`u - 1`$. That state holds $`C_0`$ and the honest blocks of slots of at most $`u - 1 - d`$. It holds no other honest block: off $`D_n`$ its own earlier blocks have slots of at most $`u - 1 - d`$, and the later blocks of other nodes have not arrived. It holds no block of the coalition, which delivers only to the target. Its $`c_{loc}`$ is a highest block of that state, by 3.1 and because $`c_{loc}`$ is in the state. So the new block has height $`1 + m(u - 1 - d)`$. For $`u \le d`$ that is $`\ell_0`$, so $`m(v) = \ell_0 = \ell_0 + N(v)`$ for $`0 \le v \le d`$. For $`v > d`$, let $`u^*`$ be the last honest win in $`(d, v]`$. If there is none, $`m(v) = \ell_0 = \ell_0 + N(v)`$. Otherwise, as $`m`$ does not fall, $`m(v) = 1 + m(u^* - d - 1) = 1 + \ell_0 + N(u^* - d - 1)`$ by induction on $`v`$. Exactly one greedy win lies in $`[u^* - d, u^*]`$. There is at most one, because greedy wins are more than $`d`$ apart. There is at least one: $`u^*`$ itself, or else the greedy win that rules it out, which lies in $`[u^* - d, u^* - 1]`$. So $`N(u^*) = N(u^* - d - 1) + 1`$, and $`m(v) = \ell_0 + N(u^*) = \ell_0 + N(v)`$.

Step 2: the target. Off $`D_n`$, the target's state at slot $`t`$ holds $`C_0`$, the honest blocks of slots of at most $`t - d`$, and what $`S^*`$ has delivered. Let $`n \ge 1`$ with $`U_n \ge 0`$. When $`S^*`$ delivers at slot $`\sigma_n`$, the target's highest honest block has height $`m(\tau_n - 1) = \ell_0 + n - 1`$. The private chain has height $`\ell_0 + A(\sigma_n) \ge \ell_0 + n`$, and its blocks have slots of at most $`\sigma_n`$. Once its tip is added, the target's $`c_{loc}`$ is a highest block (3.1 (2)). The tip is then the only block of that height, so $`c_{loc}`$ is the tip. The honest blocks delivered from then until slot $`\sigma_{n+1} - 1`$, those of slot $`\tau_n`$ included, have slots in $`[\tau_n, \tau_{n+1})`$, and so heights of at most $`m(\tau_{n+1} - 1) = \ell_0 + n`$. None is higher than the tip, so $`c_{loc}`$ stays the tip (3.1 (1)) in every state from $`\sigma_n`$ to $`\sigma_{n+1} - 1`$. For $`n = 0`$: $`H_0`$ reaches the target at slot $`d`$, before every other block of height $`\ell_0`$. The target then holds $`H_0`$, a pure branch, until a higher block arrives, which is not before $`\sigma_1`$.

Step 3: the chance. Let $`\hat G'`$ be the event that some $`n`$ has $`U_n \ge 0`$, $`\sigma_{n+1} > T`$ and $`\sigma_n \le T_{\max}`$. Off $`D_n`$, on $`\hat G'`$, step 2 puts a pure branch at the target at slot $`\max(T, \sigma_n)`$, which lies in $`[T, T_{\max}]`$. $`\hat G_T`$ minus $`\hat G'`$ lies in $`\hat G_{T_{\max}}`$, because $`U_n \ge 0`$ and $`\sigma_n > T_{\max}`$ give $`\sigma_{n+1} > T_{\max}`$. So $`\Pr[\hat G'] \ge \hat Q(T) - \hat Q(T_{\max})`$. $`\hat G'`$ is fixed by the slots that honest stake wins and by the coalition's marks. Given these, which honest node wins each such slot is independent of the coalition's marks. For one pair of slots, the chance that one node wins both, given that honest stake wins both, is at most $`n p_n^2 / h^2`$. There are at most $`(T_{\max} + 1) d`$ pairs of slots of $`[0, T_{\max}]`$ at most $`d`$ apart. So $`\Pr[D_n \mid \text{those marks}] \le c_n`$, and the chance of $`\hat G'`$ off $`D_n`$ is at least $`(1 - c_n) \Pr[\hat G']`$.

Last, every honest node's $`B_\text{imm}`$ stays on $`C_0`$ up to slot $`T_{\max}`$. `commit` moves it only to a block at least $`K`$ slots behind the tip (protocol 512), and $`T_{\max} < K`$. Every block of the instance descends from $`P`$. So A5 holds, and every delivery is accepted. ∎

**9.4 (Computed). By how much.**

- $`\hat Q(T)`$, from below, exceeds the study's law by a factor of 1.0623 to 1.1018 at the whole hours 1 to 6 in every state (`out_2_survival.txt` line 83). $`Q_1`$, the chance of a strict lead, exceeds it by 1.0114 to 1.0266, so the study's law lies below even that. $`Q`$ exceeds it by 1.3498 to 1.4889. Taken alone, the theorem's treatment of a pending block raises the study's law by a factor of 1.0153 to 1.0318, and the credit for a branch kept on a tie raises it by 1.0543 to 1.0946 (lines 101–111). Part 4 computes them from the state at $`T`$ as $`\mathbb E[\hat q(X(T), k_T)]`$ and $`\mathbb E[F_T + (1 - F_T)\,q_s(X(T), k_T)]`$, where $`q_s(x, k) = \Pr[x - [k \ge 1] + Y + M \ge 1]`$ is the study's chance of 9.2. From the same state, $`\mathbb E[q_s(X(T), k_T)]`$ agrees with `branch_survival` to $`6.8 \cdot 10^{-7}`$ at 1 to 4 hours (line 111).
- In the instance of 9.3 with $`n = 10^9`$ and $`T_{\max} = 35{,}000`$, $`c_n`$ lies between $`3.58 \cdot 10^{-4}`$ and $`5.43 \cdot 10^{-4}`$, and $`\hat Q(T_{\max})`$ is at most $`4.0 \cdot 10^{-15}`$. The adversary's chance then exceeds the study's law by a factor of 1.0624 to 1.0981 at 2, 3 and 4 hours in every state (`out_3_buffer.txt` lines 27–36). So the study's law is not an upper bound on the event of review 9.3. The attained chance exceeds it by 6 to 10 %.
- Below about $`10^{-17}`$, `branch_survival` also loses digits, because `blocks_pmf` takes differences of distribution functions near 1. With the law of $`N(T)`$ taken from survival functions, the study's own formula gives $`6.2850 \cdot 10^{-18}`$, $`2.4349 \cdot 10^{-23}`$ and $`9.7297 \cdot 10^{-29}`$ in place of $`6.2832 \cdot 10^{-18}`$, $`2.4053 \cdot 10^{-23}`$ and $`8.6293 \cdot 10^{-29}`$ at 6, 8 and 10 hours with no disturbance (`out_2_survival.txt` line 98). Values this small do not move $`w_B`$. They explain the ratios at 8 and 10 hours in lines 9–10 and 36–37.

## 10. Checks

**10.1 (Computed). The recursion against sampled lotteries.** `s5_lottery_mc.py` samples the lottery of 2.2 at inflated rates, with $`f`$ of 0.2 and 0.15 and $`d`$ of 3 and 5, in 400,000 paths each. It reads the events of $`\hat Q`$, $`Q_1`$ and $`Q`$ from each path. Every frequency lies within 1.99 standard errors of the recursion (`out_5_lottery_mc.txt` lines 1–18).

**10.2 (Computed). The Online rule as printed.** `s6_protocol_sim.py` runs honest nodes with `on_block` and `online_fork_choice` as printed, against random coalitions, with random delivery within $`d`$: $`f`$ = 0.25, $`d`$ = 3, four honest nodes with stake and one without, 150 slots a run. In nine configurations of 1,500 runs, each with 1,110,000 checks of a node at a slot, no check of 4.2, 5.2 (1) or 5.2 (2) failed. A pure branch with a lead of exactly 0 was held 18,022 to 28,136 times in each configuration, so the case of 5.2 (2) occurs (`out_6_protocol_sim.txt` lines 3–11). In the instance of 9.3, with honest wins by fresh nodes, the frequency of the event is within 2.13 standard errors of $`\hat Q`$ at each of the nine values of $`T`$ where $`\hat Q < 1`$ (lines 14–25). The seed is fixed and the parents are drawn in the order of block IDs, so every run prints the same.

The checks support the proofs. They do not replace them.

## 11. Consequences

**11.1 (Computed). The epochs that suffice.** $`E_\text{suf} = \max(P, G^* + w_B) + \max(G^*, 2K - 1)`$, or $`G^* + w_B + \max(G^*, 2K - 1)`$ with the window shortened to phases 1 and 2 (review 10.2). Phase 3 is $`2K - 1`$ slots in every case, the condition of the argument of GENESIS 7.1 (review 10.1). $`G^*`$ is the review's value; recomputed with the review's code it is the same in every case. $`w_B`$ is the largest over the states the case requires. (`out_4_epoch.txt` lines 2–5 and 9–20.)

| Case | $`G^*`$ | $`w_B`$: study's law, proved law | Window shortened: study's law, proved law | Window kept: study's law, proved law |
| --- | --- | --- | --- | --- |
| latest #533, a tenth offline after the inference corrects | 46,910 | 17,215, 17,268 | 136,124 (37.81 h), 136,177 (37.83 h) | 460,799 (128.00 h), the same |
| latest #533, a tenth offline before it corrects | 47,483 | 17,654, 17,709 | 137,136 (38.09 h), 137,191 (38.11 h) | 460,799 (128.00 h), the same |
| base, after | 86,187 | 24,645, 24,713 | 240,431 (66.79 h), 240,499 (66.81 h) | 518,399 (144.00 h), the same |
| base, before | 91,167 | 24,471, 24,540 | 245,237 (68.12 h), 245,306 (68.14 h) | 518,399 (144.00 h), the same |

- With the window kept, $`P`$ = 388,800 slots exceeds $`G^* + w_B`$, so $`w_B`$ does not enter (line 7).
- With the circuit's threshold (2.3, 6.8), the shortened epochs are 136,206, 137,221, 240,544 and 245,350 slots: 37.84, 38.12, 66.82 and 68.15 hours (lines 10, 13, 16 and 19).
- The lower bounds of review 10.3 do not use $`w_B`$ and do not change.

**11.2 (Computed). Other figures of the review that read $`w_B`$.** For the latest #533 (`out_4_epoch.txt` lines 23–26):

- the epoch with all of the inferred stake building at 15 s (review 10.3, second row): 125,379 slots (34.83 h) in place of 125,314 (34.81 h) with the window shortened, and 128.00 h unchanged with it kept;
- the wait from a late snapshot to its first use (review 11.3): 86.83 h in place of 86.81 h with all of the inferred stake building at 15 s, and over the states of the $`K`$ row 89.83 h in place of 89.81 h, or 90.11 h in place of 90.09 h before the inference corrects.

**11.3 (Proved, 8.1; Computed, 8.2, 11.1 and 11.2). What this changes in the review.** The review's statements that rest on the survival law (its sections 0, 5.9, 9.4, 10.2, 10.3, 11, 12, 14 and 15) can rest on Theorem 8.1 instead, under A5 and the final chain. Their numbers change as in 8.2, 11.1 and 11.2. The last two rows of review 10.4 also read $`w_B`$; their costs are not recomputed here.

## 12. What is not proved here

- A5. The bounds hold on the event that every honest block, and every block of its chain, that reaches an honest node descends from that node's $`B_\text{imm}`$ or is $`B_\text{imm}`$. That this fails with a chance of at most $`\varepsilon`$ per block is the guarantee that sizes $`K`$. It is cited, not derived (review 14).
- The final chain of review 9.3, and that it has blocks at slots as late as one likes (8.1).
- A1. The ticket hash is read as a random oracle, and the nonce as fixed and unbiased. A biased nonce changes the law of the marks.
- A2. A period that crosses the start of an epoch changes $`D`$, $`\eta`$, $`h`$ and $`a`$.
- A3 and A4, the network and the honest nodes. The proofs hold in the model. Whether a real network stays within it is not shown.
- The mapping of the states of the $`K`$ row to shares and delays (review 5.9).
- Rounding in double precision.
- That the study's law lies below $`\hat Q`$ at every $`T`$. It is computed at whole hours only (9.4).
- Proposition 9.3 needs many honest nodes. With few, a node can win two slots within $`d`$ slots and build on its own block, and the worst case may lie below $`\hat Q`$. That case is not examined.
- 2.4 for Proposition 9.3. $`S^*`$ delivers its chain to the target alone, and no honest node passes it on. If honest nodes pass on the blocks they accept, $`S^*`$ must instead deliver the prefix of its chain with $`n`$ blocks after $`H_0`$, to every honest node and first in slot $`\sigma_n`$. That variant is not written out here.

## 13. Files

All files are in this folder, `slot-finality/epoch/proofs/survival/`. Each script states its use in its first lines. The scripts need `numpy` and `scipy`. `s1`, `s2` and `s3` also import the finality study's package, read only, and `s4` imports the review's `common.py` and reads its `out_14_bracket.txt`, both read only. Caches go to `.cache` in this folder.

| File | Content | Statements |
| --- | --- | --- |
| `sv_common.py` | the states; the laws of $`Y`$, $`R_0`$ and $`M`$; the chain of 6.5; $`\hat q`$, $`q_0`$ and $`q_1`$; the tail of 6.7; the least $`w`$ | 6.3 to 6.7, 7.1 |
| `s1_walk.py`, `out_1_walk.txt` | per state: $`h`$, $`a`$, $`r`$, the drift, $`\theta^*`$ and the constants of 6.7; the law of $`M`$ from both sides; the study's helpers against them | 2.6, 6.4, 6.7, 9.1 |
| `s2_survival.py`, `out_2_survival.txt` | $`\hat Q`$, $`Q_1`$, $`Q`$ and the study's law by $`T`$; the study's formula recomputed; its digits below $`10^{-17}`$; each departure of 9.2 alone | 7.1, 7.2, 9.1, 9.4 |
| `s3_buffer.py`, `out_3_buffer.txt` | $`w_B`$ per state with each law; the bound at two hours; the circuit's threshold; the instance of 9.3 | 8.2, 9.4 |
| `s4_epoch.py`, `out_4_epoch.txt` | $`G^*`$ and the epochs that suffice, with the study's law and with the proved law; other figures | 11.1, 11.2 |
| `s5_lottery_mc.py`, `out_5_lottery_mc.txt` | the recursion against sampled lotteries | 10.1 |
| `s6_protocol_sim.py`, `out_6_protocol_sim.txt` | the Online rule as printed: checks of 4.2 and 5.2, and the instance of 9.3 | 10.2 |

Run `s1` to `s3` first, then `s4`, which reads `out_3_buffer.txt`, then `s5` and `s6`.
