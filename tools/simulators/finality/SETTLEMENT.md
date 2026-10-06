# Settlement

Phase B of `PLAN.md`. Tables come from `runs/` through `scripts/tables.py`; runs from
`scripts/b2_settlement.py`, `scripts/b2_lower.py`, `scripts/b3_race.py`, `scripts/b3_delay.py`,
`scripts/b4_elapsed.py`, `scripts/b5_what_k_holds.py`, `scripts/b5_recovery.py`,
`scripts/b5_recovery_sweep.py` and `scripts/b6_grinding.py`.

Two delay models are reported side by side (Q3). In the worst case, an adversary delivers each
honest message as late as a bound `Δ` allows and breaks ties; that is the model of the proofs
(B1, B2). With random delay, Blend's mixing decides when messages arrive; that is the model of
the engine (B3).

## B1 — the bounds of Gaži, Ren and Russell, ported

`src/finality_sim/lcbounds.py` ports the proof-of-stake routines of LCanalysis
(`github.com/renling/LCanalysis` @ `35cfc83`), the code behind "Practical Settlement Bounds for
Longest-Chain Consensus" (ePrint 2022/1571, revision 2025-05-02). The model is a Poisson lottery
in which one win can extend any number of chains, with honest messages delayed up to `Δ`; time is
counted in expected block intervals, so a delay of `Δ` seconds at `f = 1/30` is `D = Δ/30`.
Grinding of the epoch randomness is outside the model; B6 adds it. The upper bound covers every
attack. The lower bound is the paper's Section 4.7 attack, which needs only uniformly delayed
honest messages.

Gates (`tests/test_lcbounds.py`, mutations in `scripts/check_mutations.py`):

- **Table 1.** The port reproduces all 152 proof-of-stake cells of the revision's Table 1 within
  `1e-3` relative: both bounds, 10 % and 20 % adversary, 2 s and 5 s delay, depths 2–20. The
  lower bound at 5 s lies above the table by 4.5–5.0e-4 relative at 10 % and by 1.6–2.1e-4 at
  20 %. Every other cell is within `4.3e-5`. Three mutations of the port each fail this gate.
- **The original code.** LCanalysis itself, run in Octave 11.3 with the two pdf functions Octave
  lacks (`octave/`, `scripts/octave_reference.sh`), gives 27 values
  (`tests/data/lcanalysis_octave.csv`): Table 1's 20 % column at 2 s to depth 20, its 10 % column
  at 5 s at depths 2 and 3, a quarter of the stake with `D = 1/3` to depth 20, and a third with
  `D = 1/30` at depth 60. The port matches all 27 within `7e-14` relative, including the lower
  bound at 5 s that lies above the table. One mutation fails this gate.
- **Convergence.** The original follows the Section 4.7 attack for 80 phases, enough for Table 1
  (depth at most 20) and not beyond it. At a third of the stake and depth 60, with 30 states, the
  lower bound is `6.9e-3`, and `5.5e-12` at 80 phases. The original code shows the same at 19
  states: `5.4e-13` with its 80 phases, `6.87e-3` with 240. The port follows the attack for
  `max(80, 4K)` phases, which leaves Table 1 unchanged and converges past it. A gate checks that
  doubling the phases changes nothing at depth 60, and the 80-phase mutation fails it.
- **Every depth at once.** The port's upper bound takes time quadratic in the depth `K`.
  `ub_curve` computes it at every depth up to `K` in one pass, in time linear in `K`: every symbol
  lowers the count still to go by at least one, so the count a path has used passes each value
  once. It matches the port within `1e-12` relative at depths 1–25, and within `1e-10` at depths
  160–640 in three of B2's cells (`tests/data/lcbounds_deep.csv`, `scripts/b2_deep.py`). Three
  mutations fail this gate.

The paper does not state the alphabet and state counts behind its table. The code's defaults
(10 and 19) reproduce it, and 20 and 49 change no cell by more than `5e-5` relative. Beyond the
paper's delays the alphabet must grow, because honest runs lengthen with `D`. B2 sizes it per
point, with at least one state more than the alphabet; the original assumes the alphabet does not
exceed the states.

## B2 — settlement depth over attacker share and delay (worst case)

The bounds at `f = 1/30` for delays `Δ` from 1 s to 20 s. Each cell reads *lower – upper*, in
canonical blocks on top of the target. The paper's attack succeeds out to the lower depth; no
attack succeeds past the upper one. The upper bound is computed at every depth (B1). The lower
bound is computed at depths 20, 40, …, 120 and interpolated between them; `*` marks a lower depth
extrapolated past 120 along its last four computed depths, and `≤ 20` one below 20.

ε = 1e-06

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 20 – 29 | ≤ 20 – 31 | ≤ 20 – 32 | ≤ 20 – 36 | ≤ 20 – 42 | ≤ 20 – 48 | ≤ 20 – 66 | ≤ 20 – 93 |
| 0.10 | 20 – 48 | 20 – 51 | 20 – 53 | 21 – 58 | 21 – 67 | 21 – 75 | 23 – 101 | 24 – 141 |
| 0.15 | 30 – 75 | 31 – 79 | 31 – 82 | 32 – 90 | 33 – 105 | 34 – 117 | 37 – 157 | 40 – 218 |
| 0.20 | 46 – 117 | 47 – 123 | 48 – 128 | 50 – 142 | 53 – 166 | 55 – 185 | 62 – 252 | 70 – 357 |
| 0.25 | 72 – 188 | 74 – 198 | 76 – 209 | 80 – 233 | 88 – 276 | 93 – 313 | 109 – 438 | 131* – 645 |
| 0.30 | 121* – 324 | 125* – 344 | 130* – 366 | 141* – 416 | 160* – 509 | 174* – 589 | 221* – 878 | 290* – 1,398 |
| 0.33 | 182* – 497 | 191* – 533 | 200* – 572 | 222* – 663 | 260* – 841 | 292* – 997 | 402* – 1,608 | 584* – 2,845 |

ε = 1e-09

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 20 – 45 | ≤ 20 – 47 | ≤ 20 – 49 | ≤ 20 – 54 | 20 – 64 | 20 – 73 | 20 – 100 | 21 – 140 |
| 0.10 | 31 – 75 | 31 – 78 | 31 – 81 | 32 – 89 | 33 – 102 | 33 – 114 | 35 – 153 | 37 – 212 |
| 0.15 | 47 – 116 | 47 – 121 | 48 – 126 | 49 – 138 | 51 – 159 | 53 – 177 | 57 – 236 | 62 – 328 |
| 0.20 | 70 – 179 | 72 – 188 | 73 – 197 | 76 – 216 | 81 – 252 | 85 – 281 | 95 – 380 | 107 – 537 |
| 0.25 | 110 – 288 | 113 – 303 | 116 – 319 | 123* – 354 | 134* – 420 | 143* – 474 | 168* – 661 | 200* – 971 |
| 0.30 | 185* – 495 | 192* – 525 | 199* – 558 | 216* – 632 | 244* – 773 | 266* – 892 | 338* – 1,325 | 442* – 2,105 |
| 0.33 | 278* – 758 | 291* – 812 | 306* – 871 | 338* – 1,008 | 397* – 1,275 | 445* – 1,510 | 612* – 2,426 | 887* – 4,282 |

Checks:

- Doubling the attack's phases at depth 120 changes no lower bound.
- The skipped symbol mass is below `2e-14` per step.
- Doubling the states moves no upper depth below 30 % of the stake, at `1e-9` or at `1e-30`. From
  30 % it adds at most 0.2 %: 6 blocks at a third, 20 s and `1e-9`, and 23 at `1e-30`
  (`runs/b2/states.csv`).
