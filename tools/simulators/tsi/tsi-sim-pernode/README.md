# tsi-sim-pernode — Cryptarchia TSI **per-node** network simulator (Phase 2)

> The reduced-model simulators (`../tsi-sim/`, `../tsi-sim-mc/`) collapse the network to one
> global canonical chain and one scalar `D_est` per epoch. **This package removes that
> collapse:** every one of the `N` nodes runs TSI individually with its **own** `D_est`, from
> its **own** partial view of the block tree under explicit message propagation over a peering
> graph. Its job is to *test* the reduced model's assumption that all honest nodes agree.

## What it models

- **Per-node lottery:** node `i` wins a slot with `φ_f(w_i / D_est_i)` — `D_est` is a length-`N`
  **vector**, each node self-updating from its own view (the reduced model's key reuse: the
  sparse sampler already takes a per-node probability vector).
- **Topology** (`topology`): three propagation models over the network.
  - `full_mesh`: every node one hop away with uniform latency `L` — reproduces the reduced
    model exactly (validation baseline).
  - `regular`: a random **d-regular** peering graph (configurable `degree`) with per-link
    latency (`link_latency_dist ∈ {fixed, uniform, exp, geo}`, all with mean
    `link_latency_mean`). A block reaches a node after the shortest **weighted** path from its
    producer (gossip flooding). Models **direct block gossip**.
  - `blend`: the **same** d-regular graph, but a block is first routed through the **Blend
    mixnet** before it is public — the producer picks `blend_hops` distinct relay nodes
    uniformly at random, the block hops `producer → r₁ → … → r_hops` over the graph, each relay
    waiting a `Uniform(0, blend_delay_max)` **mixing delay** before forwarding, and the last
    relay's forward is the final network-wide gossip that makes the block visible. Relays are
    blind forwarders (they learn the block only from that final gossip). The dominant latency is
    the per-hop mixing, not the graph transport — this is the multi-slot regime where forks and
    the stake underestimate appear and uncle references matter. Because the mixing delays are
    `Uniform`-bounded, the windowed fork choice stays **exact** (horizon
    `(blend_hops+1)·max_path_latency + blend_hops·blend_delay_max`).
- **Real-world latency (units).** Latency is in **slots** and a slot is **1 s**, so measured
  internet latencies (tens–hundreds of ms) are *fractions* of a slot; arrivals are therefore
  kept **sub-slot (float)**, not rounded to whole slots. `link_latency_dist=geo` draws each
  link from a geographic band mixture (`~15 ms` metro → `~200 ms` antipodal, EU↔EU ≪ EU↔AU),
  rescaled so `link_latency_mean` stays the mean-latency knob. So `regular` runs the realistic
  sub-slot direct-gossip regime (`~0.05–0.2` slot), where forks are rare, and `blend` runs the
  multi-slot Blend-mixnet regime, where per-hop mixing delays dominate.
- **Per-node views:** one global block tree plus an `(N × n_blocks)` **arrival matrix** `A`;
  each node builds on / measures density over the blocks that have arrived at it. Uncle refs
  are **baked at production** from the producer's view (faithful — immutable once adopted).
