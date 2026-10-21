# Settlement

Phase B of `PLAN.md`. Tables come from `runs/` through `scripts/tables.py`; runs from
`scripts/b2_settlement.py`, `scripts/b2_lower.py`, `scripts/b3_race.py`, `scripts/b3_delay.py`,
`scripts/b4_elapsed.py`, `scripts/b5_what_k_holds.py`, `scripts/b5_recovery.py`,
`scripts/b5_recovery_sweep.py`, `scripts/b6_grinding.py` and `scripts/b7_nonce.py`.

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
- **In time**, on the honest chain while the coalition withholds. Under a worst case of `Δ` the
  canonical chain grows one block per `Δ + 1/p_h` slots, `p_h` the honest stake's chance to win a
  slot (B5): at `Δ = 10` s, 43.3 s a block against 10 %, 49.8 s against 25 %, 52.6 s against 30 %
  and 54.7 s against a third.
  - against 25 %, the guarantee takes 474 blocks, 6.6 h; the attack reaches 143, 2.0 h;
  - against 10 %, 114 blocks, 82 min, against 33, 24 min;
  - under random delays and the private attack (`RATE.md`, C1), 69 and 12 minutes;
  - k-finality takes 29.9 h and 26.0 h.
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
  race with a premined lead (B3) in B5's closed form, in which the coalition withholds every win,
  never extends the public chain, and does not choose Blend's delays; under a worst case of `Δ`,
  any attack (B2);
- grinding of the epoch nonce no stronger than the depth includes (B6, B7);
- the node's own view is not eclipsed.

The depth table is the RFC candidate: B2 for the worst case, B5's closed form for random delay. An
API would expose it as a configured `(α, ε)` and a settled level beside `lib` in
`/cryptarchia/info`, with a stream like `lib-stream`.

**Reading elapsed time.** A depth rule holds `ε` on average over the times at which blocks arrive,
and a client sees those times. Per slot, the coalition wins with probability `a = α·λ` and the
canonical chain grows with probability `h = (1 − α)·g·λ`, where `λ = −ln(1 − f)` and `g` is A1's
growth on the specification's Blend; `q = a/(a + h)` is then B5's. Just before the target's parent
appears, the coalition's lead over the public chain is stationary, geometric with ratio `a/h`
(B3); the parent takes one block from it. When the `n`-th canonical block counting the target
appears `t` slots after that parent, the coalition holds that lead plus a Poisson number of blocks
of mean `a·t`, whatever the times of the honest blocks. The client computes the coalition's chance
exactly (Grunspan and Pérez-Marco, "Double spend races", 2018) and accepts at the first block where
it is at most `ε` (`src/finality_sim/elapsed.py`). It reads `t` on its own clock when it evaluates.
Averaged over arrival times, that chance is the depth table's. Given any history of honest blocks
up to acceptance, it is at most `ε` as well, because the lead and the wins are independent of that
history.

The depth rule waits for B5's closed-form depth. Both rules are played on 64 timelines per share,
one epoch at `k = 256`: the engine's, on the specification's Blend with the coalition withholding,
and independent slots of the model both rules assume. The race scores each acceptance itself
(`scripts/b4_elapsed.py`). A cell of 0 means no success among 59,000–124,000 targets:

| timelines | α | ε | depth rule: blocks | depth rule: minutes, mean / p90 | elapsed-time rule: blocks, mean | elapsed-time rule: minutes, mean / p90 | race beats the rule, depth / elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| engine | 0.10 | 1e-3 | 4 | 2.6 / 4.1 | 3.7 | 2.5 / 4.7 | 7.3e-04 / 5.6e-04 |
| engine | 0.10 | 1e-6 | 12 | 7.9 / 10.4 | 9.7 | 6.4 / 10.0 | 0 / 0 |
| engine | 0.10 | 1e-9 | 19 | 12.5 / 15.7 | 15.7 | 10.4 / 15.0 | 0 / 0 |
| model | 0.10 | 1e-3 | 4 | 2.6 / 4.3 | 3.7 | 2.4 / 4.9 | 9.9e-04 / 7.1e-04 |
| model | 0.10 | 1e-6 | 12 | 7.8 / 10.7 | 9.6 | 6.2 / 10.4 | 0 / 0 |
| model | 0.10 | 1e-9 | 19 | 12.3 / 16.0 | 15.5 | 10.1 / 15.3 | 0 / 0 |
| engine | 0.25 | 1e-3 | 24 | 18.5 / 22.6 | 18.5 | 14.2 / 22.8 | 8.4e-04 / 4.0e-04 |
| engine | 0.25 | 1e-6 | 56 | 43.1 / 49.4 | 39.8 | 30.6 / 43.5 | 0 / 0 |
| engine | 0.25 | 1e-9 | 88 | 67.8 / 75.5 | 61.0 | 47.0 / 63.3 | 0 / 0 |
| model | 0.25 | 1e-3 | 24 | 18.6 / 23.5 | 18.6 | 14.4 / 24.7 | 5.0e-04 / 7.7e-04 |
| model | 0.25 | 1e-6 | 56 | 43.4 / 50.7 | 40.0 | 31.0 / 46.4 | 0 / 0 |
| model | 0.25 | 1e-9 | 88 | 68.1 / 77.1 | 61.4 | 47.5 / 67.0 | 0 / 0 |
| engine | 0.30 | 1e-3 | 47 | 38.5 / 44.8 | 33.9 | 27.8 / 43.5 | 2.7e-04 / 1.1e-03 |
| engine | 0.30 | 1e-6 | 105 | 85.9 / 95.3 | 70.4 | 57.7 / 81.3 | 0 / 0 |
| engine | 0.30 | 1e-9 | 165 | 134.9 / 146.4 | 106.6 | 87.1 / 116.7 | 0 / 0 |
| model | 0.30 | 1e-3 | 47 | 38.7 / 45.8 | 34.1 | 28.0 / 45.6 | 2.7e-04 / 5.4e-04 |
| model | 0.30 | 1e-6 | 105 | 86.4 / 96.8 | 70.9 | 58.2 / 84.7 | 0 / 0 |
| model | 0.30 | 1e-9 | 165 | 135.7 / 148.4 | 107.6 | 88.4 / 121.7 | 0 / 0 |
| engine | 0.33 | 1e-3 | 81 | 69.3 / 77.8 | 55.1 | 47.2 / 72.1 | 0 / 2.7e-04 |
| engine | 0.33 | 1e-6 | 177 | 151.4 / 164.3 | 112.4 | 96.2 / 133.1 | 0 / 0 |
| engine | 0.33 | 1e-9 | 276 | 236.2 / 252.1 | 169.2 | 144.8 / 192.9 | 0 / 0 |
| model | 0.33 | 1e-3 | 81 | 70.7 / 80.5 | 57.9 | 50.6 / 80.6 | 9.0e-04 / 2.9e-04 |
| model | 0.33 | 1e-6 | 177 | 154.5 / 169.0 | 118.5 | 103.4 / 149.3 | 0 / 0 |
| model | 0.33 | 1e-9 | 276 | 240.8 / 258.3 | 178.3 | 155.5 / 213.1 | 0 / 0 |

