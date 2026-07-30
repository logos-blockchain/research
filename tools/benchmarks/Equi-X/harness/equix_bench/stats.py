"""Aggregate a runner Result's per-rep timings into summary statistics."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Optional

from .protocol import Result

# Equi-X solve: stage 0 evaluates the HashX function once for every index in the
# 16-bit index space (equix solver_heap.h: INDEX_SPACE = 1 << 16), which dominates
# the per-solve hashing. Used to derive an effective hash-rate from throughput.
HASHX_PER_SOLVE = 1 << 16


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    # Nearest-rank method: rank = ceil(P/100 * N).
    k = max(1, min(len(s), math.ceil(pct / 100.0 * len(s))))
    return s[k - 1]


@dataclass
class CellStats:
    impl: str
    operation: str
    runtime_requested: str
    runtime_effective: Optional[str]
    label: dict[str, Any]
    reps: int
    ok: bool
    # wall-time stats (ns)
    min_ns: float
    median_ns: float
    mean_ns: float
    stddev_ns: float
    p95_ns: float
    # derived / auxiliary
    solutions_mean: float
    compile_median_ns: float
    attempts_mean: float
    achieved_effort_mean: float
    solves_per_sec: float
    hashes_per_sec: float
    peak_rss_kb: int
    verify_result: Optional[str]
    walls: list[float] = field(default_factory=list)  # per-rep wall_ns
    error: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    # executing hardware (see device.py)
    device_label: str = "host"
    device_type: str = "cpu"
    device_name: str = "unknown"
    device_arch: str = "unknown"


def summarize(
    impl: str,
    operation: str,
    runtime_requested: str,
    label: dict[str, Any],
    result: Result,
    device: Optional[dict[str, Any]] = None,
) -> CellStats:
    device = device or {}
    dkw = dict(
        device_label=device.get("label", "host"),
        device_type=device.get("type", "cpu"),
        device_name=device.get("name", result.env.get("cpu", "unknown")),
        device_arch=device.get("arch", result.env.get("arch", "unknown")),
    )
    if not result.ok or not result.runs:
        return CellStats(
            impl=impl,
            operation=operation,
            runtime_requested=runtime_requested,
            runtime_effective=result.runtime_effective,
            label=label,
            reps=0,
            ok=False,
            min_ns=0, median_ns=0, mean_ns=0, stddev_ns=0, p95_ns=0,
            solutions_mean=0, compile_median_ns=0, attempts_mean=0,
            achieved_effort_mean=0, solves_per_sec=0, hashes_per_sec=0,
            peak_rss_kb=result.peak_rss_kb,
            verify_result=None,
            error=result.error or "no runs",
            **dkw,
        )

    walls = [float(r.wall_ns) for r in result.runs]
    compiles = [float(r.compile_ns) for r in result.runs]
    sols = [float(r.solutions) for r in result.runs]
    attempts = [float(r.attempts) for r in result.runs]
    efforts = [float(r.achieved_effort) for r in result.runs]

    median_ns = statistics.median(walls)
    mean_ns = statistics.fmean(walls)
    stddev_ns = statistics.pstdev(walls) if len(walls) > 1 else 0.0

    # throughput: solves/sec from median solve time; hash-rate from solves/sec.
    solves_per_sec = 1e9 / median_ns if operation == "solve" and median_ns > 0 else 0.0
    hashes_per_sec = solves_per_sec * HASHX_PER_SOLVE

    return CellStats(
        impl=impl,
        operation=operation,
        runtime_requested=runtime_requested,
        runtime_effective=result.runtime_effective,
        label=label,
        reps=len(result.runs),
        ok=True,
        min_ns=min(walls),
        median_ns=median_ns,
        mean_ns=mean_ns,
        stddev_ns=stddev_ns,
        p95_ns=_percentile(walls, 95),
        solutions_mean=statistics.fmean(sols),
        compile_median_ns=statistics.median(compiles),
        attempts_mean=statistics.fmean(attempts),
        achieved_effort_mean=statistics.fmean(efforts),
        solves_per_sec=solves_per_sec,
        hashes_per_sec=hashes_per_sec,
        peak_rss_kb=result.peak_rss_kb,
        verify_result=result.runs[-1].verify_result,
        walls=walls,
        **dkw,
    )
