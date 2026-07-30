"""Concurrency / saturation benchmark: the machine's *measured* sustained
solve and verify capacity under parallel load.

`dosprotect.py` reports *per-core* figures derived as 1/latency from a single
serial operation -- it never runs anything concurrently, so multiplying by the
core count over-estimates (Equi-X solving is memory-hard, so N parallel solvers
contend for cache/memory bandwidth and scale sub-linearly).

This module answers the complementary, measured question: run N worker
processes at once, for N stepping up a ladder to the core count, and measure the
aggregate throughput at each level. That yields:

  * the real sustained solves/sec and verifies/sec the machine handles,
  * the "knee" -- the worker count at peak throughput, beyond which adding
    workers stops helping (bandwidth saturated),
  * a scaling efficiency vs. ideal linear scaling.

It is additive: it does not touch or replace the per-core DoS estimate.
"""
from __future__ import annotations

import math
import statistics
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .protocol import JobSpec, Result
from .registry import Adapter
from .runner import RunnerError, run


@dataclass
class LevelStat:
    workers: int                    # concurrency level attempted
    ok_workers: int                 # workers that returned a usable result
    per_worker_median_s: float      # median across workers of each worker's median op time
    aggregate_ops_per_sec: float    # sum over workers of 1/(that worker's median op time)
    per_worker_ops_per_sec: float   # aggregate / ok_workers
    scaling_efficiency: float       # aggregate(N) / (N * single-worker baseline)
    total_peak_rss_kb: int          # summed peak RSS across the concurrent workers


@dataclass
class ConcResult:
    device: str
    impl: str
    operation: str
    nproc: int
    reps: int
    challenge: str
    baseline_ops_per_sec: float     # single-worker (level 1) throughput
    peak_ops_per_sec: float         # best aggregate across levels
    knee_workers: int               # worker count at peak aggregate throughput
    levels: list[LevelStat] = field(default_factory=list)
    error: Optional[str] = None


def _ladder(max_workers: int, explicit: Optional[list[int]] = None) -> list[int]:
    """Worker-count ladder: 1, 2, 4, 8, ... capped at max_workers, with
    max_workers itself always included (so an 6- or 10-core box gets its top).
    Explicit lists are clamped to [1, max_workers]; level 1 is always included
    because it anchors the per-worker baseline every derived figure needs."""
    if explicit:
        levels = sorted({n for n in explicit if 1 <= n <= max_workers})
        if not levels:
            raise ValueError(
                f"concurrency levels {explicit} all outside [1, {max_workers}]"
            )
        return sorted({1, *levels})
    levels = []
    n = 1
    while n < max_workers:
        levels.append(n)
        n *= 2
    levels.append(max_workers)
    return sorted(set(levels))


def _worker_median_s(res: Result) -> Optional[float]:
    """One worker's median per-op time in seconds (runner-internal timing, which
    already excludes process startup and warmup). None if the worker had no runs."""
    if not res.ok or not res.runs:
        return None
    walls = [float(r.wall_ns) for r in res.runs if r.wall_ns > 0]
    if not walls:
        return None
    return statistics.median(walls) / 1e9


def _measure_level(
    adapter: Adapter,
    make_spec: Callable[[], JobSpec],
    n: int,
    repo_root: Path,
    timeout: float,
) -> tuple[list[float], int]:
    """Launch n identical workers concurrently; return (per-worker median seconds
    for the workers that succeeded, summed peak RSS KB across all workers).

    Real subprocesses run in parallel: the thread pool only blocks on their I/O,
    so contention is measured on the actual runner binary, not in Python."""
    def one(_i: int) -> Optional[Result]:
        try:
            return run(adapter, make_spec(), repo_root, timeout=timeout)
        except RunnerError:
            return None

    with ThreadPoolExecutor(max_workers=n) as pool:
        results = list(pool.map(one, range(n)))

    medians: list[float] = []
    rss = 0
    for res in results:
        if res is None:
            continue
        rss += max(0, res.peak_rss_kb)
        m = _worker_median_s(res)
        if m and m > 0:
            medians.append(m)
    return medians, rss


def _solution_for(adapter: Adapter, challenge: str, repo_root: Path, timeout: float) -> Optional[str]:
    """Solve `challenge` once to obtain a solution to feed the verify workers."""
    try:
        r = run(adapter, JobSpec(operation="solve", runtime="try-compile",
                                 repetitions=1, warmup=0, challenge_hex=challenge),
                repo_root, timeout=timeout)
    except RunnerError:
        return None
    sols = r.solutions_hex or []
    return sols[0] if sols else None


