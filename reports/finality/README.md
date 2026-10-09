# Faster finality for Cryptarchia

*This study asks how much sooner a Cryptarchia block can be relied on, and by which means, against
an adversary holding at most a third of the stake. Every number
the study computes comes from a `make` target of
[`tools/simulators/finality`](../../tools/simulators/finality); the study's notes there carry the
derivations, gates and full tables. The turnover rates of other chains, Blend's verification
budget, the proving times and Ouroboros Phalanx's parameters are read from the sources the notes
cite. Specifications are read at `logos-lips` `47a73cdc`, the node at `logos-blockchain`
`4e0405d51`. One slot is one second and `f = 1/30` unless stated.*

---

## Contents

- **[1. Summary](#s1)** — every route against 30 % and a third, and the three worth taking
- **[2. What is measured](#s2)** — finality notions, adversary, delay models, the engine
- **[3. The three routes in depth](#s3)** — the nonce, a settled level, a smaller `k`
- **[4. Settlement on the chain](#s4)** — the client rule
- **[5. The epoch nonce](#s5)** — grinding, and two ways to stop it
- **[6. A smaller `k`, and recovery from a split](#s6)**
- **[7. Block rate, orphans and fork choice](#s7)**
- **[8. Certified finality](#s8)** — anonymous votes
- **[9. The multi-proposer DAG](#s9)** — Areon
- **[10. Findings about the protocol as it stands](#s10)**
- **[11. Open questions](#s11)**
- **[12. Further routes](#s12)** — a delayed nonce, the epoch apart from `k`, Blend's delay, density, anchoring
- **[13. Three designs](#s13)** — recovery in a partition, the delay function, time under the worst case
- **[14. Reproducibility](#s14)**

---

<a id="s1"></a>
## 1. Summary

A Cryptarchia block is final once `k = 2160` blocks lie on top of it: 21 hours on the
specification's Blend, and 30 to 33 hours while 30 % to a third of the stake withholds its blocks.
The study measures seven ways to shorten it, under two delay models: random Blend delays, and a
worst case in which an adversary delivers each honest block as late as a bound `Δ` allows. It
reads them against an adversary holding a share `α` of the stake, 30 % and a third, at a failure
probability `ε = 1e-9` per block. Times are on the honest chain while the adversary withholds its
blocks, one clock per delay model ([§2](#s2)), on the specification's Blend (3 hops of up to 3
rounds), whose worst case is taken at `Δ = 10` s. Random-delay figures are the private attack's;
worst-case figures are proven against every attack.

| route | what changes | time until final, 30 % / a third | what it costs | verdict |
| --- | --- | --- | --- | --- |
| a nonce that resists grinding ([§5](#s5)) | the epoch nonce taken from the smallest contributions of 25 sub-windows | removes most of the depth grinding adds: with today's nonce, against an adversary that evaluates `2^64` nonces an epoch, the depths grow 2.7 to 4.5 times; passed through a sequential delay that spans a sub-window ([§12](#s12), G1; [§13](#s13), H.2) it leaves the choices at the cut-off alone, a factor of at most 1.08, as a bound within the model | a hard fork; a window before the cut-off of at least 54 hours (`6⌊k/f⌋` at `k = 1080`), the shortest measured at which the choices at the cut-off stay near one; without the delay, notes frozen one epoch earlier; with it, the contribution bound to the parent block and a sequential computation of about a day once an epoch | recommended, with the delay; the others depend on it |
| settled level ([§4](#s4)) | a client depth; nothing in consensus | random delay: 2.6 / 4.8–4.9 h, and 1.5 / 2.4 h reading elapsed time (measured with a nonce that is not ground); guaranteed at 10 s: 15.5–15.9 / 28.3–29.5 h | nothing | recommended |
| smaller `k` ([§6](#s6)) | `k`, and a recovery trigger | `k = 1080` against 30 %, guaranteed at 10 s: 15.8 h, at the edge (an estimated 1,060–1,093 blocks against 1,080) and only while the inference is not deflated ([§12](#s12), G7); against a third no `k` below 2160; with the delayed nonce of [§12](#s12), `k = 1620` holds a third and `k = 1080` holds 30 % as bounds | a recovery window of 36 hours; a look-back horizon of months; a partition deeper than `k` needs a one-off vote round below a third ([§13](#s13)) and operators at a third | not recommended until the nonce's factor is bounded and the trigger is partition-safe; both have designs in [§12](#s12) and [§13](#s13) |
| faster blocks ([§7](#s7)) | `f` | random delay, against a third: 160 minutes at 30 s blocks, 144 at 15 s, by the race's fit | ×2.0 the blocks at 15 s | not recommended: little gain from 30 % |
| regular block intervals ([§7](#s7)) | the lottery becomes a curve of the slots since the parent | against a third Topl's shape needs more than 60 blocks at `1e-3`, today's lottery 58 | a third more blocks; a new stake inference | not recommended |
| certificates ([§8](#s8)) | anonymous-seat votes through Blend | no committee against a third; against 30 %, 33,473 seats while every honest vote counts | ×1,675 Blend cover at 10-minute rounds | not recommended |
| multi-proposer DAG ([§9](#s9)) | replaces the chain and its fork choice | random delay, at today's block rate, against a third: 106 minutes, the chain 160 by the same fit | as the chain at that rate | not recommended: no proof; faster rates fall to a balancing attack below a third |

The worst-case figures hold while the inferred stake is the true stake. An adversary that
withholds every block for one period, 4.5 days at `k = 2160`, lowers it by its share and raises
every lottery threshold for the next epoch; the proven depth at `Δ = 10` s is then B2's at
`10/(1 − α)` s, 2,426 blocks against a third and 1,248 against 30 %, so `k = 2160` holds a third
only while the inference is not deflated ([§12](#s12), G7).

Two routes are worth taking now, and a third once two things are settled ([§3](#s3)):

1. **A nonce that resists grinding.** With today's hash-chain nonce, an adversary that withholds
   its wins picks the next epoch's leader schedule among many. Against 30 % and a third the depths
   then grow 2.7 to 4.5 times. At `Δ = 10` s `k = 2160` can no longer be proven against 30 % once
   the adversary evaluates `2^40` nonces an epoch, nor against a third from `2^8`. Taking the
   nonce from the smallest contribution of each of 25 sub-windows, with notes frozen one epoch
   earlier, cuts the factor per nonce from up to `6·10^14` to an estimated 5.9–7.3 against a third
   under random delay and 10.6–18.1 under the worst case. `k = 2160` absorbs a factor of 81. A
   delay function does as well only if an adversary can evaluate about two nonces an epoch.
2. **A settled level in the node's API.** A client accepts a block once the depth for its share
   `α`, failure probability `ε` and delay model lies on top of it. It accepts sooner if it also
   reads the time the blocks took. With the nonce of route 1, against a third this is 4.8–4.9 hours
   under random delay and 28.3–29.5 hours guaranteed at 10 s. Reading elapsed time takes 2.4 hours,
   measured with a nonce that is not ground.
3. **A smaller `k` with automatic recovery.** With the nonce of route 1, the worst case at 10 s
   needs an estimated 1,060–1,093 blocks against 30 %, so `k = 1080` holds 30 % only under the
   smaller estimate: 15.8 hours. Against a third no `k` below 2160 holds. The recovery trigger heals
   an eclipse through a density test whose window is 36 hours at `k = 1080`. It cannot heal a
   partition deeper than `k`: no density test tells a third's withheld fork from an honest third.
   The route waits for a bound on the nonce's factor and a partition-safe trigger.

Specification candidates follow from them:

1. **The epoch nonce from the smallest contributions** of sub-windows, with the contribution
   `ρ_LEAD` bound to the epoch nonce and notes frozen one epoch earlier, or, under the delay of
   [§13](#s13), bound to the parent block ([§3.1](#s31)). A bound on its factor without the delay
   is open.
2. **A settled level** beside the tip and `B_imm`: the depth table, and the elapsed-time rule under
   random delay ([§3.2](#s32)).
3. **Two corrections to the Bootstrap rule** ([§10](#s10)): its depth test should read the deeper of
   the two branches, and its density window should be sized for `(α, ε)` rather than tied to `k`.
   Both bear on testnet, which runs `k = 120`.
4. **An automatic-recovery trigger** with eight rules, for eclipses, if `k` is to shrink
   ([§3.3](#s33)).

Five further routes are read in [§12](#s12). One of them, the nonce of route 1 passed through a
sequential delay that spans the last sub-window, 4.5 hours on the adversary's hardware at
`k = 2160`, with the contribution bound to the parent block, leaves the adversary the choices at
the cut-off alone: the depths return to within eleven blocks of a nonce that is not ground, a
bound within the model, and `k = 1620` holds a third and `k = 1080` holds 30 %. Honest nodes
compute the delay in about a day.

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

**The adversary** holds a share `α` of the stake, reported from 5 % to a third. The design must
hold against a third, and 30 % at the loosest; the summary and [§3](#s3) read the results there.
`ε` is per block for settlement and per round for votes.

**Two delay models** are reported side by side:

- **Random delay.** Blend's mixing delays, measured in the per-node engine of the total-stake
  inference study (TSI): 1,000 nodes, a degree-6 peering graph, geographic links, and each relay
  holding a message a whole number of rounds as the node's release delayer does. Testnet 0.3.0
  runs 1 hop of 1 round; the specification allows 3 hops of up to 3 rounds. The specification's
  Blend orphans 18 % of blocks and delivers a block to every node within 10.2 s at the 99th
  percentile.
- **Worst case.** An adversary delivers every honest block as late as a bound `Δ` allows. The
  bounds of Gaži, Ren and Russell ("Practical Settlement Bounds for Longest-Chain Consensus",
  ePrint 2022/1571, revision 2025-05-02) apply. Their code is ported, checked against their Table 1
  and against the original run in Octave, and computed at every depth. `Δ = 10` s is a chosen
  bound, equal to the honest Blend's 99th-percentile delay. Delivery later than `Δ`, one block in a
  hundred under honest mixing and any delay an adversary adds at relays, lies outside the bound.
  Against a third the worst-case depth grows about 9 % per second of `Δ` near 10 s.

**Times** are counted on the honest chain while the adversary withholds its blocks, one clock per
delay model. Under random delay a block takes `30 s / ((1 − α) · g)`, where `g` is the canonical
growth the engine measures: on the specification's Blend 50.7 s against 30 % and 53.2 s against a
third. Under the worst case the chain grows one block per `Δ + 1/p_h` slots, `p_h` the honest
stake's chance to win a slot: at 10 s, 52.6 s against 30 % and 54.7 s against a third.

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
([§5](#s5)). The depth that holds `ε = 1e-9` under each factor, with two ground nonces:

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

**What it needs.**

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

**What it buys.** Against a third under the worst case at 10 s, the guarantee needs an estimated
1,859–1,939 blocks at `k = 2160`, against 5,732–6,287 with today's nonce: 28.3–29.5 hours instead
of 87–96. Under random delay on the specification's Blend it needs an estimated 326–333 blocks
instead of 1,171–1,245: 4.8–4.9 hours instead of 17–18. `k = 2160` holds a third up to a factor of
81 per nonce.

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
sub-window, so a delay that spans the sub-window, with the contribution bound to the parent block,
removes the decisions before the cut-off ([§12](#s12), [§13](#s13)).

**What is shown, and what is not.** The choices at the cut-off are counted against an enumeration
of every fork and every subset of withheld wins, under the condition of `SETTLEMENT.md` B6 for a
fork to win. The worst-case depths read the proven bound of Gaži, Ren and Russell. Open:

- a bound on the decisions before the cut-off, which are estimated in hindsight;
- the inferred stake, which the adversary moves by withholding blocks without changing the nonce,
  one lottery threshold step per block;
- a proof of the rule in the model of Praos's or Genesis's analysis; under the delay, [§13](#s13)
  reduces it to a bound on the choices at the cut-off.

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
[§3.1](#s31) at `k = 2160` and its estimated factor. Hours are on the clocks of [§2](#s2). The
elapsed-time rule is measured with a nonce that is not ground, on the engine's timelines, where the
depth rule's mean is 2.2 / 3.9 h:

| delay | depth rule | reading elapsed time, mean / 90th percentile | `k = 2160` |
| --- | --- | --- | --- |
| random, specification's Blend | 187–189 / 326–333 blocks: 2.6 / 4.8–4.9 h | 1.5 / 2.4 h, 1.9 / 3.2 h | 30.4 / 31.9 h |
| worst case, `Δ = 10` s | 1,057–1,088 / 1,859–1,939 blocks: 15.5–15.9 / 28.3–29.5 h | the observed counting rule with no forks, 209 / 374 blocks: 2.9 / 5.4 h ([§13](#s13)) | 31.6 / 32.9 h |

**What the client accepts.** The adversary's share; the delay model; the grinding its depths
include; a view that is not eclipsed. Under random delay also: the adversary withholds every win
and never extends the public chain, Blend's delays are not the adversary's to choose, and the
honest chain grows as the engine measured. Under the worst case only the depth rule applies. The
elapsed-time rule's rates hold while the inferred stake is the true stake; after a period of
withholding the total-stake inference raises every rate by `1/(1 − α)`, and the rule must take
those rates, with the depth rule as its cap. It then settles a chain nobody withholds from in
66 / 106 minutes against 30 % / a third, and a chain the adversary withholds from at the depth
rule's depth ([§12](#s12), G4).

**What is shown, and what is not.** The worst-case depths are the proven bound. The random-delay
depths are the private race with a premined lead, in closed form. The race played on the engine's
timelines matches it within three blocks at `1e-3` up to 30 %; against a third the closed form
over-asks by about a quarter ([§4](#s4)). On the engine's timelines both rules hold `ε` where it
can be measured, at `1e-3`: against 30 % the race beats the elapsed-time rule on 1.1e-3 of 78,696
targets, consistent with `ε`. Under the worst case the rule that reads time is the observed
counting rule of [§13](#s13): 374 blocks against a third when the adversary withholds, where the
depth rule needs 1,510. Open: both rules against an adversary that also extends the public chain.

<a id="s33"></a>
### 3.3 A smaller `k` with automatic recovery

**What `k` must cover.** `k` binds every node, so it must hold under the worst case. With the nonce
of [§3.1](#s31) the worst case at 10 s needs an estimated 1,060–1,093 blocks against 30 % at
`k = 1080`. `k = 1080` holds 30 % under the smaller estimate, fails it by 13 blocks under the
larger, and fails it after a period of withholding, when the inference is deflated and B2's depth
is 1,248 ([§12](#s12), G7): k-finality in 15.8 hours instead of 31.6, at the edge. Against a third it needs an
estimated 1,862–1,943 blocks at `k = 1620`, so no `k` below 2160 holds a third. With today's nonce,
`k = 2160` itself cannot be proven against 30 % at 10 s.

**What it breaks.** A split heals by itself only while the losing side has made fewer than `k`
blocks. Past that a node stays on the losing side. A restart does not return it ([§10](#s10)).
Automatic recovery compares a fork that diverges deeper than `k`, within a horizon `H`, by its
block density in a window after the divergence. Eight rules keep it safe where it can be
([§6](#s6)). The window may be at most `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake
take effect: 36 hours at `k = 1080`. The test holds only where the honest chain had its full
density over the window, which is an eclipse. In a partition deeper than `k` each honest side has
its own share, and a third's withheld fork is denser than an honest third every time. Such a split
still waits for operators.

**The horizon.** A note spent since the divergence is unspent on the fork, so its key can sign for
the fork. Over the horizon the chance that the window favours the adversary's fork must stay below
`1e-9`. With every freed key for sale at Bitcoin's turnover, 0.125–0.243 % a day, and the nonce of
[§3.1](#s31) at its larger estimate, the 36-hour window at `k = 1080` holds 30 % for 106–204 days
under the worst case at 10 s and 117–226 under random delay.

**What it costs.** A split heals only once its window has passed, 36 hours. `B_imm` may move back
within `H`, so every consumer of it needs a path for that, and the `k`-deep block is final only
against forks that lose the density test. Nodes keep block trees and ledger states back to `H`.

**What is shown, and what is not.** The trigger's eight rules come from attacks on simpler forms of
it (`SETTLEMENT.md`, B5). Its horizon rests on the turnover of staked notes in Cryptarchia, which
is not measured, and on how many old keys an adversary could buy. A forward-secure leader key would
remove that dependence. The `k = 1080` figure rests on the hindsight estimate of [§3.1](#s31).

### 3.4 The three together

With the nonce of [§3.1](#s31) at its estimated factor, one clock per delay model; reading elapsed
time is measured with a nonce that is not ground:

| against | today, random delay / worst case | settled, random delay | settled, reading elapsed time | settled, guaranteed at 10 s | `k`, guaranteed at 10 s |
| --- | --- | --- | --- | --- | --- |
| 30 % | 30.4 / 31.6 h; `k` not proven at 10 s with two ground nonces | 2.6 h | 1.5 h | 15.5–15.9 h | 15.8 h (`k = 1080`) under the smaller estimate, 31.6 h (`k = 2160`) otherwise |
| a third | 31.9 / 32.9 h; `k` not proven at 10 s with two ground nonces | 4.8–4.9 h | 2.4 h | 28.3–29.5 h | 32.9 h (`k = 2160`) |

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
- **`k = 2160` holds a third of the stake at `1e-9` only for delays up to 13 s,** without grinding.
- **A rule that also reads elapsed time settles 35–40 % sooner from 30 %.** Against a third at
  `1e-9`, on the engine's timelines of the specification's Blend, it accepts after 2.4 hours on
  average where the depth rule needs 276 blocks and 3.9 hours. Against a quarter it accepts after
  47 minutes where the depth rule needs 88 blocks and 68 minutes, and against a tenth it settles
  about a fifth sooner. It is derived for random delay only.

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
The table of [§3.1](#s31) compares them. Under the worst case at 10 s against a third, a cap of 2
nonces leaves 1,544–1,614 blocks; the smallest contributions leave 1,518 at the cut-off and an
estimated 1,859–1,939 with the decisions before it, at `k = 2160`.

---

<a id="s6"></a>
## 6. A smaller `k`, and recovery from a split

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
   density with probability 0.5–0.7 % at the longest windows, and under a strict order would never
   heal.
8. Compare only from a chain that had its full density over the window. Every window and horizon
   here gives the honest chain the whole honest stake. In a partition each honest side produces
   with its own share, and the adversary withholds a fork made with all of its stake: against an
   honest side holding 35 % of all stake, a 30 % adversary's fork is denser in 64–70 % of the
   specification's windows, and against an honest third, a third's fork always is. Today the Online
   rule caps what such a fork reorganises at `k`. A node whose chain was sparse over the window
   therefore does not compare, and leaves the split to operators, as today. The trigger heals an
   eclipse, where one side is the whole honest chain, and not a partition deeper than `k`.

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
  `f_A = 0.25`, where with 10 % three attempts in four hold the balance for a day. Against a third,
  only today's block rate stays out of its reach. No proof covers the DAG below that edge.
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
  holds a third; under random delay the depth is 404 blocks where it was 276, in less time. A cap on
  the correction of 5 % a period prices the deflation at 36 days of withholding
  ([§12](#s12), G7).
- **The bound's reference code needs more phases at depth.** LCanalysis follows its lower-bound
  attack for 80 phases, too few past its Table 1's depths. At a third of the stake, `Δ = 1` s and
  depth 60 the bound falls from `6.9e-3` to `5.5e-12` in the port at 30 states; the original code,
  run in Octave, falls to `5.4e-13` at its 19 states. It also scores the attack only at the moment
  of confirmation; scored at any later moment, the same attack succeeds 2–17 % more often.

---

<a id="s11"></a>
## 11. Open questions

- **A bound for the nonce rule.** The decisions an adversary takes before the cut-off, its own
  blocks published or withheld and honest minima removed, are estimated in hindsight, not bounded,
  and no analysis of Praos or Genesis covers the rule. The smaller-`k` figures of [§3.3](#s33)
  rest on that estimate. Under the delay of [§13](#s13) those decisions are blind and the bound is
  the choices at the cut-off; what a proof still needs is listed there.
- **The nonce rule's other channels.** The inferred stake moves without changing the nonce, by
  one lottery threshold step per block the adversary withholds. Choosing the level is worth under
  half a percent of the adversary's wins, and under the delay the choice is blind; the deflation
  itself is the lever ([§12](#s12), G7).
- **Recovery in a partition.** No density test tells a third's withheld fork from an honest third
  ([§6](#s6)). Whether any local test can, and what a node should do when its own chain was sparse
  over the window, is open.
- **Blend's relays.** Relays that hold every honest block for the longest mixing delay cost 7 % of
  depth; a third of the relays dropping what they carry sends half of the honest blocks through
  the sender's fallback, in the clear, and costs 37 % ([§12](#s12), G6). Open: the share of the
  relays an adversary can run, which the service declaration prices, not its stake.
- **Turnover in Cryptarchia itself.** The recovery horizon rests on how fast staked notes are spent,
  measured elsewhere at 0.05–0.3 % a day, and on how many of their old keys an adversary could buy.
  [§6](#s6) gives the horizon against turnover when every freed key is bought;
  `SETTLEMENT.md` (B5, B6) also when a tenth is.
- **The emission budget.** Votes and the DAG both pay in Blend cover traffic. Which multiple is
  acceptable is a budget decision, not a measurement.
- **Peras's proofs** for Poisson seat counts and for votes delayed by Blend (design (a)).
- **A safety proof for the DAG** below the balancing attack's edge.
- **Proving on the reference node.** The proving time on a Raspberry Pi 5, which
  `tools/benchmarks/pol-proving` measures.

The first three are taken up in [§13](#s13): recovery attestations separate partitions below a
third and nothing separates one at a third; the delay function must span the last sub-window,
4.5 hours on the adversary's hardware at `k = 2160`, with the contribution bound to the parent
block; a time-reading rule under the worst case is the counting bound read with the forks the
client sees, 374 blocks against a third.

---

<a id="s12"></a>
## 12. Further routes

Five ways to shorten finality that the routes of [§1](#s1) do not cover, and two checks on the
figures (`FURTHER.md`), each read against 30 % and a third at `ε = 1e-9`:

| route | what changes | what it buys | what it costs |
| --- | --- | --- | --- |
| a delayed nonce (G1) | the nonce of [§3.1](#s31) passes through a sequential delay that spans the last sub-window, 4.5 hours on the adversary's hardware at `k = 2160`, with the contribution bound to the parent block | the adversary decides blind before the cut-off, and the choices it can still evaluate at the cut-off leave a factor per nonce of 1.00–1.01 with a margin of ten minutes, and at most 1.08 for forks across the sub-window's start, bounded from B6's walk: against a third at 10 s the depth is the unground one within eleven blocks, 1,511–1,521 at `k = 2160` (23.0–23.1 h) instead of an estimated 1,859–1,939; `k = 1620` holds a third and `k = 1080` holds 30 % | a sequential computation of about a day once an epoch, 22 hours at a speed ratio of 5 and `k = 2160`, by whoever first needs the nonce, with a proof in the block that uses it |
| the epoch apart from `k` (G2) | the epoch keeps its length when `k` shrinks | at `k = 1080` the nonce's sub-windows, the recovery window (72 h) and the horizon stay those of `k = 2160` | one more parameter; a stake snapshot that stays 7.5 days old |
| Blend's delay (G3) | the Blend setting | from the specification's setting (`Δ = 11` s, its p99 rounded up) to testnet's (2 s), the worst-case depth against a third falls from 1,649 to 812 blocks (25.5 to 10.5 h) and the random-delay depth from 276 to 172 (4.1 to 2.2 h); one hop of three rounds (4 s) gives 936 (12.7 h); with the nonce under G1's delay each depth grows by at most 1 % | anonymity, in the Blend report's terms: one hop exposes the whole path of one message in three to an adversary holding a third of the nodes, three hops one in 27; one round of mixing blends a third of the broadcasts three rounds do |
| settlement on a chain nobody withholds from (G4) | a client rule; nothing in consensus | the elapsed-time rule of [§3.2](#s32) settles such a chain in 39 / 53 minutes against 30 % / a third on the specification's Blend, against the depth rule's 98 / 163; with the rates the total-stake inference leaves after a period of withholding, and the depth rule as a cap, 66 / 106 minutes | the rule's rates must follow the inference: after a period of withholding every rate rises by `1/(1 − α)`, and B4's rule then understates the adversary; on a chain the adversary withholds from the safe rule is the depth rule; random delay only |
| anchoring (G5) | a checkpoint written to another chain | the same choice between old forks for every node, which heals a partition deeper than `k`; finality at the anchor interval plus the other chain's | a dependence on another chain; a fork-choice rule for anchored forks; not measured |
| the inference as a lever (G7) | nothing; a check on every worst-case figure | nothing: a period of withholding, 4.5 days at `k = 2160`, lowers the inferred stake by the adversary's share and raises every threshold by `1/(1 − α)`; `Δ = 10` s then reads as `10/(1 − α)` s and the proven depth is 2,426 blocks against a third (27 hours) and 1,248 against 30 %, so `k = 2160`, `k = 1620` and `k = 1080` hold their shares only while the inference is not deflated; under random delay 276 becomes 404 blocks against a third in less time | a cap on the correction, 5 % a period, prices the deflation at 36 days and slows the response to stake that leaves alike; a client can read the worst-case table at `Δ` divided by what remains of the inferred stake |
| adversarial relays (G6), a check on the random-delay model | the adversary's relays hold every honest block for the longest mixing delay, or drop it; one copy of each block or the specification's two | holding: the honest orphan share rises by two points and the depth at `1e-9` by 7 %, 257 to 274 blocks against a third at the growth a withholding adversary leaves, and the report's 276, read at the growth with everyone producing, covers it; dropping: a third of the relays drops both copies of half of the honest blocks, which arrive by the sender's fallback 16 rounds late, and the depth is 352 with two copies, 416 with one | none for holding; dropping also identifies half of the honest leaders, since the fallback broadcasts in the clear; the lever is the adversary's share of the relays, which the service declaration prices |

**A delayed nonce.** The decisions of [§3.1](#s31) before the cut-off are worth something only if
the adversary can compute the nonce each outcome gives before it must act, and a blind choice among
`G` nonces gains nothing. It can compute an outcome's nonce from the moment the inputs are known:
for the last sub-window, from the sub-window's start, 4.3 hours before the cut-off at `k = 2160`,
since the earlier minima are fixed by then and it knows its own contributions ahead. The delay
must therefore span the sub-window, with the contribution `ρ_LEAD` bound to the parent block so
that no contribution is known before its block is built, which also replaces the binding to the
epoch nonce and the notes frozen one epoch earlier. What remains is the choices at the cut-off in
the epochs whose lead outlasts the margin beyond the sub-window: a lead lasts about one block
interval per block of lead, and against a third under the worst case it lasts 10 minutes or more in
6 % of epochs and 20 minutes or more in 0.6 %, a factor per nonce of 1.00–1.01 at a margin of 10
minutes; forks across the sub-window's start add at most 1.08, a bound from B6's walk. The depths
are [§3.1](#s31)'s "not ground" row within eleven blocks. Honest nodes compute `R·(W + margin)` for a
speed ratio `R`: 22 hours at `R = 5` and `k = 2160`, 11 at `k = 1080`, within the `4⌊k/f⌋` slots
before the nonce is first used up to `R = 16`. Phalanx's 82 independent pieces do not serve: one
piece takes 53 s on the adversary's hardware.

**A chain nobody withholds from.** A private attack withholds the adversary's blocks from the
target's parent on, so during an attack the canonical chain runs at the honest rate; a chain nobody
withholds from runs at the full rate, and a client that reads time sees the difference. The
elapsed-time rule of [§3.2](#s32) therefore settles such a chain in 39 / 53 minutes against 30 % /
a third, where the depth rule needs 98 / 163 at the same rate. The adversary cannot inflate the
density: a block that extends the public tip lengthens the chain its private one must beat, and a
block that ties an honest one replaces it. But the total-stake inference sets the lottery's
thresholds from the previous period's occupied slots, so an adversary that withholds for a whole
period, 3 days at `k = 2160`, lowers the inferred stake by its share and every rate rises by
`1/(1 − α)`: the honest stake alone then produces at the full rate, and the adversary wins faster
than the rule assumes. The race's ratio is unchanged, but the depth rule moves all the same: the
delay is fixed in slots and the orphan share rises with the rate (G7). The safe elapsed-time
rule takes the adjusted rates and the depth rule as its cap: 66 / 106 minutes on a chain nobody
withholds from (played on timelines, 65 / 103 on average and 90 / 141 at the 90th percentile),
and the depth rule's time on one the adversary withholds from. A rule that reads the density
directly accepts later than the elapsed-time rule and adds nothing to it. With the delayed nonce
of G1 the recovery horizon of [§6](#s6) is the unground one in every cell.

---

<a id="s13"></a>
## 13. Three designs

The three questions [§12](#s12) leaves open, each with a hypothesis that can fail (`DESIGNS.md`,
`PLAN.md` H8–H10):

**Recovery in a partition (H.1).** No rule that reads chains and their stake-weighted content can
tell a third's withheld fork from an honest third: after an even partition the three chains follow
the same law, and such a rule picks the fork with probability at least a third. Below a third the
honest sides hold `(1 − α)/2` each, and a one-off round of anonymous-seat votes, cast only when a
node holds two chains both deeper than `k` since their divergence, separates them: a chain is kept
when its seats exceed a threshold, the densest kept chain wins. A round of 2,300 expected seats
separates a quarter at `1e-9`; 15,000 separate 30 % if every honest vote counts, 158,000 if a tenth
are lost; 32 % needs 95,000 with every vote counted; a third none. The adversary can choose which
honest history survives, never its own. Anchoring a checkpoint to another chain timestamps a block
and does not show it was public; it settles forks older than the anchor and the start of a
bootstrapping node, not a partition. Rule 8's test serves as a partition detector: a side holding
up to about 0.6 of all stake is declared sparse with certainty against 30 % over 36 hours, the
whole honest chain once in `10^9` windows; a node whose chain is sparse reports `B_imm` as
provisional.

**The delay function (H.2).** In Praos's model a choice among nonces the adversary has not
evaluated is blind and costs nothing, and a choice among evaluated ones multiplies the failure
probability by their expected number. A candidate nonce of the last sub-window can be evaluated
from the sub-window's start, so a delay of ten minutes blinds nothing and leaves B7's estimate;
the design that works binds the contribution to the parent block and spans the sub-window,
`T_a = W + margin`, 4.5 hours at `k = 2160` with a margin of ten minutes, which leaves a factor
per nonce of 1.00–1.01 from the sub-window and at most 1.08 from forks across its start, a bound
from B6's walk.
Honest nodes pay `R·T_a` for a speed ratio `R`. The documented ratio is 3 to 5: Chia's class-group
ASIC squares in about 1 µs against 3.85 µs on the fastest CPU and 4.7 µs on a commodity one, and
the 10 that CIP-0161 assumes is attributed to Ethereum's `A_max`, which measured an attacker
against commodity ASICs. At a ratio of 5 the honest computation is 22 hours at `k = 2160` and 11 at
`k = 1080`, `1.7·10^10` squarings of one core once an epoch, and the `4⌊k/f⌋` slots before the
nonce is first used hold a ratio up to 16. The design: the hash of the sub-window minima, fixed at
the cut-off, passed through sequential squarings in a class group of a 1,024-bit discriminant, the
output hashed into the nonce, with a Wesolowski proof of one group element carried by the first
block of the new epoch and verified in milliseconds in place of the computation. MinRoot and the
other field-root candidates are broken; squaring in a group of unknown order is not. A proof still
needs Praos's argument under Genesis's fork choice and the sequentiality of the class group.

**Time under the worst case (H.3).** B3's delay-scheduling attack beats B4's elapsed-time rule at
worst-case rates whenever the rule accepts: 51–58 % of accepted targets at `ε = 1e-3`. An
adversary that schedules delays controls the clock the rule reads, so the chain's speed is not
evidence. A counting bound is: every block of a competing chain is a distinct win, the adversary's
or an honest one not on the canonical chain, so with `n` canonical blocks in `t` slots the
competing chain leads by at most `2A(t) + H(t) − 2n` plus the worst-case lead. It holds for every
strategy within `Δ`, and it bites only on a fast chain: 574 blocks against a third at `1e-9` when
the chain runs at the full rate, where B2's depth is 1,510, and nothing at the rate of a chain the
adversary withholds from. A client can count the honest wins instead of taking their mean: an
honest block that descends from the target sits on no chain without it, so the competing chain's
honest blocks are among the forks the client has received, the blocks after the target's parent
that do not descend from the target, plus those of the last `Δ` slots. The observed counting rule,
`L + A(t) + forks + H_late` against `n`, settles a chain the adversary withholds from at 374 blocks
against a third (5.4 hours on the honest chain's clock), 209 against 30 % and 112 against a
quarter, a quarter of B2's depth; three targets in four see no fork, and each fork costs about three
blocks. An adversary that balances the honest chain returns it to B2's depth, and one that
publishes every win as a fork stalls it at 30 % and above, at the cost of its rewards; the depth
rule caps it. Played at `1e-3` on the engine's timelines the race beats it on none of 70,000
targets a share. A time-conditioned form of B2's bound is not derived.

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

Proving is timed apart, on the machine at hand: `make run` in
[`tools/benchmarks/pol-proving`](../../tools/benchmarks/pol-proving) writes to
[`pol-proving/`](pol-proving).

The notes carry each result with its gate: `MAPPING.md` (what depends on `k`), `RATE.md` (block
rate and orphans), `SETTLEMENT.md` (bounds, races, a smaller `k`, recovery, grinding, the nonce),
`CERTIFIED.md` (votes), `DAG.md` (Areon), `FURTHER.md` (the routes of [§12](#s12)) and
`DESIGNS.md` (the designs of [§13](#s13)). `PLAN.md` records the questions the study was asked to
answer, its hypotheses and the verdict on each.
