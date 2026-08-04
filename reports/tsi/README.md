# Total-Stake-Inference parameter selection

*Per-node network simulation of Cryptarchia Total Stake Inference (TSI). Simulator: [`tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode). All runs at the true security parameter **k = 2160** unless noted; latency is in slots and **1 slot = 1 s**.*

This report selects and justifies the TSI parameters for Cryptarchia from a per-node network simulation. It is split into four cohesive parts; section numbers (§1–§9, A–C) are stable identifiers preserved across the set.

> **Uncle references.** The model analysed throughout is the **countable** one: counting-only references, deduplicated by slot, drawn from first-fork blocks only, within a window derived as `w_u = W_abs/f`. An **unrestricted** baseline — any orphan in the window at any fork depth — is measured alongside it for comparison. The two are indistinguishable in the design regime `ρ < 1` and diverge only under overload. See the model note at the top of [Part 1](tsi-report-1-overview-and-recommendations.md), the mechanism in [§2.1](tsi-report-2-accuracy-and-design.md#s2-1), the comparison in [§3.2](tsi-report-2-accuracy-and-design.md#s3-2)–[§3.2a](tsi-report-2-accuracy-and-design.md#s3-2a), and the reproduction notes in [§9](tsi-report-4-reproducibility-and-appendices.md#s9).

## Parts

1. **[Overview and recommendations](tsi-report-1-overview-and-recommendations.md)** — the executive summary, the per-knob parameter reference (§7), and the safest selection with residual risks and the recommendation-vs-spec deltas (§8).
2. **[Accuracy and design](tsi-report-2-accuracy-and-design.md)** — the model and counting rule (§2), the seven findings and their evidence (§3), the design equations and selection algorithm (§4), and the caveats and regime of validity (§5).
3. **[Robustness and incentives](tsi-report-3-robustness-and-incentives.md)** — jitter, grinding, withholding, selfish mining, the reward design, fork/reorg depth, and organic churn (§6).
4. **[Reproducibility and appendices](tsi-report-4-reproducibility-and-appendices.md)** — how to re-run every study (§9), the residual f-rounding offset (App A), the per-epoch noise floor (App B), and consensus detail (App C).

## Headline recommendation

Cryptarchia baseline f = 1/30. Two design choices are foundational: count uncles **per occupied slot**, not per block — the density-bug fix that lands the estimate at exactly `D` ([§2.1](tsi-report-2-accuracy-and-design.md#s2-1), [§8.5](tsi-report-1-overview-and-recommendations.md#s8-5)) — and make genesis `D̂` **a single protocol constant, identical at every node**, never client-configurable, since a per-node divergence is never self-corrected ([§8.1](tsi-report-1-overview-and-recommendations.md#s8-1) row 7). The settings: security `k = 2160`, uncle window `W = 300` slots, uncle cap `U ≥ ⌈ρ⌉ + 1` (2 at the Blend target; the protocol's `MAX_UNCLES = 4` sits safely above it), learning rate `β = 1`, on-chain `f` at 10⁻⁶ precision, peering degree ≥ 6 at scale, soft uncle rewards with `w_u + w_n < 1`, and operate at load `ρ = f·D_vis < 1`. The full recommended-configuration table and rationale are in **[Part 1 →](tsi-report-1-overview-and-recommendations.md)**.

## Figures

Figures are embedded from [`report-figures/`](report-figures) via relative links and are versioned here alongside the report. They are produced by the simulator's plotting scripts (`scripts/*.py` and `tsi_sim.plotting`) in [`tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode); that simulation folder does **not** commit its own generated figures — the copies checked in here are the report's figures of record.

## Reproducing the results

The simulation code, configs, and run data live in [`tools/simulators/tsi/tsi-sim-pernode`](../../tools/simulators/tsi/tsi-sim-pernode). Every study's exact command is listed in [Part 4 — Reproducibility (§9)](tsi-report-4-reproducibility-and-appendices.md). In short, from the simulator directory: `make install`, then `make <config>` to run a sweep (results land under `runs/<timestamp>_<label>/`), and the per-figure generators under `scripts/` render the figures. Regenerated figures must be copied into [`report-figures/`](report-figures) to update this report.
