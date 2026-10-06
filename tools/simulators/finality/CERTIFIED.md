# Certified finality

Phase D of `PLAN.md`. Tables come from `scripts/d0_emission_map.py`, `scripts/d1b_committee.py`,
`scripts/d5_privacy.py` and `scripts/d6_votes.py` through `scripts/tables.py`. Status: D0, D1b,
D2, D5 and D6 are measured. D1, D3 and D4 are sketched with the open questions they leave.

## D0 — the emission budget

A vote is a private lottery win: one seat per note per round, Poisson in number. Honest seats vote
once; adversarial seats vote for both sides; offline honest seats cast nothing. Two conflicting
quorums of `Q` need `H + 2A ≥ 2Q`, and a round stalls when `H < Q`
(`src/finality_sim/committee.py`, gated against a direct convolution in `firstlook.py`). Every vote
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
from 30 s to an hour, and with 10 % and 20 % of honest votes lost. The owner draws the budget line
on it (Q7).

Design (a) of D1 certifies a block `L` slots after its publication, plus half a round on average,
plus one Blend delivery (D6). The two-round gadget (b) adds a round. With 10-minute rounds and
`L = 60` slots, (a) takes about 6 minutes and (b) about 16. Against random Blend delays and at
30 s blocks, settlement on the chain takes 9–11 minutes against 10 % of the stake and 34–51
minutes against 25 %, from testnet's Blend to the specification's (`RATE.md`, C1). So:

- **Against 10 %,** (a) certifies in about 6 minutes at ×34 cover, against 9–11 minutes of
  settlement.
- **Against 25 %,** it certifies in about 6 minutes at ×269 cover, against 34–51 minutes.
- **Against 30 % or more,** no committee is affordable.

Votes buy minutes against a small adversary and most of an hour against a large one, at one to
three orders of magnitude of cover traffic. Under a delay chosen by an adversary, a shallow target
can be split (D6), and settlement on the chain is slower too (`SETTLEMENT.md`, B2).

## D2 — committee realism: the share of honest votes that count

Offline stake, votes lost in Blend, and honest votes split between forks all lower the share of
honest seats whose votes count. In the seat model they act as one factor. Seats per round at
`ε = 1e-9`:

| α | all honest seats vote | 90 % vote | 80 % vote |
| --- | --- | --- | --- |
| 0.05 | 443 | 510 | 598 |
| 0.10 | 665 | 801 | 997 |
| 0.15 | 1,097 | 1,400 | 1,910 |
| 0.20 | 2,085 | 3,003 | 4,878 |
| 0.25 | 5,355 | 10,110 | 28,465 |
| 0.30 | 33,473 | 345,443 | none |

At 25 % of the stake, losing a fifth of the honest votes multiplies the committee by 5.3; at 30 %
no committee survives it. Error in the inferred total stake works the other way. The inference
never exceeds the true stake (TSI report §2.2), so a low estimate inflates every note's seat
odds, honest and adversarial alike. Expected seats grow by `D/D̂`. That raises the cover cost,
not the risk. A sudden loss of stake before the inference adapts acts as offline stake, for up
to an epoch.

## D1 — design sketches

Each design keeps C1–C5 (`PLAN.md` §0): seats are private lottery wins, votes travel through
Blend (Q6), and a failed round stalls finality without halting the chain.

**The common pieces.**

- **Seat.** A note wins a seat in round `r` when
  `hash(VOTE_V1 ‖ η ‖ r ‖ noteID ‖ sk)` falls below a threshold. The threshold is set from the
  inferred stake so that all stake together expects `n` seats.
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
committee size. Anonymous seats provide both: the expected size follows from the epoch's inferred
stake, which every node shares. Whether those proofs carry over to Poisson seat counts and to
votes delayed by Blend is the open question.

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
online honest stake to reach two thirds of it. Both hold when `v ≥ 2α / ((1 − α)(3u − 2))`
(`src/finality_sim/privacy.py`). Each cell gives `v`, then the number of the largest holders that
reach it if the honest stake is spread as Cardano's 2,522 pool stakes are (the analysis
`analysis-cryptarchia-de-anonymisation-of-relative-stake.md`, its `pools.csv`;
`scripts/d1b_committee.py`):

