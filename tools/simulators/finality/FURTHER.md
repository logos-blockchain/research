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
function on the coalition's hardware, a decision whose outcome's nonce it has not computed is
taken blind, and a blind choice gains nothing: the chance against a nonce chosen blind among `G` is
the average over the `G`, which is `u`. The nonce of an outcome can be computed from the moment
its inputs are known. For the last sub-window that is the sub-window's start, since the earlier
minima are then fixed and the coalition knows its own contributions ahead (`DESIGNS.md`, H.2). The
delay must therefore span the sub-window, `W` slots, and `T` below is the margin beyond `W`. A
value then counts only if the coalition sees it while a fork that reaches it can still be published
(`finality_sim.formation`).

- **A choice is still open `T` after the cut-off** when the best lead of a fork back from the
  cut-off, `max_d L_d`, plus the most the coalition's chain gains on the honest one at or after `T`,
  reaches one. The lead after the cut-off alone, B6's `Z`, leaves out the coalition's lead at the
  cut-off. Under random delay the chance is a law from B6's walk (`formation.open_law`), which
  windows drawn slot by slot match within a standard error; under the worst case it is sampled,
  400,000 windows a point:

| delay | α | 1 min | 2 min | 5 min | 10 min | 20 min | 30 min | 60 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.25 | 0.47 | 0.36 | 0.17 | 0.059 | 0.0079 | 0.0012 | 4e-06 |
| random, specification | 0.30 | 0.63 | 0.53 | 0.34 | 0.18 | 0.054 | 0.018 | 7e-04 |
| random, specification | 0.33 | 0.73 | 0.65 | 0.49 | 0.32 | 0.15 | 0.072 | 0.0093 |
| worst, 10 s | 0.25 | 0.44 | 0.33 | 0.16 | 0.051 | 0.0062 | 8e-04 | < 3e-06 |
| worst, 10 s | 0.30 | 0.6 | 0.51 | 0.32 | 0.16 | 0.048 | 0.015 | 6e-04 |
| worst, 10 s | 0.33 | 0.72 | 0.64 | 0.47 | 0.3 | 0.14 | 0.065 | 0.0081 |

What a margin of `T` leaves of B7's contributions, which the coalition knows ahead: its own values
are formed at the sub-window's start and seen at the margin, an honest minimum is formed when its
block arrives and seen as much later, and each counts only if a fork that reaches it can still be
published when it is seen (`formation.formation_counts`, 20,000 windows a point; a window whose
deepest fork empties the sub-window counts in full). Each cell gives the factor per nonce and the
depth at `1e-9` with two nonces, read as B7 reads its factors:

| delay | α | k | not ground | B7's estimate | at the cut-off | margin 5 min | margin 10 min | margin 20 min | margin 30 min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random, specification | 0.30 | 2160 | 165 | 187–189 | 1.030, 165 | 1.009, 165 | 1.005, 165 | 1.001, 165 | 1.000, 165 |
| random, specification | 0.30 | 1620 | 165 | 187–189 | 1.043, 165 | 1.012, 165 | 1.007, 165 | 1.002, 165 | 1.001, 165 |
| random, specification | 0.30 | 1080 | 165 | 188–190 | 1.065, 166 | 1.017, 165 | 1.010, 165 | 1.003, 165 | 1.001, 165 |
| random, specification | 0.33 | 2160 | 276 | 326–333 | 1.057, 277 | 1.019, 276 | 1.013, 276 | 1.007, 276 | 1.003, 276 |
| random, specification | 0.33 | 1620 | 276 | 328–334 | 1.086, 278 | 1.031, 277 | 1.022, 276 | 1.010, 276 | 1.005, 276 |
| random, specification | 0.33 | 1080 | 276 | 329–336 | 1.159, 280 | 1.074, 278 | 1.054, 277 | 1.033, 277 | 1.024, 276 |
| worst, 10 s | 0.30 | 2160 | 892 | 1,057–1,088 | 1.031, 894 | 1.009, 892 | 1.005, 892 | 1.002, 892 | 1.001, 892 |
| worst, 10 s | 0.30 | 1620 | 892 | 1,059–1,092 | 1.039, 895 | 1.011, 892 | 1.006, 892 | 1.002, 892 | 1.001, 892 |
| worst, 10 s | 0.30 | 1080 | 892 | 1,060–1,093 | 1.066, 897 | 1.018, 893 | 1.010, 892 | 1.003, 892 | 1.001, 892 |
| worst, 10 s | 0.33 | 2160 | 1,510 | 1,859–1,939 | 1.061, 1,518 | 1.021, 1,513 | 1.015, 1,512 | 1.007, 1,511 | 1.003, 1,510 |
| worst, 10 s | 0.33 | 1620 | 1,510 | 1,862–1,943 | 1.089, 1,522 | 1.034, 1,514 | 1.023, 1,513 | 1.011, 1,511 | 1.005, 1,510 |
| worst, 10 s | 0.33 | 1080 | 1,510 | 1,873–1,952 | 1.159, 1,531 | 1.067, 1,519 | 1.049, 1,517 | 1.028, 1,514 | 1.020, 1,512 |

Were every value formed at the sub-window's start, a margin of 10 minutes would leave the choices
at the cut-off in the windows still open then:

