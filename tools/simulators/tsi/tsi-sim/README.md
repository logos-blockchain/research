# tsi-sim — Cryptarchia Total Stake Inference simulator (uncle references)

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

True constants (`k=2160`, `f=1/30`) give 648,000-slot epochs — too large to sweep.
Mean accuracy is provably `k`-invariant (only variance scales `~1/T`), so sweeps use a
**scaled `k`** (`configs/default.yaml`); the final accuracy/variance figures re-run at
true `k` (`configs/fullscale.yaml`). `configs/smoke.yaml` is a tiny dev grid.

## Layout

```
src/tsi_sim/   constants config rng stake lottery latency blocktree uncles
               tsi epoch engine metrics theory sweep  plotting/{style,figures}
scripts/       run_sweep.py  make_figures.py  verify.py
configs/       smoke.yaml  default.yaml  fullscale.yaml
tests/         test_{lottery,uncles,tsi_counting,blocktree,theory_convergence}.py
```
