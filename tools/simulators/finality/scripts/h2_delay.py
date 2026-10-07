"""Phase H.2: the delay function's time and the coalition's speed ratio (PLAN.md, H.2).

    python scripts/h2_delay.py      # needs runs/a1, runs/b2, runs/b7; writes runs/h2/*.csv

factor.csv: at delays T_a of 1, 2, 3, 5, 10 and 20 minutes on the coalition's hardware, at k = 2160
for B6's two delay models at 30 % and a third: the choices at the cut-off that remain (G1's
finality_sim.further.delayed_factor, 20,000 windows a point); the residual of the decisions before
the cut-off, B7's hindsight factor per nonce beyond the cut-off's scaled by the chance that a block
placed after the T_a's worth of canonical blocks still becomes canonical, r^d with r = p_a / p_c;
their product; and the depth at 1e-9 read as B7 reads its factors.
honest.csv: the honest computation R * T_a for speed ratios R of 2, 5, 10, 30 and 100, and the
share it takes of the 4 floor(k/f) slots between the cut-off and the first slot that uses the
nonce, at k = 2160 and 1080.
window.csv: the decision window before the cut-off. A block of the coalition's own published d
canonical honest blocks after its slot competes from d behind and becomes canonical with chance
r^d, r = p_a / p_c; the table gives r^d and the minutes d blocks take at the canonical rate.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b7_nonce import depth_reader, models
from finality_sim.further import delayed_factor
from finality_sim.nonce import _rates

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h2"
ALPHAS = (0.30, 1 / 3)
MINUTES = (1, 2, 3, 5, 10, 20)
RATIOS = (2, 5, 10, 30, 100)
KS = (2160, 1080)
SAMPLES = 20_000
EPS = 1e-9


def factor(name: str, kw: dict, alpha: float, m: int, minutes: float, seed: int) -> dict:
    window = 6 * math.floor(2160 / F)
    return dict(model=name, alpha=round(alpha, 4), minutes=minutes,
                factor=delayed_factor(F, alpha, window, m, minutes, SAMPLES, seed, **kw))


def main() -> None:
    ms = {n: kw for n, (kw, _) in models().items() if n != "random, testnet"}
    b7 = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    m = int(b7[b7.k == 2160].sub_windows.iloc[0])
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}
    pts = [(n, a, t) for n in ms for a in ALPHAS for t in MINUTES]
    rows = Parallel(n_jobs=-2)(delayed(factor)(n, ms[n], a, m, t, 104729 + 31 * int(a * 1000) + 7 * t)
                               for n, a, t in pts)
    for (n, a, t), r in zip(pts, rows):
        at = depth_reader(ms[n], a, log_ub)
        pa, _, _, rate = _rates(F, a, ms[n].get("growth"), ms[n].get("delta"))
        x = b7[(b7.model == n) & (b7.alpha == round(a, 4)) & (b7.k == 2160)].iloc[0]
        # a decision before the cut-off keeps its value only while the block can still be placed:
        # after d canonical honest blocks, with chance r^d; B7's hindsight factor scaled by that
        residual = 1.0 + (x.factor_hi / x.mean_g - 1.0) * (pa / rate) ** (60 * t * rate)
        r["residual"] = residual
        r["combined"] = r["factor"] * residual
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_two"] = at(math.log(EPS / r["combined"] ** 2))
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.DataFrame(rows)
    f.to_csv(OUT / "factor.csv", index=False)
    with pd.option_context("display.width", 200):
        print(f.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    rows = []
    for t in MINUTES:
        for ratio in RATIOS:
            row = dict(minutes=t, ratio=ratio, honest_minutes=t * ratio)
            for k in KS:
                row[f"phase_share_k{k}"] = t * ratio * 60 / (4 * math.floor(k / F))
            rows.append(row)
    h = pd.DataFrame(rows)
    h.to_csv(OUT / "honest.csv", index=False)
    print()
    print(h.to_string(index=False, float_format=lambda v: f"{v:.3g}"))

    rows = []
    for n, kw in ms.items():
        for a in ALPHAS:
            pa, _, _, rate = _rates(F, a, kw.get("growth"), kw.get("delta"))
            r = pa / rate
            for d in (1, 2, 3, 5, 8, 11):
                rows.append(dict(model=n, alpha=round(a, 4), blocks_behind=d, chance=r ** d,
                                 minutes=d / rate / 60))
    w = pd.DataFrame(rows)
    w.to_csv(OUT / "window.csv", index=False)
    print()
    print(w.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
