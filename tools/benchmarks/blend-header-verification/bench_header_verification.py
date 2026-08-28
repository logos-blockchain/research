#!/usr/bin/env python3
"""Measure how many Blend public-header verifications a node sustains per second.

Wraps the `verify_public_header` divan benchmark
(`blend/message/benches/verify_public_header.rs`) and turns its per-operation
latencies into a throughput figure, single-core and all-cores.

The number this produces bounds the Blend maximum message count: every message a
node relays now costs one public-header verification, so a node cannot accept
messages faster than it can verify headers. See `--phi-max` / `--window` below.

Three benchmarks are measured:

  bench_verify_header_signature       Ed25519 signature check alone
  bench_verify_proof_of_quota         Groth16 PoQ check alone
  bench_verify_public_header_complete signature + PoQ, the per-message cost

Proving is excluded, in both senses
-----------------------------------
The fixture proves a PoQ before anything can be verified, and proving is orders
of magnitude slower than verifying. It is kept out of the result twice over:

  * Out of the latency. Divan times only the benchmarked closure. The fixture is
    a process-wide `LazyLock` built before the first sample, so no reported
    duration — and therefore no throughput figure here — contains any proving.

  * Out of the contention. The all-cores figure uses divan's own `--threads N`
    rather than one process per core. Because the fixture is process-wide, the
    single proof is built once, up front, and every thread then verifies against
    it; divan additionally holds the threads on a `Barrier` so each sample starts
    on all of them together. Spawning a process per core instead would make each
    core prove its own fixture, and cores that finished proving early would be
    measured while their neighbours were still proving — contention against
    proving work, not against verification. That skew is what `--threads` avoids.

`--threads N` also matches the deployed shape: one node process verifying on N
threads, not N independent nodes sharing a board.

Wall-clock per phase still includes the one-off proving cost. It is reported as
`wall_s` for information only and is never an input to any throughput number.

Driven by the Makefile next to it, which vendors logos-blockchain, builds the
benchmark and passes the resolved binary in `--exe`:

    make check        # read-only: is the toolchain here?
    make smoke        # ~1 min end-to-end proof that the pipeline works
    make run          # the measurement

It also runs standalone against an existing checkout:

    ./bench_header_verification.py --repo /path/to/logos-blockchain --repeats 5

Outputs a summary table, plus `<outdir>/results.json` and `<outdir>/results.csv`.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PACKAGE = "logos-blockchain-blend-message"
BENCH_TARGET = "verify_public_header"

BENCHES = [
    "bench_verify_header_signature",
    "bench_verify_proof_of_quota",
    "bench_verify_public_header_complete",
]

# The benchmark whose throughput bounds the relay path.
PRIMARY_BENCH = "bench_verify_public_header_complete"

# Divan renders durations as e.g. "1.234 ms". It uses U+00B5 for micro; accept
# the Greek mu and a plain "us" too, in case a future version or a terminal
# re-encodes it.
UNIT_NS = {"ns": 1.0, "µs": 1e3, "μs": 1e3, "us": 1e3, "ms": 1e6, "s": 1e9}
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ns|µs|μs|us|ms|s)(?![a-z/])")
BENCH_ROW_RE = re.compile(r"^[│|\s]*[├╰]─\s+(\S+)")
THREAD_ROW_RE = re.compile(r"^t=(\d+)$")
COLUMN_WORDS = ("fastest", "slowest", "median", "mean")


# --------------------------------------------------------------------------- #
# environment capture
# --------------------------------------------------------------------------- #


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip().replace("\x00", "")
    except OSError:
        return None


def _run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def online_cores() -> list[int]:
    try:
        return sorted(os.sched_getaffinity(0))
    except AttributeError:  # not Linux
        return list(range(os.cpu_count() or 1))


def cpu_temps_c() -> dict[str, float]:
    temps = {}
    for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        raw = _read(str(zone / "temp"))
        if raw and raw.lstrip("-").isdigit():
            temps[zone.name] = int(raw) / 1000.0
    return temps


def cpu_freqs_mhz() -> dict[str, float]:
    freqs = {}
    for cpu in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*")):
        raw = _read(str(cpu / "cpufreq" / "scaling_cur_freq"))
        if raw and raw.isdigit():
            freqs[cpu.name] = int(raw) / 1000.0
    return freqs


def throttle_flags() -> dict[str, object] | None:
    """Decode `vcgencmd get_throttled`. Pi-specific; None elsewhere."""
    out = _run(["vcgencmd", "get_throttled"])
    if not out or "=" not in out:
        return None
    try:
        value = int(out.split("=", 1)[1], 0)
    except ValueError:
        return None
    bits = {
        0: "under_voltage_now",
        1: "arm_freq_capped_now",
        2: "currently_throttled",
        3: "soft_temp_limit_now",
        16: "under_voltage_occurred",
        17: "arm_freq_capped_occurred",
        18: "throttling_occurred",
        19: "soft_temp_limit_occurred",
    }
    return {"raw": hex(value), **{name: bool(value & (1 << bit)) for bit, name in bits.items()}}


def machine_info() -> dict:
    model = _read("/proc/device-tree/model") or platform.platform()
    governors = {
        cpu.name: _read(str(cpu / "cpufreq" / "scaling_governor"))
        for cpu in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*"))
    }
    return {
        "model": model,
        "machine": platform.machine(),
        "kernel": platform.release(),
        "page_size_bytes": os.sysconf("SC_PAGESIZE") if hasattr(os, "sysconf") else None,
        "cores_online": online_cores(),
        "governors": {k: v for k, v in governors.items() if v},
        "rustc": _run(["rustc", "--version"]),
        "has_taskset": shutil.which("taskset") is not None,
    }


def source_info(repo: Path) -> dict:
    """Which logos-blockchain commit produced these numbers."""
    if not (repo / ".git").exists():
        return {"repo": str(repo), "commit": None}
    return {
        "repo": str(repo),
        "commit": _run(["git", "-C", str(repo), "rev-parse", "HEAD"]),
        "described": _run(["git", "-C", str(repo), "describe", "--always", "--dirty"]),
        "subject": _run(["git", "-C", str(repo), "log", "-1", "--format=%s"]),
    }


def sample_thermals() -> dict:
    return {
        "temps_c": cpu_temps_c(),
        "freqs_mhz": cpu_freqs_mhz(),
        "throttled": throttle_flags(),
    }


# --------------------------------------------------------------------------- #
# divan output parsing
# --------------------------------------------------------------------------- #


@dataclass
class BenchStats:
    name: str
    fastest_ns: float | None = None
    slowest_ns: float | None = None
    median_ns: float | None = None
    mean_ns: float | None = None

    @property
    def per_thread_per_second(self) -> float | None:
        """Operations per second achieved by one thread. Proving is not in here."""
        if not self.median_ns:
            return None
        return 1e9 / self.median_ns


def parse_divan(output: str) -> dict[str, BenchStats]:
    """Extract per-benchmark durations from divan's table.

    Column order is read from the header row rather than assumed, and durations
    are matched by pattern so the tree-drawing characters and the optional
    counter (`item/s`) continuation rows do not need to be separated by hand.

    When more than one `--threads` value is given divan nests a `t=N` row under
    each benchmark; those rows are attributed to the benchmark above them. This
    script passes a single thread count per invocation, so that nesting normally
    does not appear, but it is handled in case the benchmark is run by hand.
    """
    columns: list[str] = []
    for line in output.splitlines():
        if all(word in line for word in COLUMN_WORDS):
            positions = sorted((line.index(w), w) for w in COLUMN_WORDS if w in line)
            columns = [w for _, w in positions]
            break
    if not columns:
        columns = list(COLUMN_WORDS)

    results: dict[str, BenchStats] = {}
    current_bench: str | None = None
    for line in output.splitlines():
        match = BENCH_ROW_RE.match(line)
        if not match:
            continue
        name = match.group(1)
        # Match durations only past the name: a benchmark called something like
        # `bench_5s_timeout` would otherwise contribute a phantom value and
        # shift every column silently.
        durations = [
            float(value) * UNIT_NS[unit]
            for value, unit in DURATION_RE.findall(line[match.end():])
        ]
        thread_row = THREAD_ROW_RE.match(name)
        if thread_row:
            # A `t=N` leaf carries the timings for the benchmark named above it.
            if current_bench is None or not durations:
                continue
            name = current_bench
        else:
            current_bench = name
            if not durations:
                # A group header with no timings of its own.
                continue

        # Columns are positional, so a row that does not carry exactly one
        # duration per column would map values onto the wrong fields. A
        # measurement that is quietly wrong is worse than one that is missing.
        if len(durations) != len(columns):
            sys.exit(
                f"cannot parse divan output for {name!r}: expected one duration "
                f"per column {columns} but found {len(durations)}. The output "
                f"format has changed; this script must be updated rather than "
                f"guessing which value is which.\n  row: {line.strip()}"
            )
        if name in results:
            sys.exit(
                f"divan reported {name!r} more than once, which happens when "
                f"several --threads values are given. This script measures one "
                f"thread count per invocation so it cannot tell the rows apart; "
                f"run it once per thread count instead."
            )

        stats = BenchStats(name=name)
        for column, value in zip(columns, durations):
            setattr(stats, f"{column}_ns", value)
        results[name] = stats
    return results


# --------------------------------------------------------------------------- #
# build & run
# --------------------------------------------------------------------------- #


def resolve_exe(path: Path) -> Path:
    """Use a bench binary handed over by the Makefile."""
    if not path.is_file() or not os.access(path, os.X_OK):
        sys.exit(f"--exe {path} is not an executable file; run `make build` first")
    return path


def build_bench(repo: Path, verbose: bool) -> Path:
    """Build the bench binary and return its path, so timing excludes the build."""
    cmd = [
        "cargo", "bench",
        "-p", PACKAGE,
        "--bench", BENCH_TARGET,
        "--no-run",
        "--message-format=json",
    ]
    print(f"building {PACKAGE} --bench {BENCH_TARGET} (release profile) ...", flush=True)
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"build failed:\n{proc.stderr}")

    executable = None
    for line in proc.stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("reason") == "compiler-artifact" and msg.get("executable"):
            target = msg.get("target", {})
            if target.get("name") == BENCH_TARGET and "bench" in target.get("kind", []):
                executable = msg["executable"]
    if not executable:
        sys.exit("could not find the bench executable in cargo's JSON output")
    if verbose:
        print(f"  -> {executable}")
    return Path(executable)


def bench_command(
    exe: Path, cores: list[int] | None, threads: int, args: argparse.Namespace
) -> list[str]:
    cmd: list[str] = []
    if cores:
        if not shutil.which("taskset"):
            sys.exit("taskset not found; install util-linux or pass --no-pin")
        cmd += ["taskset", "-c", ",".join(str(c) for c in cores)]
    cmd += [
        str(exe),
        # Divan runs in *test* mode (each benchmark once, no timings) unless
        # --bench is passed. `cargo bench` supplies it; invoking the binary
        # directly, as we do, does not.
        "--bench",
        "--sample-count", str(args.sample_count),
        "--sample-size", "1",
        "--threads", str(threads),
    ]
    if args.bench_filter:
        cmd += [args.bench_filter]
    return cmd


@dataclass
class Run:
    mode: str
    repeat: int
    threads: int
    cores: list[int] | None
    stats: dict[str, BenchStats] = field(default_factory=dict)
    # Includes the one-off fixture proving; informational only, never an input
    # to a throughput figure.
    wall_s: float = 0.0
    thermals_before: dict = field(default_factory=dict)
    thermals_after: dict = field(default_factory=dict)


def run_bench(
    exe: Path,
    cores: list[int] | None,
    threads: int,
    mode: str,
    repeat: int,
    args: argparse.Namespace,
) -> Run:
    run = Run(mode=mode, repeat=repeat, threads=threads, cores=cores)
    run.thermals_before = sample_thermals()
    started = time.monotonic()
    proc = subprocess.run(
        bench_command(exe, cores, threads, args), capture_output=True, text=True
    )
    run.wall_s = time.monotonic() - started
    run.thermals_after = sample_thermals()
    if proc.returncode != 0:
        sys.exit(f"benchmark failed ({mode}, {threads} thread(s)):\n"
                 f"{proc.stdout}\n{proc.stderr}")
    run.stats = parse_divan(proc.stdout)
    if args.verbose:
        print(proc.stdout)
    return run


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #


def fmt_ns(value: float | None) -> str:
    if value is None:
        return "n/a"
    for unit, scale in (("s", 1e9), ("ms", 1e6), ("µs", 1e3), ("ns", 1.0)):
        if value >= scale:
            return f"{value / scale:.3f} {unit}"
    return f"{value:.3f} ns"


def summarise(runs: list[Run], bench: str) -> dict:
    """Median-of-repeats latency, and the throughput implied by it.

    Divan reports one sample per thread, each the latency of a single operation
    measured while every thread was running, so aggregate throughput is the
    thread count divided by that latency.
    """
    out: dict = {"bench": bench}

    for mode in ("single", "multi"):
        selected = [r for r in runs if r.mode == mode and bench in r.stats
                    and r.stats[bench].median_ns]
        if not selected:
            continue
        medians = [r.stats[bench].median_ns for r in selected]
        thread_counts = {r.threads for r in selected}
        if len(thread_counts) != 1:
            sys.exit(f"{mode} runs mixed thread counts {sorted(thread_counts)}; "
                     f"aggregate throughput would be meaningless")
        threads = thread_counts.pop()
        latency = statistics.median(medians)
        out[mode] = {
            "repeats": len(medians),
            "threads": threads,
            "median_ns": latency,
            "spread_ns": (min(medians), max(medians)),
            "per_thread_per_second": 1e9 / latency,
            "per_second": threads * 1e9 / latency,
        }
    return out


def derive_spec_bounds(per_second: float, args: argparse.Namespace) -> dict:
    """Translate verification throughput into the Blend connection-monitoring bound.

    Every counted message costs one public-header verification, so across
    phi_max connections over a window of W rounds a node can verify at most
    per_second * W * round_seconds headers in total, i.e. that budget divided by
    phi_max per connection.
    """
    window_seconds = args.window * args.round_seconds
    total_per_window = per_second * window_seconds
    per_connection = total_per_window / args.phi_max
    expected_per_connection = args.f1 * args.window
    return {
        "verifications_per_second": per_second,
        "window_rounds": args.window,
        "round_seconds": args.round_seconds,
        "phi_cc_max": args.phi_max,
        "f1_per_round": args.f1,
        "headers_per_window_total": total_per_window,
        "max_per_connection_per_window": per_connection,
        "expected_per_connection_per_window": expected_per_connection,
        "kappa_max_capacity_ceiling": per_connection / expected_per_connection,
    }


def report(runs: list[Run], info: dict, args: argparse.Namespace) -> dict:
    print()
    print("=" * 78)
    print(f"  {info['model']}")
    print(f"  {info['machine']}  kernel {info['kernel']}  cores {info['cores_online']}")
    govs = set(info["governors"].values())
    if govs:
        print(f"  cpufreq governor: {', '.join(sorted(govs))}"
              + ("   <-- not 'performance'; results will be conservative"
                 if govs != {"performance"} else ""))
    src = source_info(args.repo)
    if src.get("commit"):
        print(f"  logos-blockchain {src['described'] or src['commit'][:12]}"
              f"  ({src.get('subject') or ''})"[:76])
    print("=" * 78)

    summaries = [summarise(runs, bench) for bench in BENCHES]
    multi_threads = next((s["multi"]["threads"] for s in summaries if "multi" in s), None)

    multi_label = f"{multi_threads} threads" if multi_threads else "all cores"
    header = f"{'benchmark':<38} {'1 thread':>13} {multi_label:>15}"
    print(f"\nverifications per second (proving excluded)\n\n{header}")
    print("-" * len(header))
    for s in summaries:
        single_txt = f"{s['single']['per_second']:>9,.0f}/s" if "single" in s else "n/a"
        multi_txt = f"{s['multi']['per_second']:>11,.0f}/s" if "multi" in s else "n/a"
        print(f"{s['bench']:<38} {single_txt:>13} {multi_txt:>15}")

    print("\nper-operation latency (median across repeats)")
    print("-" * len(header))
    for s in summaries:
        if "single" in s:
            lo, hi = s["single"]["spread_ns"]
            line = f"{s['bench']:<38} {fmt_ns(s['single']['median_ns']):>13}"
            if "multi" in s:
                line += f" {fmt_ns(s['multi']['median_ns']):>15}"
            print(f"{line}   (1-thread repeat spread {fmt_ns(lo)} .. {fmt_ns(hi)})")

    if multi_threads:
        scaling = [
            (s["bench"], s["multi"]["per_second"] / s["single"]["per_second"])
            for s in summaries if "single" in s and "multi" in s
        ]
        print(f"\nscaling from 1 to {multi_threads} threads "
              f"(perfect would be {multi_threads:.2f}x)")
        print("-" * len(header))
        for name, factor in scaling:
            print(f"{name:<38} {factor:>12.2f}x")

    # Throttling is the failure mode that silently invalidates a Pi benchmark.
    throttled = [
        r for r in runs
        if (r.thermals_after.get("throttled") or {}).get("currently_throttled")
        or (r.thermals_after.get("throttled") or {}).get("throttling_occurred")
    ]
    peak_temp = max(
        (t for r in runs for t in r.thermals_after.get("temps_c", {}).values()),
        default=None,
    )
    if peak_temp is not None:
        print(f"\npeak SoC temperature: {peak_temp:.1f} °C")
    if throttled:
        print("WARNING: the board reported throttling during the run — "
              "these numbers are a floor, not the hardware's capability.")

    primary = next((s for s in summaries if s["bench"] == PRIMARY_BENCH), None)
    bounds = {}
    if primary and "single" in primary:
        bounds["single_core"] = derive_spec_bounds(primary["single"]["per_second"], args)
        if "multi" in primary:
            bounds[f"{multi_threads}_threads"] = derive_spec_bounds(
                primary["multi"]["per_second"], args
            )

        print("\n" + "=" * 78)
        print("  implied Blend bound (complete header verification)")
        print("=" * 78)
        print(f"  assumptions: W = {args.window} rounds of {args.round_seconds}s, "
              f"Phi_CC^Max = {args.phi_max}, F_1 = {args.f1}/round")
        for label, b in bounds.items():
            print(f"\n  {label}: {b['verifications_per_second']:,.0f} verifications/s")
            print(f"    headers verifiable per {args.window}-round window: "
                  f"{b['headers_per_window_total']:,.0f}")
            print(f"    ... divided across {args.phi_max} connections: "
                  f"{b['max_per_connection_per_window']:,.0f} per connection")
            print(f"    expected honest traffic per connection: "
                  f"{b['expected_per_connection_per_window']:,.0f}")
            print(f"    => kappa_max ceiling from CPU capacity: "
                  f"{b['kappa_max_capacity_ceiling']:.2f}")
        print("\n  kappa_max must sit below the ceiling above and above the ~3.87 floor")
        print("  set by duplication and bootstrapping. If the ceiling is under the")
        print("  floor, this hardware cannot verify every message it may accept.")

    return {"machine": info, "summaries": summaries, "bounds": bounds}


def write_outputs(outdir: Path, runs: list[Run], summary: dict, args: argparse.Namespace) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_unix": int(time.time()),
        "args": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "note": "wall_s includes one-off fixture proving; no throughput figure does",
        **summary,
        "runs": [
            {
                **{k: v for k, v in asdict(r).items() if k != "stats"},
                "stats": {name: asdict(s) for name, s in r.stats.items()},
            }
            for r in runs
        ],
    }
    (outdir / "results.json").write_text(json.dumps(payload, indent=2, default=str))

    with (outdir / "results.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["mode", "repeat", "threads", "cores", "bench", "median_ns",
                         "mean_ns", "fastest_ns", "slowest_ns",
                         "per_thread_per_second", "aggregate_per_second"])
        for r in runs:
            for name, s in r.stats.items():
                rate = s.per_thread_per_second
                writer.writerow([
                    r.mode, r.repeat, r.threads,
                    "" if r.cores is None else " ".join(str(c) for c in r.cores),
                    name, s.median_ns, s.mean_ns, s.fastest_ns, s.slowest_ns,
                    f"{rate:.2f}" if rate else "",
                    f"{rate * r.threads:.2f}" if rate else "",
                ])

    print(f"\nwrote {outdir / 'results.json'} and {outdir / 'results.csv'}")


# --------------------------------------------------------------------------- #


def main() -> None:
    # Standalone default: the checkout the Makefile vendors beside this script.
    repo_default = Path(__file__).resolve().parent / "vendor" / "logos-blockchain"

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repeats", type=int, default=5,
                        help="times to repeat each configuration (default: 5)")
    parser.add_argument("--sample-count", type=int, default=200,
                        help="divan samples per benchmark; the bench itself defaults to "
                             "1000, lowered here so a repeated Pi run stays short "
                             "(default: 200)")
    parser.add_argument("--cores", type=str, default=None,
                        help="comma-separated cores for the multi-thread run "
                             "(default: every online core)")
    parser.add_argument("--single-core", type=int, default=None,
                        help="core to pin the single-thread run to (default: lowest online)")
    parser.add_argument("--threads", type=int, default=None,
                        help="threads for the multi-thread run (default: one per core)")
    parser.add_argument("--no-pin", action="store_true",
                        help="do not use taskset; let the scheduler place threads")
    parser.add_argument("--skip-multi", action="store_true", help="single-thread runs only")
    parser.add_argument("--skip-single", action="store_true", help="multi-thread runs only")
    parser.add_argument("--bench-filter", type=str, default=None,
                        help="divan filter, e.g. 'complete' to run one benchmark")
    parser.add_argument("--repo", type=Path, default=repo_default,
                        help="path to the logos-blockchain checkout "
                             "(default: the vendored one next to this script)")
    parser.add_argument("--exe", type=Path, default=None,
                        help="path to an already-built bench binary; skips cargo "
                             "entirely. The Makefile passes this after `make build`.")
    parser.add_argument("--outdir", type=Path, default=Path("bench-header-verification-out"))
    parser.add_argument("--verbose", "-v", action="store_true", help="echo divan output")

    spec = parser.add_argument_group("Blend parameters used to derive the implied bound")
    spec.add_argument("--window", type=int, default=30, help="observation window W in rounds")
    spec.add_argument("--round-seconds", type=float, default=1.0, help="round duration")
    spec.add_argument("--phi-max", type=int, default=8, help="Phi_CC^Max, core connections")
    spec.add_argument("--f1", type=float, default=3.1,
                      help="F_1, expected messages per connection per round")

    args = parser.parse_args()

    if args.skip_multi and args.skip_single:
        sys.exit("--skip-multi and --skip-single leave nothing to run")

    info = machine_info()
    cores = online_cores()
    multi_cores = [int(c) for c in args.cores.split(",")] if args.cores else cores
    threads = args.threads or len(multi_cores)
    single_cores = None if args.no_pin else [
        args.single_core if args.single_core is not None else cores[0]
    ]
    multi_cores_arg = None if args.no_pin else multi_cores

    if args.exe:
        exe = resolve_exe(args.exe)
        # The commit is read from --repo but the binary comes from --exe; if
        # they are unrelated, the recorded provenance would name a commit that
        # did not produce these numbers.
        try:
            exe.resolve().relative_to(args.repo.resolve())
        except ValueError:
            print(f"WARNING: --exe is outside --repo, so the recorded commit may "
                  f"not be the one that produced this binary\n"
                  f"  exe:  {exe}\n  repo: {args.repo}", file=sys.stderr)
    else:
        exe = build_bench(args.repo, args.verbose)

    runs: list[Run] = []
    total = (0 if args.skip_single else args.repeats) + (0 if args.skip_multi else args.repeats)
    phase = 0

    for repeat in range(1, args.repeats + 1):
        if not args.skip_single:
            phase += 1
            where = "" if single_cores is None else f" on core {single_cores[0]}"
            print(f"[{phase}/{total}] 1 thread{where}, repeat {repeat} ...", flush=True)
            runs.append(run_bench(exe, single_cores, 1, "single", repeat, args))

        if not args.skip_multi:
            phase += 1
            where = "" if multi_cores_arg is None else f" across cores {multi_cores_arg}"
            print(f"[{phase}/{total}] {threads} threads{where}, repeat {repeat} ...",
                  flush=True)
            runs.append(run_bench(exe, multi_cores_arg, threads, "multi", repeat, args))

    if not any(r.stats for r in runs):
        sys.exit("no benchmark rows were parsed from divan's output; "
                 "re-run with --verbose to see what it printed")

    summary = report(runs, info, args)
    summary["source"] = source_info(args.repo)
    write_outputs(args.outdir, runs, summary, args)


if __name__ == "__main__":
    main()