- **Reading elapsed time settles about 30 % sooner against a quarter of the stake.** At `1e-9`
  the depth rule waits 88 blocks, 68 minutes on the engine's timelines. The elapsed-time rule
  accepts after 61 blocks on average, in 47 minutes, and its 90th percentile, 63 minutes, is below
  the depth rule's 76. At `1e-3` it takes 14 minutes instead of 18.
- **Against 30 % and a third it settles 35–40 % sooner.** At `1e-9` against a third the depth
  rule waits 276 blocks, 3.9 hours on the engine's timelines. The elapsed-time rule accepts after
  169 blocks on average, in 2.4 hours, and its 90th percentile, 3.2 hours, is below the depth
  rule's mean. Against 30 % the two rules take 2.2 and 1.5 hours.
- **Against a tenth of the stake it settles about a fifth sooner** at `1e-6` and `1e-9`. At
  `1e-3` it gains 7 % on average, and its 90th percentile is 0.6 minutes longer.
- **Both rules hold `ε` where it can be measured.** At `1e-3` and a quarter of the stake, the race
  beats the depth rule on 8.4e-4 of the engine's targets and the elapsed-time rule on 4.0e-4. At
  30 % it beats the elapsed-time rule on 1.1e-3 of 78,696 targets, consistent with `1e-3`:
  successes come in clusters, so the naive standard error, 1.1e-4, understates the spread.
- **The per-history guarantee holds inside the rule's model only.** A coalition that also extends
  the public chain changes the history the client reads. Under a worst case of `Δ` the rule fails:
  B3's delay-scheduling attack beats it in 51–58 % of the targets it accepts, since the coalition
  then controls the clock the rule reads; what a client can read under the worst case is the
  counting bound of `DESIGNS.md` H.3.
- **The rates hold while the inferred stake is the true stake.** The total-stake inference sets
  the lottery's thresholds from the previous period's occupied slots, so a coalition that
  withholds for a whole period raises every rate by `1/(1 − α)`: the honest chain then runs at
  `g·λ` and the coalition wins at `α·λ/(1 − α)`. The depth rule is unmoved, since `q` is. The
  elapsed-time rule must then take those rates, with the depth rule as its cap; it settles a chain
  nobody withholds from in 66 / 106 minutes against 30 % / a third on the specification's Blend,
  and a chain the coalition withholds from at the depth rule's depth (`FURTHER.md`, G4).

Gates (`tests/test_elapsed.py`, `tests/test_race.py`): averaged over arrival times, the chance is
the depth table's closed form, with the lead and without; that closed form equals the race's at
every depth checked; each deadline is the latest time that settles; the race's per-target depths
count what the race counts; on the model's timelines the rule holds `ε = 0.01` against the premined
race, which it would not with its clock started at the target; in each of five bands of how fast
the blocks came, the rule holds `ε = 0.01`, while the depth rule exceeds `3ε` in the slowest band.
Eight mutations fail them.

## B5 — a smaller `k`

