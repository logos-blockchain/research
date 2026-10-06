"""Phase D1b: the share of the stake an opt-in public committee needs (PLAN.md D1b).

    python scripts/d1b_committee.py      # writes runs/d1b/committee.csv

The share of the honest stake that must declare, against an adversary that declares all of its
own, at uptimes of 1, 0.95 and 0.9 of the declared honest stake (src/finality_sim/privacy.py). And
how many of the largest holders that takes if the honest stake is spread as Cardano's pool stakes
are: data/cardano_pool_stakes.csv, the stake column of pools.csv from logos-lips @ 47a73cdc,
docs/blockchain/raw/analysis-cryptarchia-de-anonymisation-of-relative-stake/appendices (sha256
48661bb72645fc98e8a69f46472270c19925b43b275a0d02971ebe25a74f7aaf), drawn from Cexplorer as that
analysis states.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim.privacy import holders_needed, volunteer_share

HERE = pathlib.Path(__file__).resolve().parent.parent
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
UPTIMES = (1.0, 0.95, 0.9)


def main() -> None:
    stakes = pd.read_csv(HERE / "data" / "cardano_pool_stakes.csv").stake.to_numpy()
    rows = []
    for a in ALPHAS:
        for u in UPTIMES:
            v = volunteer_share(a, u)
            rows.append(dict(alpha=round(a, 4), uptime=u, honest_share=v,
                             declared_share=a + v * (1 - a) if math.isfinite(v) else math.inf,
                             holders=holders_needed(stakes, v) if math.isfinite(v) else None,
                             of_holders=len(stakes)))
    t = pd.DataFrame(rows)
    out = HERE / "runs" / "d1b"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "committee.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
