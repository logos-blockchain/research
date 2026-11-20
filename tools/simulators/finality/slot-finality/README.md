# Runs for finality counted in slots

Scripts and their stored outputs. They were run after the study's notes were written, so the
notes do not cite them. The specification pull requests logos-lips #532 and #533 cite these
figures.

| Folder | Subject |
| --- | --- |
| `floor/` | The finality floor, and what a finality window holds. |
| `nonce/` | The epoch nonce: what grinding gives a coalition, and designs that delay the nonce. |
| `dual/` | A depth rule kept beside the slot rule. Also the floor, the delivery delay, the deflated inference and several epochs, each on its own. |
| `rules/` | The rules as the specifications print them, run in a model: the switch to the Online rule, comparing forks and the uncle window. Also the restart path as a private race, and the density test over one window. |
| `epoch/` | The length of the epoch under a finality window of 10 hours: what bounds each phase from below, the epochs that suffice, and what each shorter schedule costs. `epoch/REVIEW.md` holds the proofs. |

The stored runs used the study's code at commit `741dc0b`. The runs of `rules/model/` read the
specification, logos-lips, at commit `ded1d4c6` of pull request #532.

## How to run

Install the study's environment once: `make install` in `tools/simulators/finality`. Then:

    cd tools/simulators/finality
    .venv/bin/python slot-finality/floor/floor_c.py

- A script finds the study's `src` from its own location.
- `<jobs>` is the number of worker processes. A script without it sets its own number.
- `floor/`: run from any folder. A script prints its result or writes it beside itself.
- `nonce/`: run in `slot-finality/nonce` and redirect the output, for example
  `../../.venv/bin/python online_limit.py > online_limit.out`. These scripts read and write
  arrays in the working folder. The scripts of `nonce/repro/` and `nonce/data/` run from any
  folder.
- `dual/`: run each script in the folder that holds it. It prints its result or writes it to
  `out/` below that folder.
- `rules/`: run from any folder. A script prints its result. The table gives each command.
- `epoch/`: run in `slot-finality/epoch` and redirect the output, for example
  `../../.venv/bin/python s03_gap_bound.py > out_03_gap_bound.txt`.
- Caches go to `.cache` beside the script.
- Arrays (`*.npy`, `*.npz`) are not stored here. The tables name the script that writes each.
- Times are rough. Each is that of one run on a machine with 14 cores.

## floor/

