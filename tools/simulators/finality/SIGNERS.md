# Certificates from other signers

Phase M of `PLAN.md`. Tables come from `scripts/m1_holds.py`, `scripts/m2_time.py`,
`scripts/m3_privacy.py`, `scripts/m4_cost.py`, `scripts/m5_quorum.py` and `scripts/m7_active.py`
through `scripts/tables.py`. Specifications are read at `logos-lips` `bd1ca2c8`, and Ouroboros Peras at
`cardano-foundation/CIPs` `86b89208` (`CIP-0140/README.md`, SHA-1 `3048a9df`). One slot is one
second and `f = 1/30`. Every committee is held at `ε = 1e-9` a round, as in D0.

## M.0 — the reading

**The yardstick.** A certificate shortens finality only where it makes a block final sooner than
the chain settles it against the same coalition, under the same delay model. Against a share `α`
of the stake, that is the chain's own wait at `1e-9`, which L.4 reads under random delay on the
specification's Blend and under the worst case at 10 s without grinding. The slot rule's 18 hours
hold a third under the worst case at 10 s, with the new nonce of `slots.md` §4 (`SLOTS.md` K.7).

**The sets.**

| set | who signs | weight | a vote shows | travels | constraints broken |
| --- | --- | --- | --- | --- | --- |
| anonymous seats (Phase D) | a note that wins a seat that round in a private lottery | one a seat | a seat won, by a proof | through Blend | C1: on top of today's cover the quota ceiling falls 41 to 69-fold; with the cover raised stake is sized 1.7 times as fast (M.3) |
| the chain's own leaders | the leaders of the latest wins recorded on the finalized chain, canonical or uncle | one a win, by its tag `ρ_LEAD` | the win its sender led | through Blend | C1: on top of today's cover a win is tied to its leader's node with chance 0.286 to 0.430, against 0.016; with the cover raised 0.026 (M.3) |
| an opt-in public set (D1b; Blend's declared nodes, Phase L) | holders who declare | by value, or one a declaration | the declaration | directly | C3; with weight by value, also C1 for the declared |
| every leading note declared | every note that may lead | by value | the declaration | directly | C1 and C3, for every holder that stakes |
| delegated weight | operators, with the weight notes delegate to them | by the value delegated | the operator's total | directly | C3, for the operators; C1 open, through the value each delegation moves |

- **The chain's own leaders need no new key.** A block's proof of leadership is bound to a
  one-time key `P_LEAD`: "This key is needed to sign the proposed block", and "The PoL is bound to
  a public key from an asymmetric signature scheme" (`cryptarchia-proof-of-leadership.md`). The
  header carries it as `leader_key: Ed25519PublicKey`, and a proposal's signature under it is
  checked to "Ensure that the leader who won the lottery is actually proposing this block since
  PoL’s are not bound to blocks directly" (`cryptarchia-v1-protocol.md`). A block references an
  uncle "by carrying its full signed header", so an uncle's key is recorded as well. A leader that
  keeps the key's secret can sign votes with it.
- **One weight a win, not a block.** The specification allows that "the owner of a winning note can
  fabricate and self-sign such a header later", and "Uncle references are **not** required to be
  unique, and duplicates are permitted". Counted by block, a coalition would add a weight with each
  variant of its own wins. The proof of leadership outputs a tag fixed by the note and the slot,
  `ρ_LEAD := hash(NONCE_CONTRIB_V1 || sl || noteID || sk)`, carried in the header as
  `entropy_contribution`, so the committee counts distinct tags and one vote a tag a round.
- **The committee is counted on the finalized chain.** It is the latest `n` wins recorded before a
  point at least the uncle window, `W·f⁻¹` = 360 slots, before the block of the latest finalized
  checkpoint, read on that chain. No uncle can still join them, and every node reads the same
  finalized chain, so every node counts the same committee and sets the quorum from the count. The
  committee therefore trails finality, and a leader keeps its key and stays online for that lag
  and the window. Anonymous seats differ: nobody counts them, so D0 sizes their quorum against a
  Poisson number of seats and the inference's error.
- **A leader's key is not tied to its stake.** `P_LEAD` is a one-time key, so equivocation under it
  cannot be slashed, and its holder can sell it within the window at no cost.
- **Every leading note declared** makes SDP's declaration the condition to lead. Service notes
  "can still participate in Proof of Stake" (Mantle, read in L.0), so the lottery already admits
  declared notes. The change is to admit no other, and a declared note stays locked, "preventing it
  from being spent until explicitly released through a Withdraw Operation" (Mantle). The proof of
  leadership still hides which note won. A holder below SDP's minimum stake can then neither lead
  nor sign.
- **Delegated weight** is a sketch. A note proves once an epoch that it delegates its value to an
  operator, with a nullifier that stops it delegating twice, and without showing which note it is.
  No circuit exists. The value delegated is shown, since an operator's weight is the sum.
- **Outside the network**, a checkpoint anchored on another chain rests on that chain's
  assumption, not on Cryptarchia's stake (G5). It is out of scope.

**What a vote must not show (C1).** "If the activity of the leader reveals their stake values
(e.g. through weighted voting), then this value can be used to reduce the anonymity set for the
leader by bucketing the leader as high/low stake and can open him up to targeting." The same list
asks that "The block proposals should not be linkable to a leader" (`cryptarchia-v1-protocol.md`).
Every public set weighs votes by declared stake where it weighs by value, the mechanism the first
sentence names.

**Blend's budget.** "In this version of the protocol, the length of the round is 1 second (an
equivalent of a single slot)" (`blend-protocol.md`). A core connection carries
`F_1 = (max(F_C(1 + R_C), F_D(1 + R_D)) + F_T)·β_max = 16` messages a round against a read limit
`r_1 = 20`, with `F_C = 1`, `F_D = 1/30`, `F_T = 130/30`, `R_C = 0`, `R_D = 1` and `β_max = 3`,
the values D3 read at `47a73cdc`. "Flooding delivers each message once per neighbor", so `F_1`
must stay below `r_1`, where "a backlog on a connection never drains", and `F_T` is sized so that
`F_1 = 16` leaves room for a backlog to drain.

