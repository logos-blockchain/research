# Cryptarchia

The Logos blockchain's consensus protocol, modelled rule by rule from its specification, with k-deep finality proven for every adversary and quantified under a random-oracle lottery.

**Sources:**
- Specification: `logos-lips` at `2cfdf03b`, `docs/blockchain/raw/`:
  - `cryptarchia-v1-protocol.md` rev 1.2.3;
  - `fork-choice.md` rev 1.1.0;
  - `cryptarchia-total-stake-inference.md` rev 1.1.0;
  - `cryptarchia-proof-of-leadership.md`;
  - `cryptarchia-v1-bootstr-sync.md`;
  - `bedrock-genesis-block.md`.
- Implementation used to settle ambiguities: `logos-blockchain` at `c4c86be18`.

## Layout

| Folder | Role | Main results |
|---|---|---|
| `Spec/` | **The protocol as specified**, as computable definitions: parameters, the lottery threshold, total stake inference, chains, fork choice, epoch states, honest nodes, executions (time, delivery, adversary). | `Config.spec` and its derived constants, checked by `decide`. |
| `Settle/` | **Settlement combinatorics** on proof-of-stake trees, after Gaži, Ren and Russell (*Practical Settlement Bounds for Longest-Chain Consensus*, CRYPTO 2023): reach and margin recurrences, upper bounds only. | `bnd_sound`, `settled` |
| `Proof/` | **Deterministic safety.** Every execution builds a valid PoS tree, and finality holds on a good event of the lottery string alone, over any number of epochs. | `agree_now`, `bimm_final`, `final_bimm`, `final_bimm_epochs`, `time_final_epochs` |
| `Prob/` | **The probability layer.** It covers the lottery as a random oracle and worst-case kernels over a band of slot laws. It proves the settlement bound, the band from stake fractions, and that the stake estimate stays in band. | `final_bimm_ro`, `lottery_law_epoch`, `slotBand_of_stake`, `prob_out_of_band`, `final_bimm_ro_tsi3` |
| `Prob/Certs/` | **A certified number** at the specification's parameters (library `CryptarchiaCerts`). | `E20D11.certified_tsi` |

## The deterministic layer

- **Executions.** An execution is a list of events (tick, delivery, block creation) from genesis. Honest nodes run the online rule. They may crash and stay offline, and the guarantees hold for nodes online at the time. Delivery is not assumed: an honest block not delivered within Δ counts as adversarial. Fork-choice tip order is arbitrary, and theorems hold for every permutation. The adversary creates any blocks it can sign, backdates, equivocates, and delivers when and to whom it wants.
- **The invariant** (`Proof/Main`): every honest node's local chain is at least as high as every honest block at least Δ + 1 slots old. So honest blocks satisfy the tree axiom, and every execution yields a valid PoS tree.
- **Settlement** (`Proof/Settlement`, `Proof/FinalE`). On the good event `GoodLS` of the lottery string, a block an honest node commits as immutable stays on every honest chain (`final_bimm_epochs`). `GoodLS` covers phases, a cold margin condition, and k-windows. The window may depend on the epoch (`final_bimm_epochWin`). `time_final_epochs` is the time-based variant.

The assumptions on the environment are the fields of `Assm E`:
- honest stakers never spend their notes;
- crash-stop participation;
- tip orders are arbitrary;
- parameters are laid out as the specification does them (`Config.Sane`).

## The probability layer

| Theorem | Statement |
|---|---|
| `final_bimm_ro` (`Prob/RO`) | **One epoch.** The tickets are a random oracle, each slot's tickets are fresh given the past (no grinding), honest blocks are delivered within Δ, and every slot's law is within a band. Then P(finality violation) ≤ `settleEps2`. |
| `slotBand_of_stake` (`Prob/Stake`) | The band condition follows from stake fractions and the stake estimate. It covers the specification's threshold approximation and any split of stake into notes. |
| `lottery_law_epoch` (`Prob/ROEpoch`) | **Many epochs.** The lottery string is dominated by a worst-case kernel with one band member per epoch. |
| `final_bimm_ro_epoch_ok`, `final_bimm_ro_epoch3_ok` (`Prob/Final2E`, `Final3E`) | P(violation) ≤ settlement bound + P(some epoch state out of band). Phases inside an epoch use each member's own contraction, and phases near a boundary pay a bounded ratio. |
| `prob_out_of_band` (`Prob/TSIRO`) | **Total stake inference.** The probability that the stake estimate leaves its band in some epoch is at most `Ne · bandEps`. The proof uses Chernoff bounds with predictable rates and a deterministic band step through the specification's fixed-point update (`infer_close`). The adversary may withhold all its blocks. |
| `final_bimm_ro_tsi3` (`Prob/FinalTSI`) | Joins the two: P(violation) ≤ `settleEps3E + Ne · bandEps`. |

The hypotheses of `final_bimm_ro_tsi3` beyond the random oracle, fresh lotteries and Δ-delivery are explicit:

| Hypothesis | Meaning | Status |
|---|---|---|
| `InB … 0` | genesis is in band | a genesis check |
| `StateOK` | distinct note ids, small notes, adversary ≤ β of participating stake | stake assumption |
| `Recur` | `D_{e+1} = infer(D_e, N_e)` on the canonical prefix, with `(1−μ)` × honest occupied slots ≤ `N_e` ≤ occupied slots + 1 | **assumed**, see open items |
| `StakePath` | the stake at each slot of epoch `e+1` is covered by epoch `e`'s window estimate | stake-drift assumption |
| `hpick` | an in-band state is within its assigned member's band | checked per certificate |

