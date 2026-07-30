"""DoS-protection effectiveness evaluation.

Equi-X is a client puzzle: a requester must *solve* the puzzle (expensive) before
a service will act, while the service only *verifies* (cheap). The protection is
effective on a given system when the attacker's cost to produce one accepted
request vastly exceeds the defender's cost to check it.

This module answers that question from MEASURED data on the running system:

  attacker_s(E)  = measured median time to produce one token at effort E
                   (the `effort` op: solve over nonces until achieved >= E)
  defender_s     = measured median time for one `verify`
  protection_factor(E) = attacker_s(E) / defender_s
       -> how many requests the defender can screen in the time an attacker needs
          to craft one accepted request. Large = strong DoS protection.

Also derived:
  verify_throughput   = 1 / defender_s          (verifications/sec per core)
  attacker_token_rate = 1 / attacker_s(E)        (accepted tokens/sec per core)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .stats import CellStats

# Protection is judged "effective" when an attacker spends at least this many
# times the defender's per-verify cost to produce one accepted request.
DEFAULT_THRESHOLD = 10_000.0


def min_verify_seconds(stats: list[CellStats], device: str) -> Optional[float]:
    """Defender's best (fastest) verify time on `device`, in seconds."""
    vs = [
        s.median_ns / 1e9
        for s in stats
        if s.operation == "verify" and s.ok and s.device_label == device and s.median_ns > 0
    ]
    return min(vs) if vs else None


@dataclass
class ProtectionRow:
    device: str
    effort: int
    attacker_impl: str
    attacker_s: float          # fastest measured time to craft a token at this effort
    defender_verify_s: float   # fastest measured verify time
    protection_factor: float   # attacker_s / defender_verify_s
    verify_per_sec: float       # defender screening capacity (per core)
    attacker_tokens_per_sec: float  # attacker output (per core)


def assess(stats: list[CellStats], threshold: float = DEFAULT_THRESHOLD):
    """Return (rows, effective, threshold). Uses the attacker's fastest impl and
    the defender's fastest verify per device -- the realistic optimized case."""
    rows: list[ProtectionRow] = []
    for dev in sorted({s.device_label for s in stats if s.ok}):
        vs = min_verify_seconds(stats, dev)
        if vs is None or vs <= 0:
            continue
        by_effort: dict[int, list[tuple[float, str]]] = {}
        for s in stats:
            if s.operation == "effort" and s.ok and s.device_label == dev and s.median_ns > 0:
                t = int(s.label.get("target_effort", 0))
                by_effort.setdefault(t, []).append((s.median_ns / 1e9, s.impl))
        for t in sorted(by_effort):
            attacker_s, attacker_impl = min(by_effort[t], key=lambda x: x[0])
            rows.append(ProtectionRow(
                device=dev, effort=t, attacker_impl=attacker_impl,
                attacker_s=attacker_s, defender_verify_s=vs,
                protection_factor=attacker_s / vs,
                verify_per_sec=1.0 / vs,
                attacker_tokens_per_sec=1.0 / attacker_s,
            ))
    # "Effective on this system" means SOME reachable effort clears the bar; the
    # smallest such effort tells the operator how hard to set the puzzle here.
    effective = any(r.protection_factor >= threshold for r in rows)
    return rows, effective, threshold


def min_effective_effort(rows, threshold: float = DEFAULT_THRESHOLD):
    """Smallest measured effort whose protection factor clears the threshold,
    grouped per device. Returns {device: effort or None}."""
    out: dict[str, Optional[int]] = {}
    for r in rows:
        if r.device not in out:
            out[r.device] = None
        if r.protection_factor >= threshold and (out[r.device] is None or r.effort < out[r.device]):
            out[r.device] = r.effort
    return out
