"""Command-line entrypoint: `python -m equix_bench run --config ... --out ...`."""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import concurrency as concmod
from . import config as cfgmod
from . import mining as miningmod
from . import report as reportmod
from . import stats as statsmod
from .crosscheck import run_crosscheck
from .device import device_from_env
from .protocol import JobSpec, Result
from .registry import load_manifests
from .runner import RunnerError, run


def _repo_root(override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def _cpu_model() -> str:
    from .device import _host_cpu  # cross-platform (Linux /proc, macOS sysctl)

    return _host_cpu()


def _resolve_verify_solutions(cells, adapters, repo_root):
    """Fill solution_hex for verify cells by solving each challenge once with the
    first capable implementation. Returns (usable_cells, warnings)."""
    warnings = []
    cache: dict[str, str | None] = {}
    solver = None
    for name, a in adapters.items():
        if not a.capabilities or "solve" in a.capabilities:
            if a.available(repo_root):
                solver = (name, a)
                break
    out = []
    for c in cells:
        # Seed-mode verify cells self-solve each derived challenge in the runner,
        # so they need no pre-resolved solution.
        if c.job.operation != "verify" or c.job.challenge_seed_hex is not None:
            out.append(c)
            continue
        chal = c.job.challenge_hex
        if chal not in cache:
            if solver is None:
                cache[chal] = None
            else:
                r = run(solver[1], JobSpec(operation="solve", runtime="try-compile",
                                           repetitions=1, warmup=0, challenge_hex=chal),
                        repo_root)
                sols = r.solutions_hex or []
                cache[chal] = sols[0] if sols else None
        sol = cache[chal]
        if sol is None:
            warnings.append(f"verify skipped for challenge {chal}: no solution found")
            continue
        c.job.solution_hex = sol
        out.append(c)
    return out, warnings


def cmd_run(args) -> int:
    repo_root = _repo_root(args.root)
    if args.manifests:
        manifest_dirs = [Path(args.manifests)]
    else:
        # built-in adapters + generated compiler-flag variants (if any)
        manifest_dirs = [repo_root / "adapters" / "examples", repo_root / "adapters" / "generated"]
    adapters = load_manifests(manifest_dirs)
    if not adapters:
        print(f"error: no adapter manifests found in {manifest_dirs}", file=sys.stderr)
        return 2

    # Keep only adapters whose runner is actually built/available.
    available = {n: a for n, a in adapters.items() if a.available(repo_root)}
    for n in adapters:
        if n not in available:
            print(f"warning: adapter '{n}' runner not found; skipping", file=sys.stderr)

    config = cfgmod.load_config(Path(args.config))
    out_dir = Path(args.out)

    # ---- cross-check only ----
    if args.crosscheck_only:
        challenges = config.crosscheck.get("challenges", ["deadbeef", "cafe"])
        pairs = [tuple(p) for p in config.crosscheck.get("pairs", [])] or None
        from .crosscheck import _pairs
        pair_list = _pairs(config.crosscheck.get("pairs", []), list(available.keys()))
        checks, ok = run_crosscheck(available, repo_root, challenges, pair_list)
        for c in checks:
            print(f"[{'PASS' if c.passed else 'FAIL'}] {c.kind}: {c.detail}")
        print(f"\nCross-check overall: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    # ---- full run ----
    cells, warns = cfgmod.expand(config, available)
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    cells, vwarns = _resolve_verify_solutions(cells, available, repo_root)
    for w in vwarns:
        print(f"warning: {w}", file=sys.stderr)

    print(f"Running {len(cells)} cells across {len(available)} implementations...")
    all_stats = []
    raw = []
    for i, c in enumerate(cells, 1):
        adapter = available[c.impl]
        try:
            result = run(adapter, c.job, repo_root, timeout=args.timeout)
        except RunnerError as e:
            print(f"  [{i}/{len(cells)}] {c.impl} {c.group} FAILED: {e}", file=sys.stderr)
            continue
        # Device identity: derived from what the runner reported (accurate even
        # for a remote or GPU runner), with the CLI label override applied.
        device = device_from_env(result.env, override_label=args.device_label)
        # Enrich the raw record so a run is self-contained for later `combine`.
        result.raw["_label"] = c.label
        result.raw["_device"] = device
        result.raw["_impl"] = c.impl
        result.raw["_group"] = c.group
        raw.append(result.raw)
        st = statsmod.summarize(c.impl, c.group, c.job.runtime, c.label, result, device)
        all_stats.append(st)
        tag = f"{c.impl}/{c.group}/{c.job.runtime} {c.label}"
        if st.ok:
            print(f"  [{i}/{len(cells)}] {tag}: median {st.median_ns/1e6:.3f} ms")
        else:
            print(f"  [{i}/{len(cells)}] {tag}: ERROR {st.error}", file=sys.stderr)

    # cross-check
    checks = []
    if config.crosscheck.get("enabled", True) and len(available) >= 2:
        from .crosscheck import _pairs
        pair_list = _pairs(config.crosscheck.get("pairs", []), list(available.keys()))
        challenges = config.crosscheck.get("challenges", ["deadbeef"])
        checks, _ = run_crosscheck(available, repo_root, challenges, pair_list)

    # concurrency / saturation benchmark (opt-in via a [concurrency] config block).
    # Measures sustained parallel solve/verify capacity; additive to the per-core
    # DoS estimate, which it never modifies.
    concurrency = None
    conc_cfg = config.raw.get("concurrency", {})
    if conc_cfg.get("enabled", False):
        print("Running concurrency / saturation ladder...")
        resolver = lambda env: device_from_env(env, override_label=args.device_label).get("label", "host")
        # Default to the impls this run selected (not every built variant); the
        # [concurrency] block can still name its own `impls` to override.
        conc_adapters = {n: available[n] for n in config.impls if n in available} or available
        concurrency = concmod.run_concurrency(conc_cfg, conc_adapters, repo_root, resolver, args.timeout)
        for r in concurrency:
            if r.error:
                print(f"  concurrency {r.impl}/{r.operation}: {r.error}", file=sys.stderr)
            else:
                print(f"  concurrency {r.impl}/{r.operation}: peak "
                      f"{r.peak_ops_per_sec:,.0f} ops/s at {r.knee_workers} workers")

    # mining-rate benchmark (opt-in via a [mining] config block): measures
    # whole-machine token production vs difficulty, the basis for rate control.
    mining = None
    mining_cfg = config.raw.get("mining", {})
    if mining_cfg.get("enabled", False):
        print("Running mining-rate / difficulty ladder...")
        resolver = lambda env: device_from_env(env, override_label=args.device_label).get("label", "host")
        mine_adapters = {n: available[n] for n in config.impls if n in available} or available
        mining = miningmod.run_mining(mining_cfg, mine_adapters, repo_root, resolver, args.timeout)
        for r in mining:
            for p in r.points:
                print(f"  mining {r.impl} E={p.effort}: {p.tokens_per_sec_1core:,.2f} tok/s/core, "
                      f"{p.tokens_per_sec_machine:,.2f} tok/s machine ({p.ok_workers} workers)")

    devices = sorted({s.device_label for s in all_stats})
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": args.config,
        "cpu": _cpu_model(),
        "nproc": os.cpu_count() or "?",
        "devices": devices,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_meta.json").write_text(json.dumps({
        **meta,
        "device_records": {s.device_label: {"type": s.device_type, "name": s.device_name,
                                             "arch": s.device_arch} for s in all_stats},
    }, indent=2))
    if concurrency:
        concmod.write_csv(concurrency, out_dir / "concurrency.csv")
    if mining:
        miningmod.write_csv(mining, out_dir / "mining.csv")
    reportmod.generate(all_stats, checks, raw, out_dir, meta, concurrency=concurrency, mining=mining)
    print(f"\nReport written to {out_dir/'report.md'} (plots in {out_dir/'plots'})")

    if checks and not all(c.passed for c in checks):
        print("Cross-check FAILED", file=sys.stderr)
        return 1
    return 0