## Certified number

One configuration is certified, as a Lean theorem with standard axioms only (`Prob/Certs/E20D11.lean`, `certified_tsi`):

> f = 1/30, k = 2160, Δ = 11 slots, β = 0.2, executions up to slot 31,536,000 (one year, 49 epochs), with the specification's stake inference and the adversary free to withhold all its blocks: **P(finality violation) ≤ 1e-13 + 49 × 3.8e-16**.

The band of slot rates is derived from the stake estimate (TSI band δ = 9 %, six band members), with μ = 0 (every honest win is counted). The remaining hypotheses are those of `final_bimm_ro_tsi3` above.

Other configurations are generated by `tools/certgen` (one-epoch, genesis and multi-epoch variants; see its README). Indicative values from the same method include:
- β = 0.1 over a year: about 1e-40;
- β = 0.3 over one epoch, assuming a fixed band within 0.1 % of the stake-proportional rates: about 1e-10.

Under full withholding at k = 2160, the method gives nothing useful at β = 0.3 over many epochs. The bounds are loose: an exact computation of the same failure event is several orders of magnitude smaller.

## Specification → model

| Specification | Model | File |
|---|---|---|
| Constants: f = 1/30, k = 2160, W = 12, MAX_UNCLES = 4, slot 1 s | `Config`, `Config.spec`; derived `⌊k/f⌋ = 64800`, epoch 648000, PERIOD 388800, `⌊W/f⌋ = 360`, s_gen = 16200 (checked by `decide`) | `Spec/Params.lean` |
| PoL threshold `v(t0 + t1 v)` in 𝔽_p, ticket `< threshold` | `t0`, `t1`, `threshold`, `wins`, exactly, including mod-p wrap-around | `Spec/Lottery.lean` |
| TSI update (fixed point, PRECISION 1000, β = 1, `f_p = 33`) | `infer`, with `Int.tdiv` for Rust's truncating division; `inferReal` is the exact-rational update | `Spec/StakeInference.lean` |
| Headers, uncle headers, block store | `Header`, `Block`, `Store` | `Spec/Chain.lean` |
| `ancestors`, height, `block_at_depth`, `common_prefix_depth`, `density`, tips | `chain`, `height`, `blockAtDepth`, `commonPrefixDepth`, `density`, `tips` | `Spec/Chain.lean` |
| `online_fork_choice`, `bootstrap_fork_choice` | `forkChoice`, with the tip order as an argument | `Spec/ForkChoice.lean` |
| Epoch state `(C_LEAD, η, D)` per chain; nonce; `N_BLOCKS` | `epochState`, `nonceAfter`, `occupied`, `stakeEstimate` | `Spec/EpochState.lean` |
| `verify_PoL` | `polValid` (ideal zero-knowledge) | `Spec/EpochState.lean` |
| `valid_header`, `valid_uncle`, `on_block`, `commit`, `prune_forks`, uncle selection, proposing | `validHeader`, `validUncle`, `onBlock`, `pruneForks`, `selectUncles`, `propose` | `Spec/Node.lean` |
| Time, adversary, network | `Event`, `World`, `run`, `DeltaDelivery` | `Spec/Execution.lean` |

`tools/difftest/cryptarchia_diff.py` compares these definitions on random block trees against an independent Python transliteration of the pseudocode. It covers fork choice, pruning, uncle selection, the TSI count and update, and the threshold. Result: 10,200 checks over three seeds, 0 mismatches.

## Where the specification is silent or the implementation differs

Each point is resolved so that theorems cover both readings, or in the adversary's favour.

| Point | Specification | Implementation | Model |
|---|---|---|---|
| Order of forks in fork choice | a set; order not given | hash-trie order of tip IDs | an argument; theorems quantify over every permutation (`Env.OrderOK`) |
| `c_loc' = B` when `parent(B) = c_loc` | shortcut, no fork choice | always runs fork choice | flag `fastPath`; theorems for both values |
| Several winning notes in one slot | silent | one block per slot | one block per slot |
| Stake snapshot boundary | ambiguous | state strictly before the slot | strictly before |
| Relay of adversarial blocks | not in the consensus spec | gossipsub forwards everything | not assumed |
| Bootstrap period T_boot | 24 h | 1 h default | a parameter |

## Idealizations

1. **Cryptography:**
   - collision-free block IDs;
   - unforgeable signatures;
   - sound, zero-knowledge proof of leadership;
   - Poseidon2 as a random oracle.
2. **Clocks** are synchronized.
3. **Δ-delivery** of honest blocks to every honest node online throughout the Δ window.
4. **The ledger is abstract** (`Ledger`: the notes held after a chain). Header validation steps 1–4 (version, sizes, body root) are not represented.
5. **Fresh lotteries.** Each epoch's lottery is fresh randomness, so nonce grinding is not covered.

## Open items

1. **Restarts within T_offline** (the specification's 20-minute rule). A restarting node's local chain is stale, and its fork choice could be captured.
2. **The bootstrap rule** (density-based fork choice over `s_gen` slots).
3. **Nonce grinding.**
4. **`Recur` from the execution.** This needs two derivations:
   - canonical-prefix consistency of `stakeEstimate` across epochs;
   - the count sandwich: chain blocks need winning tickets, and honest wins are seen directly or as uncles.
5. **Tighter bounds.** The current method has two known sources of slack:
   - one window length shared across epochs of different rates; counting the window in occupied slots would remove it;
   - the two-term potential, against the exact chain.
6. **μ > 0 certificates.**
