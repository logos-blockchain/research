# Stake counted in anonymous units

*Whether a public stake value unlinked from its owner can carry certificates that make a
Cryptarchia block final sooner than the chain does, and what it costs in privacy, in Blend and in
time. It reads Phase N of the study (`tools/simulators/finality/UNITS.md`) beside the other signers
of [`signers.md`](signers.md). Every number comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality). Specifications are read at
`logos-lips` `bd1ca2c8`. One slot is one second and `f = 1/30`. The active stake is 30 % of the
supply, so today's minimum stake, 0.001 % of the supply, makes 30,000 units.*

---

## 1. Summary

Privacy is read first. A design is judged first by how soon it lets an observer know a holder's
stake, against the 2,179 days a holder of 0.1 % takes to be sized to ±10 % from its blocks alone
today. Its time to finality comes second.

A public stake value can be unlinked from its owner only as a count of equal units. A registry of
anonymous unit keys counts the stake exactly, which removes the inference's margins and shrinks the
committee five- to fifty-fold. The wall is the transport: every vote is a message, and Blend floods
every message at every layer to every core node.

Against 30 %, every honest unit online, a public draw of 5,602 units a round, a holder of 0.1 %:

| design | time until final, on average | a holder of 0.1 % sized (days) / of today's | what it needs |
| --- | --- | --- | --- |
| the chain alone, for comparison | its own wait: 3.09 hours under random delay, 5.93 under the worst case at 10 s | 2,179 / 1 | nothing |
| votes through Blend as specified | 2.87 h | 100 / 0.05 | rounds of 4,202 s |
| the vote schedule at 8 layers, 1,000 core nodes, votes adding a fifth of a Pi 5 core | 18.7 min | 2,039 / 0.94 | Blend's node budget at 2.10 Pi 5 cores and 2.66 MB a second, where today needs 0.96 and 1.24 |
| the same with all of a core | 4.5 min | 1,599 / 0.73 | 6.45 Pi 5 cores, 8.34 MB a second |
| the vote schedule at 8 layers, 20,000 core nodes, a fifth of a core | 3.61 h | 2,165 / 0.99 | 2.77 Pi 5 cores, 3.58 MB a second |
| the same with all of a core | 44.0 min | 2,121 / 0.97 | 10.03 Pi 5 cores, 12.96 MB a second |
| one vote a message at 8 layers | 14.1 min to 1.11 h | 2,010 to 2,142 | nothing hides by count: every holder above 0.0105 % of the stake is sized by counting its messages |

**What the comparison shows.**

- **Units must be equal.** Mantle's notes are public, so a distinctive value points at its note, and
  a weight that shows stake lets an observer bucket a leader "as high/low stake", the risk the
  Cryptarchia specification names. Equal units show nothing but their number (§2).
- **Counting shrinks the committee.** A public draw from 30,000 counted units needs 5,602 a round
  against 30 %, where anonymous seats need 33,473 without a margin and 279,488 sized for the
  inference's error. With 95 % online every unit voting, 30,000 a round, holds 30 %; seats need
  361,880. Nothing holds a third (§3).
- **A lottery that divides by the registered stake cannot be surged** and costs nothing in the wait
  from 90 % online up (§4).
- **Blend's flooding caps the votes, not the network.** Delivering votes to a few collectors saves
  only the final broadcast, which Blend's budget does not count. The vote schedule, one message a
  core node a round, keeps a node's count of messages independent of its stake, at a load that grows
  with the number of core nodes (§5).
- **The layers decide privacy.** At three layers every design sizes a holder of 0.1 % within 16 days,
  at five within 328, at eight in 0.95 to 0.96 of today's time with unlinkable votes (§6).
- **The price is Blend's node class.** Every useful configuration at least doubles the node budget
  Blend's rules size (§8).

**The verdict.** The vote schedule, with a public draw from counted units, unlinkable votes and eight
layers, is the one design that keeps today's privacy and finalizes in minutes: 18.7 minutes against
30 % on 1,000 core nodes, keeping 0.94 of today's time to size a holder of 0.1 %. On 1,000 core
nodes its count of messages hides as much stake as today's only with one proof a message for all of a
node's units, whose 281 slots are not measured. It needs every honest unit online, Blend's node
budget doubled and its messages taking eight layers, and it gives up C3's letter, a committee drawn
by a private lottery. On 20,000 core nodes it gains on the chain only
with most of a core. Its circuits are not measured, and the Pi 5 run is the owner's.

