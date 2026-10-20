"""Phase J, J.3.2: the convergence-opportunity bound's depth at 1e-9 (DAG.md J.3).

    python scripts/j3_bound.py      # writes runs/j3/bound.csv

For each share and delay, the depth in slots and hours at which the bound of
``finality_sim.cobound`` falls to 1e-9 and stays there, with two events per win, J.1's rule, and
with one, which no rule that every node applies alike achieves (DAG.md J.1). A walk that does not
drift down gives no depth, nor does one still above 1e-9 after 72 hours.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim import cobound

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "j3"
F = 1 / 30
EPS = 1e-9
HORIZON = 72 * 3600
ALPHAS = (0.25, 0.30, 1 / 3)
DELAYS = (1, 2, 5, 10, 20)


def point(alpha: float, delta: int, events: int) -> dict:
    drift = cobound.drift(F, alpha, delta, events)
    slots = None
    if drift < 0:
        slots = cobound.depth(cobound.error_curve(F, alpha, delta, events, HORIZON,
                                                  stop=EPS * 1e-3), EPS)
    return dict(alpha=alpha, delay_s=delta, events=events, drift=drift, depth_slots=slots,
                hours=None if slots is None else slots / 3600)


def main() -> None:
    cells = [(a, d, e) for e in (2, 1) for a in ALPHAS for d in DELAYS]
    rows = Parallel(n_jobs=4)(delayed(point)(*c) for c in cells)
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "bound.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
