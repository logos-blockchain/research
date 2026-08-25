"""Entry point: python -m empowering --config configs/specified.toml [section...]"""
from __future__ import annotations

import argparse
import sys

from . import analyses, params


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering")
    ap.add_argument("--config", required=True, help="TOML parameter file")
    ap.add_argument("sections", nargs="*", default=[],
                    help=f"which analyses to run (default: all of {', '.join(analyses.ALL)})")
    args = ap.parse_args()

    p = params.load(args.config)
    print(f"config: {p.name} — {p.description}\n")

    names = args.sections or list(analyses.ALL)
    unknown = [n for n in names if n not in analyses.ALL]
    if unknown:
        ap.error(f"unknown section(s): {', '.join(unknown)}")
    for i, n in enumerate(names):
        if i:
            print()
        analyses.ALL[n](p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
