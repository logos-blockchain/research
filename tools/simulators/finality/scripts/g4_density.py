"""Phase G4: a settlement rule that reads the chain's density (PLAN.md, G4).

    python scripts/g4_density.py      # needs runs/a1; writes runs/g4/density.csv

A first look, under random delay. For the adversary's bound alpha and the canonical growth g of
testnet's and the specification's Blend (A1): the depth B5's rule waits, and the depth at which a
chain with everyone producing is accepted by a rule that also requires, for every withheld share
w up to alpha, that the private race's chance times the chance of seeing that many blocks under
attack w stays at or below 1e-9 (src/finality_sim/further.py, density_depth). Minutes are on the
full-rate clock, 30 s / g, which is the clock of a chain nobody attacks; B5's rule on the clock of
a chain the coalition withholds from, 30 s / ((1 - alpha) g), is given beside it.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from b2_settlement import F
from finality_sim.further import density_depth
from finality_sim.private_race import strict_depth

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g4"
ALPHAS = (0.10, 0.25, 0.30, 1 / 3)
EPS = 1e-9


def main() -> None:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    blends = {"testnet": float(s[(s.blend_hops == 1) & (s.blend_delay_max == 1)].growth_per_f.iloc[0]),
              "specification": float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])}
    rows = []
    for blend, g in blends.items():
        for a in ALPHAS:
            plain = int(strict_depth(a / (a + (1 - a) * g), math.log(EPS)))
            d, w = density_depth(a, g, EPS, F)
            rows.append(dict(blend=blend, growth=g, alpha=round(a, 4), plain_depth=plain,
                             plain_min_full=plain * 30 / g / 60, plain_min_withheld=plain * 30 / ((1 - a) * g) / 60,
                             density_depth=d, density_min_full=d * 30 / g / 60, worst_share=w))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "density.csv", index=False)
    with pd.option_context("display.width", 200):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