| delay | α | k | every value formed at the sub-window's start, 10 min |
| --- | --- | --- | --- |
| random, specification | 0.30 | 2160 | 1.012, 165 |
| random, specification | 0.30 | 1620 | 1.017, 165 |
| random, specification | 0.30 | 1080 | 1.025, 165 |
| random, specification | 0.33 | 2160 | 1.033, 277 |
| random, specification | 0.33 | 1620 | 1.050, 277 |
| random, specification | 0.33 | 1080 | 1.090, 278 |
| worst, 10 s | 0.30 | 2160 | 1.012, 893 |
| worst, 10 s | 0.30 | 1620 | 1.014, 893 |
| worst, 10 s | 0.30 | 1080 | 1.025, 894 |
| worst, 10 s | 0.33 | 2160 | 1.035, 1,515 |
| worst, 10 s | 0.33 | 1620 | 1.051, 1,517 |
| worst, 10 s | 0.33 | 1080 | 1.083, 1,521 |

- **With a margin of 10 minutes B7's contributions leave a factor per nonce of 1.005–1.054,** and
  the depth is the unground one within seven blocks: against a third under the worst case at 10 s,
  1,512 blocks at `k = 2160`, 1,513 at 1620 and 1,517 at 1080, against B7's estimated
  1,859–1,952. These are estimates over sampled windows. The honest minima the forks keep are among
  `G_min`, which `DESIGNS.md` H.2 bounds from B6's walk.
- **These contributions are known ahead, so B7's conditions 1 and 2 stay.** A coalition that holds
  every minimum of two windows predicts the nonce and computes its delay ahead; `m` stays at B7's
  values. Bound to the parent's contribution (`DESIGNS.md` H.2), a contribution exists only once
  the block its branch forks from does, which closes the prediction channel and sets `m` by B7's
  condition 3 and the honest cost alone; under the same delay it leaves a factor of 1.002–1.04,
  with a term for the coalition's delay evaluators.
- **B6's recovery horizon is the unground one.** In days, without grinding / with this nonce under a
  10-minute delay, as B6 and B7 compute it, at each `k`'s longest window:

| delay | k | window | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- | --- |
| random, specification | 2160 | 72 h | 147–285 / 147–285 | 106–205 / 106–204 |
| random, specification | 1620 | 54 h | 137–265 / 137–265 | 97–186 / 97–186 |
| random, specification | 1080 | 36 h | 121–234 / 121–233 | 82–157 / 82–157 |
| worst, 10 s | 2160 | 72 h | 134–259 / 134–259 | 97–188 / 97–188 |
| worst, 10 s | 1620 | 54 h | 125–242 / 125–242 | 89–172 / 89–172 |
| worst, 10 s | 1080 | 36 h | 111–215 / 111–215 | 76–146 / 76–146 |

What it costs: a sequential computation of `R·(W + T)` for a speed ratio `R`, once an epoch, by
whoever first needs the nonce, with a Wesolowski proof published within the phase, before the
first slot that uses the nonce: 22 hours at `k = 2160` and 11 at `k = 1080` at `R = 5`, twice that
at the CIP-0161 assumption of 10. The lottery-constants finalization phase leaves `4⌊k/f⌋` slots
between the cut-off and that slot, 72 hours at `k = 2160` and 36 at `k = 1080`, whose squarings
alone hold a ratio of 15 to 16; the prover's work comes on top. Phalanx's 82 independent pieces do
not serve here: a piece takes 53 s on the coalition's hardware.

`DESIGNS.md` H.2 sets the delay, the binding of the contribution to the parent's contribution, and
the honest cost against the speed ratio, and states what a proof of the combined rule still needs.

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
under G1's delay, whose factor per nonce is at most the choices at the cut-off, `E[G_min]` at
`k = 2160`, met twice. `E[G_min]` is sampled per setting and delay model, 20,000 windows a cell:
under random delay at the setting's growth, under the worst case at its `Δ`. The privacy columns
are the Blend report's (`reports/blend`): a message's whole path is adversarial with chance
`f_adv^hops`, read at `f_adv = 1/3`, and the broadcasts a relay blends into one release grow with
`(2M + 1)/3` for `M` rounds of mixing delay (`scripts/g3_blend_delay.py`):

