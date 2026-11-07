# Stake counted in anonymous units

Phase N of `PLAN.md`. Tables come from `scripts/n1_committee.py`, `scripts/n2_registry.py`,
`scripts/n3_transport.py`, `scripts/n4_privacy.py`, `scripts/n5_cost.py` and `scripts/n6_time.py`
through `scripts/tables.py`. Specifications are read at `logos-lips` `bd1ca2c8`. One slot is one
second, a Blend round is one second, and `f = 1/30`. Every committee holds both its tails at
`ε = 1e-9` a round, as in D0. The active stake is 30 % of the supply (M.7), so today's minimum
stake, 0.001 % of the supply, makes 30,000 units.

## N.0 — the reading

**The owner's direction**, 2026-11-06: "a possibility of having public stake value that is unlinked
from the owner. Privacy is paramount!" Privacy is read first. A design is read by how soon it lets
an observer know a holder's stake, against what the holder's blocks alone reveal today: a holder of
0.1 % is sized to ±10 % in 2,179 days (M.3). Its time to finality is read second, against Phase M's
yardstick, the chain's own wait against the same coalition: against 30 %, 3.09 hours under random
delay and 5.93 under the worst case at 10 s (M.2).

**What the sources say.**

- *The proof of leadership* proves "the membership of the note identifier in an old snapshot of the
  Mantle Ledger, proving its age and its existence", and "in the most recent Mantle ledger, proving
  it’s unspent" (`cryptarchia-proof-of-leadership.md`). A registration proves the same of the note
  behind a unit.
- *Mantle's notes are public*: "The Mantle Ledger enables asset transfers using a transparent UTXO
  model." A distinctive value points at its note. C1's own sentence names what a value lets an
  observer do: reduce the anonymity set "by bucketing the leader as high/low stake"
  (`cryptarchia-v1-protocol.md`). Units are equal for that reason.
- *The epoch schedule.* "A snapshot of note commitments are taken at the beginning of the epoch. We
  wait for this value to finalize before entering the next phase." The buffer phase follows "to
  further ensure that there is at least one honest leader contributing to the epoch nonce
  randomness. If an adversary can predict the nonce, they can grind their coin secret keys to gain
  an advantage." A registry closed in the snapshot phase is followed by a whole buffer phase, as the
  snapshot is.
- *Blend floods every layer.* A node that receives a message checks its header, and "The proof of
  quota must be valid; if not, then discard the message and do not relay it." A received message
  "is immediately released to all neighboring nodes, except the one it was received from", and
  "Flooding delivers each message once per neighbor" (`blend-protocol.md`, Relaying, Releasing,
  Expected Traffic). Only the payload leaves Blend: a proposal "is broadcasted to the Logos
  Blockchain broadcasting channel after a random delay." The node budget is `V = 156`, one below
  the 157 "measured on one core of a Raspberry Pi 5", with `r_1 = ⌊(2V/3)/(Φ_CC + 1)⌋ = 20`,
  `Φ_CC = 4`, `F_1 = r_1·(1 − 1/(Δ_max + η)) = 16` at `Δ_max = 3` and `η = 2` rounds, and 19,318
  bytes a message. Blend "is optimized for the privacy of core nodes."
- *RLN-v1* (`docs/anoncomms/draft/32/rln-v1.md`): "Group members are allowed to send one signal per
  external nullifier", and a member who sends more "risks being slashed - by revealing his
  membership secret credentials." A signal carries the share `y = a_0 + x * a_1;` of a line whose
  intercept is the secret, and "If enough such shares are present, the user's secret can be
  retreived."
- *The stake-weighted mix RLN* (`docs/anoncomms/raw/mix-dos-protection-rln-stake-weighted.md`)
  counts stake in units too, `S_unit`, "The stake required per message per epoch." It meets both
  leaks this phase meets. "Registration is publicly observable. It reveals a node's stake amount",
  and "A node's rate is also observable at the network layer from its traffic." It names the fix:
  "A complete fix at the registry layer requires a shielded membership registry that hides the
  stake-to-identity link via ZK".
- *The libp2p mix* (`docs/anoncomms/raw/mix.md`) forwards point to point: its layered encryption
  protects "message contents as packets are forwarded hop-by-hop", and "Sphinx packets are
  fixed-size and indistinguishable from one another, providing unlinkability and metadata
  protection."

**The design.**

- *A unit* is a fixed amount `μ` of stake, by default today's minimum stake.
- *Registration.* In the snapshot phase of each epoch, once the snapshot is final, a holder
  registers each unit its notes hold for the next epoch. A registration carries a fresh unit key and
  a proof, built like the proof of leadership, that a note in the snapshot holds at least `(j + 1)μ`,
  with a tag from the note's secret, the epoch and `j` that stops a second registration of the unit.
  The proof hides the note and `j`.
- *The registry* is the epoch's unit keys. Every node counts them, and no key names its holder.
- *Committees.* A *public draw* takes the `n` keys with the lowest values of a function of the key
  and the round's randomness, so every node knows the drawn keys. A *private draw* makes each unit a
  seat by its secret, as seats are drawn. Or *every unit votes*.