def _load_cells_from_raw(raw_list: list[dict]) -> list[statsmod.CellStats]:
    """Rebuild CellStats from enriched raw records (each carries _label/_device)."""
    out = []
    for d in raw_list:
        try:
            result = Result.from_dict(d)
        except ValueError:
            continue
        label = d.get("_label", {})
        device = d.get("_device", {})
        impl = d.get("_impl", result.impl_name)
        group = d.get("_group", result.operation)
        out.append(statsmod.summarize(impl, group, result.runtime_requested, label, result, device))
    return out


def _discover_runs(root: Path) -> list[Path]:
    """Every run-output directory under `root`, identified by its `raw/results.json`.
    Layout-agnostic: works whether devices are laid out as `<root>/<device>/main`,
    `<root>/<host>/results/main`, or arbitrary rsync'd trees — a run is anything
    with a raw record file, and device identity comes from the records, not paths."""
    runs = {p.parent.parent for p in root.rglob("raw/results.json")}
    return sorted(runs)


def _dedup_key(r: dict) -> tuple:
    """Identity of one measured cell for de-duplication across discovered runs:
    (device, impl, operation, runtime, label). Includes runtime because two
    runtimes of the same op/challenge share _group and _label and would otherwise
    collide (dropping one)."""
    dev = (r.get("_device") or {}).get("label", "")
    try:
        res = Result.from_dict(r)
        op, rt = res.operation, res.runtime_requested
    except (ValueError, KeyError, TypeError):
        op, rt = r.get("operation", ""), r.get("runtime_requested", "")
    return (dev, r.get("_impl"), op, rt, json.dumps(r.get("_label", {}), sort_keys=True))