| hops | rounds | p99 delay | Δ | orphans | growth / f | path captured | blending | random, 0.30 | worst, 0.30 | random, 0.33 | worst, 0.33 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1.8 s | 2.0 s | 0.04 | 0.971 | 0.333 | 1.00 | 114 (1.4 h), 114 (1.4 h) | 525 (6.5 h), 526 (6.5 h) | 172 (2.2 h), 173 (2.2 h) | 812 (10.5 h), 814 (10.6 h) |
| 1 | 2 | 2.8 s | 3.0 s | 0.06 | 0.961 | 0.333 | 1.67 | 116 (1.4 h), 117 (1.4 h) | 558 (7.1 h), 559 (7.1 h) | 178 (2.3 h), 178 (2.3 h) | 871 (11.6 h), 873 (11.6 h) |
| 1 | 3 | 3.8 s | 4.0 s | 0.08 | 0.943 | 0.333 | 2.33 | 122 (1.5 h), 122 (1.5 h) | 593 (7.7 h), 594 (7.7 h) | 188 (2.5 h), 189 (2.5 h) | 936 (12.7 h), 939 (12.7 h) |
| 1 | 5 | 5.8 s | 6.0 s | 0.10 | 0.918 | 0.333 | 3.67 | 131 (1.7 h), 131 (1.7 h) | 675 (9.1 h), 676 (9.1 h) | 206 (2.8 h), 207 (2.8 h) | 1,087 (15.3 h), 1,092 (15.4 h) |
| 1 | 8 | 8.8 s | 9.0 s | 0.14 | 0.878 | 0.333 | 5.67 | 148 (2.0 h), 148 (2.0 h) | 829 (11.9 h), 831 (11.9 h) | 240 (3.4 h), 241 (3.4 h) | 1,385 (20.7 h), 1,393 (20.8 h) |
| 1 | 12 | 12.7 s | 13.0 s | 0.18 | 0.826 | 0.333 | 8.33 | 176 (2.5 h), 177 (2.6 h) | 1,123 (17.4 h), 1,127 (17.4 h) | 302 (4.6 h), 304 (4.6 h) | 1,987 (31.9 h), 2,002 (32.1 h) |
| 3 | 1 | 4.4 s | 5.0 s | 0.11 | 0.904 | 0.037 | 1.00 | 136 (1.8 h), 137 (1.8 h) | 632 (8.4 h), 633 (8.4 h) | 216 (3.0 h), 217 (3.0 h) | 1,008 (13.9 h), 1,011 (14.0 h) |
| 3 | 2 | 7.3 s | 8.0 s | 0.15 | 0.860 | 0.037 | 1.67 | 157 (2.2 h), 157 (2.2 h) | 773 (10.9 h), 774 (10.9 h) | 259 (3.8 h), 260 (3.8 h) | 1,275 (18.7 h), 1,281 (18.8 h) |
| 3 | 3 | 10.2 s | 11.0 s | 0.18 | 0.845 | 0.037 | 2.33 | 165 (2.3 h), 165 (2.3 h) | 961 (14.3 h), 964 (14.4 h) | 276 (4.1 h), 277 (4.1 h) | 1,649 (25.5 h), 1,659 (25.7 h) |
| 3 | 5 | 15.4 s | 16.0 s | 0.24 | 0.769 | 0.037 | 3.67 | 222 (3.4 h), 223 (3.5 h) | 1,446 (23.6 h), 1,453 (23.7 h) | 410 (6.7 h), 414 (6.7 h) | 2,696 (45.5 h), 2,724 (46.0 h) |
| 3 | 8 | 23.4 s | 24.0 s | 0.30 | 0.720 | 0.037 | 5.67 | 283 (4.7 h), 285 (4.7 h) | 3,229 (59.8 h), 3,260 (60.3 h) | 574 (10.0 h), 589 (10.2 h) | 7,367 (140.7 h), 7,904 (150.9 h) |
| 3 | 12 | 34.0 s | 34.0 s | 0.39 | 0.620 | 0.037 | 8.33 | 560 (10.8 h), 576 (11.1 h) | – | 1,657 (33.4 h), 2,142 (43.2 h) | – |

`E[G_min]` at `k = 2160`, per setting and delay model:

| hops | rounds | random, 0.30 | worst, 0.30 | random, 0.33 | worst, 0.33 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1.02 | 1.02 | 1.03 | 1.03 |
| 1 | 2 | 1.02 | 1.02 | 1.03 | 1.03 |
| 1 | 3 | 1.02 | 1.02 | 1.03 | 1.04 |
| 1 | 5 | 1.02 | 1.02 | 1.04 | 1.04 |
| 1 | 8 | 1.02 | 1.03 | 1.05 | 1.05 |
| 1 | 12 | 1.03 | 1.04 | 1.07 | 1.08 |
| 3 | 1 | 1.02 | 1.02 | 1.04 | 1.04 |
| 3 | 2 | 1.03 | 1.02 | 1.05 | 1.05 |
| 3 | 3 | 1.03 | 1.03 | 1.06 | 1.06 |
| 3 | 5 | 1.05 | 1.05 | 1.11 | 1.12 |
| 3 | 8 | 1.07 | 1.1 | 1.3 | 2.12 |
| 3 | 12 | 1.33 | – | 17.4, 1.8% deeper | – |

- **From the specification's setting to testnet's, the worst-case depth against a third falls from
  1,649 blocks at `Δ = 11` s to 812 at 2 s,** 25.5 to 10.5 hours; under random delay from 276 to
  172 blocks, 4.1 to 2.2 hours. The specification's p99 of 10.2 s rounds up to 11 s; the report's
  `Δ = 10` s gives 1,510 (B2). With the nonce under G1's delay each depth grows by at most 1 % at
  the settings of 16 s and less. The slowest settings leave more choices at the cut-off: against a
  third, 2.12 under the worst case at 24 s, where the depth grows by 7 % (7,367 to 7,904 blocks), and
  17.4 under random delay at 34 s, by 29 % (1,657 to 2,142). At 34 s 1.8 % of the windows hold a
  feasible fork deeper than the 20,000 slots drawn, so 17.4 is from below.
