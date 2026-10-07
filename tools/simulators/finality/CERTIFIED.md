# Certified finality

Phase D of `PLAN.md`. Tables come from `scripts/d0_emission_map.py`, `scripts/d1b_committee.py`,
`scripts/d5_privacy.py` and `scripts/d6_votes.py` through `scripts/tables.py`. Status: D0, D1b,
D2, D5 and D6 are measured. D1, D3 and D4 are sketched with the open questions they leave.

## D0 — the emission budget

A vote is a private lottery win: one seat per note per round, Poisson in number. Honest seats vote
once; adversarial seats vote for both sides; offline honest seats cast nothing. Two conflicting
quorums of `Q` need `H + 2A ≥ 2Q`, and a round stalls when `H < Q`
(`src/finality_sim/committee.py`; gates in D2). Every vote
is a Blend emission, so votes multiply a node's lottery emissions by `1 + n/(R·f)` for `n` seats
per round of `R` slots. Blend hides a node's emissions only while they fit its cover quota
(`reports/blend/README.md` §3.10), so the cover rate every node carries must rise by that factor
to keep today's ceiling.

Smallest committee holding both tails at `ε = 1e-9` per round, every honest seat voting, and the
cover multiple at three round lengths:

| α | seats | 90 s | 600 s | 3600 s |
| --- | --- | --- | --- | --- |
| 0.05 | 443 | ×149 | ×23 | ×5 |
| 0.1 | 665 | ×223 | ×34 | ×7 |
| 0.15 | 1,097 | ×367 | ×56 | ×10 |
| 0.2 | 2,085 | ×696 | ×105 | ×18 |
| 0.25 | 5,355 | ×1,786 | ×269 | ×46 |
| 0.3 | 33,473 | ×11,159 | ×1,675 | ×280 |

`runs/d0/emission_map.csv` holds the full map, also at `ε = 1e-6` and `2^-40`, at round lengths
from 30 s to an hour, and with the losses of D2. The owner draws the budget line on it (Q7).

Design (a) of D1 certifies a block `L` slots after its publication, plus half a round on average,
plus one Blend delivery (D6); whether its certificate makes the block final is open (D1). The
two-round gadget (b) finalizes, one round later. With 10-minute rounds and `L = 60` slots, (a)
takes about 6 minutes and (b) about 16. Against random Blend delays and at 30 s blocks, settlement
on the chain takes 10–12 minutes against 10 % of the stake and 45–68 minutes against 25 %, from
testnet's Blend to the specification's (`RATE.md`, C1). So:

- **Against 10 %,** (b) finalizes in about 16 minutes at ×34 cover, against 10–12 minutes of
  settlement.
- **Against 25 %,** it finalizes in about 16 minutes at ×269 cover, against 47–69 minutes.
- **Against 30 %,** the committee needs ×1,675 cover and exists only while every honest vote
  counts (D2).

Under a delay chosen by an adversary, a shallow target can be split (D6), and settlement on the
chain is slower too (`SETTLEMENT.md`, B2).

## D2 — committee realism: the share of honest votes that count

Offline stake and votes lost in Blend cast nothing. Honest votes split between forks are cast,
but each counts for one side only. A round stalls when the honest votes that count for one side
fall short of `Q`. Safety must count every honest seat, because split votes can fill both
conflicting certificates. Expected seats are `n` times `D/D̂`, the true over the inferred total
stake, so at a fixed `Q` a low estimate makes two quorums easier to reach. The inference holds the
true stake to within ±0.9 % per epoch (TSI report §2.2); 1.05 is about six standard deviations.
The quorum holds safety at the largest `D/D̂` it is sized for, and liveness at `D/D̂ = 1`. Seats per
round at `ε = 1e-9`:

