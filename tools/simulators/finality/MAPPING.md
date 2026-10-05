# What depends on `k`, and what each route changes

Phase A2 and A3 of `PLAN.md`. Specifications are read at `logos-lips` `47a73cdc`
(`docs/blockchain/raw/`), the node at `logos-blockchain` `4e0405d51`, testnet 0.3.0 at
`865df42ba`. Every number below is printed by `scripts/mapping_numbers.py`.

## 1. The rules that read `k`

| role | specification | node | what `k` sets |
| --- | --- | --- | --- |
| finality | `cryptarchia-v1-protocol.md`: Latest Immutable Block, Chain Maintenance, Commit, Fork Pruning, Block Header Validation rule 8 | `consensus/cryptarchia-engine/src/lib.rs`, `State::lib` | `B_imm` is the `k`-deep block of the node's own chain under the Online rule. Forks that diverge below it are pruned, and a block at or below its height is rejected. Under the Bootstrap rule `B_imm` is frozen. |
| Online fork choice | `fork-choice.md`, `maxvalid-mc` | `maxvalid_mc` | A fork deeper than `k` is ignored: `k` is the largest rollback. |
| Bootstrap fork choice | `fork-choice.md`, `maxvalid-bg`; `cryptarchia-v1-bootstr-sync.md` | `maxvalid_bg`; `services/chain/chain-service/src/bootstrap/state.rs`, `choose_engine_state` | A fork deeper than `k` is decided by block density over `s_gen = ⌊k/4f⌋` slots. |
| epoch | protocol, Epoch Schedule and Epoch State Pseudocode | `consensus/cryptarchia-engine/src/time.rs` | An epoch lasts `10⌊k/f⌋` slots, in phases of 3, 3 and 4 `⌊k/f⌋`. The nonce is fixed `6⌊k/f⌋` into the previous epoch, and the stake inference counts that epoch's first `6⌊k/f⌋` slots. |
| uncle window | protocol, note under Uncle Selection | — | `W ≤ ⌊0.6k⌋`. |

A node chooses between the two fork-choice rules only at startup. It takes the Bootstrap rule when
its `B_imm` is genesis or a checkpoint, when it was offline longer than `T_offline` (20 min), or on
the operator's flag (`cryptarchia-v1-bootstr-sync.md`, Setting the Fork Choice Rule;
`choose_engine_state`, whose source carries a TODO for further criteria). The specification then
holds the Bootstrap rule for `T_boot` = 24 h. The node's default for that period is 1 h.

## 2. What reads `k` through the epoch

Blend dropped sessions in revision 1.1.0 (2026-06-22), so these protocols run on consensus
epochs, and `k` times them.

- **SDP.** Services read the registry of `current_epoch - 2`. A declaration serves from epoch
  `e+2`, and a withdrawal takes effect at `e+2` (`bedrock-service-declaration-protocol.md`; node:
  `SNAPSHOT_FINALIZATION_DELAY = Epoch::new(2)`).
- **Blend.** The epoch is written as `E = 648000` rounds (`blend-protocol.md`, Global Parameters).
  Quotas, keys, nullifier caches and rewards are per epoch.
- **Proof of work.** `EXPECTED_BLOCKS_PER_EPOCH: uint64 = 21_600`, commented `N_b = 10 k`
  (`proof-of-work.md`).
- **Rewards.** Leader vouchers join the voucher tree in the first block of the next epoch
  (`bedrock-anonymous-leaders-reward.md`), and service rewards are paid at epoch boundaries.
- **Proof of leadership.** A note is eligible once it was in the note set at the start of the
  previous epoch (protocol, Eligible Leader Notes).
- **Storage market.** The price is fixed within a timeframe, an epoch for permanent storage
  (`storage-markets.md`).

## 3. Who waits for finality

In the specifications:

- **Mantle.** A Zone crediting a deposit waits for finality or uses the atomic transfer. Channel
  parent references exist because "Cryptarchia has long finality times".
- **Cross-channel messaging** (`template-cross-channel-messaging.md`). Asynchronous messages wait
  for finality, and "Channels can choose a specific probability threshold or wait for finality to
  achieve a 100% guarantee".
- **Architecture overview.** "Block finalizes after being buried by 2160 blocks".

In the node, the LIB is the `k`-th ancestor of the node's own tip. Its consumers:

- **Wallet.** Prunes state at the LIB. Leader-claim reservations expire after `k` immutable blocks
  (`services/wallet/src/states.rs`).
- **SDP service.** Stops tracking an activity message once it is final in the LIB
  (`services/sdp/src/lib.rs`).
- **Zone SDK and `logos_sql`.** Finalize transactions, deposits and channel notes when the LIB
  advances (`zone-sdk/src/sequencer/block_fetch.rs`).
- **HTTP and C APIs.** `/cryptarchia/lib-stream`, immutable-only block queries, and `lib` in
  `/cryptarchia/info`.
- **Storage and sync.** Both prune at the LIB.