- *A vote* proves that its sender holds the secret of a drawn unit without showing which. Its tag
  comes from that secret and the round, and its RLN share makes a second vote in the round reveal
  the unit's secret. *Linkable keys*, one key a unit signing every vote of an epoch, would allow one
  aggregate signature a round instead.
- *Optionally*, the leader lottery divides by the registered stake instead of the inferred.

| variant | who votes | a vote shows | constraints |
| --- | --- | --- | --- |
| a public draw | the `n` drawn units; every node knows the drawn keys | that its sender holds a drawn unit | C3's letter, a committee drawn by a private lottery, is not kept; the keys name no one |
| a private draw | each unit that wins a seat by its secret | a seat won | all five |
| every unit voting | every registered unit | that its sender holds a unit | no draw; the committee is the registry, whose keys name no one |
| the lottery divided by the registered stake | | | C2: registered stake that goes offline slows the chain until a registry without it |

Whatever carries the votes must keep C1. N.3 sizes the transports, and N.4 what a node's count of
messages and an attributed message reveal.

## N.1 — what a counted committee holds

Two conflicting certificates of quorum `Q` need `H + 2A ≥ 2Q` of the committee's honest and
coalition units, every honest unit counting on both sides, as in D0 and M.1. A round stalls when the
honest units online fall short of `Q`. The coalition holds 9,000 of the 30,000 units against 30 %.

- A *public draw* without replacement makes the coalition's drawn units hypergeometric, and the
  quorum is set from the drawn count, which every node knows.
- A *private draw* makes the seats binomial over the counted units: D0's rule on a count whose mean
  every node knows, so it needs no margin for the inference's error.
- *Every unit voting* is exact: safety holds while `A_U < 2Q − U`, and liveness while
  `u(1 − a) ≥ q > (1 + a)/2` in the limit of many units, for the coalition's share `a` of the units
  and the quorum share `q`: 92.86 % online against 30 %.

| coalition | honest units online | anonymous seats a round: no margin / sized for the inference's error up to 1.05 | counted, drawn with replacement (M.1) | a private draw over 30,000 units, seats expected | a public draw from 30,000 units | every unit voting, 30,000 a round |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | all | 665 / 801 | 88 | 652 | 88 | holds |
| 10 % | 95 % | 851 / 1,050 | 130 | 827 | 130 | holds |
| 10 % | 90 % | 1,137 / 1,453 | 193 | 1,097 | 193 | holds |
| 25 % | all | 5,355 / 9,728 | 1,030 | 4,547 | 994 | holds |
| 25 % | 95 % | 10,624 / 26,305 | 2,185 | 7,906 | 2,049 | holds |
| 25 % | 90 % | 31,617 / 229,888 | 6,881 | 15,835 | 5,808 | holds |
| 30 % | all | 33,473 / 279,488 | 6,922 | 15,835 | 5,602 | holds |
| 30 % | 95 % | 361,880 / none | 78,979 | 28,367 | 23,364 | holds |
| 30 % | 90 % | none / none | none | none | none | fails |
| a third | all | none / none | none | none | none | fails |
| a third | 95 % | none / none | none | none | none | fails |
| a third | 90 % | none / none | none | none | none | fails |

Counting the units removes D2's margin and shrinks D0's. Against 30 % with every honest unit online,
a public draw needs 5,602 units a round, where seats need 33,473 with no margin and 279,488 sized
for the inference's error. Drawing without replacement takes another fifth off M.1's binomial count,
6,922. With 95 % of the honest units online a public draw needs 23,364, every unit voting 30,000,
and the binomial count 78,979; seats need 361,880, and none exists once sized for the inference's
error. At 90 % nothing holds 30 %, and nothing holds a third.

The unit's size sets how many units vote and how many are lost:

| a unit, share of the supply | registered units | a public draw against 25 %: all online / 95 % | against 30 %: all online / 95 % | the least uptime at which every unit voting holds, against 25 % / 30 % |
| --- | --- | --- | --- | --- |
| 0.0001 % | 300,000 | 1,027 / 2,174 | 6,763 / 63,797 | 83.8 % / 93.2 % |
| 0.001 % | 30,000 | 994 / 2,049 | 5,602 / 23,364 | 84.8 % / 93.9 % |
| 0.01 % | 3,000 | 754 / 1,314 | 2,062 / none | 87.7 % / 95.8 % |

The coalition sizes its notes in whole units; an honest note loses its value below a whole unit,
less than one unit a note. A holder that merges its notes to whole units links them on the
transparent ledger. With a share `ρ` of the honest stake lost, the coalition holds
`α/(α + (1 − α)(1 − ρ))` of the units:

| the honest stake lost below whole units | the coalition's share of the units, holding 25 % / 30 % of the stake | a public draw against 30 %: all online / 95 % | the least uptime at which every unit voting holds, against 30 % |
| --- | --- | --- | --- |
| 0 % | 25.0 % / 30.0 % | 5,602 / 23,364 | 93.9 % |
| 1 % | 25.2 % / 30.2 % | 6,229 / 26,056 | 94.3 % |
| 5 % | 26.0 % / 31.1 % | 10,033 / none | 96.0 % |
| 10 % | 27.0 % / 32.3 % | 19,726 / none | 98.2 % |

Against 30 % the rounding counts: 5 % of the honest stake lost below whole units leaves no public
draw with 95 % online, and every unit voting then needs 96.0 %.

Gates (`tests/test_units.py`): the log-gamma hypergeometric probabilities against scipy's; the
public draw's quorum against a direct count with binomial coefficients; the public draw tends to
M.1's binomial count as the units grow, and is smaller from 30,000; the scan below the bisected
committee finds a full scan's answer, which bisection alone misses; every unit voting is the public
draw of all units, with the quorum `⌊(U + A_U)/2⌋ + 1`; its least uptime tends to the closed form
and holds 30 % at 95 %, not at 90 %; the private draw over many units is D0's Poisson committee; the
coalition's share of the units over sampled notes is `unit_share` at the measured loss, which stays
below a unit a note. Ten registered mutations fail them.

## N.2 — the registry and the lottery

Registrations for an epoch go on chain in the previous epoch's snapshot phase, once the snapshot is
final: a window of `3⌊k/f⌋ − ⌊k/f⌋` slots. The registry then closes a whole buffer phase,
`3⌊k/f⌋` slots, before the epoch nonce is fixed, so the honest contributions to the nonce follow it
as they follow the snapshot. A registry that closed after the draws' randomness were known would let
a coalition grind its keys into one round.

| registered units | the window | registrations a second | a registration (bytes) | the registry an epoch (MB) | registrations an epoch, holders of 1 % / 0.1 % / 0.01 % |
| --- | --- | --- | --- | --- | --- |
| 30,000 | 129,600 slots, 36 h | 0.231 | 196 | 5.88 | 300 / 30 / 3 |

Every node verifies 30,000 registration proofs an epoch, 191 seconds of a Pi 5 core at 157 a second
(N.5).

If the lottery divides by the registered stake, only registered stake leads, so the true over the
counted stake is at most one and M.7's rise cannot occur: no stake enters unannounced. What remains
is registered stake that goes offline. The coalition's share of the online stake is then the same as
under an inference corrected to the online stake, `α/(α + (1 − α)u)`, but the blocks slow with the
honest uptime `u`, where the inference restores the full rate. K.7's bound under the worst case at
10 s without grinding:

| coalition | honest registered stake online | the coalition's share of the online stake | a block every (s): divided by the registered stake / by the inferred | the wait (h): divided by the registered stake / by the inferred |
| --- | --- | --- | --- | --- |
| 30 % | all | 30.0 % | 30.0 / 30.0 | 5.93 / 5.93 |
| 30 % | 95 % | 31.1 % | 31.1 / 30.0 | 6.97 / 6.96 |
| 30 % | 90 % | 32.3 % | 32.2 / 30.0 | 8.40 / 8.39 |
| 30 % | two thirds | 39.1 % | 39.0 / 30.0 | 35.76 / 40.19 |
| a third | all | 33.3 % | 30.0 / 30.0 | 10.11 / 10.11 |
| a third | 95 % | 34.5 % | 31.0 / 30.0 | 12.49 / 12.55 |
| a third | 90 % | 35.7 % | 32.1 / 30.0 | 15.99 / 16.23 |
| a third | two thirds | 42.9 % | 38.4 / 30.0 | 127.84 / 153.79 |

Dividing by the registered stake changes the wait by less than 2 % against an inference corrected
to the online stake from 90 % online up, and shortens it at two thirds. The slot rule's 18 hours hold a third down to
90 % of the honest registered stake online either way. The trade is liveness against an unannounced
rise: the registered stake keeps no stake out, but a holder that registered and went offline slows
the chain until a registry without it, at most the rest of its epoch and the next.

Gates (`tests/test_units.py`): the registered units, a registration's bytes and the window; with the
lottery divided by the registered stake the coalition's rate is its stake's and the honest rate falls
with its uptime, the inference restores the full rate, and online notes split at random win a slot
with chance `1 − (1 − f)^online`. Three registered mutations fail them.

## N.3 — what carries the votes

A core connection carries every message of the network once for each of its layers, so a vote
message at `h` layers adds `h` messages on every connection, wherever its payload finally goes.
Blend's budget does not grow with the network, and sending the payload to a few collectors instead of
broadcasting it saves only the final broadcast, which Blend does not count. From the load `F_1`,
Blend's own rules give the read limit, `F_1 ≤ r_1·(1 − 1/(Δ_max + η))`, and the node budget,
`r_1 = ⌊(2V/3)/(Φ_CC + 1)⌋`. A node receives each message once from each of its four neighbors.

Three transports:

- *Blend as specified*: one vote a message at three layers within M.2's budget, 4/3 to 2.27 votes a
  second, so the round is long:

