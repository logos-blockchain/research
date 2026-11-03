# Certificates from the network

*How much sooner a Cryptarchia block can be final if the nodes that SDP declares for the Blend
network certify it, and what finality then rests on. It reads Phase L of the study
(`tools/simulators/finality/NETWORK.md`) beside finality counted in slots, which the study
recommends at `K` = 18 hours ([`slots.md`](slots.md)). Every number comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality). Specifications are read at
`logos-lips` `bd1ca2c8`. One slot is one second and `f = 1/30`.*

---

## 1. Summary

Blend's core nodes declare themselves through SDP. Each declaration carries an Ed25519 key and is
backed by a service note that holds the minimum stake. These nodes can sign blocks. A certificate
is two thirds of them voting for one link between two checkpoints, under Casper FFG's rules. A block
is then final about two minutes after its slot, where the slot rule waits 18 hours. The time is
quickly settled. What the certificate rests on decides the route.

| | the slot rule at 18 hours | certificates of the declared nodes |
| --- | --- | --- |
| time until final | 18 hours | 120 s on average, 147 s at the 95th-percentile node, on the specification's Blend with rounds of 60 slots and a lag of 30 |
| safe while the coalition holds less than | a third of the active stake, with the new nonce, at 10 s | a third of the declared weight |
| at today's minimum stake, broken by | a third of the active stake | 500 declarations: 0.5 % of the supply, 1.67 % of the active stake |
| a partition | no floor separates a split against a third | one side at most certifies, while the coalition holds less than a third of the declared weight |
| cost | none | 6.0 % of one Raspberry Pi 5 core at 20,000 declared nodes, rounds of 60 slots, ed25519-dalek |

**What it gives.**

- **Finality in about two minutes.** With rounds of 60 slots and a lag of 30, 120 s on average and
  147 s at the 95th percentile on the specification's Blend (§3).
- **One side of a partition at most certifies** while the coalition holds less than a third of the
  declared weight. With certificates as the only finality every split then heals without an
  operator, where no floor separates a partition against a third, and an eclipse finalizes nothing
  while the coalition holds less than two thirds (§5).
- **Little cost.** Votes are public signatures gossiped directly, not Blend emissions. With rounds
  of 60 slots, verifying them takes 6.0 % of one Pi 5 core at 20,000 declared nodes with the node's
  Ed25519 library (§7).

**What it needs.**

- **A declared set the coalition holds less than a third of.** Under the study's convention, which
  gives the coalition its stake share of Blend's nodes, the set holds any coalition below a third at
  full uptime. Under the economics of SDP it does not: a coalition locks its stake in notes of the
  minimum stake, and at today's minimum 1.67 % of the active stake buys a third of a network of
  1,000. Holding 30 % needs honest declarations that lock more than 60 % of the active stake at
  full uptime, and a third cannot be held (§4).
- **Every honest declaration online.** At 95 % uptime the set holds at most 29.8 % of the declared
  weight, and against 30 % of the stake no honest declared stake suffices (§4).
- **A lag that outlasts Blend's delays.** 30 slots on the specification's Blend and 60 at the
  heaviest setting measured. At the shorter lags measured, a justified block later left the longest
  chain in some runs (§3).

**What it leaves.**

- **Safety on the declared set**, not on the stake, for any finality sooner than the chain's own
  settlement wait. In a variant that votes only on its own chain, the lag decides which assumption
  carries safety while every honest block reaches every honest node; against an eclipse or a split
  it is the declared set at any lag. With FFG's fork choice, two thirds of the declared weight
  finalize at any lag (§6).
- **A cheap stall.** A coalition holding more than a third of the declared weight, or a third
  while any honest declaration is offline, stalls certificates by withholding its votes; the chain
  continues (§4).
- **Slashing, keys and long range.** Accountable safety names the signers of a violation, but SDP
  cannot slash a service note, and a released note leaves its key free to sign old certificates (§8).

**Verdict: not recommended at today's minimum stake.** Certificates of Blend's declared nodes would
rest the chain's finality on a set of which 1.67 % of the active stake can hold a third and 6.67 %
two thirds, against a third of the stake for the slot rule. Holding a coalition of `α` at uptime
`u` needs honest declarations that lock more than `2α/(3u − 2)` of the active stake: more than 60 %
against 30 %, with every declaration always online (§4). Accountability needs a slashing operation
that does not exist (§8).

---

## 2. The certificate

**The declared set** (`bedrock-service-declaration-protocol.md`; Mantle). SDP keeps "a known and
agreed-upon list of participants" for the protocols that need one, the Blend network the only one
today. A declaration carries an Ed25519 provider key, network locators and a service note that holds
at least the minimum stake. Mantle's ledger is transparent, a note backs at most one declaration per
service, and a service note can still win the leader lottery. The registry a service reads in an
epoch is the one finalized two epochs before.

