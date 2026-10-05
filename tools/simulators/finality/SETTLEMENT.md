# Settlement

Phase B of `PLAN.md`. Tables come from `runs/` through `scripts/tables.py`; runs from
`scripts/b2_settlement.py`, `scripts/b3_race.py`, `scripts/b3_delay.py`,
`scripts/b5_what_k_holds.py` and `scripts/b5_recovery.py`.

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
Grinding of the epoch randomness is outside the model. The upper bound covers every attack. The
lower bound is the paper's Section 4.7 attack, which needs only uniformly delayed honest
messages.

Gates (`tests/test_lcbounds.py`, mutations in `scripts/check_mutations.py`):

- **Table 1.** The port reproduces all 152 proof-of-stake cells of the revision's Table 1 within
  `1e-3` relative: both bounds, 10 % and 20 % adversary, 2 s and 5 s delay, depths 2–20. Three
  mutations of the port each fail this gate.
- **Convergence.** The original follows the Section 4.7 attack for 80 phases, enough for Table 1
  (depth at most 20) and not beyond it. At a third of the stake and depth 60 the lower bound
  collapses from `6.8e-3` to `5e-12` at 80 phases. The port follows the attack for
  `max(80, 4K)` phases, which leaves Table 1 unchanged and converges past it. A gate checks that
  doubling the phases changes nothing at depth 60, and the 80-phase mutation fails it.

The paper does not state the alphabet and state counts behind its table. The code's defaults
(10 and 19) reproduce it, and 20 and 49 change no cell by more than `5e-5` relative. Beyond the
paper's delays the alphabet must grow, because honest runs lengthen with `D`. B2 sizes it per
point, with at least one state more than the alphabet; the original assumes the alphabet does not
exceed the states.

## B2 — settlement depth over attacker share and delay (worst case)

The bounds at `f = 1/30` for delays `Δ` from 1 s to 20 s. Each cell reads *lower – upper*, in
canonical blocks on top of the target. The paper's attack succeeds out to the lower depth; no
attack succeeds past the upper one. Depths 20–120 were computed. `*` marks a depth extrapolated
past 120 along the measured per-block decay, and `≤ 20` a depth below the computed range.

ε = 1e-06

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 20 – 29 | ≤ 20 – 30 | ≤ 20 – 32 | ≤ 20 – 35 | ≤ 20 – 42 | ≤ 20 – 47 | ≤ 20 – 66 | ≤ 20 – 93 |
| 0.10 | 20 – 48 | 20 – 50 | 21 – 52 | 21 – 57 | 22 – 67 | 22 – 75 | 23 – 101 | 24 – 140* |
| 0.15 | 31 – 75 | 31 – 78 | 32 – 82 | 32 – 90 | 34 – 104 | 35 – 116 | 37 – 156* | 41 – 217* |
| 0.20 | 46 – 116 | 47 – 122* | 48 – 128* | 50 – 141* | 53 – 165* | 56 – 185* | 62 – 251* | 70 – 356* |
| 0.25 | 72 – 187* | 74 – 197* | 76 – 207* | 81 – 231* | 88 – 274* | 94 – 310* | 110 – 434* | 131* – 638* |
| 0.30 | 121* – 318* | 126* – 338* | 131* – 359* | 142* – 406* | 160* – 496* | 175* – 572* | 222* – 850* | 290* – 1348* |
| 0.33 | 182* – 480* | 191* – 513* | 201* – 550* | 222* – 634* | 261* – 798* | 293* – 942* | 402* – 1501* | 584* – 2627* |

ε = 1e-09

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 20 – 45 | ≤ 20 – 47 | ≤ 20 – 49 | ≤ 20 – 54 | 20 – 64 | 20 – 72 | 21 – 100 | 21 – 140* |
| 0.10 | 31 – 74 | 31 – 77 | 32 – 81 | 32 – 88 | 33 – 102 | 34 – 114 | 35 – 153* | 37 – 212* |
| 0.15 | 47 – 115 | 48 – 120* | 48 – 125* | 50 – 137* | 52 – 159* | 53 – 176* | 58 – 236* | 63 – 328* |
| 0.20 | 71 – 179* | 72 – 187* | 74 – 196* | 77 – 215* | 82 – 251* | 85 – 280* | 95 – 379* | 108 – 536* |
| 0.25 | 111 – 285* | 114 – 300* | 117 – 316* | 124* – 351* | 135* – 416* | 143* – 469* | 168* – 654* | 201* – 961* |
| 0.30 | 185* – 484* | 192* – 513* | 200* – 545* | 216* – 616* | 245* – 750* | 267* – 864* | 338* – 1280* | 443* – 2027* |
| 0.33 | 278* – 728* | 292* – 778* | 306* – 833* | 338* – 959* | 397* – 1205* | 446* – 1420* | 612* – 2257* | 888* – 3945* |

