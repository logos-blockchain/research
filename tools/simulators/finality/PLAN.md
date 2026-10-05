# Fast finalization for Cryptarchia — the plan

An exploratory study of how far, and by which means, the time until a Cryptarchia block can be
relied on can be shortened. It sizes every route by number before any design is chosen. It
changes no specification.

Branch `fast-finalization`, based on `origin/master` at `272fd9a`. The TSI per-node engine
(`../tsi/tsi-sim-pernode`) is consumed as a library for fork structure, delay and attacks.
Specifications are read at `logos-lips` `47a73cdc`. The node is read at `logos-blockchain`
`4e0405d51`, and testnet 0.3.0 at `865df42ba`.

## How to read this

*In plain words: this is the notebook the study starts from — the brief, what a first
calculation already says, the levers worth pulling, the questions only the owner can settle,
and the order of work. The finished story will be `../../../reports/finality/`.*

| section | what it carries |
| --- | --- |
| §0 | the brief, and the constraints carried from the Cryptarchia specification |
| §1 | a first look: where the time goes, what `k` buys, what each lever is worth (numbers from `firstlook.py`) |
| §2 | the levers, each with a hypothesis that can fail |
| §3 | the owner's decisions on nine questions that shape the study |
| §4 | the work plan, phases A–F |
| §5 | the measurement protocol |
| §6 | what depends on `k` today, in the specifications and in the node |
| §7 | literature to reproduce before it is relied on |

## Status

Executed on 2026-10-05. Results live in five notes beside this plan:

- `MAPPING.md`: A2, A3.
- `RATE.md`: A1, C1–C4.
- `SETTLEMENT.md`: B1–B5.
- `CERTIFIED.md`: D0–D6.
- `DAG.md`: E0–E6.

Phase by phase:

| phase | status |
| --- | --- |
| A1 baseline | done; reproduces the TSI report's and the specification's measured orphan shares |
| A2, A3 map and self-healing horizon | done |
| B1 bounds | done; the port reproduces all 152 proof-of-stake cells of the paper's Table 1 |
| B2 depth over share and delay | done, worst case |
| B3 engine validation | done: the private-chain attack under random delays, and the delay-scheduling attacker of the lower bound on the slot lottery |
| B4 confirmation rule | drafted |
| B5 smaller `k` | done: the share each `k` holds, both routes of Q8, a trigger for automatic recovery, and its horizon against stake turnover |
| C1 rate surface | done |
| C2 Blend parameters | the delay map is done; the privacy trade is with the Blend owners |
| C3 GHOST | done |
| C4 Taktikos | done: no fewer orphans; a regular interval settles faster on the specification's Blend at more blocks |
| D0 emission map, D2 committee realism | done |
| D1, D1b, D3, D4, D5 | sketched, open questions listed; D3 prices verification with the Raspberry Pi 5 measurement of Blend, proving on it is not measured |
| D6 simulation | done: votes on a target 30 slots back never split under random delay; a round certifies within one Blend delivery; an adversary that schedules delays splits shallow rounds |
| E0 audit of the Areon simulator | done |
| E1–E6 Areon-Base on the engine | done: built on the TSI engine (the owner's choice); the private race, the §5.6 fit, worst-case delay, eligibility, ledger and cost |
| F report | `reports/finality/README.md` |

Findings about the protocol as it stands:

- A restart, even with `--bootstrap`, does not return a node from the losing side of a split deeper
  than `k`; only a re-sync from genesis or a checkpoint does (`SETTLEMENT.md` B5).
- At testnet's `k = 120` the Bootstrap rule's density window is 15 minutes, and a quarter of the
  stake wins about one such window in 460 (B5).
- `maxvalid-bg` reads the depth of the local branch, so after a split the two sides can choose
  different chains until both pass `k` (B5).
- LCanalysis follows its lower-bound attack for 80 phases, too few past Table 1's depths: at a
  third of the stake and depth 60 the bound falls from `6.8e-3` to `5e-12`. It also scores the
  attack only at the moment of confirmation (B1, B3).

Hypotheses:

| hypothesis | verdict |
| --- | --- |
| H1 | fails for the guarantee: at 25 % and `ε = 1e-9` the upper bound exceeds 216 blocks at every delay. Holds for the best known attack up to about 20 s |
| H2 | holds for delays up to about 14 s |
| H3 | holds |
| H4 | refuted: GHOST's safe region never exceeds the longest-chain rule's, and in proof of stake it needs equivocation control |
| H5 | waits on the budget line of Q7 |
| H6 | holds with the trigger of `SETTLEMENT.md` B5: a density test below `B_imm` within a horizon `H`, with a window set apart from `k`. Fails as first stated, a switch to the Bootstrap rule. `H` waits on data about stake turnover |
| H7 | holds for the weight accumulated since the fork, with each `ρ_LEAD` counted once: against 25 % at `ε = 1e-9`, 38 minutes at Cryptarchia's block rate against 59 on the chain. Fails for the paper's prose horizon (the last `w` slots), which settles no depth. The emission line is the owner's |

Three notions of finality carry the document. They are measured separately and never mixed.

- **k-finality.** The latest immutable block `B_imm` of the Cryptarchia specification, the block
  `k` blocks deep. A node never reorganises past it. It is a protocol rule.
- **Settlement.** A block at depth `d` is displaced with probability at most `ε`, against an
  adversary holding stake share `α`, under a stated delay model. It is a client rule and needs no
  protocol change.
- **Certified finality.** A block is final once a certificate of anonymous votes exists for it.
  It is a protocol addition.

The multi-proposer DAG (L6) keeps the settlement notion but changes the structure it is measured
on: depth counts references inside a window of a block DAG instead of blocks on a chain.

| symbol | meaning |
| --- | --- |
| `f`, `k` | slot activation coefficient (1/30) and security parameter (2160 blocks); one slot is 1 s |
| `o` | orphan share: the share of produced blocks that end off the canonical chain |
| `α`, `α_eff` | adversary stake share; its share of chain-extending blocks, `α / (α + (1−α)(1−o))` |
| `ε` | accepted failure probability, per block for settlement, per round for votes |
| `D_vis`, `ρ` | mean time for a block to reach every node; the load `ρ = f·D_vis` (TSI report §3.3) |
| `Δ` | the delay bound of the adversarial network model, in slots |
| `n`, `Q` | expected anonymous committee seats per voting round; the quorum |

## 0. The brief

Stated by the owner, 2026-10-05: plan an exploratory research to investigate possible ways of
decreasing finalization times of Cryptarchia consensus.

The brief names no target time, no adversary and no finality notion. §3 Q1–Q3 ask for them.

Five constraints are carried from the Introduction of `cryptarchia-v1-protocol.md`. All five
bind; one opt-in relaxation of C1 is explored as a variant (§3 Q4).

- **C1 — Stake stays private.** No mechanism may reveal a participant's stake or link its
  actions. The specification names the mechanism to avoid: "If the activity of the leader
  reveals their stake values (e.g. through weighted voting), then this value can be used to
  reduce the anonymity set for the leader".
- **C2 — Liveness first.** Block production continues through a partition. Finality may stall;
  the chain may not halt.
- **C3 — No known participant set.** Any committee is drawn by a private lottery, never by
  identity.
- **C4 — Lottery wins travel through Blend.** A message that proves a lottery win reveals its
  sender's stake over time unless its origin is hidden. A vote is a lottery win. The node
  publishes block proposals through Blend, and gossips them directly only while the Blend
  membership is below its minimum size.
- **C5 — The node class.** Verification and bandwidth fit the slowest node the protocol
  targets.

## 1. What a first look says

Every number in this section is printed by `firstlook.py` beside this file
(`python3 firstlook.py`, a few seconds). Six gates check it against published or independent
results:

- Nakamoto's §11 tables, digit for digit.
- Grunspan and Pérez-Marco's corrected tables and their closed form `I_{4pq}(z, 1/2)`.
- The honest shares the specification's Praos annex reads off its plots.
- A bisection of Dembo et al.'s threshold equation.
- The Blend report's emission-quota table.
- A direct convolution of the committee tail.

A mutated copy of each implementation fails its gate. The models are crude on purpose: they size
the problem. §1.8 lists what they leave out and the phase that replaces each.

Three Blend configurations frame the numbers. The specification's has at most three blending
operations and `Δ_max` = 3 rounds per hop. At 3 hops and 2 s per hop, with a 6 s mean
end-to-end delay, the stake-inference analysis measured `o = 0.15` before uncle references
existed (`analysis-total-stake-inference.md`, `q = 0.85`). Testnet 0.3.0 runs one Blend layer
with a 1-round maximum delay. The TSI report's operating point, 8 s per hop with `o = 0.35`
(`reports/tsi/README.md` §6.10), is the heavy case.

### 1.1 Where the time goes

With uncle references, the stake inference holds *occupied* slots, canonical or referenced, at
`f`. The canonical chain therefore grows at about `f(1 − o)`, and k-finality takes about
`k / (f(1 − o))` slots. Before uncle references the inference held the canonical chain itself
at `f` and over-produced blocks instead (`analysis-total-stake-inference.md`, Cryptarchia
Metrics).

| configuration | `k` | no forks | `o = 0.15` | `o = 0.35` |
| --- | --- | --- | --- | --- |
| specification | 2160 | 18.0 h | 21.2 h | 27.7 h |
| testnet 0.3.0 | 120 | 1.0 h | — | — |

`k` also sizes the epoch. `s = 3⌊k/f⌋` is 54.0 h, and the epoch, `10⌊k/f⌋` slots, is 7.5 days
(10.0 h on testnet). A change to `k` moves both unless they are decoupled (§6.4).

`k` also bounds the partition the network heals on its own. When a partition ends, the side
that loses rolls back every block it made since the split. The Online rule "rejects chains that
diverge by more than `k` blocks" (Fork Choice Rule), and a node re-enters the Bootstrap rule
only at startup (§6.1). A side holding half the stake makes `k` blocks in 35.7 h, and one
holding a fifth in 88.8 h. At `k/10` these become 3.6 h and 8.9 h; at testnet's `k`, 2.0 h and
4.9 h.

### 1.2 What `k` buys

Under the Rosenfeld model the attacker mines privately from the moment the target block is
published, and wins if its chain ever overtakes. The depth it takes at `ε = 1e-9`, in blocks
and minutes:

| `α` | `o = 0` | `o = 0.15` | `o = 0.35` |
| --- | --- | --- | --- |
| 0.10 | 19 · 10 min | 22 · 13 min | 28 · 22 min |
| 0.20 | 43 · 22 min | 54 · 32 min | 86 · 66 min |
| 0.25 | 66 · 33 min | 89 · 52 min | 171 · 132 min |
| 0.30 | 108 · 54 min | 163 · 96 min | 434 · 334 min |
| 1/3 | 159 · 80 min | 269 · 158 min | 1,088 · 837 min |
| 0.40 | 458 · 229 min | 1,269 · 746 min | none |

`firstlook.py` prints the same table at `ε = 1e-3` and `1e-6`.

The model is exact for what it describes: it reproduces Grunspan and Pérez-Marco's corrected
double-spend tables, for example 6, 20, 32 and 133 confirmations for 0.1 % at `q` = 0.10, 0.25,
0.30 and 0.40. That is a proof-of-work race without delay. It does not cover a proof-of-stake
race under delay. The rigorous bounds for that case (Gaži, Ren and Russell, revised 2025-05-02,
§7) are the method B1 reproduces. Expect them to ask for more depth than this table.

Read the other way, `k = 2160` holds `ε = 1e-9` up to `α_eff = 0.4536`. That is `α` = 0.4536,
0.4137 and 0.3505 at `o` = 0, 0.15 and 0.35. `α_eff` reaches 1/2, and no depth suffices, at
`α = 0.4595` when `o = 0.15` and at `α = 0.3939` when `o = 0.35`. Testnet's `k = 120` holds
`ε = 1e-9` up to `α = 0.2764` at `o = 0.15`.

Two readings follow, both to be re-established under the proof-of-stake delay model (Phase B):

- The depth is set by the adversary the protocol must tolerate and by `ε`, not by the network.
  Against `α ≤ 0.25` the depth needed is 1–8 % of `k`.
- Forks lower the threshold itself: 0.46 at `o = 0.15` and 0.39 at `o = 0.35`, not 1/2.

### 1.3 What the specification already says about delay

The only delay analysis in the specifications is the Praos condition in the annex of
`analysis-block-times-blend-network.md`: `α_h (1 − f)^{Δ+1} ≥ (1 + ε)/2`, where `α_h` is the
honest stake share and `Δ` the maximum network delay. At `f = 1/30` and `ε = 1e-6` it admits an
adversary of at most 0.427 at `Δ` = 3 s, 0.366 at 6 s, 0.249 at 11 s and 0.169 at 14 s. The
annex reads 75 % and 83 % honest for the last two. At 15 s it admits 0.140, and beyond 19 s no
stake split satisfies it. The annex calls the common-prefix bound
"very loose". No specification derives `k = 2160`; it appears as a constant and as a simulation
input.

The condition is Praos's Theorem 7, for static stake. The full protocol's result is Theorem 11,
and Corollary 3 with a hash-derived nonce. Its bound adds the system's lifetime, the stake shift
over two epochs and a grinding term. Praos gives no concrete `k`, `f` or failure probability,
and never states the constant hidden in its `Ω(k)`. Its proven confirmation time, `u = 8k/f`,
is 6.0 days at `k = 2160`. The bound is loose by construction: it counts an honest slot only
when that slot has a single leader and the `Δ` slots after it are empty. Crypsinous proves no
consensus theorem of its own and inherits Ouroboros Genesis's.

So the only guarantee the specifications give, at the delay they modelled (about 11 s at most),
covers `α ≤ 0.25`.

The tight result is wider. Dembo et al. prove that the private attack is the worst attack, for
proof of work and for Praos-type proof of stake alike. A chain is safe while
`β < (1 − β)/(1 + (1 − β)fΔ)`, where `β` is the adversary's stake share (§7). At `f = 1/30` the
threshold is:

| `Δ` | 3 s | 6 s | 11 s | 15 s |
| --- | --- | --- | --- | --- |
| `β*` | 0.4875 | 0.4751 | 0.4545 | 0.4384 |

`Δ` is a variable of this study, not a fixed input (Q3). Blend's delivery deadline,
`T_M = ß(Δ_max + η)`, is 1 × (1 + 2) = 3 rounds on testnet and 3 × (3 + 2) = 15 rounds in the
specification today. Both are settings: the study derives the `Δ` each lever needs, and Blend's
parameters are chosen from it (C2). A threshold says whether a depth exists, not how deep it
is. The loose proof, not the protocol, is what caps the specification's guarantee at 0.25. How
much depth `k = 2160` buys near `β*` is B2's question.

### 1.4 The orphan share is the strongest lever; the block rate is not one, yet

`o` enters twice: through `α_eff` in the depth, and through `1/(f(1 − o))` in the time per
canonical block. At `α = 0.25` and `ε = 1e-9` the time to settle is 33 min at `o = 0`, 52 min
at 0.15, 63 min at 0.20, 132 min at 0.35 and 458 min at 0.5.

A collision model, `o = (1 − e^{−2ρ})/2`, matches the TSI engine at per-hop delays of 2 s
(0.21 against 0.20) and 8 s (0.34 against 0.35). It under-predicts at 32 s (0.49 against 0.60),
so it is used only for `ρ ≤ 1`. Under it, at `α = 0.25` and `ε = 1e-9`, in minutes:

| `D_vis` \ block interval | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- |
| 3 s | 76 | 59 | 43 | 33 | 28 | 23 |
| 6 s | 86 | 70 | 55 | 47 | 44 | 44 |
| 8 s | 93 | 78 | 65 | 59 | 58 | 61 |
| 17 s | 135 | 126 | 123 | 130 | — | — |
| 30 s | 216 | 221 | 235 | — | — | — |

`—` marks `ρ > 1`. At the TSI operating point (`D_vis` = 17 s) every block interval from 60 s to
20 s settles in 123–135 min: a faster block rate forks more and gains nothing. At `D_vis` = 3 s,
the order of testnet's single 1 s hop, shortening blocks from 30 s to 10 s cuts 43 min to
23 min. The block rate becomes a lever only once `D_vis` is small.

### 1.5 The repository's confirmation rule answers another question

The TSI report recommends waiting 4, 8 and 17 blocks for 99.9 % against 10, 20 and 30 % stake
(§6.10; §8.1, row 15). Its tail, `(α_eff/(1 − α_eff))^d`, is the chance that an attacker `d`
blocks behind ever draws level: the depth of the deepest reorganisation an attacker can force
from an arbitrary moment. A receiver needs something else: the chance that a block it relies on
is displaced by an attacker who began mining privately when that block appeared. With the same
inputs (`o = 0.35`, `ε = 1e-3`) the Rosenfeld depths are 9, 25 and 126 blocks. A client rule is
built on the second question (B4).

### 1.6 Votes cost thousands of anonymous seats a round

C1 forbids stake-weighted votes, so a vote is a private lottery win: one seat per note per
round, proven in zero knowledge and deduplicated by a nullifier. Honest seats vote once;
adversarial seats vote for both sides. Two conflicting quorums need `H + 2A ≥ 2Q`; a round
stalls when `H < Q`. With seats Poisson-distributed, the smallest expected committee that holds
both at `ε` per round:

| `α` | `ε = 1e-6` | `ε = 1e-9` |
| --- | --- | --- |
| 0.10 | 421 | 665 |
| 0.20 | 1,313 | 2,085 |
| 0.25 | 3,364 | 5,355 |
| 0.30 | 21,024 | 33,473 |

No quorum exists at `α ≥ 1/3`. Offline honest stake shrinks the window further: with a fifth
of it offline, and seats still drawn against all stake until the inference adapts, `ε = 1e-6`
takes 628, 3,067 and 17,872 seats at `α` = 0.10, 0.20 and 0.25, and none exists at 0.30.

`ε` is per round. One round per 30 s block is 1,051,200 rounds a year, so `ε = 1e-9` means
1.1e-3 expected safety failures a year; one round per 10 minutes means 5.3e-5. The
specification's `ProofOfLeadership` is 224 bytes, of which the Groth16 proof is 128 (Block
Header). A vote is at least a proof plus a nullifier and a target. At 5,355 seats and 224 bytes
each, one round carries 1.2 MB before Blend overhead.

