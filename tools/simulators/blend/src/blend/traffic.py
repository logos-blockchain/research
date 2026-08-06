"""Cover traffic on a timeline: blending, mixing, and what the network sees between blocks.

The rest of the simulator samples *independent* rounds, drawing each relay's hold from
``mixclock.mix_wait`` -- the stationary residual to that relay's next release. That is exact for one
message meeting an independent clock, but it has no notion of time, so two messages can never meet
at the same relay. Everything this module measures is defined by them meeting, so here each node
owns **one free-running clock** shared by every message that passes through it, and messages are
played out on a real timeline.

Two quantities, easy to confuse:

* **mixing** -- how many messages a relay is *holding* at once. A relay holds a message from its
  arrival until that relay's next tick.
* **blending** -- how many messages a relay has *seen* between two consecutive releases. Every
  broadcast reaches every node, so a relay sees the whole network's broadcast stream; an observer
  watching it release cannot tell which of those it forwarded. This, not the held count, is the
  anonymity set, and it grows with the broadcast rate and with the release interval:
  ``blending ~ rate * interval`` where the interval of a ``Uniform{0..M}`` clock averages ``M/2``.

Emissions are the union of cover traffic and block proposals. Each node emits at rate
``cover_rate_mult / n_nodes`` per slot; winning the block lottery consumes the next scheduled cover,
so every node emits the same number of times whether or not it produces blocks (see ``quota`` for
the stake ceiling that keeps that true). Cover and block messages travel the same cascade over
independently drawn paths, and both end in a broadcast, so they are indistinguishable in transit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.sparse.csgraph import dijkstra

from .config import SimConfig
from .graph import Graph
from .mixclock import mean_residual_ms, mix_wait


class ReleaseClock:
    """One node's free-running release clock: ticks separated by ``Uniform{0..M}`` whole seconds.

    The first tick is the stationary residual from t=0, so a clock sampled once reproduces
    ``mixclock.mix_wait``. Ticks are extended lazily, which keeps a million-node network cheap --
    only the relays a message actually visits ever grow a clock.
    """

    __slots__ = ("_lo", "_m", "_rng", "_ticks")

    def __init__(self, max_blend_delay: int, rng: np.random.Generator,
                 min_blend_delay: int = 0) -> None:
        self._m = int(max_blend_delay)
        self._lo = max(int(min_blend_delay), 0)
        self._rng = rng
        first = 0.0 if self._m <= 0 else float(mix_wait(rng, self._m, 1, self._lo)[0]) / 1000.0
        self._ticks: list[float] = [first]

    def next_tick_at_or_after(self, t: float) -> float:
        """Time of this clock's first tick at or after ``t`` (``t`` itself when M = 0)."""
        if self._m <= 0:
            return t
        while self._ticks[-1] < t:
            step = float(self._rng.integers(self._lo, self._m + 1))
            self._ticks.append(self._ticks[-1] + step)
        for tick in self._ticks:                 # tick lists stay short (window / mean interval)
            if tick >= t:
                return tick
        return self._ticks[-1]

    def ticks_in(self, lo: float, hi: float) -> list[float]:
        """Ticks in ``(lo, hi]`` -- the release opportunities used to bracket blending."""
        self.next_tick_at_or_after(hi)
        return [t for t in self._ticks if lo < t <= hi]


@dataclass
class Hold:
    """One message waiting at one relay."""
    node: int
    arrived: float
    released: float


@dataclass
class TrafficWindow:
    """Raw event record of a simulated window; :func:`traffic_metrics` reduces it."""
    emitted_cover: int = 0
    emitted_block: int = 0
    cancelled_cover: int = 0
    broadcasts: list[float] = field(default_factory=list)       # when each message floods
    holds: list[Hold] = field(default_factory=list)
    window_seconds: float = 0.0
    block_slots: list[float] = field(default_factory=list)      # when blocks were proposed
    cover_slots: list[float] = field(default_factory=list)      # when cover was emitted
    clocks: dict[int, ReleaseClock] = field(default_factory=dict)


