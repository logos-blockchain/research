"""Phase E1: Areon-Base's block DAG on the TSI engine, and the private attack on it (PLAN.md E).

Paper: Castro-Castilla, Pawlowski, Zhou, arXiv 2511.23025v1, Algorithms 5-7 and Definitions 2.3,
2.5, 5.1.

**The honest DAG.** One epoch of the engine's lottery (Cryptarchia's per-node lottery at the
production coefficient ``config.f``), topology and Blend delays. A winner at slot ``t``
short-references every tip of its view inside the window ``[t - w, t - 1]``: the visible window
blocks with no visible window child. That is the coverage ``q = 1`` the paper names (§4.1.1). With
no visible block in the window it carries one long reference to its latest visible block. A block
reaches node ``i`` through Blend as in the engine, never before its parents. Its height is one
more than its parents' highest; the depth of a block is the height its descendants have reached
above it (Def. 5.1, measured along references).

**The weight.** The paper defines the CCA-local subDAG weight over ``Desc*(i)``, which for a tip
holds only the tip itself; its proof (Def. 5.3, Lemma 5.5) needs the competing subDAG between the
closest common ancestor and the tip. Here a competing subDAG's weight counts its blocks after the
fork, each once if it carries a short reference, which is ``wref in {0, 1}`` of §5.3; long
references weigh nothing (§2.2.1). Every honest block with a short reference counts, wherever it
sits in the DAG. Two horizons are kept, because the paper describes both:

- ``recent=None``: every block since the fork (the drift of Def. 5.3 accumulates);
- ``recent=w``: only blocks of the last ``w`` slots ("only references created within the most
  recent w slots", §5.3). The coalition's blocks count from ``B`` on, the honest blocks from ``B``
  itself.

**The attack** is B3's private race on the DAG. A coalition withholds its wins and builds a private
subDAG that conflicts with the target ``B``; each of its wins adds one block (one per ``rho_LEAD``).
Before ``B`` it may hold a premined lead over the honest blocks; without one it starts from ``B``'s
latest parent, with the wins it made since. Afterwards every honest block adds one to the honest
side and every coalition block one to its side. The receiver accepts ``B`` at
depth ``K``; the attack succeeds if the coalition's weight then reaches the honest weight plus
``win_at`` (1: strictly heavier; 0: ties to the attacker, as Areon breaks ties by a VRF coin the
attacker cannot steer, so the truth lies between).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit
from tsi_sim import lottery, topology
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import make_stake


@dataclass
class Dag:
    slot: np.ndarray             # per honest block (genesis = index 0, slot -1)
    height: np.ndarray
    producer: np.ndarray
    ref_ptr: np.ndarray          # CSR of references (short and long)
    refs: np.ndarray
    long_ref: np.ndarray         # True if the block's only reference is a long one
    adv_slots: np.ndarray        # the coalition's withheld wins, one entry per win
    tips_seen: np.ndarray        # per honest block, the tips its producer referenced
    arrival: np.ndarray | None = None

    @property
    def n_blocks(self) -> int:
        return self.slot.size


def build_dag(config: SimConfig, window: int, keep_arrival: bool = False) -> Dag:
    """One epoch of honest blocks under Areon-Base's referencing; the coalition's wins withheld."""
    root = seedseq_for(config)
    c_stake, c_graph, c_lottery, c_aux = root.spawn(4)
    stake = make_stake(config, np.random.default_rng(c_stake))
    adv = (_adversary_mask(config, stake) if config.adversary_frac > 0
           else np.zeros(config.n_nodes, dtype=bool))
    path_latency = topology.build_path_latency(config, np.random.default_rng(c_graph))
    p = lottery.win_probs(stake, float(stake.sum()), config.f)
    slots, nodes = lottery.sample_wins(p, config.epoch_len, np.random.default_rng(c_lottery))
    active, groups = lottery.group_by_slot(slots, nodes)
    rng = np.random.default_rng(c_aux)

    n, cap = config.n_nodes, 1024
    slot = np.full(cap, -1, np.int64)
    height = np.zeros(cap, np.int64)
    producer = np.full(cap, -1, np.int64)
    long_ref = np.zeros(cap, dtype=bool)
    tips_seen = np.zeros(cap, np.int64)
    arrival = np.full((n, cap), np.inf)
    arrival[:, 0] = 0.0
    refs: list[np.ndarray] = [np.empty(0, np.int64)]
    adv_slots: list[int] = []
    nb = 1
    for t, winners in zip(active.tolist(), groups):
        a = adv[winners]
        adv_slots.extend([t] * int(a.sum()))
        honest = winners[~a]
        if honest.size == 0:
            continue
        lo = int(np.searchsorted(slot[:nb], t - window, side="left"))
        lo = max(lo, 1)
        chosen = []
        for v in honest.tolist():
            vis = arrival[v, lo:nb] <= t
            if vis.any():
                has_child = np.zeros(nb - lo, dtype=bool)
                for c in np.nonzero(vis)[0].tolist():
                    for q in refs[lo + c].tolist():
                        if q >= lo:
                            has_child[q - lo] = True
                tips = np.nonzero(vis & ~has_child)[0] + lo
                chosen.append((v, tips, False))
            else:
                b = nb - 1
                while b > 0 and arrival[v, b] > t:
                    b -= 1
                chosen.append((v, np.array([b], np.int64), True))
        for v, parents, is_long in chosen:
            if nb == cap:
                cap *= 2
                slot, height, producer, long_ref, tips_seen = (
                    np.resize(x, cap) for x in (slot, height, producer, long_ref, tips_seen))
                arrival = np.concatenate((arrival, np.full((n, cap - nb), np.inf)), axis=1)
            slot[nb], producer[nb], long_ref[nb] = t, v, is_long
            height[nb] = int(height[parents].max()) + 1
            tips_seen[nb] = 0 if is_long else parents.size
            refs.append(parents.astype(np.int64))
            col = topology.arrival_column(path_latency, v, t, config, rng)
            np.maximum(col, arrival[:, parents].max(axis=1), out=col)
            arrival[:, nb] = col
            arrival[v, nb] = float(t)
            nb += 1
    ref_ptr = np.zeros(nb + 1, np.int64)
    ref_ptr[1:] = np.cumsum([r.size for r in refs])
    return Dag(slot=slot[:nb].copy(), height=height[:nb].copy(), producer=producer[:nb].copy(),
               ref_ptr=ref_ptr, refs=np.concatenate(refs) if nb > 1 else np.empty(0, np.int64),
               long_ref=long_ref[:nb].copy(), adv_slots=np.asarray(adv_slots, np.int64),
               tips_seen=tips_seen[:nb].copy(),
               arrival=arrival[:, :nb].copy() if keep_arrival else None)


def children_csr(dag: Dag) -> tuple[np.ndarray, np.ndarray]:
    counts = np.bincount(dag.refs, minlength=dag.n_blocks)
    ptr = np.zeros(dag.n_blocks + 1, np.int64)
    ptr[1:] = np.cumsum(counts)
    child = np.empty(dag.refs.size, np.int64)
    fill = ptr[:-1].copy()
    for b in range(1, dag.n_blocks):
        for q in dag.refs[dag.ref_ptr[b]:dag.ref_ptr[b + 1]]:
            child[fill[q]] = b
            fill[q] += 1
    return ptr, child


@njit(cache=True)
def _dag_race(slot, height, ch_ptr, child, parent_slot, weight, adv, window, k_max, give_up,
              premine, win_at, recent, first, last, descendants_only):
    """Successes per depth K (index K-1) and the number of scored targets.

    ``slot``, ``height`` and ``weight`` (0 or 1) are per honest block in slot order (index 0 is
    genesis); ``parent_slot`` is the slot of each block's latest parent; ``adv`` holds the
    coalition's win slots, sorted. A win weighs one if the latest block on the coalition's side is
    at most ``window`` slots older. Targets are the blocks ``first..last-1``.
    """
    n, n_a = slot.size, adv.size
    succ = np.zeros(k_max, np.int64)
    scored = 0
    stamp = np.zeros(n, np.int64)
    queue = np.empty(n, np.int64)
    # premined lead, and the latest block on the coalition's side, just before each honest block;
    # a coalition with no lead starts again from the public tip
    lead_before = np.zeros(n, np.int64)
    side_before = np.zeros(n, np.int64)
    lead, ia, side = 0, 0, slot[0]
    for i in range(1, n):
        while ia < n_a and adv[ia] <= slot[i]:            # wins count first within a slot
            if adv[ia] - side <= window:
                lead += 1
            side = adv[ia]
            ia += 1
        lead_before[i] = lead
        side_before[i] = side
        if lead > weight[i]:
            lead -= weight[i]
        else:
            lead = 0
            side = slot[i]
    aw = np.zeros(n_a, np.int64)                           # this target's win weights
    big = np.int64(1) << 62
    for b in range(first, last):
        # descendants of b, in id order (id order is slot order)
        stamp_id = b + 1
        head, tail = 0, 0
        for e in range(ch_ptr[b], ch_ptr[b + 1]):
            c = child[e]
            if stamp[c] != stamp_id:
                stamp[c] = stamp_id
                queue[tail] = c
                tail += 1
        while head < tail:
            u = queue[head]
            head += 1
            for e in range(ch_ptr[u], ch_ptr[u + 1]):
                c = child[e]
                if stamp[c] != stamp_id:
                    stamp[c] = stamp_id
                    queue[tail] = c
                    tail += 1
        ja = 0
        since_parent = 0
        side = parent_slot[b]                              # the fork point
        while ja < n_a and adv[ja] <= slot[b]:
            if adv[ja] > parent_slot[b]:
                if adv[ja] - side <= window:
                    since_parent += 1
                side = adv[ja]
            ja += 1
        if premine:
            r = lead_before[b] - weight[b]
            side = side_before[b]
        else:
            r = since_parent - weight[b]
        best_after = np.full(k_max, -(np.int64(1) << 40), np.int64)
        depth = 0
        ih = b + 1                                         # next honest block (any)
        win_lo_a, win_lo_h = ja, b                         # recent-window pointers
        truncated = False
        while True:
            t_a = adv[ja] if ja < n_a else big
            t_h = slot[ih] if ih < n else big
            if t_a == big and t_h == big:
                truncated = True
                break
            if t_a <= t_h:
                t = t_a
                aw[ja] = 1 if t_a - side <= window else 0
                side = t_a
                r += aw[ja]
                ja += 1
            else:
                t = t_h
                if stamp[ih] == stamp_id:
                    d = height[ih] - height[b]
                    if d > depth:
                        depth = d
                    r -= weight[ih]
                elif not descendants_only:
                    r -= weight[ih]
                ih += 1
            score = r
            if recent > 0:
                while win_lo_a < ja and adv[win_lo_a] <= t - recent:
                    win_lo_a += 1
                while win_lo_h < ih and slot[win_lo_h] <= t - recent:
                    win_lo_h += 1
                score = 0
                for x in range(win_lo_a, ja):
                    score += aw[x]
                for x in range(win_lo_h, ih):
                    score -= weight[x]
            for kk in range(min(depth, k_max)):
                if score > best_after[kk]:
                    best_after[kk] = score
            if recent == 0 and r < -give_up and depth >= k_max:
                break
            if recent > 0 and depth >= k_max and t > slot[b] + give_up * recent:
                break
        if truncated and depth < k_max:
            continue
        scored += 1
        for kk in range(k_max):
            if best_after[kk] >= win_at:
                succ[kk] += 1
    return succ, scored


def race_weights(dag: Dag) -> tuple[np.ndarray, np.ndarray]:
    """Honest block weights and the coalition's sorted wins (see ``dag_race``)."""
    weight = (~dag.long_ref).astype(np.int64)
    weight[0] = 0
    return weight, np.sort(dag.adv_slots)


