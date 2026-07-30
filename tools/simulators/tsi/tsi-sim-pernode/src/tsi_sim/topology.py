"""Network topology and per-node message-propagation latency.

A block produced by node ``p`` at slot ``t`` becomes usable at node ``j`` after the
shortest **weighted** path latency from ``p`` to ``j`` over the peering graph (gossip
flooding = fastest path). ``path_latency[p, j]`` (in slots) is precomputed once per
trajectory and is invariant across epochs and the stake estimate. Its *shape* is determined by
``(N, topology, degree, link-latency model)``, but the concrete random draw is seeded from the
config's full-key spawn hierarchy (see ``engine.run_trajectory``), so it also re-rolls with any
other ``config.key()`` field (``graph_seed`` is one contributor, not a standalone invariance knob).

Topologies:
- ``full_mesh``: every node one hop away with uniform latency ``L`` — reproduces the
  reduced model's ``FixedSlotLatency`` and is the validation baseline.
- ``regular``: a random d-regular peering graph (configurable ``degree``) with per-link
  latency drawn from ``link_latency_dist``; distant-in-network nodes see a producer's
  blocks later, which is the sole source of per-node view divergence.
- ``blend``: the **same** d-regular graph, but a block is first relayed through
  ``blend_hops`` random nodes (a mix cascade — each adds a ``Uniform(0, blend_delay_max)``
  mixing delay) before a final network-wide gossip makes it visible. Models routing over the
  Blend mixnet, where the dominant delay is the per-hop mixing, not the graph transport. The
  ``path_latency`` matrix is identical to ``regular``; only the arrival law differs
  (``arrival_column``).
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from . import constants
from .config import SimConfig
from .memguard import check_alloc


def _circulant_edges(n: int, degree: int) -> set[tuple[int, int]]:
    """A valid d-regular base graph (ring lattice); randomised later by edge swaps."""
    edges: set[tuple[int, int]] = set()
    half = degree // 2
    for i in range(n):
        for off in range(1, half + 1):
            j = (i + off) % n
            edges.add((min(i, j), max(i, j)))
    if degree % 2 == 1:  # odd degree needs n even: add the antipodal matching
        for i in range(n // 2):
            j = i + n // 2
            edges.add((min(i, j), max(i, j)))
    return edges


def _double_edge_swaps(edges: set[tuple[int, int]], n_swaps: int,
                       rng: np.random.Generator) -> set[tuple[int, int]]:
    """Randomise a graph while preserving every node's degree (Maslov–Sneppen swaps)."""
    elist = list(edges)
    eset = set(edges)
    for _ in range(n_swaps):
        i, j = rng.integers(0, len(elist), size=2)
        if i == j:
            continue
        a, b = elist[i]
        c, d = elist[j]
        if rng.random() < 0.5:
            c, d = d, c
        if len({a, b, c, d}) < 4:
            continue
        e1 = (min(a, c), max(a, c))
        e2 = (min(b, d), max(b, d))
        if e1 in eset or e2 in eset:
            continue
        eset.discard(elist[i])       # discard the stored (min-sorted) edges, not the
        eset.discard(elist[j])       # possibly-reoriented (c, d)
        eset.add(e1)
        eset.add(e2)
        elist[i] = e1
        elist[j] = e2
    return eset


def _sample_link_latencies(n_edges: int, config: SimConfig,
                           rng: np.random.Generator) -> np.ndarray:
    """Per-link one-way latency (slots) for every peering edge.

    All four modes have expected value ``link_latency_mean`` so it stays the single mean-latency
    control knob. ``geo`` reproduces the real-world geographic spread (short intra-region links,
    long inter-continental ones) by drawing each link from ``constants.GEO_LATENCY_BANDS_SLOTS``,
    then rescaling the fixed band shape so its mean matches ``link_latency_mean``.
    """
    mean = config.link_latency_mean
    if config.link_latency_dist == "fixed":
        return np.full(n_edges, mean, dtype=float)
    if config.link_latency_dist == "uniform":
        return rng.uniform(0.0, 2.0 * mean, size=n_edges)
    if config.link_latency_dist == "exp":
        return rng.exponential(mean, size=n_edges)
    if config.link_latency_dist == "geo":
        bands = np.asarray(constants.GEO_LATENCY_BANDS_SLOTS, dtype=float)
        weights = np.asarray(constants.GEO_LATENCY_WEIGHTS, dtype=float)
        idx = rng.choice(bands.shape[0], size=n_edges, p=weights)
        scale = mean / constants.GEO_LATENCY_MEAN_SLOTS   # rescale so E[latency] == mean
        return bands[idx] * scale
    raise ValueError(config.link_latency_dist)  # pragma: no cover


