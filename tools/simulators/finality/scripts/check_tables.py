"""Check that every table scripts/tables.py prints from runs/ appears verbatim in a note.

    python scripts/check_tables.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
NAMES = ("a1", "c1", "c1settle", "c3", "c4", "b3", "b3delay", "b2", "b4", "b5", "b5rec", "b5sweep", "b5part", "b6", "b7", "d0", "d1b", "d3", "d5", "d6", "e2", "e5", "e5balance", "g1", "g3", "g4")


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
