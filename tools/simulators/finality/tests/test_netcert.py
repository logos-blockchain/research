"""Gates for Phase L's closed forms (src/finality_sim/netcert.py)."""

import math

import pytest

from finality_sim import netcert as nc
from finality_sim.privacy import volunteer_share

ALPHAS = (0.05, 0.10, 0.20, 0.25, 0.30, 1 / 3)
UPTIMES = (1.0, 0.95, 0.9)


def partitions(total: int, smallest: int):
    """Every multiset of integer note values of at least ``smallest`` summing to at most
    ``total``, as non-increasing tuples."""
    def rec(left, cap):
        yield ()
        for v in range(min(left, cap), smallest - 1, -1):
            for rest in rec(left - v, v):
                yield (v,) + rest
    yield from rec(total, total)


@pytest.mark.parametrize("m", [1, 2, 3, 4, 7])
def test_the_coalition_holds_the_most_declarations_its_stake_backs(m):
    """One note backs one declaration: over every way to split its stake into notes of at least
    the minimum, the most declarations the coalition holds is the closed form's."""
    active = 60
    for stake in range(0, 25):
        best = max(len(p) for p in partitions(stake, m))
        assert nc.coalition_declarations(stake / active, m, active) == best, (m, stake)


def test_weight_by_value_is_the_opt_in_committee():
    """With weight by value the honest declared stake the quorum needs is D1b's: the share of the
    honest stake that must declare, times the honest stake."""
    for a in ALPHAS:
        for u in UPTIMES:
            v = volunteer_share(a, u)
            x = nc.honest_locked_needed(a, u)
            if math.isinf(v):
                assert math.isinf(x), (a, u)
            else:
                assert x == pytest.approx(v * (1 - a), rel=1e-12), (a, u)


def test_two_sides_certify_only_from_two_q_minus_one():
    """Searching every split of the honest declarations, two sides both reach the quorum exactly
    when the coalition holds at least 2q − 1 of the declared weight."""
    for i in range(0, 501):
        a = i / 1000
        steps = 400
        split = any(nc.side_certifies(h, a) and nc.side_certifies(1 - a - h, a)
                    for h in ((1 - a) * k / steps for k in range(steps + 1)))
        assert split == nc.both_sides_certify(a) == (not nc.safe(a)), a


def test_liveness_needs_the_online_honest_declarations():
    """At 30 % of the declared weight the honest declarations online must be 95.24 % or more."""
    assert nc.live(0.3, 0.9524) and not nc.live(0.3, 0.95)
    assert nc.largest_share_held(0.95) == pytest.approx(1 - (2 / 3) / 0.95)
    assert nc.largest_share_held(1.0) == pytest.approx(1 / 3)
    assert nc.side_share_needed(0.3) == pytest.approx((2 / 3 - 0.3) / 0.7)


def test_the_minimum_stake_analysis_is_reproduced():
    """0.001 % of 100,000,000 LGO is 1,000 LGO; the cap, 15 % of the supply over 1,000 nodes, is
    15,000. A thousand honest declarations at the minimum, against 30 % of the supply staked,
    hold a coalition of 1/60 of the active stake; at the cap, a quarter."""
    assert nc.analysis_min_stake() == pytest.approx(1_000)
    assert nc.analysis_cap() == pytest.approx(15_000)
    locked = nc.SMALL_NETWORK * nc.MIN_STAKE_SHARE / nc.STAKED_SHARE
    assert nc.largest_alpha_held(locked) == pytest.approx(1 / 60)
    assert nc.largest_alpha_held(nc.SMALL_NETWORK * nc.CAP_SHARE / nc.STAKED_SHARE) == \
        pytest.approx(0.25)
    # at whole declarations: 499 coalition declarations against 1,000 honest stay below a third
    m = nc.MIN_STAKE_SHARE / nc.STAKED_SHARE
    assert nc.coalition_share(499 * m, 1000 * m, m) < 1 / 3 <= nc.coalition_share(500 * m, 1000 * m, m)


def test_the_pi5_measurements_are_read_from_the_benchmark():
    """The reference-grade Pi 5 run of reports/pqc: ed25519-dalek verifies in 181,036 ns, aws-lc-rs
    in 113,999; ML-DSA-44's signature is 2,420 bytes and aws-lc-rs verifies it in 67,703 ns."""
    import json
    assert json.loads(nc.PI5.read_text())["is_baseline_grade"] is True
    assert nc.pi5_signature("Ed25519", "rustcrypto") == (181_036.0, 64)
    assert nc.pi5_signature("Ed25519", "aws-lc-rs") == (113_999.0, 64)
    assert nc.pi5_signature("ML-DSA-44", "aws-lc-rs") == (67_703.0, 2_420)


def test_cost_reads_the_measured_verification():
    """20,000 votes a 60-slot round at the Pi 5's 181,036 ns per Ed25519 verification take 6.0 %
    of a core; a vote is 84 bytes and a signature; a certificate of three declarations needs two
    signatures."""
    assert nc.verify_core_share(20_000, 60, 181_036) == pytest.approx(0.060345, rel=1e-4)
    assert nc.vote_bytes(64) == 148
    assert nc.certificate_bytes(3, 64) == 80 + 2 * 68
