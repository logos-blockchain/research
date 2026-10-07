"""Phase H.3: the time-reading rule under a worst case of Delta (PLAN.md, H.3).

    python scripts/h3_time_rule.py      # needs runs/b2; writes runs/h3/*.csv (about 5 minutes)

counting.csv: the counting bound (finality_sim.further.counting_logp) at Delta = 10 s: its catch-up
ratio, and the depth at 1e-9 when the n-th block arrives n / rate slots after the parent, at the
full rate g lambda, the rate of a chain the coalition withholds from, (1 - alpha) g lambda, and the
worst-case honest rate h_w = 1 / (Delta + 1/p_h), with the hours on each clock.

precheck.csv: B3's delay-scheduling attack (finality_sim.grr_attack, Gaži, Ren and Russell §4.7 on
the slot lottery) against time-reading rules, at Delta = 10 s. Each rule accepts the k-th block of
the client's chain when it arrives within deadline[k] slots of the target's symbol:
- "depth": the depth rule at B2's lower-bound depth for 1e-3, as a reference for the attack's
  success at confirmation (B3);
- "b4 at worst rates": B4's elapsed-time rule (finality_sim.elapsed.deadlines) at eps = 1e-3, the
  coalition winning at its slot occupancy and the canonical chain growing at h_w, the premined
  lead folded in;
- "b4 at worst rates, adjusted": the same with the coalition's rate divided by 1 - alpha and the
  canonical rate h_w / (1 - alpha), the rates after a total-stake adjustment (G4);
- "counting": the counting bound's deadlines at eps = 1e-3.
Columns: the attack's success at acceptance and ever after, per accepted target; the share of
targets accepted within the attack's horizon; the mean depth at acceptance. A rule the attack
beats at its eps is dead.

played.csv: the counting rule at eps = 1e-3, Delta = 10 s, played on 32 independent-slot timelines
of 200,000 slots whose canonical chain runs at the full rate g lambda while the coalition's wins
come at its slot occupancy, scored by the premined private race (finality_sim.race.race_depths):
the share of targets accepted, the mean depth and minutes at acceptance, and the share of accepted
targets the race beats, which the bound keeps at or below eps.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from finality_sim.elapsed import deadlines, settle
from finality_sim.further import counting_deadlines, counting_depth, counting_ratio
from finality_sim.grr_attack import attack_rule, occupancy
from finality_sim.race import race_depths

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h3"
ALPHAS = (0.25, 0.30, 1 / 3)
DELTA = 10
EPS = 1e-3
RUNS = 8
SLOTS = 20_000_000
K_MAX = 400


def rules(alpha: float, lb_depth: int) -> dict[str, np.ndarray]:
    a, h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    h_w = 1.0 / (DELTA + 1.0 / h)
    depth = np.full(K_MAX + 1, -1.0)
    depth[lb_depth + 1:] = np.inf                          # accept once k exceeds the depth
    return {"depth": depth,
            "b4 at worst rates": deadlines(a, h_w, EPS, K_MAX),
            "b4 at worst rates, adjusted": deadlines(a / (1 - alpha), h_w / (1 - alpha), EPS, K_MAX),
            "counting": counting_deadlines(alpha, DELTA, EPS, K_MAX, F)}


def one(alpha: float, name: str, deadline: np.ndarray, seed: int) -> dict:
    at_conf, ever, targets, accepted, mean_depth = attack_rule(alpha, F, DELTA, SLOTS, deadline, seed)
    return dict(alpha=round(alpha, 4), rule=name, seed=seed, at_conf=at_conf, ever=ever,
                targets=targets, accepted=accepted, depth_sum=mean_depth * accepted)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    g = float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])
    lam = -math.log(1 - F)
    rows = []
    for a in (0.10, 0.25, 0.30, 1 / 3):
        h = occupancy(F, 1 - a)
        rates = {"full": g * lam, "withheld": (1 - a) * g * lam, "worst": 1.0 / (DELTA + 1.0 / h)}
        row = dict(alpha=round(a, 4), delta_s=DELTA, ratio=counting_ratio(a, DELTA, F))
        for name, rate in rates.items():
            d = counting_depth(a, DELTA, 1e-9, rate, F)
            row[f"depth_{name}"] = d
            row[f"hours_{name}"] = d / rate / 3600 if d > 0 else math.nan
        rows.append(row)
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "counting.csv", index=False)
    print(c.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    depths = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    lb = {round(a, 4): int(depths[(depths.adv.round(4) == round(a, 4)) & (depths.delay_s == DELTA)
                                  & (depths.eps == EPS)].lb_depth.iloc[0]) for a in ALPHAS}
    jobs = [(a, name, dl, s) for a in ALPHAS for name, dl in rules(a, lb[round(a, 4)]).items()
            for s in range(RUNS)]
    got = Parallel(n_jobs=-2)(delayed(one)(*j) for j in jobs)
    out = []
    for (alpha, name), grp in pd.DataFrame(got).groupby(["alpha", "rule"], sort=False):
        acc = int(grp.accepted.sum())
        out.append(dict(alpha=alpha, rule=name, lb_depth=lb[alpha], targets=int(grp.targets.sum()),
                        accepted_share=acc / grp.targets.sum(),
                        fail_at_acceptance=grp.at_conf.sum() / max(acc, 1),
                        fail_ever=grp.ever.sum() / max(acc, 1), mean_depth=grp.depth_sum.sum() / max(acc, 1)))
    t = pd.DataFrame(out)
    t.to_csv(OUT / "precheck.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    rows = []
    for a in ALPHAS:
        dl = counting_deadlines(a, DELTA, EPS, K_MAX, F)
        pa = occupancy(F, a)
        rng = np.random.default_rng(int(a * 1000))
        ks, ts, beaten = [], [], []
        for _ in range(32):
            canon = np.nonzero(rng.random(200_000) < g * lam)[0].astype(np.int64)
            adv = np.nonzero(rng.random(200_000) < pa)[0].astype(np.int64)
            k, tt, _ = settle(canon, dl, 1)
            deepest = race_depths(canon, adv, K_MAX, premine=True, win_at=1)
            ok = (k >= 1) & (deepest >= 0)
            ks.append(k[ok]), ts.append(tt[ok]), beaten.append(deepest[ok] >= k[ok])
        ks, ts, beaten = (np.concatenate(x) for x in (ks, ts, beaten))
        rows.append(dict(alpha=round(a, 4), accepted=int(ks.size), mean_depth=float(ks.mean()),
                         mean_minutes=float(ts.mean() / 60), race_beats=float(beaten.mean())))
    pl = pd.DataFrame(rows)
    pl.to_csv(OUT / "played.csv", index=False)
    print()
    print(pl.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
