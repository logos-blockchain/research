#!/usr/bin/env python3
"""Shim: add src/ to sys.path, then run blend.verify:main."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from blend.verify import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