| α | all count | all count, D/D̂ ≤ 1.05 | 90 % count | 90 % count, D/D̂ ≤ 1.05 | 80 % count |
| --- | --- | --- | --- | --- | --- |
| 0.05 | 443 | 514 | 691 | 833 | 1,273 |
| 0.10 | 665 | 801 | 1,137 | 1,453 | 2,484 |
| 0.15 | 1,097 | 1,392 | 2,156 | 3,056 | 6,617 |
| 0.20 | 2,085 | 2,945 | 5,458 | 9,921 | 46,075 |
| 0.25 | 5,355 | 9,728 | 31,617 | 229,888 | none |
| 0.30 | 33,473 | 279,488 | none | none | none |

- **Against a quarter of the stake,** a tenth of the honest votes not counting multiplies the
  committee by 5.9, and the inference's noise by 1.8. Losing a fifth leaves no committee.
- **Against 30 %,** a committee exists only while every honest vote counts.
- A sudden loss of stake acts as offline stake until the inference reads it. The inference reads
  the first `6⌊k/f⌋` slots of each epoch (`cryptarchia-total-stake-inference.md`, `PERIOD`), so a
  loss just after them lasts about 1.4 epochs.

Gates (`tests/test_committee.py`): the safety tail equals a direct convolution, with and without
inflation; liveness counts only the votes that count; the committee is the smallest that holds
both tails; no committee exists once the quorum cannot fit. Three mutations fail them.

## D1 — design sketches

Each design keeps C1–C5 (`PLAN.md` §0): seats are private lottery wins, votes travel through
Blend (Q6), and a failed round stalls finality without halting the chain.

**The common pieces.**

- **Seat.** A note wins a seat in round `r` when
  `hash(VOTE_V1 ‖ η ‖ r ‖ noteID ‖ sk)` falls below a threshold. The threshold is set from the
  inferred stake so that all stake together expects `n` seats. A note holds at most one seat a
  round. The Poisson seat counts of D0 and D2, and the vote counts of D5, assume each note is far
  below `1/n` of the stake: 0.019 % at 5,355 seats.
- **Tag.** `ρ_VOTE = hash(VOTE_TAG_V1 ‖ r ‖ noteID ‖ sk)`, the construction of `ρ_LEAD` under a
  vote domain. It is fixed per note and round, so a node counts each seat once and sees a seat
  that votes twice. Tags of different rounds are unlinkable.
- **Proof.** As the proof of leadership: the note was in the aged note set, the ticket is below
  the threshold, the tag is well formed, and the proof is bound to the voted block.
