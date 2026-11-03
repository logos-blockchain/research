"""Phase L.5: what votes of Blend's declared nodes cost on a Raspberry Pi 5 (PLAN.md Phase L).

    python scripts/l5_cost.py        # writes runs/l5/{cost,rounds}.csv

Every declared node votes once a round, so a node verifies n/R votes a second. Verification times
and signature sizes are the medians the repository measured on a Raspberry Pi 5, one core, in its
reference-grade run (reports/pqc, rasberrypi5-20260811T211615Z.json): Ed25519 with ed25519-dalek
3.0.0, the library family the node uses (its RustCrypto row), and with aws-lc-rs; ML-DSA-44 with
aws-lc-rs. A vote carries the link's two checkpoints, the signer's index in the registry and a
signature; a certificate of separate signatures carries ⌈2n/3⌉ of them, each with its index
(src/finality_sim/netcert.py). Bytes count each vote once; gossip over a mesh of degree d delivers
up to d copies.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from finality_sim import netcert as nc

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "l5"
NODES = (32, 1000, 5000, 20000)
ROUNDS = (30, 60, 600)
SIGS = {"Ed25519, ed25519-dalek": ("Ed25519", "rustcrypto"),
        "Ed25519, aws-lc-rs": ("Ed25519", "aws-lc-rs"),
        "ML-DSA-44, aws-lc-rs": ("ML-DSA-44", "aws-lc-rs")}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meas = {k: nc.pi5_signature(*v) for k, v in SIGS.items()}
    rows = []
    for n in NODES:
        for R in ROUNDS:
            row = dict(nodes=n, round_slots=R, votes_per_s=n / R)
            for k, (ns, size) in meas.items():
                row[f"core {k}"] = nc.verify_core_share(n, R, ns)
                row[f"bytes_per_s {k}"] = n / R * nc.vote_bytes(size)
                row[f"certificate {k}"] = nc.certificate_bytes(n, size)
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "cost.csv", index=False)
    pd.DataFrame([dict(signature=k, verify_ns=ns, signature_bytes=size,
                       vote_bytes=nc.vote_bytes(size)) for k, (ns, size) in meas.items()]
                 ).to_csv(OUT / "signatures.csv", index=False)
    print(pd.read_csv(OUT / "signatures.csv").to_string(index=False))
    print(pd.read_csv(OUT / "cost.csv").to_string(index=False))


if __name__ == "__main__":
    main()
