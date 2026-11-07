"""Phase N.5: what proving and verifying counted units' votes costs (PLAN.md Phase N).

    python scripts/n5_cost.py        # needs runs/n1; writes runs/n5/{bytes,verify,prove}.csv; seconds

- bytes.csv: per packaging, a proof a unit or one proof a message: a unit vote's bytes, a
  message's fixed bytes, the most votes one payload of 18,195 bytes carries, the share of the
  registered stake a node's message count then hides, a registration's bytes, and the bytes of a
  certificate of the quorum against 30 %.
- verify.csv: verifying a round's proofs on one core of a Raspberry Pi 5, at most 1/157 s a
  proof: Blend measured 157 headers a second there, and a header carries a Groth16 proof of quota
  and a signature (blend-protocol.md, Relaying, and V). A proof a unit verifies the committee's
  units; a proof a message verifies a message from each core node.
- prove.csv: proving on the Apple M4 Pro of tools/benchmarks/pol-proving, on all cores, for a
  holder of 1 %, 0.1 % and 0.01 %: a registration a unit an epoch and a vote a drawn unit a round,
  each taken at one proof of leadership. The circuits prove the same kinds of statement, a
  membership in a tree, a tag and a comparison; they are not measured. The reference board's run
  is the owner's (PLAN.md, Before review).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from finality_sim import unitnet as un
from finality_sim import units as us

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]
OUT = HERE / "runs" / "n5"
U = us.registered_units()
E = us.EPOCH_SLOTS
ROUNDS = (600, 3_600)
NODES = (1_000, 20_000)
SHARES = (0.01, 0.001, 0.0001)


def committees() -> list[tuple[str, int, int]]:
    t = pd.read_csv(HERE / "runs" / "n1" / "committee.csv")
    row = t[abs(t.alpha - 0.30) < 1e-9]
    full = row[row.uptime == 1.0].iloc[0]
    most = row[row.uptime == 0.95].iloc[0]
    return [("public draw, every honest unit online", int(full.public), int(full.public_quorum)),
            ("public draw, 95 % online", int(most.public), int(most.public_quorum)),
            ("every unit voting", U, int(most.every_quorum))]


def pol_ms() -> float:
    t = pd.read_csv(REPO / "reports" / "finality" / "pol-proving" / "results-apple-m4-pro.csv")
    return float(t[t.config == "all cores"].median_ms.median())


def main() -> None:
    fixed = sum(un.MESSAGE_FIELDS.values())
    unit = sum(un.UNIT_VOTE.values())
    rows = []
    for name, per_unit in (("a proof a unit", True), ("a proof a message", False)):
        k = un.k_max(per_unit)
        vote = unit + (un.PROOF if per_unit else 0)
        msg_fixed = fixed + (0 if per_unit else un.PROOF)
        for c, n, q in committees():
            # the quorum's votes come in between ⌈Q/k_max⌉ messages, each full, and Q, one each
            rows.append(dict(packaging=name, unit_vote_bytes=vote, message_fixed_bytes=msg_fixed,
                             k_max=k, hidden_share=k / U,
                             registration_bytes=us.registration_bytes(), committee=c, units=n,
                             quorum=q,
                             certificate_kb_min=(q * vote + math.ceil(q / k) * msg_fixed) / 1e3,
                             certificate_kb_max=q * (vote + msg_fixed) / 1e3))
    sizes = pd.DataFrame(rows)

    per_proof = 1 / un.V_PI5
    verify = []
    for r in ROUNDS:
        for c, n, q in committees():
            verify.append(dict(packaging="a proof a unit", committee=c, units=n, nodes=math.nan,
                               round_s=r, proofs=n, core_share=n * per_proof / r))
        for nodes in NODES:
            verify.append(dict(packaging="a proof a message", committee="any", units=math.nan,
                               nodes=nodes, round_s=r, proofs=nodes,
                               core_share=nodes * per_proof / r))
    verify = pd.DataFrame(verify)

    ms = pol_ms()
    prove = []
    for c, n, q in committees()[:1] + committees()[2:]:
        for s in SHARES:
            held = s * U
            drawn = held * n / U
            for r in ROUNDS:
                prove.append(dict(committee=c, units=n, share=s, units_held=held, pol_ms=ms,
                                  registration_s_per_epoch=held * ms / 1e3,
                                  votes_per_round=drawn, vote_s_per_round=drawn * ms / 1e3,
                                  round_s=r, machine_share=drawn * ms / 1e3 / r))
    prove = pd.DataFrame(prove)

    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in (("bytes", sizes), ("verify", verify), ("prove", prove)):
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(t.to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
