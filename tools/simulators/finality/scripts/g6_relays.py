"""Phase G6: Blend's delays under adversarial relays (PLAN.md, G6).

    python scripts/g6_relays.py      # writes runs/g6/relays.csv (about 5 minutes on 14 cores)

The random-delay model lets the coalition choose no delay; the worst case lets it choose every one.
Between them: the coalition's relays hold every honest block they carry for the longest mixing
delay the protocol allows (tsi_sim, blend_adversary_relays), while honest relays draw theirs as
before. B3's private race is played on the engine's timelines (finality_sim.race.withhold_timelines,
the coalition withholding), on the specification's Blend, with and without hostile relays: the
honest orphan share, the canonical growth per win, the depth at which the premined race's success
falls to 1e-3, and B5's closed form at 1e-9 at the measured growth.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b3_race import BASE, CONFIGS
from finality_sim.private_race import strict_depth
from finality_sim.race import race, withhold_timelines

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g6"
ALPHAS = (0.25, 0.30, 1 / 3)
REPLICATES = 64
K_MAX = 200
F = 1 / 30


def one(alpha: float, hostile: bool, rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep,
                    blend_adversary_relays=hostile)
    canon, adv, orphan = withhold_timelines(cfg)
    succ, scored = race(canon, adv, K_MAX, premine=True, win_at=1)
    return dict(alpha=round(alpha, 4), hostile=hostile, replicate=rep, orphan=orphan,
                canonical=int(canon.size), adversary_slots=int(adv.size), slots=int(cfg.epoch_len),
                succ=succ, scored=scored)


def main() -> None:
    jobs = [(a, h, r) for a in ALPHAS for h in (False, True) for r in range(REPLICATES)]
    rows = Parallel(n_jobs=-2, backend="loky")(delayed(one)(*j) for j in jobs)
    lam = -math.log(1 - F)
    out = []
    for (alpha, hostile), grp in pd.DataFrame(rows).groupby(["alpha", "hostile"], sort=False):
        succ = np.sum(np.stack(grp.succ.to_list()), axis=0)
        scored = int(grp.scored.sum())
        p = succ / scored
        hit = np.nonzero(p <= 1e-3)[0]
        orphan = float(grp.orphan.mean())
        rate = float(grp.canonical.sum() / grp.slots.sum())          # canonical blocks per slot
        g = rate / ((1 - alpha) * lam)                                 # growth per honest win
        q = alpha / (alpha + (1 - alpha) * g)
        out.append(dict(alpha=alpha, hostile=hostile, replicates=len(grp), orphan=orphan,
                        orphan_sem=float(grp.orphan.std(ddof=1) / math.sqrt(len(grp))),
                        canonical_per_slot=rate, growth=g, q=q,
                        race_depth_1e3=int(hit[0] + 1) if hit.size else -1, scored=scored,
                        closed_depth_1e9=strict_depth(q, math.log(1e-9)),
                        hours_1e9=strict_depth(q, math.log(1e-9)) / rate / 3600))
    t = pd.DataFrame(out)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "relays.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