- **One hop of up to three rounds, 4 s, gives 936 blocks (12.7 hours)** against a third, and three
  hops of one round, 5 s, 1,008 (13.9 hours).
- **The price in the Blend report's terms.** Testnet's hop exposes the whole path of one message
  in three to an adversary holding a third of the nodes; three hops expose one cascade in 27, and
  with the specification's two copies about one block in 14, `1 − (26/27)^2`. One round of mixing
  blends a relay's releases over 3/7 of the broadcasts that three rounds do, `(2M + 1)/3` at
  `M = 1` against 3. The
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
  withholds for a whole period, 4.5 days at `k = 2160`, lowers the inferred stake by its share, and
  every rate rises by `1/(1 − α)`: the honest stake alone then produces at `g·λ`, and the coalition
  wins at `α·λ/(1 − α)`. The catch-up ratio `a/h` is unchanged, so in the report's convention the
  depth rule is unmoved. On the engine the deflated race needs the depth of a chain on which every
  node produces, 334 blocks against a third, where the race at the true thresholds needs 257 and
  the convention reads 276 (G7). The worst case of `Δ` moves it further, since its delay is fixed
  in slots while the blocks come faster (G7). The
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
adjusted rates later than B4's; the adjusted rule accepts at the first block whose exact chance,
at the Poisson rates of the lottery's deflated thresholds, is at most `ε`, which a coalition rate
read as its occupancy fails and the direction alone does not; without the density test the density
rule is B5's depth table; the density rule is sound where it accepts, accepts later than the
elapsed-time rule, and one block earlier some share exceeds its condition. Five mutations fail
them. In `tests/test_inference.py`, the engine's tree with every estimate deflated holds the honest
stake at `f`, the coalition at its raised threshold, and the growth per win at everyone's.

## G5 — anchoring

A checkpoint written to another chain timestamps a block. It shows that the block existed when the
anchor was written, and nothing about whether honest nodes held it: a coalition anchors the blocks
of its private fork as any node anchors the public chain's, and it can anchor first. A rule that
lets the first anchored fork win, or that makes an anchored block final, therefore hands the
choice to whoever anchors first, and an anchor that carries a proof of leadership is weighted by
stake and meets the symmetry of `DESIGNS.md` H.1. What an anchor settles is a fork that did not
exist when the anchor was written: a long-range fork built later from bought keys, beyond B5's
horizon `H`, and the history offered to a node that starts from genesis, in both cases while the
anchors name one chain. It resolves no partition deeper than `k`; H.1 places that with recovery
attestations below a third and with operators at a third. The costs are a dependence on another
chain's liveness and fee market, a rule for conflicting anchors, and operators' agreement on which
chain to trust. This study does not measure it.

## G6 — Blend's delays under adversarial relays

The random-delay model lets the coalition choose no delay; the worst case lets it choose every
one. Between them lies a coalition that runs its share of the relays (`tsi_sim`,
`blend_adversary_relays`, `blend_adversary_action`). It treats every honest block it carries in
one of three ways:

- it holds the block for the longest mixing delay the protocol allows, three rounds instead of a
  draw on one to three;
- it holds the block so and, as the cascade's last relay, which decrypts the proposal and so reads
  its slot, holds it on until just before the sender's deadline, so that the broadcast reaches the
  sender before its fallback fires;
- or it drops the block.

A block proposal goes through one cascade of three relays or, as the specification's `R_D = 1` has
it, through two (`blend_copies`). A copy is dropped when any of its relays is the coalition's. A
block every copy of which is dropped reaches the network by the sender's fallback: the sender sees
no broadcast within `T_M = 15` rounds of the release, the round after the slot, and gossips the
block directly (Blend specification, Failure Detection and Reaction). B3's private race, the
coalition withholding, is played on the engine's timelines on the specification's Blend, 64 runs a
cell (`scripts/g6_relays.py`). The coalition's share of the relays is its share of the nodes, equal
to its stake share under the engine's uniform stakes. Growth is canonical blocks per honest win;
the closed form at `1e-9` is B5's at that growth, on the clock of the honest chain:

| α | relays | copies | coalition's share of relays | orphans ± sem | blocks by the fallback, orphaned | growth / win | race depth at 1e-3 | closed form at 1e-9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | honest | 1 | 0.250 | 0.152 ± 0.001 | – | 0.851 | 23 | 87 (1.1 h) |
| 0.25 | honest | 2 | 0.250 | 0.136 ± 0.001 | – | 0.863 | 20 | 84 (1.1 h) |
| 0.25 | hostile, holding | 1 | 0.250 | 0.164 ± 0.001 | – | 0.835 | 24 | 90 (1.2 h) |
| 0.25 | hostile, holding | 2 | 0.250 | 0.148 ± 0.001 | – | 0.849 | 20 | 87 (1.1 h) |
| 0.25 | hostile, holding to the deadline | 1 | 0.250 | 0.192 ± 0.001 | – | 0.810 | 25 | 96 (1.3 h) |
| 0.25 | hostile, holding to the deadline | 2 | 0.250 | 0.161 ± 0.001 | – | 0.841 | 21 | 89 (1.2 h) |
| 0.25 | hostile, dropping | 1 | 0.250 | 0.238 ± 0.001 | 0.579, 0.25 | 0.764 | 26 | 110 (1.6 h) |
| 0.25 | hostile, dropping | 2 | 0.250 | 0.200 ± 0.001 | 0.337, 0.22 | 0.801 | 20 | 99 (1.3 h) |
| 0.30 | honest | 1 | 0.300 | 0.143 ± 0.001 | – | 0.857 | 42 | 158 (2.2 h) |
| 0.30 | honest | 2 | 0.300 | 0.127 ± 0.001 | – | 0.872 | 37 | 151 (2.0 h) |
| 0.30 | hostile, holding | 1 | 0.300 | 0.158 ± 0.001 | – | 0.841 | 45 | 167 (2.3 h) |
| 0.30 | hostile, holding | 2 | 0.300 | 0.145 ± 0.001 | – | 0.855 | 38 | 159 (2.2 h) |
| 0.30 | hostile, holding to the deadline | 1 | 0.300 | 0.193 ± 0.001 | – | 0.811 | 43 | 186 (2.7 h) |
| 0.30 | hostile, holding to the deadline | 2 | 0.300 | 0.158 ± 0.001 | – | 0.841 | 44 | 167 (2.3 h) |
| 0.30 | hostile, dropping | 1 | 0.300 | 0.235 ± 0.001 | 0.657, 0.24 | 0.761 | 53 | 230 (3.5 h) |
| 0.30 | hostile, dropping | 2 | 0.300 | 0.203 ± 0.001 | 0.432, 0.21 | 0.797 | 48 | 198 (2.9 h) |
| 0.33 | honest | 1 | 0.333 | 0.135 ± 0.001 | – | 0.861 | 63 | 257 (3.7 h) |
| 0.33 | honest | 2 | 0.333 | 0.121 ± 0.001 | – | 0.878 | 56 | 240 (3.4 h) |
| 0.33 | hostile, holding | 1 | 0.333 | 0.154 ± 0.001 | – | 0.847 | 64 | 274 (4.0 h) |
| 0.33 | hostile, holding | 2 | 0.333 | 0.139 ± 0.001 | – | 0.859 | 67 | 259 (3.7 h) |
| 0.33 | hostile, holding to the deadline | 1 | 0.333 | 0.188 ± 0.001 | – | 0.816 | 87 | 317 (4.8 h) |
| 0.33 | hostile, holding to the deadline | 2 | 0.333 | 0.154 ± 0.001 | – | 0.848 | 57 | 273 (4.0 h) |
| 0.33 | hostile, dropping | 1 | 0.333 | 0.233 ± 0.001 | 0.705, 0.24 | 0.767 | 96 | 416 (6.7 h) |
| 0.33 | hostile, dropping | 2 | 0.333 | 0.201 ± 0.001 | 0.497, 0.21 | 0.796 | 71 | 352 (5.4 h) |

The fallback broadcasts in the clear, so it exposes the blocks' leaders. The share of honest nodes
with a block delivered by the fallback in a run's epoch, beside the Poisson value `1 − e^(−φm)` for
a share `φ` of the honest blocks delivered by the fallback and `m` blocks a node, and that value
over an epoch at `k = 2160`:

| α | copies | blocks by the fallback | honest nodes exposed in a run's epoch: engine, Poisson | in an epoch at k = 2160 |
| --- | --- | --- | --- | --- |
| 0.25 | 1 | 0.579 | 0.781, 0.780 | 0.999997 |
| 0.25 | 2 | 0.337 | 0.585, 0.585 | 0.999405 |
| 0.30 | 1 | 0.657 | 0.820, 0.818 | 0.999999 |
| 0.30 | 2 | 0.432 | 0.678, 0.675 | 0.999925 |
| 0.33 | 1 | 0.705 | 0.841, 0.840 | 1.000000 |
| 0.33 | 2 | 0.497 | 0.724, 0.724 | 0.999981 |

- **Relays that hold for the longest mixing delay** raise the honest orphan share by about two
  points, 0.135 to 0.154 against a third with one copy, and the depth at `1e-9` by 3–8 %: 257 to
  274 blocks against a third with one copy and 240 to 259 with two, 158 to 167 against 30 %.
- **Relays that hold to the sender's deadline** cost more, and expose no one, since no fallback
  fires. A block whose last relay is the coalition's reaches the network about 16 rounds after its
  slot instead of 3 to 10. Against a third the depth is 317 blocks with one copy, 23 % above
  honest relays, and 273 with two, 14 % above; against 30 %, 186 and 167.
