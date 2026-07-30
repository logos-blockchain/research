"""The concurrency benchmark must MEASURE aggregate parallel throughput and the
saturation knee -- distinct from dosprotect.py's per-core 1/latency estimate."""
from pathlib import Path

import equix_bench.concurrency as conc
from equix_bench.concurrency import _ladder, _worker_median_s, measure
from equix_bench.protocol import Result, Run
from equix_bench.registry import Adapter


def _result(wall_ns, ok=True, rss=1000):
    runs = [
        Run(index=i, wall_ns=w, solutions=1, compile_ns=0, attempts=0,
            achieved_effort=0, verify_result="OK")
        for i, w in enumerate(wall_ns)
    ]
    return Result(
        ok=ok, impl_name="equix-c", impl_version="1", impl_commit="c",
        operation="solve", runtime_requested="try-compile", runtime_effective="compiled",
        env={}, runs=runs, solutions_hex=["ab"], peak_rss_kb=rss, error=None,
    )


def _adapter():
    return Adapter(name="equix-c", exec=["/bin/true"], protocol_version=1,
                   capabilities=[], runtimes=[], env={})


def test_ladder_powers_of_two_plus_top():
    assert _ladder(1) == [1]
    assert _ladder(4) == [1, 2, 4]
    assert _ladder(8) == [1, 2, 4, 8]
    assert _ladder(6) == [1, 2, 4, 6]          # non-power-of-two core count still included
    assert _ladder(10, [1, 3, 10]) == [1, 3, 10]  # explicit levels honored
    assert _ladder(10, [3, 10]) == [1, 3, 10]  # level 1 forced in (baseline anchor)
    import pytest
    with pytest.raises(ValueError):
        _ladder(14, [16, 32])                  # all out of range -> loud error, not empty


def test_worker_median_seconds():
    assert _worker_median_s(_result([10, 20, 30])) == 20 / 1e9
    assert _worker_median_s(_result([], ok=True)) is None
    assert _worker_median_s(_result([10], ok=False)) is None


def test_measure_aggregates_throughput_and_scaling(monkeypatch):
    # No contention in the fake: each worker sustains 100 ops/s (10 ms/op), so
    # aggregate must scale linearly and peak at the max worker count.
    monkeypatch.setattr(conc, "run",
                        lambda a, s, r, timeout=900.0: _result([10_000_000] * 3))
    res = measure(_adapter(), "solve", "deadbeef", None, max_workers=4, reps=3,
                  warmup=1, repo_root=Path("."), device_label="cpuX", timeout=10,
                  levels=[1, 2, 4])

    assert res.baseline_ops_per_sec == 100.0
    agg = {lv.workers: lv.aggregate_ops_per_sec for lv in res.levels}
    assert agg == {1: 100.0, 2: 200.0, 4: 400.0}
    assert res.peak_ops_per_sec == 400.0 and res.knee_workers == 4
    # perfect linear scaling -> efficiency 1.0 at every level
    assert all(abs(lv.scaling_efficiency - 1.0) < 1e-9 for lv in res.levels)
    # per-level RSS is summed across the concurrent workers
    assert {lv.workers: lv.total_peak_rss_kb for lv in res.levels} == {1: 1000, 2: 2000, 4: 4000}


def test_baseline_falls_back_per_worker_when_level1_fails(monkeypatch):
    # Level 1 fails, level 2 succeeds at 100 ops/s per worker: the baseline must
    # anchor to PER-WORKER throughput (100), not the 2-worker aggregate (200) --
    # otherwise every efficiency/naive-Nx figure is off by the level's width.
    calls = {"n": 0}
    def fake_run(a, s, r, timeout=900.0):
        calls["n"] += 1
        if calls["n"] <= 2:  # calibration + the level-1 worker fail
            return _result([], ok=False)
        return _result([10_000_000] * 3)
    monkeypatch.setattr(conc, "run", fake_run)
    res = measure(_adapter(), "solve", "deadbeef", None, max_workers=2, reps=3,
                  warmup=1, repo_root=Path("."), device_label="cpuX", timeout=10,
                  levels=[1, 2], min_window_s=0)
    assert res.baseline_ops_per_sec == 100.0          # per-worker, not aggregate
    lv2 = [lv for lv in res.levels if lv.workers == 2][0]
    assert abs(lv2.scaling_efficiency - 1.0) < 1e-9   # 200/(100*2), not 200/(200*2)


def test_measure_handles_failed_workers(monkeypatch):
    monkeypatch.setattr(conc, "run",
                        lambda a, s, r, timeout=900.0: _result([], ok=False))
    res = measure(_adapter(), "solve", "deadbeef", None, max_workers=2, reps=3,
                  warmup=1, repo_root=Path("."), device_label="cpuX", timeout=10,
                  levels=[1, 2])
    assert res.peak_ops_per_sec == 0.0
    assert res.error == "no worker produced a usable measurement"
    assert all(lv.aggregate_ops_per_sec == 0.0 for lv in res.levels)
