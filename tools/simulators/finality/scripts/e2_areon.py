"""Phase E1, E2: Areon-Base on Cryptarchia's lottery and Blend (PLAN.md E).

    python scripts/e2_areon.py        # writes runs/e2/{structure,race}.csv

The production coefficient f_A runs from Cryptarchia's 1/30 to the paper's 0.25. Each epoch holds
about 20,000 slots (k = 2000 f_A); 1,000 nodes, 0.1 s links. The window is the paper's w = 30 at
f_A = 0.25, stretched with the block interval, w = 7.5 / f_A, so that it always spans about eight
blocks; the structure runs also keep w = 30 at every f_A.

structure: Pareto stake, testnet's Blend (1 hop, 1 round), the specification's (3 hops, up to 3
rounds) and the heavy point (3 hops, up to 8 rounds), 4 replicates: honest blocks and layers per
slot, the tips each block references, and the share of blocks with only a long reference.

race: equal stake, a coalition holding alpha withholds its wins; testnet's and the
specification's Blend, 16 * 0.25 / f_A replicates (about 60,000 targets per point). The private
race of src/finality_sim/areon.py with premining. The weight is counted since the fork, with a
strictly heavier coalition and with ties to it; honest blocks that do not descend from the target
count for neither side, and, as a variant, for the honest side. Last, the weight of the last w
slots only.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.areon import build_dag, dag_race

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "e2"
PAPER_WINDOW = 30


def window(f: float) -> int:
    return round(PAPER_WINDOW * 0.25 / f)


FS = (1 / 30, 1 / 20, 1 / 15, 0.1, 0.25)
BLENDS = {"testnet": dict(blend_hops=1, blend_delay_max=1.0),
          "specification": dict(blend_hops=3, blend_delay_max=3.0),
          "heavy": dict(blend_hops=3, blend_delay_max=8.0)}
ALPHAS = (0.10, 0.25, 1 / 3)
K_MAX = 60
BASE = dict(n_nodes=1000, topology="blend", degree=6, link_latency_dist="geo",
            link_latency_mean=0.1, epochs=1, max_uncles=0, prune_arrival=False,
            blend_delay_dist="rounds")


def config(f: float, blend: str, rep: int, **kw) -> SimConfig:
    return SimConfig(**BASE, **BLENDS[blend], f=f, k=max(16, round(2000 * f)), replicate=rep,
                     **kw)


def structure(f: float, blend: str, rep: int, w: int) -> dict:
    cfg = config(f, blend, rep, stake_dist="pareto")
    d = build_dag(cfg, w)
    body = slice(d.n_blocks // 10, d.n_blocks)                      # skip the first tenth
    span = d.slot[-1] - d.slot[d.n_blocks // 10]
    refs = d.tips_seen[body][~d.long_ref[body]]
    return dict(f=f, blend=blend, window=w, replicate=rep, blocks_per_slot=(d.n_blocks - d.n_blocks // 10) / span,
                layers_per_slot=(d.height[-1] - d.height[d.n_blocks // 10]) / span,
                refs_mean=float(refs.mean()), refs_p99=float(np.percentile(refs, 99)),
                long_ref_share=float(d.long_ref[body].mean()))


def race_point(f: float, blend: str, alpha: float, rep: int) -> list[dict]:
    cfg = config(f, blend, rep, stake_dist="uniform", adversary_frac=alpha,
                 adversary_strategy="withhold")
    w = window(f)
    d = build_dag(cfg, w)
    first = d.n_blocks // 10
    span = d.slot[-1] - d.slot[first]
    rows = []
    for horizon, recent, win_at, desc in (
            ("since the fork", None, 1, True),
            ("since the fork, ties to the attacker", None, 0, True),
            ("since the fork, concurrent blocks honest", None, 1, False),
            ("last w slots", w, 1, False)):
        succ, scored = dag_race(d, K_MAX, w, premine=True, win_at=win_at, recent=recent,
                                first=first, descendants_only=desc)
        rows.append(dict(f=f, blend=blend, window=w, alpha=round(alpha, 4), replicate=rep,
                         horizon=horizon,
                         scored=scored, honest_per_slot=(d.n_blocks - first) / span,
                         layers_per_slot=(d.height[-1] - d.height[first]) / span,
                         adv_per_slot=d.adv_slots.size / cfg.epoch_len,
                         **{f"s{k}": int(succ[k - 1]) for k in range(1, K_MAX + 1)}))
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    st = Parallel(n_jobs=-2)(delayed(structure)(f, b, r, w) for f in FS for b in BLENDS
                             for w in sorted({PAPER_WINDOW, window(f)}) for r in range(4))
    s = pd.DataFrame(st)
    s.to_csv(OUT / "structure.csv", index=False)
    print(s.groupby(["f", "blend", "window"], sort=False).mean(numeric_only=True).round(4),
          end="\n\n")
    rr = Parallel(n_jobs=-2)(delayed(race_point)(f, b, a, r) for f in FS
                             for b in ("testnet", "specification") for a in ALPHAS
                             for r in range(round(16 * 0.25 / f)))
    r = pd.DataFrame([x for p in rr for x in p])
    r.to_csv(OUT / "race.csv", index=False)
    g = r.groupby(["f", "blend", "alpha", "horizon"], sort=False).sum(numeric_only=True)
    for k in (5, 10, 20, 40):
        g[f"p{k}"] = g[f"s{k}"] / g.scored
    print(g[["scored", "p5", "p10", "p20", "p40"]])


if __name__ == "__main__":
    main()