### 1.7 Every extra lottery win is an emission, and Blend prices emissions

Blend hides a node's lottery wins only while they fit its cover quota. At the baseline cover
rate of one message a second across the network, the Blend report puts that ceiling at 0.147 %
of inferred stake at N = 20,000 (`reports/blend/README.md` §3.10). A vote is one more lottery
win, so votes multiply a node's emissions by `1 + n/(R·f)` for `n` seats per round of `R` slots.
A multi-proposer DAG (Areon, L6) makes every block a vote, so `λ` blocks per slot multiply them
by `λ/f`:

| design | parameters | emissions per unit stake |
| --- | --- | --- |
| Peras-style votes | `n = 900` per 90 s (Peras's `U`) | ×301 |
| votes, `α = 0.25`, `ε = 1e-9` | `n = 5,355` per 90 s | ×1,786 |
| Peras-style votes | `n = 900` per 10 min | ×46 |
| votes, `α = 0.25`, `ε = 1e-9` | `n = 5,355` per 10 min | ×269 |
| Areon DAG | `λ = 0.05` blocks per slot | ×1.5 |
| Areon DAG | `λ = 0.25` (the paper's default) | ×7.5 |

The votes come to 10.0, 59.5, 1.5 and 8.9 messages a second across the network. To keep today's
ceiling, the cover rate, which every node carries, must rise by the same factor. This, not the
committee arithmetic, is the first constraint on L5 (D0). A DAG pays one to two orders of
magnitude less than votes.

### 1.8 What the first look leaves out

- **Proof-of-stake races.** The lottery ticket hashes the epoch nonce, the slot and the note, not
  the parent (`cryptarchia-proof-of-leadership.md`, ticket computation). One win can therefore
  sign blocks on several branches. The Rosenfeld model lets each win extend one chain. → B1.
- **Adversarial delay.** `o` was measured under random Blend delays. An adversary that schedules
  delivery within `Δ` can split honest leaders on purpose. → B1, B3.
- **Pre-mining.** An attacker may start its private chain before the target block. → B1.
- **The deployed delay.** Neither measured `o` comes from the node's own Blend. → A1.
- **Committee realism.** Offline stake enters as one case only. Error in the inferred total
  stake, honest votes split across forks and Blend loss are not in the seat model. → D2.
- **Spread.** The figures are means. The time to `d` blocks is Gamma-distributed, with a 95th
  percentile 1.57× the mean at `d = 10`, 1.32× at 30 and 1.17× at 100. → §5.

## 2. The levers

| lever | what changes | protocol change | first-look effect | main risk | phase |
| --- | --- | --- | --- | --- | --- |
| L1 settlement rule | a client confirmation depth `d(α, Δ, ε)` | none in consensus; a third level in the node's APIs | at `o = 0.15`, `ε = 1e-9`: 13 min (`α = 0.10`) to 52 min (`α = 0.25`), against 21.2 h | the depth diverges as `α` nears the threshold | B |
| L2 smaller `k` | the finality depth | `k`, and with it the epoch and everything timed by it, unless decoupled (§6.4) | proportional to `k`; testnet already runs `k = 120` | lowers the tolerated `α`; shortens the self-healing horizon | A3, B2, B5 |
| L3 fewer orphans | `D_vis` (Blend); a lottery threshold that rises with the slots since the parent (Ouroboros Taktikos); or a fork choice that weighs referenced uncles | Blend parameters, the lottery, or fork choice | `o` 0.35 → 0.15 cuts 132 min to 52 | Blend's privacy budget; GHOST-style weighting narrows the safe region (§7) | C |
| L4 block rate | `f` | a constant | none at `D_vis` = 17 s; 43 → 23 min at 3 s | more forks | C1 |
| L5 certified finality | anonymous-seat votes: a Peras-style certificate with a fork-choice boost and a cool-down, a checkpoint gadget, or endorsements carried in blocks; optionally slashable nullifiers. Variant: an opt-in public committee (Q4) | large | about two minutes in Peras | Blend's emission budget (§1.7); thousands of seats a round; safety only below 1/3 | D |
| L6 multi-proposer DAG (Areon) | several proposers per slot; blocks reference the recent tips; a fork choice local to the closest common ancestor counts recent references | replaces the chain and its fork choice; the ledger needs a total order | the paper: `k ≥ C1·w + C2·ln(1/ε)` with window `w ≥ Δ`; reorgs 600–8,750× rarer than Praos at 30 % stake | anonymous eligibility (one block per win); emissions ×`λ/f`; GHOST-style weighting may narrow the safe region | E |
| L7 other structures | parallel chains, ledger combiners | very large | — | multiplies proofs and emissions by the number of chains | §7 only |

Each hypothesis below can fail, and says what would fail it.

- **H1.** Under the proof-of-stake delay analysis, settlement against `α = 0.25` at
  `ε = 1e-9` needs at most `k/10` = 216 blocks at a `Δ` Blend can reach. B2 derives the largest
  such `Δ`. Fails if it is below what one Blend hop takes (testnet's 3 s).
- **H2.** `k = 2160` holds `ε = 1e-9` against `α = 1/3` up to the `Δ` the other levers need. B2
  derives the largest `Δ` at which it does. If that falls short, the study's first finding is a
  safety margin, not a latency.
- **H3.** The time to settle falls at least as `1/(1 − o)` as `o` falls. Fails if C1's
  engine-measured surface is flatter than the collision model.
- **H4.** A fork choice that weighs referenced uncles brings `α_eff` back to `α` without opening
  a cheaper attack. Expected to fail: the tight GHOST analysis finds its safe region inferior to
  the longest-chain rule's (§7). C3 confirms or refutes this at Cryptarchia's parameters.
- **H5.** A certified-finality design fits Blend's emission budget and the node budget of Q7 at
  `α = 0.25`. Fails if, for every committee size and round length that meet `ε`, either the
  cover-rate multiple `1 + n/(R·f)` (D0) or the verification cost (D3) exceeds the budget.
- **H6.** Automatic recovery can be made safe, so the self-healing horizon stops bounding `k`.
  A node that sees a fork deeper than `k` switches to the Bootstrap rule by itself and rejoins
  the honest chain. Fails if B5 finds that an attacker can trigger the switch to its advantage,
  or that the Bootstrap rule cannot tell the honest chain apart soon enough after a split.
- **H7.** Areon, instantiated with Cryptarchia's private lottery and `w ≥ Δ`,
  settles against `α = 0.25` at `ε = 1e-9` faster than L1 does on the chain, within the
  emission budget of Q7. Fails if E2's fitted depth gives a longer time than B2, if one win can
  add weight more than once (E3), or if its safe region under worst-case delay is narrower than
  the longest-chain rule's (E5).

## 3. Questions for the owner

All nine were settled by the owner on 2026-10-05, one at a time. Each entry records the
decision and what it changes.

- **Q1 — Which notion is the target?** *Settled 2026-10-05 by the owner:* this is exploratory
  work, so every notion is explored: settlement (L1), a smaller `k` (L2), certified finality
  (L5) and the multi-proposer DAG (L6). Each runs to its own exit, numbers or a reasoned no.
  Phase A comes first. Phases B to E then run side by side, and F closes. No lever is cut at its
  first obstacle; an obstacle becomes a constraint the lever's designs are measured against.
- **Q2 — Which attacker share `α` and failure probability `ε` head the results?** *Settled
  2026-10-05 by the owner:* no headline pair. Every result is reported as curves across `α` and
  `ε`. `ε` is per block for settlement and per round for votes, each with its yearly failure
  rate. The hypotheses of §2 keep `α = 0.25` and `ε = 1e-9` as test points only.
- **Q3 — Which delay model, and which Blend?** *Settled 2026-10-05 by the owner:* `Δ` is a
  variable, not Blend's present deadline. Every result is reported as a function of `Δ`. The
  study derives the `Δ` each lever needs, and Blend's parameters are adapted to it (C2). Inside
  `Δ`, both delay models are reported side by side, with no headline: the worst case, where an
  adversary delivers each message as late as `Δ` allows (the proofs, B2), and Blend's random
  mixing delays (the simulations, B3, C1, Phase E). The specification's Blend, testnet's and the
  TSI report's 8 s per hop are marked as reference points on the `Δ` axis.
- **Q4 — Do the five constraints C1–C5 of §0 bind?** *Settled 2026-10-05 by the owner:* all
  five bind. One relaxation is also explored, as a variant of L5: an opt-in public committee,
  where holders who choose to reveal their stake vote under their identity and everyone else
  stays private (D1). Other designs that break a constraint appear in the report as described
  alternatives with their numbers.
- **Q5 — Are protocol changes in scope?** *Settled 2026-10-05 by the owner:* yes; L2, L5 and L6
  change the protocol, and all are explored (Q1, Q9). The study ends in a ranked report that
  names RFC candidates. No specification is edited on this branch; RFCs are written later in
  `logos-lips`.
- **Q6 — Do votes travel through Blend?** *Settled 2026-10-05 by the owner:* anonymous votes
  travel through Blend, as C4 requires. The opt-in committee's votes are public and may be
  gossiped directly (D1b). Anonymous votes sent by direct gossip are described as an
  alternative, with their stake leakage measured in D5, to price what Blend buys.
- **Q7 — What budget does finality traffic get?** *Settled 2026-10-05 by the owner:* curves
  first, the line later. Costs (cover-rate multiple, bandwidth, proving and verification time)
  are reported as curves on a Raspberry Pi 5, the node the repository's benchmarks already use.
  The owner draws the budget line once the curves exist; H5 and H7 are decided then.
- **Q8 — How long must a network split heal without an operator?** *Settled 2026-10-05 by the
  owner:* no fixed horizon. Today's 35.7 h for an even split is a reference point, not a bound.
  Both routes are explored in B5. One is shorter horizons, where an operator restarts nodes after
  shorter splits and a smaller `k` becomes possible. The other is automatic recovery, where a
  node that sees a fork deeper than `k` switches to the Bootstrap rule by itself.
- **Q9 — Is Areon in scope as a replacement for the chain, and is its simulator available?**
  *Settled 2026-10-05 by the owner:* Areon is in scope as L6. The simulator that produced the
  paper's values is `~/Logos/areon-simulations`, commit `4230a92`
  (`github.com/madxor/areon-simulations`). It is one notebook, `areon-full.ipynb`, holding an
  Areon simulator with greedy and ILP attacks and a Praos baseline. It needs Python 3.13,
  `pulp`, `numpy`, `joblib`, `psutil`, `matplotlib` and `pyvis`. Its own note puts a full run at
  up to 48 h on an M3 Pro with 48 GB. The owner warns it may not be correct, so E0 audits it
  before E1 relies on it.

## 4. Work plan

### Phase A — the baseline and the map (`MAPPING.md`)

- **A1.** Measure, in the TSI engine at each Blend configuration of Q3: the orphan share, the
  distribution of `D_vis`, the canonical growth rate, and the time to depth `d` at p50 and p95.
  Where the engine's Blend model differs from the node's (release delay uniform in
  `[1, Δ_max]` rounds, delivery deadline `T_M = ß(Δ_max + η)`), align it first.
- **A2.** The dependency map. §6 is its first draft; A2 re-derives every number in it and adds
  what changes if finality comes 10× or 100× sooner.
- **A3.** The self-healing horizon: how many blocks each side of a partition makes per hour,
  against `k`, and what returns an online node on the losing side to the honest chain.

Exit: `o` and `D_vis` per configuration, with replicates and standard errors, and `MAPPING.md`.

### Phase B — settlement (`SETTLEMENT.md`)

- **B1.** Reproduce Table 1 of the 2025-05-02 revision of Gaži, Ren and Russell with the
  authors' `LCanalysis` code (MATLAB/Octave). The code takes the honest ratio and `D = f·Δ` as
  its inputs, so Cryptarchia's cases are new values of `D`. Gate: the table reproduces, and a
  mutation of the code's inputs fails it.
- **B2.** Tables of `d(α, Δ, ε)` at `f = 1/30` over a range of `Δ`, as upper and lower bounds,
  with the reference points of Q3 marked. Add the `(α, ε)` that `k = 2160` and `k = 120` hold at
  each `Δ`, and the largest `Δ` for H1 and H2. Where the bounds stay far apart, the lower bound
  is an attack and the upper bound the guarantee; report both.
- **B3.** Validate against the engine. Add a targeted private-chain attacker (starts at the
  target block, may pre-mine, may sign several branches per win) and a delay-scheduling
  attacker. Compare measured displacement rates with B2 where they are measurable
  (`ε ≥ 1e-4`).
- **B4.** A client confirmation rule: a depth table, the assumptions a client accepts with it,
  and the third level the node's APIs would expose between tip and LIB.
- **B5.** A smaller `k` (L2). For `k` = 2160, 1080, 432, 216 and 120: the `(α, ε)` each holds
  (B2), the self-healing horizon it gives (A3), and the epoch-timed effects of §6.4. Do this
  once with the epoch tied to `k`, as today, and once with the epoch decoupled from it. Sketch
  the decoupling: which epoch phases need `k`-deep finality, and which need only chain growth or
  chain quality. Then the two routes of Q8:
  - **Shorter horizons.** What an operator must do after a split each `k` no longer heals.
  - **Automatic recovery.** A node that sees a fork deeper than `k` switches to the Bootstrap
    rule by itself. Design the trigger, then attack it: can an adversary build a deep fork that
    drags honest nodes into the Bootstrap rule to its advantage? Decides H6.

### Phase C — rate and forks (`RATE.md`)

- **C1.** The time-to-settle surface over `(f, D_vis)`, from the engine's measured `o` instead of
  the collision model. Decides H3.
- **C2.** From the `Δ` each lever needs (B2, D1, E2), derive Blend parameters that deliver it,
  through `T_M = ß(Δ_max + η)` and the resulting `D_vis`, and what they cost in privacy. Settled
  with the Blend owners, not here.
- **C3.** A fork choice that weighs referenced uncles. First compute the GHOST safe regions of
  Gaži, Motaqy and Russell at `f = 1/30` and each `Δ`. Only if a region beats the longest-chain
  rule's, write the rule and run the attacks (private chain, balance) in the engine. Decides H4.
- **C4.** A lottery threshold that rises with the slots since the parent (Ouroboros Taktikos):
  read the paper, check that the slot gap can be a public input of the proof of leadership, and
  measure the orphan share it leaves in the engine.

### Phase D — certified finality (`CERTIFIED.md`)

- **D0.** The emission budget, first. Map the cover-rate multiple `1 + n/(R·f)` over every
  committee size and round length that meets `ε`, and what the quota ceiling becomes. D1
  designs against this map. Once the owner draws the budget line (Q7), D1 states, for any
  design beyond it, what would have to change for it to fit: a larger cover budget, longer
  rounds, or fewer emissions per vote.
- **D1.** Design sketches, led by a Peras-style certificate with anonymous lottery tickets as
  votes, a fork-choice boost and a cool-down. Beside it: a two-round checkpoint gadget, and
  endorsements carried in blocks. For each: how it keeps C1–C5; how it composes with the
  longest-chain rule, `B_imm`, pruning and the uncle window (§6.4); and what it does when a round
  fails. Peras's proofs assume private sortition with a known expected committee size; D1 checks
  that the assumption holds for anonymous tickets. A seat's tag per round can reuse the
  construction of `ρ_LEAD` under a vote domain separator: fixed per note and round, unlinkable
  across rounds. Stake moved during the epoch carries no honest vote, as Crypsinous rules for
  leadership.
- **D1b.** The opt-in public committee (Q4). Holders who choose to reveal their stake vote
  under their identity; everyone else stays private. Their votes need no anonymous seats, so a
  stake-weighted committee becomes possible, and with it signature aggregation and direct
  gossip. Questions:
  - What share of all stake must volunteer for safety and liveness?
  - Whose honesty does a certificate then rest on: the volunteers' or the chain's?
  - How does the private chain treat a certificate?
  - What do volunteers reveal, and does it narrow the anonymity set of everyone else?
- **D2.** Committee tails with offline stake, error in the inferred total stake, votes split
  across forks, and Blend loss. The seat lottery is derived from the leader lottery.
- **D3.** The cost model: vote size, proving and verification time on the node of Q7, Blend
  load, and aggregation options. Cryptarchia's proof of leadership is the base for a vote
  proof; Crypsinous's leadership circuit, for scale, has 201,493 constraints. Decides H5.
- **D4.** Forward security and accountability. Cryptarchia leaves out Crypsinous's protection
  against adaptive adversaries: no note evolution, no per-slot key erasure (PoL specification,
  Comparison with Original Crypsinous PoL). Whoever later learns a note's key can therefore
  sign for its past wins, and could forge past rounds' certificates the same way. Decide
  whether votes carry their own forward security, either a per-round key erased after voting
  (as Crypsinous does per slot) or Praos's key-evolving signatures, and what a bootstrapping
  node may then trust. Then accountability: nullifiers that reveal the note key when a seat
  votes twice in a round (rate-limiting-nullifier style), and the note lock that slashing would
  need.
- **D5.** Privacy beyond the count, including what anonymous votes would leak if gossiped
  directly instead of through Blend (Q6). Crypsinous's model makes the frequency of leader
  election "the only privacy leakage"; votes add a sample every round. Each vote also reveals
  which block its sender saw, the signal the specification's tagging attack exploits
  (Limitations of Cryptarchia V1). Measure what seats leak beyond block wins, against
  `analysis-cryptarchia-de-anonymisation-of-relative-stake.md` and the leakage results of §7.
- **D6.** Simulate the leading design in the engine: time to certificate, liveness under
  partition, safety under the delay-scheduling attacker.

Exit: a ranked design with numbers, or a reasoned no.

### Phase E — the multi-proposer DAG (`DAG.md`)

- **E0.** Audit the simulator (Q9) against the paper's algorithms before any figure is trusted.
  A first read found seven items to confirm or fix:
  - **Attack choice.** Every figure cell attacks through `attack_on_block`, which calls the
    greedy attack. The ILP attack, which the paper reports as the stronger one (§6.4, §6.9), is
    present but not wired in.
  - **Delay rounding.** Arrival times are stored as `int32`, so sub-slot delays are truncated.
  - **Unbounded delay.** Delays are exponential and so have no bound, which leaves the
    theorem's `w ≥ Δ` without a `Δ`. The figure cells sweep mean delays from 2 s to 60 s and
    fix 10 s elsewhere, against the paper's stated default of 7.5 s.
  - **Units.** The notebook defines a virtual block as 30 slots (cells 22 and 24) and bins its
    histograms in 30-slot bins. The paper never defines the unit; E1 confirms it per figure.
  - **One adversary identity.** The adversary is one identity and wins at most one block a
    slot. Its withheld blocks are scored as a weight race after the fact; honest nodes never see
    them released.
  - **Reorg measure.** Reorg length is measured in slots, from the attacked block to the last
    adversarial block. The code's own comment calls this imprecise. Definition 5.1 counts
    depth along short references.
  - **Seeds.** The Areon cells set no random seed; the Praos cells do.
- **E1.** Reproduce Areon's comparison with Praos at 30 % stake with the audited simulator:
  15-block reorgs at about 1e-2 for Praos against 1.5e-5 for Areon-Base, 10-block reorgs at 0.7
  against 8e-5 (§6.9). Then run its empirical settlement procedure (§5.6): fit
  `P_reorg(d) ≈ A·e^{−ϱd}` and report `d*(ε) = ln(A/ε)/ϱ`. Gate: the paper's figures
  reproduce.
- **E2.** Instantiate at Cryptarchia's parameters: `w ≥ Δ` over the `Δ` range of B2, the
  reference points of Q3, and `α` from 0.10 to 0.30. Fit `C1` and `C2` of Theorem 5.6 and set
  `d*(ε)` and its wall-clock time against B2's chain numbers.
- **E3.** Private eligibility. Areon-Base signs blocks under an identified validator's VRF key;
  Cryptarchia's proof of leadership is anonymous and does not depend on the parent. Weight
  counts references, so a win must add weight once. The tag exists: every header carries
  `ρ_LEAD = hash(NONCE_CONTRIB_V1 ‖ sl ‖ noteID ‖ sk)`, which is fixed per note and slot, so a
  second block from the same win repeats it. Specify how the weight counts each `ρ_LEAD` once,
  and what happens to both blocks. Cryptarchia's lottery runs per note, so an
  adversary that splits its stake can win several blocks in one slot, where the simulator's
  single identity wins at most one. Measure what that adds. Check the paper's parallelism bias
  (§6.3) under the private lottery.
- **E4.** The ledger. Areon exports a partial order; its total order is an analysis device only.
  Mantle executes transactions in order, so specify a deterministic order over the preferred
  frontier's ancestors and check it against channels, SDP and the execution market. State how
  the stake inference counts a DAG, where concurrent blocks are referenced rather than orphaned.
- **E5.** The safe region under worst-case delay: does the window-filtered, CCA-local weight keep
  the longest-chain threshold, or narrow it as GHOST's weight does (§7)? Analysis, plus the
  delay-scheduling attacker of B3.
- **E6.** The cost: the emission multiplier `λ/f` (§1.7), references per block, and the
  maximum-antichain computation on the node of Q7.

Exit: Areon ranked against L1 and L5 by number, or a reasoned no.

### Phase F — the report (`reports/finality/`)

The options ranked by time gained, protocol change, privacy cost, resource cost and residual
risk, with RFC candidates. Every number reproduces from a `make` target.

## 5. Measurement protocol

- **Time to finality** is measured from the target block's publication. Report p50 and p95: for
  settlement, the time to depth `d`; for certificates, the time until the median and the 95th
  percentile node holds one.
- **Failure rates** are per block for settlement and per round for certificates, with the
  yearly expectation stated beside each.
- **Engine runs** keep the TSI conventions: burn-in, replicates, standard errors, committed
  configs, fixed seeds.
- **Gates** must fail under mutation. Each gate records the mutation that failed it.
- **Sources** are pinned: specification commit, node commit, paper version.

## 6. What depends on `k` today

First draft of A2. Specifications at `logos-lips` `47a73cdc`; node at `logos-blockchain`
`4e0405d51`.

### 6.1 The rules that read `k`

| role | where | what `k` sets |
| --- | --- | --- |
| finality | `cryptarchia-v1-protocol.md`: Latest Immutable Block, Chain Maintenance, Commit, Fork Pruning, Block Header Validation rule 8 | `B_imm` is the `k`-deep block under the Online rule; forks diverging below it are pruned; a block at or below its height is rejected |
| Online fork choice | `fork-choice.md` (`maxvalid-mc`) | a fork deeper than `k` is ignored: `k` is the maximum rollback |
| Bootstrap fork choice | `fork-choice.md` (`maxvalid-bg`); `cryptarchia-v1-bootstr-sync.md` | a fork deeper than `k` is decided by density over `s_gen = ⌊k/4f⌋` slots (4.5 h). A node enters the Bootstrap rule only at startup: from genesis or a checkpoint, after more than `T_offline` = 20 min offline, or on the operator's flag. It stays in it for `T_boot` = 24 h |
| epoch | protocol, Epoch Schedule | `10⌊k/f⌋` slots in phases of 3, 3 and 4 `⌊k/f⌋` that wait for the snapshot, the nonce and the inferred stake to finalize; the inference counts the first `6⌊k/f⌋` slots |
| uncle window | protocol, note under Uncle Selection | `W ≤ ⌊0.6k⌋` keeps every uncle candidate inside the finalization window |

The offline grace period rests on the attacker being unable to grow a `k`-block fork within it.
Its margin `(k/f)/T_offline` is 54.0 at `k = 2160` and 3.0 at testnet's `k`.

### 6.2 What reads `k` through the epoch

Since sessions were removed (`blend-protocol.md` revision 1.1.0, 2026-06-22), these protocols run
on consensus epochs, so `k` times them:

- **SDP.** Services read the registry of `finalized_epoch = current_epoch - 2`. A declaration
  serves from epoch `e+2`; a withdrawal takes effect at `e+2`.
- **Blend.** The epoch is written as `E = 648000` rounds. Quotas, keys, nullifier caches and
  rewards are per epoch.
- **Proof of work.** `EXPECTED_BLOCKS_PER_EPOCH = 21_600`, commented `N_b = 10 k`.
- **Rewards.** Leader vouchers and service rewards settle at epoch boundaries.
- **Proof of leadership.** A note is eligible once it was in the note set at the start of the
  previous epoch.
- **Storage market.** The price is fixed within a timeframe, an epoch for permanent storage.

### 6.3 Who waits for finality

In the specifications:

- **Mantle.** A Zone crediting a deposit waits for finality or uses the atomic transfer. Channel
  parent references exist because "Cryptarchia has long finality times".
- **Cross-channel messaging** (template). Asynchronous messages wait for finality. "Channels can
  choose a specific probability threshold or wait for finality to achieve a 100% guarantee" —
  the place a settlement rule plugs in.
- **Architecture overview.** "Block finalizes after being buried by 2160 blocks".

In the node:

- **The LIB** is the `k`-th ancestor of the node's own tip under the Online rule, and frozen under
  the Bootstrap rule (`consensus/cryptarchia-engine/src/lib.rs`, `lib`).
- **Consumers.** The wallet prunes state at the LIB, and its leader-claim reservations expire
  after `k` immutable blocks. The SDP service stops tracking an activity once it is in the LIB
  ledger. The zone SDK and `logos_sql` finalize transactions, deposits and channel notes when the
  LIB advances. The HTTP and C APIs expose `lib-stream`, immutable-only block queries and `lib`
  in `info`. Storage and sync prune at the LIB.
- **Not consumers.** The mempool, proof-of-work claims, the leader and Blend membership work
  from the tip.
- **Two levels only.** The APIs expose the tip and the LIB. No confirmation depth exists.
- **`k` is a deployment setting**, not committed in genesis. No configuration sets 2160:
  testnet 0.3.0 uses 120 at `f = 1/30`, the embedded default 30 at `f = 1/20`.
- **The prolonged bootstrap period** defaults to 1 h in the node, against 24 h in the
  specification.

### 6.4 What each route changes

- **A smaller `k` (L2)** shrinks every epoch-timed rule of §6.2 unless the epoch is decoupled
  from `k`. At `k/10`: the epoch is 18 h and SDP's two-epoch lag 36 h; the inference's
  per-epoch noise grows by `√10` (TSI report, Appendix B); the per-epoch anonymity set of leader
  vouchers shrinks tenfold; the offline grace margin falls from 54.0 to 5.4; the even-split
  partition horizon from 35.7 h to 3.6 h. `W = 12` needs `k ≥ 20`.
- **Why the epoch phases are sized from `k`.** Praos sizes its windows from chain growth:
  `8k/f` slots add `k` blocks. That way the stake snapshot is `k` deep before the nonce is drawn,
  an honest block contributes to the nonce, and a quiet period lets the nonce settle (Theorem 11
  and its proof; epoch `24k/f`, nonce from its first `16k/f` slots). Cryptarchia's phases of 3, 3
  and 4 `⌊k/f⌋` play the same three roles; no document derives the 3. Under a faster finality
  notion, the snapshot and settling phases could shrink toward its finality time. The buffer
  that guarantees an honest nonce contribution is set by chain quality and grinding, not by
  finality.
- **A faster notion beside `k` (L1, L5, L6)** helps the direct consumers of §6.3 at once. The
  epoch-timed rules of §6.2 gain nothing unless rewritten against a finalized block, as SDP's
  `current_epoch - 2` could be. A certified block must never be reverted, so `B_imm` becomes at
  least the latest certified block in commit, pruning and rule 8. If certification comes sooner
  than the 360-slot uncle window, pruning at it would discard uncle candidates the inference
  still needs; D1 decouples the two.

## 7. Literature to reproduce before it is relied on

### 7.1 Read for this plan

- David, Gaži, Kiayias, Russell, "Ouroboros Praos: An Adaptively-Secure, Semi-synchronous
  Proof-of-Stake Blockchain", EUROCRYPT 2018; ePrint 2017/573, revision 2023-04-27 (SHA-1
  `373e7ba1`). Theorem 7 is the condition the specification quotes. Theorem 11 and Corollary 3
  cover the full protocol. Also used: the epoch rule `R = 24k/f` and its windows, and
  key-evolving signatures. §1.3, §6.4, D4.
- Kerber, Kiayias, Kohlweiss, Zikas, "Ouroboros Crypsinous: Privacy-Preserving
  Proof-of-Stake", IEEE S&P 2019; ePrint 2018/1132, revision 2019-05-15 (SHA-1 `5a9913a9`). It
  proves no consensus theorem of its own. It treats leader-election frequency as the only
  leakage. Its coin evolution and per-slot key tree are what Cryptarchia leaves out, and its
  leadership circuit has 201,493 constraints. D1, D3–D5.
- Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System", §11. The attacker tables; gate.
- Grunspan, Pérez-Marco, "Double spend races", IJTAF 21(8), 2018; arXiv 1702.02867v3.
  `P(z) = I_{4pq}(z, 1/2)` and the corrected tables; gate.
- Dembo, Kannan, Tas, Tse, Viswanath, Wang, Zeitouni, "Everything is a Race and Nakamoto Always
  Wins", ACM CCS 2020; arXiv 2005.10484v4. Eq. (2), the private-attack threshold, is the true
  threshold for proof of work and for Ouroboros/Snow White proof of stake; gate.
- Gaži, Ren, Russell, "Practical Settlement Bounds for Longest-Chain Consensus", CRYPTO 2023;
  ePrint 2022/1571, revised 2025-05-02; code `github.com/renling/LCanalysis`. B1's method.
- Gaži, Motaqy, Russell, "A Tight Analysis of GHOST Consistency", ePrint 2024/1830, revised
  2026-09-11. GHOST's safe region is inferior to the longest-chain rule's; C3.
- CIP-0140, "Ouroboros Peras – Faster Settlement", status Proposed. Committee `n = 900`, quorum
  `τ = 675`, round `U = 90` slots, boost `B = 15` blocks, cool-down `K = 780` rounds. Fast
  settlement against up to a quarter of the stake, Praos-like behaviour above it. Settlement
  known "after as little as two minutes". Voters drawn by VRF sortition among stake-pool
  operators; D1.
- Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and Resilient Multi-Proposer
  Consensus", arXiv 2511.23025v1, 2025-11-28; Phase E. Theorem 5.6 gives `(k, ε)`-finality once
  `k ≥ C1·w + C2·ln(1/ε)`, for absolute constants `C1`, `C2`, under honest stake above 1/2,
  `w ≥ Δ` and honest coverage `q > 0`. Depth is counted along references inside the window, and
  `T_final = k·τ_slot`. Its worked example fits `C1 ≈ 1.8` and `C2 ≈ 2.7` for illustration,
  giving `k ≈ 91` at `w = 30` and `ε = 1e-6`. The simulations (default: 7.5 s mean delay,
  `w = 30`, 30 % stake, 1,000 validators) compare against Praos at `f = 0.05`. Their finality
  proxy, the age after which the reorg probability falls below 1e-6, is "roughly 30–40 virtual
  blocks" at 30 % stake, a 0.5 s delay and `w = 30`, and about 60 at 45 % (§6.8). At the
  notebook's 30 slots a virtual block (E0), that is 900–1,200 slots at 30 % stake, 15–20 min at
  1 s slots, not the worked example's 91 s. The model makes
  four assumptions Phase E must lift:
  - Validators are identified: each block carries a validator, a VRF proof and a signature.
  - Privacy-preserving stake is "orthogonal to our fork-choice rule but interact[s] with
    eligibility and incentives".
  - Each block carries one payload.
  - The total order is an analysis device only.

### 7.2 To read before use

Identified by the literature survey run for this plan, which checked each identifier. Not yet
read here.

- **Settlement analysis.** Gaži, Kiayias, Russell, "Tight Consistency Bounds for Bitcoin", CCS
  2020. Guo, Ren, "Bitcoin's Latency–Security Analysis Made Simple", AFT 2022. Li, Guo, Ren,
  "Close Latency–Security Trade-off for the Nakamoto Consensus", AFT 2021. Kiffer, Rajaraman,
  shelat, "A Better Method to Analyze Blockchain Consistency", CCS 2018, which also treats GHOST
  and the balance attack. Blum, Kiayias, Moore, Quader, Russell, "The Combinatorics of the
  Longest-Chain Rule: Linear Consistency for Proof-of-Stake Blockchains", SODA 2020.
- **Random delay.** Sankagiri, Gandlur, Hajek, "The Longest-Chain Protocol Under Random Delays",
  Stochastic Systems 2023. The model nearest Blend's random mixing delays; B1, B3.
- **Leader election.** Azouvi, Cappelletti, "Private Attacks in Longest Chain Proof-of-Stake
  Protocols with Single Secret Leader Elections", AFT 2021. What independent lotteries cost in
  settlement.
- **Finality overlays.** Badertscher, Coretti, Gaži, Kiayias, Russell, "Adaptively Secure Fast
  Settlement with Dynamic Participation and Self-Healing" (the Peras paper), SCN 2026. Neu, Tas,
  Tse, "Ebb-and-Flow Protocols", IEEE S&P 2021. FIP-0086, "Fast Finality in Filecoin (F3)", a
  deployed overlay whose finality halts while the chain continues. Pass, Shi, "Thunderella",
  EUROCRYPT 2018.
- **Votes under changing participation.** D'Amato, Neu, Tas, Tse, "Goldfish", FC 2024. Malkhi,
  Momose, Ren, "Towards Practical Sleepy BFT", CCS 2023. D'Amato, Saltini, Tran, Zanolini,
  TOB-SVD, ICDCS 2025. Their voters are identified, so C1 rules them out as specified.
- **Ruled out by C1 as specified** (voters identified, weights public). Casper FFG; Gasper;
  GRANDPA; Afgjort (SCN 2020); Mithril (CANS 2024). GRANDPA and Afgjort also bind block
  production to finality, against C2.
- **Anonymous committees.** Ganesh, Orlandi, Tschudi, "Proof-of-Stake Protocols for
  Privacy-Aware Blockchains", EUROCRYPT 2019 (anonymous VRF). Baldimtsi, Madathil, Scafuro, Zhou,
  "Anonymous Lottery in the Proof-of-Stake Setting", CSF 2020. David, Lavagnino, Pagnin,
  Stankovski Wagner, "Tail-Hammer", SCN 2026 (committee statistics). Gilad, Hemo, Micali,
  Vlachos, Zeldovich, "Algorand: Scaling Byzantine Agreements for Cryptocurrencies", SOSP 2017
  (committee sizes against a 20 % adversary).
- **Leakage.** Kohlweiss, Madathil, Nayak, Scafuro, "On the Anonymity Guarantees of Anonymous
  Proof-of-Stake Protocols", IEEE S&P 2021; D5.
- **Structural.** Fitzi, Gaži, Kiayias, Russell, "Ledger Combiners for Fast Settlement", TCC
  2020. Bagaria, Kannan, Tse, Fanti, Viswanath, "Prism", CCS 2019. Schutza, Behrens, Duong, Aman,
  "Ouroboros Taktikos", BlockSys 2023; C4.
- **Impossibility.** Lewis-Pye, Roughgarden, "Resource Pools and the CAP Theorem", arXiv
  2006.10698. Pass, Shi, "The Sleepy Model of Consensus", ASIACRYPT 2017. They bound what any
  design can offer: a ledger live under unknown participation cannot also be safe under
  partition, so fast finality is either probabilistic or a finalized prefix that may lag.

### 7.3 What the survey did not find

- A finality committee that keeps voter stake private. The two privacy chains it found with
  committee finality, Dusk and Zcash Crosslink, publish voter stake. D1 has no template to
  copy.
- A proof-of-stake confirmation rule that conditions on observed forks, density or
  participation. B4 could test one in the engine.
- A documented derivation of `k = 2160`, for Cardano or for Cryptarchia.