- In every cell with an extrapolated lower depth, the log of the lower bound is convex in the depth
  over 20–120. The extrapolation then falls short of the attack's depth. At a quarter of the stake
  and 10 s, the lower bound computed at depths 140 and 150 puts the attack's depth at `1e-9` at
  143, as the extrapolation does (`runs/b2/lower.csv`).

Reading:

- At `ε = 1e-9` and delays of 1–10 s the upper bound is 75–114 blocks against 10 % of the stake,
  288–474 against 25 %, and 758–1,510 against a third.
- **The attack is not far below the proof.** Where the lower depth is computed, the upper one is
  2.4–3.6 times it at delays up to 10 s, and up to 6.6 times at 20 s.
- **In time**, on the honest chain while the coalition withholds, at the specification's Blend
  (`30 s / ((1 − α) · 0.845)` a block, A1) and `Δ = 10` s:
  - against 25 %, the guarantee takes 474 blocks, 6.2 h at 47.3 s a block; the attack reaches 143,
    1.9 h;
  - against 10 %, 114 blocks, 75 min at 39.4 s a block, against 33, 22 min;
  - under random delays and the private attack (`RATE.md`, C1), 68 and 12 minutes;
  - k-finality takes 28 h and 24 h.
- **H1 fails for the guarantee.** At 25 % and `ε = 1e-9` the upper bound exceeds `k/10 = 216` at
  every delay, from 288 blocks at 1 s. The paper's attack falls below `1e-9` by depth 216 at
  every delay up to 20 s (`runs/b2/lower.csv`).
- **H2 holds up to a delay of 13 s.** At a third of the stake the upper bound at `1e-9` is 1,987
  blocks at 13 s and 2,192 at 14 s (`runs/b2/third.csv`). Past 14 s the guarantee needs more than
  `k = 2160` blocks, while the paper's attack needs 612 at 15 s and 887 at 20 s. Within 13 s the
  first finding is therefore a latency, not a safety margin (`PLAN.md`, H2). B6 counts grinding.

## B3 — the attacks, simulated

### The private-chain attack under random Blend delays

`src/finality_sim/race.py` plays a private-chain attack on the engine's own timelines. A
coalition holding stake share `α` withholds every block it wins. Honest nodes build the public
chain from honest stake under the engine's Blend delays, and the coalition's winning slots are
recorded. A win can sign a block on any branch, and a chain holds one block per slot, so the
private chain grows by one block per slot the coalition wins.

For each canonical block, the race asks whether the coalition ever releases a chain that
displaces it, once `K` blocks lie on top of it. The race is scored against the best-informed node.
A node that sees blocks later is beaten at least as often, so for a real client the race's success
rate is a lower bound. It has two settings:

- **Premining.** Before the target, the coalition keeps a private lead that a public block
  erodes. Without premining, it starts at the target's parent.
- **Ties.** Cryptarchia's Online rule keeps the first-seen chain on ties, so the coalition must be
  strictly longer. With ties to the attacker, as in Rosenfeld's race, a tie suffices.

Gates (`tests/test_race.py`): on independent Bernoulli timelines the race reproduces the closed
forms at attacker shares 0.10 and 0.25, wherever a depth of 1–8 expects at least 100 successes:
with ties to the attacker or strictly longer, without and with a premined lead. Without the lead
they are Rosenfeld's race and its strict counterpart. With it, the lead at the target is
stationary, geometric with ratio `q/(1 − q)`. Three mutations fail these gates.

64 engine runs per cell, equal stake, `f = 1/30`. "q" is the coalition's share of
chain-extending blocks. Depths at which the success rate falls to `1e-3` and `1e-4`:

| configuration | α | q | orphan share | no lead, ties ≤ 1e-03 | no lead, strict ≤ 1e-03 | premined, strict ≤ 1e-03 | no lead, ties ≤ 1e-04 | no lead, strict ≤ 1e-04 | premined, strict ≤ 1e-04 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| testnet | 0.1 | 0.103 | 0.044 | 5 | 4 | 4 | 7 | 6 | 6 |
| testnet | 0.2 | 0.206 | 0.039 | 12 | 10 | 11 | 17 | 14 | 15 |
| testnet | 0.25 | 0.255 | 0.036 | 19 | 17 | 18 | 28 | 27 | 27 |
| testnet | 0.3 | 0.307 | 0.035 | 32 | 29 | 31 | 43 | 41 | 42 |
| spec | 0.1 | 0.118 | 0.176 | 6 | 4 | 4 | 9 | 7 | 7 |
| spec | 0.2 | 0.229 | 0.158 | 13 | 11 | 11 | 22 | 19 | 20 |
| spec | 0.25 | 0.280 | 0.152 | 24 | 21 | 23 | 36 | 34 | 38 |
| spec | 0.3 | 0.334 | 0.143 | 43 | 40 | 42 | 50 | 48 | 49 |
| heavy | 0.1 | 0.145 | 0.339 | 7 | 5 | 5 | 10 | 8 | 8 |
| heavy | 0.2 | 0.265 | 0.313 | 18 | 15 | 16 | 26 | 22 | 24 |
| heavy | 0.25 | 0.322 | 0.301 | 34 | 31 | 32 | 60 | 58 | 58 |
| heavy | 0.3 | 0.372 | 0.285 | > 60 | > 60 | > 60 | > 60 | > 60 | > 60 |

"testnet" is 1 hop of 1 round and "spec" 3 hops of up to 3 rounds, both with 0.1 s links. "heavy"
is the TSI report's 3 hops of up to 8 s with 0.5 s links.

- At `1e-3`, Rosenfeld's closed form at the measured `q` asks for 0–3 blocks more than the race on
  testnet's and the specification's Blend, and 0–6 more at the heavy point. It never asks for
  fewer.
- Premining adds zero to four blocks, and the strict tie rule removes one to four.
- A crossing of `1e-4` rests on 2–21 successes, and successes come in clusters, one attack
  episode covering consecutive targets. The `1e-4` columns are not compared with the closed form.

At `f = 1/30` and `1e-3` the closed form is therefore a slightly conservative guide to this attack
under random delay. `RATE.md` (C1) uses its strict counterpart over block rate and delay.

### The delay-scheduling attacker

The attack behind B1's lower bound needs only that every honest block reaches the other honest
nodes as late as `Δ` allows (Gaži, Ren and Russell, §4.7). The adversary keeps two chains and
extends both with each win; a ticket that does not depend on the parent allows that.
`src/finality_sim/grr_attack.py` plays the attack on the slot lottery. Each slot draws honest and
adversarial wins with Cryptarchia's probabilities. An honest win adds depth only when it comes
more than `Δ` slots after the last win that did.

Gates (`tests/test_grr_attack.py`): on slots ten times finer than Cryptarchia's, the attack
reproduces the port's lower bound within statistical error at a 30 % adversary, `D = 1/3` and
depths 1–12. Four mutations fail the gates.

The gate also shows what the code's lower bound counts. It scores the attack only at the moment
the target reaches depth `K`, and drops the paths that fail there. Scored at any later moment as
well, the same attack succeeds 2–17 % more often in the runs below.

20 runs of `1e8` slots per point, `f = 1/30`, 1 s slots, ties to the attacker. The chance of
success at depth 10 / 40 (`runs/b3/delay.csv`):

