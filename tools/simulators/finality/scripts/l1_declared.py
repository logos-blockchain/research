"""Phase L.1: what Blend's declared set holds against a stake coalition (PLAN.md Phase L).

    python scripts/l1_declared.py        # writes runs/l1/{today,frontier,convention}.csv

The coalition holds ``alpha`` of the active stake ``D`` and locks all of it in service notes
(src/finality_sim/netcert.py). The minimum-stake analysis' parameters: a minimum stake of 0.001 %
of the supply, its cap of 0.015 %, a network of 1,000 nodes, and the block rewards' target of 30 %
of the supply staked.

- today: for each minimum stake, 1,000 honest declarations locking it, the largest coalition held
  at uptimes of 1, 0.95 and 0.9, and the coalition's declarations and stake at a third of the
  declared weight;
- frontier: for each coalition share, the honest declared stake the quorum needs, as a share of
  the active stake and of the honest stake, the honest declarations that is at today's minimum
  stake, and the minimum stake that makes 1,000 honest declarations lock it;
- convention: the largest coalition share of the declared weight held at each uptime, which under
  the study's convention is its share of the stake.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim import netcert as nc

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "l1"
ALPHAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
UPTIMES = (1.0, 0.95, 0.9)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    today = []
    for name, share in (("minimum", nc.MIN_STAKE_SHARE), ("cap", nc.CAP_SHARE)):
        locked = nc.SMALL_NETWORK * share / nc.STAKED_SHARE          # of the active stake
        row = dict(min_stake=name, min_stake_supply=share, min_stake_lgo=share * nc.SUPPLY,
                   honest_locked_active=locked)
        for u in UPTIMES:
            row[f"alpha_u{u}"] = nc.largest_alpha_held(locked, u)
        third = nc.SMALL_NETWORK // 2                                # 500 against 1,000 honest
        row["third_declarations"] = third
        row["third_stake_supply"] = third * share
        row["third_stake_active"] = third * share / nc.STAKED_SHARE
        today.append(row)
    pd.DataFrame(today).to_csv(OUT / "today.csv", index=False)

    frontier = []
    for a in ALPHAS:
        row = dict(alpha=a)
        for u in UPTIMES:
            row[f"locked_u{u}"] = nc.honest_locked_needed(a, u)
        x = row["locked_u1.0"]
        row["of_honest_u1"] = x / (1 - a)
        row["nodes_at_min_u1"] = x * nc.STAKED_SHARE / nc.MIN_STAKE_SHARE
        row["min_stake_multiple_u1"] = x * nc.STAKED_SHARE / nc.SMALL_NETWORK / nc.MIN_STAKE_SHARE
        frontier.append(row)
    pd.DataFrame(frontier).to_csv(OUT / "frontier.csv", index=False)

    conv = [dict(uptime=u, largest_share=nc.largest_share_held(u),
                 strict=nc.largest_share_held(u) == 2 * nc.Q - 1) for u in UPTIMES]
    pd.DataFrame(conv).to_csv(OUT / "convention.csv", index=False)
    for f in ("today", "frontier", "convention"):
        print(pd.read_csv(OUT / f"{f}.csv").to_string(index=False))
    assert all(math.isfinite(r["alpha_u1.0"]) for r in today)


if __name__ == "__main__":
    main()