**The gadget**, Casper FFG on Cryptarchia's clock (`NETWORK.md` L.0):

- A checkpoint is a round and a block. A round starts every `R` slots.
- In round `r` each declared node votes a link from the latest justified checkpoint it holds to the
  latest block at least `L` slots old on its best chain among those that contain that checkpoint,
  or to the checkpoint's own block while no block above it is that old.
- A checkpoint is justified once the votes for one link to it carry two thirds of the declared
  weight, and finalized once the next round justifies a link from it.
- A node never votes twice in a round and never casts a link that surrounds one of its own, FFG's
  two slashing conditions. Two conflicting finalized checkpoints then need a third of the declared
  weight to have signed both: FFG's accountable safety, which rests on the votes alone.

**Three ways to compose it with the slot rule:**

- *Certificates only.* `B_imm` is the latest finalized checkpoint.
- *Fast path.* `B_imm` is the later of that checkpoint and the slot rule's block, so finality waits
  at most `K` when certificates stall, and needs both assumptions to hold.
- *Both required.* `B_imm` is the earlier of the two. Finality still takes `K`, but only a block the
  declared set certified becomes final.

---

## 3. How fast

On the engine: 1,000 nodes, each a declaration of weight one, with votes gossiped over the peering
graph without Blend; rounds of 30, 60 and 600 slots; lags of 0, 10, 30 and 60 slots; the
coalition's votes withheld at up to 30 % (`NETWORK.md` L.2). The table gives each Blend at the least
lag at which no justified checkpoint left the longest chain.

| Blend | lag (slots) | rounds of 30 slots: mean / 95th percentile / longest (s) | rounds of 60 slots | rounds of 600 slots |
| --- | --- | --- | --- | --- |
| testnet | 0 | 47 / 60 / 61 | 92 / 119 / 121 | 906 / 1176 / 1201 |
| specification | 30 | 75 / 88 / 89 | 120 / 147 / 149 | 931 / 1201 / 1229 |
| heavy | 60 | 105 / 118 / 119 | 150 / 177 / 179 | 958 / 1231 / 1259 |

- **The rounds set the time.** A block waits for the first round whose target holds it, then one
  more round: `L + (R − 1)/2 + R` on average. The votes add under a second.
- **The lag must outlast Blend's delays.** At shorter lags a justified checkpoint can be a block the
  longest chain later leaves: on the specification's Blend a lag of 10 slots did so in 5 of 36 runs,
  and at the heavy point a lag of 30 in 18. FFG's fork choice then keeps nodes on that block, so the
  certificates steer the chain. At the lags in the table the two rules never disagreed.
- **Every round justified** in the runs read, with the coalition's votes withheld up to 30 %.

---

## 4. What the declared set holds

**The conditions** (`NETWORK.md` L.1). The coalition holds a share `a` of the declared weight and
signs on every side; a share `u` of the honest declarations is online.

- Safety: two conflicting links both reach two thirds for some split of the honest votes exactly
  when `a` reaches a third.
- Liveness: the honest declarations online carry two thirds on their own while `u(1 − a) ≥ 2/3`.
  At 95 % uptime the set holds at most 29.8 % of the declared weight, at 90 % 25.9 %.

**Two readings of `a`.** The study's convention gives the coalition its stake share of Blend's
nodes, as its runs of hostile relays do (`FURTHER.md` G6); the set then holds every coalition below a
third at full uptime. The economics of SDP do not give it that share. A coalition can lock all its
stake in service notes, which still lead, one declaration a note. Honest operators lock what they
choose. With one weight per declaration the coalition splits its stake into notes of the minimum
stake; with weight by a note's value each side weighs what it locks. Either way the coalition holds
`a = αD/(αD + L_h)` for honest declarations locking `L_h` of the active stake `D`.

**At the minimum-stake analysis' parameters**, 1,000 honest declarations and the active stake at 30 %
of the supply:

| minimum stake | honest declared stake | coalitions held, below: uptime 1 | uptime 0.95 | a third of the declarations takes |
| --- | --- | --- | --- | --- |
| 0.001 % of the supply, 1,000 LGO, today's | 3.3 % of the active stake | 1.67 % | 1.42 % | 500 declarations, 0.5 % of the supply |
| 0.015 % of the supply, 15,000 LGO, the analysis' cap | 50.0 % of the active stake | 25.00 % | 21.25 % | 500 declarations, 7.5 % of the supply |

**What holding each coalition takes**, the honest declared stake as a share of the active stake,
every value one to exceed:

| coalition | uptime 1 | uptime 0.95 | uptime 0.9 | of the honest stake, uptime 1 | honest declarations at today's minimum, uptime 1 | minimum stake for 1,000 honest declarations, uptime 1 |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | 20 % | 24 % | 29 % | 22 % | 6,000 | 6 times today's |
| 25 % | 50 % | 59 % | 71 % | 67 % | 15,000 | 15 times today's |
| 30 % | 60 % | none | none | 86 % | 18,000 | 18 times today's |
| a third | none | none | none | none | none | none |

- **The minimum stake prices a declaration, not a share.** The honest declared stake must exceed
  twice the coalition's at full uptime, whatever the minimum. The minimum only sets how many
  declarations that takes.
- **With weight by value this is D1b's opt-in public committee**, the alternative to anonymous
  seats (`CERTIFIED.md` D1b), with Blend's operators as the volunteers. It ties the locked stake to a
  public key and network locators on a transparent ledger, the link Blend exists to hide.
- **More than a third of the declared weight, or a third while any honest declaration is offline,
  stalls finality** by withholding its votes, under certificates only and under both required.
- **A violation costs** the third of the declared weight that signed both sides, if their notes
  could be slashed: at least half the honest declared stake, 0.5 % of the supply at today's
  minimum.

---

## 5. Partitions and eclipses

The coalition signs on both sides of a partition. A side certifies once its honest declarations
online and the coalition reach two thirds, so both sides can only once the coalition holds a third.
A side needs 56 % of the honest declared weight against a coalition of 25 % and 52 % against 30 %,
at full uptime. On the engine, a two-hour partition on the specification's Blend, four runs a cell
(`NETWORK.md` L.3):

| honest declarations, side / rest | coalition's share of the declared weight | side: rounds justified | rest: rounds justified | runs that finalize both sides |
| --- | --- | --- | --- | --- |
| 30 % / 70 % | 0.30 | 0 of 120 | 118–119 of 120 | 0 of 4 |
| 50 % / 50 % | 0.30 | 0 of 120 | 0 of 120 | 0 of 4 |
| 50 % / 50 % | 0.34 | 116–119 of 120 | 118–119 of 120 | 4 of 4 |
| 60 % / 40 % | 0.30 | 117–119 of 120 | 0 of 120 | 0 of 4 |

- **Below a third of the declared weight one side at most certifies**, in every run and at every
  split, as the closed form says.
- **Certificates only.** The side that stalls finalizes nothing and keeps building blocks. When the
  split ends it follows the other side's justified checkpoints, so every split heals without an
  operator. An eclipsed node receives too few votes to certify anything while the coalition holds
  less than two thirds of the declared weight, so no floor is needed below that. From two thirds,
  6.67 % of the active stake at today's minimum, the coalition certifies the eclipsed node's fork
  alone.
- **Fast path.** The side that stalls still finalizes its own chain by the slot rule, as today.
- **Both required.** No side finalizes past the split without a certificate, and the certifying
  side still waits `K`.
- **Against the floor.** At 18 hours the floor holds back a side of at most 0.385 of the stake and
  separates no partition against a third (`slots.md` §6). Certificates separate every split, but
  only while the declared set holds.

---

## 6. The lag as a hedge

FFG's accountable safety rests on the votes alone. Below a third of the declared weight the gadget
is safe at any lag. Above it the lag and the fork choice decide (`NETWORK.md` L.4).

- **With FFG's fork choice** nodes follow the justified checkpoint of greatest height. A coalition
  with two thirds of the declared weight finalizes a chain of its own at any lag; between a third and
  two thirds it must split the honest views at the lag.
- **In a variant** a node votes for and accepts a checkpoint only once it lies on its own chain at
  least `L` slots deep, and never reverts a finalized one. Two honest nodes then finalize conflicting checkpoints only if their chains
  disagree on a prefix at least `L` slots old: the chain's own settlement failure, priced against
  the coalition's stake, whatever it declares, while every honest block reaches every honest node.
  An eclipse or a split leaves that model: two thirds of the declared weight certify an eclipsed
  node's fork alone, and a third finalizes both sides of an even split. Against those the variant
  needs a floor over its lag. Its liveness is not derived.

The lag at which the chain's settlement holds `1e-9` against the coalition's stake:

| coalition's stake | random delay, specification's Blend (h) | worst case at 10 s (h) | worst case at 10 s, the new nonce of `slots.md` §4, after a deflation (h) |
| --- | --- | --- | --- |
| a third of today's declarations, 1.67 % | 0.20 | 0.40 | – |
| two thirds of today's declarations, 6.67 % | 0.34 | 0.62 | – |
| 30 % | 3.09 | 5.93 | 6.43 |
| a third | 5.10 | 10.11 | 12.47 |