- **Target.** The block at least `L` slots back on the voter's chain, so that honest votes
  rarely split between forks (Peras's `L`).
- **Eligibility.** Stake moved during the epoch votes nothing, as Crypsinous rules for
  leadership.

**(a) A Peras-style certificate.** `Q` votes on one block within a round form a certificate. The
certificate adds weight `B` to the block in fork choice. A round without one starts a cool-down
in which the chain runs as today. Peras's proofs assume private sortition with a known expected
committee size. Anonymous seats are private, and their expected number is `n·D/D̂`, known to the
inference's error (D2). Whether those proofs carry over to Poisson seat counts and to votes
delayed by Blend is the open question.

**(b) A two-round checkpoint gadget.** A certificate in round `r` justifies a block; a certificate
in round `r + 1` on a descendant finalizes it. A finalized block is never reverted: `B_imm`
becomes at least the latest finalized block, in commit, pruning and header rule 8.

**(c) Endorsements carried in blocks.** Votes are collected by block producers as transactions,
and the certificate forms across the blocks of a window. This saves a gossip path, but a leader
can leave votes out, so the window must span many leaders.

**All three.** Finality that arrives sooner than the uncle window (`W·f⁻¹` = 360 slots) would
prune uncle candidates the stake inference still counts, unless pruning is decoupled from
finality (`MAPPING.md` §6).

## D1b — the opt-in public committee (Q4)

Holders who choose to reveal their stake register it, for example as a declaration with a locked
note, and vote under their identity; everyone else stays private. Public votes need no seats, so
the committee can be weighted by stake, signatures can be aggregated, and votes can be gossiped
directly. A certificate needs two thirds of the declared stake.

**The share that must declare.** An adversary holding `α` declares all of it. Honest holders
declare a share `v` of the honest stake, of which a share `u` is online. Two conflicting
certificates need the adversary to hold a third of the declared stake, and a certificate needs the
online honest stake to reach two thirds of it. Both hold when `v` exceeds
`2α / ((1 − α)(3u − 2))` (`src/finality_sim/privacy.py`). Each cell gives `v`, then the number of
the largest pools that reach it if the honest stake is spread as Cardano's 2,522 pools are, 31 of
them empty (the analysis `analysis-cryptarchia-de-anonymisation-of-relative-stake.md`, its
`pools.csv`; `scripts/d1b_committee.py`):

| α | uptime 1 | uptime 0.95 | uptime 0.9 |
| --- | --- | --- | --- |
| 0.10 | 0.22 / 72 | 0.26 / 85 | 0.32 / 106 |
| 0.20 | 0.50 / 184 | 0.59 / 232 | 0.71 / 318 |
| 0.25 | 0.67 / 284 | 0.78 / 379 | 0.95 / 688 |
| 0.30 | 0.86 / 461 | impossible | impossible |
| 1/3 | impossible | impossible | impossible |

- **Against a quarter of the stake, two thirds of the honest stake must declare** if every
  volunteer is always online, and 78 % at 95 % uptime. On Cardano's spread that is the 284 or 379
  largest pools.
- **Against 30 %, uptime below 95.2 % breaks it.** A third cannot be held at all.

Gates (`tests/test_privacy.py`): just above the frontier the adversary holds less than a third of
the declared stake and liveness is tight; just below it liveness fails; the count of pools matches
a hand count. Two mutations fail them.

What the variant changes:

- **Safety rests on the volunteers**, not on the chain's honest majority, and liveness needs them
  online. They are named, so they can be targeted.
- **The private chain must never revert a certified block.** A committee in which the adversary
  holds a third of the declared stake could certify two forks, and the private chain would then
  split.
- **Declared notes must stay in the leader lottery.** If they left it, an adversary that declares
  nothing would hold `α / (1 − v(1 − α))` of the lottery: 0.13, 0.33 and 0.50 against 10 %, 20 %
  and 25 % of the stake at the frontier for full uptime.
- **Volunteers reveal their stake**, and their network addresses if they gossip directly.
- **Everyone else casts no vote, so D5's leak does not reach them.**

## D3 — the cost model

- **A vote** is at least a Groth16 proof (128 bytes, the size of the proof inside
  `ProofOfLeadership`), a tag (32), a block id (32) and a round number: about 200 bytes before
  Blend's padding and cover.
- **Proving.** A seat proves once per round, so a holder of share `s` proves `s·n` times a round:
  67 proofs for a 1.26 % holder at 5,355 seats. The specification's benchmark for the proof of
  leadership (`cryptarchia-proof-of-leadership.md`, Benchmarks) puts one proof at about 0.68 s on
  one thread of an i9-13980HX, and 0.16–0.18 s at 23–30 threads (read off its figure).
  `tools/benchmarks/pol-proving` times the node's proof of leadership at the study's commit, on
  all cores and pinned to one, and writes to `reports/finality/pol-proving/`. On an Apple M4 Pro a
  proof takes 72.5 ms on all cores. The reference node of Q7 is still to be run.
- **Aggregation** (recursive proofs, or a Groth16 aggregation scheme) would shrink certificates
  for light clients and bootstrapping nodes. It does not reduce what each vote costs to emit.

**Blend's own budget.** A vote is a Blend message: every node verifies its header once for each
of the `β_max = 3` blending operations, and its proof once. Blend sizes a core connection for
`F_1 = 16` messages a round against a read limit of `r_1 = 20`, and a node for `V = 156`
verifications a second, one core of a Raspberry Pi 5 (`blend-protocol.md`, Expected Traffic).
Today a node makes 16 verifications a second. The committees of D0 at `ε = 1e-9`, with votes sent
on top of today's cover (the quota ceiling then falls, D0) or with the cover raised by D0's
multiple to carry them (`runs/d0/blend_load.csv`):

| α | round | votes / s | votes on top of cover: F_1 / verifications per s | cover raised: F_1 / verifications per s |
| --- | --- | --- | --- | --- |
| 0.10 | 10 min | 1.11 | 19.3 / 20 | 116 / 117 |
| 0.10 | 60 min | 0.18 | 16.6 / 17 | 33 / 33 |
| 0.20 | 10 min | 3.48 | 26.4 / 30 | 329 / 332 |
| 0.20 | 60 min | 0.58 | 17.7 / 18 | 68 / 69 |
| 0.25 | 10 min | 8.93 | 42.8 / 52 | 819 / 828 |
| 0.25 | 60 min | 1.49 | 20.5 / 22 | 150 / 151 |
| 0.30 | 10 min | 55.79 | 183.4 / 239 | 5,037 / 5,093 |
| 0.30 | 60 min | 9.30 | 43.9 / 53 | 853 / 862 |

- **Votes on top of the cover fit `r_1` only while `n/R` stays below 1.33 votes a second:**
  10-minute rounds against a tenth of the stake, hour-long rounds against a fifth.
- **With the cover raised, no committee fits.** Against a quarter of the stake with 10-minute
  rounds, a connection carries 41 times `r_1` and a node verifies 5.3 times `V`. Votes then fit
  `r_1` only in rounds of at least `22.5·n` seconds: 33 hours against a quarter.
- **Bandwidth.** A Blend message is 19,318 bytes, so a core connection carries 0.31 MB/s today,
  0.83 MB/s with the votes above on top, and 16 MB/s with the cover raised, against a quarter with
  10-minute rounds. A node holds `Φ_CC = 4` core connections.

## D4 — forward security and accountability

Cryptarchia leaves out Crypsinous's protection against adaptive adversaries: there is no note
evolution and no per-slot key erasure (`cryptarchia-proof-of-leadership.md`, Comparison with
Original Crypsinous PoL). Whoever later learns a note's key can sign for its past wins. A
certificate of a past round could therefore be forged by corrupting enough past voters after the
fact. Two remedies:

- **A per-round key erased after voting.** Crypsinous erases a per-slot leaf of a secret-key tree.
  Praos uses key-evolving signatures, which allow one signature per period.
- **Certificates trusted only within a window,** with the `k`-deep rule governing older history.

Accountability can then come from the tags. A tag that reveals the note's key when the seat votes
twice in a round, in the rate-limiting-nullifier style, makes equivocation punishable without
naming the voter. Punishment needs the note locked for the round.

## D5 — privacy

**Counts.** Every vote is an emission. If the cover rate does not rise by the multiple of D0, the
quota ceiling falls by that multiple. Nodes above the lowered ceiling then become distinguishable
by emission count alone (Blend report §3.10).

**Votes sample stake.** A seat is a lottery win as a block is. A holder of share `s` makes `s·f`
blocks a slot and casts `s·n` votes a round of `R` slots, so an observer who attributes a node's
messages samples its stake from votes `n/(R·f)` times as often as from blocks.

The Blend report's model of linking (§3.6–§3.7): a message of a node with an adversarial peer is
attributed to it when its whole blend path is adversarial, with probability
`q = f_adv^hops = 0.008` at `f_adv = 0.2` and 3 hops, and `N` attributions size its stake to
`1/√N`. A block proposal is sent twice (`R_D = 1`, `blend-protocol.md`), so it is attributed with
probability `1 − (1 − q)² = 0.016`. A vote is sent once through Blend; gossiped directly, it is
taken as attributed with probability one, as the Blend report's whole-path capture takes an
adversarial peer as proof of origin (its §3.4 gives that reading 0.53 confidence). The times hold
for a node with an adversarial peer: at the specification's peering degree of 4, 59 % of nodes at
`f_adv = 0.2`. Votes are cast together at each round's start, and the observer starts at a random
point of a round. Mean time until a holder is identified (`N = 1`) / its stake is known to ±10 %
(`N = 100`), counting its blocks and its votes (`src/finality_sim/privacy.py`,
`scripts/d5_privacy.py`):

| share | blocks only, through Blend | with votes through Blend, 1 h rounds | with votes through Blend, 10 min rounds | with votes through Blend, 90 s rounds | with votes gossiped directly, 10 min rounds |
| --- | --- | --- | --- | --- | --- |
| 5 % | 10.5 h / 44 d | 36 min / 1.9 d | 6 min / 7.7 h | 57 s / 1.2 h | 5 min / 5 min |
| 1 % | 2.2 d / 218 d | 2.3 h / 9.3 d | 24 min / 1.6 d | 4 min / 5.8 h | 5 min / 17 min |
| 0.1 % | 22 d / 2,179 d | 22.3 h / 93 d | 3.9 h / 16 d | 35 min / 2.4 d | 5 min / 3.1 h |
| 0.01 % | 218 d / 21,789 d | 9.3 d / 931 d | 1.6 d / 161 d | 5.8 h / 24 d | 19 min / 1.3 d |

The analysis `analysis-cryptarchia-de-anonymisation-of-relative-stake.md` asks a related question:
the probability that an estimate of a node's stake lies within ±10 % after `T` slots, and how many
nodes a holder must split into to keep it at 0.5 or below. Over one epoch at `f = 1/30`, from the
exact Poisson count of the holder's attributed blocks and votes (its estimate solves for the
stake that count implies):

