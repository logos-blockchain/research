# The length of the epoch under a finality window of 10 hours

Date of this review: 2026-11-18.

This review states what bounds the Cryptarchia epoch from below when the finality window is 10 hours, as logos-lips pull request #533 sets it, with proofs. It also states what each shorter schedule costs.

## 0. Result in brief

- The latest #533 sets $`K`$ to 36,000 slots and keeps the epoch at 648,000 slots. (Cited, 1.4.)
- A phase that waits for a value cannot be shorter than $`K`$. At exactly $`K`$ the value is final in time only if two given slots hold blocks. (Proved, 4.6.)
- For a chance of $`10^{-9}`$ the least such phase lies between $`K + 611`$ and $`K + 736`$ slots when all of the inferred stake builds. That is 10.17 to 10.20 hours at $`K`$ = 10 hours. In every state that the $`K`$ row names, a phase of 13.03 hours keeps its rule. When only blocks of the chain count, no phase shorter than 13.03 hours does. When every win is counted, no phase shorter than 10.48 hours does. (Proved, 5.4 and 5.5. Computed, 5.8 and 5.9. Assumed, 5.9.)
- The only argument here that the Bootstrap rule keeps a joining node on the honest chain is that of GENESIS. It needs phase 3 to last at least $`2K - 1`$ slots: 20.00 hours at $`K`$ = 10 hours, where 13.03 hours suffice for the value of phase 3. Whether a shorter phase 3 breaks the Bootstrap rule is not shown. (Cited, GENESIS 7.1 and 7.3. Computed, 10.3.)
- An epoch of 37.83 hours keeps every rule of the epoch schedule of the latest #533 with today's nonce, and gives phase 3 those 20.00 hours. One of 128.00 hours does if the observation window of the stake inference keeps its 108 hours. (Proved, 10.2. Computed, 10.3. Assumed, 5.9, 9.4 and A10. Cited, GENESIS 7.1.)
- The buffer term of 4.80 hours rests on a survival law that SURVIVAL proves. The law bounds the chance that an honest node holds a branch of the coalition's blocks $`T`$ slots after the branch left the honest blocks, and a recursion over slots computes it. The theorem assumes a random-oracle lottery with an unbiased nonce, delivery within the delay, honest nodes that run the Online rule, and that every honest block reaches an honest node as a descendant of that node's latest immutable block, which is the guarantee that sizes $`K`$. (Proved, 9.4 and SURVIVAL 6.1. Assumed, 9.4.)
- The finality study's survival law is not an upper bound: the proved law exceeds it by 6 to 10 %. So every buffer is 45 to 69 slots longer than with the study's law. (Computed, 9.4.)
- No epoch shorter than 21.21 hours keeps these rules, or than 26.30 hours when only blocks of the chain count. With the window kept the bound is 118.48 hours, or 121.03 hours when only blocks of the chain count. These bounds rest neither on the survival law nor on the condition on phase 3. (Proved, 10.2. Computed, 10.3. Assumed, 5.9 and A10.) So the least epoch lies between 21.21 and 37.83 hours, and between 118.48 and 128.00 hours with the window kept. (Proved, 10.2.)
- These values take the state with a tenth of the honest stake offline after the inference has corrected to the stake that is online. The text of the $`K`$ row supports that reading. Taken before the inference corrects, the epochs that suffice are 38.11 hours, and 128.00 hours with the window kept. (Computed, 10.3. Assumed, 5.9.)
- The present 180 hours are therefore not needed for these rules: 37.83 hours suffice. (Proved, 10.2. Computed, 10.3. Assumed, 5.9, 9.4 and A10.) The rest buys margins. The values of each phase are final in time while 10.2 % and 13.8 % of the inferred stake builds. The inferred stake has a noise of 0.87 %. 5.6 % of targets meet two nonces. A coalition of 30 % gains 0.70 % in blocks by choosing among nonces. Every shortening spends part of these. (Computed, 10.4 and 10.6. Cited, RFC-532 105. Assumed, 10.6.)
- The conclusion of Theorem 2 of Ouroboros Genesis does not follow from the paper at the specification's delays. GENESIS argues it directly for the Bootstrap rule. Against a coalition of 30 %, a fork with no honest block in the density window wins the comparison with a chance of at most $`2.1\cdot10^{-13}`$ per divergence slot at 10 s and $`2.6\cdot10^{-10}`$ at 15 s, so these long-range forks meet $`10^{-9}`$. (Proved, 8.6 and GENESIS 6.2. Computed, 8.6. Assumed, 8.6.)
- Against every fork the bound found is $`1.35\cdot10^{-7}`$ at 10 s and $`4.3\cdot10^{-5}`$ at 15 s, and does not meet $`10^{-9}`$. A window of 21,336 slots at 10 s or 33,729 slots at 15 s would meet it, and one of 33,181 or 51,560 slots over a year of history. At $`K`$ = 36,000 and 15 s no window meets it by these bounds. The bound rests on a reading of the settlement analysis of Gaži, Ren and Russell and on the finality study's settlement bound. An estimate of one real attack lies 1,500 to 2,900 times lower. (Proved, 8.6 and GENESIS 6.3. Computed, 8.6. Assumed, 8.6. Cited, 8.6.)
- Posterior corruption is not prevented, because leadership keys do not evolve: keys of a further 4.8 % of the stake, bought later, lift the long-range bound above $`10^{-9}`$ at 10 s. (Cited, 8.6. Computed, 8.6.)

## 1. Setting

### 1.1 Texts

All line numbers are those of a file as `git show <branch>:<path>` prints it.

