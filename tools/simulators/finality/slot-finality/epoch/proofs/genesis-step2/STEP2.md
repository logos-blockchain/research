# A weaker condition on the last phase

Date: 2026-11-19. Status: not reviewed. Nothing in `../../REVIEW.md`, `../../schedule/` or the specification uses it.

GENESIS (`../genesis/GENESIS.md`) proves that a node joining under the Bootstrap rule ends on the honest chain: its theorem 7.3, through the reduction 7.1. Two of its hypotheses are $`s \le K - 1`$ and $`2K \le G + 1`$. Here $`s`$ = 16,200 slots is the density window, $`K`$ = 36,000 slots the finality window, and $`G`$ the length of the Lottery Constants Finalization phase, the gap from the cut-off to the next epoch. REVIEW.md turns the second hypothesis into its rule J. This folder holds a proof that the theorem holds with the same terms for every $`G`$ with $`K - 1 \le G < E`$, and the work that produced and checked it.

## 1. The result

**1.1 (Proved, given GENESIS's A6; checked).** In the model of GENESIS section 3, with $`s \le K - 1`$ and $`K - 1 \le G < E`$, the bound of GENESIS 7.3 holds term for term. There is no extra failure term (`attempt-b/PROOF.md` 7.5; `check/CHECK.md` item 2).

- $`2K \le G + 1`$ is used in one place only: Step 2 of GENESIS 7.1. There a fork $`X`$ replaces the current choice $`Y`$ by length after leaving $`Y`$ beyond $`D_Y`$, the block where $`Y`$ leaves the reference chain $`H`$. GENESIS takes $`X`$ and $`H`$ as the witnesses of event $`E_r`$, which needs every block of $`X`$ under $`H`$'s epoch states.
- The repair takes $`Y`$ and $`H`$ as the witnesses. If $`X`$ is bad, $`X`$ leaves $`H`$ at $`D_Y`$, so $`sl_{D_Y} \le sl_X - K \le \text{now} - K`$. $`Y`$ is not bad, so its blocks lie within $`K - 1`$ slots of $`D_Y`$, under $`H`$'s states when $`K \le G + 2`$. $`Y`$ and $`H`$ then share no block from slot $`\text{now} - K + 1`$ on. That is $`E_r`$, bounded by $`U(K - 2)`$ as in GENESIS 7.2. No block of $`X`$ after $`D_Y`$ is read. Both attempts found this repair.
- Attempt B also restricts the density event to divergences on $`H`$ before $`D_Y`$, its $`E_d^*`$. Every other divergence lies in its $`E_r^*`$ or in $`E_g`$. This removes $`s + K \le G + 1`$, which GENESIS 6.1 needs, and leaves $`G \ge K - 1`$, which GENESIS 3.1 needs.
- Attempt A proves the theorem under $`s + K \le G + 1`$ only (its 4.1). It is a special case of 1.1.
- The bounds are tight for the reduction. In the check's search, GENESIS 3.1 fails at $`G = K - 2`$, and the witness $`Y`$ fails at $`G = K - 3`$ (`check/CHECK.md` item 4).

**1.2. What 1.1 does not give.** GENESIS 7.3 bounds the chance that S holds and the joining node does not. S, the Online rule's guarantee, still needs each value final before its first use. For that a phase of $`G^*`$ = 46,910 slots (13.03 hours) suffices, and at least 36,611 slots are necessary (REVIEW.md 5.9). So, if 1.1 is accepted, the floor of the last phase moves from $`2K - 1`$ = 71,999 slots to $`G^*`$, not to $`K - 1`$. The items GENESIS leaves open in its section 12, among them A6 and the study's clock behind $`U`$, stay open.

## 2. Gaps in GENESIS's own proof

Each lies inside an event that GENESIS already counts, and none changes a figure (`check/CHECK.md` items 3 and 6).

1. The second bound of 7.2 extends $`X[0{:}e]`$ by blocks "within $`G + 1`$ of $`D`$". When $`D`$ lies after $`D_Y`$, that gives $`Y`$'s states, not $`H`$'s. The case lies in $`E_r \cup E_g`$. The check's search found such extensions at every $`G \ge K`$ it ran, 3,211 in all, among them 14, 34 and 7 at $`K`$ = 12 with $`G`$ = 23, 24 and 36, where $`2K \le G + 1`$ holds. Every one lay in $`E_r^*`$ or $`E_g`$. Both attempts fix the argument (`attempt-b/PROOF.md` 7.3).
2. The first case of 6.3 does not state why the added slots are wins under $`H`$'s states. The step is true: they lie below $`b \le sl_Y \le sl_{D_Y} + K - 1 \le sl_{D_Y} + G + 1`$. Attempt A supplies it.
3. $`E_r`$ as 7.1 writes it admits chains made by slot `now`, so the bound $`U(K - 2)`$ of 7.2 covers only the witness of Step 2. The attempts' events $`E_r'`$ and $`E_r^*`$ end by slot $`\text{now} - 1`$.

## 3. The terms

Per divergence slot, against 30 % of the total active stake, with $`K`$ = 36,000 and $`s`$ = 16,200, in the five states of the $`K`$ row as REVIEW.md 5.9 maps them (`check/out_c5_terms.txt`). Only $`P_1(G + 1 - s)`$ reads $`G`$.

| State | $`P_1(s)`$ | $`U(s - 1)`$ | $`U(K - 2)`$ | $`U_{\Delta+1}(K - 1)`$ | $`P_1(G + 1 - s)`$ at $`G`$ = 35,999 / 46,910 / 52,199 / 54,000 |
| --- | --- | --- | --- | --- | --- |
| no disturbance | 2.0552e-13 | 1.3493e-7 | 8.2847e-16 | 1.3482e-14 | 3.9493e-16 / 2.4938e-24 / 2.7097e-28 / 1.2140e-29 |
| every block $`T_M`$ late | 2.5638e-10 | 4.3411e-5 | 2.5075e-10 | 2.0824e-9 | 2.2980e-12 / 1.5397e-18 / 1.6038e-21 / 1.5512e-22 |
| a tenth offline, inference corrected | 5.2045e-10 | 1.2848e-5 | 2.0131e-11 | 1.7972e-10 | 5.5479e-12 / 6.2875e-18 / 8.4499e-21 / 8.9138e-22 |
| a tenth offline, before the correction | 8.9950e-10 | 1.2851e-5 | 2.0801e-11 | 1.5087e-10 | 1.0826e-11 / 1.7723e-17 / 2.8466e-20 / 3.1907e-21 |
| $`D`$ equals the honest stake online | 8.5233e-15 | 4.5061e-7 | 9.8981e-15 | 7.2613e-13 | 8.0400e-18 / 5.8775e-27 / 2.2460e-31 / 7.0545e-33 |

The totals equal GENESIS's at every gap in the table. Forks with no honest block in the window meet $`10^{-9}`$ in every state, as in GENESIS. The bound for every fork misses it in every state, as in GENESIS.

## 4. How it was produced

Two attempts were made independently, neither with access to the other's folder. A check then reviewed both line by line, reconciled their figures, and ran a search written from the specification and GENESIS's definitions, sharing no code with either attempt.

| Folder | What it holds |
| --- | --- |
| `attempt-a/` | `PROOF.md`: the repair under $`s + K \le G + 1`$, what a fork's own epoch state can be (sections 2 and 5), and random and targeted executions with epochs. |
| `attempt-b/` | `PROOF.md`: the repair with $`E_d^*`$, the theorem for every $`G \ge K - 1`$ (7.5), the terms, and random passes of the Bootstrap rule. |
| `check/` | `CHECK.md`: the verdicts, the errors found, the reconciled terms, and a search over 456,000 executions with every chain deriving its own epoch states, at $`K`$ = 10, 12 and 16 and $`G`$ from $`K - 1`$ to $`2K - 2`$. |

The attempts differ only in rounding. A states 2.9e-20 where the bound is 2.8466e-20, and B states 2.8e-20 (`check/CHECK.md` item 5).

## 5. Reproducing

Each report lists its scripts in its section on files. The scripts import `../genesis/common_g.py` read-only and load GENESIS's settlement curves from `../genesis/.cache`, which GENESIS's own scripts write: run its `g01` to `g07` first. A missing curve is an error, not a recomputation. `attempt-a/run_all.sh` reads the specification from a clone of logos-lips named by `LIPS_REPO`, at commit `83596b6e` of the branch `Bedrock-RFC-Shorter-Epoch`. The check's search runs as `python c4_sim.py 12000`, then `python c4_table.py out_c4_sim.txt` and `python c4_extra.py 8000`. Every stored output was regenerated from this folder on 2026-11-19 and matched byte for byte, except the line of `check/out_c4_sim.txt` that reports the workers' time.

## 6. For the review

- A6, GENESIS's reading of GRR, and the study's clock behind $`U`$ are not checked here, as in GENESIS.
- If 1.1 is accepted, GENESIS 7.1 (the witness of Step 2), 7.2 and 7.3 (the hypotheses) change, with the gaps of section 2 fixed. REVIEW.md rule J becomes $`G \ge K - 1`$, which $`G^*`$ exceeds, so the floor of the last phase becomes $`G^*`$. `../../schedule/costs.py` then no longer fails "no buffer: 1.5K, 1.5K" on J.