Checks:

- Doubling the attack's phases at depth 120 changes no lower bound.
- The skipped symbol mass is below `2e-14` per step.
- Between depths 60–80 and 100–120 the per-block decay ratio changes by at most 0.0009, so the
  extrapolation follows a stable geometric tail. The ratio still rises slowly at the largest
  shares, so the extrapolated depths there are slightly optimistic.

Reading:

- **The proven depth is set by the attacker the protocol must face.** At `ε = 1e-9` and delays
  of 1–10 s it is 74–114 blocks against 10 % of the stake, 285–469 against 25 %, and
  728–1,420 against a third.
- **The attack is not far below the proof.** The gap between the two bounds is a factor of 2.4
  to 3.3 in every cell.
- **In time, at the specification's Blend** (a canonical block every 35.5 s on average, A1;
  `Δ = 10` s):
  - against 25 %, the guarantee takes 469 blocks, about 4.6 h; the attack needs 143, about 1.4 h;
  - against 10 %, 114 blocks (67 min) against 34 (20 min);
  - under random delays and the private attack (`RATE.md`, C1), 51 and 11 minutes;
  - k-finality takes 18–21 h on the same Blend.
- **H1 fails for the guarantee.** At 25 % and `ε = 1e-9` the upper bound exceeds `k/10 = 216`
  at every delay, from 285 blocks at 1 s. The attack stays below 216 up to about 20 s.
- **H2 holds up to a delay of about 14 s.** At a third of the stake the upper bound is 1,420
  blocks at 10 s and 2,257 at 15 s. So `k = 2160` holds `ε = 1e-9` against a third of the stake
  for delays up to about 14 s, and not beyond. The finding is a latency, within that delay.

## B3 — the attacks, simulated

### The private-chain attack under random Blend delays

`src/finality_sim/race.py` plays a private-chain attack on the engine's own timelines. A
coalition holding stake share `α` withholds every block it wins. Honest nodes build the public
chain from honest stake under the engine's Blend delays, and the coalition's winning slots are
recorded. A win can sign a block on any branch, and a chain holds one block per slot, so the
private chain grows by one block per slot the coalition wins.

For each canonical block, the race asks whether the coalition ever releases a chain that
displaces it, once `K` blocks lie on top of it. The race is scored against the best-informed node,
so it bounds what a node with any view can see. It has two settings:

- **Premining.** Before the target, the coalition keeps a private lead that a public block
  erodes. Without premining, it starts at the target's parent.
- **Ties.** Cryptarchia's Online rule keeps the first-seen chain on ties, so the coalition must be
  strictly longer. With ties to the attacker, as in Rosenfeld's race, a tie suffices.

Gates (`tests/test_race.py`): on independent Bernoulli timelines the race reproduces Rosenfeld's
closed form with ties to the attacker, and its strict counterpart, at depths 1–8 and attacker
shares 0.10 and 0.25. Premining never lowers the attacker's success. Two mutations fail these
gates.

64 engine runs per cell, equal stake, 0.1 s links, `f = 1/30`. "q" is the coalition's share of
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

"testnet" is 1 hop of 1 round; "spec" is 3 hops of up to 3 rounds; "heavy" is the TSI report's 3
hops of up to 8 s with 0.5 s links.

- On testnet's and the specification's Blend, Rosenfeld's closed form at the measured `q` lands
  within one to three blocks of the race, usually on the deep side.
- At the heavy point it asks for up to six blocks more than the race at `1e-3`.
- Premining adds one to four blocks, and the strict tie rule removes one to three.

Under random delay, the first look's model (`firstlook.py`) is therefore a sound, slightly
conservative guide to this attack. `RATE.md` (C1) uses it over block rate and delay.

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
  `1e-4` (ratios 0.93–1.02). B2's bounds, computed in continuous time, describe the slot lottery.
- No run exceeds the upper bound.
- The private attack alone, on the same draws and delays, is far weaker: about 30 times less
  successful at 25 % and 10 s at depth 40. The second chain is what the delay model adds. When
  every honest block arrives `Δ` late, an adversarial chain of equal length reaches honest nodes
  first.

