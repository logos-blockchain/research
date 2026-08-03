"""Run a pd sweep from a YAML config -> propagation.parquet + adversary.parquet + figures.

Each topology ``(n_nodes, degree, graph_seed)`` is one embarrassingly-parallel work item; the
engine builds it once and measures the propagation and adversary sub-grids on it.
"""

from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import pandas as pd
import yaml
from joblib import Parallel, delayed
from tqdm import tqdm

from .config import SimConfig, SweepConfig
from .engine import run_graph_cell

HERE = Path(__file__).resolve().parents[2]   # pd/


def load_sweep_yaml(path: str | Path) -> SweepConfig:
    with open(path) as f:
        return SweepConfig.from_dict(yaml.safe_load(f) or {})


def new_run_dir(outdir: Path, label: str) -> Path:
    ts = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = outdir / f"{ts}_{label}"
    suffix = 2
    while run_dir.exists():
        run_dir = outdir / f"{ts}_{label}_{suffix}"
        suffix += 1
    run_dir.mkdir(parents=True)
    return run_dir


def _cell_worker(base: SimConfig, prop_grid, unresponsive_fracs, adv_grid):
    return run_graph_cell(base, prop_grid, unresponsive_fracs, adv_grid)


def run_sweep(sweep: SweepConfig,
              n_jobs: int = -1) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cells = sweep.graph_cells()
    prop_grid = sweep.prop_grid()
    unresponsive_fracs = list(sweep.unresponsive_frac)
    adv_grid = sweep.adv_grid()
    bases = [sweep.base_config(n, d, g) for (n, d, g) in cells]
    results = Parallel(n_jobs=n_jobs, prefer="processes")(
        delayed(_cell_worker)(base, prop_grid, unresponsive_fracs, adv_grid)
        for base in tqdm(bases, desc="topologies")
    )
    prop_rows = [r for pr, _, _ in results for r in pr]
    adv_rows = [r for _, ar, _ in results for r in ar]
    deanon_rows = [r for _, _, dr in results for r in dr]
    return pd.DataFrame(prop_rows), pd.DataFrame(adv_rows), pd.DataFrame(deanon_rows)


def persist(prop_df: pd.DataFrame, adv_df: pd.DataFrame, deanon_df: pd.DataFrame,
            run_dir: Path) -> None:
    prop_df.to_parquet(run_dir / "propagation.parquet", index=False)
    adv_df.to_parquet(run_dir / "adversary.parquet", index=False)
    deanon_df.to_parquet(run_dir / "deanon.parquet", index=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a pd peering-degree sweep")
    ap.add_argument("--config", required=True, help="sweep YAML (see configs/)")
    ap.add_argument("--outdir", default=str(HERE / "runs"))
    ap.add_argument("--label", default=None)
    ap.add_argument("--n-jobs", type=int, default=-1)
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args(argv)

    sweep = load_sweep_yaml(args.config)
    label = args.label or Path(args.config).stem
    run_dir = new_run_dir(Path(args.outdir), label)
    prop_df, adv_df, deanon_df = run_sweep(sweep, n_jobs=args.n_jobs)
    persist(prop_df, adv_df, deanon_df, run_dir)
    print(f"wrote {len(prop_df)} propagation + {len(adv_df)} adversary + "
          f"{len(deanon_df)} deanon rows -> {run_dir}")

    if not args.no_figures:
        from .plotting.make_figures import render
        figs = render(prop_df, adv_df, deanon_df, run_dir / "figures")
        print(f"wrote {len(figs)} figures -> {run_dir / 'figures'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
