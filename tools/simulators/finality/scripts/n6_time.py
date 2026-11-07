"""Phase N.6: how fast counted units finalize (PLAN.md Phase N).

    python scripts/n6_time.py        # needs runs/n1, d6, m2; writes runs/n6/time.csv; a minute

M.2's mean time from a block's slot until final, at a lag of 30 slots: the wait for the next round
start, the time the quorum's last honest vote leaves, ``R·Q/H`` over a round in which the votes go
out evenly, the delivery, and for the checkpoint gadget one round more
(src/finality_sim/signers.py). The delivery is D6's largest 95th percentile on the specification's
Blend, three layers, and at most Δ_max rounds for each further layer
(src/finality_sim/unitnet.py).

Against 30 % with N.1's committees, on 1,000 and 20,000 core nodes at 3, 5 and 8 layers: the
shortest round, in whole seconds, whose votes add at most a fifth, a half or all of one Pi 5 core
of verifications, headers at Blend's measured 157 a second and a proof a unit. The vote schedule
sends a message a core node a round; one vote a message sends one a unit. Blend as specified sends
one vote a message at three layers within M.2's budget of 4/3 votes a second. At each round: the
read limit and node budget Blend's rules then need, and a holder of 0.1 %'s days to be sized
(scripts/n4_privacy.py), against the chain's own wait (runs/m2/yardstick.csv).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim import signers as sg
from finality_sim import unitnet as un
from finality_sim import units as us
from n4_privacy import row as privacy

HERE = pathlib.Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
OUT = RUNS / "n6"
U = us.registered_units()
F = 1 / 30
Q_BLOCK = 1 - (1 - 0.2 ** 3) ** 2
LAG = 30
ALPHA = 0.30
NODES = (1_000, 20_000)
LAYERS = (3, 5, 8)
BUDGETS = (0.2, 0.5, 1.0)
HOLDER = 0.001


def committees() -> list[tuple[str, int, int, float, float]]:
    t = pd.read_csv(RUNS / "n1" / "committee.csv")
    row = t[abs(t.alpha - ALPHA) < 1e-9]
    full = row[row.uptime == 1.0].iloc[0]
    most = row[row.uptime == 0.95].iloc[0]
    return [("every honest unit online", int(full.public), int(full.public_quorum), 1.0,
             float(full.private) / U),
            ("95 % online", int(most.public), int(most.public_quorum), 0.95,
             float(most.private) / U),
            ("every unit voting, 95 % online", U, int(most.every_quorum), 0.95, 1.0)]


def times(r: int, n: int, q: int, uptime: float, delivery: float) -> dict:
    honest = n * (1 - ALPHA) * uptime
    emit = sg.emission_time(q, honest, r)
    return dict(emit_s=emit, delivery_s=delivery,
                gadget_s=sg.finality_time(LAG, r, 2, emit + delivery),
                single_s=sg.finality_time(LAG, r, 1, emit + delivery),
                latest_s=sg.latest_time(LAG, r, 2, emit + delivery))


def main() -> None:
    d6 = pd.read_csv(RUNS / "d6" / "certificates.csv")
    d6_p95 = float(d6[d6.blend == "specification"].p95.max())
    yard = pd.read_csv(RUNS / "m2" / "yardstick.csv")
    yard = yard[abs(yard.alpha - ALPHA) < 1e-9].iloc[0]
    rows = []
    for c, n, q, uptime, chance in committees():
        priv_committee = "every unit voting" if c.startswith("every unit") else c
        r = math.ceil(n / sg.headroom())
        rows.append(dict(committee=c, units=n, quorum=q, nodes=math.nan, layers=3,
                         budget=math.nan, transport="Blend as specified", round_s=r,
                         **times(r, n, q, uptime, d6_p95),
                         **{k: v for k, v in un.load(n / r, n / r, 3).items()},
                         size_days=privacy(HOLDER, 3, r, priv_committee, n, chance,
                                           "one vote a message, unlinkable")["size_days"]))
        for nodes in NODES:
            for h in LAYERS:
                for b in BUDGETS:
                    cap = b * un.V_PI5
                    for transport, r in (
                            ("schedule", math.ceil((h * nodes + n) / cap)),
                            ("one vote a message", math.ceil((h + 1) * n / cap))):
                        msgs = nodes / r if transport == "schedule" else n / r
                        tr = ("schedule, every unit voting" if c.startswith("every unit") else
                              "schedule, public draw, unlinkable") if transport == "schedule" \
                            else "one vote a message, unlinkable"
                        rows.append(dict(committee=c, units=n, quorum=q, nodes=nodes, layers=h,
                                         budget=b, transport=transport, round_s=r,
                                         **times(r, n, q, uptime, un.delivery_bound(d6_p95, h)),
                                         **un.load(msgs, n / r, h),
                                         size_days=privacy(HOLDER, h, r, priv_committee, n,
                                                           chance, tr)["size_days"]))
    t = pd.DataFrame(rows)
    # Blend as specified keeps r_1 = 20: its votes take the backlog's headroom (M.2), so no
    # node budget is resized for it
    spec = t.transport == "Blend as specified"
    t.loc[spec, ["r1", "v", "v_cores"]] = [20, un.V, un.V / un.V_PI5]
    t["today_size_days"] = un.size_days(100, HOLDER * Q_BLOCK * F)
    t["multiple"] = t.size_days / t.today_size_days
    t["chain_random_h"] = yard.chain_random_h
    t["chain_worst_h"] = yard.chain_worst_h
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "time.csv", index=False)
    sel = t[(t.budget.isna()) | ((t.budget == 0.2) & (t.layers == 8))]
    print(sel[["committee", "nodes", "transport", "round_s", "gadget_s", "single_s", "v_cores",
               "size_days", "multiple"]].to_string(index=False))


if __name__ == "__main__":
    main()