## 2. The design

- **A unit** is a fixed amount of stake, by default today's minimum stake.
- **Registration.** In the snapshot phase of each epoch, once the snapshot is final, a holder
  registers each unit its notes hold for the next epoch: a fresh unit key and a proof, built like the
  proof of leadership, that a note in the snapshot holds at least `(j + 1)` units, with a tag from
  the note's secret, the epoch and `j` that stops a second registration. The proof hides the note
  and `j`.
- **The registry** is the epoch's unit keys. Every node counts them, and no key names its holder. The
  stake-weighted mix RLN of `logos-lips` names this as the fix for its own leak: "A complete fix at
  the registry layer requires a shielded membership registry that hides the stake-to-identity link
  via ZK".
- **Committees.** A public draw takes the `n` keys with the lowest values of a function of the key
  and the round's randomness, so every node knows the drawn keys. A private draw makes each unit a
  seat by its secret. Or every unit votes.
- **A vote** proves that its sender holds the secret of a drawn unit without showing which. Its tag
  comes from that secret and the round, and its RLN share makes a second vote in the round reveal the
  unit's secret, as RLN-v1 does.

The registry closes a whole buffer phase before the epoch nonce is fixed, as the stake snapshot
does, since "If an adversary can predict the nonce, they can grind their coin secret keys to gain an
advantage." A registry that closed later would let a coalition grind its keys into one round.

## 3. What a counted committee holds

Two conflicting certificates need the coalition's units twice and every honest unit once, and a
round stalls when the honest units online fall short of the quorum. The coalition holds 9,000 of
the 30,000 units against 30 %.

| committee a round, against 30 % at `1e-9` | every honest unit online | 95 % online |
| --- | --- | --- |
| anonymous seats, no margin | 33,473 | 361,880 |
| anonymous seats, sized for the inference's error up to 1.05 | 279,488 | none |
| counted, drawn with replacement (M.1) | 6,922 | 78,979 |
| a private draw over 30,000 units, seats expected | 15,835 | 28,367 |
| a public draw from 30,000 units | 5,602 | 23,364 |
| every unit voting | 30,000, holds | 30,000, holds |

At 90 % online nothing holds 30 %, and nothing holds a third. Every unit voting holds 30 % from
93.9 % online.

The unit's size sets how many vote and how much is lost. With units of 0.0001 % of the supply,
300,000 units, a public draw against 30 % needs 6,763 a round; with units of 0.01 %, 3,000 units,
it needs 2,062, and none holds at 95 % online. The coalition sizes its notes in whole units, while
an honest note loses its value below a whole unit, less than one unit a note. Against 30 % that
counts: with 5 % of the honest stake lost the coalition holds 31.1 % of the units, a public draw at
full uptime needs 10,033, and every unit voting needs 96.0 % online.

## 4. The registry and the lottery

30,000 registrations go on chain in a window of 36 h, 0.231 a second, 196 bytes each, 5.88 MB an
epoch. A holder of 1 % registers 300 units an epoch, of 0.1 % 30. Every node verifies them in 191
seconds of a Pi 5 core an epoch.

If the leader lottery divides by the registered stake, only registered stake leads, and no stake can
enter unannounced, the rise M.7 found. Registered stake that goes offline then slows the chain
instead. Under the worst case at 10 s:

| coalition | honest registered stake online | the wait (h): divided by the registered stake / by the inferred |
| --- | --- | --- |
| 30 % | all | 5.93 / 5.93 |
| 30 % | 90 % | 8.40 / 8.39 |
| a third | all | 10.11 / 10.11 |
| a third | 95 % | 12.49 / 12.55 |
| a third | 90 % | 15.99 / 16.23 |
| a third | two thirds | 127.84 / 153.79 |

The wait moves by less than 2 % from 90 % online up, and the slot rule's 18 hours hold a third down
to 90 % either way. A holder that registered and went offline slows the chain until a registry
without it.

## 5. What carries the votes

Blend relays every message to all core nodes at every layer: a received message "is immediately
released to all neighboring nodes, except the one it was received from", and every node checks its
proof of quota. A vote message at `h` layers therefore adds `h` messages on every core connection,
wherever its payload finally goes. Blend's own rules then size the read limit and the slowest node's
budget from that load.