- **A vote can take its node's scheduled cover, as a won slot does.** "Winning the block lottery
  consumes the next scheduled cover, keeping every node's emission count identical whether or not it
  produces blocks" (`reports/blend`), which the `max` in `F_1` reads. A core node's quota "is used
  for generating cover messages, but the core node is not limited by this assumption"
  (`blend-protocol.md`). A vote that fits its node's cover adds no load, and the votes beyond each
  node's cover must fit the headroom from 16 to `r_1`, or take the place of transaction messages.
- **Votes beyond a node's cover need an allowance of their own**, as do an edge node's. "A single
  quota is used per single proof of leadership", which covers a proposal and its copy.
- "A payload the Blend network fails to deliver is broadcast directly by its sender, without the
  unlinkability the network provides." Votes are not replicated (D3), so every vote Blend fails to
  deliver is either lost, D2's committees with lost votes, or sent in the open, against C4.

**Ouroboros Peras** (CIP-0140). A certificate adds weight to a block in the fork choice instead of
finalizing it. "Fast settlement occurs in the presence of adversaries with up to one-quarter of the
stake, but Praos-like safety is maintained when adversaries control more than that amount of
stake." The quorum is `τ > 3n/4`, to "Guard against a minority (< 50%) of adversarial voters",
though the CIP's example sets `τ = 675`, three quarters of `n = 900` exactly, with rounds of
`U = 90` slots, a boost of `B = 15` blocks and a cool-down of 780 rounds. Its committee of 900 is
sized for "1 ppm probability of no honest quorum at 10% adversarial stake". "If they possessed
approximately at least 25% of the stake, they could choose not to vote, with the result that no
quorum would be reached and the protocol would enter a cool-down period", in which the chain runs
as Praos. At `U = 90` and `L = 30`, "settled versus rolled-back would be certain in two minutes",
with "less than a one in a trillion probability even at 45% adversarial stake" of a roll-back after
that. Its voters are stake-pool operators drawn by a VRF, so they are known. Peras's paper is not
read (`PLAN.md` §7.2).

**Readings taken without the owner's answer.**

- Public sets vote in rounds of 60 slots at a lag of 30, as L.2 measured them with 1,000
  declarations of weight one. Larger sets are not measured.
- Votes through Blend take their node's cover where it fits, and the headroom beyond it. Kept for
  the backlog instead, the headroom's messages come out of the transactions (M.4).
- The coalition's share of seats and of counted wins is its share of the stake. For wins this
  assumes it keeps no honest win out of the record, which is open.
- *Every honest seat counting* means that every honest seat votes and every vote arrives. *The
  inference's error up to 1.05* means the committee also holds while the true stake exceeds the
  inferred by up to 5 %, about six standard deviations of the inference's ±0.9 % an epoch (D2).
- Delegation is renewed each epoch, and the value delegated is public.

## M.1 — what each set holds

The coalition holds a share `a` of the signing weight. A public set's certificate needs two thirds
of its weight: safety needs `a < 1/3`, and liveness `u(1 − a) ≥ 2/3` for a share `u` of the
honest weight online (L.1). A committee of seats or wins needs its own quorum.

