"""Phase D5: what votes leak about a holder's stake (PLAN.md D5).

    python scripts/d5_privacy.py      # needs runs/d0; writes runs/d5/{times,epoch}.csv

The committee is D0's against a quarter of the stake at 1e-9 (runs/d0/emission_map.csv), voting
in rounds of 1 h, 10 min and 90 s. Votes go through Blend, captured as the Blend report captures
an emission (f_adv = 0.2, 3 hops, q = 0.008, its §3.6-§3.7 setting), or are gossiped directly
(q = 1).

times.csv: the Blend report's mean days until a holder of each share is identified (N = 1) and
its stake known to ±10 % (N = 100), counting its blocks and its votes (src/finality_sim/privacy.py).

epoch.csv: the specification analysis's confidence that the stake is known to ±10 % within one
epoch, 10 floor(k/f) slots at f = 1/30, the largest share whose confidence stays at 0.5 or below,
and the nodes a 1.26 % holder must split into to stay there. The analysis's own example
(f = 0.05, T = 432,000 slots, q = 0.657) sits beside it.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim.privacy import confidence, spec_confidence, split, stake_days

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "d5"
F, K = 1 / 30, 2160
EPOCH = 10 * int(K / F)
Q_BLEND = 0.2 ** 3
SHARES = (0.05, 0.01, 0.001, 0.0001)
GAMMA, THETA, HOLDER = 0.1, 0.5, 0.0126


def largest_hidden(conf, lo: float = 1e-9, hi: float = 0.5) -> float:
    """The largest share whose confidence stays at THETA or below (it rises with the share)."""
    for _ in range(200):
        mid = (lo * hi) ** 0.5
        lo, hi = (mid, hi) if conf(mid) <= THETA else (lo, mid)
    return lo


def main() -> None:
    d0 = pd.read_csv(HERE / "runs" / "d0" / "emission_map.csv")
    seats = float(d0[(d0.awake == 1.0) & (d0.eps == 1e-9) & (abs(d0.alpha - 0.25) < 1e-9)].seats.iloc[0])
    settings = [("blocks only, through Blend", None, 0.0)]
    settings += [(f"with votes through Blend, {label} rounds", r, Q_BLEND)
                 for label, r in (("1 h", 3600), ("10 min", 600), ("90 s", 90))]
    settings += [("with votes gossiped directly, 10 min rounds", 600, 1.0)]

    rows = []
    for name, r, qv in settings:
        kw = dict(seats=seats if r else 0.0, round_s=r or 1.0, q_votes=qv)
        for s in SHARES:
            rows.append(dict(setting=name, share=s, identify_days=stake_days(s, 1, Q_BLEND, F, **kw),
                             size_days=stake_days(s, 100, Q_BLEND, F, **kw)))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "times.csv", index=False)
    print(t.to_string(index=False), end="\n\n")

    rows = []
    for name, r, qv in settings:
        def conf(a, r=r, qv=qv):
            return confidence(a, GAMMA, EPOCH, Q_BLEND, F, seats=seats if r else 0.0,
                              round_slots=r or 1.0, q_votes=qv)
        rows.append(dict(setting=name, model="Cryptarchia, one epoch", confidence=conf(HOLDER),
                         nodes=split(HOLDER, THETA, conf), largest_hidden=largest_hidden(conf)))

    def spec(a):
        return spec_confidence(a, GAMMA, 432_000, 0.657, 0.05)

    def spec_votes(a):
        return confidence(a, GAMMA, 432_000, 0.657, 0.05, seats=seats, round_slots=600)
    rows.append(dict(setting="blocks only", model="the analysis's example", confidence=spec(HOLDER),
                     nodes=split(HOLDER, THETA, spec), largest_hidden=largest_hidden(spec)))
    rows.append(dict(setting="with votes, 10 min rounds", model="the analysis's example",
                     confidence=spec_votes(HOLDER), nodes=split(HOLDER, THETA, spec_votes),
                     largest_hidden=largest_hidden(spec_votes)))
    e = pd.DataFrame(rows)
    e.to_csv(OUT / "epoch.csv", index=False)
    print(e.to_string(index=False))


if __name__ == "__main__":
    main()