| votes | confidence for a 1.26 % holder | nodes it must split into | every share above it sized |
| --- | --- | --- | --- |
| blocks only, through Blend | 0.19 | 1 | 14 % |
| with votes through Blend, 1 h rounds | 0.68 | 3 | 0.6 % |
| with votes through Blend, 10 min rounds | 0.99 | 12 | 0.11 % |
| with votes through Blend, 90 s rounds | 1.00 | 92 | 0.016 % |
| with votes gossiped directly, 10 min rounds | 1.00 | 1,743 | 0.00083 % |
| with votes through Blend, 10 min rounds, the holder's stake in 1 note | 0.11 | – | – |
| with votes through Blend, 10 min rounds, the holder's stake in 10 notes | 0.04 | – | – |
| with votes through Blend, 10 min rounds, the holder's stake in 100 notes | 0.85 | – | – |

- **Votes make stake learnable.** Through Blend, block wins alone give an observer better than
  even odds of sizing a stake to ±10 % within an epoch only above 14 % of all stake. With
  10-minute rounds every share above 0.11 % has those odds, and a 0.1 % holder is sized in 16
  days on average instead of 2,179. The analysis' 1.26 % holder must split into 12 nodes, where
  blocks alone need no split.
- **Blend slows the leak by about `f_adv^-hops`, 125.** Gossiped directly, the same votes
  identify a holder of 0.1 % or more within the first round, about 5 minutes, and size a 0.1 %
  holder in 3 hours instead of 16 days.
