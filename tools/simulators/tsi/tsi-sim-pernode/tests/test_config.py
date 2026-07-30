import dataclasses

import pytest

from tsi_sim.config import SimConfig, SweepConfig


def test_expand_cardinality_and_u0_strategy_dedup():
    # full_mesh, where `latency` (L) IS a live axis, so the x2 latency factor applies.
    sweep = SweepConfig(
        n_nodes=[1000, 2000],
        stake_dist=["uniform"],
        topology=["full_mesh"],
        latency=[0, 4],
        max_uncles=[0, 1, 2],
        uncle_strategy=["oldest", "random"],
        replicates=3,
        base={"k": 16, "epochs": 5},
    )
    configs = sweep.expand()
    # U=0 keeps only the first strategy; U>0 keeps both.
    # per (n,dist,lat): U0 x1 strat + U1 x2 + U2 x2 = 5 strat-U combos, x3 reps = 15
    # x 2 n_nodes x 1 dist x 2 lat = 60
    assert len(configs) == 60
    u0 = [c for c in configs if c.max_uncles == 0]
    assert all(c.uncle_strategy == "oldest" for c in u0)
    assert {c.replicate for c in configs} == {0, 1, 2}


def test_latency_collapsed_for_graph_topologies():
    # `latency` is the full_mesh-only uniform-L knob; regular/blend ignore it, so sweeping it
    # must NOT emit duplicate (seed-shifted) graph cells.
    for topo in ("regular", "blend"):
        sweep = SweepConfig(
            n_nodes=[100], topology=[topo], degree=[4], latency=[0, 2, 4], max_uncles=[0],
            uncle_strategy=["oldest"], replicates=1, base={"k": 8, "epochs": 3},
        )
        configs = sweep.expand()
        assert len(configs) == 1, topo            # 3 latency values collapse to 1
        assert configs[0].latency == 0


def test_base_propagation():
    sweep = SweepConfig(n_nodes=[500], stake_dist=["pareto"], latency=[2], max_uncles=[0],
                        uncle_strategy=["oldest"], replicates=1,
                        base={"k": 32, "epochs": 7, "fixed_point": True})
    (c,) = sweep.expand()
    assert c.k == 32 and c.epochs == 7 and c.fixed_point is True and c.stake_dist == "pareto"


@pytest.mark.parametrize("kwargs", [
    {"k": 0}, {"epochs": 0}, {"n_nodes": 0}, {"latency": -1}, {"max_uncles": -1},
    {"uncle_window": 0}, {"lottery_chunks": 0}, {"uncle_random_p": 1.5}, {"f": 0.0},
    {"f": 1.0}, {"beta": 0.0}, {"genesis_d_factor": 0.0}, {"pareto_shape": 0.0},
    {"stake_dist": "zipf"}, {"uncle_strategy": "newest"}, {"topology": "star"},
    {"blend_hops": 0}, {"blend_delay_max": -1.0},
    {"adversary_period": -1}, {"adversary_withhold_epochs": -1},
    # a schedule may not withhold for more epochs than its own period
    {"adversary_period": 2, "adversary_withhold_epochs": 3},
    # blend needs `blend_hops` distinct relays from the non-producer pool (n-1 of them)
    {"topology": "blend", "n_nodes": 4, "degree": 2, "blend_hops": 4},
])
def test_validation_rejects_bad_fields(kwargs):
    with pytest.raises(ValueError):
        SimConfig(**kwargs)


def test_blend_dedup_does_not_multiply_non_blend_configs():
    # blend_hops / blend_delay_max only affect blend runs; sweeping them must not duplicate
    # the regular / full_mesh cells.
    sweep = SweepConfig(
        n_nodes=[100], stake_dist=["uniform"], topology=["regular", "blend"],
        degree=[4], link_latency_mean=[1.0], link_latency_dist=["fixed"],
        blend_hops=[2, 3], blend_delay_max=[1.0, 3.0], max_uncles=[0],
        uncle_strategy=["oldest"], init_dest=["common"], replicates=1,
        base={"k": 8, "epochs": 3},
    )
    configs = sweep.expand()
    regular = [c for c in configs if c.topology == "regular"]
    blend = [c for c in configs if c.topology == "blend"]
    assert len(regular) == 1                       # blend knobs collapsed for non-blend
    assert len(blend) == 4                          # 2 hops x 2 delay_max
    assert {(c.blend_hops, c.blend_delay_max) for c in blend} == {
        (2, 1.0), (2, 3.0), (3, 1.0), (3, 3.0)}


def test_uncle_window_sweeps_and_collapses_for_u0():
    # uncle_window is a live axis for U>0, but U=0 references no uncles so it must collapse.
    sweep = SweepConfig(
        n_nodes=[100], stake_dist=["uniform"], topology=["blend"], degree=[6],
        link_latency_mean=[0.5], link_latency_dist=["geo"], blend_hops=[3],
        blend_delay_max=[4.0], uncle_window=[10, 100], max_uncles=[0, 1],
        uncle_strategy=["oldest"], init_dest=["common"], replicates=1,
        base={"k": 8, "epochs": 3},
    )
    configs = sweep.expand()
    u0 = [c for c in configs if c.max_uncles == 0]
    u1 = [c for c in configs if c.max_uncles == 1]
    assert len(u0) == 1                                    # W collapsed for U=0
    assert {c.uncle_window for c in u1} == {10, 100}       # both W kept for U=1


def test_unknown_sweep_key_rejected():
    with pytest.raises(ValueError, match="unknown sweep keys"):
        SweepConfig.from_dict({"latencies": [0, 1], "base": {}})  # typo: latencies vs latency


def test_from_dict_roundtrip_ok():
    sw = SweepConfig.from_dict({"latency": [0, 3], "max_uncles": [0, 2], "replicates": 2,
                                "base": {"k": 8, "epochs": 4}})
    assert sw.latency == [0, 3] and sw.replicates == 2 and sw.base["k"] == 8


def test_key_covers_every_field():
    # Guard against the silent shared-RNG bug: key() must reflect all run-affecting fields.
    # root_seed enters _entropy separately; windowed_fork_choice is a pure compute
    # optimisation (no RNG, identical results) so it is intentionally not in key().
    # early_stop is truncation-only (per-epoch RNG streams are pre-spawned, so the epochs
    # that DO run are bit-identical to a full run's prefix) — intentionally excluded from key().
    ignored = {"root_seed", "windowed_fork_choice", "prune_arrival", "early_stop"}
    names = {f.name for f in dataclasses.fields(SimConfig)} - ignored
    a = SimConfig()
    for name in names:
        cur = getattr(a, name)
        alt = _perturb(cur)
        b = dataclasses.replace(a, **{name: alt})
        assert a.key() != b.key(), f"key() does not distinguish field {name!r}"


def _perturb(v):
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + 1
    if isinstance(v, float):
        # stay inside [0, 1]-capped fields (e.g. jitter_frac defaults to 1.0)
        return v - 0.001 if v >= 1.0 else v + 0.001
    flips = {
        "uniform": "pareto", "oldest": "random", "full_mesh": "regular",
        "fixed": "exp", "common": "heterogeneous", "suppress": "withhold",
        "exp": "poisson",   # jitter_dist
        "sine": "ramp",     # churn_mode
    }
    if isinstance(v, str) and v in flips:
        return flips[v]
    return v
