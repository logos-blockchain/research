# Faster finality for Cryptarchia

*An exploratory study of how far, and by which means, the time until a Cryptarchia block can be
relied on can be shortened. Every number the study computes comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality); the study's notes there carry the
derivations, gates and full tables. The turnover rates of other chains, Blend's verification
budget and the proving times are read from the sources the notes cite. Specifications are read at
`logos-lips` `47a73cdc`, the node at `logos-blockchain` `4e0405d51`. One slot is one second and
`f = 1/30` unless stated.*

---

## Contents

- **[1. Summary](#s1)** — the routes ranked, and the specification candidates
- **[2. What is measured](#s2)** — finality notions, adversary, delay models, the engine
- **[3. Settlement on the chain](#s3)** — the client rule
- **[4. A smaller `k`, and recovery from a split](#s4)**
- **[5. Block rate, orphans and fork choice](#s5)**
- **[6. Certified finality](#s6)** — anonymous votes
- **[7. The multi-proposer DAG](#s7)** — Areon
- **[8. Findings about the protocol as it stands](#s8)**
- **[9. Open questions](#s9)**
- **[10. Reproducibility](#s10)**

---

<a id="s1"></a>
## 1. Summary

A Cryptarchia block is final once `k = 2160` blocks lie on top of it: 21 hours on the
specification's Blend, and 28 hours while a quarter of the stake withholds its blocks. The study
measures six ways to shorten it, against an adversary holding a share `α` of the stake, under two
delay models: random Blend delays, and a worst case in which an adversary delivers each honest
block as late as a bound `Δ` allows.

Against a quarter of the stake on the specification's Blend (3 hops of up to 3 rounds), with times
on the honest chain while the adversary withholds its blocks:

| route | what changes | time until final | what it costs | what remains open |
| --- | --- | --- | --- | --- |
| settlement rule ([§3](#s3)) | a client depth; nothing in consensus | 18 min at `1e-3` and 68 min at `1e-9` under random delay, 45 min if the rule also reads elapsed time; 6.2 h guaranteed at `Δ = 10` s; with two ground epoch nonces, 2.6 h and 13.7 h | nothing | the adversary's share, the delay model and how far the nonce can be ground are assumptions the client accepts |
| smaller `k` ([§4](#s4)) | `k`, the epoch unless decoupled, and a recovery trigger | in proportion to `k`: 2.8 h at `k = 216`, which holds 32 % of the stake at `1e-9` under random delay and 17–22 % guaranteed at `Δ` = 1–10 s; 25 % and 16–20 % with two ground nonces | a weaker guarantee; less precise stake inference if the epoch shrinks too | a look-back horizon of 34–63 days at Bitcoin's turnover with grinding counted, at `k = 216`'s longest window of 7.2 hours |
| regular block intervals ([§5](#s5)) | the lottery coefficient becomes a curve of the slots since the parent | 12 min instead of 18 at `1e-3` | about a third more blocks; a new stake inference | no worst-case bound; against a third of the stake it settles later |
| faster blocks ([§5](#s5)) | `f` | 48 min at 20 s blocks and 40 min at 15 s, against 59 at 30 s, at `1e-9` on the race under random delay | ×1.56 and ×2.07 the blocks; more forks | no worst-case figure at `f ≠ 1/30` |
| certificates ([§6](#s6)) | anonymous-seat votes through Blend | about 16 min with 10-minute rounds, for the two-round design that finalizes | ×269 Blend cover traffic while every honest seat votes, ×1,582 if a tenth of the votes do not count; votes give an observer even odds of sizing any stake above 0.11 % within an epoch | Blend's budget does not carry the raised cover; rounds stall under a partition or a delay-scheduling adversary |
| multi-proposer DAG ([§7](#s7)) | replaces the chain and its fork choice | 38 min at `1e-9` at Cryptarchia's block rate, against 59 for the chain; 16 min at ×3.2 the blocks | ×1 to ×8.6 emissions | against delays up to 10 s chosen by an adversary, a balancing attack needs only 40–45 % of the stake at Cryptarchia's rate, 21–32 % at ×3.2 the blocks and 3–6 % at ×8.6; no proof covers the DAG below that edge |

Five candidates for specification work follow from the study:

1. **A settled level in the node's API** ([§3](#s3)). A client accepts a block once the depth for
   its chosen `(α, ε)` and delay model lies on top of it, or sooner if it also reads the time the
   blocks took. This needs no consensus change.
2. **Two corrections to the Bootstrap rule** ([§8](#s8)). Its depth test should read the deeper of
   the two branches, and its density window should be sized for `(α, ε)` rather than tied to `k`.
   Both bear on testnet, which runs `k = 120`.
3. **An automatic-recovery trigger** ([§4](#s4)), if `k` is to shrink: a fork deeper than `k` but
   within a horizon is compared by density, with six rules that keep it safe.
4. **A Peras-style certificate** ([§6](#s6)), if the cover budget allows it, if the leak of stake
   through votes is accepted, and if at least nine in ten honest votes count.
5. **Areon at about Cryptarchia's block rate** ([§7](#s7)), with the weight accumulated since the
   fork and each lottery win counted once across both sides of a conflict. Under random delay it
   settles about a third sooner than the chain. A balancing attack against it needs nearly the
   chain's share at that rate, and far less at higher block rates.

---

<a id="s2"></a>
## 2. What is measured

**Three notions of finality** are kept apart:

- **k-finality.** The `k`-deep block, `B_imm` in the specification, is never reorganised (a
  protocol rule).
- **Settlement.** A block at depth `d` is displaced with probability at most `ε` against an
  adversary holding `α`, under a stated delay model (a client rule).
- **Certified finality.** A block is final once a certificate of anonymous votes exists for it (a
  protocol addition).

**The adversary** holds a share `α` of the stake, reported from 5 % to a third. `ε` is per block
for settlement and per round for votes. Results are curves over `α` and `ε`; the summary reads
them at a quarter of the stake and `ε = 1e-9`.

**Two delay models** are reported side by side:

- **Random delay.** Blend's mixing delays, measured in the per-node engine of the total-stake
  inference study (TSI): 1,000 nodes, a degree-6 peering graph, geographic links, and each relay
  holding a message a whole number of rounds as the node's release delayer does. Testnet 0.3.0
  runs 1 hop of 1 round; the specification allows 3 hops of up to 3 rounds. The specification's
  Blend orphans 18 % of blocks and delivers a block to every node within 10.2 s at the 99th
  percentile.
- **Worst case.** An adversary delivers every honest block as late as `Δ` allows. The bounds of
  Gaži, Ren and Russell ("Practical Settlement Bounds for Longest-Chain Consensus", ePrint
  2022/1571, revision 2025-05-02) apply. Their code is ported, checked against their Table 1 and
  against the original run in Octave, and computed at every depth. `Δ = 10` s stands for the
  specification's Blend.

**Times** are counted on the honest chain while the adversary withholds its blocks: one block
every `30 s / ((1 − α) · g)`, where `g` is the canonical growth the engine measures. Against a
quarter of the stake on the specification's Blend that is 47.3 s a block.

---

<a id="s3"></a>
## 3. Settlement on the chain

The depth a client must wait, in canonical blocks, at `ε = 1e-9`:

| adversary | random delay, testnet's Blend | random delay, the specification's | worst case, `Δ` = 1–10 s, proven | worst case, best known attack |
| --- | --- | --- | --- | --- |
| 10 % | 17 | 19 | 75–114 | 31–33 |
| 25 % | 66 | 86 | 288–474 | 110–143 |
| a third | 169 | 269 | 758–1,510 | 278–445 |

Under random delay the depth is that of the private race from the target's parent in closed form,
which the race played on the engine's timelines matches to within three blocks at `1e-3`. Against a
quarter of the stake on the specification's Blend a client waits 68 minutes under random delay and
6.2 hours under the worst case at `Δ = 10` s, against 28 hours for `k`.

- **The proof is not far from the attack.** Where both are computed, the proven depth is 2.4 to 3.6
  times the attack's at delays up to 10 s, and up to 6.6 times at 20 s.
- **The bound describes Cryptarchia's slot lottery.** The attack behind the lower bound, played on
  the 1 s slot lottery, lands within 7 % of the bound computed in continuous time.
- **`k = 2160` holds a third of the stake at `1e-9` only for delays up to 13 s,** before grinding.
- **A rule that also reads elapsed time settles about a third sooner.** A client sees when the
  blocks on top of its target arrived. Against an adversary that forks at the target's parent,
  holds no premined lead and withholds its blocks, the adversary's progress depends only on that
  time. Accepting at the first block where the adversary's exact chance is at most `ε` then holds
  `ε` for every history. Against a quarter of the stake at `1e-9`, on the engine's timelines of the
  specification's Blend, it accepts after 45 minutes on average where the depth rule needs 86
  blocks and 66 minutes. Against a tenth it settles about a fifth sooner. It is derived for random
  delay only.

**Grinding the epoch nonce adds to every depth.** The nonce of the next epoch is fixed by the last
block before a cut-off slot. An adversary that withholds its wins chooses which of them end the
chain there, and so chooses among many leader schedules. Against a quarter of the stake at `1e-9`:

- the 86 blocks of the specification's Blend become 148–167 against an attack that meets one ground
  nonce, and 161–199 against one that meets two;
- the 474 of the worst case at 10 s become 748–840 and 806–988.

A block past its epoch's cut-off, whose race reaches the next epoch, meets two nonces, so the
per-block guarantee needs the second figures. They assume an adversary that evaluates `2^64`
nonces an epoch; from 30 % of the stake that budget sets the choice. With two ground nonces
`k = 2160` no longer holds a third of the stake at any delay; with one, up to 2 s, or 5 s against
an adversary that evaluates `2^40`.

The client accepts these assumptions: the adversary's share, the attack and delay model, how far
the epoch nonce can be ground, and a view that is not eclipsed. The node would expose a third
level, *settled*, beside the tip and `B_imm`.

---

<a id="s4"></a>
## 4. A smaller `k`, and recovery from a split

**What a smaller `k` holds.** The largest adversary each `k` withstands at `ε = 1e-9`, without
and with two ground epoch nonces (`2^64` nonces evaluated an epoch):

| `k` | random delay, the specification's Blend | guaranteed, `Δ` = 1–10 s | random delay, with grinding | guaranteed, with grinding |
| --- | --- | --- | --- | --- |
| 2160 | 0.41 | at least a third | 0.36 | 0.29–0.33 |
| 432 | 0.36 | 0.24–0.29 | 0.29 | 0.21–0.24 |
| 216 | 0.32 | 0.17–0.22 | 0.25 | 0.16–0.20 |
| 120 | 0.28 | 0.11–0.15 | 0.22 | 0.10–0.15 |

**What a smaller `k` breaks.** A split heals by itself only while the losing side has made fewer
than `k` blocks: 35.7 hours for an even split at `k = 2160`, 2 hours at `k = 120`. Past that, a node
on the losing side stays there ([§8](#s8)).

**Automatic recovery** can lift that bound. A fork that diverges deeper than `k` but within a
horizon `H` is compared by its block density in a window after the divergence, the test of the
Bootstrap rule. Six rules make it safe:

1. Evaluate the fork; never switch fork-choice rules. A switch would freeze `B_imm`, and one stale
   winning slot could trigger it.
2. Read the depth of the deeper branch, so that every node holding either chain decides alike.
3. Compare densities only once both chains hold the whole window.
4. Size the window for `(α, ε)` and the horizon. Windows of 1 and 2 hours hold a quarter of the
   stake for less than an hour of history even without grinding. With grinding, 4 hours hold none,
   and 8 hours hold 46–87 days at Bitcoin's turnover.
5. Keep the window within `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake take effect:
   72 hours at `k = 2160`, 7.2 at `k = 216`, 4 at `k = 120`.
6. Bound the horizon `H` against keys that become free (below).

The trigger costs three things. `B_imm` may move back within `H`, so every consumer of it needs a
path for that. The node keeps its block tree and ledger states back to `H`. A split heals only once
the window after its divergence has passed.

**The horizon.** Cryptarchia has no forward security. The key of a note that was eligible at the
divergence and has been spent since can sign for it on the fork, where the note is unspent. A share
`μ(a)` of the stake moves within an age `a`. The table gives the longest horizon, in days, that
keeps the failure over all divergence points at or below `1e-9`. The window is 4 hours, the
specification's Blend under random delay, the adversary obtains every freed key, and the epoch
nonce is not ground:

| turnover per day | α = 0.10 | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.01 % | ≥ 3650 | 1787 | 724 | 5 h | < 1 h |
| 0.03 % | 1320 | 621 | 265 | 5 h | < 1 h |
| 0.05 % | 801 | 380 | 166 | 5 h | < 1 h |
| 0.1 % | 406 | 195 | 87 | 5 h | < 1 h |
| 0.125 % | 327 | 157 | 71 | 5 h | < 1 h |
| 0.243 % | 170 | 83 | 38 | 5 h | < 1 h |
| 0.3 % | 139 | 68 | 32 | 5 h | < 1 h |
| 1 % | 43 | 21 | 10 | 5 h | < 1 h |
| 3 % | 15 | 7 | 4 | 4 h | < 1 h |
| 10 % | 4 | 2 | 29 h | 2 h | < 1 h |

The window caps the horizon whatever the turnover: a 4-hour window holds 30 % of the stake for
only about 5 hours of history, and a third not at all.

Staked value on other chains moves at 0.05–0.3 % a day: Ethereum's exits are capped at 0.13 %, and
Cosmos, Polkadot, Cardano and Solana showed 0.05–0.27 % in single-period scans. Bitcoin's supply,
the closest match to Cryptarchia's notes, moves at 0.13–0.24 % a day over a month to a year. At
Bitcoin's rates the horizon against a quarter of the stake is 38 to 71 days without grinding.

With grinding, a divergence point within one window of its epoch's end meets the nonces of two
epochs. Against a quarter of the stake, a 4-hour window then holds no horizon at any `k`. An 8-hour
window at `k = 2160` holds 46 to 87 days at Bitcoin's turnover, `k = 216`'s 7.2-hour window 34 to
63 days, and `k = 120`'s 4-hour window none. Chains whose stake is never locked protect leader keys
instead: Cardano's evolve every 36 hours, and Algorand erases each round's key. A forward-secure
leader key would free the horizon from turnover altogether.

---

<a id="s5"></a>
## 5. Block rate, orphans and fork choice

- **Faster blocks pay under random delay.** On testnet's Blend, 10 s blocks settle against a
  quarter of the stake in 18 minutes at `1e-9` against 45 at 30 s. On the specification's Blend
  the race keeps gaining at least to 15 s blocks: 59, 48 and 40 minutes at 30, 20 and 15 s. The
  cost is ×1.56 the blocks at 20 s and ×2.07 at 15 s. No worst-case figure is given at
  `f ≠ 1/30`.
- **A fork choice that weighs uncles is no better.** The exact consistency regions of GHOST, the
  fork choice that weighs every block of a subtree (Gaži, Motaqy and Russell, ePrint 2024/1830),
  never exceed the longest-chain rule's at any delay. In proof of stake GHOST also needs control of
  equivocation.
- **A lottery curve of the slots since the parent (Ouroboros Taktikos) does not cut orphans.**
  Under Blend's delays every curve raises the orphan share, to 25–44 % on the specification's
  Blend. A node that has not yet received the latest block sees a larger gap and wins more often.
  A curve that regularises the interval, Topl's published shape or a plain 10-slot gap, settles
  against a quarter of the stake in 12 minutes at `1e-3` instead of 18, at the cost of about a
  third more blocks. Against a third, Topl's shape does not reach `1e-3` within 60 blocks, where
  today's lottery needs 58. The proof of leadership needs no new circuit: its lottery constants
  are public inputs. The stake inference needs a new estimator, and no worst-case bound covers a
  curve.

---

<a id="s6"></a>
## 6. Certified finality

A vote is a private lottery win of a seat, carried through Blend. A certificate needs a quorum `Q`
of `n` expected seats per round. Two conflicting certificates need `h + 2a ≥ 2Q` for `h` honest and
`a` adversarial seats, and a round stalls when the honest seats that count fall short of `Q`.

| adversary | seats at `ε = 1e-9` per round | Blend cover, 90 s rounds | 10 min rounds | 1 h rounds |
| --- | --- | --- | --- | --- |
| 10 % | 665 | ×223 | ×34 | ×7 |
| 25 % | 5,355 | ×1,786 | ×269 | ×46 |
| 30 % | 33,473 | ×11,159 | ×1,675 | ×280 |

Every vote is a Blend emission, so the cover rate must rise by that multiple to keep today's
quota ceiling, below which a node's emission count does not identify it (`reports/blend`).

- **Two designs.** In a Peras-style design (a), a certificate adds weight to its block in fork
  choice; whether Peras's proofs carry over to Poisson seats and to votes delayed by Blend is open.
  A two-round gadget (b) finalizes a block once the next round certifies a descendant.
- **Votes certify quickly once cast.** Voting for the block 60 slots back, every simulated round
  certified within one Blend delivery: 1.6 s on testnet's Blend, 8–9 s on the specification's,
  17–19 s at 3 hops of up to 8 rounds. With 10-minute rounds, design (a) certifies a block about 6
  minutes after publication and design (b) finalizes it after about 16.
- **The committee needs nearly every honest vote.** Safety must count every honest seat, and
  liveness only those that count. Against a quarter of the stake, if a tenth of the honest votes do
  not count the committee grows to 31,617 seats, ×1,582 cover; if a fifth do not, none exists.
- **Blend's budget does not carry the raised cover.** Against a quarter of the stake with
  10-minute rounds, a core connection would carry 41 times what a node reads from it a round, and
  a node would verify 5.3 times what one core of a Raspberry Pi 5 verifies. Sent on top of today's
  cover instead, votes fit only while a committee casts fewer than 1.33 votes a second.
- **Votes on a target 30 slots back never split** under random delay, in 1,368 rounds.
- **A partition stalls finality.** The committee leaves honest seats only 10 % above the quorum at
  a quarter of the stake. Cutting off more than 9 % of the honest stake stalls certificates on
  both sides, while the chain continues.
- **A delay-scheduling adversary splits shallow targets.** It holds two chains and shows each voter
  either. Against a quarter of the stake at `Δ = 10` s, keeping its chance of splitting a round
  below `1e-3` needs a target 45 blocks deep. Under that model a certificate comes no sooner than
  settlement at `1e-3`, and then makes the block final at the round's `ε`.
- **Votes make stake learnable.** A seat is a lottery win, so every vote is a sample of its
  sender's stake: with 10-minute rounds, votes multiply an observer's samples by 269. In the Blend
  report's model of linking, an observer then sizes a 0.1 % holder's stake to ±10 % in 16 days
  instead of 2,179, and has better than even odds of sizing every share above 0.11 % within an
  epoch, against 14 % from blocks alone. Gossiped directly, the same votes size a 0.1 % holder in 3
  hours.
- **An opt-in public committee needs most of the honest stake.** If volunteers vote under their
  identity and the adversary declares all its stake, two thirds of the honest stake must declare
  against a quarter of the stake, 78 % at 95 % uptime. Against 30 %, uptime below 95.2 % breaks it.
  Declared notes must stay in the leader lottery: an adversary that declares nothing would
  otherwise hold half of it against a quarter of the stake.
- **Past certificates need forward security.** Whoever later gathers the keys of past voters can
  forge a past certificate. A per-round key erased after voting, or certificates trusted only
  within a window, would close it.

Proving a vote reuses the node's proof of leadership: 72.5 ms on an Apple M4 Pro, and a holder of
share `s` proves `s·n` times a round. The Raspberry Pi 5 is not measured yet.

---

<a id="s7"></a>
## 7. The multi-proposer DAG

Areon (Castro-Castilla, Pawlowski and Zhou, arXiv 2511.23025) lets several proposers win each slot.
A block references the recent tips its producer has seen within a window of `w` slots, and a fork
choice local to the closest common ancestor compares the weight of competing subDAGs, the parts of
the DAG on either side. Its simulator does not run that fork choice; its figures score a greedy
attack, and its comparison with Praos mixes block rates and metrics (`DAG.md`, E0). The study
builds the honest DAG on the TSI engine instead, with Cryptarchia's per-note lottery at a
production coefficient `f_A` and Blend's delays, and attacks it with the same private race as the
chain.

The paper leaves the weight open, and the reading decides the outcome:

- **Counted since the fork,** each block once, each lottery win once: the DAG settles.
- **Counted over the last `w` slots only,** as the paper's prose says: no depth settles. A
  coalition that keeps its private subDAG alive outweighs the honest side in some window.

With the first reading, against a quarter of the stake on the specification's Blend, from the
race's success fitted and extrapolated to `1e-9` as the paper's §5.6 does for both structures:

| production | blocks per slot, relative to today | settled at `1e-3` | settled at `1e-9` |
| --- | --- | --- | --- |
| the chain, `f = 1/30` | ×1 | 18 min | 59 min |
| the DAG, `f_A = 1/30` | ×1 | 12 min | 38 min |
| the DAG, `f_A = 0.1` | ×3.2 | 4.9 min | 16 min |
| the DAG, `f_A = 0.25` | ×8.6 | 2.1 min | 6 min |

- **No honest block is wasted.** Every honest block counts, wherever it sits; the chain discards its
  orphans. At the same block rate the DAG settles about a third sooner. The fit falls 3–5 % short
  of the exact depth when applied to the chain's race in closed form.
- **Raising the block rate pays more on the DAG.** The chain at 20 and 15 s blocks settles in 48
  and 40 minutes at `1e-9`, the DAG at ×3.2 the blocks in 16. The price is emissions: every block
  is a lottery win and a Blend emission.
- **At Cryptarchia's rate a uniform delay costs time, not rate.** When every honest block arrives
  exactly `Δ` late, the time to settle against a quarter of the stake stays at 12–13 minutes for
  `Δ` from 1 to 20 s. At `f_A = 0.25` the window must exceed `Δ` by several block intervals, more
  than the paper's `w ≥ Δ`.
- **A depth in layers holds only at the delay it was set for.** A wider DAG needs fewer layers, so
  a depth must be set at the shortest delay, or count weight or time instead.
- **A scheduled delay is the DAG's weakness.** Weighing every honest block of a subDAG is what
  GHOST does with a subtree, and its tight balancing attacks apply. An adversary that holds each
  honest block back until the next one appears keeps two conflicting subDAGs at equal weight, and
  nothing settles while it does. Against delays of up to 10 s, the attack needs 40–45 % of the
  stake at Cryptarchia's block rate, against the chain's 46 %; 21–32 % at `f_A = 0.1`; and 3–6 % at
  `f_A = 0.25`, where with 10 % three attempts in four hold the balance for a day. No proof covers
  the DAG below that edge.
- **One win must weigh once, across both sides.** A lottery ticket that does not depend on the
  parent can sign blocks in one subDAG or in both of two conflicting ones. Each win carries a tag,
  `ρ_LEAD`, fixed per note and slot. The weight must count each tag once, and a tag found on both
  sides must weigh on neither; without that, GHOST-like weights provide no security at all.
- **The window must span the block interval.** At `f_A = 1/30`, the paper's 30-slot window leaves
  36–56 % of the honest blocks without a reference inside it, and so without weight.
- **The ledger needs a rule.** Honest blocks must reference only the side their fork choice
  prefers, so that a defeated subDAG is never merged into honest history. The total order must skip
  transactions that conflict with earlier ones, and must not place a late block before blocks
  already settled.

---

<a id="s8"></a>
## 8. Findings about the protocol as it stands

- **A restart does not heal a split deeper than `k`.** The bootstrap specification's key invariant
  forbids reorganising below `B_imm`, and the node prunes every block below it. A restart keeps
  both, so `--bootstrap` alone leaves a node on the losing side. Only a re-sync from genesis or from
  a checkpoint returns it; the node implements the first, and checkpoints are specified but not
  implemented.
- **Testnet's Bootstrap window is too short.** The density window `s_gen = ⌊k/4f⌋` is 15 minutes at
  `k = 120`. An adversary holding a quarter of the stake wins about one such window in 460 on
  testnet's Blend. A node that syncs from genesis compares forks at every block of the history, so
  over a month of history that adversary finds such a window with probability 0.998.
- **The Bootstrap rule's depth test can split the network after a split.** It reads the depth of the
  node's own branch. When one side of a split has passed `k` blocks and the other has not, nodes on
  the short side follow the longer chain while nodes on the long side follow the denser one, and
  they alternate until both sides pass `k`.
- **The epoch nonce can be ground** ([§3](#s3)). The nonce is the hash chain at the last block
  before a cut-off slot, so an adversary that withholds its wins chooses among the chains it can
  end there.
- **The bound's reference code needs more phases at depth.** LCanalysis follows its lower-bound
  attack for 80 phases, too few past its Table 1's depths. At a third of the stake, `Δ = 1` s and
  depth 60 the bound falls from `6.9e-3` to `5.5e-12` in the port at 30 states; the original code,
  run in Octave, falls to `5.4e-13` at its 19 states. It also scores the attack only at the moment
  of confirmation; scored at any later moment, the same attack succeeds 2–17 % more often.

---

<a id="s9"></a>
## 9. Open questions

- **The emission budget.** Votes and the DAG both pay in Blend cover traffic. Which multiple is
  acceptable is a budget decision, not a measurement.
- **Turnover in Cryptarchia itself.** The recovery horizon rests on how fast staked notes are spent,
  measured elsewhere at 0.05–0.3 % a day, and on how many of their old keys an adversary could buy.
  [§4](#s4) gives the horizon against turnover when every freed key is bought;
  `SETTLEMENT.md` (B5) also when a tenth is.
- **The grinding budget and its compounding.** From 30 % of the stake, the depths and the recovery
  horizon depend on how many nonces an adversary can evaluate before it must publish its chain. The
  study assumes `2^64` and shows `2^40`. It also draws each epoch's schedule as if no one chose it,
  while an earlier grinding may have; with that counted, large choices at the next cut-off become
  more likely.
- **Peras's proofs** for Poisson seat counts and for votes delayed by Blend (design (a)).
- **A safety proof for the DAG** below the balancing attack's edge.
- **Proving on the reference node.** The proving time on a Raspberry Pi 5, which
  `tools/benchmarks/pol-proving` measures.

---

<a id="s10"></a>
## 10. Reproducibility

```
cd tools/simulators/finality
make install          # a virtualenv with the TSI engine and the study's package
make test             # every gate
make mutations        # each gate fails on its registered mutation
make all              # every run; the settlement bounds and the grinding take about 20 minutes each on 14 cores
make tables           # every table of the notes, from runs/
make check-tables     # each table appears verbatim in a note
make octave-reference # the original LCanalysis in Octave, in the background, for hours
```

Proving is timed apart, on the machine at hand: `make run` in
[`tools/benchmarks/pol-proving`](../../tools/benchmarks/pol-proving) writes to
[`pol-proving/`](pol-proving).

The notes carry each result with its gate: `MAPPING.md` (what depends on `k`), `RATE.md` (block
rate and orphans), `SETTLEMENT.md` (bounds, races, a smaller `k`, recovery, grinding),
`CERTIFIED.md` (votes) and `DAG.md` (Areon). `PLAN.md` records the questions the study was asked to
answer, its hypotheses and the verdict on each.
