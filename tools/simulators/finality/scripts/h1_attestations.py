"""Phase H.1: recovery attestations and partition detection (PLAN.md, H.1).

    python scripts/h1_attestations.py      # needs runs/a1; writes runs/h1/*.csv

seats.csv: a one-off round of anonymous-seat votes after a split deeper than k, in which each node
votes for the chain it followed. A chain is kept when its seats exceed a threshold theta. With n
expected seats in all, a chain backed by a share s draws Poisson(s n) seats
(src/finality_sim/further.py, attestation_seats). For the adversary's bound alpha and an even
partition, whose honest sides hold (1 - alpha)/2 each: the fewest n and the theta at which the
adversary's fork (share alpha) passes theta with chance at most eps, and an honest side falls
below it with chance at most eps_live; also with a share u of the honest votes undelivered.
detector.csv: rule 8's test as a partition detector. A node compares its canonical count over a
window with the count the honest stake 1 - alpha makes alone; it declares the chain sparse below
the eps lower tail of that count (src/finality_sim/recovery.py, honest_logpmf, the specification's
Blend under random delay). The table gives the chance that a side holding a share of all stake is
declared sparse; a side of 0.70 is the whole honest stake against 30 %, so its entry is the
false-alarm rate.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from b2_settlement import F
from finality_sim.further import attestation_seats, detector_power

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h1"
ALPHAS = (0.20, 0.25, 0.30, 0.32, 0.33)
EPS = 1e-9
EPS_LIVE = 1e-6
UNDELIVERED = (0.0, 0.1)
SIDES = (0.35, 0.50, 0.60, 0.65, 0.70)
WINDOWS_H = (36, 72)


def main() -> None:
    rows = []
    for alpha in ALPHAS:
        for u in UNDELIVERED:
            n, theta = attestation_seats(alpha, EPS, EPS_LIVE, u)
            rows.append(dict(alpha=round(alpha, 4), honest_side=(1 - alpha) / 2, undelivered=u,
                             seats=n, threshold=theta))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "seats.csv", index=False)
    print(t.to_string(index=False))

    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    g = float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])
    rows = []
    for alpha in (0.30, 1 / 3):
        for w_h in WINDOWS_H:
            row = dict(alpha=round(alpha, 4), window_h=w_h)
            threshold, powers = detector_power(alpha, g, w_h * 3600, EPS, SIDES, F)
            row["threshold"] = threshold
            row["expected_full"] = (1 - alpha) * g * (-math.log(1 - F)) * w_h * 3600
            for side, p in zip(SIDES, powers):
                row[f"side_{side:.4f}"] = p
            rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "detector.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(d.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
