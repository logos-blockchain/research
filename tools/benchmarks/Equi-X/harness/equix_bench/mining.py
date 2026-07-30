"""Mining-rate benchmark: how fast can tokens (effort-qualified solutions) be
minted at a given difficulty, on one core and on the whole machine.

This is the measured basis for the "control the mint rate by setting difficulty"
use case. It differs from the plain effort sweep in two ways that make it a real
statistical measurement rather than a single anecdote:

  * The runner's effort search is DETERMINISTIC from `nonce_start` (every rep
    restarts at the same nonce), so repetitions alone re-time one identical
    search. Here each sample uses a DISTINCT `nonce_start`, spaced beyond
    `max_attempts` so the search ranges never overlap -- independent draws from
    the geometric token-finding process, which we average.
  * It measures the whole-machine mint rate directly: `workers` (= core count)
    independent searches run at once, and we sum their token rates.

Outputs, per difficulty E (all POOLED estimators — total tokens over total busy
seconds, failed searches charged to the denominator; a mean of per-sample 1/t
ratios would carry a +6..25% Jensen-style upward bias at the CVs we measure):
  tokens_per_sec_1core     successes / total busy seconds, sequential  [1 core]
  tokens_per_sec_machine   workers * minted / total busy seconds       [N cores]
  attempts_mean            attempts per token, pooled over every search
"""
from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .protocol import JobSpec, Result
from .registry import Adapter
from .runner import RunnerError, run

# Nonce range reserved per sample/worker; must exceed any single token's attempts
# so independent searches never touch the same nonces.
STRIDE = 4_000_000


@dataclass
class MiningPoint:
    effort: int
    samples: int                    # independent 1-core samples that succeeded
    token_s_mean: float             # mean seconds to mint one token [1 core]
    token_s_median: float
    token_s_stddev: float
    attempts_mean: float            # POOLED over 1-core samples AND worker mints
    achieved_mean: float
    tokens_per_sec_1core: float     # successes / total busy seconds [1 core]
    workers: int
    ok_workers: int
    tokens_per_sec_machine: float   # pooled: workers * minted / total busy s
    scaling_efficiency: float       # machine / (workers * 1core rate)
    failed_searches: int = 0        # searches that hit max_attempts w/o a token
    # Message sizes, MEASURED from real minted tokens' wire bytes. The design
    # predicts both are constant in E (a solution is always 8 x u16 = 16 bytes;
    # the nonce is a protocol constant): min==max demonstrates it.
    solution_bytes_min: int = 0
    solution_bytes_max: int = 0
    nonce_bytes_wire: int = 0


@dataclass
class MiningResult:
    device: str
    impl: str
    challenge_base: str
    nproc: int
    points: list[MiningPoint] = field(default_factory=list)
    error: Optional[str] = None


def _effort_spec(base: str, effort: int, nonce_start: int, nonce_bytes: int,
                 reps: int, warmup: int, max_attempts: int) -> JobSpec:
    return JobSpec(
        operation="effort",
        runtime="try-compile",          # fastest available path per impl
        repetitions=reps,
        warmup=warmup,
        challenge_base_hex=base,
        nonce_bytes=nonce_bytes,
        nonce_start=nonce_start,
        target_effort=effort,
        max_attempts=max_attempts,
    )


def _one_token(adapter: Adapter, base: str, effort: int, nonce_start: int,
               nonce_bytes: int, max_attempts: int, repo_root: Path,
               timeout: float) -> Optional[tuple[bool, float, int, int, tuple[int, int]]]:
    """Search one fresh nonce range for a token. Returns (reached_target,
    seconds, attempts, achieved, (solution_bytes, nonce_bytes_wire)) — elapsed
    time is reported even when the target was NOT reached, so callers can charge
    failed searches to the denominator instead of silently conditioning the rate
    on success. Sizes are (0, 0) when no token was minted.
    None only when the runner itself errored (no timing available)."""
    try:
        r = run(adapter, _effort_spec(base, effort, nonce_start, nonce_bytes, 1, 0, max_attempts),
                repo_root, timeout=timeout)
    except RunnerError:
        return None
    if not r.ok or not r.runs:
        return None
    run0 = r.runs[0]
    if run0.wall_ns <= 0:
        return None
    # Wire sizes of the actual minted token (hex chars / 2 = bytes).
    sol_b = len(r.solutions_hex[0]) // 2 if r.solutions_hex else 0
    nonce_b = len(r.winning_nonce_hex) // 2 if r.winning_nonce_hex else 0
    return (run0.achieved_effort >= effort, run0.wall_ns / 1e9,
            run0.attempts, run0.achieved_effort, (sol_b, nonce_b))


