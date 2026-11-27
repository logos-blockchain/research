# Uncle references to any fork block

Scripts, data and stored outputs behind the figures of the Cryptarchia RFC "Reference any fork block as an uncle". The RFC
is `docs/blockchain/raw/rfc/RFC-558-cryptarchia-reference-any-fork-block-as-an-uncle.md` in logos-lips, on the branch
`docs/cryptarchia-uncle-any-depth`. The change lets a block name any block off its chain whose fork point lies within
`W = 240` block intervals, by block ID and slot. A missing or wrong entry no longer makes a block invalid: the fork choice
considers only chains whose entries the node has checked.

| Folder | Subject |
| --- | --- |
| `sim/` | The per-node simulator `../tsi-sim-pernode` with the rules of the change as a patch: the inferred stake by window against a selfish coalition, the waits for uncles, `W = 240` without a coalition, and the overshoot under the integer arithmetic of the Total Stake Inference. |
| `testnet/` | 14 days of testnet block trees: the share of occupied slots each rule counts, the depth of the forks, how many proposers hold a fork block, and the adoption rule on a network that spreads blocks as the testnet does. |
| `models/` | Small models of the chain maintenance, the downloads, the count and what uncle lists reveal. |
| `spec/` | Runs of the reference code that the specifications print. |

The stored runs used the simulator of this branch with `sim/id-only.diff`. The scripts of `spec/` read logos-lips at
commit `ce273c14`.

## How to run

- `sim/`: install the simulator's environment once (`make install` in `../tsi-sim-pernode`). `sh run_sweeps.sh [label ...]`
  builds a patched copy of the simulator in `work/` and writes `results/<label>.parquet`. Without labels it runs all
  nine sweeps: 84 minutes on 14 cores that other jobs shared. A summary runs with the simulator's interpreter and the patched `src`:

      PYTHONPATH=work/src ../../tsi-sim-pernode/.venv/bin/python wait_summary.py results/healthy-w12.parquet

- `testnet/` and `models/`: `python3 <script>.py > out_<script>.txt`, from any folder. Only `models/passive_leak.py`
  needs a package beyond the standard library (numpy).
- `spec/`: `python3 <script>.py <logos-lips>/docs/blockchain/raw/<document>.md`. The table names the document.
- Times are those of one run on a machine with 14 cores, while the sweeps ran.

## Figures of the RFC

