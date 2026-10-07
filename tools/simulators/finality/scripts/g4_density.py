"""Phase G4: settlement on a chain nobody withholds from (PLAN.md, G4).

    python scripts/g4_density.py      # needs runs/a1; writes runs/g4/time_rule.csv

B4's elapsed-time rule and the depth rule, read on two chains: one the coalition withholds from
from the target's parent on, whose canonical rate is (1 - alpha) g lambda, and one nobody withholds
from, at the full rate g lambda. Blocks are taken at their mean spacing
(src/finality_sim/further.py, time_rule_depth). The rule is read with B4's rates and with the rates
after a total-stake adjustment, under which a coalition that withheld for a whole period wins at
alpha lambda / (1 - alpha) against a canonical chain at g lambda. A rule that reads the chain's
density directly (density_depth) is given beside them, with the exact conditional chance at its
acceptance. Minutes are on the clock of the chain read: 30 s / g at the full rate, 30 s / ((1 - alpha) g)
while withheld from.
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from b2_settlement import F
from finality_sim.further import density_chance, density_depth, time_rule_depth
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
        full, held = 30 / g / 60, None
        for a in ALPHAS:
            held = 30 / ((1 - a) * g) / 60
            plain = int(strict_depth(a / (a + (1 - a) * g), math.log(EPS)))
            row = dict(blend=blend, growth=g, alpha=round(a, 4), plain_depth=plain,
                       plain_min_full=plain * full, plain_min_held=plain * held)
            for adjusted in (False, True):
                tag = "adjusted" if adjusted else "b4"
                nf = time_rule_depth(a, g, EPS, F, full_rate=True, adjusted=adjusted)
                nh = time_rule_depth(a, g, EPS, F, full_rate=False, adjusted=adjusted)
                row |= {f"{tag}_full_n": nf, f"{tag}_full_min": nf * full, f"{tag}_held_n": nh,
                        f"{tag}_held_min": nh * held}
            d, w = density_depth(a, g, EPS, F)
            row |= dict(density_n=d + 1, density_min_full=(d + 1) * full, density_share=w,
                        density_log10_chance=density_chance(a, g, EPS, F) / math.log(10))
            rows.append(row)
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "time_rule.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
