# Faster finality for Cryptarchia

*An exploratory study of how far, and by which means, the time until a Cryptarchia block can be
relied on can be shortened. Every number comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality); the study's notes there carry the
derivations, gates and full tables. Specifications are read at `logos-lips` `47a73cdc`, the node at
`logos-blockchain` `4e0405d51`. One slot is one second and `f = 1/30` unless stated.*

---

## Contents

- **[1. Summary](#s1)** — the routes ranked, and the specification candidates
- **[2. What is measured](#s2)** — finality notions, adversary, delay models, the engine
- **[3. Settlement on the chain](#s3)** — the client rule (L1)
- **[4. A smaller `k`, and recovery from a split](#s4)** — L2
- **[5. Block rate, orphans and fork choice](#s5)** — L3, L4
- **[6. Certified finality](#s6)** — anonymous votes (L5)
- **[7. The multi-proposer DAG](#s7)** — Areon (L6)
- **[8. Findings about the protocol as it stands](#s8)**
- **[9. Open questions](#s9)**
- **[10. Reproducibility](#s10)**

---

<a id="s1"></a>
## 1. Summary

A Cryptarchia block is final once `k = 2160` blocks lie on top of it. At `f = 1/30` that takes 18 to
21 hours. The study measures six ways to shorten it, against an adversary holding a share `α` of
the stake, under two delay models: random Blend delays and a worst case in which an adversary
delivers each honest block as late as a bound `Δ` allows.

Against a quarter of the stake on the specification's Blend (3 hops of up to 3 rounds):

| route | what changes | time until final | what it costs | what remains open |
| --- | --- | --- | --- | --- |
| settlement rule ([§3](#s3)) | a client depth; nothing in consensus | 18 min at `1e-3`, 59 min at `1e-9` under random delay, about a third less if the rule also reads elapsed time; 4.6 h guaranteed at `Δ = 10` s; 1.8 h and 7.7 h once grinding of the epoch nonce is counted | nothing | the adversary's share, the delay model and how far the nonce can be ground are assumptions the client accepts |
| smaller `k` ([§4](#s4)) | `k`, the epoch unless decoupled, and a recovery trigger | in proportion to `k`: 1.8–2.1 h at `k = 216`, which holds 32 % of the stake at `1e-9` under random delay and 17–22 % guaranteed; 27 % and 16–21 % once grinding is counted | a weaker guarantee; less precise stake inference if the epoch shrinks too | a look-back horizon of 57–108 days at Bitcoin-like turnover, with an 8-hour window and grinding counted |
| regular block intervals ([§5](#s5)) | the lottery coefficient becomes a curve of the slots since the parent | 12 min instead of 18 at `1e-3` | 30 % more blocks; a new stake inference | no worst-case bound |
| faster blocks ([§5](#s5)) | `f` | best at 15–20 s blocks: 46–48 min at `1e-9` against 51 | more forks | — |
| certificates ([§6](#s6)) | anonymous-seat votes through Blend | about 6 min with 10-minute rounds | ×269 Blend cover traffic; votes give an observer even odds of sizing any stake above 0.1 % within an epoch | rounds stall under a partition or a delay-scheduling adversary |
| multi-proposer DAG ([§7](#s7)) | replaces the chain and its fork choice | 38 min at `1e-9` at today's block rate; 15 min at ×3.2 the blocks | ×1 to ×8.6 emissions | against an adversary that schedules delays up to 10 s, safe against 40–45 % of the stake at today's rate, but only 3–6 % at ×8.6 the blocks |

Five candidates for specification work follow from the study:

1. **A settled level in the node's API** ([§3](#s3)). A client accepts a block once the depth for
   its chosen `(α, ε)` and delay model lies on top of it, or sooner if it also reads the time the
   blocks took. This needs no consensus change.
2. **Two corrections to the Bootstrap rule** ([§8](#s8)). Its depth test should read the deeper of
   the two branches, and its density window should be sized for `(α, ε)` rather than tied to `k`.
   Both bear on testnet today, which runs `k = 120`.
3. **An automatic-recovery trigger** ([§4](#s4)), if `k` is to shrink: a fork deeper than `k` but
   within a horizon is compared by density, with six rules that keep it safe.
4. **A Peras-style certificate** ([§6](#s6)), if the cover budget allows.
5. **Areon at about today's block rate** ([§7](#s7)), with the weight accumulated since the fork
   and each lottery win counted once across both sides of a conflict. It settles a third sooner
   than the chain and keeps nearly the chain's worst-case region; at higher block rates that region
   collapses.

---

<a id="s2"></a>
## 2. What is measured

**Three notions of finality** are kept apart:

- **k-finality.** The `k`-deep block `B_imm` is never reorganised (a protocol rule).
- **Settlement.** A block at depth `d` is displaced with probability at most `ε` against an
  adversary holding `α`, under a stated delay model (a client rule).
- **Certified finality.** A block is final once a certificate of anonymous votes exists for it (a
  protocol addition).

**The adversary** holds a share `α` of the stake, reported from 5 % to a third. `ε` is per block
for settlement and per round for votes. No headline pair is chosen; every result is a curve over
`α` and `ε`.

**Two delay models** are reported side by side:

- **Random delay.** Blend's mixing delays, measured in the TSI per-node engine: 1,000 nodes, a
  degree-6 peering graph, geographic links, and each relay holding a message a whole number of
  rounds as the node's release delayer does. Testnet 0.3.0 runs 1 hop of 1 round; the
  specification allows 3 hops of up to 3 rounds. The specification's Blend orphans 18 % of blocks
  and delivers a block to every node within 10 s at the 99th percentile.
- **Worst case.** An adversary delivers every honest block as late as `Δ` allows. The bounds of
  Gaži, Ren and Russell ("Practical Settlement Bounds for Longest-Chain Consensus", ePrint
  2022/1571, revision 2025-05-02) apply. Their code is ported and checked against their Table 1
  and against the original run in Octave.

---

<a id="s3"></a>
## 3. Settlement on the chain

The depth a client must wait, in canonical blocks, at `ε = 1e-9`:

| adversary | random delay, testnet's Blend | random delay, the specification's | worst case, `Δ` = 1–10 s, proven | worst case, best known attack |
| --- | --- | --- | --- | --- |
| 10 % | 16 | 18 | 74–114 | 31–34 |
| 25 % | 67 | 77 | 285–469 | 111–143 |
| a third | 152 | 188 | 728–1,420 | 278–446 |

The random-delay depths extrapolate a race measured to about `1e-4` on the engine's own timelines,
with the fit of the Areon paper's §5.6. In time, on the specification's Blend, a quarter of the
stake is settled against in 59 minutes under random delay and in 4.6 hours under the worst case at
`Δ = 10` s, against 18 to 21 hours for `k`.

- **The proof is not far from the attack.** The worst-case bounds lie within a factor of 2.4 to 3.3
  of each other in depth.
- **The bound describes Cryptarchia's slot lottery.** The attack behind the lower bound, played on
  the 1 s slot lottery, lands within 7 % of the bound computed in continuous time.
- **`k = 2160` holds a third of the stake at `1e-9` only for delays up to about 14 s.**
- **A rule that also reads elapsed time settles about a third sooner.** A client sees when the
  blocks on top of its target arrived, and the attacker's progress depends only on that time.
  Accepting at the first block where the attacker's exact chance is at most `ε` holds `ε` for
  every history. Against a quarter of the stake at `1e-9`, on the engine's timelines of the
  specification's Blend, it accepts after 45 minutes on average where the same model's depth
  rule needs 88 blocks and 68 minutes.

**Grinding the epoch nonce adds to every depth.** A coalition that withholds its wins chooses
which of them end the chain at the cut-off that fixes the next epoch's nonce, and so chooses among
many schedules. Against a quarter of the stake at `1e-9`, the 77 blocks of the specification's
Blend become 130–138, and the 469 of the worst case at 10 s become 741–785. That assumes a
coalition that can evaluate `2^64` nonces an epoch. From 30 % of the stake only that budget bounds
the choice. Once grinding is counted, `k = 2160` holds a third of the stake only up to about 7 s
against a coalition that evaluates `2^40` nonces an epoch, and below 4 s against `2^64`.

The rule a client accepts (B4 in `SETTLEMENT.md`) assumes the adversary's share, the delay model,
how far the epoch nonce can be ground, and a view that is not eclipsed. The node would expose a
third level, *settled*, beside the tip and `B_imm`.

---

<a id="s4"></a>
## 4. A smaller `k`, and recovery from a split

**What a smaller `k` holds.** The largest adversary each `k` withstands at `ε = 1e-9`, without
and with grinding of the epoch nonce (`2^64` nonces evaluated an epoch):

| `k` | random delay, the specification's Blend | guaranteed, `Δ` = 1–10 s | random delay, with grinding | guaranteed, with grinding |
| --- | --- | --- | --- | --- |
| 2160 | 0.41 | at least a third | 0.38 | 0.30 to at least a third |
| 432 | 0.36 | 0.24–0.29 | 0.30 | 0.22–0.25 |
| 216 | 0.32 | 0.17–0.22 | 0.27 | 0.16–0.21 |
| 120 | 0.28 | 0.11–0.15 | 0.24 | 0.10–0.15 |

**What a smaller `k` breaks.** A split heals by itself only while the losing side has made fewer
than `k` blocks: 35.7 hours for an even split at `k = 2160`, 2 hours at `k = 120`. Past that, a node
on the losing side stays there. Neither fork-choice rule reorganises below `B_imm`, and a restart
keeps it, so only a re-sync from genesis or a checkpoint returns the node ([§8](#s8)).

**Automatic recovery** can lift that bound. A fork that diverges deeper than `k` but within a
horizon `H` is compared by its block density in a window after the divergence, the test of the
Bootstrap rule. Six rules make it safe:

1. Evaluate the fork; never switch fork-choice rules. A switch would freeze `B_imm`, and one stale
   winning slot could trigger it.
2. Read the depth of the deeper branch, so that every node holding either chain decides alike.
3. Compare densities only once both chains hold the whole window.
4. Size the window for `(α, ε)`: about 1.7 hours holds a quarter of the stake at `1e-9` per window
   on the specification's Blend, 4.9 hours a third. Grinding lengthens it: against a quarter of
   the stake, 4 hours no longer suffices and 8 hours does.
5. Keep the window within `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake take effect.
6. Bound the horizon `H` against keys that become free (below).

**The horizon.** Cryptarchia has no forward security. The key of a note that was eligible at the
divergence and has been spent since can sign for it on the fork, where the note is unspent. A share
`μ(a)` of the stake moves within an age `a`. The table gives the longest horizon, in days, that
keeps the failure over all divergence points at or below `1e-9`. The window is 4 hours, the
specification's Blend, the adversary obtains every freed key, and the epoch nonce is not ground:

| turnover per day | α = 0.10 | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.01 % | ≥ 3650 | 1787 | 724 | 5 h | < 1 h |
| 0.03 % | 1320 | 621 | 265 | 5 h | < 1 h |
| 0.05 % | 801 | 380 | 166 | 5 h | < 1 h |
| 0.1 % | 406 | 195 | 87 | 5 h | < 1 h |
| 0.125 % | 327 | 157 | 71 | 5 h | < 1 h |
| 0.243 % | 170 | 83 | 38 | 5 h | < 1 h |
| 0.3 % | 139 | 68 | 32 | 5 h | < 1 h |
| 1 % | 43 | 21 | 10 | 4 h | < 1 h |
| 3 % | 15 | 7 | 4 | 3 h | < 1 h |
| 10 % | 4 | 2 | 29 h | 2 h | < 1 h |

The window caps the horizon whatever the turnover: a 4-hour window holds 30 % of the stake for
only about 5 hours of history, and a third not at all. A longer window lifts the cap, within the
bound of rule 5.

Staked value on other chains moves at 0.05–0.3 % a day: Ethereum's exits are capped at 0.13 %, and
Cosmos, Polkadot, Cardano and Solana showed 0.05–0.27 % in single-period scans. Bitcoin's supply,
the closest match to Cryptarchia's notes, moves at 0.13–0.24 % a day over a month to a year. At
Bitcoin's rates the horizon against a quarter of the stake is 38 to 71 days. Once grinding of the
epoch nonce is counted, a 4-hour window holds a quarter of the stake for only 3 to 5 days, and an
8-hour window for 57 to 108 days. Ethereum's weak
subjectivity period, set by its exit cap, is 15.7 days. Chains whose stake is never locked protect
leader keys instead: Cardano's evolve every 36 hours, and Algorand erases each round's key. A
forward-secure leader key would free the horizon from turnover altogether.

---

<a id="s5"></a>
## 5. Block rate, orphans and fork choice

- **Faster blocks pay only while the delay is short.** On testnet's Blend, 10 s blocks settle
  against a quarter of the stake in 13 minutes at `1e-9` against 34 at 30 s. On the specification's
  Blend the best interval is 15–20 s, at 46–48 minutes against 51.
- **A fork choice that weighs uncles is no better.** The exact consistency regions of GHOST
  (Gaži, Motaqy and Russell, ePrint 2024/1830) never exceed the longest-chain rule's at any delay,
  and in proof of stake GHOST also needs control of equivocation.
- **A lottery curve of the slots since the parent (Ouroboros Taktikos) does not cut orphans.**
  Under Blend's delays every curve raises the orphan share, to 25–44 % on the specification's
  Blend. A node that has not yet received the latest block sees a larger gap and wins more often.
  A curve that regularises the interval, Topl's shape or a plain 10-slot gap, settles against a
  quarter of the stake in 12 minutes at `1e-3` instead of 18, by making 30 % more blocks. The
  proof of leadership needs no new circuit: its lottery constants are public inputs. The stake
  inference needs a new estimator, and no worst-case bound covers a curve.

---

<a id="s6"></a>
## 6. Certified finality

A vote is a private lottery win of a seat, carried through Blend. A certificate needs a quorum `Q`
of `n` expected seats per round. Two conflicting certificates need `H + 2A ≥ 2Q`, and a round
stalls when the honest seats fall short of `Q`.

| adversary | seats at `ε = 1e-9` per round | Blend cover, 90 s rounds | 10 min rounds | 1 h rounds |
| --- | --- | --- | --- | --- |
| 10 % | 665 | ×223 | ×34 | ×7 |
| 25 % | 5,355 | ×1,786 | ×269 | ×46 |
| 30 % | 33,473 | ×11,159 | ×1,675 | ×280 |

Every vote is a Blend emission, so the cover rate must rise by that multiple to keep today's
anonymity ceiling.

- **Votes certify quickly once cast.** Voting for the block 60 slots back, every simulated round
  certified within one Blend delivery: 1.6 s on testnet's Blend, 8–9 s on the specification's,
  17–19 s at 3 hops of up to 8 rounds. A block is certified about 6 minutes after publication with
  10-minute rounds, and about 2 minutes with 90 s rounds.
- **Votes on a target 30 slots back never split** under random delay, in 1,368 rounds.
- **A partition stalls finality.** The committee leaves honest seats only 10 % above the quorum at
  a quarter of the stake. Cutting off more than 9 % of the honest stake stalls certificates on
  both sides, while the chain continues.
- **A delay-scheduling adversary splits shallow targets.** It holds two chains and shows each voter
  either. Against a quarter of the stake at `Δ = 10` s, keeping its chance of splitting a round
  below `1e-3` needs a target 45 blocks deep. Under that model a certificate comes no sooner than
  settlement at `1e-3`, and then makes the block final at the round's `ε`.
- **Verification fits the node.** One core of a Raspberry Pi 5 verifies 157 Blend headers a second,
  each an Ed25519 signature and a Groth16 proof (`blend-protocol.md`). Against a quarter of the
  stake, votes then take 6 % of a core with 10-minute rounds and 38 % with 90 s rounds. Proving on
  the Pi 5 awaits a run of `tools/benchmarks/pol-proving`; an Apple M4 Pro proves in 72.5 ms.
- **Votes make stake learnable.** A seat is a lottery win, so every vote is a sample of its
  sender's stake: with 10-minute rounds, votes multiply an observer's samples by 269. In the Blend
  report's model of linking, an observer then sizes a 0.1 % holder's stake to ±10 % in 16 days
  instead of 4,340, and has better than even odds of sizing every share above 0.1 % within an
  epoch, against 26 % from blocks alone. Gossiped directly, the same votes size a 0.1 % holder in
  3 hours.
- **An opt-in public committee needs most of the honest stake.** If volunteers vote under their
  identity and the adversary declares all its stake, two thirds of the honest stake must declare
  against a quarter of the stake, 78 % at 95 % uptime; from 30 % any downtime breaks it. Holders
  who stay private then cast no vote, so the leak above does not reach them.
- **Forward security matters more for votes.** Without it, whoever later gathers the keys of past
  voters can forge a past certificate. A per-round key erased after voting, or certificates trusted
  only within a window, would close it.

---

<a id="s7"></a>
## 7. The multi-proposer DAG

Areon (Castro-Castilla, Pawlowski and Zhou, arXiv 2511.23025) lets several proposers win each slot.
A block references the recent tips, and a fork choice local to the closest common ancestor compares
the weight of competing subDAGs. Its simulator does not run that fork choice. Areon-Base was
therefore built on the TSI engine, with Cryptarchia's per-note lottery and Blend's delays, and
attacked by the same private race as the chain.

The paper leaves the weight open, and the reading decides the outcome:

- **Counted since the fork,** each block once, each lottery win once: the DAG settles.
- **Counted over the last `w` slots only,** as the paper's prose says: no depth settles. A
  coalition that keeps its private subDAG alive eventually outweighs the honest side in some
  window.

With the first reading, against a quarter of the stake on the specification's Blend:

| production | blocks per slot, relative to today | settled at `1e-3` | settled at `1e-9` |
| --- | --- | --- | --- |
| the chain, `f = 1/30` | ×1 | 18 min | 59 min |
| the DAG, `f_A = 1/30` | ×1 | 12 min | 38 min |
| the DAG, `f_A = 0.1` | ×3.2 | 4.6 min | 15 min |
| the DAG, `f_A = 0.25` | ×8.6 | 1.9 min | 6 min |

- **No honest block is wasted.** Every honest block counts, wherever it sits; the chain discards its
  orphans. At the same block rate the DAG settles about a third sooner.
- **Raising the block rate keeps paying,** where the chain stops gaining at 15–20 s blocks. The
  price is emissions: every block is a lottery win and a Blend emission.
- **A uniform delay costs a lag, not a rate.** When every honest block arrives exactly `Δ` late,
  the time to settle against a quarter of the stake stays at 11–13 minutes for `Δ` from 1 to 20 s
  at today's block rate.
- **A scheduled delay is another matter.** Weighing every honest block of a subDAG is what GHOST
  does with a subtree, and its tight balancing attacks (Gaži, Motaqy and Russell, ePrint 2024/1830)
  apply. An adversary that holds each honest block back until the next one appears keeps two
  conflicting subDAGs at equal weight, and nothing settles while it does. Against delays of up to
  10 s, the share it needs is 40–45 % at today's block rate, against the chain's 46 %. At
  `f_A = 0.25` it needs 3–6 %, and with 10 % three attempts in four hold the balance for a day.
- **One win must weigh once, across both sides.** A ticket that does not depend on the parent can
  sign blocks in one subDAG or in both of two conflicting ones. The weight must count each
  `ρ_LEAD` once, and a tag found on both sides must weigh on neither; without that, GHOST-like
  weights provide no security at all.
- **The window must span the block interval.** At `f_A = 1/30`, the paper's 30-slot window leaves
  36–56 % of the honest blocks with only a long reference, and so without weight.
- **The ledger needs a rule.** Honest blocks must reference only their preferred frontier, so that a
  defeated subDAG is never merged into honest history, and the total order must skip transactions
  that conflict with earlier ones.

---

<a id="s8"></a>
## 8. Findings about the protocol as it stands

- **A restart does not heal a split deeper than `k`.** The bootstrap specification's key invariant
  forbids reorganising below `B_imm`, and the node prunes every block below its LIB. A restart keeps
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
- **The epoch nonce can be ground.** The nonce is the hash chain at the last block before a
  cut-off slot, so a coalition that withholds its wins chooses among the chains it can end there.
  Against a quarter of the stake at `1e-9`, the settlement depths must grow by 53–61 blocks under
  random delay on the specification's Blend and by 272–316 under the worst case at 10 s. From 30 %
  only the coalition's computation bounds the choice.
- **The bound's reference code needs more phases at depth.** LCanalysis follows its lower-bound
  attack for 80 phases, too few past its Table 1's depths. At a third of the stake and depth 60 the
  bound falls from `6.8e-3` to `5e-12`; the original code, run in Octave, does the same. It also
  scores the attack only at the moment of confirmation; scored at any later moment, the same
  attack succeeds 2–17 % more often.

---

<a id="s9"></a>
## 9. Open questions

- **The emission budget.** Votes and the DAG both pay in Blend cover traffic. Which multiple is
  acceptable is a budget decision, not a measurement.
- **Turnover in Cryptarchia itself.** The recovery horizon rests on how fast staked notes are spent,
  measured elsewhere at 0.05–0.3 % a day, and on how many of their old keys an adversary could buy.
  [§4](#s4) gives the horizon as a function of both.
- **Proving on the reference node.** `tools/benchmarks/pol-proving` times the node's proof of
  leadership, which a vote would reuse; it has not been run on a Raspberry Pi 5.
- **The grinding budget.** From 30 % of the stake, the depths and the recovery horizon depend on
  how many nonces a coalition can evaluate before it must publish its chain. The study assumes
  `2^64` and shows `2^40` where it matters. The time the honest chain leaves it is not modelled.

---

<a id="s10"></a>
## 10. Reproducibility

```
cd tools/simulators/finality
make install          # a virtualenv with the TSI engine and the study's package
make test             # every gate
make mutations        # each gate fails on its registered mutation
make all              # every run; the settlement bounds take about an hour on 14 cores
make tables           # every table of the notes, from runs/
make check-tables     # each table appears verbatim in a note
make octave-reference # the original LCanalysis in Octave, in the background, for hours
```

Proving is timed apart, on the machine at hand: `make run` in
[`tools/benchmarks/pol-proving`](../../tools/benchmarks/pol-proving) writes to
[`pol-proving/`](pol-proving).

The notes carry each result with its gate: `MAPPING.md` (what depends on `k`), `RATE.md` (block
rate and orphans), `SETTLEMENT.md` (bounds, races, a smaller `k`, recovery), `CERTIFIED.md` (votes)
and `DAG.md` (Areon). `PLAN.md` records the questions the study was asked to answer and the
verdict on each hypothesis.