def _clock(clocks: dict[int, ReleaseClock], node: int, max_blend_delay: int,
           rng: np.random.Generator, min_blend_delay: int = 0) -> ReleaseClock:
    c = clocks.get(node)
    if c is None:
        c = ReleaseClock(max_blend_delay, rng, min_blend_delay)
        clocks[node] = c
    return c


def simulate_window(graph: Graph, config: SimConfig, rng: np.random.Generator,
                    window_slots: int, max_blend_delay: int | None = None,
                    blend_hops: int | None = None, release_mode: str | None = None,
                    min_blend_delay: int | None = None) -> TrafficWindow:
    """Play ``window_slots`` seconds of network traffic and record every hold and broadcast.

    Each slot, the network emits once per ``cover_rate_mult`` on average -- the emitter is uniform
    because every node carries the same per-slot rate. A block proposal is drawn at the network
    block rate and, per the quota rule, cancels that node's next cover emission.
    """
    n = graph.n
    k = int(config.blend_hops if blend_hops is None else blend_hops)
    m = int(config.max_blend_delay if max_blend_delay is None else max_blend_delay)
    lo = int(config.min_blend_delay if min_blend_delay is None else min_blend_delay)
    mode = release_mode or config.release_mode
    # Matched delay budget: exponential jitter with the same mean hold as the clock, so the two
    # designs are compared at equal latency cost and differ only in HOW they delay.
    jitter_mean_s = mean_residual_ms(m, lo) / 1000.0
    f = 1.0 / config.block_interval_slots
    win = TrafficWindow(window_seconds=float(window_slots))
    clocks = win.clocks
    cancelled: set[int] = set()          # nodes owing a cancelled cover after a block proposal

    for slot in range(window_slots):
        t0 = float(slot)
        n_emissions = rng.poisson(config.cover_rate_mult)      # network-wide emissions this slot
        block_this_slot = rng.random() < f
        senders = rng.integers(0, n, size=n_emissions).tolist() if n_emissions else []
        if block_this_slot:
            senders.append(int(rng.integers(0, n)))            # the proposer also emits
        for i, sender in enumerate(senders):
            is_block = block_this_slot and i == len(senders) - 1
            if not is_block and sender in cancelled:
                cancelled.discard(sender)                      # this cover is the one forfeited
                win.cancelled_cover += 1
                continue
            if is_block:
                cancelled.add(sender)
                win.emitted_block += 1
                win.block_slots.append(t0)
            else:
                win.emitted_cover += 1
                win.cover_slots.append(t0)
            relays = rng.choice(n - 1, size=k, replace=False)
            relays[relays >= sender] += 1
            sources = np.empty(k + 1, dtype=np.int64)
            sources[0] = sender
            sources[1:] = relays
            data = (graph.base + rng.exponential(config.transport_jitter_mean_ms,
                                                 size=graph.base.shape[0]) + graph.p[graph.src])
            dist = dijkstra(graph.weighted_csr(data), directed=True, indices=sources)
            t = t0
            dropped = False
            for hop in range(k):
                leg = dist[hop, relays[hop]]
                if not np.isfinite(leg):
                    dropped = True
                    break
                arrived = t + float(leg) / 1000.0
                if mode == "jitter":
                    # each message waits its own independent draw -- no batching, no quantisation
                    released = arrived + float(rng.exponential(jitter_mean_s)) if m > 0 else arrived
                else:
                    released = _clock(clocks, int(relays[hop]), m, rng,
                                      lo).next_tick_at_or_after(arrived)
                win.holds.append(Hold(int(relays[hop]), arrived, released))
                t = released
            if not dropped:
                win.broadcasts.append(t)                       # the final relay floods at t
    return win


