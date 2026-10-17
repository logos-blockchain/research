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
| `Proof/` | **Deterministic safety.** Every execution builds a valid PoS tree, and finality holds on a good event of the lottery string alone, over any number of epochs. | `main`, `agree_now`, `bimm_final`, `final_bimm_dom`, `stage`, `cons_of_lot` |
| `Prob/` | **The probability layer.** It covers the lottery as a random oracle and worst-case kernels over a band of slot laws. It proves the settlement bound, the band from stake fractions, and that the stake estimate stays in band. | `settle_bound3E`, `law_le_epoch_dec`, `slotBand_pickM`, `prob_out_of_band_cover`, `finality` |
| `Prob/Certs/` | **Certified numbers** at the specification's parameters (library `CryptarchiaCerts`): each certificate is its data, checked by the generic constructions of `Prob/CertGen.lean`, `CertSpec.lean` and `CertClosed.lean`. | `E20D11.finality`, `E20D11C.finality_closed` |

## The deterministic layer

- **Executions.** An execution is a list of events (tick, delivery, block creation) from genesis. Honest nodes run the online rule. They may crash and stay offline, and the guarantees hold for nodes online at the time. Delivery is not assumed: an honest block not delivered within Δ counts as adversarial. Fork-choice tip order is arbitrary, and theorems hold for every permutation. The adversary creates any blocks it can sign, backdates, equivocates, and delivers when and to whom it wants.
- **The invariant** (`Proof/Main`): every honest node's local chain is at least as high as every honest block at least Δ + 1 slots old. So honest blocks satisfy the tree axiom, and every execution yields a valid PoS tree.
- **Settlement** (`Proof/Settlement`, `Proof/FinalE`). On the good event `GoodLS` of the lottery string, a block an honest node commits as immutable stays on every honest chain (`final_bimm_dom`, by induction over the epochs in `stage`). `GoodLS` covers phases, a cold margin condition, and k-windows, with a window that may depend on the epoch. Every world-to-world step is one transitive relation (`StepOK`, `Proof/WorldStep`), proved once per event, from which the invariants on honest blocks are projections.

The assumptions on the environment are the fields of `Assm E`:
- honest stakers never spend their notes;
- crash-stop participation;
- tip orders are arbitrary;
- parameters are laid out as the specification does them (`Config.Sane`).

## The probability layer

| Theorem | Statement |
|---|---|
| `settle_bound3E` (`Prob/Tail3E`) | **The settlement bound.** Under any kernel with one band member per epoch, the lottery's good event fails with probability at most `settleEps3E`. Phases inside an epoch use each member's own contraction, and phases near a boundary pay a bounded ratio. |
| `slotBand_of_member`, `slotBand_pickM` (`Prob/Stake`, `Prob/Pick`) | The band condition follows from stake fractions and the stake estimate. It covers the specification's threshold approximation and any split of stake into notes. |
| `law_le_epoch_dec` (`Prob/WorstE`), `lottery_law_epoch_dec` (`Prob/Finality`) | **Many epochs.** The lottery string is dominated by a worst-case kernel with one band member per epoch, needed only while the event is undecided. The lottery's conditional laws are set up once (`SlotLaws.ofRO`). |
| `prob_out_of_band_cover` (`Prob/TSIRO`) | **Total stake inference.** The probability that the stake estimate leaves its band in some epoch is at most `Ne · bandEps`. The proof uses Chernoff bounds with predictable rates and a deterministic band step through the specification's fixed-point update (`infer_close`). The adversary may withhold all its blocks. |
| `finality` (`Prob/Finality`) | **Finality over many epochs, with the stake estimate, from plain assumptions** (below), with the band's conditions as numeric facts about a certificate's constants. P(violation) ≤ `settleEps3E + Ne · bandEps`. The member assignment is constructed (`slotBand_pickM`); the estimate's update is proven from the canonical chain (`recur_of`, `occupied_le_wcnt`); canonical-prefix consistency is proven by induction on the epochs: epoch `e`'s prefixes are consistent on the lottery's good event up to `min (fix (e + 1)) N`, cut there (`cons_of_lot`, `good_trunc`, `split_up`), which needs epochs up to `e` only in band. Each such failure decides the good event's failure up to `N` (`lift_bad`), so one kernel bound covers them all together with the finality failure: the band is needed at a slot only while the event is still undecided (`law_le_epoch_dec`, `lottery_law_epoch_dec`). The certificates instantiate this one. |

`finality` assumes, beyond the certificate's numeric facts:

