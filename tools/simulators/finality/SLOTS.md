# Finality counted in slots

Phase K of `PLAN.md`. Phases A–J count `k` in blocks, as the specification does. This note reads
their results again with `k` counted in slots, the owner's direction. Specifications are read at
`logos-lips` `47a73cdc`; `origin/master` at `663ae35d` changes none of the text quoted here.

## K.0 — the reading

**What the sources count.** Each quote is from the revision named, read from the archive's
snapshots on 2026-10-21.

| source | what it counts | the text |
| --- | --- | --- |
| Praos, ePrint 2017/573, revision 2023-04-27 (SHA-1 `373e7ba1`) | persistence in blocks, liveness in slots | "a transaction is declared stable if and only if it is in a block that is more than k blocks deep in the ledger"; "after the passing of time corresponding to u slots (called the transaction confirmation time)" (§2.2) |
| Genesis, ePrint 2018/378, revision 2019-02-22 (SHA-1 `81b39baf`) | blocks | `maxvalid-bg`: "if (Ci forks from Cmax at most k blocks) then"; a read "computes and outputs the prefix of its local chain (chopping of k blocks.)" (§3.3) |
| Crypsinous, ePrint 2018/1132, revision 2019-05-15 (SHA-1 `5a9913a9`) | blocks in its chain selection, slots in its key evolution | "Our protocol behaves identically to Genesis in this regard, and we utilize the same chain selection rule in our protocol" (§6.2); "Invoke Protocol SelectChain(Cloc, N, k, s, R, f)", then "Update FFwEnc as many times as necessary for its time to be a least τ − k" (Appendix C.3, steps 27 and 28) |
| the specification, `cryptarchia-v1-protocol.md` | blocks for `k`, slots for `s` | `k`: "Block depth finality. Blocks deeper than `k` on any given chain are considered immutable", 2160 blocks; `s`: "Sufficient slots such that `k` blocks have been produced with high probability", `3⌊k/f⌋` (Notation) |
| the specification, `fork-choice.md` | blocks | "During normal operations, we use the Ouroboros Praos fork choice rule (`maxvalid-mc`). Here we reject any forks that diverge further back than `k` blocks." |

Crypsinous's step 28 keeps the decryption keys of the last `k` slots. Its chain selection and its
read count `k` in blocks, as Genesis's do.

**The rules this phase reads.** `K` is the finality window in slots.

- `B_imm` is the latest block of the local chain whose slot is at most `sl − K`, for the current
  slot `sl`. Commit, fork pruning and rule 8 of Block Header Validation read it as today.
- The Online rule ignores a fork that diverges before `B_imm`. A rollback reaches at most `K`
  slots back.
- The Bootstrap rule compares a fork that diverges before `B_imm` by its density.
- A variant adds a density floor `φ`, in one of two forms (K.3). Under the depth form `B_imm`
  moves to a block once the block is `K` slots old and `φ` blocks follow it. Under the density
  form it moves to a block once the `K` slots after the block hold `φ` blocks of the chain.

**The candidates.** `K = ⌊k/f⌋` = 64,800 slots, 18 hours, the time 2,160 blocks take at the full
rate with no forks. `K = s = 3⌊k/f⌋` = 194,400 slots, 54 hours, the specification's own slot
parameter. And the least `K` that holds each `(α, ε, Δ)`.

**Taken without the owner's answer.** These rules; the floor measured as a variant beside them;
the epoch at today's length, `10⌊k/f⌋` slots at `k = 2160` (G2).

**The owner's answer, after K.7 and K.8.** `K = ⌊k/f⌋`, 64,800 slots, with the floor in its depth
form at `φ` = 1,019 blocks, the worst case's at 10 s against a third, and no cap on the
inference's correction (`PLAN.md` Q10, Q11).

## K.1 — settlement after a wait of `T` slots

`src/finality_sim/slots.py` and `scripts/k1_settle.py`, with runs in `runs/k1/`.

**The rule.** A wait of `T` slots accepts the prefix up to a target's slot once `T` slots have
passed since that slot. A client can read it as a settled level, and `B_imm` reads it at `T = K`.
The rule fails when that prefix is displaced after the wait.

**Random delay.** The private race with a premined lead, in B4's model. Per slot the coalition wins
at `a = α·λ` and the canonical chain grows at `h = (1 − α)·g·λ`, with `λ = −ln(1 − f)` and `g`
A1's growth. B4 gives the coalition's chance `P(n, t)` exactly, for `n` canonical blocks counting
the target `t` slots after the target's parent. The wait averages it over the gap from the parent
to the target, exponential at `h`, and over the canonical blocks the wait holds, Poisson at `h·T`.
The depth rule beside it waits for B5's closed-form depth.

**The worst case.** A bound in four steps:

1. Once the prefix up to the target's slot lies `D` deep in an honest chain, B2's upper bound
   `UB(D)` holds the chance of its displacement.
2. Every honest block reaches every honest node within `Δ`. An honest win that comes at least `Δ`
   slots after the last such win, a renewal, therefore lengthens every honest chain once it is
   delivered. Over the wait every honest chain gains at least the renewals `N` delivered within
   it, B5's law: `P(N ≥ n) = P(Bin(T − nΔ, p_h) ≥ n)`.
3. A chain's blocks up to the target's slot exceed what every honest node held `Δ` after that slot
   by at most `W + 1`. Only the coalition's wins follow the last honest block of that prefix, and
   that block extended a chain every honest node held `Δ` later. `W` is the largest excess of the
   coalition's wins over the renewals since any earlier slot. Its law is the stationary lead of
   H.3's cycle walk plus the coalition's wins in the part of the current cycle that has passed.
4. After the wait the target therefore lies at least `N − W − 2` deep, one block going to a
   renewal not yet delivered. `N` is counted from `2Δ` slots after the target, so that it does
   not depend on `W`. Then `ε(T) ≤ min_D [UB(D) + P(N − W − 2 < D)]`.

The attack beside the bound is an estimate: B2's lower depth on the worst-case clock of
`Δ + 1/p_h` slots a block, marked `*` where B2 extrapolates it and `≤` where it is B2's first
computed depth.

The wait under random delay, against the depth rule's depth and its time on the report's clock,
`30/((1 − α)g)` seconds a block (`runs/k1/random.csv`):

ε = 1e-6

| α | testnet: wait (h) | testnet: depth rule, blocks / h | specification: wait (h) | specification: depth rule, blocks / h | specification: wait over the depth rule's time, report's / model's clock |
| --- | --- | --- | --- | --- | --- |
| 0.05 | 0.14 | 6 / 0.05 | 0.17 | 6 / 0.06 | 2.789 / 2.836 |
| 0.10 | 0.22 | 10 / 0.10 | 0.28 | 12 / 0.13 | 2.092 / 2.128 |
| 0.15 | 0.32 | 17 / 0.17 | 0.42 | 20 / 0.23 | 1.811 / 1.842 |
| 0.20 | 0.48 | 26 / 0.28 | 0.65 | 32 / 0.39 | 1.658 / 1.687 |
| 0.25 | 0.75 | 42 / 0.48 | 1.08 | 56 / 0.74 | 1.465 / 1.490 |
| 0.30 | 1.25 | 72 / 0.88 | 1.97 | 105 / 1.48 | 1.335 / 1.358 |
| a third | 1.88 | 110 / 1.42 | 3.27 | 177 / 2.62 | 1.250 / 1.271 |

ε = 1e-9

| α | testnet: wait (h) | testnet: depth rule, blocks / h | specification: wait (h) | specification: depth rule, blocks / h | specification: wait over the depth rule's time, report's / model's clock |
| --- | --- | --- | --- | --- | --- |
| 0.05 | 0.24 | 10 / 0.09 | 0.30 | 11 / 0.11 | 2.587 / 2.631 |
| 0.10 | 0.36 | 17 / 0.16 | 0.45 | 19 / 0.21 | 2.174 / 2.211 |
| 0.15 | 0.53 | 27 / 0.27 | 0.68 | 32 / 0.37 | 1.829 / 1.860 |
| 0.20 | 0.77 | 42 / 0.45 | 1.04 | 52 / 0.64 | 1.629 / 1.657 |
| 0.25 | 1.19 | 67 / 0.77 | 1.70 | 88 / 1.16 | 1.473 / 1.498 |
| 0.30 | 1.96 | 114 / 1.40 | 3.09 | 165 / 2.32 | 1.331 / 1.354 |
| a third | 2.94 | 172 / 2.21 | 5.10 | 276 / 4.08 | 1.249 / 1.271 |

Under the worst case, the attack's estimate – the bound, in hours (`runs/k1/worst.csv`):

ε = 1e-6, hours

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 0.2 – 0.6 | ≤ 0.2 – 0.6 | ≤ 0.2 – 0.7 | ≤ 0.2 – 0.7 | ≤ 0.2 – 0.9 | ≤ 0.2 – 1.0 | ≤ 0.3 – 1.3 | ≤ 0.3 – 1.9 |
| 0.10 | 0.2 – 0.9 | 0.2 – 0.9 | 0.2 – 1.0 | 0.2 – 1.1 | 0.2 – 1.3 | 0.3 – 1.4 | 0.3 – 2.0 | 0.4 – 2.8 |
| 0.15 | 0.3 – 1.3 | 0.3 – 1.4 | 0.3 – 1.4 | 0.4 – 1.6 | 0.4 – 1.9 | 0.4 – 2.1 | 0.5 – 3.0 | 0.6 – 4.2 |
| 0.20 | 0.5 – 1.9 | 0.5 – 2.1 | 0.5 – 2.2 | 0.6 – 2.4 | 0.7 – 2.9 | 0.7 – 3.3 | 0.9 – 4.7 | 1.1 – 6.9 |
| 0.25 | 0.8 – 3.1 | 0.9 – 3.2 | 0.9 – 3.5 | 1.0 – 3.9 | 1.2 – 4.8 | 1.3 – 5.5 | 1.7 – 8.1 | 2.2* – 12.4 |
| 0.30 | 1.5* – 5.2 | 1.6* – 5.6 | 1.7* – 6.0 | 1.9* – 6.9 | 2.3* – 8.7 | 2.6* – 10.3 | 3.6* – 16.1 | 5.0* – 26.9 |
| a third | 2.3* – 7.9 | 2.5* – 8.6 | 2.7* – 9.3 | 3.1* – 11.0 | 3.8* – 14.4 | 4.4* – 17.5 | 6.7* – 29.6 | 10.5* – 55.0 |

ε = 1e-9, hours

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 0.2 – 0.9 | ≤ 0.2 – 1.0 | ≤ 0.2 – 1.0 | ≤ 0.2 – 1.1 | 0.2 – 1.3 | 0.2 – 1.5 | 0.3 – 2.0 | 0.3 – 2.8 |
| 0.10 | 0.3 – 1.4 | 0.3 – 1.4 | 0.3 – 1.5 | 0.3 – 1.6 | 0.4 – 1.9 | 0.4 – 2.1 | 0.5 – 2.9 | 0.6 – 4.2 |
| 0.15 | 0.5 – 2.0 | 0.5 – 2.1 | 0.5 – 2.2 | 0.6 – 2.4 | 0.6 – 2.9 | 0.7 – 3.2 | 0.8 – 4.4 | 1.0 – 6.3 |
| 0.20 | 0.8 – 3.0 | 0.8 – 3.1 | 0.8 – 3.3 | 0.9 – 3.7 | 1.0 – 4.4 | 1.1 – 5.0 | 1.4 – 7.0 | 1.7 – 10.3 |
| 0.25 | 1.3 – 4.6 | 1.3 – 4.9 | 1.4 – 5.2 | 1.5* – 5.9 | 1.8* – 7.2 | 2.0* – 8.3 | 2.6* – 12.1 | 3.3* – 18.6 |
| 0.30 | 2.2* – 7.9 | 2.4* – 8.4 | 2.5* – 9.1 | 2.9* – 10.5 | 3.4* – 13.2 | 3.9* – 15.5 | 5.4* – 24.3 | 7.7* – 40.4 |
| a third | 3.5* – 12.0 | 3.8* – 13.0 | 4.1* – 14.1 | 4.7* – 16.7 | 5.8* – 21.8 | 6.8* – 26.3 | 10.2* – 44.5 | 16.0* – 82.6 |

The bound over B2's upper depth on the worst-case clock, at `1e-9`:

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 2.24 | 2.17 | 2.12 | 2.00 | 1.83 | 1.72 | 1.55 | 1.41 |
| 0.10 | 1.90 | 1.86 | 1.82 | 1.73 | 1.64 | 1.57 | 1.43 | 1.33 |
| 0.15 | 1.70 | 1.66 | 1.63 | 1.57 | 1.50 | 1.44 | 1.34 | 1.26 |
| 0.20 | 1.55 | 1.52 | 1.49 | 1.45 | 1.38 | 1.35 | 1.27 | 1.20 |
| 0.25 | 1.42 | 1.40 | 1.38 | 1.34 | 1.29 | 1.26 | 1.20 | 1.15 |
| 0.30 | 1.31 | 1.30 | 1.28 | 1.25 | 1.21 | 1.19 | 1.14 | 1.10 |
| a third | 1.25 | 1.24 | 1.22 | 1.20 | 1.17 | 1.15 | 1.11 | 1.07 |