def _first_env(adapter: Adapter, challenge: str, repo_root: Path, timeout: float) -> dict[str, Any]:
    """Cheap single run purely to learn the executing device (env) for labeling.
    Uses a 1-rep solve: always valid (a verify probe would need a solution and
    fail, silently mislabeling the device)."""
    try:
        r = run(adapter, JobSpec(operation="solve", runtime="try-compile", repetitions=1,
                                 warmup=0, challenge_hex=challenge),
                repo_root, timeout=timeout)
        return r.env
    except RunnerError:
        return {}


# Each worker's runner-internal measured window must dwarf the multi-ms
# subprocess start skew, or the workers' windows barely overlap and the
# "measured under concurrency" number degenerates to serial-rate x N.
MIN_WINDOW_S = 0.5


def measure(
    adapter: Adapter,
    operation: str,
    challenge: str,
    solution_hex: Optional[str],
    max_workers: int,
    reps: int,
    warmup: int,
    repo_root: Path,
    device_label: str,
    timeout: float,
    levels: Optional[list[int]] = None,
    min_window_s: float = MIN_WINDOW_S,
) -> ConcResult:
    """Run the saturation ladder for one (impl, operation) and summarize it."""
    def make_spec(n_reps: int) -> JobSpec:
        return JobSpec(
            operation=operation,
            runtime="try-compile",
            repetitions=n_reps,
            warmup=warmup,
            challenge_hex=challenge,
            solution_hex=solution_hex if operation == "verify" else None,
        )

    result = ConcResult(
        device=device_label, impl=adapter.name, operation=operation,
        nproc=max_workers, reps=reps, challenge=challenge,
        baseline_ops_per_sec=0.0, peak_ops_per_sec=0.0, knee_workers=0,
    )

    # Calibrate: one uncontended run tells us the per-op time, from which we
    # size reps so every worker's measured window is at least min_window_s
    # (fast ops like verify at ~17us need tens of thousands of reps to overlap
    # meaningfully; slow ops like solve already exceed the window with a few).
    cal_medians, _ = _measure_level(adapter, lambda: make_spec(reps), 1, repo_root, timeout)
    eff_reps = reps
    if cal_medians and min_window_s > 0:
        eff_reps = max(reps, math.ceil(min_window_s / cal_medians[0]))
    result.reps = eff_reps

    baseline = 0.0
    for n in _ladder(max_workers, levels):
        medians, rss = _measure_level(adapter, lambda: make_spec(eff_reps), n, repo_root, timeout)
        if not medians:
            result.levels.append(LevelStat(n, 0, 0.0, 0.0, 0.0, 0.0, rss))
            continue
        aggregate = sum(1.0 / m for m in medians)
        if baseline == 0.0:
            # Per-WORKER throughput anchors ideal scaling; falling back to a
            # level n>1 must divide by n or every derived figure is n-fold off.
            baseline = aggregate / n
        ideal = baseline * n
        result.levels.append(LevelStat(
            workers=n,
            ok_workers=len(medians),
            per_worker_median_s=statistics.median(medians),
            aggregate_ops_per_sec=aggregate,
            per_worker_ops_per_sec=aggregate / len(medians),
            scaling_efficiency=(aggregate / ideal) if ideal > 0 else 0.0,
            total_peak_rss_kb=rss,
        ))

    result.baseline_ops_per_sec = baseline
    usable = [lv for lv in result.levels if lv.aggregate_ops_per_sec > 0]
    if usable:
        peak = max(usable, key=lambda lv: lv.aggregate_ops_per_sec)
        result.peak_ops_per_sec = peak.aggregate_ops_per_sec
        result.knee_workers = peak.workers
    else:
        result.error = "no worker produced a usable measurement"
    return result


