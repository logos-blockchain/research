# Certified finality

Phase D of `PLAN.md`. Tables come from `scripts/d0_emission_map.py` and `scripts/d6_votes.py`
through `scripts/tables.py`. Status: D0, D2 and D6 are measured. D1, D1b, D3, D4 and D5 are
sketched with the open questions they leave.

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
directly. Questions for this variant:

- **Safety and liveness.** A certificate means two thirds of the volunteers' stake signed. Safety
  then rests on the volunteers, not on the chain's honest majority. Liveness needs the
  volunteers online.
- **The private chain.** It must never revert a certified block. A corrupted committee (a third
  of volunteer stake or more) could certify two forks, and the private chain would then split.
- **What volunteers reveal.** Their stake, and their network addresses if they gossip directly.
  Leadership should use other notes, so that their block wins stay private.
- **Everyone else.** Volunteer stake leaves the anonymity set of leaders. The private stake that
  remains is smaller, and so easier to profile.

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

- **Counts.** Every vote is an emission. If the cover rate does not rise by the multiple of D0,
  the quota ceiling falls by that multiple. Nodes above the lowered ceiling then become
  distinguishable by emission count alone (Blend report §3.10).
- **Views.** A vote reveals which block its sender saw. That is the signal the specification's
  tagging attack exploits (Limitations of Cryptarchia V1).
- **Direct gossip (Q6).** Votes sent outside Blend would tie seat wins, and so stake, to network
  addresses. The size of that leak is to be measured with the Blend report's time-to-link and
  stake-learning machinery (§3.6, §3.7).

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
  25 % (D0); with 90-slot rounds, about 2 minutes at ×1,786. On the specification's Blend, settlement
  against 25 % takes 18 minutes at `1e-3` and 51 at `1e-9` (`RATE.md`, C1 and C4).

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
