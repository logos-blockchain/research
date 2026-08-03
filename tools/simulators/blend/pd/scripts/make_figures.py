#!/usr/bin/env python3
"""Shim: add src/ to sys.path, then run pd.plotting.make_figures:main."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pd.plotting.make_figures import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