| Script | What it computes | Stored output | Time |
| --- | --- | --- | --- |
| `floor_c.py` | The floor at windows of 18, 36, 10 and 15 hours, in whole numbers and in floating point, and what follows from it. | none | 7 s |
| `a_vs_c.py <jobs>` | The wait at 1e-9 and the chance after 10, 15, 18 and 36 hours, by state: share, delay, honest stake online, inference deflated or not. | `out_a_vs_c.txt` | |
| `limits.py <jobs> [stage]` | Stage 1: the lottery's factor each window holds at 15 s. Stage 2: how far each disturbance reaches against 30 % under 18 hours. A stage `<share>:<delay>:<k1>,<k2>,...` refines a factor. | `out_limits_1.txt`, `out_limits_2.txt`, `out_limits_refine_*.txt` | stage 2: 3 min, 6 workers |
| `share_held.py <jobs>` | The share a window holds at 15 s after that share deflated the inference. | `out_share_held.txt` | 3 min, 6 workers |
| `share_held_pairs.py <jobs>` | The share a window holds through two and through three disturbances at once. | `out_share_held_pairs.txt` | |
| `third_keeps.py` | The chance that a third displaces a block after 10 and after 18 hours, with an unbiased nonce. | `out_third_keeps.txt` | 1 min |
| `caps_check.py` | The waits when a coalition holds 2^8, 2^16 or 2^24 nonces at both cut-offs. | `out_caps_check.txt` | 2.5 min |
| `chances_and_waits.py` | The study's wait bound up to 18 hours against 30 % and a third at 10 s, 10 s deflated, 12 s and 15 s, and against 0.29 and 0.295 at 10 s: the chance after 10 and 18 hours, and the wait at 1e-9 and at 1e-9 divided by 1.21, 0.82 and 0.26. 1.21 is the candidate nonce's factor for two nonces. The paper's attack succeeds 0.26 to 0.82 times as often as the bound allows (the study's `SLOTS.md`, K.7). | `out_chances_and_waits.txt`; writes `curve_*.npy` | 45 s, 6 workers |
| `least_waits.py <set> <jobs>` | The least wait at 1e-9 under the study's bound. `<set>` is `table` or `edges`. `table`: 30 % and a third by delay, after a deflation, with honest stake offline, at twice the inferred stake, and with a block every 15, 20 or 40 s, some also at 1e-9 divided by 1.21. `edges`: the limit on joining stake, as the ratio of the true active stake to the inferred, in steps of 0.001, at which the wait reaches 18 hours (30 % and a third), 10 hours (30 %) and 12.5 hours (a third). | `out_least_waits_table.txt`, `out_least_waits_edges.txt` | `table` 2 min, `edges` 1.5 min, 8 workers |
| `commit_sim.py` | The clock rule beside the tip rule: the lag, a clock step of K, and K slots with no block. | `out_commit_sim.txt` | 1 s |
| `floor_figures.py` | The eclipse a prepared fork needs, the depth rule's medians, the days a smaller side needs, the wins of a 1 % attacker, the floor in blocks on Blend. | `out_floor_figures.txt` | 1 s |
| `multi_epoch.py` | How long a race lasts under the floor when stake does not build, the building stake the floor needs within 72 hours, and a union bound over an epoch and a year. | none | 1 s |
| `inference_offset.py` | The floor against the rate the stake inference steers to. | none | 2 s |
| `miss_by_delay.py` | The chance that the whole stake misses the floor at K, by the delay of every block. | `out_miss_by_delay.txt` | 1 s |
| `alt_floor_10s.py` | A floor sized at 10 s: how often the whole stake misses it at 15 s. | none | 1 s |
| `run_printed_floor.py <spec> <K> <floor>` | Runs the floor's code as `cryptarchia-v1-protocol.md` prints it. `<spec>` is a checkout of the specification repository. | none | 1 s |
| `refcode/test_reference.py` | Tests of the reference code of the rules (`refcode/reference.py`) at K = 64,800 and a floor of 1,291: 49 tests, and 33 mutations that the tests must catch. | `refcode/run-floor-1291.txt` | 12 to 40 min |
| `refcode/check_spec_code.py <spec>` | Runs the code that the specifications print against the same tests. | `refcode/check-spec-code-1291.txt` | 1 min |
| `make_refcode_10h.py` | Builds `refcode-10h/` from `refcode/`: the same code, tests and check at K = 36,000 and a floor of 689. | `refcode-10h/` | |
| `refcode-10h/test_reference.py` | The same tests and mutations at K = 36,000 and a floor of 689. | `refcode-10h/run-floor-689.txt` | 12 to 40 min |
| `refcode-10h/check_spec_code.py <spec>` | The same check against the specifications of the ten-hour window. | `refcode-10h/check-spec-code-689.txt` | 1 min |

## nonce/

`model.py` is the model that most scripts here import. Run alone it prints a self-check against
sampling. Scripts marked "study" import the study's `src`.

