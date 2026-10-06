# Faster finality for Cryptarchia

*An exploratory study of how far, and by which means, the time until a Cryptarchia block can be
relied on can be shortened against an adversary holding at most a third of the stake. Every number
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
- **[12. Reproducibility](#s12)**

---

<a id="s1"></a>
## 1. Summary

A Cryptarchia block is final once `k = 2160` blocks lie on top of it: 21 hours on the
specification's Blend, and 30 to 32 hours while 30 % to a third of the stake withholds its blocks.
The study measures seven ways to shorten it, under two delay models: random Blend delays, and a
worst case in which an adversary delivers each honest block as late as a bound `Δ` allows. It
reads them against an adversary holding 30 % and a third of the stake, at `ε = 1e-9`. Times are on
the honest chain while the adversary withholds its blocks, on the specification's Blend (3 hops of
up to 3 rounds), whose worst case is taken at `Δ = 10` s.

| route | what changes | time until final, 30 % / a third | what it costs | verdict |
| --- | --- | --- | --- | --- |
| a nonce that resists grinding ([§5](#s5)) | the epoch nonce taken from the smallest contributions of 22 sub-windows | keeps most of the depth grinding would add: with today's nonce the depths grow 2.7 to 4.6 times | a hard fork; notes frozen one epoch earlier; a window of at least 54 hours before the cut-off, the shortest run that keeps the cut-off's choices near one | taken: the others need it |
| settled level ([§4](#s4)) | a client depth; nothing in consensus | random delay: 2.4 / 4.1–4.3 h, and 1.4 / 2.3 h reading elapsed time (measured with an unground nonce); guaranteed at 10 s: 13.0–13.4 / 23.1–24.2 h | nothing | taken |
| smaller `k` ([§6](#s6)) | `k`, and a recovery trigger | `k = 1080` against 30 %, guaranteed at 10 s: 15.2 h; against a third, `k = 1620` (24.0 h) only under the smaller estimates of the nonce's factor | a recovery window of 36 or 54 hours; a look-back horizon of months | taken, after the nonce |
| faster blocks ([§7](#s7)) | `f` | random delay, against a third: 160 minutes at 30 s blocks, 144 at 15 s | ×2.07 the blocks at 15 s | not taken: little gain from 30 % |
| regular block intervals ([§7](#s7)) | the lottery becomes a curve of the slots since the parent | against a third Topl's shape needs more than 60 blocks at `1e-3`, today's lottery 58 | a third more blocks; a new stake inference | not taken |
| certificates ([§8](#s8)) | anonymous-seat votes through Blend | no committee against a third; against 30 %, 33,473 seats while every honest vote counts | ×1,675 Blend cover at 10-minute rounds | not taken |
| multi-proposer DAG ([§9](#s9)) | replaces the chain and its fork choice | random delay, at today's block rate, against a third: 106 minutes, the chain 160 by the same fit | as the chain at that rate | not taken: no proof; faster rates fall to a balancing attack below a third |

Three routes are worth taking, in this order ([§3](#s3)):

1. **A nonce that resists grinding.** With today's hash-chain nonce, an adversary that withholds
   its wins picks the next epoch's leader schedule among many. Against 30 % and a third the depths
   then grow 2.7 to 4.6 times, and at `Δ = 10` s `k = 2160` can no longer be proven against 30 %.
   Taking the nonce from the smallest contribution of each of 22 sub-windows, with notes frozen one
   epoch earlier, cuts the factor per nonce from up to `6·10^14` to an estimated 1.45–2.34 against
   a third. A delay function does as well only if an adversary can evaluate about two nonces an
   epoch.
2. **A settled level in the node's API.** A client accepts a block once the depth for its `(α, ε)`
   and delay model lies on top of it, or sooner if it also reads the time the blocks took. With the
   nonce of route 1, against a third this is 4.1–4.3 hours under random delay and 23.1–24.2 hours
   guaranteed at 10 s; reading elapsed time took 2.3 hours with a nonce that is not ground.
3. **A smaller `k` with automatic recovery.** With the nonce fixed, the worst case at 10 s allows
   `k = 1080` against 30 %: 15.2 hours. Against a third, `k = 1620` (24.0 hours) holds only under
   the smaller estimates of the nonce's factor. A split deeper than `k` then heals through a density
   test whose window is at most 36 or 54 hours.

Specification candidates follow from them:

1. **The epoch nonce from the smallest contributions** of sub-windows, with `ρ_LEAD` bound to the
   epoch nonce and notes frozen one epoch earlier ([§3.1](#s31)). A bound on its factor is open.
2. **A settled level** beside the tip and `B_imm`: the depth table, and the elapsed-time rule under
   random delay ([§3.2](#s32)).
3. **Two corrections to the Bootstrap rule** ([§10](#s10)): its depth test should read the deeper of
   the two branches, and its density window should be sized for `(α, ε)` rather than tied to `k`.
   Both bear on testnet, which runs `k = 120`.
4. **An automatic-recovery trigger** with six rules, if `k` is to shrink ([§3.3](#s33)).

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
- **Worst case.** An adversary delivers every honest block as late as `Δ` allows. The bounds of
  Gaži, Ren and Russell ("Practical Settlement Bounds for Longest-Chain Consensus", ePrint
  2022/1571, revision 2025-05-02) apply. Their code is ported, checked against their Table 1 and
  against the original run in Octave, and computed at every depth. `Δ = 10` s stands for the
  specification's Blend.

**Times** are counted on the honest chain while the adversary withholds its blocks: one block
every `30 s / ((1 − α) · g)`, where `g` is the canonical growth the engine measures. On the
specification's Blend that is 50.7 s a block against 30 % and 53.2 s against a third.

---

<a id="s3"></a>
## 3. The three routes in depth

<a id="s31"></a>
### 3.1 A nonce that resists grinding

**The problem.** The nonce of the next epoch is the hash chain at the last block before a cut-off
slot, `6⌊k/f⌋` slots into the epoch. An adversary that withholds its wins chooses which of them end
the chain there, and can also fork away the last honest blocks. Each choice is a different leader
schedule. To keep an attack's chance at `ε`, its chance against one schedule must then fall by a
factor `R`; for a block whose race crosses an epoch's end it meets two ground nonces, and the factor
is `R_2`. Against 30 % and a third `R_2` reaches `10^19` and `10^28` under the worst case at 10 s
([§5](#s5)). The depth that absorbs it, at `ε = 1e-9`:

| nonce | random, specification, α = 0.30 | random, specification, α = 0.33 | worst, 10 s, α = 0.30 | worst, 10 s, α = 0.33 |
| --- | --- | --- | --- | --- |
| not ground | 161 | 269 | 892 | 1,510 |
| hash chain, 2^1 evaluated | 165–175 | 280–293 | 902–959 | 1,544–1,630 |
| hash chain, 2^2 evaluated | 173–185 | 294–309 | 935–1,011 | 1,618–1,717 |
| hash chain, 2^4 evaluated | 187–202 | 324–345 | 1,003–1,098 | 1,762–1,900 |
| hash chain, 2^8 evaluated | 216–232 | 381–407 | 1,142–1,246 | 2,048–2,215 |
| hash chain, 2^16 evaluated | 275–292 | 499–525 | 1,429–1,539 | 2,639–2,812 |
| hash chain, 2^24 evaluated | 336–353 | 618–645 | 1,723–1,837 | 3,236–3,413 |
| hash chain, 2^32 evaluated | 397–414 | 738–765 | 2,021–2,133 | 3,837–4,013 |
| hash chain, 2^40 evaluated | 455–476 | 859–886 | 2,246–2,436 | 4,437–4,617 |
| hash chain, 2^48 evaluated | 479–521 | 979–1,006 | 2,333–2,633 | 5,041–5,221 |
| hash chain, 2^56 evaluated | 491–558 | 1,100–1,127 | 2,386–2,774 | 5,529–5,828 |
| hash chain, 2^64 evaluated | 500–570 | 1,164–1,239 | 2,424–2,825 | 5,732–6,287 |
| smallest contributions, k = 2160, at the cut-off | 162 | 271 | 894 | 1,517 |
| smallest contributions, k = 2160, estimated | 167–173 | 280–293 | 920–953 | 1,565–1,636 |
| smallest contributions, k = 1620, at the cut-off | 162 | 271 | 895 | 1,520 |
| smallest contributions, k = 1620, estimated | 167–173 | 280–293 | 921–954 | 1,568–1,639 |
| smallest contributions, k = 1080, at the cut-off | 162 | 272 | 896 | 1,526 |
| smallest contributions, k = 1080, estimated | 167–173 | 282–295 | 922–956 | 1,574–1,645 |

**The rule.** The window before the cut-off is split into 22 sub-windows. The nonce is
`η_e = H(η_(e−1) ‖ μ_1 ‖ … ‖ μ_22)`, where `μ_i` is the smallest contribution `ρ_LEAD` among the
canonical blocks of sub-window `i`. A withheld block changes the nonce only if it holds a
sub-window's minimum. Two kinds of choice remain:

- **At the cut-off,** the adversary can still change only the sub-windows its feasible forks reach.
  At `k = 2160` a sub-window spans 17,672 slots, about 330 blocks, and the adversary reaches about
  1.05 nonces on average against a third.
- **Before the cut-off,** it decides as each of its blocks is produced whether to publish it. When
  its block holds the last sub-window's minimum so far, it can compute the nonce that results if
  nothing smaller follows, and publish only if that nonce suits its attack. These decisions are
  estimated, not bounded. They raise the factor per nonce to an estimated 1.45–2.34 against a third.

**What it needs.**

- **A contribution bound to the epoch nonce.** Today `ρ_LEAD = hash(NONCE_CONTRIB_V1 ‖ sl ‖ noteID ‖
  sk)` depends on the note and the slot alone. A key with small contributions in many slots could
  then be chosen when a note is created. The proof of leadership already takes the epoch nonce as
  a public input, so the change adds one input to a hash in the circuit.
- **Enough sub-windows, and notes frozen one epoch earlier.** The notes that use an epoch's nonce
  are frozen at the start of the previous epoch. The adversary learns its own wins and
  contributions in the window that decides that nonce when the previous nonce is fixed, `4⌊k/f⌋`
  slots before the freeze. It can then predict the nonce, and the prediction is right if it holds
  the smallest contribution of every sub-window. A right prediction lets it choose keys that win,
  and whose contributions are the smallest in every later window: it keeps control in every later
  epoch. Racing the honest blocks below its own, it holds a sub-window's minimum with probability
  about 0.48 against a third on the specification's Blend and 0.50 under the worst case. Keeping
  the chance of a right prediction below `1e-9` over ten years then needs 37–39 sub-windows. With
  notes frozen one epoch earlier, as Ouroboros Phalanx does, a prediction needs the minima of two
  windows, and 22 sub-windows suffice.
- **Long sub-windows.** A fork that reaches across a sub-window boundary multiplies the choices at
  the cut-off. With 22 sub-windows they stay about 1.12 against a third at `k ≥ 1080`. At `k = 432`,
  with sub-windows of about 65 blocks, the mean rises to 2.5–3.4, resting on rare windows with
  about `10^4` choices. At `k = 216` one window in a thousand offers more than `2·10^4`. A smaller
  `k` would need a window longer than `6⌊k/f⌋` slots.

**What it buys.** Against a third under the worst case at 10 s, the guarantee needs an estimated
1,565–1,636 blocks at `k = 2160`, against 5,732–6,287 with today's nonce: 23.1–24.2 hours instead
of 85–93. Under random delay on the specification's Blend it needs an estimated 280–293 blocks
instead of 1,164–1,239: 4.1–4.3 hours instead of 17–18.

**The alternative, a delay function.** Ouroboros Phalanx (CIP-0161) keeps the hash chain and passes
its value through a verifiable delay function. Honest nodes compute it once an epoch, in 82
independent iterations of about 9 minutes on a CPU, each by the first leader of an hour-long
interval. An adversary recomputes all 82 for every nonce it evaluates, on hardware the CIP takes to
be 10 times faster, so `N` machines evaluate `N/82` nonces every 53 seconds. This caps how many
nonces it evaluates, not how many it can choose between. Against a third under the worst case at
10 s, a cap of 2 nonces needs 1,544–1,630 blocks, as the smallest contributions do, and a cap of
`2^8` 2,048–2,215. A sequential delay longer than the minutes in which the adversary must publish
its fork would leave it one nonce, at the cost of a long computation for every node. The two
combine: a delay longer than a block interval also removes the decisions before the cut-off.

**What is shown, and what is not.** The choices at the cut-off are counted against an enumeration
of every fork and every subset of withheld wins, under B6's condition for a fork to win. The
worst-case depths read the proven bound of Gaži, Ren and Russell. Open:

- a bound on the decisions before the cut-off, which are only estimated;
- displacement under a worst case of `Δ`, where the adversary can also choose which of two honest
  blocks within `Δ` becomes canonical;
- the inferred stake, which the adversary moves by publishing or withholding blocks without
  changing the nonce;
- a proof of the rule in the model of Praos's or Genesis's analysis.

<a id="s32"></a>
### 3.2 A settled level in the node's API

**The rule.** A client accepts a block once `d` canonical blocks lie on top of it, with `d` taken
from a table for its `(α, ε)` and delay model. The node would expose this third level, *settled*,
beside the tip and `B_imm`. A variant also reads when the blocks arrived. Against an adversary that
forks at the target's parent, holds no premined lead and withholds its blocks, the adversary's
progress depends only on that time. The client accepts at the first block where the adversary's
exact chance (Grunspan and Pérez-Marco) is at most `ε`, which holds `ε` for every history.

**What it buys**, against 30 % / a third, at `ε = 1e-9`. The depth rule uses the nonce of
[§3.1](#s31) at `k = 2160`, at its estimated factor, with hours on the clock of [§2](#s2). The
elapsed-time rule is measured with a nonce that is not ground, on the engine's timelines, where the
depth rule's mean is 2.2 / 3.8 h:

| delay | depth rule | reading elapsed time, mean / 90th percentile | `k = 2160` |
| --- | --- | --- | --- |
| random, specification's Blend | 167–173 / 280–293 blocks: 2.4 / 4.1–4.3 h | 1.4 / 2.3 h, 1.9 / 3.1 h | 30.4 / 31.9 h |
| worst case, `Δ = 10` s | 920–953 / 1,565–1,636 blocks: 13.0–13.4 / 23.1–24.2 h | not derived | 30.4 / 31.9 h |

**What the client accepts.** The adversary's share; the delay model; the grinding its depths
include; a view that is not eclipsed. The random-delay table assumes Blend's delays are not the
adversary's to choose. Under the worst case only the depth rule applies.

**What is shown, and what is not.** The worst-case depths are the proven bound. The random-delay
depths are the private race in closed form, which the race played on the engine's timelines
matches within three blocks at `1e-3`. On the engine's timelines both rules hold `ε` where it can
be measured, at `1e-3`: against 30 % the race beats the elapsed-time rule on 1.1e-3 of 79,208
targets, within one standard error. Open: the elapsed-time rule under a worst case of `Δ`, and
against an adversary that also extends the public chain.

<a id="s33"></a>
### 3.3 A smaller `k` with automatic recovery

**What `k` must cover.** `k` binds every node, so it must hold under the worst case. With the nonce
of [§3.1](#s31) the worst case at 10 s needs an estimated 922–956 blocks against 30 % at `k = 1080`,
so `k = 1080` holds it: 15.2 hours to protocol finality instead of 30.4. Against a third it needs an
estimated 1,568–1,639 blocks at `k = 1620`, so `k = 1620` holds only under the smaller estimates,
and then takes 24.0 hours instead of 31.9. With today's nonce, `k = 2160` itself cannot be proven
against 30 % at 10 s.

**What it breaks.** A split heals by itself only while the losing side has made fewer than `k`
blocks. Past that a node stays on the losing side, and a restart does not return it
([§10](#s10)). Automatic recovery compares a fork that diverges deeper than `k`, within a horizon
`H`, by its block density in a window after the divergence. Six rules keep it safe ([§6](#s6)).
The window may be at most `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake take effect:
36 hours at `k = 1080` and 54 at `k = 1620`.

**The horizon.** Keys of notes spent since a divergence can sign for the fork, where those notes
are unspent. Over the horizon the chance that the window favours the adversary's fork must stay
below `1e-9`. With every freed key for sale at Bitcoin's turnover, 0.125–0.243 % a day, and the
nonce of [§3.1](#s31) at its largest estimate, the longest window holds 30 % for 119–230 days at
`k = 1080`, and a third for 95–183 days at `k = 1620`.

**What it costs.** A split heals only once its window has passed, 36 or 54 hours. `B_imm` may move
back within `H`, so every consumer of it needs a path for that. Nodes keep block trees and ledger
states back to `H`.

**What is shown, and what is not.** The trigger's six rules come from attacks on simpler forms of
it (`SETTLEMENT.md`, B5). Its horizon rests on the turnover of staked notes in Cryptarchia, which
is not measured, and on how many old keys an adversary could buy. A forward-secure leader key would
remove that dependence.

### 3.4 The three together

With the nonce of [§3.1](#s31), at its estimated factor; reading elapsed time is measured with a
nonce that is not ground:

| against | today | settled, random delay | settled, reading elapsed time | settled, guaranteed at 10 s | `k`, guaranteed at 10 s |
| --- | --- | --- | --- | --- | --- |
| 30 % | 30.4 h; `k` not proven at 10 s with two ground nonces | 2.4 h | 1.4 h | 13.0–13.4 h | 15.2 h (`k = 1080`) |
| a third | 31.9 h; `k` not proven at 10 s with two ground nonces | 4.1–4.3 h | 2.3 h | 23.1–24.2 h | 24.0 h (`k = 1620`) under the smaller estimates, 31.9 h (`k = 2160`) otherwise |

---

<a id="s4"></a>
## 4. Settlement on the chain

The depth a client must wait, in canonical blocks, at `ε = 1e-9`, with a nonce that is not ground:

| adversary | random delay, testnet's Blend | random delay, the specification's | worst case, `Δ` = 1–10 s, proven | worst case, best known attack |
| --- | --- | --- | --- | --- |
| 10 % | 17 | 19 | 75–114 | 31–33 |
| 25 % | 66 | 86 | 288–474 | 110–143 |
| 30 % | 111 | 161 | 495–892 | 185–266 |
| a third | 169 | 269 | 758–1,510 | 278–445 |

Under random delay the depth is that of the private race from the target's parent in closed form,
which the race played on the engine's timelines matches to within three blocks at `1e-3`.

- **The proof is not far from the attack.** Where both are computed, the proven depth is 2.4 to 3.6
  times the attack's at delays up to 10 s, and up to 6.6 times at 20 s.
- **The bound describes Cryptarchia's slot lottery.** The attack behind the lower bound, played on
  the 1 s slot lottery, lands within 7 % of the bound computed in continuous time.
- **`k = 2160` holds a third of the stake at `1e-9` only for delays up to 13 s,** without grinding.
- **A rule that also reads elapsed time settles about 40 % sooner from 30 %.** Against a third at
  `1e-9`, on the engine's timelines of the specification's Blend, it accepts after 2.3 hours on
  average where the depth rule needs 269 blocks and 3.8 hours. Against a quarter it accepts after
  45 minutes where the depth rule needs 66, and against a tenth it settles about a fifth sooner. It
  is derived for random delay only.

---

<a id="s5"></a>
## 5. The epoch nonce

**Grinding.** The coalition's choices at a cut-off are counted exactly from a random walk of its
lead, backwards from the cut-off, with the lead it may still gain after the cut-off mixed in. Two
bounds bracket the factor `R` by which the chance against one schedule must fall, for one ground
nonce and for two (`SETTLEMENT.md`, B6). They assume an adversary that evaluates `2^64` nonces an
epoch; from 30 % of the stake that budget sets the factor. At `ε = 1e-9`, the depths in blocks:

| delay | adversary | not ground | one ground nonce | two ground nonces |
| --- | --- | --- | --- | --- |
| random, the specification's Blend | 25 % | 86 | 153–163 | 169–191 |
| random, the specification's Blend | 30 % | 161 | 402–412 | 500–570 |
| random, the specification's Blend | a third | 269 | 743–762 | 1,164–1,239 |
| worst case, 10 s | 25 % | 474 | 759–819 | 824–950 |
| worst case, 10 s | 30 % | 892 | 2,056–2,124 | 2,424–2,825 |
| worst case, 10 s | a third | 1,510 | 3,879–3,994 | 5,732–6,287 |

- **`k = 2160` cannot be proven against 30 % or a third at 10 s with two ground nonces.** Against a
  third the bounds prove it with two ground nonces only at 1 s, against an adversary that
  evaluates `2^40` nonces. With one ground nonce they prove it up to 5 s against `2^40` and up to
  2 s against `2^64`.
- **Grinding also shortens the recovery horizon.** With today's nonce the longest window at
  `k = 2160` holds a third for 57–111 days at Bitcoin's turnover, against 106–205 without grinding
  ([§6](#s6)).

**Two ways to resist it** (`SETTLEMENT.md`, B7). A delay function caps how many nonces the
adversary can evaluate; the smallest contributions of sub-windows reduce how many it can reach.
The table of [§3.1](#s31) compares them. Under the worst case at 10 s against a third, a cap of 2
nonces leaves 1,544–1,630 blocks, and the smallest contributions an estimated 1,565–1,636 at
`k = 2160`.

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

**Automatic recovery** can lift that bound. A fork that diverges deeper than `k` but within a
horizon `H` is compared by its block density in a window after the divergence, the test of the
Bootstrap rule. Six rules make it safe:

1. Evaluate the fork; never switch fork-choice rules. A switch would freeze `B_imm`, and one stale
   winning slot could trigger it.
2. Read the depth of the deeper branch, so that every node holding either chain decides alike.
3. Compare densities only once both chains hold the whole window.
4. Size the window for `(α, ε)` and the horizon.
5. Keep the window within `4⌊k/f⌋` slots, before a fork's own nonce and inferred stake take effect:
   72 hours at `k = 2160`, 54 at `k = 1620`, 36 at `k = 1080`, 4 at `k = 120`.
6. Bound the horizon `H` against keys that become free (below).

The trigger costs three things. `B_imm` may move back within `H`, so every consumer of it needs a
path for that. The node keeps its block tree and ledger states back to `H`. A split heals only once
the window after its divergence has passed.

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
  against a quarter of the stake in 18 minutes at `1e-9` against 45 at 30 s. On the
  specification's Blend the race keeps gaining at least to 15 s blocks: 59, 48 and 40 minutes at
  30, 20 and 15 s. The cost is ×1.56 the blocks at 20 s and ×2.07 at 15 s. No worst-case figure is
  given at `f ≠ 1/30`.
- **From 30 % they gain little.** On the specification's Blend the closed form settles later with
  faster blocks: 136, 143 and 146 minutes at 30, 20 and 15 s against 30 %, and 239, 283 and 318
  against a third. The race, fitted and extrapolated as for the DAG ([§9](#s9)), gains 10 %
  against a third: 160, 153 and 144 minutes.
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
share `s` proves `s·n` times a round. The Raspberry Pi 5 is not measured yet.

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
- **Counted over the last `w` slots only,** as the paper's prose says: no depth settles. A
  coalition that keeps its private subDAG alive outweighs the honest side in some window.

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
- **The Bootstrap rule's depth test can split the network after a split.** It reads the depth of the
  node's own branch. When one side of a split has passed `k` blocks and the other has not, nodes on
  the short side follow the longer chain while nodes on the long side follow the denser one, and
  they alternate until both sides pass `k`.
- **The epoch nonce can be ground** ([§5](#s5)). The nonce is the hash chain at the last block
  before a cut-off slot, so an adversary that withholds its wins chooses among the chains it can
  end there. Against 30 % at `Δ = 10` s, the guarantee then needs 2,424–2,825 blocks, more than
  `k = 2160`.
- **The bound's reference code needs more phases at depth.** LCanalysis follows its lower-bound
  attack for 80 phases, too few past its Table 1's depths. At a third of the stake, `Δ = 1` s and
  depth 60 the bound falls from `6.9e-3` to `5.5e-12` in the port at 30 states; the original code,
  run in Octave, falls to `5.4e-13` at its 19 states. It also scores the attack only at the moment
  of confirmation; scored at any later moment, the same attack succeeds 2–17 % more often.

---

<a id="s11"></a>
## 11. Open questions

- **A bound for the nonce rule.** The decisions an adversary takes before the cut-off are
  estimated, not bounded, and no analysis of Praos or Genesis covers the rule.
- **The nonce rule's other channels.** Displacement under a worst case of `Δ` sets how many
  sub-windows the rule needs. The inferred stake moves without changing the nonce.
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

---

<a id="s12"></a>
## 12. Reproducibility

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
`CERTIFIED.md` (votes) and `DAG.md` (Areon). `PLAN.md` records the questions the study was asked to
answer, its hypotheses and the verdict on each.