The race scored a wait after each target, on the engine's specification Blend with the coalition
withholding (B4's timelines) and on independent slots at the model's rates, at the waits whose
closed-form chance is `1e-2` and `1e-3`; the standard error is the spread of the 64 replicates'
rates (`runs/k1/played.csv`):

| timelines | α | ε | wait (h) | closed form | race, rate ± se | targets |
| --- | --- | --- | --- | --- | --- | --- |
| engine | 0.10 | 1e-2 | 0.04 | 1.0e-02 | 7.4e-03 ± 4.7e-04 | 123,486 |
| engine | 0.10 | 1e-3 | 0.10 | 9.9e-04 | 5.4e-04 ± 1.1e-04 | 123,486 |
| model | 0.10 | 1e-2 | 0.04 | 1.0e-02 | 9.0e-03 ± 3.9e-04 | 126,884 |
| model | 0.10 | 1e-3 | 0.10 | 9.9e-04 | 7.7e-04 ± 1.3e-04 | 126,884 |
| engine | 0.25 | 1e-2 | 0.27 | 1.0e-02 | 5.6e-03 ± 9.2e-04 | 103,933 |
| engine | 0.25 | 1e-3 | 0.47 | 1.0e-03 | 5.8e-04 ± 3.8e-04 | 103,933 |
| model | 0.25 | 1e-2 | 0.27 | 1.0e-02 | 1.0e-02 ± 1.1e-03 | 103,436 |
| model | 0.25 | 1e-3 | 0.47 | 1.0e-03 | 1.4e-03 ± 4.1e-04 | 103,436 |
| engine | 0.30 | 1e-2 | 0.53 | 1.0e-02 | 5.0e-03 ± 9.6e-04 | 95,731 |
| engine | 0.30 | 1e-3 | 0.88 | 1.0e-03 | 2.2e-04 ± 1.2e-04 | 95,731 |
| model | 0.30 | 1e-2 | 0.53 | 1.0e-02 | 9.9e-03 ± 1.3e-03 | 94,196 |
| model | 0.30 | 1e-3 | 0.88 | 1.0e-03 | 7.5e-04 ± 3.5e-04 | 94,196 |
| engine | a third | 1e-2 | 0.90 | 1.0e-02 | 4.2e-03 ± 1.2e-03 | 88,964 |
| engine | a third | 1e-3 | 1.48 | 1.0e-03 | 0 | 88,964 |
| model | a third | 1e-2 | 0.90 | 1.0e-02 | 8.1e-03 ± 1.8e-03 | 87,209 |
| model | a third | 1e-3 | 1.48 | 1.0e-03 | 6.4e-04 ± 4.2e-04 | 87,209 |

Reading:

- **Under random delay a wait costs a quarter more than the depth rule against a third.** At
  `1e-9` on the specification's Blend it is 5.10 hours, where the depth rule's 276 blocks take
  4.08 on the report's clock: 1.249 times as long, and 1.271 times on the model's own clock.
- **The smaller the share, the larger the factor and the smaller the time.** Against a tenth the
  wait is 2.174 times the depth rule's time, 0.45 hours against 0.21. A depth rule waits for few
  blocks there, and a wait must also cover the runs in which the honest blocks come slowly.
- **Testnet's Blend** settles a third in 2.94 hours of wait at `1e-9`.
- **Under the worst case the bound costs a seventh over B2's depth against a third at 10 s.** It
  waits 26.3 hours, 1.15 times B2's 1,510 blocks on the worst-case clock. The excess falls as
  the depth grows, to 1.07 at 20 s, and reaches 2.24 against 5 % at 1 s, where few blocks
  suffice and the coalition's lead `W` weighs most.
- **The attack's estimate lies far below the bound**, 6.8 hours against a third at 10 s. It
  converts B2's lower depth at the clock's mean.
- **The race on the model's own slots matches the closed form.** Every cell lies within 2.5
  standard errors of it, and six of the eight at or below it. On the engine's timelines the race
  succeeds 0.42–0.74 times as often at `1e-2`, and never at `1e-3` against a third. The chain
  the coalition withholds from grows faster on the engine than A1's convention, as B3 and B4
  found, so the closed form errs on the safe side.

K.7 bounds the same worst-case wait in GRR's own model, at 10.1 hours against a third at 10 s on the
slot lottery, and reads K.2 to K.5 again under that bound.

Gates (`tests/test_slots.py`, `tests/test_k2.py`):

- the chance at every depth, in one pass, is B4's `P(n, t)`;
- the closed form matches the premined race played on its model's slots at waits whose chance
  lies between `2e-3` and `0.1`, within four standard errors;
- on a chain with one canonical block every `c` slots, a wait of `d·c` slots, or up to `c − 1`
  more, is the depth `d`, target by target;
- `W`'s law matches the walk it stands for, sampled in 30 independent runs, from above and within
  a tenth;
- the bound lies above the premined race played on the worst case's own timelines, honest blocks
  only at renewals, and falls with the wait;
- raising both of B4's rates by a factor shortens the wait by that factor exactly, the reading of
  a deflated inference in the convention's model;
- a faster honest chain lowers the worst-case bound at a given wait, and a faster coalition
  raises it.

Each gate fails under a registered mutation of its function (`scripts/check_mutations.py`).

## K.2 — what a `K` holds

`scripts/k2_holds.py`, with runs in `runs/k2/`. K.7 reads the worst-case parts again under a bound
computed in GRR's own model, which shortens every worst-case wait to under half.

**What is read.** `K` is read at `⌊k/f⌋` and `3⌊k/f⌋` slots for each `k` of B5 and 1620: the time
`k` blocks take at the full rate with no forks, and the specification's slot parameter `s`. A `K`
holds a share at `1e-9` when the chance against a wait of `K` slots (K.1), multiplied by the factor
of the nonce in force, is at most `1e-9`.

- **The share.** Under random delay it is found by bisection, as B6's `held_random` finds it for
  `k`. Under the worst case it is read on B5's grid of shares, 0.05 to a third every 0.005, from
  B2's bound recomputed here at every depth up to 7,000 (`runs/k2/ub_grid.parquet`), linear in the
  share between grid points, as B5's `held_worst` reads it.
- **Today's nonce.** One and two ground nonces carry B6's upper ends at `1e-9`, recomputed on B6's
  grids with B6's settings (`runs/k2/factors.csv`). The script checks that they return B6's shares
  for `k` in blocks. B6's factor does not depend on `k`.
- **The nonce of §3.1 under its delay.** Two nonces at H.2's bound with one delay evaluator: the
  walk's `E[G_min]` plus the blind switch plus the evaluator term, at a margin of ten minutes and
  the sub-windows of `k = 2160`, squared (`DESIGNS.md` H.2). The epoch keeps today's length (K.0),
  so its sub-windows are those of `k = 2160` whatever `K` is. H.2 computes the bound at 30 % and a
  third, on the specification's Blend and at 10 s. Its column takes the third's factor at every
  share up to a third, where the factor is largest, and reads no share above a third.
- **A deflated inference** (`FURTHER.md` G7) raises every threshold by `1/(1 − α)`. Per slot the
  honest stake then wins at `f` and the coalition at `1 − (1 − f)^(α/(1 − α))`. Under the worst
  case `Δ` stays fixed in slots, so B2's bound is read at `Δ/(1 − α)` at the old rates, as G7 reads
  it, with the renewal and lead laws at the raised rates. Under random delay, in the convention's
  model, both rates rise by `1/(1 − α)` and the race keeps its ratio: a wait of `K` slots after a
  deflation is a wait of `K/(1 − α)` before it. On the engine, G7's deflated arm measured the
  growth of that chain, one Blend copy released at the slot.

The largest share each `K` holds at `1e-9` (`runs/k2/holds.csv`):

K = ⌊k/f⌋

| model | case | k = 2160 | k = 1620 | k = 1080 | k = 432 | k = 216 | k = 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, testnet | no grinding | 0.427 | 0.417 | 0.400 | 0.348 | 0.292 | 0.231 |
| random, testnet | today's nonce, one ground | 0.381 | 0.367 | 0.344 | 0.289 | 0.250 | 0.211 |
| random, testnet | today's nonce, two ground | 0.358 | 0.344 | 0.326 | 0.280 | 0.241 | 0.203 |
| random, testnet | a deflated inference | 0.443 | 0.435 | 0.422 | 0.378 | 0.326 | 0.264 |
| random, specification | no grinding | 0.390 | 0.380 | 0.363 | 0.311 | 0.255 | 0.195 |
| random, specification | today's nonce, one ground | 0.345 | 0.330 | 0.308 | 0.256 | 0.219 | 0.180 |
| random, specification | today's nonce, two ground | 0.322 | 0.309 | 0.292 | 0.248 | 0.211 | 0.174 |
| random, specification | the nonce of §3.1 under its delay | ≥ a third | ≥ a third | ≥ a third | 0.310 | 0.254 | 0.194 |
| random, specification | a deflated inference | 0.406 | 0.397 | 0.383 | 0.337 | 0.284 | 0.222 |
| worst, 1 s | no grinding | ≥ a third | ≥ a third | 0.311 | 0.223 | 0.138 | 0.061 |
| worst, 1 s | today's nonce, one ground | 0.304 | 0.289 | 0.267 | 0.208 | 0.134 | 0.060 |
| worst, 1 s | today's nonce, two ground | 0.296 | 0.281 | 0.259 | 0.201 | 0.131 | 0.060 |
| worst, 1 s | a deflated inference | ≥ a third | ≥ a third | ≥ a third | 0.251 | 0.159 | 0.070 |
| worst, 10 s | no grinding | 0.310 | 0.290 | 0.257 | 0.164 | 0.077 | < 0.05 |
| worst, 10 s | today's nonce, one ground | 0.262 | 0.247 | 0.225 | 0.158 | 0.076 | < 0.05 |
| worst, 10 s | today's nonce, two ground | 0.254 | 0.240 | 0.218 | 0.153 | 0.075 | < 0.05 |
| worst, 10 s | the nonce of §3.1 under its delay | 0.309 | 0.289 | 0.256 | 0.163 | 0.076 | < 0.05 |
| worst, 10 s | a deflated inference | 0.307 | 0.289 | 0.260 | 0.170 | 0.081 | < 0.05 |
| worst, 20 s | no grinding | 0.248 | 0.224 | 0.187 | 0.082 | < 0.05 | < 0.05 |
| worst, 20 s | today's nonce, one ground | 0.212 | 0.197 | 0.172 | 0.080 | < 0.05 | < 0.05 |
| worst, 20 s | today's nonce, two ground | 0.205 | 0.190 | 0.166 | 0.078 | < 0.05 | < 0.05 |
| worst, 20 s | a deflated inference | 0.225 | 0.205 | 0.172 | 0.076 | < 0.05 | < 0.05 |

K = 3⌊k/f⌋

| model | case | k = 2160 | k = 1620 | k = 1080 | k = 432 | k = 216 | k = 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random, testnet | no grinding | 0.454 | 0.448 | 0.439 | 0.408 | 0.374 | 0.335 |
| random, testnet | today's nonce, one ground | 0.425 | 0.415 | 0.400 | 0.355 | 0.312 | 0.279 |
| random, testnet | today's nonce, two ground | 0.407 | 0.396 | 0.377 | 0.334 | 0.301 | 0.271 |
| random, testnet | a deflated inference | 0.465 | 0.460 | 0.453 | 0.428 | 0.400 | 0.366 |
| random, specification | no grinding | 0.419 | 0.413 | 0.403 | 0.371 | 0.337 | 0.298 |
| random, specification | today's nonce, one ground | 0.389 | 0.379 | 0.363 | 0.318 | 0.277 | 0.247 |
| random, specification | today's nonce, two ground | 0.371 | 0.359 | 0.341 | 0.300 | 0.268 | 0.238 |
| random, specification | the nonce of §3.1 under its delay | ≥ a third | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.297 |
| random, specification | a deflated inference | 0.428 | 0.424 | 0.416 | 0.390 | 0.360 | 0.325 |
| worst, 1 s | no grinding | ≥ a third | ≥ a third | ≥ a third | 0.325 | 0.265 | 0.202 |
| worst, 1 s | today's nonce, one ground | ≥ a third | ≥ a third | 0.329 | 0.277 | 0.236 | 0.192 |
| worst, 1 s | today's nonce, two ground | ≥ a third | ≥ a third | 0.316 | 0.269 | 0.229 | 0.186 |
| worst, 1 s | a deflated inference | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.295 | 0.229 |
| worst, 10 s | no grinding | ≥ a third | ≥ a third | ≥ a third | 0.273 | 0.208 | 0.142 |
| worst, 10 s | today's nonce, one ground | 0.321 | 0.305 | 0.282 | 0.235 | 0.193 | 0.138 |
| worst, 10 s | today's nonce, two ground | 0.304 | 0.292 | 0.274 | 0.228 | 0.186 | 0.135 |
| worst, 10 s | the nonce of §3.1 under its delay | ≥ a third | ≥ a third | ≥ a third | 0.272 | 0.208 | 0.141 |
| worst, 10 s | a deflated inference | ≥ a third | ≥ a third | 0.329 | 0.274 | 0.214 | 0.148 |
| worst, 20 s | no grinding | 0.315 | 0.300 | 0.276 | 0.204 | 0.132 | 0.058 |
| worst, 20 s | today's nonce, one ground | 0.266 | 0.251 | 0.232 | 0.184 | 0.128 | 0.056 |
| worst, 20 s | today's nonce, two ground | 0.256 | 0.243 | 0.225 | 0.177 | 0.124 | 0.056 |
| worst, 20 s | a deflated inference | 0.284 | 0.271 | 0.250 | 0.187 | 0.122 | 0.054 |

Against `k` in blocks, without grinding and with two ground nonces: B5's and B6's shares
(`SETTLEMENT.md` B5, B6), which B6 did not compute at `k = 1620`:

random, specification

| k | k blocks: no grinding / two ground nonces | K = ⌊k/f⌋ slots | K = 3⌊k/f⌋ slots |
| --- | --- | --- | --- |
| 2160 | 0.412 / 0.358 | 0.390 / 0.322 | 0.419 / 0.371 |
| 1620 | — / — | 0.380 / 0.309 | 0.413 / 0.359 |
| 1080 | 0.393 / 0.327 | 0.363 / 0.292 | 0.403 / 0.341 |
| 432 | 0.357 / 0.288 | 0.311 / 0.248 | 0.371 / 0.300 |
| 216 | 0.319 / 0.255 | 0.255 / 0.211 | 0.337 / 0.268 |
| 120 | 0.276 / 0.226 | 0.195 / 0.174 | 0.298 / 0.238 |

worst, 10 s

| k | k blocks: no grinding / two ground nonces | K = ⌊k/f⌋ slots | K = 3⌊k/f⌋ slots |
| --- | --- | --- | --- |
| 2160 | ≥ a third / 0.288 | 0.310 / 0.254 | ≥ a third / 0.304 |
| 1620 | — / — | 0.290 / 0.240 | ≥ a third / 0.292 |
| 1080 | 0.313 / 0.256 | 0.257 / 0.218 | ≥ a third / 0.274 |
| 432 | 0.242 / 0.208 | 0.164 / 0.153 | 0.273 / 0.228 |
| 216 | 0.172 / 0.161 | 0.077 / 0.075 | 0.208 / 0.186 |
| 120 | 0.106 / 0.103 | < 0.05 / < 0.05 | 0.142 / 0.135 |

The wait against 30 % and a third at `1e-9` in each case, beside the two candidates at
`k = 2160`; "past the curve" marks a wait beyond the 7,000 blocks of B2's bound computed at the
deflated delay (`runs/k2/waits.csv`):

| model | case | 30 %: wait (h) | a third: wait (h) | K = 64,800 (18 h): 30 % / a third | K = 194,400 (54 h): 30 % / a third |
| --- | --- | --- | --- | --- | --- |
| worst, 1 s | no grinding | 7.9 | 12.0 | yes / yes | yes / yes |
| worst, 1 s | one ground nonce, lower end | 15.5 | 28.3 | yes / no | yes / yes |
| worst, 1 s | one ground nonce, upper end | 16.7 | 29.2 | yes / no | yes / yes |
| worst, 1 s | two ground nonces, lower end | 17.0 | 34.3 | yes / no | yes / yes |
| worst, 1 s | two ground nonces, upper end | 19.5 | 39.8 | no / no | yes / yes |
| worst, 1 s | deflated | 5.7 | 8.4 | yes / yes | yes / yes |
| worst, 10 s | no grinding | 15.5 | 26.3 | yes / no | yes / yes |
| worst, 10 s | one ground nonce, lower end | 35.7 | 67.4 | no / no | yes / no |
| worst, 10 s | one ground nonce, upper end | 36.8 | 69.4 | no / no | yes / no |
| worst, 10 s | two ground nonces, lower end | 42.0 | 99.5 | no / no | yes / no |
| worst, 10 s | two ground nonces, upper end | 49.0 | 109.1 | no / no | yes / no |
| worst, 10 s | nonce §3.1, two nonces at H.2's bound | 15.6 | 26.6 | yes / no | yes / yes |
| worst, 10 s | deflated | 15.9 | 29.8 | yes / no | yes / yes |
| worst, 10 s | deflated, nonce §3.1 at H.2's bound at the old rates | 16.0 | 30.1 | yes / no | yes / yes |
| worst, 20 s | no grinding | 40.4 | 82.6 | no / no | yes / no |
| worst, 20 s | one ground nonce, lower end | 102.4 | 229.3 | no / no | no / no |
| worst, 20 s | one ground nonce, upper end | 105.5 | 235.9 | no / no | no / no |
| worst, 20 s | two ground nonces, lower end | 149.4 | 376.1 | no / no | no / no |
| worst, 20 s | two ground nonces, upper end | 164.8 | 385.4 | no / no | no / no |
| worst, 20 s | deflated | 83.2 | past the curve | no / no | no / no |
| random, specification | no grinding | 3.1 | 5.1 | yes / yes | yes / yes |
| random, specification | one ground nonce, lower end | 7.6 | 13.9 | yes / yes | yes / yes |
| random, specification | one ground nonce, upper end | 7.8 | 14.3 | yes / yes | yes / yes |
| random, specification | two ground nonces, lower end | 9.5 | 21.7 | yes / no | yes / yes |
| random, specification | two ground nonces, upper end | 10.8 | 23.1 | yes / no | yes / yes |
| random, specification | nonce §3.1, two nonces at H.2's bound | 3.1 | 5.1 | yes / yes | yes / yes |
| random, specification | deflated, the convention's model | 2.2 | 3.4 | yes / yes | yes / yes |
| random, specification | deflated, the engine's growth | 2.5 | 4.2 | yes / yes | yes / yes |

The chance of displacement after each candidate at 10 s, and the largest grinding factor on that
chance it absorbs at `1e-9` (`runs/k2/absorbs.csv`):

| α | K | chance after K slots | largest factor absorbed | after a deflated inference: chance / factor |
| --- | --- | --- | --- | --- |
| 0.30 | 64,800 | 3.9e-11 | 26 | 6.8e-11 / 15 |
| 0.30 | 194,400 | 9.2e-32 | 1.1e+22 | 4.2e-31 / 2.4e+21 |
| a third | 64,800 | 6.6e-07 | none | 3.5e-06 / none |
| a third | 194,400 | 4.4e-19 | 2.3e+09 | 5.4e-17 / 1.8e+07 |

Reading:

- **Counted in slots, `⌊k/f⌋` holds less than `k` blocks did under the worst case.** A wait does
  not stretch while the coalition withholds, so it must cover a chain that grows from the honest
  stake alone, one block per `Δ + 1/p_h` slots. At 10 s `k = 2160` blocks hold a third without
  grinding, and `K = 64,800` slots hold 0.310. With two ground nonces the shares are 0.288 and
  0.254.
- **`⌊k/f⌋` does not hold a third at 10 s.** After 64,800 slots the chance is 6.6e-7, and the
  wait that holds `1e-9` is 26.3 hours. It holds 30 %, with a factor of 26 to spare.
- **The specification's own slot parameter holds what `k = 2160` blocks held, and more.**
  `K = 3⌊k/f⌋` = 194,400 slots holds a third at 10 s without grinding, with the nonce of §3.1 under
  its delay (26.6 hours), and after a deflated inference (29.8 hours; 30.1 with the nonce of §3.1 at
  H.2's factor at the old rates). It absorbs a grinding factor of 2.3e+09, and 1.8e+07 after
  a deflated inference. With two ground nonces it holds 0.304 where `k = 2160` blocks held 0.288.
- **With today's nonce, no candidate holds a third at 10 s.** One ground nonce needs 67.4–69.4
  hours and two need 99.5–109.1. Against 30 %, `3⌊k/f⌋` holds with two ground nonces, at
  42.0–49.0 hours.
- **At 20 s no candidate holds a third.** The wait is 82.6 hours without grinding.
- **In slots a deflated inference costs about an eighth at 10 s, and helps at 1 s.** Against a
  third it lengthens the wait from 26.3 to 29.8 hours, where in blocks it raised B2's depth by 61 %
  (G7).
  The honest stake then fills slots at `f`, so the chain grows faster in slots while the delay
  weighs more in blocks. At 1 s the first wins: the wait falls from 12.0 to 8.4 hours. Under random
  delay a deflation shortens the wait: against a third from 5.1 hours to 3.4 in the convention's
  model and to 4.2 at the engine's deflated growth. At 20 s against a third the deflated bound does
  not reach `1e-9` within the 7,000 blocks computed.
- **Under random delay a `K` in slots holds about what `k` in blocks held.** On the
  specification's Blend `⌊k/f⌋` holds 0.390 at `k = 2160`, where 2,160 blocks held 0.412, and
  `3⌊k/f⌋` holds 0.419.
- **The smaller `k`s.** `3⌊k/f⌋` at `k = 1080`, 27 hours, holds a third at 10 s without grinding and
  with the nonce of §3.1, 0.329 after a deflated inference and 0.274 with two ground nonces.
  `⌊k/f⌋` at `k = 1080`, 9 hours, holds 0.257.

H19 holds: `K = ⌊k/f⌋` does not hold a third at 10 s and `1e-9`, and `K = 3⌊k/f⌋` does, with the
nonce of §3.1 under its delay, also after a deflated inference. The deflated case uses H.2's factor
at the old rates, since H.2 bounds it there only. At 194,400 slots the margin is a factor of
1.8e+07, so a factor at the raised rates up to that size leaves the verdict standing.

Gates: the share search returns the share at which a wait's chance reaches `1e-9`, and a longer
wait holds more; a deflated inference is the lottery at the raised rate
`f' = 1 − (1 − f)^(1/(1 − α))` with the shares unchanged; against a third the deflated bound lies
below the plain one at 1 s and above it at 10 s (`tests/test_k2.py`). The script also
checks that B6's shares for `k` in blocks come back from the recomputed factors. Each gate fails
under a registered mutation.

## K.3 — splits and eclipses

`src/finality_sim/floor.py` and `scripts/k3_splits.py`, with runs in `runs/k3/`. `ε = 1e-9` and
`f = 1/30`. Counts follow B5's laws: binomial at A1's growth under random delay, and the renewal law
under a worst case of `Δ = 10` s. A chain made by one share alone, at its fastest, holds one block
per slot the share occupies.

**Without a floor.** A node fixes its chain once a block the rest of the network lacks is `K` slots
old. Who made the block does not matter: the coalition, or the node itself while it is cut off.
Counted in blocks, the chain first needs `k` blocks after the divergence.

- **The self-healing horizon is `K` for every side.** In blocks a side of share `s` makes `k` blocks
  in `k / (1 − (1 − f)^s)` slots, so the horizon grows as its share falls (`MAPPING.md` §5). In
  slots it is `K`, whatever the share.
- **An eclipse fixes a fork after `K` slots and one block.** An eclipsed node that is shown a chain
  made by a share `σ`, or that makes blocks of its own, fixes that chain `K` slots after its first
  block. In blocks it needs `k + 1` of them.
- **The inference bounds both.** A chain made by `σ` alone lowers its own inferred stake. When the
  eclipse starts with the inference's window, the inference corrects in full at the next epoch,
  `10⌊k/f⌋` slots later: 7.5 days with the epoch at today's length. From then `σ` fills its slots
  at `f` (`FURTHER.md` G7). So in blocks no eclipse at `k = 2160` takes longer than 8.2 days,
  whatever `σ`.

When an eclipsed node fixes the chain it is shown, made by a share `σ`: on average, with the
inference corrected at the next epoch where that comes sooner. The two forms of the floor are
described below (`runs/k3/eclipse.csv`):

| σ | in blocks, k = 2160 (days) | slots, K = ⌊k/f⌋ (days) | slots, K = 3⌊k/f⌋ (days) | depth form at 3⌊k/f⌋ (days) | density form at ⌊k/f⌋ (days) | density form at 3⌊k/f⌋ (days) |
| --- | --- | --- | --- | --- | --- | --- |
| 0.001 | 8.24 | 1.09 | 2.59 | 8.63 | 8.25 | 9.75 |
| 0.01 | 8.17 | 0.78 | 2.28 | 8.56 | 8.25 | 9.75 |
| 0.05 | 7.87 | 0.76 | 2.26 | 8.25 | 8.25 | 9.75 |
| 0.1 | 7.39 | 0.75 | 2.25 | 7.87 | 8.25 | 9.75 |
| 0.2 | 3.70 | 0.75 | 2.25 | 5.59 | 8.25 | 9.75 |
| 0.25 | 2.96 | 0.75 | 2.25 | 4.48 | 8.25 | 9.75 |
| 0.3 | 2.47 | 0.75 | 2.25 | 3.73 | 8.25 | 9.75 |
| a third | 2.23 | 0.75 | 2.25 | 3.36 | 8.25 | 9.75 |

- In slots without a floor an eclipse takes `K` plus the first block: 0.75 or 2.25 days for every
  `σ` from a tenth up, and 1.1 or 2.6 days at `σ = 0.001`.
- In blocks the same eclipse takes 2.2 days at a third and 7.4–8.2 days from a tenth down.

**The floor.** It takes two forms:

- **The depth form.** `B_imm` moves to a block once the block is `K` slots old and `φ` blocks deep.
  This is K.0's variant: the later of a time and a depth.
- **The density form.** `B_imm` moves to a block once the `K` slots after it hold `φ` blocks. A
  chain too sparse over `K` is not fixed until its density rises, when its inference has corrected
  or the split has ended.

`φ` is the largest floor that the honest chain a coalition of `α_max` withholds from reaches within
`K` with chance at least `1 − ε`. That chain is the honest stake alone, at A1's growth under random
delay and at the renewal rate under the worst case. A protocol takes the worst case's floor, the
lower of the two, so that the chain reaches it under both models. The table gives the floor, what
it costs, and the largest side that stays below it at `K` with chance `1 − ε` at one block per
occupied slot. The last column subtracts the coalition, which can sign on the side
(`runs/k3/floor.csv`):

| K | α_max | delay | floor φ | withheld-from chain, mean | nobody withholds: waits | withheld from: waits | largest side held at K | its honest part, the coalition signing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ⌊k/f⌋, 18.0 h | 0.25 | random, specification | 1,161 | 1,375 | 2e-64 | 9e-10 | 0.445 | 0.195 |
| ⌊k/f⌋, 18.0 h | 0.25 | worst, 10 s | 1,131 | 1,300 | 9e-64 | 8e-10 | 0.432 | 0.182 |
| ⌊k/f⌋, 18.0 h | 0.3 | random, specification | 1,078 | 1,285 | 2e-82 | 1e-9 | 0.410 | 0.110 |
| ⌊k/f⌋, 18.0 h | 0.3 | worst, 10 s | 1,064 | 1,231 | 2e-82 | 8e-10 | 0.404 | 0.104 |
| ⌊k/f⌋, 18.0 h | a third | random, specification | 1,022 | 1,224 | 2e-96 | 9e-10 | 0.386 | 0.053 |
| ⌊k/f⌋, 18.0 h | a third | worst, 10 s | 1,019 | 1,184 | 2e-96 | 9e-10 | 0.385 | 0.052 |
| K.1's least against a third at 10 s, 26.3 h | 0.25 | random, specification | 1,751 | 2,012 | 6e-83 | 9e-10 | 0.475 | 0.225 |
| K.1's least against a third at 10 s, 26.3 h | 0.25 | worst, 10 s | 1,697 | 1,902 | 1e-81 | 8e-10 | 0.459 | 0.209 |
| K.1's least against a third at 10 s, 26.3 h | 0.3 | random, specification | 1,628 | 1,879 | < 1e-99 | 1e-9 | 0.439 | 0.139 |
| K.1's least against a third at 10 s, 26.3 h | 0.3 | worst, 10 s | 1,599 | 1,801 | < 1e-99 | 9e-10 | 0.430 | 0.130 |
| K.1's least against a third at 10 s, 26.3 h | a third | random, specification | 1,545 | 1,791 | < 1e-99 | 9e-10 | 0.414 | 0.081 |
| K.1's least against a third at 10 s, 26.3 h | a third | worst, 10 s | 1,532 | 1,731 | < 1e-99 | 1e-9 | 0.411 | 0.077 |
| 3⌊k/f⌋, 54.0 h | 0.25 | random, specification | 3,750 | 4,126 | < 1e-99 | 9e-10 | 0.520 | 0.270 |
| 3⌊k/f⌋, 54.0 h | 0.25 | worst, 10 s | 3,607 | 3,901 | < 1e-99 | 9e-10 | 0.499 | 0.249 |
| 3⌊k/f⌋, 54.0 h | 0.3 | random, specification | 3,491 | 3,854 | < 1e-99 | 9e-10 | 0.482 | 0.182 |
| 3⌊k/f⌋, 54.0 h | 0.3 | worst, 10 s | 3,403 | 3,693 | < 1e-99 | 9e-10 | 0.469 | 0.169 |
| 3⌊k/f⌋, 54.0 h | a third | random, specification | 3,318 | 3,673 | < 1e-99 | 9e-10 | 0.457 | 0.123 |
| 3⌊k/f⌋, 54.0 h | a third | worst, 10 s | 3,264 | 3,551 | < 1e-99 | 9e-10 | 0.449 | 0.115 |

- **At `K = 3⌊k/f⌋` the floor exceeds `k = 2160`.** Against a third it is 3,264 blocks under the
  worst case and 3,318 under random delay. At `K = ⌊k/f⌋` it is 1,019–1,022.
- **It costs nothing where nobody withholds.** A chain at the full rate falls below the floor with
  chance below `1e-63` at `⌊k/f⌋` and below `1e-99` at `3⌊k/f⌋`. The chain a coalition of `α_max`
  withholds from falls below it with chance at most `ε`. Finality then waits for the next block
  whose depth or window reaches the floor.
- **What it buys against an eclipse.** Under the depth form the eclipsed chain needs `φ + 1`
  blocks: 3.4 days at a third and 5.6 days at 0.2. At the smallest `σ` it takes 8.6 days, once its
  inference has corrected. Under the density form a chain made by any `σ` up to a third is never
  dense enough over `K`. It is fixed only after its inference corrects and a window after that is
  full: 9.75 days at `3⌊k/f⌋` and 8.25 days at `⌊k/f⌋`. In blocks the same eclipse takes 2.2–8.2
  days.

The depth form's `φ + 1` blocks and today's `k + 1`, made by `σ` alone without the inference's
correction: on average, and the earliest by which they come with chance `1e-9`
(`runs/k3/eclipse.csv`):

| σ | k = 2160 blocks: mean (days) | k = 2160 blocks: at 1e-9 (days) | φ + 1 = 3,265 blocks at 3⌊k/f⌋: mean (days) | the same at 1e-9 (days) |
| --- | --- | --- | --- | --- |
| 0.001 | 738 | 647 | 1,115 | 1,002 |
| 0.01 | 73.8 | 64.7 | 111 | 100 |
| 0.05 | 14.8 | 12.9 | 22.3 | 20.1 |
| 0.1 | 7.39 | 6.48 | 11.2 | 10.0 |
| 0.2 | 3.70 | 3.25 | 5.59 | 5.03 |
| 0.25 | 2.96 | 2.60 | 4.48 | 4.03 |
| 0.3 | 2.47 | 2.17 | 3.73 | 3.36 |
| a third | 2.23 | 1.95 | 3.36 | 3.02 |

**What the floor buys against a partition.** A side fixes its fork once its chain reaches the
floor.

- **Under the depth form, after `φ + 1` blocks.** At `k = 2160`, at one block per occupied slot, an
  even side fixes at 54 hours, a 0.3 side at 90 and a 0.2 side at 134. In blocks they take 36, 59
  and 89 hours.
- **Under the density form, a side below the floor's density stays provisional until its inference
  corrects.** Sides of 0.3 and 0.2 then fix at 9.75 days at the earliest. An even side at one block
  per occupied slot reaches the floor at `K`. Two even sides grew at 0.80 per occupied slot on the
  engine (I.3), and at that growth an even side stays below the floor until the correction.

The self-healing horizon in hours, at its earliest, at one block per occupied slot unless stated.
The floor is the worst case's against a third at `K = 3⌊k/f⌋`, with the epoch at today's length.
`–` marks a side whose window reaches the floor with a chance between `1e-9` and one half
(`runs/k3/horizon.csv`):

| k | side's share | in blocks, today (h) | slots, K = ⌊k/f⌋ (h) | slots, K = 3⌊k/f⌋ (h) | floor φ at 3⌊k/f⌋ | depth form (h) | density form (h) | density form, the side at 0.80 (h) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2160 | 0.5 | 35.7 | 18.0 | 54.0 | 3,264 | 54.0 | 54.0 | 234.0 |
| 2160 | 0.3 | 59.3 | 18.0 | 54.0 | 3,264 | 89.6 | 234.0 | 234.0 |
| 2160 | 0.2 | 88.8 | 18.0 | 54.0 | 3,264 | 134.2 | 234.0 | 234.0 |
| 1620 | 0.5 | 26.8 | 13.5 | 40.5 | 2,415 | 40.5 | 40.5 | 220.5 |
| 1620 | 0.3 | 44.5 | 13.5 | 40.5 | 2,415 | 66.3 | 220.5 | 220.5 |
| 1620 | 0.2 | 66.6 | 13.5 | 40.5 | 2,415 | 99.3 | 220.5 | 220.5 |
| 1080 | 0.5 | 17.8 | 9.0 | 27.0 | 1,573 | 27.0 | 27.0 | 207.0 |
| 1080 | 0.3 | 29.6 | 9.0 | 27.0 | 1,573 | 43.2 | 207.0 | 207.0 |
| 1080 | 0.2 | 44.4 | 9.0 | 27.0 | 1,573 | 64.7 | 207.0 | 207.0 |
| 432 | 0.5 | 7.1 | 3.6 | 10.8 | 583 | 10.8 | 10.8 | – |
| 432 | 0.3 | 11.9 | 3.6 | 10.8 | 583 | 16.0 | 190.8 | 190.8 |
| 432 | 0.2 | 17.8 | 3.6 | 10.8 | 583 | 24.0 | 190.8 | 190.8 |
| 216 | 0.5 | 3.6 | 1.8 | 5.4 | 266 | 5.4 | 5.4 | – |
| 216 | 0.3 | 5.9 | 1.8 | 5.4 | 266 | 7.3 | – | 185.4 |
| 216 | 0.2 | 8.9 | 1.8 | 5.4 | 266 | 11.0 | 185.4 | 185.4 |
| 120 | 0.5 | 2.0 | 1.0 | 3.0 | 131 | 3.0 | 3.0 | 3.0 |
| 120 | 0.3 | 3.3 | 1.0 | 3.0 | 131 | 3.6 | – | – |
| 120 | 0.2 | 4.9 | 1.0 | 3.0 | 131 | 5.4 | 183.0 | 183.0 |

**A floor as a quorum.** The coalition signs on both sides of a partition. The two sides therefore
reach the floor together once `h_1 + α` and `h_2 + α` both do, with `h_1 + h_2 = 1 − α`, and the
smaller side holds at most `(1 + α)/2`. Under the density form a floor separates the sides of every
partition only if two conditions hold. A side of `(1 + α)/2`, at its fastest, reaches it with
chance at most `ε`. The honest chain the coalition withholds from reaches it with chance at least
`1 − ε`. This is H.1's bound, with blocks as the votes. A side is fastest at one block per slot it
occupies. Under the worst case no delay slows it, and under random delay the coalition's blocks
need not be orphaned. The table gives the least `K` at which a floor exists, beside the seats of
H.1's attestation round, whose safety is at `1e-9` and liveness at `1e-6`
(`runs/k3/quorum.csv`):

| α | model | honest chain withheld from, blocks per 1,000 slots | side of (1 + α)/2, blocks per 1,000 slots | least K (days) | floor at it | at 3⌊k/f⌋: honest tail / side tail | H.1's seats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.2 | random, the side at one block per occupied slot | 22.62 | 20.14 | 5.65 | 10,417 | 4,010 / 4,292 | 832 |
| 0.2 | random, the side at 0.863 | 22.62 | 17.38 | 1.18 | 2,034 | 4,010 / 3,730 | 832 |
| 0.2 | worst, 1 s | 26.06 | 20.14 | 1.04 | 2,068 | 4,661 / 4,292 | 832 |
| 0.2 | worst, 5 s | 23.60 | 20.14 | 2.63 | 4,980 | 4,237 / 4,292 | 832 |
| 0.2 | worst, 10 s | 21.11 | 20.14 | 28.4 | 50,670 | 3,806 / 4,292 | 832 |
| 0.25 | random, the side at one block per occupied slot | 21.22 | 20.97 | 516 | 940,407 | 3,750 / 4,461 | 2,271 |
| 0.25 | random, the side at 0.863 | 21.22 | 18.09 | 3.27 | 5,549 | 3,750 / 3,876 | 2,271 |
| 0.25 | worst, 1 s | 24.49 | 20.97 | 2.91 | 5,700 | 4,367 / 4,461 | 2,271 |
| 0.25 | worst, 5 s | 22.31 | 20.97 | 17.5 | 32,754 | 3,993 / 4,461 | 2,271 |
| 0.25 | worst, 10 s | 20.07 | 20.97 | none | – | 3,607 / 4,461 | 2,271 |
| 0.3 | random, the side at one block per occupied slot | 19.83 | 21.79 | none | – | 3,491 / 4,630 | 14,966 |
| 0.3 | random, the side at 0.863 | 19.83 | 18.81 | 30.5 | 50,961 | 3,491 / 4,022 | 14,966 |
| 0.3 | worst, 1 s | 22.91 | 21.79 | 28.4 | 54,835 | 4,073 / 4,630 | 14,966 |
| 0.3 | worst, 5 s | 20.99 | 21.79 | none | – | 3,745 / 4,630 | 14,966 |
| 0.3 | worst, 10 s | 19.00 | 21.79 | none | – | 3,403 / 4,630 | 14,966 |
| a third | random, the side at one block per occupied slot | 18.89 | 22.35 | none | – | 3,318 / 4,742 | none |
| a third | random, the side at 0.863 | 18.89 | 19.29 | none | – | 3,318 / 4,119 | none |
| a third | worst, 1 s | 21.86 | 22.35 | none | – | 3,876 / 4,742 | none |
| a third | worst, 5 s | 20.10 | 22.35 | none | – | 3,578 / 4,742 | none |
| a third | worst, 10 s | 18.27 | 22.35 | none | – | 3,264 / 4,742 | none |

- **At a third no floor exists at any `K`.** There `(1 + α)/2 = 1 − α`. A side that holds the
  coalition's blocks grows at least as fast as the honest chain the coalition withholds from.
- **Under the worst case the honest chain loses `Δ` a block, and the side loses nothing.** At 10 s
  no floor separates a quarter at any `K`. At 5 s it takes 17.5 days, and at 1 s 2.9.
- **Under random delay it rests on the side's growth.** At one block per occupied slot it takes
  516 days against a quarter, and nothing works against 30 %. At 0.863 per occupied slot, the
  fastest a side grew on the engine, it takes 3.3 days and 30.5 days.
- **At `K = 3⌊k/f⌋` no floor separates partitions against a quarter in any model.** In every row
  the honest chain's lower tail lies below the side's upper tail.
- **Seats are better votes than blocks.** H.1's round separates a quarter with 2,271 seats and
  30 % with 14,966. A seat is drawn in proportion to stake whatever the delay. A block of the
  honest chain is lost to delay; a block of a side the coalition fills is not.

**The Bootstrap rule, the offline grace period and recovery.** The Bootstrap rule's window and the
offline grace margin against `K`, with the epoch at today's length (`runs/k3/bootstrap.csv`):

| k | s_gen = ⌊k/4f⌋ (h) | window B5 needs against a third, random / worst 10 s (h) | K = ⌊k/f⌋ / 3⌊k/f⌋ (h) | rule 5's cap (h) | K / T_offline |
| --- | --- | --- | --- | --- | --- |
| 2160 | 4.50 | 4.9 / 4.8 | 18.0 / 54.0 | 72.0 | 54.0 / 162.0 |
| 1620 | 3.38 | 4.9 / 4.8 | 13.5 / 40.5 | 72.0 | 40.5 / 121.5 |
| 1080 | 2.25 | 4.9 / 4.8 | 9.0 / 27.0 | 72.0 | 27.0 / 81.0 |
| 432 | 0.90 | 4.9 / 4.8 | 3.6 / 10.8 | 72.0 | 10.8 / 32.4 |
| 216 | 0.45 | 4.9 / 4.8 | 1.8 / 5.4 | 72.0 | 5.4 / 16.2 |
| 120 | 0.25 | 4.9 / 4.8 | 1.0 / 3.0 | 72.0 | 3.0 / 9.0 |

- **Rule 2 holds by construction.** A fork diverges before `B_imm` when its divergence block's
  slot is at most `sl − K`. That reads the same from either branch, so every node holding both
  chains decides alike. §10's finding cannot occur: nodes on the two sides of a split no longer
  choose different chains until both pass `k`.
- **Rule 3 holds whenever the window fits in `K`.** A fork that diverges before `B_imm` is at least
  `K` slots old, so both chains hold the whole window. Both candidates exceed the 4.8–4.9 hours a
  window needs against a third at `1e-9` per window (B5). Today's `s_gen = ⌊k/4f⌋`, 4.5 hours at
  `k = 2160` and 15 minutes at `k = 120`, falls short of it. Rule 4 still sizes the window for
  `(α, ε, H)`, apart from `K`.
- **Rule 5 keeps its cap.** With the epoch at today's length, a fork's own nonce and inferred stake
  take effect 72 hours after its divergence, whatever `K`.
- **The density form is rule 8 applied to `B_imm`.** Under random delay its floor is H.1's
  detector threshold over a window of `K`: the same lower tail of the same count, gated in
  `tests/test_floor.py`. A node whose chain is sparse then never fixes its fork. An eclipse or a
  sparse partition heals by the Online rule when it ends, with no trigger. The trigger's rules
  matter only for a chain that was dense, or for a split that outlasts the inference's correction.
- **The floor holds only until the inference corrects.** A side keeps the thresholds set before
  the split for at least `4⌊k/f⌋` slots, 3 days at `k = 2160`, and has corrected in full 7.5 to 15
  days after it (H.1). From then every chain, the coalition's fork included, fills its slots at `f`
  and reaches either form of the floor.
- **`B_imm` must not move on time alone.** Without a floor, a node that receives no blocks for `K`
  slots sees `B_imm` reach its own tip. A node offline that long would come back fixed on whatever
  tip it held. Today a node offline for longer than `T_offline`, 20 minutes, takes the Bootstrap
  rule, which freezes `B_imm`. At `k = 2160`, `K` is 54 or 162 times `T_offline`. Either form of
  the floor also keeps `B_imm` from passing a block that `φ` blocks do not follow.
- **What the floor leaves to operators.** A split that outlasts the inference's correction. A
  partition at a third, where the coalition fills both sides. Below a third, every split that the
  quorum table does not separate at the chosen `K`. H.1's attestation round separates those while
  Blend's relays deliver the votes.

H.1's detector over a window of `K`: the chance that a side holding a share of all stake falls
below the threshold, under random delay at A1's growth. The whole honest stake gives the false
alarm (`runs/k3/detector.csv`):

| K | α | expected, honest alone | threshold | side 0.35 | side 0.50 | side 0.57 | side 0.60 | side 0.65 | side 0.70 | the whole honest chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ⌊k/f⌋, 18 h | 0.3 | 1,285 | 1,078 | 1.0000 | 1.0000 | 0.8177 | 0.2197 | 3e-04 | 1e-09 | 1e-09 |
| ⌊k/f⌋, 18 h | a third | 1,224 | 1,022 | 1.0000 | 0.9995 | 0.2015 | 0.0062 | 1e-07 | 8e-15 | 9e-10 |
| 3⌊k/f⌋, 54 h | 0.3 | 3,854 | 3,491 | 1.0000 | 1.0000 | 1.0000 | 0.9992 | 0.0613 | 9e-10 | 9e-10 |
| 3⌊k/f⌋, 54 h | a third | 3,673 | 3,318 | 1.0000 | 1.0000 | 0.9989 | 0.5597 | 3e-06 | 2e-19 | 9e-10 |

- At `3⌊k/f⌋` against a third the detector declares a side of 0.57 of all stake sparse with
  chance 0.999, and one of 0.6 with chance 0.56. It declares the whole honest chain sparse once in
  `10^9` windows.
- At `⌊k/f⌋` it still sees an even side, and few larger ones.

**Verdicts.**

- **H20 holds.** Without a floor an eclipse of `K` slots fixes a fork whatever the stake, with one
  block. At `K = 3⌊k/f⌋` a floor sized at `1e-9` for the honest chain a third withholds from is
  3,264 blocks under the worst case and 3,318 under random delay, more than `k = 2160`. A chain
  nobody withholds from falls below it with chance below `1e-99`. At the smallest stake both forms
  meet the inference's correction as blocks do: 8.2 days in blocks, 8.6 under the depth form and
  9.75 under the density form.
- **H21 fails in its first part.** At `K = 3⌊k/f⌋` no floor separates the sides of every partition
  against a quarter, in either model. The least `K` is 2.9 days under the worst case at 1 s, 17.5
  days at 5 s, and none at 10 s. Under random delay it is 3.3 days with the side at the engine's
  0.863, and 516 days with the side at one block per occupied slot. The second part holds: at a
  third no floor exists at any `K`.

Gates (`tests/test_floor.py`):

- the counts are B5's laws in both models;
- the floor is the largest the withheld-from chain reaches at `ε`, and under random delay it is
  H.1's detector threshold;
- the safe floor is the smallest a side reaches at `ε`, and the provisional share reaches the floor
  at `ε`;
- the least quorum window is the first that separates, by direct binomial and renewal tails, and
  no window exists where the side grows as fast;
- the eclipse time is the blocks' lower tail;
- after the correction a chain fills its slots at `f`, sampled slot by slot;
- a sparse chain waits for its correction under the density form.

Each fails under a registered mutation (`scripts/check_mutations.py`).

## K.4 — the nonce and the epoch

**What does not move.** The nonce's rules count the walk's blocks and the epoch's slots, never the
unit of `k`. With the epoch at its length at `k = 2160` (K.0), B7's sub-windows stay 15,552 slots
at `m = 25`. H.2's delay still spans the last sub-window and a margin, 4.5 hours on the coalition's
hardware. The lottery constants are still fixed `4⌊k/f⌋` slots, 72 hours, before their epoch. B6's
choices at the cut-off, B7's estimate and H.2's lemma read the coalition's lead backwards from the
cut-off, which no rule about `B_imm` changes. A factor `F` per nonce multiplies the chance against
one schedule, so a wait absorbs it where its chance is at most `ε/F`: K.2 reads the factor off
K.1's wait instead of B2's depth.

**What moves: how long a race lasts.** Counted in blocks, a race against a target lasts until the
target lies deep enough, however long the chain takes. Against a third under the worst case at
10 s, B6's two-nonce depth takes 96 hours on the worst-case clock, 24 past the 72 hours from a
cut-off to the next epoch's first slot. A target within 24 hours before a cut-off then races into
the next epoch with a private chain that holds the cut-off. It meets a nonce the coalition picks
itself, and no bound covers it (`SETTLEMENT.md` B6): 24 of each epoch's 180 hours, 13 % of
targets. Counted in slots, the Online
rule ignores a fork that diverges before `B_imm`, so a race lasts at most `K` slots after its
target (`finality_sim.slotmap`):

- **A target meets two ground nonces** only past its epoch's cut-off and within `K` slots of the
  epoch's end: 10 % of targets at `K = ⌊k/f⌋` and 30 % at `K = 3⌊k/f⌋`, at `k = 2160`.
- **No target meets a nonce its own private chain set** while `K` is at most the `4⌊k/f⌋` slots
  from a cut-off to the next epoch. Both candidates are, at every `k` of B5 (`MAPPING.md` §7), so
  B6's bounds cover every target.
- **A `K` past `4⌊k/f⌋` uncovers targets again.** If the `K` that holds a share under a nonce's
  factor exceeds 72 hours, the targets within `K − 4⌊k/f⌋` slots before a cut-off race into an
  epoch whose nonce their private chain set, as in B6. K.2 gives the `K` each factor needs. With
  today's nonce, against a third under the worst case at 10 s, B6's two-nonce depth alone takes 96
  hours.

**The epoch's phases.** The specification already times the epoch in slots that stand for
finality (`cryptarchia-v1-protocol.md`, Epoch Schedule). The snapshot phase lasts `s` slots: "We
wait for this value to finalize before entering the next phase". The buffer phase waits "another
slot finality period". The lottery constants wait "another `4k/f` slots for these values to
finalize". Counted in slots a value is final once `K` slots have passed, so each phase that waits
for finality must last at least `K`: the snapshot phase, `s` slots, and the constants' lead,
`4⌊k/f⌋`. Both candidates fit. `K = ⌊k/f⌋` leaves the phases three and four windows long. `K = s`
makes the snapshot phase one window and the constants' lead one and a third. The buffer phase
exists so that an honest leader contributes to the nonce, which rests on the honest stake's wins
over its slots, not on finality (`MAPPING.md` §6). A `K` above `s` would need the phases to grow
with it. The inference's period, `6⌊k/f⌋` slots, keeps its length with the epoch. G7's deflation
becomes a time (K.2).

## K.5 — every other result, read again

Each note ends with a section that reads it in slots:

- **`MAPPING.md` §7.** The rules of §1 with `K`. `B_imm` trails the clock by `K` slots, so every
  consumer waits a fixed time. The `k`-sized quantities at both candidates, and the self-healing
  horizon, which becomes `K` for every side.
- **`RATE.md`.** k-finality no longer shrinks with the block rate. Under the worst case at 10 s a
  faster rate needs a longer `K`: against a third the wait K.1 bounds grows from 26.3 hours at 30 s
  blocks to 29.6 at 20 s and 41.1 at 15 s.
- **`FURTHER.md`.** G3: from the specification's Blend to testnet's, the worst-case wait against a
  third falls to 45 %, where the depth falls to 49 %. G4: a wait gains nothing on a chain nobody
  withholds from. G6: hostile relays cost more as a wait than as a depth, 56 % against 47 % for
  relays that drop, with two copies. G7: a deflation costs less in time than in blocks (K.2).
- **`DESIGNS.md`.** H.1's seats and H.2 do not move. H.1's trigger fires at one slot for every
  node holding both chains. H.3's rules already read time.
- **`CERTIFIED.md`.** Settlement becomes a wait. Certificates stall in a partition, where a window
  in slots without a floor finalizes both sides.
- **`DAG.md`.** J.0 already counted `k` in slots, so nothing moves; retraction outlasts every `K`.
- **`SETTLEMENT.md`.** B2–B7, each pointed to its part of K.1–K.4.

## K.7 — a wait in GRR's own model

`src/finality_sim/waitbound.py` and `scripts/k7_wait.py`, with runs in `runs/k7/`.

**Why K.1's bound is loose.** B2 freezes LCanalysis's chain at the earliest moment the target could
lie `D` deep: when the coalition's lead, the honest successes and twice the coalition's successes
since the target reach `D`. Against a third that count grows by `4/3` a block interval. K.1 then
also waits for the honest chain to grow `D` blocks at its slowest, about `0.55` a block interval at
10 s. Each step is sound. Together they ask for B2's depth at the honest chain's slowest pace, where
B2 itself froze more than twice as early.

**The bound.** The paper's Lemma 10 keeps the prefix up to slot `ℓ` in every dominant chain from
`t` on if the margin `μ_ℓ` is negative at every time from `t`. A wait of `T` slots fixes that
prefix at `ℓ + T`, so it fails only if `μ_ℓ ≥ 0` at some time from `ℓ + T`. LCanalysis's chain bounds
the margin phase by phase. The bound runs the same chain, with the same symbols, transitions, final
vector and stationary reach where it starts, and freezes it at the phase in which the wait passes
instead of at B2's count:

- **The clock.** A phase is a wait for the next success, exponential with a mean of one block
  interval, and, for a phase of `h` honest successes, a span below `h·Δ`. The clock counts each
  wait rounded up to a slot and each span as `h·Δ`, so it runs ahead of time. The chain therefore
  freezes at, or before, the phase in which `T` passes, and keeps the state after that phase, which
  bounds the margin over all of it.
- **The start.** The phase that covers the target is weighted by its length, which is at most its
  wait plus `h·Δ`, over the mean phase, `1/g` block intervals with `g = e^(−(1 − α)·D)` and `D` the
  delay in block intervals. The clock starts at that phase's start, before the target. The weights
  add `g + (1 − α)·D − 1` to the mass.
- **Slots.** The paper computes in continuous time, and B2 reads it at `D = f·Δ`. On the lottery a
  phase also holds the slot of its first honest success, so the coalition wins in `Δ + 1` slots of
  a lone honest success, where continuous time gives it `Δ`. The bound runs the chain at `Δ + 1`
  slots and `λ = −ln(1 − f)` successes a slot, whose chance of at least one success per slot is the
  lottery's. Per honest phase the coalition then wins at least as often as on the lottery, and the
  honest depth needs gaps of `Δ + 1`. The continuous reading, at `Δ` and `f`, sits beside it.

The attack's estimate – the bound on slots, in hours, beside K.1's table (`runs/k7/worst.csv`):

ε = 1e-6, hours

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 0.2 – 0.2 | ≤ 0.2 – 0.2 | ≤ 0.2 – 0.2 | ≤ 0.2 – 0.3 | ≤ 0.2 – 0.3 | ≤ 0.2 – 0.4 | ≤ 0.3 – 0.5 | ≤ 0.3 – 0.8 |
| 0.10 | 0.2 – 0.3 | 0.2 – 0.4 | 0.2 – 0.4 | 0.2 – 0.4 | 0.2 – 0.5 | 0.3 – 0.5 | 0.3 – 0.8 | 0.4 – 1.2 |
| 0.15 | 0.3 – 0.5 | 0.3 – 0.5 | 0.3 – 0.6 | 0.4 – 0.6 | 0.4 – 0.7 | 0.4 – 0.8 | 0.5 – 1.1 | 0.6 – 1.7 |
| 0.20 | 0.5 – 0.8 | 0.5 – 0.8 | 0.5 – 0.8 | 0.6 – 0.9 | 0.7 – 1.1 | 0.7 – 1.3 | 0.9 – 1.8 | 1.1 – 2.8 |
| 0.25 | 0.8 – 1.2 | 0.9 – 1.3 | 0.9 – 1.3 | 1.0 – 1.5 | 1.2 – 1.8 | 1.3 – 2.1 | 1.7 – 3.1 | 2.2* – 4.9 |
| 0.30 | 1.5* – 2.0 | 1.6* – 2.2 | 1.7* – 2.3 | 1.9* – 2.7 | 2.3* – 3.3 | 2.6* – 3.9 | 3.6* – 6.2 | 5.0* – 10.7 |
| a third | 2.3* – 3.1 | 2.5* – 3.4 | 2.7* – 3.6 | 3.1* – 4.2 | 3.8* – 5.5 | 4.4* – 6.7 | 6.7* – 11.5 | 10.5* – 22.3 |

ε = 1e-9, hours

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ≤ 0.2 – 0.4 | ≤ 0.2 – 0.4 | ≤ 0.2 – 0.4 | ≤ 0.2 – 0.4 | 0.2 – 0.5 | 0.2 – 0.5 | 0.3 – 0.8 | 0.3 – 1.2 |
| 0.10 | 0.3 – 0.5 | 0.3 – 0.6 | 0.3 – 0.6 | 0.3 – 0.6 | 0.4 – 0.7 | 0.4 – 0.8 | 0.5 – 1.2 | 0.6 – 1.7 |
| 0.15 | 0.5 – 0.8 | 0.5 – 0.8 | 0.5 – 0.9 | 0.6 – 0.9 | 0.6 – 1.1 | 0.7 – 1.2 | 0.8 – 1.7 | 1.0 – 2.6 |
| 0.20 | 0.8 – 1.2 | 0.8 – 1.2 | 0.8 – 1.3 | 0.9 – 1.4 | 1.0 – 1.7 | 1.1 – 1.9 | 1.4 – 2.7 | 1.7 – 4.2 |
| 0.25 | 1.3 – 1.8 | 1.3 – 1.9 | 1.4 – 2.0 | 1.5* – 2.3 | 1.8* – 2.8 | 2.0* – 3.2 | 2.6* – 4.7 | 3.3* – 7.4 |
| 0.30 | 2.2* – 3.1 | 2.4* – 3.3 | 2.5* – 3.5 | 2.9* – 4.0 | 3.4* – 5.0 | 3.9* – 5.9 | 5.4* – 9.4 | 7.7* – 16.1 |
| a third | 3.5* – 4.7 | 3.8* – 5.1 | 4.1* – 5.5 | 4.7* – 6.4 | 5.8* – 8.4 | 6.8* – 10.1 | 10.2* – 17.4 | 16.0* – 33.5 |

K.1's bound over the continuous reading, at `1e-9`:

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 2.55 | 2.60 | 2.64 | 2.72 | 2.81 | 2.84 | 2.76 | 2.57 |
| 0.10 | 2.56 | 2.60 | 2.63 | 2.70 | 2.77 | 2.79 | 2.76 | 2.63 |
| 0.15 | 2.57 | 2.60 | 2.63 | 2.69 | 2.75 | 2.78 | 2.77 | 2.68 |
| 0.20 | 2.59 | 2.62 | 2.65 | 2.70 | 2.76 | 2.78 | 2.79 | 2.74 |
| 0.25 | 2.61 | 2.64 | 2.67 | 2.72 | 2.78 | 2.80 | 2.83 | 2.80 |
| 0.30 | 2.65 | 2.68 | 2.70 | 2.75 | 2.81 | 2.84 | 2.88 | 2.88 |
| a third | 2.68 | 2.71 | 2.73 | 2.78 | 2.84 | 2.87 | 2.92 | 2.93 |

The bound on slots over the continuous reading, at `1e-9`:

| α | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 1.010 | 1.013 | 1.017 | 1.027 | 1.045 | 1.058 | 1.089 | 1.108 |
| 0.10 | 1.015 | 1.018 | 1.021 | 1.029 | 1.043 | 1.054 | 1.082 | 1.105 |
| 0.15 | 1.020 | 1.023 | 1.026 | 1.033 | 1.045 | 1.055 | 1.080 | 1.105 |
| 0.20 | 1.026 | 1.029 | 1.032 | 1.039 | 1.050 | 1.059 | 1.083 | 1.109 |
| 0.25 | 1.034 | 1.037 | 1.040 | 1.047 | 1.058 | 1.067 | 1.092 | 1.121 |
| 0.30 | 1.045 | 1.048 | 1.052 | 1.060 | 1.073 | 1.082 | 1.111 | 1.147 |
| a third | 1.056 | 1.060 | 1.064 | 1.073 | 1.089 | 1.101 | 1.137 | 1.187 |

Reading:

- **A wait needs well under half of what K.1 read.** Against a third at 10 s and `1e-9` the bound
  is 10.1 hours on slots and 9.2 in the continuous reading, where K.1 bounds 26.3. K.1 is 2.55
  to 2.93 times the continuous reading at every cell. Against 30 % the bound is 5.9 hours, against
  15.5.
- **It lies below B2's depth on its own clock.** 1,510 blocks take 23.0 hours on the worst-case
  clock at 10 s, and the wait is 10.1. The proven wait now asks less time than the proven depth.
- **Under the worst case at 2 to 3 s a wait costs what random delay costs on the specification's
  Blend.** Against a third the bound on slots is 4.7 hours at 1 s and 5.5 at 3 s, where the
  random-delay wait is 5.10.
- **The slot costs 1 to 19 %.** It weighs most where the delay is long and the coalition large,
  where the bound lies nearest the edge of the secure region: 10 % against a third at 10 s and 19 %
  at 20 s.
- **Against a third the attack's estimate lies at 0.48 to 0.75 of the bound,** nearest at short
  delays: 3.5 hours against 4.7 at 1 s, 6.8 against 10.1 at 10 s, and 16.0 against 33.5 at 20 s.
- **B2 itself freezes at half the paper's count.** The paper's text puts the earliest error at
  `ρ + h + 2a ≥ 2k`: two chains of `k` blocks above the target, the coalition's wins counting on
  both. The code freezes at `ρ + h + 2a ≥ k`, and its Table 1 uses that count. At the text's count
  B2's depth at `1e-9` halves: 755 blocks against a third at 10 s instead of 1,510, and 446 against
  30 % instead of 892. The study keeps the code's count for every depth in blocks.

**Checks.** The wait with half-slot levels, with twice the states, and with each phase's span
charged at the depth it adds, which the span exceeds, so that the last is no bound and brackets
what the `h·Δ` charge costs (`runs/k7/checks.csv`):

| α | Δ | variant | wait at 1e-6 (h) | wait at 1e-9 (h) |
| --- | --- | --- | --- | --- |
| a third | 10 s | the bound | 6.69 | 10.11 |
| a third | 10 s | half-slot levels | 6.64 | 10.04 |
| a third | 10 s | twice the states | 6.69 | 10.11 |
| a third | 10 s | spans at the depth they add | 6.37 | 9.64 |
| a third | 20 s | the bound | 22.30 | 33.47 |
| a third | 20 s | half-slot levels | 22.19 | 33.31 |
| a third | 20 s | twice the states | 22.33 | 33.53 |
| a third | 20 s | spans at the depth they add | 19.09 | 28.76 |
| 0.10 | 10 s | the bound | 0.54 | 0.81 |
| 0.10 | 10 s | half-slot levels | 0.53 | 0.81 |
| 0.10 | 10 s | twice the states | 0.54 | 0.81 |
| 0.10 | 10 s | spans at the depth they add | 0.49 | 0.75 |
| a third | 1 s | the bound | 3.12 | 4.75 |
| a third | 1 s | half-slot levels | 3.09 | 4.71 |
| a third | 1 s | twice the states | 3.12 | 4.75 |
| a third | 1 s | spans at the depth they add | 3.11 | 4.74 |

- Half-slot levels shorten the bound by under 1 %, and twice the states change it by under 0.2 %.
- The `h·Δ` charge costs 4.6 % against a third at 10 s and 14 % at 20 s, where phases hold most
  honest successes.

**The bound against its chain and against the attack.** The continuous reading beside its chain
played on phases drawn in continuous time with their true lengths, targets at uniform times; and
the bound on slots beside the paper's attack played against a wait on the slot lottery. The
attack's late successes come in clusters, one long-lived fork beating many targets in a row, so its
standard error is the spread of 16 runs' rates (`runs/k7/played.csv`):

| α | Δ | wait (h) | continuous reading | its chain, true lengths | reading over its chain | bound on slots | the paper's attack on slots |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a third | 10 s | 0.25 | 4.65e-01 | 4.31e-01 ± 6.2e-04 | 1.08 | 5.04e-01 | 3.51e-01 ± 2.1e-03 |
| a third | 10 s | 0.50 | 2.51e-01 | 2.29e-01 ± 5.3e-04 | 1.10 | 2.87e-01 | 1.68e-01 ± 1.8e-03 |
| a third | 10 s | 1.00 | 7.89e-02 | 6.90e-02 ± 3.2e-04 | 1.14 | 1.00e-01 | 4.47e-02 ± 8.4e-04 |
| a third | 10 s | 2.00 | 8.37e-03 | 5.97e-03 ± 9.6e-05 | 1.40 | 1.29e-02 | 3.40e-03 ± 3.5e-04 |
| 0.25 | 5 s | 0.25 | 5.66e-02 | 4.83e-02 ± 2.7e-04 | 1.17 | 6.52e-02 | 3.71e-02 ± 6.9e-04 |
| 0.25 | 5 s | 0.50 | 5.32e-03 | 4.56e-03 ± 8.4e-05 | 1.17 | 6.78e-03 | 2.80e-03 ± 1.7e-04 |
| 0.25 | 5 s | 1.00 | 5.20e-05 | 2.03e-05 ± 5.6e-06 | 2.56 | 8.07e-05 | 1.16e-05 ± 8.5e-06 |
| 0.25 | 5 s | 2.00 | 5.21e-09 | 0 | – | 1.19e-08 | 0 |
| a third | 1 s | 0.25 | 2.04e-01 | 1.91e-01 ± 4.9e-04 | 1.07 | 2.22e-01 | 1.82e-01 ± 1.4e-03 |
| a third | 1 s | 0.50 | 6.10e-02 | 5.76e-02 ± 2.9e-04 | 1.06 | 7.06e-02 | 5.23e-02 ± 1.0e-03 |
| a third | 1 s | 1.00 | 6.16e-03 | 5.99e-03 ± 9.6e-05 | 1.03 | 8.01e-03 | 4.69e-03 ± 3.2e-04 |
| a third | 1 s | 2.00 | 6.93e-05 | 3.91e-05 ± 7.8e-06 | 1.77 | 1.13e-04 | 7.08e-05 ± 5.5e-05 |

- **The clock costs little.** The continuous reading lies 3 to 40 % above its chain where the
  chain fails more often than once in a thousand, more as the wait grows, since the clock's lead
  over time accumulates; and up to 2.56 times above where the chain's rate rests on a few dozen
  failures.
- **The bound on slots lies above the attack at every wait.** The attack reaches 0.82 of it at 1 s
  and a quarter of an hour, and 0.26 to 0.70 at 10 s.

**K.2 read again.** The largest share each `K` holds at `1e-9` under the bound, with K.2's factors
(`runs/k7/holds.csv`):

K = ⌊k/f⌋

| model | case | k = 2160 | k = 1620 | k = 1080 | k = 432 | k = 216 | k = 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| worst, 1 s | no grinding | ≥ a third | ≥ a third | ≥ a third | 0.312 | 0.248 | 0.180 |
| worst, 1 s | today's nonce, one ground | ≥ a third | ≥ a third | 0.318 | 0.268 | 0.225 | 0.174 |
| worst, 1 s | today's nonce, two ground | ≥ a third | 0.326 | 0.307 | 0.260 | 0.217 | 0.169 |
| worst, 1 s | a deflated inference | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.275 | 0.205 |
| worst, 10 s | no grinding | ≥ a third | ≥ a third | 0.327 | 0.261 | 0.194 | 0.126 |
| worst, 10 s | today's nonce, one ground | 0.313 | 0.298 | 0.275 | 0.228 | 0.183 | 0.123 |
| worst, 10 s | today's nonce, two ground | 0.298 | 0.286 | 0.267 | 0.220 | 0.177 | 0.120 |
| worst, 10 s | the nonce of §3.1 under its delay | ≥ a third | ≥ a third | 0.326 | 0.261 | 0.193 | 0.125 |
| worst, 10 s | a deflated inference | ≥ a third | ≥ a third | 0.319 | 0.261 | 0.198 | 0.130 |
| worst, 20 s | no grinding | 0.306 | 0.290 | 0.264 | 0.185 | 0.104 | < 0.05 |
| worst, 20 s | today's nonce, one ground | 0.256 | 0.242 | 0.223 | 0.171 | 0.101 | < 0.05 |
| worst, 20 s | today's nonce, two ground | 0.248 | 0.235 | 0.216 | 0.165 | 0.099 | < 0.05 |
| worst, 20 s | a deflated inference | 0.270 | 0.256 | 0.233 | 0.163 | 0.091 | < 0.05 |

K = 3⌊k/f⌋

| model | case | k = 2160 | k = 1620 | k = 1080 | k = 432 | k = 216 | k = 120 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| worst, 1 s | no grinding | ≥ a third | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.297 |
| worst, 1 s | today's nonce, one ground | ≥ a third | ≥ a third | ≥ a third | 0.329 | 0.290 | 0.257 |
| worst, 1 s | today's nonce, two ground | ≥ a third | ≥ a third | ≥ a third | 0.316 | 0.281 | 0.249 |
| worst, 1 s | a deflated inference | ≥ a third | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.323 |
| worst, 10 s | no grinding | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.293 | 0.245 |
| worst, 10 s | today's nonce, one ground | ≥ a third | ≥ a third | ≥ a third | 0.285 | 0.249 | 0.217 |
| worst, 10 s | today's nonce, two ground | ≥ a third | 0.332 | 0.315 | 0.276 | 0.242 | 0.210 |
| worst, 10 s | the nonce of §3.1 under its delay | ≥ a third | ≥ a third | ≥ a third | ≥ a third | 0.293 | 0.245 |
| worst, 10 s | a deflated inference | ≥ a third | ≥ a third | ≥ a third | 0.327 | 0.289 | 0.246 |
| worst, 20 s | no grinding | ≥ a third | ≥ a third | 0.325 | 0.276 | 0.224 | 0.166 |
| worst, 20 s | today's nonce, one ground | 0.311 | 0.298 | 0.278 | 0.232 | 0.196 | 0.156 |
| worst, 20 s | today's nonce, two ground | 0.292 | 0.281 | 0.265 | 0.224 | 0.189 | 0.151 |
| worst, 20 s | a deflated inference | 0.310 | 0.301 | 0.287 | 0.244 | 0.198 | 0.146 |

At 10 s, without grinding / with two ground nonces, beside K.1's bound:

| k | K = ⌊k/f⌋: K.1's bound | K = ⌊k/f⌋: K.7's bound | K = 3⌊k/f⌋: K.1's bound | K = 3⌊k/f⌋: K.7's bound |
| --- | --- | --- | --- | --- |
| 2160 | 0.310 / 0.254 | ≥ a third / 0.298 | ≥ a third / 0.304 | ≥ a third / ≥ a third |
| 1620 | 0.290 / 0.240 | ≥ a third / 0.286 | ≥ a third / 0.292 | ≥ a third / 0.332 |
| 1080 | 0.257 / 0.218 | 0.327 / 0.267 | ≥ a third / 0.274 | ≥ a third / 0.315 |
| 432 | 0.164 / 0.153 | 0.261 / 0.220 | 0.273 / 0.228 | ≥ a third / 0.276 |
| 216 | 0.077 / 0.075 | 0.194 / 0.177 | 0.208 / 0.186 | 0.293 / 0.242 |
| 120 | < 0.05 / < 0.05 | 0.126 / 0.120 | 0.142 / 0.135 | 0.245 / 0.210 |

The wait against 30 % and a third at `1e-9` in each case, K.1's in brackets, beside the two
candidates at `k = 2160` (`runs/k7/waits.csv`):

| model | case | 30 %: wait (h), K.1's bound in brackets | a third: wait (h), K.1's bound in brackets | K = 64,800 (18 h): 30 % / a third | K = 194,400 (54 h): 30 % / a third |
| --- | --- | --- | --- | --- | --- |
| worst, 1 s | no grinding | 3.1 (7.9) | 4.7 (12.0) | yes / yes | yes / yes |
| worst, 1 s | one ground nonce, lower end | 6.2 (15.5) | 11.2 (28.3) | yes / yes | yes / yes |
| worst, 1 s | one ground nonce, upper end | 6.6 (16.7) | 11.6 (29.2) | yes / yes | yes / yes |
| worst, 1 s | two ground nonces, lower end | 6.8 (17.0) | 13.6 (34.3) | yes / yes | yes / yes |
| worst, 1 s | two ground nonces, upper end | 7.7 (19.5) | 15.8 (39.8) | yes / yes | yes / yes |
| worst, 1 s | deflated | 2.3 (5.7) | 3.4 (8.4) | yes / yes | yes / yes |
| worst, 10 s | no grinding | 5.9 (15.5) | 10.1 (26.3) | yes / yes | yes / yes |
| worst, 10 s | one ground nonce, lower end | 13.6 (35.7) | 25.9 (67.4) | yes / no | yes / yes |
| worst, 10 s | one ground nonce, upper end | 14.1 (36.8) | 26.7 (69.4) | yes / no | yes / yes |
| worst, 10 s | two ground nonces, lower end | 16.1 (42.0) | 38.3 (99.5) | yes / no | yes / yes |
| worst, 10 s | two ground nonces, upper end | 18.7 (49.0) | 42.0 (109.1) | no / no | yes / yes |
| worst, 10 s | deflated | 6.4 (15.9) | 12.4 (29.8) | yes / yes | yes / yes |
| worst, 10 s | nonce §3.1, two nonces at H.2's bound | 6.0 (15.6) | 10.2 (26.6) | yes / yes | yes / yes |
| worst, 10 s | deflated, nonce §3.1 at H.2's bound at the old rates | 6.4 (16.0) | 12.5 (30.1) | yes / yes | yes / yes |
| worst, 20 s | no grinding | 16.1 (40.4) | 33.5 (82.6) | yes / no | yes / yes |
| worst, 20 s | one ground nonce, lower end | 40.8 (102.4) | 92.8 (229.3) | no / no | yes / no |
| worst, 20 s | one ground nonce, upper end | 42.1 (105.5) | 95.5 (235.9) | no / no | yes / no |
| worst, 20 s | two ground nonces, lower end | 59.6 (149.4) | 152.2 (376.1) | no / no | no / no |
| worst, 20 s | two ground nonces, upper end | 65.7 (164.8) | 156.0 (385.4) | no / no | no / no |
| worst, 20 s | deflated | 38.9 (83.2) | 156.2 (past the curve) | no / no | yes / no |

The chance of displacement after each candidate at 10 s, and the largest grinding factor on that
chance it absorbs (`runs/k7/absorbs.csv`):

| α | K | chance after K slots | largest factor absorbed | after a deflated inference: chance / factor |
| --- | --- | --- | --- | --- |
| 0.30 | 64,800 | 9.4e-28 | 1.1e+18 | 7.2e-26 / 1.4e+16 |
| 0.30 | 194,400 | < 1e-55 | > 1e46 | < 1e-55 / > 1e46 |
| a third | 64,800 | 1.2e-16 | 8.4e+06 | 8.4e-14 / 1.2e+04 |
| a third | 194,400 | 3.2e-48 | 3.2e+38 | 8.0e-40 / 1.2e+30 |

- **`⌊k/f⌋` = 18 hours holds a third at 10 s.** Without grinding the wait is 10.1 hours, with the
  nonce of §3.1 under its delay 10.2, and after a deflated inference 12.4, or 12.5 with that nonce.
  The chance after 64,800 slots is 1.2e-16, a factor of 8.4e+06 to spare, and 8.4e-14 after a
  deflation.
- **With today's nonce 18 hours does not hold a third at 10 s.** One ground nonce needs 25.9–26.7
  hours and two need 38.3–42.0. Against 30 % 18 hours holds up to the lower end of two ground
  nonces, 16.1 hours, and not its upper end, 18.7.
- **`3⌊k/f⌋` = 54 hours holds a third at 10 s in every case**, today's nonce with two ground nonces
  included, and absorbs a factor of 3.2e+38, or 1.2e+30 after a deflation.
- **At 20 s 54 hours holds a third only without grinding or a deflation.** The wait is 33.5 hours
  without grinding, 92.8–156.0 with today's nonce and 156.2 after a deflated inference.
- **Against `k` in blocks.** At 10 s `⌊k/f⌋` slots now hold what `k = 2160` blocks hold without
  grinding, a third, and more with two ground nonces, 0.298 against 0.288 (`SETTLEMENT.md` B5, B6).

**K.3 read again.** The floor at the least `K` that holds a third at 10 s without grinding, beside
K.3's rows (`runs/k7/floor.csv`):

| K | α_max | delay | floor φ | withheld-from chain, mean | nobody withholds: waits | withheld from: waits | largest side held at K | its honest part, the coalition signing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K.7's least against a third at 10 s, 10.1 h | 0.25 | random, specification | 613 | 772 | 2e-45 | 9e-10 | 0.389 | 0.139 |
| K.7's least against a third at 10 s, 10.1 h | 0.25 | worst, 10 s | 604 | 730 | 3e-45 | 9e-10 | 0.383 | 0.133 |
| K.7's least against a third at 10 s, 10.1 h | 0.3 | random, specification | 568 | 721 | 1e-56 | 1e-9 | 0.357 | 0.057 |
| K.7's least against a third at 10 s, 10.1 h | 0.3 | worst, 10 s | 567 | 691 | 8e-57 | 9e-10 | 0.356 | 0.056 |
| K.7's least against a third at 10 s, 10.1 h | a third | random, specification | 537 | 687 | 4e-65 | 8e-10 | 0.334 | 0.001 |
| K.7's least against a third at 10 s, 10.1 h | a third | worst, 10 s | 542 | 665 | 2e-65 | 1e-9 | 0.338 | 0.005 |

- At 10.1 hours the floor against a third is 537 blocks under random delay and 542 under the worst
  case, and a protocol takes the lower, 537. It holds back a cut-off side of at most a third, so at
  so short a window the floor protects against an eclipse by the coalition and against no
  partition the coalition signs on.

**K.5 read again.** The block rate, against 25 %, 30 % and a third at 10 s, beside K.1's bound
(`runs/k7/rate.csv`):

| block interval | 0.25: K.7 / K.1 (h) | 0.30: K.7 / K.1 (h) | a third: K.7 / K.1 (h) |
| --- | --- | --- | --- |
| 30 s | 3.2 / 8.3 | 5.9 / 15.5 | 10.1 / 26.3 |
| 20 s | 3.3 / 8.1 | 6.6 / 16.1 | 12.5 / 29.6 |
| 15 s | 4.2 / 9.2 | 9.5 / 20.1 | 20.4 / 41.1 |

A1's Blend settings at their worst-case delay, beside the random-delay wait (`runs/k7/blend.csv`):

| hops | rounds | Δ | 0.30: random delay / worst, K.7 (K.1) (h) | a third: random delay / worst, K.7 (K.1) (h) |
| --- | --- | --- | --- | --- |
| 1 | 1 | 2 s | 2.0 / 3.3 (8.4) | 2.9 / 5.1 (13.0) |
| 1 | 2 | 3 s | 2.0 / 3.5 (9.1) | 3.1 / 5.5 (14.1) |
| 1 | 3 | 4 s | 2.1 / 3.8 (9.7) | 3.3 / 5.9 (15.3) |
| 1 | 5 | 6 s | 2.3 / 4.3 (11.3) | 3.6 / 7.0 (18.2) |
| 1 | 8 | 9 s | 2.7 / 5.5 (14.3) | 4.3 / 9.2 (23.9) |
| 1 | 12 | 13 s | 3.4 / 7.7 (20.2) | 5.7 / 13.8 (35.7) |
| 3 | 1 | 5 s | 2.5 / 4.0 (10.5) | 3.9 / 6.4 (16.7) |
| 3 | 2 | 8 s | 2.9 / 5.0 (13.2) | 4.7 / 8.4 (21.8) |
| 3 | 3 | 11 s | 3.1 / 6.5 (16.9) | 5.1 / 11.2 (29.0) |
| 3 | 5 | 16 s | 4.4 / 10.4 (26.7) | 8.0 / 19.6 (49.9) |
| 3 | 8 | 24 s | 5.8 / 26.7 (64.5) | 11.6 / 62.7 (147.9) |

- **Faster blocks still need a longer `K` under the worst case, by less.** Against a third at 10 s
  the wait is 10.1 hours at 30 s blocks, 12.5 at 20 s and 20.4 at 15 s, where K.1 read 26.3, 29.6
  and 41.1.
- **From the specification's Blend to testnet's** the worst-case wait against a third falls from
  11.2 hours to 5.1, to 46 %, where K.1 read 29.0 to 13.0.

**Verdict.** H22 holds. Against a third at 10 s and `1e-9` the bound is 10.1 hours on slots and 9.2
in the continuous reading, under half of K.1's 26.3, and `⌊k/f⌋` = 18 hours holds a third at 10 s
without grinding: the chance after it is 1.2e-16. H19's first part, that `⌊k/f⌋` does not hold a
third at 10 s, held under K.1's bound and fails under this one. H18 holds by more: the wait is 0.44
times B2's depth on its clock.

Gates (`tests/test_waitbound.py`):

- with LCanalysis's counts as costs and no wait, the level pass is B1's `ub_curve` within `1e-12`;
- the covering phase's weights sum to `g + (1 − α)·D`;
- the phases drawn in continuous time follow `PoSSlotPdf`'s law;
- on hand-built runs the played chain freezes in the phase in which the wait passes, and the attack
  holds two chains at the public depth until the symbols it should;
- the continuous reading lies above its chain played with true lengths, and within a factor of
  `1/0.7` of it;
- per honest phase the slot lottery gives the coalition at most the wins of the reading on slots,
  which is the continuous chain at `Δ + 1` and `λ`, and more than the continuous reading's;
- a deflated inference is the slot lottery at `f' = 1 − (1 − f)^(1/(1 − α))`, and lengthens the wait
  at 10 s;
- the bound on slots lies above the paper's attack against a wait on the slot lottery, with the
  spread of runs as its error.

Each fails under a registered mutation (`scripts/check_mutations.py`).

## K.8 — a capped correction

`src/finality_sim/cap.py` and `scripts/k8_cap.py`, with runs in `runs/k8/`.

**The rule.** The inference corrects each epoch's estimate in full from the occupied slots of the
observation period, the first `P = 6⌊k/f⌋` slots of the epoch before
(`cryptarchia-total-stake-inference.md`, `beta = 1`): `D' = D·N/(f·P)`. It counts occupied slots,
a slot holding a canonical block or an uncle the chain references, so it reads every win of the
stake that makes the chain: with one uncle a block it recovers the honest stake at 0.998–1.001
under Blend (`reports/tsi/README.md` §3.2a), and each correction here reads a chain's full
occupancy. A cap `c` bounds each correction: `D' ≥ (1 − c)·D`. The inference reads a side cut off
from the rest as stake that left, and stake that left as a side cut off: both are stake that is not
participating, which the TSI report reads as the inference measuring correctly (§6.4). A cap
therefore lengthens both alike: how long a side stays below the floor, and how long finality stalls
after the active stake falls. The TSI report finds the deployed learning rate `β = 1` best against
withholding, since a slower one deepens the standing deflation (§6.5); a cap slows only the falls.

**The reading.** The floor is K.3's, the worst case's at 10 s against a third. A side at its
fastest holds one block per slot it occupies. Corrections take effect at an epoch's start, `E`
slots apart. A split at a period's start is first corrected one epoch later, the earliest. A fall
just after a period ends is first corrected `2E − P` later, 1.4 epochs, the latest. The protection
is read at its earliest and the stall at its latest.

- **The density form.** A side can fix a fork once its stake over its estimate passes `σ*`, the
  largest share whose chain reaches the floor within `K` with chance at most `ε`, and a window after
  the correction that takes it there. A chain whose stake fell resumes once its stake over its
  estimate reaches `r*`, the least share whose chain reaches the floor within `K` with chance
  `1 − ε`, and a window after.
- **The depth form.** A side fixes a fork once it has made `φ + 1` blocks and its first is `K` slots
  old, at a rate that steps up with each correction.

| K | floor φ | σ*: the largest side it holds back | r*: the least stake that reaches it, random delay | r*, worst case at 10 s |
| --- | --- | --- | --- | --- |
| ⌊k/f⌋, 18 h | 1,019 | 0.385 | 0.665 | 0.666 |
| 3⌊k/f⌋, 54 h | 3,264 | 0.449 | 0.656 | 0.667 |

The days a side of share `σ` stays below the floor, at the earliest (`runs/k8/protection.csv`):

K = ⌊k/f⌋, days: density form / depth form

| σ | none | 20 % | 10 % | 5 % | 2 % |
| --- | --- | --- | --- | --- | --- |
| 0.10 | 8.25 / 3.49 | 53.25 / 3.49 | 98.25 / 3.49 | 203 / 3.49 | 503 / 3.49 |
| 0.20 | 8.25 / 1.75 | 23.25 / 1.75 | 53.25 / 1.75 | 98.25 / 1.75 | 248 / 1.75 |
| 0.25 | 8.25 / 1.40 | 15.75 / 1.40 | 38.25 / 1.40 | 68.25 / 1.40 | 166 / 1.40 |
| 0.30 | 8.25 / 1.17 | 15.75 / 1.17 | 23.25 / 1.17 | 38.25 / 1.17 | 98.25 / 1.17 |
| a third | 8.25 / 1.05 | 8.25 / 1.05 | 15.75 / 1.05 | 23.25 / 1.05 | 60.75 / 1.05 |
| 0.40 | 0.75 / 0.88 | 0.75 / 0.88 | 0.75 / 0.88 | 0.75 / 0.88 | 0.75 / 0.88 |
| 0.45 | 0.75 / 0.78 | 0.75 / 0.78 | 0.75 / 0.78 | 0.75 / 0.78 | 0.75 / 0.78 |

K = 3⌊k/f⌋, days: density form / depth form

| σ | none | 20 % | 10 % | 5 % | 2 % |
| --- | --- | --- | --- | --- | --- |
| 0.10 | 9.75 / 7.88 | 54.75 / 10.43 | 115 / 10.80 | 227 / 10.98 | 565 / 11.09 |
| 0.20 | 9.75 / 5.59 | 32.25 / 5.59 | 62.25 / 5.59 | 122 / 5.59 | 310 / 5.59 |
| 0.25 | 9.75 / 4.48 | 24.75 / 4.48 | 47.25 / 4.48 | 92.25 / 4.48 | 220 / 4.48 |
| 0.30 | 9.75 / 3.73 | 17.25 / 3.73 | 32.25 / 3.73 | 62.25 / 3.73 | 152 / 3.73 |
| a third | 9.75 / 3.36 | 17.25 / 3.36 | 24.75 / 3.36 | 47.25 / 3.36 | 115 / 3.36 |
| 0.40 | 9.75 / 2.81 | 9.75 / 2.81 | 17.25 / 2.81 | 24.75 / 2.81 | 47.25 / 2.81 |
| 0.45 | 2.25 / 2.50 | 2.25 / 2.50 | 2.25 / 2.50 | 2.25 / 2.50 | 2.25 / 2.50 |

- **Under the density form a cap holds a side back for months.** At `3⌊k/f⌋` a cap of 5 % keeps a
  side of 0.3 provisional for 62 days and one of 0.1 for 227, where without a cap every side below
  0.449 fixes its fork after 9.75 days. At `⌊k/f⌋` the same cap gives 38 and 203 days.
- **Under the depth form a cap buys almost nothing.** A side of 0.2 or more makes its `φ + 1` blocks
  before its first correction: 3.4 days at a third and 5.6 at 0.2 at `3⌊k/f⌋`, whatever the cap.
  Only a side of 0.1 gains, from 7.9 days to 11.
- **The protection holds per window.** A side has one chance at `ε` per window of `K` slots, most
  of them in the last epoch before it passes `σ*`.

What a fall of the active stake to `r` costs, with nobody withholding, at the latest
(`runs/k8/stall.csv`):

K = ⌊k/f⌋, days: the density form's stall, random delay / worst case at 10 s

| r | none | 20 % | 10 % | 5 % | 2 % |
| --- | --- | --- | --- | --- | --- |
| 80 % | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 70 % | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 60 % | 11.25 / 11.25 | 11.25 / 11.25 | 11.25 / 11.25 | 18.75 / 26.25 | 48.75 / 48.75 |
| 50 % | 11.25 / 11.25 | 18.75 / 18.75 | 26.25 / 26.25 | 48.75 / 48.75 | 116 / 116 |
| 40 % | 11.25 / 11.25 | 26.25 / 26.25 | 41.25 / 41.25 | 78.75 / 78.75 | 199 / 199 |

K = 3⌊k/f⌋, days: the density form's stall, random delay / worst case at 10 s

| r | none | 20 % | 10 % | 5 % | 2 % |
| --- | --- | --- | --- | --- | --- |
| 80 % | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 70 % | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 60 % | 12.75 / 12.75 | 12.75 / 12.75 | 12.75 / 12.75 | 20.25 / 27.75 | 42.75 / 50.25 |
| 50 % | 12.75 / 12.75 | 20.25 / 20.25 | 27.75 / 27.75 | 50.25 / 50.25 | 110 / 118 |
| 40 % | 12.75 / 12.75 | 27.75 / 27.75 | 42.75 / 42.75 | 80.25 / 80.25 | 193 / 200 |

K = 3⌊k/f⌋, random delay: under the depth form, the days until a block made at the fall is fixed; the days until the chain fills its slots within 5 % of f

| r | depth form | slow, none | slow, 20 % | slow, 10 % | slow, 5 % | slow, 2 % |
| --- | --- | --- | --- | --- | --- | --- |
| 80 % | 2.25 | 10.50 | 10.50 | 18.00 | 33.00 | 70.50 |
| 70 % | 2.25 | 10.50 | 18.00 | 25.50 | 48.00 | 123 |
| 60 % | 2.25 | 10.50 | 25.50 | 40.50 | 70.50 | 176 |
| 50 % | 2.66 | 10.50 | 25.50 | 55.50 | 100 | 243 |
| 40 % | 3.32 | 10.50 | 33.00 | 70.50 | 130 | 326 |

- **The density form stalls whenever the active stake falls below `r*`, with a cap or without.**
  Below about two thirds of the stake the chain no longer reaches the floor with chance `1 − ε`.
  Without a cap finality waits for the first correction: 12.75 days at the latest at `3⌊k/f⌋`. A
  cap of 5 % stretches a fall to half to 50 days, and a fall to 60 % to 20 days under random delay
  and 28 under the worst case.
- **The depth form never stalls.** A block made as the stake halves is fixed after 2.7 days instead
  of 2.25.
- **A capped chain stays slow.** After a fall to half the chain fills its slots within 5 % of `f`
  again after 10.5 days without a cap, 100 at 5 % and 243 at 2 %.

The protection against a side of 0.3 over the stall after a fall to half (`runs/k8/ratio.csv`):

| K | cap | protection, a side of 0.3 (days) | stall after a fall to 50 %, random / worst (days) | protection over stall, random / worst |
| --- | --- | --- | --- | --- |
| ⌊k/f⌋ | none | 8.25 | 11.25 / 11.25 | 0.73 / 0.73 |
| ⌊k/f⌋ | 20 % | 15.75 | 18.75 / 18.75 | 0.84 / 0.84 |
| ⌊k/f⌋ | 10 % | 23.25 | 26.25 / 26.25 | 0.89 / 0.89 |
| ⌊k/f⌋ | 5 % | 38.25 | 48.75 / 48.75 | 0.78 / 0.78 |
| ⌊k/f⌋ | 2 % | 98.25 | 116 / 116 | 0.85 / 0.85 |
| 3⌊k/f⌋ | none | 9.75 | 12.75 / 12.75 | 0.76 / 0.76 |
| 3⌊k/f⌋ | 20 % | 17.25 | 20.25 / 20.25 | 0.85 / 0.85 |
| 3⌊k/f⌋ | 10 % | 32.25 | 27.75 / 27.75 | 1.16 / 1.16 |
| 3⌊k/f⌋ | 5 % | 62.25 | 50.25 / 50.25 | 1.24 / 1.24 |
| 3⌊k/f⌋ | 2 % | 152 | 110 / 118 | 1.38 / 1.29 |

- **No cap separates a split from a fall.** The protection against a side of 0.3 lasts 0.73 to 1.38
  times the stall after a fall to half, at every cap and both `K`. Each needs the estimate to fall
  by a set ratio, and the cap sets only how many corrections that takes.

The periods of withholding a coalition needs to lower the inferred stake by its share, under each
cap (G7; `runs/k8/deflation.csv`):

| cap an epoch | α = 0.25 | α = 0.30 | α = a third |
| --- | --- | --- | --- |
| 20 % | 2 periods: 9.0 days withheld, 15.0 in all | 2 periods: 9.0 days withheld, 15.0 in all | 2 periods: 9.0 days withheld, 15.0 in all |
| 10 % | 3 periods: 13.5 days withheld, 22.5 in all | 4 periods: 18.0 days withheld, 30.0 in all | 4 periods: 18.0 days withheld, 30.0 in all |
| 5 % | 6 periods: 27.0 days withheld, 45.0 in all | 7 periods: 31.5 days withheld, 52.5 in all | 8 periods: 36.0 days withheld, 60.0 in all |
| 2 % | 15 periods: 67.5 days withheld, 112.5 in all | 18 periods: 81.0 days withheld, 135.0 in all | 21 periods: 94.5 days withheld, 157.5 in all |

- **The cap also prices G7's deflation.** At 5 % a coalition of a third withholds for 8 periods,
  36 days, over 60 days in all; at 2 % for 94.5 days over 157.5.

**The specification's target is rounded, as the TSI report records.** `total_stake_inference`
computes `f_p = truncate(f·PRECISION)` with `PRECISION = 1e3`, so for `f = 1/30` the inference holds
the occupied slots, canonical or referenced, at 0.033 a slot, 1 % below `f`. Played in its own
integer arithmetic with every unit of stake producing, it rests with the estimate 1 % above the
stake and an occupied slot every 30.3 slots; canonical blocks come at the chain's growth times that
(`runs/k8/spec.csv`):

| f | f_p | occupied slots a slot at rest | estimate over the stake | slots per occupied slot |
| --- | --- | --- | --- | --- |
| 1/30 | 33 | 0.0330 | 1.0103 | 30.30 |
| 1/20 | 50 | 0.0500 | 1.0000 | 20.00 |

At `f = 1/20` the product is whole and the target is `f`. The TSI report derives the same residual,
`f/f_p ≈ 1.010`, and sizes the one-constant change that removes it (`reports/tsi/README.md` §2.2,
Appendix A, §8).

**Verdict.** H23 holds under random delay, and under the worst case at 10 s fails in its second
part. A cap of 5 % keeps a side of 0.3 below the density floor for 62 days at `3⌊k/f⌋`. A fall to
60 % then stalls finality for 20.25 days under random delay, within three epochs, and for 27.75
under the worst case, past them. The protection against a side of 0.3 lasts at most 1.38 times the
stall after a fall to half.

Gates (`tests/test_cap.py`):

- the estimate follows the specification's correction, played period by period with binomial counts
  of occupied slots and the cap, within 1 %;
- the specification's integer inference rests at 0.033 for `f = 1/30` and at `f` for `1/20`;
- under the worst case the least share that reaches the floor at `1 − ε` is the honest share the
  floor was sized for;
- the protection counts corrections from the split, one an epoch, and a window after;
- the stall and the slow chain read the first correction `2E − P` after a fall;
- without a cap the blocks come as K.3's `after_correction` reads them, within 0.5 %;
- with a cap of zero the earliest slot by which a side holds `n` blocks with chance `ε` lies at or
  before the binomial's, within 0.5 %.

Each fails under a registered mutation (`scripts/check_mutations.py`).

## K.9 — the floor counted as the stake inference counts

`scripts/k9_occupancy.py`, with runs in `runs/k9/`, on K.3's and K.8's functions.

**The count.** The stake inference counts occupied slots: a slot holding a canonical block or an
uncle the chain references, each slot once. With one uncle a block it recovers the honest stake at
0.998–1.001 under Blend, the first-fork rule costing nothing measurable up to three rounds a hop
(`reports/tsi/README.md` §3.2a). K.3's floor counts canonical blocks, which lose the orphans: on the
specification's Blend the honest chain keeps 0.845 of its wins. A floor on occupied slots reads the
honest chain at its stake's occupancy, here at 0.998 of it, the least completeness the TSI report
measured in its design band. A side at its fastest holds one block per slot it occupies, so it
counts the same on either.

**The worst case.** Every canonical block occupies its own slot, so on every path the count of
occupied slots is at least the count of canonical blocks, and a floor sized on blocks keeps its
liveness on occupied slots. No larger worst-case floor is read. An adversary that orphans a run of
honest blocks at once leaves one countable uncle, the run's first block (TSI report §6.6), and the
worst-case count of occupied slots is not bounded here.

The floor on each count against 25 %, 30 % and a third (`runs/k9/floor.csv`):

| K | α_max | count | floor φ | withheld-from chain, mean | nobody withholds: waits | withheld from: waits | largest side held at K |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ⌊k/f⌋ | 0.25 | blocks, random delay | 1,161 | 1,375 | 2e-64 | 9e-10 | 0.445 |
| ⌊k/f⌋ | 0.25 | blocks, worst 10 s | 1,131 | 1,300 | 9e-64 | 8e-10 | 0.432 |
| ⌊k/f⌋ | 0.25 | occupied slots, random delay | 1,391 | 1,624 | 6e-72 | 1e-9 | 0.542 |
| ⌊k/f⌋ | 0.3 | blocks, random delay | 1,078 | 1,285 | 2e-82 | 1e-9 | 0.410 |
| ⌊k/f⌋ | 0.3 | blocks, worst 10 s | 1,064 | 1,231 | 2e-82 | 8e-10 | 0.404 |
| ⌊k/f⌋ | 0.3 | occupied slots, random delay | 1,291 | 1,517 | 4e-93 | 9e-10 | 0.500 |
| ⌊k/f⌋ | a third | blocks, random delay | 1,022 | 1,224 | 2e-96 | 9e-10 | 0.386 |
| ⌊k/f⌋ | a third | blocks, worst 10 s | 1,019 | 1,184 | 2e-96 | 9e-10 | 0.385 |
| ⌊k/f⌋ | a third | occupied slots, random delay | 1,225 | 1,445 | < 1e-99 | 9e-10 | 0.472 |
| 3⌊k/f⌋ | 0.25 | blocks, random delay | 3,750 | 4,126 | < 1e-99 | 9e-10 | 0.520 |
| 3⌊k/f⌋ | 0.25 | blocks, worst 10 s | 3,607 | 3,901 | < 1e-99 | 9e-10 | 0.499 |
| 3⌊k/f⌋ | 0.25 | occupied slots, random delay | 4,463 | 4,871 | < 1e-99 | 1e-9 | 0.625 |
| 3⌊k/f⌋ | 0.3 | blocks, random delay | 3,491 | 3,854 | < 1e-99 | 9e-10 | 0.482 |
| 3⌊k/f⌋ | 0.3 | blocks, worst 10 s | 3,403 | 3,693 | < 1e-99 | 9e-10 | 0.469 |
| 3⌊k/f⌋ | 0.3 | occupied slots, random delay | 4,156 | 4,550 | < 1e-99 | 1e-9 | 0.580 |
| 3⌊k/f⌋ | a third | blocks, random delay | 3,318 | 3,673 | < 1e-99 | 9e-10 | 0.457 |
| 3⌊k/f⌋ | a third | blocks, worst 10 s | 3,264 | 3,551 | < 1e-99 | 9e-10 | 0.449 |
| 3⌊k/f⌋ | a third | occupied slots, random delay | 3,951 | 4,336 | < 1e-99 | 1e-9 | 0.550 |

- **On occupied slots the floor under random delay rises by a fifth.** Against a third it is 1,225
  at 18 hours where blocks give 1,022, and 3,951 at 54 hours where blocks give 3,318. The largest
  side it holds back rises from 0.386 to 0.472 at 18 hours, and from 0.457 to 0.550 at 54.

The days a side at its fastest takes to fix a fork under the depth form, on average / at the
earliest with chance `ε`, at the worst case's floor on blocks and at the floor on occupied slots
sized under random delay (`runs/k9/protection.csv`):

| K | floor | σ = 0.1 | σ = 0.2 | σ = 0.25 | σ = 0.3 | σ = a third |
| --- | --- | --- | --- | --- | --- | --- |
| ⌊k/f⌋ | 1,019, blocks, worst 10 s | 3.49 / 2.87 | 1.75 / 1.44 | 1.40 / 1.15 | 1.17 / 0.96 | 1.05 / 0.87 |
| ⌊k/f⌋ | 1,225, occupied slots, random delay | 4.19 / 3.52 | 2.10 / 1.76 | 1.68 / 1.41 | 1.40 / 1.18 | 1.26 / 1.06 |
| 3⌊k/f⌋ | 3,264, blocks, worst 10 s | 11.17 / 10.04 | 5.59 / 5.03 | 4.48 / 4.03 | 3.73 / 3.36 | 3.36 / 3.02 |
| 3⌊k/f⌋ | 3,951, occupied slots, random delay | 13.52 / 12.27 | 6.77 / 6.15 | 5.42 / 4.92 | 4.52 / 4.10 | 4.07 / 3.70 |

- **At the protocol's floor the protection does not move.** A side counts the same on either, so at
  1,019 a third still fixes after 1.05 days. A floor sized on occupied slots under random delay,
  1,225, would hold it 1.26 days, and the worst case gives no such floor.

The least share whose chain reaches the protocol's floor within `K` with chance `1 − ε`, `r*`, under
random delay; and the days until a block made as the active stake falls to `r` is fixed under the
depth form with no cap, on blocks / on occupied slots (`runs/k9/stall.csv`):

| K | floor | r*: blocks / occupied slots | depth form, fall to 70 % | depth form, fall to 60 % | depth form, fall to 50 % | depth form, fall to 40 % |
| --- | --- | --- | --- | --- | --- | --- |
| ⌊k/f⌋ | 1,019 | 0.665 / 0.562 | 0.75 / 0.75 | 0.75 / 0.75 | 0.83 / 0.75 | 1.04 / 0.88 |
| 3⌊k/f⌋ | 3,264 | 0.656 / 0.555 | 2.25 / 2.25 | 2.25 / 2.25 | 2.66 / 2.25 | 3.32 / 2.81 |

- **On occupied slots finality is more robust to stake that leaves.** The density form stalls only
  below 0.562 of the stake at 18 hours, where on blocks it stalls below 0.665. Under the depth form
  a block made as the stake halves is fixed at 18 hours, where on blocks it waits 0.83 days.

The floor as a quorum under random delay, beside K.3's on blocks with the side at its fastest
(`runs/k9/quorum.csv`):

| α | count | honest chain withheld from, per 1,000 slots | side of (1 + α)/2, per 1,000 slots | least K (days) | floor at it |
| --- | --- | --- | --- | --- | --- |
| 0.2 | blocks, the side at one block per occupied slot | 22.62 | 20.14 | 5.65 | 10,417 |
| 0.2 | occupied slots, both | 26.70 | 20.14 | 0.88 | 1,773 |
| 0.25 | blocks, the side at one block per occupied slot | 21.22 | 20.97 | 516 | 940,407 |
| 0.25 | occupied slots, both | 25.06 | 20.97 | 2.24 | 4,437 |
| 0.3 | blocks, the side at one block per occupied slot | 19.83 | 21.79 | none | – |
| 0.3 | occupied slots, both | 23.40 | 21.79 | 14.20 | 27,714 |
| a third | blocks, the side at one block per occupied slot | 18.89 | 22.35 | none | – |
| a third | occupied slots, both | 22.30 | 22.35 | none | – |

- **Counted alike, the two sides separate below a third.** Under random delay a floor on occupied
  slots separates the sides of every partition against a quarter from 2.24 days, where on blocks it
  takes 516, and against 30 % from 14.2 days, where on blocks none does. At a third none exists, as
  K.3 found: the honest chain the coalition withholds from and a side of `(1 + α)/2` occupy slots at
  the same rate.
- **Under the worst case nothing moves.** The honest chain's count of occupied slots there is at
  least its canonical blocks, which K.3 reads, and no larger lower bound is derived.

**Verdict.** H24 holds. Under random delay the floor on occupied slots lies a fifth above the floor
on blocks at 18 hours against a third, 1,225 against 1,022, and separates partitions against a
quarter from 2.24 days. Under the worst case the count of occupied slots is at least the count of
blocks on every path, so the floor of 1,019 keeps its liveness. H21's first part, which failed with
both sides read on blocks, holds under random delay on occupied slots: a floor separates a quarter
from 2.24 days, within 54 hours. Under the worst case it still fails.

The figures come from K.3's and K.8's gated functions at the honest chain's occupancy; no new
function enters.
