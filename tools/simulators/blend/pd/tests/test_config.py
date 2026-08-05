import dataclasses

import pytest

from pd.config import SimConfig, SweepConfig


def test_key_covers_every_field():
    fields = [f.name for f in dataclasses.fields(SimConfig)]
    assert len(SimConfig().key()) == len(fields)
    # n_regions=2 in the base so the region/churn fields can each be varied on their own
    # (region_locality and churn_mode="regional" both require n_regions >= 2)
    base = SimConfig(n_regions=2)
    for name in fields:
        cur = getattr(base, name)
        alt = {"n_nodes": 2000, "degree": 4, "n_regions": 4, "region_locality": 0.5,
               "blend_hops": 2, "max_blend_delay": 5,
               "unresponsive_frac": 0.2, "churn_mode": "regional", "redundancy": 2,
               "cover_rate_mult": 2.0, "block_interval_slots": 60, "slots_per_epoch": 1000,
               "stake_inference_ratio": 0.7, "traffic_window_slots": 100,
               "n_rounds": 10, "transport_jitter_mean_ms": 1.0,
               "processing_lags_ms": (11.0, 51.0, 101.0), "processing_lag_probs": (0.6, 0.3, 0.1),
               "link_latency_dist": "fixed", "link_latency_mean_ms": 1.0,
               "coverage_pcts": (25.0,), "f_adv": 0.1, "adversary_mode": "worstcase_coverage",
               "n_placements": 1, "worstcase_max_n": 5, "graph_seed": 99, "replicate": 1,
               "root_seed": 7}[name]
        assert alt != cur
        assert dataclasses.replace(base, **{name: alt}).key() != base.key(), name


@pytest.mark.parametrize("kw", [
    {"n_nodes": 999},                       # odd
    {"degree": 1000},                       # >= n
    {"blend_hops": 0},                      # < 1
    {"f_adv": 1.0},                         # >= 1
    {"max_blend_delay": -1},
    {"processing_lag_probs": (0.5, 0.4)},   # doesn't sum to 1 (with default 3 lags -> len mismatch)
    {"link_latency_dist": "bogus"},
    {"adversary_mode": "bogus"},
])
def test_validation_rejects(kw):
    with pytest.raises(ValueError):
        SimConfig(**kw)


def test_sweep_grids_and_collapse():
    sw = SweepConfig(n_nodes=[1000, 10000], degree=[4, 8], blend_hops=[2, 3],
                     max_blend_delay=[0, 3], f_adv=[0.0, 0.2],
                     adversary_mode=["random", "worstcase_coverage"], seeds=3)
    assert len(sw.graph_cells()) == 2 * 2 * 3
    assert len(sw.prop_grid()) == 2 * 2
    # f_adv=0 collapses to a single (mode-irrelevant) row; f_adv=0.2 keeps both modes
    assert sw.adv_grid() == [(0.0, "random"), (0.2, "random"), (0.2, "worstcase_coverage")]


def test_from_dict_rejects_unknown():
    with pytest.raises(ValueError):
        SweepConfig.from_dict({"nonsense": [1]})


def test_base_config_coerces_tuples():
    sw = SweepConfig(base={"processing_lags_ms": [10.0, 90.0], "processing_lag_probs": [0.3, 0.7]})
    cfg = sw.base_config(1000, 8, 0)
    assert cfg.processing_lags_ms == (10.0, 90.0)
    assert isinstance(cfg.key(), tuple)
