# Certificates from other signers

*Which other signers could certify a Cryptarchia block so that it is final sooner than the slot
rule's 18 hours, and what finality then rests on. It reads Phase M of the study
(`tools/simulators/finality/SIGNERS.md`) beside certificates of Blend's declared nodes
([`network.md`](network.md)) and finality counted in slots ([`slots.md`](slots.md)). Every number
comes from a `make` target of [`tools/simulators/finality`](../../tools/simulators/finality).
Specifications are read at `logos-lips` `bd1ca2c8`, and Ouroboros Peras at
`cardano-foundation/CIPs` `86b89208`. One slot is one second and `f = 1/30`.*

---

## 1. Summary

A certificate shortens finality only where it makes a block final sooner than the chain itself
settles it against the same coalition, under the same delay model. Every signer set is read against
that yardstick. Against the study's 30 % to a third, only one set rests on the stake share and
finalizes in about two minutes, and it makes public the stake of every holder that stakes.

| signers | against 30 %: time until final | safety rests on | what a vote shows |
| --- | --- | --- | --- |
| the chain alone, for comparison | its own wait: 3.09 hours under random delay, 5.93 under the worst case at 10 s; the slot rule's 18 hours hold a third | the stake | nothing |
| anonymous seats through Blend (Phase D) | 10.1 to 17.2 hours on average under random delay, every honest seat counting; 3.7 to 6.3 days with the inference's error | a sampled committee of 33,473 seats a round; a third never | a seat won; the quota ceiling falls 41 to 69-fold |
| the chain's own leaders through Blend | 2.1 to 3.5 hours on average under random delay, every honest leader online; 24 to 41 hours with 95 % online | a counted committee of 6,922 lottery wins, if the coalition keeps no honest win out of the record; a third never | the win its sender led, tied to its leader's node with chance 0.286 to 0.430 |
| Blend's declared nodes, or another opt-in set | 120 s on average | the volunteers: at today's minimum stake, 1.67 % of the active stake holds a third of Blend's declarations | the volunteers' declarations |
| every leading note declared | 120 s on average | the stake, while at least 95.24 % of the honest stake is online and every honest holder can declare; a third never | the stake and node of every holder that stakes |
| weight delegated to declared operators | 120 s on average | where the delegation goes: it fails once the coalition's operators hold 4.76 % of the honest stake at full uptime, and with none attracted at 95.24 % online | each operator's total |

The public sets' 120 s are L.2's mean with rounds of 60 slots and a lag of 30 on the
specification's Blend, measured with 1,000 declarations. The ranges through Blend run from no vote
fitting its node's cover to equal stakes, where every vote first takes its node's scheduled cover.

**What the comparison shows.**

- **Votes that keep the stake private are slow, because Blend has little room for them.** A vote
  takes its node's next scheduled cover message, as a won slot does, and the votes beyond each
  node's cover fit only in the headroom Blend keeps for backlogs to drain, or in place of 30.8 % of
  its transaction messages. A round's votes then take hours to send against 30 %. Raising Blend's
  cover to keep today's quota ceiling makes every set through Blend slower than the chain at 10 %,
  25 % and 30 % (§4).
- **The chain's own leaders come closest.** Each block's header already carries a one-time key, and
  every node can count the wins on the finalized chain, so the committee needs neither the anonymous
  seats' Poisson margin nor the stake inference's. Under random delay they finalize sooner than the
  chain against a quarter. Against 30 % they do so only with every honest leader online through a
  window of 2.4 days, and they tie 29 % to 43 % of wins to their leaders' nodes (§3 to §5).
- **Public signers are fast at any share.** What they hold depends on who signs. Opt-in sets rest
  on their volunteers. Every leading note declared puts the coalition at its stake share.
  Delegated weight rests on which operators honest holders choose (§3).
- **The quorum matters at 30 %.** Ouroboros Peras's three quarters stall once a quarter of the
  weight withholds its votes; of the two quorums compared, only Casper FFG's two thirds can hold
  30 % (§7).
- **Reading the active stake as 30 % of the supply moves none of these figures.** A coalition of
  30 % then holds 9.0 % of the supply. Stake outside the active stake can join the lottery without
  notice, which leaves the anonymous seats no committee from 21.9 %, and holds the slot rule's 18
  hours against a third only while the true active stake stays within 1.925 times the inferred
  (§9).

