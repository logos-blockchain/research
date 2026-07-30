"""Poisson long-tail jitter model (case (b) of the N-scaling study)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tsi_sim import topology as topo
from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory

BASE = dict(n_nodes=200, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=4.0,
            max_uncles=1, uncle_window=300, k=64, epochs=8, genesis_d_factor=0.5)


def test_poisson_frac_zero_matches_no_jitter_statistics():
    """jitter_frac=0 hits nobody: consensus holds and accuracy matches the jitter-free run."""
    off = pd.DataFrame(run_trajectory(SimConfig(**BASE)))
    z = pd.DataFrame(run_trajectory(SimConfig(
        **BASE, jitter_mean=3.0, jitter_dist="poisson", jitter_frac=0.0)))
    assert z.range_ratio.max() == 0.0
    assert z.agreement_window.min() == 1.0
    # same equilibrium to MC noise (different RNG stream — key includes jitter fields)
    assert abs(z[z.epoch >= 4].mean_ratio.mean() - off[off.epoch >= 4].mean_ratio.mean()) < 0.1


def test_poisson_tail_consensus_survives():
    """10% long-tail stragglers (lambda=3 slots): spread stays 0, agreement stays 1."""
    df = pd.DataFrame(run_trajectory(SimConfig(
        **BASE, jitter_mean=3.0, jitter_dist="poisson", jitter_frac=0.1)))
    assert df.range_ratio.max() == 0.0
    assert df.agreement_window.min() == 1.0


def test_jitter_fields_validated_and_keyed():
    with pytest.raises(ValueError):
        SimConfig(jitter_dist="weibull")
    with pytest.raises(ValueError):
        SimConfig(jitter_frac=1.5)
    a = SimConfig(**BASE, jitter_mean=3.0, jitter_dist="poisson", jitter_frac=0.1)
    b = SimConfig(**BASE, jitter_mean=3.0, jitter_dist="poisson", jitter_frac=0.05)
    c = SimConfig(**BASE, jitter_mean=3.0, jitter_dist="exp", jitter_frac=0.1)
    assert len({a.key(), b.key(), c.key()}) == 3


def test_poisson_only_hits_the_requested_fraction():
    """Direct check on one arrival column: ~frac of nodes delayed, by whole slots."""
    big = {**BASE, "n_nodes": 2000}
    cfg_j = SimConfig(**big, jitter_mean=3.0, jitter_dist="poisson", jitter_frac=0.1)
    cfg_0 = SimConfig(**big)
    pl = topo.build_path_latency(cfg_j, np.random.default_rng(0))
    # same rng seed: relay/mixing draws happen before jitter, so the columns differ by jitter only
    col_j = topo.arrival_column(pl, producer=0, slot=100, config=cfg_j,
                                rng=np.random.default_rng(1))
    col_0 = topo.arrival_column(pl, producer=0, slot=100, config=cfg_0,
                                rng=np.random.default_rng(1))
    extra = col_j - col_0
    delayed = extra > 0
    frac = delayed[1:].mean()          # exclude the producer (clamped to its own slot)
    assert 0.04 < frac < 0.16          # ~10%, minus the Poisson(3) zeros (~5%)
    assert np.allclose(extra[delayed], np.round(extra[delayed]))   # whole-slot stragglers
