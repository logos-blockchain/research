# Further routes

Phase G of `PLAN.md`: ways to shorten finality that the three routes of the report do not cover,
read against 30 % and a third of the stake at `ε = 1e-9`. Tables come from `runs/` through
`scripts/tables.py`; runs from `scripts/g1_delayed_nonce.py`, `scripts/g3_blend_delay.py` and
`scripts/g4_density.py`. G2 and G5 need no run.

## G1 — the smallest contributions with a delayed nonce

B7's factor is dominated by the decisions a coalition takes before the cut-off: to publish or
withhold a block of its own, and to remove an honest block that holds a sub-window's minimum. Each
decision is worth something only if the coalition can compute the nonce each outcome gives before
it must act. If the nonce is `η_e = delay(hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m))`, with `delay` a sequential
function of `T` seconds on the coalition's hardware, every decision whose window is shorter than
`T` is taken blind, and a blind choice gains nothing: the chance against a nonce chosen blind among
`G` is the average over the `G`, which is `u`.

The decision windows:

- **Before the cut-off**, a block of the coalition's own must be published before the honest
  chain grows past it, or it needs a fork; an honest block must be removed within `Δ` under the
  worst case, or raced from its parent before the chain grows past it. Both windows are about one
  block interval, 50–55 s.
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

With `T` of a few minutes the decisions before the cut-off are blind. With `T` of 10 minutes the
choice at the cut-off is available in 6 % of epochs against a third, and with 20 minutes in
0.6 %. What remains is at most the choices at the cut-off, `E[G_min]` per nonce, which B7 counts
against an enumeration of every fork and every subset of withheld wins. The depth at `1e-9` with
two nonces is then B7's "at the cut-off" row, a bound within B6's model rather than an estimate:

| delay | α | k | not ground | blind before the cut-off | B7's estimate |
| --- | --- | --- | --- | --- | --- |
| random, specification | 0.25 | 2160 | 88 | 88 | 96 |
| random, specification | 0.25 | 1620 | 88 | 88 | 96 |
| random, specification | 0.25 | 1080 | 88 | 88 | 96 |
| random, specification | 0.30 | 2160 | 165 | 165 | 187–189 |
| random, specification | 0.30 | 1620 | 165 | 165 | 187–189 |
| random, specification | 0.30 | 1080 | 165 | 166 | 188–190 |
| random, specification | 0.33 | 2160 | 276 | 277 | 326–333 |
| random, specification | 0.33 | 1620 | 276 | 278 | 328–334 |
| random, specification | 0.33 | 1080 | 276 | 280 | 329–336 |
| worst, 10 s | 0.25 | 2160 | 474 | 474 | 538–548 |
| worst, 10 s | 0.25 | 1620 | 474 | 475 | 538–549 |
| worst, 10 s | 0.25 | 1080 | 474 | 475 | 539–549 |
| worst, 10 s | 0.30 | 2160 | 892 | 894 | 1,057–1,088 |
| worst, 10 s | 0.30 | 1620 | 892 | 895 | 1,059–1,092 |
| worst, 10 s | 0.30 | 1080 | 892 | 897 | 1,060–1,093 |
| worst, 10 s | 0.33 | 2160 | 1,510 | 1,518 | 1,859–1,939 |
| worst, 10 s | 0.33 | 1620 | 1,510 | 1,522 | 1,862–1,943 |
| worst, 10 s | 0.33 | 1080 | 1,510 | 1,532 | 1,873–1,952 |

- **Against a third under the worst case at 10 s, 1,518 blocks at `k = 2160` instead of an estimated
  1,859–1,939:** 23.1 hours on the worst-case clock instead of 28.3–29.5, and 8 blocks above the
  unground 1,510.
- **`k = 1620` holds a third (1,522 blocks) and `k = 1080` holds 30 % (897 blocks)** with margins of
  6 % and 17 %, where B7's estimate leaves `k = 1620` short and `k = 1080` at the edge.
- **The prediction channel is unchanged.** A coalition that holds every minimum of two windows
  computes the delay as anyone does; `m` stays at B7's values.

What it costs, with the CIP-0161 assumption that the coalition's hardware is 10 times faster than a
CPU: a sequential computation of `10·T`, 100–200 minutes for `T` of 10–20 minutes, once an epoch,
by whoever first needs the nonce, with a Wesolowski proof in the block that first uses it. The
lottery-constants finalization phase leaves `4⌊k/f⌋` slots between the cut-off and the first slot
that uses the nonce, 72 hours at `k = 2160` and 36 at `k = 1080`. Phalanx's 82 independent pieces do
not serve here: a piece takes 53 s on the coalition's hardware, less than a decision window.