- **The report's convention covers honest relays, not hostile ones.** It reads the growth A1
  measured with every node producing, 0.845, and gives 165 and 276 blocks against 30 % and a
  third. With one copy released at the slot, holding for the longest mixing delay stays below it
  against a third, 274, and passes it against 30 %, 167; in the specification's setup, two copies
  released a round after the slot, it passes it at both shares, 170 and 282. Holding to the
  deadline passes it at both, 186 and 317 with one copy and 176 and 299 in the specification's
  setup, and so does every deflated race (G7's engine table). The race with honest relays stays
  within it in both setups, 158 / 257 and 160 / 261. A1's growth reads a chain on which every node
  produces low, by about 5 % from sampling and by 5–10 % more from the engine's release round
  (`RATE.md` A1).
- **Relays that drop cost the most.** A copy passes three relays intact with chance `(1 − c)^3`
  for the coalition's share `c` of the relays, so a third of the relays drops a single copy of
  70 % of the honest blocks and both copies of 50 %, as the fallback column measures:
  `1 − (2/3)^3 = 0.70` and its square, 0.50. Those blocks arrive 16 rounds late and 21–25 % of
  them are orphaned. With two copies the honest orphan share rises to 0.20 and the growth per win
  falls to 0.796. Against a third the depth at `1e-9` is 352 blocks with two copies, 47 % above
  the 240 of honest relays with two, and 416 with one, 62 % above 257.
- **The fallback exposes nearly every leader.** Against a third, half of the honest blocks go out
  in the clear with two copies, and a node making `m` blocks an epoch keeps them all hidden with
  chance about `e^(−0.5m)`. The runs match the Poisson value within a point, and over an epoch at
  `k = 2160` the engine's equal-stake nodes are exposed with chance 0.9994–1.0000. The
  specification tells nodes that value privacy to disable the fallback, which would lose their
  blocks instead. The lever is the coalition's share of the relays, which the service declaration
  prices, not its stake.
- **The specification's two copies are worth 3–7 % of depth under honest relays,** more at a
  larger share: 87 to 84 blocks against 25 %, 158 to 151 against 30 %, 257 to 240 against a third.
  The engine sends one copy by default. The report keeps the one-copy growth, which understates
  honest growth and so overstates the depths under honest relays.

## G7 — the total-stake inference as a lever

The inference sets the next epoch's lottery thresholds from the occupied slots of the previous
period, `6⌊k/f⌋` slots, with a full correction (`cryptarchia-total-stake-inference.md`,
`beta = 1`). A coalition that withholds every block it wins for a period lowers the inferred stake
by its share and raises every threshold by `1/(1 − α)` for the next epoch (G4). The honest stake
alone then occupies slots at `f`, the coalition at `1 − (1 − f)^(α/(1−α))`, and the deflation
holds while it withholds, since the honest stake alone fills the slots the inference expects. The
catch-up ratio is unchanged. Under a worst case of `Δ` the delay is fixed in slots while the blocks
come `1/(1 − α)` times as fast, so `Δ = 10` s reads as `10/(1 − α)` s at the old rates and the
proven depth is B2's there. Under random delay the honest chain then runs as A1 measured `g`,
with every node producing, so in the report's convention B5's `q = α/(α + (1 − α)·g)` and its depth
are unchanged and reached sooner on a faster chain; on the engine the race's depth rises to that of
a chain on which every node produces, past the convention (below). The coalition may withhold fewer
blocks for a smaller raise, and it knows its own wins at every raise level before it chooses, while
the honest nodes' stay unknown to it: the most it gains is the largest excess of its own extra wins
over their mean along the levels, about `sqrt(2M/π)` for `M` extra wins at the full raise
(`finality_sim.inference`). Per share, at `Δ = 10` s and on the specification's Blend, with hours
before and after the deflation: under the worst case on the clock `Δ + 1/p_h`, 54.7 s a block
against a third before and 40 s after, since the honest occupancy `p_h` becomes `f`; under random
delay on the honest chain, `1/((1 − α)·g·f)` before and `1/(g·f)` = 35.5 s after, at A1's growth
(`scripts/g7_inference.py`):

| α | raise | Δ = 10 s reads as | B2's depth at 1e-9 | B5's closed form at 1e-9, A1's growth | k = 2160, random delay / worst case | extra wins an epoch | selection, Brownian / played |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 1.33 | 13.3 s | 474 → 589 (6.5 h) | 88 (1.2 → 0.9 h) | 28.4 → 21.3 h / 29.9 → 24.0 h | 1,813 | 34 / 34 (0.46% of its wins) |
| 0.30 | 1.43 | 14.3 s | 892 → 1,248 (13.9 h) | 165 (2.3 → 1.6 h) | 30.4 → 21.3 h / 31.6 → 24.0 h | 2,790 | 42 / 42 (0.45% of its wins) |
| 0.33 | 1.50 | 15.0 s | 1,510 → 2,426 (27.0 h) | 276 (4.1 → 2.7 h) | 31.9 → 21.3 h / 32.8 → 24.0 h | 3,610 | 48 / 48 (0.44% of its wins) |

- **Under the worst case the proven depth grows by 24–61 % in blocks and by at most 17 % in
  time.** Against a third B2's depth at 10 s becomes its depth at 15 s, 2,426 blocks: `k = 2160`
  holds a third only while the inference is not deflated. Against 30 % it becomes 1,248, above
  `k = 1080`. The time grows less, 23.0 to 27.0 hours against a third, since the blocks come
  faster; against a quarter it does not grow.
- **Under random delay the convention's depth is unchanged and comes sooner,** 276 blocks against
  a third in 2.7 hours instead of 4.1, but the engine's race is not: the deflation raises the
  private attack's depth from 257 to 334 blocks against a third, past the convention (below).
  `k = 2160` itself takes 21.3 hours on the honest chain instead of 31.9, and 24.0 instead of 32.8
  on the worst case's clock.
- **Choosing the raise level is worth under half a percent of the coalition's wins,** 48 wins an
  epoch against a third, and under the delay of `DESIGNS.md` H.2 the choice is blind besides.
- **The price is one period's rewards,** about 4,400 blocks against a third at `k = 2160`, and
  nothing more while it attacks, since a private attack withholds anyway.

The engine plays B3's private race against a coalition that withholds at the deflated
thresholds, every node's estimate at `1 − α` of the true stake (`finality_sim.race.withhold_tree`,
B3's settings, the specification's Blend, 64 runs a cell). Beside it are the same coalition at the
true thresholds, each case with honest relays, with relays that hold every honest block for the
longest mixing delay and with relays that hold it to the sender's deadline (G6), and every node
producing at `f` with no coalition. The growth is per honest win, on B3's equal stakes. Each cell
gives the engine's default, one Blend copy released at the slot, and then the specification's
setup, two copies released a round after the slot (`RATE.md` A1). The hours are on each chain's
own canonical rate, and with every node producing on the clock of a chain withheld from at that
growth:

| α | arm | orphans | growth / win ± sem | race depth at 1e-3 | closed form at 1e-9 |
| --- | --- | --- | --- | --- | --- |
| 0.25 | withheld | 0.152 / 0.153 | 0.851 ± 0.002 / 0.843 ± 0.002 | 23 / 21 | 87 (1.1 h) / 88 (1.1 h) |
| 0.25 | withheld, holding relays | 0.164 / 0.167 | 0.835 ± 0.002 / 0.831 ± 0.002 | 24 / 22 | 90 (1.2 h) / 91 (1.2 h) |
| 0.25 | withheld, holding to the deadline | 0.192 / 0.176 | 0.810 ± 0.002 / 0.820 ± 0.002 | 25 / 23 | 96 (1.3 h) / 94 (1.3 h) |
| 0.25 | deflated | 0.191 / 0.195 | 0.811 ± 0.002 / 0.802 ± 0.002 | 21 / 23 | 96 (1.0 h) / 99 (1.0 h) |
| 0.25 | deflated, holding relays | 0.208 / 0.210 | 0.791 ± 0.001 / 0.788 ± 0.002 | 25 / 22 | 102 (1.1 h) / 103 (1.1 h) |
| 0.25 | deflated, holding to the deadline | 0.240 / 0.222 | 0.761 ± 0.002 / 0.775 ± 0.001 | 27 / 28 | 112 (1.2 h) / 107 (1.1 h) |
| 0.25 | everyone producing | 0.192 / 0.195 | 0.808 ± 0.002 / 0.804 ± 0.002 | – / – | 97 (1.3 h) / 98 (1.3 h) |
| 0.30 | withheld | 0.143 / 0.143 | 0.857 ± 0.002 / 0.854 ± 0.002 | 42 / 35 | 158 (2.2 h) / 160 (2.2 h) |
| 0.30 | withheld, holding relays | 0.158 / 0.160 | 0.841 ± 0.002 / 0.836 ± 0.002 | 45 / 41 | 167 (2.3 h) / 170 (2.4 h) |
| 0.30 | withheld, holding to the deadline | 0.193 / 0.173 | 0.811 ± 0.002 / 0.826 ± 0.002 | 43 / 49 | 186 (2.7 h) / 176 (2.5 h) |
| 0.30 | deflated | 0.192 / 0.194 | 0.808 ± 0.002 / 0.805 ± 0.002 | 43 / 48 | 189 (1.9 h) / 191 (1.9 h) |
| 0.30 | deflated, holding relays | 0.210 / 0.215 | 0.789 ± 0.002 / 0.782 ± 0.002 | 44 / 55 | 204 (2.1 h) / 210 (2.2 h) |
| 0.30 | deflated, holding to the deadline | 0.251 / 0.231 | 0.752 ± 0.002 / 0.769 ± 0.002 | 48 / 60 | 240 (2.6 h) / 223 (2.4 h) |
| 0.30 | everyone producing | 0.192 / 0.195 | 0.808 ± 0.002 / 0.804 ± 0.002 | – / – | 189 (2.7 h) / 192 (2.8 h) |
| 0.33 | withheld | 0.135 / 0.141 | 0.861 ± 0.002 / 0.858 ± 0.002 | 63 / 62 | 257 (3.7 h) / 261 (3.7 h) |
| 0.33 | withheld, holding relays | 0.154 / 0.155 | 0.847 ± 0.002 / 0.841 ± 0.002 | 64 / 70 | 274 (4.0 h) / 282 (4.1 h) |
| 0.33 | withheld, holding to the deadline | 0.188 / 0.170 | 0.816 ± 0.002 / 0.828 ± 0.002 | 87 / 86 | 317 (4.8 h) / 299 (4.4 h) |
| 0.33 | deflated | 0.192 / 0.196 | 0.806 ± 0.002 / 0.803 ± 0.002 | 81 / 92 | 334 (3.4 h) / 339 (3.5 h) |
| 0.33 | deflated, holding relays | 0.213 / 0.218 | 0.788 ± 0.002 / 0.780 ± 0.002 | 81 / 88 | 367 (3.8 h) / 385 (4.0 h) |
| 0.33 | deflated, holding to the deadline | 0.256 / 0.233 | 0.747 ± 0.002 / 0.766 ± 0.002 | 114 / 121 | 473 (5.2 h) / 420 (4.5 h) |
| 0.33 | everyone producing | 0.192 / 0.195 | 0.808 ± 0.002 / 0.804 ± 0.002 | – / – | 329 (5.0 h) / 337 (5.2 h) |

