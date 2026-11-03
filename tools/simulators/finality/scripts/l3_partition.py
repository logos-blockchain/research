"""Phase L.3: a partition on the engine, with the coalition signing on both sides (PLAN.md Phase L).

    python scripts/l3_partition.py        # writes runs/l3/partition.csv (a few minutes on 12 cores)

B3's configuration on the specification's Blend (1,000 nodes of equal stake, one epoch at
k = 256), with the engine's partition mode (I.3): from slot 3,000, for two hours, the honest nodes
are split into a side holding a share s of them and the rest; a block or a vote cast on one side
reaches the other at the span's end plus the path latency. Every node is an honest declaration of
weight one. The coalition holds c further declarations, a share a = c/(1,000 + c) of the declared
weight, and signs every link either side casts (src/finality_sim/gadget.py). Rounds of 60 slots,
a lag of 30, a quorum of two thirds.

Per run: the rounds of the span whose justified checkpoint lies on each side's branch, those
finalized, the rounds that justified both sides, and the conflicting pairs of finalized
checkpoints, beside the closed form's verdict for each side, u·h + a ≥ q at full uptime
(src/finality_sim/netcert.py).
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim import topology
from tsi_sim.config import SimConfig
from tsi_sim.rng import seedseq_for

from b3_race import BASE, CONFIGS
from finality_sim import netcert as nc
from finality_sim.gadget import run_gadget
from finality_sim.race import partition_tree

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "l3"
START, SPAN = 3000, 7200
R, LAG = 60, 30
SIDES = (0.30, 0.50, 0.60)
SHARES = (0.25, 0.30, 0.34)
REPLICATES = 4


def one(s: float, a: float, rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=0.0, replicate=rep,
                    partition_share=s, partition_start=START, partition_slots=SPAN)
    tree, arrival, _, _, side, _ = partition_tree(cfg)
    delay = topology.build_path_latency(cfg, np.random.default_rng(seedseq_for(cfg).spawn(4)[1]))
    n = cfg.n_nodes
    c = int(round(a / (1 - a) * n))
    end = START + SPAN
    across = side[:, None] != side[None, :]

    def cut(t: float):
        if not START <= t < end:
            return None
        return np.where(across, end + delay, np.inf)

    rounds = np.arange(R, START + SPAN + 20 * R, R)
    run = run_gadget(tree, arrival, delay, np.arange(n), rounds, LAG, n + c, coalition=c, cut=cut)
    leader_side = np.where(tree.leader >= 0, side[tree.leader.clip(min=0)], False)

    def branch(b: int) -> str:
        while b > 0 and tree.slot[b] >= START:
            if tree.slot[b] < end:
                return "side" if leader_side[b] else "rest"
            b = int(tree.parent[b])
        return "before"

    span = [c_ for c_ in run.checkpoints[1:] if START <= run.rounds[c_.round - 1] < end]
    count = {k: sum(branch(c_.block) == k for c_ in span) for k in ("side", "rest", "before")}
    final = {k: sum(branch(c_.block) == k and c_.final is not None for c_ in span)
             for k in ("side", "rest")}
    h_side = float(side.sum()) / (n + c)
    h_rest = float(n - side.sum()) / (n + c)
    share = c / (n + c)
    return dict(side_share=s, coalition_share=round(share, 4), coalition=c, replicate=rep,
                side_nodes=int(side.sum()), span_rounds=SPAN // R,
                side_justified=count["side"], rest_justified=count["rest"],
                before_justified=count["before"], side_finalized=final["side"],
                rest_finalized=final["rest"], both_rounds=run.conflicts,
                finalized_conflicts=run.finalized_conflicts,
                side_closed_form=nc.side_certifies(h_side, share),
                rest_closed_form=nc.side_certifies(h_rest, share))


def main() -> None:
    rows = Parallel(n_jobs=-2)(delayed(one)(s, a, r) for s in SIDES for a in SHARES
                               for r in range(REPLICATES))
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "partition.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
