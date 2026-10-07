"""Phase B5: the density test during a partition (PLAN.md B5, rule 7).

    python scripts/b5_partition.py      # needs runs/a1; writes runs/b5/partition.csv, ties.csv

Every window and horizon of B5 gives the honest chain its full share, 1 - alpha. A split deeper
than k that is not an eclipse is a partition, and during a partition each honest side produces
with its own share only, while the coalition withholds a fork made with all of its stake.
partition.csv holds the chance that the fork is strictly denser than an honest side holding a
share s of all stake over a window (src/finality_sim/recovery.py, log_failure with honest = s), and
the largest s the fork beats in expectation. ties.csv holds the chance that two honest sides of an
even split, with no coalition, tie in density over the window and so, under a strict order, never
heal.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from scipy import special

from finality_sim.recovery import honest_logpmf, log_failure, occupancy

HERE = pathlib.Path(__file__).resolve().parent.parent
F = 1 / 30
ALPHAS = (0.25, 0.30, 1 / 3)
SIDES = (0.30, 1 / 3, 0.35, 0.40, 0.45, 0.50)
WINDOWS_H = (36, 54, 72)
KS = {2160: 72, 1620: 54, 1080: 36, 120: 4}


def models() -> dict[str, dict]:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    g = float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])
    return {"random, specification": dict(growth=g), "worst, 10 s": dict(delta=10)}


def beaten_side(alpha: float, growth: float | None = None, delta: int | None = None) -> float:
    """The largest honest share the fork beats in expectation: a side's canonical rate equals the
    coalition's win rate."""
    a = occupancy(F, alpha)
    lo, hi = 0.0, 1.0 - alpha
    for _ in range(60):
        s = (lo + hi) / 2
        ph = occupancy(F, s)
        rate = growth * ph if growth is not None else 1.0 / (delta + 1.0 / ph)
        lo, hi = (s, hi) if rate < a else (lo, s)
    return lo


def tie(w: int, share: float, growth: float) -> float:
    """Two honest sides of share ``share`` each, independent: P(equal counts)."""
    logp = honest_logpmf(w, occupancy(F, share), growth=growth)
    return float(math.exp(special.logsumexp(2 * logp)))


def main() -> None:
    ms = models()
    rows = []
    for name, kw in ms.items():
        for alpha in ALPHAS:
            for w_h in WINDOWS_H:
                row = dict(model=name, alpha=round(alpha, 4), window_h=w_h,
                           beaten_side=beaten_side(alpha, **kw))
                for s in SIDES:
                    row[f"side_{s:.4f}"] = math.exp(log_failure(w_h * 3600, alpha, F, honest=s, **kw))
                row["side_whole"] = math.exp(log_failure(w_h * 3600, alpha, F, **kw))
                rows.append(row)
    t = pd.DataFrame(rows)
    out = HERE / "runs" / "b5"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "partition.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.3g}"))
    g = ms["random, specification"]["growth"]
    ties = pd.DataFrame([dict(k=k, window_h=w_h, mean=g * occupancy(F, 0.5) * w_h * 3600,
                              p_tie=tie(w_h * 3600, 0.5, g)) for k, w_h in KS.items()])
    ties.to_csv(out / "ties.csv", index=False)
    print()
    print(ties.to_string(index=False))


if __name__ == "__main__":
    main()