| RFC section | Figure | Script | Stored output |
| --- | --- | --- | --- |
| A missing uncle delays adoption | each earlier wording's failure | `models/adopt_mut.py`, `models/adopt2.py`, `models/option_ab.py` | `out_adopt_mut.txt`, `out_adopt2.txt`, `out_option_ab.txt` |
| | eight wins, 21,844 downloads against 4 | `models/verdicts2.py` | `out_verdicts2.txt` |
| | forks kept for `k/f` slots | `models/fast_growth.py` | `out_fast_growth.txt` |
| | groups more than `k` blocks apart in up to 9 of 12 runs, none under the drafted rule | `models/verdicts2.py` | `out_verdicts2.txt` |
| The window | the table | `sim/window_summary.py` | `sim/out_window_summary.txt` |
| | extra forks and ledger states kept, share of `k` | `models/window_costs.py` | `out_window_costs.txt` |
| | 1.0011 against 0.9860 at ρ 1.76 | `sim/healthy_w240.py` | `sim/out_healthy_w240.txt` |
| | half of the blocks off the chain; 0.613 counted today | `testnet/window_real.py` | `out_window_real.txt` |
| | 37 % of the orphans three or more blocks deep | `testnet/forkage.py` | `out_forkage.txt` |
| | 0.915 to 0.934 at `W = 240`, 0.861 to 0.882 at 144 | `testnet/select_rules.py` (p = 0.9), `testnet/select_rules_low.py` (p = 0.5) | `out_select_rules.txt`, `out_select_rules_low.txt` |
| | the states agree up to `4⌊k/f⌋ + 2` slots | `models/rules.py` | `out_rules.txt` |
| | up to 400 blocks for one block's entries | `models/window_costs.py` | `out_window_costs.txt` |
| Uncle selection and leader privacy | a block handed to one node alone is never named | `spec/planted.py` | `out_planted.txt` |
| | 79,984 proposals: 0.24 to 1.51 % without the wait, none with it | `models/passive_leak.py 5000` | `out_passive_leak.txt` |
| | 0.828 to 0.925 for the whole branch, 0.936 for any block held | `testnet/select_rules.py`, `testnet/select_rules_low.py` | as above |
| | the leaks that remain: two, three and one win | `spec/withheld.py` | `out_withheld.txt` |
| | three tries one second apart remove the first form | `models/orphan_spread.py` | `out_orphan_spread.txt` |
| | 0.91 within 7,200 slots against 0.11 within 360 | `models/window_costs.py` | `out_window_costs.txt` |
| Downloads | `2M(M+1)` downloads, 5,100 at `M = 50` | `models/downloads.py` | `out_downloads.txt` |
| | `α(k + W)` = 720 blocks against `αW` = 72 | `models/branch_cost.py` | `out_branch_cost.txt` |
| | about 690 peer requests instead of 5,543 | `models/synced_load.py`, `models/synced_load_capped.py` | `out_synced_load.txt`, `out_synced_load_capped.txt` |
| | 99 % hold an honest uncle within 3 s | `models/pull.py` | `out_pull.txt` |
| | 600 honest uncles in 5.6 minutes behind 2,592 fake entries, against 171 | `models/lagging.py` | `out_lagging.txt` |
| | a fork block held by about 9 % of the proposers | `testnet/hold_fit.py` | `out_hold_fit.txt` |
| | the stop at the window cuts off no valid uncle | `models/stop_rule.py`, `spec/sync_code.py` | `out_stop_rule.txt`, `out_sync_code.txt` |
| The count | chains share the count unless fewer than `k` blocks fall in `4⌊k/f⌋ − W/f` slots | `models/gap_bound.py`, `models/tsi_views.py` | `out_gap_bound.txt`, `out_tsi_views.txt` |
| | a higher count gives a higher estimate | `models/monotone.py` | `out_monotone.txt` |
| | 1.0098 to 1.0107 under the truncated `f` | `sim/wait_summary.py` on `healthy-w12-depth-truncated` (any depth, delays 4 to 16 s) | `sim/out_wait_summary.txt` |
| Costs | 20 to 50 % of the chain's blocks hold an entry | `sim/wait_summary.py` on `healthy-w12` | `sim/out_wait_summary.txt` |
| | waits in half to all epochs without the broadcast condition, in none of 1,823 with it | `sim/wait_summary.py` on `healthy-w12-depth` (any depth: 46 to 99 % of the epochs) and `healthy-w12` | `sim/out_wait_summary.txt` |
| | orphans 50.5 to 51.3 % and 54.5 to 63.4 % | `testnet/gate_240.py` | `out_gate_240.txt` |
| | 490 to 700 fork blocks for a node that syncs | `sim/wait_summary.py` on `healthy-w12` (`fork_blocks_per_k`, delays 2 and 4) | `sim/out_wait_summary.txt` |
| | 16,908 and 18,192 bytes; 19,318 and 18,034 | `models/sizes.py` | `out_sizes.txt` |
| Details: sizes and test vectors | the vectors | `spec/vectors.py`, `spec/vectors_new.py` | `out_vectors.txt`, `out_vectors_new.txt` |

Three figures differ slightly from the stored runs:

- `testnet/select_rules.py` runs three seeds and gives 0.916 and 0.829 at p = 0.5. The RFC's 0.915 and 0.828 are the
  four seeds of `select_rules_low.py`. Both lie within one standard error, 0.001.
- `models/gap_bound.py` gives 10⁻²⁶⁸ at half the target growth with `W = 240`. The RFC's 10⁻²⁹² is the value at
  `W = 12`, the window when it was computed. Either way the count is shared unless growth falls below about a quarter of
  the target.