| committee against 30 % | units a round | the shortest round: no vote in a node's cover, 4/3 votes a second / equal stakes, 2.27 |
| --- | --- | --- |
| public draw, every honest unit online | 5,602 | 1.17 h / 41.2 min |
| public draw, 95 % online | 23,364 | 4.87 h / 2.86 h |
| every unit voting | 30,000 | 6.25 h / 3.68 h |

- *One vote a message* with the read limit raised: `n/R` vote messages a second at `h` layers. A
  node's count of messages grows with its drawn units.
- *The vote schedule*: every core node sends exactly one vote message a round, empty when none of its
  units is drawn, carrying up to `k_max` of its drawn units' votes (N.5), and more messages only
  beyond. Its load grows with the core nodes, `h·N/R` messages a connection, and not with the stake.

At rounds of 10 minutes against 30 % with every honest unit online, 5,602 units a round:

| core nodes | layers | transport | vote messages a second | verifications the votes add, share of one Pi 5 core | the read limit / the node budget, in Pi 5 cores | received (MB/s) |
| --- | --- | --- | --- | --- | --- | --- |
| any | 3 | today's traffic, no votes | 0 | 0 | 20 / 0.96 | 1.24 |
| 1,000 | 3 | one vote a message | 9.34 | 23.8 % | 56 / 2.68 | 3.40 |
| 1,000 | 3 | schedule, a proof a unit | 1.67 | 9.1 % | 27 / 1.29 | 1.62 |
| 1,000 | 3 | schedule, a proof a message | 1.67 | 4.2 % | 27 / 1.29 | 1.62 |
| 1,000 | 8 | one vote a message | 9.34 | 53.5 % | 114 / 5.45 | 7.01 |
| 1,000 | 8 | schedule, a proof a unit | 1.67 | 14.4 % | 37 / 1.77 | 2.27 |
| 1,000 | 8 | schedule, a proof a message | 1.67 | 9.6 % | 37 / 1.77 | 2.27 |
| 20,000 | 3 | one vote a message | 9.34 | 23.8 % | 56 / 2.68 | 3.40 |
| 20,000 | 3 | schedule, a proof a unit | 33.33 | 69.6 % | 145 / 6.93 | 8.96 |
| 20,000 | 3 | schedule, a proof a message | 33.33 | 84.9 % | 145 / 6.93 | 8.96 |
| 20,000 | 8 | one vote a message | 9.34 | 53.5 % | 114 / 5.45 | 7.01 |
| 20,000 | 8 | schedule, a proof a unit | 33.33 | 175.8 % | 354 / 16.91 | 21.84 |
| 20,000 | 8 | schedule, a proof a message | 33.33 | 191.1 % | 354 / 16.91 | 21.84 |

The schedule adds 14.4 % of a Pi 5 core of verifications at 8 layers on 1,000 core nodes and 175.8 %
on 20,000. Blend's rules then need a node budget of 1.77 and 16.91 Pi 5 cores, where today's load
needs 0.96, and a node receives 2.27 and 21.84 MB a second, where it receives 1.24 today.

*Forwarding point to point*, as the libp2p mix forwards, would carry each vote message `h` times in
all, so a node carries `h/R` of the schedule's messages a second whatever the network's size. Its
exposure to an observer of links lies outside Blend's analysis, and C4 binds (Q4), so it is
described with its load only:

| core nodes | layers | the schedule's messages a node carries a second: point to point / through Blend's flooding |
| --- | --- | --- |
| 1,000 | 3 | 0.005 / 5.0 |
| 1,000 | 5 | 0.008 / 8.3 |
| 1,000 | 8 | 0.013 / 13.3 |
| 20,000 | 3 | 0.005 / 100.0 |
| 20,000 | 5 | 0.008 / 166.7 |
| 20,000 | 8 | 0.013 / 266.7 |

Gates (`tests/test_unitnet.py`): Blend's rules give today's read limit and node budget, and the
budget is the least whose read limit carries the load; one vote a message at three layers is
`committee.blend_load`'s votes on top of today's cover, and each further layer adds a message a
connection; in simulated rounds of a public draw, each node sends `max(1, ⌈k/k_max⌉)` messages for
its `k` drawn units, every node holding at most `k_max` units exactly one, and larger holders more in
some rounds; `k_max` from the payload. Six registered mutations fail them.

## N.4 — what the votes reveal

D5's model as M.3 reads it: a node's message is attributed to it when its whole blend path is
adversarial, `0.2^h` at `h` layers; a block proposal goes out twice at three layers; a holder is
identified at its first attributed emission that shows stake, and sized to ±10 % at 100
observations. A message of the schedule that is attributed reveals how many units it carries, a draw
from the node's units, worth `E[k]²/Var[k]` observations: hypergeometric for a public draw, binomial
for a private one, and the node's every unit for every unit voting, which one attributed message
sizes exactly. Registrations ride the schedule's messages at random rounds; with one vote a message
each is its own message. With linkable keys and one vote a message, a unit is tied to its node once
any of its epoch's messages is attributed; in the schedule one attributed message ties the node's
every later message of the epoch, each carrying one of its known units, so its stake is known by the
epoch's end.

