"""Phase I.2: the class group's size (PLAN.md, I.2).

    python scripts/i2_discriminant.py      # writes runs/i2/discriminant.csv

discriminant.csv: for discriminants of 798, 1024, 1348, 1827 and 2048 bits, the estimated cost of
the class number in log2 operations (finality_sim.discriminant, Biasse, Jacobson and Silvester's
Table 4 read through L_|d|[1/2, 1]), the RSA modulus Table 4 pairs it with, the years it takes at
10^18 and 10^21 operations a second, and the operations a second that compute it within the delay
of H.2, 4.49 hours at k = 2160.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim.discriminant import TABLE_4, calibration, class_number_bits, time_to_compute

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "i2"
YEAR = 365.25 * 86_400
T_A = 4.49 * 3600


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paired = {disc: rsa for rsa, disc, _ in TABLE_4}
    rows = []
    for bits in (798, 1024, 1348, 1827, 2048):
        c = class_number_bits(bits)
        rows.append(dict(bits=bits, rsa=paired.get(bits), log2_ops=c,
                         years_1e18=time_to_compute(bits, 1e18) / YEAR,
                         years_1e21=time_to_compute(bits, 1e21) / YEAR,
                         ops_per_second_within_delay=2.0 ** c / T_A))
    t = pd.DataFrame(rows)
    t["calibration_spread_bits"] = calibration()[1]
    t.to_csv(OUT / "discriminant.csv", index=False)
    print(t.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
