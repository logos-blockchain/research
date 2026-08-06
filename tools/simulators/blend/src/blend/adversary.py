"""Adversary observation + eclipse metrics (exact, O(N*degree)) and placement strategies.

- ``adversary_metrics``: given a boolean adversary mask, count the honest nodes peered with >=1
  adversary (**observed**) and the honest nodes whose EVERY peer is adversarial (**eclipsed**),
  via one sparse reduction over the CSR. Exact at every N (incl. 1e6).
- ``place_adversary``: pick the adversary set. ``random`` (average case) scales to 1e6; the
  worst-case greedy strategies (``worstcase_coverage``/``worstcase_eclipse``) characterize the
  security *envelope* and are meant for N <= ``worstcase_max_n``. ``worstcase_degree`` is
  degenerate on a strict d-regular graph (all degrees equal) and coincides with ``random``.
"""

from __future__ import annotations

import heapq

import numpy as np

from .config import WORSTCASE_MODES
from .graph import Graph


def adversary_metrics(graph: Graph, adv_mask: np.ndarray) -> dict:
    """Exact observation/eclipse counts for the given adversary mask."""
    adv = adv_mask
    honest = ~adv
    counts = np.add.reduceat(adv[graph.indices].astype(np.int32), graph.indptr[:-1])
    observed = honest & (counts >= 1)
    eclipsed = honest & (counts == graph.degree)
    n_adv = int(adv.sum())
    n_honest = int(honest.sum())
    obs = int(observed.sum())
    ecl = int(eclipsed.sum())
    return {
        "n_adv": n_adv,
        "n_honest": n_honest,
        "observed_count": obs,
        "observed_frac": float(obs / n_honest) if n_honest else 0.0,
        "eclipsed_count": ecl,
        "eclipsed_frac": float(ecl / n_honest) if n_honest else 0.0,
        "mean_adv_peers_honest": float(counts[honest].mean()) if n_honest else 0.0,
        "max_adv_peers": int(counts.max()) if graph.n else 0,
    }


def deanon_metrics(n: int, n_adv: int, observed_frac: float, blend_hops: int,
                   redundancy: int = 1) -> dict:
    """Exact deanonymization rates for an honest sender whose message traverses ``blend_hops``
    relays chosen uniformly *blind to who is adversarial* (the sender cannot know who is honest).

    With messaging **redundancy** ``R``, each emission is sent over ``R`` independent blend cascades
    and is captured if **any** cascade's whole path is adversarial, so the single-cascade
    hypergeometric ``d1`` becomes ``1 - (1 - d1)**R``. ``R = 1`` is the plain single-cascade case.

    * ``deanon_rate`` — P(some cascade has **every** relay adversarial): the adversary then controls
      a whole cascade and links the message from entry to exit. The single-cascade term is the
      hypergeometric ``d1 = C(n_adv, k) / C(n-1, k)`` (an honest sender leaves all ``n_adv``
      adversaries in the ``n-1``-node relay pool) — it depends only on the adversary *count*, not
      the placement, and ``d1 ~ f_adv**blend_hops``.
    * ``full_deanon_rate`` — additionally the honest sender is directly peered with >=1 adversary,
      so the adversary also ties the message to its originator: ``deanon_rate * observed_frac``.
      ``observed_frac`` (the honest-node fraction with an adversary peer) is placement-dependent, so
      full deanonymization carries the placement's fingerprint (worst-case coverage drives it up).

    Both are exact at every N -- no Monte-Carlo -- matching the other adversary metrics.
    """
    k, R = int(blend_hops), int(redundancy)
    d1 = 0.0
    if 1 <= k <= n_adv and k <= n - 1:
        d1 = 1.0
        for i in range(k):
            d1 *= (n_adv - i) / (n - 1 - i)   # C(n_adv,k)/C(n-1,k), stable for small k
    deanon = 1.0 - (1.0 - d1) ** R            # any of R independent cascades whole-path-adversarial
    return {"deanon_rate": float(deanon), "full_deanon_rate": float(deanon * observed_frac)}


def attribution_confidence(adv_peers: np.ndarray | int, degree: int) -> np.ndarray | float:
    """How sure the adversary is that a node it saw transmitting is the message's **originator**.

    Capturing the whole cascade tells the adversary which message it is following, not who started
    it. Seeing an honest node ``X`` transmit is consistent with two stories: ``X`` originated the
    message, or ``X`` received it from a peer and passed it on. The adversary separates them by
    *not* having seen the message arrive at ``X`` -- certain if ``X`` originated it, but of
    probability ``1 - a/d`` if ``X`` relayed, since the delivering peer may simply have been one it
    cannot watch. With equal priors that gives

        confidence = 1 / (2 - a/d) = d / (2d - a)

    for ``a`` adversarial peers out of degree ``d``. The relays do not enter: the conditioning event
    already fixes them as adversarial, so an honest ``X`` cannot be one of them for this message.

    Note the ends: ``a = d`` (every link watched) gives certainty, and ``a = 0`` returns the 0.5
    prior -- though such a node is never observed transmitting at all, so callers should treat it as
    unattributable rather than as a coin flip.

    This is a **lower bound on the adversary's capability**: it credits only the sender's own links.
    An honest peer that has adversarial peers of its own also leaks the message upstream, so real
    confidence is higher (see the report's caveat on neighbourhood observability).
    """
    a = np.asarray(adv_peers, dtype=float)
    return degree / (2.0 * degree - a)