- **Longer rounds leak less, in proportion.** With rounds of an hour, every share above 0.6 % is
  sized within an epoch at better than even odds.
- **A holder with few large notes leaks less.** Each note wins a seat in nearly every round, so the
  count of its votes says little about its stake: a 1.26 % holder in one note or ten is sized
  within an epoch with probability 0.11 or 0.04, and in 100 notes with 0.85.

Gates (`tests/test_privacy.py`): without votes the times are the Blend report's §3.7, as printed;
the analysis' example (confidence 0.824, five nodes) is reproduced with its own formula, and the
exact confidence agrees with it at its large counts; votes speed sizing by D0's multiples when
attributed alike; one attribution waits for the first round start as a closed form says; the
confidence equals a simulated estimate's, with many notes and with ten; the share sized at better
than even odds is read above the largest share that is not. Five mutations fail them.

**Views.** A vote names the block its sender saw `L` slots back. The specification's tagging
attack reads a leader's view from the transactions in its block (Limitations of Cryptarchia V1).
A vote carries no transaction, so a tag needs voters to see different blocks `L` slots back:
under random delay, votes on a target 30 slots back never split (D6).

## D6 — votes on the engine's chains

The Peras-style certificate of D1 (a), on the A1 configuration at three Blends
(`scripts/d6_votes.py`, `src/finality_sim/votes.py`). A round starts every 600 slots. Each node
votes for the latest block at least `L` slots old on the best chain it holds at the round's start.
Its seats, Poisson with the expectation its stake gives, carry the vote. A vote reaches each node
as a block from the same sender would, and a node holds a certificate once the votes it has
received give one block the quorum. Gates (`tests/test_votes.py`): a node's chain is the best it
has received, the target is the latest block old enough, and the quorum is counted on one block.
Four mutations fail them.