- **After a deflation the honest chain grows as one on which every node produces.** At the true
  thresholds the chain withheld from loses fewer blocks to orphans than one on which every node
  produces, 0.135 against 0.192 against a third, and its race needs 257 blocks where every node
  producing on the same engine gives 329. Deflated, the honest stake alone produces at `f` and
  loses 0.192, and the race needs 96 / 189 / 334 blocks against 97 / 189 / 329 with every node
  producing: the growth per win differs by at most about one standard error. The specification's
  setup gives 99 / 191 / 339 against 98 / 192 / 337. A world in which every node produces at the
  raised rate, `f/(1 − α)`, is not the attack's, since it publishes the coalition's blocks as well.
- **The deflation takes the private attack past the report's convention.** The convention, B5's
  closed form at A1's growth, gives 165 / 276 blocks against 30 % / a third. It covers the race at
  the true thresholds, 158 / 257, and 160 / 261 in the specification's setup. It reads the growth
  with every node producing from eight runs on Pareto stakes and per `f`, which put that depth
  lower than this engine does (`RATE.md` A1), so it does not cover the deflated race: 189 / 334,
  and 191 / 339 in the specification's setup.
- **Relays that hold and a deflated inference together go furthest:** relays that hold to the
  sender's deadline take the deflated race to 240 / 473 blocks against 30 % / a third with one
  copy, and 223 / 420 in the specification's setup; relays that hold for the longest mixing delay
  to 204 / 367 and 210 / 385.

A cap on the correction a period raises the price. The periods and days a coalition needs to lower
the inferred stake by its share at `k = 2160`:

| cap a period | α = 0.25 | α = 0.30 | α = 0.33 |
| --- | --- | --- | --- |
| 5% | 6 periods (27 d) | 7 periods (32 d) | 8 periods (36 d) |
| 10% | 3 periods (14 d) | 4 periods (18 d) | 4 periods (18 d) |
| 20% | 2 periods (9 d) | 2 periods (9 d) | 2 periods (9 d) |

- **A cap of 5 % a period prices the deflation at 36 days of withholding against a third.** The
  cap slows the inference's response to stake that leaves by the same factor. A client that reads
  the inferred stake's fall over the last period can read the worst-case table at `Δ` divided by
  what remains, whether the stake left or was withheld; `k` is a constant and cannot.

## What the further routes change

- **G1 removes grinding within B6's model:** with a delay that spans the last sub-window and the
  contribution bound to the parent's contribution (`DESIGNS.md` H.2), the depth against a third at
  `k = 2160` is that of a nonce that is not ground within thirteen blocks as a bound and two
  sampled, rather than B7's estimate, and `k = 1620` holds a third and `k = 1080` holds 30 %
  against up to 7,800 and 450,000 delay evaluators, while the inference is not deflated, at the
  cost of a sequential computation of about a day per epoch.
- **G2 keeps the nonce's window and the recovery window long when `k` shrinks,** at the cost of a
  parameter.
- **G3 halves the worst-case depth** if Blend delivers within 2 s, and cuts it by 43 % within 4 s,
  at a cost in anonymity the Blend report prices and this study reads from it.
- **G4 finds the gain on a chain nobody withholds from already in B4's elapsed-time rule,** 39 / 53
  minutes against 30 % / a third, and a condition B4 lacked: the rule's rates must follow the
  total-stake inference, which leaves 66 / 106 minutes on such a chain and the depth rule on one
  the coalition withholds from. A rule that reads density directly adds nothing.
- **G5 bounds long-range forks built from bought keys and gives a node that starts from genesis a
  checkpoint,** at the cost of a dependence on another chain. It resolves no partition: an anchor
  shows when a block existed, not that honest nodes held it (`DESIGNS.md` H.1).
- **G6 finds the random-delay depths covered for honest relays only:** holding every honest block
  for the longest mixing delay costs 3–8 % of depth and holding it to the sender's deadline 14–23 %
  against a third, past the report's convention in the specification's setup; a third of the
  relays dropping what they carry sends
  half of the honest blocks through the sender's fallback, 16 rounds late and in the clear, and
  raises the depth at `1e-9` against a third from 257 to 352 blocks with the specification's two
  copies.
- **G7 finds the inference a lever on every worst-case figure:** a period of withholding raises
  every threshold by `1/(1 − α)`, and the proven depth at `Δ = 10` s becomes B2's at `10/(1 − α)` s,
  2,426 blocks against a third and 1,248 against 30 %, so `k = 2160` holds a third, `k = 1620` a
  third and `k = 1080` 30 % only while the inference is not deflated; a cap on the correction of
  5 % a period prices the deflation at 36 days. Under random delay the deflation takes the private
  attack's depth to that of a chain on which every node produces, 334 blocks against a third on
  the engine where the race at the true thresholds needs 257 and the report's convention reads 276,
  though it comes sooner.
