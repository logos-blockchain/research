"""Phase G1: the smallest contributions with a delayed nonce (PLAN.md, G1).

    python scripts/g1_delayed_nonce.py      # needs runs/b7; writes runs/g1/*.csv

With the nonce of B7 passed through a sequential delay, the coalition decides blind wherever the
delay outlasts the time it has to decide. Before the cut-off it has about one block interval: a
withheld block can be published later only through a fork. At the cut-off it has until the lead of
its private chain is spent. lasts.csv holds the chance that the lead lasts at least a given time
(src/finality_sim/further.py, lead_lasts) for B6's delay models. depths.csv reads, from
runs/b7/minimum.csv, the depth with the choices at the cut-off alone (depth_two_cutoff), which is
what remains once every decision before the cut-off is blind, beside the unground depth and B7's
estimate with those decisions.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from b2_settlement import F
from b7_nonce import models
from finality_sim.further import lead_lasts

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "g1"
ALPHAS = (0.25, 0.30, 1 / 3)
MINUTES = (1, 2, 5, 10, 20, 30, 60)


def main() -> None:
    ms = {n: kw for n, (kw, _) in models().items() if n != "random, testnet"}
    rows = [dict(model=n, alpha=round(a, 4), minutes=t, p_lasts=lead_lasts(F, a, 60 * t, **kw))
            for n, kw in ms.items() for a in ALPHAS for t in MINUTES]
    OUT.mkdir(parents=True, exist_ok=True)
    lasts = pd.DataFrame(rows)
    lasts.to_csv(OUT / "lasts.csv", index=False)
    print(lasts.pivot_table(index=["model", "alpha"], columns="minutes", values="p_lasts")
          .to_string(float_format=lambda v: f"{v:.2g}"))
    m = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    m = m[m.model.isin(ms) & (m.alpha >= 0.25) & (m.k >= 1080)]
    d = m[["model", "alpha", "k", "sub_windows", "depth_1e-09", "depth_two_cutoff", "depth_two_lo",
           "depth_two_hi"]]
    d.to_csv(OUT / "depths.csv", index=False)
    print()
    print(d.to_string(index=False))


if __name__ == "__main__":
    main()
