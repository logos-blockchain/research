"""Which blocks make a validator wait under the depth-2 rule? (PLAN.md Phase 2d)

``reroot_analysis.py`` reads the wait from the per-epoch columns of a run. This script finds the
epochs of the run's depth-2 arm in which a node receives a canonical window block before an
off-chain parent of its entries. It re-runs those trajectories on the full arrival matrix, which
gives the same tree, and checks that each such epoch reproduces the run's node share. It then
lists each block that makes a node wait: its slot and leader, and the nodes that wait and for how
long. For each off-chain parent it lists the parent's slot and leader, whether the block itself
carries the parent as an entry, the entries built on it, and the nodes it makes wait.

Run:  python scripts/parent_wait_blocks.py runs/<dir> configs/reroot-overload-paired.yaml
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pandas as pd

import tsi_sim.fork as fork
from tsi_sim.blocktree import _off_chain_parents
from tsi_sim.engine import run_trajectory
from tsi_sim.sweep import load_sweep_yaml

CELL = ["blend_delay_max", "max_uncles", "replicate"]


def main() -> None:
    run, sweep = Path(sys.argv[1]), Path(sys.argv[2])
    df = pd.read_parquet(run / "results.parquet")
    deep = df[(df.uncle_depth == 2) & (df.reroot_share == 0.0)]
    waits = deep[deep.parent_wait_node_share > 0]
    cfgs = {(c.blend_delay_max, c.max_uncles, c.replicate): c
            for c in load_sweep_yaml(sweep).expand()
            if c.uncle_depth == 2 and c.reroot_share == 0.0}
    print(f"{len(waits)} of {len(deep)} depth-2 epochs make a node wait, in "
          f"{waits.groupby(CELL).ngroups} of {deep.groupby(CELL).ngroups} trajectories")

    seen: list = []
    aggregate = fork.parent_wait

    def capture(tree, A, T, cutoff, n_nodes):
        seen.append((tree, A, T, cutoff))
        return aggregate(tree, A, T, cutoff, n_nodes)

    fork.parent_wait = capture
    for cell, rows in waits.groupby(CELL):
        seen.clear()
        out = run_trajectory(dataclasses.replace(cfgs[cell], prune_arrival=False))
        for epoch, share in zip(rows.epoch, rows.parent_wait_node_share, strict=True):
            assert out[epoch]["parent_wait_node_share"] == share, "the re-run must reproduce"
            tree, A, T, cutoff = seen[epoch]
            canonical, _ = fork.canonical_and_depth(tree, A, cutoff)
            print(f"\ndelay {cell[0]:g}, U = {cell[1]}, replicate {cell[2]}, epoch {epoch}")
            for b in range(1, tree.n_blocks):
                if not (canonical[b] and 0 <= tree.slot[b] < T and tree.parent_wait[b, 0] > 0):
                    continue
                late, total, longest = tree.parent_wait[b]
                print(f"  block {b}, slot {tree.slot[b]}, leader {tree.leader[b]}: {late:.0f} of "
                      f"{A.shape[0]} nodes wait, {total / late:.2f} slots on average, "
                      f"{longest:.2f} at most")
                for u in _off_chain_parents(b, tree.uncles[b], tree.ref_parent, tree.ref_slot):
                    wait = A[:, u] - A[:, b]
                    on = [e for e in tree.uncles[b] if tree.ref_parent[e] == u]
                    print(f"    parent {u}, slot {tree.slot[u]}, leader {tree.leader[u]}, "
                          f"{'carried by the block' if u in tree.uncles[b] else 'not carried'}; "
                          f"entries on it {on}, leaders {[int(tree.leader[e]) for e in on]}; "
                          f"{(wait > 0).sum()} nodes wait, {max(wait.max(), 0.0):.2f} at most")


if __name__ == "__main__":
    main()
