"""Compiler-flag variants ride on the multi-implementation machinery: several C
builds register as distinct impls (from a second manifest dir) and expand into
comparable cells."""
from equix_bench.config import Config, expand
from equix_bench.registry import Adapter, load_manifests

_MANIFEST = (
    'name = "{name}"\n'
    'exec = "build/runners/c/equix_runner"\n'
    'protocol_version = 1\n'
    'capabilities = ["solve", "hashx_compile"]\n'
    'runtimes = ["try-compile", "interpret"]\n'
)


def test_load_manifests_merges_multiple_dirs(tmp_path):
    d1, d2 = tmp_path / "examples", tmp_path / "generated"
    d1.mkdir()
    d2.mkdir()
    (d1 / "base.manifest.toml").write_text(_MANIFEST.format(name="equix-c"))
    (d2 / "o2.manifest.toml").write_text(_MANIFEST.format(name="equix-c-gcc-o2"))
    (d2 / "o3.manifest.toml").write_text(_MANIFEST.format(name="equix-c-gcc-o3"))
    adapters = load_manifests([d1, d2])
    assert set(adapters) == {"equix-c", "equix-c-gcc-o2", "equix-c-gcc-o3"}
    # a non-existent dir is simply skipped
    assert set(load_manifests([d1, tmp_path / "nope"])) == {"equix-c"}


def test_expand_sweeps_variant_impls():
    names = ["equix-c-gcc-o0", "equix-c-gcc-o3", "equix-c-clang-o3"]
    adapters = {
        n: Adapter(name=n, exec=["/bin/true"], protocol_version=1,
                   capabilities=["solve"], runtimes=["try-compile"], env={})
        for n in names
    }
    cfg = Config(
        warmup=1, repetitions=2, impls=names,
        jobs=[{"operation": "solve", "runtimes": ["try-compile"],
               "challenges": ["deadbeef", "cafe"]}],
    )
    cells, warnings = expand(cfg, adapters)
    # 3 variants x 2 challenges x 1 runtime
    assert len(cells) == 6
    assert {c.impl for c in cells} == set(names)
    assert not warnings


def test_expand_warns_on_unsupported_runtime():
    adapters = {
        "equix-c-gcc-o3": Adapter(name="equix-c-gcc-o3", exec=["/bin/true"],
                                  protocol_version=1, capabilities=["solve"],
                                  runtimes=["try-compile"], env={}),
    }
    cfg = Config(warmup=1, repetitions=1, impls=["equix-c-gcc-o3"],
                 jobs=[{"operation": "solve", "runtimes": ["must-compile"],
                        "challenges": ["deadbeef"]}])
    cells, warnings = expand(cfg, adapters)
    assert cells == []
    assert any("must-compile" in w for w in warnings)
