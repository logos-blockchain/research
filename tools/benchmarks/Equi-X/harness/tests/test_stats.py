from equix_bench.protocol import Result
from equix_bench.stats import _percentile, summarize


def _make(walls):
    runs = [
        {"index": i, "wall_ns": w, "solutions": 4, "compile_ns": 0,
         "attempts": 0, "achieved_effort": 0, "verify_result": None}
        for i, w in enumerate(walls)
    ]
    return Result.from_dict({
        "schema_version": 1, "ok": True,
        "impl": {"name": "x", "version": "1", "commit": "c", "runtime_effective": "compiled"},
        "operation": "solve", "runtime_requested": "try-compile",
        "runtime_effective": "compiled", "env": {}, "runs": runs,
        "solutions_hex": None, "peak_rss_kb": 100, "error": None,
    })


def test_percentile_nearest_rank():
    assert _percentile([1, 2, 3, 4, 5], 95) == 5
    assert _percentile([1, 2, 3, 4, 5], 50) == 3
    assert _percentile([], 95) == 0.0


def test_summarize_basic():
    s = summarize("x", "solve", "try-compile", {}, _make([10, 20, 30]))
    assert s.ok and s.reps == 3
    assert s.min_ns == 10 and s.median_ns == 20
    assert s.solves_per_sec > 0  # 1e9 / 20 ns
    assert s.walls == [10, 20, 30]


def test_summarize_handles_failure():
    r = Result.from_dict({
        "schema_version": 1, "ok": False,
        "impl": {"name": "x", "version": "1", "commit": "c", "runtime_effective": None},
        "operation": "solve", "runtime_requested": "must-compile",
        "runtime_effective": None, "env": {}, "runs": [],
        "solutions_hex": None, "peak_rss_kb": 0, "error": "boom",
    })
    s = summarize("x", "solve", "must-compile", {}, r)
    assert not s.ok and s.error == "boom"
