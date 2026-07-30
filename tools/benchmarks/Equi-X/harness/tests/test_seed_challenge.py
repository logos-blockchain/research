"""vary_challenge turns each configured challenge into a SEED: the runner derives
a fresh challenge per rep by SHA-256-chaining it, so measurements span many
challenges. These tests pin the harness wiring (config expansion, protocol
serialization, verify-resolution skip)."""
import json

from equix_bench.cli import _resolve_verify_solutions
from equix_bench.config import Config, expand
from equix_bench.protocol import JobSpec
from equix_bench.registry import Adapter


def _adapter(name, caps):
    return Adapter(name=name, exec=["/bin/true"], protocol_version=1,
                   capabilities=caps, runtimes=["interpret", "try-compile"], env={})


def test_expand_sets_seed_not_challenge_when_varied():
    cfg = Config(warmup=1, repetitions=5, impls=["x"],
                 jobs=[{"operation": "solve", "runtimes": ["interpret"],
                        "challenges": ["deadbeef", "cafe"], "vary_challenge": True}])
    cells, _ = expand(cfg, {"x": _adapter("x", ["solve"])})
    assert len(cells) == 2
    for c in cells:
        assert c.job.challenge_seed_hex in ("deadbeef", "cafe")
        assert c.job.challenge_hex is None          # seed replaces the fixed challenge
        assert c.label.get("varied") is True


def test_expand_fixed_challenge_when_not_varied():
    cfg = Config(warmup=1, repetitions=5, impls=["x"],
                 jobs=[{"operation": "solve", "runtimes": ["interpret"],
                        "challenges": ["deadbeef"]}])
    cells, _ = expand(cfg, {"x": _adapter("x", ["solve"])})
    assert cells[0].job.challenge_hex == "deadbeef"
    assert cells[0].job.challenge_seed_hex is None


def test_jobspec_serializes_seed_and_omits_none_challenge():
    d = json.loads(JobSpec(operation="solve", runtime="interpret",
                           challenge_seed_hex="abcd").to_json())
    assert d["challenge_seed_hex"] == "abcd"
    assert "challenge_hex" not in d                 # None fields dropped from the wire


def test_verify_resolution_skips_seed_mode_cells():
    # A seed-mode verify cell must pass through untouched (runner self-solves) —
    # never dropped for "no solution found", never sent to a solver.
    cfg = Config(warmup=1, repetitions=3, impls=["x"],
                 jobs=[{"operation": "verify", "runtimes": ["interpret"],
                        "challenges": ["deadbeef"], "vary_challenge": True}])
    cells, _ = expand(cfg, {"x": _adapter("x", ["verify"])})
    # adapters/repo_root are irrelevant here: seed cells short-circuit before any run.
    out, warnings = _resolve_verify_solutions(cells, {}, repo_root=None)
    assert len(out) == 1 and out[0].job.challenge_seed_hex == "deadbeef"
    assert warnings == []
