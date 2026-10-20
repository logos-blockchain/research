"""The class group's size for the delay function (DESIGNS.md, H.2; PLAN.md I.2).

Biasse, Jacobson and Silvester (arXiv 1004.5512v1) time the discrete logarithm in the class group
of an imaginary quadratic field by Vollmer's algorithm (their Table 2) and size, in their Table 4,
the discriminant whose discrete logarithm costs what factoring each RSA modulus of NIST's levels
costs, in MIPS-years. Their method (Section 5) reads the cost at ``N`` bits as the cost ``t_1`` at a
256-bit anchor scaled by ``L_N[1/2, 1] / L_256[1/2, 1]``, with ``t_1`` the anchor's seconds on a machine
they take to run 4,800 MIPS. Their Table 1 puts the class group's computation at 1.33-1.61 times the
discrete logarithm's.

Two readings of the cost follow. Table 4's rows, read through ``L_|d|[1/2, 1]``, fix a constant
(``calibration``, ``rows_bits``); the rows come out of the method only with the anchor converted at
4.8 MIPS. The stated method at the stated 4,800 MIPS gives costs 2^10 times higher (``anchor_bits``).
"""

from __future__ import annotations

import math

MIPS_YEAR_OPS = 1e6 * 365.25 * 86_400                     # instructions in one MIPS-year
# Biasse, Jacobson and Silvester, Table 4: RSA bits, imaginary discriminant bits, MIPS-years
TABLE_4 = ((768, 640, 8.80e6), (1024, 798, 1.07e10), (2048, 1348, 1.25e19), (3072, 1827, 4.74e25),
           (7680, 3598, 1.06e45), (15360, 5971, 1.01e65))
# Table 2: the 256-bit anchor of Section 5, seconds per discrete logarithm on the 2.4 GHz Xeon
ANCHOR_BITS, ANCHOR_SECONDS = 256, 22_992.70
STATED_MIPS = 4_800.0                                     # Section 5's conversion
# Table 1: total seconds, class group (CL) and discrete logarithm (DL), 140 to 220 bits
TABLE_1 = ((140, 5.08, 3.81), (160, 21.01, 13.65), (180, 31.28, 21.33), (200, 247.93, 157.96),
           (220, 1098.43, 681.71))


def l_half_bits(bits: int) -> float:
    """``log2 L_|d|[1/2, 1]`` for a discriminant of ``bits`` bits."""
    ln_d = bits * math.log(2.0)
    return math.sqrt(ln_d * math.log(ln_d)) / math.log(2.0)


def calibration() -> tuple[float, float]:
    """The constant that takes ``l_half_bits`` to Table 4's cost in log2 operations: its mean over
    the rows of NIST's 80- to 128-bit levels and the spread between them."""
    offsets = [math.log2(mips * MIPS_YEAR_OPS) - l_half_bits(disc)
               for rsa, disc, mips in TABLE_4 if 1024 <= rsa <= 3072]
    return sum(offsets) / len(offsets), max(offsets) - min(offsets)


def rows_bits(bits: int) -> float:
    """The discrete logarithm's cost at ``bits`` bits as Table 4's rows give it, in log2 operations."""
    return l_half_bits(bits) + calibration()[0]


def anchor_bits(bits: int, mips: float = STATED_MIPS) -> float:
    """The discrete logarithm's cost at ``bits`` bits by Section 5's method, the anchor converted at
    ``mips``, in log2 operations."""
    t1 = ANCHOR_SECONDS * mips * 1e6
    return math.log2(t1) + l_half_bits(bits) - l_half_bits(ANCHOR_BITS)


def method_size(mips_years: float, mips: float) -> int:
    """Section 5: the smallest discriminant of ``b`` bits with ``L_2^b[1/2, 1] > L_256[1/2, 1]·t_2/t_1``,
    for a target of ``mips_years`` and the anchor converted at ``mips``."""
    t1 = ANCHOR_SECONDS * mips / (365.25 * 86_400)        # MIPS-years
    target = l_half_bits(ANCHOR_BITS) + math.log2(mips_years / t1)
    b = 2
    while l_half_bits(b) <= target:
        b += 1
    return b


def class_group_ratio() -> tuple[float, float]:
    """The least and largest ratio of the class group's computation to the discrete logarithm's
    over Table 1's sizes."""
    ratios = [cl / dl for _, cl, dl in TABLE_1]
    return min(ratios), max(ratios)


def time_to_compute(log2_ops: float, ops_per_second: float) -> float:
    """Seconds for ``2^log2_ops`` operations at ``ops_per_second``."""
    return 2.0 ** log2_ops / ops_per_second
