"""Phase D0: the emission cost of anonymous-seat votes, as curves (PLAN.md D0, Q7).

    python scripts/d0_emission_map.py        # writes runs/d0/emission_map.csv

For every attacker share, failure target and awake share, the smallest committee that holds
both tails per round, and the cover-rate multiple it costs at each round length. Q7 leaves the
budget line to the owner; this map is what it will be drawn on.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim.committee import emission_multiplier, smallest_committee

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "d0"
ALPHAS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
EPSILONS = (1e-6, 1e-9, 2.0 ** -40)
AWAKE = (1.0, 0.9, 0.8)
ROUNDS_S = (30, 90, 300, 600, 1800, 3600)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for awake in AWAKE:
        for alpha in ALPHAS:
            for eps in EPSILONS:
                res = smallest_committee(alpha, eps, awake)
                row = dict(awake=awake, alpha=alpha, eps=eps,
                           seats=res[0] if res else None, quorum=res[1] if res else None)
                for r in ROUNDS_S:
                    row[f"x_R{r}"] = emission_multiplier(res[0], r, F) if res else None
                rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "emission_map.csv", index=False)
    with pd.option_context("display.width", 200):
        print(df.to_string(index=False, float_format=lambda v: f"{v:,.4g}"))


if __name__ == "__main__":
    main()
