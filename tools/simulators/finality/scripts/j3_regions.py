"""Phase J, J.3: the regions each published technique certifies on the slot lottery (DAG.md J.3).

    python scripts/j3_regions.py      # writes runs/j3/regions.csv

For each production coefficient and delay of E5, the largest adversary share inside four regions:
the convergence-opportunity technique of Kiffer, Rajaraman and shelat (finality_sim.convergence),
GHOST with ties steered by the adversary and with ties fixed in advance (Gaži, Motaqy and Russell,
finality_sim.balance), and the longest-chain rule (E5's chain column). Beside them, the same
with retraction, J.1's rule letting a second copy of a win cancel the first, so that each win
moves a comparison twice: the opportunities' region with two events a win, and the balancing
attack's edges with two moves a win (``convergence.retraction_threshold``). Each is a region, not a
depth: it says where a settlement bound may exist, not how deep a block must be.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from e5_balance import DELAYS, FS, chain_region

from finality_sim import convergence
from finality_sim.balance import threshold

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "j3"


def main() -> None:
    rows = [dict(f=f, delay_s=d, convergence=convergence.edge(f, d),
                 ghost_adversarial_ties=threshold(f, d, "adversarial"),
                 ghost_fixed_ties=threshold(f, d, "deterministic"), chain=chain_region(f, d),
                 convergence_two_events=convergence.edge(f, d, events=2),
                 ghost_adversarial_ties_retraction=convergence.retraction_threshold(
                     f, d, "adversarial"),
                 ghost_fixed_ties_retraction=convergence.retraction_threshold(f, d, "deterministic"))
            for f in FS for d in DELAYS]
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "regions.csv", index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