**Verdict.** No signer set within the study's constraints C1–C5 finalizes a block in minutes
against 30 %. Every leading note declared does it in two minutes at the stake's own share, and is a
candidate only if the owner relaxes C1 and C3 for every holder that stakes (§2, §9). Delegated
weight does it only
while at least 95.24 % of the honest weight is online and the coalition's operators hold less than
4.76 % of the honest stake, so it is not recommended. Otherwise the slot rule's 18 hours stand.

---

## 2. The options

The study carries five constraints from the Cryptarchia specification: stake stays private (C1),
the chain never halts (C2), no participant set is known (C3), lottery wins travel through Blend
(C4), and the slowest node the protocol targets carries the load (C5). C1 quotes the
specification: "If the activity of the leader reveals their stake values (e.g. through weighted
voting), then this value can be used to reduce the anonymity set for the leader by bucketing the
leader as high/low stake and can open him up to targeting." The same list asks that "The block
proposals should not be linkable to a leader".

| set | who signs | weight | a vote shows | travels | constraints broken |
| --- | --- | --- | --- | --- | --- |
| anonymous seats (Phase D) | a note that wins a seat that round in a private lottery | one a seat | a seat won, by a proof | through Blend | C1: on top of today's cover the quota ceiling falls 41 to 69-fold; with the cover raised stake is sized 1.7 times as fast (M.3) |
| the chain's own leaders | the leaders of the latest wins recorded on the finalized chain, canonical or uncle | one a win, by its tag `ρ_LEAD` | the win its sender led | through Blend | C1: on top of today's cover a win is tied to its leader's node with chance 0.286 to 0.430, against 0.016; with the cover raised 0.026 (M.3) |
| an opt-in public set (D1b; Blend's declared nodes, Phase L) | holders who declare | by value, or one a declaration | the declaration | directly | C3; with weight by value, also C1 for the declared |
| every leading note declared | every note that may lead | by value | the declaration | directly | C1 and C3, for every holder that stakes |
| delegated weight | operators, with the weight notes delegate to them | by the value delegated | the operator's total | directly | C3, for the operators; C1 open, through the value each delegation moves |

- **The chain's own leaders need no new key.** Each block's proof of leadership is bound to a
  one-time key, `P_LEAD`, under which its header is signed, and uncles are recorded with their
  signed headers. A leader that keeps the key's secret can sign votes with it. The key is not tied
  to stake, so a leader's equivocation cannot be slashed, and the key can be sold within the window.
- **They are counted by win, on the finalized chain.** A winner may sign further headers for the
  same win and carry them as uncles, so the committee counts the win's tag, which the proof of
  leadership fixes by note and slot. It takes the latest wins recorded before a point at least 360
  slots before the latest finalized checkpoint, so that every node counts the same committee.
- **Every leading note declared** makes an SDP declaration the condition to lead, and locks every
  note that leads. The proof of leadership still hides which note won. A holder below SDP's minimum
  stake can no longer lead.
- **Delegated weight** is a sketch: a note proves once an epoch that it delegates its value to an
  operator, without showing which note it is. No circuit exists.
- **Outside the network**, a checkpoint anchored on another chain rests on that chain, and is out
  of scope.

---

## 3. What each set holds

A public set's certificate needs two thirds of its weight: safety needs the coalition below a
third of it, and liveness needs the honest weight online to reach two thirds on its own. A
committee of seats or wins needs a quorum sized for its sampling. Anonymous seats are a Poisson
number nobody counts, so their quorum also carries the stake inference's error: *the inference's
error up to 1.05* holds while the true stake exceeds the inferred by up to 5 %, about six standard
deviations. Stake joining from outside the active stake raises it further (§9). *Every honest seat counting* means every honest seat votes and every vote arrives. The
chain's own leaders are counted, so neither margin applies.

The anonymous sets:

| coalition | anonymous seats a round: every honest seat counting / the inference's error up to 1.05 / a tenth of the honest votes lost | the chain's own leaders, counted: wins / the time the chain takes to record them, every honest leader online | the same, 95 % of the honest leaders online | the same, 90 % online |
| --- | --- | --- | --- | --- |
| 10 % | 665 / 801 / 1,137 | 88 / 44.0 min | 130 / 1.1 h | 193 / 1.6 h |
| 25 % | 5,355 / 9,728 / 31,617 | 1,030 / 8.6 h | 2,185 / 18.2 h | 6,881 / 2.4 d |
| 30 % | 33,473 / 279,488 / none | 6,922 / 2.4 d | 78,979 / 27.4 d | none |
| a third | none / none / none | none | none | none |

The public sets:

| coalition | an opt-in set: the honest stake declared, uptime 1 / 0.95 | every leading note declared: the honest stake online, at least | with 5 % of the honest stake below the minimum stake: the coalition's share of the weight / the honest stake online, at least | the honest stake below the minimum stake that breaks it at full uptime |
| --- | --- | --- | --- | --- |
| 10 % | 22 % / 26 % | 74.07 % | 10.47 % / 74.46 % | 77.8 % |
| 25 % | 67 % / 78 % | 88.89 % | 25.97 % / 90.06 % | 33.3 % |
| 30 % | 86 % / none | 95.24 % | 31.09 % / 96.74 % | 14.3 % |
| a third | none / none | none | 34.48 % / none | – |

Delegated weight with every note delegating: the share of the honest stake the coalition's
operators may hold before the set fails, and how many of the largest holders hold that share if the
honest stake is spread as Cardano's pools are:

| coalition | uptime 1 | uptime 0.95 | uptime 0.9 | Cardano's largest pools that hold it, uptime 1 |
| --- | --- | --- | --- | --- |
| 10 % | 25.93 % | 22.03 % | 17.70 % | 84 of 2,522 |
| 25 % | 11.11 % | 6.43 % | 1.23 % | 35 of 2,522 |
| 30 % | 4.76 % | none | none | 15 of 2,522 |
| a third | none | none | none | – |

- **Counting the leaders shrinks the committee fivefold, while every honest leader is online.**
  Against a quarter they need 1,030 wins, where anonymous seats need 5,355 a round. With 95 % of the
  honest leaders online, 30 % needs 78,979 wins, 27.4 days of the chain. This holds only if the
  coalition keeps no honest win out of the record.
- **No opt-in set rests on the stake.** Whatever service it serves and whatever minimum stake it
  asks, it holds a coalition only while the honest stake declared exceeds D1b's frontier: 86 %
  against 30 % at full uptime, and none at 95 %.
- **Every leading note declared holds the coalition at its stake share**, if every honest holder
  can declare: 30 % while at least 95.24 % of the honest stake is online, a third never. Honest
  stake below the minimum stake leaves the leader lottery too, so with 14.3 % of it below, the
  coalition holds a third of both, and the slot rule's fallback fails with the certificates.
- **Delegated weight rests on where the delegation goes.** With every note delegating, against 30 %
  it fails once the coalition's operators hold 4.76 % of the honest stake at full uptime, what
  Cardano's 15 largest pools hold, and the edge falls to nothing at 95.24 % online.

---

## 4. How fast

A block first lies in a round's target at the first round start at least `L` slots after its slot.
A single certificate holds it once the quorum's votes have arrived, and the checkpoint gadget
finalizes it one round later: `L + (R − 1)/2` and `L + (R − 1)/2 + R` slots on average, plus the
time the quorum's votes take. A block just past a round's target waits `(R − 1)/2` longer.

**Public signers** gossip their votes directly: 120 s on average and 147 s at the 95th percentile,
with rounds of 60 slots and a lag of 30 on the specification's Blend, measured with 1,000
declarations ([`network.md`](network.md) §3).

**Votes through Blend.** A vote first takes its node's spare scheduled cover. The votes beyond each
node's cover must fit Blend's headroom, 4/3 messages a second network-wide, so the budget depends
on how the stake is spread:

| budget | votes a second, network-wide |
| --- | --- |
| no vote in a node's cover | 1.333 |
| Cardano's pools | 1.620 |
| equal stakes | 2.267 |
| cover raised | 0.044 |

With the cover raised to keep today's quota ceiling, a vote costs 30 cover messages. A committee of
`n` needs rounds of `n` over the budget, and the votes go out evenly over the round. With the
coalition withholding its own, the quorum's last honest vote leaves most of the way through it: 96 %
of the round for anonymous seats against 30 %. At a lag of 30 slots, with D6's largest
95th-percentile time to a quorum on the specification's Blend, 10.3 s, added:

| coalition | set | committee / quorum | no vote in a node's cover: round / gadget, mean / gadget, latest / single certificate, mean | Cardano's pools: round / gadget, mean | equal stakes: round / gadget, mean | cover raised: round / gadget, mean |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | anonymous seats, every honest seat counting | 665 / 458 | 8.3 min / 19.5 min / 23.7 min / 11.2 min | 6.8 min / 16.2 min | 4.9 min / 11.8 min | 4.2 h / 9.4 h |
| 10 % | anonymous seats, the inference's error up to 1.05 | 801 / 566 | 10.5 min / 24.7 min / 29.9 min / 14.2 min | 8.7 min / 20.5 min | 6.2 min / 14.8 min | 5.3 h / 12.0 h |
| 10 % | the chain's own leaders, counted, every honest leader online | 88 / 59 | 1.1 min / 3.1 min / 3.7 min / 2.0 min | 0.9 min / 2.7 min | 0.7 min / 2.1 min | 33.0 min / 1.2 h |
| 10 % | the chain's own leaders, counted, 95 % online | 130 / 84 | 1.6 min / 4.3 min / 5.2 min / 2.7 min | 1.4 min / 3.7 min | 1.0 min / 2.8 min | 48.8 min / 1.8 h |
| 25 % | anonymous seats, every honest seat counting | 5,355 / 3,642 | 1.1 h / 2.7 h / 3.3 h / 1.6 h | 55.1 min / 2.2 h | 39.4 min / 1.6 h | 33.5 h / 3.4 d |
| 25 % | anonymous seats, the inference's error up to 1.05 | 9,728 / 6,790 | 2.1 h / 5.2 h / 6.2 h / 3.1 h | 1.8 h / 4.3 h | 1.3 h / 3.1 h | 2.7 d / 6.5 d |
| 25 % | the chain's own leaders, counted, every honest leader online | 1,030 / 687 | 12.9 min / 31.4 min / 37.9 min / 18.6 min | 10.6 min / 26.0 min | 7.6 min / 18.8 min | 6.4 h / 15.4 h |
| 25 % | the chain's own leaders, counted, 95 % online | 2,185 / 1,428 | 27.3 min / 1.1 h / 1.3 h / 39.4 min | 22.5 min / 55.1 min | 16.1 min / 39.5 min | 13.7 h / 33.0 h |
| 30 % | anonymous seats, every honest seat counting | 33,473 / 22,519 | 7.0 h / 17.2 h / 20.7 h / 10.2 h | 5.7 h / 14.1 h | 4.1 h / 10.1 h | 8.7 d / 21.5 d |
| 30 % | anonymous seats, the inference's error up to 1.05 | 279,488 / 192,995 | 2.5 d / 6.3 d / 7.6 d / 3.8 d | 2.1 d / 5.2 d | 36.0 h / 3.7 d | 76.4 d / 190.0 d |
| 30 % | the chain's own leaders, counted, every honest leader online | 6,922 / 4,615 | 1.4 h / 3.5 h / 4.3 h / 2.1 h | 1.2 h / 2.9 h | 50.9 min / 2.1 h | 43.3 h / 4.4 d |
| 30 % | the chain's own leaders, counted, 95 % online | 78,979 / 51,724 | 16.5 h / 40.9 h / 2.0 d / 24.4 h | 13.5 h / 33.7 h | 9.7 h / 24.1 h | 20.6 d / 51.1 d |
| a third | anonymous seats, every honest seat counting | none | none | none | none | none |
| a third | anonymous seats, the inference's error up to 1.05 | none | none | none | none | none |
| a third | the chain's own leaders, counted, every honest leader online | none | none | none | none | none |
| a third | the chain's own leaders, counted, 95 % online | none | none | none | none | none |

These times hold under random delay, where the lag of 30 and the delivery were measured. Under a
delay an adversary chooses, it can split votes on a target that shallow, and a target deep enough
not to be split comes no sooner than the chain's own wait. So the gadget is set against the chain's
wait under random delay, with the worst case's waits beside it:

| coalition | the chain's own wait, random delay (h) | anonymous seats, every honest seat counting, on top of today's cover: no vote in a node's cover / Cardano's pools / equal stakes (h) | the chain's own leaders, counted, every honest leader online, the same three (h) | the same, 95 % of the honest leaders online (h) | with the cover raised, the fastest set: the chain's own leaders, every one online (h) | the chain's own wait, worst case at 10 s: without grinding / the new nonce of `slots.md` §4 after a deflation (h) |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | 0.45 | 0.33 / 0.27 / 0.20 | 0.05 / 0.05 / 0.04 | 0.07 / 0.06 / 0.05 | 1.25 | 0.81 / – |
| 25 % | 1.70 | 2.70 / 2.22 / 1.59 | 0.52 / 0.43 / 0.31 | 1.11 / 0.92 / 0.66 | 15.39 | 3.16 / – |
| 30 % | 3.09 | 17.17 / 14.14 / 10.11 | 3.55 / 2.92 / 2.09 | 40.90 / 33.67 / 24.06 | 106.11 | 5.93 / 6.43 |
| a third | 5.10 | – / – / – | – / – / – | – / – / – | – | 10.11 / 12.47 |

- **With today's quota ceiling kept, every set through Blend is slower than the chain** at 10 %,
  25 % and 30 %. The counted leaders, the fastest, take 1.25 hours against 10 %, where the chain
  waits 0.45.
- **On top of today's cover, anonymous seats gain against 10 %**, and against a quarter only with
  equal stakes, 1.59 hours where the chain waits 1.70. Against 30 % they take 10.11 to 17.17 hours.
- **The counted leaders gain against 10 % and a quarter**, also with 95 % of them online. Against
  30 % they gain only with every honest leader online and the stake spread at least as evenly as
  Cardano's pools: 2.92 hours, and 2.09 with equal stakes, where the chain waits 3.09. With 95 %
  online they take 24.06 to 40.90 hours.
- **These times assume the votes beyond each node's cover take transaction messages**, keeping the
  backlog's headroom. Using the headroom itself puts every core connection at its read limit, where
  a backlog never drains.
- **A single certificate at the set's quorum** comes about one round sooner, but it is the
  Peras-style design D1 sketched, whose guarantee is open. Under Peras's own quorum of three
  quarters, no committee exists from a quarter (§7).

---

## 5. Privacy

In the Blend report's model of linking, for a node with an adversarial peer, 59 % of nodes at the
specification's peering degree: a message is tied to its node when its whole blend path is
adversarial, 0.008 at 3 hops, and a proposal goes out twice. Votes take scheduled cover as won
slots do, so on top of today's cover the quota ceiling, the stake above which a node's emission
count identifies it, falls by the emission multiple. Mean days until an observer identifies a holder
whose stake lies in many small notes, and until it knows the stake to ±10 %:

| votes | votes a second, network-wide | a node's lottery emissions, times blocks alone | the quota ceiling on 20,000 nodes | a win tied to its leader's node | a 1 % holder: identified / sized to ±10 % | a 0.1 % holder: identified / sized to ±10 % | a 0.01 % holder: identified / sized to ±10 % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blocks only, through Blend | – | 1.00 | 0.1475 % | 0.016 | 2.2 d / 218 d | 22 d / 2,179 d | 218 d / 21,789 d |
| anonymous seats against 10 %, no vote in a node's cover, rounds of 8.3 min | 1.333 | 40.98 | 0.0036 % | 0.016 | 2.5 h / 10 d | 1.0 d / 103 d | 10 d / 1,034 d |
| anonymous seats against 10 %, equal stakes, rounds of 4.9 min | 2.262 | 68.86 | 0.0021 % | 0.016 | 1.5 h / 6.2 d | 14.9 h / 62 d | 6.2 d / 621 d |
| anonymous seats against 10 %, cover raised, rounds of 4.2 h | 0.044 | 2.33 | 0.1475 % | 0.016 | 1.3 d / 131 d | 13 d / 1,305 d | 131 d / 13,052 d |
| anonymous seats against 25 %, no vote in a node's cover, rounds of 1.1 h | 1.333 | 40.99 | 0.0036 % | 0.016 | 2.5 h / 10 d | 1.0 d / 103 d | 10 d / 1,034 d |
| anonymous seats against 25 %, equal stakes, rounds of 39.4 min | 2.266 | 68.99 | 0.0021 % | 0.016 | 1.5 h / 6.2 d | 14.9 h / 62 d | 6.2 d / 620 d |
| anonymous seats against 25 %, cover raised, rounds of 33.5 h | 0.044 | 2.33 | 0.1475 % | 0.016 | 1.3 d / 131 d | 13 d / 1,305 d | 131 d / 13,052 d |
| the chain's own leaders, no vote in a node's cover | 1.333 | 41.00 | 0.0036 % | 0.286 | 2.9 h / 12 d | 1.2 d / 121 d | 12 d / 1,213 d |
| the chain's own leaders, equal stakes | 2.267 | 69.00 | 0.0021 % | 0.430 | 1.9 h / 8.1 d | 19.4 h / 81 d | 8.1 d / 807 d |
| the chain's own leaders, cover raised | 0.044 | 2.33 | 0.1475 % | 0.026 | 1.3 d / 131 d | 13 d / 1,314 d | 131 d / 13,143 d |

- **On top of today's cover the quota ceiling falls 41 to 69-fold**, from 0.1475 % of the inferred
  stake on 20,000 nodes to 0.0036 % and 0.0021 %, below an equal share. A node above it is told
  apart by its emission count alone.
- **Through attribution, seats' votes make stake learnable 21 to 35 times as fast**, whatever the
  coalition the committee is sized for: a 0.1 % holder is sized in 103 or 62 days instead of 2,179.
- **With the cover raised, the ceiling holds**, but stake is still sized 1.7 times as fast as from
  blocks alone.
- **The chain's own leaders tie wins to nodes**: with chance 0.286 to 0.430 for a node with an
  adversarial peer, against 0.016 for a proposal alone, against the specification's own
  requirement. Stake is sized 18 to 27 times as fast, and the tied wins name the online leaders the
  committee needs.
- **Public sets show what they declare.** With every leading note declared that is the stake
  and node of each holder that stakes, the targeting C1 names, and targeting bears on liveness as well: the set holds
  30 % only while 95.24 % of the honest stake stays online. Delegated weight shows each operator's
  total, and the value each delegation moves.

---

## 6. Cost

Public signers vote once a round of 60 slots; bytes count each vote once. Ed25519 verification is
the Raspberry Pi 5's median with ed25519-dalek:

| public signers, rounds of 60 slots | votes a second | one Pi 5 core, verifying | received (KB/s) |
| --- | --- | --- | --- |
| 1,000 | 16.67 | 0.30 % | 2.5 |
| 20,000 | 333.33 | 6.03 % | 49.3 |
| 100,000 | 1,666.67 | 30.17 % | 246.7 |

Votes through Blend at each budget. The votes beyond each node's cover fill the headroom, and every
node verifies a message's header once for each of its three blending operations, against 156 a
second on one Pi 5 core:

| votes through Blend | votes a second, network-wide | Blend headers a node verifies a second, more / one Pi 5 core | a leader's signature, one Pi 5 core | a core connection carries, today / with the votes (KB/s) | transaction messages the votes take, the backlog's headroom kept | Blend keys a leader's votes need a win / today's leadership quota a win |
| --- | --- | --- | --- | --- | --- | --- |
| no vote in a node's cover | 1.333 | 4.0 / 2.56 % | 0.0241 % | 309 / 386 | 30.8 % | 120 / 6 |
| equal stakes | 2.267 | 4.0 / 2.56 % | 0.0410 % | 309 / 386 | 30.8 % | 204 / 6 |
| cover raised | 0.044 | 4.0 / 2.56 % | 0.0008 % | 309 / 386 | 30.8 % | 4 / 6 |

- **Every leading note declared is the costliest public set**: one signer a declaration, 30 % of a
  Pi 5 core at 100,000 declarations. A minimum stake low enough for every holder lets the coalition
  set that load by splitting into declarations, unless signatures aggregate. With the active stake
  at 30 % of the supply, today's minimum stake caps them at 30,000 declarations, 9.05 % of a Pi 5
  core (§9). Delegated weight signs
  with its operators only.
- **Votes through Blend cost Blend more than their own checks**: 2.56 % of a Pi 5 core in headers
  and 77 KB/s more on every core connection, or, with the backlog's headroom kept, 30.8 % of the
  transaction messages.
- **Votes need Blend keys.** A leader votes 40 to 68 times a win, 120 to 204 keys against today's
  quota of 6, so Blend's quota needs a rule for votes beyond a node's cover.
- **Proving.** Seats prove each seat they win. Leaders prove nothing new for the lottery, only their
  quota; making a leader's equivocation punishable would cost a proof a vote. Delegation proves once
  a note an epoch, with a circuit not designed.

---

## 7. Composition

| quorum | two conflicting certificates from | certificates stall above, uptime 1 / 0.95 / 0.9 |
| --- | --- | --- |
| two thirds, Casper FFG | 33.3 % | 33.3 % / 29.8 % / 25.9 % |
| three quarters, Ouroboros Peras | 50.0 % | 25.0 % / 21.1 % / 16.7 % |

- **Casper FFG's two thirds** finalize a block once the next round certifies a descendant. Two
  conflicting finalizations need a third of the weight to sign both ([`network.md`](network.md)
  §2).
- **Ouroboros Peras's three quarters** add weight to a certified block in the fork choice. Two
  conflicting certificates need half the weight, but certificates stall once a quarter withholds,
  and its strict quorum stalls at a quarter exactly: "Fast settlement occurs in the presence of
  adversaries with up to one-quarter of the stake, but Praos-like safety is maintained when
  adversaries control more than that amount of stake." A coalition of 30 % stops fast settlement by
  withholding its votes, whichever the signers.
- **Of the two quorums, only two thirds can hold 30 %**, while at least 95.24 % of the honest
  weight is online, on a set that holds it.
- **A boost settles a block and does not finalize it.** Finality still comes from the slot rule.
- **The slot rule stays under both.** Under FFG with the fast path, `B_imm` is the later of the
  latest finalized checkpoint and the slot rule's block. Under Peras's boost, `B_imm` stays the slot
  rule's block. A stall leaves finality at 18 hours under both.

---

## 8. What else changes, and the specification candidates

- **Every set that finalizes in minutes** moves `B_imm`, follows FFG's fork choice from the latest
  justified checkpoint, needs links across a registry change to carry two thirds of both
  registries, and keeps the uncle window in pruning ([`network.md`](network.md) §8).
- **The chain's own leaders** need a vote counted once a tag a round, a committee of the latest wins
  counted on the finalized chain, and a Blend quota for votes beyond a node's cover. With a sliding
  window every link crosses a registry change. Leaders keep their keys' secrets through the window
  and its lag behind finality, and no stake answers for a key leaked or sold, so certificates are
  trusted only within the window.
- **Every leading note declared** changes the proof of leadership, to prove membership in the
  declared notes, locks every note that leads, and leaves a holder below SDP's minimum stake unable
  to lead.
- **Delegated weight** needs a Mantle operation and a circuit for private delegation, the
  operators' totals tallied each epoch, and slashing for operators.

None is recommended within C1–C5. If the owner relaxes C1 and C3 for every holder that stakes,
every leading note declared needs:

- **SDP**: a declaration for every note that leads, with a vote key.
- **Cryptarchia**: the proof of leadership over declared notes only; the votes, rounds of `R` slots
  and a lag `L`; justification and finalization; FFG's fork choice from the latest justified
  checkpoint; `B_imm` by the chosen composition; links across a registry change, with two thirds of
  both registries; pruning that keeps the uncle window.
- **Mantle**: an operation that slashes a declared note given two votes that break a slashing
  condition.

---

## 9. The active stake at 30 % of the supply

The lottery weighs each note against the total active stake, which every node infers from the
chain's growth: "the probability that an eligible Cryptarchia participant wins the right to propose
a block depends on that participant’s stake relative to the total active stake". Every share in this
report is a share of the active stake, and certificates from Blend's declared nodes were already
read with the active stake at the block rewards' target of 30 % of the supply
([`network.md`](network.md) §4). Reading the active stake as at most 30 % of the supply moves no
figure above. It changes three readings.

**A coalition holds less of the supply:**

| coalition, share of the active stake | share of the supply, at most, with the active stake at 30 % of it |
| --- | --- |
| 10 % | 3.0 % |
| 25 % | 7.5 % |
| 30 % | 9.0 % |
| a third | 10.0 % |

**Stake from outside the active stake joins without notice.** A note joins the lottery by proving a
win, with no declaration, and the inference reads the new stake only at its next correction, up to
1.4 epochs or 10.5 days later. Until then the true active stake exceeds the inferred. Only the sets
whose quorum reads the inference are affected: the anonymous seats and the slot rule's lottery. The
chain's own leaders are counted, a public set's weight is declared, and delegated weight is tallied
each epoch.

The anonymous seats were sized for the inference's noise, a true stake up to 1.05 times the
inferred. A coalition whose stake joins from outside raises it to `1/(1 − α)`, the state a deflation
leaves without the assumption, and no committee exists from a coalition of 21.9 %. Honest stake
joining breaks them too:

| coalition | anonymous seats a round, sized for the inference's error up to 1.05 | the true over the inferred active stake once the coalition's stake enters | anonymous seats a round, sized for that | honest stake entering that breaks the seats sized for 1.05: share of the active stake / of the supply |
| --- | --- | --- | --- | --- |
| 10 % | 801 | 1.11 | 1,025 | 5.6 % / 1.7 % |
| 25 % | 9,728 | 1.33 | none | 6.3 % / 1.9 % |
| 30 % | 279,488 | 1.43 | none | 6.5 % / 2.0 % |
| a third | none | 1.50 | none | – |

A coalition's own stake joining is the deflated case the chain's wait in §4 already reads. A larger
rise makes blocks come faster until the inference corrects, and under the worst case faster blocks
need a longer wait. At 10 s, without grinding:

| the true over the inferred active stake | a block every | the wait against 30 % (h) | the wait against a third (h) |
| --- | --- | --- | --- |
| 1.00, the inference at the true stake | 30.0 s | 5.93 | 10.11 |
| 1.43, a coalition of 30 % entering | 21.2 s | 6.41 | 11.81 |
| 1.50, a coalition of a third entering | 20.2 s | 6.60 | 12.36 |
| 1.90 | 16.0 s | 8.46 | 17.52 |
| 2.00 | 15.3 s | 9.18 | 19.58 |
| 2.50 | 12.3 s | 15.32 | 40.07 |
| 3.00 | 10.3 s | 30.81 | 114.18 |

| coalition | the true over the inferred active stake up to which the wait stays within 18 hours | the least inferred active stake that keeps the true within it, the active stake at most 30 % of the supply |
| --- | --- | --- |
| 30 % | 2.627 | 11.5 % |
| a third | 1.925 | 15.6 % |

With the active stake at most 30 % of the supply, the slot rule's 18 hours hold a third whenever the
inferred active stake is at least 15.6 % of the supply, and a rise from 15 % to 30 % of the supply
within one inference period breaks them, at 19.58 hours. Against 30 % they hold from 11.5 %. The
new nonce adds less than 1 % where both are read.

**Every leading note declared costs only the holders that stake.** The declared stake is the active
stake, so a holder outside it leads and signs nothing, and no set shows its stake. At today's minimum
stake the active stake makes at most 30,000 declarations, however the coalition splits its stake:

| active stake, share of the supply | the minimum stake, share of the supply | declarations, at most | votes a second, rounds of 60 slots | one Pi 5 core, verifying | received (KB/s) |
| --- | --- | --- | --- | --- | --- |
| 30 % | 0.001 % | 30,000 | 500.00 | 9.05 % | 74.0 |

New stake joins only through a declaration on the ledger, so the quorum never lags the stake. What
the set holds is §3's.

---

## 10. Open questions

- Whether C1 and C3 may be relaxed for every holder that stakes. That is the owner's decision, and
  the only route here to finality in minutes that rests on the stake.
- How fast the active stake can grow within one inference period. Against a third the slot rule's
  18 hours hold while the true active stake stays within 1.925 times the inferred, against 30 %
  within 2.627 (§9).
- How far a coalition can keep honest wins out of a window's record, which the leaders' committee
  assumes it cannot.
- A Blend quota for votes beyond a node's cover, and how much of Blend's transaction share they may
  take.
- A delegation circuit, and what the delegated value reveals on a transparent ledger.
- The public sets' time at 100,000 signers, measured only at 1,000.
- Peras's paper: whether its proofs carry over to Poisson seats and to Blend's delays.
- Verifying a seat's proof on the Raspberry Pi 5.

---

## 11. Reproducing the figures

```
cd tools/simulators/finality
make install
make d0 d6 l1 l2 l4       # the committees, Blend's delivery, the declared set, public signers' time, the chain's waits
make m1 m2 m3 m4 m5       # what each set holds, how fast, privacy, cost, quorums
make m7                   # the active stake at 30 % of the supply
make tables check-tables
```

`make l4` needs `make a1` and `make k7`. The gates are `tests/test_signers.py` and
`tests/test_active.py`; every gate but the check that no counted committee holds a third fails under
a registered mutation
(`make mutations`). The study's report reads every route: [`README.md`](README.md).