At rounds of 10 minutes against 30 %, every honest unit online, a holder of 0.1 %:

| layers | votes | days to identify | days to size to ±10 % | of today's time |
| --- | --- | --- | --- | --- |
| 3 | none: blocks only, today | 22 d | 2,179 d | 1 |
| 3 | one vote a message, unlinkable | 3.7 h | 15 d | 0.007 |
| 3 | one vote a message, linkable keys | 3.7 h | 7.5 d | 0.003 |
| 3 | schedule, public draw, unlinkable | 20.1 h | 13 d | 0.006 |
| 3 | schedule, public draw, linkable keys | 20.1 h | 7.5 d | 0.003 |
| 3 | schedule, private draw, unlinkable | 20.0 h | 2.6 d | 0.001 |
| 3 | schedule, every unit voting | 20.0 h | 20.8 h | 0.000 |
| 5 | one vote a message, unlinkable | 3.3 d | 328 d | 0.150 |
| 5 | one vote a message, linkable keys | 3.3 d | 322 d | 0.148 |
| 5 | schedule, public draw, unlinkable | 11 d | 283 d | 0.130 |
| 5 | schedule, public draw, linkable keys | 11 d | 26 d | 0.012 |
| 5 | schedule, private draw, unlinkable | 11 d | 65 d | 0.030 |
| 5 | schedule, every unit voting | 11 d | 22 d | 0.010 |
| 8 | one vote a message, unlinkable | 21 d | 2,085 d | 0.957 |
| 8 | one vote a message, linkable keys | 21 d | 2,094 d | 0.961 |
| 8 | schedule, public draw, unlinkable | 22 d | 2,077 d | 0.953 |
| 8 | schedule, public draw, linkable keys | 22 d | 1,450 d | 0.665 |
| 8 | schedule, private draw, unlinkable | 22 d | 1,779 d | 0.817 |
| 8 | schedule, every unit voting | 22 d | 1,494 d | 0.686 |

The layers decide. At three layers every design sizes the holder within 16 days. At five, within
328. At eight, unlinkable votes of the public draw leave 0.95 to 0.96 of today's time, by one vote a
message or by the schedule. Linkable keys cost 30 % of it in the schedule, where one attributed
message ties the node's every unit, and nothing with one vote a message. The private draw and every unit voting reveal more in each
attributed message, 0.82 and 0.69 of today's.

At eight layers, by holder:

| holder | today: days to size | schedule, public draw, unlinkable: days / of today's | schedule, public draw, linkable keys | one vote a message, unlinkable |
| --- | --- | --- | --- | --- |
| 1 % | 218 d | 210 d / 0.96 | 202 d / 0.93 | 208 d / 0.96 |
| 0.1 % | 2,179 d | 2,077 d / 0.95 | 1,450 d / 0.67 | 2,085 d / 0.96 |
| 0.01 % | 21,789 d | 20,748 d / 0.95 | 5,692 d / 0.26 | 20,846 d / 0.96 |

What a node's count of messages hides, as a share of the registered stake: today's quota ceiling for
blocks, the stake whose wins a slot match a node's share of one cover message a round (M.3); with
one vote a message, that ceiling over the emission multiple; in the schedule, the most units whose
drawn count exceeds `k_max` with chance at most `1e-9` a round:

| what a node sends | on 1,000 core nodes | on 20,000 core nodes |
| --- | --- | --- |
| blocks only, today | 2.95 % | 0.147 % |
| one vote a message, rounds of 600 s, every honest unit online | 0.0105 % | 0.0005 % |
| one vote a message, rounds of 600 s, 95 % online | 0.0025 % | 0.0001 % |
| the schedule, every honest unit online, a proof a unit | 0.93 % | 0.93 % |
| the schedule, every honest unit online, a proof a message | 3.62 % | 3.62 % |
| the schedule, 95 % online, a proof a unit | 0.32 % | 0.32 % |
| the schedule, 95 % online, a proof a message | 1.03 % | 1.03 % |
| the schedule, every unit voting, a proof a unit | 0.31 % | 0.31 % |
| the schedule, every unit voting, a proof a message | 0.94 % | 0.94 % |

One vote a message lets anyone who counts a node's messages size every holder above 0.0105 % of the
stake on 1,000 core nodes and 0.0005 % on 20,000, whatever the layers. The schedule hides every
holder up to 0.93 % with a proof a unit and 3.62 % with a proof a message, against today's 2.95 % on
1,000 core nodes and 0.147 % on 20,000. Only the schedule keeps C1, and on 1,000 core nodes only
with a proof a message: a proof a unit lowers today's ceiling there from 2.95 % to 0.93 %.

Gates (`tests/test_unitnet.py`): an observer averaging the drawn units of attributed messages
estimates the stake with the relative spread `1/sqrt(m·c)`, for the hypergeometric and the binomial
count; the mean time to size without votes is the Blend report's, with single observations the
merged Poisson process's and `attribution_days`', and with an exact sizing at an epoch's end with
chance `p`, `E/p`; with messages worth several observations and observations at epochs' ends, the
simulated first-passage mean; the chance that one of several messages is tied; the count ceiling
against a direct count. Seven registered mutations fail them.