def dag_race(dag: Dag, k_max: int, window: int, give_up: int = 60, premine: bool = True,
             win_at: int = 1, recent: int | None = None, first: int = 1,
             last: int | None = None, descendants_only: bool = False):
    """Attack successes at acceptance depths 1..k_max (in layers), and the scored targets.

    A block weighs one if it short-references a block at most ``window`` slots older, and nothing
    otherwise. An honest block weighs one unless it carries only a long reference. The coalition's
    block weighs one if the latest block on its side is at most ``window`` slots older: its previous
    win, the fork point, or, while premining with no lead, the public tip. With
    ``descendants_only``, an honest block after ``B`` that does not descend from it weighs nothing
    for either side: the coalition could reference it and so make it common to both subDAGs.
    """
    ptr, child = children_csr(dag)
    parent_slot = np.full(dag.n_blocks, -1, np.int64)
    for b in range(1, dag.n_blocks):
        parent_slot[b] = dag.slot[dag.refs[dag.ref_ptr[b]:dag.ref_ptr[b + 1]]].max()
    weight, adv = race_weights(dag)
    return _dag_race(dag.slot, dag.height, ptr, child, parent_slot, weight, adv, window,
                     k_max, give_up, premine, win_at, 0 if recent is None else int(recent),
                     first, dag.n_blocks if last is None else last, descendants_only)
