"""Phase G7: the total-stake inference as a lever (FURTHER.md, G7).

    python scripts/g7_inference.py      # needs runs/a1, runs/b2; writes runs/g7/*.csv (about 8 minutes on 4 cores)

A coalition that withholds every block it wins for a period lowers the inferred stake by its share
and raises every lottery threshold by 1/(1 - alpha) for the next epoch (finality_sim.inference).

inference.csv, per share: the raise; the worst case of Delta = 10 s read at the old rates,
Delta/(1 - alpha); B2's proven depth at 1e-9 there (scripts/b2_settlement.upper) and its hours on
the deflated worst-case clock, Delta + 1/f, since the honest stake alone then occupies slots at f;
B5's closed form at 1e-9 at A1's growth on the specification's Blend, with its hours on the clock of
the chain withheld from, 1/((1 - alpha) g f), and on the deflated honest chain's, 1/(g f); the
hours k = 2160 blocks take on each of the four clocks; and the most the coalition gains by
choosing the raise level after seeing its own wins, the Brownian value sqrt(2M/pi) and a Monte
Carlo of the Poisson path, as a share of its wins.

engine.csv, per share: B3's private race on the engine's timelines (B3's settings, the
specification's Blend, 64 runs a cell) with the coalition withholding at the true thresholds and at
the deflated ones (every node's estimate at 1 - alpha of the true stake), each with honest relays,
with the coalition's relays holding every honest block for the longest mixing delay, and with them
holding it to the sender's deadline (G6); and every node producing at f with no coalition, the
quantity the report's convention reads from A1, here per honest win on B3's uniform stakes. Each
in two setups: one Blend copy released at the slot, the engine's default, and the
specification's two copies released at the next round. Per cell: the honest orphan share, the
canonical growth per honest win with its standard error over the runs, the depth at which the
premined race's success falls to 1e-3, and B5's closed form at 1e-9 at the measured growth, with
its hours on the cell's canonical rate.

clamp.csv: the periods and days a coalition needs to lower the inferred stake by its share when
the inference lowers it by at most a cap a period, for caps of 5, 10 and 20 % and k = 2160.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F, first_depth, upper
from b3_race import BASE, CONFIGS
from finality_sim.baseline import run
from finality_sim.inference import (deflated_delay, extra_wins, periods_to_deflate, raise_factor,
                                    raised_rates, selection_excess)
from finality_sim.private_race import strict_depth
from finality_sim.race import race, withhold_timelines
from finality_sim.recovery import occupancy
from tsi_sim.config import SimConfig

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g7"
ALPHAS = (0.25, 0.30, 1 / 3)
DELTA = 10.0
EPS = 1e-9
K = 2160
REPLICATES = 64
K_MAX = 200
# (arm, deflated, the coalition's relays: None for honest ones, else their action, as in G6)
ARMS = (("withheld", False, None), ("withheld, holding relays", False, "hold"),
        ("withheld, holding to the deadline", False, "deadline"),
        ("deflated", True, None), ("deflated, holding relays", True, "hold"),
        ("deflated, holding to the deadline", True, "deadline"))
# (Blend copies, released at the next round): the engine's default, and the specification's
# R_D = 1 with its release a round after the slot (RATE.md A1, G6)
SETUPS = ((1, False), (2, True))


def arm(alpha: float, deflated: bool, action: str | None, copies: int, next_round: bool,
        rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep,
                    blend_adversary_relays=action is not None,
                    blend_adversary_action=action or "hold", blend_copies=copies,
                    blend_release_next_round=next_round)
    canon, adv, orphan = withhold_timelines(cfg, 1.0 - alpha if deflated else 1.0)
    succ, scored = race(canon, adv, K_MAX, premine=True, win_at=1)
    return dict(alpha=round(alpha, 4), deflated=deflated, action=action or "", copies=copies,
                next_round=next_round, replicate=rep, orphan=orphan, canonical=int(canon.size),
                slots=int(cfg.epoch_len), succ=succ, scored=scored)


def everyone(copies: int, next_round: bool, rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=0.0, replicate=rep,
                    blend_copies=copies, blend_release_next_round=next_round)
    m = run(cfg)
    return dict(copies=copies, next_round=next_round, replicate=rep, orphan=m.orphan_share,
                rate=m.growth_rate)


def engine() -> pd.DataFrame:
    lam = -math.log(1 - F)
    jobs = [(a, d, h, c, n, r) for c, n in SETUPS for a in ALPHAS for _, d, h in ARMS
            for r in range(REPLICATES)]
    rows = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(delayed(arm)(*j) for j in jobs))
    every = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(
        delayed(everyone)(c, n, r) for c, n in SETUPS for r in range(REPLICATES)))
    out = []
    for c, n in SETUPS:
        conv = every[(every.copies == c) & (every.next_round == n)]
        g_all = float(conv.rate.mean()) / lam                # growth per win, everyone producing
        for a in ALPHAS:
            for name, d, h in ARMS:
                grp = rows[(rows.alpha == round(a, 4)) & (rows.deflated == d)
                           & (rows.action == (h or "")) & (rows.copies == c) & (rows.next_round == n)]
                rate = float(grp.canonical.sum() / grp.slots.sum())     # canonical blocks per slot
                win = lam if d else (1 - a) * lam                        # honest wins per slot
                g = rate / win                                           # growth per honest win
                g_runs = grp.canonical / grp.slots / win
                q = a / (a + (1 - a) * g)
                p = np.sum(np.stack(grp.succ.to_list()), axis=0) / int(grp.scored.sum())
                hit = np.nonzero(p <= 1e-3)[0]
                depth = strict_depth(q, math.log(EPS))
                out.append(dict(alpha=round(a, 4), arm=name, copies=c, next_round=n,
                                orphan=float(grp.orphan.mean()),
                                orphan_sem=float(grp.orphan.std(ddof=1) / math.sqrt(len(grp))),
                                growth=g, growth_sem=float(g_runs.std(ddof=1) / math.sqrt(len(grp))),
                                q=q, race_depth_1e3=int(hit[0] + 1) if hit.size else -1,
                                closed_depth_1e9=depth, hours_1e9=depth / rate / 3600))
            q = a / (a + (1 - a) * g_all)
            depth = strict_depth(q, math.log(EPS))
            out.append(dict(alpha=round(a, 4), arm="everyone producing", copies=c, next_round=n,
                            orphan=float(conv.orphan.mean()),
                            orphan_sem=float(conv.orphan.std(ddof=1) / math.sqrt(len(conv))),
                            growth=g_all,
                            growth_sem=float(conv.rate.std(ddof=1) / math.sqrt(len(conv))) / lam,
                            q=q, race_depth_1e3=-1, closed_depth_1e9=depth,
                            hours_1e9=depth / ((1 - a) * g_all * lam) / 3600))
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a1 = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    a1 = a1[(a1.family == "rounds") & (a1.link_latency_mean == 0.1)]
    g = float(a1[(a1.blend_hops == 3) & (a1.blend_delay_max == 3)].growth_per_f.iloc[0])
    b2 = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    epoch = 10 * math.floor(K / F)
    period = 6 * math.floor(K / F)
    rows = []
    for a in ALPHAS:
        d_eq = deflated_delay(DELTA, a)
        depth_w = first_depth(upper(a, d_eq, 6000, floor=EPS / 10), EPS)
        h_r, a_r = raised_rates(F, a)
        clock_w0 = DELTA + 1.0 / occupancy(F, 1 - a)                  # the worst-case clock
        clock_w = DELTA + 1.0 / h_r                                   # the same, deflated
        clock_r0 = 1.0 / ((1 - a) * g * F)                            # the chain withheld from
        clock_r = 1.0 / (g * F)                                       # the honest chain, deflated
        depth_r = strict_depth(a / (a + (1 - a) * g), math.log(EPS))
        m = extra_wins(F, a, epoch)
        levels = int(round(period * occupancy(F, a)))                # one level per block it can withhold
        brown, mc = selection_excess(m, levels, 20_000, 7 + int(a * 1000))
        rows.append(dict(alpha=round(a, 4), raise_factor=raise_factor(a), delay_eq_s=d_eq,
                         worst_depth_base=int(b2.query("delay_s == 10 and eps == 1e-9 and abs(adv - @a) < 1e-3")
                                              .ub_depth.iloc[0]),
                         worst_depth=depth_w, worst_hours=depth_w * clock_w / 3600,
                         clock_worst_s=clock_w, growth_a1=g, random_depth=depth_r,
                         random_hours_base=depth_r * clock_r0 / 3600, random_hours=depth_r * clock_r / 3600,
                         k_hours_random_base=K * clock_r0 / 3600, k_hours_random=K * clock_r / 3600,
                         k_hours_worst_base=K * clock_w0 / 3600, k_hours_worst=K * clock_w / 3600,
                         extra_wins=m, levels=levels, excess_brownian=brown, excess_mc=mc,
                         excess_share=mc / (epoch * a_r)))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "inference.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    e = engine()
    e.to_csv(OUT / "engine.csv", index=False)
    print()
    with pd.option_context("display.width", 250):
        print(e.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    rows = []
    for cap in (0.05, 0.10, 0.20):
        row = dict(cap=cap)
        for a in ALPHAS:
            n = periods_to_deflate(a, cap)
            row[f"periods_{round(a, 4)}"] = n
            row[f"days_{round(a, 4)}"] = n * period / 86_400
        rows.append(row)
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "clamp.csv", index=False)
    print()
    print(c.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main()