| Script | What it computes | Stored output | Arrays | Time |
| --- | --- | --- | --- | --- |
| `wait_curves.py` (study) | The study's wait bound, once per share (30 %, a third) and delay (10 s, 15 s), down to 1e-42. | `wait_curves.out` | writes `wait_curve_*.npy` | 5 min |
| `survival_table.py` (study) | Branch survival and the chance that a choice is still open, beside the study's own survival. | `survival_table.out` | writes `survival_*.npy` | 2 min |
| `today_choices.py` (study) | The number of nonces a coalition of 30 % or a third can choose among at one cut-off, sampled. | `today_choices.out` | writes `today_log2G_*.npy`, `today_log2M0_*.npy` | 3 min |
| `attack_today.py` | One concrete attack with the best of n nonces: the least wait whose chance is at most 1e-9. | `attack_today.out` | reads the arrays of `today_choices.py`, writes `attack_today_*.npy` | |
| `by_share.py` | The same two sets of arrays for coalitions of 1 to 25 %. | `by_share.out` | writes `today_log2*.npy`, `attack_today_*.npy` | 9 min |
| `attack_rules.py` | The chance of each grinding attack by finality rule: depth, slot, first met, both. | `attack_rules.out` | reads `today_log2M0_*.npy`, and `review3/slot_fixed_*.npy` if present | |
| `attack_rules_v1.py` | The first version of `attack_rules.py`. | `attack_rules_v1.out` | reads `today_log2M0_*.npy`, `attack_today_*.npy` | |
| `candidate.py` (study) | The study's candidate nonce, measured with the study's functions at 10 s and at 15 s. | `candidate.out` | writes `candidate.npy` | 1 min |
| `delayed_chain.py` | Design D1, one sequential delay on today's hash-chain value: the factor per nonce and the wait, by delay and by the coalition's delay machines. | `delayed_chain.out` | reads `wait_curve_*.npy`, writes `delayed_chain_curves.npz` | 20 s |
| `delay_sizing.py` | The shortest delay of D1 whose factor a window still absorbs. | `delay_sizing.out` | reads `wait_curve_*.npy` | 25 s |
| `factor_by_delay.py` | The two-nonce factor of D1 by worst-case delay, 5 to 15 s. | `factor_by_delay.out` | | 15 s |
| `d2_fallback.py` | What the delayed chained minima (D2) fall back to when the delay gives no protection. | `d2_fallback.out` | | 2.5 min |
| `d2_fallback_windows.py` (study) | The window D2 needs in that case. | `d2_fallback_windows.out` | reads `wait_curve_*.npy` | 15 s |
| `today_states.py` (study) | Today's nonce in each disturbance and each pair: the pair factor, the wait, and the largest share that 18 and 10 hours prove. | `today_states.out` | | 22 min |
| `deflated_states.py` (study) | The two-epoch attack with an unbiased nonce: the chance after 18 and 10 hours, by delay. | `deflated_states.out` | | 8 min |
| `deflated_delay.py` (study) | The single delay after a deflated inference, at 15 s. | `deflated_delay.out` | | 4 min |
| `single_delay_cases.py` (study) | The single delay of 9 hours in each case named with "a nonce that resists grinding". | `single_delay_cases.out` | | 1.5 min |
| `online_limit.py` (study) | The least share of the honest stake online at which the window still holds, with an unbiased nonce at 10 s. | `online_limit.out` | | 25 s |
| `practice.py` | The expected gain in a coalition's own wins when it keeps the best of n nonces. | `practice.out` | | 1 s |
| `mean_gain.py` | The mean gain in blocks over all epochs. | `mean_gain.out` | | 5 min |
| `compound.py` | Grinding over several epochs: whether a ground nonce gives more nonces at the next cut-off. | `compound.out` | | |
| `honest_blocks.py` | The honest blocks that a fork published at a cut-off replaces: the honest chain's blocks in the last 600 and 3,600 slots before the cut-off, at mean rates, against 30 % and a third at 10 s and 15 s. | `honest_blocks.out` | | 1 s |
| `stake_growth.py` | How grinding moves a coalition's share of the stake over time. | `stake_growth.out` | | 1 s |
| `choices_plot_data.py` | The share of epochs in which a coalition holds at least 2^x nonces, by coalition size and delay. | `choices_plot_data.out` | writes `choices_plot_data.npy` | 13 min |
| `data/ks_curves.py` (study) | The study's wait bound on a grid of shares at 10 s, 10 s deflated, 12 s and 15 s, for waits up to 64,800 slots. Also the grinding factors per share at 10 s. | `data/ks_factors.csv` | writes `data/ks_curves.npy` | 6 min |
| `repro/k_by_nonce.py` (study) | The least window that holds 30 % and a third under each epoch-nonce design. | `repro/k_by_nonce.out` | | 7 min |
| `repro/recheck.py` (study) | Waits for today's hash chain with the pair factor taken at the wait's own delay, and the shares held at 15 s. | `repro/recheck.out` | part 3 reads `data/ks_curves.npy` | 6 min |
| `repro/accept_bias.py` (study) | The largest share a window holds with today's nonce, with the delayed nonce and with no grinding. The wait when a race meets n nonces. | `repro/accept_bias.out` | part 1 reads `data/ks_curves.npy` | 1.5 min |
| `repro/k_short_windows.py` (study) | The least window for the delayed nonce when its sub-windows shrink. | `repro/k_short_windows.out` | | 3 min |
| `repro/single_delay.py` (study) | An estimate of how long one sequential delay would have to be. | `repro/single_delay.out` | | 10 s |