| Assumption | Meaning |
|---|---|
| `Model` | tickets are a random oracle; each slot's lottery is fresh (no grinding); honest blocks are delivered within Δ; honest nodes follow the protocol and only crash; they go online or offline only at epoch boundaries; some honest node is online at every slot; each slot's epoch state is measurable |
| `GenesisOK` | the genesis stake estimate is the genesis stake, all of it online |
| `Exec.StakeOK β ζ` | the adversary holds at most a fraction β of the participating stake; notes are small (ζ); lead note identifiers are distinct |
| `Exec.ChainQuality μ` | in every epoch, the canonical chain counts (as block or uncle slots) at least a fraction `1 − μ` of the window's slots an online honest node won. **Assumed** at μ = 0.13. An adversary that cannot predict honest leaders, with first-seen tie-breaking, can force about 0.122 at the band's fastest rates (a two-branch attack, solved as an MDP and replayed on an explicit block tree with the specification's uncle selection); one that can predict them, which `Model` does not exclude, about 0.22. Chain growth alone proves μ ≈ 0.25 |
| `Exec.StakeDrift ρ` | from each epoch to the next, honest online stake grows by at most a factor ρ and participating stake shrinks by at most a factor ρ, slot for slot against the previous epoch's window |
| `Exec.MinStake Hmin` | honest online stake is at least `Hmin` at every slot (it absorbs the estimate's fixed-point rounding) |

Two of these replace conditions of the earlier statements that a reader could not check. `StakeDrift` and `MinStake` imply the band step's `StakePath` (`stakePath_of_drift`); the band (`tools/certgen`, `tband`) leaves room for the drift. `OnlineEpoch`, part of `Model`, is what lets one band member serve a whole epoch: a slot's honest exponent counts only online honest stake.

## Certified numbers

Three certificates, as Lean theorems with standard axioms only, under the assumptions of `finality` above with β = 0.2, μ = 0.13, ρ = 1.01 and `Hmin` = 10⁶. Two are numeric, at the specification's depth (`finality` in `Prob/Certs/E20D11M2.lean` and `Prob/Certs/E20D11.lean`):

> f = 1/30, k = 2160, Δ = 11 slots, with the specification's stake inference and the adversary free to withhold all its blocks:
> * executions up to slot 5,184,000 (two months, 9 epochs): **P(finality violation) ≤ 1.3e-11**;
> * executions up to slot 31,536,000 (one year, 49 epochs): **P(finality violation) ≤ 7.2e-11**.

Each bound is `settleEps3E + Ne · bandEps`: the settlement bound (1.2e-11 and 7.0e-11), which covers canonical-prefix consistency in every epoch as well as finality, plus the estimate's band (2.3e-14 per epoch). The band of slot rates is derived from the stake estimate (TSI band δ = 8.5 %, 32 band members), with room for the stake drift ρ.

The third is in closed form (`finality_closed` in `Prob/Certs/E20D11C.lean`): for **every depth k ≥ 1000 and every horizon N**, at the specification with depth `k` (`Config.specK k`: epochs of `300 k` slots), P(finality violation) ≤ `par.epsC der N k`, a sum of nine terms `(N + c) · A · qᵗ` and `Ne · C · qᵗ` in `t = ⌊k/20⌋`, `Ne = ⌊N / (300 k)⌋ + 2`. The automaton certificates do not depend on `k`, and the settlement lengths grow linearly in `t` (`Prob/Closed.lean`). `finality_closed_short` folds it into two rates:

> P(finality violation) ≤ (N + 18 t + 640) · (2.4e-25 + 0.5816 · 0.702021ᵗ) + Ne · 1.562 · 0.745235ᵗ.

| k | two months | one year |
|---|---|---|
| 1500 | 6.6e-6 | |
| 2160 | 5.0e-11 | 3.0e-10 |
| 3000 | 1.9e-17 | |

(`epsC`; the short form is within a factor 2 at k = 2160.) Each 20 blocks of depth multiply the settlement part by about 0.70 and the band part by about 0.75. The constant 2.4e-25 bounds a phase lasting longer than a fixed 638 slots (`settleEps3E`'s first term); it does not decay in `k`. At k = 1000 the bound is 6e-2.

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
4. **The estimate's update from the execution.** The recursion (`cs_succ_D`), canonical-prefix consistency (`cp_consistent`, `cons_of_lot` and the epoch induction) and the upper count (`occupied_le_wcnt`) are proven. Two steps remain:
   - Replace the assumed μ = 0.13 in `hlo` with a proof. Chain growth gives μ ≈ 0.25. The uncle rule counts only forks whose parent is on the chain, so deeper forks are lost. Against an adversary that cannot predict honest leaders the best attack found forces about 0.122, so a proof needs a causality condition in `Model` (the execution up to slot t independent of later honest tickets); without it, an adversary that steers each honest leader forces about 0.22.
5. **Tighter bounds.** The current method has two known sources of slack:
   - one window length shared across epochs of different rates; counting the window in occupied slots would remove it;
   - the two-term potential, against the exact chain.