## B4 — a client confirmation rule

Today the node exposes two levels, the tip and the LIB (`MAPPING.md` §3). The rule adds a third:
a block is *settled* for `(α, ε)` once `d(α, ε)` canonical blocks lie on top of it. A client that
uses it accepts these assumptions:

- the adversary holds at most `α` of the active stake;
- the delay model the table was computed under: random Blend delays (B3, `RATE.md`) or a worst
  case of `Δ` (B2);
- no grinding of the epoch randomness beyond what the model includes;
- a per-block failure probability of `ε`;
- the node's own view is not eclipsed.

The depth table is the RFC candidate: B2 for the worst case, B3 and `RATE.md` for random delay. An
API would expose it as a configured `(α, ε)` and a settled level beside `lib` in
`/cryptarchia/info`, with a stream like `lib-stream`. A rule that also conditions on elapsed time
(Grunspan and Pérez-Marco; Sompolinsky and Zohar) could settle sooner when blocks come fast.
That is left open.

## B5 — a smaller `k`

The largest attacker share each `k` holds, under random delays (the private race with premining
and the strict tie rule), at the canonical growth A1 measured:

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
bound. Between B2's shares, the log of the depth is interpolated linearly in the share
(`runs/b5/worst_case.csv`):

| Δ | k = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| 1 s | ≥ 1/3 | ≥ 1/3 | 0.289 | 0.220 | 0.155 |
| 2 s | ≥ 1/3 | ≥ 1/3 | 0.284 | 0.215 | 0.150 |
| 3 s | ≥ 1/3 | ≥ 1/3 | 0.279 | 0.210 | 0.145 |
| 5 s | ≥ 1/3 | ≥ 1/3 | 0.268 | 0.200 | 0.135 |
| 8 s | ≥ 1/3 | 0.326 | 0.253 | 0.184 | 0.118 |
| 10 s | ≥ 1/3 | 0.315 | 0.242 | 0.172 | 0.106 |
| 15 s | 0.331 | 0.287 | 0.212 | 0.140 | 0.072 |
| 20 s | 0.303 | 0.258 | 0.178 | 0.102 | < 0.05 |

Testnet's `k = 120` guarantees 0.15 of the stake at a 1 s delay and 0.11 at 10 s. A tenth of
today's `k` guarantees 0.17–0.22 for delays of 1–10 s. That is half of what it holds against the
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
failure matches a Monte Carlo estimate in both models, and the probabilities stay finite at the
longest window used. Five mutations fail them.

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
4. **Size the window for `α` and `ε`, apart from `k`.** The table above gives it.
5. **Keep the window inside the lottery parameters fixed before the divergence.** A chain fixes
   the next epoch's nonce and inferred stake `6⌊k/f⌋` slots into an epoch. A fork that diverges
   just before that slot runs on its own nonce and inferred stake `4⌊k/f⌋` slots later. The window
   may therefore be at most `4⌊k/f⌋` slots. Past that, a sparse fork's inference raises its own
   win rate, the attack `fork-choice.md` describes for long-range forks, and its nonce can be
   ground.
6. **Bound the horizon `H`.** Cryptarchia has no forward security (`CERTIFIED.md` D4). Whoever holds
   the key of a note eligible at the divergence point can sign for it on the fork, where it may be
   unspent though spent on the honest chain. `H` must keep `α` plus the stake whose keys an
   adversary can collect within `H` below the share the window holds. No data on stake turnover
   bounds it yet. `H` also multiplies the chance per window by the blocks it holds: about 2,400 a
   day on the specification's Blend.

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

Under random delay this exceeds what each `k` holds against the private race at `ε = 1e-9` (the
first B5 table): 0.297 against 0.278 at `k = 120` on the specification's Blend, even at `1e-12`
per window. So with rules 1–6 the density test does not limit `k`; the private race does.

What the trigger costs:

- `B_imm` is no longer immutable within `H`. Every consumer of the LIB (`MAPPING.md` §3) needs a
  path for a LIB that moves back.
- The node keeps its block tree and the ledger states its proofs need back to `H`, instead of
  pruning at the LIB.
- A split heals only once the window after its divergence point has passed: 1.7 h against a
  quarter of the stake at `1e-9` per window on the specification's Blend, 4.9 h against a third.

**H6** holds with the trigger of rules 1–6 and fails as the plan first stated it. The self-healing
horizon then stops bounding `k`; `H` takes its place, and `H` waits on data about stake turnover.