| α | Δ | lower bound | attack, at confirmation | attack, any moment after | private attack alone | upper bound |
| --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 2 s | 7.2e-04 / 4.6e-12 | 7.0e-04 / < 2e-08 | 7.2e-04 / < 2e-08 | 3.1e-06 / < 2e-08 | 3.2e-02 / 1.3e-05 |
| 0.10 | 5 s | 8.5e-04 / 9.1e-12 | 8.3e-04 / < 2e-08 | 8.5e-04 / < 2e-08 | 5.2e-06 / < 2e-08 | 5.2e-02 / 5.2e-05 |
| 0.10 | 10 s | 1.1e-03 / 2.8e-11 | 1.1e-03 / < 2e-08 | 1.1e-03 / < 2e-08 | 1.2e-05 / < 2e-08 | 1.1e-01 / 4.9e-04 |
| 0.25 | 2 s | 9.0e-02 / 4.2e-04 | 9.0e-02 / 4.1e-04 | 9.8e-02 / 4.4e-04 | 2.0e-02 / 3.8e-06 | 3.3e-01 / 3.6e-02 |
| 0.25 | 5 s | 1.0e-01 / 7.3e-04 | 1.0e-01 / 7.2e-04 | 1.1e-01 / 7.8e-04 | 2.8e-02 / 1.2e-05 | 4.0e-01 / 5.9e-02 |
| 0.25 | 10 s | 1.3e-01 / 1.8e-03 | 1.3e-01 / 1.8e-03 | 1.5e-01 / 1.9e-03 | 4.6e-02 / 5.6e-05 | 5.2e-01 / 1.2e-01 |
| 0.33 | 2 s | 3.2e-01 / 3.4e-02 | 3.1e-01 / 3.4e-02 | 3.6e-01 / 3.8e-02 | 1.8e-01 / 4.6e-03 | 6.1e-01 / 2.4e-01 |
| 0.33 | 5 s | 3.5e-01 / 5.0e-02 | 3.5e-01 / 5.0e-02 | 4.0e-01 / 5.8e-02 | 2.2e-01 / 9.4e-03 | 6.8e-01 / 3.2e-01 |
| 0.33 | 10 s | 4.2e-01 / 9.2e-02 | 4.2e-01 / 9.3e-02 | 4.9e-01 / 1.1e-01 | 3.1e-01 / 2.8e-02 | 7.8e-01 / 4.7e-01 |

- On Cryptarchia's slots the attack lands within 7 % of the lower bound wherever the bound exceeds
  `1e-4` (ratios 0.93–1.02). At these nine points B2's lower bound, computed in continuous time,
  describes the slot lottery.
- No run exceeds the upper bound.
- The private attack alone, on the same draws and delays, is far weaker: about 30 times less
  successful at 25 % and 10 s at depth 40. The second chain is what the delay model adds. When
  every honest block arrives `Δ` late, an adversarial chain of equal length reaches honest nodes
  first.

## B4 — a client confirmation rule

Today the node exposes two levels, the tip and the latest immutable block `B_imm`, which its API
calls `lib` (`MAPPING.md` §3). The rule adds a third: a block is *settled* for `(α, ε)` and a delay
model once `d` canonical blocks lie on top of it, where `d` holds the chance of its displacement to
`ε`. A client that uses it accepts these assumptions:

- the coalition holds at most `α` of the active stake;
- the attack and delay model the depth was computed for: under random Blend delays the private
  race from the target's parent without a premined lead (B5's closed form); under a worst case of
  `Δ`, any attack (B2);
- grinding of the epoch nonce no stronger than the depth includes (B6);
- the node's own view is not eclipsed.

The depth table is the RFC candidate: B2 for the worst case, B5's closed form for random delay. An
API would expose it as a configured `(α, ε)` and a settled level beside `lib` in
`/cryptarchia/info`, with a stream like `lib-stream`.

**Reading elapsed time.** A depth rule holds `ε` on average over the times at which blocks arrive,
and a client sees those times. Per slot, the coalition wins with probability `a = α·λ` and the
canonical chain grows with probability `h = (1 − α)·g·λ`, where `λ = −ln(1 − f)` and `g` is A1's
growth on the specification's Blend; `q = a/(a + h)` is then B5's. Let the coalition fork at the
target's parent without a premined lead and withhold every win. When the `n`-th canonical block
counting the target appears `t` slots after that parent, the coalition holds a Poisson number of
blocks of mean `a·t`, whatever the times of the honest blocks. The client computes the coalition's
chance exactly (Grunspan and Pérez-Marco, "Double spend races", 2018) and accepts at the first
block where it is at most `ε` (`src/finality_sim/elapsed.py`). It reads `t` on its own clock when
it evaluates. Averaged over arrival times, that chance is the depth table's. Given any history of
honest blocks up to acceptance, it is at most `ε` as well.

The depth rule waits for B5's closed-form depth. Both rules are played on 64 timelines per share,
one epoch at `k = 256`: the engine's, on the specification's Blend with the coalition withholding,
and independent slots of the model both rules assume. The race scores each acceptance itself
(`scripts/b4_elapsed.py`). A cell of 0 means no success among about 100,000 targets:

| timelines | α | ε | depth rule: blocks | depth rule: minutes, mean / p90 | elapsed-time rule: blocks, mean | elapsed-time rule: minutes, mean / p90 | race beats the rule, depth / elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| engine | 0.10 | 1e-3 | 4 | 2.6 / 4.1 | 3.6 | 2.4 / 4.5 | 5.9e-04 / 5.0e-04 |
| engine | 0.10 | 1e-6 | 12 | 7.9 / 10.4 | 9.5 | 6.3 / 9.8 | 0 / 0 |
| engine | 0.10 | 1e-9 | 19 | 12.5 / 15.7 | 15.5 | 10.2 / 14.9 | 0 / 0 |
| model | 0.10 | 1e-3 | 4 | 2.6 / 4.3 | 3.5 | 2.3 / 4.8 | 9.5e-04 / 7.4e-04 |
| model | 0.10 | 1e-6 | 12 | 7.8 / 10.7 | 9.4 | 6.1 / 10.2 | 0 / 0 |
| model | 0.10 | 1e-9 | 19 | 12.3 / 16.0 | 15.3 | 9.9 / 15.2 | 0 / 0 |
| engine | 0.25 | 1e-3 | 23 | 17.7 / 21.8 | 16.7 | 12.8 / 21.4 | 6.4e-04 / 4.9e-04 |
| engine | 0.25 | 1e-6 | 54 | 41.6 / 47.7 | 37.3 | 28.7 / 41.8 | 0 / 0 |
| engine | 0.25 | 1e-9 | 86 | 66.2 / 74.0 | 58.2 | 44.8 / 61.4 | 0 / 0 |
| model | 0.25 | 1e-3 | 23 | 17.8 / 22.6 | 16.8 | 13.0 / 23.1 | 5.0e-04 / 6.8e-04 |
| model | 0.25 | 1e-6 | 54 | 41.8 / 49.0 | 37.6 | 29.0 / 44.5 | 0 / 0 |
| model | 0.25 | 1e-9 | 86 | 66.6 / 75.5 | 58.5 | 45.3 / 64.9 | 0 / 0 |

- **Reading elapsed time settles about a third sooner against a quarter of the stake.** At `1e-9`
  the depth rule waits 86 blocks, 66 minutes on the engine's timelines. The elapsed-time rule
  accepts after 58 blocks on average, in 45 minutes, and its 90th percentile, 61 minutes, is below
  the depth rule's 74. At `1e-3` it takes 13 minutes instead of 18.
- **Against a tenth of the stake it settles about a fifth sooner** at `1e-6` and `1e-9`. At
  `1e-3` it gains 11 % on average, and its 90th percentile is 0.4 minutes longer.
- **Both rules hold `ε` where it can be measured.** At `1e-3` and a quarter of the stake, the race
  beats the depth rule on 6.4e-4 of the engine's targets and the elapsed-time rule on 4.9e-4.
