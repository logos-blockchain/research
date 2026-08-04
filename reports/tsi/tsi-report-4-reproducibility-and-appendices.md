# Total-Stake-Inference parameter selection — Reproducibility and appendices

*Per-node network simulation of Cryptarchia Total Stake Inference (TSI). Simulator: `tsi-sim-pernode`. All runs at the true security parameter **k = 2160** unless noted; latency is in slots and **1 slot = 1 s**.*

*[Part 1 — Overview & recommendations](tsi-report-1-overview-and-recommendations.md) · [Part 2 — Accuracy & design](tsi-report-2-accuracy-and-design.md) · [Part 3 — Robustness & incentives](tsi-report-3-robustness-and-incentives.md) · [Part 4 — Reproducibility & appendices](tsi-report-4-reproducibility-and-appendices.md) · [Index](README.md)*

*Sections live across the set: [§1](tsi-report-1-overview-and-recommendations.md#s1)/[§7](tsi-report-1-overview-and-recommendations.md#s7)/[§8](tsi-report-1-overview-and-recommendations.md#s8) in Part 1, [§2](tsi-report-2-accuracy-and-design.md#s2)–[§5](tsi-report-2-accuracy-and-design.md#s5) in Part 2, [§6](tsi-report-3-robustness-and-incentives.md#s6) in Part 3, [§9](#s9) and Appendices A–C in Part 4.*

---

<a id="s9"></a>
## 9. Reproducibility

Sweep studies are committed configs, run with `make <name>` (writes a dated `runs/` folder with results + figures); standalone studies are scripts. Throughout this part, `D` is the true active stake, `D̂` a node's TSI estimate of it, `D̂/D` the accuracy (1.0 = exact; [§2.2](tsi-report-2-accuracy-and-design.md#s2-2)), `f` the target block rate (`1/30` here) and `ρ = f·D_vis` the delay load ([§3.3](tsi-report-2-accuracy-and-design.md#s3-3)). In section order:

*Symbols used in this table (defined in Parts 2–3): `D̂/D` = recovered estimate ÷ true total stake; `U` = per-block uncle cap; `W` = uncle window in slots ([§3.4](tsi-report-2-accuracy-and-design.md#s3-4)); `ℓ_mean` = mean gossip path latency between two nodes, `D_vis` = mean visibility delay `hops·δ_max/2 + (hops+1)·ℓ_mean`, `ρ` = load `f·D_vis` ([§3.3](tsi-report-2-accuracy-and-design.md#s3-3)); `p_ref` = the probability an orphaned honest block is referenced as an uncle within `W` ([§6.7](tsi-report-3-robustness-and-incentives.md#s6-7)).*

| study | config / script | § |
|---|---|---|
| full-scale confirmation (N, uncle recovery) | `configs/fullscale.yaml` (as committed: `n_nodes: [5000, 10000]`; the N = 1 000/2 000 rows come from a dedicated committed config, `configs/fullscale-small.yaml` — a separate, coarser grid, not this config re-run with `n_nodes` edited) | [§3.1](tsi-report-2-accuracy-and-design.md#s3-1), [§3.2](tsi-report-2-accuracy-and-design.md#s3-2) |
| bootstrap at full scale (k = 2160, Blend, N = 1 000/5 000, U ∈ {0, 2}) | `scripts/bootstrap_dynamics.py` (`runs/bootstrap_fullscale`) | [§3.2](tsi-report-2-accuracy-and-design.md#s3-2) |
| one-uncle breakdown (hops × delay, N = 1 000/2 000) | `configs/blend-hops-delay.yaml`; fig3 by `scripts/hops_delay_grid.py` | [§3.3](tsi-report-2-accuracy-and-design.md#s3-3) |
| ρ-boundary deficit sweep (`1 − D̂/D` vs ρ per U; hops=3, N=1000, 20 reps, k=256) | `configs/rho-boundary.yaml`; fig26 by `scripts/rho_boundary_analysis.py` | [§3.3](tsi-report-2-accuracy-and-design.md#s3-3) |
| relative stake vs delay (D̂/D vs D_vis, per U) | `scripts/stake_vs_delay.py` | [§3.3](tsi-report-2-accuracy-and-design.md#s3-3) |
| uncle-window sufficiency (W × delay, N = 1 000/2 000) | `configs/uncle-window.yaml` | [§3.4](tsi-report-2-accuracy-and-design.md#s3-4) |
| joint (W, U) region (N = 1 000/2 000) | `configs/window-uncles.yaml` | [§3.5](tsi-report-2-accuracy-and-design.md#s3-5) |
| block rate | `configs/block-rate.yaml` | [§3.6](tsi-report-2-accuracy-and-design.md#s3-6) |
| heterogeneous-start (no re-convergence; N = 400, k = 256) | `configs/default.yaml` (`init_dest: heterogeneous`, `init_spread: 0.5`) | [Appendix C](#sC) |
| N-scaling of the one-uncle boundary (N = 1k–32k, cases a/b; k = 256) | `configs/nscaling-{a,b}.yaml`, `configs/nscaling32-{a,b}.yaml`; analysis + figures by `scripts/nscaling_analysis.py` | [§3.7](tsi-report-2-accuracy-and-design.md#s3-7) |
| exact large-N topology probe (`ℓ_mean` to N = 10⁶, degrees 4/6/8) | `scripts/topology_probe.py` (`runs/topology_probe.parquet`) | [§3.7](tsi-report-2-accuracy-and-design.md#s3-7) |
| link-latency shape sensitivity (exp vs geo at equal mean) | `configs/expdist.yaml` (baseline cells: the nscaling-a run) | [§2](tsi-report-2-accuracy-and-design.md#s2) |
| stake-tail sensitivity (Pareto 1.33 vs 1.16) | `configs/pareto133.yaml` (baseline cells: the nscaling-a run) | [§2](tsi-report-2-accuracy-and-design.md#s2) |
| window sufficiency at scale + W-as-buffer (N = 1 000/10 000, W ≤ 600) | `configs/window-scale.yaml`; fig25 by `scripts/window_scale_analysis.py` | [§3.4](tsi-report-2-accuracy-and-design.md#s3-4) |
| fork rate + reorg depth vs delay/adversary stake | `scripts/reorg_depth.py` (`--measure`; `--measure-scale` for fork rate vs N/degree; `src/tsi_sim/reorg.py`); fig27, fig28 | [§6.10](tsi-report-3-robustness-and-incentives.md#s6-10) |
| organic stake churn (sine/ramp/step) | `scripts/churn.py` (`churn_amp`/`churn_period`/`churn_mode` fields); fig29 | [§6.11](tsi-report-3-robustness-and-incentives.md#s6-11) |
| per-node clock skew (bounded consensus cost) | `scripts/clock_skew.py` (`clock_skew_max` field) | [§6.1](tsi-report-3-robustness-and-incentives.md#s6-1) |
| capstone: recommended config end-to-end + 30 % adversary | `scripts/capstone.py` (`runs/capstone.parquet`) | [§8.4](tsi-report-1-overview-and-recommendations.md#s8-4) |
| jitter / consensus | `jitter_mean` > 0 + `windowed_fork_choice: false` (exact oracle); data in `runs/jitter_grid/results.parquet` | [§6.1](tsi-report-3-robustness-and-incentives.md#s6-1) |
| load-feedback fixed point | analysis of the U=0 sweep + `theory.expected_ratio` | [§6.2](tsi-report-3-robustness-and-incentives.md#s6-2) |
| adversarial grinding (uncle suppression) | `scripts/adversary_grid.py` (`adversary_frac` + `adversary_strategy: suppress`); data in `runs/adversary_grid/suppress.parquet` | [§6.3](tsi-report-3-robustness-and-incentives.md#s6-3) |
| block withholding | `scripts/adversary_grid.py` (`adversary_strategy: withhold`); data in `runs/adversary_grid/withhold.parquet` | [§6.4](tsi-report-3-robustness-and-incentives.md#s6-4) |
| dynamic withhold-rejoin grinding | `scripts/dynamic_withhold.py` (`adversary_period`, `adversary_withhold_epochs`) | [§6.5](tsi-report-3-robustness-and-incentives.md#s6-5) |
| selfish / private-chain withholding | `scripts/selfish_mining.py` (`src/tsi_sim/selfish.py`) | [§6.6](tsi-report-3-robustness-and-incentives.md#s6-6) |
| optimal selfish (SSZ MDP) + uncle rewards | `scripts/selfish_rewards.py` (`src/tsi_sim/selfish_mdp.py`, `RewardParams`) | [§6.6](tsi-report-3-robustness-and-incentives.md#s6-6), [§6.7](tsi-report-3-robustness-and-incentives.md#s6-7) |
| soft uncle inclusion (reward share vs emergent `p_ref`) | `scripts/reward_mandate.py` | [§6.8](tsi-report-3-robustness-and-incentives.md#s6-8), [§6.9](tsi-report-3-robustness-and-incentives.md#s6-9) |
| U = 0 fluctuation series (zero delay, k ∈ {256, 1024, 2160}) | `scripts/appendix_fluct.py --run` (`runs/fluctuation_u0.parquet`) | [Appendix B](#sB) |
| CI smoke grid + analytic sanity checks | `configs/smoke.yaml`; `scripts/verify.py` (`make verify`) — validation only, no figures | — |
| **countable vs unrestricted referencing** (accuracy over delay × U; measured `q_u`/recovery `r`) | `configs/countable-vs-old.yaml` run twice — default and with `--old`; figures + significance table by `scripts/plot_countable_vs_old.py` | [§2.1](tsi-report-2-accuracy-and-design.md#s2-1), [§3.2](tsi-report-2-accuracy-and-design.md#s3-2) |
| **fine delay band** (δ_max 1–5 at 40 replicates; tight CI on the model gap in the design regime) | `configs/fine-delay.yaml` run twice — default and with `--old`; figure + table by `scripts/plot_fine_delay.py` | [§3.2a](tsi-report-2-accuracy-and-design.md#s3-2a) |
| **window absorption sweep** (`W` in expected block-intervals, `w_u = W/f` derived) | `configs/absorption-window.yaml`; figure by `scripts/plot_countable_vs_old.py` | [§3.4](tsi-report-2-accuracy-and-design.md#s3-4) |

**Uncle-model convention.** The simulator's default is the **countable** model — first-fork candidates only, derived window `w_u = W/f`, occupied-slot exclusion, per-reference counting rules ([§2.1](tsi-report-2-accuracy-and-design.md#s2-1)). The **unrestricted** baseline is preserved in the code and selected with `--old` on `tsi-sweep`/`tsi-verify`. Its RNG key is byte-identical to the pre-restriction key, so `--old` **bit-reproduces the earlier runs**: a `rho-boundary` cell (δ_max = 8, U = 2, k = 256, N = 1 000) re-run under `--old` matches the committed `2026-07-27_195627_rho-boundary` parquet with `max |Δ| = 0` on every epoch and every metric. Studies in the table above that predate the countable default were produced under the unrestricted model and reproduce exactly under `--old`; the comparison rows quantify where the two models differ, and in the design regime (`ρ < 1`) no difference is resolvable, so those findings carry over unchanged.

Because the two models draw independent RNG streams, every countable-vs-unrestricted comparison is **unpaired**, and its resolution is set by the replicate spread rather than by the effect size. Each comparison sweep therefore includes a `U = 0` arm as a **negative control**: with no uncles the models are identical by construction, so the measured `U = 0` gap is a direct reading of the noise floor at that delay and replicate count. At `δ_max = 32` with 5 replicates that floor is ≈ 0.23 in `D̂/D` — larger than several real effects elsewhere in the grid — which is why [§3.2](tsi-report-2-accuracy-and-design.md#s3-2) reports a `t` statistic per cell and why the design regime is measured separately at 40 replicates ([§3.2a](tsi-report-2-accuracy-and-design.md#s3-2a)).

All studies were **re-run on 2026-07-23/24 with the corrected slot-counting mechanism** ([§2.1](tsi-report-2-accuracy-and-design.md#s2-1)) and the early-stop optimisation; the resilient batch is `scripts/run_all_reruns.sh` (per-step log in `runs/rerun_status.log`). Canonical run directories (latest): fullscale N=5000/10000 = `2026-07-24_094519_fullscale`; fullscale N=1000/2000 = `2026-07-23_171803_fullscale-small`; uncle-window = `2026-07-24_001456`; window-uncles = `2026-07-24_014240`; block-rate = `2026-07-24_043943`; blend-hops-delay = `2026-07-24_064052`; window-scale = `2026-07-24_085234`; latency-shape = `2026-07-24_090014_expdist`; stake-tail = `2026-07-24_090044_pareto133`; heterogeneous-start = `2026-07-24_090114_default`; N-scaling = the `nscaling-{a,b}` + `nscaling32-{a,b}` runs; adversary grids = `runs/adversary_grid/`; jitter = `runs/jitter_grid/`; bootstrap = `runs/bootstrap_fullscale/`; fluctuation = `runs/fluctuation_u0.parquet`; fork-rate = `runs/fork_rate_vs_delay.parquet`; ρ-boundary = `2026-07-27_195627_rho-boundary`.

Figures are in `report-figures/` (`fig1`–`fig29`, plus [Appendix B](#sB)'s `figB1`–`figB2`; numbering is generation order, not order of appearance). Committed generators: `fig1` (bootstrap, k=2160) by `scripts/bootstrap_dynamics.py`; `fig2`,`fig4`,`fig5`,`fig17`–`fig22` by `scripts/regenerate_extra_figs.py` from the latest sweeps (`fig3` hops×delay×U grid by `scripts/hops_delay_grid.py`, `fig6` (block-rate `U_min` grid + ρ-collapse) rendered ad hoc from `runs/2026-07-24_043943_block-rate` with no committed generator; `fig26` deficit-vs-ρ by `scripts/rho_boundary_analysis.py`) (fullscale-derived `fig17`–`fig20` pool both sizes in that run, N = 5 000 and N = 10 000 — the generators filter on stake_dist/topology/degree/init_dest only, never on `n_nodes`); `fig8`,`fig9` by `scripts/adversary_figs.py` from `runs/adversary_grid/`; `fig10`–`fig12` by `scripts/dynamic_withhold.py`; `fig13`–`fig15` by `scripts/selfish_mining.py`/`selfish_rewards.py`/`reward_mandate.py`; `fig16` by `scripts/stake_vs_delay.py`; `fig23`–`fig24` by `scripts/nscaling_analysis.py`; `fig25` by `scripts/window_scale_analysis.py`; `fig27`–`fig28` by `scripts/reorg_depth.py` (fork rates via `--measure`; private-chain model `src/tsi_sim/reorg.py`); `fig29` by `scripts/churn.py`; `figB1`–`figB2` by `scripts/appendix_fluct.py`. `fig7` (feedback fixed-point) is an analytic overlay; `fig30`–`fig33` (countable-vs-unrestricted accuracy, `q_u`-prediction check, recovery rate, absorption-window sweep) by `scripts/plot_countable_vs_old.py` from the `cvo-countable`/`cvo-old`/`absorption-window` runs; `fig34`–`fig35` (design-regime accuracy and the model gap with 95 % CIs) by `scripts/plot_fine_delay.py` from the `fine-countable`/`fine-old` runs. Every figure type the per-node simulator generates appears in this report, and the fork-rate/reorg-depth study closes the previous reproducibility gap for the adversarial figures (`fig8`,`fig9` now have committed generators from `runs/adversary_grid/`).

---


<a id="sA"></a>
## Appendix A — The residual ~1 % offset: on-chain rounding of `f`

**The question.** With correct slot-counting ([§2.1](tsi-report-2-accuracy-and-design.md#s2-1)) the recovered estimate `D̂` settles at the true active stake `D`. Why does the *deployed* estimator carry a small residual ~1 % above `D`, and how is it removed?

**The multi-winner slot, counted once.** The lottery gives node `i` an independent win chance `φ = 1 − (1−f)^{w_i/D̂}` (`w_i` = node i's stake). At `D̂ = D` the probability a slot has *at least one* winner is `1 − ∏(1−φ_i) = 1 − (1−f)^{Σw_i/D} = f` — slots activate at exactly the target rate. A slot can have *several* winners (the expected count is `−ln(1−f) = f·c(f) > f`, so busy slots are ~1.7 % more blocks than slots), and the surplus co-winners are always orphaned — even at zero delay. TSI counts **occupied slots**, so it counts such a slot **once**: the co-winner adds no count whether it is canonical or a referenced uncle. Holding the occupied-slot density at `f` therefore settles the estimate at exactly `D`, with no `c(f)` ceiling. (Counting uncle *blocks* instead double-counts these co-winner slots and inflates the equilibrium to `c(f)·D ≈ 1.017·D`; that is the deployed-spec bug and fix — see [§2.1](tsi-report-2-accuracy-and-design.md#s2-1) and [§8.5](tsi-report-1-overview-and-recommendations.md#s8-5).)

**Verified in isolation.** The zero-delay isolation series of [§3.2](tsi-report-2-accuracy-and-design.md#s3-2) (full mesh, latency 0 — same-slot co-winners the only orphans) confirms this: `U = 2` lands at `1.000 ± 0.007`, not at a ceiling, because the co-winner slots are counted once. Double counting is structurally impossible: uncle slots are de-duplicated against the canonical slots and against each other, and a slot can never be both canonical and a counted uncle.

**The one residual offset — and it is optional.** The spec stores the target rate as an on-chain integer at three-decimal precision: `f_p = ⌊1000·f⌋/1000 = 0.033`, not `1/30 = 0.03333…`. Driving the density to `f_p` rather than to `f` leaves the estimate high by the fixed factor `f/f_p ≈ 1.010` — a ~1 % over-estimate, common to every node (so fairness is untouched) but an absolute ~1 % under-delivery of win probability and a ~1 % slow canonical pace. It grows mildly with the block rate. It is removed by carrying `f` at higher precision. **This report's estimator uses exact `f` (the analysis-faithful default, `fixed_point=False`), so `f/f_eff = 1.000` and the residual is 0** — finer than the recommended 10⁻⁶ spec bump (`33333`→`0.033333`, `f/f_p = 1.00001`, residual < 10⁻⁵); the current spec still uses 10⁻³ and should adopt the bump ([§8](tsi-report-1-overview-and-recommendations.md#s8) row 14). This `f/f_p` factor is the *only* systematic departure from 1 that the counting fix leaves, and it is the sole reason a deployed `D̂/D` reads ≈ 1.01 rather than 1.00.

---


<a id="sB"></a>
## Appendix B — the per-epoch sampling-noise floor (and why one uncle restores it)

**The question.** The equilibrium is bounded by 1 ([§2.2](tsi-report-2-accuracy-and-design.md#s2-2)), but individual epochs read 1.003 or 0.994. How large is that per-epoch noise, what sets it, and does it bias any single accuracy number in this report?

**The answer up front.** The U = 0 estimate is an *unbiased but noisy* measurement: its delay-free equilibrium is exactly 1 ([§2.2](tsi-report-2-accuracy-and-design.md#s2-2)) and its per-epoch spread is pure sampling noise of the finite measurement window — `σ ≈ √((1−f)/(f·T))`, about **±0.9 % at the production window** (k = 2160). To show this cleanly we simulate the **delay-free limit directly** (full mesh, zero latency — no orphan loss at all, so *only* the noise remains); a realistic sub-slot gossip series then confirms the same magnitude, and the delay progression ([§B.3](#sB-3)) shows how real orphan loss turns that noise one-sided, pinning the estimate **below** 1 — the bounded-by-1 deficit of [§3.2](tsi-report-2-accuracy-and-design.md#s3-2). Every number below is measured; nothing is asserted.

<a id="sB-1"></a>
### B.1 The mechanism: a stochastic controller passes its measurement noise through

At U = 0 with negligible delay the counted density is the *active-slot* rate, which the lottery calibrates to exactly `f` at `D̂ = D` (the multi-winner identity of [Appendix A](#sA)) — so the fixed point is exactly 1, with no ceiling. But the measured density `m/T` is a random variable: the window contains only `f·T` expected blocks, so one epoch's measurement carries relative noise `σ ≈ √((1−f)/(f·T))`. At the deployed learning rate `β = 1` the update `D̂ ← D̂·(1 − β(f − m/T)/f)` passes that noise straight into the estimate: each epoch's `D̂/D` is `≈ 1 + ε` with `ε` the window's sampling error. The estimate is therefore *expected* to read 1.003 or 0.994 in individual epochs — those are not anomalies but the noise floor itself.

<a id="sB-2"></a>
### B.2 Measured: the ±0.9 % noise floor, shrinking as 1/√T

A dedicated zero-delay series (full mesh, link latency `L = 0`, U = 0, equal stakes, 4 × 120 epochs per k) isolates the fluctuation with no orphan loss at all:

| k (window `T = 6⌊k/f⌋`) | mean `D̂/D` | per-epoch σ (measured) | σ theory | P(`D̂/D` > 1) | largest excursion (448 epochs) |
|---|---|---|---|---|---|
| 256 | 0.99914 | 0.0254 | 0.0251 | 0.50 | **1.082** (3.3σ) |
| 1024 | 1.00079 | 0.0126 | 0.0125 | 0.54 | 1.049 (3.9σ) |
| 2160 | 1.00006 | 0.0088 | 0.0086 | 0.53 | 1.035 (4.1σ) |

The mean is pinned at 1 to within ±0.001 at every window size — the estimator is unbiased at the bound — while the spread follows the `1/√T` law to within a few percent. `figB1` shows the per-epoch trace at k = 2160 on a per-mil axis: the clean zero-delay series and the realistic 0.1-slot direct-gossip series (epochs 4–16, where the two overlap) both fluctuate about zero *on the scale of* the predicted ±σ_th band — 65 % of zero-delay epochs fall inside it, the ~68 % a ±1σ band should contain — with Gaussian tails out to ≈ 4σ (+35 per-mil). The band is the noise scale, not a bound.

![Fig B1 — per-epoch (D̂/D − 1) in per-mil at U=0, k=2160: the zero-delay series (epochs 4–119) and the sub-slot-gossip series (epochs 4–16) fluctuate about zero on the scale of the ±σ_th = √((1−f)/fT) sampling-noise band — ~2/3 of epochs inside it, tails to ≈4σ — around the ≤1 equilibrium.](report-figures/figB1_fluctuation_trace.png)

<a id="sB-3"></a>
### B.3 Delay converts the fluctuation into a one-sided under-count

The committed full-scale N = 1 000/2 000 (k = 2160) data shows how real delay changes the picture (`figB2`, middle): at 0.1-slot links the U = 0 estimate reads `0.9993 ± 0.0089` with `P(>1) = 52 %`; at 0.2 slots the mean slips to 0.9955 and `P(>1)` to 34 %; by 0.5-slot links orphan loss dominates (mean 0.962, **never** above 1 in the 136 tail epochs); and under Blend U = 0 sits far below (mean 0.726, maximum 0.993). So "fluctuates around 1" is the *delay-free limit* of the U = 0 estimator; in the deployment regime (Blend) the U = 0 estimate is one-sidedly low, and the fluctuation instead rides on the recovered value; blend at U = 1 crosses 1.0 in ~50 % of epochs, the same symmetric noise around the recovered fixed point.

**Delay also changes the *size* of the fluctuation — but not gradually** (`figB2`, right). Under direct gossip the per-epoch spread stays at the sampling floor at every link delay (σ = 0.008–0.010 from 0.1 to a full slot): mild orphan loss shifts the *mean*, not the noise. Under Blend at U = 0 the fluctuation **explodes to σ ≈ 0.15–0.16 — about 18× the floor**: with a third of blocks orphaning, the counted density is decided by fork races, and the [§6.2](tsi-report-3-robustness-and-incentives.md#s6-2) load feedback (a deflated `D̂` raises the raw proposal rate, which raises orphaning again) amplifies that race noise into ±15 % per-epoch swings. **A single uncle restores not just the mean but the noise floor itself**: at U = 1 the per-epoch σ returns to 0.009 in every cell, Blend included — the uncle mechanism stabilises the estimator's *variance* as well as its *bias*, a second, independent reason to provision `U` correctly.

![Fig B2 — left: the per-epoch deviation distribution shrinks as 1/√T (k = 256 → 2160, measured σ vs theory); middle: as link delay grows the U=0 mean drops below 1 and P(D̂/D > 1) collapses to zero — orphan loss is one-sided; right: per-epoch σ stays at the sampling floor under direct gossip but explodes ~18× under Blend at U=0, and one uncle restores the floor.](report-figures/figB2_fluctuation_stats.png)

<a id="sB-4"></a>
### B.4 What precision is meaningful

A reading like `1.001` is well inside one epoch's noise (±0.009 at k = 2160) — real and expected. A reading like `1.000001` is **not resolvable**: it is four orders of magnitude below the per-epoch noise floor, and even averaging would need ~10⁷ epochs to distinguish it from 1. The meaningful statements at the production window are: the U = 0 delay-free estimate is unbiased at 1 with ±0.9 % per-epoch noise; per-epoch tables in this report are therefore quoted to three decimals, and equilibrium values are tail-averages over ≥ 15 epochs × replicates (±0.1–0.2 % standard error). Any accuracy differences smaller than that are noise, not signal.

---


<a id="sC"></a>
## Appendix C — Consensus properties in detail

*Supporting detail for [§3.1](tsi-report-2-accuracy-and-design.md#s3-1): the per-epoch traces, the tip-agreement contrast, and the one caveat — agreement is inherited from initialization, never rebuilt.*

<a id="sC-1"></a>
### C.1 Per-epoch traces at the largest scale

`fig17` shows the per-epoch picture **at the two largest tested scales pooled, N = 5 000 and N = 10 000** (the `fullscale` config sweeps both sizes; 6 replicates per cell, up to 30 epochs — early stopping thins the trace after ≈ epoch 24, so the last points rest on a handful of trajectories): the per-node `D̂/D` spread (full range and interquartile range, top) sits at 0 for the whole run while node agreement on the finalized window prefix (bottom) stays at 1.000 — the consensus result holds unchanged from `N = 1 000` up to `N = 10 000`.

![Fig 17 — pooled over N=5000 and N=10000, per-node D̂/D spread stays ≡ 0 and window agreement ≡ 1.000 at every epoch reached, even as current-tip agreement stays below 1.](report-figures/fig17_divergence.png)

The one metric that is *not* exactly 1 is **current-tip** agreement (`fig18`, same fullscale run — but its `U = 0` curves pool both sizes in that run, N = 5 000 and N = 10 000): nodes share the live tip most of the time (≈ 0.985–0.994 typical), dipping to ~0.985 in the worst plotted cell; restricted to N = 10 000 the same cells run 0.978–0.996 (worst 0.978 at degree 6, delay 1 s), and the worst tip cell at N = 10 000 over all `U` is 0.971 — a small, transient tip churn that never reaches the deeply-buried density window, which is why `D̂` agreement is exact regardless.

![Fig 18 — current-tip agreement (fullscale run, U=0, N=5000 and N=10000 pooled) is high but below 1 (≈ 0.985–0.994 typical, ~0.985 worst plotted cell; 0.978–0.996 restricted to N=10000); the transient tip forking it measures never propagates into D̂.](report-figures/fig18_tip_agreement.png)

<a id="sC-2"></a>
### C.2 Consensus rests on common initialization — there is no active re-convergence

The [§3.1](tsi-report-2-accuracy-and-design.md#s3-1) consensus (spread → 0) holds because every node starts at the *same* genesis `D̂` and applies the *same* update to the *same* finalized density. To test whether TSI would *re-heal* a divergence that arose anyway, we seeded the nodes with a **heterogeneous** initial `D̂` (a ±50 % per-node spread around a genesis guess set at `0.5×` the true stake; N = 400 / scaled k = 256, equal stakes, regular topology) and watched it evolve.

The inter-node disagreement does **not** contract (`fig21`): the strictly conserved quantity is the **ratio between the highest and lowest node estimate**, `max/min ≈ 3.0`, which stays flat to three digits across all epochs. The absolute spread `range(D̂/D)` is *not* invariant — because the mean starts low (`0.5×`) it is scaled **up** in the first epoch (a common factor ≈ 2.15 rescales mean *and* spread together, so the spread jumps from its injected ≈ 0.5 to ≈ 1.07 within epoch 0) and then holds flat near ≈ 1.09 — so the disagreement is rescaled, never healed. (`fig21` plots the *post*-update spread, which already sits at ≈ 1.07 by epoch 0 and stays flat; the ≈ 0.5 → ≈ 1.07 rescale happens inside the first epoch and is not itself drawn.) The reason is structural — the recursion `D̂ ← D̂·(1 − β(f − m/T)/f)` (`β` = the TSI learning rate, `m/T` = the measured density over the window `T`; [§6.5](tsi-report-3-robustness-and-incentives.md#s6-5)) applies a *common* multiplicative factor (all nodes read the same global `m`), so the ratio between any two nodes' estimates is invariant; there is no inter-node coupling to pull them together.

**Caveat:** TSI's consensus is *maintenance*, not *repair* — it keeps identically-initialized nodes identical, but a coalition that could inject persistent per-node `D̂` disagreement (e.g. via a genesis/clock exploit) would not be corrected by the estimator itself. In the honest protocol this never arises (genesis `D` is a shared constant), so [§3.1](tsi-report-2-accuracy-and-design.md#s3-1) stands; the point is that the consensus is an *initialization* property, not a restoring force.

![Fig 21 — heterogeneous start: an injected per-node D̂ disagreement (node-to-node ratio max/min ≈ 3.0) is preserved, not healed — the common multiplicative update rescales the spread but never contracts the ratio, so TSI has no active re-convergence mechanism.](report-figures/fig21_heterogeneous_recovery.png)
