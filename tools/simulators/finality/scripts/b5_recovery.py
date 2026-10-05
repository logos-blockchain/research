"""Phase B5: the density window automatic recovery needs (PLAN.md B5, H6).

    python scripts/b5_recovery.py       # needs runs/a1; writes runs/b5/recovery_*.csv

- engine: the canonical chain's block count in windows of W slots, from the A1 configuration at
  testnet's Blend (1 hop, 1 round) and the specification's (3 hops, up to 3 rounds), 0.1 s
  links, 8 replicates. Its variance over its mean is set beside the binomial model's.
- window: the adversary's chance of a strictly denser fork in one window
  (src/finality_sim/recovery.py) at today's s_gen = floor(k/4f), and the smallest window that
  brings it to eps, under random delay (A1's growth) and a worst case of delta seconds.
- share: the largest share each k holds when the window is as long as the lottery parameters
  allow, 4 floor(k/f) slots.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.baseline import build_epoch
from finality_sim.recovery import log_failure, window_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b5"
F = 1 / 30
KS = (2160, 1080, 432, 216, 120)
ALPHAS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
EPS = (1e-6, 1e-9, 1e-12)
DELAYS = (1, 3, 5, 10, 15, 20)
WINDOWS = (900, 3600)
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", link_latency_mean=0.1, k=256, epochs=1, f=F,
            max_uncles=0, prune_arrival=False, blend_delay_dist="rounds")
BLENDS = {"testnet": dict(blend_hops=1, blend_delay_max=1.0),
          "specification": dict(blend_hops=3, blend_delay_max=3.0)}


def window_counts(blend: str, rep: int) -> list[dict]:
    cfg = SimConfig(**BASE, **BLENDS[blend], replicate=rep)
    tree, _ = build_epoch(cfg)
    slots = tree.slot[np.asarray(tree.canonical_chain(), dtype=np.int64)]
    cut = int(cfg.epoch_len * 0.9)
    rows = []
    for w in WINDOWS:
        n = cut // w
        c = np.bincount(slots[(slots >= 0) & (slots < n * w)] // w, minlength=n)
        rows.append(dict(blend=blend, replicate=rep, window=w, windows=n,
                         mean=float(c.mean()), var=float(c.var(ddof=1))))
    return rows


def engine(growth: dict[str, float]) -> pd.DataFrame:
    rows = Parallel(n_jobs=-1)(delayed(window_counts)(b, r) for b in BLENDS for r in range(8))
    d = pd.DataFrame([x for r in rows for x in r])
    d["dispersion"] = d["var"] / d["mean"]
    out = []
    for (b, w), g in d.groupby(["blend", "window"], sort=False):
        p = g["mean"].mean() / w
        out.append(dict(blend=b, window=w, growth_per_f=p / F,
                        dispersion=g.dispersion.mean(),
                        dispersion_sem=g.dispersion.std(ddof=1) / math.sqrt(len(g)),
                        binomial_dispersion=1 - growth[b] * F))
    return pd.DataFrame(out)


def models(growth: dict[str, float]) -> list[tuple[str, dict]]:
    return ([(f"random, {b}", dict(growth=g)) for b, g in growth.items()]
            + [(f"worst, {d} s", dict(delta=d)) for d in DELAYS])


def window(growth: dict[str, float]) -> pd.DataFrame:
    rows = []
    for name, m in models(growth):
        for a in ALPHAS:
            row = dict(model=name, alpha=round(a, 4))
            for k in KS:
                row[f"log10_fail_k{k}"] = log_failure(int(k / (4 * F)), a, F, **m) / math.log(10)
            for eps in EPS:
                w = window_needed(a, eps, F, **m)
                row[f"window_h_{eps:.0e}"] = np.nan if w is None else w / 3600
            rows.append(row)
    return pd.DataFrame(rows)


def largest_share(w: int, eps: float, m: dict) -> float:
    lo, hi = 0.0, 0.5
    for _ in range(40):
        a = (lo + hi) / 2
        if log_failure(w, a, F, **m) <= math.log(eps):
            lo = a
        else:
            hi = a
    return lo


def share(growth: dict[str, float]) -> pd.DataFrame:
    pts = [(name, m, eps) for name, m in models(growth) for eps in EPS]
    vals = Parallel(n_jobs=-1)(delayed(largest_share)(4 * int(k / F), eps, m)
                               for _, m, eps in pts for k in KS)
    rows = []
    for i, (name, _, eps) in enumerate(pts):
        rows.append(dict(model=name, eps=eps,
                         **{f"k={k}": round(vals[i * len(KS) + j], 4) for j, k in enumerate(KS)}))
    return pd.DataFrame(rows)


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    growth = {b: float(s[(s.blend_hops == v["blend_hops"])
                         & (s.blend_delay_max == v["blend_delay_max"])].growth_per_f.iloc[0])
              for b, v in BLENDS.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("engine", engine), ("window", window), ("share", share)):
        t = fn(growth)
        t.to_csv(OUT / f"recovery_{name}.csv", index=False)
        print(t.to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
