"""Blend-cascade propagation: per-round delivery success and full delay (ms), aggregated.

One round: a (responsive) sender injects a message that must traverse a **blend path** of
``blend_hops`` relays chosen *blind to responsiveness* (the path is drawn from the consensus node
list, not from who happens to be up) -> the last relay floods the whole network. Transport legs are
directed shortest paths with edge weights ``base + Exp(jitter) + p(relaying node)`` (ms); each relay
adds a free-running-clock mixing wait (``mixclock.mix_wait``). Full delay = sum of transport legs +
sum of mixing waits + the final broadcast delay. Only the ``blend_hops`` relays mix; the final flood
is plain.

**Unresponsive nodes** (a configurable ``unresponsive_frac`` of the population) relay nothing: their
outgoing edges are removed (weight -> inf), so nothing routes *through* them, though they can still
*receive* (be reached as a leaf). Two consequences, both measured:

* **message success-delivery-rate** (``delivery_rate``) — the fraction of rounds whose message is
  delivered through the whole cascade to a **responsive** final relay that then floods. If any relay
  on the drawn path is unresponsive the message dies there, so the rate falls ~
  ``(1-f)^blend_hops``; a shorter path or a higher degree that keeps legs routable raises it.
* **coverage** (``frac_reached``, ``coverN_ms``) of a delivered flood, which degrades as routing
  holes strand pockets of the network.

Delay statistics are conditioned on delivery; ``delivery_rate`` is over all rounds.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse.csgraph import dijkstra

from .config import SimConfig
from .graph import Graph
from .memguard import check_alloc
from .mixclock import mix_wait


def assign_responsive(n: int, unresponsive_frac: float, rng: np.random.Generator) -> np.ndarray:
    """Boolean mask (True == responsive/relaying). A random ``unresponsive_frac`` are set False."""
    responsive = np.ones(n, dtype=bool)
    n_unresp = int(round(unresponsive_frac * n))
    if n_unresp > 0:
        responsive[rng.choice(n, size=n_unresp, replace=False)] = False
    return responsive


def blend_round(graph: Graph, sender: int, relays: np.ndarray, jitter_mean_ms: float,
                max_blend_delay: int, rng: np.random.Generator,
                coverage_pcts: tuple[float, ...], responsive: np.ndarray | None = None) -> dict:
    """One Blend cascade. ``delivered`` is True iff every relay forwards and the final relay (which
    must be responsive) floods; delay fields are NaN on a dropped message."""
    data = (graph.base
            + rng.exponential(jitter_mean_ms, size=graph.base.shape[0])
            + graph.p[graph.src])
    if responsive is not None:
        data[~responsive[graph.src]] = np.inf   # unresponsive nodes relay nothing (no out-edges)
    csr = graph.weighted_csr(data)
    k = int(relays.shape[0])
    sources = np.empty(k + 1, dtype=np.int64)
    sources[0] = sender
    sources[1:] = relays
    dist = dijkstra(csr, directed=True, indices=sources)   # (k+1, n)

    # legs s->r1->...->rk. A leg from an unresponsive relay is inf (no outgoing edges), so legs_ok
    # already encodes "every intermediate relay forwarded"; the final relay is checked below.
    legs = 0.0
    legs_ok = True
    for i in range(k):
        d = dist[i, relays[i]]
        if not np.isfinite(d):
            legs_ok = False
            break
        legs += float(d)
    mix_total = float(mix_wait(rng, max_blend_delay, k).sum())

    final_relay = int(sources[k])
    final_ok = responsive is None or bool(responsive[final_relay])

    flood = dist[k]
    finite = np.isfinite(flood)
    delivered = legs_ok and final_ok and bool(finite.any())
    if delivered:
        reached = flood[finite]
        broadcast = float(reached.max())
        covers = [float(np.percentile(reached, pc)) for pc in coverage_pcts]
        frac_reached = float(finite.mean())
        path = legs + mix_total
        full = path + broadcast
    else:
        broadcast = float("nan")
        covers = [float("nan")] * len(coverage_pcts)
        frac_reached = 0.0
        path = float("nan")
        full = float("nan")
    return {"full": full, "path": path, "broadcast": broadcast, "covers": covers,
            "frac_reached": frac_reached, "delivered": delivered}


def propagation_metrics(graph: Graph, blend_hops: int, max_blend_delay: int,
                        unresponsive_frac: float, responsive: np.ndarray,
                        config: SimConfig, rng: np.random.Generator) -> dict:
    """Aggregate the Blend cascade over ``config.n_rounds`` rounds.

    Each round a responsive node injects a message and the ``blend_hops`` relays are drawn from the
    whole node list (blind to responsiveness). ``delivery_rate`` is the fraction that complete the
    cascade; delay/coverage statistics are conditioned on those delivered rounds.
    """
    n = graph.n
    check_alloc(int((blend_hops + 1) * n * 8), "sampled (blend_hops+1) x N distance matrix",
                f"N={n}, blend_hops={blend_hops}")
    pcts = tuple(config.coverage_pcts)
    resp_ids = np.where(responsive)[0]

    def _empty() -> dict:
        out = {name: float("nan") for name in
               ("full_delay_ms_mean", "full_delay_ms_p50", "full_delay_ms_p90",
                "full_delay_ms_p99", "path_delay_ms_mean", "broadcast_delay_ms_mean")}
        out["frac_reached"] = 0.0
        out["delivery_rate"] = 0.0
        for pc in pcts:
            out[f"cover{int(pc)}_ms"] = float("nan")
        return out

    if resp_ids.shape[0] < 1 or n < blend_hops + 1:
        return _empty()   # no responsive sender, or too few nodes to draw a distinct path

    fulls, paths, bcasts, fracs = [], [], [], []
    covers = [[] for _ in pcts]
    delivered = 0
    for _ in range(config.n_rounds):
        sender = int(rng.choice(resp_ids))
        relays = rng.choice(n - 1, size=blend_hops, replace=False)
        relays[relays >= sender] += 1          # blend_hops distinct nodes, all != sender
        r = blend_round(graph, sender, relays, config.transport_jitter_mean_ms,
                        max_blend_delay, rng, pcts, responsive)
        if not r["delivered"]:
            continue
        delivered += 1
        fulls.append(r["full"])
        paths.append(r["path"])
        bcasts.append(r["broadcast"])
        fracs.append(r["frac_reached"])
        for j, c in enumerate(r["covers"]):
            covers[j].append(c)

    delivery_rate = delivered / config.n_rounds
    if delivered == 0:
        out = _empty()
        out["delivery_rate"] = delivery_rate
        return out

    fulls = np.asarray(fulls)
    out = {
        "full_delay_ms_mean": float(np.mean(fulls)),
        "full_delay_ms_p50": float(np.percentile(fulls, 50)),
        "full_delay_ms_p90": float(np.percentile(fulls, 90)),
        "full_delay_ms_p99": float(np.percentile(fulls, 99)),
        "path_delay_ms_mean": float(np.mean(paths)),
        "broadcast_delay_ms_mean": float(np.mean(bcasts)),
        "frac_reached": float(np.mean(fracs)),
        "delivery_rate": delivery_rate,
    }
    for pc, col in zip(pcts, covers, strict=True):
        out[f"cover{int(pc)}_ms"] = float(np.mean(col))
    return out
