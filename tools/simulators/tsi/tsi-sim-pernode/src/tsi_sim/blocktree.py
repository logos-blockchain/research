"""Block tree, latency-driven forks, and honest longest-chain fork choice.

Blocks are stored in parallel arrays (id == index). A virtual genesis is block 0 at
slot -1, height 0. Every real block is produced at an active slot by one winning node
and points at the best tip *visible to that node at production time*, which is what makes
network latency (and same-slot multi-winners) produce forks.

Fork choice is honest longest-chain with a first-seen tie-break (prefer higher height,
then earlier slot, then lower id) — no adversary is modelled, so the spec's density /
deep-fork rules never engage.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from .latency import LatencyModel
from .memguard import ArrivalMatrixTooLarge, check_alloc

__all__ = ["ArrivalMatrixTooLarge", "BlockTree", "build_tree", "build_tree_pernode",
           "tips_for_all_nodes"]

GENESIS = 0


@dataclass
class BlockTree:
    slot: np.ndarray          # int64, slot of each block (genesis = -1)
    parent: np.ndarray        # int64, parent id (genesis = -1)
    height: np.ndarray        # int64, chain height (genesis = 0)
    leader: np.ndarray        # int64, producing node id (genesis = -1)
    uncles: list[tuple[int, ...]]   # referenced uncle ids per block (filled later)

    @property
    def n_blocks(self) -> int:
        return self.slot.shape[0]

    def ancestors(self, block_id: int) -> list[int]:
        """Ancestor chain of ``block_id`` from itself down to (excluding) genesis."""
        out: list[int] = []
        b = block_id
        while b > GENESIS:
            out.append(b)
            b = int(self.parent[b])
        return out

    def canonical_chain(self) -> list[int]:
        """Honest longest-chain: ancestors of the best tip over the whole tree.

        Returns real block ids (genesis excluded), tip-first.
        """
        tip = self._best_over_all()
        return self.ancestors(tip)

    def _rank(self, bid: int) -> tuple[int, int, int]:
        # Preference order for "better tip": higher height, earlier slot, lower id.
        return (int(self.height[bid]), -int(self.slot[bid]), -bid)

    def _best_over_all(self) -> int:
        best = GENESIS
        best_rank = self._rank(GENESIS)
        for bid in range(1, self.n_blocks):
            r = self._rank(bid)
            if r > best_rank:
                best_rank, best = r, bid
        return best


def build_tree(
    active_slots: np.ndarray,
    winners_per_slot: list[np.ndarray],
    latency: LatencyModel,
    rng: np.random.Generator,
) -> BlockTree:
    """Construct the block tree from grouped lottery winners under a latency model."""
    # Preallocate with genesis in slot 0.
    slot = [-1]
    parent = [-1]
    height = [0]
    leader = [-1]

    # global_best = best publicly-visible tip so far, as (height, slot, id).
    def better(a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
        # higher height, then earlier slot, then lower id
        ah, as_, ai = a
        bh, bs, bi = b
        if ah != bh:
            return a if ah > bh else b
        if as_ != bs:
            return a if as_ < bs else b
        return a if ai < bi else b

    global_best = (0, -1, GENESIS)
    own_best: dict[int, tuple[int, int, int]] = {}
    # min-heap of (visible_at, block_id) awaiting public visibility
    pending: list[tuple[int, int]] = []

    next_id = 1
    for si in range(active_slots.shape[0]):
        t = int(active_slots[si])
        # advance visibility frontier to slot t
        while pending and pending[0][0] <= t:
            _, bid = heapq.heappop(pending)
            cand = (height[bid], slot[bid], bid)
            global_best = better(global_best, cand)
        for v in winners_per_slot[si].tolist():
            gb = global_best
            ob = own_best.get(v, (0, -1, GENESIS))
            chosen = better(gb, ob)
            p_id = chosen[2]
            h = chosen[0] + 1
            bid = next_id
            next_id += 1
            slot.append(t)
            parent.append(p_id)
            height.append(h)
            leader.append(v)
            own_best[v] = (h, t, bid)
            va = latency.visible_at(t, rng)
            heapq.heappush(pending, (va, bid))

    return BlockTree(
        slot=np.asarray(slot, np.int64),
        parent=np.asarray(parent, np.int64),
        height=np.asarray(height, np.int64),
        leader=np.asarray(leader, np.int64),
        uncles=[() for _ in range(next_id)],
    )


# --- Per-node engine -------------------------------------------------------

def _rank_keys(height: np.ndarray, slot: np.ndarray, ids: np.ndarray,
               epoch_len: int) -> np.ndarray:
    """Composite int64 sort key so argmax reproduces the (height, −slot, −id) tie-break."""
    n = ids.shape[0]
    c2 = np.int64(n + 1)
    c1 = np.int64(epoch_len + 2) * c2
    return height.astype(np.int64) * c1 - slot.astype(np.int64) * c2 - ids.astype(np.int64)


@dataclass
class SlidingArrival:
    """Pruned arrival store: per-node columns only for blocks still inside the keep-span.

    Blocks with ``slot <= t - horizon`` are finalized — under deterministic latency every node
    has received them — so their per-node columns are dropped. ``buf[:, b - base]`` holds the
    arrival column for any live block ``b`` (``b >= base``); a block id ``< base`` is finalized and
    treated as "arrived at every node". This is what turns the ``O(N * n_blocks)`` arrival matrix
    into ``O(N * keep-span-blocks)``; ``tips_for_all_nodes`` reconstructs exact per-node tips from
    it. Equivalent to the full matrix when ``jitter_mean == 0``.
    """
    buf: np.ndarray          # (N, buf_width) base-offset column buffer of recent arrivals
    base: int                # absolute block id stored at buf[:, 0]
    horizon: float           # slot <= t - horizon  =>  arrived at every node
    n: int                   # N (node count)
    nb: int                  # number of blocks


def _max_span_blocks(active_slots: np.ndarray, counts: np.ndarray, span: float) -> int:
    """Max number of blocks whose slot lies in any ``span``-wide slot window (for buffer sizing)."""
    if active_slots.size == 0:
        return 1
    # inclusive window slot >= t - span (matches the sliding buffer's kept set / uncle window)
    cum = np.concatenate([[0], np.cumsum(counts)])
    best, left = 0, 0
    for r in range(active_slots.shape[0]):
        while active_slots[left] < active_slots[r] - span:
            left += 1
        best = max(best, int(cum[r + 1] - cum[left]))
    return best


def build_tree_pernode(
    active_slots: np.ndarray,
    winners_per_slot: list[np.ndarray],
    path_latency: np.ndarray,
    config,
    rng: np.random.Generator,
    adversary_mask: np.ndarray | None = None,
):
    """Build the global block tree AND the per-node arrival matrix.

    ``adversary_mask[v] == True`` marks a node that suppresses uncle references in its own blocks
    (references none), to deflate the TSI density count (grinding). ``None`` = fully honest.

    Each winner builds on the best tip *in its own arrival-filtered view*; uncle refs are
    baked at production from the producer's view. Returns ``(BlockTree, A)`` where
    ``A[i, b]`` is the slot block ``b`` becomes usable at node ``i``.

    Fork choice — full scan vs windowed horizon
    -------------------------------------------
    A winner ``v`` at slot ``t`` builds on the highest-key block it has received
    (``A[v, b] <= t``). Naively this scans all ``nb`` blocks so far → ``O(n_blocks^2)`` per
    epoch. With ``config.windowed_fork_choice`` (default) we scan only a horizon and add one
    representative of everything older:

      * ``H = max path latency`` over the graph (for ``blend``, ``H`` also adds the whole mix
        cascade: ``(blend_hops+1)*max_path_latency + blend_hops*blend_delay_max``, a hard bound
        since the per-relay mixing delays are ``Uniform``-bounded). Any block with
        ``slot <= t - H`` has, under *deterministic* latency, reached **every** node
        (``slot + propagation <= t``), so the best of them — the "fully-propagated tip" ``gb`` —
        is a valid candidate for *all* nodes and is tracked incrementally. Only blocks with
        ``slot > t - H`` need a per-node arrival check. Result: ``O(n_blocks * H * f)``, and
        **exact** when latency is deterministic (including blend's bounded mixing delays).

    CAVEAT: exactness assumes actual arrival never exceeds ``slot + H``. That holds only when
    ``jitter_mean == 0``. With ``jitter_mean > 0`` the stochastic jitter can delay a block past
    the horizon, so ``gb`` may be offered to a node that has not actually received it, or a
    node's true best old tip may sit just outside the window — a (usually tiny) approximation.
    We warn in that case; a guaranteed-exact result is available via
    ``windowed_fork_choice=False`` (full scan). A safety clamp below still guarantees no node
    ever builds on a block it has not received, so the tree stays valid regardless.
    """
    import warnings

    from .topology import arrival_column
    from .uncles import select_uncles_at_production

    n = config.n_nodes
    n_blocks = 1 + sum(int(g.shape[0]) for g in winners_per_slot)
    E = config.epoch_len

    slot = np.empty(n_blocks, np.int64)
    parent = np.empty(n_blocks, np.int64)
    height = np.empty(n_blocks, np.int64)
    leader = np.empty(n_blocks, np.int64)
    uncles: list[tuple[int, ...]] = [() for _ in range(n_blocks)]
    slot[0], parent[0], height[0], leader[0] = -1, -1, 0, -1

    c2 = np.int64(n_blocks + 1)
    c1 = np.int64(E + 2) * c2
    key = np.empty(n_blocks, np.int64)
    key[0] = np.int64(0) * c1 - np.int64(-1) * c2 - np.int64(0)
    NEG = np.iinfo(np.int64).min

    windowed = bool(config.windowed_fork_choice)
    if not windowed:
        horizon = float(E)                             # full scan (gb unused)
    elif config.topology == "blend":
        # blend arrival = cascade of (hops+1) transport legs + hops Uniform(0, delay_max) mix
        # delays; all bounded, so this is a HARD upper bound on (arrival - slot) -> still exact.
        max_pl = float(path_latency.max())
        dmax = float(config.blend_delay_max)
        horizon = (config.blend_hops + 1) * max_pl + config.blend_hops * dmax
    else:
        horizon = float(path_latency.max())            # H; disconnected -> full scan
    if windowed and config.jitter_mean > 0.0:
        warnings.warn(
            "windowed_fork_choice / prune_arrival are only approximate when jitter_mean > 0: "
            "stochastic arrival jitter can push a block past the deterministic horizon, so a "
            "node's true best older tip may be missed. Set windowed_fork_choice=False for a "
            "guaranteed-exact full scan.",
            RuntimeWarning, stacklevel=2,
        )

    # Sliding-window prune needs the deterministic horizon, so it only applies with windowed fork
    # choice AND jitter_mean == 0. With jitter the full matrix's safety clamp is required. A
    # withholding adversary produces blocks that NEVER arrive (arrival > E), violating the prune's
    # "finalized => arrived-everywhere" assumption, so it too forces the full matrix.
    withholding = (adversary_mask is not None and config.adversary_frac > 0.0
                   and config.adversary_strategy == "withhold")
    if config.prune_arrival and windowed and config.jitter_mean == 0.0 and not withholding:
        return _build_pruned(active_slots, winners_per_slot, path_latency, config, rng,
                             slot, parent, height, leader, uncles, key, c1, c2,
                             float(horizon), n_blocks, E, n, adversary_mask)

    # --- full (N x n_blocks) matrix path: the exact parity oracle -----------------
    # Guard BEFORE the big allocation: A is (N x n_blocks) float64. A collapsed D_est (small
    # genesis_d_factor) inflates lottery wins, so n_blocks can explode far past the ~10*k
    # equilibrium and make A tens of GB. Fail loud rather than freeze the machine.
    check_alloc(
        n * n_blocks * 8, f"arrival matrix A (N={n} x n_blocks={n_blocks} x 8B)",
        f"n_blocks={n_blocks} is ~{n_blocks / max(10 * config.k, 1):.0f}x the ~{10 * config.k} "
        f"equilibrium, driven by genesis_d_factor={config.genesis_d_factor} "
        f"(sum(stake)/D_est_genesis={1.0 / config.genesis_d_factor:.0f}). Raise "
        f"genesis_d_factor, lower n_nodes/k, prune_arrival, or raise --mem-frac.")

    # arrival times are sub-slot (float): latency is in slots and a slot is 1 s, so realistic
    # inter-node latencies are fractions of a slot (see topology.build_path_latency).
    A = np.full((n, n_blocks), float(E), np.float64)  # sentinel = epoch_len ("never" arrives)
    A[:, 0] = 0.0                                # genesis known to all from slot 0
    withheld = np.zeros(n_blocks, dtype=bool)   # adversary "withhold": block never arrives anywhere

    gb_key = key[0]     # running best fully-propagated tip (slot <= t - H)
    gb_id = 0
    fp_idx = 1          # frontier pointer over fully-propagated blocks

    nb = 1
    for si in range(active_slots.shape[0]):
        t = int(active_slots[si])
        winners = winners_per_slot[si]
        # --- fork choice: window [lo, nb) + fully-propagated best gb ---
        if windowed:
            thr = t - horizon
            while fp_idx < nb and int(slot[fp_idx]) <= thr:   # advance propagated frontier
                if not withheld[fp_idx] and key[fp_idx] > gb_key:   # withheld blocks reach no node
                    gb_key, gb_id = int(key[fp_idx]), fp_idx
                fp_idx += 1
            lo = int(np.searchsorted(slot[:nb], thr, side="right"))   # first slot > t - H
        else:
            lo = 0                                            # full scan (gb unused)
        if lo < nb:
            sub = A[winners, lo:nb] <= t                      # (w, nb-lo)
            masked = np.where(sub, key[lo:nb], NEG)
            win_key = masked.max(axis=1)
            parents = masked.argmax(axis=1) + lo
        else:
            win_key = np.full(winners.shape[0], NEG, np.int64)
            parents = np.zeros(winners.shape[0], np.int64)
        if windowed:
            gb_ok = A[winners, gb_id] <= t                    # gb actually received? (jitter)
            use_gb = gb_ok & (gb_key > win_key)
            parents = np.where(use_gb, gb_id, parents)
            # safety: never build on a block a node has not received (jitter edge) -> genesis
            bad = A[winners, parents] > t
            if bad.any():
                parents = np.where(bad, 0, parents)
        for wi in range(winners.shape[0]):
            v = int(winners[wi])
            p_id = int(parents[wi])
            h = int(height[p_id]) + 1
            b = nb
            slot[b], parent[b], height[b], leader[b] = t, p_id, h, v
            key[b] = np.int64(h) * c1 - np.int64(t) * c2 - np.int64(b)
            adv = adversary_mask is not None and adversary_mask[v]
            hide = adv and config.adversary_strategy == "withhold"
            if adv:                                          # suppress refs (both adversary modes)
                uncles[b] = ()
            else:
                uncles[b] = select_uncles_at_production(
                    slot, parent, uncles, A[v], b, p_id, t, config, rng
                )
            col = arrival_column(path_latency, v, t, config, rng)   # (rng drawn either way)
            if hide:
                A[:, b] = float(E) + 1.0                     # withheld: never arrives -> orphan
                withheld[b] = True
            else:
                np.maximum(col, A[:, p_id], out=col)
                A[:, b] = col
                A[v, b] = max(float(t), float(A[v, p_id]))   # producer sees own block at its slot
            nb += 1

    tree = BlockTree(slot=slot, parent=parent, height=height, leader=leader, uncles=uncles)
    return tree, A


def _build_pruned(active_slots, winners_per_slot, path_latency, config, rng,
                  slot, parent, height, leader, uncles, key, c1, c2, horizon, n_blocks, E, n,
                  adversary_mask=None):
    """Windowed build with a sliding-window arrival buffer (see ``SlidingArrival``).

    Identical tree/uncles to the full-matrix path when ``jitter_mean == 0`` (the guaranteed regime
    for ``windowed_fork_choice``): a block ``slot <= t - horizon`` is received by everyone, so its
    per-node column is never needed again — fork choice only scans the horizon window, the parent
    clamp on a finalized parent is a no-op (its arrival ``<= t <= col``), and uncle candidates
    older than the horizon are trivially received. We therefore keep columns only for blocks inside
    ``max(horizon, uncle_window)`` slots, in a base-offset buffer, and finalize (drop) the rest.
    """
    from .topology import arrival_column
    from .uncles import select_uncles_at_production

    NEG = np.iinfo(np.int64).min
    keepspan = max(float(horizon), float(config.uncle_window))    # columns kept within this span
    counts = np.array([int(g.shape[0]) for g in winners_per_slot], dtype=np.int64)
    cap = _max_span_blocks(active_slots, counts, keepspan)        # max live blocks at once
    max_slot = int(counts.max()) if counts.size else 0
    buf_width = 2 * (cap + max_slot) + 8                          # headroom => rare compaction
    check_alloc(
        n * buf_width * 8, f"pruned arrival buffer (N={n} x {buf_width} cols x 8B)",
        f"sliding-window prune keeps ~{cap} of {n_blocks} block-columns "
        f"(keepspan={keepspan:g} slots); raise --mem-frac if genuinely too large.")
    buf = np.full((n, buf_width), float(E), np.float64)           # sentinel = E ("never arrives")
    buf[:, 0] = 0.0                                               # genesis (id 0) known to all
    base = 0                                                      # absolute id at buf[:, 0]

    gb_key, gb_id, fp_idx = int(key[0]), 0, 1
    nb = 1
    for si in range(active_slots.shape[0]):
        t = int(active_slots[si])
        winners = winners_per_slot[si]
        thr = t - horizon
        while fp_idx < nb and int(slot[fp_idx]) <= thr:          # advance fully-propagated frontier
            if int(key[fp_idx]) > gb_key:
                gb_key, gb_id = int(key[fp_idx]), fp_idx
            fp_idx += 1
        lo = int(np.searchsorted(slot[:nb], thr, side="right"))  # first block with slot > t - H
        if lo < nb:
            sub = buf[winners, lo - base:nb - base] <= t         # window blocks are all live
            masked = np.where(sub, key[lo:nb], NEG)
            win_key = masked.max(axis=1)
            parents = masked.argmax(axis=1) + lo
        else:
            win_key = np.full(winners.shape[0], NEG, np.int64)
            parents = np.zeros(winners.shape[0], np.int64)
        # gb is fully-propagated (slot <= t - H) => received by all under jitter=0 (gb_ok=True), and
        # the finally-chosen parent is always received, so no bad-clamp is needed (parity: the full
        # path's gb_ok/bad are likewise no-ops at jitter=0).
        parents = np.where(gb_key > win_key, gb_id, parents)
        for wi in range(winners.shape[0]):
            v = int(winners[wi])
            p_id = int(parents[wi])
            h = int(height[p_id]) + 1
            b = nb
            slot[b], parent[b], height[b], leader[b] = t, p_id, h, v
            key[b] = np.int64(h) * c1 - np.int64(t) * c2 - np.int64(b)
            if b - base >= buf_width:                            # compact: drop finalized columns
                # keep slot >= t - keepspan (side="left"): the uncle window's lower bound is also
                # inclusive (slot >= t-W), so base must not advance past a block it may still read.
                live_lo = int(np.searchsorted(slot[:nb], t - keepspan, side="left"))
                if live_lo > base:
                    keep = nb - live_lo
                    if keep > 0:
                        buf[:, :keep] = buf[:, live_lo - base:nb - base].copy()
                    base = live_lo
            if adversary_mask is not None and adversary_mask[v]:
                uncles[b] = ()                               # adversary suppresses uncle refs
            else:
                uncles[b] = select_uncles_at_production(
                    slot, parent, uncles, buf[v], b, p_id, t, config, rng, arr_base=base)
            col = arrival_column(path_latency, v, t, config, rng)
            if p_id >= base:                                     # live parent -> clamp; else no-op
                np.maximum(col, buf[:, p_id - base], out=col)
            buf[:, b - base] = col
            pv = float(buf[v, p_id - base]) if p_id >= base else float(t)   # finalized parent <= t
            buf[v, b - base] = max(float(t), pv)
            nb += 1

    tree = BlockTree(slot=slot, parent=parent, height=height, leader=leader, uncles=uncles)
    return tree, SlidingArrival(buf=buf, base=base, horizon=float(horizon), n=n, nb=nb)


def _tips_pruned(tree: BlockTree, arr: SlidingArrival, cutoff: int) -> np.ndarray:
    """Per-node tips from the sliding buffer: best fully-propagated block (global) vs each node's
    best recent (still-in-window) arrival. Exact equivalent of the full-matrix argmax at jitter=0.
    """
    nb = tree.n_blocks
    key = _rank_keys(tree.height, tree.slot, np.arange(nb), cutoff + 2)
    NEG = np.iinfo(np.int64).min
    recent = tree.slot > (cutoff - arr.horizon)         # slot > E - H: per-node arrival varies
    recent[0] = False                                   # genesis is finalized (arrived at all)
    # best over finalized/"arrived-everywhere" blocks (slot <= E - H): a candidate for every node
    fin_ids = np.nonzero(~recent)[0]
    gb_final = int(fin_ids[np.argmax(key[fin_ids])])
    recent_ids = np.nonzero(recent)[0]
    if recent_ids.size == 0:
        return np.full(arr.n, gb_final, np.int64)
    arrived = arr.buf[:, recent_ids - arr.base] <= cutoff          # (N, R) recent blocks in buffer
    masked = np.where(arrived, key[recent_ids][None, :], NEG)
    best_recent = recent_ids[masked.argmax(axis=1)]
    use_recent = masked.max(axis=1) > int(key[gb_final])
    return np.where(use_recent, best_recent, gb_final)


def tips_for_all_nodes(tree: BlockTree, arrival, cutoff: int,
                       row_chunk: int = 64) -> np.ndarray:
    """Per-node best tip = argmax (height, −slot, −id) over blocks arrived by ``cutoff``.

    ``arrival`` is either the full ``(N, n_blocks)`` matrix or a pruned ``SlidingArrival``; both
    yield the same tips at ``jitter_mean == 0``. For the full matrix, each node's argmax is
    independent, so we process it in ``row_chunk`` node-row bands — capping the transient
    ``np.where`` mask at ``(row_chunk, nb)`` instead of a second full ``(N, nb)`` int64 array
    (bitwise-identical to the unchunked argmax).
    """
    if isinstance(arrival, SlidingArrival):
        return _tips_pruned(tree, arrival, cutoff)
    nb = tree.n_blocks
    n = arrival.shape[0]
    ids = np.arange(nb)
    key = _rank_keys(tree.height, tree.slot, ids, cutoff + 2)
    NEG = np.iinfo(np.int64).min
    tips = np.empty(n, np.int64)
    for lo in range(0, n, row_chunk):
        hi = min(lo + row_chunk, n)
        masked = np.where(arrival[lo:hi] <= cutoff, key[None, :], NEG)   # (row_chunk, nb)
        tips[lo:hi] = masked.argmax(axis=1)
    return tips                                                    # (N,)