- **Anonymous seats** sample the stake. D0 and D2's committee holds `α` at `1e-9` a round, against
  a Poisson number of seats.
- **The chain's own leaders** are a counted committee of `n` wins. The coalition holds
  `A ~ Bin(n, α)` of them, two conflicting certificates need `A ≥ 2Q − n`, and a round stalls when
  the honest wins online, `Bin(n, (1 − α)u)`, fall short of `Q` (`src/finality_sim/signers.py`).
  No inference enters, since the wins are counted.
- **An opt-in set** gives the coalition `a = α/(α + (1 − α)v)` for a share `v` of the honest stake
  declared (D1b, L.1).
- **Every leading note declared** gives `v = 1`, so `a = α`, if every honest holder can declare.
  With a share `z` of the honest stake below SDP's minimum stake, `v = 1 − z`. That stake leaves the
  leader lottery as well, so the coalition holds the same share `a` of the lottery, and the chain's
  own wait and the slot rule face `a` too.
- **Delegated weight.** With a share `v` of the honest stake delegated, `c` of it to the
  coalition's operators, `a = (α + (1 − α)c)/(α + (1 − α)v)`. With every note delegating, safety
  holds below `c = (1/3 − α)/(1 − α)`, and liveness up to `c = 1 − 2/(3u(1 − α))`.

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
honest stake is spread as Cardano's pools are (D1b's data):

| coalition | uptime 1 | uptime 0.95 | uptime 0.9 | Cardano's largest pools that hold it, uptime 1 |
| --- | --- | --- | --- | --- |
| 10 % | 25.93 % | 22.03 % | 17.70 % | 84 of 2,522 |
| 25 % | 11.11 % | 6.43 % | 1.23 % | 35 of 2,522 |
| 30 % | 4.76 % | none | none | 15 of 2,522 |
| a third | none | none | none | – |

- **Counting the committee shrinks it fivefold, while every honest leader is online.** Against a
  quarter the leaders need 1,030 wins, 8.6 hours of the chain, where anonymous seats need 5,355 a
  round. With 95 % of the honest leaders online a quarter needs 2,185 wins, and 30 % needs 78,979,
  27.4 days of the chain; with 90 % online, 30 % cannot be held.
- **No opt-in set rests on the stake.** Whatever service it serves and whatever minimum stake it
  asks, it holds a coalition only while the honest stake declared exceeds D1b's frontier: 86 %
  against 30 % at full uptime, and none at 95 %.
- **Every leading note declared holds the coalition at its stake share**, if every honest holder
  can declare: 30 % while at least 95.24 % of the honest stake is online, a quarter from 88.89 %, a
  third never. With 5 % of the honest stake below the minimum stake, 30 % needs 96.74 %. From
  14.3 % below it the coalition holds a third of the weight and of the leader lottery alike, so
  the slot rule's fallback fails at the same point as the certificates.
- **Delegated weight rests on where the delegation goes.** With every note delegating, against 30 %
  it fails once the coalition's operators hold 4.76 % of the honest stake at full uptime, what
  Cardano's 15 largest pools hold, and the edge falls to nothing at 95.24 % of the honest weight
  online. Against a quarter it fails at 11.11 % at full uptime, 6.43 % at 95 %.

Gates (`tests/test_signers.py`): the delegated share equals the coalition's share of the weight
over 200 random allocations of holders to operators; with nothing attracted, the set holds from
D1b's frontier and not below it, at three uptimes; the largest attracted share is an edge, held
just below and lost just above, at quorums of 2/3, 0.6 and 0.75 (at 2/3 safety and liveness meet
at full uptime, so the other two test each bound alone), and with part of the honest stake
delegated it equals a scan; every leading note declared weighs the stake share and is live from
the least uptime and not below it; the counted committee equals a direct scan over every size and
quorum with the binomial tails summed term by term, which caught a search that skipped valid sizes,
and its quorum is live and one vote fewer is not safe. Twelve registered mutations fail them. The
check that no counted committee holds a third follows from the closed condition and has none.

## M.2 — how fast

A block at slot `s` first lies in a round's target at the first round start `t ≥ s + L`. A single
certificate holds it once the quorum's votes have arrived, and the checkpoint gadget finalizes it
one round later. Averaged over a round that is `L + (R − 1)/2` and `L + (R − 1)/2 + R` slots, plus
the time the quorum's votes take. A block just past a round's target waits `(R − 1)/2` longer than
the mean.

**Public signers** gossip their votes directly. With rounds of 60 slots and a lag of 30 on the
specification's Blend, measured with 1,000 declarations of weight one, a block is final in 120 s
on average and 147 s at the 95th percentile (L.2). That time does not depend on the coalition. What
the set holds does (M.1).

