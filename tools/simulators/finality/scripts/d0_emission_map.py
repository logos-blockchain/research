"""Phase D0: the emission cost of anonymous-seat votes, as curves (PLAN.md D0, Q7).

    python scripts/d0_emission_map.py        # writes runs/d0/{emission_map,blend_load}.csv

For every attacker share, failure target, share of honest votes that count (``awake``) and seat
inflation ``D/D̂``, the smallest committee that holds both tails per round, and the cover-rate
multiple it costs at each round length. Q7 leaves the budget line to the owner; this map is what it
will be drawn on. The inflation 1.05 is about six standard deviations of the inferred stake's
per-epoch noise (±0.9 %, reports/tsi §2.2). blend_load.csv holds what the votes cost Blend's own
budget: messages per core connection per round, and verifications per node.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim.committee import blend_load, emission_multiplier, smallest_committee

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "d0"
ALPHAS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
EPSILONS = (1e-6, 1e-9, 2.0 ** -40)
AWAKE = (1.0, 0.9, 0.8)
INFLATION = (1.0, 1.05)
ROUNDS_S = (30, 90, 300, 600, 1800, 3600)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for awake in AWAKE:
        for inflation in INFLATION:
            for alpha in ALPHAS:
                for eps in EPSILONS:
                    res = smallest_committee(alpha, eps, awake, inflation)
                    rows.append(dict(awake=awake, inflation=inflation, alpha=alpha, eps=eps,
                                     seats=res[0] if res else None,
                                     quorum=res[1] if res else None))
                    row = rows[-1]
                    for r in ROUNDS_S:
                        row[f"x_R{r}"] = emission_multiplier(res[0], r, F) if res else None
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "emission_map.csv", index=False)
    with pd.option_context("display.width", 200):
        print(df.to_string(index=False, float_format=lambda v: f"{v:,.4g}"))

    # what the votes of the committee that holds 1e-9 cost Blend's own budget (D3)
    load = []
    base = df[(df.awake == 1.0) & (df.inflation == 1.0) & (df.eps == 1e-9)]
    for _, r in base.iterrows():
        for round_s in (600, 3600):
            votes = r.seats / round_s
            f1_on, ver_on = blend_load(votes)
            f1_in, ver_in = blend_load(votes, emission_multiplier(r.seats, round_s, F))
            load.append(dict(alpha=r.alpha, round_s=round_s, seats=r.seats, votes=votes,
                             f1_on_top=f1_on, verify_on_top=ver_on, f1_in_cover=f1_in,
                             verify_in_cover=ver_in))
    pd.DataFrame(load).to_csv(OUT / "blend_load.csv", index=False)
    print(pd.DataFrame(load).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
