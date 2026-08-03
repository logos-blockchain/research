"""Deterministic random d-regular peer graph as a sparse CSR, scalable to 1e6 nodes.

Construction: a **union of `degree` random perfect matchings** (fully vectorized), repaired to
drop the few parallel edges (expected count ~ C(degree,2), independent of N) so the result is
EXACTLY d-regular, simple, undirected — and reconstructible from one global seed. Preferred over
the tsi ring-lattice + Maslov-Sneppen generator: O(N*degree) (~seconds at 1e6 vs minutes of
Python swaps) and genuinely low-diameter immediately.

The ``Graph`` holds the undirected CSR adjacency (``indptr``/``indices`` — drives the exact
adversary reductions) plus the directed per-edge base latency (``base``) and source node
(``src``), and the per-node processing lags (``p``), which drive the per-round directed Dijkstra
in ``propagation.py``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix

from . import latency
from .config import SimConfig
from .memguard import check_alloc
from .rng import graph_seedseq


@dataclass(frozen=True)
class Graph:
    n: int
    degree: int
    indptr: np.ndarray      # (n+1,)  CSR row pointers (contiguous degree-length blocks)
    indices: np.ndarray     # (2E,)   peers of each node, grouped by source; 2E = n*degree
    base: np.ndarray        # (2E,)   geo base latency (ms) per directed edge, CSR-aligned
    src: np.ndarray         # (2E,)   source node per directed edge, CSR-aligned
    p: np.ndarray           # (n,)    per-node processing lag (ms)

    @property
    def n_edges(self) -> int:
        return int(self.indices.shape[0] // 2)

    def weighted_csr(self, data: np.ndarray) -> csr_matrix:
        """A directed CSR sharing this graph's sparsity, with the given per-edge ``data``."""
        return csr_matrix((data, self.indices, self.indptr), shape=(self.n, self.n))


def build_regular_edges(n: int, degree: int, rng: np.random.Generator) -> np.ndarray:
    """Exactly d-regular simple undirected edge list, shape (E, 2) with u < v.

    Requires ``n`` even and ``1 <= degree < n``. Deterministic in ``rng``.
    """
    if n % 2 != 0:
        raise ValueError("n must be even")
    if not (1 <= degree < n):
        raise ValueError("need 1 <= degree < n")
    h = n // 2
    lo = np.empty(degree * h, dtype=np.int64)
    hi = np.empty(degree * h, dtype=np.int64)
    for m in range(degree):
        perm = rng.permutation(n)
        a, b = perm[0::2], perm[1::2]
        lo[m * h:(m + 1) * h] = np.minimum(a, b)
        hi[m * h:(m + 1) * h] = np.maximum(a, b)
    # drop parallel edges (keep first occurrence of each undirected pair)
    key = lo * n + hi
    order = np.argsort(key, kind="stable")
    ks = key[order]
    first = np.ones(ks.shape[0], dtype=bool)
    first[1:] = ks[1:] != ks[:-1]
    edges = np.stack([lo[order][first], hi[order][first]], axis=1)
    deg = np.bincount(edges.ravel(), minlength=n)
    if np.all(deg == degree):
        return edges
    return _repair_to_regular(edges, deg, n, degree, rng)


def _repair_to_regular(edges_arr: np.ndarray, deg: np.ndarray, n: int, degree: int,
                       rng: np.random.Generator, max_passes: int = 100_000) -> np.ndarray:
    """Restore exact d-regularity after dedup dropped a few parallel edges.

    Re-pairs the freed stubs (a tiny set, size ~ 2*C(degree,2)) into new simple edges, using a
    single Maslov-Sneppen swap against a full-degree edge whenever a pass makes no progress.
    """
    deficient = np.where(deg < degree)[0]
    defset = set(int(x) for x in deficient)
    nbr: dict[int, set[int]] = defaultdict(set)
    mask = np.isin(edges_arr[:, 0], deficient) | np.isin(edges_arr[:, 1], deficient)
    for a, b in edges_arr[mask].tolist():
        if a in defset:
            nbr[a].add(b)
        if b in defset:
            nbr[b].add(a)
    edges: list[list[int]] = edges_arr.tolist()
    deg = deg.astype(np.int64).copy()

    def _swap_connect(x: int, y: int) -> bool:
        for _ in range(500):
            idx = int(rng.integers(0, len(edges)))
            a, b = edges[idx]
            if deg[a] != degree or deg[b] != degree:   # only rewire full-degree edges
                continue
            if a in (x, y) or b in (x, y):
                continue
            if a in nbr[x] or b in nbr[y]:
                continue
            # remove (a,b); add (x,a) and (y,b) -> x,y gain a peer; a,b unchanged
            if a in defset:
                nbr[a].discard(b)
                nbr[a].add(x)
            if b in defset:
                nbr[b].discard(a)
                nbr[b].add(y)
            edges[idx] = [min(x, a), max(x, a)]
            edges.append([min(y, b), max(y, b)])
            nbr[x].add(a)
            nbr[y].add(b)
            deg[x] += 1
            deg[y] += 1
            return True
        return False

    for _ in range(max_passes):
        stubs: list[int] = []
        for node in defset:
            stubs.extend([node] * int(degree - deg[node]))
        if not stubs:
            break
        rng.shuffle(stubs)
        progressed = False
        leftover: list[int] = []
        i = 0
        while i < len(stubs) - 1:
            x, y = int(stubs[i]), int(stubs[i + 1])
            i += 2
            if x != y and y not in nbr[x]:
                edges.append([min(x, y), max(x, y)])
                nbr[x].add(y)
                nbr[y].add(x)
                deg[x] += 1
                deg[y] += 1
                progressed = True
            else:
                leftover.extend([x, y])
        if i == len(stubs) - 1:
            leftover.append(int(stubs[-1]))
        if not progressed and leftover:
            x = leftover[0]
            y = leftover[1] if len(leftover) > 1 else leftover[0]
            if not _swap_connect(x, y):
                raise RuntimeError("graph repair swap failed")

    out = np.asarray(edges, dtype=np.int64)
    if not np.all(np.bincount(out.ravel(), minlength=n) == degree):
        raise RuntimeError("graph repair failed to reach exact d-regularity")
    return out


def build_graph(config: SimConfig) -> Graph:
    """Build the exact d-regular peer graph + directed base/src arrays + per-node lags.

    Everything is a pure function of ``graph_seedseq(config)`` (topology fields only).
    """
    n, degree = config.n_nodes, config.degree
    check_alloc(int(n * degree * 24), "d-regular CSR (indices+base+src)",
                f"N={n}, degree={degree}")
    rng = np.random.default_rng(graph_seedseq(config))
    edges = build_regular_edges(n, degree, rng)
    base_u = latency.sample_link_latencies(edges.shape[0], config, rng)
    p = latency.assign_processing_lags(n, config, rng)
    rows = np.concatenate([edges[:, 0], edges[:, 1]])
    cols = np.concatenate([edges[:, 1], edges[:, 0]])
    data = np.concatenate([base_u, base_u])
    csr = csr_matrix((data, (rows, cols)), shape=(n, n))
    csr.sort_indices()
    indptr = csr.indptr.astype(np.int64)
    src = np.repeat(np.arange(n, dtype=np.int64), np.diff(indptr))
    return Graph(n=n, degree=degree, indptr=indptr, indices=csr.indices,
                 base=csr.data, src=src, p=p)
