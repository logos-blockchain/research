"""Phase I.2: the class group's size (PLAN.md, I.2).

    python scripts/i2_discriminant.py      # writes runs/i2/discriminant.csv

discriminant.csv: for discriminants of 798, 1024, 1348, 1827 and 2048 bits, the RSA modulus Biasse,
Jacobson and Silvester's Table 4 pairs with it, and the discrete logarithm's cost in log2 operations
two ways (finality_sim.discriminant): Table 4's rows read through L_|d|[1/2, 1], which the paper's
Section 5 method gives with its 256-bit anchor converted at 4.8 MIPS, and the method at the stated
4,800 MIPS; the class group's computation at the stated conversion, 1.33-1.61 times the discrete
logarithm (their Table 1); the years at 10^18 operations a second and the operations a second that
finish within the delay of H.2, 4.49 hours at k = 2160, for the rows and for the class group at the
stated conversion. The calibration's spread over Table 4's rows of NIST's 80- to 128-bit levels is
the last column.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim.discriminant import (TABLE_4, anchor_bits, calibration, class_group_ratio, rows_bits,
                                       time_to_compute)

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "i2"
YEAR = 365.25 * 86_400
T_A = 4.49 * 3600


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paired = {disc: rsa for rsa, disc, _ in TABLE_4}
    lo, hi = class_group_ratio()
    rows = []
    for bits in (798, 1024, 1348, 1827, 2048):
        r, s = rows_bits(bits), anchor_bits(bits)
        cl_lo, cl_hi = s + math.log2(lo), s + math.log2(hi)
        rows.append(dict(bits=bits, rsa=paired.get(bits), dl_rows=r, dl_stated=s, cl_stated_lo=cl_lo,
                         cl_stated_hi=cl_hi,
                         years_1e18_rows=time_to_compute(r, 1e18) / YEAR,
                         years_1e18_stated=time_to_compute(cl_hi, 1e18) / YEAR,
                         ops_within_delay_rows=2.0 ** r / T_A, ops_within_delay_stated=2.0 ** cl_hi / T_A))
    t = pd.DataFrame(rows)
    t["calibration_spread_bits"] = calibration()[1]
    t.to_csv(OUT / "discriminant.csv", index=False)
    print(t.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