The mempool, proof-of-work claims, the leader and Blend membership work from the tip. The APIs
expose two levels, tip and LIB; no confirmation depth exists anywhere in the node. `k` is a
deployment setting, not committed in genesis. No configuration sets 2160: testnet 0.3.0 uses 120
at `f = 1/30`, and the embedded default is 30 at `f = 1/20`.

## 4. How the `k`-sized quantities move with `k`

At `f = 1/30` and 1 s slots:

| quantity | `k` = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| `k` blocks with no forks | 18.0 h | 9.0 h | 3.6 h | 1.8 h | 1.0 h |
| `s = 3⌊k/f⌋` | 54.0 h | 27.0 h | 10.8 h | 5.4 h | 3.0 h |
| epoch, `10⌊k/f⌋` | 180 h | 90 h | 36 h | 18 h | 10 h |
| nonce fixed ahead of use, `4⌊k/f⌋` | 72.0 h | 36.0 h | 14.4 h | 7.2 h | 4.0 h |
| Bootstrap density window `s_gen` | 4.50 h | 2.25 h | 0.90 h | 0.45 h | 0.25 h |
| blocks per epoch, `10k` | 21,600 | 10,800 | 4,320 | 2,160 | 1,200 |
| inference window, occupied slots, `6k` | 12,960 | 6,480 | 2,592 | 1,296 | 720 |
| inference noise per epoch | 0.90 % | 1.27 % | 2.01 % | 2.85 % | 3.82 % |
| offline grace margin, `(k/f)/T_offline` | 54.0 | 27.0 | 10.8 | 5.4 | 3.0 |
| SDP lag, two epochs | 360 h | 180 h | 72 h | 36 h | 20 h |

The inference noise is the TSI report's measured ±0.9 % per epoch at `k = 2160` (Appendix B),
scaled as `1/√T` with the window `T = 6⌊k/f⌋`. The offline grace period rests on an attacker being
unable to grow a `k`-block fork within it (`cryptarchia-v1-bootstr-sync.md`, Offline Grace Period).
`W = 12` stays within `⌊0.6k⌋` for every `k ≥ 20`. At `k = 120` the Bootstrap density window is
too short to hold a quarter of the stake (`SETTLEMENT.md` B5).

## 5. The self-healing horizon (A3)

When a split ends, the side that loses rolls back every block it made during the split. A side
holding stake share `σ` occupies a slot with probability `1 − (1 − f)^σ` until the inference
adapts, so it makes `k` blocks in `k / (1 − (1 − f)^σ)` slots:

| side's share of stake | `k` = 2160 | 1080 | 432 | 216 | 120 |
| --- | --- | --- | --- | --- | --- |
| 0.5 | 35.7 h | 17.8 h | 7.1 h | 3.6 h | 2.0 h |
| 0.3 | 59.3 h | 29.6 h | 11.9 h | 5.9 h | 3.3 h |
| 0.2 | 88.8 h | 44.4 h | 17.8 h | 8.9 h | 4.9 h |

Past the horizon, a node on the losing side holds a `B_imm` past the divergence point. Neither
fork-choice rule reorganises below `B_imm`, and a restart keeps it, so a restart does not return
the node. Only a re-sync from genesis or from a checkpoint does (`SETTLEMENT.md` B5). The two
routes the owner set for B5 (PLAN.md Q8) act here. Shorter horizons accept that operators re-sync
nodes after shorter splits. Automatic recovery has the node compare a deep fork by density by
itself.

## 6. What each route changes

- **A smaller `k`, with the epoch tied to it (L2, as today).** Everything in §2 and §4 shrinks in
  proportion: the epoch, SDP's lag, Blend's epoch, the proof-of-work epoch, reward and voucher
  periods, the storage-price timeframe. The inference loses precision as `1/√k`, and the
  per-epoch voucher anonymity set falls with the blocks per epoch. The offline grace margin and
  the self-healing horizon fall linearly. `k` cannot go below 20 without retuning `W`.
- **A smaller `k`, with the epoch decoupled from it (L2, B5).** §2 and the inference keep their
  periods. What still shrinks is the largest rollback, the Bootstrap density window, the offline
  grace margin and the self-healing horizon. The epoch phases that exist to let the stake snapshot
  and the nonce settle (`k` deep before use) would rest on whatever finality notion is in force;
  the phase that guarantees an honest nonce contribution rests on chain quality, not on finality
  (PLAN.md §6.4).
- **A faster notion beside `k` (L1, L5, L6).** The consumers of §3 gain at once if they read the
  new notion; each would need a third level between tip and LIB. §2 gains nothing unless its rules
  are rewritten against a finalized block, as SDP's `current_epoch - 2` could be. A certified block
  must never be reverted, so `B_imm` would become at least the latest certified block in commit,
  pruning and rule 8. If certification arrives sooner than the uncle window (`W·f⁻¹` = 360 slots),
  pruning at it would discard uncle candidates the inference still needs.
