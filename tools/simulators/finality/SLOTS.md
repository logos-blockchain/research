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
- A variant adds a density floor `φ`: `B_imm` moves to a block only once `φ` blocks of the chain
  follow it.

**The candidates.** `K = ⌊k/f⌋` = 64,800 slots, 18 hours, the time 2,160 blocks take at the full
rate with no forks. `K = s = 3⌊k/f⌋` = 194,400 slots, 54 hours, the specification's own slot
parameter. And the least `K` that holds each `(α, ε, Δ)`.

**Taken without the owner's answer.** These rules; the floor measured as a variant beside them;
the epoch at today's length, `10⌊k/f⌋` slots at `k = 2160` (G2).

## K.1 — settlement after a wait of `T` slots

## K.2 — what a `K` holds

## K.3 — splits and eclipses

## K.4 — the nonce and the epoch

## K.5 — every other result, read again
