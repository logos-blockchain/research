"""Gates for a cap on the inference's correction (src/finality_sim/cap.py, SLOTS.md K.8)."""

import math

import numpy as np

from finality_sim.cap import (blocks_by, correct, density_protection, density_stall, estimates,
                              resume_share, slow, spec_correction, spec_rate)
from finality_sim.floor import after_correction, blocks_time, floor_for
from finality_sim.recovery import occupancy

F = 1 / 30
EPS = 1e-9
KF = math.floor(2160 / F)
EPOCH, PERIOD = 10 * KF, 6 * KF


def test_the_estimate_follows_the_specifications_correction():
    """Played period by period with binomial counts of occupied slots and the specification's
    integer correction at ``f = 1/20``, where ``f·1000`` is whole, with the cap applied to each
    correction, the estimate tracks ``estimates`` within 1 % for a side of 0.3: capped at 5 %
    and uncapped."""
    f = 1 / 20
    period = 6 * math.floor(2160 / f)
    stake = 10**12
    rng = np.random.default_rng(7)
    for cap in (None, 0.05):
        want = estimates(0.3, cap, 12, f)
        paths = []
        for _ in range(40):
            d = stake
            path = [1.0]
            for _ in range(12):
                n = rng.binomial(period, occupancy(f, 0.3 * stake / d))
                full = spec_correction(d, int(n), period, f)
                d = full if cap is None else max(full, math.ceil((1 - cap) * d))
                path.append(d / stake)
            paths.append(path)
        got = np.mean(paths, axis=0)
        assert np.allclose(got, want, rtol=0.01), (cap, got, want)
    assert abs(correct(1.0, 1.0, None, f) - 1.0) < 1e-12


def test_the_specification_rests_at_its_truncated_rate():
    """``f_p = truncate(f·1000)`` makes the specification's inference aim at 0.033 occupied slots
    a slot for ``f = 1/30``; at ``f = 1/20`` it aims at ``f``."""
    assert abs(spec_rate(1 / 30, PERIOD) - 0.033) < 2e-5
    assert abs(spec_rate(1 / 20, 6 * math.floor(2160 / (1 / 20))) - 1 / 20) < 2e-5


def test_the_resume_share_at_the_worst_case_is_the_honest_share():
    """Under the worst case the least share whose chain reaches the floor at ``1 − ε`` is the
    honest share the floor was sized for, ``1 − α``."""
    for w, alpha in ((3 * KF, 1 / 3), (KF, 0.25)):
        phi = floor_for(w, alpha, EPS, F, delta=10)
        r = resume_share(w, phi, EPS, F, delta=10)
        assert 1 - alpha - 0.005 <= r <= 1 - alpha + 1e-9, (w, alpha, r)


def test_the_protection_counts_corrections_from_the_split():
    """A side of 0.3 against a floor that holds back 0.449: capped at 5 %, it passes after the
    eighth correction, since 0.3/0.95⁷ = 0.425 and 0.3/0.95⁸ = 0.452, the corrections at one
    epoch each; uncapped, after the first. A window follows."""
    w = 3 * KF
    assert density_protection(0.3, 0.449, 0.05, EPOCH, w) == 8 * EPOCH + w
    assert density_protection(0.3, 0.449, None, EPOCH, w) == EPOCH + w
    assert density_protection(0.5, 0.449, 0.05, EPOCH, w) == w


def test_the_stall_and_the_slow_chain_read_the_latest_alignment():
    """A fall just after a period ends is first corrected ``2E − P`` later. Uncapped, one correction
    takes a fall to half back past ``r*`` and to within 5 % of ``f``."""
    w = 3 * KF
    assert density_stall(0.5, 0.656, None, EPOCH, PERIOD, w) == 2 * EPOCH - PERIOD + w
    assert density_stall(0.7, 0.656, 0.05, EPOCH, PERIOD, w) == 0.0
    assert slow(0.5, None, EPOCH, PERIOD) == 2 * EPOCH - PERIOD
    assert slow(0.99, 0.05, EPOCH, PERIOD) == 0.0


def test_without_a_cap_the_blocks_come_as_k3_reads_them():
    """With no cap a side's blocks come on average as ``floor.after_correction`` reads them, which
    fills the slots at ``f`` from the first correction: within 0.5 %."""
    for sigma, n in ((0.1, 3265), (0.05, 1020), (0.2, 3265)):
        got = blocks_by(n, sigma, None, EPOCH, EPOCH)
        want = after_correction(n, sigma, EPOCH)
        assert abs(got / want - 1) < 0.005, (sigma, n, got, want)


def test_the_early_time_is_the_blocks_tail_without_corrections():
    """With a cap of zero the estimate never moves, and the earliest slot by which a side holds
    ``n`` blocks with chance ``ε`` lies at or before the binomial's (``floor.blocks_time``), whose
    upper tail is lighter than the Poisson's, and within 0.5 % of it."""
    for sigma, n in ((0.1, 3265), (1 / 3, 1020)):
        got = blocks_by(n, sigma, 0.0, EPOCH, EPOCH, EPS)
        want = blocks_time(n, sigma, EPS)[1]
        assert got <= want + 1 and got >= 0.995 * want, (sigma, got, want)
