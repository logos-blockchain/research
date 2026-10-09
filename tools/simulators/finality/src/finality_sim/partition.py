"""A partition on the engine (SETTLEMENT.md B5, rule 8; PLAN.md I.3).

The network splits into two honest sides for a span of slots while a coalition withholds every
block it wins. At the span's end each side holds its own chain. Rule 8 compares densities over a
window: a side's density is the number of blocks of its chain with slots in the window, the
coalition's fork holds one block per slot it won there. The closed form of B5 takes each side's
blocks as binomial at the growth A1 measured for the whole network; the engine shows what a side
grows at on its own.
"""

from __future__ import annotations

import numpy as np
from tsi_sim.blocktree import tips_for_all_nodes
from tsi_sim.config import SimConfig

from finality_sim.race import partition_tree


def best_tip(tree, arrival: np.ndarray, nodes: np.ndarray, cutoff: int) -> int:
    """The best block any of ``nodes`` holds by ``cutoff``: highest, then earliest slot, then
    lowest id."""
    tips = np.unique(tips_for_all_nodes(tree, arrival[nodes], cutoff))
    order = np.lexsort((-tips, -tree.slot[tips], tree.height[tips]))
    return int(tips[order[-1]])


def chain_slots(tree, tip: int) -> np.ndarray:
    """The slots of the chain ending at ``tip``, genesis excluded."""
    out = []
    b = tip
    while b > 0:
        out.append(int(tree.slot[b]))
        b = int(tree.parent[b])
    return np.array(out, dtype=np.int64)


def measure(config: SimConfig) -> dict:
    """One partitioned run: each side's share of all stake, its chain's density over the span and
    its length at the span's end, the blocks its leaders made in the span, and the coalition's
    distinct winning slots there."""
    tree, arrival, stake, mask, side, public = partition_tree(config)
    start = int(config.partition_start)
    end = start + int(config.partition_slots)
    total = float(stake.sum())
    honest = ~mask
    sides = {"a": side, "b": honest & ~side}
    out = dict(alpha=float(stake[mask].sum() / total), span_slots=end - start)
    in_span = (tree.slot >= start) & (tree.slot < end)
    for name, nodes in sides.items():
        tip = best_tip(tree, arrival, np.nonzero(nodes)[0], end - 1)
        slots = chain_slots(tree, tip)
        out[f"share_{name}"] = float(stake[nodes].sum() / total)
        out[f"density_{name}"] = int(np.sum((slots >= start) & (slots < end)))
        out[f"length_{name}"] = int(tree.height[tip])
        made = public & in_span & nodes[tree.leader.clip(min=0)]
        out[f"made_{name}"] = int(made.sum())
    coalition = mask[tree.leader.clip(min=0)] & (tree.slot >= 0) & in_span
    out["fork"] = int(np.unique(tree.slot[coalition]).size)
    return out
