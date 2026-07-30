"""Early stop: converge-then-measure truncation that preserves equilibrium statistics."""

from __future__ import annotations

import pandas as pd

from tsi_sim.config import SimConfig
from tsi_sim.engine import ES_MEASURE, ES_MIN_EPOCH, run_trajectory

BASE = dict(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=4.0,
            max_uncles=2, uncle_window=300, k=256, epochs=40, genesis_d_factor=0.5)


def test_early_stop_truncates_and_matches_full_run():
    full = pd.DataFrame(run_trajectory(SimConfig(**BASE)))
    es = pd.DataFrame(run_trajectory(SimConfig(**BASE, early_stop=True)))
    # truncation happened, with room for the measurement budget
    assert ES_MIN_EPOCH + 1 <= len(es) < len(full)
    # bit-identical prefix (same RNG streams; early_stop is excluded from key())
    n = len(es)
    assert (full.head(n).mean_ratio.to_numpy() == es.mean_ratio.to_numpy()).all()
    # equilibrium agrees: early-stop tail (measurement sample) vs full-run tail
    es_tail = es.tail(ES_MEASURE).mean_ratio.mean()
    full_tail = full[full.epoch >= 20].mean_ratio.mean()
    assert abs(es_tail - full_tail) < 0.015


def test_sawtooth_never_stops_early():
    cfg = SimConfig(**{**BASE, "epochs": 24}, early_stop=True,
                    adversary_frac=0.3, adversary_strategy="withhold",
                    adversary_period=6, adversary_withhold_epochs=3)
    df = pd.DataFrame(run_trajectory(cfg))
    assert len(df) == 24                        # full budget: detector disabled for schedules
