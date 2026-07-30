#!/usr/bin/env python
"""Thin shim so `python scripts/verify.py` works without installing; see tsi_sim.verify."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.verify import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