- **Blend as specified** carries 4/3 to 2.27 votes a second, so a round of 5,602 votes takes 41.2
  minutes to 1.17 hours.
- **One vote a message** with the read limit raised: a node sends one message for each drawn unit,
  so its count of messages grows with its stake.
- **The vote schedule**: every core node sends exactly one vote message a round, empty when none of
  its units is drawn, carrying all its drawn units' votes. Its count says nothing of its stake, and
  its load grows with the core nodes, `h·N/R` messages a connection.

At rounds of 10 minutes against 30 %:

| core nodes | layers | transport | verifications the votes add, share of one Pi 5 core | the node budget Blend's rules need, Pi 5 cores | received (MB/s) |
| --- | --- | --- | --- | --- | --- |
| any | 3 | today's traffic, no votes | 0 | 0.96 | 1.24 |
| 1,000 | 8 | one vote a message | 53.5 % | 5.45 | 7.01 |
| 1,000 | 8 | the schedule, a proof a unit | 14.4 % | 1.77 | 2.27 |
| 20,000 | 8 | the schedule, a proof a unit | 175.8 % | 16.91 | 21.84 |

Forwarding point to point, as the libp2p mix of `logos-lips` forwards its packets "hop-by-hop",
would carry a vote message eight times in all, 0.013 messages a node a second at any size of
network, where Blend's flooding carries 13.3 on 1,000 core nodes and 266.7 on 20,000. Its exposure
to an observer of links lies outside Blend's analysis, and C4 binds, so it is described only.

## 6. What the votes reveal

The study's model: a message is tied to its node when its whole blend path is adversarial, `0.2^h`
at `h` layers. A message of the schedule that is tied reveals how many units it carries, a draw from
the node's units. At rounds of 10 minutes against 30 %, a holder of 0.1 %:

| layers | votes | days to size to ±10 % | of today's time |
| --- | --- | --- | --- |
| – | none: blocks only, today | 2,179 d | 1 |
| 3 | the schedule, a public draw, unlinkable | 13 d | 0.006 |
| 5 | the schedule, a public draw, unlinkable | 283 d | 0.130 |
| 8 | the schedule, a public draw, unlinkable | 2,077 d | 0.953 |
| 8 | the schedule, a public draw, linkable keys | 1,450 d | 0.665 |
| 8 | the schedule, a private draw, unlinkable | 1,779 d | 0.817 |
| 8 | the schedule, every unit voting | 1,494 d | 0.686 |
| 8 | one vote a message, unlinkable | 2,085 d | 0.957 |

- **Unlinkable votes are needed in the schedule.** One key a unit signing every vote of an epoch
  would allow one aggregate signature a round, but one tied message then ties the node's every unit,
  and the time falls by 30 %.
- **A node's count of messages is the other leak**, which the stake-weighted mix RLN names too: "A
  node's rate is also observable at the network layer from its traffic." The most stake a node's
  count hides, as a share of the registered stake:

| what a node sends | on 1,000 core nodes | on 20,000 core nodes |
| --- | --- | --- |
| blocks only, today | 2.95 % | 0.147 % |
| one vote a message, rounds of 600 s, every honest unit online | 0.0105 % | 0.0005 % |
| the schedule, every honest unit online, a proof a unit | 0.93 % | 0.93 % |
| the schedule, every honest unit online, a proof a message | 3.62 % | 3.62 % |

One vote a message fails C1 by counting alone, whatever the layers. The schedule keeps C1, and on
1,000 core nodes only with one proof a message, since a proof a unit lowers today's ceiling there
from 2.95 % to 0.93 %.

## 7. Cost

- **Bytes.** A unit's vote is 64 bytes, its tag and its RLN share, with a Groth16 proof of 128 bytes
  a unit or a message. A message carries at most 94 units' votes with a proof a unit and 281 with
  one proof a message. A certificate of the quorum against 30 % is 719 to 867 KB with a proof a unit.
- **Verifying.** A Blend header carries a Groth16 proof of quota and a signature, and Blend measured
  157 headers a second on one Pi 5 core. At rounds of 10 minutes a proof a unit costs 5.9 % of that
  core against 30 % with every honest unit online, 24.8 % with 95 % online, and 31.8 % for every
  unit voting.