| α | uptime 1 | uptime 0.95 | uptime 0.9 |
| --- | --- | --- | --- |
| 0.10 | 0.22 / 72 | 0.26 / 85 | 0.32 / 106 |
| 0.20 | 0.50 / 184 | 0.59 / 232 | 0.71 / 318 |
| 0.25 | 0.67 / 284 | 0.78 / 379 | 0.95 / 688 |
| 0.30 | 0.86 / 461 | impossible | impossible |
| 0.33 | impossible | impossible | impossible |

- **Against a quarter of the stake, two thirds of the honest stake must declare** if every
  volunteer is always online, and 78 % at 95 % uptime. On Cardano's spread that is the 284 or 379
  largest holders.
- **From 30 % any downtime breaks it, and a third cannot be held at all.**

Gates (`tests/test_privacy.py`): at the frontier the adversary holds exactly a third of the declared
stake at full uptime and liveness is tight; just below it liveness fails; the count of holders
matches a hand count. Two mutations fail them.

What the variant changes:

- **Safety rests on the volunteers**, not on the chain's honest majority, and liveness needs them
  online. They are named, so they can be targeted.
- **The private chain must never revert a certified block.** A committee in which the adversary
  holds a third of the declared stake could certify two forks, and the private chain would then
  split.
- **Volunteers reveal their stake**, and their network addresses if they gossip directly.
  Leadership should use other notes, so that their block wins stay private.
- **Everyone else casts no vote, so D5's leak does not reach them.** If declared notes leave the
  leader lottery, a private holder's share of the lottery, and so of the blocks, rises by the
  factor `1/(1 − V)`, where `V` is the declared share of all stake. Every time in the first
  column of D5's first table then falls by the factor `1 − V`.

## D3 — the cost model

- **A vote** is at least a Groth16 proof (128 bytes, the size of the proof inside
  `ProofOfLeadership`), a tag (32), a block id (32) and a round number: about 200 bytes before
  Blend's padding and cover.
- **Proving.** A seat winner proves once per round. The specification's benchmark for the proof
  of leadership (`cryptarchia-proof-of-leadership.md`, Benchmarks) puts it at about 0.68 s on one
  thread of an i9-13980HX, and 0.17–0.18 s at 23–30 threads (read off its figure). The reference
  node of Q7 is still to be measured.
- **Verification.** Every node verifies `n/R` votes per second: 9 per second at 5,355 seats and
  10-minute rounds, 60 at 90 s. One core of a Raspberry Pi 5 verifies 157 Blend headers per
  second, each an Ed25519 signature and a Groth16 proof (`blend-protocol.md`, `V`). A vote's proof
  is a Groth16 proof as well, so one core verifies on the order of 157 votes per second: the votes
  take 6 % of a core with 10-minute rounds and 38 % with 90 s rounds.
- **Bandwidth.** `n × 200 B / R` per node before Blend overhead: 1.8 KB/s at 5,355 seats and
  10-minute rounds, 12 KB/s at 90 s.
- **Aggregation** (recursive proofs, or a Groth16 aggregation scheme) would shrink certificates
  for light clients and bootstrapping nodes. It does not reduce what each vote costs to emit.

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

**Votes sample stake.** A seat is a lottery win as a block is. A holder of stake share `s` makes
`s·f` blocks a slot and `s·n` votes a round of `R` slots, so an observer who attributes a node's
votes samples its stake `1 + n/(R·f)` times as fast: D0's multiple, ×269 for the committee of
5,355 seats against a quarter of the stake in 10-minute rounds.

The Blend report's model of linking (§3.6–§3.7, `blend.linkability` loaded from
`tools/simulators/blend`): each emission of a node with an adversarial peer is attributed to it
with probability `q`, and `N` attributions size its stake to `1/√N`. Through Blend
`q = f_adv^hops`, `0.008` at `f_adv = 0.2` and 3 hops for blocks and votes alike. A vote gossiped
directly has no blend path, so `q = 1`. Mean time until a holder is identified (`N = 1`) / its
stake is known to ±10 % (`N = 100`), counting its blocks and its votes (`scripts/d5_privacy.py`):

