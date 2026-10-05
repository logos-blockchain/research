"""Phase B3: the private-chain attack on the engine's timelines (PLAN.md B3).

    python scripts/b3_race.py            # writes runs/b3/{curves.csv,orphans.csv}

For three delay configurations (testnet-like, the specification's Blend, the TSI report's heavy
point) and attacker shares 0.10-0.30: 64 engine runs with a withholding coalition, each one
epoch at k = 256 (about 2,560 slots won). Stake is equal across nodes: under the Pareto draw a
random coalition cannot always reach its share (the engine warns, and one replicate realised 0.106
for 0.30), while the stake split does not change the honest dynamics (TSI report §2). On every run the race of ``finality_sim.race`` is
played for each canonical block, with and without premining, and with ties to the first-seen
chain (Cryptarchia's rule) or to the attacker. Depths 1..60.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.race import race, withhold_timelines

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "b3"
REPLICATES = 64
K_MAX = 60
CONFIGS = {
    "testnet": dict(blend_hops=1, blend_delay_max=1.0, blend_delay_dist="rounds",
                    link_latency_mean=0.1),
    "spec": dict(blend_hops=3, blend_delay_max=3.0, blend_delay_dist="rounds",
                 link_latency_mean=0.1),
    "heavy": dict(blend_hops=3, blend_delay_max=8.0, blend_delay_dist="continuous",
                  link_latency_mean=0.5),
}
ALPHAS = (0.10, 0.20, 0.25, 0.30)
BASE = dict(n_nodes=1000, stake_dist="uniform", topology="blend", degree=6,
            link_latency_dist="geo", k=256, epochs=1, f=1 / 30, max_uncles=0,
            prune_arrival=False, adversary_strategy="withhold")


def one(name: str, alpha: float, rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS[name], adversary_frac=alpha, replicate=rep)
    canon, adv, orphan = withhold_timelines(cfg)
    out = dict(config=name, alpha=alpha, replicate=rep, orphan=orphan,
               canonical=int(canon.size), adversary_slots=int(adv.size))
    for premine in (True, False):
        for win_at in (1, 0):
            succ, scored = race(canon, adv, K_MAX, premine=premine, win_at=win_at)
            out[f"succ_p{int(premine)}_w{win_at}"] = succ
            out[f"scored_p{int(premine)}_w{win_at}"] = scored
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(n, a, r) for n in CONFIGS for a in ALPHAS for r in range(REPLICATES)]
    rows = Parallel(n_jobs=-2, backend="loky")(delayed(one)(*j) for j in jobs)
    curves, orphans = [], []
    for (name, alpha), grp in pd.DataFrame(rows).groupby(["config", "alpha"], sort=False):
        orphans.append(dict(config=name, alpha=alpha, orphan=grp.orphan.mean(),
                            orphan_sem=grp.orphan.std(ddof=1) / np.sqrt(len(grp)),
                            canonical=int(grp.canonical.sum()),
                            adversary_slots=int(grp.adversary_slots.sum())))
        for premine in (1, 0):
            for win_at in (1, 0):
                succ = np.sum(np.stack(grp[f"succ_p{premine}_w{win_at}"].to_list()), axis=0)
                scored = int(grp[f"scored_p{premine}_w{win_at}"].sum())
                for k in range(1, K_MAX + 1):
                    curves.append(dict(config=name, alpha=alpha, premine=premine, win_at=win_at,
                                       depth=k, successes=int(succ[k - 1]), scored=scored,
                                       p=succ[k - 1] / scored))
    pd.DataFrame(curves).to_csv(OUT / "curves.csv", index=False)
    o = pd.DataFrame(orphans)
    o.to_csv(OUT / "orphans.csv", index=False)
    print(o.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
