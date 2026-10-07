# Further routes

Phase G of `PLAN.md`: ways to shorten finality that the three routes of the report do not cover,
read against 30 % and a third of the stake at `ε = 1e-9`. Tables come from `runs/` through
`scripts/tables.py`; runs from `scripts/g1_delayed_nonce.py`, `scripts/g3_blend_delay.py`,
`scripts/g4_density.py` and `scripts/g6_relays.py`. G2 and G5 need no run.

## G1 — the smallest contributions with a delayed nonce

B7's factor is dominated by the decisions a coalition takes before the cut-off: to publish or
withhold a block of its own, and to remove an honest block that holds a sub-window's minimum. Each
decision is worth something only if the coalition can compute the nonce each outcome gives before
it must act. If the nonce is `η_e = delay(hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m))`, with `delay` a sequential
function of `T` minutes on the coalition's hardware, every decision whose window is shorter than
`T` is taken blind, and a blind choice gains nothing: the chance against a nonce chosen blind among
`G` is the average over the `G`, which is `u`.

The decision windows:

- **Before the cut-off**, a block of the coalition's own must be published before the honest
  chain grows a few blocks past it, or it needs a fork the honest chain has outrun; an honest block
  must be removed within `Δ` under the worst case, or raced from its parent before the chain grows
  past it. Both windows are a few block intervals, minutes.
