# Certificates from the network

Phase L of `PLAN.md`, on the branch `fast-finalization-slots`. The owner's direction (Q12): the
nodes SDP registers for the Blend network sign blocks under their public keys, and two thirds of
them form a certificate. Tables come from `scripts/l1_declared.py`, `scripts/l2_gadget.py`,
`scripts/l3_partition.py`, `scripts/l4_hedge.py` and `scripts/l5_cost.py` through
`scripts/tables.py`. Specifications are read at `logos-lips` `bd1ca2c8` (`origin/master`,
2026-11-02).

## L.0 — the reading

**What the sources say**, with their formulas written as text.

| source | the text |
| --- | --- |
| `bedrock-service-declaration-protocol.md`, Introduction | "This document defines a mechanism enabling validators to declare their participation in specific protocols that require a known and agreed-upon list of participants. One example of this is the Blend Network." "Before being admitted to the repository, the validator proves that it locked at least a minimum stake through a service note." |
| the same, Identifiers | "`provider_id`: used to sign the SDP messages and to establish secure links between validators; it is `Ed25519PublicKey`." |
| the same, Overview and Withdraw message | services read the registry at "`finalized_epoch = current_epoch - 2`"; after a withdrawal included in epoch `e`, at `e+2` "Every service excludes the declaration", at `e+3` "the declaration is removed in the first block", and "Its declaration is removed and its service note released once that epoch has been rewarded." |
| `bedrock-v1.1-mantle-specification.md` | "The Mantle Ledger enables asset transfers using a transparent UTXO model." Service notes: "A note backs at most one declaration per service", and "Though locked, these notes remain in the Ledger and can still participate in Proof of Stake." |
| `analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md` | the minimum stake "Stake_LGO = 0.001% · S_TGE", below a cap of 0.015 % that lets 1,000 nodes hold 15 % of the supply; "A network size that is considered small has 1000 nodes." |
| `block-rewards.md` | "Inferred Total Stake: Measures network security by tracking the total amount staked against a target threshold (e.g., 30% of the maximum supply)." |
| `blend-protocol.md` | "The minimal network size is 32." A node's activity proof "confirms that the node was processing messages during the epoch". "The cost of attacking the network is high due to decentralization and the economic value of stake needed to add a single node." |

Casper FFG, Buterin and Griffith, arXiv 1710.09437v4 (2019-01-22; the PDF served on 2026-11-03,
SHA-1 `bd287d9f`), is the template. It overlays a chain with votes of a known validator set:

- §2.1: "Accountable safety means that two conflicting checkpoints cannot both be finalized unless
  ≥ 1/3 of validators violate a slashing condition (meaning at least one third of the total deposit
  is lost). Plausible liveness means that, regardless of any previous events (e.g., slashing events,
  delayed blocks, censorship attacks, etc.), if ≥ 2/3 of validators follow the protocol, then it's
  always possible to finalize a new checkpoint without any validator violating a slashing
  condition." The PDF sets the fractions as stacked numerals.
- Figure 2, the two slashing conditions: a validator "must not publish two distinct votes for the
  same target height", and "must not vote within the span of its other votes".
- §2.2, the fork choice: "follow the chain containing the justified checkpoint of the greatest
  height". Theorem 1's proof uses only the votes, so safety does not depend on it. Liveness does.
- §3: a validator joins and leaves two dynasties after its message, and "At the start of the end
  dynasty, the validator's deposit is locked for a long period of time, called the withdrawal
  delay (approximately "four months worth of blocks")".
- §4.1: "Once a coalition of validators has withdrawn their deposits, if that coalition had more
  than 2/3 of deposits long ago in the past, they can use their historical supermajority to
  finalize conflicting checkpoints without fear of getting slashed". It is met by "a fork choice
  rule to never revert a finalized block, as well as an expectation that each client will "log on"
  and gain a complete up-to-date view of the chain at some regular frequency".