def _worker_batch(adapter: Adapter, base: str, effort: int, nonce_start: int,
                  count: int, nonce_bytes: int, max_attempts: int,
                  repo_root: Path, timeout: float) -> tuple[int, float, int, int, list[tuple[int, int]]]:
    """One concurrent worker STREAMING `count` searches over advancing nonce
    ranges (like a real miner). Returns (tokens_minted, total_busy_seconds,
    attempts_total, failed_searches, token_sizes). Failed searches contribute
    their full solve time to the denominator — a real miner pays for them too."""
    minted, total, attempts, failed = 0, 0.0, 0, 0
    sizes: list[tuple[int, int]] = []
    for k in range(count):
        got = _one_token(adapter, base, effort, nonce_start + k * STRIDE, nonce_bytes,
                         max_attempts, repo_root, timeout)
        if got is None:
            continue
        ok, secs, atts, _ach, size = got
        total += secs
        attempts += atts
        if ok:
            minted += 1
            sizes.append(size)
        else:
            failed += 1
    return (minted, total, attempts, failed, sizes)


def measure_point(adapter: Adapter, base: str, effort: int, samples: int,
                  workers: int, tokens_per_worker: int, nonce_bytes: int,
                  max_attempts: int, repo_root: Path, timeout: float) -> MiningPoint:
    if max_attempts > STRIDE:
        raise ValueError(
            f"max_attempts ({max_attempts}) must not exceed STRIDE ({STRIDE}); "
            "independent nonce ranges would overlap"
        )

    # --- 1-core: `samples` independent, sequential searches (distinct nonces) ---
    secs: list[float] = []          # successful token times
    attempts_all: list[int] = []    # attempts, pooled over ALL mints (see below)
    achieved: list[int] = []
    all_sizes: list[tuple[int, int]] = []  # (solution_bytes, nonce_bytes) per token
    fail_s, fails = 0.0, 0
    for s in range(samples):
        got = _one_token(adapter, base, effort, s * STRIDE, nonce_bytes,
                          max_attempts, repo_root, timeout)
        if got is None:
            continue
        ok, t, atts, ach, size = got
        if ok:
            secs.append(t); attempts_all.append(atts); achieved.append(ach)
            all_sizes.append(size)
        else:
            fail_s += t; fails += 1

    if not secs:
        return MiningPoint(effort, 0, 0, 0, 0, 0, 0, 0, workers, 0, 0, 0, fails)

    # Pooled rate: total tokens over total busy time (failed searches included
    # in the denominator — a miner pays for them too). Stable for the
    # heavy-tailed token-time distribution, unlike a mean of 1/t ratios.
    token_s_mean = statistics.fmean(secs)
    onecore_rate = len(secs) / (sum(secs) + fail_s)

    # --- whole machine: `workers` concurrent streams on disjoint nonce ranges ---
    def one(w: int) -> tuple[int, float, int, int]:
        start = (samples + w * tokens_per_worker) * STRIDE
        return _worker_batch(adapter, base, effort, start, tokens_per_worker,
                             nonce_bytes, max_attempts, repo_root, timeout)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        batches = list(pool.map(one, range(workers)))

    # Pooled machine estimator: workers x (all tokens / all busy seconds).
    # Summing per-worker m/t ratios (few heavy-tailed samples each) carries a
    # +6..25% Jensen-style upward bias at the CVs we measure; pooling first
    # reduces the residual bias to ~+1% at 70 mints.
    minted = sum(b[0] for b in batches)
    busy = sum(b[1] for b in batches)
    ok_workers = sum(1 for b in batches if b[0] > 0)
    w_fails = sum(b[3] for b in batches)
    machine_rate = (workers * minted / busy) if busy > 0 else 0.0
    # Attempts per TOKEN, pooled across every search (1-core + workers, failed
    # searches' attempts charged to the numerator): the real cost of a token,
    # at ~8x the sample size of the 1-core batch alone.
    total_attempts = sum(attempts_all) + sum(b[2] for b in batches)
    total_tokens = len(secs) + minted
    attempts_mean = total_attempts / total_tokens if total_tokens else 0.0
    # Token wire sizes across EVERY minted token (1-core + workers).
    for b in batches:
        all_sizes.extend(b[4])
    sol_sizes = [s for (s, _n) in all_sizes if s > 0]
    nonce_sizes = [n for (_s, n) in all_sizes if n > 0]

    ideal = onecore_rate * workers
    return MiningPoint(
        effort=effort,
        samples=len(secs),
        token_s_mean=token_s_mean,
        token_s_median=statistics.median(secs),
        token_s_stddev=statistics.pstdev(secs) if len(secs) > 1 else 0.0,
        attempts_mean=attempts_mean,
        achieved_mean=statistics.fmean(achieved),
        tokens_per_sec_1core=onecore_rate,
        workers=workers,
        ok_workers=ok_workers,
        tokens_per_sec_machine=machine_rate,
        scaling_efficiency=(machine_rate / ideal) if ideal > 0 else 0.0,
        failed_searches=fails + w_fails,
        solution_bytes_min=min(sol_sizes) if sol_sizes else 0,
        solution_bytes_max=max(sol_sizes) if sol_sizes else 0,
        nonce_bytes_wire=max(nonce_sizes) if nonce_sizes else 0,
    )


