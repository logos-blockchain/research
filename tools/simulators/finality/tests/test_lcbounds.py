"""Gates for the port of LCanalysis (src/finality_sim/lcbounds.py).

``data/grr2022-1571_rev20250502_table1.tsv`` is Table 1 of Gaži, Ren, Russell, "Practical
Settlement Bounds for Longest-Chain Consensus", ePrint 2022/1571, revision 2025-05-02 (PDF SHA-1
42a59cfe…), transcribed and checked against the rendered page. Its proof-of-stake half uses a
20 s block interval and a delay of 2 s or 5 s, so the delay in block intervals is D = 0.1 or
0.25; the code takes the honest fraction (0.9 or 0.8) and D.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from finality_sim.lcbounds import error_lb, error_ub, skipped_mass, slot_pdf, ub_curve

TABLE = pd.read_csv(pathlib.Path(__file__).parent / "data" / "grr2022-1571_rev20250502_table1.tsv",
                    sep="\t")
ALPHABET, STATES = 10, 19          # the committed defaults of PoSRandomWalk.m
REL_TOL = 1e-3


@pytest.mark.parametrize("adv", [10, 20])
@pytest.mark.parametrize("delay_s", [2, 5])
def test_table1_pos_bounds_reproduce(adv, delay_s):
    sp = slot_pdf(1 - adv / 100, delay_s / 20, ALPHABET)
    rows = TABLE[TABLE.adversary_pct == adv]
    for _, row in rows.iterrows():
        k = int(row.k)
        ub = error_ub(k, sp, ALPHABET, STATES)
        lb = error_lb(k, sp, ALPHABET, STATES)
        assert ub == pytest.approx(row[f"PoS_UB_D{delay_s}s"], rel=REL_TOL), ("UB", k)
        assert lb == pytest.approx(row[f"PoS_LB_D{delay_s}s"], rel=REL_TOL), ("LB", k)


def test_probability_floor_is_off_by_default():
    sp = slot_pdf(0.8, 0.1, ALPHABET)
    exact = error_ub(12, sp, ALPHABET, STATES)
    assert error_ub(12, sp, ALPHABET, STATES, min_prob=0.0) == exact
    floor = 1e-18
    assert skipped_mass(sp, ALPHABET, floor) < 1e-15
    assert error_ub(12, sp, ALPHABET, STATES, min_prob=floor) == pytest.approx(exact, rel=1e-12)


def test_bounds_bracket_and_decay():
    sp = slot_pdf(0.8, 0.25, ALPHABET)
    ub = np.array([error_ub(k, sp, ALPHABET, STATES) for k in (5, 10, 15)])
    lb = np.array([error_lb(k, sp, ALPHABET, STATES) for k in (5, 10, 15)])
    assert np.all(lb < ub)
    assert np.all(np.diff(ub) < 0) and np.all(np.diff(lb) < 0)


def test_lower_bound_converges_in_phases_at_depth():
    """Past Table 1 the attack must be followed long enough: doubling the phases changes nothing."""
    sp = slot_pdf(2 / 3, 1 / 30, ALPHABET)
    k = 60
    lb = error_lb(k, sp, ALPHABET, 30)
    assert lb == pytest.approx(error_lb(k, sp, ALPHABET, 30, steps=2 * 4 * k), rel=1e-9)
    assert lb > 1e-3


def test_port_matches_the_original_code_run_in_octave():
    """``data/lcanalysis_octave.csv``: LCanalysis @ 35cfc83 run in Octave 11.3 with the two pdf
    functions of ``octave/`` (``scripts/octave_reference.sh``), beyond Table 1's points."""
    ref = pd.read_csv(pathlib.Path(__file__).parent / "data" / "lcanalysis_octave.csv")
    for (honest, d, a, s), g in ref.groupby(["honest", "D", "alphabet", "states"]):
        sp = slot_pdf(honest, d, int(a))
        for _, r in g.iterrows():
            got = (error_ub(int(r.K), sp, int(a), int(s)) if r.bound == "ub" else
                   error_lb(int(r.K), sp, int(a), int(s), steps=int(r.lb_steps)))
            assert got == pytest.approx(r.value, rel=1e-9), (honest, d, r.bound, r.K)


def test_the_curve_is_the_port_at_every_depth():
    """``ub_curve`` against ``error_ub``: every depth to 25 at Table 1's 20 % and 5 s, and
    ``data/lcbounds_deep.csv``, the port at depths 160 to 640 in three of B2's cells
    (``scripts/b2_deep.py``)."""
    sp = slot_pdf(0.8, 0.25, ALPHABET)
    want = [error_ub(k, sp, ALPHABET, STATES) for k in range(1, 26)]
    assert ub_curve(25, sp, ALPHABET, STATES) == pytest.approx(want, rel=1e-12)
    ref = pd.read_csv(pathlib.Path(__file__).parent / "data" / "lcbounds_deep.csv",
                      float_precision="round_trip")
    for (honest, d, a, s, cut), g in ref.groupby(["honest", "D", "alphabet", "states", "min_prob"]):
        got = ub_curve(int(g.K.max()), slot_pdf(honest, d, int(a)), int(a), int(s), cut)
        assert got[g.K.to_numpy() - 1] == pytest.approx(g.ub.to_numpy(), rel=1e-10), (honest, d)


def test_the_curve_stops_at_its_floor():
    sp = slot_pdf(0.8, 0.25, ALPHABET)
    full = ub_curve(40, sp, ALPHABET, STATES)
    cut = ub_curve(40, sp, ALPHABET, STATES, floor=full[29])
    assert cut.size == 30
    assert cut == pytest.approx(full[:30], rel=1e-14)