**The gadget.** Casper FFG on Cryptarchia's clock, with the declarations of the registry each
epoch reads as the validators (`src/finality_sim/gadget.py`).

- A checkpoint is a pair of a round and a block. A round starts every `R` slots.
- In round `r` each declared node votes a link from the latest justified checkpoint it holds to its
  checkpoint of round `r`: the latest block at least `L` slots old on its best chain among the
  chains that contain that justified checkpoint, or that checkpoint's own block while no block
  above it is that old.
- A checkpoint is justified once the votes for one link to it carry `q` of the declared weight. It
  is finalized once the next round justifies a link from it.
- A node signs under FFG's two slashing conditions.

Two conflicting finalized checkpoints then need `2q − 1` of the declared weight to have signed
both, a third at `q = 2/3`.

**Three compositions with the slot rule** (`SLOTS.md`):

- *Certificates only.* `B_imm` is the latest finalized checkpoint. The slot rule moves it no more.
- *Fast path.* `B_imm` is the later of the latest finalized checkpoint and the slot rule's block.
- *Both required.* `B_imm` is the earlier of the two. Finality takes `K` as today; a certificate
  only holds back a block the declared set has not certified.

**Taken without the owner's answer.** One weight per declaration, as Blend counts its nodes; weight
by a service note's value read beside it. `q = 2/3`. The compositions measured side by side.

## L.1 — what the declared set holds

A certificate needs links carrying `q` of the declared weight. The coalition holds a share `a` of it
and signs on every side. The honest declarations vote one link each, and a share `u` of them is
online (`src/finality_sim/netcert.py`).

- **Safety.** Two conflicting links need `h_1 + a ≥ q` and `h_2 + a ≥ q` with `h_1 + h_2 ≤ 1 − a`.
  Some split of the honest votes meets both exactly when `a ≥ 2q − 1`, a third.
- **Liveness.** The honest declarations online carry `q` on their own once `u(1 − a) ≥ q`.

**The study's convention** gives the coalition its stake share of Blend's nodes, `a = α`, as G6
runs its relays (`FURTHER.md` G6). The declared set then holds every coalition below a third at
full uptime, and less as the honest declarations go offline:

| uptime of the honest declarations | largest coalition share of the declared weight |
| --- | --- |
| 1 | below a third |
| 0.95 | 29.8 % |
| 0.9 | 25.9 % |

**The economics.** The coalition can lock all its stake in service notes, since they still lead,
and a note backs one declaration a service. With one weight per declaration it splits its stake
into notes of the minimum stake `m`, and honest declarations lock `m` each. With weight by value
each side weighs what it locks, however it splits its notes. Either way the coalition's share is
`a = αD/(αD + L_h)`, up to whole declarations, for honest declarations locking `L_h` of the active
stake `D`. With weight by value and the honest declarations a share `v` of the honest stake,
`L_h = v(1 − α)D`, which is D1b's opt-in committee (`CERTIFIED.md` D1b).

At the minimum-stake analysis' parameters, 1,000 honest declarations, and the active stake at the
block rewards' target of 30 % of the supply:

| minimum stake | honest declared stake | coalitions held, below: uptime 1 | uptime 0.95 | uptime 0.9 | a third of the declarations takes |
| --- | --- | --- | --- | --- | --- |
| the minimum, 0.001 % of the supply (1,000 LGO) | 3.3 % of the active stake | 1.67 % | 1.42 % | 1.17 % | 500 declarations, 0.5 % of the supply, 1.67 % of the active stake |
| the cap, 0.015 % of the supply (15,000 LGO) | 50.0 % of the active stake | 25.00 % | 21.25 % | 17.50 % | 500 declarations, 7.5 % of the supply, 25.00 % of the active stake |

What holding each coalition takes, every value one to exceed: the honest declared stake as a share
of the active stake at three uptimes; at full uptime, as a share of the honest stake, in
declarations of today's minimum stake, and as the minimum stake 1,000 honest declarations would
need:

| coalition | honest declared stake, more than: uptime 1 | uptime 0.95 | uptime 0.9 | of the honest stake, uptime 1 | honest declarations at the minimum stake | minimum stake for 1,000 honest declarations |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | 20 % | 24 % | 29 % | 22 % | 6,000 | 6 times today's |
| 20 % | 40 % | 47 % | 57 % | 50 % | 12,000 | 12 times today's |
| 25 % | 50 % | 59 % | 71 % | 67 % | 15,000 | 15 times today's |
| 30 % | 60 % | none | none | 86 % | 18,000 | 18 times today's |
| a third | none | none | none | none | none | none |

- **The minimum stake prices a declaration, not a share.** At full uptime the honest declared
  stake must exceed twice the coalition's stake, `2α/(3u − 2)` of the active stake in general. The
  minimum stake only sets how many declarations that takes.
- **At today's minimum, 500 declarations hold a third** of a network of 1,000: 0.5 % of the supply,
  a coalition of 1.67 % of the active stake, where the chain at `K` = 18 hours holds a third.
- **At the analysis' cap**, 15,000 LGO a declaration, 1,000 honest declarations hold a quarter at
  full uptime, and lock half of the active stake.
- **Against 30 %** the honest declarations must lock 60 % of the active stake, 86 % of the honest
  stake, and stay online without a gap: 18,000 declarations at today's minimum. At 95 % uptime no
  share suffices. **A third cannot be held at all.**
- **What a violation costs.** Accountable safety names the third of the declared weight that
  signed both sides. Slashing their service notes, which SDP does not do today, would burn at
  least half the honest declared stake: 0.5 % of the supply at today's minimum.

Gates (`tests/test_netcert.py`): the coalition's most declarations equal an enumeration of every
split of its stake into notes; with weight by value the honest declared stake equals D1b's
frontier; two sides both certify, searched over every split, exactly from `2q − 1`; liveness
against 30 % needs 95.24 % uptime; the analysis' 1,000 and 15,000 LGO and the shares held at them
reproduce. Each with a mutation that fails it.

## L.2 — time to finality on the engine

D6's configuration (A1: 1,000 nodes, Pareto stake, 0.1 s links, one epoch at `k = 256`) at the three
Blends of Q3, four replicates. Every node is a declaration of weight one, and votes travel by direct
gossip over the engine's peering graph, not through Blend. Rounds of 30, 60 and 600 slots; lags of
0, 10, 30 and 60 slots; the coalition's declarations, a random share of the nodes, withheld at 0,
25 % and 30 %, so the honest votes alone must carry two thirds of all declarations
(`scripts/l2_gadget.py`).

The engine builds its chains by the longest-chain rule. A justified checkpoint that later falls off
that chain is one FFG's fork choice would have kept the nodes on, and from that round the run no
longer models the gadget. The runs in which that happened, of 36 at each lag (three round lengths,
three coalitions, four replicates):

| Blend | lag 0 | lag 10 | lag 30 | lag 60 |
| --- | --- | --- | --- | --- |
| testnet | 0 of 36 | 0 of 36 | 0 of 36 | 0 of 36 |
| specification | 21 of 36 | 5 of 36 | 0 of 36 | 0 of 36 |
| heavy | 33 of 36 | 33 of 36 | 18 of 36 | 0 of 36 |

At the least lag with no such run, the time from a block's slot until it is final: the mean of the
median node's time, the 95th percentile over blocks of the 95th-percentile node's time, and the
longest; the share of rounds justified, at its least; and when two thirds of the votes, cast at
once, reach the median and the 95th-percentile node:

| Blend | lag (slots) | rounds of 30 slots: mean / 95th percentile / longest (s) | rounds of 60 slots: mean / 95th percentile / longest (s) | rounds of 600 slots: mean / 95th percentile / longest (s) | rounds justified | two thirds of the votes at the median / 95th-percentile node (s) |
| --- | --- | --- | --- | --- | --- | --- |
| testnet | 0 | 47 / 60 / 61 | 92 / 119 / 121 | 906 / 1176 / 1201 | 1.000 | 0.31 / 0.38 |
| specification | 30 | 75 / 88 / 89 | 120 / 147 / 149 | 931 / 1201 / 1229 | 1.000 | 0.30 / 0.37 |
| heavy | 60 | 105 / 118 / 119 | 150 / 177 / 179 | 958 / 1231 / 1259 | 1.000 | 0.31 / 0.39 |

- **About two minutes with rounds of 60 slots**: 147 s at the 95th percentile on the
  specification's Blend at a lag of 30, 177 s at the heavy point at a lag of 60, and 119 s on
  testnet's at a lag of 0. Rounds of 30 slots give 60 to 118 s, rounds of 600 about 20 minutes.
- **The rounds set the time, not the network.** A block waits for the first round whose target holds
  it, then for one more round: `L + (R − 1)/2 + R` on average for blocks in random slots. Two thirds
  of the votes reach the median node within 0.31 s and the 95th-percentile node within 0.39 s.
- **The lag must outlast Blend's delays.** On the specification's Blend a lag of 10 slots let a
  justified checkpoint leave the longest chain in 5 of 36 runs, and at the heavy point a lag of 30 in
  18. Nodes that follow FFG's fork choice would then build on a branch the longest-chain rule had
  left: the certificates would steer the chain. From the lags in the table on, the two rules never
  disagreed.
- **Withholding the coalition's votes changes nothing while views agree.** With every honest node on
  one target, 70 % of the declarations carry two thirds in every round, and the times move by under
  0.1 s.

Gates (`tests/test_gadget.py`): on a chain every node agrees on, a block is final at the start of
the round after the first whose target holds it, `L + (R − 1)/2 + R` on average; votes from two
sources are two links and justify nothing; a link that skips a round finalizes nothing; a node
votes on the best chain that holds its justified checkpoint, that block is a brute force's on
random trees, and a target never falls below its source; a justified checkpoint off the longest
chain is a departure from its first round; two sides finalize only from a third of the declared
weight, and a one-sided split conflicts nothing; a cut holds votes until it lifts, and a checkpoint
two links finalize is final at the earlier. Each with a mutation that fails it.

## L.3 — partitions and eclipses

The coalition signs on both sides of a partition. A side whose honest declarations hold `h` of the
declared weight certifies once `u·h + a ≥ q`, so both sides certify only when `a ≥ 2q − 1`, a third.
A side needs `(q − a)/(u(1 − a))` of the honest declared weight: two thirds without a coalition,
56 % against 25 % and 52 % against 30 % at full uptime, 58 % and 55 % at 95 %.

On the engine: B3's configuration on the specification's Blend, 1,000 nodes of equal stake, each an
honest declaration; from slot 3,000 the engine's partition mode (I.3) cuts the honest nodes into a
side and the rest for two hours, and a block or a vote crosses the cut only at its end. The
coalition holds further declarations and signs every link either side casts. Rounds of 60 slots, a
lag of 30, four runs a cell:

| honest declarations, side / rest | coalition's share of the declared weight | side: rounds justified on the engine; the closed form | rest: rounds justified; the closed form | runs that finalize both sides |
| --- | --- | --- | --- | --- |
| 30 % / 70 % | 0.25 | 0 of 120; stalls | 118–119 of 120; certifies | 0 of 4 |
| 30 % / 70 % | 0.30 | 0 of 120; stalls | 118–119 of 120; certifies | 0 of 4 |
| 30 % / 70 % | 0.34 | 0 of 120; stalls | 118–119 of 120; certifies | 0 of 4 |
| 50 % / 50 % | 0.25 | 0 of 120; stalls | 0 of 120; stalls | 0 of 4 |
| 50 % / 50 % | 0.30 | 0 of 120; stalls | 0 of 120; stalls | 0 of 4 |
| 50 % / 50 % | 0.34 | 116–119 of 120; certifies | 118–119 of 120; certifies | 4 of 4 |
| 60 % / 40 % | 0.25 | 117–119 of 120; certifies | 0 of 120; stalls | 0 of 4 |
| 60 % / 40 % | 0.30 | 117–119 of 120; certifies | 0 of 120; stalls | 0 of 4 |
| 60 % / 40 % | 0.34 | 117–119 of 120; certifies | 0 of 120; stalls | 0 of 4 |

