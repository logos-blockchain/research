"""Parameter-sweep expansion, parallel execution, and result persistence."""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import pandas as pd
import yaml
from joblib import Parallel, delayed
from tqdm import tqdm

from .config import SweepConfig
from .engine import run_trajectory


def run_sweep(sweep: SweepConfig, n_jobs: int = -1, progress: bool = True) -> pd.DataFrame:
    """Expand the grid, run every config (embarrassingly parallel), return one big frame."""
    configs = sweep.expand()
    runner = Parallel(n_jobs=n_jobs, return_as="generator")(
        delayed(run_trajectory)(c) for c in configs
    )
    if progress:
        runner = tqdm(runner, total=len(configs), desc="configs")
    rows: list[dict] = []
    for traj in runner:
        rows.extend(traj)
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
    while run_dir.exists():
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
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--no-figures", action="store_true", help="skip auto figure generation")
    args = parser.parse_args(argv)

    label = args.label or Path(args.config).stem
    run_dir = new_run_dir(args.outdir, label)
    sweep = load_sweep_yaml(args.config)
    df = run_sweep(sweep, n_jobs=args.n_jobs)
    results_path = run_dir / "results.parquet"
    persist(df, results_path)
    n_cfg = df[["n_nodes", "stake_dist", "latency", "max_uncles", "uncle_strategy", "replicate"]]
    print(f"wrote {len(df)} rows ({len(n_cfg.drop_duplicates())} configs) -> {results_path}")
    if not args.no_figures:
        from .plotting.make_figures import render
        n_fig = render(df, run_dir / "figures")
        print(f"wrote {n_fig} figures -> {run_dir / 'figures'}")
    print(f"run dir: {run_dir}")


if __name__ == "__main__":  # pragma: no cover
    main()
