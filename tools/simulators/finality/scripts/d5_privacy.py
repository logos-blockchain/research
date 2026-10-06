"""Phase D5: what votes leak about a holder's stake (PLAN.md D5).

    python scripts/d5_privacy.py      # needs runs/d0; writes runs/d5/{times,epoch}.csv

The committee is D0's against a quarter of the stake at 1e-9 (runs/d0/emission_map.csv), voting
in rounds of 1 h, 10 min and 90 s. A message of a node with an adversarial peer is attributed to it
when its whole blend path is adversarial, with probability f_adv^hops = 0.008 at f_adv = 0.2 and 3
hops (the Blend report's §3.6-§3.7 setting). A block proposal is sent twice (R_D = 1,
blend-protocol.md), so it is attributed with 1 - (1 - 0.008)^2. A vote is sent once through Blend,
or gossiped directly and attributed with probability one. Votes are cast together at each round's
start; a holder's stake is spread over many small notes unless a row says otherwise.

times.csv: the mean days until a holder of each share is identified (N = 1) and its stake known to
±10 % (N = 100), counting its blocks and its votes (src/finality_sim/privacy.py).

epoch.csv: over one epoch, 10 floor(k/f) slots at f = 1/30, the probability that the stake is known
to ±10 % for a 1.26 % holder (the analysis' example holder), the nodes it must split into to keep
that at 0.5 or below, and the share above which every holder's stake is known to ±10 % with
probability above 0.5. Counts are exact Poisson counts.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from finality_sim.privacy import attribution_days, confidence, split

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "d5"
F, K = 1 / 30, 2160
EPOCH = 10 * int(K / F)
Q = 0.2 ** 3
Q_BLOCK = 1 - (1 - Q) ** 2
SHARES = (0.05, 0.01, 0.001, 0.0001)
GAMMA, THETA, HOLDER = 0.1, 0.5, 0.0126
GRID = np.logspace(-7, math.log10(0.5), 2000)


def sized_above(conf) -> float:
    """The share above which every share's confidence exceeds THETA, on GRID."""
    low = [s for s in GRID if conf(s) <= THETA]
    return float(max(low)) if low else 0.0


def main() -> None:
    d0 = pd.read_csv(HERE / "runs" / "d0" / "emission_map.csv")
    seats = float(d0[(d0.awake == 1.0) & (d0.inflation == 1.0) & (d0.eps == 1e-9)
                     & (abs(d0.alpha - 0.25) < 1e-9)].seats.iloc[0])
    settings = [("blocks only, through Blend", None, 0.0, math.inf)]
    settings += [(f"with votes through Blend, {label} rounds", r, Q, math.inf)
                 for label, r in (("1 h", 3600), ("10 min", 600), ("90 s", 90))]
    settings += [("with votes gossiped directly, 10 min rounds", 600, 1.0, math.inf)]

    rows = []
    for name, r, qv, _ in settings:
        kw = dict(seats=seats if r else 0.0, round_s=r or 1.0, q_votes=qv)
        for s in SHARES:
            rows.append(dict(setting=name, share=s,
                             identify_days=attribution_days(s, 1, Q_BLOCK, F, **kw),
                             size_days=attribution_days(s, 100, Q_BLOCK, F, **kw)))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "times.csv", index=False)
    print(t.to_string(index=False), end="\n\n")

    epoch = settings + [(f"with votes through Blend, 10 min rounds, the holder's stake in {m} "
                         f"note{'s' if m > 1 else ''}", 600, Q, m) for m in (1, 10, 100)]
    rows = []
    for name, r, qv, notes in epoch:
        def conf(a, r=r, qv=qv, notes=notes):
            return confidence(a, GAMMA, EPOCH, Q_BLOCK, F, seats=seats if r else 0.0,
                              round_slots=r or 1.0, q_votes=qv, notes=notes)
        many = math.isinf(notes)
        rows.append(dict(setting=name, confidence=conf(HOLDER),
                         nodes=split(HOLDER, THETA, conf) if many else math.nan,
                         sized_above=sized_above(conf) if many else math.nan))
    e = pd.DataFrame(rows)
    e.to_csv(OUT / "epoch.csv", index=False)
    print(e.to_string(index=False))


if __name__ == "__main__":
    main()
