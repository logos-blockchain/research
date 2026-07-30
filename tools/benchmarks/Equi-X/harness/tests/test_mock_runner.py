"""The harness must speak the protocol to ANY conforming runner, and a job with
`repetitions=N` must yield exactly N timed entries (warmups excluded)."""
import sys

from equix_bench.protocol import JobSpec
from equix_bench.registry import Adapter
from equix_bench.runner import run

MOCK = '''#!/usr/bin/env python3
import sys, json
job = json.loads(sys.stdin.read())
reps = job.get("repetitions", 1)
# A conforming runner emits exactly `repetitions` timed runs (no warmups).
runs = [{"index": i, "wall_ns": 100 + i, "solutions": 1, "compile_ns": 0,
         "attempts": 0, "achieved_effort": 0, "verify_result": None} for i in range(reps)]
print(json.dumps({
    "schema_version": 1, "ok": True,
    "impl": {"name": "mock", "version": "0", "commit": "0", "runtime_effective": "interpreted"},
    "operation": job["operation"], "runtime_requested": job.get("runtime", "?"),
    "runtime_effective": "interpreted", "env": {}, "runs": runs,
    "solutions_hex": ["00" * 16], "peak_rss_kb": 42, "error": None}))
'''


def test_run_parses_conforming_runner(tmp_path):
    script = tmp_path / "mock.py"
    script.write_text(MOCK)
    adapter = Adapter(
        name="mock", exec=[sys.executable, str(script)], protocol_version=1,
        capabilities=["solve"], runtimes=["interpret"], env={},
    )
    r = run(adapter, JobSpec(operation="solve", runtime="interpret",
                             repetitions=5, warmup=2, challenge_hex="ab"), tmp_path)
    assert r.ok
    assert len(r.runs) == 5  # exactly repetitions; warmups excluded
    assert r.solutions_hex == ["00" * 16]


def test_run_tolerates_progress_lines(tmp_path):
    script = tmp_path / "chatty.py"
    script.write_text(MOCK.replace(
        'print(json.dumps({', 'print("progress: warming up", flush=True)\nprint(json.dumps({'
    ))
    adapter = Adapter(name="chatty", exec=[sys.executable, str(script)],
                      protocol_version=1, capabilities=["solve"], runtimes=["interpret"], env={})
    r = run(adapter, JobSpec(operation="solve", runtime="interpret",
                             repetitions=2, warmup=0, challenge_hex="ab"), tmp_path)
    assert r.ok and len(r.runs) == 2  # last stdout line is the JSON result
