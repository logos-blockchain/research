"""Phase B2: the lower bound computed past depth 120 where SETTLEMENT.md B2 reads it.

    python scripts/b2_lower.py      # writes runs/b2/lower.csv (about half an hour on 14 cores)

A quarter of the stake: depths 140 and 150 at 10 s, around the attack's depth at 1e-9, and depth
216 (k/10) at 10, 15 and 20 s. Alphabet, states and symbol cut are B2's
(scripts/b2_settlement.py).
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F, MIN_PROB, MIN_STATES, alphabet_for
from finality_sim.lcbounds import error_lb, slot_pdf

HERE = pathlib.Path(__file__).resolve().parent.parent
POINTS = ((0.25, 10, 140), (0.25, 10, 150), (0.25, 10, 216), (0.25, 15, 216), (0.25, 20, 216))


def point(adv: float, delay_s: int, k: int) -> dict:
    d = F * delay_s
    a = alphabet_for(adv, d)
    return dict(adv=adv, delay_s=delay_s, depth=k,
                lb=error_lb(k, slot_pdf(1 - adv, d, a), a, max(MIN_STATES, a + 1),
                            min_prob=MIN_PROB))


def main() -> None:
    t = pd.DataFrame(Parallel(n_jobs=-2)(delayed(point)(*p) for p in POINTS))
    t.to_csv(HERE / "runs" / "b2" / "lower.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
