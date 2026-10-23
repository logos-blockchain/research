# Three designs

Phase H of `PLAN.md`: the three questions the routes of the report leave open, each with a
hypothesis that can fail (H8–H10). Tables come from `runs/` through `scripts/tables.py`; runs from
`scripts/h1_attestations.py`, `scripts/h2_delay.py` and `scripts/h3_time_rule.py`. The adversary's
share is `α`, `ε = 1e-9` unless stated.

## H.1 — a recovery trigger that survives a partition

**What no local rule can do.** After an even partition under a coalition holding a third of the
stake, three chains stand: two honest sides, each produced by a third of the stake, and the
coalition's withheld fork, produced by a third. Each is a valid chain of lottery wins; none carries
a mark of having been public, since a block proves its slot and its producer's win and nothing
about who saw it. A rule that reads the chains and their stake-weighted content alone sees three
objects of the same law and picks the coalition's fork with probability at least a third. Below a
third the honest sides hold `(1 − α)/2 > α` each, and the question becomes how much stake-weighted
evidence separates `(1 − α)/2` from `α` at `ε`. B5's density test over a window is such evidence,
and its noise is what loses it: a 30 % fork beats a 35 % side in 64–70 % of windows (B5, rule 8).

**Recovery attestations.** A one-off round of anonymous-seat votes, Phase D's machinery
(`CERTIFIED.md`), cast only after a node holds two chains that both exceed `k` blocks since their
divergence. Each node votes for the chain it followed; a chain is kept when its seats exceed a
threshold `θ`, and among the chains kept the densest wins, ties broken by rule 7. With `n` expected
seats in the round, a chain backed by a share `s` draws Poisson(`s·n`) seats. `θ` and `n` are the
fewest at which the coalition's fork, backed by `α`, reaches `θ` with chance at most `1e-9` while an
honest side of an even partition, backed by `(1 − α)/2`, falls short of `θ` with chance at most
`1e-6`. Whether a count suffices is not monotone in the count, since `θ` moves in whole seats, so
every count is scanned (`finality_sim.further.attestation_seats`). The table also gives the seats
with a tenth of the honest votes lost, and with the votes lost when the coalition holds a share `α`
of the relays and they drop what they carry, as in G6. A vote crosses the specification's three
hops, so a copy is lost with chance `1 − (1 − α)^3`, and a vote sent as two copies with its square;
the coalition's own votes are delivered:

| α | honest side | seats, every honest vote counts | a tenth of honest votes lost | relays at α dropping, one copy | two copies |
| --- | --- | --- | --- | --- | --- |
| 0.20 | 0.400 | 832 (θ = 250) | 1,224 (θ = 345) | 49% lost: 1,014,927 (θ = 205,694) | 24% lost: 2,612 (θ = 666) |
| 0.25 | 0.375 | 2,271 (θ = 717) | 4,388 (θ = 1,302) | 58% lost: none | 33% lost: none |
| 0.30 | 0.350 | 14,966 (θ = 4,898) | 157,799 (θ = 48,651) | 66% lost: none | 43% lost: none |
| 0.32 | 0.340 | 95,242 (θ = 31,531) | none | 69% lost: none | 47% lost: none |
| 0.33 | 0.335 | 1,536,940 (θ = 511,468) | none | 70% lost: none | 49% lost: none |

- **A round of 2,300 seats separates a quarter; 15,000 separate 30 % if every honest vote
  counts,** 158,000 if a tenth are lost. At 32 % the round needs 95,000 seats with every vote
  counted and none suffices with a tenth lost; at a third none at all. H8's figure of 10,000
  seats fails at 30 %; a one-off round of 15,000 is a burst of votes once per incident, not D0's
  cover multiple per round.
- **The seats hold only while Blend's relays deliver.** Relays at the coalition's share that drop
  what they carry lose 58–66 % of single-copy votes against 25–30 %, and 33–43 % of votes sent as
  two copies. At those losses an honest side's delivered share falls to the fork's or below, and
  no count of seats separates a quarter or 30 %; against a fifth two copies keep the round at
  2,612 seats. The round then rests on the sender's fallback, if votes carry the one Blend gives
  block proposals and transactions (`blend-protocol.md`, Delivery failure): a vote not seen
  within `T_M = 15` rounds is broadcast directly, so it arrives, and its voter is identified (G6).
- **The coalition's moves.** Its seats go where it likes: to its fork, which the threshold
  discards; or to one honest side, which then wins over the other, a choice between two honest
  histories that any resolution of a partition gives it. Votes withheld lower its fork's count.
  Votes cast before the sides are fully reconnected miss the round, which is why the round starts
  only when a node holds both chains.
- **What the round costs once.** `n` votes through Blend within the round's window, each a lottery
  win carried as D1 carries a vote; D5's leakage applies to the one sample.

**Anchoring, placed.** A checkpoint written to another chain timestamps a block. It does not show
that the block was public: the coalition anchors the blocks of its private fork as any node
anchors the public chain's, and it can anchor first, so a rule in which the first anchored fork
wins hands it the choice. An anchor carrying a proof of leadership is stake-weighted and meets the
symmetry above. What an anchor settles is a fork older than the anchor, which is the
long-range fork of B5's horizon `H`, and the start of a bootstrapping node. Which mechanism
resolves which split:

| the split | resolved by |
| --- | --- |
| an eclipse: one side is the whole honest chain | B5's trigger, rules 1–8 |
| a partition deeper than `k`, below a third | recovery attestations, while the relays deliver the votes |
| a partition deeper than `k`, at a third | nothing local; operators |
| a fork from bought keys older than `H` | an anchor, or `H` itself |
| a node starting from genesis | a checkpoint |