def attribution_metrics(graph: Graph, adv_mask: np.ndarray,
                        thresholds: tuple[float, ...] = (0.5, 0.9, 0.99)) -> dict:
    """Distribution of :func:`attribution_confidence` over the honest nodes of this placement.

    ``attributable_frac_<t>`` is the share of honest nodes the adversary could name as originator
    with confidence at least ``t`` -- the factor that should multiply the whole-path capture rate,
    in place of the binary "has at least one adversarial peer".
    """
    adv = adv_mask
    honest = ~adv
    n_honest = int(honest.sum())
    counts = np.add.reduceat(adv[graph.indices].astype(np.int32), graph.indptr[:-1])
    if n_honest == 0:
        out = {"attribution_conf_mean": 0.0}
        for t in thresholds:
            out[f"attributable_frac_{int(t * 100)}"] = 0.0
        return out
    a_honest = counts[honest]
    conf = attribution_confidence(a_honest, graph.degree)
    seen = a_honest >= 1                      # never observed transmitting without a watched link
    out = {"attribution_conf_mean": float(np.mean(np.where(seen, conf, 0.0)))}
    for t in thresholds:
        out[f"attributable_frac_{int(t * 100)}"] = float(np.mean(seen & (conf >= t - 1e-12)))
    return out


def _peers(graph: Graph, v: int) -> np.ndarray:
    return graph.indices[graph.indptr[v]:graph.indptr[v + 1]]


def _greedy_coverage(graph: Graph, n_adv: int, rng: np.random.Generator) -> np.ndarray:
    """Lazy-greedy (CELF) maximum-coverage: pick adversaries covering the most honest neighbours."""
    n, degree = graph.n, graph.degree
    adv = np.zeros(n, dtype=bool)
    covered = np.zeros(n, dtype=bool)

    def gain(v: int) -> int:
        pu = _peers(graph, v)
        return int(np.count_nonzero(~adv[pu] & ~covered[pu]))

    heap = [(-degree, int(v)) for v in range(n)]
    heapq.heapify(heap)
    chosen: list[int] = []
    while len(chosen) < n_adv and heap:
        neg, v = heapq.heappop(heap)
        if adv[v]:
            continue
        g = gain(v)
        if -neg != g:
            heapq.heappush(heap, (-g, v))
            continue
        adv[v] = True
        chosen.append(v)
        pu = _peers(graph, v)
        covered[pu[~adv[pu] & ~covered[pu]]] = True
    return np.asarray(chosen, dtype=np.int64)


def _greedy_eclipse(graph: Graph, n_adv: int, rng: np.random.Generator) -> np.ndarray:
    """Greedy fully-surround: repeatedly finish the honest node closest to eclipse.

    Heuristic (eclipse maximization is NP-hard) — an upper-envelope, not exact.
    """
    n, degree = graph.n, graph.degree
    adv = np.zeros(n, dtype=bool)
    remaining = np.full(n, degree, dtype=np.int64)   # honest node's peers not yet adversary
    budget = int(n_adv)
    heap = [(degree, int(u)) for u in range(n)]
    heapq.heapify(heap)
    while budget > 0 and heap:
        rem_u, u = heapq.heappop(heap)
        if adv[u]:
            continue
        cur = int(remaining[u])
        if cur != rem_u:
            heapq.heappush(heap, (cur, u))
            continue
        if cur == 0:
            continue
        pu = _peers(graph, u)
        tozap = pu[~adv[pu]]
        if tozap.shape[0] > budget:
            tozap = tozap[:budget]
        for z in tozap.tolist():
            if adv[z]:
                continue
            adv[z] = True
            budget -= 1
            remaining[_peers(graph, z)] -= 1
    return np.where(adv)[0]


def place_adversary(graph: Graph, f_adv: float, mode: str, rng: np.random.Generator,
                    worstcase_max_n: int) -> np.ndarray:
    """Return a boolean adversary mask of size ``graph.n``."""
    n = graph.n
    n_adv = int(round(f_adv * n))
    mask = np.zeros(n, dtype=bool)
    if n_adv <= 0:
        return mask
    if n_adv >= n:
        mask[:] = True
        return mask
    if mode in ("random", "worstcase_degree"):
        # d-regular: all degrees equal, so degree-ranked == uniform-random.
        mask[rng.choice(n, size=n_adv, replace=False)] = True
        return mask
    if mode not in WORSTCASE_MODES:
        raise ValueError(f"unknown adversary_mode {mode!r}")
    if n > worstcase_max_n:
        raise ValueError(
            f"worst-case mode {mode!r} at N={n} exceeds worstcase_max_n={worstcase_max_n}; "
            f"run worst-case only at smaller N (the engine skips it above the cap).")
    if mode == "worstcase_coverage":
        mask[_greedy_coverage(graph, n_adv, rng)] = True
    else:  # worstcase_eclipse
        mask[_greedy_eclipse(graph, n_adv, rng)] = True
    return mask
