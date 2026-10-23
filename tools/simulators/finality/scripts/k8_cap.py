"""Phase K.8: a cap on the inference's correction, and the floor (SLOTS.md K.8).

    python scripts/k8_cap.py      # needs runs/a1; writes runs/k8/ (under a minute)

At K = ⌊k/f⌋ and 3⌊k/f⌋ for k = 2160, the floor K.3 takes, the worst case's at 10 s against a third
(floor.floor_for), and caps of 20, 10, 5 and 2 % an epoch beside none (finality_sim.cap):

- params.csv: the floor φ, the largest share it holds back at its fastest, σ* (floor.provisional_share),
  and the least share whose chain reaches it with chance 1 − ε, r*, under random delay at A1's growth
  on the specification's Blend and under the worst case at 10 s (cap.resume_share).
- protection.csv: for a side of share σ cut off from the rest, its corrections earliest: the days it
  stays below the density floor, and under the depth form the days to φ + 1 blocks and a first
  block K slots old, on average and at the earliest with chance ε.
- stall.csv: after the active stake falls to r with nobody withholding, its corrections latest: the
  days finality stalls under the density form, the days until a block made at the fall is fixed under
  the depth form (on average), and the days until the chain fills its slots within 5 % of f.
- ratio.csv: the protection against a side of 0.3 over the stall after a fall to 50 %, per cap.
- deflation.csv: the periods of withholding a coalition needs to lower the inferred stake by its share
  under each cap (inference.periods_to_deflate, FURTHER.md G7), in days withheld and in epochs.
- spec.csv: where the specification's inference, in its own integer arithmetic, rests with every
  unit of stake producing (cap.spec_rate): its target f_p = truncate(f·1000) over 1000.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from k3_splits import growth
from finality_sim.cap import (density_protection, density_stall, depth_finality, depth_protection,
                              resume_share, slow, spec_rate)
from finality_sim.floor import floor_for, provisional_share
from finality_sim.inference import periods_to_deflate

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k8"
F = 1 / 30
EPS = 1e-9
DELTA = 10
KF = math.floor(2160 / F)
EPOCH = 10 * KF
PERIOD = 6 * KF
WINDOWS = {"⌊k/f⌋": KF, "3⌊k/f⌋": 3 * KF}
CAPS = (None, 0.20, 0.10, 0.05, 0.02)
SIGMAS = (0.10, 0.20, 0.25, 0.30, 1 / 3, 0.40, 0.45)
FALLS = (0.80, 0.70, 0.60, 0.50, 0.40)
DAY = 86_400


def name(cap: float | None) -> str:
    return "none" if cap is None else f"{cap:.0%}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g = growth()
    models = {"random, specification": dict(growth=g), f"worst, {DELTA} s": dict(delta=DELTA)}
    prow, crow, srow, rrow = [], [], [], []
    for wname, w in WINDOWS.items():
        phi = floor_for(w, 1 / 3, EPS, F, delta=DELTA)
        s_star = provisional_share(w, phi, EPS)
        r_star = {m: resume_share(w, phi, EPS, F, **kw) for m, kw in models.items()}
        prow.append(dict(window=wname, slots=w, phi=phi, sigma_star=s_star,
                         **{f"r_star, {m}": v for m, v in r_star.items()}))
        for cap in CAPS:
            for s in SIGMAS:
                crow.append(dict(window=wname, cap=name(cap), sigma=s,
                                 density_days=density_protection(s, s_star, cap, EPOCH, w) / DAY,
                                 depth_mean_days=depth_protection(s, phi, cap, EPOCH, w) / DAY,
                                 depth_early_days=depth_protection(s, phi, cap, EPOCH, w, EPS) / DAY))
            for m, kw in models.items():
                for r in FALLS:
                    srow.append(dict(window=wname, cap=name(cap), r=r, model=m,
                                     density_stall_days=density_stall(r, r_star[m], cap, EPOCH, PERIOD, w) / DAY,
                                     depth_finality_days=depth_finality(r, phi, cap, EPOCH, PERIOD, w, F, **kw) / DAY,
                                     slow_days=slow(r, cap, EPOCH, PERIOD) / DAY))
                prot = density_protection(0.30, s_star, cap, EPOCH, w)
                stall = density_stall(0.50, r_star[m], cap, EPOCH, PERIOD, w)
                rrow.append(dict(window=wname, cap=name(cap), model=m, protection_days=prot / DAY,
                                 stall_days=stall / DAY, ratio=prot / stall))
    drow = []
    for cap in CAPS[1:]:
        for a in (0.25, 0.30, 1 / 3):
            n = periods_to_deflate(a, cap)
            drow.append(dict(cap=name(cap), alpha=a, periods=n, withheld_days=n * PERIOD / DAY,
                             epochs_days=n * EPOCH / DAY))
    sp = []
    for interval in (30, 20):
        f = 1 / interval
        rate = spec_rate(f, 6 * math.floor(2160 / f))
        sp.append(dict(f=f, interval_s=interval, f_p=int(f * 1000), rests_at=rate,
                       estimate_over_stake=math.log(1 - f) / math.log(1 - rate),
                       block_interval_s=1 / rate))
    for fname, rows in (("params", prow), ("protection", crow), ("stall", srow), ("ratio", rrow),
                        ("deflation", drow), ("spec", sp)):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"{fname}.csv", index=False)
        with pd.option_context("display.max_rows", 400, "display.width", 200):
            print(df.round(3).to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