## N.5 — cost

A unit's vote is its tag and its RLN share, 64 bytes; a message adds the block and the round, 40
bytes, and a Groth16 proof, 128 bytes, a unit or a message. A registration is 196 bytes: the unit
key, the proof, the tag and the epoch.

| packaging | a unit's vote (bytes) | a message's own bytes | units' votes a message carries, at most | a certificate of the quorum against 30 %, every honest unit online (KB) |
| --- | --- | --- | --- | --- |
| a proof a unit | 192 | 40 | 94 | 719 to 867 |
| a proof a message | 64 | 168 | 281 | 241 to 867 |

Verifying: a Blend header carries a Groth16 proof of quota and a signature, and Blend measured 157
headers a second on one Pi 5 core, so a proof costs at most 1/157 s there.

| packaging | proofs | one Pi 5 core, rounds of 10 minutes / an hour |
| --- | --- | --- |
| a proof a unit | public draw, every honest unit online, 5,602 proofs a round | 5.9 % / 1.0 % |
| a proof a unit | public draw, 95 % online, 23,364 proofs a round | 24.8 % / 4.1 % |
| a proof a unit | every unit voting, 30,000 proofs a round | 31.8 % / 5.3 % |
| a proof a message | one from each of 1,000 core nodes | 1.1 % / 0.2 % |
| a proof a message | one from each of 20,000 core nodes | 21.2 % / 3.5 % |

Proving, on the Apple M4 Pro of `tools/benchmarks/pol-proving`, all cores, a proof of leadership in
72.45 ms: a registration and a unit's vote are taken at one proof of leadership each. Their circuits
prove the same kinds of statement, a membership in a tree, a tag and a comparison, and are not
measured. One proof a message must fix its slots at `k_max`, 281, so that its verifying key shows
nothing, and every node proves all of them each round; it is not measured either. The reference
board's run is the owner's.

| committee against 30 % | holder | registrations an epoch (s) | votes a round | proving a round (s) | the machine, rounds of 10 minutes |
| --- | --- | --- | --- | --- | --- |
| public draw, every honest unit online | 1 % | 21.7 | 56.0 | 4.06 | 0.68 % |
| public draw, every honest unit online | 0.1 % | 2.2 | 5.6 | 0.41 | 0.07 % |
| public draw, every honest unit online | 0.01 % | 0.2 | 0.6 | 0.04 | 0.01 % |
| every unit voting | 1 % | 21.7 | 300.0 | 21.73 | 3.62 % |
| every unit voting | 0.1 % | 2.2 | 30.0 | 2.17 | 0.36 % |
| every unit voting | 0.01 % | 0.2 | 3.0 | 0.22 | 0.04 % |

Linkable keys would make a round's certificate one aggregate signature and a bitmap of the 30,000
units, 3,750 bytes, at the privacy N.4 prices; not measured.

## N.6 — how fast

M.2's mean time at a lag of 30 slots: the wait for the next round start, the quorum's last honest
vote leaving `R·Q/H` into a round over which the votes go out evenly, the delivery, and for the
checkpoint gadget one round more. The delivery is D6's largest 95th percentile on the
specification's Blend, 10.34 s at three layers, plus at most `Δ_max = 3` rounds for each further
layer. The round is the shortest whose votes add at most a fifth, a half or all of one Pi 5 core of
verifications, a proof a unit. Against 30 % with every honest unit online, at 8 layers, beside the
chain's 3.09 hours under random delay and 5.93 under the worst case at 10 s:

| transport | core nodes | verifications the votes add, share of one Pi 5 core | round (s) | final on average: the checkpoint gadget / one certificate | the node budget, in Pi 5 cores / received (MB/s) | a holder of 0.1 % sized (days) / of today's |
| --- | --- | --- | --- | --- | --- | --- |
| Blend as specified | any | M.2's budget | 4,202 | 2.87 h / 1.71 h | 0.99 / 1.55 | 100 / 0.05 |
| schedule, 8 layers | 1,000 | 20 % | 434 | 18.7 min / 11.4 min | 2.10 / 2.66 | 2,039 / 0.94 |
| schedule, 8 layers | 1,000 | 50 % | 174 | 8.0 min / 5.1 min | 3.73 / 4.79 | 1,851 / 0.85 |
| schedule, 8 layers | 1,000 | 100 % | 87 | 4.5 min / 3.0 min | 6.45 / 8.34 | 1,599 / 0.73 |
| schedule, 8 layers | 20,000 | 20 % | 5,274 | 3.61 h / 2.14 h | 2.77 / 3.58 | 2,165 / 0.99 |
| schedule, 8 layers | 20,000 | 50 % | 2,110 | 1.45 h / 52.0 min | 5.50 / 7.10 | 2,150 / 0.99 |
| schedule, 8 layers | 20,000 | 100 % | 1,055 | 44.0 min / 26.5 min | 10.03 / 12.96 | 2,121 / 0.97 |
| one vote a message, 8 layers | any | 20 % | 1,606 | 1.11 h / 39.8 min | 2.63 / 3.39 | 2,142 / 0.98 |
| one vote a message, 8 layers | any | 50 % | 643 | 27.2 min / 16.5 min | 5.16 / 6.62 | 2,091 / 0.96 |
| one vote a message, 8 layers | any | 100 % | 322 | 14.1 min / 8.7 min | 9.27 / 11.99 | 2,010 / 0.92 |

