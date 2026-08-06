# Evidence of record

The sweep outputs behind every number in [the report](../README.md). The simulator does not commit
its own `runs/` directory — these are the copies of record, kept so that any figure or table can be
re-derived, or challenged, without re-running hours of compute.

Each run directory holds the three tables the simulator writes: `propagation.parquet`,
`adversary.parquet` and `deanon.parquet`.

| directory | config | sampling | backs |
|---|---|---|---|
| `default/` | `configs/default.yaml` | 1 000 rounds × 8 seeds = **8 000/cell** | §3.1–§3.5 — delay, observation, eclipse, deanonymization, delivery, coverage |
| `redundancy/` | `configs/redundancy.yaml` | 1 200 × 8 = **9 600/cell** | §3.8 — messaging redundancy R = 1…4 |
| `percolation/` | `configs/percolation.yaml` | 800 × 8 = **6 400/cell** | §3.5 — the churn threshold `u_c = 1 − 1/(degree − 1)` |
| `correlated-churn/` | `configs/correlated-churn.yaml` | 800 × 8 = **6 400/cell** | §3.9 — correlated AS/region outages vs uniform churn |
| `fullscale/` | `configs/fullscale.yaml` | 64 × 3 = **192/cell** | §5 — the 10⁶ scaling check (deliberately lighter; not a source of headline numbers) |
| `cover-traffic/` | `configs/cover-traffic.yaml` | 900 s timeline × 4 seeds | §3.10 — blending, mixing, and the emission-quota stake ceiling. Carries a fourth table, `traffic.parquet` |
| `timing/` | `configs/timing.yaml` | 120 s timeline × 3 seeds | §3.11 — the two release designs under a timing attack, and the minimum-interval control |

The linkability results (§3.6–§3.7) and both deanonymization rates are closed forms over these
tables rather than separate measurements, so they have no run of their own — `blend.linkability`
derives them and `make verify` checks them against Monte-Carlo.

## Regenerating the report's numbers

```
python report_numbers.py
```

prints every quoted value with its across-topology standard error, straight from the parquets here.
That is the fastest way to check a table in the report against its evidence. It takes optional
paths (`report_numbers.py <default> <redundancy> <percolation>`) if you want to point it at fresh
runs instead.

## Regenerating the data itself

From [`tools/simulators/blend`](../../../tools/simulators/blend): `make sweep`,
`make redundancy`, `make percolation`, `make correlated-churn`, `make sweep-fullscale`. Results
land in that simulator's `runs/<timestamp>_<label>/`. Note that the seed streams depend on the
configuration, so re-running reproduces the *statistics*, not bit-identical numbers, unless the
config is unchanged — in which case it does reproduce exactly.

Two runs from the same session are deliberately **not** kept: the smoke runs (throwaway, far too
noisy to interpret) and an earlier 144-rounds/cell redundancy grid that was superseded because its
sampling error produced a non-monotonic delivery curve — the reason `redundancy/` samples 9 600.