- **Below a third of the declared weight one side at most certifies**, at every split and in every
  run. At 0.34 an even split certifies both sides and finalizes both in every run. The engine agrees
  with the closed form in every cell.
- **Certificates only.** The side that stalls finalizes nothing while the split lasts, and keeps
  building blocks (C2). When the split ends its nodes see the other side's justified checkpoints,
  of greater height, and follow them, so every split heals without an operator. An eclipsed node
  receives only the coalition's votes, short of the quorum while the coalition holds less than two
  thirds of the declared weight, so it finalizes nothing and needs no floor. From two thirds, 6.67 %
  of the active stake at today's minimum (L.4), the coalition certifies the eclipsed node's fork
  alone.
- **Fast path.** The side that stalls still finalizes its own chain by the slot rule once a block is
  `K` slots old and the floor is met, so a split the floor does not hold back ends with two
  finalized histories, as without certificates (`SLOTS.md` K.3, K.9).
- **Both required.** A side finalizes only what it certifies, so the stalled side finalizes nothing
  past the split while the certifying side still waits `K`. Every split heals without an operator.
- **Against the floor.** At 18 hours the floor holds back a side of at most 0.385 of the stake, and
  no floor separates a partition against a third (`SLOTS.md` K.3, K.9). H.1's one-off round of
  anonymous seats separates a quarter with 2,271 seats, 30 % with 14,966 and a third with none
  (`DESIGNS.md` H.1). Certificates separate every split while the coalition holds less than a third
  of the declared weight, and none once it holds a third and the honest declarations split evenly.

## L.4 — the lag as a hedge

FFG's Theorem 1 rests on the votes alone, so below a third of the declared weight the gadget is safe
whatever the fork choice and the lag. They decide what a coalition above a third can do.

- **With FFG's fork choice** honest nodes follow the justified checkpoint of greatest height,
  wherever it lies. A coalition holding two thirds of the declared weight justifies and finalizes
  checkpoints on a chain of its own, and every node that has not yet finalized the honest one
  follows it, at any lag. Between a third and two thirds it needs honest votes on both sides, so a
  split of the honest views at the lag.
- **A variant** votes for, and accepts, a checkpoint only once its block lies on the node's own
  chain at least `L` slots deep, and never reverts a finalized one. Two honest nodes that finalize
  conflicting checkpoints then hold, at least `L` slots after some slot, chains that disagree on the
  prefix up to it. That is the settlement failure K.1 and K.7 bound per target, against the
  coalition's stake, whatever share of the declared weight it holds. So the variant is safe below a
  third of the declared weight whatever the chain does, and at the chain's `ε(L)` whatever the
  coalition declares, within K.1 and K.7's models, in which every honest block reaches every honest
  node, within `Δ` under the worst case. Eclipses and splits leave those models. A coalition with
  two thirds of the declared weight eclipses a node, shows it a fork of its own, and certifies the
  fork alone once it lies `L` deep. One with a third finalizes both sides of an even split that
  outlasts `L + 2R`, as L.3's row at 0.34 does without the variant. Against both the variant needs
  K.3's floor over its lag, as the slot rule has it. Its liveness rests on the chain: a node cannot vote a link from a checkpoint
  older than the source of a link it voted before, so a reorganization past its source stalls its
  votes, and finality with them once it moves a third of the declared weight. L.2's departures
  count such reorganizations at each lag.