Open: the choice of delay function and its parameters, as for Phalanx; the 10× assumption; and a
proof of the combined rule.

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
delay rounded up, without grinding (`scripts/g3_blend_delay.py`):

| hops | rounds | p99 delay | Δ | orphans | growth / f | random, 0.30 | worst, 0.30 | random, 0.33 | worst, 0.33 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1.8 s | 2.0 s | 0.04 | 0.971 | 114 (1.4 h) | 525 (6.5 h) | 172 (2.2 h) | 812 (10.5 h) |
| 1 | 2 | 2.8 s | 3.0 s | 0.06 | 0.961 | 116 (1.4 h) | 558 (7.1 h) | 178 (2.3 h) | 871 (11.6 h) |
| 1 | 3 | 3.8 s | 4.0 s | 0.08 | 0.943 | 122 (1.5 h) | 593 (7.7 h) | 188 (2.5 h) | 936 (12.7 h) |
| 1 | 5 | 5.8 s | 6.0 s | 0.10 | 0.918 | 131 (1.7 h) | 675 (9.1 h) | 206 (2.8 h) | 1,087 (15.3 h) |
| 1 | 8 | 8.8 s | 9.0 s | 0.14 | 0.878 | 148 (2.0 h) | 829 (11.9 h) | 240 (3.4 h) | 1,385 (20.7 h) |
| 1 | 12 | 12.7 s | 13.0 s | 0.18 | 0.826 | 176 (2.5 h) | 1,123 (17.4 h) | 302 (4.6 h) | 1,987 (31.9 h) |
| 3 | 1 | 4.4 s | 5.0 s | 0.11 | 0.904 | 136 (1.8 h) | 632 (8.4 h) | 216 (3.0 h) | 1,008 (13.9 h) |
| 3 | 2 | 7.3 s | 8.0 s | 0.15 | 0.860 | 157 (2.2 h) | 773 (10.9 h) | 259 (3.8 h) | 1,275 (18.7 h) |
| 3 | 3 | 10.2 s | 11.0 s | 0.18 | 0.845 | 165 (2.3 h) | 961 (14.3 h) | 276 (4.1 h) | 1,649 (25.5 h) |
| 3 | 5 | 15.4 s | 16.0 s | 0.24 | 0.769 | 222 (3.4 h) | 1,446 (23.6 h) | 410 (6.7 h) | 2,696 (45.5 h) |
| 3 | 8 | 23.4 s | 24.0 s | 0.30 | 0.720 | 283 (4.7 h) | 3,229 (59.8 h) | 574 (10.0 h) | 7,367 (140.7 h) |
| 3 | 12 | 34.0 s | 34.0 s | 0.39 | 0.620 | 560 (10.8 h) | – | 1,657 (33.4 h) | – |

- **From the specification's setting to testnet's, the worst-case depth against a third falls from
  1,649 blocks at `Δ = 11` s to 812 at 2 s,** 25.5 to 10.5 hours; under random delay from 276 to
  172 blocks, 4.1 to 2.2 hours. The specification's p99 of 10.2 s rounds up to 11 s; the report's
  `Δ = 10` s gives 1,510 (B2).
- **One hop of up to three rounds, 4 s, gives 936 blocks (12.7 hours)** against a third, and three
  hops of one round, 5 s, 1,008 (13.9 hours).
- **Faster blocks pay once the delay is short.** On testnet's Blend 15 s blocks settle against a
  third in 80 minutes at `1e-9` and 10 s blocks in 56 (`RATE.md`, C1), where 30 s blocks take 133.
- **The price is Blend's anonymity,** which the Blend report models and this study does not. Which
  setting is acceptable is the Blend owners' decision (C2).

## G4 — a settlement rule that reads density

A private attack on a target withholds the coalition's blocks from the target's parent on. The
canonical chain then runs at the honest rate, `(1 − w)·g·λ` per slot for a withheld share `w`,
instead of the full rate `g·λ` of a chain nobody withholds from. A client sees the rate. A rule that
reads it accepts a target once, for every `w` up to its bound `α`, the private race's chance at the
target's depth times the chance that a chain under attack `w` shows at least the blocks the client
saw since the parent is at or below `ε` (`finality_sim.further.density_depth`). A chain under attack
fails the second factor, and the client waits for B5's depth as it does today; a chain nobody
attacks passes it, and the client accepts sooner. A first look under random delay, the chain's count
taken as Poisson, in blocks and in minutes on the full-rate clock `30 s / g`
(`scripts/g4_density.py`):

