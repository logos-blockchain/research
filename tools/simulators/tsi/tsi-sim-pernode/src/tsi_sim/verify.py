"""Per-node analytic checks (``tsi-verify``). Exits non-zero if any check fails.

Validates that per-node D_est disagreement collapses (the reduced-model assumption) and
that the full-mesh baseline reproduces the reduced model. Replicates run across cores.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .config import SimConfig
from .engine import run_trajectory
from .theory import expected_ratio

F = 1.0 / 30.0
K = 32
EPOCHS = 20
REPS = 8
BURN = 10


def tail(cfg: SimConfig, col: str, reps: int = REPS) -> float:
    def one(r: int) -> float:
        df = pd.DataFrame(run_trajectory(replace(cfg, replicate=r)))
        return float(df[col].iloc[BURN:].mean())
    vals = Parallel(n_jobs=-1, backend="loky", inner_max_num_threads=1)(
        delayed(one)(r) for r in range(reps)
    )
    return float(np.mean(vals))


def check(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Per-node TSI analytic checks")
    ap.add_argument("--old", action="store_true",
                    help="run the old (pre countable redesign) uncle model")
    args = ap.parse_args(argv)
    uncle_model = "old" if args.old else "countable"

    results = []
    common = dict(n_nodes=300, stake_dist="uniform", k=K, epochs=EPOCHS, genesis_d_factor=0.5,
                  uncle_model=uncle_model)

    # 1. Full-mesh baseline: zero per-node divergence, full window agreement.
    fm = SimConfig(topology="full_mesh", latency=4, max_uncles=0, **common)
    rng_range = tail(fm, "range_ratio")
    agree = tail(fm, "agreement_window")
    results.append(check("full-mesh: zero D_est spread, full window agreement",
                         rng_range < 1e-9 and agree > 0.999,
                         f"range={rng_range:.2e} agreement_window={agree:.4f}"))

    # 2. Full-mesh mean accuracy ~ reduced theory(q).
    mean_r = tail(fm, "mean_ratio")
    q = tail(fm, "mean_q")
    pred = float(expected_ratio(F, q))
    results.append(check("full-mesh mean ratio ~ theory(q)",
                         abs(mean_r - pred) < 0.03,
                         f"sim={mean_r:.4f} theory(q={q:.3f})={pred:.4f}"))

    # 3. Regular graph: still zero D_est divergence (window settled), but tip forking present.
    reg = SimConfig(topology="regular", degree=8, link_latency_mean=2.0, max_uncles=0, **common)
    rng_range = tail(reg, "range_ratio")
    agree_w = tail(reg, "agreement_window")
    agree_t = tail(reg, "agreement_tip")
    results.append(check("regular graph: D_est agrees (window) despite tip forks",
                         rng_range < 1e-9 and agree_w > 0.999 and agree_t < 1.0,
                         f"range={rng_range:.2e} agree_win={agree_w:.4f} agree_tip={agree_t:.4f}"))

    # 4. Topology affects mean accuracy: sparser/slower graph -> lower mean ratio (more forks).
    sparse = tail(SimConfig(topology="regular", degree=4, link_latency_mean=6.0,
                            max_uncles=0, **common), "mean_ratio")
    dense = tail(SimConfig(topology="regular", degree=16, link_latency_mean=1.0,
                           max_uncles=0, **common), "mean_ratio")
    results.append(check("topology shifts mean accuracy (sparse < dense)",
                         sparse < dense,
                         f"sparse(deg4,ll6)={sparse:.4f} < dense(deg16,ll1)={dense:.4f}"))

    # 5. Uncles recover the mean accuracy under a graph (as in the reduced model).
    u0 = tail(SimConfig(topology="regular", degree=8, link_latency_mean=4.0,
                        max_uncles=0, **common), "mean_ratio")
    u4 = tail(SimConfig(topology="regular", degree=8, link_latency_mean=4.0,
                        max_uncles=4, uncle_strategy="oldest", **common), "mean_ratio")
    results.append(check("uncles recover mean accuracy under topology",
                         abs(u4 - 1) < abs(u0 - 1) and abs(u4 - 1) < 0.03,
                         f"mean ratio U0={u0:.4f} -> U4={u4:.4f}"))

    print()
    n_pass = sum(results)
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
