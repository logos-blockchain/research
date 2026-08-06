"""Parameter-sweep expansion, parallel execution, and result persistence.

Across-config parallelism is the main multicore lever: ``run_trajectory`` is a pure
function of an immutable, hash-seeded ``SimConfig``, so results are bitwise
order-independent and the grid is embarrassingly parallel. We use joblib's process-based
**loky** backend (this workload is CPU-bound Python that holds the GIL, so threads would
serialise), and pin each worker to a single BLAS thread to avoid oversubscription.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import multiprocessing as mp
import os
import queue
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from joblib import Parallel, delayed
from tqdm import tqdm

from .config import SimConfig, SweepConfig
from .engine import run_trajectory
from .memguard import DEFAULT_BUDGET_FRAC, ArrivalMatrixTooLarge
from .memguard import total_ram_bytes as _total_ram_bytes

# ``calibrate="auto"`` runs a real memory probe when the analytic estimate is either extrapolated
# past the validated network size (N > CALIBRATION_N_THRESHOLD) OR simply large in absolute terms
# (per-worker estimate > CALIBRATION_BYTES_THRESHOLD) — the latter catches a block-count explosion
# from a low genesis_d_factor even at small N, which is exactly what OOM-froze the box at N=1000.
CALIBRATION_N_THRESHOLD = 2000
CALIBRATION_BYTES_THRESHOLD = 1.5 * 1024**3

# Keep numpy/BLAS single-threaded inside each worker process (belt-and-braces alongside
# joblib's inner_max_num_threads); prevents N_workers x N_blas_threads oversubscription.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")


def expected_peak_blocks(config: SimConfig) -> int:
    """Expected block count of the *heaviest* epoch (genesis), which sizes the arrival matrix.

    ``n_blocks`` is NOT ``~10*k``: it is the number of lottery wins over the epoch, which scales
    with ``sum_i phi(w_i / D_est)``. At genesis ``D_est = genesis_d_factor * D_true`` is at its
    smallest, so ``sum(stake)/D_est = 1/genesis_d_factor`` is largest and block production peaks
    there (a low ``genesis_d_factor`` can inflate it 100x — the collapsed-estimate regime). We
    realise the seeded stake and compute the expected genesis-epoch win count exactly; this is
    what previously blew the estimate up by ~90x and OOM-ed the box. Capped at ``N*E`` (every
    node can win every slot at most once).
    """
    from .lottery import win_probs
    from .rng import seedseq_for
    from .stake import make_stake

    child0 = seedseq_for(config).spawn(config.epochs + 3)[0]
    stake = make_stake(config, np.random.default_rng(child0))
    d_est_genesis = config.genesis_d_factor * float(stake.sum())
    p = win_probs(stake, d_est_genesis, config.f)
    expected = float(config.epoch_len) * float(p.sum())
    return int(min(expected, float(config.n_nodes) * config.epoch_len)) + 1


def _arrival_columns(config: SimConfig, peak_blocks: int) -> int:
    """Estimated stored arrival columns: full ``n_blocks``, or the pruned keep-span window.

    With ``prune_arrival`` the arrival buffer keeps only blocks inside ``max(horizon, W)``
    slots, so its width is ``~keepspan * blocks_per_slot`` regardless of how far the block count
    exploded. We don't have the graph here, so ``horizon`` is approximated generously (dominated by
    ``uncle_window``, plus the blend mix cascade); the exact buffer size is guarded in-worker.
    """
    if not (config.prune_arrival and config.windowed_fork_choice):
        return peak_blocks
    per_slot = peak_blocks / config.epoch_len if config.epoch_len else peak_blocks
    keepspan = float(config.effective_uncle_window)
    if config.topology == "blend":
        lat = max(config.link_latency_mean, 0.1)
        keepspan = max(keepspan, (config.blend_hops + 1) * lat * 4
                       + config.blend_hops * config.blend_delay_max)
    buf_width = 2.0 * (keepspan * per_slot * 1.5 + 64)     # ~ _build_pruned's 2*(cap + slack)
    return int(min(peak_blocks, buf_width)) + 1


def estimate_worker_bytes(config: SimConfig) -> int:
    """Rough peak RSS of one worker running ``config``.

    The arrival buffer and the dense ``path_latency`` (``N x N`` float64, plus Dijkstra scratch)
    dominate; everything else (block-tree 1-D arrays, measurement temp) is smaller. The arrival
    term is ``N * columns * 8`` where ``columns`` is the full peak-epoch block count
    (``expected_peak_blocks``, capturing a low-``genesis_d_factor`` explosion) or, with
    ``prune_arrival``, just the bounded keep-span window (``_arrival_columns``). Factors are
    generous so the cap errs toward fewer, safe workers.
    """
    n = config.n_nodes
    cols = _arrival_columns(config, expected_peak_blocks(config))
    arrival = 1.35 * n * cols * 8                       # buffer + measurement/fork-choice temps
    path_latency = 2.2 * n * n * 8                      # dense (N,N) + Dijkstra predecessor/scratch
    fixed = 250 * 1024**2                               # python + numpy + numba loaded per process
    return int(arrival + path_latency + fixed)


def _ru_maxrss_bytes(ru_maxrss: int) -> int:
    """Normalise ``getrusage`` peak RSS to bytes (macOS reports bytes, Linux kibibytes)."""
    return int(ru_maxrss) if sys.platform == "darwin" else int(ru_maxrss) * 1024


def _calibration_target(config: SimConfig, q: mp.Queue) -> None:  # pragma: no cover - subprocess
    """Child entry point: run ONE epoch of ``config`` and report this process's peak RSS.

    One epoch reaches the same peak as a full trajectory — the arrival matrix ``A`` and the
    ``path_latency`` matrix are (re)built every epoch and the measurement temporary peaks within
    an epoch — so a single epoch is a faithful, cheap probe of a worker's high-water mark.

    The probe bounds ITSELF to a fraction of physical RAM (overriding any inherited budget): it
    must be free to allocate the real peak in order to measure it, but must still fail loud rather
    than freeze if the heaviest config exceeds the box — in which case the parent falls back to the
    (large) analytic estimate.
    """
    import resource

    from .engine import run_trajectory
    from .memguard import total_ram_bytes
    os.environ["TSI_ARRIVAL_BYTES_BUDGET"] = str(int(DEFAULT_BUDGET_FRAC * total_ram_bytes()))
    run_trajectory(replace(config, epochs=1))
    q.put(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def measure_worker_bytes(config: SimConfig, timeout: float = 900.0) -> int | None:
    """Peak RSS (bytes) of a real worker running ``config``, measured in a fresh spawned
    process — the same isolation loky gives each worker, so numba/numpy/scratch are all counted.

    Returns ``None`` if the probe cannot start, crashes, or exceeds ``timeout`` (the caller then
    falls back to the analytic estimate). ``spawn`` matches loky and keeps the probe independent
    of the parent's already-imported modules; it needs an importable ``__main__`` (a real script
    or ``-m`` entry point), so from a bare REPL/stdin the child fails to bootstrap and we return
    ``None`` promptly by polling liveness rather than blocking the full timeout.
    """
    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_calibration_target, args=(config, q), daemon=True)
    proc.start()
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                ru_maxrss = q.get(timeout=1.0)
                return _ru_maxrss_bytes(ru_maxrss)
            except queue.Empty:
                if not proc.is_alive():        # child died (bootstrap failure / crash / OOM-kill)
                    return None
                if time.monotonic() >= deadline:
                    return None
    finally:
        if proc.is_alive():
            proc.terminate()
        proc.join(timeout=5.0)


@dataclass
class WorkerPlan:
    """The chosen worker count plus the numbers behind it (for logging)."""
    n_jobs: int
    per_worker_bytes: int
    calibrated: bool
    ram_bytes: int
    mem_frac: float


def plan_workers(requested: int, configs: list[SimConfig], mem_frac: float,
                 calibrate: str = "auto") -> WorkerPlan:
    """Size the worker pool so ``n_jobs * per-worker peak`` fits ``mem_frac`` of physical RAM.

    Per-worker peak is the analytic ``estimate_worker_bytes`` by default, but is replaced by a
    **measured** peak RSS (one epoch of the heaviest config, in a spawned process) when the
    calibration probe fires:

    * ``calibrate="auto"`` (default) — probe when the estimate is extrapolated past the validated
      network size (N > ``CALIBRATION_N_THRESHOLD``) OR is large in absolute terms
      (> ``CALIBRATION_BYTES_THRESHOLD``); the latter catches a low-``genesis_d_factor`` block
      explosion even at small N;
    * ``calibrate="always"`` — always probe;
    * ``calibrate="never"`` — never probe (analytic estimate only).

    ``requested`` follows joblib's convention (``-1`` = all logical cores); ``mem_frac <= 0``
    disables the cap entirely.
    """
    cores = os.cpu_count() or 1
    want = cores if requested < 0 else max(1, requested)
    ram = _total_ram_bytes()
    if mem_frac <= 0.0 or not configs:
        return WorkerPlan(want, 0, False, ram, mem_frac)

    heaviest = max(configs, key=estimate_worker_bytes)
    per_worker = estimate_worker_bytes(heaviest)
    calibrated = False
    do_probe = calibrate == "always" or (calibrate == "auto" and (
        heaviest.n_nodes > CALIBRATION_N_THRESHOLD
        or per_worker > CALIBRATION_BYTES_THRESHOLD))
    if do_probe:
        measured = measure_worker_bytes(heaviest)
        if measured is not None:
            per_worker = int(measured * 1.1)        # 10% headroom over the measured high-water mark
            calibrated = True

    budget = int(mem_frac * ram)
    fit = max(1, budget // per_worker)
    return WorkerPlan(min(want, fit), per_worker, calibrated, ram, mem_frac)


def run_sweep(
    sweep: SweepConfig, n_jobs: int = -1, progress: bool = True, batch_size: str | int = "auto",
    mem_frac: float = 0.7, calibrate: str = "auto",
) -> pd.DataFrame:
    """Expand the grid, run every config across cores (loky), return one big frame.

    ``n_jobs=-1`` uses all logical cores, but the count is then **capped** so that
    ``workers * per-worker peak RSS`` stays under ``mem_frac`` of physical RAM (``mem_frac=0``
    uncaps concurrency but still keeps the per-process fail-loud guard). This prevents the
    ``(N x n_blocks)`` arrival matrix from OOM-ing the box when many heavy configs run at once —
    including the collapsed-``D_est`` regime where a low ``genesis_d_factor`` explodes ``n_blocks``
    (see ``expected_peak_blocks``). Per-worker peak is measured by a **calibration probe** when
    heavy (see ``plan_workers`` / ``calibrate``), and each worker additionally enforces an
    in-process budget (``TSI_ARRIVAL_BYTES_BUDGET`` on both ``A`` and ``path_latency``) so a
    mis-estimated config fails loud instead of freezing the box. ``batch_size`` defaults to joblib
    "auto"; pass ``1`` for a small grid of heavy full-scale configs.
    """
    configs = sweep.expand()
    plan = plan_workers(n_jobs, configs, mem_frac, calibrate)
    # Per-worker byte budget for the in-worker guard: each worker's share of the RAM budget.
    # Enforced in build_tree_pernode (A) and build_path_latency (N^2) -> ArrivalMatrixTooLarge.
    # "0" is NOT "unlimited": memguard resolves it to DEFAULT_BUDGET_FRAC of RAM, so even a
    # `mem_frac=0` run keeps an absolute per-process ceiling (no single alloc can freeze the box).
    worker_budget = (int(mem_frac * plan.ram_bytes // plan.n_jobs)
                     if (mem_frac > 0 and plan.n_jobs) else 0)
    os.environ["TSI_ARRIVAL_BYTES_BUDGET"] = str(worker_budget)
    if progress:
        src = "measured" if plan.calibrated else "estimated"
        gb = plan.per_worker_bytes / 1024**3
        print(f"[sweep] {len(configs)} configs; ~{gb:.2f} GB/worker ({src}); "
              f"using {plan.n_jobs} worker(s) of {os.cpu_count()} cores "
              f"(RAM {plan.ram_bytes / 1024**3:.0f} GB x cap {mem_frac:g})")
        if worker_budget and plan.per_worker_bytes > worker_budget:
            print(f"[sweep] WARNING: a single config's estimated peak "
                  f"({gb:.1f} GB) exceeds its per-worker RAM share "
                  f"({worker_budget / 1024**3:.1f} GB); it may swap or hit the arrival-matrix "
                  f"guard. Raise genesis_d_factor, lower n_nodes/k/epochs, or raise --mem-frac.")
    runner = Parallel(
        n_jobs=plan.n_jobs,
        backend="loky",
        inner_max_num_threads=1,
        batch_size=batch_size,
        return_as="generator",
    )(delayed(run_trajectory)(c) for c in configs)
    if progress:
        runner = tqdm(runner, total=len(configs), desc="configs")
    rows: list[dict] = []
    try:
        for traj in runner:
            rows.extend(traj)
    except ArrivalMatrixTooLarge as exc:
        raise RuntimeError(
            f"aborting sweep: {exc} (worker memory guard tripped — the per-worker estimate was "
            f"too low, likely an under-modelled block explosion)."
        ) from exc
    return pd.DataFrame(rows)


def persist(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)


def load_sweep_yaml(path: str | Path) -> SweepConfig:
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return SweepConfig.from_dict(data)


def new_run_dir(outdir: str | Path, label: str) -> Path:
    """Create a fresh timestamped run directory so runs never overwrite each other."""
    ts = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = Path(outdir) / f"{ts}_{label}"
    run_dir, i = base, 2
    while run_dir.exists():                 # avoid same-second collisions
        run_dir = base.with_name(f"{base.name}_{i}")
        i += 1
    run_dir.mkdir(parents=True)
    return run_dir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a TSI parameter sweep + figures")
    parser.add_argument("--config", required=True, help="sweep YAML")
    parser.add_argument("--outdir", default="runs",
                        help="parent dir; a dated sub-folder is created per run")
    parser.add_argument("--label", default=None, help="run label (default: config name)")
    parser.add_argument("--n-jobs", type=int, default=-1, help="-1 = all logical cores")
    parser.add_argument("--batch-size", default="auto",
                        help="'auto' (default) or an int; use 1 for a small heavy grid")
    parser.add_argument("--mem-frac", type=float, default=0.7,
                        help="cap concurrent workers to this fraction of physical RAM "
                             "(0 disables the cap)")
    parser.add_argument("--calibrate", choices=["auto", "always", "never"], default="auto",
                        help="measure a real worker's peak RSS to size the pool: 'auto' "
                             "(default) probes when N>2000, 'always', or 'never' (estimate only)")
    parser.add_argument("--no-figures", action="store_true",
                        help="skip auto figure generation")
    parser.add_argument("--old", action="store_true",
                        help="run the old (pre countable redesign) uncle model: window = "
                             "uncle_window slots, any-depth orphans referenceable, every "
                             "baked reference counts; bit-reproduces historical runs")
    args = parser.parse_args(argv)

    batch_size = int(args.batch_size) if args.batch_size != "auto" else "auto"
    label = args.label or (Path(args.config).stem + ("-old" if args.old else ""))
    run_dir = new_run_dir(args.outdir, label)

    sweep = load_sweep_yaml(args.config)
    if args.old:
        sweep.base["uncle_model"] = "old"
    df = run_sweep(sweep, n_jobs=args.n_jobs, batch_size=batch_size, mem_frac=args.mem_frac,
                   calibrate=args.calibrate)
    results_path = run_dir / "results.parquet"
    persist(df, results_path)
    key_cols = ["n_nodes", "stake_dist", "topology", "degree", "link_latency_mean",
                "latency", "uncle_model", "max_uncles", "uncle_strategy", "init_dest",
                "replicate"]
    n_cfg = len(df[key_cols].drop_duplicates())
    print(f"wrote {len(df)} rows ({n_cfg} configs) -> {results_path}")

    if not args.no_figures:
        from .plotting.make_figures import render
        n_fig = render(df, run_dir / "figures")
        print(f"wrote {n_fig} figures -> {run_dir / 'figures'}")
    print(f"run dir: {run_dir}")


if __name__ == "__main__":  # pragma: no cover
    main()
