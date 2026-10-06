#!/usr/bin/env python3
"""Time the node's proof of leadership, the circuit a vote proof would reuse.

Wraps the `prove` divan benchmark of logos-blockchain (`zk/proofs/pol/benches/prove.rs`): one
call to `prove` per sample, witness generation and the rapidsnark Groth16 proof together. It runs
in two configurations:

  all cores  rapidsnark's thread pool takes every core the machine has
  one core   pinned with `taskset -c 0`; the pool's threads then share that core

Each configuration is repeated, and every repeat's divan statistics are kept. The machine, its
frequency governor, the SoC temperature and, on a Raspberry Pi, `vcgencmd get_throttled` are
recorded around each run, with the logos-blockchain commit measured.

Driven by the Makefile next to it (`make run`), or standalone:

    ./bench_pol_proving.py --exe <bench binary> --repo <logos-blockchain checkout> --outdir <dir>

Writes <outdir>/results-<label>.json and .csv, the label naming the machine.
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
from pathlib import Path

BENCH = "bench_prove"
UNIT_MS = {"ns": 1e-6, "µs": 1e-3, "μs": 1e-3, "us": 1e-3, "ms": 1.0, "s": 1e3}
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ns|µs|μs|us|ms|s)(?![a-z/])")


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip().replace("\x00", "")
    except OSError:
        return None


def _run(cmd: list[str], cwd: str | None = None) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def machine(repo: str) -> dict:
    """The machine, and the toolchain the checkout builds with (its rust-toolchain.toml)."""
    model = _read("/proc/device-tree/model") or _run(["sysctl", "-n", "machdep.cpu.brand_string"])
    if model is None:
        cpuinfo = _read("/proc/cpuinfo") or ""
        names = re.findall(r"^model name\s*:\s*(.+)$", cpuinfo, re.M)
        model = names[0] if names else platform.processor() or "unknown"
    return dict(model=model, arch=platform.machine(), system=platform.platform(),
                cores=os.cpu_count(),
                governor=_read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
                rustc=_run(["rustc", "--version"], cwd=repo))


def thermals() -> dict:
    raw = _read("/sys/class/thermal/thermal_zone0/temp")
    return dict(temp_c=int(raw) / 1000 if raw and raw.isdigit() else None,
                throttled=_run(["vcgencmd", "get_throttled"]))


def parse(output: str) -> dict:
    """Divan's row for the benchmark: fastest, slowest, median, mean (ms), samples, iterations."""
    for line in output.splitlines():
        if BENCH in line:
            cells = [c.strip() for c in line.split(BENCH, 1)[1].split("│")]
            times = [DURATION_RE.search(c) for c in cells[:4]]
            if all(times):
                values = [float(m.group(1)) * UNIT_MS[m.group(2)] for m in times]
                samples, iters = (int(c) for c in cells[4:6])
                return dict(zip(("fastest_ms", "slowest_ms", "median_ms", "mean_ms"), values),
                            samples=samples, iters=iters)
    raise SystemExit(f"no '{BENCH}' row in the benchmark's output:\n{output}")


def measure(prefix: list[str], exe: str, sample_count: int) -> dict:
    before = thermals()
    start = time.monotonic()
    out = subprocess.run(prefix + [exe, "--bench", "--sample-count", str(sample_count),
                                   "--sample-size", "1"],
                         capture_output=True, text=True, check=True)
    row = parse(out.stdout)
    after = thermals()
    return row | dict(wall_s=round(time.monotonic() - start, 1), temp_before_c=before["temp_c"],
                      temp_after_c=after["temp_c"], throttled_after=after["throttled"])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--exe", required=True, help="the compiled prove benchmark")
    p.add_argument("--repo", required=True, help="the logos-blockchain checkout it was built from")
    p.add_argument("--outdir", required=True)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--sample-count", type=int, default=20)
    p.add_argument("--label", help="names the result files; defaults to the machine's model")
    p.add_argument("--no-pin", action="store_true", help="skip the one-core run")
    a = p.parse_args()

    info = machine(a.repo)
    info["commit"] = _run(["git", "-C", a.repo, "rev-parse", "HEAD"])
    label = a.label or re.sub(r"[^a-z0-9]+", "-", info["model"].lower()).strip("-")
    configs = [("all cores", [])]
    if a.no_pin:
        pass
    elif shutil.which("taskset"):
        configs.append(("one core", ["taskset", "-c", "0"]))
    else:
        print("taskset absent: the one-core run is skipped", file=sys.stderr)

    runs = []
    for name, prefix in configs:
        for r in range(a.repeats):
            row = measure(prefix, a.exe, a.sample_count)
            runs.append(dict(config=name, repeat=r) | row)
            print(f"  {name:9s} repeat {r}: median {row['median_ms']:.1f} ms "
                  f"(samples {row['samples']}, {row['wall_s']} s)", flush=True)
            if row["throttled_after"] not in (None, "throttled=0x0"):
                print(f"  WARNING: the board reports {row['throttled_after']}; "
                      "treat this run as a lower bound", file=sys.stderr)

    summary = {}
    for name, _ in configs:
        medians = [r["median_ms"] for r in runs if r["config"] == name]
        summary[name] = dict(median_ms=statistics.median(medians), min_ms=min(medians),
                             max_ms=max(medians), repeats=len(medians))
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"results-{label}.json").write_text(json.dumps(
        dict(machine=info, sample_count=a.sample_count, summary=summary, runs=runs), indent=2))
    with open(out / f"results-{label}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["label", *runs[0].keys()])
        w.writeheader()
        for r in runs:
            w.writerow(dict(label=label) | r)
    print(f"\n{info['model']} ({info['cores']} cores), logos-blockchain {info['commit']}")
    for name, s in summary.items():
        print(f"  {name:9s} {s['median_ms']:8.1f} ms per proof "
              f"(medians of {s['repeats']} repeats: {s['min_ms']:.1f}-{s['max_ms']:.1f})")
    print(f"written to {out}/results-{label}.{{json,csv}}")


if __name__ == "__main__":
    main()
