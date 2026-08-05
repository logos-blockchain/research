# Total-Stake-Inference parameter selection

*Per-node network simulation of Cryptarchia Total Stake Inference (TSI). Simulator: [`tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode). All runs at the true security parameter **k = 2160** unless noted; latency is in slots and **1 slot = 1 s**.*

This report selects and justifies the TSI parameters for Cryptarchia from a per-node network simulation. The whole report is one document — **[tsi-report.md](tsi-report.md)** — and section numbers (§1–§9, Appendices A–C) are stable identifiers referenced from the simulator and from spec discussion.

> **Uncle references.** The model analysed throughout is the **countable** one: counting-only references, deduplicated by slot, drawn from first-fork blocks only, within a window derived as `w_u = W_abs/f`. An **unrestricted** baseline — any orphan in the window at any fork depth — is measured alongside it for comparison. The two are indistinguishable in the design regime `ρ < 1` and diverge only under overload. See the model note at the top of the [report](tsi-report.md), the mechanism in [§2.1](tsi-report.md#s2-1), the comparison in [§3.2](tsi-report.md#s3-2)–[§3.2a](tsi-report.md#s3-2a), and the reproduction notes in [§9](tsi-report.md#s9).

## Contents

**[Read the report →](tsi-report.md)**

| § | what it covers |
|---|---|
| [§1](tsi-report.md#s1) | executive summary — the problem, the findings, the recommendation |
| [§2](tsi-report.md#s2) | the model, the measurement convention, and the counting rule |
| [§3](tsi-report.md#s3) | the findings and their evidence, including the high-precision design band ([§3.2a](tsi-report.md#s3-2a)) |
| [§4](tsi-report.md#s4) | design equations and the parameter-selection algorithm |
| [§5](tsi-report.md#s5) | caveats and regime of validity |
| [§6](tsi-report.md#s6) | robustness — jitter, grinding, withholding, selfish mining, rewards, reorg depth, churn |
| [§7](tsi-report.md#s7) | parameter reference — what each knob does |
| [§8](tsi-report.md#s8) | the safest selection, residual risks, and the recommendation-vs-spec deltas |
| [§9](tsi-report.md#s9) | reproducibility — how to re-run every study |
| [A](tsi-report.md#sA) · [B](tsi-report.md#sB) · [C](tsi-report.md#sC) | the residual `f`-rounding offset · the per-epoch noise floor · consensus detail |

## Headline recommendation

Cryptarchia baseline f = 1/30. Two design choices are foundational: count uncles **per occupied slot**, not per block — the density-bug fix that lands the estimate at exactly `D` ([§2.1](tsi-report.md#s2-1), [§8.5](tsi-report.md#s8-5)) — and make genesis `D̂` **a single protocol constant, identical at every node**, never client-configurable, since a per-node divergence is never self-corrected ([§8.1](tsi-report.md#s8-1) row 7). The settings: security `k = 2160`, uncle window `W = 300` slots, uncle cap `U ≥ ⌈ρ⌉ + 1` (2 at the Blend target; the protocol's `MAX_UNCLES = 4` sits safely above it), learning rate `β = 1`, on-chain `f` at 10⁻⁶ precision, peering degree ≥ 6 at scale, soft uncle rewards with `w_u + w_n < 1`, and operate at load `ρ = f·D_vis < 1`. The full recommended-configuration table and rationale are in **[§8 →](tsi-report.md#s8)**.

## Figures

Figures are embedded from [`report-figures/`](report-figures) via relative links and are versioned here alongside the report. They are produced by the simulator's plotting scripts (`scripts/*.py` and `tsi_sim.plotting`) in [`tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode); that simulation folder does **not** commit its own generated figures — the copies checked in here are the report's figures of record.

## Reproducing the results

The simulation code, configs, and run data live in [`tools/simulators/tsi/tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode). Every study's exact command is listed in [§9 — Reproducibility](tsi-report.md#s9). In short, from the simulator directory: `make install`, then `make <config>` to run a sweep (results land under `runs/<timestamp>_<label>/`), and the per-figure generators under `scripts/` render the figures. Regenerated figures must be copied into [`report-figures/`](report-figures) to update this report.