The stake share agreeing on the most common target, mean / worst 1 % of 456 rounds per Blend:

| Blend | L = 0 | L = 30 | L = 60 | L = 120 | L = 300 |
| --- | --- | --- | --- | --- | --- |
| testnet | 0.993 / 0.731 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| specification | 0.980 / 0.524 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |
| heavy | 0.980 / 0.793 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 |

Votes on the tip split. A lag of 30 slots removes every split in all 1,368 rounds.

Certificates at `L = 60`, with D0's committee at `ε = 1e-9` and the adversary's seats withheld:

| Blend | α | seats / quorum | rounds | certified | time to quorum p50 / p95 (s) |
| --- | --- | --- | --- | --- | --- |
| testnet | 0.10 | 665 / 458 | 456 | 1.000 | 1.6 / 1.6 |
| testnet | 0.25 | 5,355 / 3,642 | 456 | 1.000 | 1.6 / 1.6 |
| specification | 0.10 | 665 / 458 | 456 | 1.000 | 8.0 / 8.0 |
| specification | 0.25 | 5,355 / 3,642 | 456 | 1.000 | 8.9 / 9.0 |
| heavy | 0.10 | 665 / 458 | 456 | 1.000 | 17.1 / 17.2 |
| heavy | 0.25 | 5,355 / 3,642 | 456 | 1.000 | 19.3 / 19.3 |

- **Every round certifies within one Blend delivery** of its start: 1.6 s on testnet's Blend, 8–9 s
  on the specification's, 17–19 s at the heavy point.
- **A block is certified `L` slots after its publication, plus the wait for the next round, plus
  that delivery.** With 600-slot rounds that is about 6 minutes on average, at ×269 cover against
  25 % (D0); with 90-slot rounds, about 2 minutes at ×1,786. On the specification's Blend,
  settlement against 25 % takes 18 minutes at `1e-3` and 68 at `1e-9` (`RATE.md`, C1).

Where rounds fail:

- **A partition.** The committee leaves the honest seats 10 % above the quorum at 25 % (31 % at
  10 %). A partition that cuts off more than 9 % of the honest stake (23 % at 10 %) stalls
  certificates on both sides. The chain continues (C2).
- **A delay chosen by an adversary.** The attack of B3 holds a second chain at least as long as
  the honest one, and can show each voter either. At 25 % and `Δ = 10` s it succeeds at depth 2
  with probability 0.53 and at depth 10 with 0.13 (`runs/b3/delay.csv`). Votes on a target that
  shallow can be split in most rounds. Splits stall finality but cannot certify two blocks: two
  certificates still need `H + 2A ≥ 2Q` (D0). Holding the attacker's chance of splitting a round
  below `1e-3` takes a target 45 blocks deep at 25 % and 11 at 10 %. Under that delay model a
  certificate therefore comes no sooner than settlement at `1e-3`. It then makes the block final
  at the round's `ε`, where settlement on the chain needs the depths of B2.
