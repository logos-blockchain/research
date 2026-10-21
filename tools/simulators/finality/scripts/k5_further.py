"""Phase K, K.5: FURTHER.md's Blend settings (G3) and adversarial relays (G6) with k counted in
slots.

    python scripts/k5_further.py   # needs runs/g3, runs/g6; writes runs/k5/blend.csv, relays.csv
                                   # (about three minutes on 4 cores)

G3: for each of A1's Blend settings, against 30 % and a third at eps = 1e-9, the wait
slots.wait_needed gives at the setting's growth, beside G3's depth on the clock of the honest
chain; and the wait slots.worst_needed bounds at the setting's Delta, from B2's upper bound at
D = Delta/30 (b2_settlement.upper), beside G3's worst-case depth on its clock. The slowest setting,
34 s, has no worst-case depth in G3 and none here.

G6: for each relay arm, the wait slots.wait_needed gives at the arm's growth per honest win, which
G6's hours read on the same clock, 1 / ((1 - alpha) growth lambda), beside G6's closed-form depth;
and each arm's cost over honest relays with as many copies, in blocks and in the wait.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import upper
from finality_sim.slots import wait_needed, worst_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k5"
EPS = 1e-9
FLOOR = 1e-14


def blend_row(r: dict) -> dict:
    alpha, delta = float(r["alpha"]), int(r["delta_s"])
    out = dict(hops=int(r["hops"]), rounds=int(r["rounds"]), delta_s=delta, alpha=alpha,
               random_depth=r["random_depth"], random_h=r["random_h"],
               worst_depth=r["worst_depth"], worst_h=r["worst_h"])
    out["random_wait_h"] = wait_needed(alpha, EPS, float(r["growth"])) / 3600
    if np.isfinite(r["worst_depth"]):
        ub = upper(alpha, delta, 60_000, floor=FLOOR)
        out["worst_wait_h"] = worst_needed(alpha, EPS, delta, np.log(np.minimum(ub, 1.0))) / 3600
    else:
        out["worst_wait_h"] = float("nan")
    return out


def main() -> None:
    g3 = pd.read_csv(HERE / "runs" / "g3" / "blend_delay.csv")
    blend = Parallel(n_jobs=4)(delayed(blend_row)(r) for r in g3.to_dict("records"))
    g6 = pd.read_csv(HERE / "runs" / "g6" / "relays.csv")
    relays = []
    for r in g6.to_dict("records"):
        wait = wait_needed(float(r["alpha"]), EPS, float(r["growth"]))
        relays.append(dict(alpha=r["alpha"], hostile=r["hostile"], action=r["action"],
                           copies=int(r["copies"]), growth=r["growth"],
                           depth=r["closed_depth_1e9"], hours=r["hours_1e9"],
                           wait_h=wait / 3600))
    rel = pd.DataFrame(relays)
    base = rel[~rel.hostile].set_index(["alpha", "copies"])
    rel["depth_cost"] = [d / base.loc[(a, c), "depth"] - 1
                         for a, c, d in zip(rel.alpha, rel.copies, rel.depth)]
    rel["wait_cost"] = [w / base.loc[(a, c), "wait_h"] - 1
                        for a, c, w in zip(rel.alpha, rel.copies, rel.wait_h)]
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(blend).to_csv(OUT / "blend.csv", index=False)
    rel.to_csv(OUT / "relays.csv", index=False)
    print(pd.DataFrame(blend).to_string())
    print(rel.to_string())


if __name__ == "__main__":
    main()
