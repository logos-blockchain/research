"""Phase M.5: what a quorum withstands (PLAN.md Phase M).

    python scripts/m5_quorum.py     # writes runs/m5/quorum.csv

For Casper FFG's quorum of two thirds and Ouroboros Peras's of three quarters (CIP-0140,
`τ > 3n/4`): the coalition's share of the signing weight from which two conflicting certificates
can form, `2q − 1`, and the share above which the honest weight online no longer forms one,
`1 − q/u`, at uptimes of 1, 0.95 and 0.9 of the honest weight (src/finality_sim/netcert.py).
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim import netcert as nc

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "m5"
QUORUMS = (("two thirds, Casper FFG", 2 / 3), ("three quarters, Ouroboros Peras", 3 / 4))
UPTIMES = (1.0, 0.95, 0.9)


def main() -> None:
    rows = []
    for name, q in QUORUMS:
        for u in UPTIMES:
            rows.append(dict(quorum=name, q=q, uptime=u, conflicting=2 * q - 1,
                             stalls_above=1 - q / u, held=nc.largest_share_held(u, q)))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "quorum.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