`data/ks_common.py` holds the settings of `data/ks_curves.py`, `repro/recheck.py` and
`repro/accept_bias.py`.
`data/ks_factors.csv` holds the grinding factors per share at 10 s. `repro/k_by_nonce.py`,
`repro/accept_bias.py` and `../dual/nonce_shares.py` read it.
`data/ks_curves.npy` is not stored. `data/ks_curves.py` writes both files beside itself.

## dual/

`env.py` sets the path to the study and the caches. Scripts marked "study" import it first.

| Script | What it computes | Stored output | Time |
| --- | --- | --- | --- |
| `timing.py` | The time to finality under each rule (depth, slot, both, first met), as a distribution. | `out/timing.txt` | 1 s |
| `dial.py` | The rule "age at least K and n blocks follow" for n from the floor to k, and the variants C and D. | `out/dial.txt` | 1 s |
| `bounds.py <jobs> cases` (study) | The study's depth bound and wait bound side by side, for a list of cases. | `out/bounds_cases.csv` | 14 min |
| `bounds.py <jobs> grid` (study) | The same on a grid of shares at 10, 15 and 20 s. | `out/bounds_grid.csv` | 48 min |
| `table.py [extra]` (study) | The safety table in one reading for both legs, from the two files above. The stored run used `extra`. It read the grid when 26 of its 31 points at 20 s were written. With all 31 the values are the same. | `out/table.txt` | 30 s |
| `curves.py <jobs>` (study) | The wait-bound curves that `b_bound.py` reads. | none; writes `out/wait_*.npy` | |
| `b_bound.py` | A bound on rule B (first met) and on rule D (depth with a minimum age), from the wait bound alone. | `out/b_bound.txt` | 1 s |
| `nonce_shares.py <jobs>` (study) | The largest share each leg holds at 1e-9 with today's epoch nonce, at 10 s. Reads `../nonce/data/ks_factors.csv`. | `out/nonce_shares.txt`, `out/nonce_legs.csv` | |
| `cap/race.py` | The deflation attack at mean rates. | `cap/out/race.txt` | 1 s |
| `cap/speed_limit.py <jobs>` (study) | How fast the lottery may run before a window stops holding a third, by delay. | `cap/out/speed_limit.csv`, `cap/out/speed_limit.txt` | |
| `cap/cap.py` | A cap on how far the inferred stake may fall from one epoch to the next. Reads `out/speed_limit.csv`. | `cap/out/cap.txt` | 1 s |
| `cap/depth_fast.py <jobs>` (study) | The depth bound and the wait bound at a lottery 1.5 times fast, against a third, by delay. | `cap/out/depth_fast.txt` | |
| `cap/depth_fast30.py <jobs>` (study) | The same against 30 %. | `cap/out/depth_fast30.txt` | |
| `cap/b_fast.py` (study) | Rule B after a deflation. | `cap/out/b_fast.txt` | 1.5 min |
| `delay/delay_range.py <jobs>` (study) | The wait a window must cover, for a worst-case delay from 5 to 15 slots. | `delay/out/delay_range.csv` | |
| `delay/delay_table.py` | Per delay: the wait needed, the window in whole hours, and the floor. | `delay/out/delay_table.txt` | 3 s |
| `delay/delay_nonce.py <jobs>` (study) | The window by delay with the two-nonce factor of the single delay. Reads `../../nonce/factor_by_delay.out`. | `delay/out/delay_nonce.txt` | |
| `delay/typical_delay.py` | The floor when the mean delay per block is below 15 s. | `delay/out/typical_delay.txt` | 1 s |
| `epochs/epochs.py [K floor]` | The floor and the time to finality over several epochs, at mean rates. | `epochs/out/epochs_18h.txt`, `epochs/out/epochs_10h.txt` | 30 s |
| `epochs/phase_waits.py` | The building stake below which a value is not final when its phase ends. | `epochs/out/phase_waits.txt` | 1 s |
| `epochs/rate_miss.py` | The chance that the whole stake misses the floor when the lottery does not run at exactly f. | `epochs/out/rate_miss.txt` | 4 s |
| `epochs/scale_wait.py <jobs>` (study) | The wait a window must cover when the lottery runs fast by a factor, by delay. | `epochs/out/scale_wait.txt` | |
| `floor/floor.py [K]` | The slot rule with a higher floor: the floor by its targets, its cost and its benefit. | `floor/out_floor_18h.txt`, `floor/out_floor_10h.txt` | 2 s |
| `floor/floor_table.py [K]` | A summary at the floors the derivation gives for each share that withholds. | `floor/out_table_18h.txt`, `floor/out_table_10h.txt` | 1 s |
| `floor/floor_n.py K n [n ...]` | The same rows for given floors. | `floor/out_floor_1291.txt`, `floor/out_floor_689.txt` | 1 s |
| `floor/change_floor.py [delay]` | Figures for a floor sized with no stake withholding. The stored run is at 15 s. | `floor/out_change_15s.txt` | 3 s |
| `floor/change_1443.py` | The same at 10 s. | `floor/out_change_1443.txt` | 3 s |