| share | blocks only, through Blend | with votes through Blend, 1 h rounds | with votes through Blend, 10 min rounds | with votes through Blend, 90 s rounds | with votes gossiped directly, 10 min rounds |
| --- | --- | --- | --- | --- | --- |
| 5 % | 20.8 h / 87 d | 27 min / 1.9 d | 5 min / 7.8 h | 42 s / 1.2 h | 2 s / 4 min |
| 1 % | 4.3 d / 434 d | 2.3 h / 9.5 d | 23 min / 1.6 d | 3 min / 5.8 h | 11 s / 19 min |
| 0.1 % | 43 d / 4,340 d | 22.8 h / 95 d | 3.9 h / 16 d | 35 min / 2.4 d | 2 min / 3.1 h |
| 0.01 % | 434 d / 43,403 d | 9.5 d / 951 d | 1.6 d / 161 d | 5.8 h / 24 d | 19 min / 1.3 d |

The analysis `analysis-cryptarchia-de-anonymisation-of-relative-stake.md` asks a related question:
the probability that a naive estimate of a node's stake lies within ±10 % after `T` slots of which
a share `q` is observed, and how many nodes a holder must split into to keep it at 0.5 or below.
Each observed round of votes adds a Poisson count of mean `n·α` to the slots' information. Over
one epoch at `f = 1/30` with `q = 0.008`, beside the analysis's own example (`f = 0.05`,
`T = 432,000` slots, `q = 0.657`):

| model | votes | confidence for a 1.26 % holder | nodes it must split into | largest share an observer cannot size |
| --- | --- | --- | --- | --- |
| Cryptarchia, one epoch | blocks only, through Blend | 0.12 | 1 | 26 % |
| Cryptarchia, one epoch | with votes through Blend, 1 h rounds | 0.68 | 3 | 0.58 % |
| Cryptarchia, one epoch | with votes through Blend, 10 min rounds | 0.98 | 13 | 0.098 % |
| Cryptarchia, one epoch | with votes through Blend, 90 s rounds | 1.00 | 86 | 0.015 % |
| Cryptarchia, one epoch | with votes gossiped directly, 10 min rounds | 1.00 | 1,602 | 0.00079 % |
| the analysis's example | blocks only | 0.82 | 5 | 0.31 % |
| the analysis's example | with votes, 10 min rounds | 1.00 | 706 | 0.0018 % |

- **Votes make stake learnable.** Through Blend, block wins alone give an observer better than
  even odds of sizing a stake to ±10 % within an epoch only above 26 % of all stake. With
  10-minute rounds every share above 0.098 % has those odds, and a 0.1 % holder is sized in 16
  days on average instead of 4,340. The analysis's 1.26 % holder must split into 706 nodes
  instead of 5.
- **Blend buys a factor of `f_adv^-hops`.** Gossiped directly, the same votes identify a 0.1 %
  holder in 2 minutes and size it in 3 hours: about 125 times as fast as through Blend at
  `f_adv = 0.2` and 3 hops.
- **Longer rounds leak less, in proportion.** With rounds of an hour, the shares an observer has
  even odds of sizing within an epoch start at 0.58 %.

Gates (`tests/test_privacy.py`): the Blend report's §3.7 times and the analysis's example
(confidence 0.824, five nodes) are reproduced as printed; votes speed sizing by D0's multiples; the
confidence a vote count adds matches the exact Poisson probability. Three mutations fail them.

**Views.** A vote reveals which block its sender saw. That is the signal the specification's
tagging attack exploits (Limitations of Cryptarchia V1), and votes give it the same `1 + n/(R·f)`
samples. A tag needs the voters to see different blocks at the target's depth: under random
delay, votes on a target 30 slots back never split (D6).

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
  settlement against 25 % takes 18 minutes at `1e-3` and 51 at `1e-9` (`RATE.md`, C1 and C4).

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