- **Proving.** Taken at one proof of leadership each, 72.45 ms on all cores of an Apple M4 Pro: a
  holder of 1 % proves its registrations in 21.7 s an epoch and its votes in 4.06 s a round. The vote
  and registration circuits are not measured, nor is one proof a message, whose 281 slots every node
  proves each round.

## 8. How fast

M.2's mean time at a lag of 30 slots, with the delivery through `h` layers. The round is the
shortest whose votes add at most a fifth, a half or all of one Pi 5 core of verifications. Against
30 % with every honest unit online, the vote schedule at 8 layers:

| core nodes | the votes' share of one Pi 5 core | round (s) | final on average: the checkpoint gadget / one certificate | the node budget, in Pi 5 cores / received (MB/s) | a holder of 0.1 % sized (days) / of today's |
| --- | --- | --- | --- | --- | --- |
| 1,000 | 20 % | 434 | 18.7 min / 11.4 min | 2.10 / 2.66 | 2,039 / 0.94 |
| 1,000 | 50 % | 174 | 8.0 min / 5.1 min | 3.73 / 4.79 | 1,851 / 0.85 |
| 1,000 | 100 % | 87 | 4.5 min / 3.0 min | 6.45 / 8.34 | 1,599 / 0.73 |
| 20,000 | 20 % | 5,274 | 3.61 h / 2.14 h | 2.77 / 3.58 | 2,165 / 0.99 |
| 20,000 | 50 % | 2,110 | 1.45 h / 52.0 min | 5.50 / 7.10 | 2,150 / 0.99 |
| 20,000 | 100 % | 1,055 | 44.0 min / 26.5 min | 10.03 / 12.96 | 2,121 / 0.97 |

At three layers the same budget gives 11.9 minutes on 1,000 core nodes but sizes a holder of 0.1 %
in 5.9 days. With 95 % of the honest units online, every unit voting finalizes in 50.9 minutes on
1,000 core nodes at a fifth of a core, at 0.82 of today's time to size a holder. The lag of 30 slots
holds under random delay only, so these times are read beside the chain's 3.09 hours under random
delay.

## 9. What else changes

- **C3.** A public draw is known a round ahead, so a key once tied to its node can be targeted in
  its rounds; with unlinkable votes that costs liveness only. A private draw names nobody, at 15,835
  seats where the public draw takes 5,602.
- **Slashing.** A second vote in a round reveals the unit's secret, which excludes the unit for its
  epoch. It reaches the note behind the unit only if the registration carries the note under a key
  the secret opens.
- **Edge nodes.** Blend "is optimized for the privacy of core nodes": a holder behind an edge node
  shows its messages to the core node it connects to.
- **Rounding.** Notes below a unit carry no weight, and merging notes to whole units links them on
  the transparent ledger.
- **The node class.** Every useful configuration at least doubles the node budget Blend's rules size,
  a line Q7 leaves to the owner.

No specification is a candidate yet. The lottery divided by the registered stake is the one change
that stands alone: it removes M.7's rise at no cost in the wait from 90 % online up.

## 10. Open questions

- Blend at eight layers: its privacy beyond the path model, its delay, and a node class whose budget
  doubles. The Blend owners' trade.
- The vote and registration circuits, and one proof a message with 281 slots; the Pi 5 run.
- How many core nodes the network will have: the schedule gains on the chain on 1,000 and needs most
  of a core on 20,000.
- Whether a public draw meets C3's purpose, and whether C3's letter may yield: the owner's decision.
- A lag that holds under the worst case.
- Slashing the note behind a unit.
- Votes from holders behind edge nodes.
- Whether the lottery should divide by the registered stake.

## 11. Reproducing the figures

```
cd tools/simulators/finality
make n1 n2 n3 n4 n5 n6        # N.2 about 10 minutes on 12 cores, the rest seconds to minutes
make check-tables             # every table of UNITS.md, verbatim
python -m pytest tests/test_units.py tests/test_unitnet.py
python scripts/check_mutations.py "units:"; python scripts/check_mutations.py "unitnet:"
```

`make n3` to `make n6` read `runs/n1`; `make n6` also reads `runs/d6` and `runs/m2`.