| Short name | Path under `docs/blockchain/raw/` | Branch and commit |
| --- | --- | --- |
| protocol | `cryptarchia-v1-protocol.md` | `Bedrock-RFC-Slot-Finality-10h`, `7f3cf149` (the latest #533) |
| inference | `cryptarchia-total-stake-inference.md` | same |
| fork choice | `fork-choice.md` | same |
| bootstrap | `cryptarchia-v1-bootstr-sync.md` | same |
| leadership | `cryptarchia-proof-of-leadership.md` | same |
| RFC-533 | `rfc/RFC-533-cryptarchia-shorten-the-finality-window-to-10-hours.md` | same |
| RFC-532 | `rfc/RFC-532-cryptarchia-count-finality-in-slots.md` | same |
| base | the same paths | `Bedrock-RFC-Slot-Finality`, `ded1d4c6` (the base of #533, 18 hours) |

The two branches differ in three files only: protocol, inference and RFC-533. (Cited: the diff of the two branches.)

The paper is "Ouroboros Genesis: Composable Proof-of-Stake Blockchains with Dynamic Availability", full version of February 22, 2019 (IACR ePrint 2018/378). The settlement analysis of Gaži, Ren and Russell is "Practical Settlement Bounds for Longest-Chain Consensus" (IACR ePrint 2022/1571).

The finality study is the package `finality_sim` and its stored runs under `tools/simulators/finality/` of the research repository. Section 13 gives the paths.

Two proofs in this folder extend the review. SURVIVAL is `proofs/survival/SURVIVAL.md`, a proof of the survival law behind the buffer (section 9). GENESIS is `proofs/genesis/GENESIS.md`, an argument for the conclusion of Theorem 2 of Ouroboros Genesis under the specification's rules and parameters (section 8). They are cited by their own section numbers, for example SURVIVAL 6.1.

### 1.2 Symbols

The symbols are the specification's. $`U`$, $`E`$, $`sl_\text{cut}`$, $`sl_\text{use}`$, $`G`$, $`x`$, $`d`$ and $`P`$ are shorthands of this review.

| Symbol | Meaning | Latest #533 | Base | Place |
| --- | --- | --- | --- | --- |
| $`f`$ | slot activation coefficient | 1/30 | same | protocol 102 |
| $`k`$ | security parameter | 2,160 blocks | same | protocol 103 |
| $`U`$ | $`\lfloor k/f \rfloor`$, the unit of the Epoch Schedule | 64,800 slots, 18 h | same | protocol 153–159 |
| $`K`$ | finality window | 36,000 slots, 10 h | 64,800 slots, 18 h | protocol 104 |
| $`\phi`$ | finality floor | 689 occupied slots | 1,291 | protocol 105, 553 |
| $`T_M`$ | message traversal time of Blend | 15 slots | same | `blend-protocol.md` 481 |
| $`\Delta`$, $`\alpha_\text{max}`$, $`\varepsilon`$ | targets of the $`K`$ row | 10 slots, 3/10, $`10^{-9}`$ | same | protocol 104, 531 |
| phases | Stake Distribution Snapshot, Buffer, Lottery Constants Finalization | $`3U`$, $`3U`$, $`4U`$: 54 h, 54 h, 72 h | same lengths, written $`3K`$, $`3K`$, $`4K`$ | protocol 153–155 |
| $`E`$ | epoch length, $`10U`$ | 648,000 slots, 180 h | same | protocol 159 |
| $`sl_\text{cut}`$ | the cut-off: slot $`6U`$ of an epoch, where $`\eta`$ and $`D`$ are read | 388,800 slots, 108 h into the epoch | same | protocol 155, 229, 237 |
| $`sl_\text{use}`$ | the first slot of the next epoch, where they are first used | | | protocol 209–249 |
| $`G`$ | the gap $`sl_\text{use} - sl_\text{cut}`$ | $`4U`$ = 259,200 slots, 72 h | same | protocol 155 |
| $`P`$ | `PERIOD`, the observation window of the inference | $`6U`$ = 388,800 slots, 108 h | same, written $`6K`$ | inference 55 |
| `beta` | learning rate of the inference | 1.0 | same | inference 54 |
| $`s_{gen}`$ | density window, $`\lfloor k/(4f) \rfloor`$ | 16,200 slots, 4.5 h | same | fork choice 80 |
| $`W \cdot f^{-1}`$ | uncle reference window | 360 slots | same | protocol 109 |
| $`T_\text{offline}`$ | offline grace period | 20 minutes | same | bootstrap 110 |
| $`D`$, $`\eta`$, $`\mathbb{C}_\text{LEAD}`$ | inferred total stake, epoch nonce, eligible notes | | | protocol 163–169 |
| $`B_\text{imm}`$, $`c_{loc}`$ | latest immutable block, tip of the local chain | | | protocol 118–119 |

Places are lines of the latest #533. On the base, the protocol's lines from 40 on are one lower, and so are the inference's lines from 31 on.

The derived values are recomputed in `out_01_setting.txt`, lines 2 to 8. (Computed.)

### 1.3 Conventions

- A slot lasts one second (Cited: protocol 106). So 3,600 slots are one hour.
- Hours are rounded from counts of slots. A bound given in hours is a bound on the count of slots it is rounded from.
- A coalition's share is a share of the total active stake, counted while all of the honest stake is online. This is the convention of both RFCs (Cited: RFC-533 31, RFC-532 41). Every share of a coalition in this review is meant so.
- The building share $`x`$ is a different quantity. It is the stake that builds blocks, as a share of the inferred total stake $`D`$. The specification's Finality Floor takes $`x = 1`$ (Cited: protocol 526).
- $`\mathrm{Bin}(m, p)`$ is a binomial variable with $`m`$ trials of chance $`p`$.

### 1.4 The state of the specification

Each line was checked against the texts. (All Cited.)

1. $`K`$ is 36,000 slots in #533 and 64,800 in its base (protocol 104 on the latest #533, 103 on the base).
2. The epoch keeps its length. Its phases read $`\lfloor k/f \rfloor`$ in place of $`K`$ (protocol 153–159, RFC-533 221–225). The nonce and the inferred stake are read at slot $`6\lfloor k/f \rfloor`$ of the epoch (protocol 155, 229, 237). `PERIOD` is $`6\lfloor k/f \rfloor`$ (inference 55).
3. $`\phi`$ is 689 at 10 hours and 1,291 at 18 hours (protocol 105 and 553 on the latest #533, 104 and 552 on the base). It is sized while the stake that builds equals $`D`$ and every block is $`T_M`$ slots late (protocol 526).
4. The $`K`$ row requires a coalition of $`\alpha_\text{max} = 3/10`$ of the total active stake to be held while at most one of three disturbances holds. The base requires at most two together. Both take the epoch nonce as unbiased, and both say that a coalition can bias it (protocol 104 on the latest #533, 103 on the base).
5. The nonce is not redesigned. It is the hash chain of protocol 181–197. RFC-533 says that the nonce stays as it is (line 91) and that a sequential delay is not proposed (line 108).
6. With today's nonce the bound proves 27.2 to 27.9 % at 10 hours with no disturbance, and 24.7 to 25.5 % at 15 s (RFC-533 97–98).
7. An attack that meets two ground nonces reaches only targets within $`K`$ slots of the epoch's end: 5.6 % of targets at 10 hours and 10 % at 18 (RFC-533 106, RFC-532 117).

## 2. Labels

Every numbered statement carries one label.

- **Proved.** The definitions, the statement and a complete argument are in this text.
- **Computed.** A script in this folder evaluates a formula that is proved or cited. The file and its lines are named. Binomial tails are evaluated in double precision. The floor's values are exact integers.
- **Cited.** A statement of the specification, of an RFC, of the paper, or of a stored run of the finality study, with its place.
- **Assumed.** Named as an assumption. A model, a design standard, or a reading of a text that is not the text's own statement.

A statement proved in SURVIVAL or GENESIS is labelled Proved with its place there, and the assumptions it rests on are labelled Assumed with their place there. A number that GENESIS gives as an estimate, not a bound, is cited and called an estimate.

In sections 0, 11 and 12 a sentence ends with its label and the statement it rests on.

## 3. When a block becomes immutable

**3.1 (Cited).** `commit` is defined at protocol 500–522:

```
B := B_imm
while B ≠ c_loc:
    C := child_on_chain(B, c_loc)
    if sl_C + K > sl_{c_loc}  or  density_over_slots(c_loc, sl_C + 1, sl_{c_loc} − sl_C) < φ:  break
    B := C
prune the forks that diverged deeper than B, and return B
```

It runs in `on_block` under the Online rule (protocol 488–492) and at the switch to the Online rule (protocol 498). After startup $`B_\text{imm}`$ moves only through it (protocol 498).

**3.2 (Cited).** `density_over_slots(c, s, p)` is the number of distinct occupied slots of the chain ending in $`c`$ among the $`p`$ slots from $`s`$. A slot of $`[s, s+p)`$ counts if it holds a block of the chain, or an uncle referenced by a block of the chain that lies in $`[s, s+p)`$ itself (inference 62). The slot of a block exceeds the slot of its parent (protocol 432). An uncle's slot lies after its parent's slot and before the slot of the block that references it (protocol 332).

**3.3 (Definitions).** Let $`b_0, b_1, \dots, b_n = c_{loc}`$ be the chain of $`c_{loc}`$, with $`b_{j-1}`$ the parent of $`b_j`$. Write $`sl_j`$ for the slot of $`b_j`$. Let $`B_\text{imm} = b_i`$ with $`0 \le i \le n`$ when `commit` is called (protocol 119). For $`1 \le j \le n`$ define:

- the age test $`A(j)`$: $`sl_j + K \le sl_n`$;
- the set $`O(j)`$ of slots $`s`$ with $`sl_j < s \le sl_n`$ that hold a block of the chain, or an uncle referenced by a block $`b_m`$ of the chain with $`sl_j < sl_m \le sl_n`$;
- the count $`N(j) = |O(j)|`$, which is `density_over_slots(c_loc, sl_j + 1, sl_n − sl_j)` by 3.2;
- the floor test $`F(j)`$: $`N(j) \ge \phi`$.

The loop moves from $`b_{j-1}`$ to $`b_j`$ exactly when $`A(j)`$ and $`F(j)`$ hold.

A block is *immutable* at a node when it is the node's $`B_\text{imm}`$ or an ancestor of it.

**3.4 (Proved). The two tests are monotone along the chain.** For $`1 \le j < j' \le n`$:

1. $`O(j') \subseteq O(j)`$, so $`N(j') \le N(j)`$;
2. $`A(j')`$ implies $`A(j)`$;
3. $`F(j')`$ implies $`F(j)`$;
4. $`N(j) \ge n - j`$.

*Proof.* Slots increase along the chain (3.2), so $`sl_j < sl_{j'}`$.
(1) Let $`s \in O(j')`$. Then $`sl_{j'} < s \le sl_n`$, hence $`sl_j < s \le sl_n`$. If $`s`$ holds a block of the chain, then $`s \in O(j)`$. Otherwise $`s`$ holds an uncle referenced by a block $`b_m`$ with $`sl_{j'} < sl_m \le sl_n`$. Then $`sl_j < sl_m \le sl_n`$, so $`s \in O(j)`$.
(2) $`sl_j + K < sl_{j'} + K \le sl_n`$.
(3) By (1), $`N(j) \ge N(j') \ge \phi`$.
(4) The blocks $`b_{j+1}, \dots, b_n`$ have $`n - j`$ distinct slots in $`(sl_j, sl_n]`$, and each of these slots is in $`O(j)`$. ∎

**3.5 (Proved). The result of the loop.** Let $`M`$ be the set of indices $`m`$ with $`i < m \le n`$ at which $`A(m)`$ and $`F(m)`$ both hold. `commit` returns $`b_{m^*}`$ with

$$
m^* = \max(\{i\} \cup M).
$$

So the new $`B_\text{imm}`$ is the later of the old $`B_\text{imm}`$ and the latest block of the chain that meets both tests.

*Proof.* The loop keeps this invariant: $`B = b_m`$ with $`i \le m \le n`$, and both tests hold at every $`j`$ with $`i < j \le m`$. It holds at the start with $`m = i`$. One pass with $`B = b_m \ne b_n`$ sets $`C = b_{m+1}`$. It stops if a test fails at $`m + 1`$. Otherwise it sets $`B = b_{m+1}`$, which keeps the invariant. So the loop ends at an index $`m`$ with $`m = n`$, or with a test that fails at $`m + 1`$.

If $`M`$ is empty and $`i < n`$, a test fails at $`i + 1`$, so the loop ends at $`m = i`$. If $`i = n`$ the loop does not run.

If $`M`$ is not empty, let $`m_1 = \max M`$. By 3.4 (2) and (3), both tests hold at every $`j`$ with $`i < j \le m_1`$. So the loop reaches $`b_{m_1}`$. It stops there, because either $`m_1 = n`$, or a test fails at $`m_1 + 1`$ by the choice of $`m_1`$. ∎

**3.6 (Proved). The exact condition on the tip.** After the call, for every $`x`$ with $`i < x \le n`$: $`b_x`$ is immutable if and only if $`A(x)`$ and $`F(x)`$ hold. In words, a block $`X`$ after the old $`B_\text{imm}`$ is immutable after a call with tip $`c_{loc}`$ exactly when

1. $`X`$ is on the chain of $`c_{loc}`$,
2. $`sl_X + K \le sl_{c_{loc}}`$, and
3. the chain of $`c_{loc}`$ counts at least $`\phi`$ occupied slots in $`(sl_X, sl_{c_{loc}}]`$.

*Proof.* $`b_x`$ is immutable after the call exactly when $`x \le m^*`$. If both tests hold at $`x`$, then $`x \in M`$, so $`x \le m^*`$ by 3.5. If $`i < x \le m^*`$, then $`m^* > i`$, so $`m^* \in M`$, and 3.4 gives both tests at $`x`$. ∎

Three consequences follow at once. (All Proved.)

- The slot of the tip that makes $`X`$ immutable is at least $`sl_X + K`$. It is also at least $`sl_X + \phi`$, because $`N \le sl_n - sl_X`$.
- The condition reads the slot of the tip and not a clock. A block becomes immutable only when the node processes a block.
- The old $`B_\text{imm}`$ need not meet the tests against the new tip. The Online rule can move $`c_{loc}`$ to a longer fork whose tip has an earlier slot. `out_02_commit.txt`, lines 3 to 4, gives an example. (Computed.)

**3.7 (Proved). An immutable block stays on the local chain.** While a node runs `on_block` (protocol 470–494): (a) $`B_\text{imm}`$ is $`c_{loc}`$ or an ancestor of it; (b) each new $`B_\text{imm}`$ is the old one or a descendant of it.

*Proof.* By induction over the calls. At startup (a) holds by protocol 119. In a call, the chain $`c`$ is the new block if it extends $`c_{loc}`$, and $`c_{loc}`$ otherwise (protocol 484). Both descend from $`B_\text{imm}`$. Each fork choice rule starts from that chain and moves only to a fork that passes `is_ancestor(B_imm, c_fork)` (fork choice 119 and 151). So the new $`c_{loc}`$ is $`B_\text{imm}`$ or a descendant of it. Under the Online rule `commit` then returns a block of that chain at or after $`B_\text{imm}`$ (3.5). Under the Bootstrap rule $`B_\text{imm}`$ does not move (protocol 127). ∎

**3.8 (Computed).** `s02_commit.py` writes the loop and the count from 3.1 and 3.2 and checks 3.4, 3.5 and 3.6 on 300,000 random chains with uncles, random $`K`$, $`\phi`$ and starting $`B_\text{imm}`$. Every check held (`out_02_commit.txt`, line 1). The check supports the proofs. It does not replace them.

## 4. When a value read at a slot can no longer change

**4.1 (Cited).** `compute_epoch_state(ep, tip)` reads three values from the chain of `tip` (protocol 209–249). Write $`s_0`$ for the first slot of epoch $`ep - 1`$.

- $`\eta^{ep}`$ is $`\eta_{B'}`$, where $`B'`$ is the last block before the start of the Lottery Constants Finalization phase (protocol 197, 229). $`\eta_B`$ is a hash of the parent's value, of the block's contribution and of its slot (protocol 191–192).
- $`D^{ep}`$ is computed from $`D^{ep-1}`$ and from the number of occupied slots of the chain in the window $`[s_0, s_0 + 6U)`$ (protocol 233–247).
- $`\mathbb{C}_\text{LEAD}^{ep}`$ is the commitment root at slot $`s_0`$ (protocol 225).

The lottery of every slot of epoch $`ep`$ reads them (leadership 137–146).

**4.2 (Definitions).** A *read slot* $`sl_\text{cut}`$ is a slot at which the specification reads a value from the chain. A *use slot* $`sl_\text{use} > sl_\text{cut}`$ is the slot from which the value must no longer change. $`G = sl_\text{use} - sl_\text{cut}`$ is the gap. Two pairs occur in the Epoch Schedule.

| Value | $`sl_\text{cut}`$ | $`sl_\text{use}`$ | $`G`$ |
| --- | --- | --- | --- |
| $`\eta`$ and $`D`$ of the next epoch | slot $`6U`$ of the epoch | the first slot of the next epoch | $`4U`$, phase 3 |
| the snapshot $`\mathbb{C}_\text{LEAD}`$ | the first slot of the epoch | the first slot of phase 2 | $`3U`$, phase 1 |

The second row follows the phase's description: the phase waits for the snapshot to finalize before the next phase is entered (Cited: protocol 153).

For a chain, $`B'`$ is its last block with a slot below $`sl_\text{cut}`$, and $`Y`$ is its first block with a slot of $`sl_\text{cut}`$ or later, if there is one. Then $`B'`$ is the parent of $`Y`$.

**4.3 (Proved). The value is a function of the chain that ends at $`B'`$.** This holds for $`(\eta^{ep}, D^{ep})`$ with $`sl_\text{cut} = s_0 + 6U`$.

*Proof.* $`\eta^{ep} = \eta_{B'}`$, and $`\eta_{B'}`$ is defined by a recursion over $`B'`$ and its ancestors (4.1). The count of occupied slots reads the blocks of the chain in the window and the uncles that those blocks carry. Each such block has a slot below $`sl_\text{cut}`$, so it is $`B'`$ or an ancestor of $`B'`$. $`D^{ep-1}`$ is, by induction on the epoch, a function of blocks with slots below the previous cut-off. ∎

**(Assumed, A4.)** The specification does not define `commitment_root_at_slot`. This review assumes that the root at slot $`s_0`$ reads only blocks of the chain with slots below $`s_0`$. Then 4.3 holds for the snapshot with $`sl_\text{cut} = s_0`$.

**4.4 (Proved). Which block must be immutable.** Say that the value is *fixed* at a node when every chain through the node's $`B_\text{imm}`$ has the same $`B'`$. By 3.7 and 4.3 the node then derives the same value whatever blocks it receives later. Let $`B'`$ and $`Y`$ be those of the node's chain.

1. If $`Y`$ is immutable, the value is fixed.
2. If $`B'`$ is immutable and $`sl_{B'} = sl_\text{cut} - 1`$, the value is fixed.
3. In every other case the value is not fixed. There is a chain through $`B_\text{imm}`$ with another $`B'`$, and the Online rule adopts such a chain as soon as it holds it and it is longer than $`c_{loc}`$.

*Proof.* (1) Every chain through $`B_\text{imm}`$ contains $`Y`$ and its parent $`B'`$. Slots increase along a chain, and $`sl_{B'} < sl_\text{cut} \le sl_Y`$. So $`B'`$ is the last block below $`sl_\text{cut}`$ on that chain.
(2) Every chain through $`B_\text{imm}`$ contains $`B'`$. Each later block has a slot above $`sl_\text{cut} - 1`$. So $`B'`$ is the last block below $`sl_\text{cut}`$.
(3) Either $`B_\text{imm} = B'`$ with $`sl_{B'} \le sl_\text{cut} - 2`$, or $`B_\text{imm}`$ is a strict ancestor of $`B'`$. In the first case let $`X`$ be a block with parent $`B'`$ and slot $`sl_\text{cut} - 1`$. On a chain through $`X`$ the last block below $`sl_\text{cut}`$ is $`X`$, not $`B'`$. In the second case let $`C`$ be the child of $`B_\text{imm}`$ on $`c_{loc}`$, and let $`X \ne C`$ be a block with parent $`B_\text{imm}`$ and slot $`sl_C`$. A chain through $`X`$ does not contain $`C`$, so it does not contain $`B'`$. The Online rule moves to a fork that descends from $`B_\text{imm}`$ and has more blocks (fork choice 148–159). ∎

Statement 3 is about what the node's rules allow. Whether such a block $`X`$ can exist depends on who won its slot.

**4.5 (Definition).** A node *first uses* the value when it validates or builds its first block with a slot of $`sl_\text{use}`$ or later. Until then every block it has processed has a slot below $`sl_\text{use}`$. The value is *final when first used* if it is fixed at that moment.

**4.6 (Proved). The least gap.** Consider a node whose $`B_\text{imm}`$ was a strict ancestor of $`B'`$ at some earlier time. If the value is final when the node first uses it, then the node has held a tip $`T`$ with $`sl_T \le sl_\text{use} - 1`$ such that one of these holds:

1. $`Y`$ is on the chain of $`T`$, $`sl_Y + K \le sl_T`$, and that chain counts at least $`\phi`$ occupied slots in $`(sl_Y, sl_T]`$;
2. $`sl_{B'} = sl_\text{cut} - 1`$, $`sl_\text{cut} - 1 + K \le sl_T`$, and the chain of $`T`$ counts at least $`\phi`$ occupied slots in $`(sl_\text{cut} - 1, sl_T]`$.

Hence:

- if $`G < K`$, the value is never final when first used;
- if $`G = K`$, it is final only in case 2 with $`sl_T = sl_\text{use} - 1`$, so blocks must sit in the slots $`sl_\text{cut} - 1`$ and $`sl_\text{use} - 1`$ exactly;
- case 1 needs $`G \ge K + 1`$.

*Proof.* By 4.4 the value is fixed only if $`Y`$ is immutable, or $`B'`$ is immutable with $`sl_{B'} = sl_\text{cut} - 1`$. $`B_\text{imm}`$ moved past its earlier position only through `commit` (3.1). Each call before the first use had a tip with a slot below $`sl_\text{use}`$ (4.5). If the value is fixed because $`Y`$ is immutable, take the first call after which $`Y`$ was immutable. Otherwise take the first call after which $`B'`$ was immutable, where $`sl_{B'} = sl_\text{cut} - 1`$. Let $`T`$ be its tip. The block lay after the starting $`B_\text{imm}`$ of that call, so 3.6 gives both tests against $`T`$. For $`Y`$ that is case 1, and for $`B'`$ it is case 2. In case 1, $`sl_\text{cut} \le sl_Y`$ and $`sl_Y + K \le sl_T \le sl_\text{use} - 1`$, so $`G \ge K + 1`$. In case 2, $`sl_\text{cut} - 1 + K \le sl_T \le sl_\text{use} - 1`$, so $`G \ge K`$, with equality only if $`sl_T = sl_\text{use} - 1`$. ∎

**4.7 (Cited).** The specification states: each phase that waits for a value to finalize must last at least $`K`$, or `commit` cannot make the value final within the phase (protocol 157). The $`K`$ row repeats it (protocol 104). 4.6 confirms that bound. It also shows that a phase of exactly $`K`$ slots makes its value final only when two given slots hold blocks.

## 5. The chance that a value is not final when first used

**5.1 (Cited).** Finality Floor defines $`\phi`$ as the largest $`n`$ such that the chance of the chain holding fewer than $`n`$ blocks in $`K`$ slots is at most $`\varepsilon`$. The chance is taken while the stake that builds equals $`D`$ and every block is delivered $`T_M`$ slots late (protocol 526). Its code takes a gap between blocks as $`T_M`$ slots plus the wait for the next win, whose chance per slot is $`f`$, and returns

$$
\texttt{blocks\_short}(n) = \Pr[\mathrm{Bin}(K - n\,T_M,\ f) \le n - 1],
$$

and 1 when $`K - n\,T_M < n`$ (protocol 533–544).

**5.2 (Assumed). The model $`M(p, d)`$.** It is the model of 5.1 with the chance $`p`$ and the delay $`d`$ left free.

- M1. Each slot $`t`$ has a mark $`\xi_t \in \{0, 1\}`$. The mark is 1 when the stake that builds wins the slot. The marks are independent, and each is 1 with chance $`p`$.
- M2. The node follows one chain. If slot $`s`$ holds a block of the chain, the next block of the chain is in the first slot $`t > s + d`$ with $`\xi_t = 1`$.
- M3. A count of `density_over_slots` over a range is at least the number of blocks of the chain in the range, and at most the number of marked slots in it.
- M4. When the stake that builds is a share $`x`$ of $`D`$, then $`p = p_x = 1 - (1-f)^x`$.
- M5. The node runs the Online rule and processes every block of the chain, in the order of their slots.

The specification's case is $`p = f`$ and $`d = T_M`$.

Notes on the model. (Cited, except where marked.)

- The lower end of M3 is 3.4 (4). The upper end holds when every win that can be counted is a win of the stake that builds. A counted slot holds a block or a referenced uncle, each a genuine lottery win (protocol 322, 336), and stake that does not build publishes no block that a block of the chain could reference (protocol 342–344). (Assumed.)
- On M4: the leadership proof uses the second-order expansion of $`1 - (1-f)^{v/D}`$ for a note of value $`v`$. Its error is at most 0.045 % of the chance (leadership 199–212, 254–281). That tickets of different notes are independent is assumed.
- The model has no adversary that reorganises the chain. $`K`$ is sized against that (protocol 104). The model measures only how fast blocks accumulate. (Assumed.)

Two functions are used below. For integers $`n \ge 0`$, $`L`$, $`m`$:

$$
S(n; L, p, d) = \Pr[\mathrm{Bin}(L - nd,\ p) \le n - 1], \qquad R(m; p) = \Pr[\mathrm{Bin}(m, p) \le 1] = (1-p)^m + m\,p\,(1-p)^{m-1}.
$$

$`S`$ is 1 when $`L - nd < n`$, and $`R`$ is 1 when $`m \le 0`$. So $`\texttt{blocks\_short}(n) = S(n; K, f, T_M)`$.

**5.3 (Proved). Blocks in a window.** In $`M(p, d)`$ let $`a`$ be a slot that is not before the first block of the chain. For integers $`n \ge 1`$ and $`L \ge 0`$,

$$
\Pr[\text{fewer than } n \text{ blocks of the chain have slots in } (a, a + L]] \le S(n; L, p, d).
$$

Equality holds when slot $`a`$ holds a block of the chain. So `blocks_short(n)` is exactly the chance that fewer than $`n`$ blocks follow a block of the chain within $`K`$ slots.

*Proof.* Step 1. Let $`s \le a`$ be the slot of the last block of the chain at or before $`a`$. By M2 the next block is in the first marked slot after $`s + d`$. Call that slot $`s'`$. Then $`s' > a`$ by the choice of $`s`$. Every slot after $`a + d`$ is after $`s + d`$. So $`s'`$ is at or before the first marked slot after $`a + d`$.

Step 2. Put $`\tau_0 = a`$, and let $`\tau_i`$ be the first marked slot after $`\tau_{i-1} + d`$. Let $`s_1 < s_2 < \dots`$ be the slots of the blocks of the chain after $`a`$. Then $`s_i \le \tau_i`$ for every $`i`$. Step 1 gives $`i = 1`$. If $`s_i \le \tau_i`$, then $`s_{i+1}`$, the first marked slot after $`s_i + d`$, is at or before the first marked slot after $`\tau_i + d`$. If slot $`a`$ holds a block, then $`s_1 = \tau_1`$ by M2, and by the same induction $`s_i = \tau_i`$.

Step 3. Put $`W_i = \tau_i - \tau_{i-1} - d`$. $`W_1`$ is the position of the first 1 among $`\xi_{a+d+1}, \xi_{a+d+2}, \dots`$. For each slot $`t`$, the event $`\tau_1 = t`$ is fixed by the marks up to $`t`$. By M1 the marks after $`t`$ are independent of it. Repeating the argument, $`W_1, W_2, \dots`$ are independent with $`\Pr[W_i = w] = (1-p)^{w-1}p`$, and the trials they consume form one sequence of independent marks. So $`W_1 + \dots + W_n`$ is the position of the $`n`$-th 1 in such a sequence, and for every integer $`m \ge 0`$

$$
\Pr[W_1 + \dots + W_n > m] = \Pr[\mathrm{Bin}(m, p) \le n - 1].
$$

Step 4. Fewer than $`n`$ blocks in $`(a, a + L]`$ means $`s_n > a + L`$. That implies $`\tau_n > a + L`$, which is $`nd + W_1 + \dots + W_n > L`$. By Step 3 its chance is $`S(n; L, p, d)`$. With a block in slot $`a`$ the implication is an equivalence. ∎

`split/SPLIT.md`, sections 2.6 to 2.8, corrects 5.3, 5.4, 5.9, 9.4 and 10.2: delays that vary up to $`d`$ cost one $`d`$, $`G^*`$ leaves out a coalition's private lead, and a span that starts at the epoch's first slot needs another bound.

**5.4 (Proved). Upper bound.** In $`M(p, d)`$ take a read slot $`sl_\text{cut}`$ and a use slot $`sl_\text{use} = sl_\text{cut} + G`$, and integers $`K \ge 1`$, $`\phi \ge 0`$, $`d \ge 0`$. Then

$$
\Pr[\text{the value is not final when first used}] \le S(\phi + 1;\ G, p, d) + R(G - K - 2d + 1;\ p).
$$

The first term bounds the chance that the gap does not hold $`\phi + 1`$ blocks of the chain, with equality when slot $`sl_\text{cut} - 1`$ holds a block. The second bounds the chance that no block of the gap lies at least $`K`$ slots after $`Y`$.

*Proof.* Let $`T`$ be the last block of the chain with a slot of at most $`sl_\text{use} - 1`$. By M5 it is the node's tip when the node first uses the value (4.5). Put $`a = sl_\text{cut} - 1`$ and take $`\tau_i`$ and $`W_i`$ as in 5.3. $`Y`$ is the first block after slot $`a`$, so $`sl_Y \le \tau_1 = sl_\text{cut} - 1 + d + W_1`$.

Event (i): $`\tau_{\phi+1} \le sl_\text{use} - 1`$. Then the chain has $`\phi + 1`$ blocks with slots in $`[sl_\text{cut}, sl_\text{use} - 1]`$. The first is $`Y`$, and the other $`\phi`$ lie in $`(sl_Y, sl_T]`$. By M3 the count over that range is at least $`\phi`$. By 5.3, $`\Pr[\text{not (i)}] = \Pr[\tau_{\phi+1} - a > G] = S(\phi+1; G, p, d)`$.

Event (ii): $`\sigma \le sl_\text{use} - 1`$, where $`\sigma`$ is the first marked slot after $`\tau_1 + K - 1 + d`$. Step 1 of 5.3 at the slot $`sl_Y + K - 1`$ gives a block of the chain with a slot of at least $`sl_Y + K`$, at or before the first marked slot after $`sl_Y + K - 1 + d`$. That slot is at or before $`\sigma`$, because $`sl_Y \le \tau_1`$. On (ii) this block is at or before $`T`$, so $`sl_T \ge sl_Y + K`$. Now $`\sigma = \tau_1 + K - 1 + d + V`$, where $`V`$ is the wait for the first mark after slot $`\tau_1 + K - 1 + d`$. As in Step 3 of 5.3, $`V`$ is independent of $`W_1`$ and has its law. Event (ii) fails exactly when $`W_1 + V > G - K - 2d + 1`$. By Step 3 with $`n = 2`$, $`\Pr[\text{not (ii)}] = R(G - K - 2d + 1; p)`$.

On (i) and (ii) both tests of `commit` hold at $`Y`$ against $`T`$. When the node processes $`T`$, `commit` makes $`Y`$ immutable, unless it already is (3.6). Then the value is fixed (4.4). The union bound gives the claim. ∎

**5.5 (Proved). Lower bounds.** In $`M(p, d)`$, for a node as in 4.6:

1. $`\Pr[\text{not final when first used}] \ge \max\big(\Pr[\mathrm{Bin}(G, p) \le \phi - 1],\ (1-p)^{G - K + 1}\big)`$ for $`G \ge K`$. The chance is 1 for $`G < K`$.
2. If only blocks of the chain count as occupied slots, $`\Pr[\text{not final when first used}] \ge \max\big(\Pr[\mathrm{Bin}(G + 1 - \phi d,\ p) \le \phi],\ (1-p)^{G-K+1}\big)`$ for $`G \ge K`$.
3. A chance of at most $`\varepsilon`$ needs $`G \ge K - 1 + \ln(1/\varepsilon) \big/ \big(x \ln\tfrac{1}{1-f}\big)`$. At $`\varepsilon = 10^{-9}`$ that is $`K - 1 + 611.28/x`$ slots.
4. At $`G = K`$ the value is final when first used with chance at most $`p^2`$.

*Proof.* By 4.6 the value is final only in case 1 or case 2 of 4.6.
(1) In both cases at least $`\phi`$ slots are counted in a range inside $`[sl_\text{cut}, sl_\text{use} - 1]`$. By M3 they are marked slots, and that interval has $`G`$ slots. So the chance of being final is at most $`\Pr[\mathrm{Bin}(G, p) \ge \phi]`$. Also, in case 1 the slot of $`Y`$ is a marked slot in $`[sl_\text{cut}, sl_\text{use} - 1 - K]`$, and in case 2 the slot $`sl_\text{cut} - 1`$ is marked. So a marked slot lies in $`[sl_\text{cut} - 1, sl_\text{cut} + G - K - 1]`$, an interval of $`G - K + 1`$ slots. The chance of that is $`1 - (1-p)^{G-K+1}`$.
(2) In both cases at least $`\phi + 1`$ blocks of the chain have slots in $`[sl_\text{cut} - 1, sl_\text{use} - 1]`$. Let their slots be $`b_1 < b_2 < \dots`$. Let $`\tau'_1`$ be the first marked slot at or after $`sl_\text{cut} - 1`$, and $`\tau'_{i+1}`$ the first marked slot after $`\tau'_i + d`$. Then $`b_1 \ge \tau'_1`$, because a block sits in a marked slot. By M2, $`b_{i+1}`$ is the first marked slot after $`b_i + d`$, so $`b_i \ge \tau'_i`$ implies $`b_{i+1} \ge \tau'_{i+1}`$. Hence the chance of being final is at most $`\Pr[\tau'_{\phi+1} \le sl_\text{use} - 1]`$. As in Step 3 of 5.3, this is $`\Pr[\mathrm{Bin}(G + 1 - \phi d, p) \ge \phi + 1]`$. (1) gives the second term.
(3) By (1), $`(1-p)^{G-K+1} \le \varepsilon`$ with $`1 - p = (1-f)^x`$.
(4) By 4.6 both slots $`sl_\text{cut} - 1`$ and $`sl_\text{use} - 1`$ must be marked. ∎

**5.6 (Computed).** `s04_gap_sim.py` samples the model at reduced sizes and applies the rule of 4.4 and 4.5 to each sample. For the first 300 samples of each row it also runs the literal loop of 3.1. In all 20 rows the sampled frequency lies between the bounds of 5.5 (2) and 5.4, and the count after a block in slot $`sl_\text{cut} - 1`$ matches $`S(\phi+1; G, p, d)`$ (`out_04_gap_sim.txt`, lines 2 to 22). One row: $`K`$ = 3,000, $`\phi`$ = 55, $`d`$ = 15, $`x`$ = 0.7, $`G = K + 1{,}500`$ gives a lower bound of $`1.86 \cdot 10^{-4}`$, 81 failures in 400,000 samples, and an upper bound of $`2.16 \cdot 10^{-4}`$ (line 12).

**5.7 (Computed). The least building share, by gap.** `s03_gap_bound.py` solves the bounds for the least $`x`$ that keeps the chance at most $`10^{-9}`$ (`out_03_gap_bound.txt`, lines 4 to 19 and 88 to 100).

- "Necessary" is 5.5 (1): below this share the chance exceeds $`10^{-9}`$ even if every win of the gap is counted and no block is late.
- "Sufficient" is 5.4: at this share the chance is at most $`10^{-9}`$ when only blocks of the chain count and every block is $`d`$ slots late.
- When only blocks of the chain count, 5.5 (2) puts the least share within 0.15 points below the sufficient one in every row.
- "Mean rate" is the RFCs' figure: the share at which the gap holds $`\phi`$ occupied slots on average, $`p_x G = \phi`$ (Cited: RFC-533 183, RFC-532 308).

$`K`$ = 36,000, $`\phi`$ = 689 (the latest #533):

| Gap | Mean rate | Necessary | Sufficient, 10 s | Sufficient, 15 s |
| --- | --- | --- | --- | --- |
| 72 h | 7.85 % | 9.78 % | 10.06 % | 10.20 % |
| 54 h | 10.47 % | 13.05 % | 13.54 % | 13.80 % |
| 45 h | 12.57 % | 15.66 % | 16.38 % | 16.75 % |
| 40 h | 14.15 % | 17.62 % | 18.54 % | 19.02 % |
| 36 h | 15.72 % | 19.59 % | 20.72 % | 21.32 % |
| 30 h | 18.88 % | 23.52 % | 25.16 % | 26.05 % |
| 24 h | 23.62 % | 29.42 % | 32.03 % | 33.48 % |
| 22 h | 25.77 % | 32.10 % | 35.23 % | 37.00 % |
| 18 h | 31.53 % | 39.28 % | 44.04 % | 46.85 % |
| 14 h | 40.60 % | 50.58 % | 58.74 % | 63.85 % |
| 12 h | 47.42 % | 59.07 % | 70.50 % | 77.99 % |
| 11 h | 51.77 % | 64.49 % | 78.35 % | 87.70 % |
| 10.5 h | 54.26 % | 67.59 % | 82.97 % | 93.53 % |
| 10.25 h | 55.60 % | 69.26 % | 85.60 % | 96.75 % |

$`K`$ = 64,800, $`\phi`$ = 1,291 (the base):

| Gap | Mean rate | Necessary | Sufficient, 10 s | Sufficient, 15 s |
| --- | --- | --- | --- | --- |
| 72 h | 14.73 % | 17.32 % | 18.25 % | 18.74 % |
| 54 h | 19.65 % | 23.11 % | 24.78 % | 25.70 % |
| 45 h | 23.60 % | 27.76 % | 30.19 % | 31.57 % |
| 40 h | 26.56 % | 31.24 % | 34.36 % | 36.15 % |
| 36 h | 29.53 % | 34.73 % | 38.62 % | 40.90 % |
| 30 h | 35.47 % | 41.72 % | 47.46 % | 50.94 % |
| 24 h | 44.41 % | 52.23 % | 61.53 % | 67.52 % |
| 22 h | 48.48 % | 57.01 % | 68.29 % | 75.74 % |
| 20 h | 53.37 % | 62.77 % | 76.70 % | 86.23 % |
| 19 h | 56.21 % | 66.10 % | 81.74 % | 92.65 % |
| 18.5 h | 57.74 % | 67.91 % | 84.51 % | 96.23 % |
| 18.25 h | 58.54 % | 68.84 % | 86.05 % | 98.13 % |

Three comparisons.

- The RFCs give 7.9 % and 10.5 % for the phases of 72 and 54 hours at 10 hours, and 14.7 % and 19.7 % at 18 hours. These are the mean-rate column. At the mean-rate share the value is not final in time with a chance of at least 0.49 (`out_03_gap_bound.txt`, lines 22–23 and 103–104). The shares that keep the chance at $`10^{-9}`$ are 10.2 % and 13.8 %, and 18.7 % and 25.7 %.
- The stored run `slot-finality/dual/epochs/out/phase_waits.txt` of the finality study gives 9.8 to 10.2 % and 13.0 to 13.8 % at the floor of 689, and 17.3 to 18.7 % and 23.1 to 25.7 % at 1,291 (Cited: its lines 3, 4, 8, 9). The table agrees.

**5.8 (Computed). The least gap, by building share.** The least gap with a chance of at most $`10^{-9}`$ lies between the "necessary" and the "sufficient" columns (`out_03_gap_bound.txt`, lines 46 to 57, 61 to 72, 124 to 135, 139 to 150). Hours are in brackets.

$`K`$ = 36,000, $`\phi`$ = 689:

| Building share | Necessary, every win counted | Necessary, chain blocks only, 15 s | Sufficient, 10 s | Sufficient, 15 s |
| --- | --- | --- | --- | --- |
| 100 % | 36,611 (10.17) | 36,611 (10.17) | 36,726 (10.20) | 36,736 (10.20) |
| 93 % | 36,657 (10.18) | 37,938 (10.54) | 36,779 (10.22) | 37,954 (10.54) |
| 90 % | 36,679 (10.19) | 38,847 (10.79) | 36,805 (10.22) | 38,863 (10.80) |
| 70 % | 36,873 (10.24) | 46,894 (13.03) | 43,460 (12.07) | 46,910 (13.03) |
| 63 % | 40,531 (11.26) | 50,917 (14.14) | 47,483 (13.19) | 50,933 (14.15) |
| 50 % | 50,978 (14.16) | 61,379 (17.05) | 57,945 (16.10) | 61,395 (17.05) |
| 30 % | 84,733 (23.54) | 95,178 (26.44) | 91,744 (25.48) | 95,194 (26.44) |
| 20 % | 126,928 (35.26) | 137,426 (38.17) | 133,992 (37.22) | 137,442 (38.18) |
| 10 % | 253,510 (70.42) | 264,173 (73.38) | 260,739 (72.43) | 264,189 (73.39) |

$`K`$ = 64,800, $`\phi`$ = 1,291:

| Building share | Necessary, every win counted | Necessary, chain blocks only, 15 s | Sufficient, 10 s | Sufficient, 15 s |
| --- | --- | --- | --- | --- |
| 100 % | 65,411 (18.17) | 65,411 (18.17) | 65,526 (18.20) | 65,537 (18.20) |
| 93 % | 65,457 (18.18) | 68,204 (18.95) | 65,579 (18.22) | 68,220 (18.95) |
| 90 % | 65,479 (18.19) | 69,810 (19.39) | 65,605 (18.22) | 69,826 (19.40) |
| 70 % | 65,673 (18.24) | 84,037 (23.34) | 77,593 (21.55) | 84,053 (23.35) |
| 63 % | 71,735 (19.93) | 91,151 (25.32) | 84,707 (23.53) | 91,167 (25.32) |
| 50 % | 90,218 (25.06) | 109,646 (30.46) | 103,202 (28.67) | 109,662 (30.46) |
| 30 % | 149,931 (41.65) | 169,402 (47.06) | 162,958 (45.27) | 169,418 (47.06) |
| 20 % | 224,573 (62.38) | 244,097 (67.80) | 237,653 (66.01) | 244,113 (67.81) |
| 10 % | 448,499 (124.58) | 468,183 (130.05) | 461,739 (128.26) | 468,199 (130.06) |

Write $`G^*(x, d)`$ for the "sufficient" value: the least $`G`$ at which the bound of 5.4 is at most $`10^{-9}`$.

Readings of the table. (Computed, from the rows above, except where marked.)

- With all of the inferred stake building, the least gap is $`K + 611`$ to $`K + 736`$ slots. The margin over $`K`$ is 10 to 12 minutes.
- At 15 s the floor has no margin (Cited: RFC-533 143). So, when only blocks of the chain count, any stake that does not build moves the least gap well past $`K`$: 13.03 hours at 70 % and 17.05 hours at 50 %, for $`K`$ = 10 hours.
- If every win is counted, as when every lost block returns as an uncle, 5.5 (1) rules out only gaps below 10.24 hours at 70 %. That such a gap suffices is not proved here. The count of uncles is what separates the two "necessary" columns.
- RFC-533 gives 12.1 hours at 10 s and 13.0 at 15 s as the latest finality while 30 % withholds (Cited: line 141). The row of 70 % gives 12.07 and 13.03.
- By construction of $`\phi`$, $`S(\phi + 1; K, f, T_M) > \varepsilon`$. So at $`G = K`$ the first term of 5.4 alone exceeds $`\varepsilon`$ when $`x = 1`$ and $`d = T_M`$. (Proved from 5.1.) `out_01_setting.txt`, lines 13, 14, 22 and 23, gives the exact values: `blocks_short` is $`9.815 \cdot 10^{-10}`$ at 689 and $`1.367 \cdot 10^{-9}`$ at 690, and $`9.933 \cdot 10^{-10}`$ at 1,291 and $`1.271 \cdot 10^{-9}`$ at 1,292. (Computed, in exact integer arithmetic.)

**5.9 (Computed). The least gap in each state of the $`K`$ row.** The $`K`$ row names a state without a disturbance and three disturbances (Cited: protocol 104). The table maps each to a building share and a delay, for a coalition of 30 % that does not build. The mapping is this review's. (Assumed.)

- No disturbance: honest blocks are up to $`\Delta`$ = 10 slots late and $`D`$ is the total active stake. So $`x`$ = 0.7 and $`d`$ = 10.
- First disturbance: honest blocks are up to $`T_M`$ = 15 slots late. So $`x`$ = 0.7 and $`d`$ = 15.
- Second disturbance: a tenth of the honest stake is offline and the inference has corrected to the stake that is online, as RFC-533 reads these rows (Cited: line 60). So $`D`$ is 0.93 of the total, and $`x`$ = 0.63/0.93 = 0.677, with $`d`$ = 10.
- Third disturbance: $`D`$ equals the honest stake that is online. So $`x`$ = 1 and $`d`$ = 10.

| State | $`x`$ | $`d`$ | $`G^*`$ at $`K`$ = 36,000, $`\phi`$ = 689 | $`G^*`$ at $`K`$ = 64,800, $`\phi`$ = 1,291 |
| --- | --- | --- | --- | --- |
| no disturbance | 70 % | 10 | 43,460 (12.07 h) | 77,593 (21.55 h) |
| every block $`T_M`$ late | 70 % | 15 | 46,910 (13.03 h) | 84,053 (23.35 h) |
| a tenth of the honest stake offline | 67.74 % | 10 | 44,667 (12.41 h) | 79,727 (22.15 h) |
| deflated inference | 100 % | 10 | 36,726 (10.20 h) | 65,526 (18.20 h) |
| 15 s and a tenth offline (base only) | 67.74 % | 15 | | 86,187 (23.94 h) |
| 15 s and a deflated inference (base only) | 100 % | 15 | | 65,537 (18.20 h) |
| a tenth offline and a deflated inference (base only) | 100 % | 10 | | 65,526 (18.20 h) |

Source: `out_09_epoch.txt`, lines 11 to 14 and 40 to 46. The largest value is 13.03 hours for the latest #533, which requires one disturbance at a time. It is 23.94 hours for the base, which requires two together.

The necessary values of 5.5 in the same states follow. A shorter gap fails with a chance above $`10^{-9}`$ (`out_14_bracket.txt`, lines 7 to 10 and 14 to 20).

| State | Every win counted, $`K`$ = 36,000 | Chain blocks only, $`K`$ = 36,000 | Every win counted, $`K`$ = 64,800 | Chain blocks only, $`K`$ = 64,800 |
| --- | --- | --- | --- | --- |
| no disturbance | 36,873 (10.24 h) | 43,449 (12.07 h) | 65,673 (18.24 h) | 77,582 (21.55 h) |
| every block $`T_M`$ late | 36,873 (10.24 h) | 46,894 (13.03 h) | 65,673 (18.24 h) | 84,037 (23.34 h) |
| a tenth of the honest stake offline | 37,718 (10.48 h) | 44,656 (12.40 h) | 66,759 (18.54 h) | 79,716 (22.14 h) |
| deflated inference | 36,611 (10.17 h) | 36,611 (10.17 h) | 65,411 (18.17 h) | 65,411 (18.17 h) |
| 15 s and a tenth offline (base only) | | | 66,759 (18.54 h) | 86,171 (23.94 h) |
| 15 s and a deflated inference (base only) | | | 65,411 (18.17 h) | 65,411 (18.17 h) |
| a tenth offline and a deflated inference (base only) | | | 65,411 (18.17 h) | 65,411 (18.17 h) |

The largest necessary values are 37,718 slots with every win counted and 46,894 with chain blocks only for the latest #533. They are 66,759 and 86,171 for the base.

The second disturbance can be read in two ways: after the inference has corrected to the stake that is online, as above, or before it corrects. Before it corrects, $`D`$ is still the total, and $`x`$ = 0.63. Then $`G^*`$ is 13.19 hours at 10 hours and 23.53 hours at 18 (`out_09_epoch.txt`, lines 15 and 47). The necessary values at 10 hours are 40,531 slots with every win counted and 47,472 with chain blocks only (`out_14_bracket.txt`, line 12). $`w_B`$ is 17,709 slots (4.92 h) at 10 s (9.4). With the window shortened, the epochs that suffice in 10.3 become 137,191 slots (38.11 h) for the latest #533 and 245,306 slots (68.14 h) for the base. With the window kept they stay 460,799 and 518,399 slots (128.00 and 144.00 h), because phase 3 then lasts $`2K - 1`$ slots (10.2) (`out_14_bracket.txt`, lines 32–33 and 38–39). (Computed. Assumed, 9.4.)

The text of the $`K`$ row supports the first reading. (Assumed: a reading of protocol 104.)

- The state without a disturbance has three clauses: honest blocks up to $`\Delta`$ late, all of the honest stake online, and $`D`$ equal to the total active stake. Each disturbance replaces one of them. The second replaces only the clause on the honest stake. So $`D`$ still equals the total active stake.
- The row says that the coalition's share "is counted while all of the honest stake is online". That is needed only if the total active stake falls when honest stake goes offline. So the total active stake is the stake that is online, and $`D`$ is 0.93 of the total.

RFC-533 reads the row the same way, and defines the total active stake as the stake that takes part in the lottery (Cited: lines 31 and 60). The rest of this review uses the first reading, and gives the second where it changes a result.

**5.10 (Proved). A remark on the node's clock.** 4.5 reads the first use on the chain. A node that draws the lottery of slot $`sl_\text{use}`$ holds, in $`M(p, d)`$, only the blocks with slots up to $`sl_\text{use} - 1 - d`$ from other nodes. For such a node the bound of 5.4 holds with $`G - d`$ in place of $`G`$, by the same proof. The difference is $`d`$ slots, at most 15.

## 6. Targets whose race meets two nonces

**6.1 (Cited).** RFC-533 106: two ground nonces reach only targets past the cut-off and within $`K`$ slots of the epoch's end, 5.6 % of targets at 10 hours against 10 % at 18. RFC-532 117 adds that on a chain that meets the floor a race lasts about $`K`$.

**6.2 (Proved). The count of nonces.** Let the epoch have $`E`$ slots, so that epoch $`e`$ holds the slots $`[eE, (e+1)E)`$ and the lottery of slot $`s`$ reads the nonce of epoch $`\lfloor s/E \rfloor`$ (4.1). Take a target block in slot $`t`$. Let $`t + L`$ be the slot of the tip that makes the target immutable. By 3.6, $`L \ge K`$, with equality when a block sits in slot $`t + K`$ and the floor is met. The race for the target draws the lotteries of the slots $`t, \dots, t + L`$. It meets

$$
n(t, L) = \lfloor (t + L)/E \rfloor - \lfloor t/E \rfloor + 1
$$

nonces. Then:

1. if $`L \le E`$, $`n`$ is 1 or 2, and $`n = 2`$ exactly when $`t`$ is one of the last $`L`$ slots of its epoch, a share $`L/E`$ of the slots;
2. for every $`L`$, the mean of $`n`$ over the slots of an epoch is $`1 + L/E`$, and its largest value is $`1 + \lceil L/E \rceil`$.

*Proof.* The slots $`t, \dots, t+L`$ lie in the epochs $`\lfloor t/E \rfloor, \dots, \lfloor (t+L)/E \rfloor`$, and each of these epochs holds one of them. That gives $`n`$. Write $`t = eE + r`$ with $`0 \le r < E`$. Then $`n = 1 + \lfloor (r + L)/E \rfloor`$. (1) If $`L \le E`$ then $`r + L < 2E`$, so $`n \le 2`$, and $`n = 2`$ exactly when $`r \ge E - L`$. (2) Write $`L = qE + \rho`$ with $`0 \le \rho < E`$. Then $`\lfloor (r + L)/E \rfloor`$ is $`q + 1`$ when $`r \ge E - \rho`$ and $`q`$ otherwise. Its sum over $`r`$ is $`qE + \rho = L`$. Its largest value is $`q + 1`$ when $`\rho \ge 1`$ and $`q`$ when $`\rho = 0`$. ∎

With $`L = K \le E`$ the share is exactly $`K/E`$: 36,000/648,000 = 5.56 % and 64,800/648,000 = 10 %. This is the RFCs' figure. The last $`K`$ slots of an epoch lie past the cut-off exactly when $`K \le G`$. (Proved.)

**6.3 (Computed). Shorter epochs.** `out_05_targets.txt`, lines 5 to 19, gives $`K/E`$ for shorter epochs. An enumeration of 2,540 pairs $`(E, L)`$ agrees with 6.2 (line 1). The epochs of 128.00, 37.83 and 34.83 hours are schedules of 10.4 (`out_09_epoch.txt`, lines 23, 27, 28).

| Epoch | 180 h | 128.00 h | 100 h | 90 h | 60 h | 45 h | 37.83 h | 34.83 h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| $`K`$ = 10 h | 5.56 % | 7.81 % | 10.00 % | 11.11 % | 16.67 % | 22.22 % | 26.44 % | 28.71 % |

For the base, with $`K`$ = 18 hours, the share is 10 % at 180 hours, 18 % at 100 hours and 30 % at 60 hours (`out_05_targets.txt`, lines 5, 9, 12). It is 12.50 % and 26.94 % at the epochs that suffice for the base in 10.3, 144.00 and 66.81 hours (`out_09_epoch.txt`, lines 55 and 58).

- An epoch shorter than $`K`$ would make every target meet two nonces or more (6.2). The schedules of section 10 all have $`E \ge 2K`$. (Proved, 10.2.)
- A race that lasts longer than $`K`$ reaches more targets. A race of 13 hours meets two nonces for 7.22 % of targets at today's epoch (`out_05_targets.txt`, line 25). 13.03 hours is the latest race while 30 % withholds at 15 s (5.8).
- What the second nonce costs is in RFC-533: against 30 % at 10 s the wait with today's nonce is 13.6 to 14.1 hours with one ground nonce and 16.0 to 18.8 with two (Cited: lines 45–46).

## 7. The noise of the stake inference and its window

**7.1 (Cited).** The inference's algorithm is at inference 68–88. With `PRECISION` = 1000 it computes, in integers:

```
beta_p = truncate(beta * PRECISION);  f_p = truncate(f * PRECISION);  tse_p = D * PRECISION
measured = N * PRECISION;  expected = PERIOD * f_p;  diff = expected − measured
error = (tse_p * diff) / expected;  correction = (beta_p * error) / PRECISION
D' = max((tse_p − correction) / PRECISION, 1)
```

$`N`$ is the count of occupied slots of the window, $`D`$ the current estimate and $`D'`$ the next. `beta` is 1.0 and $`f`$ is 1/30, so `beta_p` = 1000 and `f_p` = 33.

**7.2 (Proved). The rule in closed form.** Put $`\hat f = 33/1000`$. With integer division that truncates toward zero, the algorithm returns $`\max(D'', 1)`$ with

$$
\frac{D\,N}{P\,\hat f} - 1.001 < D'' < \frac{D\,N}{P\,\hat f} + 0.001 .
$$

*Proof.* Write $`e = 33P`$ and $`m = 1000N`$. The exact value of `error` before truncation is $`v = 1000D(e - m)/e`$. Truncation gives $`v - \theta`$ with $`0 \le \theta < 1`$ if $`v \ge 0`$ and $`-1 < \theta \le 0`$ if $`v < 0`$. `correction` equals `error`, because `beta_p` equals `PRECISION`. So `tse_p − correction` is $`z = 1000Dm/e + \theta`$. If $`v \ge 0`$ then $`z \ge 0`$. If $`v < 0`$ then `error` $`\le 0`$, so $`z \ge 1000D \ge 0`$. So the last division is a floor, and $`z/1000 - 1 < D'' \le z/1000`$. Finally $`z/1000 = DN/(P\hat f) + \theta/1000`$. ∎

`s06_inference.py` runs the algorithm as printed on 200,000 random inputs. The largest distance from the closed form is 0.999938 (`out_06_inference.txt`, line 2). (Computed.)

**7.3 (Assumed). The count.** The count $`N`$ of a window of $`P`$ slots is $`\mathrm{Bin}(P, q)`$, where $`q`$ is the chance that a slot is occupied and counted. When the stake that builds is $`r`$ times $`D`$ and every won slot is counted, $`q = 1 - (1-f)^r`$. The specification's own analysis uses the same law (Cited: `analysis-total-stake-inference.md` 229–245, 374).

**7.4 (Proved). Mean, variance, fixed point and scaling.** Under 7.3, and up to the rounding of 7.2, which is below 1.001 units of stake:

1. $`\mathbb{E}[D'/D] = q/\hat f`$ and $`\mathrm{Var}[D'/D] = q(1-q)/(P\hat f^2)`$;
2. the rule leaves $`D`$ unchanged on average exactly when $`q = \hat f`$, that is when $`r = r^* = \ln(1-\hat f)/\ln(1-f)`$;
3. at that point the standard deviation of $`D'/D`$ is $`\sqrt{(1-\hat f)/(P\hat f)}`$;
4. for a fixed $`q`$ the standard deviation is proportional to $`P^{-1/2}`$: a window $`c`$ times shorter has a standard deviation $`\sqrt{c}`$ times larger;
5. the ratio of the next epoch is $`r' = r\,P\hat f/N`$.

*Proof.* By 7.2, $`D'/D = N/(P\hat f)`$. (1) $`\mathbb{E}[N] = Pq`$ and $`\mathrm{Var}[N] = Pq(1-q)`$. (2) $`q/\hat f = 1`$, and $`1 - (1-f)^r = \hat f`$ gives $`r^*`$. (3) Put $`q = \hat f`$ in (1). (4) In (1), $`P`$ enters only as $`1/P`$. (5) $`r' = S/D'`$ for the stake $`S`$ that builds, and $`S/D = r`$. ∎

Numbers (`out_06_inference.txt`). (Computed.)

- $`r^*`$ = 0.989830. The rule settles where slots are occupied at $`\hat f`$ = 0.033, which is 1.00 % below $`f`$, with $`D`$ 1.03 % above the stake that builds (lines 6–7). RFC-533 states the same (Cited: line 144).
- The mean and variance of 7.4 (1) equal those computed from the binomial law to all printed digits (lines 8–13).
- Iterating the rule for 40 epochs on 200,000 chains gives a standard deviation of $`r/r^*`$ of 0.868 %, 1.228 %, 2.130 % and 2.861 % for windows of 108, 54, 18 and 10 hours. The one-step values of 7.4 (3) are 0.868 %, 1.228 %, 2.127 % and 2.853 % (lines 26–29).

**7.5 (Computed). The noise by window length** (`out_06_inference.txt`, lines 16–23):

| Window | 108 h | 72 h | 54 h | 36 h | 27 h | 18 h | 14.2 h | 10 h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Expected occupied slots | 12,830 | 8,554 | 6,415 | 4,277 | 3,208 | 2,138 | 1,687 | 1,188 |
| Standard deviation of $`D'/D`$ | 0.868 % | 1.063 % | 1.228 % | 1.504 % | 1.736 % | 2.127 % | 2.394 % | 2.853 % |

**7.6 (Computed). What the noise costs the floor.** The floor is sized with $`r = 1`$: the stake that builds equals $`D`$ (5.1). One step of the rule from its fixed point sets the next epoch's ratio to $`r' = r^* P\hat f/N`$ with $`N \sim \mathrm{Bin}(P, \hat f)`$ (7.4). By 5.3 the chance that fewer than $`n`$ blocks follow a block within $`K`$ slots is then $`S(n; K, 1-(1-f)^{r'}, T_M)`$. The table gives its mean over $`N`$ at $`n = \phi`$, and the largest $`n`$ whose mean is at most $`10^{-9}`$ (`out_06_inference.txt`, lines 33–57).

| Window | $`K`$ = 10 h: chance of fewer than 689 blocks in $`K`$ | Floor at $`10^{-9}`$ | $`K`$ = 18 h: chance of fewer than 1,291 | Floor at $`10^{-9}`$ |
| --- | --- | --- | --- | --- |
| premise of Finality Floor, $`r = 1`$ | $`9.8 \cdot 10^{-10}`$ | 689 | $`9.9 \cdot 10^{-10}`$ | 1,291 |
| fixed point, no noise | $`5.6 \cdot 10^{-9}`$ | 683 | $`1.0 \cdot 10^{-8}`$ | 1,281 |
| 108 h | $`1.4 \cdot 10^{-8}`$ | 680 | $`4.7 \cdot 10^{-8}`$ | 1,273 |
| 54 h | $`3.2 \cdot 10^{-8}`$ | 677 | $`1.7 \cdot 10^{-7}`$ | 1,266 |
| 36 h | $`6.6 \cdot 10^{-8}`$ | 674 | $`4.7 \cdot 10^{-7}`$ | 1,259 |
| 18 h | $`3.9 \cdot 10^{-7}`$ | 666 | $`4.8 \cdot 10^{-6}`$ | 1,242 |
| 10 h | $`3.0 \cdot 10^{-6}`$ | 655 | $`4.8 \cdot 10^{-5}`$ | 1,218 |

- The row "premise" repeats RFC-533 125 and RFC-532 155: $`9.8 \cdot 10^{-10}`$ and 689, $`9.9 \cdot 10^{-10}`$ and 1,291. The row "fixed point" repeats RFC-533 144 and RFC-532 174: $`5.6 \cdot 10^{-9}`$ and 683, $`10^{-8}`$ and 1,281. (Cited.)
- With today's window the noise raises the chance from $`5.6 \cdot 10^{-9}`$ to $`1.4 \cdot 10^{-8}`$ at 10 hours. A floor derived with the noise would be 680.
- If the rule computed with $`f`$ exactly, the values at 108 hours would be $`2.7 \cdot 10^{-9}`$ and 685 at 10 hours, and $`5.8 \cdot 10^{-9}`$ and 1,283 at 18 (lines 37 and 50).
- Missing the floor delays finality past $`K`$. It does not make a block immutable early (Cited: RFC-533 131).

**7.7 (Computed). What the noise costs the window $`K`$.** RFC-533 states that at 15 s, 10 hours holds 30 % while the true active stake stays within 1.094 times the inferred stake. RFC-532 gives 1.593 at 18 hours (Cited: RFC-533 61, RFC-532 74). One step of the rule from its fixed point exceeds the limit when $`N < r^* P \hat f / 1.094`$. Its chance per epoch (`out_06_inference.txt`, lines 62–69):

| Window | 108 h | 72 h | 54 h | 36 h | 27 h | 18 h | 14.2 h | 10 h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| above 1.094 | $`3.8 \cdot 10^{-29}`$ | $`4.8 \cdot 10^{-20}`$ | $`1.7 \cdot 10^{-15}`$ | $`6.3 \cdot 10^{-11}`$ | $`1.3 \cdot 10^{-8}`$ | $`2.7 \cdot 10^{-6}`$ | $`2.8 \cdot 10^{-5}`$ | $`3.4 \cdot 10^{-4}`$ |
| above 1.593 | $`10^{-478}`$ | $`5 \cdot 10^{-320}`$ | $`2 \cdot 10^{-240}`$ | $`4 \cdot 10^{-161}`$ | $`2 \cdot 10^{-121}`$ | $`10^{-81}`$ | $`8 \cdot 10^{-65}`$ | $`3 \cdot 10^{-46}`$ |

At $`K`$ = 10 hours a window of 36 hours keeps the chance at $`6.3 \cdot 10^{-11}`$ per epoch, and a window of 27 hours gives $`1.3 \cdot 10^{-8}`$. At $`K`$ = 18 hours the chance stays below $`10^{-45}`$ at every length shown.

**7.8 (Computed). The price of a deflation.** A coalition deflates the inference by withholding every block for one observation window (Cited: RFC-533 57). It gives up its wins of the window, $`(1 - (1-f)^{0.3})\,P`$: 3,934 at 108 hours, 1,967 at 54 hours, 656 at 18 hours and 364 at 10 hours (`out_06_inference.txt`, lines 72–79). The price is proportional to the window.

## 8. Ouroboros Genesis: what its proof needs of the schedule, and what holds

**8.1 (Cited). The theorem.** Theorem 2 of the paper (section 4.3) considers the protocol with the chain selection rule `maxvalid-bg`, in the setting with static $`\mathcal{F}_\text{N-MC}`$-registration, where every honest party is online from the start. It assumes the conditions of Theorem 1 and

$$
k > 192\Delta/(\epsilon\beta), \qquad R/6 \ge s = k/(4f) \ge 48\Delta/(\epsilon\beta f).
$$

It concludes that the guarantees of Theorem 1 for common prefix, chain growth, chain quality and existential chain quality still hold, except for an additional error that it states. Theorem 1 (section 4.2) assumes $`\alpha(1-f)^{\Delta+1} \ge (1+\epsilon)/2`$ for some $`\epsilon \in (0,1)`$ and $`R \ge 144\Delta/(\epsilon\beta f)`$. Here $`R`$ is the epoch length, $`s`$ the density window, $`\alpha`$ the alert ratio and $`\beta`$ the participating ratio.

**8.2 (Cited). The paper's schedule.** In the paper the stake distribution of epoch $`ep`$ is that at the end of epoch $`ep - 2`$, and the nonce of epoch $`ep`$ hashes values from the blocks of the first $`2R/3`$ slots of epoch $`ep - 1`$ (Figure 8). The proof sketch of Theorem 7 (Appendix E) gives each third of the epoch a task: agreement on the stake distribution, at least one honest block, and agreement on the randomness. It adds that this derivation still allows grinding by a leader who chooses whether to include a block, and bounds it by the number of random-oracle queries.

**8.3 (Assumed: a reading of the proof of Theorem 2, not a statement of the paper).** The proof compares two chains over two windows of $`s`$ slots that follow their last common block: one for the growth of the local chain, one for an honest block that follows. It uses two facts about these windows.

- (R1) Both windows lie between the last common block and the slot at which the chains are compared. The paper derives this from the depth of the fork: $`k`$ blocks span at least $`k/(2f) = 2s`$ slots.
- (R2) Both chains draw their leaders from one stake distribution and one nonce over both windows. The paper's words are: "since 2s ≤ R/3, the chains … use the same stake distribution and randomness". $`R/3`$ is the span from the end of the nonce's inputs to the next epoch (8.2).

So the hypothesis $`R/6 \ge s`$ of the theorem is $`2s \le R/3`$. In the proof it is a condition on that span, not on the epoch as a whole.

**8.4 (Proved). The two facts for the specification's rules.**

(a) The Bootstrap rule compares two chains by density only when $`sl_\text{div} + K \le sl_\text{top}`$, where $`sl_\text{div}`$ is the slot of their divergence block and $`sl_\text{top}`$ the later of the two tips' slots (Cited: fork choice 124–137). If $`2s_{gen} \le K`$, both windows $`(sl_\text{div}, sl_\text{div} + s_{gen}]`$ and $`(sl_\text{div} + s_{gen}, sl_\text{div} + 2s_{gen}]`$ lie within $`(sl_\text{div}, sl_\text{top}]`$ in every such comparison. If $`2s_{gen} > K`$, they do not when $`sl_\text{top} = sl_\text{div} + K`$.

(b) Let two chains share exactly the blocks up to a divergence block $`A`$. Let the gap be $`G`$ and the epoch $`E`$, with $`2s_{gen} \le E`$. If $`2s_{gen} \le G + 1`$, then for every slot $`t`$ in $`(sl_A, sl_A + 2s_{gen}]`$ both chains derive the epoch state of $`t`$ from blocks they share. If $`2s_{gen} \ge G + 2`$, there are two such chains and a slot $`t`$ of their two windows for which they read blocks they do not share.

*Proof.* (a) The second window ends at $`sl_\text{div} + 2s_{gen} \le sl_\text{div} + K \le sl_\text{top}`$.
(b) Let $`A`$ lie in epoch $`e`$, and let $`c_e`$ be the cut-off of epoch $`e`$, so that epoch $`e + 1`$ starts at $`c_e + G`$. By 4.3 the state of epoch $`e`$ reads blocks with slots below the cut-off of epoch $`e - 1`$. That cut-off is before the first slot of epoch $`e`$, hence at or before $`sl_A`$. So both chains share the state of epoch $`e`$. The state of epoch $`e + 1`$ reads blocks with slots below $`c_e`$.
Case $`sl_A \ge c_e - 1`$. The blocks that the chains do not share have slots above $`sl_A`$, hence at least $`c_e`$. So the chains share the state of epoch $`e + 1`$ too. Every $`t`$ in the two windows lies in epoch $`e`$ or $`e + 1`$, because $`sl_A + 2s_{gen} < c_e + G + E`$.
Case $`sl_A \le c_e - 2`$. Every $`t`$ in the two windows is at most $`c_e - 2 + 2s_{gen} \le c_e + G - 1`$. So $`t`$ lies in epoch $`e`$.
Conversely, let $`2s_{gen} \ge G + 2`$. Then $`E - G \ge 2`$, because $`2s_{gen} \le E`$, so slot $`c_e - 2`$ lies in epoch $`e`$. Let $`sl_A = c_e - 2`$, and let one of the chains hold a block in slot $`c_e - 1`$. The slot $`sl_A + 2s_{gen} \ge c_e + G`$ lies in epoch $`e + 1`$. Its state reads that block, which the chains do not share. ∎

`s07_genesis.py` confirms (b) by enumeration for 434 pairs $`(E, G)`$: the property holds for every divergence slot exactly when $`2s \le G + 1`$ (`out_07_genesis.txt`, lines 45–46). (Computed.)

For the specification: $`2s_{gen}`$ = 32,400 slots. $`K - 2s_{gen}`$ is 3,600 slots at 10 hours and 32,400 at 18. The gap is 259,200 slots, 16 times $`s_{gen}`$ (`out_07_genesis.txt`, lines 49–53). (Computed.) The specification states $`2s_{gen} \le K`$ as a rule (Cited: fork choice 80, protocol 104). It states no rule on the gap. Any gap of at least $`K`$ meets (b), because $`K \ge 2s_{gen}`$.

**8.5 (Computed). The theorem's hypotheses at the specification's parameters.** Take a coalition of share $`a`$ and all of the honest stake online, so $`\alpha = 1 - a`$ and $`\beta = 1`$. The largest $`\epsilon`$ that Theorem 1 allows is $`2(1-a)(1-f)^{\Delta+1} - 1`$. With $`k`$ = 2,160 and $`f`$ = 1/30 (`out_07_genesis.txt`, lines 5–22 and 26–43):

- the hypotheses of 8.1 hold for $`\Delta \le 2`$ slots, for 30 % and for a third;
- at $`\Delta = 3`$ they need $`k > 2{,}589`$ for 30 % and $`k > 3{,}507`$ for a third;
- for $`\Delta \ge 9`$ at 30 %, and $`\Delta \ge 8`$ at a third, the first condition of Theorem 1 has no $`\epsilon`$ at all.

So the theorem does not cover the specification's $`\Delta`$ = 10 slots or $`T_M`$ = 15 slots.

**8.6 (Proved, GENESIS 2.4, 6.2 to 8.1 and 9.1; Computed, GENESIS 6.2 to 10.4; Assumed, GENESIS 3). The conclusion of Theorem 2 at the specification's parameters.** The conclusion does not follow from the paper (8.5). GENESIS gives an argument of its own for a node that bootstraps under the Bootstrap rule. Its target is that the node holds, when it switches to the Online rule, a chain at least as long as the honest chain that left it less than $`K`$ slots before its own tip. Then `commit` fixes only blocks of the honest chain (Proved, GENESIS 2.4). A divergence slot is the slot of the last block that a fork shares with the chain it is compared with. The figures are for a coalition of 30 %.

- The reduction. While the Online rule keeps its own guarantee, the node misses the target only if a fork is at least as dense as a dominant chain in the $`s_{gen}`$ slots after a divergence slot of its history, or two dominant chains differ on a slot $`K - 1`$ or more slots before the switch, or honest stake wins no slot for nearly $`K`$ slots. This needs $`s_{gen} \le K - 1`$ and $`2K \le G + 1`$, that is a phase 3 of at least $`2K - 1`$ slots (10.1), and not $`2s_{gen} \le K`$. (Proved, GENESIS 7.1.)
- Long-range forks, with no honest block in the window, meet $`10^{-9}`$ per divergence slot. The bound is $`2.1\cdot10^{-13}`$ at 10 s and $`2.6\cdot10^{-10}`$ at 15 s. In every state of the $`K`$ row it is at most $`9.0\cdot10^{-10}`$. (Proved, GENESIS 6.2. Computed, GENESIS 6.2 and 10.4. Assumed, 5.9.) Over a year of history at 10 s the bound is $`3.1\cdot10^{-8}`$. (Computed, GENESIS 8.2.)
- Every fork. The bound per divergence slot is the finality study's settlement bound at a wait of $`s_{gen} - 1`$ slots, plus terms that are negligible at $`s_{gen}`$: $`1.35\cdot10^{-7}`$ at 10 s and $`4.3\cdot10^{-5}`$ at 15 s. It does not meet $`10^{-9}`$. (Proved, GENESIS 6.3. Computed, GENESIS 6.3.)
- The window it would need is 21,336 slots at 10 s and 33,729 slots at 15 s per divergence slot, and 33,181 and 51,560 slots over a year of history. (Computed, GENESIS 6.3 and 8.2.) At $`K`$ = 64,800 all four fit. At $`K`$ = 36,000 the two at 10 s fit. At 15 s no window meets $`10^{-9}`$ at $`K`$ = 36,000 by these bounds. The settlement bound meets it per divergence slot only from 33,729 slots. From there on, the smaller of the two bounds for the case in which the dominant chain has no honest block after the window is the finality study's settlement bound at a delay of 16 slots and a wait of $`K - 1`$ slots, $`2.1\cdot10^{-9}`$ for all divergence slots together. (Computed, GENESIS 6.3, 7.2 and 8.2.)
- The bound for every fork rests on GENESIS's A6. Two dominant chains that share no block from some slot on make the margin of Gaži, Ren and Russell for that slot non-negative. This follows from their Definitions 4 and 11, with both chains taken to end one slot before the comparison, which costs one slot. That the finality study's settlement bound covers the margin at every slot is the study's construction, not their statement, and GENESIS does not check it. (Assumed, GENESIS 3, A6. Cited, GENESIS 3, A6.)
- An attack that splits the honest nodes for the whole window leaves a fork that wins the density comparison, in the model of Gaži, Ren and Russell, where ties are broken for the coalition. (Proved, GENESIS 6.4.) The finality study's figures put its chance at about $`4.7\cdot10^{-11}`$ at 10 s and $`3.0\cdot10^{-8}`$ at 15 s per divergence slot. These are estimates, not bounds. They lie 2,900 and 1,500 times below the bound for every fork. (Cited, GENESIS 6.4.)
- Posterior corruption is not prevented, because leadership keys do not evolve. Whoever later holds the key of a note can sign the slots that note wins on any fork where it is unspent. On a fork from a divergence slot the tickets are those of the honest chain, so an acquired note wins exactly the slots it won as an honest note. Keys of a further 4.8 % of the window's stake lift the long-range bound above $`10^{-9}`$ at 10 s. With acquired wins independent of the honest ones it would be 3.9 %. (Cited, GENESIS 4.5. Proved, GENESIS 9.1. Computed, GENESIS 9.2.)
- Every bound holds in GENESIS's model: independent tickets, an unbiased nonce, delivery within the delay, the Online rule's guarantee up to the switch, and keys of at most 30 % of each epoch's stake in the coalition's hands, which the specification does not enforce. (Assumed, GENESIS 3.)

## 9. The buffer

**9.1 (Cited).** The Buffer phase is there to ensure that at least one honest leader contributes to the epoch nonce after the stake distribution is finalized (protocol 154). The paper gives the second third of its epoch the same task and proves it from existential chain quality (8.2).

**9.2 (Proved). A necessary span.** A span that holds an honest block must hold a slot won by honest stake. Take the lottery model of 5.2 (M1 and M4), with the honest stake that is online as the stake that builds, a share $`x`$ of $`D`$. The slots are independent, and honest stake wins each with chance $`1 - (1-f)^x`$. So the chance that honest stake wins no slot of a span of $`w`$ slots is $`(1-f)^{xw}`$. It is at most $`10^{-9}`$ only if $`w \ge 611.28/x`$ slots. With a coalition of share $`a`$ and $`D`$ equal to the total active stake, $`x = 1 - a`$, and at $`a`$ = 0.3 that is 874 slots (`out_08_buffer.txt`, line 3). Over the states of 5.9 the largest value is 903 slots, with a tenth of the honest stake offline. It is 971 slots if that state is read before the inference corrects (`out_14_bracket.txt`, lines 9 and 12).

**9.3 (Proved). A reduction.** Assume that there is a *final chain*: a chain of which every block is in time immutable at every honest node. (Assumed.) Call a block honest when its leader built it on its own $`c_{loc}`$ at its slot. Suppose that the final chain holds no honest block with a slot in $`(a, a + w]`$. Let $`H_0`$ be its last honest block with a slot of at most $`a`$, and $`H_1`$ its first honest block with a slot above $`a + w`$, if any. Then:

1. every block of the final chain between $`H_0`$ and $`H_1`$ is the coalition's;
2. the leader of $`H_1`$ held, at a slot above $`a + w`$, a local chain that ends with those blocks.

So a branch that leaves the honest blocks at $`H_0`$, and holds none after it, was the local chain of an honest node more than $`w`$ slots after the slot of $`H_0`$. Let $`\mathrm{survival}(T)`$ bound the chance of that for a span of $`T`$ slots, whatever $`H_0`$ is, and let $`h`$ be the chance that honest stake wins a given slot. Then

$$
\Pr[\text{the final chain holds no honest block of } (a, a + w]] \le h \sum_{t \ge 0} \mathrm{survival}(w + t).
$$

*Proof.* (1) A block between them with a slot of at most $`a`$ is not honest by the choice of $`H_0`$. One with a slot in $`(a, a+w]`$ is not honest by the hypothesis. One with a later slot is not honest by the choice of $`H_1`$. (2) $`H_1`$ is honest, so its leader built it on its local chain, which is the final chain up to the parent of $`H_1`$. If there is no $`H_1`$, the branch is held from then on. The bound is the union over the slot $`a - t`$ of $`H_0`$: that slot is won by honest stake with chance at most $`h`$, and the branch then lasts at least $`w + t`$ slots. ∎

**9.4 (Proved, SURVIVAL 6.1 and 8.1; Computed; Assumed, SURVIVAL A1 to A5).** The law of 9.3 is proved in SURVIVAL. Fix a slot $`s_0`$ and $`T \ge d`$. The chance that slot $`s_0`$ holds an honest block $`H_0`$ and that some honest node holds, at some slot of at least $`s_0 + T`$, a local chain whose blocks after $`H_0`$ are all the coalition's, is at most $`h\,\hat Q(T)`$ (Proved, SURVIVAL 6.1). $`\hat Q(T)`$ is the chance of an event of the lottery alone. A recursion over slots computes it from above and from below (Proved, SURVIVAL 6.3 to 6.7). So $`\mathrm{survival} = \hat Q`$ in 9.3, and $`w_B`$ is the least $`w`$ with $`h \sum_{t \ge 0} \hat Q(w + t) \le 10^{-9}`$ (Proved, SURVIVAL 8.1). In each state the chance $`h`$ is $`1 - (1-f)^x`$, with the building share $`x`$ of 5.9.

The theorem holds in a model with five assumptions (Assumed, SURVIVAL 2). A1: the ticket hash acts as a random oracle, and the nonce is fixed and unbiased. A2: the shares of $`D`$ do not change during the period. A3: every honest block reaches every honest node, with its chain, within $`d`$ slots. A4: the honest nodes run the Online rule. A5: every honest block, and every block of its chain, that reaches an honest node descends from that node's $`B_\text{imm}`$ or is $`B_\text{imm}`$. A5 is the guarantee that sizes $`K`$.

`s08_buffer.py` reads $`w_B`$ from SURVIVAL's output, and computes it for a third with SURVIVAL's code (`out_08_buffer.txt`, lines 139–150).

| State, coalition of 30 % | $`w_B`$ | The finality study's law | Line |
| --- | --- | --- | --- |
| no disturbance, 10 s | 12,295 slots, 3.42 h | 12,242 slots | 140 |
| every honest block 15 s late | 16,644 slots, 4.62 h | 16,579 slots | 141 |
| a tenth of the honest stake offline, 10 s | 17,268 slots, 4.80 h | 17,215 slots | 142 |
| deflated inference, 10 s | 11,171 slots, 3.10 h | 11,126 slots | 143 |
| 15 s and a tenth offline | 24,713 slots, 6.86 h | 24,645 slots | 144 |
| 15 s and a deflated inference | 18,142 slots, 5.04 h | 18,081 slots | 145 |
| a tenth offline and a deflated inference, 10 s | 16,497 slots, 4.58 h | 16,452 slots | 146 |
| a tenth offline before the inference corrects, 10 s | 17,709 slots, 4.92 h | 17,654 slots | 149 |
| 15 s and a tenth offline before the inference corrects | 24,540 slots, 6.82 h | 24,471 slots | 150 |

- For a coalition of a third, $`w_B`$ is 5.75 hours at 10 s and 8.51 hours at 15 s (lines 147–148).
- The finality study's law `branch_survival` (module `formation`, lines 390–405) is not an upper bound. $`\hat Q`$ exceeds it by a factor of 1.062 to 1.102 at every whole hour from 1 to 6 in every state, that is by 6 to 10 %. (Computed, SURVIVAL 9.4.) The law counts an honest block when it is made, not when every honest node must hold it, and it does not count a branch that an honest node keeps on a tie. (Proved, SURVIVAL 9.2.)
- An adversary attains $`\hat Q`$ up to a factor of $`1 - 5.43\cdot10^{-4}`$ and a term below $`4.0\cdot10^{-15}`$, in an instance with many honest nodes. (Proved, SURVIVAL 9.3. Computed, SURVIVAL 9.4.)
- With the proved law every $`w_B`$ is 45 to 69 slots longer than with the study's law (lines 140–150).

So in every state of the latest #533 the buffer needs at least 903 slots (9.2), and 4.80 hours suffice (9.4).

## 10. The least epoch

**10.1 The rules a schedule keeps.** (Cited, with one standard that is Assumed.)

- S. Phase 1 waits for the snapshot to finalize (protocol 153, 157).
- B. Phase 2 follows, so that at least one honest leader contributes to the nonce after that (protocol 154).
- L. Phase 3 waits for $`\eta`$ and $`D`$ to finalize. They are used from the first slot of the next epoch (protocol 155, 157).
- I. The observation window is the first `PERIOD` slots of the epoch and ends at the cut-off (protocol 237, inference 55).
- Bounds on $`K`$ that do not read the epoch: $`K > W \cdot f^{-1}`$, $`K > T_\text{offline}`$, $`K \ge 2s_{gen}`$ (protocol 104, 109; bootstrap 110; fork choice 80).
- J. The Bootstrap rule keeps a joining node on the honest chain (bootstrap 36). The only argument for it here is that of 8.6. That argument needs a phase 3 of at least $`2K - 1`$ slots and $`s_{gen} \le K - 1`$ (Cited: GENESIS 7.1 and 7.3). A schedule meets J when it meets both conditions. Whether the condition on phase 3 is necessary is not shown.

**(Assumed, A10.)** The specification sets no standard for "in time". RFC-532 says that what a node does when a value is not final at the end of its phase is specified under neither rule (Cited: line 308). This review takes the standard by which $`K`$ and $`\phi`$ are sized: a rule is kept when it fails with a chance of at most $`\varepsilon = 10^{-9}`$, at a building share $`x`$ and a delay $`d`$.

**10.2 (Proved). Bounds on the least epoch.** Let the phases have $`L_1`$, $`L_2`$, $`L_3`$ slots and the window $`P`$ slots. Under A10, in a state of 5.9 with building share $`x`$ and delay $`d`$:

1. S and L are kept if $`L_1 \ge G^*(x, d)`$ and $`L_3 \ge G^*(x, d)`$, by 5.4. They are not kept if $`L_1`$ or $`L_3`$ is below the necessary value of 5.5.
2. B is kept if $`L_2 \ge w_B`$, by 9.3 with the law of 9.4. It is not kept if $`L_2 < 611.28/x`$, by 9.2.
3. I needs $`P \le L_1 + L_2`$.
4. J is met if $`L_3 \ge 2K - 1`$, because $`s_{gen}`$ = 16,200 is at most $`K - 1`$ at both values of $`K`$. Nothing here shows that the Bootstrap rule fails when $`L_3 < 2K - 1`$.

Over the states that the $`K`$ row requires, let $`G^*`$ and $`w_B`$ be the largest values of 5.9 and 9.4. Let $`G_\text{nec}`$ be the largest necessary value of 5.5, and $`w_\text{nec}`$ the largest necessary span of 9.2. Then an epoch of

$$
E_\text{suf} = \max\big(P,\ G^* + w_B\big) + \max\big(G^*,\ 2K - 1\big)
$$

keeps S, B, L and I in every such state, and meets J. No epoch shorter than

$$
E_\text{nec} = \max\big(P,\ G_\text{nec} + w_\text{nec}\big) + G_\text{nec}
$$

keeps S, B, L and I. The least epoch that keeps S, B, L and I and meets J lies between them. $`G_\text{nec}`$ is the value of 5.5 (1) when every win is counted, and the larger value of 5.5 (2) when only blocks of the chain count. When the window is shortened to phases 1 and 2, $`P`$ drops out of both.

The condition $`L_3 \ge 2K - 1`$ enters $`E_\text{suf}`$ and not $`E_\text{nec}`$. It is a condition of the only argument for J that this review has. It is not a proven necessity.

$`E_\text{suf}`$ also has $`K \le L_1`$ and $`K \le L_3`$ (4.6), a gap of at least $`2s_{gen}`$ (8.4), and $`E \ge 2K`$, so that a race of $`K`$ slots meets at most two nonces (6.2).

*Proof.* Lines 1 to 3 restate the statements they name, with the read slot and the use slot of 4.2 for the phase. The bounds of 5.4, 5.5, 9.2 and 9.3 do not grow when the span grows. Line 4 restates J (10.1): the gap $`G`$ of GENESIS is phase 3 (1.2, 4.2), and GENESIS 7.1 and 7.3 hold for every gap with $`2K \le G + 1`$ when $`s_{gen} \le K - 1`$.

Upper side. Phases of $`G^*`$, $`w_B`$ and $`\max(G^*, 2K - 1)`$ slots meet the sufficient conditions of 1, 2 and 4 in every state. A longer phase 1 or 2 still meets them, so phases 1 and 2 can be lengthened to hold a window of $`P`$ slots, as 3 requires. The sum is $`E_\text{suf}`$.

Lower side. A schedule that keeps S, B, L and I in every state has $`L_1 \ge G_\text{nec}`$, $`L_3 \ge G_\text{nec}`$ and $`L_2 \ge w_\text{nec}`$ by 1 and 2, and $`L_1 + L_2 \ge P`$ by 3. So $`L_1 + L_2 + L_3 \ge E_\text{nec}`$.

Last, the bound of 5.4 is at least the chance it bounds, so $`G^* \ge K - 1 + 611.28/x > K`$ by 5.5 (3). And $`K \ge 2s_{gen}`$ by the rule on $`K`$. ∎

**10.3 (Computed). The values.** The epochs that suffice, $`E_\text{suf}`$: `out_09_epoch.txt`, lines 4–8, 17–18, 33–37 and 49–50. Phase 3 is $`\max(G^*, 2K - 1)`$: at least 71,999 slots (20.00 h) at $`K`$ = 36,000 and 129,599 slots (36.00 h) at 64,800 (lines 2 and 31).

| Case | $`G^*`$ | $`w_B`$ | Phase 3 | Epoch that suffices, window shortened to $`G^* + w_B`$ | Epoch that suffices, window kept at 108 h |
| --- | --- | --- | --- | --- | --- |
| latest #533, every state of the $`K`$ row | 13.03 h | 4.80 h | 20.00 h | 136,177 slots, 37.83 h | 460,799 slots, 128.00 h |
| latest #533, all of the inferred stake builds, 15 s | 10.20 h | 4.62 h | 20.00 h | 34.83 h | 128.00 h |
| latest #533, a half builds, 15 s | 17.05 h | 4.62 h | 20.00 h | 41.68 h | 128.00 h |
| latest #533, a quarter builds, 15 s | 31.14 h | 4.62 h | 31.14 h | 66.90 h | 139.14 h |
| base, every state of its $`K`$ row | 23.94 h | 6.86 h | 36.00 h | 240,499 slots, 66.81 h | 518,399 slots, 144.00 h |
| base, all of the inferred stake builds, 15 s | 18.20 h | 4.62 h | 36.00 h | 58.83 h | 144.00 h |

The bounds of 10.2 over every state of the $`K`$ row, $`E_\text{nec}`$ and $`E_\text{suf}`$ (`out_14_bracket.txt`, lines 28 to 39):

| Case | Window shortened: no shorter epoch keeps the rules, every win counted; chain blocks only | Window shortened: suffices | Window kept: no shorter epoch keeps the rules, every win counted; chain blocks only | Window kept: suffices |
| --- | --- | --- | --- | --- |
| latest #533 | 76,339 slots, 21.21 h; 94,691 slots, 26.30 h | 136,177 slots, 37.83 h | 426,518 slots, 118.48 h; 435,694 slots, 121.03 h | 460,799 slots, 128.00 h |
| latest #533, a tenth offline read before the inference corrects | 82,033 slots, 22.79 h; 95,915 slots, 26.64 h | 137,191 slots, 38.11 h | 429,331 slots, 119.26 h; 436,272 slots, 121.19 h | 460,799 slots, 128.00 h |
| base | 134,421 slots, 37.34 h; 173,245 slots, 48.12 h | 240,499 slots, 66.81 h | 455,559 slots, 126.54 h; 474,971 slots, 131.94 h | 518,399 slots, 144.00 h |
| base, a tenth offline read before the inference corrects | 144,441 slots, 40.12 h; 183,273 slots, 50.91 h | 245,306 slots, 68.14 h | 460,535 slots, 127.93 h; 479,951 slots, 133.32 h | 518,399 slots, 144.00 h |

- "Every state of the $`K`$ row" takes the largest values over the states that the row requires: one disturbance at a time for the latest #533, two together for the base. The upper side takes $`G^*`$ from 5.9, $`w_B`$ from 9.4, and phase 3 at $`\max(G^*, 2K - 1)`$. The lower side takes the necessary values of 5.9 and 9.2. For the latest #533 these are 37,718 slots with every win counted, 46,894 with chain blocks only, and 903 slots for the buffer.
- The lower side rests neither on the survival law of 9.4 nor on J. When only blocks of the chain count and the window is kept, it is 121.03 hours. The upper side is 128.00 hours, because J sets phase 3.
- In every row but "a quarter builds", J sets phase 3. Over the $`K`$ row it adds $`2K - 1 - G^*`$ slots to the epoch: 25,089 slots (6.97 h) for the latest #533, and 43,412 slots (12.06 h) for the base (`out_14_bracket.txt`, lines 28 and 34).
- A second computation, with the binomial tails summed in log space, gives the same necessary values and the same $`G^*`$ in every state (`out_14_bracket.txt`, lines 50–65).
- Every epoch that suffices is at least 34.83 hours, above $`6s_{gen}`$ = 27 hours, the bound $`R \ge 6s`$ of Theorem 2 as written (8.1) (`out_09_epoch.txt`, lines 4 and 19). A phase 3 of $`2K - 1`$ slots also meets the proof's use of that bound (8.4), because $`K \ge 2s_{gen}`$.
- With the window kept, phases 1 and 2 stay at 108 hours together, and only phase 3 shrinks, to 20.00 hours.
- For a node's own draw of the lottery at the use slot, each waiting phase needs $`d`$ more slots (5.10): 46,925 slots for phase 1. Phase 3 stays at $`2K - 1`$ slots, and the epoch is 136,192 slots (37.83 h) (`out_14_bracket.txt`, line 42).
- The bounds of 8.6 were computed at today's phase 3 of 259,200 slots, which one of their terms reads. At a phase 3 of $`2K - 1`$ slots, against 30 %, every bound and window that 8.6 gives stays the same at both values of $`K`$ but one. At $`K`$ = 36,000 and 15 s no window over a year meets $`10^{-9}`$ even from the cells alone, where today's phase 3 gives 51,560 slots. 8.6 finds no window at that $`K`$ and delay in either case. (`out_14_bracket.txt`, lines 67–76.)

**10.4 (Computed). What each schedule costs.** `out_09_epoch.txt`, lines 22–28, for the latest #533. Each row is a schedule. The columns are defined below the table. Every schedule of the table gives phase 3 at least $`2K - 1`$ slots and meets J (the last column of the output).

| Schedule (phases, hours) | Epoch | Window | Least share, phase 1 and phase 3 | Two nonces | Noise of $`D`$ | Fewer than 689 blocks in $`K`$ | Noise past 1.094 | No correction for | New stake waits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| today: 54 + 54 + 72 | 180 h | 108 h | 13.80 %, 10.20 % | 5.56 % | 0.868 % | $`1.4 \cdot 10^{-8}`$ | $`3.8 \cdot 10^{-29}`$ | 252 h | 180 to 360 h |
| phase 3 at the value that suffices: 54 + 54 + 20.00 | 128.00 h | 108 h | 13.80 %, 41.35 % | 7.81 % | 0.868 % | $`1.4 \cdot 10^{-8}`$ | $`3.8 \cdot 10^{-29}`$ | 148 h | 128 to 256 h |
| $`3K`$, $`3K`$, $`4K`$: 30 + 30 + 40 | 100 h | 60 h | 26.05 %, 19.02 % | 10.00 % | 1.165 % | $`2.7 \cdot 10^{-8}`$ | $`5.2 \cdot 10^{-17}`$ | 140 h | 100 to 200 h |
| halved: 27 + 27 + 36 | 90 h | 54 h | 29.30 %, 21.32 % | 11.11 % | 1.228 % | $`3.2 \cdot 10^{-8}`$ | $`1.7 \cdot 10^{-15}`$ | 126 h | 90 to 180 h |
| a third: 18 + 18 + 24 | 60 h | 36 h | 46.85 %, 33.48 % | 16.67 % | 1.504 % | $`6.6 \cdot 10^{-8}`$ | $`6.3 \cdot 10^{-11}`$ | 84 h | 60 to 120 h |
| every phase at the value that suffices: 13.03 + 4.80 + 20.00 | 37.83 h | 17.83 h | 70 %, 41.35 % | 26.44 % | 2.137 % | $`4.0 \cdot 10^{-7}`$ | $`3.1 \cdot 10^{-6}`$ | 58 h | 38 to 76 h |
| the same with all of the stake building: 10.20 + 4.62 + 20.00 | 34.83 h | 14.83 h | 99.98 %, 41.35 % | 28.71 % | 2.343 % | $`7.3 \cdot 10^{-7}`$ | $`1.8 \cdot 10^{-5}`$ | 55 h | 35 to 70 h |

- "Least share": the least building share at which 5.4 certifies the value of phase 1, and of phase 3, final in time but for $`10^{-9}`$, at 15 s.
- "Two nonces": the share of targets whose race of $`K`$ slots meets two nonces (6.2).
- "Noise of $`D`$": the standard deviation of 7.4 (3) at the window.
- "Fewer than 689 blocks in $`K`$": the chance of 7.6 at the window.
- "Noise past 1.094": the chance per epoch of 7.7 at the window.
- "No correction for": the longest time for which a change of the active stake leaves $`D`$ untouched, $`E + L_3`$. A change just after a cut-off is first counted in the next epoch's window, and the $`D`$ computed from that window is first used at the start of the epoch after it, $`L_3 + E`$ slots after the change. (Proved from 4.1.)
- "New stake waits": from a note's creation to the first slot in which it may lead. A note may lead once it was in the note set at the beginning of the previous epoch (Cited: protocol 173), so it waits between $`E`$ and $`2E`$. (Proved from that rule.)

For the base, the same rows are in `out_09_epoch.txt`, lines 54–59. There the schedule at a third has a phase 3 of 24 hours, below the 36.00 hours of J (line 57).

**10.5 (Cited). Other readers of the epoch.** These texts read the epoch's length or its boundaries. A schedule that changes the length changes each of them.

- Blend defines its epoch as 648,000 slots and derives 21,600 blocks from it (`blend-protocol.md` 115, 476, 669–672).
- The service declaration protocol reads the registry at the last block of epoch $`n - 2`$ at the start of epoch $`n`$, and takes that epoch as finalized (`bedrock-service-declaration-protocol.md` 71, 131–132). This needs $`E \ge G^*`$, which every schedule of 10.4 meets. (Proved from that reading.)
- Proof of work credits its reward pool at each epoch boundary, takes the expected blocks per epoch from the epoch's length, and computes a difficulty at the cut-off of epoch $`N - 1`$ from the blocks of epoch $`N - 2`$ (`proof-of-work.md` 113, 126, 180, 215).
- Leader rewards add the vouchers of an epoch to the voucher tree in the first block of the next epoch, to guarantee a minimal anonymity set (`bedrock-anonymous-leaders-reward.md` 38). The set is the blocks of an epoch: 21,600 at 180 hours and 4,539 at 37.83 hours (`out_09_epoch.txt`, lines 22 and 27).
- The storage market bounds a price change at 12.5 % between two epochs (`storage-markets.md` 128).
- The block rewards document takes an epoch of 7.5 days (`block-rewards.md` 141).

**10.6 (Computed). What a shorter epoch gives a coalition that chooses among nonces.** RFC-532 gives the gain of a coalition of 30 % that keeps, at each cut-off, the nonce that gives it the most slots: 0.70 % more blocks at 10 s and 0.82 % at 15 s, with at most $`2^{16}`$ nonces (Cited: line 105). `s11_gain.py` repeats that computation with the study's sampler and changes only the number of slots of the epoch (`out_11_gain.txt`, lines 5–11 and 15–21). It returns the published figures at 648,000 slots.

| Epoch | 180 h | 128.00 h | 100 h | 90 h | 60 h | 37.83 h | 34.83 h |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gain at 10 s | 0.70 % | 0.83 % | 0.94 % | 0.99 % | 1.21 % | 1.53 % | 1.59 % |
| gain at 15 s | 0.82 % | 0.97 % | 1.10 % | 1.16 % | 1.43 % | 1.80 % | 1.87 % |
| extra blocks a year at 10 s | 2,230 | 2,646 | 2,995 | 3,157 | 3,870 | 4,880 | 5,087 |

The gain follows $`0.70\,\% \cdot \sqrt{180\,\text{h}/E}`$ at 10 s, and $`0.82\,\% \cdot \sqrt{180\,\text{h}/E}`$ at 15 s, to within 0.02 points (the last column of the output). Two assumptions are not derived here: that the number of nonces a coalition holds at a cut-off does not depend on the epoch's length, and that the bound behind RFC-533's shares with today's nonce does not depend on the gap while the cut-off is final at first use. (Assumed.)

## 11. What bounds the epoch, what shortening takes, and what it costs

### 11.1 What bounds each span from below

| Span | Rule | Exact bound | For a chance of $`10^{-9}`$, latest #533 | Today |
| --- | --- | --- | --- | --- |
| phase 1 | S | at least $`K`$; at $`K`$ only if two given slots hold blocks (Proved, 4.6) | 10.17 to 10.20 h with all of the stake building; over the $`K`$ row at most 13.03 h, and at least 10.48 h, or 13.03 h with chain blocks only (Computed, 5.8, 5.9; Assumed, 5.9) | 54 h |
| phase 2 | B | an honest win: 874 slots at $`x`$ = 0.7, and 903 over the $`K`$ row (Proved, 9.2) | 3.10 to 4.80 h (Proved, SURVIVAL 8.1; Computed, 9.4; Assumed, 9.4) | 54 h |
| phases 1 and 2 | I | at least the window $`P`$ (Cited, 10.1) | no bound on $`P`$ in the specification (Assumed: no text found); the noise is proportional to $`P^{-1/2}`$ (Proved, 7.4) | 108 h |
| phase 3 | L, J | as phase 1; also $`2s_{gen} - 1`$ by the reading of 8.3 (Proved, 8.4); $`2K - 1`$ for the argument of 8.6, not shown to be necessary (Cited, GENESIS 7.1) | as phase 1; 20.00 h for the argument of 8.6 (Computed, 10.3) | 72 h |
| epoch | sum | $`E \ge 2K`$ follows (Proved, 10.2) | at most 37.83 h, at least 21.21 h; at most 128.00 h with the window kept, at least 118.48 h (Computed, 10.3; Assumed, 5.9 and 9.4; Cited, GENESIS 7.1) | 180 h |

No rule of the latest #533 bounds the epoch's length. (Assumed: no such rule found.) The length is the sum of its phases. (Cited, protocol 159.)

### 11.2 What it takes to shorten the epoch

- The phase lengths of the Epoch Schedule, the slot of the cut-off, and `PERIOD` read $`\lfloor k/f \rfloor`$ today. A shorter schedule needs other multiples of it, or lengths that read $`K`$ as the base's did. (Cited, 1.4.)
- A standard for "in time": the building share and the delay at which a phase must still make its value final. The specification has none. (Cited, RFC-532 308; Assumed, A10.)
- Every text of 10.5 that states the epoch's length or a value derived from it. (Cited, 10.5.)
- If the window shrinks: the floor's premise that the inferred stake is exact weakens. Either the chance of missing the floor is accepted as it then is, or $`\phi`$ is derived again. (Computed, 7.6.)
- A phase 3 shorter than $`2K - 1`$ slots, 20.00 hours at $`K`$ = 10 hours, needs another argument that the Bootstrap rule keeps a joining node on the honest chain, or a proof that the condition of GENESIS can be weakened (12). (Cited, GENESIS 7.1 and 7.3; Computed, 10.3.)

### 11.3 The options

The numbers are those of 10.4 and 10.6 for the latest #533. None of the options is recommended over another here.

**Keep 180 hours** (the choice of the latest #533).

- For. The values of the phases stay final in time down to a building share of 13.8 % and 10.2 %. (Computed, 5.7.) The noise of $`D`$ stays at 0.87 %. (Computed, 7.5.) No other text changes. (Cited, RFC-533 182; follows from 10.5.)
- Against. Phases 1 and 3 are 5.4 and 7.2 times $`K`$. (Computed, `out_01_setting.txt` line 11.) New stake waits 180 to 360 hours. A change of the active stake can leave $`D`$ untouched for 252 hours. (Computed, 10.4.)

**Shorten phase 3 only**, to 20.00 hours: an epoch of 128.00 hours.

- For. The window and its noise do not change. $`\eta`$ and $`D`$ are 20 hours old at first use in place of 72. The longest time with no correction falls from 252 to 148 hours. New stake waits 128 to 256 hours. (Computed, 10.4.)
- Against. Phase 3 cannot be shorter than 20.00 hours without another argument for the Bootstrap rule (11.2), although 13.03 hours suffice for its value. (Cited, GENESIS 7.1; Computed, 10.3.) The cut-off is certified final in time (5.4) only down to 41.4 % of the inferred stake building, against 10.2 %. Targets that meet two nonces rise from 5.56 % to 7.81 %. The gain of a coalition that chooses among nonces rises from 0.70 % to 0.83 %. Every text of 10.5 changes. (Computed, 10.4, 10.6; Cited, 10.5; Assumed, 10.6.)

**Scale every phase and the window together**: 100 hours ($`3K`$, $`3K`$, $`4K`$), 90 hours (halved) or 60 hours (a third).

- For. One factor, and at 100 hours the base's own rule. At 90 hours the phases stay final in time down to 29.3 % and 21.3 %, the noise is 1.23 %, and the chance that noise passes the limit of 7.7 is $`1.7 \cdot 10^{-15}`$ per epoch. (Computed, 10.4.)
- Against. Each cost grows as the factor shrinks. At 60 hours phase 1 is certified (5.4) only down to 46.9 % of the stake building, 16.7 % of targets meet two nonces, the gain of 10.6 is 1.21 %, and the chance of fewer than 689 blocks in $`K`$ is $`6.6 \cdot 10^{-8}`$. A deflation costs a coalition of 30 % 1,311 wins in place of 3,934. Every text of 10.5 changes. (Computed, 10.4, 10.6, 7.8; Cited, 10.5; Assumed, 10.6.)

**Take every phase at the value that suffices**: 37.83 hours.

- For. An epoch that keeps the rules in every state of the $`K`$ row and meets J. The least such epoch lies between 21.21 and 37.83 hours (10.2). New stake waits 38 to 76 hours. The longest time with no correction is 58 hours. (Computed, 10.3, 10.4.)
- Against. No margin is left in phases 1 and 2: the snapshot's value is certified final in time (5.4) only down to 70 % of the inferred stake building. Phase 3 has no margin for J, and its value is certified final in time down to 41.4 %. The noise of $`D`$ is 2.14 %. The chance of fewer than 689 blocks in $`K`$ is $`4.0 \cdot 10^{-7}`$, or the floor falls to 666. Noise alone passes the limit of 7.7 with a chance of $`3.1 \cdot 10^{-6}`$ per epoch. 26.4 % of targets meet two nonces. The gain of 10.6 is 1.53 %. An epoch holds 4,539 blocks in place of 21,600. The buffer of 4.80 hours holds under the assumptions of the survival theorem. (Computed, 10.4, 10.6, 10.5; Cited, GENESIS 7.1; Assumed, 9.4 and 10.6.)

**Leave the epoch and move the snapshot later.**

- For. New stake's wait falls without a change of the epoch's length. From the snapshot to its first use, $`G^*`$ + $`w_B`$ + gap is 86.8 hours with all of the inferred stake building at 15 s, and 89.8 hours in the worst state of the $`K`$ row, at $`K`$ = 10 hours, against 180. No wait below 82.7 hours keeps the rules in every state of the $`K`$ row. (Computed, 5.8, 5.9, 9.2, 9.4, `out_14_bracket.txt` lines 46–47; Assumed, 9.4.) No other protocol's clock moves. (Assumed: the texts of 10.5 read the epoch, not the snapshot.)
- Against. It changes the rule of protocol 173, which names the beginning of the previous epoch. It is not part of #533. The snapshot must then be final before the buffer that precedes the cut-off, with the margins of 5.8 and 9.4. (Cited, protocol 173; Computed, 5.8, 9.4.)

**Separate the lottery's cycle from the epoch that other protocols read.**

- For. The lottery's schedule could change without the texts of 10.5.
- Against. It adds a second clock to the specification. Nothing in #533 defines it. (Assumed: no text was found.)

## 12. What is not proved here

- That the conclusion of Theorem 2 of Ouroboros Genesis holds against every fork at $`10^{-9}`$. GENESIS bounds the chance per divergence slot by $`1.35\cdot10^{-7}`$ at 10 s and $`4.3\cdot10^{-5}`$ at 15 s against 30 %, and the finality study's estimates of one attack lie 1,500 to 2,900 times lower (8.6). Whether the true chance meets $`10^{-9}`$ at $`s_{gen}`$ is open.
- GENESIS's A6, on which its bound for every fork rests. Its reading of the margin of Gaži, Ren and Russell for two chains is argued from their Definitions 4 and 11, not proved in full. That the finality study's settlement bound covers the margin at every slot is the study's construction, and is not checked (GENESIS 12, items 1 and 10).
- The chance of a split of the honest nodes that lasts the density window. It is only estimated, from two extended depths of the study's numerical lower bound (GENESIS 6.4 and 12, item 2). The construction also uses tie-breaking for the coalition, which the specification does not give (GENESIS 12, item 11).
- The other conditions of GENESIS: the Online rule's guarantee S up to the switch, cited from the $`K`$ row; an unbiased nonce; keys of at most 30 % of each epoch's stake in the coalition's hands, which the specification does not enforce; the circuit's shortfall on the honest side in the settlement bound; and a union over a history that may be loose (GENESIS 12).
- The assumptions of the survival theorem (9.4): a random-oracle lottery with an unbiased nonce, shares that do not change during the period, delivery within $`d`$, and A5, which is the guarantee that sizes $`K`$, cited and not derived (SURVIVAL 12). That the law is nearly attained also needs many honest nodes, and honest nodes that do not pass on the coalition's blocks (SURVIVAL 12).
- The existence of a final chain in 9.3. It is assumed.
- Whether a weaker condition than $`2K \le G + 1`$ suffices for the argument of 8.6, and whether the Bootstrap rule fails with a phase 3 shorter than $`2K - 1`$ slots. GENESIS uses the condition to place the blocks of a fork, up to $`2K`$ slots after it leaves the honest chain, under the honest chain's epoch states (GENESIS 7.1, Step 2). The epochs that suffice in 10.3 rest on the condition. The lower bounds do not.
- The least epoch itself. 10.2 proves only that it lies between the bounds of 10.3.
- That the bounds behind RFC-533's shares with today's nonce, and the number of nonces a coalition holds at a cut-off, do not depend on the gap or on the epoch's length (10.6). They were computed by the finality study for today's schedule.
- The wait bound that sizes $`K`$. It is cited from the RFCs, not derived.
- The limits 1.094 and 1.593 of 7.7. They are cited from the RFCs.
- The model $`M(p, d)`$ is the specification's own model of the floor. Whether a real network stays within it is not shown. The bounds of 5.4 and 5.5 hold in the model.
- The mapping of the $`K`$ row's states to a building share and a delay (5.9) is this review's, and so is the reading of the second disturbance after the inference corrects.

## 13. Files

All files of this review are in this folder, `slot-finality/epoch/`.

| File | Content | Statement |
| --- | --- | --- |
| `common.py` | constants and the formulas of 5.3 to 5.5 | |
| `s01_setting.py`, `out_01_setting.txt` | the constants; the floor from the specification's code and in exact integers | 1.2, 5.8 |
| `s02_commit.py`, `out_02_commit.txt` | the loop of `commit` on random chains | 3.8 |
| `s03_gap_bound.py`, `out_03_gap_bound.txt` | the bounds of 5.4 and 5.5: least share by gap, least gap by share | 5.7, 5.8 |
| `s04_gap_sim.py`, `out_04_gap_sim.txt` | a simulation of the model against the bounds | 5.6 |
| `s05_targets.py`, `out_05_targets.txt` | targets that meet two nonces | 6.3 |
| `s06_inference.py`, `out_06_inference.txt` | the inference: rule, noise, the floor, the limit, the price of a deflation | 7.2 to 7.8 |
| `s07_genesis.py`, `out_07_genesis.txt` | the hypotheses of the paper's theorems; the schedule facts | 8.4, 8.5 |
| `s08_buffer.py`, `out_08_buffer.txt` | the buffer with the finality study's survival law, the same on a finer grid, and the buffer with the proved law, read from `proofs/survival/out_3_buffer.txt` or computed for a third | 9.2, 9.4 |
| `s09_epoch.py`, `out_09_epoch.txt` | the epochs that suffice, with phase 3 at $`\max(G^*, 2K - 1)`$, the cost of each schedule, and whether its phase 3 meets J | 5.9, 6.3, 10.3, 10.4, 10.5 |
| `s11_gain.py`, `out_11_gain.txt` | the gain of choosing among nonces, by epoch length | 10.6 |
| `s14_bracket.py`, `out_14_bracket.txt` | the necessary values of 5.5 and 9.2 in each state, the bounds on the least epoch, a node's own draw, the wait with a late snapshot, a second computation of the necessary values and of $`G^*`$, and the bounds of GENESIS at a phase 3 of $`2K - 1`$ slots | 5.9, 9.2, 10.3, 11.3 |
| `proofs/survival/` | SURVIVAL: `SURVIVAL.md`, its module `sv_common.py`, its scripts `s1_walk.py` to `s6_protocol_sim.py` and their outputs `out_1_walk.txt` to `out_6_protocol_sim.txt` | 9.4, 10.3 |
| `proofs/genesis/` | GENESIS: `GENESIS.md`, its module `common_g.py`, its scripts `g01_setting.py` to `g07_states.py` and their outputs `out_01_setting.txt` to `out_07_states.txt` | 8.6 |

Each proof's own section on files gives the content of each script and the order in which to run them. GENESIS read the specification at the commits of 1.1, and the paper; neither is copied here.

Read-only sources outside this folder:

- the finality study: `tools/simulators/finality/` of this repository, package `src/finality_sim`, stored runs `slot-finality/`;
- the specification: the repository `logos-co/logos-lips`, branches and commits as in 1.1.

`s08` and `s11` import the finality study's code. The other scripts need only `numpy` and `scipy`. `s08` reads `proofs/survival/out_3_buffer.txt` and imports `proofs/survival/sv_common.py`, so it runs after SURVIVAL's `s3_buffer.py`. `s09` and `s14` read `out_08_buffer.txt`, and `s11` reads `out_09_epoch.txt`. `s14` also imports `proofs/genesis/common_g.py` and reads the settlement curves that GENESIS's `g03_settle.py` caches in `proofs/genesis/.cache`, so it runs after `g03`. SURVIVAL's `s4_epoch.py` reads `out_14_bracket.txt`, so it runs after `s14`. Each script names its usage in its first lines. Caches go to `.cache` in this folder.