The lag that holds `1e-9`, the chain's settlement wait against the coalition's stake (`SLOTS.md`
K.1, K.7, recomputed at the two shares of today's declarations):

| coalition's stake | random delay, specification's Blend (h) | worst case at 10 s (h) | worst case, nonce of §3.1 after a deflation (h) |
| --- | --- | --- | --- |
| a third of today's declarations, 1.67 % | 0.20 | 0.40 | – |
| two thirds of today's declarations, 6.67 % | 0.34 | 0.62 | – |
| 10 % | 0.45 | 0.81 | – |
| 25 % | 1.70 | 3.16 | – |
| 30 % | 3.09 | 5.93 | 6.43 |
| a third | 5.10 | 10.11 | 12.47 |

- **With FFG's fork choice, at today's minimum stake**, a coalition of 1.67 % of the active stake
  holds a third of the declarations and then needs only a split of the honest views at the lag; one
  of 6.67 % holds two thirds and finalizes what it chooses at any lag. Against the study's adversary, from 30 % to a
  third, no lag helps.
- **The variant holds a coalition at the lag of its row**, whatever the coalition declares, while
  every honest block reaches every honest node: 37 minutes against 6.67 % under the worst case at
  10 s without grinding, and 6.4 hours against 30 % and 12.5 against a third with the nonce of §3.1
  after a deflation.
- **In the variant the lag sets which assumption carries safety** against a coalition that delays
  but does not eclipse or split. Below the chain's wait it is the declared set; at the wait, either.
  Against an eclipse or a split it is the declared set at any lag, unless a floor is added. With
  FFG's fork choice no lag helps against two thirds of the declared weight. Finality sooner than the
  chain's own wait rests on the declared set.

## L.5 — cost

A declared node verifies every vote once a round, `n/R` votes a second. The Pi 5 figures are the
medians of the repository's reference-grade run on one core (`reports/pqc`,
`rasberrypi5-20260811T211615Z.json`): Ed25519 verifies in 181 µs with ed25519-dalek, the library
family the node uses, and in 114 µs with aws-lc-rs; ML-DSA-44 in 68 µs with aws-lc-rs, at 2,420
bytes a signature. A vote carries the link's two checkpoints, the signer's index and a signature,
148 bytes with Ed25519. With rounds of 60 slots:

| declared nodes | votes a second | Ed25519, ed25519-dalek: one core | Ed25519, aws-lc-rs | ML-DSA-44, aws-lc-rs | received, Ed25519 (KB/s) | received, ML-DSA-44 (KB/s) | certificate, Ed25519 (KB) | certificate, ML-DSA-44 (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | 0.5 | 0.01 % | 0.01 % | 0.00 % | 0.1 | 1 | 1.6 | 0.05 |
| 1,000 | 16.7 | 0.30 % | 0.19 % | 0.11 % | 2.5 | 42 | 45.4 | 1.62 |
| 5,000 | 83.3 | 1.51 % | 0.95 % | 0.56 % | 12.3 | 209 | 226.8 | 8.08 |
| 20,000 | 333.3 | 6.03 % | 3.80 % | 2.26 % | 49.3 | 835 | 906.8 | 32.32 |

- **Verification takes 6.0 % of one Pi 5 core at 20,000 declared nodes** with ed25519-dalek, and
  0.30 % at 1,000. Votes are public, so they travel by direct gossip and cost Blend nothing.
- **Bytes count each vote once.** Gossip over a mesh of degree `d` delivers up to `d` copies. At
  20,000 declared nodes the votes come to 49 KB/s with Ed25519 and 835 KB/s with ML-DSA-44, against
  the 0.31 MB/s a core connection of Blend carries today (`CERTIFIED.md` D3).
- **A certificate of separate signatures** is 0.9 MB at 20,000 declarations with Ed25519 and 32 MB
  with ML-DSA-44, 36 times larger. An aggregate signature would shrink it to one signature and a
  bitmap of the signers, but needs a key the declarations do not carry, and the pairing-based ones
  are not post-quantum. Not measured here.

## L.6 — what else changes

**What reads finality, once it takes minutes** (`MAPPING.md` §7; `SLOTS.md` K.4, K.5):

- Under certificates only and the fast path, `B_imm` and the node's LIB follow the latest finalized
  checkpoint, at most `L + 2R` slots behind the tip while rounds justify, and the largest rollback
  shrinks with them.
- Fork pruning at `B_imm` would discard uncle candidates the stake inference still counts: the
  uncle window `W·f⁻¹` is 360 slots, longer than `L + 2R` at a lag of 30 and rounds of 60. Pruning
  must keep the uncle window (`MAPPING.md` §6).
- A node that returns checks the certificates of the rounds it missed against the registry. That
  replaces the offline grace period only while the keys that signed them stay slashable. A
  withdrawn declaration's note is released one epoch after the node stops signing (SDP, Withdraw
  message), so a node away longer needs a checkpoint or the Bootstrap rule, as FFG's clients must
  "log on" within its four-month withdrawal delay.