def traffic_metrics(win: TrafficWindow, config: SimConfig,
                    max_blend_delay: int | None = None) -> dict:
    """Reduce a window to the reported quantities.

    ``blending`` is evaluated per release: every broadcast in the network is seen by every node, so
    the anonymity set of a release at time ``T`` is the number of broadcasts since that relay's
    previous release.
    """
    m = int(config.max_blend_delay if max_blend_delay is None else max_blend_delay)
    # cover emitted between consecutive block proposals, measured gap by gap
    if len(win.block_slots) >= 2:
        cover = np.sort(np.asarray(win.cover_slots))
        blocks = np.sort(np.asarray(win.block_slots))
        gaps = np.diff(np.searchsorted(cover, blocks, "right")).astype(float)
        per_block = float(gaps.mean())
    else:
        per_block = float("nan")
    out = {
        "emitted_cover": win.emitted_cover,
        "emitted_block": win.emitted_block,
        "cancelled_cover": win.cancelled_cover,
        "broadcasts_seen": len(win.broadcasts),
        "cover_per_block_interval": per_block,
        "hold_events": len(win.holds),
    }
    if not win.holds:
        out.update(hold_seconds_mean=float("nan"), delayed_frac=0.0,
                   queue_mean=0.0, queue_p90=0.0, queue_max=0.0,
                   blending_mean=float("nan"), blending_p50=float("nan"),
                   blending_p90=float("nan"), blending_max=float("nan"))
        return out
    hold_s = np.array([h.released - h.arrived for h in win.holds])
    out["hold_seconds_mean"] = float(hold_s.mean())
    out["delayed_frac"] = float(np.mean(hold_s > 0.0))

    # mixing: concurrent holds at a relay, time-weighted over the window
    by_node: dict[int, list[Hold]] = {}
    for h in win.holds:
        by_node.setdefault(h.node, []).append(h)
    occupancy, peaks = [], []
    for holds in by_node.values():
        events = sorted([(h.arrived, 1) for h in holds] + [(h.released, -1) for h in holds])
        cur = peak = 0
        area = 0.0
        prev = events[0][0]
        for tstamp, delta in events:
            area += cur * (tstamp - prev)
            prev = tstamp
            cur += delta
            peak = max(peak, cur)
        occupancy.append(area / win.window_seconds)
        peaks.append(peak)
    out["queue_mean"] = float(np.sum(occupancy) / max(len(by_node), 1))
    out["queue_p90"] = float(np.percentile(peaks, 90))
    out["queue_max"] = float(np.max(peaks))

    # Blending: the anonymity set of a release. A timed-release relay would have flushed anything
    # that arrived before its previous tick, so the message it forwards must have arrived in the
    # last inter-tick interval -- and since every broadcast reaches every node, the candidates are
    # all broadcasts in that interval. Uses each clock's real previous tick, not the mean interval.
    casts = np.sort(np.asarray(win.broadcasts))
    sets: list[int] = []
    for node, holds in by_node.items():
        clock = win.clocks.get(node)
        for r in sorted({h.released for h in holds}):
            if m <= 0:
                prev = r                                  # no delay: the set is whatever is instant
            elif clock is not None:
                earlier = [t for t in clock.ticks_in(-1e18, r) if t < r]
                prev = earlier[-1] if earlier else max(0.0, r - m / 2.0)
            else:
                prev = max(0.0, r - m / 2.0)
            # strictly before the release: when this relay is the last hop it broadcasts at exactly
            # `r`, and that is its own output, not a candidate input it saw.
            sets.append(int(np.searchsorted(casts, r, "left")
                            - np.searchsorted(casts, prev, "right")))
    if sets:
        arr = np.asarray(sets, dtype=float)
        out.update(blending_mean=float(arr.mean()), blending_p50=float(np.percentile(arr, 50)),
                   blending_p90=float(np.percentile(arr, 90)), blending_max=float(arr.max()))
    return out


