"""Cross-implementation correctness gate.

Two independent checks that any conforming implementations must pass:

1. Interop: solve a challenge with impl A, then verify EACH returned solution
   with impl B (both directions). Every solution must verify OK. This proves the
   implementations compute the same HashX/Equihash puzzle.

2. Effort agreement: run the effort op on A and B with identical parameters. Since
   solving is deterministic, both must report the same attempts and achieved
   effort -- this guards that the BLAKE2b effort preimage is byte-identical
   across languages.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .protocol import JobSpec
from .registry import Adapter
from .runner import run


@dataclass
class Check:
    kind: str
    detail: str
    passed: bool


def _pairs(config_pairs: list[list[str]], impls: list[str]) -> list[tuple[str, str]]:
    if config_pairs:
        return [(p[0], p[1]) for p in config_pairs]
    # default: all ordered pairs
    out = []
    for a in impls:
        for b in impls:
            if a != b:
                out.append((a, b))
    return out


def run_crosscheck(
    adapters: dict[str, Adapter],
    repo_root: Path,
    challenges: list[str],
    pairs: list[tuple[str, str]],
    effort_base: str = "abcd",
    effort_target: int = 200,
    effort_max_attempts: int = 200_000,
) -> tuple[list[Check], bool]:
    checks: list[Check] = []

    # 1. Interop: solutions from A verify under B.
    for a_name, b_name in pairs:
        a, b = adapters.get(a_name), adapters.get(b_name)
        if not a or not b:
            checks.append(Check("interop", f"{a_name}->{b_name}: missing adapter", False))
            continue
        for chal in challenges:
            solve = run(
                a,
                JobSpec(operation="solve", runtime="try-compile", repetitions=1, warmup=0, challenge_hex=chal),
                repo_root,
            )
            sols = solve.solutions_hex or []
            if not sols:
                checks.append(Check("interop", f"{a_name} found 0 solutions for {chal} (nothing to verify)", True))
                continue
            all_ok = True
            for sol in sols:
                v = run(
                    b,
                    JobSpec(operation="verify", runtime="interpret", repetitions=1, warmup=0, challenge_hex=chal, solution_hex=sol),
                    repo_root,
                )
                vr = v.runs[-1].verify_result if v.runs else None
                if vr != "OK":
                    all_ok = False
                    checks.append(Check("interop", f"{a_name} solution {sol} for {chal} did NOT verify under {b_name} (got {vr})", False))
            if all_ok:
                checks.append(Check("interop", f"{a_name}->{b_name}: all {len(sols)} solutions for {chal} verify OK", True))

    # 2. Effort agreement across all impls.
    impls = list(adapters.keys())
    effort_results = {}
    for name in impls:
        a = adapters[name]
        if a.capabilities and "effort" not in a.capabilities:
            continue
        r = run(
            a,
            JobSpec(
                operation="effort", runtime="try-compile", repetitions=1, warmup=0,
                challenge_base_hex=effort_base, nonce_bytes=8, nonce_start=0,
                target_effort=effort_target, max_attempts=effort_max_attempts,
            ),
            repo_root,
        )
        if r.runs:
            effort_results[name] = (r.runs[-1].attempts, r.runs[-1].achieved_effort)
    if len(effort_results) >= 2:
        vals = set(effort_results.values())
        passed = len(vals) == 1
        checks.append(
            Check(
                "effort-agreement",
                f"effort (attempts, achieved) across impls: {effort_results} "
                + ("-- AGREE" if passed else "-- DISAGREE"),
                passed,
            )
        )

    overall = all(c.passed for c in checks) and len(checks) > 0
    return checks, overall
