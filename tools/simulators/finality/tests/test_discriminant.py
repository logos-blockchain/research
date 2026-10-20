"""Gates for the class group's size (src/finality_sim/discriminant.py)."""

import math

import pytest

from finality_sim.discriminant import (MIPS_YEAR_OPS, STATED_MIPS, TABLE_4, anchor_bits, calibration,
                                       class_group_ratio, l_half_bits, method_size, rows_bits,
                                       time_to_compute)


def test_the_calibration_reads_every_row_of_table_4_within_a_bit():
    mean, spread = calibration()
    assert spread < 0.3
    for rsa, disc, mips in TABLE_4:
        if 1024 <= rsa <= 3072:
            assert rows_bits(disc) == pytest.approx(math.log2(mips * MIPS_YEAR_OPS), abs=0.3)
    assert rows_bits(798) < 80 < 85                                    # NIST's 80-bit level, RSA-1024
    assert 108 < rows_bits(1348) < 112                                 # the 112-bit level, RSA-2048
    assert 128 < rows_bits(1827) < 132                                 # the 128-bit level, RSA-3072


def test_section_5s_method_gives_table_4_only_with_the_anchor_at_4_8_mips():
    """The discriminants of Table 4 come out of the stated method, from Table 2's 256-bit anchor, when
    its seconds are converted at 4.8 MIPS, and fall short by more than a hundred bits at the stated
    4,800; the two readings of the cost then differ by that factor of a thousand."""
    for _, disc, mips in TABLE_4:
        assert abs(method_size(mips, 4.8) - disc) <= 1
        assert method_size(mips, STATED_MIPS) < disc - 100
    assert anchor_bits(1024, 4.8) == pytest.approx(rows_bits(1024), abs=0.1)
    assert anchor_bits(1024) - anchor_bits(1024, 4.8) == pytest.approx(math.log2(1000), abs=1e-9)
    assert 101 < anchor_bits(1024) < 102 and 91 < rows_bits(1024) < 92


def test_the_class_group_costs_a_third_to_three_fifths_more_than_the_discrete_logarithm():
    lo, hi = class_group_ratio()
    assert lo == pytest.approx(5.08 / 3.81) and hi == pytest.approx(1098.43 / 681.71)
    assert 1.3 < lo < hi < 1.65


def test_the_estimate_grows_with_the_size_and_sets_the_design_between_the_levels():
    assert l_half_bits(2048) > l_half_bits(1024) > l_half_bits(798)
    assert 138 < rows_bits(2048) < 141 and 148 < anchor_bits(2048) < 151
    hours = 4.49 * 3600
    assert time_to_compute(rows_bits(1024), 1e18) > 50 * 365.25 * 86_400  # decades at 1e18 a second
    assert time_to_compute(rows_bits(1024), 1e24) < hours < time_to_compute(rows_bits(1024), 1e23)