def run_concurrency(
    cfg: dict[str, Any],
    adapters: dict[str, Adapter],
    repo_root: Path,
    device_resolver: Callable[[dict[str, Any]], str],
    timeout: float,
) -> list[ConcResult]:
    """Drive the concurrency benchmark from a `[concurrency]` config block.

    cfg keys (all optional): operations (["solve","verify"]), impls ([] = all
    available), challenge ("deadbeef"), reps (40), warmup (5), max_workers
    (0 = os.cpu_count()), levels ([] = auto power-of-two ladder)."""
    import os

    operations = list(cfg.get("operations", ["solve", "verify"]))
    challenge = str(cfg.get("challenge", "deadbeef"))
    reps = int(cfg.get("reps", 40))
    warmup = int(cfg.get("warmup", 5))
    max_workers = int(cfg.get("max_workers", 0)) or (os.cpu_count() or 4)
    levels = [int(x) for x in cfg.get("levels", [])] or None
    want_impls = list(cfg.get("impls", [])) or list(adapters.keys())

    impls = [(n, adapters[n]) for n in want_impls if n in adapters]
    out: list[ConcResult] = []
    if not impls:
        return out

    # Learn the device label once from a cheap probe on the first impl.
    probe_env = _first_env(impls[0][1], challenge, repo_root, timeout)
    device_label = device_resolver(probe_env)

    # A verify needs a valid solution; solve once (impl-independent) and reuse.
    solution_hex = None
    if "verify" in operations:
        for _, a in impls:
            solution_hex = _solution_for(a, challenge, repo_root, timeout)
            if solution_hex:
                break

    for op in operations:
        if op == "verify" and not solution_hex:
            continue  # nothing to verify against; skip rather than error the run
        for name, adapter in impls:
            out.append(measure(
                adapter, op, challenge, solution_hex, max_workers, reps, warmup,
                repo_root, device_label, timeout, levels,
            ))
    return out


def write_csv(results: list[ConcResult], path: Path) -> None:
    import csv

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "device", "impl", "operation", "workers", "ok_workers",
            "per_worker_median_s", "aggregate_ops_per_sec",
            "per_worker_ops_per_sec", "scaling_efficiency", "total_peak_rss_kb",
        ])
        for r in results:
            for lv in r.levels:
                w.writerow([
                    r.device, r.impl, r.operation, lv.workers, lv.ok_workers,
                    f"{lv.per_worker_median_s:.9f}", f"{lv.aggregate_ops_per_sec:.3f}",
                    f"{lv.per_worker_ops_per_sec:.3f}", f"{lv.scaling_efficiency:.4f}",
                    lv.total_peak_rss_kb,
                ])


def read_csv(path: Path) -> list[ConcResult]:
    """Reconstruct ConcResults from a concurrency.csv (the inverse of write_csv),
    so `combine` can fold in each device's measured saturation ladder.

    The CSV is per-level; the per-result summary fields (baseline/peak/knee/nproc)
    are re-derived from the levels — baseline is the single-worker aggregate,
    nproc the top level, and peak/knee the best aggregate — matching how
    `measure()` computed them originally."""
    import csv

    def _i(row, k):
        v = row.get(k, "")
        return int(v) if v not in ("", None) else 0

    def _f(row, k):
        v = row.get(k, "")
        return float(v) if v not in ("", None) else 0.0

    by_key: dict[tuple[str, str, str], ConcResult] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["device"], row["impl"], row["operation"])
            res = by_key.get(key)
            if res is None:
                res = ConcResult(
                    device=row["device"], impl=row["impl"], operation=row["operation"],
                    nproc=0, reps=0, challenge="", baseline_ops_per_sec=0.0,
                    peak_ops_per_sec=0.0, knee_workers=0,
                )
                by_key[key] = res
            res.levels.append(LevelStat(
                workers=_i(row, "workers"),
                ok_workers=_i(row, "ok_workers"),
                per_worker_median_s=_f(row, "per_worker_median_s"),
                aggregate_ops_per_sec=_f(row, "aggregate_ops_per_sec"),
                per_worker_ops_per_sec=_f(row, "per_worker_ops_per_sec"),
                scaling_efficiency=_f(row, "scaling_efficiency"),
                total_peak_rss_kb=_i(row, "total_peak_rss_kb"),
            ))
    for res in by_key.values():
        res.levels.sort(key=lambda lv: lv.workers)
        res.nproc = max((lv.workers for lv in res.levels), default=0)
        base = next((lv for lv in res.levels if lv.workers == 1), None)
        res.baseline_ops_per_sec = base.aggregate_ops_per_sec if base else 0.0
        usable = [lv for lv in res.levels if lv.aggregate_ops_per_sec > 0]
        if usable:
            peak = max(usable, key=lambda lv: lv.aggregate_ops_per_sec)
            res.peak_ops_per_sec = peak.aggregate_ops_per_sec
            res.knee_workers = peak.workers
    return list(by_key.values())
