# tsi-sim-mc — Cryptarchia TSI simulator (multicore build)

> **This is the multicore-optimised, reviewed copy of `../tsi-sim/`.** The original is left
> untouched. Versus the original it adds: a **sparse lottery sampler** (~30–100× faster per
> epoch), a **hardened multicore sweep** (loky + single-thread BLAS), an **opt-in parallel
> chunked lottery**, an optional **spec fixed-point mode**, corrected figures, config
> validation, and a larger test suite. See "Performance & reproducibility" below.

Monte-Carlo simulation framework used to choose safe values for the **uncle-reference**
parameters of Cryptarchia's Total Stake Inference (TSI):

- `U` — max uncles referenced per block (`MAX_UNCLES`); `U=0` is the no-uncle baseline.
- `W` — uncle reference window in slots (spec default 300).
- swept against network size `N`, stake distribution `S` (uniform / Pareto), and
  network **latency** `L` (in slots — deliberately *not* `D`, which denotes the stake estimate).

It measures how well the inferred total active stake `D` tracks the true total stake, and
whether uncle references recover the active slots that network latency loses to forks.

> This lives under a `raw/` docs path, so it is invisible to the repository's
> markdown-lint CI. It is a standalone Python package with its own tooling.

## Model

Reduced **canonical-chain-with-orphans** model: we simulate the global winning-slot
sequence (stake-weighted φ lottery), build a real block tree with latency- and
multi-winner-induced forks, resolve the canonical chain (honest longest-chain), let
canonical blocks reference uncles per the spec's selection rules, and count TSI density
`m = honest-chain blocks + deduplicated referenced uncles` in the measurement window.
All honest nodes converge to the same deep chain (k-finality), so a single per-epoch
`D` is faithful. A full per-node model is the planned next phase (`per_node_dest` flag
scaffolds it).

See the sibling spec `../` and `../../cryptarchia-total-stake-inference.md` for the math.

## Quick start

```bash
make install         # create .venv and install (editable) with dev deps
make test            # unit tests + fast theory checks
make verify          # simulator vs closed-form analytic checks
make smoke           # tiny scaled-k sweep + figures (end-to-end smoke test)
make sweep figures   # full scaled-k parameter sweep + academic figures
```

Outputs: `results/*.parquet` (one row per config×epoch) and `figures/*.{pdf,png}`
(both git-ignored).

## Scale

True constants (`k=2160`, `f=1/30`) give 648,000-slot epochs. Mean accuracy is provably
`k`-invariant (only variance scales `~1/T`), so sweeps use a **scaled `k`**
(`configs/default.yaml`); the final accuracy/variance figures re-run at true `k`
(`configs/fullscale.yaml`, `make sweep-fullscale`). `configs/smoke.yaml` is a tiny dev grid.

## Performance & reproducibility

- **Sparse lottery (the main win).** The number of slots a node wins is `Binomial(n_slots,
  p_i)` and the won slots are a uniform distinct subset — distributionally identical to an
  independent Bernoulli per slot, but without the dense `(n_nodes, n_slots)` array that was
  ~95% of runtime. Full-scale (`k=2160`) epoch: **~3.3 s → ~0.1 s (~30×)**; at `k=256`,
  **~0.39 s → ~0.009 s (~40×)**.
- **Multicore across configs (the main lever).** `run_trajectory` is a pure function of a
  hash-seeded, immutable `SimConfig`, so the sweep is order-independent and embarrassingly
  parallel. `run_sweep` uses joblib's process-based **loky** backend with
  `inner_max_num_threads=1` (and the Makefile pins `*_NUM_THREADS=1`) to use all cores
  without BLAS oversubscription. `--n-jobs -1` (default) uses every core; `--batch-size 1`
  suits the small heavy full-scale grid. Measured on a 14-core box, the full scaled-`k`
  sweep (`configs/default.yaml`, 3888 configs) runs in **~58 s parallel vs ~561 s serial
  (9.7×)**.
- **Opt-in within-config parallelism.** `lottery_chunks > 1` splits the per-slot lottery
  across slot-chunks with independent `SeedSequence.spawn` children. After the sparse fix the
  lottery is a small fraction of an epoch, so this rarely helps — it exists for a single
  isolated config with an enormous `n_slots`. **Reproducibility caveat:** the chunked stream
  differs from the serial stream and *changes with `n_chunks`*, so `lottery_chunks` must be a
  pinned, recorded parameter, never derived from the core count.
- **RNG reproducibility.** Every draw is a deterministic spawn off `SeedSequence(hash(config))`
  — child 0 draws stake, child `e+1` drives epoch `e`, which spawns lottery/aux sub-streams.
  Results are identical regardless of parallel scheduling order. The sparse sampler consumes
  the RNG differently from the original dense one, so committed baselines here were
  regenerated against the sparse sampler.

## Faithfulness notes (from review)

- `update_D(..., fixed_point=True)` mirrors the spec's integer `f`-truncation
  (`int(f·1000)/1000 = 0.033`), reproducing the on-chain estimator's ~1% systematic
  overestimate. Default `False` keeps the exact-`f`, analysis-faithful behaviour.
- TSI counts *blocks* (wins), so at full uncle recovery the estimate equilibrates at the
  **block-count ceiling** `-ln(1-f)/f ≈ 1.017`, not 1.0 — a deterministic overshoot, not
  noise. Figures overlay this ceiling; `theory.block_count_ceiling` computes it.

## Layout

```
src/tsi_sim/   constants config rng stake lottery latency blocktree uncles tsi epoch
               engine metrics theory sweep verify  plotting/{style,figures,make_figures}
scripts/       run_sweep.py  make_figures.py  verify.py   (thin shims; installed as
                                                            tsi-sweep / tsi-figures / tsi-verify)
configs/       smoke.yaml  default.yaml  fullscale.yaml
tests/         test_{lottery,uncles,tsi_counting,blocktree,config,rng,stake,theory,
                     latency,theory_convergence}.py
```
