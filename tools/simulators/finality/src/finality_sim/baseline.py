"""Phase A1: orphan share, visibility delay, canonical growth and time to depth (PLAN.md).

One epoch of the TSI per-node engine (``tsi_sim``) is built from the engine's own lottery,
topology and block-tree functions, with every node's stake estimate held at the true stake.
That is the equilibrium uncle references give the inference (TSI report §3.2), and uncle
references never touch fork choice, so none are selected here (``max_uncles = 0``).

Measured over the blocks of the first ``1 - tail`` of the epoch, so that forks at the end of the
run have settled:

- ``orphan_share``: produced blocks off the final canonical chain;
- ``occupied_rate``: distinct occupied slots per slot (the lottery's ``f``, a sanity check);
- ``growth_rate``: canonical blocks per slot;
- ``vis_mean``, ``vis_full``: per block, the mean and the largest delay until a node holds it;
- ``depth_time[d]``: per canonical block, the slots until the canonical chain holds ``d`` blocks
  on top of it (``chain``), and until every node holds that ``d``-th block (``seen``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import make_stake

DEPTHS = (1, 10, 30, 100)


@dataclass
class EpochMeasure:
    orphan_share: float
    occupied_rate: float
    growth_rate: float
    n_blocks: int
    vis_mean: np.ndarray                 # per eligible block, slots
    vis_full: np.ndarray                 # per eligible block, slots
    depth_chain: dict[int, np.ndarray] = field(default_factory=dict)
    depth_seen: dict[int, np.ndarray] = field(default_factory=dict)


def build_epoch(config: SimConfig):
    """One epoch's global block tree and full arrival matrix, inference at the true stake."""
    if config.prune_arrival:
        raise ValueError("A1 needs the full arrival matrix: set prune_arrival=False")
    root = seedseq_for(config)
    c_stake, c_graph, c_lottery, c_aux = root.spawn(4)
    stake = make_stake(config, np.random.default_rng(c_stake))
    path_latency = topology.build_path_latency(config, np.random.default_rng(c_graph))
    d_est = np.full(config.n_nodes, float(stake.sum()))
    p = lottery.win_probs(stake, d_est, config.f)
    slots, nodes = lottery.sample_wins(p, config.epoch_len, np.random.default_rng(c_lottery))
    active, groups = lottery.group_by_slot(slots, nodes)
    tree, arrival = build_tree_pernode(active, groups, path_latency, config,
                                       np.random.default_rng(c_aux))
    return tree, arrival


def measure_epoch(tree, arrival: np.ndarray, epoch_len: int, tail: float = 0.1,
                  depths: tuple[int, ...] = DEPTHS) -> EpochMeasure:
    cut = int(epoch_len * (1.0 - tail))
    slot = tree.slot
    chain = np.asarray(tree.canonical_chain(), dtype=np.int64)[::-1]   # genesis-side first
    canonical = np.zeros(tree.n_blocks, dtype=bool)
    canonical[chain] = True

    eligible = (slot >= 0) & (slot < cut)
    ids = np.nonzero(eligible)[0]
    n = int(ids.size)
    orphan_share = 1.0 - canonical[ids].sum() / n
    occupied_rate = np.unique(slot[ids]).size / cut
    growth_rate = canonical[ids].sum() / cut

    delays = arrival[:, ids] - slot[ids][None, :]
    producer = tree.leader[ids]
    delays[producer, np.arange(n)] = np.nan               # a producer holds its block at once
    vis_mean = np.nanmean(delays, axis=0)
    vis_full = np.nanmax(delays, axis=0)

    full_by_block = np.full(tree.n_blocks, np.nan)
    full_by_block[ids] = vis_full
    tail_ids = np.nonzero(slot >= cut)[0]                  # canonical successors past the cut
    if tail_ids.size:
        d_tail = arrival[:, tail_ids] - slot[tail_ids][None, :]
        d_tail[tree.leader[tail_ids], np.arange(tail_ids.size)] = np.nan
        full_by_block[tail_ids] = np.nanmax(d_tail, axis=0)

    cs = slot[chain]
    base = np.nonzero(cs < cut)[0]
    depth_chain, depth_seen = {}, {}
    for d in depths:
        ok = base[base + d < chain.size]
        succ = chain[ok + d]
        depth_chain[d] = (slot[succ] - cs[ok]).astype(float)
        depth_seen[d] = slot[succ] + full_by_block[succ] - cs[ok]
    return EpochMeasure(orphan_share=float(orphan_share), occupied_rate=float(occupied_rate),
                        growth_rate=float(growth_rate), n_blocks=n, vis_mean=vis_mean,
                        vis_full=vis_full, depth_chain=depth_chain, depth_seen=depth_seen)


def run(config: SimConfig, tail: float = 0.1) -> EpochMeasure:
    tree, arrival = build_epoch(config)
    return measure_epoch(tree, arrival, config.epoch_len, tail)
