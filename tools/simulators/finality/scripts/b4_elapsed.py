"""Phase B4: a confirmation rule that reads elapsed time, against the depth rule (PLAN.md B4).

    python scripts/b4_elapsed.py      # needs runs/a1; writes runs/b4/elapsed.csv

Both rules face B5's private race with the strict tie rule and a premined lead
(src/finality_sim/elapsed.py). The depth rule waits for the depth of B5's closed form; the
elapsed-time rule accepts at the first canonical block whose time since the parent leaves the
coalition a chance of at most eps. Both use B5's rates: the coalition wins at a = alpha lambda per
slot and the canonical chain grows at h = (1 - alpha) g lambda, with lambda = -ln(1 - f) and g A1's
growth on the specification's Blend, so q = a / (a + h) is B5's.

They are played on two kinds of timeline, 64 of each per share, one epoch at k = 256: the engine's
(scripts/b3_race.py's specification Blend, the coalition withholding), and independent slots with
an honest block at rate h and a coalition win at rate a (the model both rules assume). Each target
is scored by the race itself (finality_sim.race.race_depths), so the failure columns measure
the rule, not its model.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b3_race import BASE, CONFIGS
from b5_what_k_holds import log_strict
from finality_sim.elapsed import deadlines, settle
from finality_sim.race import race_depths, withhold_timelines

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "b4"
F = 1 / 30
ALPHAS = (0.10, 0.25, 0.30, 1 / 3)
EPS = (1e-3, 1e-6, 1e-9)
REPLICATES = 64
SLOTS = BASE["epochs"] * 10 * int(BASE["k"] / F)


def timelines(kind: str, alpha: float, rep: int, a: float, h: float, k_max: int):
    if kind == "engine":
        cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep)
        canon, adv, _ = withhold_timelines(cfg)
    else:
        rng = np.random.default_rng([rep, int(alpha * 1000)])
        canon = np.nonzero(rng.random(SLOTS) < h)[0].astype(np.int64)
        adv = np.nonzero(rng.random(SLOTS) < a)[0].astype(np.int64)
    return canon, race_depths(canon, adv, k_max, premine=True, win_at=1)


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    g = float(s[(s.family == "rounds") & (s.link_latency_mean == 0.1) & (s.blend_hops == 3)
                & (s.blend_delay_max == 3)].growth_per_f.iloc[0])
    rows = []
    for alpha in ALPHAS:
        lam = -math.log(1 - F)
        a, h = alpha * lam, (1 - alpha) * g * lam
        q = a / (a + h)
        rules = {}
        for eps in EPS:
            d = next(k for k in range(1, 10_000) if log_strict(q, k + 1) <= math.log(eps))
            rules[eps] = (d, deadlines(a, h, eps, 3 * d + 60))
        k_max = 2 * max(d for d, _ in rules.values())
        for kind in ("engine", "model"):
            runs = Parallel(n_jobs=-2)(delayed(timelines)(kind, alpha, r, a, h, k_max)
                                       for r in range(REPLICATES))
            for eps, (d, dl) in rules.items():
                k_t, t_t, t_d, deep = [], [], [], []
                for canon, deepest in runs:
                    kt, tt, td = settle(canon, dl, d)
                    ok = (kt >= 1) & (td >= 0) & (deepest >= 0)
                    k_t.append(kt[ok]), t_t.append(tt[ok]), t_d.append(td[ok]), deep.append(deepest[ok])
                k_t, t_t, t_d, deep = (np.concatenate(x) for x in (k_t, t_t, t_d, deep))
                if k_t.max() > k_max:
                    raise ValueError("the rule accepted past the race's depth")
                rows.append(dict(timelines=kind, alpha=alpha, eps=eps, targets=k_t.size, depth=d,
                                 depth_mean_min=t_d.mean() / 60, depth_p50_min=np.median(t_d) / 60,
                                 depth_p90_min=np.percentile(t_d, 90) / 60,
                                 depth_fail=float(np.mean(deep >= d)),
                                 elapsed_blocks=k_t.mean(), elapsed_mean_min=t_t.mean() / 60,
                                 elapsed_p50_min=np.median(t_t) / 60,
                                 elapsed_p90_min=np.percentile(t_t, 90) / 60,
                                 elapsed_fail=float(np.mean(deep >= k_t))))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "elapsed.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
