"""Phase N.1: what a committee drawn from counted units holds (PLAN.md Phase N).

    python scripts/n1_committee.py   # writes runs/n1/{committee,units,rounding}.csv; a few minutes

src/finality_sim/units.py. Every committee holds both tails at 1e-9 a round: two conflicting
certificates need the coalition's units twice and every honest unit once, and a round stalls when
the honest units online fall short of the quorum.

- committee.csv: per coalition share and honest uptime, D0's anonymous seats without a margin and
  sized for the inference's error up to 1.05 (src/finality_sim/committee.py), M.1's count drawn
  with replacement (signers.known_committee), and over 30,000 registered units, the active stake at
  30 % of the supply at today's minimum stake: the private draw's expected seats, the public draw
  without replacement, and whether every unit voting holds.
- units.csv: per unit size, the registered units, the public draw against 25 % and 30 % at full
  uptime and 95 %, and the least uptime at which every unit voting holds.
- rounding.csv: the honest stake lost below whole units, the coalition's share of the units it
  leaves, and the public draw against that share.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim import committee as cm
from finality_sim import signers as sg
from finality_sim import units as un

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "n1"
EPS = 1e-9
U = un.registered_units()
COALITIONS = (0.10, 0.25, 0.30, 1 / 3)
UPTIMES = (1.0, 0.95, 0.9)
UNIT_SIZES = (1e-6, 1e-5, 1e-4)        # shares of the supply: 0.0001 %, 0.001 % (today), 0.01 %
LOSSES = (0.0, 0.01, 0.05, 0.10)
JOBS = 12


def _pair(r):
    return (math.nan, math.nan) if r is None else (float(r[0]), float(r[1]))


def committee_row(alpha: float, uptime: float) -> dict:
    seats = _pair(cm.smallest_committee(alpha, EPS, awake=uptime))
    sized = _pair(cm.smallest_committee(alpha, EPS, awake=uptime, inflation=1.05))
    count = _pair(sg.known_committee(alpha, EPS, uptime))
    private = _pair(un.private_draw(alpha, EPS, U, uptime))
    public = _pair(un.public_draw(alpha, EPS, U, uptime))
    every = un.every_unit(alpha, EPS, U, uptime)
    return dict(alpha=alpha, uptime=uptime, units=U, seats=seats[0], seats_quorum=seats[1],
                sized=sized[0], sized_quorum=sized[1], count=count[0], count_quorum=count[1],
                private=private[0], private_quorum=private[1], public=public[0],
                public_quorum=public[1], every_holds=every is not None,
                every_quorum=every[1] if every else math.nan)


def units_row(size: float, alpha: float, uptime: float) -> dict:
    units = un.registered_units(unit=size)
    public = _pair(un.public_draw(alpha, EPS, units, uptime))
    return dict(unit=size, units=units, alpha=alpha, uptime=uptime, public=public[0],
                public_quorum=public[1], every_uptime=un.every_unit_uptime(alpha, EPS, units))


def rounding_row(loss: float, alpha: float, uptime: float) -> dict:
    adv = un.coalition_units(alpha, U)
    honest = math.floor((U - adv) * (1 - loss))
    units = adv + honest
    share = un.unit_share(alpha, loss)
    public = _pair(un.public_draw(share, EPS, units, uptime))
    return dict(loss=loss, alpha=alpha, uptime=uptime, units=units, unit_share=share,
                public=public[0], public_quorum=public[1],
                every_uptime=un.every_unit_uptime(share, EPS, units))


def main() -> None:
    par = Parallel(n_jobs=JOBS)
    committee = pd.DataFrame(par(delayed(committee_row)(a, u)
                                 for a in COALITIONS for u in UPTIMES))
    units = pd.DataFrame(par(delayed(units_row)(s, a, u) for s in UNIT_SIZES
                             for a in (0.25, 0.30) for u in (1.0, 0.95)))
    rounding = pd.DataFrame(par(delayed(rounding_row)(r, a, u) for r in LOSSES
                                for a in (0.25, 0.30) for u in (1.0, 0.95)))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in (("committee", committee), ("units", units), ("rounding", rounding)):
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(t.to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