- **Uncle model (`uncle_model`, CLI `--old`):** the default **countable** model implements the
  spec's counting-only rules (cryptarchia-v1-protocol.md): only the **first block of a fork**
  (parent on the producer's chain) is referenceable/countable, the window is **derived** as
  `w_u = window_absorption / f` slots (`W` expected block-intervals, default `W = 10` → 300
  slots, bounded `W ≤ 0.6·k`), selection skips slots already occupied on the producer's chain
  and picks one uncle per slot, and the measurement pass re-checks every rule per reference
  (rejections tallied as `deep_ref_share`). Passing `--old` to `tsi-sweep`/`tsi-verify` runs
  the pre-redesign model unchanged — window = `uncle_window` slots, any-depth orphans
  referenceable, every baked reference counted — and **bit-reproduces historical runs** (the
  old model's RNG key is byte-identical to the pre-`uncle_model` key).
- **Metrics:** per-node `D_est` spread (`range`, `IQR`), canonical-chain **agreement**
  (window prefix vs current tip), mean accuracy, and — with `init_dest=heterogeneous` —
  transient re-convergence.

## Headline result

**Per-node `D_est` disagreement collapses to zero.** Because TSI reads density from a window
buried far past `k`-finality, and all nodes seed the recursion from a common hardcoded
genesis `D`, every node computes the **same** measured density `m` → **identical** `D_est`
(`range ≈ 0`, `agreement_window = 1`) — *even under a sparse graph with high latency and heavy
tip-level forking* (`agreement_tip` can drop well below 1). This **validates the reduced
model**. Topology/latency instead shift the shared *mean* accuracy (via fork rate → `q`),
which uncle references recover just as in the reduced model. (Injected heterogeneous
disagreement, which the real protocol never creates, is *preserved* by the common
multiplicative update — a cautionary note, not protocol behaviour.)

## Quick start

```bash
make install         # venv + editable install
make test            # unit + fast per-node checks
make verify          # per-node validation (parity, spread→0, agreement, topology effect)
# Run any configs/<name>.yaml by its stem (auto-discovered); each writes a dated runs/ folder:
make smoke           # tiny end-to-end grid + figures  (configs/smoke.yaml)
make default         # scaled-k divergence/topology sweep + figures  (configs/default.yaml)
make fullscale       # full-scale (true k) confirmation  (configs/fullscale.yaml)
make figures RESULTS=runs/<dir>/results.parquet          # re-render figures from a run
# Extra sweep flags: make fullscale SWEEP_ARGS="--batch-size 1 --mem-frac 0.6"
```

## Scale & performance

- **Representation:** one global block tree + `(N × n_blocks)` `float64` arrival matrix `A`
  (sub-slot arrivals); topology `path_latency[N,N]` (per-node Dijkstra, once per trajectory).
- **`n_blocks` is NOT `~10·k` in general — it tracks block production.** `n_blocks` is the number
  of lottery wins in an epoch, `≈ E·Σᵢφ(wᵢ/D_est)`. At equilibrium that is `~10·k` (≈ 22k at
  k=2160), but when `D_est` is far below the true stake — the **collapsed-estimate regime**, e.g. a
  small `genesis_d_factor` — `Σ(stake)/D_est = 1/genesis_d_factor` is large and block production
  explodes proportionally. At `genesis_d_factor=0.01`, genesis epoch-0 produces **~2.0M blocks**
  (100× equilibrium) → `A ≈ 15 GB` for a *single* worker; `D_est` self-corrects to equilibrium
  within ~2 epochs, so only the earliest epoch(s) are heavy. **Raising `genesis_d_factor` toward
  0.1–0.5 collapses this cost** (0.1 → ~0.22M blocks → ~1.6 GB; 0.5 → ~44k → ~0.4 GB) and does not
  change the equilibrium result, which is measured after burn-in.
- **Sliding-window prune (`prune_arrival`, default on):** the arrival matrix never needs per-node
  columns for blocks past the horizon — under deterministic latency a block with `slot ≤ t − H` has
  reached *every* node, so its column is finalized and dropped. We keep columns only for blocks
  inside `max(horizon, uncle_window)` slots in a base-offset buffer, turning the `O(N·n_blocks)`
  matrix into `O(N · keep-span-blocks)`. This is what makes the collapsed regime affordable: at
  N=1000/k=2160/`gdf=0.01` the buffer is ~tens of MB instead of the ~15 GB full matrix (fork choice,
  the parent clamp, uncle selection, and per-node tips all reconstruct exactly from it). It is
  **bit-identical** to the full matrix at `jitter_mean == 0` (proven by `test_prune_matches_full_matrix`
  across topologies/uncles/`gdf`); with jitter it falls back to the full matrix (whose safety clamp
  keeps the tree valid). Set `prune_arrival: false` to force the full matrix (the parity oracle).
  The measurement pass also argmaxes in node-row bands so it adds only a small temporary. Divergence
  sweeps run at scaled **k=256** (`configs/default.yaml`); full-scale k=2160 is validated to **N ≤ 2000**.
- **Worker sizing (auto, RAM-safe):** both `A` (`~N·n_blocks`, incl. the block explosion above)
  and `path_latency` (`~N²`) grow, so the sweep runner sizes the loky pool to fit a RAM budget
  (`--mem-frac`, default 0.7 of physical RAM) instead of blindly using every core. The per-worker
  estimate realises the seeded stake to compute the **genesis-epoch** block count
  (`expected_peak_blocks`), so it reflects a low-`genesis_d_factor` explosion rather than assuming
  `~10·k`. A **calibration probe** measures a real worker's peak RSS (one genesis epoch of the
  heaviest config in a spawned process) whenever the estimate is heavy or `N > 2000`
  (`--calibrate {auto,always,never}`, default `auto`; the probe bounds itself to physical RAM so it
  fails loud rather than freezing).
- **Fail-loud memory guard (`memguard.py`):** every worker checks size *before* allocating both
  big arrays — the `(N × n_blocks)` `A` (in `build_tree_pernode`) and the `(N × N)` `path_latency`
  (in `build_path_latency`, built first) — and raises `ArrivalMatrixTooLarge` if it would exceed
  the budget `TSI_ARRIVAL_BYTES_BUDGET`. The sweep sets that to each worker's RAM share; **unset or
  `0` is not "unlimited"** — it resolves to `DEFAULT_BUDGET_FRAC` (0.9) of physical RAM, so a bare
  `run_trajectory`, `tsi-verify`, the probe, or a `--mem-frac 0` run all keep an absolute
  per-process ceiling. So a mis-estimated block explosion (or a huge `N`) fails with a clear
  message instead of freezing the machine.
- **Cost:** dominated by the per-node fork choice (batched per slot) and the arrival-matrix
  fill; the sparse lottery is negligible. Across-config joblib **loky** parallelism reused.
- **Measurement optimisation (`measure.py`):** the per-node canonical/density/agreement pass
  was ~95% of an epoch. It is now **deduped by tip** (nodes sharing a tip share every derived
  quantity — high agreement collapses `N` to a handful of computations) and the per-tip chain
  walk runs as a cached **numba** kernel (pure-Python fallback if numba is absent). Exact —
  bit-identical to the naive loop (`test_measure`). Measured **~9× end-to-end** (heavy config
  11.3 s → 1.2 s) and ~14× on measurement-bound configs. numba comes via the `accel` extra
  (`pip install -e ".[dev,accel]"`, done by `make install`).
- **Windowed fork choice (`windowed_fork_choice`, default on):** bounds the block-tree build's
  per-slot candidate scan to a horizon of the max path latency plus the fully-propagated best
  tip, turning `O(n_blocks^2)` fork choice into `O(n_blocks*H)`. **Exact** when link latency is
  deterministic (`jitter_mean == 0`) — bit-identical to a full scan (parity test). With
  `jitter_mean > 0` it becomes a tiny approximation and **warns**; a safety clamp still keeps
  the tree valid, and `windowed_fork_choice=False` forces a guaranteed-exact full scan.
- **Reproducibility:** every draw spawns off `SeedSequence(hash(config))` — child 0 stake,
  1 graph, 2 init, 3+e epoch `e`. `graph_seed`/`degree`/`link_latency_*` are part of the
  config identity.
  - **numpy-version caveat:** the `accel` extra (numba) requires `numpy<2.5`, so installing it
    pins numpy to 2.4.x. numpy's `Generator.choice(replace=False)` is **not** stream-stable
    across the 2.4↔2.5 boundary, and the sparse lottery uses it heavily only in the degenerate
    *collapsed-estimate* regime (`D_est → 0` ⇒ win-prob → 1 ⇒ `count ≈ n_slots`). So a run on
    numpy 2.5 and a run on numpy 2.4 give **identical results for all normal configs** but can
    diverge chaotically in that one extreme regime (e.g. `degree=4, link_latency=8`, where the
    estimate has already collapsed to ~0.13 — off the safe chart). The differences are tiny
    (max |Δ mean_ratio| ≈ 3e-3) and change no conclusion; pin numpy if bit-reproducibility
    across environments is required.

## Layout

```
src/tsi_sim/   constants config rng stake lottery topology blocktree(+build_tree_pernode)
               uncles(+select_uncles_at_production) tsi(+update_D_vec) epoch engine metrics
               theory verify  plotting/{style, figures_pernode, make_figures}
configs/       smoke.yaml  default.yaml  fullscale.yaml
               countable-vs-old.yaml  absorption-window.yaml   (countable-model studies)
               fine-delay.yaml   (delay 1-5 at 40 replicates: the design band, high precision)
tests/         test_{pernode,config,rng,lottery,blocktree,uncles,tsi_counting,stake,
                     theory,latency,theory_convergence,countable_counting,...}.py
scripts/       plot_countable_vs_old.py  (countable-vs-unrestricted comparison figures)
               plot_fine_delay.py        (design-band accuracy + model gap with 95% CIs)
```
