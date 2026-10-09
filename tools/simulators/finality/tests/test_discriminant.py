"""Gates for the class group's size (src/finality_sim/discriminant.py)."""

import math

import pytest

from finality_sim.discriminant import (TABLE_4, calibration, class_number_bits, l_half_bits,
                                       time_to_compute)


def test_the_calibration_reads_every_row_of_table_4_within_a_bit():
    mean, spread = calibration()
    assert spread < 0.3
    for rsa, disc, mips in TABLE_4:
        assert class_number_bits(disc) == pytest.approx(math.log2(mips * 1e6 * 365.25 * 86_400), abs=0.3)
    assert class_number_bits(798) < 80 < 85                           # NIST's 80-bit level, RSA-1024
    assert 108 < class_number_bits(1348) < 112                        # the 112-bit level, RSA-2048
    assert 128 < class_number_bits(1827) < 132                        # the 128-bit level, RSA-3072


def test_the_estimate_grows_with_the_size_and_sets_the_design_between_the_levels():
    assert l_half_bits(2048) > l_half_bits(1024) > l_half_bits(798)
    assert 90 < class_number_bits(1024) < 93                           # between the 80- and 112-bit levels
    assert 138 < class_number_bits(2048) < 141
    hours = 4.49 * 3600
    assert time_to_compute(1024, 1e18) > 50 * 365.25 * 86_400          # decades at a billion billion a second
    assert time_to_compute(1024, 1e24) < hours < time_to_compute(1024, 1e23)
