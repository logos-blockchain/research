"""The class group's size for the delay function (DESIGNS.md, H.2; PLAN.md I.2).

The best published algorithms for the class number of an imaginary quadratic order of discriminant
``d`` run in ``L_|d|(1/2)``; Biasse, Jacobson and Silvester (arXiv 1004.5512, Table 4) estimate the
discriminant that matches each RSA modulus of NIST's levels in MIPS-years. Reading their rows
through ``L_|d|[1/2, 1] = exp(sqrt(ln |d| · ln ln |d|))`` fixes a constant, and the constant reads
the cost at any size.
"""

from __future__ import annotations

import math

MIPS_YEAR_OPS = 1e6 * 365.25 * 86_400                     # instructions in one MIPS-year
# Biasse, Jacobson and Silvester, Table 4: RSA bits, imaginary discriminant bits, MIPS-years
TABLE_4 = ((1024, 798, 1.07e10), (2048, 1348, 1.25e19), (3072, 1827, 4.74e25))


def l_half_bits(bits: int) -> float:
    """``log2 L_|d|[1/2, 1]`` for a discriminant of ``bits`` bits."""
    ln_d = bits * math.log(2.0)
    return math.sqrt(ln_d * math.log(ln_d)) / math.log(2.0)


def calibration() -> tuple[float, float]:
    """The constant that takes ``l_half_bits`` to Table 4's cost in log2 operations: its mean over
    the three rows and the spread between them."""
    offsets = [math.log2(mips * MIPS_YEAR_OPS) - l_half_bits(disc) for _, disc, mips in TABLE_4]
    return sum(offsets) / len(offsets), max(offsets) - min(offsets)


def class_number_bits(bits: int) -> float:
    """The estimated cost of the class number of a ``bits``-bit discriminant, in log2 operations."""
    return l_half_bits(bits) + calibration()[0]


def time_to_compute(bits: int, ops_per_second: float) -> float:
    """Seconds to compute the class number at ``ops_per_second``."""
    return 2.0 ** class_number_bits(bits) / ops_per_second
