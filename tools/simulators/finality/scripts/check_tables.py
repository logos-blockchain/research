"""Check that every table scripts/tables.py prints from runs/ appears verbatim in a note.

    python scripts/check_tables.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
NAMES = ("a1", "a1release", "a1conv", "c1", "c1settle", "c3", "c4", "b3", "b3delay", "b2", "b4", "b5", "b5rec", "b5sweep", "b5part", "b5eng", "b6", "b7", "d0", "d1b", "d3", "d5", "d6", "e2", "e5", "e5balance", "g1", "g3", "g4", "g6", "g7", "h1", "h2", "h3", "i2", "j1", "j2", "j3", "j3bound",
         "k1", "k1worst", "k1ratio", "k1played", "k2", "k2compare", "k2waits", "k2absorbs", "k3horizon", "k3eclipse", "k3early", "k3floor", "k3quorum", "k3detector", "k3bootstrap", "k5mapping", "k5rate", "k5blend", "k5relays",
         "k7worst", "k7ratio", "k7slots", "k7checks", "k7played", "k7holds", "k7compare", "k7waits", "k7absorbs", "k7rate",
         "k7blend", "k7floor", "k8params", "k8protection", "k8stall", "k8ratio", "k8deflation", "k8spec",
         "k9floor", "k9protection", "k9stall", "k9quorum",
         "l1today", "l1frontier", "l1convention", "l2departs", "l2time", "l3partition", "l4hedge",
         "l5cost", "m1anon", "m1public", "m1delegation", "m2budget", "m2blend", "m2compare",
         "m3privacy", "m4cost", "m4blend", "m5quorum", "m7supply", "m7seats",
         "m7wait", "m7edge", "m7declared",
         "n1committee", "n1units", "n1rounding", "n2registry", "n2lottery", "n3budget", "n3load",
         "n3p2p", "n4privacy", "n4holders", "n4ceilings", "n5bytes", "n5verify", "n5prove",
         "n6time", "n6layers", "n6online")


def tables(text: str) -> list[str]:
    out, cur = [], []
    for line in text.splitlines():
        if line.startswith("|"):
            cur.append(line)
        elif cur:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return out


def main() -> None:
    notes = "\n".join(p.read_text() for p in sorted(HERE.glob("*.md")))
    missing = []
    for name in NAMES:
        r = subprocess.run([sys.executable, str(HERE / "scripts" / "tables.py"), name],
                           capture_output=True, text=True, check=True)
        for i, t in enumerate(tables(r.stdout)):
            ok = t in notes
            print(f"  [{'ok' if ok else 'MISSING'}] {name} table {i + 1}")
            if not ok:
                missing.append(f"{name} table {i + 1}")
    if missing:
        raise SystemExit(f"tables not found verbatim in the notes: {missing}")


if __name__ == "__main__":
    main()