## rules/

`model/model.py` is the model. It runs the two fork choice rules and `commit` as a checkout of
the specification prints them. `<spec>` is that checkout. It must hold the rules of pull request
#532. The cases at full scale use a window of 64,800 slots, a density window of 16,200 slots and
a floor of 1,019.

`python` is the study's interpreter, `.venv/bin/python` below `tools/simulators/finality`. Each
command is given as run in the folder of its script.

| Script | Command | What it computes | Stored output | Time |
| --- | --- | --- | --- | --- |
| `model/switch.py` | `SPEC_ROOT=<spec> python switch.py` | The switch to the Online rule with `commit` and without it. A fork that is sparse in the density window but longer overall loses under the Bootstrap rule. Without `commit`, its next block wins. | `model/switch.out` | 20 s |
| `model/comparing_forks.py` | `SPEC_ROOT=<spec> python comparing_forks.py` | The same blocks in two delivery orders. The lag at the switch. The two changes that were rejected: pruning the fork at the switch, and the Bootstrap test under the Online rule. In random trees at a window of 40 slots: the cases that depend on the order of visits and the pairs of chains that disagree, beside the depth test. It reads the depth test from commit `f28cf3e5` of `<spec>` with `git`. | `model/comparing_forks.out` | 2 min |
| `model/random_trees.py` | `SPEC_ROOT=<spec> python random_trees.py` | 9,000 random trees with random delivery orders and switch times, checked against the invariants of the rules. One of them: a candidate uncle whose parent is within the uncle window is still in the block tree. | `model/random_trees.out` | 1 min |
| `restart/private_race.py` | `python private_race.py` | The restart path as a private race at 10 s: the wait that 18 and 10 hours behave like when the fork runs for the whole window and the node's chain stopped 20 minutes earlier, by share. | `restart/private_race.out` | 3 s |
| `restart/ks_tables.py` (study) | `python ks_tables.py`, after `python ks_curves.py` in `nonce/data` | The largest share each window holds under each worst case. The waits at 25 %, 30 % and a third. The share held on the restart path, with the same race in another form. It imports the study's `src` and reads `nonce/data/ks_curves.npy` and `nonce/data/ks_factors.csv`. | `restart/ks_tables.out` | 1 min |
| `density-window/single_window.py` | `python single_window.py` | The chance that a private fork is at least as dense as the honest chain over one density window, against 30 % and a third, with no delay and at 10 s. | `density-window/single_window.out` | 7 s |

## epoch/