def timing_linkability(win: TrafficWindow, config: SimConfig,
                       max_blend_delay: int | None = None,
                       min_blend_delay: int | None = None,
                       release_mode: str | None = None,
                       adversary_knows_schedule: bool = True) -> dict:
    """Can an observer match a relay's outgoing message to the incoming one, from timing alone?

    This is the attack that distinguishes a *blended* message from a merely *relayed* one: a relay
    that holds and re-emits leaves a timing signature, and if only one arrival can explain a given
    release then the two are linked and the relay's role in that cascade is exposed.

    The measure is the **effective anonymity set** of each release -- the perplexity of the
    observer's posterior over which arrival produced it. It is comparable across designs:

    * ``clock`` -- a release at a tick could be any arrival since the previous tick, all equally
      likely, so the effective set is simply the batch size.
    * ``jitter`` -- each message waits an independent draw, so every earlier arrival is a candidate
      weighted by the delay density (exponential here). Nothing is quantised, so the weights decay
      smoothly and the posterior concentrates on whichever arrival is closest to the expected lag.

    ``adversary_knows_schedule`` selects how much the clock design concedes. A free-running clock
    ticks whether or not anything is held, but only ticks that *release* something are visible. The
    strong adversary (default) is handed the true schedule and can exclude everything before the
    previous tick; the weak one sees only the node's previous release, so silent ticks widen its
    candidate window. Jitter has no schedule to know, so the switch does not affect it -- which is
    exactly why the comparison has to be run both ways.

    ``linked_frac`` is the share of releases whose set collapses to one candidate: the message is
    then linked with certainty, whatever the nominal delay was.

    The effective set alone flatters a heavy-tailed delay, because a long thin tail keeps old
    arrivals nominally "possible" while contributing almost nothing. ``map_success`` therefore also
    reports how often the adversary's single best guess is right -- for an exponential delay the
    most likely source is always the most recent arrival, so a design can look unlinkable by
    perplexity and still be guessed correctly most of the time.
    """
    m = int(config.max_blend_delay if max_blend_delay is None else max_blend_delay)
    lo = int(config.min_blend_delay if min_blend_delay is None else min_blend_delay)
    mode = release_mode or config.release_mode
    if not win.holds or m <= 0:
        return {"timing_set_mean": 1.0, "timing_set_p90": 1.0, "timing_linked_frac": 1.0}
    mean_hold = mean_residual_ms(m, lo) / 1000.0
    by_node: dict[int, list[Hold]] = {}
    for h in win.holds:
        by_node.setdefault(h.node, []).append(h)

    sets: list[float] = []
    hits: list[float] = []
    for node, holds in by_node.items():
        arrivals = np.sort(np.array([h.arrived for h in holds]))
        true_src = {h.released: h.arrived for h in holds}     # the arrival that really produced it
        rel_times = sorted({h.released for h in holds})
        for r in rel_times:
            if mode == "clock":
                prev = 0.0
                if adversary_knows_schedule:
                    clock = win.clocks.get(node)
                    if clock is not None:
                        earlier = [t for t in clock.ticks_in(-1e18, r) if t < r]
                        if earlier:
                            prev = earlier[-1]
                else:
                    seen = [t for t in rel_times if t < r]     # only releases are observable
                    if seen:
                        prev = seen[-1]
                cand = arrivals[(arrivals > prev) & (arrivals <= r + 1e-12)]
                n_c = max(len(cand), 1)
                sets.append(float(n_c))                        # uniform posterior -> perplexity = n
                hits.append(1.0 / n_c)                         # MAP is a coin flip among the batch
            else:
                earlier = arrivals[arrivals <= r + 1e-12]
                if earlier.size == 0:
                    sets.append(1.0)
                    hits.append(1.0)
                    continue
                w = np.exp(-(r - earlier) / mean_hold)         # exponential delay density
                p = w / w.sum()
                ent = float(-np.sum(p * np.log(np.clip(p, 1e-300, None))))
                sets.append(float(np.exp(ent)))                # perplexity = effective set size
                # MAP for an exponential is the most recent arrival; is that the true source?
                hits.append(float(abs(earlier[int(np.argmax(p))] - true_src[r]) < 1e-12))
    arr = np.asarray(sets)
    return {
        "timing_set_mean": float(arr.mean()),
        "timing_set_p90": float(np.percentile(arr, 90)),
        "timing_linked_frac": float(np.mean(arr < 1.5)),       # effectively a forced match
        "map_success": float(np.mean(hits)) if hits else 1.0,  # best single guess is correct
    }
