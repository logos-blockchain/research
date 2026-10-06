"""Phase B2, the reference for the gate of ``ub_curve``: the port's upper bound past depth 120.

    python scripts/b2_deep.py      # writes tests/data/lcbounds_deep.csv (an hour on 14 cores)

``error_ub`` follows the original code, in time quadratic in the depth; ``ub_curve`` computes
every depth at once (``src/finality_sim/lcbounds.py``). This computes ``error_ub`` at depths 160
to 640 in three cells of B2, a quarter of the stake at 10 s and a third at 10 s and 15 s, with
B2's alphabet, states and symbol cut (``scripts/b2_settlement.py``).
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F, MIN_PROB, MIN_STATES, alphabet_for
from finality_sim.lcbounds import error_ub, slot_pdf

HERE = pathlib.Path(__file__).resolve().parent.parent
CELLS = ((0.25, 10), (1 / 3, 10), (1 / 3, 15))
DEPTHS = (160, 240, 320, 480, 640)


def point(adv: float, delay_s: int, k: int) -> dict:
    d = F * delay_s
    a = alphabet_for(adv, d)
    s = max(MIN_STATES, a + 1)
    return dict(honest=1 - adv, D=d, alphabet=a, states=s, min_prob=MIN_PROB, K=k,
                ub=error_ub(k, slot_pdf(1 - adv, d, a), a, s, MIN_PROB))


def main() -> None:
    rows = Parallel(n_jobs=-2)(delayed(point)(a, dl, k) for a, dl in CELLS for k in DEPTHS)
    t = pd.DataFrame(rows)
    t.to_csv(HERE / "tests" / "data" / "lcbounds_deep.csv", index=False, float_format="%.17g")
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
