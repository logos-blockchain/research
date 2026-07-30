"""Exact large-N topology probe: mean gossip path latency l_mean(N, degree) up to N = 10^6.

The only N-dependent term in the load law rho = f*D_vis (report §3.3/§4, eq 1) is the mean
shortest-path transport latency l_mean over the peering graph, which grows ~ log_(d-1) N.
Direct per-node simulation is memory-bound at N ~ 3*10^4 (the N x N matrix), but l_mean is
measurable EXACTLY at any N with sampled-source Dijkstra on the same graph generator the
simulator uses (circulant base + 10x Maslov-Sneppen swaps, geo per-link latencies).

Writes runs/topology_probe.parquet: one row per (n, degree, replicate) with l_mean, quantiles,
and the derived D_vis / rho for the study's mixing budgets. Used by report §3.8.

Run:  python scripts/topology_probe.py          (~2-3 h, parallel over cells)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.config import SimConfig  # noqa: E402
from tsi_sim.topology import (  # noqa: E402
    _circulant_edges,
    _double_edge_swaps,
    _sample_link_latencies,
)

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"

F = 1.0 / 30.0
HOPS = 3
DELAYS = (4.0, 8.0)                 # blend mixing budgets studied in the N-scaling ladder
LINK_MEAN = 0.5                     # per-link geo mean (slots), matching the ladder configs
N_GRID = (1_000, 4_000, 16_000, 64_000, 250_000, 1_000_000)
DEGREES = (4, 6, 8)
N_SOURCES = 64                      # sampled Dijkstra sources per graph
REPS = {n: (3 if n <= 64_000 else 1) for n in N_GRID}


def probe_cell(n: int, degree: int, rep: int) -> dict:
    rng = np.random.default_rng(np.random.SeedSequence([n, degree, rep, 20260721]))
    cfg = SimConfig(n_nodes=min(n, 10_000), degree=degree, link_latency_mean=LINK_MEAN,
                    link_latency_dist="geo")   # only used for latency sampling params
    t0 = time.time()
    edges = _circulant_edges(n, degree)
    edges = _double_edge_swaps(edges, n_swaps=10 * len(edges), rng=rng)
    e = np.array(sorted(edges), dtype=np.int64)
    w = _sample_link_latencies(e.shape[0], cfg, rng)
    adj = csr_matrix(
        (np.concatenate([w, w]),
         (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))),
        shape=(n, n))
    sources = rng.choice(n, size=min(N_SOURCES, n), replace=False)
    dist = dijkstra(adj, directed=False, indices=sources)
    mask = np.isfinite(dist) & (dist > 0)
    d = dist[mask]
    row = dict(
        n=n, degree=degree, replicate=rep, n_sources=len(sources), n_edges=e.shape[0],
        l_mean=float(d.mean()), l_p50=float(np.percentile(d, 50)),
        l_p90=float(np.percentile(d, 90)), l_p99=float(np.percentile(d, 99)),
        l_max=float(d.max()), build_s=float(time.time() - t0),
    )
    for delay in DELAYS:
        dvis = HOPS * delay / 2.0 + (HOPS + 1) * row["l_mean"]
        row[f"d_vis_{delay:g}"] = dvis
        row[f"rho_{delay:g}"] = F * dvis
    print(f"n={n:>9,} deg={degree} rep={rep}: l_mean={row['l_mean']:.2f} "
          f"p99={row['l_p99']:.2f} rho(8)={row['rho_8']:.3f}  [{row['build_s']:.0f}s]",
          flush=True)
    return row


def main() -> None:
    cells = [(n, d, r) for n in N_GRID for d in DEGREES for r in range(REPS[n])]
    # large-N cells first so the slowest work starts immediately
    cells.sort(key=lambda c: -c[0])
    rows = Parallel(n_jobs=4, prefer="processes")(
        delayed(probe_cell)(n, d, r) for n, d, r in cells)
    df = pd.DataFrame(rows)
    out = RUNS / "topology_probe.parquet"
    df.to_parquet(out)
    print(f"wrote {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
