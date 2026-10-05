"""Phase C4: a lottery coefficient that rises with the slots since the parent (PLAN.md C4).

Ouroboros Taktikos (Schutza, Behrens, Duong, Aman, BlockSys 2023) replaces the constant
coefficient ``f`` by a curve ``f(delta)`` of the slots ``delta`` since the parent. Topl documented
its "snowplow" curve (wiki.topl.co, Taktikos Proof-of-Stake, archived 2023-03-23) with a slot gap
``Psi``, a cutoff ``gamma``, an amplitude ``f_A`` and a baseline ``f_B``:

- ``f = 0`` for ``delta <= gap``;
- a ramp from 0 at ``gap`` to ``amp`` at ``cutoff``;
- ``f = base`` past the cutoff.

A note holding relative stake ``s`` wins with probability ``1 - (1 - f(delta))^s``, with
``delta`` measured from the parent it extends.

The block tree is built per node as the engine builds it (``build_tree_pernode``, honest nodes,
full arrival matrix): a winner extends the best block it holds (height, then earlier slot, then
lower id), and a block reaches each node through ``topology.arrival_column``, never before its
parent. Candidates are drawn at the curve's largest coefficient and kept with the ratio of the
two win probabilities, which draws the ``delta``-dependent lottery exactly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from tsi_sim import lottery, topology
from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import make_stake


@dataclass(frozen=True)
class Curve:
    gap: int
    cutoff: int
    amp: float
    base: float

    def __call__(self, delta) -> np.ndarray:
        d = np.asarray(delta, dtype=float)
        ramp = self.amp * (d - self.gap) / max(self.cutoff - self.gap, 1)
        return np.where(d <= self.gap, 0.0, np.where(d <= self.cutoff, ramp, self.base))

    @property
    def peak(self) -> float:
        return max(self.amp, self.base)


def constant(f: float) -> Curve:
    """Cryptarchia's lottery: the same coefficient at every distance from the parent."""
    return Curve(gap=0, cutoff=0, amp=f, base=f)


def win_prob(curve: Curve, share, delta) -> np.ndarray:
    return 1.0 - (1.0 - curve(delta)) ** np.asarray(share, dtype=float)


def interval_pmf(curve: Curve, share: float, tail: float = 1e-15) -> np.ndarray:
    """P(the next block of a lone producer comes delta slots after its last), delta = 0, 1, ..."""
    h_base = 1.0 - (1.0 - curve.base) ** share
    if h_base <= 0.0:
        raise ValueError("a curve with no baseline never finishes")
    n = curve.cutoff + int(math.ceil(math.log(tail) / math.log1p(-h_base))) + 2
    h = win_prob(curve, share, np.arange(n))
    h[0] = 0.0
    survive = np.concatenate(([1.0], np.cumprod(1.0 - h[1:])))
    pmf = np.zeros(n)
    pmf[1:] = survive[:-1] * h[1:]
    return pmf


def mean_interval(curve: Curve, share: float = 1.0) -> float:
    """Mean slots between the blocks of a lone producer holding ``share`` of the stake."""
    pmf = interval_pmf(curve, share)
    return float(np.dot(np.arange(pmf.size), pmf))


def build_epoch(config: SimConfig, curve: Curve):
    """One epoch's block tree and arrival matrix under ``curve``. Adversarial stake withholds."""
    root = seedseq_for(config)
    c_stake, c_graph, c_lottery, c_aux = root.spawn(4)
    stake = make_stake(config, np.random.default_rng(c_stake))
    honest = np.ones(config.n_nodes, dtype=bool)
    if config.adversary_frac > 0:
        honest = ~_adversary_mask(config, stake)
    path_latency = topology.build_path_latency(config, np.random.default_rng(c_graph))
    rel = stake / stake.sum()
    p_max = np.where(honest, 1.0 - (1.0 - curve.peak) ** rel, 0.0)
    slots, nodes = lottery.sample_wins(p_max, config.epoch_len, np.random.default_rng(c_lottery))
    active, groups = lottery.group_by_slot(slots, nodes)
    rng = np.random.default_rng(c_aux)

    n, cap = config.n_nodes, 1024
    slot = np.full(cap, -1, np.int64)
    parent = np.full(cap, -1, np.int64)
    height = np.zeros(cap, np.int64)
    leader = np.full(cap, -1, np.int64)
    key = np.zeros(cap, np.int64)
    arrival = np.full((n, cap), np.inf)
    arrival[:, 0] = 0.0
    c2 = np.int64(slots.size + 2)
    c1 = np.int64(config.epoch_len + 2) * c2
    neg = np.iinfo(np.int64).min
    nb = 1
    for t, cands in zip(active.tolist(), groups):
        u = rng.random(cands.size)
        seen = np.where(arrival[cands, :nb] <= t, key[:nb], neg)
        parents = seen.argmax(axis=1)
        keep = u * p_max[cands] < win_prob(curve, rel[cands], t - slot[parents])
        for v, p in zip(cands[keep].tolist(), parents[keep].tolist()):
            if nb == cap:
                cap *= 2
                slot, parent, height, leader, key = (np.resize(x, cap) for x in
                                                     (slot, parent, height, leader, key))
                arrival = np.concatenate((arrival, np.full((n, cap - nb), np.inf)), axis=1)
            slot[nb], parent[nb], height[nb], leader[nb] = t, p, height[p] + 1, v
            key[nb] = np.int64(height[nb]) * c1 - np.int64(t) * c2 - np.int64(nb)
            col = topology.arrival_column(path_latency, v, t, config, rng)
            np.maximum(col, arrival[:, p], out=col)
            arrival[:, nb] = col
            arrival[v, nb] = max(float(t), float(arrival[v, p]))
            nb += 1
    tree = BlockTree(slot=slot[:nb].copy(), parent=parent[:nb].copy(), height=height[:nb].copy(),
                     leader=leader[:nb].copy(), uncles=[() for _ in range(nb)])
    return tree, np.where(np.isinf(arrival[:, :nb]), float(config.epoch_len), arrival[:, :nb])


def renewal_slots(curve: Curve, share: float, n_slots: int, rng) -> np.ndarray:
    """Block slots of a lone producer holding ``share``, each interval drawn from the curve."""
    pmf = interval_pmf(curve, share)
    n = int(2 * n_slots / mean_interval(curve, share)) + 100
    t = np.cumsum(rng.choice(pmf.size, size=n, p=pmf / pmf.sum()))
    return t[t < n_slots].astype(np.int64)

