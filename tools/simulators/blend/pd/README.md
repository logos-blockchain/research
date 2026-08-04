# pd — peering-degree Monte-Carlo graph simulator

Quantifies how a node's **peering degree** trades off, in the Blend network:

- **propagation speed** — the full delay (ms) of a message: a random sender routes it along a
  `blend_hops`-relay Blend path (each relay a free-running timed-release mix node) and the last
  relay floods the whole network;
- **adversary exposure** — with a fraction `f_adv` of adversarial nodes, how many honest nodes are
  peered with ≥1 adversary (**observed**) and how many are fully surrounded (**eclipsed**);
- **deanonymization** — tying propagation to the adversary: how often a message's *whole* blend path
  is adversarial (**deanonymization** — the adversary owns the cascade end-to-end) and how often the
  honest sender is *additionally* peered with an adversary (**full deanonymization** — the message is
  tied back to its originator); and
- **reliability under churn** — with a fraction `unresponsive_frac` of nodes that relay nothing, the
  **message success-delivery-rate** (fraction of messages that survive the whole blend cascade to a
  responsive final relay) and the flood **coverage** of those that do.

The peer graph is a seeded random **d-regular** graph (exactly `degree` symmetric peers, identical
for everyone from one global seed). This is static-graph analysis — no consensus — so it is far
lighter than the TSI simulators and scales to **10⁶ nodes** (sparse CSR + sampled Dijkstra; the
adversary metrics are exact at every N).

## Model (all delays in ms)
- **Link delay:** geographic base (metro 15 → antipodal 200 ms) + exponential transport jitter.
- **Processing lag:** each node draws a fixed lag from a categorical distribution (default
  {10, 50, 100} ms at {0.5, 0.4, 0.1}), incurred every time it relays.
- **Blend mixing:** each relay releases on a free-running clock whose successive intervals are
  Uniform{0…`max_blend_delay`} whole seconds; a held message waits for the relay's next release
  (the renewal residual). Mixing happens only at the `blend_hops` relays; the final flood is plain.
- **Unresponsive nodes:** a random `unresponsive_frac` of the population relays nothing (its outgoing
  edges are removed). Relays are drawn from the whole node list *blind to responsiveness*, so a
  message dies if any relay on its path is unresponsive — the delivery-rate then tracks
  `(1−unresponsive_frac)^blend_hops`. Unresponsive nodes still *receive*, but they are routing holes,
  so a delivered flood can strand pockets; a higher peering degree supplies redundant paths that keep
  coverage high. This axis affects propagation only, not the adversary metrics.
- **Deanonymization:** relays are picked *blind to who is adversarial*, so P(the whole blend path is
  adversarial) is the exact hypergeometric `C(n_adv, blend_hops) / C(N−1, blend_hops)` ≈
  `f_adv^blend_hops` (**deanon_rate**) — placement-independent, driven by path length, not degree.
  Multiplying by the fraction of honest nodes with ≥1 adversary peer (`observed_frac`, which the
  worst-case-coverage placement maximizes) gives **full_deanon_rate** — the honest sender is *also*
  directly exposed, so the message is tied to its originator. Lengthening the blend path is the
  dominant defence; a higher degree speeds propagation but *raises* the chance a sender directly
  touches the adversary. Both are exact at every N (no Monte-Carlo), like the other adversary metrics.
- **Messaging redundancy:** `redundancy` R sends each emission over R *independent* blend cascades.
  A node receives the message from whichever cascade reaches it first (arrival times are combined
  element-wise), so it is delivered if any cascade delivers (`delivery = 1−(1−(1−u)^blend_hops)^R`)
  and captured if any cascade is whole-path-adversarial (`deanon = 1−(1−f_adv^blend_hops)^R`) — the
  same `1−(1−x)^R` law, so redundancy trades reliability against anonymity. It buys **no** extra
  coverage: a cascade only delivers if the sender could route to its relay, so every delivered
  cascade floods the sender's own component. R = 1 is the plain single-cascade model (default), to
  which the whole aggregation reduces exactly.
- **Churn percolation:** the flood only crosses responsive nodes, so it lives on the responsive
  sub-graph — site percolation on a d-regular graph, whose giant component survives only while the
  responsive fraction exceeds `1/(degree−1)`. A network tolerates churn up to
  `u_c = 1 − 1/(degree−1)` (degree 3 → 0.5, degree 6 → 0.8, degree 16 → 0.93) and shatters above it;
  `configs/percolation.yaml` walks u across the threshold and `make verify` checks it.
- **Linkability over time** (`pd.linkability`): given the rates above and an emission cadence (one
  node emits per 30 s slot, chosen ∝ stake), the module derives the *time to link* an emitter
  (`≈ 30 s·ln(1/(1−α))/(stake·q)`, inverse in stake) and the *time to learn its stake* to a threshold
  from the count of attributable observations. See `configs/redundancy.yaml` and the report.

## Quick start
```
make install                 # or reuse a sibling venv: PYTHONPATH=src <python> -m pd.sweep ...
make smoke                   # fast end-to-end -> runs/<ts>_smoke/{propagation,adversary}.parquet + figures/
make verify                  # analytic checks (closed forms + graph invariants)
make test                    # unit tests
make sweep                   # configs/default.yaml (N up to 1e5, both adversary modes)
make sweep-fullscale         # configs/fullscale.yaml (N up to 1e6, random-mode exact)
make redundancy              # configs/redundancy.yaml (R=1..4: delivery vs deanonymization)
make percolation             # configs/percolation.yaml (churn threshold u_c = 1-1/(degree-1))
make figures RUN=runs/<dir>
```

## Outputs
Three parquets per run: `propagation.parquet` (`full_delay_ms_*`, `delivery_rate`, `frac_reached`,
`coverN_ms` vs degree / blend_hops / N / unresponsive_frac), `adversary.parquet` (`observed_frac` /
`eclipsed_frac` vs degree / f_adv / mode, random + worst-case envelope), and `deanon.parquet`
(`deanon_rate` / `full_deanon_rate` vs degree / blend_hops / f_adv / mode — propagation paths crossed
with the adversary set). Figures render all three, including delivery-rate and flood-coverage vs the
unresponsive fraction and the deanonymization rates vs blend-path length, f_adv, and degree.

## Layout
`src/pd/`: `graph` (matching-union CSR d-regular), `propagation` (Blend cascade), `mixclock`
(release-clock residual), `adversary` (exact observation/eclipse + deanonymization + placement),
`config`/`engine`/`sweep`/`metrics`, `plotting`. `configs/` sweeps, `tests/`, `scripts/` shims.
Reports of record live outside the sim at `reports/blend/pd/`.
