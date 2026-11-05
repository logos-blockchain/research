"""Phase M.4: what verifying and carrying the votes costs each signer set (PLAN.md Phase M).

    python scripts/m4_cost.py       # writes runs/m4/{cost,blend}.csv; reads reports/pqc

cost.csv: public signers vote once a round of 60 slots, as L.5 counts them, at 1,000, 20,000 and
100,000 signers (src/finality_sim/netcert.py). Ed25519 verification is the Raspberry Pi 5's median
on one core with ed25519-dalek (reports/pqc). Bytes count each vote once; gossip over a mesh of
degree d delivers up to d copies.

blend.csv: votes through Blend at each budget of src/finality_sim/signers.py: 4/3 a second with no
vote fitting a node's cover, 34/15 with equal stakes, where the votes beyond each node's cover fill
the same headroom, and 4/90 with the cover raised. Every node verifies a message's
header once for each of its β_max blending operations (D3), against V = 156 a second, one core of a
Raspberry Pi 5 (blend-protocol.md); a leader's vote also carries an Ed25519 signature, a seat's a
proof the repository has not measured on the Pi 5. A core connection carries F_1 messages a round
of 19,318 bytes each (blend-protocol.md). Kept for the backlog, the headroom comes out of the
transaction messages. Blend's keys for a leader's votes a win, β_max a vote, against today's
leadership quota of β_max(1 + R_D) a win.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from finality_sim import committee as cm
from finality_sim import netcert as nc
from finality_sim import signers as sg

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "m4"
ROUND = 60
SIGNERS = (1000, 20000, 100000)
MESSAGE_BYTES = 19318


def main() -> None:
    ns, size = nc.pi5_signature("Ed25519", "rustcrypto")
    rows = []
    for n in SIGNERS:
        rows.append(dict(signers=n, votes_per_s=n / ROUND,
                         core_share=nc.verify_core_share(n, ROUND, ns),
                         kb_per_s=n / ROUND * nc.vote_bytes(size) / 1000))
    cost = pd.DataFrame(rows)

    rows = []
    today = cm.blend_load(0.0)[0]
    modes = (("no vote in a node's cover", sg.headroom(), cm.blend_load(sg.headroom())[0]),
             ("equal stakes", sg.vote_budget(np.ones(1000)), cm.blend_load(sg.headroom())[0]),
             ("cover raised", sg.vote_rate("raised"),
              cm.blend_load(0.0, 1 + sg.vote_rate("raised") / sg.F)[0]))
    for mode, v, f1 in modes:
        headers = f1 - today
        rows.append(dict(mode=mode, votes_per_s=v, headers_per_s=headers,
                         headers_share=headers / cm.V, signature_share=v * ns * 1e-9,
                         f1_today=today, f1=f1, kb_per_connection_today=today * MESSAGE_BYTES / 1000,
                         kb_per_connection=f1 * MESSAGE_BYTES / 1000,
                         transactions_taken=sg.transaction_share(headers / cm.BETA_MAX),
                         leader_keys_per_win=sg.leader_votes(rate=v) * cm.BETA_MAX,
                         leadership_quota=cm.BETA_MAX * (1 + cm.R_D)))
    blend = pd.DataFrame(rows)

    OUT.mkdir(parents=True, exist_ok=True)
    cost.to_csv(OUT / "cost.csv", index=False)
    blend.to_csv(OUT / "blend.csv", index=False)
    print(f"Ed25519 verify {ns:.0f} ns, signature {size} B")
    print(cost.to_string(index=False), end="\n\n")
    print(blend.to_string(index=False))


if __name__ == "__main__":
    main()
