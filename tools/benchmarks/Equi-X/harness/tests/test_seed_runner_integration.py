"""Integration checks on the real runners' seed mode (skipped if not built).
The load-bearing property: because both impls derive challenges with STANDARD
SHA-256, the same seed yields the same challenge stream, so a seed-varied
measurement still compares the two implementations on identical inputs."""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
C = ROOT / "build/runners/c/equix_runner"
RUST = ROOT / "runners/rust/target/release/equix_runner"


def _run(binary, spec):
    p = subprocess.run([str(binary)], input=json.dumps(spec),
                       capture_output=True, text=True, timeout=120)
    return json.loads(p.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(not (C.exists() and RUST.exists()), reason="runners not built")
def test_seed_mode_derives_identical_challenges_across_impls():
    # challenge_0 = SHA256(seed): solving it in seed mode must give, in BOTH
    # impls, exactly the solutions of that derived challenge (fixed mode).
    seed = "abcd"
    derived = hashlib.sha256(bytes.fromhex(seed)).hexdigest()
    outs = {}
    for name, b in (("c", C), ("rust", RUST)):
        seeded = _run(b, {"schema_version": 1, "operation": "solve", "runtime": "interpret",
                          "repetitions": 1, "warmup": 0, "challenge_seed_hex": seed})
        fixed = _run(b, {"schema_version": 1, "operation": "solve", "runtime": "interpret",
                         "repetitions": 1, "warmup": 0, "challenge_hex": derived})
        # seed mode's first challenge IS sha256(seed): same solutions as fixed.
        assert sorted(seeded["solutions_hex"]) == sorted(fixed["solutions_hex"])
        outs[name] = sorted(seeded["solutions_hex"])
    # And both implementations agree on that derived challenge.
    assert outs["c"] == outs["rust"]


@pytest.mark.skipif(not RUST.exists(), reason="rust runner not built")
def test_seed_mode_verify_selfsolves_valid_tokens():
    # Seed-mode verify needs no solution_hex and every timed sample is a real,
    # accepted token (the runner self-solves each derived challenge).
    d = _run(RUST, {"schema_version": 1, "operation": "verify", "runtime": "try-compile",
                    "repetitions": 8, "warmup": 2, "challenge_seed_hex": "deadbeef"})
    assert d["ok"] and len(d["runs"]) == 8
    assert all(r["verify_result"] == "OK" for r in d["runs"])
