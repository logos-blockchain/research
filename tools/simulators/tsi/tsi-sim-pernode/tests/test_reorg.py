"""Private-chain reorg-depth model: effective share, closed-form tail, MC validation."""

from __future__ import annotations

import numpy as np

from tsi_sim.reorg import alpha_effective, reorg_depth_tail, simulate_deepest_reorg


def test_alpha_effective_monotone_in_orphan_rate():
    # honest forks waste honest blocks -> raise the adversary's effective share
    assert alpha_effective(0.2, 0.0) == 0.2
    assert alpha_effective(0.2, 0.1) > 0.2
    assert alpha_effective(0.2, 0.5) > alpha_effective(0.2, 0.25)
    assert alpha_effective(0.0, 0.3) == 0.0          # no adversary -> no share


def test_tail_shape():
    assert reorg_depth_tail(0.3, 0) == 1.0
    assert reorg_depth_tail(0.0, 3) == 0.0
    assert reorg_depth_tail(0.6, 5) == 1.0           # majority -> unbounded
    # geometric decay: P(>=2)/P(>=1) = beta/(1-beta)
    b = 0.3
    assert abs(reorg_depth_tail(b, 2) / reorg_depth_tail(b, 1) - b / (1 - b)) < 1e-12


def test_reverse_d_matches_catch_up_from_behind():
    """(beta/(1-beta))**d == P(a walker starting d behind ever reaches 0) — the reorg tail."""
    rng = np.random.default_rng(7)
    beta, d = 0.3, 3
    hits = 0
    trials = 40000
    horizon = 4000
    up = rng.random((trials, horizon)) < beta
    for row in up:
        pos = -d
        for step in row:
            pos += 1 if step else -1
            if pos >= 0:
                hits += 1
                break
    mc = hits / trials
    cf = reorg_depth_tail(beta, d)
    assert abs(mc - cf) < 0.02                        # 0.0937 closed form


def test_simulate_realized_depths_are_shallow_and_bounded():
    rng = np.random.default_rng(1)
    d = simulate_deepest_reorg(alpha_effective(0.3, 0.0), 500_000, rng)
    assert d.size > 1000
    assert d.min() >= 1
    assert d.mean() < 2.0                             # typical opportunistic reorg is ~1 deep
