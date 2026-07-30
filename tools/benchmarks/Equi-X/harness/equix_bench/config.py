"""Config loading + parameter-matrix expansion into concrete runner cells.

A "cell" is one fully-specified runner invocation: (impl, JobSpec) plus grouping
metadata used for aggregation and plotting. Expansion is the cartesian product
of impls x operations x runtimes x challenges/targets, filtered by each adapter's
declared capabilities/runtimes.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .protocol import JobSpec
from .registry import Adapter


@dataclass
class Cell:
    impl: str
    group: str  # operation, used as the primary plot grouping
    label: dict[str, Any]  # human-facing params (challenge, target, ...)
    job: JobSpec


@dataclass
class Config:
    warmup: int
    repetitions: int
    impls: list[str]
    jobs: list[dict[str, Any]]
    crosscheck: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        d = tomllib.load(f)
    run = d.get("run", {})
    return Config(
        warmup=int(run.get("warmup", 3)),
        repetitions=int(run.get("repetitions", 10)),
        impls=list(run.get("impls", [])),
        jobs=list(d.get("jobs", [])),
        crosscheck=dict(d.get("crosscheck", {})),
        raw=d,
    )


def _supports(adapter: Adapter, operation: str, runtime: str) -> bool:
    if adapter.capabilities and operation not in adapter.capabilities:
        return False
    if adapter.runtimes and runtime not in adapter.runtimes:
        return False
    return True


def expand(config: Config, adapters: dict[str, Adapter]) -> tuple[list[Cell], list[str]]:
    """Return (cells, warnings). Cells whose impl/op/runtime is unsupported are
    skipped with a warning rather than crashing the run."""
    cells: list[Cell] = []
    warnings: list[str] = []

    for job in config.jobs:
        op = job["operation"]
        runtimes = job.get("runtimes", ["try-compile"])
        reps = int(job.get("repetitions", config.repetitions))
        warmup = int(job.get("warmup", config.warmup))

        for impl in config.impls:
            adapter = adapters.get(impl)
            if adapter is None:
                warnings.append(f"impl '{impl}' has no manifest; skipped")
                continue
            for runtime in runtimes:
                if not _supports(adapter, op, runtime):
                    warnings.append(
                        f"{impl} does not support {op}/{runtime}; skipped"
                    )
                    continue
                cells.extend(
                    _expand_job(impl, op, runtime, reps, warmup, job)
                )
    return cells, warnings


def _expand_job(
    impl: str,
    op: str,
    runtime: str,
    reps: int,
    warmup: int,
    job: dict[str, Any],
) -> list[Cell]:
    out: list[Cell] = []

    if op in ("solve", "verify", "hashx_compile"):
        challenges = job.get("challenges", ["deadbeef"])
        # vary_challenge: treat each listed value as a SEED, deriving a fresh
        # challenge per rep (SHA-256 chain) so the measurement spans many
        # challenges instead of assuming one fixed instance.
        vary = bool(job.get("vary_challenge", False)) and op in ("solve", "verify")
        for chal in challenges:
            spec = JobSpec(
                operation=op,
                runtime=runtime,
                repetitions=reps,
                warmup=warmup,
            )
            if vary:
                spec.challenge_seed_hex = chal
            else:
                spec.challenge_hex = chal
            if op == "hashx_compile":
                # hashx_compile varies the seed per rep via a nonce counter.
                spec.challenge_hex = None
                spec.challenge_base_hex = chal
                spec.nonce_start = int(job.get("nonce_start", 0))
            # verify needs a solution_hex (filled by resolve_verify_solutions) —
            # UNLESS in seed mode, where the runner self-solves each challenge.
            out.append(
                Cell(impl=impl, group=op,
                     label={"challenge": chal, "varied": True} if vary else {"challenge": chal},
                     job=spec)
            )

    elif op == "effort":
        bases = job.get("bases", ["abcd"])
        targets = job.get("targets", [1000])
        for base in bases:
            for target in targets:
                spec = JobSpec(
                    operation="effort",
                    runtime=runtime,
                    repetitions=reps,
                    warmup=warmup,
                    challenge_base_hex=base,
                    nonce_bytes=int(job.get("nonce_bytes", 8)),
                    nonce_start=int(job.get("nonce_start", 0)),
                    target_effort=int(target),
                    max_attempts=int(job.get("max_attempts", 5_000_000)),
                )
                out.append(
                    Cell(
                        impl=impl,
                        group="effort",
                        label={"base": base, "target_effort": int(target)},
                        job=spec,
                    )
                )
    else:
        raise ValueError(f"unknown operation in config: {op}")

    return out