`REVIEW.md` states each result with its proof, and names the script and the lines of its output
that compute it. It reads the specification, logos-lips, at commit `7f3cf149` of pull request
#533 for a finality window of 10 hours, and at `ded1d4c6` for 18 hours. `common.py` holds the
constants and the bounds of the review's statements 5.3 to 5.5, which the other scripts import.
Scripts 10, 12 and 13 are not used.

`proofs/survival/SURVIVAL.md` proves the survival law behind the buffer, and
`proofs/genesis/GENESIS.md` argues the Bootstrap rule at the specification's parameters. Each
gives its scripts and their order in its own section on files. `proofs/genesis/g01_setting.py`
reads the specification from a clone of logos-lips named by `LIPS_REPO`. The review's scripts
read the proofs' outputs: run SURVIVAL's `s1` to `s3`, then `s08`, `s09` and `s11`; GENESIS's
`g01` to `g07`, then `s14`; and SURVIVAL's `s4` after `s14`.

`proofs/genesis-step2/STEP2.md` proves that GENESIS's theorem holds with a last phase of `K − 1`
slots in place of `2K − 1`, through two independent attempts and a check of both. It is not
reviewed, and nothing else in this folder uses it. Its section 5 says how to run its scripts,
after GENESIS's.

`schedule/SCHEDULE.md` states the schedule of 60 hours that the specification branch
`Bedrock-RFC-Shorter-Epoch` adopts: why the Buffer phase can go, the condition on phase 3, the
stake inference's learning rate with its simulations, and what each schedule costs. Its section
7 lists its scripts.

`schedule/CONSTRUCTIONS.md` compares that schedule, `3K + 3K`, with two constructions that keep a
Buffer phase, `2K + 2K + 2K` and `2.5K + K + 2K`, and derives the learning rate for each window.
Its section 7 lists its scripts.

| Script | What it computes | Stored output | Time |
| --- | --- | --- | --- |
| `s01_setting.py` | The constants of the windows of 10 and 18 hours, and the finality floor, with the code the specification prints and in exact integers. | `out_01_setting.txt` | 10 s |
| `s02_commit.py` | The loop of `commit` on 300,000 random chains with uncles, against the condition the review proves it computes. | `out_02_commit.txt` | 17 s |
| `s03_gap_bound.py` | The least share of the inferred stake that must build for a value read at a cut-off to be final when first used, by the gap to its first use, and the least gap by share. | `out_03_gap_bound.txt` | 1 s |
| `s04_gap_sim.py` | A simulation of the model at reduced sizes, against those bounds. | `out_04_gap_sim.txt` | 1 min |
| `s05_targets.py` | The share of targets whose race meets two epoch nonces, by the length of the epoch. | `out_05_targets.txt` | 1 s |
| `s06_inference.py` | The stake inference: its integer rule against a closed form, its noise by window, the floor under that noise, the chance per epoch that the noise passes the limits 1.094 and 1.593, and the wins a deflation costs. | `out_06_inference.txt` | 3 s |
| `s07_genesis.py` | The hypotheses of Theorems 1 and 2 of Ouroboros Genesis at the specification's parameters, and the fact about the schedule that the proof of Theorem 2 uses, by enumeration. | `out_07_genesis.txt` | 1 s |
| `s08_buffer.py` (study) | The buffer that keeps an honest block with chance `1 − 1e-9`, by state, with the study's `branch_survival` and with the proved law of `proofs/survival`. | `out_08_buffer.txt` | 2.5 min |
| `s09_epoch.py` | The least phase in each state of the `K` row, the epochs that suffice with phase 3 at `max(G*, 2K − 1)`, and what each schedule costs. It reads `out_08_buffer.txt`. | `out_09_epoch.txt` | 1 s |
| `s11_gain.py` | What a coalition of 30 % gains in blocks by choosing among nonces, by the length of the epoch. It imports `nonce/model.py` and `nonce/today_choices.py`, and reads the epochs of `out_09_epoch.txt`. | `out_11_gain.txt` | 1.5 min |
| `s14_bracket.py` | The phases and the buffer below which a rule fails in each state, the bounds on the least epoch, the wait with a later snapshot, a second computation of the necessary values in log space, and the bounds of GENESIS at a phase 3 of `2K − 1` slots. It reads `out_08_buffer.txt` and GENESIS's cached curves. | `out_14_bracket.txt` | 1 s |