The schedule at 8 layers on 1,000 core nodes finalizes in 18.7 minutes on average with a fifth of a
core, keeping 0.94 of today's time to size a holder of 0.1 %; with all of a core in 4.5 minutes at
0.73. On 20,000 core nodes a fifth of a core needs rounds of 5,274 s, 3.61 hours, later than the
chain; all of a core 44.0 minutes at 0.97. Every row needs Blend's node budget and bandwidth to grow:
2.10 Pi 5 cores and 2.66 MB a second on 1,000 core nodes at a fifth, where today needs 0.96 and 1.24.
One vote a message is as fast at 8 layers but fails C1 by its count of messages (N.4). Blend as
specified finalizes in 2.87 hours and sizes the holder in 100 days.

At a fifth of a core, by layers:

| core nodes | layers | round (s) | final on average, the checkpoint gadget | a holder of 0.1 % sized (days) / of today's |
| --- | --- | --- | --- | --- |
| 1,000 | 3 | 274 | 11.9 min | 5.9 / 0.003 |
| 1,000 | 5 | 338 | 14.6 min | 169 / 0.08 |
| 1,000 | 8 | 434 | 18.7 min | 2,039 / 0.94 |
| 20,000 | 3 | 2,090 | 1.43 h | 44.3 / 0.020 |
| 20,000 | 5 | 3,364 | 2.30 h | 983 / 0.45 |
| 20,000 | 8 | 5,274 | 3.61 h | 2,165 / 0.99 |

With 95 % of the honest units online:

| committee against 30 %, 95 % of the honest units online | units a round | core nodes | verifications the votes add, share of one Pi 5 core | round (s) | final on average, the checkpoint gadget | a holder of 0.1 % sized (days) / of today's |
| --- | --- | --- | --- | --- | --- | --- |
| a public draw | 23,364 | 1,000 | 20 % | 999 | 42.3 min | 1,725 / 0.79 |
| a public draw | 23,364 | 1,000 | 50 % | 400 | 17.5 min | 1,262 / 0.58 |
| a public draw | 23,364 | 1,000 | 100 % | 200 | 9.2 min | 821 / 0.38 |
| a public draw | 23,364 | 20,000 | 20 % | 5,840 | 4.04 h | 2,091 / 0.96 |
| a public draw | 23,364 | 20,000 | 50 % | 2,336 | 1.63 h | 1,967 / 0.90 |
| a public draw | 23,364 | 20,000 | 100 % | 1,168 | 49.3 min | 1,782 / 0.82 |
| every unit voting | 30,000 | 1,000 | 20 % | 1,211 | 50.9 min | 1,795 / 0.82 |
| every unit voting | 30,000 | 1,000 | 50 % | 485 | 20.9 min | 1,377 / 0.63 |
| every unit voting | 30,000 | 1,000 | 100 % | 243 | 10.9 min | 944 / 0.43 |
| every unit voting | 30,000 | 20,000 | 20 % | 6,051 | 4.18 h | 2,094 / 0.96 |
| every unit voting | 30,000 | 20,000 | 50 % | 2,421 | 1.68 h | 1,974 / 0.91 |
| every unit voting | 30,000 | 20,000 | 100 % | 1,211 | 50.9 min | 1,795 / 0.82 |

The lag of 30 slots holds under random delay only: under the worst case a target 30 slots back can
be split (M.2), so these times are read beside the chain's 3.09 hours under random delay.

Gates: M.2's `finality_time`, `latest_time` and `emission_time` (`tests/test_signers.py`); the
delivery bound (`tests/test_unitnet.py`), which a registered mutation fails.

## N.7 — what else changes

- **C3.** Every node can compute a public draw a round ahead. A key tied to its node, through an
  attributed registration or linkable keys, can be targeted in the rounds it is drawn; with
  unlinkable votes that costs liveness only. The private draw names nobody, at 15,835 seats against
  30 % where the public draw takes 5,602.
- **Slashing.** A second vote in a round reveals the unit's secret. That excludes the unit for the
  rest of its epoch. It reaches the note behind the unit only if the registration carries the note
  under a key the secret opens, which the registration proof would then also prove; RLN-v1 takes the
  stake the same way, "If the financial stake is put in place, the user also risks his stake being
  taken."
- **Edge nodes.** Blend "is optimized for the privacy of core nodes": a holder behind an edge node
  shows its messages to the core node it connects to, and the schedule's count hides nothing there.
