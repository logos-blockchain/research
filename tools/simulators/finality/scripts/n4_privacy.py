"""Phase N.4: what the votes of counted units reveal (PLAN.md Phase N).

    python scripts/n4_privacy.py     # needs runs/n1; writes runs/n4/privacy.csv; a few minutes

src/finality_sim/unitnet.py, D5's model as M.3 reads it: a node's message is attributed to it
when its whole blend path is adversarial, f_adv^h at f_adv = 0.2 and h layers; a block proposal
goes out twice at Blend's three layers; a holder is identified at its first attributed emission
that shows stake and sized to ±10 % at 100 observations.

Holders of 1 %, 0.1 % and 0.01 % of 30,000 registered units, against 30 % with N.1's committees:
the public draw (5,602 a round with every honest unit online, 23,364 with 95 %), the private draw
(its chance a unit at full uptime) and every unit voting. Each registers its units once an epoch.

- blocks only: today, the Blend report's time.
- one vote a message: each vote and each registration its own message at h layers. Unlinkable
  votes are single observations; with linkable keys a unit is tied once any of its epoch's
  messages is attributed, and each epoch's tied units are a binomial draw.
- the schedule: one message a node a round, attributed with f_adv^h, worth E[k]²/Var[k]
  observations of its drawn units, plus the registrations it carries, spread at random over the
  rounds of the epoch, u·R/E on average. With linkable keys, the first attributed message that
  carries a unit sizes the holder at the epoch's end. Every unit voting sizes it at the first.

ceilings.csv: the most stake a node's count of messages hides, as a share of the registered stake:
today's quota ceiling for blocks (M.3), the stake whose wins a slot match a node's share of one
cover message a round, on 1,000 and 20,000 core nodes; with one vote a message, that ceiling over
the emission multiple at rounds of 600 s; in the schedule, the most units whose drawn count exceeds
k_max with chance at most 1e-9 a round (src/finality_sim/unitnet.py, count_ceiling).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim import unitnet as un
from finality_sim import units as us
from finality_sim.privacy import attribution_days

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "n4"
F = 1 / 30
Q3 = 0.2 ** 3
Q_BLOCK = 1 - (1 - Q3) ** 2
U = us.registered_units()
E = us.EPOCH_SLOTS
SHARES = (0.01, 0.001, 0.0001)
LAYERS = (3, 5, 8)
ROUNDS = (600, 3_600)
JOBS = 12


def committees() -> list[tuple[str, int, float]]:
    t = pd.read_csv(HERE / "runs" / "n1" / "committee.csv")
    row = t[abs(t.alpha - 0.30) < 1e-9]
    full = row[row.uptime == 1.0].iloc[0]
    most = row[row.uptime == 0.95].iloc[0]
    return [("every honest unit online", int(full.public), float(full.private) / U),
            ("95 % online", int(most.public), float(most.private) / U)]


def row(share: float, h: int, r: int, committee: str, n: int, chance: float, transport: str) -> dict:
    held = share * U
    q = 0.2 ** h
    blocks = share * Q_BLOCK * F
    reg_info = held * r / E                       # registrations an attributed message carries
    p_any = 1 - us.hyper_pmf(n, U, round(held))[0]   # the node draws some unit in a round
    out = dict(share=share, units_held=held, layers=h, round_s=r, committee=committee, units=n,
               transport=transport)
    if transport.startswith("one vote a message"):
        rate = blocks + share * n * q / r + held * q / E
        out.update(identify_days=un.size_days(1, rate))
        if transport.endswith("unlinkable"):
            out.update(size_days=un.size_days(100, rate))
        else:
            tie = un.tie_chance(n / U * E / r + 1, q)       # a unit's votes and registration
            epoch_info = 100.0 if tie >= 1 else held * tie / (1 - tie)
            out.update(size_days=un.size_days(100, blocks, epoch_s=E,
                                              epoch_info=min(epoch_info, 100.0)))
    else:
        rate_msg = q / r
        if transport.startswith("schedule, public draw"):
            info = un.info_public(held, n, U)
        elif transport.startswith("schedule, private draw"):
            info = un.info_private(held, chance)
            p_any = 1 - (1 - chance) ** held
        else:                                     # every unit voting
            info, p_any = math.inf, 1.0
        info = info + reg_info
        exact = un.tie_chance(E / r * p_any, q) if transport.endswith("linkable keys") else 0.0
        out.update(identify_days=un.size_days(1, blocks, rate_msg * p_any, 1.0),
                   size_days=un.size_days(100, blocks, rate_msg, info, epoch_s=E,
                                          epoch_exact=exact))
    return out


TRANSPORTS = ("one vote a message, unlinkable", "one vote a message, linkable keys",
              "schedule, public draw, unlinkable", "schedule, public draw, linkable keys",
              "schedule, private draw, unlinkable", "schedule, every unit voting")


def main() -> None:
    jobs = []
    for committee, n, chance in committees():
        for s in SHARES:
            for h in LAYERS:
                for r in ROUNDS:
                    for tr in TRANSPORTS:
                        if tr == "schedule, every unit voting":
                            jobs.append((s, h, r, "every unit voting", U, 1.0, tr))
                        else:
                            jobs.append((s, h, r, committee, n, chance, tr))
    jobs = list(dict.fromkeys(jobs))
    rows = Parallel(n_jobs=JOBS)(delayed(row)(*j) for j in jobs)
    t = pd.DataFrame(rows)
    today = {s: attribution_days(s, 100, Q_BLOCK) for s in SHARES}
    today_id = {s: attribution_days(s, 1, Q_BLOCK) for s in SHARES}
    t["today_size_days"] = t.share.map(today)
    t["today_identify_days"] = t.share.map(today_id)
    t["multiple"] = t.size_days / t.today_size_days
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "privacy.csv", index=False)

    # the most stake a node's count of messages hides: today's quota ceiling for blocks on each
    # network; with one vote a message that ceiling over the emission multiple at rounds of 600 s;
    # in the schedule, the most units whose drawn count exceeds k_max with chance 1e-9 a round
    ceilings = []
    for nodes in (1_000, 20_000):
        today_c = math.log(1 - 1 / nodes) / math.log(1 - F)
        ceilings.append(dict(nodes=nodes, design="blocks only, today", committee="",
                             packaging="", share=today_c))
        for committee, n, _ in committees():
            ceilings.append(dict(nodes=nodes, design="one vote a message", committee=committee,
                                 packaging="", share=today_c / (1 + n / (600 * F))))
    for committee, n, _ in committees() + [("every unit voting", U, 1.0)]:
        for packaging, per_unit in (("a proof a unit", True), ("a proof a message", False)):
            c = un.count_ceiling(un.k_max(per_unit), n, U, 1e-9)
            ceilings.append(dict(nodes=math.nan, design="schedule", committee=committee,
                                 packaging=packaging, share=c / U))
    pd.DataFrame(ceilings).to_csv(OUT / "ceilings.csv", index=False)
    print(pd.DataFrame(ceilings).to_string(index=False))
    sel = t[(t.share == 0.001) & (t.round_s == 600)]
    print(sel[["committee", "layers", "transport", "identify_days", "size_days",
               "multiple"]].to_string(index=False))
    print({s: (round(today_id[s], 1), round(today[s], 1)) for s in SHARES})


if __name__ == "__main__":
    main()
