"""Phase K, K.4 and K.5: MAPPING.md's k-sized quantities with k counted in slots.

    python scripts/k5_mapping.py      # needs nothing; writes runs/k5/mapping.csv

For each k of B5 and the two candidates of SLOTS.md K.0, K = floor(k/f) and K = 3 floor(k/f): the
window in hours; the offline grace margin K / T_offline (T_offline = 20 min, as MAPPING.md §4);
the share of targets whose race of at most K slots meets two ground nonces, and the share that
meets a nonce its own private chain set (finality_sim.slotmap), with the epoch at its length at
k = 2160, as K.0 reads it; and today's self-healing horizon in blocks for sides holding half and a
fifth of the stake (MAPPING.md §5), which counted in slots becomes K for every side.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim.slotmap import nonce_coverage
from mapping_numbers import horizon_hours

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k5"
F = 1 / 30
T_OFFLINE_S = 20 * 60
KS = (2160, 1620, 1080, 432, 216, 120)
EPOCH = 10 * math.floor(2160 / F)          # K.0: the epoch keeps its length at k = 2160
CUTOFF = 6 * math.floor(2160 / F)


def main() -> None:
    rows = []
    for k in KS:
        b = math.floor(k / F)
        for mult in (1, 3):
            window = mult * b
            one, two, private = nonce_coverage(window, EPOCH, CUTOFF)
            rows.append(dict(k=k, multiple=mult, window=window, hours=window / 3600,
                             offline_margin=window / T_OFFLINE_S, one_nonce=one, two_nonces=two,
                             private_nonce=private, horizon_half_h=horizon_hours(k, 0.5),
                             horizon_fifth_h=horizon_hours(k, 0.2)))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "mapping.csv", index=False)
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
