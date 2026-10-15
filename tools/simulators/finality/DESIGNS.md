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
`1e-6`; also with a tenth of the honest votes undelivered
(`finality_sim.further.attestation_seats`):

| α | honest side | seats, every honest vote counts | seats, 10% of honest votes lost |
| --- | --- | --- | --- |
| 0.20 | 0.400 | 832 (θ = 250) | 1,224 (θ = 345) |
| 0.25 | 0.375 | 2,277 (θ = 719) | 4,401 (θ = 1,306) |
| 0.30 | 0.350 | 14,993 (θ = 4,907) | 157,893 (θ = 48,680) |
| 0.32 | 0.340 | 95,248 (θ = 31,533) | none |
| 0.33 | 0.335 | 1,537,024 (θ = 511,496) | none |

- **A round of 2,300 seats separates a quarter; 15,000 separate 30 % if every honest vote
  counts,** 158,000 if a tenth are lost. At 32 % the round needs 95,000 seats with every vote
  counted and none suffices with a tenth lost; at a third none at all. H8's figure of 10,000
  seats fails at 30 %; a one-off round of 15,000 is a burst of votes once per incident, not D0's
  cover multiple per round.
- **The coalition's moves.** Its seats go where it likes: to its fork, which the threshold
  discards; or to one honest side, which then wins over the other, a choice between two honest
  histories that any resolution of a partition gives it. Votes withheld lower its fork's count.
  Votes cast before the sides are fully reconnected miss the round, which is why the round starts
  only when a node holds both chains.
- **What the round costs once.** `n` votes through Blend within the round's window, each a lottery
  win carried as D1 carries a vote; D5's leakage applies to the one sample.

**Anchoring, placed.** A checkpoint written to another chain timestamps a block. It does not show
that the block was public: the coalition anchors the blocks of its private fork as any node
anchors the public chain's, and an anchor carrying a proof of leadership is stake-weighted and
meets the symmetry above. What an anchor settles is a fork older than the anchor, which is the
long-range fork of B5's horizon `H`, and the start of a bootstrapping node. Which mechanism
resolves which split:

| the split | resolved by |
| --- | --- |
| an eclipse: one side is the whole honest chain | B5's trigger, rules 1–8 |
| a partition deeper than `k`, below a third | recovery attestations |
| a partition deeper than `k`, at a third | nothing local; operators |
| a fork from bought keys older than `H` | an anchor, or `H` itself |
| a node starting from genesis | a checkpoint |

