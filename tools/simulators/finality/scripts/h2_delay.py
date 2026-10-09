"""Phase H.2: the delay function's time and the coalition's speed ratio (PLAN.md, H.2).

    python scripts/h2_delay.py      # needs runs/a1, runs/b2, runs/b7; writes runs/h2/*.csv

A candidate nonce of the last sub-window can be formed from the sub-window's start, so the delay on
the coalition's hardware is T_a = W + margin, with W the sub-window and the margin the time the
coalition's lead must outlast after the cut-off (DESIGNS.md, H.2).

factor.csv: at margins of 1, 2, 3, 5, 10 and 20 minutes, at k = 2160 for B6's two delay models at
30 % and a third: the choices at the cut-off that remain (G1's finality_sim.further.delayed_factor,
20,000 windows a point) and the depth at 1e-9 with two nonces read as B7 reads its factors.
span.csv: per k, the sub-windows m of B7, the sub-window W, T_a at margins of 10 and 20 minutes, the
honest computation R * T_a for speed ratios R of 3, 5, 10 and 15, the 4 floor(k/f) slots between the
cut-off and the first slot that uses the nonce, and the largest R that fits them.
gmin.csv: per model, share and k, the choices at the cut-off E[G_min]: B7's sampled mean; the mean
of the exact expectation given the slots (finality_sim.fork_bound.conditional_mean, 10,000 windows);
the bound from B6's walk alone (fork_bound.gmin_bound, at the split n_lo that makes it smallest);
E[D] and E[A] of the deepest feasible fork; and the depth at 1e-9 with two nonces at the bound.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b7_nonce import depth_reader, models
from finality_sim.fork_bound import conditional_mean, gmin_bound
from finality_sim.further import delayed_factor
from finality_sim.nonce import _rates

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h2"
ALPHAS = (0.30, 1 / 3)
MINUTES = (1, 2, 3, 5, 10, 20)
RATIOS = (3, 5, 10, 15)
KS = (2160, 1620, 1080)
MARGINS = (10, 20)
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
        r["depth_1e-09"] = at(math.log(EPS))
        r["depth_two"] = at(math.log(EPS / r["factor"] ** 2))
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.DataFrame(rows)
    f.to_csv(OUT / "factor.csv", index=False)
    with pd.option_context("display.width", 200):
        print(f.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    rows = []
    for k in KS:
        m_k = int(b7[b7.k == k].sub_windows.iloc[0])
        w = math.floor(6 * math.floor(k / F) / m_k)
        phase = 4 * math.floor(k / F)
        for margin in MARGINS:
            t_a = w + 60 * margin
            row = dict(k=k, sub_windows=m_k, sub_window_slots=w, margin_min=margin, t_a_slots=t_a,
                       phase_slots=phase, largest_ratio=phase / t_a)
            for ratio in RATIOS:
                row[f"honest_hours_r{ratio}"] = ratio * t_a / 3600
            rows.append(row)
    sp = pd.DataFrame(rows)
    sp.to_csv(OUT / "span.csv", index=False)
    print()
    print(sp.to_string(index=False, float_format=lambda v: f"{v:.3g}"))

    def cell(n, a, k):
        kw = ms[n]
        m_k = int(b7[b7.k == k].sub_windows.iloc[0])
        window = 6 * math.floor(k / F)
        sub = window // m_k
        _, _, _, rate = _rates(F, a, kw.get("growth"), kw.get("delta"))
        best = min((gmin_bound(F, a, sub, int(frac * sub * rate), **kw)
                    for frac in (0.6, 0.65, 0.7, 0.75, 0.8, 0.85)), key=lambda b: b["bound"])
        cond, _ = conditional_mean(F, a, window, 10_000, 211 + k + int(a * 1000), sub_windows=m_k,
                                   **kw)
        x = b7[(b7.model == n) & (b7.alpha == round(a, 4)) & (b7.k == k)].iloc[0]
        at = depth_reader(kw, a, log_ub)
        return dict(model=n, alpha=round(a, 4), k=k, sub_windows=m_k, sampled=float(x.mean_g),
                    conditional=float(cond.mean()), conditional_sem=float(cond.std() / math.sqrt(cond.size)),
                    bound=best["bound"], main=best["main"], tails=best["tail_d"] + best["tail_n"] + best["cross"],
                    e_d=best["e_d"], e_a=best["e_a"], depth_two=at(math.log(EPS / best["bound"] ** 2)),
                    depth_two_sampled=at(math.log(EPS / float(x.mean_g) ** 2)))
    cells = Parallel(n_jobs=-2)(delayed(cell)(n, a, k) for n in ms for a in ALPHAS for k in KS)
    gm = pd.DataFrame(cells)
    gm.to_csv(OUT / "gmin.csv", index=False)
    print()
    with pd.option_context("display.width", 220):
        print(gm.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