**Votes through Blend.** Node `i` of `N` emits cover at `F_C(1 + R_C)/N` a second, proposals at
`F_D(1 + R_D)·s_i` and votes at `v·s_i`. Its votes fill its spare cover first, and the votes beyond
each node's cover must fit the headroom, `4/3` messages a second (`vote_budget`). The budget then
depends on how the stake is spread: `4/3` when no vote fits a node's cover, and
`F_C(1 + R_C) − F_D(1 + R_D) + 4/3` with equal stakes, where every node's spare cover fills before
the headroom. With the cover raised by the emission multiple `x = 1 + n/(R·f)` to keep today's
quota ceiling, a vote costs `1/f` cover messages: `F_1 = (x + 13/3)·3 ≤ 20` needs `x ≤ 7/3`.

| budget | votes a second, network-wide |
| --- | --- |
| no vote in a node's cover | 1.333 |
| Cardano's pools | 1.620 |
| equal stakes | 2.267 |
| cover raised | 0.044 |

A round of `R` slots carries `R` times the budget's votes, so `R ≥ n` over the budget, and `1.05n`
over it with the inference's error. Blend carries the votes evenly over the round, so with the
coalition withholding its own the quorum's last honest vote leaves `R·Q/H` into it, for the `H`
honest votes cast: 96 % of the round for anonymous seats against 30 %. Rounds rounded up to whole
slots, a lag of 30 slots, and the largest 95th-percentile time to a quorum D6 measured on the
specification's Blend, 10.3 s, added:

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

These times hold under random delay. The lag of 30 slots and the delivery were measured there
(D6), and under a delay an adversary chooses, votes on a target that shallow can be split: at a
quarter and `Δ = 10` s a split succeeds at depth 2 with probability 0.53 (D6). A target deep enough
not to be split comes no sooner than the chain's own wait at the chance of a split a round accepts
(D6; `CERTIFIED.md`, Phase K). So the gadget's times are set against the chain's wait under random
delay, and the worst case's waits are shown apart:

| coalition | the chain's own wait, random delay (h) | anonymous seats, every honest seat counting, on top of today's cover: no vote in a node's cover / Cardano's pools / equal stakes (h) | the chain's own leaders, counted, every honest leader online, the same three (h) | the same, 95 % of the honest leaders online (h) | with the cover raised, the fastest set: the chain's own leaders, every one online (h) | the chain's own wait, worst case at 10 s: without grinding / the new nonce of `slots.md` §4 after a deflation (h) |
| --- | --- | --- | --- | --- | --- | --- |
| 10 % | 0.45 | 0.33 / 0.27 / 0.20 | 0.05 / 0.05 / 0.04 | 0.07 / 0.06 / 0.05 | 1.25 | 0.81 / – |
| 25 % | 1.70 | 2.70 / 2.22 / 1.59 | 0.52 / 0.43 / 0.31 | 1.11 / 0.92 / 0.66 | 15.39 | 3.16 / – |
| 30 % | 3.09 | 17.17 / 14.14 / 10.11 | 3.55 / 2.92 / 2.09 | 40.90 / 33.67 / 24.06 | 106.11 | 5.93 / 6.43 |
| a third | 5.10 | – / – / – | – / – / – | – / – / – | – | 10.11 / 12.47 |

- **With today's quota ceiling kept, every set through Blend is slower than the chain** at 10 %,
  25 % and 30 %: the counted leaders, the fastest of them, take 1.25 hours against 10 %, where the
  chain waits 0.45.
- **On top of today's cover, anonymous seats gain against 10 %**, 0.20 to 0.33 hours where the chain
  waits 0.45, and against a quarter only with equal stakes, 1.59 hours against 1.70. Against 30 %
  they take 10.11 to 17.17 hours.
- **The counted leaders gain against 10 % and a quarter**, also with 95 % of the honest leaders
  online. Against 30 % they gain only with every honest leader online and the stake spread at least
  as evenly as Cardano's pools: 2.92 hours, and 2.09 with equal stakes, where the chain waits 3.09.
  With 95 % online they take 24.06 to 40.90 hours.
- **These times assume the votes beyond each node's cover take transaction messages**, keeping the
  backlog's headroom. Using the headroom itself puts `F_1` at `r_1`, where a backlog never drains.
- **A single certificate at the set's quorum** comes about one round sooner. That is D1 (a)'s
  certificate, whose guarantee D1 leaves open, not Peras's: under Peras's three quarters no
  committee exists from a quarter (M.5).
- **Public signers take two minutes at any share**, but hold only what M.1 gives each set.