def run_mining(cfg: dict[str, Any], adapters: dict[str, Adapter], repo_root: Path,
               device_resolver: Callable[[dict[str, Any]], str],
               timeout: float) -> list[MiningResult]:
    """Drive the mining benchmark from a `[mining]` config block.

    cfg keys (optional): impls ([] = all given), challenge_base ("abcd"),
    efforts ([100,300,1000,3000,10000]), samples (12, 1-core mints per effort),
    workers (0 = cpu count), tokens_per_worker (6, streamed per concurrent
    worker), nonce_bytes (8), max_attempts (1_500_000)."""
    import os

    base = str(cfg.get("challenge_base", "abcd"))
    efforts = [int(e) for e in cfg.get("efforts", [100, 300, 1000, 3000, 10000])]
    samples = int(cfg.get("samples", 12))
    workers = int(cfg.get("workers", 0)) or (os.cpu_count() or 4)
    tokens_per_worker = int(cfg.get("tokens_per_worker", cfg.get("reps", 6)))
    nonce_bytes = int(cfg.get("nonce_bytes", 8))
    max_attempts = int(cfg.get("max_attempts", 1_500_000))
    want = list(cfg.get("impls", [])) or list(adapters.keys())

    impls = [(n, adapters[n]) for n in want if n in adapters]
    out: list[MiningResult] = []
    for name, adapter in impls:
        # Learn device from a cheap probe: target_effort=1 with a single attempt
        # (a probe at efforts[0] would run a full search — minutes on a slow
        # interpreted impl at high E, just to read the env).
        try:
            probe = run(adapter, _effort_spec(base, 1, 0, nonce_bytes, 1, 0, 1),
                        repo_root, timeout=timeout)
            device = device_resolver(probe.env)
        except RunnerError:
            device = device_resolver({})
        res = MiningResult(device=device, impl=name, challenge_base=base, nproc=workers)
        for e in efforts:
            res.points.append(measure_point(adapter, base, e, samples, workers,
                                             tokens_per_worker, nonce_bytes, max_attempts,
                                             repo_root, timeout))
        out.append(res)
    return out


def write_csv(results: list[MiningResult], path: Path) -> None:
    import csv

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "device", "impl", "challenge_base", "effort", "samples",
            "attempts_mean", "achieved_mean", "token_s_mean", "token_s_median",
            "token_s_stddev", "tokens_per_sec_1core", "workers", "ok_workers",
            "tokens_per_sec_machine", "scaling_efficiency", "failed_searches",
            "solution_bytes_min", "solution_bytes_max", "nonce_bytes_wire",
        ])
        for r in results:
            for p in r.points:
                w.writerow([
                    r.device, r.impl, r.challenge_base, p.effort, p.samples,
                    f"{p.attempts_mean:.2f}", f"{p.achieved_mean:.1f}",
                    f"{p.token_s_mean:.6f}", f"{p.token_s_median:.6f}",
                    f"{p.token_s_stddev:.6f}", f"{p.tokens_per_sec_1core:.4f}",
                    p.workers, p.ok_workers, f"{p.tokens_per_sec_machine:.4f}",
                    f"{p.scaling_efficiency:.4f}", p.failed_searches,
                    p.solution_bytes_min, p.solution_bytes_max, p.nonce_bytes_wire,
                ])


def read_csv(path: Path) -> list[MiningResult]:
    """Reconstruct MiningResults from a mining.csv (the inverse of write_csv), so
    `combine` can fold in each device's measured mint-rate ladder. Every field is
    round-tripped from the CSV; nproc is recovered from the per-point worker count."""
    import csv

    # Columns added over time (failed_searches, message-size fields) may be absent
    # in older CSVs; default them so a mixed-vintage `combine` still round-trips.
    def _i(row, k):
        v = row.get(k, "")
        return int(v) if v not in ("", None) else 0

    def _f(row, k):
        v = row.get(k, "")
        return float(v) if v not in ("", None) else 0.0

    by_key: dict[tuple[str, str, str], MiningResult] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["device"], row["impl"], row["challenge_base"])
            res = by_key.get(key)
            if res is None:
                res = MiningResult(device=row["device"], impl=row["impl"],
                                   challenge_base=row["challenge_base"], nproc=0)
                by_key[key] = res
            res.points.append(MiningPoint(
                effort=_i(row, "effort"),
                samples=_i(row, "samples"),
                token_s_mean=_f(row, "token_s_mean"),
                token_s_median=_f(row, "token_s_median"),
                token_s_stddev=_f(row, "token_s_stddev"),
                attempts_mean=_f(row, "attempts_mean"),
                achieved_mean=_f(row, "achieved_mean"),
                tokens_per_sec_1core=_f(row, "tokens_per_sec_1core"),
                workers=_i(row, "workers"),
                ok_workers=_i(row, "ok_workers"),
                tokens_per_sec_machine=_f(row, "tokens_per_sec_machine"),
                scaling_efficiency=_f(row, "scaling_efficiency"),
                failed_searches=_i(row, "failed_searches"),
                solution_bytes_min=_i(row, "solution_bytes_min"),
                solution_bytes_max=_i(row, "solution_bytes_max"),
                nonce_bytes_wire=_i(row, "nonce_bytes_wire"),
            ))
    for res in by_key.values():
        res.points.sort(key=lambda p: p.effort)
        res.nproc = max((p.workers for p in res.points), default=0)
    return list(by_key.values())