- **At the cut-off**, the coalition knows which forks are feasible and must publish one before the
  lead `Z` of its private chain is spent. A lead of `z` lasts about `z/(p_c − p_a)` slots. The
  chance that it lasts at least a given time (`finality_sim.further.lead_lasts`, B6's `Z`):

| delay | α | 1 min | 2 min | 5 min | 10 min | 20 min | 30 min | 60 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.25 | 0.4 | 0.16 | 0.024 | 6e-04 | 3e-07 | 2e-10 | 8e-20 |
| random, specification | 0.30 | 0.51 | 0.26 | 0.13 | 0.017 | 3e-04 | 5e-06 | 4e-11 |
| random, specification | 0.33 | 0.59 | 0.59 | 0.21 | 0.072 | 0.0052 | 6e-04 | 4e-07 |
| worst, 10 s | 0.25 | 0.42 | 0.16 | 0.021 | 1e-03 | 8e-07 | 7e-10 | 4e-19 |
| worst, 10 s | 0.30 | 0.53 | 0.26 | 0.12 | 0.013 | 3e-04 | 8e-06 | 6e-11 |
| worst, 10 s | 0.33 | 0.62 | 0.62 | 0.2 | 0.063 | 0.0064 | 6e-04 | 4e-07 |

What remains under a delay of `T` is the choices at the cut-off in the windows whose lead outlasts
`T`: the factor per nonce is `E[1 + (G_min − 1)·1{the lead lasts T}]`
(`finality_sim.further.delayed_factor`, 20,000 windows a point), and the depth at `1e-9` with two
nonces is read as B7 reads its factors. Each cell gives the factor and the depth:

| delay | α | k | not ground | B7's estimate | T = 0 min | T = 5 min | T = 10 min | T = 20 min | T = 30 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2160 | 165 | 187–189 | 1.030, 165 | 1.008, 165 | 1.001, 165 | 1.000, 165 | 1.000, 165 |
| random, specification | 0.30 | 1620 | 165 | 187–189 | 1.043, 165 | 1.012, 165 | 1.002, 165 | 1.000, 165 | 1.000, 165 |
| random, specification | 0.30 | 1080 | 165 | 188–190 | 1.065, 166 | 1.019, 165 | 1.003, 165 | 1.000, 165 | 1.000, 165 |
| random, specification | 0.33 | 2160 | 276 | 326–333 | 1.057, 277 | 1.021, 276 | 1.010, 276 | 1.001, 276 | 1.000, 276 |
| random, specification | 0.33 | 1620 | 276 | 328–334 | 1.086, 278 | 1.033, 277 | 1.017, 276 | 1.002, 276 | 1.000, 276 |
| random, specification | 0.33 | 1080 | 276 | 329–336 | 1.159, 280 | 1.064, 277 | 1.023, 276 | 1.001, 276 | 1.006, 276 |
| worst, 10 s | 0.30 | 2160 | 892 | 1,057–1,088 | 1.031, 894 | 1.007, 892 | 1.001, 892 | 1.000, 892 | 1.000, 892 |
| worst, 10 s | 0.30 | 1620 | 892 | 1,059–1,092 | 1.039, 895 | 1.009, 892 | 1.002, 892 | 1.000, 892 | 1.000, 892 |
| worst, 10 s | 0.30 | 1080 | 892 | 1,060–1,093 | 1.066, 897 | 1.015, 893 | 1.002, 892 | 1.000, 892 | 1.000, 892 |
| worst, 10 s | 0.33 | 2160 | 1,510 | 1,859–1,939 | 1.061, 1,518 | 1.021, 1,513 | 1.008, 1,511 | 1.002, 1,510 | 1.000, 1,510 |
| worst, 10 s | 0.33 | 1620 | 1,510 | 1,862–1,943 | 1.089, 1,522 | 1.028, 1,514 | 1.010, 1,511 | 1.002, 1,510 | 1.001, 1,510 |
| worst, 10 s | 0.33 | 1080 | 1,510 | 1,873–1,952 | 1.159, 1,531 | 1.048, 1,517 | 1.025, 1,513 | 1.003, 1,510 | 1.000, 1,510 |

- **With `T` of 10 minutes the factor per nonce is 1.00–1.03 and the depth is the unground one
  within three blocks:** against a third under the worst case at 10 s, 1,511 blocks at `k = 2160`
  and 1,513 at `k = 1080`, against B7's estimated 1,859–1,952; 23.0 hours on the worst-case clock
  instead of 28.3–29.7. With `T` of 20 minutes the depth is the unground one at every `k`.
- **`k = 1620` holds a third and `k = 1080` holds 30 %** with margins of 7 % and 17 %, where B7's
  estimate leaves `k = 1620` short and `k = 1080` at the edge. These are bounds within B6's model:
  `G_min` is counted against an enumeration of every fork and every subset of withheld wins, and
  the lead `Z` is B6's walk.
- **The prediction channel is unchanged.** A coalition that holds every minimum of two windows
  computes the delay as anyone does; `m` stays at B7's values.
- **B6's recovery horizon is the unground one.** In days, without grinding / with this nonce under a
  10-minute delay, as B6 and B7 compute it, at each `k`'s longest window:

| delay | k | window | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- |
| random, specification | 2160 | 72 h | 147–285 / 147–285 | 106–205 / 106–204 |
| random, specification | 1620 | 54 h | 137–265 / 137–265 | 97–186 / 97–186 |
| random, specification | 1080 | 36 h | 121–234 / 121–234 | 82–157 / 82–157 |
| worst, 10 s | 2160 | 72 h | 134–259 / 134–259 | 97–188 / 97–188 |
| worst, 10 s | 1620 | 54 h | 125–242 / 125–242 | 89–172 / 89–172 |
| worst, 10 s | 1080 | 36 h | 111–215 / 111–215 | 76–146 / 76–146 |

What it costs, with the CIP-0161 assumption that the coalition's hardware is 10 times faster than a
CPU: a sequential computation of `10·T`, 100–200 minutes for `T` of 10–20 minutes, once an epoch,
by whoever first needs the nonce, with a Wesolowski proof in the block that first uses it. The
lottery-constants finalization phase leaves `4⌊k/f⌋` slots between the cut-off and the first slot
that uses the nonce, 72 hours at `k = 2160` and 36 at `k = 1080`. If the coalition's hardware were
100 times faster, `10·T` becomes `100·T`, 17–33 hours, still inside that phase at `k ≥ 1080`.
Phalanx's 82 independent pieces do not serve here: a piece takes 53 s on the coalition's hardware,
less than a decision window.

Open: the choice of delay function and its parameters, as for Phalanx; the speed ratio between the
coalition's hardware and an honest node's; and a proof of the combined rule.

## G2 — the epoch decoupled from `k`

The epoch, the nonce's window before the cut-off and the recovery window are all multiples of
`⌊k/f⌋`. A smaller `k` therefore shortens them, which is what costs route 3 most: at `k = 1080` the
sub-windows shrink, `E[G_min]` rises from 1.06 to 1.16 against a third, and the recovery window
falls from 72 to 36 hours. If the epoch keeps its length, `10·64,800` slots, while `k` falls to
1080, every figure of the nonce and of the recovery window is the `k = 2160` row of B7 and B6: the
sub-window stays 15,552 slots, `E[G_min]` 1.06, the recovery window 72 hours, and the horizon
against 30 % 129–251 days under the worst case at 10 s (B7's recovery table) instead of 106–204.
`MAPPING.md` §4–§6 maps what else `k` changes with the epoch tied to it or decoupled. The cost is
one more parameter in the specification, and a stake snapshot that stays 7.5 days old at any `k`.

## G3 — Blend's delay

The depth depends on how late a block can arrive: the worst-case bound `Δ`, and under random delay
the orphan share. C2 left the trade between delay and privacy to the Blend owners. The lever is
read here on the twelve Blend settings A1 measured, with `Δ` the setting's 99th-percentile full
delay rounded up. Each depth cell gives the depth and time without grinding, then with B7's nonce
under G1's delay, whose factor per nonce is the choices at the cut-off at `k = 2160`, met twice.
The privacy columns are the Blend report's (`reports/blend`): a message's whole path is adversarial
with chance `f_adv^hops`, read at `f_adv = 1/3`, and the broadcasts a relay blends into one release
grow with `(2M + 1)/3` for `M` rounds of mixing delay (`scripts/g3_blend_delay.py`):

| hops | rounds | p99 delay | Δ | orphans | growth / f | path captured | blending | random, 0.30 | worst, 0.30 | random, 0.33 | worst, 0.33 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1.8 s | 2.0 s | 0.04 | 0.971 | 0.333 | 1.00 | 114 (1.4 h), 114 (1.4 h) | 525 (6.5 h), 526 (6.5 h) | 172 (2.2 h), 173 (2.2 h) | 812 (10.5 h), 816 (10.6 h) |
| 1 | 2 | 2.8 s | 3.0 s | 0.06 | 0.961 | 0.333 | 1.67 | 116 (1.4 h), 117 (1.4 h) | 558 (7.1 h), 559 (7.1 h) | 178 (2.3 h), 179 (2.3 h) | 871 (11.6 h), 876 (11.6 h) |
| 1 | 3 | 3.8 s | 4.0 s | 0.08 | 0.943 | 0.333 | 2.33 | 122 (1.5 h), 122 (1.5 h) | 593 (7.7 h), 595 (7.7 h) | 188 (2.5 h), 190 (2.5 h) | 936 (12.7 h), 941 (12.7 h) |
| 1 | 5 | 5.8 s | 6.0 s | 0.10 | 0.918 | 0.333 | 3.67 | 131 (1.7 h), 131 (1.7 h) | 675 (9.1 h), 677 (9.1 h) | 206 (2.8 h), 207 (2.8 h) | 1,087 (15.3 h), 1,094 (15.4 h) |
| 1 | 8 | 8.8 s | 9.0 s | 0.14 | 0.878 | 0.333 | 5.67 | 148 (2.0 h), 148 (2.0 h) | 829 (11.9 h), 832 (11.9 h) | 240 (3.4 h), 242 (3.4 h) | 1,385 (20.7 h), 1,393 (20.8 h) |
| 1 | 12 | 12.7 s | 13.0 s | 0.18 | 0.826 | 0.333 | 8.33 | 176 (2.5 h), 177 (2.6 h) | 1,123 (17.4 h), 1,126 (17.4 h) | 302 (4.6 h), 304 (4.6 h) | 1,987 (31.9 h), 1,999 (32.1 h) |
| 3 | 1 | 4.4 s | 5.0 s | 0.11 | 0.904 | 0.037 | 1.00 | 136 (1.8 h), 137 (1.8 h) | 632 (8.4 h), 634 (8.4 h) | 216 (3.0 h), 218 (3.0 h) | 1,008 (13.9 h), 1,014 (14.0 h) |
| 3 | 2 | 7.3 s | 8.0 s | 0.15 | 0.860 | 0.037 | 1.67 | 157 (2.2 h), 157 (2.2 h) | 773 (10.9 h), 775 (10.9 h) | 259 (3.8 h), 260 (3.8 h) | 1,275 (18.7 h), 1,282 (18.8 h) |
| 3 | 3 | 10.2 s | 11.0 s | 0.18 | 0.845 | 0.037 | 2.33 | 165 (2.3 h), 165 (2.3 h) | 961 (14.3 h), 963 (14.3 h) | 276 (4.1 h), 277 (4.1 h) | 1,649 (25.5 h), 1,659 (25.7 h) |
| 3 | 5 | 15.4 s | 16.0 s | 0.24 | 0.769 | 0.037 | 3.67 | 222 (3.4 h), 223 (3.5 h) | 1,446 (23.6 h), 1,450 (23.6 h) | 410 (6.7 h), 412 (6.7 h) | 2,696 (45.5 h), 2,711 (45.7 h) |
| 3 | 8 | 23.4 s | 24.0 s | 0.30 | 0.720 | 0.037 | 5.67 | 283 (4.7 h), 283 (4.7 h) | 3,229 (59.8 h), 3,238 (59.9 h) | 574 (10.0 h), 577 (10.0 h) | 7,367 (140.7 h), 7,409 (141.5 h) |
| 3 | 12 | 34.0 s | 34.0 s | 0.39 | 0.620 | 0.037 | 8.33 | 560 (10.8 h), 561 (10.8 h) | – | 1,657 (33.4 h), 1,667 (33.6 h) | – |

- **From the specification's setting to testnet's, the worst-case depth against a third falls from
  1,649 blocks at `Δ = 11` s to 812 at 2 s,** 25.5 to 10.5 hours; under random delay from 276 to
  172 blocks, 4.1 to 2.2 hours. The specification's p99 of 10.2 s rounds up to 11 s; the report's
  `Δ = 10` s gives 1,510 (B2). With the nonce under G1's delay each depth grows by at most 1 %.
- **One hop of up to three rounds, 4 s, gives 936 blocks (12.7 hours)** against a third, and three
  hops of one round, 5 s, 1,008 (13.9 hours).
- **The price in the Blend report's terms.** Testnet's hop exposes the whole path of one message
  in three to an adversary holding a third of the nodes; three hops expose one in 27. One round of
  mixing blends a relay's releases over a third of the broadcasts that three rounds do. The
  Blend report also notes that a staker's emission count, not the path, is what identifies the
  largest holders. Which setting is acceptable is the Blend owners' decision (C2).
- **Faster blocks pay once the delay is short.** On testnet's Blend 15 s blocks settle against a
  third in 80 minutes at `1e-9` and 10 s blocks in 56 (`RATE.md`, C1), where 30 s blocks take 133.

## G4 — settlement on a chain nobody withholds from

The report's hours are on the clock of a chain the coalition withholds from. A private attack on a
target withholds the coalition's blocks from the target's parent on, so during an attack the
canonical chain runs at the honest rate `(1 − α)·g·λ`; a chain nobody withholds from runs at the
full rate `g·λ`, `λ = −ln(1 − f)`. A client that reads time sees the difference. B4's elapsed-time
rule accepts the `n`-th block counting the target when the coalition's exact chance given the time
since the parent is at most `ε`; a fast chain leaves the coalition little time, so the rule accepts
sooner on a chain nobody withholds from. A rule that reads the chain's density directly, the race's
chance times the chance of seeing that many blocks under an attack of share `w` for every `w` up
to `α` (`finality_sim.further.density_depth`), is given beside it. Blocks at their mean spacing
(`finality_sim.further.time_rule_depth`); minutes on the clock of the chain read
(`scripts/g4_density.py`):

| Blend | α | depth rule, full / withheld from | elapsed time, B4's rates, full | withheld from | adjusted rates, full | withheld from  | reading density, full |
| --- | --- | --- | --- | --- | --- | --- | --- |
| testnet | 0.10 | 17: 9 / 10 min | 14, 7 min | 15, 9 min | 15, 8 min | 16, 9 min | 17, 9 min, 1e-11 |
| testnet | 0.25 | 67: 34 / 46 min | 37, 19 min | 49, 34 min | 49, 25 min | 79, 54 min | 54, 28 min, 1e-13 |
| testnet | 0.30 | 114: 59 / 84 min | 51, 26 min | 79, 58 min | 79, 41 min | 203, 149 min | 77, 40 min, 1e-14 |
| testnet | 0.33 | 172: 89 / 133 min | 65, 33 min | 116, 90 min | 116, 60 min | the depth rule's | 94, 48 min, 1e-13 |
| specification | 0.10 | 19: 11 / 12 min | 16, 9 min | 17, 11 min | 17, 10 min | 18, 12 min | 19, 11 min, 1e-11 |
| specification | 0.25 | 88: 52 / 69 min | 45, 27 min | 63, 50 min | 63, 37 min | 112, 88 min | 69, 41 min, 1e-14 |
| specification | 0.30 | 165: 98 / 139 min | 66, 39 min | 111, 94 min | 111, 66 min | 396, 335 min | 100, 59 min, 1e-14 |
| specification | 0.33 | 276: 163 / 245 min | 89, 53 min | 180, 160 min | 180, 106 min | the depth rule's | 121, 72 min, 1e-12 |

The two elapsed-time rules played on 32 timelines of 200,000 slots at the full rate with no
coalition blocks, scored at every target: the mean blocks on top of the target, and the mean and
90th-percentile minutes to acceptance:

| Blend | α | B4's rates: blocks on top, minutes, p90 | adjusted rates: blocks on top, minutes, p90 |
| --- | --- | --- | --- |
| testnet | 0.10 | 13.1, 7, 10 | 13.9, 7, 11 |
| testnet | 0.25 | 35.7, 18, 25 | 47.8, 24, 35 |
| testnet | 0.30 | 50.1, 25, 34 | 78.5, 40, 56 |
| testnet | 0.33 | 64.5, 33, 43 | 114.7, 58, 80 |
| specification | 0.10 | 14.6, 8, 13 | 15.5, 9, 14 |
| specification | 0.25 | 44.0, 26, 35 | 61.5, 36, 51 |
| specification | 0.30 | 65.2, 38, 50 | 110.7, 65, 90 |
| specification | 0.33 | 88.5, 52, 66 | 177.9, 103, 141 |

- **B4's rule already settles a chain nobody withholds from in 39 / 53 minutes against 30 % / a
  third** on the specification's Blend, against the depth rule's 98 / 163 at the same rate. The
  density rule accepts later, at 59 / 72 minutes, and its acceptance point is sound (the exact
  conditional chance there is `1e-14` / `1e-12`): it adds nothing to the elapsed-time rule.
- **B4's rates hold while the inferred stake is the true stake.** The total-stake inference sets
  the lottery's thresholds from the previous period's occupied slots
  (`cryptarchia-total-stake-inference.md`, `PERIOD = 6⌊k/f⌋`, `beta = 1`). A coalition that
  withholds for a whole period, 3 days at `k = 2160`, lowers the inferred stake by its share, and
  every rate rises by `1/(1 − α)`: the honest stake alone then produces at `g·λ`, and the coalition
  wins at `α·λ/(1 − α)`. The catch-up ratio `a/h` is unchanged, so the depth rule is unmoved. The
  elapsed-time rule with B4's rates would then take the coalition's wins as Poisson at `α·λ` where
  they come at `α·λ/(1 − α)`, and its chance is understated. The inferred stake's history does not
  tell the client which world it is in: a coalition that withheld long ago looks like stake that
  left.
- **The safe rule takes the adjusted rates, with the depth rule as its cap.** Under the adjusted
  rates the chain the coalition withholds from, at `(1 − α)·g·λ`, reads as slow, and the rule
  accepts after the depth rule or never; the cap returns the depth rule there. On a chain nobody
  withholds from it accepts at 111 / 180 blocks, 66 / 106 minutes against 30 % / a third, where
  the depth rule needs 98 / 163; played on timelines, 65 / 103 minutes on average and 90 / 141 at
  the 90th percentile, against B4's rates' 38 / 52 and 50 / 66. B4's gains on a chain withheld
  from, 94 / 160 minutes against the depth rule's 139 / 245, hold only with the inferred stake at
  the true stake.
- **A coalition cannot inflate the density.** A block it publishes that extends the public tip
  lengthens the chain its private one must beat; one that ties an honest block replaces it one for
  one.
- **Not covered:** the worst case of `Δ`, under which the coalition also lowers the honest rate by
  delaying blocks, so a slow chain is no sign of withholding; honest nodes offline, which slow the
  chain and only delay acceptance; and the variance of the canonical count, which B5 found below
  the binomial's on the engine.

Gates (`tests/test_further.py`): the lead lasts as long as its mean drift allows and the chance
falls with time; the delayed factor runs from every choice at the cut-off, with no delay, to none;
the elapsed-time rule settles a chain nobody withholds from sooner than one withheld from, and the
adjusted rates later than B4's; without the density test the density rule is B5's depth table; the
density rule is sound where it accepts, accepts later than the elapsed-time rule, and one block
earlier some share exceeds its condition. Four mutations fail them.

## G5 — anchoring

A checkpoint written to another chain gives every node the same choice between forks older than
the anchor, which is what a partition deeper than `k` lacks (B5, rule 8), and a point before which
no fork can be presented to a bootstrapping node. Finality then comes at the anchor's interval plus
the other chain's own finality: about 15 minutes on Ethereum, an hour on Bitcoin. Any node can
write the anchor; a conflict between anchors is settled by the other chain's order. Nothing about
stake is revealed. The costs are a dependence on another chain's liveness and fee market, a rule
that makes anchored forks win in fork choice, and operators' agreement on which chain to trust.
This study does not measure it.

## G6 — Blend's delays under adversarial relays

The random-delay model lets the coalition choose no delay; the worst case lets it choose every
one. Between them lies a coalition that runs its share of the relays and holds every honest block
it carries for the longest mixing delay the protocol allows, three rounds instead of a draw on one
to three, while honest relays draw theirs (`tsi_sim`, `blend_adversary_relays`). B3's private race,
the coalition withholding, is played on the engine's timelines on the specification's Blend with
and without hostile relays, 64 runs a cell (`scripts/g6_relays.py`). Growth is canonical blocks
per honest win; the closed form at `1e-9` is B5's at that growth, on the clock of the honest chain:

| α | honest relays: orphans ± sem | honest relays: growth / win | honest relays: race depth at 1e-3 | honest relays: closed form at 1e-9 | hostile relays: orphans ± sem | hostile relays: growth / win | hostile relays: race depth at 1e-3 | hostile relays: closed form at 1e-9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 0.152 ± 0.001 | 0.851 | 23 | 87 (1.1 h) | 0.164 ± 0.001 | 0.835 | 24 | 90 (1.2 h) |
| 0.30 | 0.143 ± 0.001 | 0.857 | 42 | 158 (2.2 h) | 0.158 ± 0.001 | 0.841 | 45 | 167 (2.3 h) |
| 0.33 | 0.135 ± 0.001 | 0.861 | 63 | 257 (3.7 h) | 0.154 ± 0.001 | 0.847 | 64 | 274 (4.0 h) |

- **Hostile relays raise the honest orphan share by about two points,** 0.135 to 0.154 against a
  third, and lower the growth per win from 0.861 to 0.847: the depth at `1e-9` grows by 7 %, 257
  to 274 blocks, and the race's depth at `1e-3` by one block.
- **The report's random-delay depths already cover it.** They read the growth A1 measured with
  everyone producing, 0.845, below the growth a withholding coalition leaves even with hostile
  relays, and give 276 blocks against a third.
- **Not modelled:** a relay that drops the blocks it carries. That is a liveness attack on Blend's
  delivery, which the Blend report prices as a reliability factor per hop, not a delay.

## What the further routes change

- **G1 removes grinding within B6's model:** with a delay of 10–20 minutes the depths are those of a
  nonce that is not ground, a bound rather than B7's estimate, and `k = 1620` holds a third and
  `k = 1080` holds 30 %, at the cost of a sequential computation per epoch.
- **G2 keeps the nonce's window and the recovery window long when `k` shrinks,** at the cost of a
  parameter.
- **G3 halves the worst-case depth** if Blend delivers within 2 s, and cuts it by 43 % within 4 s,
  at a cost in anonymity the Blend report prices and this study reads from it.
- **G4 finds the gain on a chain nobody withholds from already in B4's elapsed-time rule,** 39 / 53
  minutes against 30 % / a third, and a condition B4 lacked: the rule's rates must follow the
  total-stake inference, which leaves 66 / 106 minutes on such a chain and the depth rule on one
  the coalition withholds from. A rule that reads density directly adds nothing.
- **G5 heals partitions and bounds long-range forks,** at the cost of a dependence on another chain.
- **G6 finds the random-delay depths robust to hostile relays:** holding every honest block for
  the longest mixing delay costs about 7 % of depth, within what the report's growth convention
  already covers.