Gates (`tests/test_signers.py`): with the honest votes of a round leaving evenly over it and the
coalition's withheld, the closed forms equal the gadget's mean time and its longest on an agreed
chain, for one round and for two, with a lag and a round that differ; at each mode's vote rate,
D3's `blend_load` takes a core connection from the specification's 16 messages a round to `r_1`,
and the headroom equals 40 of the 130 transaction messages per 30 slots; with equal stakes the
budget is the spare cover plus the headroom, with all stake on one node it is the headroom, and any
other spread lies between. Ten registered mutations fail them.

## M.3 — privacy

D5's model, for a node with an adversarial peer, 59 % of nodes at `f_adv = 0.2` and the
specification's peering degree (D5): a message is attributed to its node when its whole blend path
is adversarial, 0.008 at 3 hops; a proposal goes out twice. Each seat's vote is a fresh lottery win,
so each attributed vote samples the stake. A leader votes for one win in every round of the window,
40 votes a win at 4/3 votes a second, 68 at 34/15 and 4/3 with the cover raised, so the observer
samples the stake by the wins it ties to a node. Votes take scheduled cover as won slots do, so on
top of today's cover the quota ceiling, the stake above which a node's emission count identifies it
(the Blend report's §3.10), falls by the emission multiple. Mean days until a holder whose stake
lies in many small notes is identified, and until its stake is known to ±10 %:

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

- **On top of today's cover the quota ceiling falls 41 to 69-fold**: from 0.1475 % of the inferred
  stake on 20,000 nodes to 0.0036 % at 4/3 votes a second and 0.0021 % at 34/15, below an equal
  share of the stake on those nodes. A node above it is told apart by its emission count alone.
- **Through attribution, seats' votes make stake learnable 21 to 35 times as fast**, whatever the
  coalition the committee is sized for: a 0.1 % holder is sized in 103 days at 4/3 votes a second
  and 62 at 34/15, instead of 2,179. That holds for stake in many small notes; a holder with few
  notes wins at most one seat a note a round.
- **With the cover raised, the ceiling holds**, but stake is still sized 1.7 times as fast as from
  blocks alone: in 1,305 days for a 0.1 % holder.
- **The chain's own leaders tie wins to nodes.** For a node with an adversarial peer, a win's votes
  tie it to the node with chance 0.286 at 4/3 votes a second and 0.430 at 34/15, against 0.016 for
  its proposal alone, against the specification's "The block proposals should not be linkable to a
  leader". Stake is sized 18 to 27 times as fast as from blocks alone. Tied wins name online
  leaders, who must stay online through the window for the committee to hold.
- **Every public set shows what it declares**: each signer's stake and node, and with every leading
  note declared, each staking holder's. That is the targeting C1 names, and it bears on liveness too: the
  set holds 30 % only while 95.24 % of the honest stake stays online.
- **Delegated weight shows each operator's total**, and the value each delegation moves. On a
  transparent ledger that value may narrow which note delegated (open).

Gates (`tests/test_signers.py`): a proposal alone is tied to its node as D5 counts it; a leader
casts 40 votes a win on top of today's cover and 4/3 with the cover raised; a direct draw of
attributions agrees with the closed form. Two registered mutations fail them.

## M.4 — cost

Public signers vote once a round of 60 slots, as L.5 counts them; bytes count each vote once.
Ed25519 verification is the Raspberry Pi 5's median with ed25519-dalek (`reports/pqc`):

| public signers, rounds of 60 slots | votes a second | one Pi 5 core, verifying | received (KB/s) |
| --- | --- | --- | --- |
| 1,000 | 16.67 | 0.30 % | 2.5 |
| 20,000 | 333.33 | 6.03 % | 49.3 |
| 100,000 | 1,666.67 | 30.17 % | 246.7 |

Votes through Blend at each budget. The votes beyond each node's cover fill the headroom, and every
node verifies a message's header once for each of its three blending operations, against `V = 156`
a second, one core of a Raspberry Pi 5 (D3); a Blend message is 19,318 bytes:

| votes through Blend | votes a second, network-wide | Blend headers a node verifies a second, more / one Pi 5 core | a leader's signature, one Pi 5 core | a core connection carries, today / with the votes (KB/s) | transaction messages the votes take, the backlog's headroom kept | Blend keys a leader's votes need a win / today's leadership quota a win |
| --- | --- | --- | --- | --- | --- | --- |
| no vote in a node's cover | 1.333 | 4.0 / 2.56 % | 0.0241 % | 309 / 386 | 30.8 % | 120 / 6 |
| equal stakes | 2.267 | 4.0 / 2.56 % | 0.0410 % | 309 / 386 | 30.8 % | 204 / 6 |
| cover raised | 0.044 | 4.0 / 2.56 % | 0.0008 % | 309 / 386 | 30.8 % | 4 / 6 |

- **Every leading note declared is the costliest public set**: one signer a declaration, 30 % of a
  Pi 5 core at 100,000 declarations with rounds of 60 slots. A minimum stake low enough for every
  holder lets the coalition split into as many declarations as it likes, so the load is the
  coalition's to set unless signatures aggregate (C5). Delegated weight signs with its operators
  only.
- **Votes through Blend cost Blend more than their checks**: four header verifications a second,
  2.56 % of a Pi 5 core, and 77 KB/s more on every core connection, or, with the backlog's headroom
  kept, 30.8 % of Blend's transaction messages.
- **Votes need Blend keys.** At 4/3 votes a second a leader votes 40 times a win, 120 keys, and at
  34/15, 204, against today's leadership quota of 6 a win. Votes in a core node's cover use its core
  quota; the rest need a rule of their own.
- **Proving.** Seats prove each seat they win (D3). Leaders prove nothing new for the lottery, only
  their quota; a tag that makes a leader's equivocation punishable (D4) would cost a proof a vote.
  Delegation proves once a note an epoch, with a circuit not designed.

## M.5 — composition

| quorum | two conflicting certificates from | certificates stall above, uptime 1 / 0.95 / 0.9 |
| --- | --- | --- |
| two thirds, Casper FFG | 33.3 % | 33.3 % / 29.8 % / 25.9 % |
| three quarters, Ouroboros Peras | 50.0 % | 25.0 % / 21.1 % / 16.7 % |

- **Peras's three quarters trade liveness for safety.** Two conflicting certificates need half the
  weight, against a third under two thirds, but certificates stall once the coalition withholds a
  quarter. The CIP's quorum is strict, `τ > 3n/4`, so a quarter already stalls it, where the table
  reads the closed form at its edge. A coalition of 30 % stops fast settlement under three quarters
  by withholding its votes, whichever the signers. A sampled committee stalls below a quarter as
  well; the CIP sizes 900 for one stall in a million rounds at 10 %.
- **Of the two quorums, only two thirds can hold 30 %**, while at least 95.24 % of the honest
  weight is online, on a set that holds it (M.1).
- **A boost settles a block, and finality still comes from the slot rule.** "Peras's boosted blocks
  protect against rollbacks because it can be made extremely difficult for an adversary to cause a
  rollback of a boosted block" (CIP-0140), but the block becomes final only at the slot rule's
  window.
- **The slot rule stays under both.** Under FFG with the fast path, `B_imm` is the later of the
  latest finalized checkpoint and the slot rule's block (L.0); under Peras's boost, `B_imm` stays
  the slot rule's block. A stall leaves finality at 18 hours under both. A set captured past its
  conflicting-certificate share finalizes two forks under FFG, which splits the nodes (L.3).

## M.6 — what else changes

- **Every set that finalizes in minutes** moves `B_imm`, follows FFG's fork choice from the latest
  justified checkpoint, and needs links across a registry change to carry two thirds of both
  registries (L.6). Pruning must keep the uncle window.
- **The chain's own leaders** need a vote counted once a tag `ρ_LEAD` a round, a committee of the
  latest wins counted on the finalized chain, and a Blend quota for votes beyond a node's cover.
  With a sliding window every link crosses a registry change. Leaders keep their keys' secrets
  through the window and its lag behind finality. Whoever learns or buys one signs that win's votes
  in any past round (D4), and no stake answers for it, so certificates are trusted only within the
  window and rest also on no honest leader leaking or selling its key.
- **Every leading note declared** changes the proof of leadership, to prove membership in the
  declared notes, locks every note that leads, and leaves a holder below SDP's minimum stake unable
  to lead. Slashing needs the Mantle operation of L.6.
- **Delegated weight** needs a Mantle operation and a circuit for private delegation, the
  operators' totals tallied each epoch, and slashing for operators.
- **Anonymous seats** keep D1, D3 and D4's open questions, and need a proof of quota for votes.

## M.7 — the active stake at 30 % of the supply

The owner's question, 2026-11-06: what changes if the active stake is at most 30 % of the supply,
and that stake governs consensus.

**The reading.** The lottery already weighs each note against the active stake: "the probability
that an eligible Cryptarchia participant wins the right to propose a block depends on that
participant’s stake relative to the total active stake. Because leader selection in Cryptarchia is
private, the total active stake is not directly observable. Instead, nodes must infer it from
observable chain growth" (`cryptarchia-total-stake-inference.md`). Every share `α` in the study is
therefore a share of the active stake, and L.1 already set the active stake at the block rewards'
target of 30 % of the supply (L.0). No figure of M.1 to M.6 moves. Three readings change
(`src/finality_sim/active.py`, `scripts/m7_active.py`):

- **A coalition holds at most `0.3α` of the supply.**
- **Stake outside the active stake joins the lottery without notice.** A note joins by proving a
  win, with no declaration (C3). The inference reads the first `6⌊k/f⌋` slots of each epoch, so a
  change just after them lasts about 1.4 epochs (D2), 10.5 days at `k = 2160`; it corrects a rise
  in full at its next correction (`beta = 1`, K.8). Until then the true active stake exceeds the
  inferred by a factor `x`, and a slot is won with chance `1 − (1 − f)^x`.
- **Only the sets whose quorum reads the inference see `x`**: the anonymous seats, whose threshold
  D1 sets from the inferred stake so that all stake together expects `n` seats, and the slot rule's
  lottery. The chain's own leaders are counted (M.1), a public set's weight is declared, and
  delegated weight is tallied each epoch.

| coalition, share of the active stake | share of the supply, at most, with the active stake at 30 % of it |
| --- | --- |
| 10 % | 3.0 % |
| 25 % | 7.5 % |
| 30 % | 9.0 % |
| a third | 10.0 % |

**Anonymous seats.** A coalition whose stake joins from outside the active stake makes
`x = 1/(1 − α)`, the state a deflation leaves (`FURTHER.md` G7), without withholding a block. D2
sized the seats for `x` up to 1.05, the inference's noise. Once the coalition's stake joins, no
committee exists from a coalition of 21.9 %, where `2α² − 5α + 1` reaches zero. Honest stake joining
breaks the committees sized for 1.05 too, under D2's count, where honest votes split between two
forks fill both certificates:

| coalition | anonymous seats a round, sized for the inference's error up to 1.05 | the true over the inferred active stake once the coalition's stake enters | anonymous seats a round, sized for that | honest stake entering that breaks the seats sized for 1.05: share of the active stake / of the supply |
| --- | --- | --- | --- | --- |
| 10 % | 801 | 1.11 | 1,025 | 5.6 % / 1.7 % |
| 25 % | 9,728 | 1.33 | none | 6.3 % / 1.9 % |
| 30 % | 279,488 | 1.43 | none | 6.5 % / 2.0 % |
| a third | none | 1.50 | none | – |

- **The gap does not need the assumption.** A coalition that withholds its blocks for one period
  deflates the inference to the same `x` (G7), so anonymous seats hold no coalition from 21.9 %
  whatever share of the supply is active. Their verdict stands, more firmly.

**The slot rule.** A coalition's stake joining is the deflated case M.2's yardstick reads. A larger
`x` makes blocks come faster until the inference corrects, and under the worst case faster blocks
need a longer wait (K.5, K.7). K.7's bound at `1e-9` under the worst case at 10 s, without grinding,
with both shares' rates scaled by `x`:

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

- **Against a third, `⌊k/f⌋` = 18 hours hold while the true active stake stays within 1.925 times
  the inferred.** A coalition's own stake joining makes 1.5. With the active stake at most 30 % of
  the supply, that holds whenever the inferred active stake is at least 15.6 % of the supply, and a
  rise from 15 % of the supply to 30 % within one inference period breaks it: 19.58 hours.
- **Against 30 %, 18 hours hold up to 2.627 times**, so whenever the inferred active stake is at
  least 11.5 % of the supply.
- **The new nonce of `slots.md` §4 adds less than 1 %** where M.2 reads both, after a deflation:
  6.43 hours against 6.41 at 30 %, and 12.47 against 12.36 at a third.

**Every leading note declared.** The declared stake is the active stake, so only holders that stake
give up C1 and C3. A holder outside the active stake leads and signs nothing, and no set shows its
stake. The minimum stake caps the declarations the active stake can make, however the coalition
splits its stake:

| active stake, share of the supply | the minimum stake, share of the supply | declarations, at most | votes a second, rounds of 60 slots | one Pi 5 core, verifying | received (KB/s) |
| --- | --- | --- | --- | --- | --- |
| 30 % | 0.001 % | 30,000 | 500.00 | 9.05 % | 74.0 |

- **That caps the load M.4 left to the coalition** at 9.05 % of a Pi 5 core, with rounds of 60
  slots.
- **Stake outside the active stake joins only by a declaration on the ledger**, so the quorum never
  lags the stake. What the set holds is M.1's.

Gates (`tests/test_active.py`): a coalition whose stake joins holds `α` of the true stake at
`x = 1/(1 − α)`, over 200 random stakes; the supply share; D2's committee exists just below the
seats' edge and not from it, both read from `committee.smallest_committee`; the honest stake joining
that breaks the committee sized for 1.05 is an edge, held just below and lost at it, with the
coalition diluted to `α/x`; notes holding `x` times the inferred stake, split at random, win a slot
with chance `1 − (1 − f)^x`, and K.7's bound at that chance equals the bound with both rates scaled
by `x`; the least inferred stake; the cap on declarations. Nine registered mutations fail them.

## Verdicts

- **H29 holds.** Against 30 %, anonymous seats on top of today's cover finalize in 10.11 to 17.17
  hours, where the chain waits 5.93 under the worst case at 10 s and 3.09 under random delay, the
  like-for-like comparison. With the cover raised every set through Blend finalizes later than the
  chain at 10 %, 25 % and 30 %.
- **H30 fails.** The leaders' committee is counted, so it needs neither D0's Poisson margin nor the
  inference's: 1,030 wins against a quarter, 8.6 hours of the chain, with rounds of 773 s where the
  seats' take 4,017 s at 4/3 votes a second. Against 30 %, with every honest leader online, they
  take 2.09 to 3.55 hours where the chain waits 3.09 under random delay.
- **H31 holds, if every honest holder can declare.** Opt-in sets hold only above D1b's frontier.
  With every leading note declared the coalition weighs its stake share, and 30 % is held from
  95.24 % of the honest stake online; with 5 % of the honest stake below the minimum stake, from
  96.74 %.
- **H32 holds.** Against 30 % the edge is 4.76 % of the honest stake at full uptime, which Cardano's
  15 largest pools hold.
- **H33 holds for stake in many small notes.** Through attribution a 0.1 % holder is sized in 103
  days at the committees against 10 % and against 25 % alike at 4/3 votes a second, against 2,179
  from blocks alone.

By set, against the study's 30 % to a third:

- **Anonymous seats: not recommended.** Under random delay they finalize sooner than the chain
  against 10 %, and against a quarter only with equal stakes, always with the quota ceiling lowered
  41 to 69-fold. With the ceiling kept they are slower at every share. Once a coalition's stake
  joins from outside the active stake, or after a deflation, none exists from 21.9 % (M.7).
- **The chain's own leaders: not recommended against 30 % to a third**, and the anonymous set that
  comes closest. Under random delay, on top of today's cover, they finalize sooner than the chain
  against 10 % and a quarter. Against 30 % they do so only with every honest leader online through
  a window of 2.4 days and the stake spread at least as evenly as Cardano's pools, 2.92 hours where
  the chain waits 3.09; with 95 % online they take 33.67. That speed costs 30.8 % of Blend's
  transaction messages, a Blend quota 20 to 34 times today's a win, a quota ceiling lowered 41 to
  69-fold, and wins tied to their leaders' nodes with chance 0.286 to 0.430. With the ceiling kept
  they are slower than the chain at every share, and a third is never held.
- **Opt-in public sets, Blend's declared nodes among them: not recommended** (D1b, L).
- **Every leading note declared: the one set that rests on the stake and finalizes in two
  minutes.** It holds 30 % from 95.24 % of the honest stake online, if every honest holder can
  declare, and never a third. It makes the stake and node of every holder that stakes public, against
  C1 and C3, and locks every note that leads. It is a candidate only if the owner relaxes C1 and C3
  for every holder that stakes; a holder outside the active stake shows nothing (M.7).
- **Delegated weight: not recommended against 30 %.** It finalizes in two minutes and hides which
  note delegates, but holds 30 % only while at least 95.24 % of the honest weight is online and the
  coalition's operators hold less than 4.76 % of the honest stake at full uptime, and less at lower
  uptime.

## What the phase leaves open

- Whether C1 and C3 may be relaxed for every holder that stakes. That is the owner's decision, and
  the only route here to finality in minutes that rests on the stake.
- How fast the active stake can grow within one inference period. Against a third the slot rule's
  18 hours hold while the true active stake stays within 1.925 times the inferred, against 30 %
  within 2.627 (M.7).
- How far a coalition can keep honest wins out of a window's record, which the leaders' committee
  assumes it cannot.
- A Blend quota for votes beyond a node's cover, and how much of Blend's transaction share they may
  take.
- A delegation circuit, and what the delegated value reveals on a transparent ledger.
- The public sets' time at 100,000 signers, measured only at 1,000.
- Peras's paper: whether its proofs carry over to Poisson seats and to Blend's delays (D1).
- Verifying a seat's proof on the Raspberry Pi 5.