- **The node class.** Every useful row of N.6 doubles Blend's node budget at least, which Q7 leaves to
  the owner.
- **The registry on chain.** 5.88 MB an epoch in the snapshot phase's blocks, and 191 seconds of a Pi
  5 core an epoch to verify. A bootstrapping node needs the registry of the epochs whose certificates
  it reads.
- **Rounding.** Notes below a unit carry no weight. Merging notes to whole units links them on the
  transparent ledger.
- **The lottery.** Dividing by the registered stake trades the inference's tracking of offline stake
  for a count no stake can enter unannounced (N.2).

## Verdicts

- **H34 holds.** Drawn publicly without replacement from 30,000 registered units, a committee against
  30 % at `1e-9` needs 5,602 units a round with every honest unit online, where seats need 33,473,
  and 279,488 sized for the inference's error. Every unit voting holds 30 % from 93.9 % of the honest
  units online, so at 95 %, where M.1's count needs 78,979.
- **H35 holds.** With the lottery dividing by the registered stake the true over the counted stake
  stays at most one, so the slot rule's 18 hours hold a third at 10 s whatever stake joins, 10.11
  hours, and 12.49 hours with 95 % of the honest registered stake online.
- **H36 holds for the verifications, not for the node class.** At 8 layers and rounds of 10 minutes
  the schedule adds 14.4 % of a Pi 5 core on 1,000 core nodes, 24.6 % with today's load, and 175.8 %
  on 20,000. Blend's own rules then need node budgets of 1.77 and 16.91 Pi 5 cores.
- **H37 holds.** At three layers the votes of a committee against 30 % in rounds of 10 minutes size a
  holder of 0.1 % within 13 to 15 days with unlinkable votes, against 2,179 from its blocks alone. At
  eight layers it takes 2,077 to 2,085 days.
- **H38 holds in the schedule and fails with one vote a message.** Linkable keys size a holder of
  0.1 % at 8 layers in 0.70 of the time unlinkable votes take in the schedule, 1,450 days against
  2,077. With one vote a message a unit's votes are rarely attributed within its epoch, and the time
  does not shorten.
- **H39 holds with every honest unit online.** A proof a unit costs 5.9 % of a Pi 5 core at rounds
  of 10 minutes against 30 %. With 95 % online, 24.8 %.
- **H40 holds.** With a holder of 0.1 % sized no sooner than 0.94 of today's time, at 8 layers and a
  fifth of a Pi 5 core, the schedule finalizes against 30 % in 18.7 minutes on average on 1,000 core
  nodes, and in 3.61 hours on 20,000, later than the chain's 3.09. With all of a core, 20,000 core
  nodes take 44.0 minutes.

By variant, against 30 %, privacy first:

- **The schedule with a public draw, unlinkable votes and 8 layers: the one design that keeps
  today's privacy and finalizes in minutes.** It keeps 0.94 of today's time to size a holder of
  0.1 %. By its count of messages it hides every holder up to 3.62 % with one proof a message, above
  today's 2.95 % on 1,000 core nodes, and up to 0.93 % with a proof a unit. It finalizes in 18.7
  minutes on 1,000 core nodes with a fifth of a core of verifications, counted for a proof a unit;
  one proof a message verifies fewer proofs there, but its 281 slots are not measured. It needs
  every honest unit online for 5,602 units a round, Blend's node budget doubled and its messages
  taking eight layers, and it gives up C3's letter. On 20,000 core nodes it gains on the chain only
  with most of a core.
- **Every unit voting: no draw, and safety exact.** It holds 30 % from 93.9 % of the honest units
  online with 30,000 votes a round, where a public draw needs 23,364 at 95 %. At 95 % online it
  finalizes in 50.9 minutes on 1,000 core nodes with a fifth of a core, at 0.82 of today's time to
  size a holder.
- **The private draw: keeps C3, at 15,835 seats** against 30 %, and reveals more in each attributed
  message, 0.82 of today's time at 8 layers.
- **One vote a message: not recommended.** Its count of messages sizes every holder above 0.0105 %.
- **Blend as specified: not recommended.** 2.87 hours, and a holder of 0.1 % sized in 100 days.
- **Linkable keys: not recommended** in the schedule; one aggregate signature a round costs 30 % of
  the time to size a holder of 0.1 %.
- **The lottery divided by the registered stake: a candidate.** It removes M.7's rise at no cost in
  the wait from 90 % online up, and slows the chain while registered stake is offline.

## What the phase leaves open

- Blend at eight layers: its privacy beyond the path model, its delay, and a node class whose budget
  doubles. The Blend owners' trade.
- The vote and registration circuits, and a proof a message with 281 slots: not measured; the Pi 5
  run.
- How many core nodes the network will have: the schedule gains on the chain on 1,000 and needs most
  of a core on 20,000.
- Whether a public draw meets C3's purpose, and whether C3's letter may yield: the owner's decision.
- A lag that holds under the worst case.
- Slashing the note behind a unit.
- Votes from holders behind edge nodes.
- Whether the lottery should divide by the registered stake: C2's trade of N.2.
