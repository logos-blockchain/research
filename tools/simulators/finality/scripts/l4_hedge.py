"""Phase L.4: the lag at which the chain's own settlement keeps the gadget safe (PLAN.md Phase L).

    python scripts/l4_hedge.py      # needs runs/a1 and runs/k7; writes runs/l4/hedge.csv (minutes)

A coalition holding between a third and two thirds of the declared weight finalizes a checkpoint
that conflicts with one honest nodes finalize only by splitting the honest votes, so that honest
nodes hold two chains that disagree on the block the lag reaches. That is a settlement failure at
the target's age, which the chain's own bounds price against the coalition's share of the stake:
K.1's wait under random delay on the specification's Blend, and K.7's bound under the worst case
at Δ = 10 s, both at ε = 1e-9 without grinding (SLOTS.md K.1, K.7).

The shares read: those at which the minimum-stake analysis' 1,000 honest declarations lose a
third and two thirds of the declared weight to a coalition that locks its stake at the minimum,
1/60 and 1/15 of the active stake (src/finality_sim/netcert.py), and B2's shares from 10 % to a
third. K.7's own waits at a third and 30 % with the nonce of §3.1, after a deflated inference,
are read from runs/k7/waits.csv.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed

from k1_settle import growths
from k7_wait import need
from finality_sim import netcert as nc
from finality_sim.slots import wait_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "l4"
F = 1 / 30
EPS = 1e-9
DELTA_S = 10
LOCKED = nc.SMALL_NETWORK * nc.MIN_STAKE_SHARE / nc.STAKED_SHARE      # 1/30 of the active stake


def shares() -> list[tuple[str, float]]:
    third = nc.largest_alpha_held(LOCKED)                                 # 1/60
    two_thirds = 2 * LOCKED                                               # 2,000 declarations: 1/15
    return [("a third of today's declarations", third),
            ("two thirds of today's declarations", two_thirds),
            ("10 %", 0.10), ("25 %", 0.25), ("30 %", 0.30), ("a third", 1 / 3)]


def row(name: str, alpha: float, g: float) -> dict:
    rand = wait_needed(alpha, EPS, g, F)
    worst = need(alpha, DELTA_S, EPS)
    return dict(share=name, alpha=alpha, random_slots=rand, random_h=rand / 3600,
                worst_slots=worst, worst_h=worst / 3600 if worst > 0 else float("nan"))


def main() -> None:
    g = growths()["specification"]
    rows = Parallel(n_jobs=6)(delayed(row)(n, a, g) for n, a in shares())
    df = pd.DataFrame(rows)
    w = pd.read_csv(HERE / "runs" / "k7" / "waits.csv")
    w = w[(w.model == "worst, 10 s") & w.case.str.startswith("deflated, nonce §3.1")]
    df["nonce_deflated_h"] = [next((float(h) for x, h in zip(w.alpha, w.wait_h)
                                    if abs(x - a) < 1e-9), float("nan")) for a in df.alpha]
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "hedge.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
