#!/usr/bin/env python
"""Per-node clock skew: does a whole-timeline slot-clock offset break consensus? (report §6.1).

Unlike per-arrival jitter (which leaves range_ratio EXACTLY 0, §6.1), a constant per-node clock
offset shifts each node's measurement window by δ_i slots, so nodes count different blocks in the
boundary slots and their occupied-slot counts differ. We build one honest finalized tree, then for
each node evaluate its occupied-slot density over its OWN shifted window [δ_i, T+δ_i), and report
the resulting inter-node spread vs skew. Bound: |Δm|/m ≲ 2·skew/T, so the effect is O(skew/T) —
tiny at the production window (T ≈ 4.3e5 slots) but, unlike jitter, not exactly zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from tsi_sim import lottery
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.topology import build_path_latency

SKEWS = (0, 1, 2, 5, 10, 20)


def build_honest_tree(cfg: SimConfig, seed: int):
    rng = np.random.default_rng(seed)
    stake = np.random.default_rng(seed + 1).random(cfg.n_nodes) + 0.1
    d_est = np.full(cfg.n_nodes, float(stake.sum()))
    pl = build_path_latency(cfg, np.random.default_rng(seed + 2))
    p = lottery.win_probs(stake, d_est, cfg.f)
    ws, wn = lottery.sample_wins(p, cfg.epoch_len, np.random.default_rng(seed + 3))
    active, groups = lottery.group_by_slot(ws, wn)
    tree, _A = build_tree_pernode(active, groups, pl, cfg, rng)
    return tree


def occupied_slots(tree, T: int, lo: int) -> int:
    """Occupied canonical+uncle slots in the window [lo, lo+T) (one count per slot)."""
    nb = tree.n_blocks
    ids = np.arange(nb)
    h = tree.height.copy()
    best = int(np.lexsort((-ids, -tree.slot, h))[-1])
    canon = []
    b = best
    while b > 0:
        canon.append(b)
        b = int(tree.parent[b])
    occ = set()
    for b in canon:
        s = int(tree.slot[b])
        if lo <= s < lo + T:
            occ.add(s)
    for b in canon:
        for u in tree.uncles[b]:
            su = int(tree.slot[u])
            if lo <= su < lo + T and su not in occ:
                occ.add(su)
    return len(occ)


def main() -> None:
    cfg = SimConfig(n_nodes=400, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=8.0, max_uncles=2, uncle_window=300, k=256, epochs=1)
    T = cfg.period_T
    print(f"window T = {T} slots (k={cfg.k}); production k=2160 -> T≈{6 * int(2160 / cfg.f):.0e}")
    tree = build_honest_tree(cfg, seed=20260724)
    m0 = occupied_slots(tree, T, 0)
    print(f"baseline occupied slots m0 = {m0}")
    print("skew (slots) | inter-node range(m)/m0 | bound 2·skew/T")
    for skew in SKEWS:
        if skew == 0:
            print(f"{skew:>4}          | 0.000000              | 0")
            continue
        rng = np.random.default_rng(7)
        offs = rng.integers(-skew, skew + 1, size=cfg.n_nodes)
        ms = np.array([occupied_slots(tree, T, int(o)) for o in offs])
        rng_ratio = (ms.max() - ms.min()) / m0
        print(f"{skew:>4}          | {rng_ratio:.6f}              | {2 * skew / T:.6f}")
    print("\nInterpretation: the spread is O(skew/T) — bounded and vanishing at the production "
          "window, but (unlike per-arrival jitter) not exactly 0, so bounded clock skew is a "
          "small, quantifiable consensus cost, not a break.")


if __name__ == "__main__":
    main()
