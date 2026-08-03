"""Fail-loud memory guard for large allocations (copied from tsi-sim-pernode).

The dominant arrays here are the sparse CSR adjacency (``2E = N*degree`` entries) and the
sampled single-source distance matrices (``S x N`` or ``(blend_hops+1) x N``), which grow with
``N``. Every worker checks the size *before* allocating and raises ``AllocationTooLarge`` if it
would exceed its budget, so an under-sized config fails with a clear message instead of freezing
the machine.

Budget (``budget_bytes``): ``PD_BYTES_BUDGET`` > 0 -> that many bytes (the sweep sets this to
each worker's RAM share); otherwise ``DEFAULT_BUDGET_FRAC`` of physical RAM.
"""

from __future__ import annotations

import os
import subprocess

DEFAULT_BUDGET_FRAC = 0.9


class AllocationTooLarge(MemoryError):
    """A pd array would exceed the memory budget; raised before allocating."""


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


def budget_bytes() -> int:
    """Per-process byte budget for a single big array (see module docstring)."""
    try:
        explicit = int(os.environ.get("PD_BYTES_BUDGET", "0"))
    except ValueError:
        explicit = 0
    if explicit > 0:
        return explicit
    return int(DEFAULT_BUDGET_FRAC * total_ram_bytes())


def check_alloc(nbytes: int, label: str, detail: str = "") -> None:
    """Raise ``AllocationTooLarge`` if allocating ``nbytes`` would exceed the budget."""
    budget = budget_bytes()
    if nbytes > budget:
        raise AllocationTooLarge(
            f"{label} needs {nbytes / 1024**3:.1f} GB > per-process budget "
            f"{budget / 1024**3:.1f} GB.{(' ' + detail) if detail else ''}")
