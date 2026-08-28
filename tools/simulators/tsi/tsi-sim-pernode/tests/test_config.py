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
    # OLD model: uncle_window is a live axis for U>0, but U=0 references no uncles so it
    # must collapse. (The countable model ignores uncle_window entirely — see the twin
    # test below.)
    sweep = SweepConfig(
        n_nodes=[100], stake_dist=["uniform"], topology=["blend"], degree=[6],
        link_latency_mean=[0.5], link_latency_dist=["geo"], blend_hops=[3],
        blend_delay_max=[4.0], uncle_window=[10, 100], max_uncles=[0, 1],
        uncle_strategy=["oldest"], init_dest=["common"], replicates=1,
        base={"k": 8, "epochs": 3, "uncle_model": "old"},
    )
    configs = sweep.expand()
    u0 = [c for c in configs if c.max_uncles == 0]
    u1 = [c for c in configs if c.max_uncles == 1]
    assert len(u0) == 1                                    # W collapsed for U=0
    assert {c.uncle_window for c in u1} == {10, 100}       # both W kept for U=1


def test_window_absorption_sweeps_and_ignored_axis_collapses():
    # COUNTABLE model: window_absorption is the live window axis; uncle_window is ignored
    # and must collapse. And vice versa for the old model (guarded above).
    sweep = SweepConfig(
        n_nodes=[100], stake_dist=["uniform"], topology=["blend"], degree=[6],
        link_latency_mean=[0.5], link_latency_dist=["geo"], blend_hops=[3],
        blend_delay_max=[4.0], uncle_window=[10, 100], window_absorption=[2.0, 4.0],
        max_uncles=[0, 1], uncle_strategy=["oldest"], init_dest=["common"], replicates=1,
        base={"k": 8, "epochs": 3},
    )
    configs = sweep.expand()
    u0 = [c for c in configs if c.max_uncles == 0]
    u1 = [c for c in configs if c.max_uncles == 1]
    assert len(u0) == 1                                          # all window knobs collapse
    assert {c.window_absorption for c in u1} == {2.0, 4.0}       # live axis kept for U=1
    assert {c.uncle_window for c in u1} == {10}                  # ignored axis collapsed


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
    # uncle_window is read ONLY by the old model; under the (default) countable model it is
    # an ignored field, deliberately left in the base tuple at its old position so that an
    # --old run's key stays byte-identical to historical keys.
    # paired_streams must NOT be in key(): it selects WHICH key the RNG root is derived from
    # (see seed_key), so putting it in key() would perturb every historical seed and break
    # --old bit-reproduction. Its own behaviour is pinned in test_rng.py.
    # ref_scope is a MEASUREMENT rule that consumes no RNG: both scopes read the same block
    # tree, so excluding it from key() is what makes the two arms share a tree and their
    # difference carry no sampling noise. Like selfish_lead_cap it changes results at an
    # unchanged key, which is why report §9 records what was re-measured for it.
    ignored = {"root_seed", "windowed_fork_choice", "prune_arrival", "early_stop",
               "uncle_window", "paired_streams", "ref_scope"}
    names = {f.name for f in dataclasses.fields(SimConfig)} - ignored
    a = SimConfig()
    for name in names:
        cur = getattr(a, name)
        alt = _perturb(cur)
        b = dataclasses.replace(a, **{name: alt})
        assert a.key() != b.key(), f"key() does not distinguish field {name!r}"
    # ... and uncle_window IS distinguished under the old model, where it is live.
    old = SimConfig(uncle_model="old")
    assert old.key() != dataclasses.replace(old, uncle_window=old.uncle_window + 1).key()
    # paired_streams leaves key() untouched but DOES change the seed derived from it.
    a_paired = dataclasses.replace(a, paired_streams=True)
    assert a.key() == a_paired.key()
    assert a.seed_key() != a_paired.seed_key()
    # ref_scope leaves both untouched: the tree is generated identically and only the
    # measurement differs, which is what makes a scope comparison exactly paired.
    a_chain = dataclasses.replace(a, ref_scope="chain")
    assert a.key() == a_chain.key()
    assert a.seed_key() == a_chain.seed_key()


def test_old_model_key_is_historical():
    # --old must bit-reproduce historical runs: its key is exactly the pre-uncle_model
    # tuple (no uncle_model / window_absorption entries), and the countable key extends it.
    old = SimConfig(uncle_model="old")
    new = SimConfig()
    assert new.key()[: len(old.key())] == old.key()
    assert new.key()[len(old.key()):] == ("countable", new.window_absorption)
    # window_absorption is ignored (and absent from key) under the old model...
    assert dataclasses.replace(old, window_absorption=2.0).key() == old.key()
    # ...and live under the countable model.
    assert dataclasses.replace(new, window_absorption=2.0).key() != new.key()


def test_effective_uncle_window():
    # countable: derived w_u = round(W / f); old: uncle_window taken directly.
    assert SimConfig(k=2160).effective_uncle_window == 300          # W=10, f=1/30
    assert SimConfig(k=2160, window_absorption=5.0).effective_uncle_window == 150
    assert SimConfig(uncle_model="old", uncle_window=42).effective_uncle_window == 42


def test_window_absorption_bound():
    import warnings

    with pytest.raises(ValueError):
        SimConfig(window_absorption=0.5)                            # W < 1 rejected
    with pytest.warns(RuntimeWarning, match="exceeds the spec bound"):
        SimConfig(k=8, window_absorption=10.0)                      # W > 0.6*k warns
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        SimConfig(k=2160, window_absorption=10.0)                   # full scale: silent
        SimConfig(k=8, uncle_model="old", uncle_window=300)         # old model: no bound


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
        "countable": "old",  # uncle_model
        # adversary_selection. Keyed by VALUE, so this only fires on fields that are currently
        # "random" — uncle_strategy defaults to "oldest" and keeps its own flip above.
        "random": "whale",
        "uncle": "parent",   # uncle_window_anchor
    }
    if isinstance(v, str) and v in flips:
        return flips[v]
    return v
