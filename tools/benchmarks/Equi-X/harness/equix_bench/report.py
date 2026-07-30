"""Reporting: CSV, raw JSON, comparison plots, and a markdown report.

Design rules (per requirements):
  * EVERY plot compares all implementations on the same axes. `_require_multi_impl`
    fails loudly if a figure would show fewer than two implementations.
  * Plots reflect the executing device (CPU). With ONE device, the device is shown
    in the title. With MULTIPLE devices (e.g. after `combine`), each plot becomes a
    small-multiples grid (one facet per device, C-vs-Rust within each), plus
    dedicated cross-device charts (x=device, series=impl) for headline metrics.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .crosscheck import Check
from .dosprotect import assess as dos_assess
from .dosprotect import min_verify_seconds
from .stats import CellStats

_PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]


def _impl_color(impl: str, all_impls: list[str]) -> str:
    idx = all_impls.index(impl) if impl in all_impls else len(all_impls)
    return _PALETTE[idx % len(_PALETTE)]


def _require_multi_impl(impls_present: Iterable[str], plot: str) -> list[str]:
    impls = sorted(set(impls_present))
    if len(impls) < 2:
        raise RuntimeError(
            f"plot '{plot}' requires >=2 implementations to compare, "
            f"but only found: {impls}. Build/enable both C and Rust runners."
        )
    return impls


# --------------------------------------------------------------------- outputs


def write_csv(stats: list[CellStats], path: Path) -> None:
    cols = [
        "impl", "device_label", "device_type", "device_name", "device_arch",
        "operation", "runtime_requested", "runtime_effective", "label",
        "reps", "ok", "min_ns", "median_ns", "mean_ns", "stddev_ns", "p95_ns",
        "solutions_mean", "compile_median_ns", "attempts_mean",
        "achieved_effort_mean", "solves_per_sec", "hashes_per_sec",
        "peak_rss_kb", "verify_result", "error",
    ]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for s in stats:
            w.writerow([
                s.impl, s.device_label, s.device_type, s.device_name, s.device_arch,
                s.operation, s.runtime_requested, s.runtime_effective,
                json.dumps(s.label), s.reps, s.ok, f"{s.min_ns:.1f}",
                f"{s.median_ns:.1f}", f"{s.mean_ns:.1f}", f"{s.stddev_ns:.1f}",
                f"{s.p95_ns:.1f}", f"{s.solutions_mean:.3f}",
                f"{s.compile_median_ns:.1f}", f"{s.attempts_mean:.2f}",
                f"{s.achieved_effort_mean:.1f}", f"{s.solves_per_sec:.2f}",
                f"{s.hashes_per_sec:.0f}", s.peak_rss_kb, s.verify_result, s.error,
            ])


def write_raw(raw: list[dict[str, Any]], path: Path) -> None:
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)


# ----------------------------------------------------------------- plot helpers


def _grouped_bar(ax, categories, series, all_impls, errors=None) -> None:
    names = sorted(series.keys())
    n = len(names)
    width = 0.8 / max(n, 1)
    x = np.arange(len(categories))
    for i, name in enumerate(names):
        off = (i - (n - 1) / 2) * width
        err = errors.get(name) if errors else None
        ax.bar(x + off, series[name], width, label=name, yerr=err, capsize=3,
               color=_impl_color(name, all_impls), edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=0)
    ax.legend(title="implementation", fontsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.5)


def _agg(stats, cat_key, val):
    """Aggregate (mean) `val` grouped by (category, impl) over a pre-filtered set."""
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    impls_present: set[str] = set()
    cats: list[str] = []
    for s in stats:
        c = cat_key(s)
        buckets[(s.impl, c)].append(val(s))
        impls_present.add(s.impl)
        if c not in cats:
            cats.append(c)
    cats = sorted(cats)
    impls = sorted(impls_present)
    series = {
        impl: [float(np.mean(buckets[(impl, c)])) if buckets.get((impl, c)) else 0.0
               for c in cats]
        for impl in impls
    }
    return cats, series, impls


def _save(fig, path: Path) -> str:
    # Only run tight_layout when no layout engine is active (faceted figures use
    # constrained layout, which is incompatible with tight_layout and can produce
    # NaN axes geometry if both run).
    try:
        if fig.get_layout_engine() is None:
            fig.tight_layout()
    except Exception:  # noqa: BLE001 - layout is best-effort, never fatal
        pass
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path.name


# ------------------------------------------------------------------ panels (per device)


def _panel_time(ax, stats, all_impls):
    cats, series, _ = _agg(stats, lambda s: s.runtime_requested, lambda s: s.median_ns)
    _, errs, _ = _agg(stats, lambda s: s.runtime_requested,
                      lambda s: max(0.0, s.p95_ns - s.median_ns))
    _grouped_bar(ax, cats, series, all_impls, errs)
    ax.set_xlabel("HashX runtime")


def _panel_throughput(ax, stats, all_impls):
    cats, series, _ = _agg(stats, lambda s: s.runtime_requested, lambda s: s.solves_per_sec)
    _grouped_bar(ax, cats, series, all_impls)
    ax.set_xlabel("HashX runtime")


def _panel_rss(ax, stats, all_impls):
    cats, series, _ = _agg(stats, lambda s: s.runtime_requested, lambda s: float(s.peak_rss_kb))
    _grouped_bar(ax, cats, series, all_impls)
    ax.set_xlabel("HashX runtime")


def _panel_compile(ax, stats, all_impls):
    cats, series, _ = _agg(stats, lambda s: s.runtime_requested, lambda s: s.compile_median_ns)
    _grouped_bar(ax, cats, series, all_impls)
    ax.set_xlabel("HashX runtime")


def _panel_speedup(ax, stats, all_impls):
    med: dict[tuple[str, str], list[float]] = defaultdict(list)
    for s in stats:
        med[(s.impl, s.runtime_requested)].append(s.median_ns)
    impls = sorted({s.impl for s in stats})
    speedups = []
    for impl in impls:
        interp = med.get((impl, "interpret"))
        comp = med.get((impl, "try-compile")) or med.get((impl, "must-compile"))
        speedups.append(float(np.mean(interp)) / float(np.mean(comp)) if interp and comp else 0.0)
    x = np.arange(len(impls))
    ax.bar(x, speedups, 0.5, color=[_impl_color(i, all_impls) for i in impls],
           edgecolor="black", linewidth=0.4)
    for xi, v in zip(x, speedups):
        ax.text(xi, v, f"{v:.1f}x", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(impls)
    ax.set_xlabel("implementation")


def _panel_distribution(ax, stats, all_impls):
    runtimes: list[str] = []
    data: dict[tuple[str, str], list[float]] = defaultdict(list)
    impls = sorted({s.impl for s in stats})
    for s in stats:
        if s.walls:
            if s.runtime_requested not in runtimes:
                runtimes.append(s.runtime_requested)
            data[(s.impl, s.runtime_requested)].extend([w / 1e6 for w in s.walls])
    runtimes = sorted(runtimes)
    positions, box_data, colors = [], [], []
    width = 0.8 / max(len(impls), 1)
    for ri, rt in enumerate(runtimes):
        for ii, impl in enumerate(impls):
            vals = data.get((impl, rt))
            if not vals:
                continue
            positions.append(ri + (ii - (len(impls) - 1) / 2) * width)
            box_data.append(vals)
            colors.append(_impl_color(impl, all_impls))
    if box_data:
        bp = ax.boxplot(box_data, positions=positions, widths=width * 0.9,
                        patch_artist=True, showfliers=False)
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.8)
    ax.set_xticks(range(len(runtimes)))
    ax.set_xticklabels(runtimes)
    ax.set_xlabel("HashX runtime")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=_impl_color(i, all_impls), label=i) for i in impls],
              title="implementation", fontsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.5)


def _panel_effort(ax, stats, all_impls, which):
    pts: dict[str, dict[int, tuple[float, float]]] = defaultdict(dict)
    for s in stats:
        t = int(s.label.get("target_effort", 0))
        pts[s.impl][t] = (s.attempts_mean, s.median_ns / 1e9)
    for impl in sorted(pts):
        xs = sorted(pts[impl].keys())
        ys = [pts[impl][x][0 if which == "attempts" else 1] for x in xs]
        ax.plot(xs, ys, "o-", label=impl, color=_impl_color(impl, all_impls))
    ax.set_xscale("log")
    if which == "attempts":
        ax.set_yscale("log")
        ax.set_ylabel("mean attempts")
    else:
        ax.set_ylabel("median time (s)")
    ax.set_xlabel("target effort")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)


# ------------------------------------------------------------------ facet driver


def _facet(stats, panel_fn, title, ylabel, path, all_impls, keep) -> str:
    subset = [s for s in stats if keep(s) and s.ok]
    devices = sorted({s.device_label for s in subset})
    _require_multi_impl({s.impl for s in subset}, path.name)

    if len(devices) <= 1:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        panel_fn(ax, subset, all_impls)
        dev = devices[0] if devices else "host"
        ax.set_title(f"{title}\n[{dev}]")
        ax.set_ylabel(ylabel)
        return _save(fig, path)

    n = len(devices)
    fig, axes = plt.subplots(1, n, figsize=(min(7 * n, 22), 4.8), sharey=True,
                             squeeze=False, layout="constrained")
    for ax, dev in zip(axes[0], devices):
        panel_fn(ax, [s for s in subset if s.device_label == dev], all_impls)
        ax.set_title(dev)
    axes[0][0].set_ylabel(ylabel)
    fig.suptitle(title, fontweight="bold")
    return _save(fig, path)


def _plot_dos(stats, path, all_impls) -> Optional[str]:
    """DoS-protection asymmetry: attacker cost to craft a token / defender verify
    cost, vs effort. One line per implementation (attacker), faceted per device."""
    panels = []
    for dev in sorted({s.device_label for s in stats if s.ok and s.operation == "effort"}):
        vs = min_verify_seconds(stats, dev)
        if not vs:
            continue
        per_impl: dict[str, dict[int, float]] = defaultdict(dict)
        for s in stats:
            if s.operation == "effort" and s.ok and s.device_label == dev and s.median_ns > 0:
                e = int(s.label.get("target_effort", 0))
                per_impl[s.impl][e] = (s.median_ns / 1e9) / vs
        if per_impl:
            panels.append((dev, per_impl))
    if not panels:
        return None
    _require_multi_impl({im for _, pi in panels for im in pi}, path.name)

    from .dosprotect import DEFAULT_THRESHOLD
    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(min(7 * n, 22), 4.8), squeeze=False,
                             sharey=True, layout="constrained" if n > 1 else None)
    for ax, (dev, per_impl) in zip(axes[0], panels):
        for impl in sorted(per_impl):
            xs = sorted(per_impl[impl])
            ys = [per_impl[impl][x] for x in xs]
            ax.plot(xs, ys, "o-", label=impl, color=_impl_color(impl, all_impls))
        ax.axhline(DEFAULT_THRESHOLD, ls="--", color="red", alpha=0.7,
                   label=f"effective ≥ {DEFAULT_THRESHOLD:.0f}×")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("target effort (attacker difficulty)")
        ax.set_title(dev)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
    axes[0][0].set_ylabel("protection factor  (attacker time / verify time)")
    fig.suptitle("DoS-protection asymmetry: cost to attack vs cost to verify", fontweight="bold")
    return _save(fig, path)


def _cross_device_bar(stats, keep, val, title, ylabel, path, all_impls) -> Optional[str]:
    subset = [s for s in stats if keep(s) and s.ok]
    devices = sorted({s.device_label for s in subset})
    if len(devices) < 2:
        return None  # only meaningful across multiple devices
    cats, series, impls = _agg(subset, lambda s: s.device_label, val)
    _require_multi_impl(impls, path.name)
    fig, ax = plt.subplots(figsize=(max(6, 2 + 2 * len(devices)), 4.5))
    _grouped_bar(ax, cats, series, all_impls)
    ax.set_xlabel("device / CPU")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    return _save(fig, path)


def _devices_of(results) -> list[str]:
    """Devices present in a concurrency/mining result set, in stable order.
    Blank device labels (e.g. a single-host run before `combine`) collapse to one
    unnamed facet so the plot still renders."""
    return sorted({(getattr(r, "device", "") or "") for r in results})


def _facet_axes(devices, figsize_per, **kw):
    """One subplot column per device (constrained layout when faceted, so the
    shared suptitle never overlaps the panels)."""
    n = max(len(devices), 1)
    w_per, h = figsize_per
    fig, axes = plt.subplots(1, n, figsize=(min(w_per * n, 22), h), squeeze=False,
                             layout="constrained" if n > 1 else None, **kw)
    return fig, axes[0]


def _plot_concurrency(results, operation: str, path: Path, all_impls) -> Optional[str]:
    """Aggregate throughput vs worker count for one operation, one line per impl,
    with the ideal-linear-scaling reference. Shows where the machine saturates.
    With >1 device (after `combine`), each device gets its own panel."""
    rows = [r for r in results if r.operation == operation and r.levels]
    if not rows:
        return None
    devices = _devices_of(rows)
    multi = len(devices) > 1
    fig, axes = _facet_axes(devices, (7, 4.5), sharey=True)
    for ax, dev in zip(axes, devices):
        for r in sorted([x for x in rows if (getattr(x, "device", "") or "") == dev],
                        key=lambda r: r.impl):
            pts = [(lv.workers, lv.aggregate_ops_per_sec) for lv in r.levels
                   if lv.aggregate_ops_per_sec > 0]
            if not pts:
                continue
            xs, ys = zip(*pts)
            color = _impl_color(r.impl, all_impls)
            ax.plot(xs, ys, marker="o", color=color, label=f"{r.impl} (measured)")
            # ideal linear scaling from this impl's single-worker baseline
            if r.baseline_ops_per_sec > 0:
                ax.plot(xs, [r.baseline_ops_per_sec * x for x in xs], linestyle=":",
                        color=color, alpha=0.5, label=f"{r.impl} (ideal linear)")
        ax.set_xlabel("concurrent workers")
        ax.set_title(dev if multi else f"[{dev}]" if dev else "")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel(f"aggregate {operation}s / second")
    fig.suptitle(f"Sustained {operation} throughput under concurrency (measured)",
                 fontweight="bold")
    return _save(fig, path)


def _plot_mining(results, path: Path, all_impls) -> Optional[str]:
    """Token mint rate vs difficulty (effort), log-log. Per impl: 1-core and
    whole-machine lines. A straight line here means rate ∝ 1/effort. With >1
    device (after `combine`), each device gets its own panel."""
    rows = [r for r in results if r.points]
    if not rows:
        return None
    devices = _devices_of(rows)
    multi = len(devices) > 1
    fig, axes = _facet_axes(devices, (7, 4.5), sharey=True)
    for ax, dev in zip(axes, devices):
        for r in sorted([x for x in rows if (getattr(x, "device", "") or "") == dev],
                        key=lambda r: r.impl):
            pts = [(p.effort, p.tokens_per_sec_1core, p.tokens_per_sec_machine)
                   for p in r.points if p.samples > 0 and p.tokens_per_sec_1core > 0]
            if not pts:
                continue
            xs = [p[0] for p in pts]
            color = _impl_color(r.impl, all_impls)
            ax.plot(xs, [p[1] for p in pts], marker="o", color=color,
                    label=f"{r.impl} — 1 core")
            ax.plot(xs, [p[2] for p in pts], marker="s", linestyle="--", color=color,
                    label=f"{r.impl} — {r.nproc} cores")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("difficulty (effort target)")
        ax.set_title(dev if multi else "")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("tokens minted / second")
    fig.suptitle("Mining rate vs difficulty (measured)", fontweight="bold")
    return _save(fig, path)


# ---------------------------------------------------------------- report driver


def generate(stats, checks, raw, out_dir: Path, meta, concurrency=None, mining=None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)

    write_csv(stats, out_dir / "results.csv")
    write_raw(raw, out_dir / "raw" / "results.json")

    impl_meta: dict[str, dict[str, Any]] = {}
    for r in raw:
        im = r.get("impl", {}) or {}
        name = im.get("name")
        if name and name not in impl_meta:
            impl_meta[name] = {"version": im.get("version"), "commit": im.get("commit"),
                               "compiler": (r.get("env", {}) or {}).get("compiler")}
    meta = {**meta, "impls": impl_meta}

    all_impls = sorted({s.impl for s in stats})
    devices = sorted({s.device_label for s in stats if s.ok})
    plots: list[str] = []

    def try_plot(fn, *a, **k):
        try:
            r = fn(*a, **k)
            if isinstance(r, list):
                plots.extend([x for x in r if x])
            elif r:
                plots.append(r)
        except RuntimeError as e:
            plots.append(f"__error__:{e}")

    has = lambda op: any(s.operation == op for s in stats)

    if has("solve"):
        try_plot(_facet, stats, _panel_time, "Solve time by runtime: C vs Rust",
                 "median solve time (ns)", plots_dir / "solve_time_by_runtime.png",
                 all_impls, lambda s: s.operation == "solve")
        try_plot(_facet, stats, _panel_throughput, "Solve throughput: C vs Rust",
                 "solves / second", plots_dir / "throughput.png", all_impls,
                 lambda s: s.operation == "solve")
        try_plot(_facet, stats, _panel_speedup, "JIT speedup over interpreter: C vs Rust",
                 "interpret / compiled (x faster)", plots_dir / "jit_speedup.png",
                 all_impls, lambda s: s.operation == "solve")
        try_plot(_facet, stats, _panel_rss, "Peak memory during solve: C vs Rust",
                 "peak RSS (KB)", plots_dir / "peak_rss.png", all_impls,
                 lambda s: s.operation == "solve")
        try_plot(_facet, stats, _panel_distribution, "Solve-time distribution: C vs Rust",
                 "solve time (ms)", plots_dir / "solve_distribution.png", all_impls,
                 lambda s: s.operation == "solve")
    if has("verify"):
        try_plot(_facet, stats, _panel_time, "Verify time by runtime: C vs Rust",
                 "median verify time (ns)", plots_dir / "verify_time.png", all_impls,
                 lambda s: s.operation == "verify")
    if has("hashx_compile"):
        try_plot(_facet, stats, _panel_compile, "HashX compile overhead: C vs Rust",
                 "median program-gen + compile (ns)", plots_dir / "compile_overhead.png",
                 all_impls, lambda s: s.operation == "hashx_compile")
    if has("effort"):
        try_plot(_facet, stats, lambda ax, s, im: _panel_effort(ax, s, im, "attempts"),
                 "Effort cost (attempts): C vs Rust", "mean attempts",
                 plots_dir / "effort_attempts.png", all_impls, lambda s: s.operation == "effort")
        try_plot(_facet, stats, lambda ax, s, im: _panel_effort(ax, s, im, "time"),
                 "Effort cost (time): C vs Rust", "median time (s)",
                 plots_dir / "effort_time.png", all_impls, lambda s: s.operation == "effort")

    # Cross-device (CPU vs CPU) headline charts -- emitted only when >1 device.
    if len(devices) >= 2:
        try_plot(_cross_device_bar, stats,
                 lambda s: s.operation == "solve" and s.runtime_requested in ("try-compile", "must-compile"),
                 lambda s: s.solves_per_sec, "Solve throughput across CPUs: C vs Rust",
                 "solves / second", plots_dir / "xdev_throughput.png", all_impls)
        try_plot(_cross_device_bar, stats,
                 lambda s: s.operation == "solve" and s.runtime_requested in ("try-compile", "must-compile"),
                 lambda s: s.median_ns, "Solve time across CPUs: C vs Rust",
                 "median solve time (ns)", plots_dir / "xdev_solve_time.png", all_impls)
        try_plot(_cross_device_bar, stats, lambda s: s.operation == "solve",
                 lambda s: float(s.peak_rss_kb), "Peak RSS across CPUs: C vs Rust",
                 "peak RSS (KB)", plots_dir / "xdev_peak_rss.png", all_impls)
        try_plot(_cross_device_bar, stats, lambda s: s.operation == "verify",
                 lambda s: s.median_ns, "Verify time across CPUs: C vs Rust",
                 "median verify time (ns)", plots_dir / "xdev_verify_time.png", all_impls)

    # DoS-protection effectiveness (needs both effort and verify measurements).
    dos = None
    if any(s.operation == "effort" for s in stats) and any(s.operation == "verify" for s in stats):
        try_plot(_plot_dos, stats, plots_dir / "dos_protection.png", all_impls)
        dos = dos_assess(stats)

    # Concurrency / saturation curves (one figure per operation; C vs Rust lines).
    if concurrency:
        for op in sorted({r.operation for r in concurrency}):
            try_plot(_plot_concurrency, concurrency, op,
                     plots_dir / f"concurrency_{op}.png", all_impls)

    # Mining rate vs difficulty (tokens/s vs effort, 1-core and whole-machine).
    if mining:
        try_plot(_plot_mining, mining, plots_dir / "mining_rate.png", all_impls)

    _write_markdown(stats, checks, plots, out_dir, meta, devices, dos, concurrency, mining)


def _fmt_ns(ns: float) -> str:
    if ns >= 1e9:
        return f"{ns/1e9:.3f} s"
    if ns >= 1e6:
        return f"{ns/1e6:.3f} ms"
    if ns >= 1e3:
        return f"{ns/1e3:.3f} µs"
    return f"{ns:.0f} ns"


def _concurrency_section(lines: list, concurrency, dos=None) -> None:
    """Render the measured concurrency/saturation results as a self-contained
    section. Deliberately additive: it reports the machine's real sustained
    capacity next to the per-core estimate, without altering the DoS numbers."""
    ok = [r for r in concurrency if r.levels and r.peak_ops_per_sec > 0]
    lines.append("## Sustained throughput under concurrency (measured)\n")
    lines.append(
        "The DoS section above reports **per-core** capacity as 1/latency from a "
        "single serial op. This section instead **measures** aggregate throughput "
        "with *N* worker processes running at once (N stepping up to the core "
        "count), so it captures real memory-bandwidth contention. It is additive — "
        "the per-core figures above are unchanged.\n"
    )
    if not ok:
        lines.append("_No usable concurrency measurements._\n")
        return

    devices = sorted({(r.device or "") for r in ok})
    multi = len(devices) > 1
    dev_hdr = "device | " if multi else ""
    dev_sep = "---|" if multi else ""
    nproc = max(r.nproc for r in ok)
    lines.append(
        f"Measured on up to **{nproc}** concurrent workers"
        + (f" across **{len(devices)}** devices" if multi else "") + ". "
        "*Peak* is the best aggregate ops/s observed; *knee* is the worker count "
        "where it peaks (adding workers past it stops helping). *Naïve N×* is the "
        "per-core figure multiplied by the core count — what a linear extrapolation "
        "would (over)predict; the *efficiency* column is measured peak ÷ naïve N×.\n"
    )
    lines.append(f"| {dev_hdr}impl | operation | 1 worker (per-core) | knee | measured peak | naïve N× | scaling efficiency |")
    lines.append(f"|{dev_sep}---|---|---|---|---|---|---|")
    for r in sorted(ok, key=lambda r: ((r.device or ""), r.operation, r.impl)):
        naive = r.baseline_ops_per_sec * r.nproc
        eff = (r.peak_ops_per_sec / naive) if naive > 0 else 0.0
        dev_cell = f"{r.device} | " if multi else ""
        lines.append(
            f"| {dev_cell}{r.impl} | {r.operation} | {r.baseline_ops_per_sec:,.0f} ops/s | "
            f"{r.knee_workers} workers | **{r.peak_ops_per_sec:,.0f} ops/s** | "
            f"{naive:,.0f} ops/s | {eff*100:.0f}% |"
        )
    lines.append("")

    # Per-level detail, grouped by operation then (device, impl).
    for op in sorted({r.operation for r in ok}):
        lines.append(f"### {op}: throughput vs. concurrency\n")
        lines.append(f"| {dev_hdr}impl | workers | ok | aggregate ops/s | per-worker ops/s | scaling eff. | peak RSS |")
        lines.append(f"|{dev_sep}---|---|---|---|---|---|---|")
        for r in sorted([x for x in ok if x.operation == op], key=lambda r: ((r.device or ""), r.impl)):
            dev_cell = f"{r.device} | " if multi else ""
            for lv in r.levels:
                rss = f"{lv.total_peak_rss_kb/1024:.0f} MB" if lv.total_peak_rss_kb else "n/a"
                lines.append(
                    f"| {dev_cell}{r.impl} | {lv.workers} | {lv.ok_workers} | "
                    f"{lv.aggregate_ops_per_sec:,.0f} | {lv.per_worker_ops_per_sec:,.0f} | "
                    f"{lv.scaling_efficiency*100:.0f}% | {rss} |"
                )
        lines.append("")


def _mining_section(lines: list, mining) -> None:
    """Measured mint rate vs difficulty: 1-core and whole-machine tokens/s."""
    ok = [r for r in mining if any(p.samples > 0 for p in r.points)]
    lines.append("## Mining rate vs difficulty (measured)\n")
    lines.append(
        "How many effort-qualified tokens can be minted per second at a given "
        "difficulty. The **whole-machine** rate is the reliable figure: it averages "
        "one streaming search per core over independent nonce ranges. Per-core is that "
        "rate divided by the core count (token-find time is heavy-tailed, so the "
        "separately-sampled single-core mean is noisier and can even exceed the machine "
        "rate ÷ cores at low sample counts — prefer the derived per-core). Mint rate "
        "falls ~1/effort, so difficulty sets the rate directly.\n"
    )
    if not ok:
        lines.append("_No usable mining measurements._\n")
        return
    for r in ok:
        nproc = r.nproc
        lines.append(f"**`{r.impl}`** on `{r.device}` (base `{r.challenge_base}`), "
                     f"whole-machine = {nproc} cores:\n")
        lines.append("| difficulty (effort) | mean attempts/token | tokens/s [%d cores] | "
                     "tokens/s [1 core, ÷%d] |" % (nproc, nproc))
        lines.append("|---|---|---|---|")
        for p in sorted(r.points, key=lambda p: p.effort):
            if p.samples == 0:
                lines.append(f"| {p.effort} | _no sample reached target_ | — | — |")
                continue
            per_core = p.tokens_per_sec_machine / nproc if nproc else 0.0
            lines.append(
                f"| {p.effort} | {p.attempts_mean:,.0f} | "
                f"**{p.tokens_per_sec_machine:,.2f}** | {per_core:,.3f} |"
            )
        lines.append("")
        # Message sizes vs difficulty, measured from real minted tokens. The
        # interesting result is constancy: cost scales with E, bytes do not.
        sized = [p for p in r.points if p.solution_bytes_max > 0]
        if sized:
            lines.append("**Message sizes (measured from every minted token):** ")
            rows_sz = []
            for p in sorted(sized, key=lambda p: p.effort):
                span = (f"{p.solution_bytes_min}" if p.solution_bytes_min == p.solution_bytes_max
                        else f"{p.solution_bytes_min}-{p.solution_bytes_max}")
                rows_sz.append(f"E={p.effort}: solution {span} B + nonce {p.nonce_bytes_wire} B")
            const = all(p.solution_bytes_min == sized[0].solution_bytes_max == p.solution_bytes_max
                        for p in sized)
            lines.append("; ".join(rows_sz) + ".")
            if const:
                lines.append(
                    f"Token size is **constant in difficulty**: every token at every "
                    f"measured E is exactly {sized[0].solution_bytes_max} B solution + "
                    f"{sized[0].nonce_bytes_wire} B nonce — raising E raises solve cost, "
                    f"never message size.\n"
                )
            else:
                lines.append("Token size VARIED across efforts — investigate.\n")
        # Headline: 1/effort check across the measured span, on the machine rate.
        # (sorted by effort so lo/hi are the true endpoints regardless of config order)
        good = sorted([p for p in r.points if p.samples > 0 and p.tokens_per_sec_machine > 0],
                      key=lambda p: p.effort)
        if len(good) >= 2:
            lo, hi = good[0], good[-1]
            fold_e = hi.effort / lo.effort if lo.effort else 0
            fold_r = (lo.tokens_per_sec_machine / hi.tokens_per_sec_machine) if hi.tokens_per_sec_machine else 0
            lines.append(
                f"> Over a {fold_e:.0f}× rise in difficulty ({lo.effort}→{hi.effort}), "
                f"the machine mint rate fell {fold_r:.0f}× — ~1/effort, "
                f"so halving the target roughly doubles the mint rate.\n"
            )


def _write_markdown(stats, checks, plots, out_dir: Path, meta, devices, dos=None, concurrency=None, mining=None) -> None:
    lines: list[str] = []
    lines.append("# Equi-X Benchmark Report\n")
    lines.append(f"- Generated: {meta.get('timestamp', 'n/a')}")
    lines.append(f"- Config: `{meta.get('config', 'n/a')}`")
    lines.append(f"- Devices (CPUs): {', '.join(devices) if devices else 'n/a'}")
    for dl in devices:
        ex = next((s for s in stats if s.device_label == dl), None)
        if ex:
            lines.append(f"    - `{dl}`: {ex.device_name} ({ex.device_arch}, {ex.device_type})")
    for impl, info in (meta.get("impls") or {}).items():
        lines.append(
            f"- `{impl}`: version {info.get('version')}, commit {info.get('commit')}, "
            f"built with {info.get('compiler')}"
        )
    lines.append("")

    lines.append("## Correctness cross-check (interop gate)\n")
    if checks:
        overall = all(c.passed for c in checks)
        lines.append(f"**Overall: {'PASS ✅' if overall else 'FAIL ❌'}**\n")
        lines.append("| kind | detail | result |")
        lines.append("|------|--------|--------|")
        for c in checks:
            lines.append(f"| {c.kind} | {c.detail} | {'PASS' if c.passed else 'FAIL'} |")
    else:
        lines.append("_No cross-checks run (e.g. combined report)._")
    lines.append("")

    # DoS-protection effectiveness
    if dos is not None:
        rows, effective, threshold = dos
        lines.append("## DoS-protection effectiveness (this system)\n")
        lines.append(
            "Equi-X defends by making requesters *solve* (expensive) while the service "
            "only *verifies* (cheap). Protection factor = measured attacker time to craft "
            "one accepted token at a given effort ÷ measured verify time. "
            f"Judged **effective** when ≥ {threshold:.0f}× on every measured point.\n"
        )
        if rows:
            from .dosprotect import min_effective_effort
            verdict = "EFFECTIVE ✅" if effective else "WEAK ⚠️"
            mee = min_effective_effort(rows, threshold)
            eff_where = ", ".join(
                f"`{d}`: effort ≥ {e}" if e is not None else f"`{d}`: not reached in tested range"
                for d, e in mee.items()
            )
            best = max(rows, key=lambda r: r.effort)
            lines.append(
                f"**Verdict: {verdict}** (effective from — {eff_where}).\n\n"
                f"At effort {best.effort}, an attacker needs ~{best.attacker_s:.3g}s "
                f"(impl `{best.attacker_impl}`) to craft one accepted request, while the "
                f"defender verifies in ~{best.defender_verify_s*1e6:.2f}µs "
                f"(**{best.protection_factor:,.0f}×** asymmetry; one core screens "
                f"~{best.verify_per_sec:,.0f} requests/s vs the attacker's "
                f"~{best.attacker_tokens_per_sec:,.2f} tokens/s).\n"
            )
            lines.append("| device | effort | attacker time/token | attacker impl | verify time | protection factor | verify/s | attacker tokens/s |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for r in rows:
                lines.append(
                    f"| {r.device} | {r.effort} | {_fmt_ns(r.attacker_s*1e9)} | {r.attacker_impl} | "
                    f"{_fmt_ns(r.defender_verify_s*1e9)} | {r.protection_factor:,.0f}× | "
                    f"{r.verify_per_sec:,.0f} | {r.attacker_tokens_per_sec:,.3f} |"
                )
        else:
            lines.append("_Insufficient effort/verify measurements to assess._")
        lines.append("")

    # Measured concurrency / saturation -- complements (never overwrites) the
    # per-core DoS estimate above.
    if concurrency:
        _concurrency_section(lines, concurrency, dos)

    # Measured mining rate vs difficulty.
    if mining:
        _mining_section(lines, mining)

    note = ("every plot compares C vs Rust; with multiple CPUs each plot is faceted "
            "per CPU and `xdev_*` charts compare CPUs directly")
    lines.append(f"## Comparison plots ({note})\n")
    for p in plots:
        if p.startswith("__error__:"):
            lines.append(f"> ⚠️ {p[len('__error__:'):]}\n")
        else:
            lines.append(f"### {p.replace('_', ' ').replace('.png','').title()}\n")
            lines.append(f"![{p}](plots/{p})\n")

    def table(op, cols, rowfn):
        rows = [s for s in stats if s.operation == op]
        if not rows:
            return
        lines.append(f"## {op} results\n")
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for s in sorted(rows, key=lambda s: (s.device_label, json.dumps(s.label), s.impl, s.runtime_requested)):
            lines.append("| " + " | ".join(rowfn(s)) + " |")
        lines.append("")

    table("solve", ["device", "challenge", "impl", "runtime", "median", "p95", "solves/s", "hashes/s", "sols/solve", "RSS(KB)"],
          lambda s: [s.device_label, str(s.label.get("challenge")), s.impl, str(s.runtime_effective),
                     _fmt_ns(s.median_ns), _fmt_ns(s.p95_ns), f"{s.solves_per_sec:.1f}",
                     f"{s.hashes_per_sec:,.0f}", f"{s.solutions_mean:.2f}", str(s.peak_rss_kb)])
    table("verify", ["device", "challenge", "impl", "runtime", "median", "p95", "result", "RSS(KB)"],
          lambda s: [s.device_label, str(s.label.get("challenge")), s.impl, str(s.runtime_effective),
                     _fmt_ns(s.median_ns), _fmt_ns(s.p95_ns), str(s.verify_result), str(s.peak_rss_kb)])
    table("hashx_compile", ["device", "challenge", "impl", "runtime", "median compile", "median exec", "RSS(KB)"],
          lambda s: [s.device_label, str(s.label.get("challenge")), s.impl, str(s.runtime_effective),
                     _fmt_ns(s.compile_median_ns), _fmt_ns(s.median_ns), str(s.peak_rss_kb)])
    table("effort", ["device", "base", "target", "impl", "runtime", "mean attempts", "median time", "mean achieved"],
          lambda s: [s.device_label, str(s.label.get("base")), str(s.label.get("target_effort")), s.impl,
                     str(s.runtime_effective), f"{s.attempts_mean:.1f}", _fmt_ns(s.median_ns),
                     f"{s.achieved_effort_mean:.0f}"])

    lines.append("---")
    lines.append("_See `results.csv` for the full flat dataset and `raw/results.json` for per-rep data._")
    (out_dir / "report.md").write_text("\n".join(lines))