- **The per-history guarantee holds inside the rule's model only.** A coalition that also extends
  the public chain changes the history the client reads. Under a worst case of `Δ` the rule would
  need B2's model, which is not derived here.

Gates (`tests/test_elapsed.py`): averaged over arrival times, the chance is the depth table's
closed form; each deadline is the latest time that settles; the race's per-target depths count
what the race counts; on the model's timelines the rule holds `ε = 0.01`, which it would not with
its clock started at the target; in each of five bands of how fast the blocks came, the rule holds
`ε = 0.01`, while the depth rule exceeds `3ε` in the slowest band. Five mutations fail them.

## B5 — a smaller `k`

The largest attacker share each `k` holds without grinding (B6 adds it), under random delays (the
private race from the target's parent, without a premined lead, and the strict tie rule), at the
canonical growth A1 measured:

| Blend | growth / f | ε | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| testnet (1 hop, 1 round) | 0.971 | 1e-6 | 0.456 | 0.441 | 0.411 | 0.378 | 0.342 |
| testnet (1 hop, 1 round) | 0.971 | 1e-9 | 0.447 | 0.428 | 0.391 | 0.351 | 0.307 |
| testnet (1 hop, 1 round) | 0.971 | 1e-12 | 0.439 | 0.417 | 0.374 | 0.328 | 0.278 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-6 | 0.422 | 0.407 | 0.378 | 0.346 | 0.311 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-9 | 0.413 | 0.394 | 0.358 | 0.320 | 0.278 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-12 | 0.405 | 0.384 | 0.342 | 0.299 | 0.251 |

Against this attack, dividing `k` by ten (2160 to 216) lowers the share held at `ε = 1e-9` from
0.41 to 0.32 on the specification's Blend. Testnet's `k = 120` holds 0.31 on its own Blend.

In the worst case, the largest share each `k` guarantees at `ε = 1e-9` is read off B2's upper
bound at depth `k`, on a grid of shares in steps of 0.005, its log linear in the share between
grid points (`runs/b5/worst_case.csv`):

| Δ | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| 1 s | ≥ 1/3 | ≥ 1/3 | 0.288 | 0.221 | 0.155 |
| 2 s | ≥ 1/3 | ≥ 1/3 | 0.283 | 0.215 | 0.150 |
| 3 s | ≥ 1/3 | ≥ 1/3 | 0.278 | 0.210 | 0.145 |
| 5 s | ≥ 1/3 | ≥ 1/3 | 0.268 | 0.200 | 0.135 |
| 8 s | ≥ 1/3 | 0.323 | 0.253 | 0.184 | 0.118 |
| 10 s | ≥ 1/3 | 0.313 | 0.242 | 0.172 | 0.106 |
| 15 s | 0.328 | 0.287 | 0.213 | 0.140 | 0.072 |
| 20 s | 0.301 | 0.258 | 0.179 | 0.102 | < 0.05 |

Testnet's `k = 120` guarantees 0.15 of the stake at a 1 s delay and 0.11 at 10 s. A tenth of
today's `k` guarantees 0.17–0.22 for delays of 1–10 s, 54–69 % of the 0.32 it holds against the
private attack under random delays.

What a smaller `k` changes beyond the share held, with the epoch tied to it or decoupled, is
mapped in `MAPPING.md` §4–§6.

### The two routes of Q8

**What a split leaves today.**

- Neither fork-choice rule reorganises below `B_imm`. That is the key invariant of
  `cryptarchia-v1-bootstr-sync.md`, and the node removes every block below its LIB from its block
  tree (`prune_immutable_blocks`).
- Once the losing side of a split has made `k + 1` blocks, a node on that side holds a `B_imm`
  past the divergence point.
- A restart keeps the block tree, and with it that `B_imm`. The `--bootstrap` flag selects the
  Bootstrap rule, which cannot reach below it either.
- The node returns to the winning chain only when it is re-synced from genesis, or from a
  checkpoint on the winning chain. The node implements the first. Checkpoints are specified and
  not implemented (`choose_engine_state`, issue #1454).

**Shorter horizons.** Every split that outlasts the self-healing horizon (`MAPPING.md` §5; 2.0 h
for an even split at `k = 120`) leaves the losing side on its own chain until operators re-sync
its nodes. The route needs three things the node lacks:

- a signal: blocks whose ancestry ends below the node's LIB never attach to its block tree, and
  nothing reports them;
- checkpoints, so that a re-sync need not start from genesis;
- if it does start from genesis, a density window that does not shrink with `k` (below).

**The density test.** Both the Bootstrap rule and any automatic recovery rest on `maxvalid-bg`:
the chain with strictly more blocks in the `s_gen` slots after the divergence point wins. An
adversary holding share `α` withholds its wins and builds a fork from a divergence point of its
choice. One win signs a block on any branch, so the fork holds one block per slot the adversary
wins. `src/finality_sim/recovery.py` computes the chance that the fork is strictly denser in one
window:

- under random delay, the honest chain's blocks are binomial, thinned by the canonical growth A1
  measured;
- under a worst case of `Δ`, an honest win counts only if it comes more than `Δ` slots after the
  last counted one, the chain-growth argument of the delay proofs.

Gates (`tests/test_recovery.py`): the worst-case count matches a slot-by-slot computation, the
failure matches a Monte Carlo estimate in both models, the probabilities stay finite at the
longest window used, and bought keys raise the fork's rate without lowering the honest chain's.
Six mutations fail them.

The engine's canonical chain varies less from window to window than the binomial model, so the
model overstates the adversary's chance under random delay (`runs/b5/recovery_engine.csv`):

| Blend | window (slots) | growth / f | variance / mean, engine | ± SEM | binomial model |
| --- | --- | --- | --- | --- | --- |
| testnet | 900 | 0.971 | 0.85 | 0.04 | 0.97 |
| testnet | 3600 | 0.971 | 0.90 | 0.08 | 0.97 |
| specification | 900 | 0.846 | 0.77 | 0.04 | 0.97 |
| specification | 3600 | 0.846 | 0.69 | 0.07 | 0.97 |

The adversary's chance per window at today's `s_gen = ⌊k/4f⌋`:

| delay | α | k = 2160 (4.5 h) | k = 1080 (2.25 h) | k = 432 (0.9 h) | k = 216 (0.45 h) | k = 120 (0.25 h) |
| --- | --- | --- | --- | --- | --- | --- |
| random, testnet | 0.10 | 2e-93 | 6e-48 | 2e-20 | 3e-11 | 4e-07 |
| random, testnet | 0.15 | 6e-67 | 1e-34 | 4e-15 | 2e-08 | 2e-05 |
| random, testnet | 0.20 | 5e-47 | 1e-24 | 5e-11 | 2e-06 | 2e-04 |
| random, testnet | 0.25 | 7e-32 | 6e-17 | 7e-08 | 8e-05 | 2e-03 |
| random, testnet | 0.30 | 3e-20 | 4e-11 | 2e-05 | 2e-03 | 1e-02 |
| random, testnet | 0.33 | 3e-14 | 5e-08 | 3e-04 | 7e-03 | 3e-02 |
| random, specification | 0.10 | 1e-75 | 5e-39 | 7e-17 | 2e-09 | 4e-06 |
| random, specification | 0.15 | 2e-52 | 2e-27 | 4e-12 | 5e-07 | 1e-04 |
| random, specification | 0.20 | 1e-35 | 8e-19 | 1e-08 | 3e-05 | 1e-03 |
| random, specification | 0.25 | 7e-23 | 2e-12 | 5e-06 | 8e-04 | 8e-03 |
| random, specification | 0.30 | 1e-13 | 1e-07 | 5e-04 | 9e-03 | 3e-02 |
| random, specification | 0.33 | 5e-09 | 2e-05 | 5e-03 | 3e-02 | 7e-02 |
| worst, 10 s | 0.10 | 3e-83 | 8e-43 | 2e-18 | 3e-10 | 2e-06 |
| worst, 10 s | 0.15 | 9e-57 | 2e-29 | 5e-13 | 2e-07 | 7e-05 |
| worst, 10 s | 0.20 | 8e-38 | 6e-20 | 4e-09 | 2e-05 | 9e-04 |
| worst, 10 s | 0.25 | 5e-24 | 6e-13 | 3e-06 | 6e-04 | 7e-03 |
| worst, 10 s | 0.30 | 4e-14 | 6e-08 | 4e-04 | 8e-03 | 3e-02 |
| worst, 10 s | 0.33 | 3e-09 | 2e-05 | 4e-03 | 3e-02 | 7e-02 |

The adversary may pick any block in reach as the divergence point. So the chance over a span of
history is at most the chance per window times the number of blocks in the span.

- **The window shrinks with `k`.** At testnet's `k = 120` it is 15 minutes. An adversary holding a
  quarter of the stake then wins about one window in 460 on testnet's Blend.
- **Bootstrapping meets every window of the history.** A node that syncs from genesis compares
  forks at every block. Disjoint windows are independent in this model, so over a month of
  history, 2,880 windows of 15 minutes, a quarter of the stake finds such a window with
  probability 0.998. The window must be set apart from `k`.

The window that holds the chance per window to `1e-9` / `1e-12`, in hours
(`runs/b5/recovery_window.csv`):

| α | random, testnet | random, specification | worst, 1 s | worst, 10 s | worst, 20 s |
| --- | --- | --- | --- | --- | --- |
| 0.05 | 0.3 / 0.4 | 0.3 / 0.4 | 0.3 / 0.4 | 0.3 / 0.4 | 0.3 / 0.4 |
| 0.10 | 0.4 / 0.5 | 0.5 / 0.6 | 0.4 / 0.5 | 0.4 / 0.6 | 0.5 / 0.7 |
| 0.15 | 0.5 / 0.7 | 0.7 / 1.0 | 0.5 / 0.7 | 0.6 / 0.9 | 0.8 / 1.1 |
| 0.20 | 0.8 / 1.1 | 1.0 / 1.4 | 0.7 / 1.0 | 1.0 / 1.3 | 1.4 / 1.9 |
| 0.25 | 1.2 / 1.6 | 1.7 / 2.3 | 1.1 / 1.6 | 1.6 / 2.2 | 2.5 / 3.4 |
| 0.30 | 1.9 / 2.6 | 3.0 / 4.2 | 1.8 / 2.5 | 2.9 / 4.0 | 5.3 / 7.3 |
| 0.33 | 2.9 / 3.9 | 4.9 / 6.8 | 2.7 / 3.8 | 4.8 / 6.6 | 10.7 / 14.8 |

**Automatic recovery.** The route as the plan stated it, a switch to the Bootstrap rule when a
node sees a fork deeper than `k`, fails on two counts:

- It cannot heal: the Bootstrap rule does not reach below `B_imm` either.
- It hands the adversary a lever. One stale winning slot makes a one-block fork that diverges
  deeper than `k`. Each such fork would freeze `B_imm` for the Bootstrap period (`T_boot`, 24 h in
  the specification).

A trigger that heals and gives no such lever:

1. **Evaluate the fork; do not switch rules.** A fork that diverges within a recovery horizon `H`,
   and more than `k` blocks deep, is compared by density. The node adopts it only if it is
   strictly denser, and stays under the Online rule either way. `B_imm` may then move back, but
   never past `H`.
2. **Test the deeper branch.** The depth test reads the deeper of the two branches since the
   divergence. `maxvalid-bg`, in the specification and in the node, reads the local one. After a
   split in which one side has passed `k` blocks and the other has not, nodes on the short side
   then follow the longer chain while nodes on the long side follow the denser one. Where the two
   differ, nodes alternate until the short side also passes `k`.
3. **Wait for the whole window.** Densities are compared only once both chains hold every slot of
   the window.
4. **Size the window for `α`, `ε` and the horizon, apart from `k`.** Over a horizon, windows of 1
   and 2 hours hold a quarter of the stake for less than an hour of history even without grinding
   (below). With grinding, 4 hours hold none and 8 hours hold 48–92 days at Bitcoin's turnover
   (B6).
5. **Keep the window inside the lottery parameters fixed before the divergence.** A chain fixes
   the next epoch's nonce and inferred stake `6⌊k/f⌋` slots into an epoch. A fork that diverges
   just before that slot runs on its own nonce and inferred stake `4⌊k/f⌋` slots later. The window
   may therefore be at most `4⌊k/f⌋` slots. Past that, a sparse fork's inference raises its own
   win rate, the attack `fork-choice.md` describes for long-range forks, and its nonce can be
   ground.
6. **Bound the horizon `H`.** Cryptarchia has no forward security (`CERTIFIED.md` D4). Whoever holds
   the key of a note eligible at the divergence point can sign for it on the fork, where it may be
   unspent though spent on the honest chain. `H` must keep `α` plus the stake whose keys an
   adversary can collect within `H` below the share the window holds. No data on Cryptarchia's
   stake turnover bounds it yet. `H` also multiplies the chance per window by the blocks it holds:
   1,833 a day on the specification's Blend while a quarter of the stake withholds.

With the window at its longest, `4⌊k/f⌋` slots, the largest share the density test holds
(`runs/b5/recovery_share.csv`):

| delay | ε per window | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- | --- |
| random, testnet | 1e-09 | 0.460 | 0.447 | 0.421 | 0.391 | 0.357 |
| random, testnet | 1e-12 | 0.455 | 0.439 | 0.408 | 0.374 | 0.335 |
| random, specification | 1e-09 | 0.424 | 0.411 | 0.384 | 0.354 | 0.320 |
| random, specification | 1e-12 | 0.419 | 0.403 | 0.371 | 0.337 | 0.297 |
| worst, 10 s | 1e-09 | 0.425 | 0.411 | 0.385 | 0.356 | 0.322 |
| worst, 10 s | 1e-12 | 0.419 | 0.404 | 0.373 | 0.339 | 0.300 |
| worst, 20 s | 1e-09 | 0.384 | 0.371 | 0.344 | 0.316 | 0.283 |
| worst, 20 s | 1e-12 | 0.379 | 0.363 | 0.332 | 0.299 | 0.262 |

Per window, under random delay, this exceeds what each `k` holds against the private race at
`ε = 1e-9` (the first B5 table): 0.297 against 0.278 at `k = 120` on the specification's Blend,
even at `1e-12` per window. Over a horizon it holds less. At `k = 120`, whose window is at most
4 hours, it holds a fifth of the stake for 61–114 days at Bitcoin's turnover with grinding, and a
quarter for no horizon (B6).

What the trigger costs:

- `B_imm` is no longer immutable within `H`. Every consumer of the LIB (`MAPPING.md` §3) needs a
  path for a LIB that moves back.
- The node keeps its block tree and the ledger states its proofs need back to `H`, instead of
  pruning at the LIB.
- A split heals only once the window after its divergence point has passed: 8 hours against a
  quarter of the stake (rule 4).

**The horizon against stake turnover.** `scripts/b5_recovery_sweep.py` turns rule 6 into numbers.
A share `μ(a) = 1 − e^{−τa}` of the stake moves within an age `a`, at a turnover rate `τ` per day.
An adversary holding `α` that obtains a fraction `c` of the freed keys signs the fork with
`α + c(1 − α)μ(a)`, while the honest chain kept `1 − α`. Over the horizon, the chance of a denser
fork is at most the sum, over divergence points of age up to `H` (one per honest block), of the
window's chance at that point's age. The longest `H`, in days, that keeps it at or below `1e-9`,
with a 4-hour window on the specification's Blend and random delay (`runs/b5/recovery_sweep.csv`
also holds `1e-6`, windows of 1–8 hours and the worst case at 10 s):

Every freed key reaches the adversary (`c = 1`):

| turnover per day | α = 0.10 | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.01 % | ≥ 3650 | 1787 | 724 | 5 h | < 1 h |
| 0.03 % | 1320 | 621 | 265 | 5 h | < 1 h |
| 0.05 % | 801 | 380 | 166 | 5 h | < 1 h |
| 0.1 % | 406 | 195 | 87 | 5 h | < 1 h |
| 0.125 % | 327 | 157 | 71 | 5 h | < 1 h |
| 0.243 % | 170 | 83 | 38 | 5 h | < 1 h |
| 0.3 % | 139 | 68 | 32 | 5 h | < 1 h |
| 1 % | 43 | 21 | 10 | 5 h | < 1 h |
| 3 % | 15 | 7 | 4 | 4 h | < 1 h |
| 10 % | 4 | 2 | 29 h | 2 h | < 1 h |

A tenth of the freed keys reaches the adversary (`c = 0.1`):

| turnover per day | α = 0.10 | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.01 % | ≥ 3650 | ≥ 3650 | ≥ 3650 | 5 h | < 1 h |
| 0.03 % | ≥ 3650 | ≥ 3650 | 2961 | 5 h | < 1 h |
| 0.05 % | ≥ 3650 | ≥ 3650 | 1906 | 5 h | < 1 h |
| 0.1 % | ≥ 3650 | ≥ 3650 | 1048 | 5 h | < 1 h |
| 0.125 % | ≥ 3650 | ≥ 3650 | 865 | 5 h | < 1 h |
| 0.243 % | ≥ 3650 | ≥ 3650 | 488 | 5 h | < 1 h |
| 0.3 % | ≥ 3650 | ≥ 3650 | 407 | 5 h | < 1 h |
| 1 % | ≥ 3650 | ≥ 3650 | 145 | 5 h | < 1 h |
| 3 % | ≥ 3650 | ≥ 3650 | 57 | 5 h | < 1 h |
| 10 % | ≥ 3650 | ≥ 3650 | 21 | 5 h | < 1 h |

The window, against a quarter of the stake with every freed key (`c = 1`):

| turnover per day | 1 h window | 2 h window | 4 h window | 8 h window |
| --- | --- | --- | --- | --- |
| 0.01 % | < 1 h | < 1 h | 724 | 2012 |
| 0.03 % | < 1 h | < 1 h | 265 | 692 |
| 0.05 % | < 1 h | < 1 h | 166 | 421 |
| 0.1 % | < 1 h | < 1 h | 87 | 215 |
| 0.125 % | < 1 h | < 1 h | 71 | 173 |
| 0.243 % | < 1 h | < 1 h | 38 | 91 |
| 0.3 % | < 1 h | < 1 h | 32 | 74 |
| 1 % | < 1 h | < 1 h | 10 | 23 |
| 3 % | < 1 h | < 1 h | 4 | 8 |
| 10 % | < 1 h | < 1 h | 29 h | 2 |

- **Turnover sets the horizon once the window holds the adversary.** Against a quarter of the stake,
  a 4-hour window allows 87 days at 0.1 % of the stake moving per day and 10 days at 1 %, if every
  freed key can be bought.
- **The window sets a ceiling no horizon escapes.** A 4-hour window cannot hold 30 % of the stake
  for more than about 5 hours of history, and a third not at all. Windows of 1 and 2 hours hold a
  quarter for less than an hour.

**How fast stake moves elsewhere.** Per day, as a share of stake or supply, read 2026-10-05:

| chain | what moves | per day | kind |
| --- | --- | --- | --- |
| Ethereum | exits, at most 256 ETH per 6.4-minute epoch, of 43.66M ETH staked (consensus-specs @ `71c0019`) | 0.13 % | cap |
| Ethereum | the largest exit queue, 7.5 % of the 35.58M ETH staked on 2025-09-13, drained at that cap over 46 days (validatorqueue.com @ `3f32aef`) | 0.16 % | measured |
| Cosmos Hub | ATOM unbonding started in the 21 days to 2026-10-05: 2.1 % of bonded stake | 0.10 % | measured |
| Polkadot | nominator unbonding requests, eras 2296–2314, median per daily era | 0.05 % | measured |
| Cardano | net stake leaving pools, median per 5-day epoch, 2023-03 to 2026-09 (a lower bound) | 0.11 % | measured |
| Solana | stake deactivated, mean per epoch of about 1.9 days over the last 100 epochs | 0.27 % | measured |
| Bitcoin | supply last moved within a month (7.0 %) or a year (36.7 %), 2026-09-18 | 0.24 % / 0.13 % | measured |

Sources: Ethereum consensus-specs @ `71c0019` (`electra/beacon-chain.md`,
`electra/weak-subjectivity.md`) and github.com/etheralpha/validatorqueue-com @ `3f32aef`; Cosmos
Hub staking REST (cosmoshub-4, height 33,271,284); Polkadot Asset Hub staking ledgers, eras
2296–2314; Koios `pool_history`, epochs 400–657; Solana's `StakeHistory` sysvar, epochs 950–1049;
CryptoSlate's supply-age series (Glassnode method), 2026-09-18; Cardano's Shelley genesis
(`slotsPerKESPeriod`) and Algorand's participation-key documentation for the key rules below. The
Cosmos, Polkadot, Cardano and Solana rows are chain scans of a single period. The values are
read from these sources; no target computes them.

Staked value elsewhere moves at 0.05–0.3 % a day, and Bitcoin's supply, the closest match to
Cryptarchia's notes, at 0.13–0.24 % a day over a month to a year. At Bitcoin's rates a 4-hour
window holds a quarter of the stake for a horizon of 38 to 71 days if every freed key can be
bought, and of 16 months to 2.4 years if a tenth can, both without grinding. Across 0.05–0.3 % a
day the first range widens to 32–166 days. The yearly rate understates a month's movement: at
0.125 % a day, 3.7 % of the supply moves in 30 days, against the 7.0 % measured. Ethereum bounds
the same exposure with bonded stake and churn limits. Its weak subjectivity period, 15.7 days at
any stake, is 256 epochs plus the time a balance churn of 1/65,536 of the stake per epoch takes to
move 5 % of it (`electra/weak-subjectivity.md`). Exits, capped at 256 ETH per epoch, move at most
2.1 % of today's stake in that period. Chains
whose stake is never locked protect leader keys instead: Cardano's keys evolve every 36 hours, and
Algorand deletes each round's key once the round ends. A forward-secure leader key would free the
horizon from turnover altogether.

**H6** holds with the trigger of rules 1–6 and fails as the plan first stated it. The self-healing
horizon then stops bounding `k`, and `H` takes its place. Against a quarter of the stake at
Bitcoin's turnover, with every freed key for sale, `H` is 48 to 92 days with an 8-hour window at
`k = 2160` once grinding is counted (B6), and 38 to 71 days with a 4-hour window without it. At
`k = 120`, whose window is at most 4 hours, no horizon holds a quarter with grinding.

## B6 — grinding the epoch nonce

The bounds of B2 and the density test of B5 assume an epoch nonce that no one chose. The next
epoch's nonce is the hash chain `η_B = H(η_parent ‖ ρ_LEAD ‖ sl)` at the last block before the
cut-off slot, `6⌊k/f⌋` into the epoch (protocol, Epoch Nonce). A coalition that withholds its wins
chooses that block. It forks at an honest block `d` canonical blocks before the cut-off and keeps
any `j > d` of the `W_d` wins it made since. Its chain then displaces the honest one. The
coalition therefore picks among `G = 1 + Σ_d S_d` nonces, with `S_d = Σ_{j>d} C(W_d, j)`, and
evaluates at most `B` of them. Let `u` be an attack's chance against the schedule of an honest
nonce. Against a nonce picked among those it evaluates, the chance is at most
`φ(u) = E[min(1, u·min(G, B))]`, a union bound over the choices. The coalition is allowed to
evaluate its choices before the honest chain grows past its fork.

- **After the cut-off.** The nonce is final only once the chain past the cut-off is. A coalition
  that keeps winning after the cut-off can complete a fork that holds fewer of its earlier wins.
  With `Z` the most its private chain ever leads the public one after the cut-off, a fork from
  `d ≥ 1` needs only `j > d − Z` of its `W_d` wins, so `S_d = Σ_{j>d−Z} C(W_d, j)`.
- **Two epochs.** An attack whose schedule spans the end of an epoch meets two nonces, picked at
  two cut-offs with independent choices `G` and `G'`. A target past its epoch's cut-off, whose
  race reaches the next epoch, faces such an attack. Its chance is at most
  `φ_2(u) = E[min(1, u·min(G, B)·min(G', B))]`.

`src/finality_sim/grinding.py` reads the coalition's lead `L_d = W_d − d` backwards from the cut-off
as a random walk, under the delay models of B5, and `Z` as the same walk forwards. From the walk it
computes two bounds on `φ` exactly, each mixed over `Z`:

- the lower one counts the fork point with the most choices, `M = max_d S_d`;
- the upper one adds the choices of every fork point.

Under random delay `Z` is exact. Under a worst case of `Δ` the upper bound takes the first gap after
the cut-off whole, and the lower one leaves the coalition's wins in it out. `φ` is concave with
`φ(0) = 0`. So `φ_2(u)` is at most the smaller of `φ(u) + Σ_d E[φ(u·min(S'_d, B))]` and, for every
threshold `x`, `φ(uB)·P(M' ≥ x) + φ(u)·(1 + Σ_d E[S'_d; S'_d < x])`, where primes mark the second
epoch and each `φ` is at its upper bound. From below, `G ≥ max(1, M)` in each epoch. To hold `ε`,
the chance against one schedule must fall by the factor `R = ε/u*`, where `φ(u*) = ε`, and likewise
by `R_2` for `φ_2`. The depth that holds `ε/R` is read off the attack's own chance: B5's closed form
under random delay, and B2's upper bound under a worst case of `Δ` (`scripts/b6_grinding.py`). The
budget *sets* the factor where `R > ε·B`.

Not counted: orphaned honest blocks as fork points; slots the coalition wins more than once; a
schedule that an earlier grinding picked; and an attack longer than `4⌊k/f⌋` slots, which crosses
a cut-off of its own and can pick its own nonce.

Gates (`tests/test_grinding.py`, `tests/test_b6_reading.py`): the walk's lead and the largest
single choice match a slot-by-slot simulation under both delay models; the table given `Z` counts
the choices directly, and one walk mixes it over `Z` as a walk for each `Z` does; the simulated
`φ` lies between the bounds, and the forks completed after the cut-off take it above the upper
bound that leaves them out; `Z` follows the forward walk; two independently simulated epochs lie
between the pair's bounds and above one epoch's upper bound; doubling the walk's truncation moves
no bound; without stake the factor is one; the factors bracket where the bounds cross `ε`; the
lower bound lies below its integral; and the readings below take each age once and the upper bound
at the next larger `u`. Twenty-four mutations fail them.

With `B = 2^64`:

| delay | α | epochs with a choice | factor at 1e-9, one nonce | two nonces | set by the budget | depth at 1e-9 → one nonce → two nonces |
| --- | --- | --- | --- | --- | --- | --- |
| random, testnet | 0.10 | 11 % | 1.0–1.3 | 1.0–1.7 | – | 17 → 17 → 17 |
| random, testnet | 0.20 | 26 % | 3.0–9.8 | 8.6–72 | – | 41 → 44–46 → 46–51 |
| random, testnet | 0.25 | 34 % | 2,700–1e4 | 3e4–1e6 | – | 66 → 94–100 → 103–115 |
| random, testnet | 0.30 | 44 % | 2e9–2e10 | 1e11–3e13 | yes | 111 → 240–255 → 265–299 |
| random, testnet | 0.33 | 51 % | 2e12–6e12 | 4e17–2e21 | yes | 169 → 425–436 → 539–614 |
| random, specification | 0.10 | 13 % | 1.0–1.4 | 1.1–1.9 | – | 19 → 19 → 19–20 |
| random, specification | 0.20 | 29 % | 33–130 | 190–2,600 | – | 51 → 61–64 → 65–73 |
| random, specification | 0.25 | 39 % | 2e6–1e7 | 5e7–5e9 | – | 86 → 153–163 → 169–191 |
| random, specification | 0.30 | 51 % | 1e12–3e12 | 8e16–2e20 | yes | 161 → 402–412 → 500–570 |
| random, specification | 0.33 | 59 % | 2e14–6e14 | 6e26–1e29 | yes | 269 → 743–762 → 1,164–1,239 |
| worst, 10 s | 0.10 | 12 % | 1.0–1.3 | 1.0–1.8 | – | 114 → 114–116 → 114–117 |
| worst, 10 s | 0.20 | 27 % | 11–58 | 41–970 | – | 281 → 314–337 → 332–376 |
| worst, 10 s | 0.25 | 37 % | 2e5–3e6 | 3e6–7e8 | – | 474 → 759–819 → 824–950 |
| worst, 10 s | 0.30 | 48 % | 3e11–2e12 | 2e15–1e19 | yes | 892 → 2,056–2,124 → 2,424–2,825 |
| worst, 10 s | 0.33 | 57 % | 8e13–4e14 | 5e24–1e28 | yes | 1,510 → 3,879–3,994 → 5,732–6,287 |

- **Below a fifth of the stake the guarantee needs little more depth.** At 10 % the factor is at
  most 1.4 for one nonce and 1.9 for two, and the depth grows by at most 3 blocks.
- **Against a quarter of the stake, two nonces need 1.6 to 2.2 times the depth.** On the
  specification's Blend, 86 blocks become 153–163 with one nonce and 169–191 with two. Under the
  worst case at 10 s, 474 become 759–819 and 824–950.
- **Against 30 % and a third, two nonces need 2.4 to 4.6 times the depth.** On the specification's
  Blend a third needs 1,164–1,239 blocks instead of 269. Under the worst case at 10 s, 30 % needs
  2,424–2,825 instead of 892, and a third 5,732–6,287 instead of 1,510.
- **From 30 % the budget sets the one-nonce factor** in every delay model.
- The depths with two nonces take 0.2–18 hours on the attack clock under random delay, and 1.4–96
  hours under the worst case at 10 s. Against a third under the worst case, 96 hours exceed the
  `4⌊k/f⌋ = 72` hours of today's `k`.

B2's upper bound at `ε = 1e-9`, in blocks, without grinding → with two nonces, at the upper end of
the factor (`runs/b6/delays.csv` also holds one nonce):

| α | nonces evaluated | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 2^64 | 45 → 45 | 47 → 47 | 49 → 50 | 54 → 55 | 64 → 65 | 73 → 73 | 100 → 101 | 140 → 142 |
| 0.10 | 2^64 | 75 → 76 | 78 → 80 | 81 → 83 | 89 → 91 | 102 → 105 | 114 → 117 | 153 → 158 | 212 → 220 |
| 0.15 | 2^64 | 116 → 123 | 121 → 128 | 126 → 134 | 138 → 147 | 159 → 171 | 177 → 191 | 236 → 261 | 328 → 371 |
| 0.20 | 2^64 | 179 → 215 | 188 → 227 | 197 → 241 | 216 → 271 | 252 → 328 | 281 → 376 | 380 → 550 | 537 → 850 |
| 0.25 | 2^40 | 288 → 470 | 303 → 503 | 319 → 539 | 354 → 622 | 420 → 780 | 474 → 917 | 661 → 1,421 | 971 → 2,307 |
| 0.25 | 2^64 | 288 → 477 | 303 → 511 | 319 → 549 | 354 → 637 | 420 → 805 | 474 → 950 | 661 → 1,493 | 971 → 2,473 |
| 0.30 | 2^40 | 495 → 1,163 | 525 → 1,254 | 558 → 1,353 | 632 → 1,587 | 773 → 2,044 | 892 → 2,436 | 1,325 → 3,818 | 2,105 → 6,374 |
| 0.30 | 2^64 | 495 → 1,230 | 525 → 1,338 | 558 → 1,458 | 632 → 1,742 | 773 → 2,312 | 892 → 2,825 | 1,325 → 4,884 | 2,105 → 8,617 |
| 0.33 | 2^40 | 758 → 2,119 | 812 → 2,295 | 871 → 2,487 | 1,008 → 2,938 | 1,275 → 3,828 | 1,510 → 4,617 | 2,426 → 7,755 | 4,282 → 14,255 |
| 0.33 | 2^64 | 758 → 2,523 | 812 → 2,784 | 871 → 3,079 | 1,008 → 3,780 | 1,275 → 5,082 | 1,510 → 6,287 | 2,426 → 10,854 | 4,282 → 20,032 |

- **`k = 2160` cannot be shown to hold 30 % or a third at 10 s once two nonces are ground.** Against
  a third, these bounds prove `k = 2160` with two ground nonces only at 1 s against a coalition
  that evaluates `2^40` nonces an epoch (1,992–2,119 blocks). Against `2^64` even the lower end of
  the factor needs 2,170 blocks at 1 s. With one nonce they prove it up to 5 s against `2^40` and
  up to 2 s against `2^64`. Against 30 %, two nonces are proven up to 8 s against `2^40` and up to
  5 s against `2^64`.
- At 30 % from 15 s, and at a third from 8 s, the depths with two nonces against `2^64` take longer
  than 72 hours on the attack clock, outside the model.

The largest share each `k` holds at `ε = 1e-9`, without grinding → with two nonces, at the upper
end of the factor and `B = 2^64` (`runs/b6/shares.csv` also holds one nonce):

| delay | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| random, testnet | 0.447 → 0.391 | 0.428 → 0.359 | 0.391 → 0.317 | 0.351 → 0.283 | 0.307 → 0.252 |
| random, specification | 0.413 → 0.359 | 0.394 → 0.328 | 0.358 → 0.288 | 0.320 → 0.256 | 0.278 → 0.227 |
| worst, 1 s | ≥ 1/3 → 0.326 | ≥ 1/3 → 0.293 | 0.288 → 0.244 | 0.221 → 0.200 | 0.155 → 0.148 |
| worst, 2 s | ≥ 1/3 → 0.322 | ≥ 1/3 → 0.289 | 0.283 → 0.240 | 0.215 → 0.196 | 0.150 → 0.143 |
| worst, 3 s | ≥ 1/3 → 0.318 | ≥ 1/3 → 0.285 | 0.278 → 0.236 | 0.210 → 0.192 | 0.145 → 0.139 |
| worst, 5 s | ≥ 1/3 → 0.310 | ≥ 1/3 → 0.277 | 0.268 → 0.228 | 0.200 → 0.183 | 0.135 → 0.130 |
| worst, 8 s | ≥ 1/3 → 0.297 | 0.323 → 0.264 | 0.253 → 0.216 | 0.184 → 0.170 | 0.118 → 0.114 |
| worst, 10 s | ≥ 1/3 → 0.288 | 0.313 → 0.256 | 0.242 → 0.208 | 0.172 → 0.161 | 0.106 → 0.103 |
| worst, 15 s | 0.328 → 0.267 | 0.287 → 0.235 | 0.213 → 0.186 | 0.140 → 0.133 | 0.072 → 0.069 |
| worst, 20 s | 0.301 → 0.244 | 0.258 → 0.212 | 0.179 → 0.161 | 0.102 → 0.098 | < 0.05 → < 0.05 |

- **With two ground nonces today's `k` holds less than a third.** At `k = 2160` the share falls to
  0.359 under random delay on the specification's Blend, and to 0.288–0.326 guaranteed for delays
  of 1–10 s.
- **A tenth of today's `k` holds less.** At `k = 216` the share falls from 0.320 to 0.256 on the
  specification's Blend under random delay. The share guaranteed for delays of 1–10 s falls from
  0.172–0.221 to 0.161–0.200.

**The recovery horizon.** The window after a divergence point lies within the lottery parameters
fixed before it (B5, rule 5). An epoch is `10⌊k/f⌋` slots long and the window at most `4⌊k/f⌋`. A
divergence point within one window of its epoch's end has a window that reaches the next epoch, so
its chance meets both nonces. Over a horizon `H` the chance is then at most the sum, over its
epochs, of the upper bound on `φ` at the epoch's other points and the upper bound on `φ_2` at
these, each at the sum of their chances against honest nonces. The horizon holds at the worst of
48 phases of the epoch boundaries. The longest `H` that holds `1e-9`, in days, without / with
grinding, on the specification's Blend under random delay, with `B = 2^64`, every freed key for
sale, and each `k` at its longest window. Each cell spans Bitcoin's monthly and yearly turnover,
0.243 % and 0.125 % a day (`runs/b6/recovery.csv` also holds a tenth of the freed keys, shorter
windows and the worst case at 10 s):

| k | window | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 2160 | 72 h | 273–530 / 262–508 | 210–406 / 185–358 | 147–285 / 107–207 | 106–205 / 57–111 |
| 1620 | 54 h | 261–504 / 248–481 | 198–384 / 171–330 | 137–265 / 93–179 | 97–186 / 43–83 |
| 1080 | 36 h | 240–465 / 227–439 | 180–348 / 149–288 | 121–234 / 70–135 | 82–157 / 21–41 |
| 432 | 14.4 h | 184–354 / 166–320 | 130–250 / 89–171 | 76–145 / 11–19 | 40–75 / < 1 h |
| 216 | 7.2 h | 132–253 / 112–213 | 83–158 / 37–68 | 34–62 / < 1 h | 42–49 h / < 1 h |
| 120 | 4 h | 83–157 / 61–114 | 38–71 / < 1 h | 5 h / < 1 h | < 1 h / < 1 h |

- **Against 30 % and a third only the longest windows hold a horizon with grinding.** At
  `k = 2160` the 72-hour window holds 30 % for 107–207 days and a third for 57–111. At `k = 1080`
  the 36-hour window holds 70–135 and 21–41 days. At `k = 432` the 14.4-hour window holds 30 % for
  11–19 days and a third for none.
- **Without grinding the same windows hold a third for weeks down to `k = 432`.** At `k = 432` the
  horizon is 40–75 days, and at `k = 216` 42–49 hours.
- **Shorter windows hold less.** At `k = 2160` with grinding, a 4-hour window holds no horizon
  against a quarter, and an 8-hour window holds a quarter for 48–92 days and 30 % for none.