| Blend | α | depth rule: blocks, minutes at the full rate, minutes while withheld from | reading density: blocks, minutes at the full rate | share that binds |
| --- | --- | --- | --- | --- |
| testnet | 0.10 | 17, 9, 10 | 16, 8 | 0.10 |
| testnet | 0.25 | 67, 34, 46 | 53, 27 | 0.25 |
| testnet | 0.30 | 114, 59, 84 | 76, 39 | 0.30 |
| testnet | 0.33 | 172, 89, 133 | 93, 48 | 0.33 |
| specification | 0.10 | 19, 11, 12 | 18, 11 | 0.10 |
| specification | 0.25 | 88, 52, 69 | 68, 40 | 0.25 |
| specification | 0.30 | 165, 98, 139 | 99, 59 | 0.30 |
| specification | 0.33 | 276, 163, 245 | 120, 71 | 0.33 |

- **A chain nobody attacks settles against a third in 71 minutes instead of 163** on the
  specification's Blend, and against 30 % in 59 instead of 98. The report's hours, on the clock of
  a chain the coalition withholds from, are the attacked case, which this rule leaves as it is.
- **The bound binds.** A smaller withheld share hides better in the density but loses the race
  sooner, and at every point of the table the largest share needs the most depth.
- **The coalition cannot inflate the density.** A block it publishes that extends the public tip
  lengthens the chain its private one must beat; one that ties an honest block replaces it one for
  one.
- **The total-stake inference removes the signal after one of its periods.** The inference sets the
  lottery's thresholds from the blocks of the previous `6⌊k/f⌋` slots (`cryptarchia-total-stake-
  inference.md`, β = 1). A coalition that withholds for a whole period lowers the inferred stake by
  its share, and the honest stake then produces at the full rate on its own. The density signal
  lasts one period, 3 days at `k = 2160`, and costs the coalition that period's rewards; after it
  the signal moves to the inferred stake, which has fallen by the coalition's share. A rule that
  reads density must therefore also read the inferred stake against its recent history, and treat a
  fall of the order of `α` as an attack in progress. Stake that leaves the protocol looks the same;
  the rule then falls back to B5's depth, which is safe.
- **Not covered:** the worst case of `Δ`, under which the coalition also lowers the honest rate by
  delaying blocks, so the full-rate baseline must be the worst-case honest rate and the test loses
  power; honest nodes offline, which lower the density and only delay acceptance; and the
  variance of the canonical count, which B5 found below the binomial's on the engine.

Gates (`tests/test_further.py`): the lead lasts as long as its mean drift allows and the chance
falls with time; without the density test the rule is B5's depth table; with it the rule settles
sooner, and at the accepted depth no share up to the bound gets more than `ε` while one block
earlier some share does. Two mutations fail them.

## G5 — anchoring

A checkpoint written to another chain gives every node the same choice between forks older than
the anchor, which is what a partition deeper than `k` lacks (B5, rule 8), and a point before which
no fork can be presented to a bootstrapping node. Finality then comes at the anchor's interval plus
the other chain's own finality: about 15 minutes on Ethereum, an hour on Bitcoin. Any node can
write the anchor; a conflict between anchors is settled by the other chain's order. Nothing about
stake is revealed. The costs are a dependence on another chain's liveness and fee market, a rule
that makes anchored forks win in fork choice, and operators' agreement on which chain to trust.
This study does not measure it.

## What the further routes change

- **G1 turns B7's estimate into a bound within its model** and restores `k = 1620` against a third
  and `k = 1080` against 30 %, at the cost of a sequential computation per epoch.
- **G2 keeps the nonce's window and the recovery window long when `k` shrinks,** at the cost of a
  parameter.
- **G3 halves the worst-case depth** if Blend delivers within 2 s, and cuts it by 43 % within 4 s,
  at a cost in anonymity this study does not price.
- **G4 shortens the common case** by a factor of about two against a third, with no protocol change,
  if the rule also reads the inferred stake; it leaves the attacked case as it is.
- **G5 heals partitions and bounds long-range forks,** at the cost of a dependence on another chain.
