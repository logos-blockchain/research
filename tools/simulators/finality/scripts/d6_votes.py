"""Phase D6: votes on the engine's chains (PLAN.md D6).

    python scripts/d6_votes.py        # writes runs/d6/{agreement,certificates}.csv

The A1 configuration (1,000 nodes, Pareto stake, 0.1 s links, one epoch at k = 256) at testnet's
Blend (1 hop, 1 round), the specification's (3 hops, up to 3 rounds) and the heavy point
(3 hops, up to 8 rounds), 4 replicates. A round starts every 600 slots after slot 1,000.

- agreement: for each lag L, the stake share of nodes whose vote target is the most common one.
- certificates: the committee of D0 for an adversary holding alpha at eps = 1e-9 per round, the
  adversary's seats withheld. Honest seats are Poisson with the expectation (1 - alpha) n times the
  node's share of honest stake. A vote reaches each node as a block from its sender would. The
  time from the round's start until a node holds the quorum, and the share of rounds in which
  every node does.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim import topology
from tsi_sim.config import SimConfig
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import make_stake

from finality_sim.baseline import build_epoch
from finality_sim.committee import smallest_committee
from finality_sim.votes import certificate_times, local_tips, vote_targets

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "d6"
BLENDS = {"testnet": dict(blend_hops=1, blend_delay_max=1.0),
          "specification": dict(blend_hops=3, blend_delay_max=3.0),
          "heavy": dict(blend_hops=3, blend_delay_max=8.0)}
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", link_latency_mean=0.1, k=256, epochs=1, f=F, max_uncles=0,
            prune_arrival=False, blend_delay_dist="rounds")
LAGS = (0, 30, 60, 120, 300)
ALPHAS = (0.10, 0.25)
EPS = 1e-9
FIRST, EVERY = 1000, 600
REPLICATES = 4


def one(blend: str, rep: int) -> tuple[list[dict], list[dict]]:
    cfg = SimConfig(**BASE, **BLENDS[blend], replicate=rep)
    tree, arrival = build_epoch(cfg)
    stake = make_stake(cfg, np.random.default_rng(seedseq_for(cfg).spawn(4)[0]))
    share = stake / stake.sum()
    path_latency = topology.build_path_latency(cfg, np.random.default_rng(
        seedseq_for(cfg).spawn(4)[1]))
    rng = np.random.default_rng([rep, 6, len(blend)])
    committees = {a: smallest_committee(a, EPS) for a in ALPHAS}
    agree, certs = [], []
    for t in range(FIRST, int(cfg.epoch_len * 0.9), EVERY):
        tips = local_tips(tree, arrival, float(t))
        targets = {lag: vote_targets(tree, tips, float(t), lag) for lag in LAGS}
        for lag, tg in targets.items():
            w = np.bincount(tg, weights=share)
            agree.append(dict(blend=blend, replicate=rep, round=t, lag=lag,
                              agreement=float(w.max())))
        vote_arrival = np.stack([topology.arrival_column(path_latency, i, t, cfg, rng)
                                 for i in range(cfg.n_nodes)])
        for a, (n, q) in committees.items():
            seats = rng.poisson((1 - a) * n * share)
            for lag in (60, 120):
                c = certificate_times(vote_arrival, seats, targets[lag], q) - t
                certs.append(dict(blend=blend, replicate=rep, round=t, alpha=a, seats=n,
                                  quorum=q, lag=lag, all_certified=bool(np.isfinite(c).all()),
                                  p50=float(np.percentile(c, 50)),
                                  p95=float(np.percentile(c, 95))))
    return agree, certs


def main() -> None:
    parts = Parallel(n_jobs=-2)(delayed(one)(b, r) for b in BLENDS for r in range(REPLICATES))
    agree = pd.DataFrame([x for p in parts for x in p[0]])
    certs = pd.DataFrame([x for p in parts for x in p[1]])
    OUT.mkdir(parents=True, exist_ok=True)
    agree.to_csv(OUT / "agreement.csv", index=False)
    certs.to_csv(OUT / "certificates.csv", index=False)
    g = agree.groupby(["blend", "lag"], sort=False).agreement
    print(pd.DataFrame({"mean": g.mean(), "p1": g.quantile(0.01), "min": g.min()}).round(4))
    c = certs.copy()
    c["p50"] = c.p50.where(np.isfinite(c.p50))
    print(c.groupby(["blend", "alpha", "lag"], sort=False).agg(
        rounds=("all_certified", "size"), certified=("all_certified", "mean"),
        p50=("p50", "median"), p95=("p95", "median")).round(3))


if __name__ == "__main__":
    main()