- The registry changes at epoch boundaries, from a finalized epoch two back. A link that crosses a
  change needs two thirds of both registries, as FFG's dynasties do (FFG §3).
- The epoch's phases, SDP's two-epoch lag and the stake inference's period read finality through
  the epoch, which keeps its length (K.4). The wallet's reservations and the zone SDK read the LIB,
  so they wait minutes instead of hours.

**Keys and accountability.**

- The provider key, Ed25519, also authenticates the node's connections. It can sign votes under a
  vote domain. A key of its own in the declaration keeps a network-facing key out of slashing and
  allows an aggregate scheme, at a change to SDP's declaration.
- Accountable safety needs evidence the chain acts on: two signed votes that break a slashing
  condition. Slashing a service note is a new Mantle operation. Today a note is only locked and
  released.
- The evidence must land while the note is locked, at most about one epoch after its signer stops
  voting, where FFG locks deposits for four months.

**Privacy (C1).**

- With one weight per declaration, votes reveal nothing new about stake: a declaration's key,
  locators and note value are public already. A vote names the block its node held `L` slots back,
  on which every node agrees from a lag of 30 slots (L.2), so it gives the tagging attack no view to
  read. A vote carries no lottery win, so unlike D5's seats it samples no stake.
- Weight by value asks operators to lock their stake in the notes behind their declarations. On a
  transparent ledger that ties the stake to a public key and to network locators, the link C1
  forbids and Blend exists to hide.

**The constraints.** C1 holds with one weight per declaration. C2 holds: certificates stall while
more than a third of the declared weight withholds its votes, is offline or is split away, and the
chain continues. Q12 relaxes C3. C4
does not apply, since a vote is not a lottery win. C5 holds (L.5).

## Verdicts

- **H25** holds on testnet's Blend and the specification's: with rounds of 60 slots and a lag of 30
  a block is final within 147 s at the 95th percentile, and every round in the runs read justifies.
  At the heavy point it fails as stated: a lag of 30 slots let a justified checkpoint leave the
  longest chain in 18 of 36 runs. A lag of 60 gives 177 s there.
- **H26** holds. At the analysis' minimum, 500 declarations, 1.67 % of the active stake, hold a
  third of a network of 1,000. Holding 30 % needs honest declarations that lock 60 % of the active
  stake at full uptime, and none suffices at 95 %.
- **H27** holds. Below a third of the declared weight one side at most certifies, in the closed form
  and in every engine run; at 0.34 an even split finalizes both sides.
- **H28** holds: 6.0 % of one Pi 5 core at 20,000 declared nodes and 60-slot rounds with
  ed25519-dalek.

## What the phase leaves open

- The variant of L.4: its liveness after a reorganization past a source is not derived, and nor is
  a floor over its lag against eclipses and splits.
- How much of the honest stake would lock into declarations, and whether the study's convention,
  the coalition's stake share of the declarations, or the economics of the minimum stake governs.
- Slashing service notes: the operation, the evidence and its window.
- A vote key in the declaration, and an aggregate scheme for certificates.
- Links across a registry change.