**Partition detection.** Rule 8's test as a detector: a node compares its canonical count over
the window with the count the honest stake `1 − α` makes alone, and declares its chain sparse
below the `1e-9` lower tail of that count (`finality_sim.further.detector_power`, the
specification's Blend under random delay). While the detector fires the node reports `B_imm` as
provisional and refuses the recovery comparison. The chance that a side holding a share of all
stake is declared sparse; the whole honest stake, 0.70 against 30 %, gives the false-alarm rate:

| α | window | expected, honest alone | threshold | side 0.350 | side 0.500 | side 0.600 | side 0.650 | side 0.700 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 36 h | 2,600 | 2,274 | 1.0000 | 1.0000 | 0.926 | 0.0087 | 9e-10 |
| 0.30 | 72 h | 5,200 | 4,719 | 1.0000 | 1.0000 | 1.0000 | 0.202 | 1e-09 |
| 0.33 | 36 h | 2,476 | 2,160 | 1.0000 | 1.0000 | 0.159 | 8e-07 | 2e-17 |
| 0.33 | 72 h | 4,952 | 4,487 | 1.0000 | 1.0000 | 0.871 | 1e-05 | 3e-21 |

- **Every side of an even partition is detected,** and any side holding up to about 0.6 of all
  stake with a 36-hour window against 30 %. A side of 0.65 passes as full in 99 % of windows,
  which is a partition that took 7 % of the stake away: the trigger's window then compares a
  0.65 side against a 0.30 fork and holds.

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
factor per nonce is the expected number of candidates evaluated before the last choice that can
still select them, and a proof needs that number bounded.

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
adversary can afford" (§4.9). The nonce is `η_j = H(η_{j−1} ‖ j ‖ v)` over the VRF values of the
blocks of epoch `j − 1` "up to the slot with timestamp up to (j* − 2)R + 16k/f" (Fig. 10), and
"the stakeholder distribution is determined in each epoch j ≥ 2 by the block that has time stamp
up to (j − 2)R" (proof of Theorem 11), so the stake is fixed before the nonce's inputs. Genesis
keeps the nonce rule, "a hash of additional VRF-values y_ρ that were included … into blocks from
the first two thirds of epoch ep − 1", with the stake "recorded in the ledger up to the last block
of epoch ep − 2" (§3). Its Theorem 1 states Praos's bounds for `maxvalid-mc` with a term `ε_lift`
that carries `Q`, "an upper bound on the total number of queries issued to G_RO", and its
Theorem 2 adds for `maxvalid-bg` only "an additional error probability exp(ln L − Ω(k)) +
ε_CG(βf/16, k/(4f)) + ε_∃CQ(k/(4f)) + ε_CP(kβ/64)" when "k > 192∆/(εβ) and R/6 ≥ s = k/(4f) ≥
48∆/(βf)" (§4.3). Of grinding it says: "the process of deriving it described above still allows
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
if the adversary has seen its output when it last chooses, so `r` is the number of evaluated
candidates, `E[G_min]` under the delay of this section, and the bound is Theorem 11's with
`log r` read at it. Cryptarchia's Online rule is `maxvalid-mc` within `k` and its Bootstrap rule
`maxvalid-bg` (`MAPPING.md`), so Theorem 1 covers the first and Theorem 2 the second; the nonce
enters both through the leader schedule alone, and the stake of epoch `ep − 2` is fixed before
any candidate exists, as the lemma requires. What the papers bound with `Q` and the rule with
`E[G_min]` is the same quantity.

A candidate of the last sub-window needs `μ_1 … μ_(m−1)`, fixed when the sub-window starts, and a
value for `μ_m`: an honest contribution once its block is received, or one of the coalition's
own, which it knows in advance for every slot, since `ρ_LEAD` depends on the slot, the note and
the key. Candidates therefore exist from the start of the last sub-window, `W = ⌊6⌊k/f⌋/m⌋`
slots before the cut-off, 4.3 hours at `k = 2160`, and the coalition evaluates them hours before
it withholds a block of its own or removes an honest one. G1 took a candidate to be formed when
the coalition must act, within minutes of the choice. That was wrong: a delay of ten minutes
blinds only the choices formed in the last ten minutes of the sub-window, and leaves B7's
estimate. Two changes make the delay work:

- **The contribution is bound to the parent block,** `ρ_LEAD := hash(NONCE_CONTRIB_V1 ‖ parent ‖
  sl ‖ noteID ‖ sk)`, so that a contribution exists only when its block is built on a known
  parent. The coalition then forms no candidate before the last sub-window starts and cannot
  predict a sub-window's minimum ahead, which replaces B7's conditions 1 and 2, the binding to the
  epoch nonce and the notes frozen one epoch earlier; `m` is then set by B7's condition 3 and by
  the honest cost below. A coalition still chooses the parent among the blocks it may extend, which
  gives it as many contributions per win as it has parents in reach, and that only raises `G_min`.
- **The delay spans the sub-window:** `T_a = W + margin`. Every candidate is formed at or after
  the sub-window's start, so its output arrives at or after the cut-off plus the margin, and the
  choice is still open only while the coalition's lead outlasts the margin. Candidates of a fork
  that reaches into the previous sub-window are formed earlier and count in full; they are within
  `E[G_min]`, which the walk bounds below: 278 and 1,521 against a third at `k = 2160`.

What the margin leaves of the choices at the cut-off (G1's factor, `finality_sim.further.delayed_factor`,
20,000 windows a point), and the depth at `1e-9` with two nonces, at `k = 2160`:

| delay | α | not ground | margin 1 min | margin 2 min | margin 3 min | margin 5 min | margin 10 min | margin 20 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 165 | 1.019, 165 | 1.013, 165 | 1.013, 165 | 1.008, 165 | 1.001, 165 | 1.000, 165 |
| random, specification | 0.33 | 276 | 1.040, 277 | 1.042, 277 | 1.030, 277 | 1.021, 276 | 1.010, 276 | 1.001, 276 |
| worst, 10 s | 0.30 | 892 | 1.020, 893 | 1.012, 893 | 1.012, 893 | 1.008, 892 | 1.001, 892 | 1.000, 892 |
| worst, 10 s | 0.33 | 1,510 | 1.042, 1,516 | 1.042, 1,516 | 1.028, 1,514 | 1.019, 1,512 | 1.008, 1,511 | 1.001, 1,510 |

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

- **A margin of ten minutes leaves a factor of 1.00–1.01 from the choices formed in the last
  sub-window,** and `E[G_min]`, at most 1.04–1.08 at `k = 2160`, bounds the rest: the depth is the
  unground one within eleven blocks.
- **The honest cost is about a day.** `T_a` is 4.5 hours at `k = 2160` and 2.2 at `k = 1080`;
  honest nodes compute 22 and 11 hours at a speed ratio of 5, 45 and 22 at 10, once an epoch, and
  the phase holds a ratio up to 16 at every `k`, since `W` and the phase both scale with `k`. A
  larger `m` shortens `W` and the cost at the price of forks crossing more sub-window boundaries
  (B7's condition 3).

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
bounded apart, the last through the coalition's wins in the sub-window, which must reach the blocks
it empties. Per model, share and `k`: B7's sampled mean; the mean of the expectation given the
slots over 10,000 windows; the bound at the `n_lo` that makes it smallest; `E[D]` and `E[A]`; and
the depth at `1e-9` with two nonces at the sampled mean and at the bound:

| delay | α | k | E[G_min], sampled | given the slots | bound | E[D] | E[A] | depth with two nonces, sampled → bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2,160 | 1.030 | 1.030 ± 0.000 | 1.040 | 4.5 | 4.2 | 165 → 165 |
| random, specification | 0.30 | 1,620 | 1.042 | 1.042 ± 0.001 | 1.061 | 4.5 | 4.2 | 165 → 166 |
| random, specification | 0.30 | 1,080 | 1.066 | 1.065 ± 0.001 | 1.100 | 4.5 | 4.2 | 166 → 166 |
| random, specification | 0.33 | 2,160 | 1.062 | 1.061 ± 0.001 | 1.081 | 8.4 | 7.8 | 277 → 278 |
| random, specification | 0.33 | 1,620 | 1.087 | 1.086 ± 0.001 | 1.127 | 8.4 | 7.8 | 278 → 279 |
| random, specification | 0.33 | 1,080 | 1.160 | 1.178 ± 0.026 | 1.462 | 8.4 | 7.8 | 280 → 287 |
| worst, 10 s | 0.30 | 2,160 | 1.030 | 1.029 ± 0.000 | 1.040 | 4.5 | 4.2 | 894 → 895 |
| worst, 10 s | 0.30 | 1,620 | 1.043 | 1.041 ± 0.001 | 1.059 | 4.5 | 4.2 | 895 → 897 |
| worst, 10 s | 0.30 | 1,080 | 1.067 | 1.065 ± 0.001 | 1.097 | 4.5 | 4.2 | 897 → 900 |
| worst, 10 s | 0.33 | 2,160 | 1.061 | 1.061 ± 0.001 | 1.079 | 8.3 | 7.8 | 1,518 → 1,521 |
| worst, 10 s | 0.33 | 1,620 | 1.088 | 1.087 ± 0.001 | 1.123 | 8.3 | 7.8 | 1,522 → 1,527 |
| worst, 10 s | 0.33 | 1,080 | 1.161 | 1.144 ± 0.005 | 1.363 | 8.3 | 7.8 | 1,532 → 1,556 |

- **The bound lies within four points of the sampled mean at `k ≥ 1620`:** 1.04 and 1.08 against
  30 % and a third at `k = 2160`, 1.06 and 1.12 at `k = 1620`, against means of 1.03, 1.06, 1.04
  and 1.09. At `k = 1080` a sub-window holds about 140 blocks, forks cross it more often, and the
  bound loosens to 1.10 against 30 % and 1.36–1.46 against a third.
- **The depths move by at most five blocks at the cells the routes claim:** 1,521 against a third
  at `k = 2160` under the worst case, 1,527 at `k = 1620`, which holds a third, and 900 against
  30 % at `k = 1080`, which holds 30 %. Within B6's model the choices at the cut-off are bounded,
  not estimated.

**The lemma, stated and proved.** In Praos's resettable model (§4.9) the adversary draws up to
`r − 1` further nonces from the beacon and sets the epoch's nonce to any of them. Here the beacon
is replaced by the delay: the adversary *forms* a candidate by fixing a pre-nonce `x_i`, which it
can do only once `x_i`'s inputs exist, and the candidate's value `η_i = H(delay(x_i))` reaches it
`T_a` later. Let the honest default be candidate 0, the pre-nonce the honest chain gives. The
adversary's last choice for epoch `e` is made at a time `D_e` after which no candidate of epoch `e`
can still become the nonce, the end of its lead; let `r_eval` be the number of candidates
`i ≥ 1` whose values it has seen by `D_e`. Model `H ∘ delay` as a random oracle and the delay as
sequential: no party sees `delay(x)` sooner than `T_a` after `x` is known to it.

*Claim.* For any event `B` of epoch `e` that is a function of the schedule, with `P(B) = ε` under
a uniformly random nonce, the adversary's choice gives `P(B) ≤ ε · E[1 + r_eval]`.

*Proof.* The nonce is some candidate `S ∈ {0, 1, …}`, and `P(B) = Σ_i P(S = i, B_i)`, with `B_i`
the event under candidate `i`'s value. Split the candidates at `D_e` into the seen, whose values
the adversary's view holds, and the unseen. For a seen `i`, `P(S = i, B_i) ≤ P(B_i) = ε`, since
`η_i` is a fresh oracle output and `B_i` depends on nothing else the adversary chose, so the seen
contribute at most `ε · E[r_eval]` by the union bound over a random count. For an unseen `i`,
including the default when the adversary has seen nothing, `η_i` is independent of the view at
`D_e`, hence of the event `{S = i}`, so `P(S = i, B_i) = P(S = i) · ε`, and the unseen contribute at
most `ε · P(S unseen) ≤ ε`. Summing gives the claim. ∎

The claim is Praos's union bound with `r` read as `1 + r_eval` rather than as every candidate
drawn: Theorem 11 holds with `log r` read at `log E[1 + r_eval]`, by the concavity of the
logarithm, and Corollary 3's `log tkq`, which counts every oracle query as a candidate, is
replaced by it. `E[1 + r_eval] ≤ E[G_min]` under the design above, since a candidate's value
arrives at or after the cut-off plus the margin and the lead must last it: 1.08 against a third
at `k = 2160`. The stake snapshot of epoch `ep − 2` is fixed before any candidate of epoch `ep`
exists, so `ε` is the per-epoch failure of Theorems 7–9 at the honest schedule, and the lifetime
bound sums over epochs as Praos's Theorem 11 sums it.

What a proof still needs beyond this: the sequentiality of squaring in the class group, an
assumption pinned below, and that `H ∘ delay` is a random oracle, which a hash of the delay's
output gives.

**The design.** The input is `hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, fixed at the cut-off; the output,
after `R·T_a` of sequential squarings in the class group of a prime discriminant derived from the
input, hashed, is the epoch's nonce `η_e`, with a Wesolowski proof. Any node may compute it; the first block of the
new epoch carries the output and its proof, and every node verifies the proof in place of the
computation. A block of the new epoch without a verified nonce is invalid. If no block carries it
by the epoch's start, the honest leaders of the phase have had `4⌊k/f⌋` slots to compute it, so the
epoch starts late only if no honest node computed it, which is a liveness failure of the honest
set, not of the rule.

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
| Biasse, Jacobson, Silvester, ACISP 2010 (arXiv 1004.5512v1) | Table 4, "Security Parameter Estimates": the imaginary discriminant that matches each RSA modulus of NIST's levels, 798 bits for RSA-1024, 1,348 for RSA-2048, 1,827 for RSA-3072, in MIPS-years; the estimates follow Hamdy and Möller and "provide a good rough guideline on the required discriminant sizes that is likely sufficiently accurate in the inexact science of predicting security levels" |
| Chia, `classgroups.pdf` (Long); Chia's Proof of Time page (read 2026-10-09) | "the order of the class group of a negative prime discriminant d, where |d| ≡ 3 mod 4, is believed to be difficult to compute when |d| is sufficiently large, making the order of the class group effectively unknown"; "use the challenge to generate a new random prime number for each VDF, which is used as the discriminant"; "The discriminant has a size of 1024 bits" |

What the sources settle:

- **The function is Wesolowski's over a class group of a 1024-bit discriminant,** as Chia runs it:
  no trusted setup, a proof of one group element, about 1,024 bits, and a verification of two
  exponentiations with 256-bit exponents, about a millisecond on a CPU at 4.7 µs a squaring.
  MinRoot and the other field-root candidates are broken; squaring in a group of unknown order is
  not.
- **The documented speed ratio is 3 to 5, not 10 or 20.** Chia's ASIC squares in about 1 µs
  against 3.85 µs on the fastest CPU timelord and 4.7 µs on a commodity CPU; Zhu et al. design at
  3.6×; the CIP's 10 is an assumption it attributes to Ethereum, whose `A_max = 10` measured an
  attacker against commodity ASICs, not CPUs. At the documented ratio honest nodes compute 13–22
  hours at `k = 2160` for a `T_a` of 4.5 hours; at the CIP's 10, 45 hours; the phase holds a ratio
  of 16.
- **The honest cost** at a ratio of 5 is `1.7·10^10` squarings of one CPU core once an epoch, 31 %
  of the lottery-constants phase at every `k`; the verification is one proof per epoch.
- **The group and its size.** The delay rests on Wesolowski's time-lock assumption in the class
  group and its proof on the adaptive-root assumption, both pinned above. The discriminant is a
  negative prime derived from the input, as Chia derives it from each challenge, so its class
  group exists only from the cut-off and admits no precomputation; a prime discriminant leaves no
  element of order two. Its size sets what computing the class number costs. Biasse, Jacobson and
  Silvester's Table 4, read through `L_|d|[1/2, 1]`, which fits its three rows to within 0.06 bits
  (`finality_sim.discriminant`, `scripts/i2_discriminant.py`):

| discriminant | RSA modulus of Table 4 | class number, log2 operations | years at 10^18 a second | years at 10^21 a second | operations a second within 4.49 h |
| --- | --- | --- | --- | --- | --- |
| 798 bits | 1,024 bits | 78 | 0.0109 | 1.09e-05 | 2.1e+19 |
| 1,024 bits | – | 91 | 103 | 0.103 | 2.0e+23 |
| 1,348 bits | 2,048 bits | 108 | 1.22e+07 | 1.22e+04 | 2.4e+28 |
| 1,827 bits | 3,072 bits | 130 | 4.75e+13 | 4.75e+10 | 9.3e+34 |
| 2,048 bits | – | 139 | 2.83e+16 | 2.83e+13 | 5.5e+37 |

  A 1024-bit discriminant, Chia's size, costs about `2^91` operations, between NIST's 80- and
  112-bit levels: a century for a machine of `10^18` operations a second, and two hundred thousand
  of them to finish within the delay, which is the threat here, since a class number computed
  after the epoch's nonce is public buys nothing. A class number computed in time evaluates the
  delay at once and returns B7's estimate, nothing worse than today's nonce. 2048 bits give
  `2^139`, NIST's 128-bit level and beyond, at no cost in time: a squaring takes twice as long, so
  the count that fills `T_a` halves, and the honest hours, the ratio and the margin are unchanged;
  the proof doubles to 2,048 bits.

H9 fails as stated: 100 honest minutes blind nothing, since the coalition forms the last
sub-window's candidates from the sub-window's start. It holds for a delay that spans the
sub-window, with the contribution bound to the parent block: a margin of ten minutes leaves a
factor of 1.00–1.01 from the sub-window's candidates and at most 1.08 from forks across its start,
a bound from B6's walk, against any ratio up to 16, with verification in milliseconds rather than
under one.


## H.3 — the time-reading rule under a worst case of `Δ`

B4's rule is derived under random delay. Under a worst case of `Δ` the coalition also delays
honest blocks and runs the two-chain attack of B3, and B2's proven depth reads no time.

**The counting bound.** Every block is a distinct lottery win. Above the target's parent the
competing chain holds at most the coalition's wins `A(t)`, each of which may also sit on the
canonical chain since a win signs on any branch, and the honest wins `H(t)` the canonical chain
does not hold. With `n` canonical blocks counting the target it leads by at most `2A + H − 2n`,
plus the stationary lead of the worst-case walk before the parent, geometric with the catch-up
ratio `(a + h − h_w)/h_w`, where `h_w = 1/(Δ + 1/p_h)` is the canonical chain's worst-case growth.
The target falls if the lead reaches one at acceptance or by a later catch-up
(`finality_sim.further.counting_logp`). The bound holds for every strategy within `Δ`: it reads
`(n, t)` and nothing about who delayed what. Its depth at `1e-9` when the `n`-th block arrives at
the mean spacing of three chains, at `Δ = 10` s:

| α | catch-up ratio | depth at 1e-9, full rate | depth at 1e-9, withheld from | depth at 1e-9, worst-case rate |
| --- | --- | --- | --- | --- |
| 0.10 | 0.45 | 131 (1.3 h) | 216 (2.3 h) | 453 (5.4 h) |
| 0.25 | 0.67 | 310 (3.0 h) | – | – |
| 0.30 | 0.77 | 434 (4.2 h) | – | – |
| 0.33 | 0.84 | 574 (5.6 h) | – | – |

- **The bound is empty on a slow chain and bites on a fast one.** At the worst-case rate and at
  the rate of a chain the coalition withholds from, the mean of `2A + H` over `t = n/rate` exceeds
  `2n`, and no depth holds. At the full rate, `g·λ`, it holds at 574 blocks against a
  third, where B2's depth is 1,510: a client under the worst case can read time, and it gains only
  while the chain runs at the full rate. The depth rule caps it.

**The attack against the rules.** B3's delay-scheduling attack (Gaži, Ren and Russell §4.7 on the
slot lottery, `finality_sim.grr_attack.attack_rule`) against time-reading rules at `Δ = 10` s and
`ε = 1e-3`, 8 runs of `2·10^7` slots a point. A rule accepts the `k`-th block of the client's chain
when it arrives within its deadline for `k`; the attack wins at acceptance when its second chain is
at or above the client's, or at any later symbol:

| α | rule | B2's attack depth at 1e-3 | targets | accepted | mean depth at acceptance | attack wins at acceptance | ever |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | depth | 44 | 4,108,096 | 1.000 | 45.0 | 1.1e-03 | 1.2e-03 |
| 0.25 | b4 at worst rates | 44 | 4,108,096 | 0.053 | 54.4 | 5.1e-01 | 5.3e-01 |
| 0.25 | b4 at worst rates, adjusted | 44 | 4,108,096 | 0.003 | 27.4 | 9.3e-01 | 9.4e-01 |
| 0.25 | counting | 44 | 4,108,096 | 0.000 | 0.0 | 0 | 0 |
| 0.30 | depth | 82 | 4,179,322 | 1.000 | 83.0 | 1.1e-03 | 1.2e-03 |
| 0.30 | b4 at worst rates | 82 | 4,179,322 | 0.043 | 75.9 | 5.4e-01 | 5.6e-01 |
| 0.30 | b4 at worst rates, adjusted | 82 | 4,179,322 | 0.000 | 50.5 | 1.0e+00 | 1.0e+00 |
| 0.30 | counting | 82 | 4,179,322 | 0.000 | 0.0 | 0 | 0 |
| 0.33 | depth | 139 | 4,227,181 | 1.000 | 140.0 | 8.2e-04 | 9.2e-04 |
| 0.33 | b4 at worst rates | 139 | 4,227,181 | 0.038 | 102.2 | 5.8e-01 | 6.0e-01 |
| 0.33 | b4 at worst rates, adjusted | 139 | 4,227,181 | 0.000 | 0.0 | 0 | 0 |
| 0.33 | counting | 139 | 4,227,181 | 0.000 | 0.0 | 0 | 0 |

The counting rule at `ε = 1e-3` played on 32 independent-slot timelines of 200,000 slots whose
canonical chain runs at the full rate while the coalition wins at its slot occupancy, scored by the
premined private race:

| α | targets accepted | mean depth at acceptance | minutes | the race beats the rule |
| --- | --- | --- | --- | --- |
| 0.25 | 170,754 | 90.9 | 53 | 0 |
| 0.30 | 170,366 | 134.9 | 78 | 0 |
| 0.33 | 165,650 | 191.2 | 111 | 0 |

- **B4's rule is beaten whenever it accepts.** At worst-case rates it accepts 4–5 % of the targets
  within the attack's horizon, and the attack's second chain is level with the client's at 51–58 %
  of those acceptances; with the adjusted rates it accepts fewer and loses almost all of them. The
  rule reads the chain's speed, and under a scheduled delay the coalition sets the speed: it holds
  honest blocks back and releases them when its second chain has caught up, so that the client sees
  a burst and accepts at the moment the attack is ready. H10 fails for B4's rule under the worst
  case; the rule stays a random-delay rule.
- **The depth rule at B2's attack depth loses at `1e-3`,** as B3 found: 8.2e-4 to 1.1e-3 at
  acceptance, which is the lower bound's depth read at the lower bound's chance.
- **The counting rule never accepts under the attack** within its horizon, since the attack keeps
  the client's chain slow, and so is never beaten there; on fast timelines it accepts at 91 / 135 /
  191 blocks against a quarter / 30 % / a third at `1e-3`, and the race beats it on none of about
  170,000 targets a share, as a bound must. Its gain is confined to a chain at the full rate: 574
  blocks against a third at `1e-9` where B2 needs 1,510, and nothing at the rate of a chain the
  coalition withholds from or delays.

**The observed counting rule.** The counting bound counts every honest win the canonical chain
does not hold as a block the competing chain may hold, `H − n_h`, and must take `H` at its mean.
A client can count them instead. An honest block sits on one chain, and one that descends from the
target sits on no chain without it. So the honest blocks a competing chain holds above the parent
are among the **forks** the client has received, the blocks with a slot after the target's parent's
that do not descend from the target, once the honest blocks of the last `Δ` slots, `H_late`, have
arrived. The competing chain holds at most `L + A(t) + forks + H_late` blocks above the parent
against the canonical `n`, and the target falls if `L + A + H_late ≥ n + 1 − forks` at acceptance
or by the catch-up (`finality_sim.further.counting_observed_logp`). A coalition that publishes a
win as a fork at the parent raises the count by one and keeps the win for its competing chain, so
the bound stays sound and the rule accepts later. A block a coalition publishes twice, with one
leadership on two branches, carries the same entropy contribution twice; the specification has no
rule that reads such a pair. The rule's depth at `1e-9`, `Δ = 10` s, with the `n`-th block at the
mean spacing of each chain, beside B2's depth and B5's closed form at the random-delay growth:

| α | B2, worst case | B5, random delay | no forks, full rate | no forks, withheld from | two forks, withheld from | four forks, withheld from | a balancing coalition, worst-case rate | a coalition publishing every win as a fork |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.10 | 114 | 19 | 34 | 35 (0.4 h) | 38 | 40 | 58 | 42 |
| 0.25 | 474 | 88 | 91 | 112 (1.4 h) | 116 | 120 | 245 | 437 |
| 0.30 | 892 | 165 | 148 | 209 (2.9 h) | 213 | 218 | 549 | – |
| 0.33 | 1,510 | 276 | 235 | 374 (5.4 h) | 380 | 386 | 1,246 | – |

The forks a client counts, measured on G6's engine timelines of the specification's Blend with
honest relays, the coalition withholding, 64 runs a share, every public block counted however late
it arrives:

| α | targets | none | mean | 90th percentile | 99th percentile | most |
| --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 106,292 | 0.709 | 0.344 | 1 | 2 | 5 |
| 0.30 | 99,880 | 0.725 | 0.322 | 1 | 2 | 4 |
| 0.33 | 95,588 | 0.739 | 0.302 | 1 | 2 | 6 |

The rule at `ε = 1e-3` played on those timelines with each target's measured forks, and on the
independent-slot timelines above with none, scored by the premined private race:

| α | timelines | targets | accepted | mean depth at acceptance | minutes | the race beats the rule |
| --- | --- | --- | --- | --- | --- | --- |
| 0.25 | engine | 80,628 | 1.000 | 41.5 | 32 | 0 |
| 0.25 | full rate, no forks | 170,754 | 1.000 | 33.6 | 20 | 0 |
| 0.30 | engine | 74,216 | 1.000 | 76.8 | 63 | 0 |
| 0.30 | full rate, no forks | 170,593 | 1.000 | 55.5 | 32 | 0 |
| 0.33 | engine | 69,924 | 1.000 | 136.8 | 117 | 0 |
| 0.33 | full rate, no forks | 170,007 | 1.000 | 88.9 | 52 | 0 |

- **A client that counts the forks it sees settles under the worst case at 374 blocks against a
  third** when the coalition withholds and the chain runs at the honest rate, where B2's depth is
  1,510 and the counting bound holds nothing: 5.4 hours on the honest chain's clock against 23.0.
  Below a third the gain is the same four-fold, 209 against 892 and 112 against 474. The depth
  stays above B5's random-delay closed form, 276, because the lead before the parent and the
  catch-up after acceptance keep the worst case's ratio, 0.84 against a third.
- **Honest forks cost a few blocks.** Three targets in four see none, one in a hundred sees two
  or more, and each fork costs about three blocks of depth. Played at `1e-3` the rule accepts every target
  at a mean depth of 137 against a third, B2's attack depth at `1e-3` being 139, and the race beats
  it on none of 70,000 targets a share.
- **A coalition that balances the honest chain at the worst-case rate returns the rule to B2's
  depth,** 1,246 against 1,510, since the forks it keeps alive are the honest wins the bound
  counts: the rule reads the attack it is under.
- **A coalition that publishes every win as a fork stalls the rule at 30 % and a third,** since
  the count then grows at twice the coalition's rate against a canonical chain that grows at the
  honest rate, and at a quarter it leaves 437 blocks. The forks cost the coalition its rewards and
  nothing else, and they are visible: an honest network produces a third of a fork per block. The
  depth rule is the cap, as before, and the client settles at the earlier of the two.

H10 holds in this form: a rule that reads `(n, t)` and the forks accepts a chain the coalition
withholds from at a quarter of B2's depth and a chain it balances at B2's depth, sound for every
strategy within `Δ`. A time-conditioned form of B2's bound, the port's recursion read at `(n, t)`
rather than at `n`, is not derived here.