- `sim/wait_summary.py` gives 19 % of blocks with an entry at a Blend delay of 2 s, 48 % at 16 s and 66 % at 32 s
  (ρ 1.76).

## sim/

`id-only.diff` adds the rules of the change to the simulator. Each is chosen by an environment variable:

- `IDONLY_WAIT=1`: a block waits until the node holds every block that its entries name, with their branches. The
  simulator records how many nodes wait and for how long.
- `IDONLY_BROADCAST=1`: a proposer names a fork block only if every block of its branch reached it by broadcast. Its own
  blocks count once their broadcast came back to it.
- `IDONLY_TM=<s>`: and only `<s>` seconds after it received each of them.

In these two conditions the simulator is stricter than the drafted rule. Its wait counts from receipt, not from the
uncle's slot, and a branch block that the chain references does not count unless it came by broadcast. Every fork block
that passes them in the simulator passes the drafted conditions too. Any depth is the simulator's `uncle_depth: 0`, with
the window measured to the fork point (`uncle_window_anchor: parent`).

Every sweep, rerun from `id-only.diff` on this branch, matches the results stored on 2026-11-20 and 2026-11-24
row for row, in every column.

| Label | Configuration | Rules |
| --- | --- | --- |
| `healthy-w12` | `k = 2160`, no coalition, any depth, `W = 12`, Blend delays 2 to 32 s | wait, broadcast, 15 s |
| `healthy-w12-tm0` | the same | wait, broadcast |
| `healthy-w12-depth` | the same, first fork block (depth 1) against any depth | wait |
| `healthy-w12-depth-truncated` | the same, with `f` truncated to thousandths as the inference does | none |
| `healthy-w240` | `k = 2160`, no coalition, any depth, `W = 240`, delays 8 and 32 s, 10 replicates | wait, broadcast, 15 s |
| `coalition-fork-point` | `k = 256`, selfish coalition of 0, 0.2 and 0.3, any depth, `W` = 12 to 144 to the fork point | wait, broadcast, 15 s |
| `coalition-own-slot` | the same, `W` = 12 and 24 measured to the uncle's own slot | wait, broadcast, 15 s |
| `coalition-today` | the same, the first fork block only, `W = 12` (today's rule) | none |
| `coalition-w240` | the same, `W` = 144 and 240 to the fork point | wait, broadcast, 15 s |

| Script | What it computes | Stored output |
| --- | --- | --- |
| `run_sweeps.sh [label ...]` | Builds the patched simulator and runs the sweeps. | `results/` (not stored) |
| `window_summary.py <fork-point> <own-slot> <today> [<w240>]` | The inferred stake over the true stake by window and coalition, with the paired gap to `W = 12` and the uncounted honest slots by depth. Drops replicates whose coalition misses its share by more than 0.01. | `out_window_summary.txt` |
| `healthy_w240.py <healthy-w12> <healthy-w240>` | `W = 12` against `W = 240` without a coalition, paired by replicate. | `out_healthy_w240.txt` |
| `wait_summary.py <results>` | Without a coalition: the inferred stake, the blocks with an entry, the blocks that make nodes wait, the epochs with a wait, and the fork blocks per `k` chain blocks. | `out_wait_summary.txt`, one section per sweep |

## testnet/

`data/` holds what the scripts read. It was downloaded from a testnet block explorer's API on 2026-11-24 and covers the 14
days before, with `k = 1000`.

- `tree.json.gz`: 56,714 blocks with their ID, parent, slot, height, transaction count and the IDs they reference
  (`uncle_in`). `header_only` marks a block that the explorer knows only from a reference.
- `forks.json.gz`: one record per fork point of the 14 days: its branches and blocks, how many of the watched peers
  followed a losing branch, and how soon they left it.
- `sample.json`: 210 blocks, by kind: fork blocks of depth 1 without children, with children, deeper fork blocks, and
  canonical blocks.
- `spread.json.gz`: for each of these blocks and each watched peer, when the peer first followed the block on its own
  chain. Each peer ID is replaced by a number. IP addresses, client versions and leader keys are removed.

| Script | What it computes | Stored output | Time |
| --- | --- | --- | --- |
| `base.py` | Loads the tree and finds the canonical chain, the fork points and the depths. Imported by the others. | | |
| `window_real.py` | The share of occupied slots that each rule counts, by window, if every proposer holds every fork block at once or only when its branch stops growing. Today's real share. | `out_window_real.txt` | 10 s |
| `forkage.py` | The forks of the last 7 days: slots from fork point to orphan, depths, branch durations, the fewest canonical blocks in `4k/f − W/f` slots, and references to blocks the explorer never got. | `out_forkage.txt` | 10 s |
| `hold_fit.py` | How many proposers hold a fork block, fitted from which orphans the chain referenced, and the counted share with that holding. | `out_hold_fit.txt` | 30 s |
| `bcast_share.py` | How soon after its slot a peer follows a block, among the peers that follow it within 600 s. | `out_bcast_share.txt` | 5 s |
| `select_rules.py [seeds]` | The selection conditions compared on the tree, with 150 persistent nodes: none, the whole branch by broadcast, the branch by broadcast or referenced (drafted), the block alone. | `out_select_rules.txt` | 45 s |
| `select_rules_low.py` | The same at `W` = 144 and 240 with four seeds, broadcast shares 0.3 to 0.7, and longer waits. | `out_select_rules_low.txt` | 50 s |
| `select_rules_wait.py` | The drafted condition at `W = 240`: no wait, 15 s after receipt, and 15 slots after the uncle's slot. | `out_select_rules_wait.txt` | 20 s |
| `select_rules_check.py` | Checks of `select_rules.py`: with every block received by broadcast the conditions agree, and with none only first fork blocks count. | `out_select_rules_check.txt` | 20 s |
| `gate_sim.py` | The adoption rule on a 60-node network where half of the producers reach about 9 % of the nodes by broadcast. Imported by `gate_240.py`. | | |
| `gate_240.py` | Orphans and waits with and without the adoption rule at `W = 240`, by how often and how widely a node asks for a missing uncle. | `out_gate_240.txt` | 10 s |

## models/

`adopt.py` is a toy network with the drafted chain maintenance: adoptable chains, step 8, pruning and uncle downloads. A
lottery win is a coin flip. Several models import it.

| Script | What it computes | Stored output | Time |
| --- | --- | --- | --- |
| `adopt.py` | Divergence, a node cut off for more than `k` blocks, a fresh node, forged entries, a coordinated restart, uncles around the latest immutable block. | `out_adopt.txt` | 20 s |
| `adopt_mut.py` | Each rule of `adopt.py` broken in turn: the depth rule, step 8 and pruning, the downloads, the block tree across a restart. | `out_adopt_mut.txt` | 10 s |
| `adopt2.py` | The drafted adoption rule against the first wording, which counted the `k` descendants on the chain: capture by a fork without entries, and a halt after a lost uncle. | `out_adopt2.txt` | 20 s |
| `option_ab.py` | A block that enters the tree only once its uncles are held and valid, against the drafted rule: syncing, rejoining, and an uncle lost everywhere. | `out_option_ab.txt` | 20 s |
| `verdicts.py` | Three treatments of a reference: the drafted one, a wrong entry that condemns its block for good, and waiting outside the tree. | `out_verdicts.txt` | 1 min |
| `verdicts2.py` | The wrong-entry attack with an uncle that stays private, and the downloads one attacker block causes. | `out_verdicts2.txt` | 2 min |
| `fast_growth.py` | Waiting outside the tree when the chain grows faster than the target. | `out_fast_growth.txt` | 10 s |
| `rules.py` | Property checks on random trees: the retention bound and the slots up to which the epoch states agree. | `out_rules.txt` | 15 s |
| `checkpoint_bound.py` | Which checkpoints let a new node check every entry it must check. | `out_checkpoint_bound.txt` | 25 s |
| `checkpoint.py` | How long a node that starts from a checkpoint takes to follow the honest chain, by checkpoint depth. | `out_checkpoint.txt` | 4.5 min |
| `tsi_views.py [seeds]` | Whether the Total Stake Inference differs between nodes or between competing chains. | `out_tsi_views.txt` (5 seeds) | 20 s |
| `gap_bound.py` | The chance that fewer than `k` blocks fall in the last `4⌊k/f⌋ − W/f` slots, by chain growth. | `out_gap_bound.txt` | 1 s |
| `monotone.py` | Whether the inferred stake never falls as the count grows, under the integer algorithm. | `out_monotone.txt` | 1 s |
| `window_costs.py` | What `W` costs: forks kept, the blocks one block's entries can name, and the chance that a marked node proposes in time. | `out_window_costs.txt` | 1 s |
| `passive_leak.py [blocks]` | What an honest proposal's uncle list reveals about its proposer, with no wait, a wait after receipt, and a wait from the uncle's slot. 400 nodes, Blend with three hops. | `out_passive_leak.txt` (5,000 blocks) | 70 s |
| `orphan_spread.py` | A block broadcast while one node holds its parent: how many nodes hold it after one to four tries. | `out_orphan_spread.txt` | 25 s |
| `pull.py` | How fast a missing uncle spreads by download, with and without a retry every second. | `out_pull.txt` | 30 s |
| `downloads.py` | Downloads caused by `M` versions of one block with fake entries, without the download limits. | `out_downloads.txt` | 5 s |
| `branch_cost.py` | Blocks one entry makes a node validate, with and without the stop at the window. | `out_branch_cost.txt` | 10 s |
| `synced_load.py` | Peer requests per synced node for each win an attacker gives up: a retry every `T_round` against a doubling wait. | `out_synced_load.txt` | 5 s |
| `synced_load_capped.py` | The same with the drafted cap of `f⁻¹` slots on the wait. | `out_synced_load_capped.txt` | 5 s |
| `lagging.py` | A node behind the tip fetching honest uncles behind fake entries: without an order, with the chain of `best_tip()` first, and with a doubling wait. | `out_lagging.txt` | 1 min |
| `stop_rule.py` | The stop at the window on random trees: no valid uncle cut off, no block outside the window added. | `out_stop_rule.txt` | 30 s |
| `tampered_copy.py` | Which nodes may name a block after a tampered copy of its proposal, under two readings of `broadcast`. | `out_tampered_copy.txt` | 10 s |
| `sizes.py` | The sizes that follow from an entry of 361 and of 40 bytes. | `out_sizes.txt` | 1 s |

## spec/

Each script extracts the code from the document it is given and runs it.

| Script | Document | What it checks | Stored output | Time |
| --- | --- | --- | --- | --- |
| `selection_code.py` | `cryptarchia-v1-protocol.md` | Uncle Selection against a brute-force oracle on 300 random trees. | `out_selection_code.txt` | 10 s |
| `sync_code.py` | `cryptarchia-v1-bootstr-sync.md` | Listening, downloading and uncle downloads on eight small cases. | `out_sync_code.txt` | 1 s |
| `planted.py` | `cryptarchia-v1-protocol.md` | Whether a proposal names a block handed to its proposer alone, under four selection conditions. | `out_planted.txt` | 10 s |
| `withheld.py` | `cryptarchia-v1-protocol.md` | Whether a proposal differs from other nodes' after an attacker's block reached one node alone, in five forms. | `out_withheld.txt` | 10 s |
| `vectors.py` | `cryptarchia-v1-protocol.md` at master `3b3298f5` | The block vectors of Cryptarchia 1.2.5, and the entries and `body_root` of the new vector. | `out_vectors.txt` | 1 s |
| `vectors_new.py` | `cryptarchia-v1-protocol.md` | Every `body_root` of the drafted vectors follows from the table's inputs. | `out_vectors_new.txt` | 1 s |

`planted.py` and `withheld.py` set `T_M` to the drafted 15 slots. Their trees place the attacker's blocks far enough back
that the wait does not decide the result.
