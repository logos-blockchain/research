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

G1 passes B7's nonce through a sequential delay. The coalition decides blind wherever the delay on
its hardware, `T_a`, outlasts its decision window; honest nodes pay `R·T_a` for a speed ratio `R`.

**The decision window before the cut-off.** A block of the coalition's own, or a race against an
honest block, must be placed before the canonical chain moves on. Placed `d` canonical blocks late
it competes from `d` behind and becomes canonical with chance `r^d`, `r = p_a/p_c`:

| delay | α | 1 behind | 2 behind | 3 behind | 5 behind | 8 behind | 11 behind |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 0.51 (0.8 min) | 0.26 (1.7 min) | 0.13 (2.5 min) | 0.035 (4.2 min) | 0.0046 (6.7 min) | 0.00061 (9.2 min) |
| random, specification | 0.33 | 0.59 (0.9 min) | 0.35 (1.8 min) | 0.21 (2.6 min) | 0.074 (4.4 min) | 0.016 (7.1 min) | 0.0033 (9.7 min) |
| worst, 10 s | 0.30 | 0.53 (0.9 min) | 0.28 (1.8 min) | 0.15 (2.6 min) | 0.043 (4.4 min) | 0.0065 (7.0 min) | 0.00098 (9.7 min) |
| worst, 10 s | 0.33 | 0.62 (0.9 min) | 0.38 (1.8 min) | 0.23 (2.7 min) | 0.088 (4.6 min) | 0.021 (7.3 min) | 0.0048 (10.0 min) |

**What a delay leaves.** At the cut-off, the choices in the epochs whose lead outlasts `T_a` (G1's
factor). Before the cut-off, B7's hindsight factor scaled by the chance that a decision can still
be acted on after the canonical blocks `T_a` holds, `r^d`. Each cell gives the cut-off factor, the
residual before the cut-off, their product and the depth at `1e-9` with two nonces, at `k = 2160`:

| delay | α | not ground | T_a = 1 min | T_a = 2 min | T_a = 3 min | T_a = 5 min | T_a = 10 min | T_a = 20 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 165 | 1.019 × 2.34 = 2.38, 180 | 1.013 × 1.60 = 1.62, 173 | 1.013 × 1.27 = 1.29, 169 | 1.008 × 1.05 = 1.06, 166 | 1.001 × 1.00 = 1.00, 165 | 1.000 × 1.00 = 1.00, 165 |
| random, specification | 0.33 | 276 | 1.040 × 4.27 = 4.44, 318 | 1.042 × 2.81 = 2.93, 307 | 1.030 × 2.01 = 2.07, 296 | 1.021 × 1.31 = 1.34, 284 | 1.010 × 1.02 = 1.03, 276 | 1.001 × 1.00 = 1.00, 276 |
| worst, 10 s | 0.30 | 892 | 1.020 × 4.98 = 5.08, 1,034 | 1.012 × 2.94 = 2.98, 987 | 1.012 × 1.95 = 1.97, 951 | 1.008 × 1.23 = 1.23, 910 | 1.001 × 1.01 = 1.01, 892 | 1.000 × 1.00 = 1.00, 892 |
| worst, 10 s | 0.33 | 1,510 | 1.042 × 10.42 = 10.86, 1,863 | 1.042 × 6.53 = 6.81, 1,794 | 1.028 × 4.25 = 4.37, 1,728 | 1.019 × 2.12 = 2.16, 1,624 | 1.008 × 1.08 = 1.09, 1,522 | 1.001 × 1.00 = 1.00, 1,510 |

- **Ten minutes on the coalition's hardware leaves a factor of about 1.1,** five minutes about
  2.2 under the worst case against a third, and one minute most of B7's estimate. The requirement
  is `T_a ≥ 10` minutes.
- **The honest cost is `R·T_a`.** The share of the `4⌊k/f⌋` slots between the cut-off and the first
  slot that uses the nonce, at `k = 2160` / `k = 1080`:

| T_a | R = 2 | R = 5 | R = 10 | R = 30 | R = 100 |
| --- | --- | --- | --- | --- | --- |
| 1 min | 2 min (0.0 % / 0.1 %) | 5 min (0.1 % / 0.2 %) | 10 min (0.2 % / 0.5 %) | 30 min (0.7 % / 1.4 %) | 100 min (2.3 % / 4.6 %) |
| 2 min | 4 min (0.1 % / 0.2 %) | 10 min (0.2 % / 0.5 %) | 20 min (0.5 % / 0.9 %) | 60 min (1.4 % / 2.8 %) | 200 min (4.6 % / 9.3 %) |
| 3 min | 6 min (0.1 % / 0.3 %) | 15 min (0.3 % / 0.7 %) | 30 min (0.7 % / 1.4 %) | 90 min (2.1 % / 4.2 %) | 300 min (6.9 % / 13.9 %) |
| 5 min | 10 min (0.2 % / 0.5 %) | 25 min (0.6 % / 1.2 %) | 50 min (1.2 % / 2.3 %) | 150 min (3.5 % / 6.9 %) | 500 min (11.6 % / 23.1 %) |
| 10 min | 20 min (0.5 % / 0.9 %) | 50 min (1.2 % / 2.3 %) | 100 min (2.3 % / 4.6 %) | 300 min (6.9 % / 13.9 %) | 1,000 min (23.1 % / 46.3 %) |
| 20 min | 40 min (0.9 % / 1.9 %) | 100 min (2.3 % / 4.6 %) | 200 min (4.6 % / 9.3 %) | 600 min (13.9 % / 27.8 %) | 2,000 min (46.3 % / 92.6 %) |

- **A hundred honest minutes buys `R = 10`,** two hundred `R = 20`. Either stays inside the phase
  at `k ≥ 1080`. Which `R` the coalition can reach is what the sources below settle.

**The design.** The input is `hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, fixed at the cut-off; the output,
after `R·T_a` of sequential squarings in a class group of an imaginary quadratic field, is the
epoch's nonce `η_e`, with a Wesolowski proof. Any node may compute it; the first block of the new
epoch carries the output and its proof, and every node verifies the proof in place of the
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

What the sources settle:

- **The function is Wesolowski's over a class group of a 1024-bit discriminant,** as Chia runs it:
  no trusted setup, a proof of one group element, about 1,024 bits, and a verification of two
  exponentiations with 256-bit exponents, about a millisecond on a CPU at 4.7 µs a squaring.
  MinRoot and the other field-root candidates are broken; squaring in a group of unknown order is
  not.
- **The documented speed ratio is 3 to 5, not 10 or 20.** Chia's ASIC squares in about 1 µs
  against 3.85 µs on the fastest CPU timelord and 4.7 µs on a commodity CPU; Zhu et al. design at
  3.6×; the CIP's 10 is an assumption it attributes to Ethereum, whose `A_max = 10` measured an
  attacker against commodity ASICs, not CPUs. With 100 honest minutes the coalition at the
  documented ratio has `T_a` of 20 to 30 minutes, which leaves a factor per nonce of 1.00–1.01;
  at the CIP's 10, ten minutes and 1.09; a ratio of 20, which no source documents, would leave five
  minutes and 2.2.
- **The honest cost** of 100 minutes is `1.3·10^9` squarings of one CPU core once an epoch, 2.3 %
  of the lottery-constants phase at `k = 2160` and 4.6 % at `k = 1080`; the verification is one
  proof per epoch.

H9 holds against the documented hardware and the CIP's assumption, with verification in
milliseconds rather than under one; it would fail only against a coalition twenty times faster
than a commodity CPU, which no source documents, and 200 honest minutes would cover even that.


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

A time-conditioned form of B2's bound, the port's recursion read at `(n, t)` rather than at `n`,
is not derived here; the counting bound shows what such a rule can gain, and only on a chain at
the full rate.
