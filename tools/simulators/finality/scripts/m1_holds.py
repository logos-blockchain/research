"""Phase M.1: what each signer set holds (PLAN.md Phase M).

    python scripts/m1_holds.py      # needs runs/d0; writes runs/m1/{anonymous,public,delegation}.csv

anonymous.csv, per coalition share at 1e-9 a round: D0 and D2's committee of anonymous seats with
every honest seat counting, with the inference's error up to 1.05, and with a tenth of the honest
votes lost (runs/d0/emission_map.csv); and the counted committee of the chain's own leaders, in
wins and in the hours the chain takes to record them, with every honest leader online, with 95 %
online and with 90 % (src/finality_sim/signers.py).

public.csv, per coalition share: the share of the honest stake an opt-in set needs declared, at
full uptime and at 0.95 (D1b); and for every leading note declared, the least share of the honest
stake online, the coalition's share of the weight and that least uptime when 5 % of the honest
stake lies below SDP's minimum stake and cannot declare, and the share below the minimum at which
the set fails at full uptime.

delegation.csv, per coalition share and uptime of the honest operators' weight: the share of the
honest stake below which the coalition's operators may hold delegation with every note
delegating, and how many of the largest holders hold that share if the honest stake is spread as
Cardano's pools are (D1b's data/cardano_pool_stakes.csv).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim import committee as cm
from finality_sim import signers as sg
from finality_sim.privacy import holders_needed, volunteer_share

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "m1"
EPS = 1e-9
SHARES = (("10 %", 0.10), ("25 %", 0.25), ("30 %", 0.30), ("a third", 1 / 3))
UPTIMES = (1.0, 0.95, 0.9)
BELOW_MINIMUM = 0.05


def committee(d0: pd.DataFrame, alpha: float, awake: float, inflation: float) -> float:
    """D0's committee from its map, or the closed condition where the map has no row."""
    row = d0[(abs(d0.alpha - alpha) < 1e-9) & (d0.awake == awake)
             & (d0.inflation == inflation) & (d0.eps == EPS)]
    if row.empty:
        found = cm.smallest_committee(alpha, EPS, awake, inflation)
        return float(found[0]) if found else math.nan
    return float(row.seats.iloc[0])


def counted(alpha: float, uptime: float) -> float:
    found = sg.known_committee(alpha, EPS, uptime)
    return float(found[0]) if found else math.nan


def main() -> None:
    d0 = pd.read_csv(HERE / "runs" / "d0" / "emission_map.csv")
    stakes = pd.read_csv(HERE / "data" / "cardano_pool_stakes.csv").stake.to_numpy()
    rows = []
    for name, a in SHARES:
        w1, w95, w9 = counted(a, 1.0), counted(a, 0.95), counted(a, 0.9)
        rows.append(dict(share=name, alpha=a, seats_all=committee(d0, a, 1.0, 1.0),
                         seats_inflated=committee(d0, a, 1.0, 1.05),
                         seats_lost=committee(d0, a, 0.9, 1.0),
                         wins_u1=w1, window_u1_h=sg.leaders_window(w1) / 3600,
                         wins_u095=w95, window_u095_h=sg.leaders_window(w95) / 3600,
                         wins_u09=w9, window_u09_h=sg.leaders_window(w9) / 3600))
    anonymous = pd.DataFrame(rows)

    rows = []
    for name, a in SHARES:
        safe = a < 1 / 3 - 1e-12
        below = sg.delegated_share(a, 1 - BELOW_MINIMUM, 0.0)
        v = volunteer_share(a, 1.0)
        rows.append(dict(share=name, alpha=a, optin_u1=volunteer_share(a, 1.0),
                         optin_u095=volunteer_share(a, 0.95),
                         declared_least_uptime=sg.least_uptime(a) if safe else math.inf,
                         below_share=below,
                         below_least_uptime=(sg.least_uptime(below) if below < 1 / 3 - 1e-12
                                             else math.inf),
                         below_breaks=1 - v if math.isfinite(v) else 0.0))
    public = pd.DataFrame(rows)

    rows = []
    for name, a in SHARES:
        for u in UPTIMES:
            c = sg.largest_attracted(a, u)
            rows.append(dict(share=name, alpha=a, uptime=u,
                             attracted=c if c is not None else math.nan,
                             pools=(holders_needed(stakes, c) if c and c > 0
                                    else (0 if c is not None else None)),
                             of_pools=len(stakes)))
    delegation = pd.DataFrame(rows)

    OUT.mkdir(parents=True, exist_ok=True)
    for stale in ("holds.csv",):
        (OUT / stale).unlink(missing_ok=True)
    anonymous.to_csv(OUT / "anonymous.csv", index=False)
    public.to_csv(OUT / "public.csv", index=False)
    delegation.to_csv(OUT / "delegation.csv", index=False)
    print(anonymous.to_string(index=False), end="\n\n")
    print(public.to_string(index=False), end="\n\n")
    print(delegation.to_string(index=False))


if __name__ == "__main__":
    main()