## Rechecks

| Recheck | What it rechecks | Stored results |
| --- | --- | --- |
| `floor/recheck/delay-limits/recheck.py` | `floor/limits.py`, stage 2. | `results.txt` (18 min, 8 workers) |
| `floor/recheck/todays-nonce/` | `nonce/today_states.py`. `main.py [jobs]` fills the cache (10 min, 8 workers). `report.py [variant ...]`, `extra.py` and `timing.py` read it. | `out_main.txt`, `out_report_main.txt`, `out_report_alt.txt`, `out_extra.txt`, `out_timing.txt` |
| `dual/a-vs-c/recheck.py <jobs>` | Rows of `floor/a_vs_c.py`, `floor/share_held.py`, `floor/share_held_pairs.py` and `floor/floor_c.py`. | `out/recheck.txt` (2 min, 6 workers) |
| `dual/blind/blind.py <jobs>` | The same scripts' rows with two and three disturbances, and the factors of `floor/limits.py`. It did not read their outputs. | `out/blind.txt` |
| `nonce/repro/` | Five scripts from before these runs, run again. `recheck.py` recomputes the waits with the grinding factor taken at the wait's own delay. | the five `.out` files |
| `nonce/review/` | `model.py`, `delayed_chain.py`, the wait curves and `attack_today.py`. Run `check2.py`, `check3.py` and `check5*.py` in `nonce`, as `python review/check2.py`. They read the arrays those scripts write. | `check5b.out` |
| `nonce/review2/` | `d2_fallback.py`, `d2_fallback_windows.py` and `practice.py`. Run in `review2`. `gen.py` writes `pair_*.npy`. `shift.py` reads them: run it in `nonce` with `PYTHONPATH=.`. | `gen.out`, `shift.out` |
| `nonce/review3/` | `attack_rules.py`. Run in `nonce`, as `python review3/slot_check.py`. `slot_check.py` writes `review3/slot_fixed_*.npy`. | `depth_A.out`, `depth_B.out`, `slot_check.out`, `stretch_check.out`, `misc_check.out` |
| `nonce/review4/` | `compound.py`. | `indep.out`, `brute_full.out`, `orig_cap6.out` |
| `nonce/review5/recheck.py` | `mean_gain.py`. | none |
| `nonce/review6/recheck.py` | `stake_growth.py`. | none |
| `dual/review/` | `bounds.py` (`spot.py`), `b_bound.py` (`bbound_check.py`), `timing.py` and `dial.py` (`timing_check.py`), and the count of the depth bound (`count_check.py`, `count_check2.py`, `small_k.py`, `stored_check.py`). `renv.py` sets the path to the study. `bbound_check.py` reads `out/wait_*.npy`. `stored_check.py` reads the study's `runs/b2/curves.csv`, which `make b2` writes. | `spot.txt`, `bbound_check.txt`, `timing_check.txt`, `count_check.txt`, `count_check2.txt` |
| `dual/cap/review/` | The scripts of `dual/cap/`. `waits.py <jobs>` writes `curve_*.npy`, which `bcheck.py` reads. | `arith.txt`, `waits.txt`, `depth.txt` |
| `dual/epochs/review/` | `dual/epochs/epochs.py`. `rv.py` is a second model. `check.py [K floor]`, `search.py [K floor]` and `extra.py` use it. `extra.py` adds the longest stretch of late finality when a coalition tunes how much it withholds, a coalition that withholds in the same part of every epoch, and the chance that the floor is missed at K when the lottery runs below `f`. | `c18.txt`, `c10.txt`, `s18.txt`, `s10.txt`, `extra.txt` (9 s) |
| `dual/floor/review/` | `dual/floor/floor.py`. | `check_out.txt`, `occ_out.txt` |
| `dual/floor/review-1291/rc.py` | The floors 1,291 and 689, and the figures of `dual/floor/change_floor.py` and `dual/floor/floor_n.py`. | `out.txt` |
