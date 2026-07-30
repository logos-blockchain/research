#!/usr/bin/env python
"""Thin shim so `python scripts/make_figures.py` works without installing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting.make_figures import main  # noqa: E402

if __name__ == "__main__":
    main()