def _collect_runs(inputs: list[Path]):
    """Load and de-duplicate raw records + concurrency/mining results across runs.
    When the same cell (or device's concurrency/mining ladder) appears in more
    than one run, the record from the newest run (by run_meta timestamp) wins, so
    re-runs replace rather than double-count. Returns (raw, conc, mining, seen_dirs)."""
    from . import concurrency as concmod
    from . import mining as miningmod

    raw_by_key: dict[tuple, tuple[str, dict]] = {}      # key -> (ts, record)
    conc_by_key: dict[tuple, tuple[str, Any]] = {}
    mine_by_key: dict[tuple, tuple[str, Any]] = {}
    seen_dirs: list[Path] = []
    for d in inputs:
        raw_path = d / "raw" / "results.json"
        if not raw_path.exists():
            print(f"warning: skipping '{d}' (no raw/results.json)", file=sys.stderr)
            continue
        seen_dirs.append(d)
        meta_path = d / "run_meta.json"
        ts = ""
        if meta_path.exists():
            try:
                ts = json.loads(meta_path.read_text()).get("timestamp", "")
            except (ValueError, OSError):
                ts = ""
        for r in json.loads(raw_path.read_text()):
            k = _dedup_key(r)
            if k not in raw_by_key or ts >= raw_by_key[k][0]:
                raw_by_key[k] = (ts, r)
        cpath = d / "concurrency.csv"
        if cpath.exists():
            for cr in concmod.read_csv(cpath):
                k = (cr.device, cr.impl, cr.operation)
                if k not in conc_by_key or ts >= conc_by_key[k][0]:
                    conc_by_key[k] = (ts, cr)
        mpath = d / "mining.csv"
        if mpath.exists():
            for mr in miningmod.read_csv(mpath):
                k = (mr.device, mr.impl, mr.challenge_base)
                if k not in mine_by_key or ts >= mine_by_key[k][0]:
                    mine_by_key[k] = (ts, mr)
    raw = [rec for _ts, rec in raw_by_key.values()]
    conc = [cr for _ts, cr in conc_by_key.values()]
    mining = [mr for _ts, mr in mine_by_key.values()]
    return raw, conc, mining, seen_dirs


