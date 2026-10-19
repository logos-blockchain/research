"""Does the spec 1.2.5 selection order move the parent-anchored results? (PLAN.md Phase 0)

Reads a run of ``configs/spec-order-paired.yaml``: the parent-anchored window at W = 12, with
entries filled by the uncle's own slot (``uncle_order="uncle"``, the order of every earlier
parent-arm run) or by the parent's slot (``"parent"``, the spec). Both arms share their random
streams, so replicate *i* of each is a matched pair. Prints, per (delay, U), the mean paired
difference ``parent − uncle`` in equilibrium D̂/D with its SEM and |t|, and the number of
pairs that are bit-identical. U = 0 must be bit-identical in every pair: with no uncles the
order is never consulted.

Run:  python scripts/spec_order_analysis.py runs/<dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from tsi_sim.plotting.figures_pernode import equilibrium, sem

KEYS = ["blend_delay_max", "max_uncles", "replicate"]


def paired(df: pd.DataFrame) -> pd.DataFrame:
    eq = equilibrium(df)
    u = eq[eq.uncle_order == "uncle"][[*KEYS, "mean_ratio", "p_ref"]]
    p = eq[eq.uncle_order == "parent"][[*KEYS, "mean_ratio", "p_ref"]]
    m = u.merge(p, on=KEYS, suffixes=("_u", "_p"), validate="one_to_one")
    m["d"] = m.mean_ratio_p - m.mean_ratio_u
    rows = []
    for (delay, cap), s in m.groupby(["blend_delay_max", "max_uncles"]):
        se = sem(s.d.to_numpy())
        rows.append({"delay": delay, "U": cap, "uncle_order": s.mean_ratio_u.mean(),
                     "parent_order": s.mean_ratio_p.mean(), "gap": s.d.mean(), "se": se,
                     "t": abs(s.d.mean()) / se if se > 0 else float("nan"),
                     "n_pair": len(s), "n_identical": int((s.d == 0.0).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    run = Path(sys.argv[1])
    df = pd.read_parquet(run / "results.parquet")
    assert df.paired_streams.all(), "both arms must share their random streams"
    out = paired(df)
    pd.set_option("display.width", 120)
    print(out.to_string(index=False, float_format=lambda x: f"{x:.5f}"))


if __name__ == "__main__":
    main()