**Partition detection.** Rule 8's test as a detector: a node compares its canonical count over
the window with the count the honest stake `1 − α` makes alone, and declares its chain sparse
below the `1e-9` lower tail of that count (`finality_sim.further.detector_power`, the
specification's Blend under random delay). While the detector fires the node reports `B_imm` as
provisional and refuses the recovery comparison. The chance that a side holding a share of all
stake is declared sparse; the whole honest stake, 0.70 against 30 %, gives the false-alarm rate:

| α | window | expected, honest alone | threshold | side 0.350 | side 0.500 | side 0.570 | side 0.600 | side 0.650 | side 0.700 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 36 h | 2,600 | 2,274 | 1.0000 | 1.0000 | 0.9999 | 0.926 | 0.0087 | 9e-10 |
| 0.30 | 72 h | 5,200 | 4,719 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.202 | 1e-09 |
| 0.33 | 36 h | 2,476 | 2,160 | 1.0000 | 1.0000 | 0.916 | 0.159 | 8e-07 | 2e-17 |
| 0.33 | 72 h | 4,952 | 4,487 | 1.0000 | 1.0000 | 1.0000 | 0.871 | 1e-05 | 3e-21 |

- **Every side of an even partition is detected,** and with a 36-hour window against 30 % any
  side holding up to 0.57 of all stake with chance 0.9999 or more, one of 0.6 with 0.926. A side
  of 0.65 passes as full in 99 % of windows, which is a partition that took 7 % of the stake
  away: the trigger's window then compares a 0.65 side against a 0.30 fork and holds.
- **The detector reads a side only while it runs at the thresholds set before the split.** Each
  side's inference corrects in full from its own chain. An epoch's thresholds come from the first
  `6⌊k/f⌋` slots of the epoch before and apply from its first slot
  (`cryptarchia-total-stake-inference.md`), and an epoch lasts `10⌊k/f⌋` slots
  (`cryptarchia-v1-protocol.md`). A side therefore keeps its old thresholds for at least `4⌊k/f⌋`
  slots after the split, 3 days at `k = 2160`. At the next epoch boundary it is corrected in
  proportion to the part of that period which followed the split, and it is corrected in full
  `10⌊k/f⌋` to `20⌊k/f⌋` slots after the split, 7.5 to 15 days. From then on every chain fills
  its slots at `f`, the coalition's fork included, and neither the detector nor a comparison of
  densities tells them apart. A window that closes within 3 days of the split reads every case,
  so the detector runs on every window, not on demand.

## H.2 — the delay function and its speed ratio

G1 passes B7's nonce through a sequential delay so that the coalition chooses blind. Honest nodes
pay `R·T_a` for a delay of `T_a` on the coalition's hardware and a speed ratio `R`.

**The rule in Praos's model.** Stake is fixed within an epoch, every honest block arrives within
`Δ`, hashes are random oracles, and the delay is a random oracle whose answer takes `T_a` on the
coalition's hardware and `R·T_a` on an honest node. A leader schedule drawn from a uniformly random
nonce is bad with probability `ε_e`; Praos's bound for the full protocol carries a grinding term
for the nonces the adversary can evaluate (below). For the rule, a **candidate** is a value of the
pre-nonce
`hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)` the coalition can still bring about. A choice among candidates
whose outputs it has not seen is blind: given its view the chosen output is uniform, and the
schedule is bad with `ε_e`. A choice among candidates whose outputs it has seen multiplies `ε_e`
by their expected number, since each output is uniform at the moment the candidate is formed. The
factor per nonce counts the candidates whose outputs the coalition sees while it can still make
them the nonce (the lemma below), and a proof needs that count bounded.

**What the papers state** (Praos: ePrint 2017/573, revision 2023-04-27, SHA-1 `373e7ba1`;
Genesis: ePrint 2018/378, revision 2019-02-22, SHA-1 `81b39baf`; both read 2026-10-09 from the
archive's snapshots of 2025-01-02 and 2024-12-28). Praos models the adversary's influence on the
nonce as a resettable beacon and bounds it by a union bound over the candidates: "A simple
application of the union bound shows that this selection of η from among a set of size r
uniformly random candidate nonces can inflate the probability of events during the run of πSPoS
by a factor no more than r" (§4.9). Its Theorem 11 carries the factor as `log r`: the protocol
"satisfies persistence with parameters k and liveness with parameters u = 8k/f throughout a
period of L slots of ∆-semisynchronous execution with probability 1 − exp(ln L + ∆ + log(r) −
Ω(k))". With the beacon replaced by a hash of the VRF values, Corollary 3 bounds `r` by the
adversary's oracle queries, "with probability 1 − exp(ln L + ∆ − Ω(k − log tkq))", since "the
size of this space is however upper-bounded by the number of random oracle queries that the
adversary can afford" (§5). The nonce is `η_j = H(η_{j−1} ‖ j ‖ v)` over the VRF values of the
blocks of epoch `j − 1` "up to the slot with timestamp up to (j* − 2)R + 16k/f" (Fig. 10), and
"the stakeholder distribution is determined in each epoch j ≥ 2 by the block that has time stamp
up to (j − 2)R" (proof of Theorem 11), so the stake is fixed before the nonce's inputs. Genesis
keeps the nonce rule, "a hash of additional VRF-values y_ρ that were included … into blocks from
the first two thirds of epoch ep − 1", with the stake "recorded in the ledger up to the last block
of epoch ep − 2" (§3). Its Theorem 1 states Praos's bounds for `maxvalid-mc` with a term `ε_lift`
that carries `Q`, "an upper bound on the total number of queries issued to G_RO", and its
Theorem 2 adds for `maxvalid-bg` only "an additional error probability exp(ln L − Ω(k)) +
ε_CG(βf/16, k/(4f)) + ε_∃CQ(k/(4f)) + ε_CP(kβ/64)" when "k > 192∆/(εβ) and R/6 ≥ s = k/(4f) ≥
48∆/(εβf)" (§4.3). Of grinding it says: "the process of deriving it described above still allows
a limited amount of grinding by the adversary, who can decide whether to include blocks (with VRF
outputs) in slots where he is a slot leader. In [14], it is shown that this grinding effect can be
crudely upper-bounded by limiting the number of queries to the random oracle that the adversary
makes … The same argument applies here, and hence we need to introduce the quantity Q into our
bound" (Appendix E), and of its combinatorial objects: "the characteristic string resulting from
an execution is determined by both the nonce (and the effective leader selection process), the
adaptive adversary A, and the environment Z (which, in particular, determines the stake
distribution)" (Appendix E).

**The lemma, placed.** Both papers bound the nonce's bias by the number of candidates the
adversary can set the nonce to, `r`, through a union bound, and then bound `r` by the oracle
queries. The rule here keeps that structure and changes what bounds `r`: a candidate counts only
if the adversary sees its output while it can still make it the nonce, so `r` is the number of such
candidates, bounded below for the design of this section, and the bound is Theorem 11's with `r`
read at it. Cryptarchia's Online rule is `maxvalid-mc` within `k` and its Bootstrap rule
`maxvalid-bg` (`MAPPING.md`), so Theorem 1 covers the first and Theorem 2 the second; the nonce
enters both through the leader schedule alone, and the stake of epoch `ep − 2` is fixed before
any candidate exists, as the lemma requires. What the papers bound with `Q` and the rule with the
candidates it sees is the same quantity.

A candidate of the last sub-window needs `μ_1 … μ_(m−1)`, fixed when the sub-window starts, and a
value for `μ_m`: an honest contribution once its block is received, or one of the coalition's
own, which it knows in advance for every slot, since `ρ_LEAD` depends on the slot, the note and
the key. Candidates therefore exist from the start of the last sub-window, `W = ⌊6⌊k/f⌋/m⌋`
slots before the cut-off, 4.3 hours at `k = 2160`, and the coalition evaluates them hours before
it withholds a block of its own or removes an honest one. G1 took a candidate to be formed when
the coalition must act, within minutes of the choice. That was wrong: a delay of ten minutes
blinds only the choices formed in the last ten minutes of the sub-window, and leaves B7's
estimate. Two changes make the delay work:

- **The delay spans the sub-window:** `T_a = W + margin`. A candidate formed at the sub-window's
  start is seen at the cut-off plus the margin, one formed later as much later, and it counts only
  if a fork that reaches it can still be published when it is seen (`finality_sim.formation`).
- **The contribution is bound to the parent's contribution.** The win tag `ρ_LEAD(b)` stays as
  today, independent of the parent. Every node derives the nonce contribution from public values,
  `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`, and the minima `μ_i` are taken over `c`.
  A contribution then exists only once every block before it on its branch does, back to the block
  the branch forks from, and no body or proof enters it; it adds nothing to the proof of
  leadership. The coalition forms no value of a branch before that block arrives and cannot predict
  a sub-window's minimum ahead, which replaces B7's conditions 1 and 2, the binding to the epoch
  nonce and the notes frozen one epoch earlier; `m` is then set by B7's condition 3 and by the
  honest cost below.

**The binding.** The win tag `ρ_LEAD` stays independent of the parent, since the weight, the tie
rule and the detection of a win published twice read it (Phase J, J.1). The nonce's minima are
taken over a contribution `c(b) = hash(NONCE_CONTRIB_V2 ‖ v(parent) ‖ ρ_LEAD(b))` for some value `v`
of the parent. Four values were weighed:

- *The parent block's identifier.* It hashes the parent's header, which commits to the body and
  carries the proof (`cryptarchia-v1-protocol.md`), and the coalition varies its own block's body,
  or re-randomises its proof, at will: every block after its first on a branch takes as many
  contributions as variants it computes.
- *The parent's slot.* One contribution per win and parent slot, known ahead for every parent,
  honest ones included, so no value waits for its branch.
- *The parent's win tag*, the parent's own `ρ_LEAD`, which does not depend on the parent's ancestry
  and cannot be varied: one contribution per win and parent. The tag of the coalition's own win is
  known as soon as the win is, so a win on its own previous win has a value known ahead, as B7's
  own contributions are.
- *The parent's contribution*, `v = c`, chained: one contribution per win and chain prefix. A value
  exists only once its prefix does, the block the branch forks from included, and no body or proof
  enters it.

With no delay, the values the last sub-window's minimum can take at the cut-off, over every feasible
fork and every subset of the coalition's wins after it (`formation.binding_counts`, 4,000 windows a
cell; windows past 200,000 subsets are left out, so the prefix column is from below):

| delay | α | k | one per win | one per parent | one per chain prefix | windows left out |
| --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2,160 | 1.025 ± 0.003 | 1.069 ± 0.005 | 11.7 ± 2.6 | 36 |
| random, specification | 0.30 | 1,620 | 1.041 ± 0.003 | 1.094 ± 0.006 | 9.9 ± 1.9 | 29 |
| random, specification | 0.30 | 1,080 | 1.058 ± 0.004 | 1.153 ± 0.009 | 24.1 ± 4.8 | 30 |
| random, specification | 0.33 | 2,160 | 1.051 ± 0.004 | 1.132 ± 0.007 | 23.7 ± 2.6 | 127 |
| random, specification | 0.33 | 1,620 | 1.070 ± 0.005 | 1.188 ± 0.011 | 63.8 ± 10.2 | 120 |
| random, specification | 0.33 | 1,080 | 1.108 ± 0.006 | 1.283 ± 0.014 | 52.8 ± 7.6 | 150 |
| worst, 10 s | 0.30 | 2,160 | 1.028 ± 0.003 | 1.057 ± 0.004 | 7.6 ± 2.0 | 16 |
| worst, 10 s | 0.30 | 1,620 | 1.042 ± 0.003 | 1.107 ± 0.007 | 15.8 ± 3.6 | 11 |
| worst, 10 s | 0.30 | 1,080 | 1.058 ± 0.004 | 1.134 ± 0.008 | 17.5 ± 4.7 | 16 |
| worst, 10 s | 0.33 | 2,160 | 1.052 ± 0.004 | 1.133 ± 0.008 | 33.3 ± 4.6 | 125 |
| worst, 10 s | 0.33 | 1,620 | 1.070 ± 0.004 | 1.182 ± 0.009 | 32.8 ± 5.0 | 89 |
| worst, 10 s | 0.33 | 1,080 | 1.114 ± 0.006 | 1.304 ± 0.015 | 74.5 ± 10.9 | 109 |

Under the delay the count that matters is the values whose output the coalition sees while a fork
that reaches them can still be published, and that turns on when each value is formed: an honest
minimum when its block arrives; a value known ahead at the sub-window's start, B7's contribution
and, bound to the parent's win tag, a win on the coalition's own previous win; bound to the
parent's contribution, every value of a branch when the block it forks from arrives. Per window,
each value counts where a fork with every win the value allows reaches it, and the default counts
too when it is seen while a branch the coalition has not seen can still replace it, a blind switch
(the lemma below), by a union bound over that branch's values (`formation.formation_counts`,
100,000 windows a cell at `k ≤ 1620`, 50,000 at 2160; a window whose deepest fork empties the
sub-window counts in full). At margins of 10 / 20 minutes, with the share of windows in which a
choice is still open:

| delay | α | k | open | every value at the start | per win | parent's win tag | parent's contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2,160 | 0.18 / 0.05 | 1.012 / 1.003 | 1.004 / 1.001 | 1.010–1.011 / 1.003–1.003 | 1.0024 / 1.0007 |
| random, specification | 0.30 | 1,620 | 0.18 / 0.05 | 1.016 / 1.005 | 1.006 / 1.002 | 1.014–1.016 / 1.004–1.005 | 1.0038 / 1.0011 |
| random, specification | 0.30 | 1,080 | 0.18 / 0.05 | 1.025 / 1.009 | 1.010 / 1.003 | 1.021–1.027 / 1.007–1.009 | 1.0067 / 1.0022 |
| random, specification | 0.33 | 2,160 | 0.32 / 0.15 | 1.036 / 1.020 | 1.015 / 1.007 | 1.043–1.051 / 1.021–1.025 | 1.0105 / 1.0052 |
| random, specification | 0.33 | 1,620 | 0.32 / 0.15 | 1.050 / 1.027 | 1.022 / 1.010 | 1.060–1.076 / 1.030–1.038 | 1.0160 / 1.0080 |
| random, specification | 0.33 | 1,080 | 0.32 / 0.14 | 1.100 / 1.057 | 1.054 / 1.034 | 1.107–1.146 / 1.061–1.081 | 1.0417 / 1.0288 |
| worst, 10 s | 0.30 | 2,160 | 0.16 / 0.05 | 1.010 / 1.004 | 1.004 / 1.001 | 1.009–1.010 / 1.003–1.003 | 1.0028 / 1.0010 |
| worst, 10 s | 0.30 | 1,620 | 0.16 / 0.05 | 1.016 / 1.006 | 1.007 / 1.002 | 1.013–1.016 / 1.004–1.005 | 1.0034 / 1.0011 |
| worst, 10 s | 0.30 | 1,080 | 0.16 / 0.05 | 1.024 / 1.009 | 1.010 / 1.003 | 1.019–1.025 / 1.006–1.008 | 1.0060 / 1.0018 |
| worst, 10 s | 0.33 | 2,160 | 0.30 / 0.13 | 1.034 / 1.017 | 1.015 / 1.007 | 1.040–1.047 / 1.019–1.023 | 1.0091 / 1.0046 |
| worst, 10 s | 0.33 | 1,620 | 0.30 / 0.14 | 1.049 / 1.026 | 1.022 / 1.010 | 1.054–1.069 / 1.026–1.033 | 1.0148 / 1.0070 |
| worst, 10 s | 0.33 | 1,080 | 0.30 / 0.14 | 1.093 / 1.050 | 1.053 / 1.032 | 1.098–1.136 / 1.054–1.072 | 1.0373 / 1.0253 |

- **The parent's contribution leaves the fewest values seen:** 1.009 against a third under the
  worst case at `k = 2160` and a margin of 10 minutes, almost all of it the blind switch, against
  1.015 for B7's contributions and 1.040–1.047 for the parent's win tag. A value formed at the
  sub-window's start is seen at the margin, when a choice is still open in 30 % of windows; a
  branch's values under the chained binding are seen `W + margin` after the block it forks from
  arrives, which only a branch that keeps up with the honest chain for 4.5 hours survives.
- **The parent's win tag does worse than no binding,** since its pairs of the coalition's own wins
  add values formed at the start. It also leaves those values known from the epoch's start, so a
  coalition that holds the minima of the last two sub-windows with them forms candidates before the
  last sub-window starts, which the table does not count.
- **The parent's contribution is recommended.** The parent block's identifier forms its values at
  the same times, so under the delay it leaves the same count, but a branch that survives the
  delay's span brings as many body variants as the coalition computes, and with the delay broken
  the variants are free. The chained contribution leaves one value per chain prefix, the count of
  the first table, which is what a coalition that breaks the delay would face; under the delay it
  enters only through the branches that survive.

**The evaluator term.** A branch that keeps up with the honest chain over the delay's span brings
values the coalition sees while they are still reachable, one per chain prefix. An evaluation takes
`T_a`, longer than the sub-window, so a coalition with `E` delay evaluators sees at most about `E`
of them. The walk bounds the chance that any branch survives: at one of the sub-window's fork
points, `E[N] + 1` of them, the coalition's wins over the `W + margin` slots after it must outnumber
the canonical honest blocks (`formation.branch_survival`, `formation.evaluator_bound`), or the
deepest fork must empty the sub-window (the crossing law of the bound below). The factor is then at
most the walk's bound on `E[G_min]`, plus the blind switch, bounded by the open chance averaged over
the default's arrival in the sub-window (`formation.blind_bound`, 100,000 windows), plus `E` times
the chance that a branch survives. At a margin of 10 minutes, the depth at `1e-9` with two nonces
with one evaluator, sampled and at the bounds, and the most evaluators each `k` admits before the
depth at the bounds passes it:

| delay | α | k | branches seen | the walk's bound | blind switch, sampled / bound | depth, one evaluator, sampled | depth, one evaluator, bound | evaluators within k, bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2,160 | < 2e-05 | 7.5e-11 | 2.3e-03 / 6.2e-03 | 165 → 165 | 165 | 3.1e+27 |
| random, specification | 0.30 | 1,620 | < 1e-05 | 7.8e-08 | 3.4e-03 / 8.6e-03 | 165 → 165 | 166 | 3.0e+24 |
| random, specification | 0.30 | 1,080 | < 1e-05 | 2.9e-05 | 6.0e-03 / 1.3e-02 | 165 → 165 | 166 | 8.1e+21 |
| random, specification | 0.33 | 2,160 | < 2e-05 | 2.9e-06 | 9.6e-03 / 1.7e-02 | 276 → 276 | 278 | 8.2e+22 |
| random, specification | 0.33 | 1,620 | < 1e-05 | 1.9e-04 | 1.4e-02 / 2.4e-02 | 276 → 276 | 280 | 1.3e+21 |
| random, specification | 0.33 | 1,080 | 5.0e-04 | 6.4e-03 | 2.1e-02 / 3.6e-02 | 276 → 277 | 292 | 1.8e+14 |
| worst, 10 s | 0.30 | 2,160 | < 2e-05 | 2.4e-11 | 2.6e-03 / 5.5e-03 | 892 → 892 | 895 | 7.9e+16 |
| worst, 10 s | 0.30 | 1,620 | < 1e-05 | 3.4e-08 | 3.1e-03 / 7.6e-03 | 892 → 892 | 897 | 1.2e+11 |
| worst, 10 s | 0.30 | 1,080 | 2.0e-05 | 1.7e-05 | 5.3e-03 / 1.1e-02 | 892 → 892 | 901 | 4.5e+05 |
| worst, 10 s | 0.33 | 2,160 | < 2e-05 | 1.6e-06 | 8.3e-03 / 1.6e-02 | 1,510 → 1,511 | 1,523 | 4.9e+07 |
| worst, 10 s | 0.33 | 1,620 | 2.0e-05 | 1.2e-04 | 1.3e-02 / 2.2e-02 | 1,510 → 1,512 | 1,530 | 7.8e+03 |
| worst, 10 s | 0.33 | 1,080 | 4.0e-04 | 4.8e-03 | 1.9e-02 / 3.3e-02 | 1,510 → 1,516 | 1,578 | none |

- **At `k = 2160` the walk bounds the branches at `1.6·10^-6` against a third** under the worst
  case, and none was seen in 50,000 windows; the depth with one evaluator is 1,511 sampled and 1,523
  at the bounds, 13 blocks above the unground 1,510, and `k = 2160` holds a third against up to
  `4.9·10^7` evaluators.
- **`k = 1620` holds a third against up to 7,800 evaluators,** at 1,530 blocks with one at the
  bounds, and `k = 1080` holds 30 % against up to 450,000, at 901. Both hold only while the inferred
  stake is the true stake (`FURTHER.md` G7).
- **At `k = 1080` against a third** a branch survives in 4 to 5 windows in 10,000, against the
  walk's bound of 5–6 in 1,000.

**The margin.** Under the chained binding the margin matters little, since a branch's values wait
`W` for the delay whatever the margin; the blind switch and the honest minima are what it shrinks.
The factor and the depth at `k = 2160` (20,000 windows a point):

| delay | α | not ground | margin 1 min | margin 2 min | margin 5 min | margin 10 min | margin 20 min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 165 | 1.0073, 165 | 1.0063, 165 | 1.0044, 165 | 1.0024, 165 | 1.0008, 165 |
| random, specification | 0.33 | 276 | 1.0210, 276 | 1.0193, 276 | 1.0150, 276 | 1.0100, 276 | 1.0044, 276 |
| worst, 10 s | 0.30 | 892 | 1.0063, 892 | 1.0057, 892 | 1.0042, 892 | 1.0022, 892 | 1.0010, 892 |
| worst, 10 s | 0.33 | 1,510 | 1.0183, 1,512 | 1.0171, 1,512 | 1.0137, 1,512 | 1.0096, 1,511 | 1.0044, 1,510 |

The honest cost, `R·T_a`, against the `4⌊k/f⌋` slots between the cut-off and the first slot that
uses the nonce, with B7's `m`:

| k | m | sub-window W | margin | T_a = W + margin | honest time, R = 3 | honest time, R = 5 | honest time, R = 10 | honest time, R = 15 | phase 4⌊k/f⌋ | largest R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2,160 | 25 | 4.32 h | 10 min | 4.49 h | 13.5 h | 22.4 h | 44.9 h | 67.3 h | 72 h | 16.0 |
| 2,160 | 25 | 4.32 h | 20 min | 4.65 h | 14.0 h | 23.3 h | 46.5 h | 69.8 h | 72 h | 15.5 |
| 1,620 | 26 | 3.12 h | 10 min | 3.28 h | 9.8 h | 16.4 h | 32.8 h | 49.2 h | 54 h | 16.5 |
| 1,620 | 26 | 3.12 h | 20 min | 3.45 h | 10.3 h | 17.2 h | 34.5 h | 51.7 h | 54 h | 15.7 |
| 1,080 | 26 | 2.08 h | 10 min | 2.24 h | 6.7 h | 11.2 h | 22.4 h | 33.6 h | 36 h | 16.0 |
| 1,080 | 26 | 2.08 h | 20 min | 2.41 h | 7.2 h | 12.1 h | 24.1 h | 36.1 h | 36 h | 14.9 |

- **The honest cost is about a day.** `T_a` is 4.5 hours at `k = 2160` and 2.2 at `k = 1080`;
  honest nodes compute 22 and 11 hours at a speed ratio of 5, 45 and 22 at 10, once an epoch. The
  phase's squarings alone hold a ratio of 15 to 16 at every `k`, since `W` and the phase both scale
  with `k`, and the prover's work comes on top. A larger `m` shortens `W` and the cost at the price
  of forks crossing more sub-window boundaries (B7's condition 3).

**A bound on `G_min` from the walk.** B7 samples `G_min`. Given the slots, the contributions are
independent uniforms, so their expectation has a closed form: with `N` canonical blocks in the last
sub-window, the deepest feasible fork dropping `D` of them and `A` coalition wins after its fork
point, the kept minimum changes at the `j`-th dropped block with chance `1/(N − j)` and a win lies
below the floor the deepest fork keeps with chance `1/(N − D + 1)`, so
`E[G_min | slots] = 1 + Σ_{j<D} 1/(N − j) + A/(N − D + 1)` while the fork stays in the sub-window
(`finality_sim.fork_bound`). B6's walk gives the law of `D` and `A` exactly: the walk falls by at
most one per block, so the deepest feasible fork sits where the lead equals `1 − Z`, the next gap
holds no win and the walk never rises again, and there `A = D + 1 − Z`. With at least `n_lo` blocks
in the sub-window the kept ones number at least `n_lo − D`; the forks deeper than `n_lo`, the
sub-windows with fewer than `n_lo` blocks and the forks that cross into the previous sub-window are
bounded apart. A fork crosses when the coalition's wins in the sub-window and its lead after the
cut-off leave an offset `o` at the boundary that the previous sub-window's walk lifts to one: every
fork with `o ≥ 1`, and a fork with `o ≤ 0` when the previous sub-window's wins complete it, which
the bound's first form left out. The crossing law matches the share of windows drawn slot by slot whose
deepest fork empties a short sub-window, exactly under random delay and from above under the worst
case, and the previous sub-window's blocks are split apart from the last one's. Per model, share
and `k`: B7's sampled mean; the mean of the expectation given the slots over 10,000 windows; the
bound at the splits that make it smallest, and its crossing term; `E[D]` and `E[A]`; and
the depth at `1e-9` with two nonces at the sampled mean and at the bound:

| delay | α | k | E[G_min], sampled | given the slots | bound | of which crossing | E[D] | E[A] | depth with two nonces, sampled → bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2,160 | 1.030 | 1.030 ± 0.000 | 1.040 | 0.000 | 4.5 | 4.2 | 165 → 165 |
| random, specification | 0.30 | 1,620 | 1.042 | 1.042 ± 0.001 | 1.061 | 0.000 | 4.5 | 4.2 | 165 → 166 |
| random, specification | 0.30 | 1,080 | 1.066 | 1.065 ± 0.001 | 1.100 | 0.000 | 4.5 | 4.2 | 166 → 166 |
| random, specification | 0.33 | 2,160 | 1.062 | 1.061 ± 0.001 | 1.081 | 0.000 | 8.4 | 7.8 | 277 → 278 |
| random, specification | 0.33 | 1,620 | 1.087 | 1.086 ± 0.001 | 1.128 | 0.002 | 8.4 | 7.8 | 278 → 279 |
| random, specification | 0.33 | 1,080 | 1.160 | 1.178 ± 0.026 | 1.736 | 0.465 | 8.4 | 7.8 | 280 → 291 |
| worst, 10 s | 0.30 | 2,160 | 1.030 | 1.029 ± 0.000 | 1.040 | 0.000 | 4.5 | 4.2 | 894 → 895 |
| worst, 10 s | 0.30 | 1,620 | 1.043 | 1.041 ± 0.001 | 1.059 | 0.000 | 4.5 | 4.2 | 895 → 897 |
| worst, 10 s | 0.30 | 1,080 | 1.067 | 1.065 ± 0.001 | 1.097 | 0.000 | 4.5 | 4.2 | 897 → 900 |
| worst, 10 s | 0.33 | 2,160 | 1.061 | 1.061 ± 0.001 | 1.079 | 0.000 | 8.3 | 7.8 | 1,518 → 1,521 |
| worst, 10 s | 0.33 | 1,620 | 1.088 | 1.087 ± 0.001 | 1.124 | 0.001 | 8.3 | 7.8 | 1,522 → 1,527 |
| worst, 10 s | 0.33 | 1,080 | 1.161 | 1.144 ± 0.005 | 1.553 | 0.308 | 8.3 | 7.8 | 1,532 → 1,575 |

- **The bound lies within four points of the sampled mean at `k ≥ 1620`:** 1.04 and 1.08 against
  30 % and a third at `k = 2160`, 1.06 and 1.12 at `k = 1620`, against means of 1.03, 1.06, 1.04
  and 1.09. At `k = 1080` a sub-window holds about 140 blocks, forks cross it more often, and the
  bound loosens to 1.10 against 30 % and 1.55–1.74 against a third, of which the crossing term is
  0.31–0.47: a coarse bound on a previous sub-window with few blocks, which the forks with `o ≤ 0`
  now carry.
- **The depths at the bound move by at most five blocks at the cells the routes claim:** 1,521
  against a third at `k = 2160` under the worst case, 1,527 at `k = 1620` and 900 against 30 % at
  `k = 1080`. The bound covers the honest minima of the lemma below; the blind switch and the
  evaluator term above come on top.

**The lemma, stated and proved.** In Praos's resettable model (§4.9) the adversary draws up to
`r − 1` further nonces from the beacon and sets the epoch's nonce to any of them. Here the beacon
is replaced by the delay: the adversary *forms* a candidate by fixing a pre-nonce `x_i`, which it
can do only once `x_i`'s inputs exist, and the candidate's value `η_i = H(delay(x_i))` reaches it at
`τ_i`, `T_a` after the candidate is formed. The honest default is the pre-nonce the honest chain
gives. A candidate is *reachable* at a time if some continuation of the execution makes it the
nonce. The adversary's choices for epoch `e` end at a time `D_e` after which only the candidate
that becomes the nonce, `S`, is reachable, the end of its lead; `D_e` is a stopping time of its
view. Let `A` be the set of candidates `i`, the default included, with `τ_i ≤ D_e` that are
reachable at `τ_i`. Model `H ∘ delay` as a random oracle and the delay as sequential: no party sees
`delay(x)` sooner than `T_a` after `x` is known to it.

*Claim.* For any event `B` of epoch `e` that is a function of the schedule, with `P(B) = ε` under
a uniformly random nonce, the adversary's choice gives `P(B) ≤ ε · E[|A| + 1{S ∉ A}]`.

*Proof.* `P(B) = Σ_i P(S = i, B_i)`, with `B_i` the event under candidate `i`'s value. Whether
`i ∈ A` is fixed by the history before `τ_i`, since `D_e` is a stopping time and reachability at
`τ_i` is a property of the execution up to `τ_i`; `η_i` is a fresh oracle output independent of that
history. For `i ∈ A`, `P(S = i, B_i) ≤ P(i ∈ A, B_i) = ε · P(i ∈ A)`, and these terms sum to
`ε · E[|A|]`. If `S = i ∉ A`, then `τ_i > D_e`, since the candidate that becomes the nonce is
reachable at every time and would be in `A` had its value arrived by `D_e`. The event `S = i` is
then fixed by the view at `D_e`, which does not hold `η_i`, so `P(S = i ∉ A, B_i) = ε · P(S = i ∉ A)`,
and these terms sum to `ε · P(S ∉ A)`. ∎

The factor per nonce is `E[|A| + 1{S ∉ A}]`. With no choice `A` is empty and the factor one. When
the adversary sees every candidate it can reach, as in Praos's resettable model, `S ∈ A` and the
factor is the number of reachable candidates, `G_min` at the cut-off. When it sees the default's
value while a candidate it never sees can still replace the default, it keeps the default or
switches blind, and `1{S ∉ A}` counts the switch. The bound is linear in the factor, as Praos's
union bound is linear in `r`: Theorem 11's term `exp(log r − Ω(k))` is `r·exp(−Ω(k))`, read with `r`
at the factor, and Corollary 3's `log tkq`, which counts every oracle query as a candidate, is
replaced by it. `ε` is the per-epoch failure of Theorems 7–9 at the lottery's thresholds. The
total-stake inference sets them from the same window, and a coalition that withholds for a period
raises them by `1/(1 − α)` (`FURTHER.md` G7), so `ε` is taken at the highest thresholds the
coalition can reach. The stake snapshot of epoch `ep − 2` is fixed before any candidate of epoch
`ep` exists, and the lifetime bound sums over epochs as Praos's Theorem 11 sums it.

Under the design above, `|A| + 1{S ∉ A}` is at most one, plus the honest minima the forks keep that
are seen while reachable, which are among `G_min`, plus one for a blind switch, plus the values of
the coalition's own branches seen while reachable, at most `E` in a window in which some branch
survives the delay's span. Their expectations are bounded by the walk's bound on `E[G_min]`, by the
open chance averaged over the default's arrival, and by `E` times the survival law, the bounds of
the tables above.

What a proof still needs beyond this: the sequentiality of squaring in the class group, an
assumption pinned below, and that `H ∘ delay` is a random oracle, which a hash of the delay's
output gives.

**The design.** The input is `hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, fixed at the cut-off; the output,
after `R·T_a` of sequential squarings in the class group of a prime discriminant derived from the
input, hashed, is the epoch's nonce `η_e`, with a Wesolowski proof. The new epoch's first slot
needs `η_e`, so a block of the phase carries the output and its proof, and every node verifies the
proof in place of the computation. Any node may compute it, and the honest leaders of the phase
have `4⌊k/f⌋` slots to compute and publish it, so the epoch starts late only if no honest node did,
a liveness failure of the honest set, not of the rule.

**The function and the speed ratio, from the sources** (read 2026-10-07; ePrint bodies through
the archive's snapshots of 2024-12-27 and 2025-01-03):

| source | what it pins |
| --- | --- |
| Wesolowski, "Efficient verifiable delay functions", ePrint 2018/623 (revised 2022-10-26) | "The output and the proof of correctness are each a single element of the group G"; verification "requires essentially two exponentiations in the group G, with exponents of bit-length 2k"; evaluation "requires t sequential squarings in the group" |
| Pietrzak, "Simple verifiable delay functions", ePrint 2018/627 (revised 2019-04-30) | the proof is `log T` elements, "about 10KB" at a 2048-bit modulus and `log T ≤ 40`; Wesolowski's "is just a single group element" |
| Boneh, Bünz, Fisch, "A survey of two verifiable delay functions", ePrint 2018/712 (revised 2020-01-05) | "shorter proofs (one group element versus log2 T elements) and proof verification is faster (two exponentiations versus 2 log2 T)"; Pietrzak's prover is `O(√T)` against Wesolowski's `O(T)`; "If Wesolowski's protocol is secure then so is Pietrzak's" |
| Chia, Proof of Time (docs.chia.net) | "repeated squaring in a class group of unknown order"; "The discriminant has a size of 1024 bits, which means the proof sizes are around 1024 bits" |
| Chia, VDF competition, round 1 (2019-01-17) and round 2 (2019-07-18) | the reference took 169 s for `2^21` squarings at 2048 bits on an i5-8400 (80.6 µs a squaring); the round-1 winner was 4.2 times faster, the round-2 winner "a 2x speedup over the reference implementation" |
| Chia, "We're going to ludicrous speed" (2023-10-26) and its timelord docs | the ASIC runs "between 800,000 iterations per second (IPS) and 1,000,000 IPS"; "The fastest non-ASIC Timelords currently running operate in the 260,000 IPS range"; the docs say "approximately four times the speed of the fastest non-ASIC timelords" |
| Zhu et al., ePrint 2022/755 (2022-06-13) | a 28 nm class-group ASIC design: "a speedup of 3.6x compared to the optimal C++ implementation for the VDF evaluation over an advanced CPU" |
| Drake, ethresear.ch (2018-07-16, 2018-09-26) | "the maximum attacker advantage", `A_max = 10`, measured against a commodity ASIC that honest nodes would also run, in RSA groups |
| Ethereum Foundation, statement on the MinRoot report (2023-09-18); Leurent et al., CRYPTO 2024 | "At present we do not recommend using VDFs within Ethereum"; the RSA ASIC was never reported built; the only chip built ran MinRoot |
| Analysis of MinRoot, EF workshop (2023-04-28 to 30) | "a speedup factor of 20 (ignoring communication latency) using 2^29 processors"; the attack breaks field-root VDFs (MinRoot, VeeDo, Sloth++) and leaves squaring in groups of unknown order untouched |
| CIP-0161, Ouroboros Phalanx (`cardano-foundation/CIPs` `20c819b`) | "Specialized hardware such as ASICs can be used to evaluate VDF output much faster, up to a factor of 5 in Chia's VDF project, while Ethereum considers a factor of 10"; "a 12-hour computation budget on standard CPU-based machines, which we estimate to be 10× slower than specialized ASICs"; no source is given for the 10 |
| Chia's old competition README (2018), CIP-0161 §5.2 (i9-14900HX) | a commodity CPU squares a 1024-bit class group element in about 4.7 µs (213,319 IPS) and a 2048-bit one in 9.5 µs; Chia's best timelord 3.85 µs |
| Wesolowski, ePrint 2018/623 (the archive's PDF of 2024-12-27, built 2020-07-24) | Assumption 1, the time-lock assumption: a cost `δ(k)` of one squaring such that "no algorithm A of polynomial cost wins the (δ, t)-time-lock game with non-negligible probability"; Assumption 2 generalises it to "arbitrary families of groups of unknown orders"; Example 2: "Choose a random, negative, square-free integer d, of large absolute value, and such that d ≡ 1 mod 4 … one should choose d to be a negative prime, which ensures that |Cl(d)| is odd"; "the best known algorithms for computing the order of the class group of an imaginary quadratic field of discriminant d are still of complexity L_|d|(1/2) under the generalised Riemann hypothesis" |
| Boneh, Bünz, Fisch, ePrint 2018/712 (revised 2020-01-05) | Definition 2, the adaptive root assumption: no efficient adversary that first "outputs an element w ∈ G" and then, for "a random prime ℓ in Primes(λ)", "outputs w^(1/ℓ) ∈ G"; Theorem 2: "Suppose the adaptive root assumption holds for GGen. Then Wesolowski's succinct argument" is sound; "The adaptive root assumption is necessary for soundness of the protocol" |
| Biasse, Jacobson, Silvester, ACISP 2010 (arXiv 1004.5512v1) | Table 4, "Security Parameter Estimates": the imaginary discriminant whose discrete logarithm costs what factoring each RSA modulus of NIST's levels costs, 798 bits for RSA-1024, 1,348 for RSA-2048, 1,827 for RSA-3072, in MIPS-years; the discrete logarithm is Vollmer's algorithm, timed in Table 2, 22,992.70 s at 256 bits; Table 1 puts the class group's computation at 1.33–1.61 times the discrete logarithm's at 140–220 bits; Section 5 converts seconds to MIPS-years assuming "the 2.4 GHz Intel Xeon machine runs at 4800 MIPS"; the estimates follow Hamdy and Möller and "provide a good rough guideline on the required discriminant sizes that is likely sufficiently accurate in the inexact science of predicting security levels" |
| Chia, `classgroups.pdf` (Long); Chia's Proof of Time page (read 2026-10-09) | "the order of the class group of a negative prime discriminant d, where |d| ≡ 3 mod 4, is believed to be difficult to compute when |d| is sufficiently large, making the order of the class group effectively unknown"; "use the challenge to generate a new random prime number for each VDF, which is used as the discriminant"; "The discriminant has a size of 1024 bits" |

What the sources settle:

- **The function is Wesolowski's over a class group of a 1024-bit discriminant,** as Chia runs it:
  no trusted setup, a proof of one group element, about 1,024 bits, and a verification of two
  exponentiations with 256-bit exponents, 600 to 800 group operations, 2–4 ms on a CPU at 3.85–4.7
  µs an operation. MinRoot and the other field-root candidates are broken; squaring in a group of
  unknown order is not.
- **The documented speed ratio is 3 to 5, not 10 or 20.** Chia's ASIC squares in about 1 µs
  against 3.85 µs on the fastest CPU timelord and 4.7 µs on a commodity CPU; Zhu et al. design at
  3.6×; the CIP's 10 is an assumption it attributes to Ethereum, whose `A_max = 10` measured an
  attacker against commodity ASICs, not CPUs. At the documented ratio honest nodes compute 13–22
  hours at `k = 2160` for a `T_a` of 4.5 hours; at the CIP's 10, 45 hours; the phase's squarings
  hold a ratio of 15 to 16.
- **The honest cost** at a ratio of 5 is `1.7·10^10` squarings of one CPU core once an epoch, 31 %
  of the lottery-constants phase at every `k`; the verification is one proof per epoch.
- **The group and its size.** The delay rests on Wesolowski's time-lock assumption in the class
  group and its proof on the adaptive-root assumption, both pinned above. The discriminant is a
  negative prime derived from each candidate's input, as Chia derives it from each challenge, so a
  candidate's class group exists only from the candidate's formation, the last sub-window's start
  at the earliest, and admits no precomputation; a prime discriminant leaves no element of order
  two. Its size sets what computing the class group costs. Biasse, Jacobson and Silvester's Table 4
  is the discrete logarithm's cost by Vollmer's algorithm, and their Table 1 puts the class group's
  computation at 1.33–1.61 times it. Their Section 5 reads the cost at any size from Table 2's
  256-bit anchor through `L_|d|[1/2, 1]`; Table 4's discriminants come out of that method only with
  the anchor's seconds converted at 4.8 MIPS, a thousandth of the 4,800 the paper states
  (`finality_sim.discriminant`, `scripts/i2_discriminant.py`). Both readings, with the years at
  `10^18` operations a second and the operations a second that finish within the delay of 4.49
  hours given for Table 4's rows / for the class group at the stated conversion:

| discriminant | RSA modulus of Table 4 | discrete log, Table 4's rows | discrete log, stated method | class group, stated method | years at 10^18 a second | operations a second within 4.49 h |
| --- | --- | --- | --- | --- | --- | --- |
| 798 bits | 1,024 bits | 2^78.2 | 2^88.2 | 2^88.6–2^88.9 | 0.0109 / 18 | 2.1e+19 / 3.5e+22 |
| 1,024 bits | – | 2^91.4 | 2^101.4 | 2^101.8–2^102.1 | 103 / 1.7e+05 | 2.0e+23 / 3.3e+26 |
| 1,348 bits | 2,048 bits | 2^108.3 | 2^118.2 | 2^118.7–2^118.9 | 1.22e+07 / 2.02e+10 | 2.4e+28 / 3.9e+31 |
| 1,827 bits | 3,072 bits | 2^130.1 | 2^140.1 | 2^140.6–2^140.8 | 4.75e+13 / 7.83e+16 | 9.3e+34 / 1.5e+38 |
| 2,048 bits | – | 2^139.4 | 2^149.4 | 2^149.8–2^150.0 | 2.83e+16 / 4.67e+19 | 5.5e+37 / 9.1e+40 |

  A 1024-bit discriminant, Chia's size, costs `2^91.4` operations for the discrete logarithm by
  Table 4's rows, between NIST's 80- and 112-bit levels, and `2^101.4` by the stated method, with the
  class group at `2^101.8`–`2^102.1`. The threat is a class group computed while a candidate's delay
  runs, since one computed after the nonce is public buys nothing: two hundred thousand machines of
  `10^18` operations a second by the rows, three hundred million by the stated method. A class group
  computed in time evaluates every candidate's delay at once, so the coalition sees every value the
  binding gives at the cut-off, one per chain prefix, and its decisions before the cut-off are no
  longer blind; it still reaches no nonce today's hash chain does not, since every candidate is a
  fork and a subset of its wins (B6). 2048 bits give `2^139.4` by the rows and `2^149.4` by the
  stated method. A 2048-bit squaring takes about twice as long as a 1024-bit one (9.5 µs against
  4.7 on CIP-0161's CPU), so the count that fills `T_a` halves and the honest hours stay, if the
  speed ratio is the same at 2048 bits, which no source measures; the proof doubles to 2,048 bits.

H9 fails as stated: 100 honest minutes blind nothing, since the coalition forms the last
sub-window's candidates from the sub-window's start. It holds for a delay that spans the
sub-window, with the contribution bound to the parent's contribution: against a third under the
worst case at `k = 2160` a margin of ten minutes leaves a factor of 1.009 sampled, and at most the
walk's bound of 1.08 plus a blind switch of 0.016 plus `1.6·10^-6` per delay evaluator, so the
depth is 1,511 sampled and 1,523 at the bounds against a ratio of 15 to 16, the most the phase's
squarings hold; verification takes 2–4 ms rather than under one. With the contribution bound to
the parent block, as first stated, the factor under the delay is the same, but every branch that
survives the delay's span brings as many body variants as the coalition computes.


## H.3 — the time-reading rule under a worst case of `Δ`

B4's rule is derived under random delay. Under a worst case of `Δ` the coalition also delays
honest blocks and runs the two-chain attack of B3, and B2's proven depth reads no time.

Every rule below reads `t`, the client's clock when it evaluates, less the slot of the target's
parent. A block the coalition releases late carries a slot earlier than that clock, and the
coalition's wins in between count. The client keeps the chain it holds on a tie, as Cryptarchia's
Online rule keeps the first-seen chain (`SETTLEMENT.md` B3), so a competing chain must be strictly
longer.

**The counting bound.** Every block is a distinct lottery win. Above the target's parent the
competing chain holds at most the coalition's wins `A(t)`, each of which may also sit on the
canonical chain since a win signs on any branch, and the honest wins `H(t)` the canonical chain
does not hold. With `n` canonical blocks counting the target it leads by at most `2A + H − 2n`,
plus the stationary lead of the worst-case walk before the parent, geometric with the catch-up
ratio `(a + h − h_w)/h_w`, where `h_w = 1/(Δ + 1/p_h)` is the canonical chain's worst-case growth.
The target falls if the lead reaches one at acceptance or by a later catch-up
(`finality_sim.further.counting_logp`). The bound reads `(n, t)` and nothing about who delayed
what. Its depth at `1e-9` when the client holds the `n`-th block at the mean spacing of three
chains, at `Δ = 10` s, with the mean of `2A + H` over `2n` at the two slower rates:

| α | catch-up ratio | depth at 1e-9, full rate | depth at 1e-9, withheld from | depth at 1e-9, worst-case rate | mean of 2A + H over 2n, withheld from | at the worst-case rate |
| --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 0.45 | 131 (1.3 h) | 216 (2.3 h) | 453 (5.4 h) | 0.71 | 0.80 |
| 0.25 | 0.67 | 310 (3.0 h) | – | – | 0.98 | 1.05 |
| 0.30 | 0.77 | 434 (4.2 h) | – | – | 1.09 | 1.15 |
| 0.33 | 0.84 | 574 (5.6 h) | – | – | 1.17 | 1.23 |

- **The bound bites only on a fast chain.** At the rate of a chain the coalition withholds from,
  the mean of `2A + H` is 1.95 `n` against a quarter: below `2n`, but so close that no depth below
  5,000 blocks holds `1e-9`. Against 30 % and a third, and at the worst-case rate from a quarter up,
  it exceeds `2n`. At the full rate, `g·λ`, the bound holds at 574 blocks against a third, where
  B2's depth is 1,510. A client under the worst case can read time, and it gains only while the
  chain runs at the full rate. The depth rule caps it.

**The attack against the rules.** B3's delay-scheduling attack (Gaži, Ren and Russell §4.7 on the
slot lottery, `finality_sim.grr_attack.attack_rule`) against time-reading rules at `Δ = 10` s and
`ε = 1e-3`, 8 runs of `2·10^7` slots a point. A rule accepts the `k`-th block of the client's chain
when it arrives within its deadline for `k`. The attack wins at acceptance when its second chain is
at or above the client's, or at any later symbol:

| α | rule | B2's attack depth at 1e-3 | targets | accepted | mean depth at acceptance | attack wins at acceptance | ever | at acceptance, per target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | depth | 44 | 4,108,096 | 1.000 | 45.0 | 1.1e-03 | 1.2e-03 | 1.1e-03 |
| 0.25 | b4 at worst rates | 44 | 4,108,096 | 0.053 | 54.4 | 5.1e-01 | 5.3e-01 | 2.7e-02 |
| 0.25 | b4 at worst rates, adjusted | 44 | 4,108,096 | 0.003 | 27.4 | 9.3e-01 | 9.4e-01 | 3.1e-03 |
| 0.25 | counting | 44 | 4,108,096 | 0.000 | 0.0 | 0 | 0 | 0 |
| 0.30 | depth | 82 | 4,179,322 | 1.000 | 83.0 | 1.1e-03 | 1.2e-03 | 1.1e-03 |
| 0.30 | b4 at worst rates | 82 | 4,179,322 | 0.043 | 75.9 | 5.4e-01 | 5.6e-01 | 2.3e-02 |
| 0.30 | b4 at worst rates, adjusted | 82 | 4,179,322 | 0.000 | 50.5 | 1.0e+00 | 1.0e+00 | 9.1e-05 |
| 0.30 | counting | 82 | 4,179,322 | 0.000 | 0.0 | 0 | 0 | 0 |
| 0.33 | depth | 139 | 4,227,181 | 1.000 | 140.0 | 8.2e-04 | 9.2e-04 | 8.2e-04 |
| 0.33 | b4 at worst rates | 139 | 4,227,181 | 0.038 | 102.2 | 5.8e-01 | 6.0e-01 | 2.2e-02 |
| 0.33 | b4 at worst rates, adjusted | 139 | 4,227,181 | 0.000 | 0.0 | 0 | 0 | 0 |
| 0.33 | counting | 139 | 4,227,181 | 0.000 | 0.0 | 0 | 0 | 0 |

The counting rule at `ε = 1e-3` played on 32 independent-slot timelines of 200,000 slots whose
canonical chain runs at the full rate while the coalition wins at its slot occupancy, the client
holding each block `Δ` after its slot, scored by the premined private race; beside it the wins B5's
closed form expects over the accepted targets at the timelines' share of the wins:

| α | targets accepted | mean depth at acceptance | minutes | the race beats the rule | wins B5's closed form expects |
| --- | --- | --- | --- | --- | --- |
| 0.25 | 170,754 | 92.5 | 54 | 0 | 1.3e-01 |
| 0.30 | 170,350 | 136.5 | 79 | 0 | 1.5e-02 |
| 0.33 | 165,498 | 192.8 | 112 | 0 | 3.5e-04 |

- **B4's rule is beaten in 51–58 % of the targets it accepts.** At worst-case rates it accepts
  3.8–5.3 % of the targets within the attack's horizon, and the attack's second chain is level with
  the client's at 51–58 % of those acceptances: 2.2–2.7e-2 per target, more than twenty times `ε`.
  With the adjusted rates it accepts fewer and loses almost all of them. The rule reads the chain's
  speed, and under a scheduled delay the coalition sets the speed: it holds honest blocks back and
  releases them when its second chain has caught up, so that the client sees a burst and accepts at
  the moment the attack is ready. H10 fails for B4's rule under the worst case; the rule stays a
  random-delay rule.
- **The depth rule at B2's attack depth loses at `1e-3`,** as B3 found: 8.2e-4 to 1.1e-3 at
  acceptance, which is the lower bound's depth read at the lower bound's chance.
- **The counting rule never accepts under the attack** within its horizon, since the attack keeps
  the client's chain slow. On fast timelines it accepts at a mean depth of 92.5 / 136.5 / 192.8
  blocks against a quarter / 30 % / a third at `1e-3`, and the race beats it on none of about
  170,000 targets a share. At those depths B5's closed form expects fewer than 0.2 wins in all, so
  the plays show where the rule accepts, not that it is sound.

**The observed counting rule.** The counting bound counts every honest win the canonical chain
does not hold as a block the competing chain may hold, `H − n_h`, and must take `H` at its mean. A
client can count them instead. An honest block sits on one chain, and one that descends from the
target sits on no chain without it. A chain holds one block per slot. So the honest blocks a
competing chain holds above the parent sit at distinct slots among the **forks** the client has
received: the blocks with a slot after the target's parent's that do not descend from the target,
counted once a slot, once the honest blocks of the last `Δ` slots, `H_late`, have arrived. A
received block whose ancestry the client cannot yet resolve counts as a fork. The competing chain
holds at most `L + A(t) + forks + H_late` blocks above the parent against the canonical `n`, and
the target falls if `L + A + H_late ≥ n + 1 − forks` at acceptance or by the catch-up
(`finality_sim.further.counting_observed_logp`, `finality_sim.forks`). A coalition that publishes a
win as a fork raises the count by one, however many blocks it signs with that win, and keeps the
win for its competing chain, so the bound stays sound and the rule accepts later. One win signed
on two branches carries the same entropy contribution twice; the specification has no rule that
reads such a pair. The rule's depth at `1e-9`, `Δ = 10` s, with no forks and the `n`-th block at
the mean spacing of each chain, beside B2's depth with its hours on the clock of a chain the
coalition withholds from, and B5's closed form at the random-delay growth:

| α | B2, worst case | B5, random delay | full rate | withheld from | withheld from, at 5e-10 | withheld from, ties to the coalition | worst-case rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 114 (1.2 h) | 19 | 34 | 35 (0.4 h) | 36 | 37 | 36 (0.4 h) |
| 0.25 | 474 (6.1 h) | 88 | 91 | 112 (1.4 h) | 116 | 114 | 120 (1.7 h) |
| 0.30 | 892 (12.4 h) | 165 | 148 | 209 (2.9 h) | 215 | 211 | 226 (3.3 h) |
| 0.33 | 1,510 (22.0 h) | 276 | 235 | 374 (5.4 h) | 386 | 377 | 408 (6.2 h) |

- **Under a worst-case delay the rule settles at 408 blocks against a third, 6.2 hours, and at
  226 against 30 %, 3.3 hours,** where B2 needs 1,510 and 892: the client's chain then grows at the
  worst-case rate. On a chain the coalition withholds from but does not delay it settles at 374 and
  209 blocks, 5.4 and 2.9 hours, against B2's 22.0 and 12.4 hours on that clock. The gain is about
  four-fold at every share.
- **Ties to the coalition add two or three blocks; reading the rule at `ε/2` adds four to twelve
  from a quarter to a third.** A client that settles at the earlier of this rule and the depth rule
  is displaced with chance up to the sum of theirs, so it reads each at `ε/2`.

**What the rule's law is worth.** The bound takes the lead before the parent and the catch-up
after acceptance as geometric at the counting ratio, the ratio of the mean gains. Under a worst
case of `Δ` both follow the worst-case renewal walk (`finality_sim.adaptive`). The canonical chain
gains one block per cycle of a geometric wait for an honest win and `Δ` slots more. The competing
chain gains the coalition's wins of the cycle, the honest wins of its last `Δ` slots, and the block
of a second honest leader of the slot that ends the wait, at most, with the stake spread over many
holders. No schedule within `Δ` grows the canonical chain slower or the competing chain faster. The
walk has the rule's mean gain, but its tail falls faster. Each cell gives the rule's law / the walk
/ the walk with a second leader:

| α | mean gain a block, the rule's law / the walk / with a second leader | tail factor a block | P(L ≥ 100) | depth at 1e-9, the client's ties | ties to the coalition |
| --- | --- | --- | --- | --- | --- |
| 0.25 | 0.672 / 0.672 / 0.684 | 0.672 / 0.542 / 0.555 | 5.2e-18 / 1.7e-27 / 1.8e-26 | 112 / 80 / 83 | 114 / 82 / 85 |
| 0.30 | 0.767 / 0.767 / 0.779 | 0.767 / 0.674 / 0.687 | 3.1e-12 / 5.6e-18 / 4.0e-17 | 209 / 152 / 158 | 211 / 155 / 160 |
| 0.33 | 0.839 / 0.839 / 0.850 | 0.839 / 0.773 / 0.787 | 2.3e-08 / 5.9e-12 / 3.4e-11 | 374 / 274 / 290 | 377 / 277 / 293 |

- **The counting ratio is the mean, not the decay.** Against a third the walk's lead falls by
  0.773 a block, 0.787 with a second leader, where the rule's law falls by 0.839: at 100 blocks
  the walk's tail is 5.9e-12 against the rule's 2.3e-8. Read with the walk's own law, the rule would
  settle a withheld-from chain against a third at 274 blocks, 290 with a second leader, about B5's
  random-delay 276. The rule keeps the geometric law. The slack is what holds it against a
  coalition that times the acceptance, below.

**Per target, not per view.** `p(n, t, forks)` charges the coalition's wins `A(t)` as Poisson,
independent of what the client sees. Under the worst case the coalition signs a win on the
client's chain as well as on its own, delays honest blocks and publishes forks, and so chooses when
the client's count reaches the threshold. So `p` is not the risk given the client's view. A play
that signs every win on both chains while delaying honest blocks shows it
(`finality_sim.adaptive.view_risk`). Its competing chain then holds the coalition's blocks alone,
and a view at acceptance that consists mostly of them fails more often than `ε`:

| α | ε | likeliest view above ε | fails given the view | the rule's bound there | the view's chance | of chance 1e-12 or more, the view that fails most often | all views above ε | most honest blocks in one | the play per target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 1e-03 | 26 blocks in 349 slots, 19 of them the coalition's | 1.1e-03 | 8.5e-04 | 3e-10 | 26 in 335, 20 the coalition's: 2.8e-03 against 8.1e-04 | 2e-09 | 7 | 8e-09 |
| 0.25 | 1e-09 | 70 blocks in 1,047 slots, 49 of them the coalition's | 1.8e-09 | 9.0e-10 | 3e-21 | none | 1e-20 | 21 | 2e-22 |
| 0.30 | 1e-03 | 40 blocks in 527 slots, 30 of them the coalition's | 1.3e-03 | 9.2e-04 | 7e-14 | none | 4e-13 | 10 | 1e-09 |
| 0.30 | 1e-09 | 108 blocks in 1,580 slots, 78 of them the coalition's | 1.2e-09 | 8.4e-10 | 2e-29 | none | 2e-28 | 30 | 7e-25 |
| 0.33 | 1e-03 | 61 blocks in 767 slots, 47 of them the coalition's | 1.0e-03 | 9.3e-04 | 2e-20 | none | 2e-19 | 14 | 3e-11 |
| 0.33 | 1e-09 | 161 blocks in 2,136 slots, 122 of them the coalition's | 1.5e-09 | 9.9e-10 | 1e-46 | none | 3e-46 | 39 | 3e-29 |

The guarantee is per target: the chance that the rule accepts the target and the target later
falls, with the acceptance a stopping time of the coalition's choosing. Backward induction over the
coalition's play gives it under the rule's law and under the worst-case walk, as a multiple of `ε`,
each play conditioned on the lead `L`, which the coalition knows (`finality_sim.adaptive`):

- *every win private:* the rule's own case, accepted when the honest part alone reaches the
  threshold;
- *induction:* each win kept private or signed on both chains as it falls, the honest part of the
  client's chain growing at the worst-case rate;
- *free timing:* the acceptance placed at any slot between the full-rate and the worst-case paths'
  arrival at the threshold;
- *upper bound:* the acceptance at any slot the coalition chooses, the client's chain growing no
  slower than the walk's canonical chain, a forced acceptance postponed by a published fork at the
  cost of one block. It bounds every play that keeps the competing chain private until acceptance.

| α | ε | law | every win private | induction | free timing | upper bound |
| --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 1e-03 | the rule's | 0.88 ε | 0.97 ε | 1.08 ε | 1.14 ε |
| 0.25 | 1e-03 | the worst-case walk | 0.047 ε | 0.051 ε | 0.058 ε | 0.059 ε |
| 0.25 | 1e-09 | the rule's | 0.90 ε | 1.01 ε | 1.08 ε | 1.16 ε |
| 0.25 | 1e-09 | the worst-case walk | 0.00048 ε | 0.0005 ε | 0.00054 ε | 0.0006 ε |
| 0.30 | 1e-03 | the rule's | 0.98 ε | 1.07 ε | 1.10 ε | 1.15 ε |
| 0.30 | 1e-03 | the worst-case walk | 0.072 ε | 0.076 ε | 0.079 ε | 0.08 ε |
| 0.30 | 1e-09 | the rule's | 0.87 ε | 1.06 ε | 1.09 ε | 1.15 ε |
| 0.30 | 1e-09 | the worst-case walk | 0.00091 ε | 0.00099 ε | 0.0011 ε | 0.0011 ε |
| 0.33 | 1e-03 | the rule's | 0.94 ε | 1.05 ε | 1.10 ε | 1.13 ε |
| 0.33 | 1e-03 | the worst-case walk | 0.084 ε | 0.092 ε | 0.099 ε | 0.10 ε |
| 0.33 | 1e-09 | the rule's | 0.92 ε | 1.06 ε | 1.08 ε | 1.13 ε |
| 0.33 | 1e-09 | the worst-case walk | 0.0016 ε | 0.0017 ε | 0.0018 ε | 0.0018 ε |

- **The rule holds `ε` per target by computation, with the worst-case walk's law.** The upper bound
  is 0.10 ε against a third at `1e-3` and 0.0018 ε at `1e-9`, and at most 0.10 ε in any cell.
- **The rule's own law does not carry it.** Under the geometric law the induction already reaches
  1.06 ε against a third at `1e-9`, free timing 1.08 ε, and the upper bound 1.13 ε: a coalition
  that times the acceptance would beat the rule if the lead and the catch-up were geometric. Under a
  schedule within `Δ` they follow the walk, whose faster tail pays for the timing many times over.
  A rule read with the walk's law would need that argument of its own.
- **What the computation does not cover.** A coalition that shows its chain to honest nodes, so
  that their blocks join it, publishes its own wins on it as forks the client counts. None of the
  plays above covers that.

**The delay-scheduling attack against the observed rule.** B3's attack played against the observed
rule at `ε = 1e-3` (`finality_sim.grr_attack.attack_observed`), the forks counted three ways: every
honest block since the target that is off the client's chain, which counts at least what the client
counts; only those on the attack's competing chain, at most what it counts; none:

| α | forks counted | targets | accepted | attack wins at acceptance, per target | per accepted target | mean depth at acceptance | mean forks at acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | every honest block off the client's chain | 4,108,096 | 0 | 0 | – | – | – |
| 0.25 | those on the competing chain | 4,108,096 | 0 | 0 | – | – | – |
| 0.25 | none | 4,108,096 | 26,276 | 6.4e-04 | 9.9e-02 | 169.0 | 0.0 |
| 0.30 | every honest block off the client's chain | 4,179,322 | 0 | 0 | – | – | – |
| 0.30 | those on the competing chain | 4,179,322 | 5 | 1.2e-06 | 1.0e+00 | 81.6 | 2.8 |
| 0.30 | none | 4,179,322 | 11,583 | 4.0e-04 | 1.4e-01 | 204.6 | 0.0 |
| 0.33 | every honest block off the client's chain | 4,227,181 | 0 | 0 | – | – | – |
| 0.33 | those on the competing chain | 4,227,181 | 0 | 0 | – | – | – |
| 0.33 | none | 4,227,181 | 3,558 | 1.1e-04 | 1.3e-01 | 256.8 | 0.0 |

- **The forks carry the rule's safety under the attack.** Counted in full they keep the rule from
  accepting any target, at every share. Counted only on the competing chain they let it accept five
  targets at 30 %, every one lost: 1.2e-6 per target, below `ε`, but all of its acceptances.
  Ignored, they let the rule accept 0.08–0.64 % of the targets and lose 10–14 % of those, 1.1e-4 to
  6.4e-4 per target.

**Forks.** The rule's depth at `1e-9` with forks, and against coalitions that add them:

| α | no forks, withheld from | two forks | four forks | a balancing coalition, its honest forks | with its own blocks | a coalition publishing every win as a fork |
| --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 35 | 38 | 40 | 58 | 84 | 42 |
| 0.25 | 112 | 116 | 120 | 245 | – | 437 |
| 0.30 | 209 | 213 | 218 | 549 | – | – |
| 0.33 | 374 | 380 | 386 | 1,246 | – | – |

- **A coalition that balances the honest chain at the worst-case rate stalls the rule** from a
  quarter up, once its own blocks on the balanced chain are counted: they are forks too. With the
  honest forks alone the rule needs 1,246 blocks against a third, B2's depth. The depth rule caps
  both.
- **A coalition that publishes every win as a fork stalls the rule at 30 % and a third, and leaves
  437 blocks at a quarter.** The count then grows at the coalition's rate against a canonical chain
  that grows at the honest rate. Counting slots holds this however many blocks the coalition signs
  with a win. A count of blocks would stall at a quarter with two blocks a win, and at 10 % with
  ten:

| α | blocks signed a win | depth at 1e-9, forks counted as blocks | as slots |
| --- | --- | --- | --- |
| 0.10 | 1 | 42 | 42 |
| 0.10 | 2 | 51 | 42 |
| 0.10 | 3 | 69 | 42 |
| 0.10 | 5 | 188 | 42 |
| 0.10 | 10 | – | 42 |
| 0.25 | 1 | 437 | 437 |
| 0.25 | 2 | – | 437 |
| 0.25 | 3 | – | 437 |
| 0.25 | 5 | – | 437 |
| 0.25 | 10 | – | 437 |

The forks a client counts, measured on G6's engine timelines of the specification's Blend with
honest relays, the coalition withholding, 64 runs a share, every public block counted however late
it arrives; with how late a fork reaches the client, an honest node, and the accepted targets of
the play below for which a counted fork had not yet reached it:

| α | targets | none | two or more | mean | 90th percentile | 99th percentile | most | a fork reaches the client, slots after its slot: 99th percentile | latest | accepted with a fork still in flight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 106,292 | 0.709 | 0.044 | 0.340 | 1 | 2 | 5 | 10.1 | 10.4 | 0 |
| 0.30 | 99,880 | 0.725 | 0.039 | 0.318 | 1 | 2 | 4 | 10.1 | 10.5 | 0 |
| 0.33 | 95,588 | 0.739 | 0.035 | 0.299 | 1 | 2 | 4 | 10.1 | 10.3 | 0 |

The rule at `ε = 1e-3` played on those timelines with each target's measured forks and the client's
arrival times, and on the independent-slot timelines above with none, scored by the premined
private race:

| α | timelines | targets | accepted | mean depth at acceptance | minutes | the race beats the rule | wins B5's closed form expects |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | engine | 80,628 | 1.000 | 41.7 | 32 | 0 | 2.0e+00 |
| 0.25 | full rate, no forks | 170,754 | 1.000 | 33.8 | 20 | 0 | 1.4e-01 |
| 0.30 | engine | 74,216 | 1.000 | 77.0 | 63 | 0 | 2.6e+00 |
| 0.30 | full rate, no forks | 170,593 | 1.000 | 55.7 | 33 | 0 | 1.5e-02 |
| 0.33 | engine | 69,924 | 1.000 | 137.1 | 117 | 0 | 9.4e-01 |
| 0.33 | full rate, no forks | 170,007 | 1.000 | 89.1 | 52 | 0 | 2.4e-04 |

- **Honest forks cost a few blocks.** Three targets in four see none, 4.4 % and 3.5 % see two or
  more against a quarter and a third, and each fork costs two blocks of depth against a quarter and
  30 %, three against a third. A fork reaches the client within 10.5 slots of its slot, so the
  engine's network exceeds `Δ = 10` by up to half a slot. No target was accepted with a counted fork
  still on its way.
- **The plays show where the rule accepts, not that it is sound.** The race beats it on none of
  70,000 targets a share, where B5's closed form expects 0.9 to 2.6 wins a share on the engine's
  timelines and fewer than 0.15 on the fast ones.

H10 holds per target by computation for the observed counting rule. With the worst-case walk's law
for the lead before the parent and the catch-up after acceptance, a coalition that keeps its chain
private until acceptance and times the acceptance as it likes fails at most 0.10 ε per target at
`1e-3` and 0.0018 ε at `1e-9`. The rule accepts a chain under a worst-case delay at 408 blocks
against a third, 6.2 hours, where B2 needs 1,510, and a chain the coalition only withholds from at
374, 5.4 hours. A coalition that balances the honest chain, or one that publishes every win as a
fork from 30 % up, stalls it, and the depth rule caps it. The rule does not hold `ε` given the
client's view, and its own geometric law would not hold it against a coalition that times the
acceptance. A time-conditioned form of B2's bound, the port's recursion read at `(n, t)` rather than
at `n`, is not derived here.

## Counted in slots (Phase K)

With `k` counted in slots (`SLOTS.md` K.0), the three designs move little.

- **H.1's seats do not move.** They separate shares of the stake, not blocks. The round's trigger,
  two chains that both exceed `k` blocks since their divergence, becomes two chains whose
  divergence is older than `K`. Both chains reach that age at the same slot, so every node that
  holds both enters the same round. The detector reads a side at the thresholds set before the
  split, which the epoch times, not `K`. `SLOTS.md` K.3 reads a floor that makes finality itself
  wait on a sparse chain.
- **H.2 does not move.** The delay spans the last sub-window and a margin, and the honest nodes
  compute it within the `4⌊k/f⌋` slots before the nonce is first used. Both are in slots and keep
  their lengths with the epoch (`SLOTS.md` K.4).
- **H.3's rules already read time.** The observed counting rule reads `(n, t)`, and a wait is the
  rule that reads `t` alone: K.1 bounds it from B2 and the honest chain's growth over the wait, and
  K.7 in GRR's own model, 10.1 hours against a third at 10 s. A bound read at `(n, t)` is still not
  derived.