The largest attacker share each `k` holds without grinding (B6 adds it), under random delays (the
private race with a premined lead and the strict tie rule, B5's closed form), at the canonical
growth A1 measured:

| Blend | growth / f | ε | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| testnet (1 hop, 1 round) | 0.971 | 1e-6 | 0.455 | 0.439 | 0.409 | 0.376 | 0.340 |
| testnet (1 hop, 1 round) | 0.971 | 1e-9 | 0.446 | 0.427 | 0.390 | 0.349 | 0.305 |
| testnet (1 hop, 1 round) | 0.971 | 1e-12 | 0.438 | 0.416 | 0.373 | 0.327 | 0.277 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-6 | 0.421 | 0.406 | 0.376 | 0.344 | 0.309 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-9 | 0.412 | 0.393 | 0.357 | 0.319 | 0.276 |
| specification (3 hops, 3 rounds) | 0.845 | 1e-12 | 0.404 | 0.383 | 0.341 | 0.297 | 0.250 |

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
7. **Break ties.** Under a strict order two chains of equal density keep their own nodes. Two
   honest sides of an even split tie with probability 0.5–0.7 % at the longest windows
   (`scripts/b5_partition.py`, below), and would then never heal. On equal densities both sides
   adopt the chain picked by a rule that reads the two chains alone, such as the smaller block id
   at the first slot after the divergence.
8. **Compare only from a chain that had its full density.** Every window and horizon above gives
   the honest chain the whole honest stake. A split deeper than `k` that is not an eclipse is a
   partition, and during a partition each honest side produces with its own share while the
   coalition withholds a fork made with all of its stake. Against an honest side of 35 % of all
   stake, a 30 % coalition's fork is denser in 64–70 % of the specification's windows; against an
   honest third, a third's fork always is (the first table below). Today the Online rule caps
   what such a fork reorganises at `k`; the trigger would lift the cap to `H`. A node therefore
   compares densities only if its own chain held, over the window, at least the blocks the honest
   stake `1 − α` makes at the model's `ε` tail. A node whose chain was sparser stays on it and
   leaves the split to operators, as today. The trigger then heals an eclipse, where one side is
   the whole honest chain, and not a partition deeper than `k`. `DESIGNS.md` H.1 states why no
   local rule can at a third, and gives a one-off vote round that does below it.

The density test during a partition (rule 8): the chance that the coalition's fork is strictly
denser than an honest side holding a share `s` of all stake, over a window, and the largest `s`
the fork beats in expectation (`runs/b5/partition.csv`):

| delay | α | window | side beaten in expectation | side 0.300 | side 0.333 | side 0.350 | side 0.400 | side 0.450 | side 0.500 | the whole honest chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.25 | 36 h | ≤ 0.296 | 0.37 | 0.002 | 2e-05 | 1e-14 | 6e-28 | 7e-45 | 4e-168 |
| random, specification | 0.25 | 72 h | ≤ 0.296 | 0.32 | 2e-05 | 4e-09 | 3e-27 | 8e-54 | 1e-87 | 0e+00 |
| random, specification | 0.30 | 36 h | ≤ 0.355 | 1 | 0.94 | 0.64 | 8e-04 | 6e-11 | 7e-22 | 7e-95 |
| random, specification | 0.30 | 72 h | ≤ 0.355 | 1 | 0.99 | 0.7 | 5e-06 | 5e-20 | 9e-42 | 2e-187 |
| random, specification | 0.33 | 36 h | ≤ 0.395 | 1 | 1 | 1 | 0.36 | 1e-04 | 6e-12 | 7e-59 |
| random, specification | 0.33 | 72 h | ≤ 0.395 | 1 | 1 | 1 | 0.3 | 1e-07 | 5e-22 | 2e-115 |
| worst, 10 s | 0.25 | 36 h | ≤ 0.273 | 0.016 | 2e-06 | 2e-09 | 8e-21 | 4e-36 | 2e-54 | 4e-177 |
| worst, 10 s | 0.25 | 72 h | ≤ 0.273 | 0.0012 | 2e-11 | 6e-17 | 1e-39 | 5e-70 | 1e-106 | 0e+00 |
| worst, 10 s | 0.30 | 36 h | ≤ 0.334 | 0.99 | 0.51 | 0.12 | 3e-06 | 6e-15 | 6e-27 | 8e-99 |
| worst, 10 s | 0.30 | 72 h | ≤ 0.334 | 1 | 0.52 | 0.052 | 6e-11 | 6e-28 | 9e-52 | 3e-195 |
| worst, 10 s | 0.33 | 36 h | ≤ 0.376 | 1 | 1 | 0.96 | 0.054 | 1e-06 | 7e-15 | 7e-61 |
| worst, 10 s | 0.33 | 72 h | ≤ 0.376 | 1 | 1 | 0.99 | 0.012 | 9e-12 | 7e-28 | 1e-119 |

Two honest sides of an even split, without a coalition, tie over the window with probability
(`runs/b5/ties.csv`):

| k | window | blocks a side, mean | P(tie) |
| --- | --- | --- | --- |
| 2160 | 72 h | 3,683 | 0.0047 |
| 1620 | 54 h | 2,762 | 0.0054 |
| 1080 | 36 h | 1,841 | 0.0066 |
| 120 | 4 h | 205 | 0.0199 |

**On the engine.** The engine splits the honest nodes into a side holding a share of all stake and
the rest for a span of 36 hours while the coalition withholds (`tsi_sim`, `partition_share`;
`finality_sim.partition`, `scripts/b5_partition_engine.py`). A block made on one side reaches the
other at the span's end. A Blend copy whose relay lies across the cut is lost, so most blocks reach
their own side by the sender's fallback, 16 rounds late. Within a side, gossip takes the full
graph's shortest paths, as if each side's peers formed a connected graph of their own. A side's
density counts its chain's blocks, as `maxvalid-bg` does, and no uncles are referenced. A side's
growth is per occupied slot: its chain's blocks in the span over the slots its leaders occupied
there. That is the unit of A1's growth and of the closed form. On the specification's Blend with
B3's settings, 256 runs a cell and 512 for the ties, with the coalition's nodes on the rest's side
of the cut and one Blend copy, the closed form is read at the side's realised share, at A1's
growth and at the growth the side showed, with its distance from the engine in standard errors:

| α | side set | side held | density: side / fork | growth per occupied slot: side, rest, A1 | fork denser, engine ± sem | closed form at A1's growth (z) | closed form at the side's growth (z) | chain longer at rejoin: side, rest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 0.30 | 0.300 | 1,131 / 1,098 | 0.863, 0.841, 0.845 | 0.195 ± 0.025 | 0.371 (+7.1) | 0.206 (+0.4) | 0.000, 1.000 |
| 0.25 | 0.35 | 0.350 | 1,293 / 1,093 | 0.845, 0.848, 0.845 | 0.000 ± 0.001 | 0.000 (+0.0) | 0.000 (+0.0) | 0.000, 1.000 |
| 0.25 | 0.40 | 0.400 | 1,448 / 1,095 | 0.829, 0.858, 0.845 | 0.000 ± 0.001 | 0.000 (+0.0) | 0.000 (+0.0) | 1.000, 0.000 |
| 0.30 | 0.30 | 0.300 | 1,129 / 1,310 | 0.862, 0.855, 0.845 | 1.000 ± 0.001 | 1.000 (-0.0) | 1.000 (-0.2) | 0.000, 1.000 |
| 0.30 | 0.35 | 0.350 | 1,292 / 1,311 | 0.844, 0.864, 0.845 | 0.652 ± 0.030 | 0.643 (-0.3) | 0.657 (+0.2) | 0.270, 0.719 |
| 0.30 | 0.40 | 0.400 | 1,446 / 1,316 | 0.828, 0.877, 0.845 | 0.004 ± 0.004 | 0.001 (-0.8) | 0.005 (+0.3) | 1.000, 0.000 |
| 0.33 | 0.30 | 0.300 | 1,130 / 1,453 | 0.862, 0.865, 0.845 | 1.000 ± 0.001 | 1.000 (-0.0) | 1.000 (-0.0) | 0.000, 1.000 |
| 0.33 | 0.35 | 0.350 | 1,291 / 1,455 | 0.845, 0.875, 0.845 | 1.000 ± 0.001 | 0.999 (-1.4) | 0.999 (-1.3) | 0.953, 0.043 |
| 0.33 | 0.40 | 0.400 | 1,446 / 1,455 | 0.829, 0.889, 0.845 | 0.547 ± 0.031 | 0.355 (-6.2) | 0.561 (+0.5) | 1.000, 0.000 |

| sides | copies | runs | density tie, engine | equal length at rejoin | growth per occupied slot: a, b, A1 |
| --- | --- | --- | --- | --- | --- |
| 0.500 / 0.500 | 1 | 512 | 0.0098 | 0.0098 | 0.800, 0.802, 0.845 |
| 0.500 / 0.500 | 2 | 512 | 0.0156 | 0.0156 | 0.813, 0.812, 0.845 |

- **A side grows as the whole network does.** Per occupied slot a side holding 30 %, 35 % and
  40 % of all stake grows at 0.863, 0.845 and 0.829 against the whole network's 0.845: the smaller
  side faster, the larger slower. Two even sides, each losing seven copies in eight across the
  cut, grow at 0.80.
- **The closed form holds at the side's growth.** Read there it lies within half a standard error
  of the engine where the outcome is uncertain: 0.206 against 0.195, 0.657 against 0.652, and
  0.561 against 0.547. Read at A1's growth it misses by six and seven standard errors, 0.371
  against 0.195 and 0.355 against 0.547: where the fork and the side are close, two points of
  growth move the beaten share by nearly twenty.

The coalition's nodes may sit on either side of the cut, as the adversary chooses
(`partition_adversary_side`), and a block proposal may go through the specification's two copies
(`blend_copies`). The share of windows in which the fork is denser than the side, ± sem, with the
coalition's nodes with the rest or beside the side:

| α | side set | with the rest, one copy | beside the side, one copy | with the rest, two copies | beside the side, two copies |
| --- | --- | --- | --- | --- | --- |
| 0.25 | 0.30 | 0.195 ± 0.025 | 0.102 ± 0.019 | 0.148 ± 0.022 | 0.059 ± 0.015 |
| 0.25 | 0.35 | 0.000 ± 0.001 | 0.004 ± 0.004 | 0.004 ± 0.004 | 0.000 ± 0.001 |
| 0.25 | 0.40 | 0.000 ± 0.001 | 0.000 ± 0.001 | 0.000 ± 0.001 | 0.000 ± 0.001 |
| 0.30 | 0.30 | 1.000 ± 0.001 | 1.000 ± 0.001 | 1.000 ± 0.001 | 1.000 ± 0.001 |
| 0.30 | 0.35 | 0.652 ± 0.030 | 0.422 ± 0.031 | 0.637 ± 0.030 | 0.199 ± 0.025 |
| 0.30 | 0.40 | 0.004 ± 0.004 | 0.008 ± 0.006 | 0.004 ± 0.004 | 0.004 ± 0.004 |
| 0.33 | 0.30 | 1.000 ± 0.001 | 1.000 ± 0.001 | 1.000 ± 0.001 | 1.000 ± 0.001 |
| 0.33 | 0.35 | 1.000 ± 0.001 | 0.988 ± 0.007 | 1.000 ± 0.001 | 0.977 ± 0.009 |
| 0.33 | 0.40 | 0.547 ± 0.031 | 0.172 ± 0.024 | 0.504 ± 0.031 | 0.062 ± 0.015 |

At rejoin, between two honest sides of 35 % each against a 30 % coalition:

| coalition's nodes | copies | longer at rejoin: side, rest | equal length |
| --- | --- | --- | --- |
| with the rest | 1 | 0.270, 0.719 | 0.012 |
| beside the side | 1 | 0.777, 0.211 | 0.012 |
| with the rest | 2 | 0.133, 0.867 | 0.000 |
| beside the side | 2 | 0.879, 0.113 | 0.008 |

The threshold of H.1's detector over the 36 hours, at `1e-9` and A1's growth
(`finality_sim.further.detector_power`), against each side's own density:

| α | threshold over 36 h | sides held | runs below it, engine | closed form, least |
| --- | --- | --- | --- | --- |
| 0.25 | 2,445 | 0.30, 0.35, 0.40, 0.45 | 1.000 | 1.000000 |
| 0.30 | 2,274 | 0.30, 0.35, 0.40 | 1.000 | 1.000000 |
| 0.33 | 2,160 | 0.27, 0.30, 0.32, 0.35, 0.37, 0.40 | 1.000 | 1.000000 |

- **The adversary's best placement is with the rest,** where the side under test cannot use its
  relays. From there a 30 % fork beats a 35 % side in 65 % of windows, and from beside the side
  in 42 %; a third's beats a 40 % side in 55 % and 17 %.
- **The specification's two copies help the side a little.** With the coalition with the rest
  the two shares fall to 0.637 and 0.504, and beside the side to 0.199 and 0.062.
- **The rule-8 figures stand where they decide.** The adversary chooses its placement, so the
  first column decides: a 30 % fork is denser than an honest 35 % side in 65 % of windows, 64 %
  with two copies; a third's than an honest third in every one, and than a 40 % side in half.
  Two even honest sides tie in 1.0 % of windows with one copy and 1.6 % with two, against the
  closed form's 0.7 %, within 0.7 and 1.6 standard errors.
- **H.1's detector sees every side.** Every side of every run falls below the detector's
  threshold, as the closed form says. The engine holds every stake estimate at the true stake,
  so this is the detector within one inference period of the split: after it each side's
  inference adapts to its own stake (`DESIGNS.md` H.1).
- **At rejoin the longest-chain rule follows the longer chain,** the larger side's in every run
  where the sides differ by five points of stake. Between two sides of 35 % each the coalition's
  nodes decide: the side they sit with is longer in 72–78 % of runs with one copy and 87–88 %
  with two, and the sides tie in at most 1.2 %. The runs read the longest chain without `B_imm`.
  At `k = 2160` a 36-hour split adds 1,129–1,448 blocks to a side of 30–40 %, fewer than `k`, so
  the Online rule compares the chains. At a `k` below a side's blocks over the split, as at the
  runs' `k = 512`, `B_imm` forbids the switch and the sides stay apart.
- **Gaps that reach no result.** The engine's partition splits only the first epoch of a
  multi-epoch run, and a selfish coalition's releases wait for the span's end across the cut, as
  every other block does. Within a side gossip keeps the full graph's paths: a side drawn at
  random from a degree-6 graph would otherwise fall apart, which a real partition's sides, each
  connected, do not.

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
`ε = 1e-9` (the first B5 table): 0.297 against 0.276 at `k = 120` on the specification's Blend,
even at `1e-12` per window. Over a horizon it holds less. At `k = 120`, whose window is at most
4 hours, it holds a fifth of the stake for 61–114 days at Bitcoin's turnover with grinding, and a
quarter for no horizon (B6).

What the trigger costs:

- `B_imm` is no longer immutable within `H`. Every consumer of the LIB (`MAPPING.md` §3) needs a
  path for a LIB that moves back. The `k`-deep block is then final only against forks that lose
  the density test; the block that nothing reverts lies `H` back.
- The node keeps its block tree and the ledger states its proofs need back to `H`, instead of
  pruning at the LIB, and validates every fork deeper than `k` it is shown, ledger states included.
- A split heals only once the window after its divergence point has passed: 8 hours against a
  quarter of the stake (rule 4).
- A partition deeper than `k` still waits for operators (rule 8).

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

**H6** holds for eclipses with the trigger of rules 1–8, fails for partitions deeper than `k`
(rule 8), and fails as the plan first stated it. For eclipses the self-healing horizon stops
bounding `k`, and `H` takes its place. Against a quarter of the stake at
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
  `φ_2(u) = E[min(1, u·min(G, B)·min(G', B))]`, and `min(G, B)·min(G', B) ≤ B²`. A target before
  the cut-off whose race outlasts the `4⌊k/f⌋` slots to the epoch's end is attacked by a private
  chain forked before the cut-off, which carries a nonce the coalition picks itself; no bound here
  covers it.

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
budget *sets* the factor where `R > ε·B`. Both ends of every range below bound `R` or `R_2`: the
lower end is where the lower bound on `φ` crosses `ε`, and neither end is an attack.

One evaluation costs one hash per slot of the attack window: a note holding a third of the stake
wins a slot with probability `1 − (1 − f)^(1/3) = 0.01124`, more than a third of `f`, so the
coalition loses nothing by keeping its stake in one note. A window of 1,600 blocks at 54.7 s, the
worst-case clock against a third at 10 s, is 87,600 slots: `9.6·10^16` hashes an epoch at
`B = 2^40` and `1.6·10^24` at `2^64`.

Not counted: orphaned honest blocks as fork points; slots the coalition wins more than once; a
schedule that an earlier grinding picked; and the private chain of the two-epochs bullet above,
whose race is longer than `4⌊k/f⌋` slots.

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

| delay | α | epochs with a choice at the cut-off | factor at 1e-9, one nonce | two nonces | set by the budget | depth at 1e-9 → one nonce → two nonces |
| --- | --- | --- | --- | --- | --- | --- |
| random, testnet | 0.10 | 11 % | 1.0–1.3 | 1.0–1.7 | – | 17 → 17 → 17 |
| random, testnet | 0.20 | 26 % | 3.0–9.8 | 8.6–72 | – | 42 → 44–47 → 47–51 |
| random, testnet | 0.25 | 34 % | 2,700–1e4 | 3e4–1e6 | – | 67 → 95–101 → 104–116 |
| random, testnet | 0.30 | 44 % | 2e9–2e10 | 1e11–3e13 | yes | 114 → 243–257 → 268–302 |
| random, testnet | 0.33 | 51 % | 2e12–6e12 | 4e17–2e21 | yes | 172 → 428–439 → 543–618 |
| random, specification | 0.10 | 13 % | 1.0–1.4 | 1.1–1.9 | – | 19 → 19–20 → 19–20 |
| random, specification | 0.20 | 29 % | 33–130 | 190–2,600 | – | 52 → 61–65 → 66–74 |
| random, specification | 0.25 | 39 % | 2e6–1e7 | 5e7–5e9 | – | 88 → 155–164 → 171–193 |
| random, specification | 0.30 | 51 % | 1e12–3e12 | 8e16–2e20 | yes | 165 → 405–416 → 504–574 |
| random, specification | 0.33 | 59 % | 2e14–6e14 | 6e26–1e29 | yes | 276 → 750–768 → 1,171–1,245 |
| worst, 10 s | 0.10 | 12 % | 1.0–1.3 | 1.0–1.8 | – | 114 → 114–116 → 114–117 |
| worst, 10 s | 0.20 | 27 % | 11–58 | 41–970 | – | 281 → 314–337 → 332–376 |
| worst, 10 s | 0.25 | 37 % | 2e5–3e6 | 3e6–7e8 | – | 474 → 759–819 → 824–950 |
| worst, 10 s | 0.30 | 48 % | 3e11–2e12 | 2e15–1e19 | yes | 892 → 2,056–2,124 → 2,424–2,825 |
| worst, 10 s | 0.33 | 57 % | 8e13–4e14 | 5e24–1e28 | yes | 1,510 → 3,879–3,994 → 5,732–6,287 |

- **Below a fifth of the stake the guarantee needs little more depth.** At 10 % the factor is at
  most 1.4 for one nonce and 1.9 for two, and the depth grows by at most 3 blocks.
- **Against a quarter of the stake, two nonces need 1.6 to 2.2 times the depth.** On the
  specification's Blend, 88 blocks become 155–164 with one nonce and 171–193 with two. Under the
  worst case at 10 s, 474 become 759–819 and 824–950.
- **Against 30 % and a third, two nonces need 2.4 to 4.5 times the depth.** On the specification's
  Blend a third needs 1,171–1,245 blocks instead of 276. Under the worst case at 10 s, 30 % needs
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
  30 % the claim holds from `B = 2^40`, 2,246–2,436 blocks, and fails at `2^32`, 2,021–2,133;
  against a third from `2^8`, 2,048–2,215 (B7's budget table). Against a third, these bounds prove
  `k = 2160` with two ground nonces only at 1 s against a coalition that evaluates `2^40` nonces
  an epoch (1,992–2,119 blocks). Against `2^64` even the lower end of
  the factor needs 2,170 blocks at 1 s. With one nonce they prove it up to 5 s against `2^40` and
  up to 2 s against `2^64`. Against 30 %, two nonces are proven up to 8 s against `2^40` and up to
  5 s against `2^64`.
- At 30 % from 15 s, and at a third from 8 s, the depths with two nonces against `2^64` take longer
  than 72 hours on the attack clock, outside the model.

The largest share each `k` holds at `ε = 1e-9`, without grinding → with two nonces, at the upper
end of the factor and `B = 2^64` (`runs/b6/shares.csv` also holds one nonce):

| delay | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| random, testnet | 0.446 → 0.391 | 0.427 → 0.359 | 0.390 → 0.317 | 0.349 → 0.283 | 0.305 → 0.252 |
| random, specification | 0.412 → 0.358 | 0.393 → 0.327 | 0.357 → 0.288 | 0.319 → 0.255 | 0.276 → 0.226 |
| worst, 1 s | ≥ 1/3 → 0.326 | ≥ 1/3 → 0.293 | 0.288 → 0.244 | 0.221 → 0.200 | 0.155 → 0.148 |
| worst, 2 s | ≥ 1/3 → 0.322 | ≥ 1/3 → 0.289 | 0.283 → 0.240 | 0.215 → 0.196 | 0.150 → 0.143 |
| worst, 3 s | ≥ 1/3 → 0.318 | ≥ 1/3 → 0.285 | 0.278 → 0.236 | 0.210 → 0.192 | 0.145 → 0.139 |
| worst, 5 s | ≥ 1/3 → 0.310 | ≥ 1/3 → 0.277 | 0.268 → 0.228 | 0.200 → 0.183 | 0.135 → 0.130 |
| worst, 8 s | ≥ 1/3 → 0.297 | 0.323 → 0.264 | 0.253 → 0.216 | 0.184 → 0.170 | 0.118 → 0.114 |
| worst, 10 s | ≥ 1/3 → 0.288 | 0.313 → 0.256 | 0.242 → 0.208 | 0.172 → 0.161 | 0.106 → 0.103 |
| worst, 15 s | 0.328 → 0.267 | 0.287 → 0.235 | 0.213 → 0.186 | 0.140 → 0.133 | 0.072 → 0.069 |
| worst, 20 s | 0.301 → 0.244 | 0.258 → 0.212 | 0.179 → 0.161 | 0.102 → 0.098 | < 0.05 → < 0.05 |

- **With two ground nonces today's `k` holds less than a third.** At `k = 2160` the share falls to
  0.358 under random delay on the specification's Blend, and to 0.288–0.326 guaranteed for delays
  of 1–10 s.
- **A tenth of today's `k` holds less.** At `k = 216` the share falls from 0.319 to 0.255 on the
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

## B7 — a nonce that resists grinding

B6's factor comes from the choices a hash chain offers at the cut-off. Two changes reduce it: a cap
on the nonces a coalition can evaluate, and a nonce that a withheld block rarely changes. The depth
at `ε = 1e-9` for an attack that meets two nonces (`scripts/b7_nonce.py`):

| nonce | random, specification, α = 0.30 | random, specification, α = 0.33 | worst, 10 s, α = 0.30 | worst, 10 s, α = 0.33 |
| --- | --- | --- | --- | --- |
| not ground | 165 | 276 | 892 | 1,510 |
| hash chain, 2^1 evaluated | 168–177 | 286–296 | 902–954 | 1,544–1,614 |
| hash chain, 2^2 evaluated | 176–188 | 301–316 | 935–1,011 | 1,618–1,717 |
| hash chain, 2^4 evaluated | 191–206 | 330–351 | 1,003–1,098 | 1,762–1,900 |
| hash chain, 2^8 evaluated | 220–236 | 388–413 | 1,142–1,246 | 2,048–2,215 |
| hash chain, 2^16 evaluated | 279–296 | 506–532 | 1,429–1,539 | 2,639–2,812 |
| hash chain, 2^24 evaluated | 339–356 | 625–652 | 1,723–1,837 | 3,236–3,413 |
| hash chain, 2^32 evaluated | 401–417 | 745–772 | 2,021–2,133 | 3,837–4,013 |
| hash chain, 2^40 evaluated | 459–479 | 865–893 | 2,246–2,436 | 4,437–4,617 |
| hash chain, 2^48 evaluated | 482–525 | 986–1,013 | 2,333–2,633 | 5,041–5,221 |
| hash chain, 2^56 evaluated | 495–562 | 1,107–1,134 | 2,386–2,774 | 5,529–5,828 |
| hash chain, 2^64 evaluated | 504–574 | 1,171–1,245 | 2,424–2,825 | 5,732–6,287 |
| smallest contributions, k = 2160, at the cut-off | 165 | 277 | 894 | 1,518 |
| smallest contributions, k = 2160, estimated | 187–189 | 326–333 | 1,057–1,088 | 1,859–1,939 |
| smallest contributions, k = 1620, at the cut-off | 165 | 278 | 895 | 1,522 |
| smallest contributions, k = 1620, estimated | 187–189 | 328–334 | 1,059–1,092 | 1,862–1,943 |
| smallest contributions, k = 1080, at the cut-off | 166 | 280 | 897 | 1,532 |
| smallest contributions, k = 1080, estimated | 188–190 | 329–336 | 1,060–1,093 | 1,873–1,952 |

**A delay function.** Ouroboros Phalanx (CIP-0161 at `cardano-foundation/CIPs` `20c819b`,
2026-06-23; the problem is CPS-0021) keeps Praos's hash chain and derives the nonce from it through
a verifiable delay function, Wesolowski's over a class group. The function is split into 82
independent iterations of 527 s each on a CPU, computed by the first leaders of 1-hour intervals
over an epoch. Every iteration takes the pre-nonce as input, so the coalition computes all 82 for
every nonce it evaluates, on hardware the CIP takes to be 10 times faster: one candidate in 72
minutes on one machine, or one every 53 s on 82. Phalanx also takes the stake distribution one
epoch earlier. In B6's terms the function caps `B` at `⌊N·t_c/(82·52.7 s)⌋` for `N` machines and
the time `t_c` the coalition has. A candidate is a fork point and a subset of the coalition's wins
after it, and its hash-chain value does not depend on the honest blocks the fork drops. The
coalition therefore evaluates a candidate from the moment its last win exists and learns at the
cut-off which candidates are feasible: `t_c` is the window, not the minutes it has to publish.
Over the 54-hour window of `k = 1080`, 82 machines evaluate about 3,700 candidates.

- **Phalanx's cap lies between the `2^8` and `2^16` rows:** against a third under the worst case
  at 10 s, 2,048–2,215 and 2,639–2,812 blocks. A cap of `B = 2` would leave 1,544–1,614.
- **A delay whose input the coalition cannot evaluate before it must choose leaves `B = 1`.**
  With the smallest contributions, the input of the last sub-window can be formed from the
  sub-window's start, so the delay must span the sub-window, with the contribution bound to the
  parent's contribution (`FURTHER.md` G1, `DESIGNS.md` H.2).

**The smallest contributions.** The window before the cut-off, `6⌊k/f⌋` slots, is split into `m`
sub-windows counted back from the cut-off, each `⌊6⌊k/f⌋/m⌋` slots long, the oldest taking the
remainder. The nonce is `η_e = hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, under its own domain separator.
`μ_i` is the smallest `ρ_LEAD` among the canonical blocks of sub-window `i`, or a fixed value if
there is none (`src/finality_sim/nonce.py`). A withheld block changes `μ_i` only if its
contribution would be the smallest.

- **At the cut-off** the coalition can change only the sub-windows after the deepest fork point it
  can complete (B6). In each of them `μ_i` is one of two kinds of value. Either it is the smallest
  contribution among the honest blocks that some feasible fork keeps there. Or it is a coalition
  contribution after the deepest fork point, below the smallest contribution the deepest fork
  keeps. `G_min`, the product over those sub-windows of the number of these values, bounds the
  nonces the coalition can reach at the cut-off.
- **Before the cut-off** the coalition decides, as blocks appear, whether to publish each of its
  own and whether to remove an honest one. Its own block holding the last sub-window's smallest
  contribution so far gives it a nonce to accept or refuse: the earlier minima are fixed, and it
  computes the nonce that results if no later contribution is smaller. An honest block holding it
  can be removed. Raced from its parent, a race from one block behind is won with
  `r² = (p_a/p_c)²`, where `p_a` is the coalition's chance to win a slot and `p_c` the rate of
  canonical honest blocks per slot. Under a worst case of `Δ` the block is lost outright when an
  honest rival or a coalition win falls within `Δ` slots after it, which the coalition delivers
  first. Under random delay a natural tie, at the orphan share, is settled by one win, a race from
  level won with `r`. `c` is the chance that one attempt succeeds (`nonce.displacement`). In
  hindsight the last sub-window's minimum can end at any honest floor exposed by removing the
  smaller honest blocks, or at any coalition contribution below the exposed floor. `c_last` is the
  mean number of such values (`nonce.last_sub_window`), with the coalition attempting every honest
  block, the larger figure, or only the blocks that held the running minimum when they appeared,
  the smaller. A decision in an earlier sub-window is informed only if the coalition holds every
  later minimum, each with chance `p_disp`, and then adds `c_last − 1` values. The factor per
  nonce is therefore about `E[G_min]·c_last·(1 + p_disp/(1 − p_disp)·(c_last − 1))`, the last
  term to first order (`nonce.estimate`). `p_own = p_a/(p_a + p_c)` is the chance that the
  coalition holds a long sub-window's smallest contribution without removing an honest block, and
  `p_disp = p_own/(1 − (1 − p_own)·c)` the chance when it attempts every honest block below its
  own: the smallest is its own, or it is honest, is removed, and the question repeats. These are
  estimates, not bounds: the coalition decides before it knows the later contributions, so a
  hindsight count overstates what it reaches.

The rule needs three conditions:

1. **A contribution bound to the epoch nonce of its slot:** `ρ_LEAD := hash(NONCE_CONTRIB_V1 ‖ η ‖
   sl ‖ noteID ‖ sk)`. Today it depends on the note and the slot alone (Proof of Leadership, Circuit
   Constraints 7). A coalition that creates a note can then choose, among many keys, one whose
   contributions are small in many slots.
2. **Enough sub-windows that the coalition rarely knows the nonce before its notes are fixed.** The
   notes that use the nonce of epoch `e` are those at the start of epoch `e − 1`. The coalition
   learns its wins in epoch `e − 1`, and their contributions, when that epoch's nonce and inferred
   stake are fixed, `4⌊k/f⌋` slots before those notes are fixed. It can then predict the nonce of
   epoch `e`, and the prediction is right if it holds the smallest contribution of every
   sub-window. With a right prediction it chooses its notes' keys so that their contributions are
   the smallest of every later window too. One right prediction therefore holds for every later
   epoch. It holds a sub-window's minimum with chance `p_disp`, 0.58 against a third under the
   worst case, the largest of the table below, and over ten years the chance of a right
   prediction is at most the epochs times `p_disp^m`. Keeping that at or below `1e-9` needs 50
   sub-windows at `k = 2160`. With notes frozen one epoch earlier, as Phalanx does, a prediction
   needs every minimum of two windows, `p_disp^(2m)`, and 25 suffice at `k = 2160`, 26 at
   `k = 1620` and `k = 1080`. `m` is set per `k` from this condition (the third table below).
3. **Sub-windows long enough that forks rarely cross them.** Each sub-window a feasible fork
   reaches multiplies the choices at the cut-off.

Under the delay of `DESIGNS.md` H.2 the contribution bound to the parent's contribution replaces
conditions 1 and 2: no contribution of a branch exists before the block it forks from.

`E[G_min]` with the sub-windows each `k` needs, from 100,000 windows a cell, each drawn slot by
slot over its last 20,000 slots; the standard error is at most 0.3 % at `k ≥ 1080`, and
`DESIGNS.md` H.2 bounds it from B6's walk:

| delay | α | k = 2160, m = 25 | k = 1620, m = 26 | k = 1080, m = 26 | k = 432, m = 27 |
| --- | --- | --- | --- | --- | --- |
| random, testnet | 0.25 | 1.01 | 1.01 | 1.02 | 1.04 |
| random, testnet | 0.30 | 1.02 | 1.02 | 1.03 | 1.12 |
| random, testnet | 0.33 | 1.03 | 1.04 | 1.06 | 1.35 |
| random, specification | 0.25 | 1.01 | 1.02 | 1.03 | 1.08 |
| random, specification | 0.30 | 1.03 | 1.04 | 1.07 | 1.47 |
| random, specification | 0.33 | 1.06 | 1.09 | 1.16 | 14 |
| worst, 10 s | 0.25 | 1.01 | 1.02 | 1.03 | 1.08 |
| worst, 10 s | 0.30 | 1.03 | 1.04 | 1.07 | 1.37 |
| worst, 10 s | 0.33 | 1.06 | 1.09 | 1.16 | 5.38 |

At `k = 2160`: the removal chance `c` of each model, `c_last` from 20,000 windows a cell, and the
factor per nonce, smaller to larger estimate:

| delay | α | p_own | removal | p_disp | at the cut-off | last sub-window | factor per nonce |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, testnet | 0.25 | 0.26 | 0.13 | 0.28 | 1.01 | 1.54–1.56 | 1.89–1.91 |
| random, testnet | 0.30 | 0.31 | 0.21 | 0.36 | 1.02 | 1.76–1.80 | 2.54–2.65 |
| random, testnet | 0.33 | 0.34 | 0.28 | 0.42 | 1.03 | 2.02–2.12 | 3.58–3.92 |
| random, specification | 0.25 | 0.28 | 0.20 | 0.33 | 1.01 | 1.72–1.76 | 2.36–2.45 |
| random, specification | 0.30 | 0.34 | 0.31 | 0.42 | 1.03 | 2.04–2.15 | 3.69–4.10 |
| random, specification | 0.33 | 0.37 | 0.40 | 0.50 | 1.06 | 2.36–2.64 | 5.86–7.31 |
| worst, 10 s | 0.25 | 0.30 | 0.41 | 0.42 | 1.01 | 2.15–2.42 | 3.96–4.93 |
| worst, 10 s | 0.30 | 0.35 | 0.49 | 0.51 | 1.03 | 2.50–2.98 | 6.59–9.44 |
| worst, 10 s | 0.33 | 0.38 | 0.56 | 0.58 | 1.06 | 2.82–3.65 | 10.58–18.08 |

The sub-windows each `k` needs:

| k | epochs in ten years | m, one window | m, two windows | sub-window (slots) |
| --- | --- | --- | --- | --- |
| 2160 | 487 | 50 | 25 | 15,552 |
| 1620 | 649 | 51 | 26 | 11,215 |
| 1080 | 974 | 51 | 26 | 7,476 |
| 432 | 2,435 | 53 | 27 | 2,880 |
| 216 | 4,870 | 54 | 27 | 1,440 |
| 120 | 8,766 | 55 | 28 | 771 |

- **The choices at the cut-off stay small at `k ≥ 1080`:** 1.06 against a third at `k = 2160` and
  1.16 at `k = 1080`. At `k = 432` a sub-window holds 2,880 slots, about 54 canonical blocks, and
  the mean against a third rises to 5–14, resting on rare windows with many choices. A smaller `k`
  needs a window longer than `6⌊k/f⌋` slots.
- **The decisions before the cut-off dominate.** Against a third the factor per nonce is an
  estimated 5.9–7.3 on the specification's Blend and 10.6–18.1 under the worst case at 10 s, where
  a removal within `Δ` is free. Under the worst case at 10 s the depth is then an estimated
  1,859–1,939 blocks at `k = 2160`, against 5,732–6,287 for today's nonce, and 1,862–1,943 at
  `k = 1620`: `k = 1620` does not hold a third. At `k = 1080`, 30 % needs an estimated
  1,060–1,093, at the edge of `k`.
- **A delay function matches the rule only at a cap of about 2.** A delay that outlasts the time
  the coalition has to decide on a block would also remove the decisions before the cut-off
  (`FURTHER.md`, G1).

With this nonce, at the larger estimate, B6's recovery horizon shortens by at most 10 days
against a third at each `k`'s longest window. In days, without grinding / with this nonce, as in
B6, under random delay on the specification's Blend and under the worst case at 10 s:

| delay | k | window | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| random, specification | 2160 | 72 h | 210–406 / 207–402 | 147–285 / 144–279 | 106–205 / 102–197 |
| random, specification | 1620 | 54 h | 198–384 / 196–379 | 137–265 / 134–258 | 97–186 / 92–178 |
| random, specification | 1080 | 36 h | 180–348 / 178–343 | 121–234 / 117–226 | 82–157 / 76–147 |
| worst, 10 s | 2160 | 72 h | 188–364 / 184–357 | 134–259 / 129–251 | 97–188 / 92–178 |
| worst, 10 s | 1620 | 54 h | 178–345 / 175–338 | 125–242 / 120–233 | 89–172 / 83–161 |
| worst, 10 s | 1080 | 36 h | 163–315 / 159–308 | 111–215 / 106–204 | 76–146 / 69–133 |

Not counted: honest blocks lost to natural forks, as fork points; the inferred stake, which the
coalition moves without changing the nonce by withholding blocks that hold no minimum, each block
moving every lottery threshold by one part in `f·6⌊k/f⌋`, 12,960 at `k = 2160`, one knob that
raises both sides' win rate alike; and slots the coalition wins more than once, about one in
17,000.

Gates (`tests/test_nonce.py`): the count bounds the nonces an enumeration of every fork point and
every subset of the coalition's wins reaches, and equals it with one sub-window; a fork wins
exactly where B6's walk counts a choice; the coalition holds a long sub-window's smallest
contribution in proportion to its rate; the removal chance is the race from one behind plus the
free channels, from the rates alone; `p_disp` solves its recursion; the reachable minima of the
last sub-window average `1/((1 − c)(1 − p_own))` when any honest block may be attempted and
`1/(1 − p_own)` without removals; and over today's window at `k = 2160`, against a third under the
worst case at 10 s, no fork reaches past the near slots. Eleven mutations fail them.

## Counted in slots (Phase K)

`SLOTS.md` reads this note with `k` counted in slots. Where each part goes:

- **B2 and B3** become waits. K.1 bounds a wait of `T` slots by B2's bound at the depth the wait
  guarantees, with the honest chain's growth over the wait and the coalition's lead at the target,
  and plays B3's private race scored `T` slots after the target. Against a third at `Δ = 10` s and
  `1e-9` the wait is 26.3 hours, where 1,510 blocks take 23.0 on the worst-case clock.
- **B4's depth rule** becomes a wait, which K.1 gives under random delay: 5.1 hours against a third
  on the specification's Blend, where 276 blocks take 4.1. B4's elapsed-time rule reads blocks and
  time, and stays a client's rule beside the protocol's `K`.
- **B5's table of what each `k` holds** becomes K.2's table of what each `K` holds, and its trigger
  and horizon K.3's splits and eclipses: counted in slots the self-healing horizon is `K` for every
  side.
- **B6's factors** stay the nonce's. K.2 absorbs them in a wait, and K.4 reads B6's two-nonce
  coverage with races that last at most `K` slots: no target meets a nonce its own private chain
  set while `K` is at most `4⌊k/f⌋`.
- **B7's sub-windows** keep their lengths with the epoch (K.4).
