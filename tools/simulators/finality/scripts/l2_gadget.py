"""Phase L.2: Casper FFG run by Blend's declared nodes on the engine's chains (PLAN.md Phase L).

    python scripts/l2_gadget.py        # writes runs/l2/gadget.csv (about 5 minutes on 14 cores)

The A1 configuration of D6 (1,000 nodes, Pareto stake, 0.1 s links, one epoch at k = 256) at
testnet's Blend, the specification's and the heavy point, 4 replicates. Every node is a declared
node of weight one, and its votes are gossiped over the engine's peering graph without Blend: a
vote cast at t reaches node j at t + path_latency[i, j] (src/finality_sim/gadget.py). Rounds of 30,
60 and 600 slots from slot R to 90 % of the epoch; lags of 0, 10, 30 and 60 slots; the coalition's
declarations, a random share a of the nodes, withheld at a of 0, 0.25 and 0.3, so the honest votes
alone must carry two thirds of all declarations.

Per run: the rounds, the share justified and the share whose checkpoint was finalized; votes whose
best chain had to be restricted to the justified checkpoint; justified checkpoints off the
engine's final chain, and the round of the first (``first_off``, -1 if none): from it on, nodes
that follow the justified checkpoint stay on a branch the engine's longest-chain rule left, which
the engine does not model, so only runs without one are read. When each node holds two thirds of
the declarations' votes cast at once, at the median node, the 95th percentile and the last
(``quorum_*``). For each canonical block from slot 1,000 to 80 % of the epoch, the time from its
slot until each node holds it final; summaries over the blocks: the mean of the median node's time,
the 95th percentile of the 95th-percentile node's time, its largest value, and the blocks never
final; and the mean of the median node's time less L + (R − 1)/2 + R, the time an agreed chain
takes with votes delivered at once (``delivery``).
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim import topology
from tsi_sim.config import SimConfig
from tsi_sim.rng import seedseq_for

from finality_sim.baseline import build_epoch
from finality_sim.gadget import block_final_times, link_times, run_gadget

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "l2"
BLENDS = {"testnet": dict(blend_hops=1, blend_delay_max=1.0),
          "specification": dict(blend_hops=3, blend_delay_max=3.0),
          "heavy": dict(blend_hops=3, blend_delay_max=8.0)}
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", link_latency_mean=0.1, k=256, epochs=1, f=F, max_uncles=0,
            prune_arrival=False, blend_delay_dist="rounds")
ROUNDS = (30, 60, 600)
LAGS = (0, 10, 30, 60)
WITHHELD = (0.0, 0.25, 0.30)
REPLICATES = 4
FIRST = 1000


def one(blend: str, rep: int) -> list[dict]:
    cfg = SimConfig(**BASE, **BLENDS[blend], replicate=rep)
    tree, arrival = build_epoch(cfg)
    delay = topology.build_path_latency(cfg, np.random.default_rng(seedseq_for(cfg).spawn(4)[1]))
    n = cfg.n_nodes
    chain = np.asarray(tree.canonical_chain(), dtype=np.int64)[::-1]
    s = tree.slot[chain]
    blocks = chain[(s >= FIRST) & (s <= 0.8 * cfg.epoch_len)]
    rng = np.random.default_rng([rep, 12, len(blend)])
    order = rng.permutation(n)
    tips: dict = {}
    rows = []
    for R in ROUNDS:
        rounds = np.arange(R, int(0.9 * cfg.epoch_len), R)
        for lag in LAGS:
            for a in WITHHELD:
                voters = np.sort(order[int(round(a * n)):])
                quorum = link_times(delay, voters, 0.0, math.ceil(2 / 3 * n - 1e-9))
                run = run_gadget(tree, arrival, delay, voters, rounds, lag, n, tips_cache=tips)
                t = block_final_times(tree, run, blocks) - tree.slot[blocks][:, None]
                done = np.isfinite(t).all(axis=1)
                p50 = np.median(t[done], axis=1) if done.any() else np.full(1, np.nan)
                p95 = np.percentile(t[done], 95, axis=1) if done.any() else np.full(1, np.nan)
                finalized = sum(c.final is not None for c in run.checkpoints[1:])
                rows.append(dict(
                    blend=blend, replicate=rep, round_slots=R, lag=lag, withheld=a,
                    rounds=len(rounds), justified=run.justified_rounds / len(rounds),
                    finalized=finalized / len(rounds), restricted=run.restricted,
                    off_chain=run.off_chain, first_off=run.first_off,
                    conflicts=run.conflicts, blocks=int(blocks.size),
                    never_final=int((~done).sum()), quorum_p50=float(np.median(quorum)),
                    quorum_p95=float(np.percentile(quorum, 95)), quorum_max=float(quorum.max()),
                    mean_p50=float(p50.mean()),
                    p95_p95=float(np.percentile(p95, 95)), max_p95=float(p95.max()),
                    delivery=float(p50.mean() - (lag + (R - 1) / 2 + R))))
    return rows


def main() -> None:
    parts = Parallel(n_jobs=-2)(delayed(one)(b, r) for b in BLENDS for r in range(REPLICATES))
    df = pd.DataFrame([x for p in parts for x in p])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "gadget.csv", index=False)
    g = df.groupby(["blend", "round_slots", "lag", "withheld"], sort=False)
    print(g.agg(justified=("justified", "min"), finalized=("finalized", "min"),
                off=("off_chain", "sum"), restricted=("restricted", "sum"),
                never=("never_final", "sum"), mean_p50=("mean_p50", "mean"),
                p95=("p95_p95", "max"), worst=("max_p95", "max")).round(2).to_string())


if __name__ == "__main__":
    main()