def build_path_latency(config: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Return ``path_latency[N, N]`` in **slots** (float, sub-slot capable); 0 on the diagonal.

    Latency is measured in slots and a slot is 1 second (``constants.SLOT_SECONDS``), so
    real-world inter-node latencies (tens to hundreds of milliseconds) are *fractions* of a
    slot. We keep the value as a float rather than rounding to whole slots so that realistic
    sub-second latencies are not discarded — a block whose fastest path is 0.3 slots (300 ms)
    is delivered mid-slot, not "0 slots" or "1 slot".
    """
    n = config.n_nodes
    # Guard BEFORE allocating: path_latency is a dense (N x N) float64, built here at the start of
    # each trajectory — BEFORE the arrival-matrix guard runs — and grows as N^2 independently of
    # n_blocks. The 2.2x covers the Dijkstra predecessor/scratch + finite-mask temporaries.
    check_alloc(int(2.2 * n * n * 8), f"path_latency (N={n} x N x 8B, +Dijkstra scratch)",
                f"N={n} makes the dense (N x N) latency matrix ~{n * n * 8 / 1024**3:.1f} GB. "
                f"Lower n_nodes or raise --mem-frac.")
    if config.topology == "full_mesh":
        pl = np.full((n, n), float(config.latency), dtype=np.float64)
        np.fill_diagonal(pl, 0.0)
        return pl

    # "regular" and "blend" share the same weighted d-regular graph; blend adds a mix cascade
    # on top of it in arrival_column, but the transport-latency matrix is identical.
    edges = _circulant_edges(n, config.degree)
    edges = _double_edge_swaps(edges, n_swaps=10 * len(edges), rng=rng)
    e = np.array(sorted(edges), dtype=np.int64)
    w = _sample_link_latencies(e.shape[0], config, rng)
    rows = np.concatenate([e[:, 0], e[:, 1]])
    cols = np.concatenate([e[:, 1], e[:, 0]])
    data = np.concatenate([w, w])
    adj = csr_matrix((data, (rows, cols)), shape=(n, n))
    dist = dijkstra(adj, directed=False)               # (N, N) float slots, inf if disconnected
    dist[~np.isfinite(dist)] = float(config.epoch_len)  # unreachable -> never arrives
    np.fill_diagonal(dist, 0.0)
    return dist


def _blend_arrival_column(
    path_latency: np.ndarray, producer: int, slot: int, config: SimConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sub-slot arrival of a block via the Blend mix cascade (``topology == "blend"``).

    The producer picks ``blend_hops`` DISTINCT relay nodes uniformly at random. The block hops
    ``producer -> r1 -> ... -> r_hops`` over the shortest weighted path, and each relay waits a
    ``Uniform(0, blend_delay_max)`` mixing delay before forwarding. The last relay's forward is
    the final network-wide gossip that makes the block visible. Relays are blind forwarders, so
    every node — relays included — first learns the block from that final gossip; only the
    producer knows it earlier (handled by the caller).
    """
    n = path_latency.shape[0]
    hops = int(config.blend_hops)
    delay_max = float(config.blend_delay_max)
    pool = np.delete(np.arange(n), producer)               # distinct relays, never the producer
    relays = rng.choice(pool, size=hops, replace=False)
    t = float(slot)
    src = int(producer)
    for r in relays.tolist():                     # transport leg, then this relay's mix delay
        t += float(path_latency[src, r])
        t += float(rng.uniform(0.0, delay_max))
        src = r
    last = int(relays[-1])
    return t + path_latency[last].astype(np.float64)       # final gossip floods from the last relay


def arrival_column(
    path_latency: np.ndarray, producer: int, slot: int, config: SimConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sub-slot arrival time of a block at every node (before the parent clamp)."""
    if config.topology == "blend":
        col = _blend_arrival_column(path_latency, producer, slot, config, rng)
    else:
        col = float(slot) + path_latency[producer].astype(np.float64)
    if config.jitter_mean > 0.0:
        if config.jitter_dist == "poisson":
            # Long-tail model: a `jitter_frac` fraction of deliveries straggle by a
            # Poisson(jitter_mean) whole-slot delay; the rest arrive on time.
            extra = rng.poisson(config.jitter_mean, size=col.shape).astype(np.float64)
            if config.jitter_frac < 1.0:
                extra = extra * (rng.random(col.shape) < config.jitter_frac)
            col = col + extra
        else:
            col = col + rng.exponential(config.jitter_mean, size=col.shape)
    col[producer] = float(slot)                        # producer sees own block instantly
    return col
