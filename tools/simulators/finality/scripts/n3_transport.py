"""Phase N.3: what carries the votes of counted units (PLAN.md Phase N).

    python scripts/n3_transport.py   # needs runs/n1; writes runs/n3/{budget,load,p2p}.csv; seconds

src/finality_sim/unitnet.py. The committees are N.1's public draws from 30,000 units against 30 %,
with every honest unit online (5,602 a round) and with 95 % (23,364), and every unit voting
(30,000), which holds 30 % at 95 %.

- budget.csv: Blend as specified, one vote a message at three layers within M.2's budget of 4/3
  to 2.27 votes a second (src/finality_sim/signers.py): the shortest round for each committee.
- load.csv: per committee, core nodes, layers and round, for one vote a message and for the vote
  schedule with a proof a unit or a proof a message: the vote messages a second, ``F_1``, the
  verifications the votes add and their share of one Pi 5 core at Blend's measured 157 a second,
  the read limit and the node budget Blend's rules then need, the bytes a node receives, and the
  most units a node's message count hides: ``k_max`` in the schedule, and with one vote a message
  M.3's quota ceiling over the emission multiple, as a count of units: the stake whose wins a slot
  match a node's share of the cover, one message a round shared by the core nodes.
- p2p.csv: forwarding point to point, described: each vote message crosses ``h`` links, so a node
  carries ``h/R`` of the schedule's messages a second and their bytes.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from finality_sim import signers as sg
from finality_sim import unitnet as un
from finality_sim import units as us

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "n3"
F = 1 / 30
U = us.registered_units()
NODES = (1_000, 20_000)


def ceiling(nodes: int) -> float:
    """M.3's quota ceiling: the stake whose wins a slot match a node's cover, one message a round
    network-wide shared by ``nodes``."""
    return math.log(1 - 1 / nodes) / math.log(1 - F)
LAYERS = (3, 5, 8)
ROUNDS = (60, 600, 3_600, 21_600)


def committees() -> list[tuple[str, int]]:
    t = pd.read_csv(HERE / "runs" / "n1" / "committee.csv")
    row = t[(abs(t.alpha - 0.30) < 1e-9)]
    full = int(row[row.uptime == 1.0].public.iloc[0])
    most = int(row[row.uptime == 0.95].public.iloc[0])
    return [("public draw, every honest unit online", full),
            ("public draw, 95 % online", most),
            ("every unit voting", U)]


def main() -> None:
    budgets = (("no vote in a node's cover", sg.headroom()),
               ("equal stakes", sg.vote_budget(np.ones(1000))))
    budget = pd.DataFrame([dict(committee=c, units=n, budget=b, votes_per_s=rate,
                                round_s=math.ceil(n / rate))
                           for c, n in committees() for b, rate in budgets])

    rows = []
    for c, n in committees():
        for nodes in NODES:
            for h in LAYERS:
                for r in ROUNDS:
                    multiple = 1 + n / (r * F)
                    for transport, msgs, proofs, hidden in (
                            ("one vote a message", n / r, n / r, ceiling(nodes) / multiple * U),
                            ("schedule, a proof a unit", nodes / r, n / r, un.k_max(True)),
                            ("schedule, a proof a message", nodes / r, nodes / r, un.k_max(False))):
                        rows.append(dict(committee=c, units=n, nodes=nodes, layers=h, round_s=r,
                                         transport=transport, vote_messages_per_s=msgs,
                                         proofs_per_s=proofs, hidden_units=hidden,
                                         hidden_share=hidden / U,
                                         **un.load(msgs, proofs, h)))
    load = pd.DataFrame(rows)
    today = un.load(0.0, 0.0, 3)
    load["received_over_today"] = load.received_mb / today["received_mb"]

    p2p = pd.DataFrame([dict(nodes=nodes, layers=h, round_s=r, messages_per_s=h / r,
                             kb_per_s=h / r * un.MESSAGE_BYTES / 1e3)
                        for nodes in NODES for h in LAYERS for r in ROUNDS])

    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in (("budget", budget), ("load", load), ("p2p", p2p)):
        t.to_csv(OUT / f"{name}.csv", index=False)
    print(budget.to_string(index=False), end="\n\n")
    sel = load[(load.round_s == 600) & (load.committee == committees()[0][0])]
    print(sel[["nodes", "layers", "transport", "vote_messages_per_s", "added", "added_cores", "r1",
               "v_cores", "received_mb", "hidden_share"]].to_string(index=False))
    print(f"\ntoday: {today}")


if __name__ == "__main__":
    main()
