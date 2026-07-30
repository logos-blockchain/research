import json

import pytest

from equix_bench.protocol import SCHEMA_VERSION, JobSpec, Result


def test_jobspec_omits_none_fields():
    d = json.loads(JobSpec(operation="solve", runtime="interpret", challenge_hex="ab").to_json())
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["operation"] == "solve"
    assert d["challenge_hex"] == "ab"
    assert "solution_hex" not in d  # None fields are dropped from the wire form


def test_result_rejects_wrong_schema():
    with pytest.raises(ValueError):
        Result.from_dict({"schema_version": 999})


def test_result_parse_roundtrip():
    d = {
        "schema_version": 1,
        "ok": True,
        "impl": {"name": "x", "version": "1", "commit": "c", "runtime_effective": "compiled"},
        "operation": "solve",
        "runtime_requested": "try-compile",
        "runtime_effective": "compiled",
        "env": {"os": "linux"},
        "runs": [
            {"index": 0, "wall_ns": 10, "solutions": 4, "compile_ns": 0,
             "attempts": 0, "achieved_effort": 0, "verify_result": None},
            {"index": 1, "wall_ns": 20, "solutions": 4, "compile_ns": 0,
             "attempts": 0, "achieved_effort": 0, "verify_result": None},
        ],
        "solutions_hex": ["00" * 16],
        "peak_rss_kb": 100,
        "error": None,
    }
    r = Result.from_dict(d)
    assert r.ok and r.impl_name == "x"
    assert len(r.runs) == 2 and r.runs[1].wall_ns == 20
