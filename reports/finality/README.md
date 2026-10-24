# Faster finality for Cryptarchia

*This study asks how much sooner a Cryptarchia block can be relied on, and by which means, against
an adversary holding at most a third of the stake. It counts finality in slots: a block is final
once `K` slots have passed since its slot ([§2](#s2); `SLOTS.md`). The specification counts
`k = 2160` blocks, and the figures in blocks stand beside the slot ones where they differ. Every
number the study computes comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality); the study's notes there carry the
derivations, gates and full tables. The turnover rates of other chains, Blend's verification
budget, the proving times and Ouroboros Phalanx's parameters are read from the sources the notes
cite. Specifications are read at `logos-lips` `47a73cdc`, the node at `logos-blockchain`
`4e0405d51`. One slot is one second and `f = 1/30` unless stated.*

---

## Contents

- **[1. Summary](#s1)** — finality counted in slots: what `K` must be, what it changes, and every route against 30 % and a third
- **[2. What is measured](#s2)** — finality notions in slots, adversary, delay models, the engine
- **[3. The three routes in depth](#s3)** — the nonce, a settled level, finality counted in slots with a floor
- **[4. Settlement on the chain](#s4)** — the client rule
- **[5. The epoch nonce](#s5)** — grinding, and two ways to stop it
- **[6. The window `K`, and recovery from a split](#s6)** — what each `K` holds, eclipses, splits and the floor
- **[7. Block rate, orphans and fork choice](#s7)**
- **[8. Certified finality](#s8)** — anonymous votes
- **[9. The multi-proposer DAG](#s9)** — Areon
- **[10. Findings about the protocol as it stands](#s10)**
- **[11. Open questions](#s11)**
- **[12. Further routes](#s12)** — a delayed nonce, the epoch apart from `k`, Blend's delay, density, anchoring, the inference, adversarial relays, a fork choice that tolerates delay
- **[13. Three designs](#s13)** — recovery in a partition, the delay function, time under the worst case
- **[14. Reproducibility](#s14)**
- **[The epoch nonce, the lottery and the length of finality](grinding.md)** — a review of the approaches to grinding and what each leaves of the depth

---

<a id="s1"></a>
## 1. Summary

Counted in slots, a Cryptarchia block is final once `K` slots have passed since its slot. `B_imm`
is the latest block that old, and no fork that diverges before it is followed. Finality is then a
fixed time. Counted in blocks, as the specification counts it, `k = 2160` blocks take 21 hours on
its Blend and 30 to 33 hours while 30 % to a third of the stake withholds its blocks. The study
reads every route under the slot rule ([§2](#s2); `SLOTS.md`). It reads them against an adversary
holding a share `α` of the stake, 30 % and a third, at a failure probability `ε = 1e-9` per block,
under two delay models: random Blend delays on the specification's Blend (3 hops of up to 3
rounds), and a worst case in which an adversary delivers each honest block as late as a bound `Δ`
allows, taken at `Δ = 10` s, that Blend's 99th-percentile delay. Random-delay figures are the
private attack's with honest relays, read at a convention that covers it ([§2](#s2)); worst-case
figures are proven against every attack.

**What `K` must be.** A wait does not stretch while the adversary withholds, so `K` must hold while
the honest chain grows from the honest stake alone, and under the worst case one block per
`Δ + 1/p_h` slots. It must also cover the runs in which those blocks come late. The bound of Gaži,
Ren and Russell keeps everything up to a slot once their margin stays negative, so their chain
bounds a wait directly, frozen at the phase in which the wait passes and run on the 1 s slot
lottery. Against a third at 10 s the wait that holds `ε` is 10.1 hours, where the 1,510 blocks of
their depth bound take 23.0 on that clock ([§4](#s4)). With the nonce of route 1 it is 10.2 hours,
and 12.5 after a period of withholding has deflated the inferred stake ([§6](#s6)):

| `K` | hours | against 30 % at 10 s | against a third at 10 s |
| --- | --- | --- | --- |
| the least that holds a third with the nonce of route 1, a deflated inference included | 12.5 | holds | holds |
| `⌊k/f⌋` = 64,800 slots, the time 2,160 blocks take at the full rate | 18 | holds, with a grinding factor of 1.1e18 to spare | holds, with a factor of 8.4e6 to spare; not with today's nonce, which needs 26 to 42 hours |
| `s = 3⌊k/f⌋` = 194,400 slots, the specification's own slot parameter | 54 | holds, also with today's nonce | holds, also with today's nonce |

`K = ⌊k/f⌋`, 18 hours, is recommended, with the nonce of route 1 and a floor in its depth form
([§3.3](#s33)).

**What counting in slots changes in kind.**

- **Without a floor, an eclipse or a split fixes a fork after `K` slots, whatever its stake.** A
  node fixes its chain once a block the rest of the network lacks is `K` slots old, a block it made
  itself included. Counted in blocks the fork first needs 2,160 blocks: 2.2 days for a third of
  the stake and up to 8.2 days for the smallest. A density floor restores the protection: `B_imm`
  passes a block only once `φ` blocks follow it, or once the `K` slots after it hold `φ` blocks.
  At 54 hours the floor against a third is 3,264 blocks, more than 2,160, and a chain nobody
  withholds from falls below it with chance below `1e-99` ([§6](#s6)).
- **A floor is a quorum, and it separates partitions only below a third.** The adversary signs on
  both sides of a partition. The floor must then lie above what a side of `(1 + α)/2` of the stake
  makes and below what the honest chain makes while the adversary withholds. At a third the two
  are equal, and no window separates the sides. Counted as the stake inference counts, on occupied
  slots with the uncles the chain references, the honest chain keeps the wins it loses to orphans:
  under random delay a floor separates a quarter from 2.2 days and 30 % from 14 days. Counted on
  blocks it takes 516 days against a quarter, and under the worst case at 10 s no window exists
  on either count ([§3.3](#s33), [§6](#s6), [§13](#s13)).
- **Three findings in blocks disappear or shrink.** Both branches of a fork have one divergence
  age, so the Bootstrap rule can no longer split the nodes after a split ([§10](#s10)). A race
  lasts at most `K`, so every target stays inside the grinding bound while `K` is at most 72 hours
  ([§5](#s5)). A deflated inference lengthens the guaranteed wait against a third by 23 %, where it
  lengthened the proven depth by 61 % ([§12](#s12)).
- **The block rate no longer sets finality's time, and a faster one needs a longer `K`.** Against
  a third at 10 s the wait grows from 10.1 hours at 30 s blocks to 12.5 at 20 s and 20.4 at 15 s
  ([§7](#s7)).

| route | what changes | time until final in slots, 30 % / a third | what it costs | verdict |
| --- | --- | --- | --- | --- |
| a nonce that resists grinding ([§5](#s5)) | the epoch nonce taken from the smallest contributions of 25 sub-windows and passed through a sequential delay that spans the last one, each contribution bound to its parent's ([§12](#s12), G1; [§13](#s13), H.2) | guaranteed at 10 s: a wait of 6.0 / 10.2 hours, within 0.1 hours of a nonce that is not ground; with today's nonce 14 to 19 / 26 to 42 hours | a hard fork; a window before the cut-off of at least 54 hours; a sequential computation of about a day once an epoch | recommended, with the delay; every `K` below 42 hours that holds a third at 10 s depends on it |
| settled level ([§4](#s4)) | a client rule; nothing in consensus | random delay: a wait of 3.1 / 5.1 h, a depth of 2.3 / 4.1 h, 1.5 / 2.4 h reading elapsed time; guaranteed at 10 s: a wait of 6.0 / 10.2 h, a depth of 13.1 / 23.2 h, 3.3 / 6.2 h counting the forks seen | nothing | recommended |
| finality counted in slots ([§6](#s6)) | `K` slots, and a density floor | `K` of 6.4 / 12.5 hours at 10 s with route 1's nonce, a deflated inference included; 18 hours holds both, and 54 hours holds both with today's nonce too | a floor, without which eclipses and splits fix forks after `K`; at 18 hours the floor against a third is 1,019 blocks, below today's 2,160, and holds back a cut-off side up to 0.385 of the stake; no floor separates a partition at a third | recommended at `K = ⌊k/f⌋`, 18 hours, with route 1's nonce and the floor in its depth form, 1,019 blocks: a third at 10 s holds with a factor of `8.4·10^6` to spare, `1.2·10^4` after a deflation |
| faster blocks ([§7](#s7)) | `f` | random delay: a wait of 3.0 / 6.2 h at 15 s blocks; worst case at 10 s: 9.5 / 20.4 h | ×2.0 the blocks at 15 s | not recommended: under the worst case a faster rate needs a longer `K` |
| regular block intervals ([§7](#s7)) | the lottery becomes a curve of the slots since the parent | against a third Topl's shape needs more than 60 blocks at `1e-3`, today's lottery 58 | a third more blocks; a new stake inference | not recommended |
| certificates ([§8](#s8)) | anonymous-seat votes through Blend | no committee against a third; against 30 %, 33,473 seats while every honest vote counts | ×1,675 Blend cover at 10-minute rounds | not recommended |
| multi-proposer DAG ([§9](#s9)) | replaces the chain and its fork choice | random delay, at today's block rate, against a third: 106 minutes, the chain 160 by the same fit | as the chain at that rate | not recommended: a balancing attack that retracts its wins holds a third for ever at every delay, so no `K` exists |

Two routes are recommended, and finality counted in slots is recommended at 18 hours under three
conditions:

1. **A nonce that resists grinding.** With today's hash-chain nonce, an adversary that withholds
   its wins picks the next epoch's leader schedule among many. Counted in slots, no `K` below 26
   hours then holds a third at 10 s: one ground nonce needs 26 to 27 hours of wait and two need
   38 to 42, and at 20 s one needs 93 to 96. The nonce taken from the smallest contribution of
   each of 25 sub-windows and passed through a sequential delay that spans the last sub-window,
   with each contribution bound to its parent's, leaves the adversary few values it can see while
   it can still choose between them. Against a third under the worst case the guaranteed wait is
   then 10.2 hours, against 10.1 with a nonce that cannot be ground. Counted in blocks the depth is
   1,523 blocks as a bound within the model, 13 more than a nonce that is not ground.
2. **A settled level in the node's API.** A client accepts a block after a wait, or a depth, from a
   table for its share `α`, failure probability `ε` and delay model. A wait reads the clock alone;
   a depth also reads the blocks, and a client may read both. With the nonce of route 1, against a
   third, the wait is 5.1 hours under random delay and 10.2 guaranteed at 10 s; a depth takes 4.1
   and 23.2 hours on the clocks of [§2](#s2), and reading elapsed time 2.4 hours under random
   delay.
3. **Finality counted in slots at 18 hours, with a floor in its depth form.** `K` must hold the
   worst case for the share, with the nonce of route 1 and a deflated inference counted: about
   12.5 hours against a third at 10 s and about 6.4 against 30 %. `K = ⌊k/f⌋`, 18 hours, holds a
   third with a factor of `1.2·10^4` to spare after a deflation. It rests on the nonce of route 1:
   with today's nonce a third needs 26 to 42 hours. A floor keeps an eclipse or a minority split
   from fixing a fork after `K` slots. In its depth form `B_imm` passes a block once 1,019 blocks
   follow it, which never stalls finality and needs no cap on the inference's correction. A side
   cut off from the rest then fixes its fork once it has made those blocks: 1.05 days with a third
   of the stake and 3.5 with a tenth, where 2,160 blocks give 2.2 and 7.4. The density form holds
   a sparse side back longer, until its inferred stake corrects, and stalls finality whenever the
   active stake falls below about two thirds. No floor separates a partition at a third, where
   splits still wait for operators, as they do counted in blocks.

Specification candidates follow from them:

1. **The epoch nonce from the smallest contributions** of sub-windows, passed through a sequential
   delay that spans the last sub-window, with the minima taken over a contribution bound to the
   parent's contribution ([§3.1](#s31), [§13](#s13)). Without the delay the contribution `ρ_LEAD` is
   bound to the epoch nonce and notes are frozen one epoch earlier, and a bound on the factor is
   open.
2. **A settled level** beside the tip and `B_imm`: the table of waits, the depth table, and the
   elapsed-time rule under random delay ([§3.2](#s32)).
3. **`B_imm` counted in slots, with a floor** ([§3.3](#s33)): `B_imm` passes a block once it is
   `K = ⌊k/f⌋` = 64,800 slots old and `φ` = 1,019 blocks follow it. `K` holds a third at 10 s with
   the nonce of route 1, a deflated inference counted, and `φ` is the `ε` lower tail of the blocks
   the honest chain makes in `K` while a third withholds, under the worst case at 10 s. The
   inference's correction stays uncapped.
4. **The Bootstrap rule's density window** sized for `(α, ε)` rather than tied to `k`
   ([§10](#s10)). Counted in slots its depth test reads one divergence age on both branches and
   needs no correction. The window bears on testnet, which runs `k = 120`.

Six further routes are read in [§12](#s12). One of them is the delay of route 1: a sequential
computation that spans the last sub-window, 4.5 hours on the adversary's hardware at the epoch's
length at `k = 2160`, with the contribution bound to the parent's contribution. It leaves the
adversary few values it can see while it can still choose them: against a third under the worst
case at 10 s the guaranteed wait is 10.2 hours. Honest nodes compute the delay in about a day.

---

<a id="s2"></a>
## 2. What is measured

**Three notions of finality** are kept apart:

- **k-finality.** `B_imm`, the latest immutable block, is never reorganised (a protocol rule).
  Counted in slots, `B_imm` is the latest block whose slot lies at least `K` slots back, and the
  Online rule follows no fork that diverges before it. The specification counts `k = 2160` blocks
  instead, and `B_imm` is the `k`-deep block. Praos counts persistence in blocks and liveness in
  slots, Genesis's chain selection counts blocks, and Crypsinous takes Genesis's chain selection
  and reads `k` as slots where it evolves its encryption keys (`SLOTS.md` K.0). A variant adds a
  density floor `φ`, in a depth form and a density form ([§3.3](#s33)).
- **Settlement.** A block at depth `d` is displaced with probability at most `ε` against an
  adversary holding `α`, under a stated delay model (a client rule).
- **Certified finality.** A block is final once a certificate of anonymous votes exists for it (a
  protocol addition).

**The adversary** holds a share `α` of the stake, reported from 5 % to a third. The design must
hold against a third, and 30 % at the loosest; the summary and [§3](#s3) read the results there.
`ε` is per block for settlement and per round for votes.

**Two delay models** are reported side by side:

- **Random delay.** Blend's mixing delays, measured in the per-node engine of the total-stake
  inference study (TSI): 1,000 nodes, a degree-6 peering graph, geographic links, and each relay
  holding a message a whole number of rounds as the node's release delayer does. Testnet 0.3.0
  runs 1 hop of 1 round; the specification allows 3 hops of up to 3 rounds. The specification's
  Blend orphans 18 % of blocks and delivers a block to every node within 10.2 s at the 99th
  percentile. The depths read the private race at the growth the engine measures with every node
  producing, a canonical chain of `0.845·f` blocks a slot over eight runs: the report's convention,
  the figure the specification's stake-inference analysis uses. As a measure of a chain on which
  every node produces it is low. 32 runs give `0.834·f`, equal stakes `0.819·f` on the same seeds,
  and Blend releases a block a round after its slot where the engine starts its cascade at the slot,
  which lowers the growth by 0.02 more (`RATE.md` A1). The attack it stands for needs less, since a
  withholding adversary orphans no honest block with its own: on the engine, with honest relays and
  the specification's two Blend copies released a round after the slot, the race needs 160 / 261
  blocks against 30 % / a third, within the convention's 165 / 276. Relays that hold or drop blocks,
  and a deflated inference, take it past the convention ([§12](#s12), G6, G7).
- **Worst case.** An adversary delivers every honest block as late as a bound `Δ` allows. The
  bounds of Gaži, Ren and Russell ("Practical Settlement Bounds for Longest-Chain Consensus",
  ePrint 2022/1571, revision 2025-05-02) apply. Their code is ported, checked against their Table 1
  and against the original run in Octave, and computed at every depth. `Δ = 10` s is a chosen
  bound, equal to the honest Blend's 99th-percentile delay. Delivery later than `Δ`, one block in a
  hundred under honest mixing and any delay an adversary adds at relays, lies outside the bound.
  Against a third the worst-case depth grows about 9 % per second of `Δ` near 10 s. On the 1 s
  slot lottery a phase of honest blocks also holds the slot of its first block, which gives the
  adversary one slot more per phase than their continuous time; the bound for a wait counts it.

**Times** are counted on the honest chain while the adversary withholds its blocks, one clock per
delay model. Under random delay a block takes `30 s / ((1 − α) · g)`, where `g` is the canonical
growth the engine measures: on the specification's Blend 50.7 s against 30 % and 53.2 s against a
third. Under the worst case the chain grows one block per `Δ + 1/p_h` slots, `p_h` the honest
stake's chance to win a slot: at 10 s, 52.6 s against 30 % and 54.7 s against a third.

**A wait is a time.** A wait of `K` slots is the same on every chain, so its chance of failure
averages over the honest blocks the wait holds and must cover the runs in which they come late.
Under random delay it averages B4's exact chance; under the worst case it is bounded in the model
of Gaži, Ren and Russell, their chain frozen at the phase in which the wait passes
([§4](#s4); `SLOTS.md` K.1, K.7).

**The random-delay figures are the private attack's.** Under random delay the only attack played
is a private chain with a premined lead. An adversary that also publishes blocks to prolong the
honest ties Blend causes is not played, and no bound covers it. The worst-case figures are proven
against every attack.

---

<a id="s3"></a>
## 3. The three routes in depth

<a id="s31"></a>
### 3.1 A nonce that resists grinding

**The problem.** The nonce of the next epoch is the hash chain at the last block before a cut-off
slot, `6⌊k/f⌋` slots into the epoch. An adversary that withholds its wins chooses which of them end
the chain there, and can also fork away the last honest blocks. Each choice is a different leader
schedule. To keep an attack's chance at `ε`, its chance against one schedule must fall by a factor
`R`. A block whose race crosses an epoch's end meets two ground nonces, and its factor is `R_2`.
Against 30 % and a third `R_2` reaches `10^19` and `10^28` under the worst case at 10 s
(`SETTLEMENT.md`, B6), and [§5](#s5) gives the depths. The depth that holds `ε = 1e-9` under
each factor, with two ground nonces:

| nonce | random, specification, α = 0.30 | random, specification, α = 0.33 | worst, 10 s, α = 0.30 | worst, 10 s, α = 0.33 |
| --- | --- | --- | --- | --- |
| not ground | 165 | 276 | 892 | 1,510 |
| hash chain, 2^1 evaluated | 168–177 | 286–296 | 902–954 | 1,544–1,614 |
| hash chain, 2^2 evaluated | 176–188 | 301–316 | 935–1,011 | 1,618–1,717 |
| hash chain, 2^4 evaluated | 191–206 | 330–351 | 1,003–1,098 | 1,762–1,900 |
| hash chain, 2^8 evaluated | 220–236 | 388–413 | 1,142–1,246 | 2,048–2,215 |
| hash chain, 2^16 evaluated | 279–296 | 506–532 | 1,429–1,539 | 2,639–2,812 |
| hash chain, 2^24 evaluated | 339–356 | 625–652 | 1,723–1,837 | 3,236–3,413 |
| hash chain, 2^32 evaluated | 401–417 | 745–772 | 2,021–2,133 | 3,837–4,013 |
| hash chain, 2^40 evaluated | 459–479 | 865–893 | 2,246–2,436 | 4,437–4,617 |
| hash chain, 2^48 evaluated | 482–525 | 986–1,013 | 2,333–2,633 | 5,041–5,221 |
| hash chain, 2^56 evaluated | 495–562 | 1,107–1,134 | 2,386–2,774 | 5,529–5,828 |
| hash chain, 2^64 evaluated | 504–574 | 1,171–1,245 | 2,424–2,825 | 5,732–6,287 |
| smallest contributions, k = 2160, at the cut-off | 165 | 277 | 894 | 1,518 |
| smallest contributions, k = 2160, estimated | 187–189 | 326–333 | 1,057–1,088 | 1,859–1,939 |
| smallest contributions, k = 1620, at the cut-off | 165 | 278 | 895 | 1,522 |
| smallest contributions, k = 1620, estimated | 187–189 | 328–334 | 1,059–1,092 | 1,862–1,943 |
| smallest contributions, k = 1080, at the cut-off | 166 | 280 | 897 | 1,532 |
| smallest contributions, k = 1080, estimated | 188–190 | 329–336 | 1,060–1,093 | 1,873–1,952 |

Hash-chain ranges span the two bounds on the factor (`SETTLEMENT.md`, B6); neither end is an
attack. "At the cut-off" counts the choices the adversary has at the cut-off alone. "Estimated"
ranges span the two estimates of its decisions before the cut-off, below.

**The rule.** The window before the cut-off is split into `m` sub-windows, 25 at `k = 2160`. The
nonce is `η_e = hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, where `η_e` is the nonce of epoch `e` and `μ_i`
the smallest contribution `ρ_LEAD` among the canonical blocks of sub-window `i`. A withheld block
changes the nonce only if it holds a sub-window's minimum. Two kinds of choice remain:

- **At the cut-off,** the adversary can still change only the sub-windows reached by a fork it
  can complete. At `k = 2160` a sub-window spans 15,552 slots, about 290 blocks, and the adversary
  reaches 1.06 nonces on average against a third.
- **Before the cut-off,** the adversary decides, as blocks appear, whether to publish each of its
  own blocks and whether to remove an honest one. If its block holds the smallest contribution so
  far in the last sub-window, it computes the nonce that results if no smaller contribution
  follows, and publishes the block only if that nonce suits its attack. If an honest block holds
  it, the adversary can remove that block: by racing it from its parent, won with chance
  `(p_a/p_c)²` for its win rate `p_a` and the honest canonical rate `p_c`; under the worst case for
  free, when an honest rival or an own win falls within `Δ` of it; under random delay with one win,
  when the block has a natural rival. Counted in hindsight, these decisions raise the factor per
  nonce to an estimated 5.9–7.3 against a third under random delay and 10.6–18.1 under the worst
  case at 10 s. The adversary decides before it knows the later contributions, so a hindsight count
  overstates what it reaches. These are estimates, not bounds.

**What it needs.** Without a delay, the three conditions below. With the delay of [§12](#s12), a
contribution bound to the parent's contribution, which every node derives, replaces the first two,
and the third stands.

- **A contribution bound to the epoch nonce.** Today `ρ_LEAD = hash(NONCE_CONTRIB_V1 ‖ sl ‖ noteID ‖
  sk)`, for the slot `sl`, the note `noteID` and its secret key `sk`, depends on the note and the
  slot alone. A key with small contributions in many slots could then be chosen when a note is
  created. The proof of leadership already takes the epoch nonce as a public input, so the change
  adds one input to a hash in the circuit.
- **Enough sub-windows, and notes frozen one epoch earlier.** The notes that use an epoch's nonce
  are frozen at the start of the previous epoch. The previous epoch's nonce is fixed `4⌊k/f⌋`
  slots before that freeze. From then on the adversary knows its own wins in the window that
  decides the next nonce, and their contributions. It can then predict the nonce, and the
  prediction is right if it holds the smallest contribution of every sub-window. With a right
  prediction it chooses keys that win and whose contributions are the smallest in every later
  window. It then controls every later epoch. Attempting every honest block below its own, it holds
  a sub-window's minimum with probability 0.50 against a third on the specification's Blend and
  0.58 under the worst case. Keeping the chance of a right prediction over ten years below `1e-9`
  then needs 50 sub-windows at `k = 2160`. With notes frozen one epoch earlier, as Ouroboros
  Phalanx does, a prediction needs the minima of two windows, and 25 suffice at `k = 2160`, 26 at
  `k = 1080`.
- **Long sub-windows.** A fork that reaches across a sub-window boundary multiplies the choices at
  the cut-off. With the sub-windows each `k` needs, the mean against a third is 1.06 at `k = 2160`
  and 1.16 at `k = 1080`. At `k = 432`, with sub-windows of about 54 blocks, it rises to 5–14,
  because rare windows offer many choices. A smaller `k` would need a window longer than `6⌊k/f⌋`
  slots.

**What it buys.** With the delay of [§12](#s12), against a third under the worst case at 10 s the
guarantee needs 1,523 blocks at `k = 2160` as a bound within the model, against 5,732–6,287 with
today's nonce: 23.2 hours instead of 87–96. Under random delay on the specification's Blend it
needs 278 blocks instead of 1,171–1,245: 4.1 hours instead of 17–18. Without the delay it needs an
estimated 1,859–1,939 and 326–333 blocks, 28.3–29.5 and 4.8–4.9 hours. `k = 2160` holds a third up
to a factor of 80.7 per nonce. Counted in slots, against a third the guaranteed wait at 10 s is 10.2
hours with it and 25.9–42.0 hours with today's nonce, and the wait under random delay 5.1 hours with
it and 13.9–23.1 with today's (`SLOTS.md` K.2, K.7).

**The alternative, a delay function.** Ouroboros Phalanx (CIP-0161) keeps the hash chain and passes
its value through a verifiable delay function. Honest nodes compute it once an epoch, in 82
independent iterations of about 9 minutes on a CPU, each by the first leader of an hour-long
interval. Every iteration takes the pre-nonce as input, so an adversary recomputes all 82 for every
nonce it evaluates, on hardware the CIP takes to be 10 times faster: one candidate in 72 minutes on
one machine, or one every 53 seconds on 82. A candidate's hash-chain value does not depend on the
honest blocks its fork drops, so the adversary evaluates each candidate from the moment its last
win exists, hours before the cut-off, and learns at the cut-off which candidates are feasible. Over
the 54-hour window of `k = 1080`, 82 machines evaluate about 3,700 candidates. This caps how many
nonces it evaluates, not how many it can choose between. Against a third under the worst case at
10 s the cap lies between the `2^8` and `2^16` rows, 2,048–2,812 blocks. A cap of 2 nonces would
leave 1,544–1,614, as the smallest contributions do at the cut-off. A delay whose input the
adversary cannot evaluate before it must choose would leave it one nonce. The two combine: the
smallest contributions make an input the adversary can form only from the start of the last
sub-window, so a delay that spans the sub-window, with the contribution bound to the parent's
contribution, removes the decisions before the cut-off ([§12](#s12), [§13](#s13)).

**What is shown, and what is not.** The choices at the cut-off are counted against an enumeration
of every fork and every subset of withheld wins, under the condition of `SETTLEMENT.md` B6 for a
fork to win. The worst-case depths read the proven bound of Gaži, Ren and Russell. Open:

- without the delay, a bound on the decisions before the cut-off, which are estimated in
  hindsight;
- the inferred stake, which the adversary moves by withholding blocks without changing the nonce,
  one lottery threshold step per block;
- under the delay, the sequentiality assumption and the number of delay evaluators an adversary
  runs: [§13](#s13) proves the lemma that reduces the rule to the values the adversary sees while
  it can still choose them, and bounds those within the walk's model.

<a id="s32"></a>
### 3.2 A settled level in the node's API

**The rule.** A client accepts a block once `d` canonical blocks lie on top of it, with `d` taken
from a table for its `(α, ε)` and delay model. The node would expose this third level, *settled*,
beside the tip and `B_imm`. A variant also reads when the blocks arrived. In the model of the
random-delay table the adversary withholds every win, holds the stationary lead of a private chain
it has kept all along, and never extends the public chain. Its progress since the target's parent
then depends only on the time since the parent. The client accepts at the first block at which the
adversary's chance, computed exactly as Grunspan and Pérez-Marco do, is at most `ε`. Within this
model the rule holds `ε` for every history of honest block times.

**What it buys**, against 30 % / a third, at `ε = 1e-9`. The depth rule includes the nonce of
[§3.1](#s31) at `k = 2160` under the delay of [§12](#s12), at its bound. Hours are on the clocks of
[§2](#s2). The elapsed-time rule is measured with a nonce that is not ground, on the engine's
timelines, where the depth rule's mean is 2.2 / 3.9 h:

| delay | depth rule | reading elapsed time, mean / 90th percentile | `k = 2160` |
| --- | --- | --- | --- |
| random, specification's Blend | 165 / 278 blocks: 2.3 / 4.1 h | 1.5 / 2.4 h, 1.9 / 3.2 h | 30.4 / 31.9 h |
| worst case, `Δ = 10` s | 895 / 1,523 blocks: 13.1 / 23.2 h | the observed counting rule with no forks under worst-case delay, 226 / 408 blocks: 3.3 / 6.2 h ([§13](#s13)) | 31.6 / 32.8 h |

Without the delay the depth rule needs an estimated 187–189 / 326–333 blocks under random delay and
1,057–1,088 / 1,859–1,939 under the worst case: 2.6–2.7 / 4.8–4.9 h and 15.5–15.9 / 28.3–29.5 h.

Counted in slots a client can also wait, reading the clock alone. Under random delay the wait that
holds `ε` is 3.1 / 5.1 hours against 30 % / a third, 1.33 and 1.25 times the depth rule's time.
Under the worst case at 10 s, with the nonce of [§3.1](#s31), it is 6.0 / 10.2 hours, 0.46 and
0.44 times the depth's (`SLOTS.md` K.7). Under random delay a depth, which also reads the blocks,
comes sooner; under the worst case the wait does, since the depth's bound freezes at the earliest
moment the target could lie that deep.

**What the client accepts.** The adversary's share; the delay model; the grinding its depths
include; a view that is not eclipsed. Under random delay also: the adversary withholds every win
and never extends the public chain, Blend's delays are not the adversary's to choose, its relays
are honest, and the honest chain grows as the engine measured. Under the worst case the depth rule
applies, and the observed counting rule of [§13](#s13), which holds `ε` per target, not given the
client's view. Both random-delay rules hold while the inferred stake is the true stake. After a
period of withholding the total-stake inference raises every rate by `1/(1 − α)`: the
elapsed-time rule must take those rates, with the depth rule as its cap, and then settles a chain
nobody withholds from in 66 / 106 minutes against 30 % / a third; and the private attack needs
189 / 334 blocks, past the depth rule's table, whose random-delay depths cover only an inference
that is not deflated ([§12](#s12), G4, G7).

**What is shown, and what is not.** The worst-case depths are the proven bound. The random-delay
depths are the private race with a premined lead, in closed form. The race played on the engine's
timelines matches it within three blocks at `1e-3` up to 30 %; against a third the closed form
over-asks by about a quarter ([§4](#s4)). On the engine's timelines both rules hold `ε` where it
can be measured, at `1e-3`: against 30 % the race beats the elapsed-time rule on 1.1e-3 of 78,696
targets, consistent with `ε`. Under the worst case the rule that reads time is the observed
counting rule of [§13](#s13): 408 blocks against a third under a worst-case delay, and 374 when the
adversary withholds without delaying, where the depth rule needs 1,510. Open: both rules against an
adversary that also extends the public chain.

<a id="s33"></a>
### 3.3 Finality counted in slots, with a floor

**What `K` must cover.** `K` binds every node, so it must hold under the worst case. A wait does
not stretch while the adversary withholds. It must therefore cover the honest chain growing from
the honest stake alone, one block per `Δ + 1/p_h` slots at 10 s, and the runs in which it grows
slower. With the nonce of [§3.1](#s31) under its delay, the guaranteed wait at 10 s is 6.0 hours
against 30 % and 10.2 against a third, and 6.4 and 12.5 after a deflated inference (`SLOTS.md`
K.7). `K = ⌊k/f⌋`, 18 hours, holds both, a third with a factor of `1.2·10^4` to spare after a
deflation. `K = s = 3⌊k/f⌋`, 54 hours, holds a third with a factor of `1.2·10^30` to spare after a
deflation. With today's nonce 18 hours does not hold a third, whose wait is 26 to 42 hours, and 54
hours does.

**What it breaks without a floor.** A node fixes its chain once a block the rest of the network
lacks is `K` slots old. An eclipsed node does so `K` slots after the first block it is shown, or
makes, whatever stake made it: 0.75 days at 18 hours and 2.25 days at 54. A partition side does so
after `K` slots whatever its share. Counted in blocks, an eclipse by a third took 2.2 days and one
by a tenth or less 7.4 to 8.2, and a side's horizon grew as its share fell: 35.7 hours for half of
the stake and 88.8 for a fifth (`SLOTS.md` K.3).

**The floor.** `B_imm` passes a block only once `φ` blocks follow it, the depth form, or only once
the `K` slots after it hold `φ` blocks, the density form. `φ` is the `ε` lower tail of the blocks
the honest chain makes in `K` slots while a coalition of `α` withholds: against a third, 3,264 at
54 hours under the worst case and 1,019 at 18 hours. At 10.1 hours, the least window that holds a
third at 10 s without grinding, it is 537 blocks and holds back a cut-off side of at most a third
(`SLOTS.md` K.7). A chain nobody withholds from falls below it with chance below `1e-99` at 54
hours.

- **Against an eclipse.** Under the depth form an eclipse by a third takes 3.4 days, and by the
  smallest stake 8.6 days, once the eclipsed chain's inferred stake has corrected. Under the
  density form it takes 9.75 days at 54 hours, for any stake up to a third.
- **Against a split.** Under the depth form an even side fixes its fork at 54 hours, a side of 0.3
  of the stake at 90 and one of 0.2 at 134. Under the density form a side too sparse over `K`
  stays provisional until its inferred stake corrects, at least 3 days after the split, and
  rejoins by the Online rule if the split ends first.

**What no floor does.** The adversary signs on both sides of a partition. The floor must then lie
above what a side of `(1 + α)/2` of the stake makes and below what the honest chain makes while the
adversary withholds. At a third the two are equal, and no `K` separates a partition. Against a
quarter a window separates the sides from 2.9 days under the worst case at 1 s and 17.5 days at
5 s, and none does at 10 s. Under random delay one does from 3.3 days with a side at the engine's
growth. Counted on blocks, at 54 hours no floor separates a partition against a quarter in either
model. Counted on occupied slots, as the stake inference counts, the honest chain keeps the wins it
loses to orphans, and under random delay a floor separates a quarter from 2.24 days and 30 % from
14.2 (`SLOTS.md` K.9). Under the worst case the honest chain's count of occupied slots is at least
its canonical blocks, and no larger bound is derived. H.1's attestation round, 2,271 seats against a
quarter, separates them while Blend's relays deliver the votes ([§13](#s13)).

**Counted as the stake inference counts.** The stake inference counts occupied slots, a canonical
block's or a referenced uncle's, and recovers the honest stake at 0.998–1.001 under Blend
(`reports/tsi/README.md` §3.2a). A floor on that count reads the honest chain at its stake's
occupancy, where a floor on blocks reads it at the 0.845 its orphans leave. A side at its fastest
counts the same either way. Against a third, at 18 hours (`SLOTS.md` K.9):

| a floor counted on | floor under random delay | largest cut-off side that floor holds back | stake below which the density form stalls, at the protocol's 1,019 | a block made as the stake halves is fixed after, depth form at 1,019 |
| --- | --- | --- | --- | --- |
| canonical blocks | 1,022 | 0.386 | 0.665 | 0.83 days |
| occupied slots, uncles included | 1,225 | 0.472 | 0.562 | 0.75 days |

- **At the protocol's floor the protection does not move,** since a side counts the same either way.
  A third still fixes a fork after 1.05 days.
- **The count gives liveness.** Every canonical block occupies its own slot, so the count of
  occupied slots is at least the count of blocks on every path, and finality survives a larger fall
  of the active stake.
- **Only a worst-case bound would raise the floor itself.** An adversary that orphans a run of
  honest blocks at once leaves one countable uncle, the run's first block (TSI report §6.6).

**What it fixes.** Both branches of a fork have one divergence age, so every node holding both
decides alike, and the Bootstrap rule's split of [§10](#s10) cannot occur. A race lasts at most
`K`, so every target stays inside B6's grinding bound while `K` is at most `4⌊k/f⌋` slots, 72
hours at the epoch's length (`SLOTS.md` K.4).

**What it costs.** The block rate no longer shortens finality, and under the worst case a faster
rate needs a longer `K` ([§7](#s7)). A node that receives no blocks for `K` slots would see
`B_imm` reach its own tip; a floor, or the Bootstrap rule taken after `T_offline`, keeps it from
fixing a chain no one else holds. Every floor's protection ends once a sparse chain's inferred
stake corrects, 3 to 15 days after a split.

**A cap on the correction.** The inference corrects its estimate in full each epoch. A cap `c`
bounds each correction, `D' ≥ (1 − c)·D`. The inference reads a side cut off from the rest as stake
that left, so a cap lengthens the density form's protection and its stall after a genuine fall
alike. At 54 hours, the protection at its earliest and the stall at its latest, in days
(`SLOTS.md` K.8):

| at `K` = 54 hours | no cap | 10 % an epoch | 5 % an epoch | 2 % an epoch |
| --- | --- | --- | --- | --- |
| density form: a cut-off side of 0.3 held back | 9.75 | 32.25 | 62.25 | 152 |
| density form: finality stalls after the active stake halves, random delay | 12.75 | 27.75 | 50.25 | 110 |
| depth form: a cut-off side of 0.3 / 0.1 held back | 3.73 / 7.88 | 3.73 / 10.80 | 3.73 / 10.98 | 3.73 / 11.09 |
| depth form: a block made as the stake halves is fixed after | 2.66 | 2.66 | 2.66 | 2.66 |
| the chain fills its slots within 5 % of `f` again after the stake halves | 10.5 | 55.5 | 100 | 243 |

- **No cap separates a split from a fall.** The protection against a side of 0.3 lasts 0.73 to
  1.38 times the stall after a fall to half, at every cap and both candidate windows.
- **The depth form needs no cap and never stalls.** A side of a fifth or more makes its `φ + 1`
  blocks before its first correction.

**What is recommended.** `K = ⌊k/f⌋`, 18 hours, with the nonce of [§3.1](#s31) under its delay,
and the floor in its depth form at 1,019 blocks, with the inference's correction uncapped.

- **It holds a third at 10 s with a margin.** The wait that holds `ε` is 10.2 hours with that nonce
  and 12.5 after a deflated inference as well. After a deflation the chance at 18 hours is
  `8.4·10^-14`, about `10^4` times below `ε` with the nonce's factor counted.
- **It rests on the nonce and on the delay bound.** With today's nonce a third needs 26 to 42
  hours. Without grinding a third needs 17.4 hours at 15 s and 33.5 at 20 s (`SLOTS.md` K.7).
- **Its floor never stalls finality**, and keeps a node cut off with a third of the stake from
  fixing the fork it is shown for 1.05 days, about half of what 2,160 blocks give. The floor holds
  back a cut-off side up to 0.385 of the stake (`SLOTS.md` K.3, K.8).

**What is shown, and what is not.** The worst-case wait is the bound of Gaži, Ren and Russell's
chain frozen at the phase in which the wait passes, each phase's span charged at its longest and
the slot lottery's extra slot per phase counted. It lies above their attack played against a wait
on the slot lottery (`SLOTS.md` K.7). The deflated wait with the nonce of [§3.1](#s31) takes H.2's
factor at the old rates. A side of a partition grows at most one block per slot it occupies, and
the floor's figures rest on it.

### 3.4 The three together

With the nonce of [§3.1](#s31) under the delay of [§12](#s12), at its bound, one clock per delay
model; reading elapsed time is measured with a nonce that is not ground. A wait in slots stands
beside a depth in blocks:

| against | today, `k = 2160` blocks: random delay / worst case | settled, random delay: a wait / a depth | settled, reading elapsed time | settled, guaranteed at 10 s: a wait / a depth | `K` that holds it at 10 s, a deflated inference included |
| --- | --- | --- | --- | --- | --- |
| 30 % | 30.4 / 31.6 h; `k` not proven at 10 s with two ground nonces | 3.1 / 2.3 h | 1.5 h | 6.0 / 13.1 h | 6.4 h |
| a third | 31.9 / 32.8 h; `k` not proven at 10 s with two ground nonces | 5.1 / 4.1 h | 2.4 h | 10.2 / 23.2 h | 12.5 h |

---

<a id="s4"></a>
## 4. Settlement on the chain

The depth a client must wait, in canonical blocks, at `ε = 1e-9`, with a nonce that is not ground:

| adversary | random delay, testnet's Blend, private attack | random delay, the specification's, private attack | worst case, `Δ` = 1–10 s, proven | worst case, best known attack |
| --- | --- | --- | --- | --- |
| 10 % | 17 | 19 | 75–114 | 31–33 |
| 25 % | 67 | 88 | 288–474 | 110–143 |
| 30 % | 114 | 165 | 495–892 | 185–266 |
| a third | 172 | 276 | 758–1,510 | 278–445 |

Under random delay the depth is that of the private race with a premined lead, in closed form.
The race played on the engine's timelines matches it within three blocks at `1e-3` up to 30 %.
Against a third the closed form asks 81 blocks at `1e-3` where the race needs 58, and at `1e-9` the
race's fit needs 188 blocks against the closed form's 276: the closed form over-asks as orphans
rise, and the client rule uses it as the conservative side. The attack column is extrapolated past
depth 120 from 25 % at 5 s, and at 30 % and a third throughout (`SETTLEMENT.md`, B2).

- **The proof is not far from the attack.** Where both are computed, the proven depth is 2.4 to 3.6
  times the attack's at delays up to 10 s, and up to 6.6 times at 20 s.
- **The bound describes Cryptarchia's slot lottery.** The attack behind the lower bound, played on
  the 1 s slot lottery, lands within 7 % of the bound computed in continuous time.
- **`k = 2160` holds a third of the stake at `1e-9` only for delays up to 13 s,** without grinding
  and while the inference is not deflated.
- **A rule that also reads elapsed time settles 35–40 % sooner from 30 %.** Against a third at
  `1e-9`, on the engine's timelines of the specification's Blend, it accepts after 2.4 hours on
  average where the depth rule needs 276 blocks and 3.9 hours. Against a quarter it accepts after
  47 minutes where the depth rule needs 88 blocks and 68 minutes, and against a tenth it settles
  about a fifth sooner. It is derived for random delay only.

**Counted in slots.** A wait reads the clock alone, so it must also cover the runs in which the
honest blocks come late. At `ε = 1e-9` on the specification's Blend (`SLOTS.md` K.1):

| adversary | random delay: a wait / the depth rule | worst case at 10 s: a wait, bound / B2's depth on its clock |
| --- | --- | --- |
| 10 % | 0.45 / 0.21 h | 0.8 / 1.4 h |
| 25 % | 1.70 / 1.16 h | 3.2 / 6.6 h |
| 30 % | 3.09 / 2.32 h | 5.9 / 13.0 h |
| a third | 5.10 / 4.08 h | 10.1 / 23.0 h |

- **Against a third a wait costs a quarter more than a depth under random delay, and under the
  worst case at 10 s 0.44 times the proven depth's time.** Under random delay, against smaller
  shares it costs more in proportion and less in time: against a tenth the wait is 2.2 times the
  depth rule's time, 27 minutes against 13.
- **The worst-case wait is a bound in the paper's own model.** The margin of Gaži, Ren and Russell
  keeps the prefix up to a slot once it stays negative, so their chain, frozen at the phase in
  which the wait passes, bounds the wait directly. Reading their depth bound at the depth the wait
  guarantees asks 2.6 to 2.9 times as long, since that bound already freezes at the earliest moment
  the target could lie that deep. On the slot lottery a phase also holds its first honest slot,
  which costs 10 % against a third at 10 s. Their attack, played against a wait on the slot
  lottery, succeeds 0.26 to 0.82 times as often as the bound allows (`SLOTS.md` K.7).
- **The depth bound freezes at half the paper's count.** The paper puts the earliest settlement
  error at `ρ + h + 2a ≥ 2k`; its code, and its Table 1, freeze at `ρ + h + 2a ≥ k`. At the paper's
  count the proven depths halve, 755 blocks against a third at 10 s instead of 1,510; the study
  keeps the code's count ([§11](#s11)).
- **The race played on the engine's timelines succeeds 0.42–0.74 times as often as the closed form
  at `1e-2`**, and never at `1e-3` against a third, so the closed form errs on the safe side. On the
  model's own slots it matches within 2.5 standard errors.

---

<a id="s5"></a>
## 5. The epoch nonce

**Grinding.** The adversary's choices at a cut-off are counted exactly from a random walk of its
lead, backwards from the cut-off, with the lead it may still gain after the cut-off mixed in. Two
bounds bracket the factor `R` by which the chance against one schedule must fall, for one ground
nonce and for two (`SETTLEMENT.md`, B6). Both ends of a range bound `R`; neither is an attack. The
rows below assume an adversary that evaluates `B = 2^64` nonces an epoch, the row that stands for
unlimited hardware; from 30 % of the stake the budget sets the factor. One evaluation costs one
hash per slot of the attack window, with the stake in one note: `9.6·10^16` hashes an epoch at
`2^40` for a window of 1,600 blocks, `1.6·10^24` at `2^64`. At `ε = 1e-9`, the depths in blocks:

| delay | adversary | not ground | one ground nonce | two ground nonces |
| --- | --- | --- | --- | --- |
| random, the specification's Blend | 25 % | 88 | 155–164 | 171–193 |
| random, the specification's Blend | 30 % | 165 | 405–416 | 504–574 |
| random, the specification's Blend | a third | 276 | 750–768 | 1,171–1,245 |
| worst case, 10 s | 25 % | 474 | 759–819 | 824–950 |
| worst case, 10 s | 30 % | 892 | 2,056–2,124 | 2,424–2,825 |
| worst case, 10 s | a third | 1,510 | 3,879–3,994 | 5,732–6,287 |

- **`k = 2160` cannot be proven against 30 % or a third at 10 s with two ground nonces.** Against
  30 % the claim holds from `B = 2^40` (2,246–2,436 blocks) and fails at `2^32` (2,021–2,133);
  against a third it holds from `2^8` (2,048–2,215). Against a third the bounds prove `k = 2160`
  with two ground nonces only at 1 s, against an adversary that evaluates `2^40` nonces. With one
  ground nonce they prove it up to 5 s against `2^40` and up to 2 s against `2^64`.
- **The two-nonce depth covers a target after its epoch's cut-off.** A target before the cut-off
  whose race outlasts the `4⌊k/f⌋` slots to the epoch's end is attacked by a private chain carrying
  a nonce the adversary picks itself, and no bound covers it. Against a third at 10 s the two-nonce
  depth takes 96 hours on the worst-case clock, 24 hours past 72: every target within 24 hours
  before a cut-off, 13 % of targets, is outside the bound. Uncovered targets can only need more
  depth, so the claim above stands, and the depths of [§3.1](#s31) lie inside the covered range.
- **Grinding also shortens the recovery horizon.** With today's nonce the longest window at
  `k = 2160` holds a third for 57–111 days at Bitcoin's turnover, against 106–205 without grinding
  ([§6](#s6)).

**Two ways to resist it** (`SETTLEMENT.md`, B7). A delay function caps how many nonces the
adversary can evaluate; the smallest contributions of sub-windows reduce how many it can reach.
The table of [§3.1](#s31) compares them, and [`grinding.md`](grinding.md) reviews every approach
side by side. Under the worst case at 10 s against a third, a cap of 2
nonces leaves 1,544–1,614 blocks; the smallest contributions leave 1,518 at the cut-off and an
estimated 1,859–1,939 with the decisions before it, at `k = 2160`, and passed through a delay that
spans the last sub-window, 1,523 as a bound ([§12](#s12)).

**Counted in slots** (`SLOTS.md` K.2, K.4). The Online rule follows no fork older than `K`, so a race
lasts at most `K` slots. A target meets two ground nonces only past its epoch's cut-off and within
`K` slots of the epoch's end: 10 % of targets at `K = ⌊k/f⌋` and 30 % at `3⌊k/f⌋`. While `K` is at
most `4⌊k/f⌋` slots, 72 hours at the epoch's length, no target meets a nonce its own private chain
set, so B6's bounds cover every target; counted in blocks 13 % lay outside them. With today's nonce,
against a third at 10 s, one ground nonce needs a wait of 25.9–26.7 hours and two 38.3–42.0; against
30 %, 13.6–14.1 and 16.1–18.7 (`SLOTS.md` K.7).

---

<a id="s6"></a>
## 6. The window `K`, and recovery from a split

**What a `K` holds.** The largest share each window holds at `ε = 1e-9` under the worst case at
10 s, beside `k` blocks, without grinding / with two ground epoch nonces (`SLOTS.md` K.7):

| `k` | `k` blocks | `K = ⌊k/f⌋` slots | `K = 3⌊k/f⌋` slots |
| --- | --- | --- | --- |
| 2160 | ≥ a third / 0.288 | ≥ a third / 0.298 | ≥ a third / ≥ a third |
| 1080 | 0.313 / 0.256 | 0.327 / 0.267 | ≥ a third / 0.315 |
| 432 | 0.242 / 0.208 | 0.261 / 0.220 | ≥ a third / 0.276 |
| 216 | 0.172 / 0.161 | 0.194 / 0.177 | 0.293 / 0.242 |
| 120 | 0.106 / 0.103 | 0.126 / 0.120 | 0.245 / 0.210 |

- **`⌊k/f⌋` slots hold what `k` blocks hold under the worst case, and `3⌊k/f⌋` slots more.** A
  wait must cover the honest chain's slowest growth, but its bound reads no depth bound at that
  pace: at `k = 2160`, 18 hours hold a third without grinding and 0.298 with two ground nonces,
  where 2,160 blocks hold 0.288.
- **Under random delay** on the specification's Blend, `⌊k/f⌋` holds 0.390 at `k = 2160`, where
  2,160 blocks held 0.412, and `3⌊k/f⌋` holds 0.419.
- **At 20 s only `3⌊k/f⌋` holds a third, and only without grinding or a deflation.** The wait is
  33.5 hours without grinding, 93 to 156 with today's nonce and 156 after a deflation.

**Eclipses and splits.** Counted in slots, a node fixes its chain once a block the rest of the
network lacks is `K` slots old, whatever stake made it. When an eclipsed node fixes the chain it is
shown, made by a share `σ`, on average, with the inferred stake corrected at the next epoch where
that comes sooner (`SLOTS.md` K.3):

| σ | `k = 2160` blocks (days) | `K = 54` h, no floor (days) | depth form at 54 h (days) | density form at 54 h (days) |
| --- | --- | --- | --- | --- |
| a third | 2.23 | 2.25 | 3.36 | 9.75 |
| 0.1 | 7.39 | 2.25 | 7.87 | 9.75 |
| 0.001 | 8.24 | 2.59 | 8.63 | 9.75 |

- **The self-healing horizon is `K` for every side.** Counted in blocks it grows as a side's share
  falls, 35.7 hours for half of the stake and 88.8 for a fifth at `k = 2160`.
- **A floor restores what `k` blocks gave.** At 54 hours it is 3,264 blocks against a third under
  the worst case and 3,318 under random delay, more than 2,160. Under its density form a side too
  sparse over `K` stays provisional and rejoins by the Online rule when the split ends, with no
  trigger; it holds until the side's inferred stake corrects, at least 3 days after the split.
- **No floor separates a partition at a third.** The adversary signs on both sides, and a side of
  `(1 + α)/2` of the stake makes as many blocks as the honest chain it withholds from. Against a
  quarter a window separates the sides only from 2.9 days under the worst case at 1 s, and none
  does at 10 s ([§13](#s13)).

The rest of this section counts `k` in blocks, as the specification does. Where a rule reads
otherwise in slots, it says so.

**What a smaller `k` holds.** The largest adversary each `k` withstands at `ε = 1e-9`, without
grinding and with two ground epoch nonces (`2^64` nonces evaluated an epoch):

| `k` | random delay, the specification's Blend | guaranteed, `Δ` = 1–10 s | random delay, with grinding | guaranteed, with grinding |
| --- | --- | --- | --- | --- |
| 2160 | 0.41 | at least a third | 0.36 | 0.29–0.33 |
| 1080 | 0.39 | 0.31 to at least a third | 0.33 | 0.26–0.29 |
| 432 | 0.36 | 0.24–0.29 | 0.29 | 0.21–0.24 |
| 216 | 0.32 | 0.17–0.22 | 0.26 | 0.16–0.20 |
| 120 | 0.28 | 0.11–0.15 | 0.23 | 0.10–0.15 |

**What a smaller `k` breaks.** A split heals by itself only while the losing side has made fewer
than `k` blocks: 35.7 hours for an even split at `k = 2160`, 2 hours at `k = 120`. Past that, a node
on the losing side stays there ([§10](#s10)).

**Automatic recovery** can lift that bound for an eclipse. A fork that diverges deeper than `k`
but within a horizon `H` is compared by its block density in a window after the divergence, the
test of the Bootstrap rule. Eight rules keep it safe where it can be:

1. Evaluate the fork; never switch fork-choice rules. A switch would freeze `B_imm`, and one stale
   winning slot could trigger it.
2. Read the depth of the deeper branch, so that every node holding either chain decides alike.
3. Compare densities only once both chains hold the whole window.
4. Size the window for `(α, ε)` and the horizon.
5. Keep the window within `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake take effect:
   72 hours at `k = 2160`, 54 at `k = 1620`, 36 at `k = 1080`, 4 at `k = 120`.
6. Bound the horizon `H` against keys that become free (below).
7. Break ties by a rule that reads the two chains alone. Two honest sides of an even split tie in
   density with probability 0.5–0.7 % at the longest windows by the closed form, and on the engine
   in 1.0 % of windows with one Blend copy and 1.6 % with two; under a strict order they would
   never heal.
8. Compare only from a chain that had its full density over the window. Every window and horizon
   here gives the honest chain the whole honest stake. In a partition each honest side produces
   with its own share, and the adversary withholds a fork made with all of its stake: against an
   honest side holding 35 % of all stake, a 30 % adversary's fork is denser in 64–70 % of the
   specification's windows, and against an honest third, a third's fork always is. On the engine,
   with most Blend copies lost across the cut, a side holding 30–40 % of all stake grows at
   0.83–0.86 per occupied slot, about the whole network's 0.845, and the closed form read at the
   side's growth lies within half a standard error of the engine. With the adversary's nodes on
   the far side of the cut, its best placement, a 30 % fork beats a 35 % side in 65 % of windows
   and a third's beats a 40 % side in 55 %, where the closed form at the whole network's growth
   says 36 %; with its nodes beside the side, 42 % and 17 % (`SETTLEMENT.md`, B5). Today the
   Online rule caps what such a fork reorganises at `k`. A node whose chain was sparse over the
   window therefore does not
   compare, and leaves the split to operators, as today. The trigger heals an eclipse, where one
   side is the whole honest chain, and not a partition deeper than `k`.

Counted in slots, rule 2 holds by construction: a fork's divergence age is the same from either
branch. Rule 3 holds whenever the window fits in `K`, and rule 5 keeps its 72-hour cap with the
epoch at its length. The floor's density form is rule 8 applied to `B_imm`: under random delay its
threshold is H.1's detector's over a window of `K` (`SLOTS.md` K.3).

The trigger costs four things. `B_imm` may move back within `H`, so every consumer of it needs a
path for that, and the `k`-deep block is final only against forks that lose the density test. The
node keeps its block tree and ledger states back to `H`, and validates every fork deeper than `k`
it is shown. A split heals only once the window after its divergence has passed. A partition deeper
than `k` still waits for operators.

**The horizon.** Cryptarchia has no forward security. The key of a note that was eligible at the
divergence and has been spent since can sign for it on the fork, where the note is unspent. The
longest horizon, in days, that keeps the failure over all divergence points at or below `1e-9`,
without / with grinding, with every freed key for sale, on the specification's Blend under random
delay. Each `k` uses its longest window, and each cell spans Bitcoin's monthly and yearly
turnover, 0.243 % and 0.125 % a day:

| k | window | α = 0.20 | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 2160 | 72 h | 273–530 / 262–508 | 210–406 / 185–358 | 147–285 / 107–207 | 106–205 / 57–111 |
| 1620 | 54 h | 261–504 / 248–481 | 198–384 / 171–330 | 137–265 / 93–179 | 97–186 / 43–83 |
| 1080 | 36 h | 240–465 / 227–439 | 180–348 / 149–288 | 121–234 / 70–135 | 82–157 / 21–41 |
| 432 | 14.4 h | 184–354 / 166–320 | 130–250 / 89–171 | 76–145 / 11–19 | 40–75 / < 1 h |
| 216 | 7.2 h | 132–253 / 112–213 | 83–158 / 37–68 | 34–62 / < 1 h | 42–49 h / < 1 h |
| 120 | 4 h | 83–157 / 61–114 | 38–71 / < 1 h | 5 h / < 1 h | < 1 h / < 1 h |

- **Against 30 % and a third only the long windows hold.** Even without grinding, `k = 120`'s
  4-hour window holds 30 % for 5 hours of history and a third for none.
- **Grinding halves the horizon against a third** at `k = 2160` and cuts it to a quarter at
  `k = 1080`.

Staked value on other chains moves at 0.05–0.3 % a day: Ethereum's exits are capped at 0.13 %, and
Cosmos, Polkadot, Cardano and Solana showed 0.05–0.27 % in single-period scans. Bitcoin's supply,
the closest match to Cryptarchia's notes, moves at 0.13–0.24 % a day over a month to a year. Chains
whose stake is never locked protect leader keys instead: Cardano's evolve every 36 hours, and
Algorand erases each round's key. A forward-secure leader key would free the horizon from turnover
altogether.

---

<a id="s7"></a>
## 7. Block rate, orphans and fork choice

- **Faster blocks pay under random delay below 30 %.** On testnet's Blend, 10 s blocks settle
  against a quarter of the stake in 18 minutes at `1e-9` against 46 at 30 s. On the
  specification's Blend the race keeps gaining at least to 15 s blocks: 59, 48 and 40 minutes at
  30, 20 and 15 s. The cost is 1.56 blocks per 30 slots at 20 s and 2.07 at 15 s, against 1.03
  today (×1.5 and ×2.0). No worst-case figure is given at `f ≠ 1/30`.
- **From 30 % they gain little.** On the specification's Blend the closed form settles later with
  faster blocks: 139, 147 and 150 minutes at 30, 20 and 15 s against 30 %, and 245, 290 and 327
  against a third. The race, fitted and extrapolated as for the DAG ([§9](#s9)), gains 10 %
  against a third: 160, 153 and 144 minutes. The race is the better estimate at this orphan share
  ([§4](#s4)); the verdict reads it.
- **Counted in slots, a faster block rate needs a longer `K` under the worst case.** A fixed delay
  costs more block intervals as blocks speed up. Against a third at 10 s the wait grows from 10.1
  hours at 30 s blocks to 12.5 at 20 s and 20.4 at 15 s, and against 30 % from 5.9 to 6.6 and 9.5
  (`SLOTS.md` K.7). Under random delay the closed-form wait against a third grows from 5.1 hours to 5.7 and
  6.2, and against a quarter falls from 1.7 to 1.5 and 1.4 (`RATE.md`). Counted in blocks, faster
  blocks shortened k-finality in proportion.
- **A fork choice that weighs uncles is no better.** The exact consistency regions of GHOST, the
  fork choice that weighs every block of a subtree (Gaži, Motaqy and Russell, ePrint 2024/1830),
  never exceed the longest-chain rule's at any delay. In proof of stake GHOST also needs control of
  equivocation. Weighing every honest block with one weight per win does not help against a
  scheduled delay either: a coalition that places and retracts its wins keeps two sides level for
  ever against a third ([§9](#s9)).
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

<a id="s8"></a>
## 8. Certified finality

A vote is a private lottery win of a seat, carried through Blend. A certificate needs a quorum `Q`
of `n` expected seats per round. Two conflicting certificates need `h + 2a ≥ 2Q` for `h` honest and
`a` adversarial seats, and a round stalls when the honest seats that count fall short of `Q`.
Against a third of the stake no quorum does both.

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
  Against 30 % a committee exists only while every honest vote counts.
- **Blend's budget does not carry the raised cover.** Against a quarter of the stake with
  10-minute rounds, a core connection would carry 41 times what a node reads from it a round, and
  a node would verify 5.3 times what one core of a Raspberry Pi 5 verifies. Sent on top of today's
  cover instead, votes fit only while a committee casts fewer than 1.33 votes a second.
- **Votes on a target 30 slots back never split** under random delay, in 1,368 rounds.
- **Counted in slots** a certificate still comes no sooner than settlement at `1e-3` under a
  scheduled delay. A partition that stalls certificates lets a window in slots without a floor
  finalize both sides (`CERTIFIED.md`).
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
  against a quarter of the stake, 78 % at 95 % uptime. Against 30 %, uptime below 95.2 % breaks it,
  and a third cannot be held at all. Declared notes must stay in the leader lottery: an adversary
  that declares nothing would otherwise hold half of it against a quarter of the stake.
- **Past certificates need forward security.** Whoever later gathers the keys of past voters can
  forge a past certificate. A per-round key erased after voting, or certificates trusted only
  within a window, would close it.

Proving a vote reuses the node's proof of leadership: 72.5 ms on an Apple M4 Pro, and a holder of
share `s` proves `s·n` times a round. The Raspberry Pi 5 is not measured.

---

<a id="s9"></a>
## 9. The multi-proposer DAG

Areon (Castro-Castilla, Pawlowski and Zhou, arXiv 2511.23025) lets several proposers win each slot.
A block references the recent tips its producer has seen within a window of `w` slots, and a fork
choice local to the closest common ancestor compares the weight of competing subDAGs, the parts of
the DAG on either side. Its simulator does not run that fork choice; its figures score a greedy
attack, and its comparison with Praos mixes block rates and metrics (`DAG.md`, E0). The study
builds the honest DAG on the TSI engine instead, with Cryptarchia's per-note lottery at a
production coefficient `f_A` and Blend's delays, and attacks it with the same private race as the
chain.

Phase J counted `k` in slots for the DAG (`DAG.md` J.0), so nothing in this section moves:
retraction outlasts every `K`.

The paper leaves the weight open, and the reading decides the outcome:

- **Counted since the fork,** each block once, each lottery win once: the DAG settles.
- **Counted over the last `w` slots only,** as the paper's prose says: no depth settles. An
  adversary that keeps its private subDAG alive outweighs the honest side in some window.

With the first reading, on the specification's Blend, from the race's success fitted and
extrapolated to `1e-9` as the paper's §5.6 does for both structures:

| production | blocks per slot, relative to today | against a quarter, `1e-3` | against a quarter, `1e-9` | against a third, `1e-9` |
| --- | --- | --- | --- | --- |
| the chain, `f = 1/30` | ×1 | 18 min | 59 min | 160 min |
| the DAG, `f_A = 1/30` | ×1 | 12 min | 38 min | 106 min |
| the DAG, `f_A = 0.1` | ×3.2 | 4.9 min | 16 min | 39 min |
| the DAG, `f_A = 0.25` | ×8.6 | 2.1 min | 6 min | 20 min |

- **No honest block is wasted.** Every honest block counts, wherever it sits; the chain discards its
  orphans. At the same block rate the DAG settles about a third sooner. The fit falls 3–5 % short
  of the exact depth when applied to the chain's race in closed form.
- **Raising the block rate pays more on the DAG.** The chain at 20 and 15 s blocks settles in 48
  and 40 minutes at `1e-9` against a quarter, the DAG at ×3.2 the blocks in 16. The price is
  emissions: every block is a lottery win and a Blend emission.
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
  `f_A = 0.25`, where with 10 % three attempts in four hold the balance for a day. These edges
  count one move per withheld win. With one move per win and a tie rule every node applies alike,
  the strongest attack against a third needs 2.8 hours at `1e-9` at `Δ = 1` s and 5.0 at 10 s,
  against the chain's 3.5 and 6.8. But a tag found on both sides weighs on neither, so a placed win
  can be retracted by a second copy on the other side, and one win moves the balance twice. The
  edges then fall below a third at every block rate and delay measured: at today's rate to 0.318
  with ties steered and 0.326 with a fixed tie rule at `Δ = 1` s, and to 0.235 and 0.279 at 10 s. A
  third holds the balance for ever with positive chance at every delay, so no depth settles against
  it, and no bound does: the bound from convergence opportunities, counting both moves of a win, is
  finite at 10 s only up to 0.223 of the stake, and against 25 % at 1 s it needs 14.2 hours where
  the chain's bound needs 3.3 (`DAG.md` J.2, J.3).
- **One win weighs once on a side, and still moves a balance twice.** A lottery ticket that does
  not depend on the parent can sign blocks in one subDAG or in both of two conflicting ones. Each
  win carries a tag, `ρ_LEAD`, fixed per note and slot, and the weight must count each tag once on
  a side; without that, GHOST-like weights provide no security at all. Across two sides no rule
  every node applies alike makes a win weigh once: whether a tag found on both weighs on both or on
  neither, its second copy moves the balance again, when the adversary chooses (`DAG.md` J.1).
- **The window must span the block interval.** At `f_A = 1/30`, the paper's 30-slot window leaves
  36–56 % of the honest blocks without a reference inside it, and so without weight.
- **The ledger needs a rule.** Honest blocks must reference only the side their fork choice
  prefers, so that a defeated subDAG is never merged into honest history. The total order must skip
  transactions that conflict with earlier ones, and must not place a late block before blocks
  already settled.

---

<a id="s10"></a>
## 10. Findings about the protocol as it stands

- **A restart does not heal a split deeper than `k`.** The bootstrap specification's key invariant
  forbids reorganising below `B_imm`, and the node prunes every block below it. A restart keeps
  both, so `--bootstrap` alone leaves a node on the losing side. Only a re-sync from genesis or from
  a checkpoint returns it; the node implements the first, and checkpoints are specified but not
  implemented.
- **Testnet's Bootstrap window is too short.** The density window `s_gen = ⌊k/4f⌋` is 15 minutes at
  `k = 120`. An adversary holding a quarter of the stake wins about one such window in 460 on
  testnet's Blend. A node that syncs from genesis compares forks at every block of the history, so
  over a month of history that adversary finds such a window with probability 0.998.
- **The Bootstrap rule's depth test can split the nodes that run it after a split.** It reads the
  depth of the node's own branch. When one side of a split has passed `k` blocks and the other has
  not, nodes on the short side follow the longer chain while nodes on the long side follow the
  denser one, and they alternate until both sides pass `k`. A node runs the Bootstrap rule when it
  starts from genesis or a checkpoint, after more than 20 minutes offline, or on the operator's
  flag, and keeps it for 24 hours; nodes under the Online rule converge on the long side.
  Counted in slots both branches read one divergence age, and the split cannot occur.
- **The epoch nonce can be ground** ([§5](#s5)). The nonce is the hash chain at the last block
  before a cut-off slot, so an adversary that withholds its wins chooses among the chains it can
  end there. Against 30 % at `Δ = 10` s, the guarantee then needs 2,424–2,825 blocks, more than
  `k = 2160`.
- **The total-stake inference can be deflated.** The inference corrects its estimate in full each
  period from the occupied slots. An adversary that withholds every block for one period, 4.5 days
  at `k = 2160`, lowers the estimate by its share and raises every lottery threshold by
  `1/(1 − α)` for the next epoch, and the deflation holds while it withholds. The honest chain then
  runs at the full rate `f`, and a worst case of `Δ = 10` s reads as 15 s against a third: the
  proven depth is 2,426 blocks (27 hours) where it was 1,510 (23 hours), so `k = 2160` no longer
  holds a third. Under random delay the chain the adversary withholds from then grows as one on
  which every node produces: on the engine its private attack needs 334 blocks where it needed 257,
  past the 276 the random-delay figures read, though in less time. A cap on the correction of 5 % a
  period prices the deflation at 36 days of withholding ([§12](#s12), G7). Counted in slots it
  lengthens the guaranteed wait against a third at 10 s by 23 %, 10.1 to 12.4 hours, and shortens
  the wait under random delay, 5.1 to 3.4 hours in the convention's model (`SLOTS.md` K.2, K.7).
- **The total-stake inference rounds its target,** as the TSI report records
  (`reports/tsi/README.md` §2.2, Appendix A). `total_stake_inference` computes
  `f_p = truncate(f·PRECISION)` with `PRECISION = 1e3`, so for `f = 1/30` it holds the occupied
  slots, canonical or referenced, at 0.033 a slot. Its estimate then rests 1 % above the stake, the
  one residual uncle references leave (`SLOTS.md` K.8).
- **Counted in slots, finality needs a floor.** A node fixes its chain once a block the rest of the
  network lacks is `K` slots old, whatever stake made it, its own blocks included. An eclipse then
  fixes a fork in `K` slots and one block, 2.25 days at `K = 54` hours, where `k = 2160` blocks need
  2.2 days against a third and up to 8.2 days for the smallest stake. A partition side of any share
  fixes its fork after `K` slots. A density floor restores the protection ([§3.3](#s33)).
- **The bound's reference code needs more phases at depth.** LCanalysis follows its lower-bound
  attack for 80 phases, too few past its Table 1's depths. At a third of the stake, `Δ = 1` s and
  depth 60 the bound falls from `6.9e-3` to `5.5e-12` in the port at 30 states; the original code,
  run in Octave, falls to `5.4e-13` at its 19 states. It also scores the attack only at the moment
  of confirmation; scored at any later moment, the same attack succeeds 2–17 % more often.
- **The bound's reference code confirms at half the paper's count.** LCanalysis freezes its upper
  bound once the adversary's lead, the honest successes and twice the adversary's successes reach
  `k`; the paper's own argument needs `2k`, two chains of `k` blocks above the target. At the
  paper's count the proven depths halve, 755 blocks against a third at 10 s instead of 1,510
  (`SLOTS.md` K.7).

---

<a id="s11"></a>
## 11. Open questions

- **A bound for the nonce rule without the delay.** The decisions an adversary takes before the
  cut-off, its own blocks published or withheld and honest minima removed, are estimated in
  hindsight, not bounded. Under the delay of [§13](#s13) those decisions are blind, and the values
  the adversary sees while it can still choose them are bounded within the walk's model for a
  stated number of delay evaluators; the lemma that carries the count into Praos's and Genesis's
  theorems is stated and proved there. What remains is the sequentiality assumption itself and the
  number of evaluators an adversary runs.
- **The inference's correction.** A period of withholding deflates the inferred stake by the
  adversary's share, raises every worst-case depth and takes the private attack under random delay
  past the convention ([§12](#s12), G7). A cap on the correction an epoch prices the deflation and
  extends the density floor, and stalls that floor as long after stake genuinely leaves: at 5 % a
  deflation by a third takes 36 days of withholding, a side of 0.3 stays provisional for 62 days,
  and finality under the density form stalls for 50 days after the active stake halves. No cap
  separates a split from a fall, since the inference reads them alike ([§3.3](#s33); `SLOTS.md`
  K.8). The recommended depth form gains almost nothing from a cap, and at 18 hours it holds a
  third after a deflation.
- **The nonce rule's other channels.** The inferred stake moves without changing the nonce, by
  one lottery threshold step per block the adversary withholds. Choosing the level is worth under
  half a percent of the adversary's wins, and under the delay the choice is blind; the deflation
  itself is the lever ([§12](#s12), G7).
- **Recovery in a partition.** No density test tells a third's withheld fork from an honest third
  ([§6](#s6)). Whether any local test can, and what a node should do when its own chain was sparse
  over the window, is open.
- **Blend's relays.** Relays that hold every honest block for the longest mixing delay cost 3–8 %
  of depth, and holding to the sender's deadline 14–23 % against a third with no exposure; a third
  of the relays dropping what they carry sends half of the honest blocks through the sender's
  fallback, in the clear, and costs 47 % with two copies and 62 % with one ([§12](#s12), G6).
  Open: the share of the relays an adversary can run, which the service declaration prices, not
  its stake.
- **Turnover in Cryptarchia itself.** The recovery horizon rests on how fast staked notes are spent,
  measured elsewhere at 0.05–0.3 % a day, and on how many of their old keys an adversary could buy.
  [§6](#s6) gives the horizon against turnover when every freed key is bought;
  `SETTLEMENT.md` (B5, B6) also when a tenth is.
- **The emission budget.** Votes and the DAG both pay in Blend cover traffic. Which multiple is
  acceptable is a budget decision, not a measurement.
- **Peras's proofs** for Poisson seat counts and for votes delayed by Blend (design (a)).
- **A safety proof for a weight of every honest block** below the balancing attack's edge, which
  retraction puts below a third at today's block rate; the bound from convergence opportunities
  covers up to 0.223 of the stake at 10 s ([§9](#s9)).
- **An eclipse of a day.** Under the recommended floor a node cut off with a third of the stake
  fixes the fork it is shown after 1.05 days, and one cut off with a tenth after 3.5; counted in
  blocks, 2.2 and 7.4 days. How long an eclipse an adversary can hold against a node is open.
- **Delay past 15 s.** At 18 hours `K` holds a third without grinding up to 15 s of worst-case
  delay, 17.4 hours, and not at 20 s, 33.5 hours. Delivery later than `Δ`, under honest mixing one
  block in a hundred at the specification's Blend, lies outside the bound.
- **The depth bound's count.** LCanalysis freezes its upper bound at half the count the paper's
  argument needs. Whether the depths in blocks should take the paper's count, which halves them,
  rests on that argument; the study keeps the code's (`SLOTS.md` K.7).
- **A worst-case bound for the count of occupied slots.** Under the worst case the floor stays at
  the canonical count, since no larger lower bound on the honest chain's occupied slots is derived.
  Such a bound would raise the floor by up to a fifth and let it separate partitions under the
  worst case as it does under random delay ([§3.3](#s33); `SLOTS.md` K.9).
- **Proving on the reference node.** The proving time on a Raspberry Pi 5, which
  `tools/benchmarks/pol-proving` measures.

[§13](#s13) takes up recovery in a partition, the delay function and time under the worst case:
recovery attestations separate partitions below a third while Blend's relays deliver the votes,
and nothing separates one at a third; the delay function must span the last sub-window, 4.5 hours
on the adversary's hardware at `k = 2160`, with the contribution bound to the parent's
contribution; a time-reading rule under the worst case is the counting bound read with the forks
the client sees, 408 blocks against a third, which holds `ε` per target by computation.

---

<a id="s12"></a>
## 12. Further routes

Six ways to shorten finality that the routes of [§1](#s1) do not cover, and two checks on the
figures (`FURTHER.md`; phase J in `DAG.md`), each read against 30 % and a third at `ε = 1e-9`:

| route | what changes | what it buys | what it costs |
| --- | --- | --- | --- |
| a delayed nonce (G1) | the nonce of [§3.1](#s31) passes through a sequential delay that spans the last sub-window, 4.5 hours on the adversary's hardware at `k = 2160`, with the contribution bound to the parent's contribution | the adversary decides blind before the cut-off; at a margin of ten minutes the contributions of [§3.1](#s31), which it knows ahead, leave a factor per nonce of 1.005–1.054, and the chained contribution 1.002–1.04; against a third at 10 s the depth is 1,511 blocks at `k = 2160` sampled and 1,523 as a bound (23.0–23.2 h), instead of an estimated 1,859–1,939; `k = 1620` holds a third and `k = 1080` holds 30 % unless the adversary runs more than 7,800 and 450,000 delay evaluators | a sequential computation of about a day once an epoch, 22 hours at a speed ratio of 5 and `k = 2160`, by whoever first needs the nonce, with a proof published before the nonce is first used |
| the epoch apart from `k` (G2) | the epoch keeps its length when `k` shrinks | at `k = 1080` the nonce's sub-windows, the recovery window (72 h) and the horizon stay those of `k = 2160` | one more parameter; a stake snapshot that stays 7.5 days old |
| Blend's delay (G3) | the Blend setting | from the specification's setting (`Δ = 11` s, its p99 rounded up) to testnet's (2 s), the worst-case depth against a third falls from 1,649 to 812 blocks (25.5 to 10.5 h) and the random-delay depth from 276 to 172 (4.1 to 2.2 h); one hop of three rounds (4 s) gives 936 (12.7 h); with the nonce under G1's delay each depth grows by at most 1 % at 16 s and less, by 7 % under the worst case at 24 s and by 29 % under random delay at 34 s | anonymity, in the Blend report's terms: one hop exposes the whole path of one message in three to an adversary holding a third of the nodes, three hops one cascade in 27, about one block in 14 with the specification's two copies; one round of mixing blends 3/7 of what three rounds do |
| settlement on a chain nobody withholds from (G4) | a client rule; nothing in consensus | the elapsed-time rule of [§3.2](#s32) settles such a chain in 39 / 53 minutes against 30 % / a third on the specification's Blend, against the depth rule's 98 / 163; with the rates the total-stake inference leaves after a period of withholding, and the depth rule as a cap, 66 / 106 minutes | the rule's rates must follow the inference: after a period of withholding every rate rises by `1/(1 − α)`, and the elapsed-time rule of [§3.2](#s32) then understates the adversary; on a chain the adversary withholds from the safe rule is the depth rule, whose random-delay table covers an inference that is not deflated (G7); random delay only |
| anchoring (G5) | a checkpoint written to another chain | a timestamp: it settles forks that did not exist when the anchor was written, a long-range fork from bought keys and the history offered to a node starting from genesis, never a partition, since an anchor does not show a block was public and an adversary can anchor its private fork first ([§13](#s13)); finality at the anchor interval plus the other chain's | a dependence on another chain; a rule for conflicting anchors; not measured |
| the inference as a lever (G7) | nothing; a check on every worst-case figure | nothing: a period of withholding, 4.5 days at `k = 2160`, lowers the inferred stake by the adversary's share and raises every threshold by `1/(1 − α)`; `Δ = 10` s then reads as `10/(1 − α)` s and the proven depth is 2,426 blocks against a third (27 hours) and 1,248 against 30 %, so `k = 2160`, `k = 1620` and `k = 1080` hold their shares only while the inference is not deflated; under random delay the private attack's race on the engine then needs 189 / 334 blocks against 30 % / a third, where it needed 158 / 257, past the convention's 165 / 276, in less time, and with relays that hold to the sender's deadline 240 / 473 | a cap on the correction, 5 % a period, prices the deflation at 36 days and slows the response to stake that leaves alike; a client can read the worst-case table at `Δ` divided by what remains of the inferred stake |
| adversarial relays (G6), a check on the random-delay model | the adversary's relays hold every honest block for the longest mixing delay or to the sender's deadline, or drop it; one copy of each block or the specification's two | holding: +3–8 %, 257 to 274 blocks against a third with one copy; to the deadline 317 with one copy and 273 with two; the report's 165 and 276 cover holding against a third with one copy released at the slot, and neither holding against 30 % (167), the deadline (186, 317), holding in the specification's setup of two copies released a round after the slot (170, 282) nor holding under deflation (204, 367); dropping: the depth is 352 with two copies, +47 %, and 416 with one, +62 % | none for holding, which exposes no one; dropping exposes nearly every honest leader within an epoch, since the fallback sends half the blocks in the clear; the lever is the adversary's share of the relays, which the service declaration prices |
| a fork choice that tolerates delay (phase J) | each side of a fork weighed by its wins since the closest common ancestor, one weight per win: the chain with its uncles weighed, or the DAG | against a third nothing: an adversary that places and retracts its wins keeps two sides level for ever under either tie rule, at every delay, so neither an attack depth nor a bound exists; with one move per win, which no rule every node applies alike enforces, the strongest attack would need 2.8 hours at 1 s and 5.0 at 10 s against the chain's 3.5 and 6.8; against 25 % at 1 s the bound needs 14.2 hours, the chain's 3.3 | a new fork choice, a tie rule every node applies alike, and the bound that does not exist |

**Counted in slots** (`FURTHER.md`). G3: from the specification's Blend to testnet's, the
worst-case wait against a third falls from 11.2 to 5.1 hours at G3's setting, and under random delay
from 5.1 to 2.9. G4: a wait reads no rate, so it gains nothing on a chain nobody withholds from. G6:
hostile relays cost more as a wait than as a depth, since they slow the honest chain the wait must
cover: against a third, relays that hold to the sender's deadline cost 27 % with one copy, and
relays that drop cost 56 % with two copies and 73 % with one. G7: a deflation lengthens the
guaranteed wait against a third at 10 s by 23 %, shortens it at 1 s, from 4.7 to 3.4 hours, and
shortens it under random delay (`SLOTS.md` K.2, K.7). A cap on the correction prices the deflation
in epochs, and lengthens the density floor's protection at the rate it lengthens its stalls
([§3.3](#s33); `SLOTS.md` K.8).

**A delayed nonce.** The decisions of [§3.1](#s31) before the cut-off are worth something only if
the adversary can compute the nonce each outcome gives before it must act, and a blind choice among
`G` nonces gains nothing. It can compute an outcome's nonce from the moment the inputs are known:
for the last sub-window, from the sub-window's start, 4.3 hours before the cut-off at `k = 2160`,
since the earlier minima are fixed by then and it knows its own contributions ahead. The delay
must therefore span the sub-window, and a value counts only if the adversary sees it while it can
still publish a fork that reaches it. A choice is still open ten minutes after the cut-off in 30 %
of epochs against a third under the worst case, and in 14 % at twenty, since the adversary's lead
at the cut-off adds to what it gains after. The contributions of [§3.1](#s31), which the adversary
knows ahead, then leave a factor per nonce of 1.005–1.054 at a margin of ten minutes. With the
minima taken over a contribution bound to the parent's contribution, `c(b) = hash(NONCE_CONTRIB_V2 ‖
c(parent) ‖ ρ_LEAD(b))`, which every node derives from public values while `ρ_LEAD` stays the win
tag it is today, a value of the adversary's branch exists only once the block the branch forks
from does. That also replaces the binding to the epoch nonce and the notes frozen one epoch
earlier, and the factor is 1.002–1.04. The depths are [§3.1](#s31)'s "not ground" row within two
blocks sampled at `k = 2160`, and within thirteen as a bound that grows with the delay evaluators
the adversary runs. Honest nodes compute `R·(W + margin)` for a speed ratio `R`: 22 hours at
`R = 5` and `k = 2160`, 11 at `k = 1080`, within the `4⌊k/f⌋` slots before the nonce is first used
up to a ratio of 15 to 16, counting the squarings. Phalanx's 82 independent pieces do not serve:
one piece takes 53 s on the adversary's hardware.

**A chain nobody withholds from.** A private attack withholds the adversary's blocks from the
target's parent on, so during an attack the canonical chain runs at the honest rate; a chain nobody
withholds from runs at the full rate, and a client that reads time sees the difference. The
elapsed-time rule of [§3.2](#s32) therefore settles such a chain in 39 / 53 minutes against 30 % /
a third, where the depth rule needs 98 / 163 at the same rate. The adversary cannot inflate the
density: a block that extends the public tip lengthens the chain its private one must beat, and a
block that ties an honest one replaces it. But the total-stake inference sets the lottery's
thresholds from the previous period's occupied slots, so an adversary that withholds for a whole
period, 4.5 days at `k = 2160`, lowers the inferred stake by its share and every rate rises by
`1/(1 − α)`: the honest stake alone then produces at the full rate, and the adversary wins faster
than the rule assumes. The race's ratio is unchanged, and so is the depth rule in the report's
convention; on the engine the deflated race needs the depth of a chain on which every node
produces, past the convention, and the worst case moves it further, since its delay is fixed in
slots (G7). The safe elapsed-time
rule takes the adjusted rates and the depth rule as its cap: 66 / 106 minutes on a chain nobody
withholds from (played on timelines, 65 / 103 on average and 90 / 141 at the 90th percentile),
and the depth rule's time on one the adversary withholds from. A rule that reads the density
directly accepts later than the elapsed-time rule and adds nothing to it. With the delayed nonce
of G1 the recovery horizon of [§6](#s6) is the unground one in every cell.

---

<a id="s13"></a>
## 13. Three designs

The three questions [§12](#s12) leaves open, each with a hypothesis that can fail (`DESIGNS.md`;
`PLAN.md` H8–H10, and H11–H13 for what the designs rest on):

**Recovery in a partition (H.1).** No rule that reads chains and their stake-weighted content can
tell a third's withheld fork from an honest third: after an even partition the three chains follow
the same law, and such a rule picks the fork with probability at least a third. Below a third the
honest sides hold `(1 − α)/2` each, and a one-off round of anonymous-seat votes, cast only when a
node holds two chains both deeper than `k` since their divergence, separates them: a chain is kept
when its seats exceed a threshold, the densest kept chain wins. A round of 2,300 expected seats
separates a quarter at `1e-9`; 15,000 separate 30 % if every honest vote counts, 158,000 if a tenth
are lost; 32 % needs 95,000 with every vote counted; a third none. The round needs relays that
deliver: relays at the adversary's share that drop what they carry lose 58–66 % of single-copy votes
against 25–30 %, and 33–43 % with two copies. Then no round separates a quarter or 30 % unless the
lost votes fall back to direct broadcast, which identifies their voters. The adversary can choose
which honest history survives, never its own. Anchoring a checkpoint to another chain timestamps a
block and does not show it was public; it settles forks older than the anchor and the start of a
bootstrapping node, not a partition. Rule 8's test serves as a partition detector: against 30 %
over 36 hours a side holding up to 0.57 of all stake is declared sparse with chance 0.9999 or more,
one of 0.6 with 0.926, and the whole honest chain once in `10^9` windows; a node whose chain is
sparse reports `B_imm` as provisional. It reads a side only while the side runs at the thresholds
set before the split, at least 3 days at `k = 2160`; within 7.5 to 15 days each side's inference
has corrected, and every chain, the adversary's fork included, fills its slots at `f`. Counted in
slots, a density floor on `B_imm` is the same quorum with blocks as the votes. It separates a
quarter only at windows of days, since a delay costs the honest chain blocks and costs a side the
adversary fills nothing; seats are drawn in proportion to stake whatever the delay (`SLOTS.md`
K.3).

**The delay function (H.2).** In Praos's model a choice among nonces the adversary has not
evaluated is blind and costs nothing, and a choice among evaluated ones multiplies the failure
probability by their expected number. A candidate nonce of the last sub-window can be evaluated
from the sub-window's start, so a delay of ten minutes blinds nothing and leaves the estimate of
[§3.1](#s31). The design that works spans the sub-window, `T_a = W + margin`, 4.5 hours at
`k = 2160` with a margin of ten minutes, and takes the minima over a contribution bound to the
parent's contribution, `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`, which every node
derives from public values and which leaves `ρ_LEAD` the win tag it is today. A value of the
adversary's branch then exists only once the block it forks from does, and the proof of leadership
is unchanged. Bound to the parent block itself, a branch takes a contribution for every body
variant the adversary computes; bound to the parent's own tag, a block on the adversary's own win
has a value known ahead, which does worse than no binding. The chained contribution leaves a factor
of 1.009 against a third under the worst case at `k = 2160`, sampled, and as a bound the walk's
1.08 plus 0.016 for a blind switch plus `1.6·10^-6` for each delay evaluator. Honest nodes pay
`R·T_a` for a speed ratio `R`. The documented ratio is 3 to 5: Chia's class-group ASIC squares in
about 1 µs against 3.85 µs on the fastest CPU and 4.7 µs on a commodity one, and the 10 that
CIP-0161 assumes is attributed to Ethereum's `A_max`, which measured an attacker against commodity
ASICs. At a ratio of 5 the honest computation is 22 hours at `k = 2160` and 11 at `k = 1080`,
`1.7·10^10` squarings of one core once an epoch, and the `4⌊k/f⌋` slots before the nonce is first
used hold a ratio of 15 to 16 counting the squarings. The design: the hash of the sub-window
minima, fixed at the cut-off, passed through sequential squarings in a class group of a 1,024-bit
discriminant, the output hashed into the nonce, with a Wesolowski proof of one group element
published within the phase and verified in 2–4 ms in place of the computation. MinRoot and the
other field-root candidates are broken; squaring in a group of unknown order is not. Praos and
Genesis bound the nonce's bias by a union bound over the candidates the adversary can set it to and
then bound the candidates by its oracle queries; the rule bounds the same count by the candidates
whose values the adversary sees while it can still choose them, and Genesis's theorem for the
Bootstrap rule adds to Praos's only a term in `k` and the density window, so the lemma stands under
both of Cryptarchia's rules. The discrete logarithm in the class group of a 1024-bit discriminant
costs `2^91.4` operations by Biasse, Jacobson and Silvester's table, between NIST's 80- and 112-bit
levels, and `2^101.4` by their stated method, with the class group up to 1.6 times that: two
hundred thousand to three hundred million machines of `10^18` operations a second within the
delay. 2048 bits give `2^139.4` and `2^149.4`, at no cost in time if the speed ratio holds there. A
proof still needs the formal write-up and the sequentiality assumption itself.

**Time under the worst case (H.3).** The delay-scheduling attack behind the lower bound of
[§4](#s4) beats the elapsed-time rule of [§3.2](#s32) in 51–58 % of the targets the rule accepts at
`ε = 1e-3`, 2.2–2.7e-2 per target: an adversary that schedules delays controls the clock the rule
reads, so the chain's speed is not evidence. A counting bound is: every block of a competing chain
is a distinct win, the adversary's or an honest one not on the canonical chain, so with `n`
canonical blocks in `t` slots the competing chain leads by at most `2A(t) + H(t) − 2n` plus the
worst-case lead. It holds for every strategy within `Δ`, and it bites only on a fast chain: 574
blocks against a third at `1e-9` when the chain runs at the full rate, where the proven depth is
1,510, and nothing at the rate of a chain the adversary withholds from. A client can count the
honest wins instead of taking their mean: an honest block that descends from the target sits on no
chain without it, so the competing chain's honest blocks are among the forks the client has
received, counted once a slot, plus those of the last `Δ` slots. The observed counting rule,
`L + A(t) + forks + H_late` against `n` with `t` read on the client's clock, settles at 408 / 226 /
120 blocks against a third / 30 % / a quarter under a worst-case delay, 6.2 hours against a third,
and at 374 / 209 / 112 on a chain the adversary withholds from without delaying it, a quarter of
the proven depth; each fork costs 2–3 blocks, and 3.5–4.4 % of targets see two or more. It holds
`ε` per target, not given the client's view, and a wait of [§4](#s4), which reads time alone,
holds by B2's bound at the depth it guarantees: with the worst-case walk's law an adversary that keeps
its chain private until acceptance, and times it as it likes, fails at most 0.10 ε at `1e-3` and
0.0018 ε at `1e-9`, where the rule's own geometric law would allow 1.13–1.16 ε. The delay-scheduling
attack, with every honest block off the client's chain counted as a fork, makes it accept no
target. An adversary that balances the honest chain, its own blocks counted as forks, stalls it
from a quarter up, and one that publishes every win as a fork stalls it at 30 % and a third, at the
cost of its rewards; the depth rule caps it. A time-conditioned form of the proven bound is not
derived.

---

<a id="s14"></a>
## 14. Reproducibility

```
cd tools/simulators/finality
make install          # a virtualenv with the TSI engine and the study's package
make test             # every gate
make mutations        # each gate fails on its registered mutation
make all              # every run; the settlement bounds take about 25 minutes on 14 cores
make tables           # every table of the notes, from runs/
make check-tables     # each table appears verbatim in a note
make octave-reference # the original LCanalysis in Octave, in the background, for hours
```

`make a1` also compares the random-delay convention with the engine's own arms
(`scripts/a1_convention.py`); `make further` plays the engine's arms of G6 and G7; `make designs`
counts the values an adversary sees while it can still choose them (H.2, `finality_sim.formation`)
and plays the observed counting rule against adaptive timing (H.3, `finality_sim.adaptive`).
Phase J's fork choice has its own targets: `make j1` counts the proof of leadership's constraints
(`scripts/j1_circuit.py`), `make j2` plays every attack within `Δ` with one and two moves per win
(`finality_sim.delayfc`, `scripts/j2_attacks.py`; it needs `make b2` and `make e5`), and `make j3`
computes the published regions and the bound from convergence opportunities
(`finality_sim.convergence`, `finality_sim.cobound`, `scripts/j3_regions.py`,
`scripts/j3_bound.py`).

Phase K counts finality in slots: `make k1` gives the waits (`finality_sim.slots`), `make k2` what
each `K` holds with grinding and a deflated inference, `make k3` eclipses, splits and the floor
(`finality_sim.floor`), and `make k5` the nonce's coverage and the other notes read in slots
(`finality_sim.slotmap`). `make k7` bounds a wait in the model of Gaži, Ren and Russell on the slot
lottery and reads K.2 to K.5 again under it (`finality_sim.waitbound`; it needs `make k1`, `make k2`
and `make k5`), `make k8` caps the inference's correction (`finality_sim.cap`), and `make k9` reads
the floor on occupied slots, as the stake inference counts.

Proving is timed apart, on the machine at hand: `make run` in
[`tools/benchmarks/pol-proving`](../../tools/benchmarks/pol-proving) writes to
[`pol-proving/`](pol-proving).

The notes carry each result with its gate: `MAPPING.md` (what depends on `k`), `RATE.md` (block
rate and orphans), `SETTLEMENT.md` (bounds, races, a smaller `k`, recovery, grinding, the nonce),
`CERTIFIED.md` (votes), `DAG.md` (Areon), `FURTHER.md` (the routes of [§12](#s12)) and
`DESIGNS.md` (the designs of [§13](#s13)) and `SLOTS.md` (finality counted in slots). `PLAN.md` records the questions the study was asked to
answer, its hypotheses and the verdict on each.
