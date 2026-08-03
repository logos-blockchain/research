"""Network-latency constants for pd. All delays are in **milliseconds**.

One-way, application-level latency between two directly-peered nodes, bucketed by the
geographic relationship of the peers (~ RTT/2 from public latency measurements plus a little
gossip processing overhead). In a globally distributed node set a random peer is usually on
another continent, so most peer links fall in the long-latency bands. A message gossip-floods
over the peering graph, so its delay to a far node is the sum of a few such per-link latencies
along the fastest (Dijkstra) path — see graph.py / propagation.py.
"""

from __future__ import annotations

GEO_LATENCY_BANDS_MS = (
    15.0,    # metro / same country            (~15 ms one-way)
    40.0,    # same continent, e.g. EU<->EU    (~40 ms)
    90.0,    # transatlantic, e.g. EU<->US-East (~90 ms)
    200.0,   # antipodal, e.g. EU<->AU / EU<->JP (~200 ms)
)
# Share of random peer links falling in each band for a globally distributed node set.
GEO_LATENCY_WEIGHTS = (0.15, 0.35, 0.35, 0.15)
# Mean one-way latency of a random global peer link under the mixture above (~78.75 ms).
GEO_LATENCY_MEAN_MS = sum(
    b * w for b, w in zip(GEO_LATENCY_BANDS_MS, GEO_LATENCY_WEIGHTS, strict=True)
)
