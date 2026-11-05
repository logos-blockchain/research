"""Phase M.2: how fast each signer set finalizes (PLAN.md Phase M).

    python scripts/m2_time.py       # needs runs/d0, d6, l2, l4; writes runs/m2/{budget,blend,yardstick}.csv

budget.csv: the votes a second Blend carries when a vote takes its node's next scheduled cover
message, as a won slot does, and only a node's emissions beyond its cover fill the headroom
(src/finality_sim/signers.py, vote_budget): with no vote fitting a node's cover, on Cardano's pools
as nodes (D1b's data/cardano_pool_stakes.csv), and with equal stakes on 1,000 nodes; and with the
cover raised to keep today's quota ceiling.

blend.csv: votes through Blend, per coalition share, for anonymous seats (D0's committee and quorum
at 1e-9, every honest seat counting, and with the inference's error up to 1.05, whose rounds carry
1.05 times the committee; runs/d0/emission_map.csv) and for the chain's own leaders (the counted
committee at 1e-9, with every honest leader online and with 95 % online). Rounds are the shortest
that carry the votes at each budget, rounded up to whole slots. The coalition withholds its votes,
so the quorum's last honest vote leaves R·Q/H into the round, for H the honest votes cast; D6's
largest 95th-percentile delivery on the specification's Blend is added (runs/d6/certificates.csv).
At a lag of 30 slots: the gadget's mean time from a block's slot until final and the time for the
block placed worst in a round; a single certificate's mean time at the same quorum (D1 (a)).

yardstick.csv: per coalition share, the chain's own wait at 1e-9 under random delay on the
specification's Blend, and under the worst case at 10 s without grinding and with the new nonce
after a deflation where K.7 reads it (L.4, runs/l4/hedge.csv); and public signers at rounds of 60
slots and a lag of 30 on the specification's Blend, 1,000 declarations of weight one (L.2,
runs/l2/gadget.csv): the mean over replicates of the median node's mean time, and the largest
95th-percentile time.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from finality_sim import signers as sg

HERE = pathlib.Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
OUT = RUNS / "m2"
EPS = 1e-9
LAG = 30
SHARES = (("10 %", 0.10), ("25 %", 0.25), ("30 %", 0.30), ("a third", 1 / 3))


def budgets() -> list[tuple[str, float]]:
    stakes = pd.read_csv(HERE / "data" / "cardano_pool_stakes.csv").stake.to_numpy()
    return [("no vote in a node's cover", sg.headroom()),
            ("Cardano's pools", sg.vote_budget(stakes)),
            ("equal stakes", sg.vote_budget(np.ones(1000))),
            ("cover raised", sg.vote_rate("raised"))]


def seats(d0: pd.DataFrame, alpha: float, inflation: float) -> tuple[float, float]:
    row = d0[(abs(d0.alpha - alpha) < 1e-9) & (d0.awake == 1.0) & (d0.inflation == inflation)
             & (d0.eps == EPS)]
    if row.empty or not math.isfinite(row.seats.iloc[0]):
        return math.nan, math.nan
    return float(row.seats.iloc[0]), float(row.quorum.iloc[0])


def leaders(alpha: float, uptime: float) -> tuple[float, float]:
    found = sg.known_committee(alpha, EPS, uptime)
    return (float(found[0]), float(found[1])) if found else (math.nan, math.nan)


def main() -> None:
    d0 = pd.read_csv(RUNS / "d0" / "emission_map.csv")
    d6 = pd.read_csv(RUNS / "d6" / "certificates.csv")
    delivery = float(d6[d6.blend == "specification"].p95.max())
    modes = budgets()
    rows = []
    for name, a in SHARES:
        sets = (("anonymous seats, every honest seat counting", seats(d0, a, 1.0), 1.0, 1.0),
                ("anonymous seats, the inference's error up to 1.05", seats(d0, a, 1.05), 1.05, 1.0),
                ("the chain's own leaders, counted, every honest leader online", leaders(a, 1.0),
                 1.0, 1.0),
                ("the chain's own leaders, counted, 95 % online", leaders(a, 0.95), 1.0, 0.95))
        for label, (n, quorum), carried, online in sets:
            for mode, rate in modes:
                row = dict(share=name, alpha=a, set=label, n=n, quorum=quorum, mode=mode,
                           rate=rate, delivery_s=delivery)
                if math.isfinite(n):
                    r = math.ceil(carried * n / rate)
                    emit = sg.emission_time(quorum, (1 - a) * online * n, r)
                    row.update(round_s=r, emission_s=emit,
                               gadget_s=sg.finality_time(LAG, r, 2, emit + delivery),
                               latest_s=sg.latest_time(LAG, r, 2, emit + delivery),
                               single_s=sg.finality_time(LAG, r, 1, emit + delivery))
                else:
                    row.update(round_s=math.nan, emission_s=math.nan, gadget_s=math.nan,
                               latest_s=math.nan, single_s=math.nan)
                rows.append(row)
    blend = pd.DataFrame(rows)

    hedge = pd.read_csv(RUNS / "l4" / "hedge.csv")
    l2 = pd.read_csv(RUNS / "l2" / "gadget.csv")
    pub = l2[(l2.blend == "specification") & (l2.round_slots == 60) & (l2.lag == LAG)
             & (l2.withheld == 0.0)]
    assert (pub.first_off < 0).all(), "a justified checkpoint left the chain"
    rows = []
    for name, a in SHARES:
        h = hedge[abs(hedge.alpha - a) < 1e-9].iloc[0]
        rows.append(dict(share=name, alpha=a, chain_random_h=h.random_h, chain_worst_h=h.worst_h,
                         chain_deflated_h=h.nonce_deflated_h, slot_rule_h=18.0,
                         public_mean_s=pub.mean_p50.mean(), public_p95_s=pub.p95_p95.max()))
    yard = pd.DataFrame(rows)

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([dict(mode=m, votes_per_s=v) for m, v in modes]).to_csv(OUT / "budget.csv",
                                                                         index=False)
    blend.to_csv(OUT / "blend.csv", index=False)
    yard.to_csv(OUT / "yardstick.csv", index=False)
    print(pd.read_csv(OUT / "budget.csv").to_string(index=False), end="\n\n")
    print(blend.to_string(index=False), end="\n\n")
    print(yard.to_string(index=False))


if __name__ == "__main__":
    main()