- **In the variant the lag sets which assumption carries safety**, against a coalition that delays
  but does not eclipse or split. Below the chain's own wait it is the declared set; at that wait,
  either. Against a third under the worst case at 10 s, with the new
  nonce after a deflation, the variant then finalizes at about 12.5 hours, where `K` is 18. With
  FFG's fork choice no lag helps against two thirds of the declared weight. Finality in minutes rests
  on the declared set.

---

## 7. Cost

Every declared node votes once a round, so a node verifies `n/R` votes a second. Pi 5 figures are
the repository's reference-grade medians on one core (`reports/pqc`): Ed25519 in 181 µs with
ed25519-dalek, the node's library family, and ML-DSA-44 in 68 µs with aws-lc-rs at 2,420 bytes a
signature (`NETWORK.md` L.5). With rounds of 60 slots:

| declared nodes | votes a second | one Pi 5 core, Ed25519 | received, Ed25519 (KB/s) | received, ML-DSA-44 (KB/s) | certificate, Ed25519 (KB) | certificate, ML-DSA-44 (MB) |
| --- | --- | --- | --- | --- | --- | --- |
| 1,000 | 16.7 | 0.30 % | 2.5 | 42 | 45.4 | 1.62 |
| 20,000 | 333.3 | 6.03 % | 49.3 | 835 | 906.8 | 32.32 |

- Votes cost Blend nothing: they are public and travel by direct gossip. The bytes count each vote
  once; a gossip mesh delivers up to one copy a neighbour.
- ML-DSA-44 multiplies a certificate by 36. An aggregate signature would shrink it
  to one signature and a bitmap, but needs a key the declarations do not carry; it is not measured.

---

## 8. What else changes

- **`B_imm` and the node's LIB**, under certificates only and the fast path, follow the latest
  finalized checkpoint, at most `L + 2R` slots behind the tip while rounds justify, and the largest
  rollback shrinks with them.
- **Pruning must keep the uncle window.** The window, 360 slots, is longer than `L + 2R` at a lag of
  30 and rounds of 60, so pruning at `B_imm` would discard uncle candidates the stake inference still
  counts.
- **A node that returns** checks the certificates it missed against the registry, but only while
  the keys that signed them can still be slashed. A withdrawn declaration's note is released one
  epoch after its node stops signing, so a node away longer needs a checkpoint or the Bootstrap
  rule, as FFG's clients must "log on" within its four-month withdrawal delay.
- **A link across a registry change** needs two thirds of both registries, as FFG's dynasties do.
- **The epoch keeps its length**, and its phases, SDP's lag and the stake inference read finality
  through it. The wallet and the zone SDK read the LIB, so under certificates only and the fast path
  they wait minutes.
- **Keys.** The provider key also authenticates the node's connections. A vote key of its own in
  the declaration keeps that key out of slashing and allows an aggregate scheme.
- **Accountability** needs a Mantle operation that slashes a service note on two votes that break a
  slashing condition, landed while the note is locked.
- **Privacy.** With one weight per declaration a vote reveals nothing new: the declaration is public
  already, a vote carries no lottery win, and from a lag of 30 slots every node votes the same block.

---

## 9. Specification candidates, if adopted

None is recommended at today's minimum stake. If the declared set were to carry finality:

- **SDP**: a vote key in the declaration, and a minimum stake and participation at which the honest
  declared stake exceeds `2α/(3u − 2)` of the active stake for the coalition the protocol must hold.
- **Mantle**: an operation that slashes a service note given two votes that break a slashing
  condition, within the note's lock.
- **Cryptarchia**: the votes, rounds of `R` slots and a lag `L`; justification and finalization;
  the fork choice from the latest justified checkpoint; `B_imm` by the chosen composition; pruning
  that keeps the uncle window; links across a registry change.

---

## 10. Open questions

- Which reading governs the declared set: the coalition's stake share, or the economics of the
  minimum stake? How much honest stake would lock into declarations?
- The variant of §6: its liveness after a reorganization past a node's source, and a floor over its
  lag against eclipses and splits.
- Slashing service notes: the operation, the evidence and the window before a note is released.
- An aggregate signature for certificates, and whether it must be post-quantum.

---

## 11. Reproducing the figures

```
cd tools/simulators/finality
make install
make l1 l2 l3 l4 l5      # the declared set, the engine's gadget, partitions, the hedge, cost
make tables check-tables
```

`make l4` needs `make a1` and `make k7`. The gates are `tests/test_netcert.py` and
`tests/test_gadget.py`, each with registered mutations (`make mutations`). The study's report
reads every route: [`README.md`](README.md).
