"""Phase M.3: what votes through Blend leak at the rates Blend admits (PLAN.md Phase M).

    python scripts/m3_privacy.py    # needs runs/d0; writes runs/m3/privacy.csv

D5's model (src/finality_sim/privacy.py, scripts/d5_privacy.py), for a node with an adversarial
peer: a message of the node is attributed to it when its whole blend path is adversarial, 0.008 at
f_adv = 0.2 and 3 hops; a block proposal goes out twice; a holder's stake lies in many small notes.

Votes at the budgets of src/finality_sim/signers.py: 4/3 a second with no vote fitting a node's
cover, 34/15 with equal stakes, and 4/90 with the cover raised. Anonymous seats: D0's committees
against 10 % and 25 % at 1e-9, each vote a fresh lottery win, so each attributed vote samples the
stake. The chain's own leaders: a leader votes for a win in every round of the window, rate/f votes
a win, and its votes and proposal repeat one lottery win, so the observer samples the stake by the
wins it ties to a node: each win with the chance that one of its messages is attributed.

Mean days until a holder of each share is identified (N = 1) and its stake known to ±10 %
(N = 100). The emission multiple is D0's, 1 + rate/f: a node's lottery emissions over blocks
alone. Votes take scheduled cover as won slots do, so on top of today's cover the quota ceiling,
the stake above which a node's emission count identifies it, falls by that multiple, from the
Blend report's ln(1 − q)/ln(1 − f) at q = 1/20,000 a slot, 0.147 % of the inferred stake on 20,000
nodes (reports/blend §3.10). With the cover raised the ceiling holds.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from finality_sim import signers as sg
from finality_sim.privacy import attribution_days

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "m3"
F = 1 / 30
Q = 0.2 ** 3
Q_BLOCK = 1 - (1 - Q) ** 2
SHARES = (0.01, 0.001, 0.0001)
CEILING = math.log(1 - 1 / 20000) / math.log(1 - F)


def main() -> None:
    d0 = pd.read_csv(HERE / "runs" / "d0" / "emission_map.csv")
    equal = sg.vote_budget(np.ones(1000))
    rows = []

    def add(name, n, r, rate, q_votes, q_win, raised):
        multiple = 1 + rate / F
        for s in SHARES:
            if q_votes > 0:
                ident = attribution_days(s, 1, Q_BLOCK, F, seats=n, round_s=r, q_votes=q_votes)
                size = attribution_days(s, 100, Q_BLOCK, F, seats=n, round_s=r, q_votes=q_votes)
            else:
                ident = attribution_days(s, 1, q_win, F)
                size = attribution_days(s, 100, q_win, F)
            rows.append(dict(setting=name, seats=n, round_s=r, votes_per_s=rate,
                             emission_multiple=multiple,
                             ceiling=CEILING if raised else CEILING / multiple,
                             win_linked=q_win, share=s, identify_days=ident, size_days=size))

    add("blocks only, through Blend", 0.0, math.nan, 0.0, 0.0, Q_BLOCK, True)
    for alpha in (0.10, 0.25):
        n = float(d0[(abs(d0.alpha - alpha) < 1e-9) & (d0.awake == 1.0) & (d0.inflation == 1.0)
                     & (d0.eps == 1e-9)].seats.iloc[0])
        for label, rate, raised in (("no vote in a node's cover", sg.headroom(), False),
                                    ("equal stakes", equal, False),
                                    ("cover raised", sg.vote_rate("raised"), True)):
            r = math.ceil(n / rate)
            add(f"anonymous seats against {round(100 * alpha)} %, {label}", n, r, n / r, Q,
                Q_BLOCK, raised)
    for label, rate, raised in (("no vote in a node's cover", sg.headroom(), False),
                                ("equal stakes", equal, False),
                                ("cover raised", sg.vote_rate("raised"), True)):
        votes = sg.leader_votes(rate=rate)
        add(f"the chain's own leaders, {label}", math.nan, math.nan, rate, 0.0,
            sg.link_chance(2 + votes, Q), raised)
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "privacy.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