def cmd_combine(args) -> int:
    """Merge multiple prior runs into a single faceted (per-device) report — with
    the concurrency and mining sections/figures carried across all runs. Inputs
    are either listed explicitly (--inputs) or discovered under a tree (--root)."""
    inputs: list[Path] = [Path(p) for p in (args.inputs or [])]
    if args.root:
        discovered = _discover_runs(Path(args.root))
        if not discovered:
            print(f"error: no run directories (with raw/results.json) found under "
                  f"'{args.root}'", file=sys.stderr)
            return 2
        inputs.extend(discovered)
    if not inputs:
        print("error: provide run dirs via --inputs DIR... or a tree via --root DIR",
              file=sys.stderr)
        return 2
    # De-dup identical paths (e.g. --root and --inputs overlapping) preserving order.
    seen: set[str] = set()
    inputs = [p for p in inputs if not (str(p) in seen or seen.add(str(p)))]

    all_raw, conc, mining, seen_dirs = _collect_runs(inputs)
    stats = _load_cells_from_raw(all_raw)
    if not stats:
        print("error: no usable records found in inputs", file=sys.stderr)
        return 2

    devices_seen = sorted({s.device_label for s in stats})
    # Manifest: show exactly which dirs contributed which devices, so a missed
    # tree can't silently masquerade as full coverage.
    print(f"Discovered {len(seen_dirs)} run(s) across {len(devices_seen)} device(s):")
    for d in seen_dirs:
        try:
            recs = json.loads((d / "raw" / "results.json").read_text())
            devs = sorted({(r.get("_device") or {}).get("label", "?") for r in recs})
        except (ValueError, OSError):
            devs = ["?"]
        extra = []
        if (d / "concurrency.csv").exists():
            extra.append("concurrency")
        if (d / "mining.csv").exists():
            extra.append("mining")
        tail = f"  (+{', '.join(extra)})" if extra else ""
        print(f"  - {d}  ->  {', '.join(devs)}{tail}")

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": f"combine of {len(seen_dirs)} runs",
        "cpu": ", ".join(devices_seen),
        "nproc": "?",
        "devices": devices_seen,
    }
    out_dir = Path(args.out)
    reportmod.generate(stats, [], all_raw, out_dir, meta,
                       concurrency=conc or None, mining=mining or None)
    print(f"\nCombined report for devices {devices_seen} -> {out_dir/'report.md'}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="equix_bench", description="Equi-X PoW benchmarking framework")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a benchmark config")
    r.add_argument("--config", required=True, help="path to a TOML config")
    r.add_argument("--out", default="results", help="output directory")
    r.add_argument("--root", default=None, help="repo root (default: inferred)")
    r.add_argument("--manifests", default=None, help="adapter manifest directory")
    r.add_argument("--timeout", type=float, default=900.0, help="per-cell timeout (s)")
    r.add_argument("--crosscheck-only", action="store_true", help="only run the interop cross-check")
    r.add_argument("--device-label", "--cpu-label", dest="device_label", default=None,
                   help="human label for the executing device/CPU (default: auto from CPU model)")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("combine", help="merge multiple runs into per-device comparison figures")
    c.add_argument("--inputs", nargs="+", default=None, help="run output directories to merge")
    c.add_argument("--root", default=None,
                   help="auto-discover every run (dir with raw/results.json) under this tree")
    c.add_argument("--out", default="combined", help="output directory")
    c.set_defaults(func=cmd_combine)

    args = p.parse_args(argv)

    # Clean Ctrl+C: kill any live runner subprocesses (worker threads in the
    # concurrency/mining pools never receive KeyboardInterrupt themselves, so the
    # handler — which always runs in the main thread — reaps them promptly so a
    # blocked pool.shutdown can't hang), then raise KeyboardInterrupt so the run
    # unwinds normally. We catch it below to exit 130 without a traceback.
    from .runner import terminate_all_children

    def _on_sigint(signum, frame):
        terminate_all_children()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _on_sigint)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        terminate_all_children()
        print("\nInterrupted (Ctrl+C) — stopped; runner subprocesses killed.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
