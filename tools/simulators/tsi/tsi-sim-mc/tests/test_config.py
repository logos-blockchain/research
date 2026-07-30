import dataclasses

import pytest

from tsi_sim.config import SimConfig, SweepConfig


def test_expand_cardinality_and_u0_strategy_dedup():
    sweep = SweepConfig(
        n_nodes=[1000, 2000],
        stake_dist=["uniform"],
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
    {"stake_dist": "zipf"}, {"uncle_strategy": "newest"},
])
def test_validation_rejects_bad_fields(kwargs):
    with pytest.raises(ValueError):
        SimConfig(**kwargs)


def test_unknown_sweep_key_rejected():
    with pytest.raises(ValueError, match="unknown sweep keys"):
        SweepConfig.from_dict({"latencies": [0, 1], "base": {}})  # typo: latencies vs latency


def test_from_dict_roundtrip_ok():
    sw = SweepConfig.from_dict({"latency": [0, 3], "max_uncles": [0, 2], "replicates": 2,
                                "base": {"k": 8, "epochs": 4}})
    assert sw.latency == [0, 3] and sw.replicates == 2 and sw.base["k"] == 8


def test_key_covers_every_field():
    # Guard against the silent shared-RNG bug: key() must reflect all run-affecting fields.
    ignored = {"root_seed"}  # root_seed enters _entropy separately, not via key()
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
        return v + 0.001
    if v == "uniform":
        return "pareto"
    if v == "oldest":
        return "random"
    return v
