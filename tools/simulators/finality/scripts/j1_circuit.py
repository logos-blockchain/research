"""Phase J, J.1: the price of a second hash in the proof of leadership (DAG.md J.1).

    python scripts/j1_circuit.py [CHECKOUT]   # writes runs/j1/circuit.csv; needs circom 2.2.2

Compiles the proof-of-leadership circuit of logos-blockchain-circuits v0.5.6 (07c43935, the
revision that logos-blockchain 4e0405d51 pins; a cargo build of the node checks it out under
~/.cargo/git/checkouts) with the build's flags, `--r1cs --O2`, and three variants that each add
one Poseidon2 hash:

- the tag bound to the epoch nonce: the entropy contribution also hashes `eta`;
- the contribution proved from the tag: `hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ tag)`, with the
  parent's contribution a public input and the block's a public output;
- the contribution proved from the secrets: `hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ sl ‖ noteID ‖
  sk)`, with the same public values.

A contribution that every node derives, `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`,
from the parent's contribution and the block's tag, both public, changes nothing in the circuit.
The proving key's domain is the smallest power of two that holds the constraints, the public
values and the constant.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "j1"
REV = "07c439356435eb6a2f1f4a8daa973bd04bd0b088"
CHECKOUT = pathlib.Path.home() / ".cargo/git/checkouts/logos-blockchain-circuits-6ffb2cf5a63ddcbb/07c4393"
CIRCOM = "2.2.2"
SOURCES = ("mantle", "hash_bn", "ledger", "misc", "circomlib/circuits")
DST2 = int.from_bytes(b"NONCE_CONTRIB_V2", "little")

MAIN = "P_lead_part_one,P_lead_part_two]}"
TAIL = "    entropy_contribution <== entropy.out;\n"


def contribution(inputs: str) -> list[tuple[str, str, str]]:
    """The edits that prove `hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ inputs)` beside the tag."""
    names = ["parent_contribution"] + [s.strip() for s in inputs.split(",")]
    body = "".join(f"    contrib.inp[{i + 1}] <== {n};\n" for i, n in enumerate(names))
    return [("pol.circom", MAIN, "P_lead_part_one,P_lead_part_two,parent_contribution]}"),
            ("pol_lib.circom", TAIL, TAIL + "\n    signal input parent_contribution;\n"
             "    signal output contribution;\n"
             f"    component contrib = Poseidon2_hash({len(names) + 1});\n"
             f"    contrib.inp[0] <== {DST2};\n" + body
             + "    contribution <== contrib.out;\n")]


VARIANTS = {
    "today": [],
    "the contribution derived by every node": [],
    "the tag bound to the epoch nonce": [
        ("pol_lib.circom", "    signal input slot;\n    signal input note_id;\n    signal input secret_key;\n"
         "    signal output out;\n\n    component hash = Poseidon2_hash(4);\n"
         "    component dst = NONCE_CONTRIB_V1();\n    hash.inp[0] <== dst.out;\n"
         "    hash.inp[1] <== slot;\n    hash.inp[2] <== note_id;\n    hash.inp[3] <== secret_key;\n",
         "    signal input epoch_nonce;\n    signal input slot;\n    signal input note_id;\n"
         "    signal input secret_key;\n    signal output out;\n\n    component hash = Poseidon2_hash(5);\n"
         "    component dst = NONCE_CONTRIB_V1();\n    hash.inp[0] <== dst.out;\n"
         "    hash.inp[1] <== epoch_nonce;\n    hash.inp[2] <== slot;\n    hash.inp[3] <== note_id;\n"
         "    hash.inp[4] <== secret_key;\n"),
        ("pol_lib.circom", "    entropy.slot <== sl;\n",
         "    entropy.epoch_nonce <== epoch_nonce;\n    entropy.slot <== sl;\n")],
    "the contribution proved from the tag": contribution("entropy.out"),
    "the contribution proved from the secrets": contribution(
        "sl, lottery_checker.note_identifier, secret_key"),
}


def compile_variant(checkout: pathlib.Path, edits: list[tuple[str, str, str]]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "src"
        for d in SOURCES:
            shutil.copytree(checkout / d, src / d)
        for name, old, new in edits:
            path = src / "mantle" / name
            text = path.read_text()
            if text.count(old) != 1:
                raise ValueError(f"{name}: the edit's text occurs {text.count(old)} times")
            path.write_text(text.replace(old, new))
        r = subprocess.run(["circom", "mantle/pol.circom", "--r1cs", "--O2", "--output", tmp],
                           cwd=src, capture_output=True, text=True, check=True)
    log = re.sub(r"\x1b\[[0-9;]*m", "", r.stdout)
    get = {k: int(re.search(rf"^{k}: (\d+)", log, re.M).group(1))
           for k in ("non-linear constraints", "linear constraints", "public inputs",
                     "public outputs", "wires")}
    public = get["public inputs"] + get["public outputs"]
    n = get["non-linear constraints"] + get["linear constraints"]
    rows = n + public + 1
    return dict(constraints=n, wires=get["wires"], public=public,
                domain=1 << (rows - 1).bit_length())


def measure(checkout: pathlib.Path = CHECKOUT) -> pd.DataFrame:
    rev = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True,
                         text=True, check=True).stdout.strip()
    if rev != REV:
        raise SystemExit(f"{checkout} is at {rev}, not {REV}")
    version = subprocess.run(["circom", "--version"], capture_output=True, text=True,
                             check=True).stdout
    if CIRCOM not in version:
        raise SystemExit(f"circom {CIRCOM} required; got {version.strip()}")
    rows = [dict(variant=v, **compile_variant(checkout, e)) for v, e in VARIANTS.items()]
    t = pd.DataFrame(rows)
    t["added"] = t.constraints - t.constraints.iloc[0]
    t["share"] = t.added / t.constraints.iloc[0]
    return t


def main() -> None:
    t = measure(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else CHECKOUT)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "circuit.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
