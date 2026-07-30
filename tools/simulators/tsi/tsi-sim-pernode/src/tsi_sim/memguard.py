"""Fail-loud memory guards for the per-node engine's large allocations.

The two dominant arrays — the ``(N x n_blocks)`` arrival matrix ``A`` and the ``(N x N)``
``path_latency`` — can each reach tens to hundreds of GB: ``A`` when a low ``genesis_d_factor``
explodes ``n_blocks`` (the collapsed-``D_est`` regime), ``path_latency`` at very large ``N``.
Every worker checks the size *before* allocating and raises ``ArrivalMatrixTooLarge`` if it would
exceed its budget, so an under-estimated config fails with a clear message instead of freezing the
machine.

Budget resolution (``arrival_budget_bytes``):
- ``TSI_ARRIVAL_BYTES_BUDGET`` > 0  -> that many bytes (the sweep sets this to each worker's RAM
  share so concurrent workers can't collectively OOM);
- unset / ``0`` / invalid       -> a default of ``DEFAULT_BUDGET_FRAC`` of physical RAM, so a
  *single* process (a bare ``run_trajectory``, ``tsi-verify``, the calibration probe, or a
  ``--mem-frac 0`` run) still cannot allocate past what the box physically has.
There is intentionally no "unlimited" setting: no correct run needs to allocate more than physical
RAM, and allowing it is exactly what froze the machine.
"""

from __future__ import annotations

import os
import subprocess

# Absolute per-process ceiling (fraction of physical RAM) used when no explicit budget is set.
DEFAULT_BUDGET_FRAC = 0.9


class ArrivalMatrixTooLarge(MemoryError):
    """A per-node engine array would exceed the memory budget; raised before allocating.

    Typically a block-count explosion (a low ``genesis_d_factor`` inflating early-epoch lottery
    wins) blowing up the ``(N x n_blocks)`` arrival matrix, or a very large ``N`` blowing up the
    ``(N x N)`` ``path_latency`` matrix.
    """


def total_ram_bytes() -> int:
    """Best-effort physical RAM in bytes (POSIX sysconf, then Darwin sysctl, then 8 GB)."""
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        pass
    try:  # macOS lacks SC_PHYS_PAGES
        out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        return int(out.stdout.strip())
    except (OSError, ValueError):
        return 8 * 1024**3


def arrival_budget_bytes() -> int:
    """Per-process byte budget for a single big array (see module docstring)."""
    try:
        explicit = int(os.environ.get("TSI_ARRIVAL_BYTES_BUDGET", "0"))
    except ValueError:
        explicit = 0
    if explicit > 0:
        return explicit
    return int(DEFAULT_BUDGET_FRAC * total_ram_bytes())


def check_alloc(nbytes: int, label: str, detail: str = "") -> None:
    """Raise ``ArrivalMatrixTooLarge`` if allocating ``nbytes`` would exceed the budget."""
    budget = arrival_budget_bytes()
    if nbytes > budget:
        raise ArrivalMatrixTooLarge(
            f"{label} needs {nbytes / 1024**3:.1f} GB > per-process budget "
            f"{budget / 1024**3:.1f} GB.{(' ' + detail) if detail else ''}")
