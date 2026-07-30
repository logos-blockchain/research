"""Wire protocol: job-spec (harness -> runner) and result (runner -> harness).

The schema is documented in adapters/README.md. Runners are language-agnostic;
this module is the single source of truth for how the Python harness speaks it.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

SCHEMA_VERSION = 1


@dataclass
class JobSpec:
    """One runner invocation. Only the fields relevant to the operation are set."""

    operation: str  # solve | verify | effort | hashx_compile
    runtime: str  # interpret | try-compile | must-compile
    repetitions: int = 10
    warmup: int = 3
    challenge_hex: Optional[str] = None
    # When set, each rep derives a fresh challenge by SHA-256-chaining this seed
    # (solve/verify only); challenge generation is excluded from timed regions.
    challenge_seed_hex: Optional[str] = None
    challenge_base_hex: Optional[str] = None
    solution_hex: Optional[str] = None
    nonce_bytes: Optional[int] = None
    nonce_start: Optional[int] = None
    target_effort: Optional[int] = None
    max_attempts: Optional[int] = None
    seed: Optional[int] = None

    def to_json(self) -> str:
        d: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
        d.update({k: v for k, v in asdict(self).items() if v is not None})
        return json.dumps(d)


@dataclass
class Run:
    index: int
    wall_ns: int
    solutions: int
    compile_ns: int
    attempts: int
    achieved_effort: int
    verify_result: Optional[str]


@dataclass
class Result:
    ok: bool
    impl_name: str
    impl_version: str
    impl_commit: str
    operation: str
    runtime_requested: str
    runtime_effective: Optional[str]
    env: dict[str, Any]
    runs: list[Run]
    solutions_hex: Optional[list[str]]
    peak_rss_kb: int
    error: Optional[str]
    raw: dict[str, Any] = field(default_factory=dict)
    # effort op only: wire bytes (hex) of the winning token's nonce.
    winning_nonce_hex: Optional[str] = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Result":
        sv = d.get("schema_version")
        if sv != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {sv!r} (expected {SCHEMA_VERSION})")
        impl = d.get("impl", {}) or {}
        runs = [
            Run(
                index=r.get("index", i),
                wall_ns=int(r.get("wall_ns", 0)),
                solutions=int(r.get("solutions", 0)),
                compile_ns=int(r.get("compile_ns", 0)),
                attempts=int(r.get("attempts", 0)),
                achieved_effort=int(r.get("achieved_effort", 0)),
                verify_result=r.get("verify_result"),
            )
            for i, r in enumerate(d.get("runs", []) or [])
        ]
        return Result(
            ok=bool(d.get("ok", False)),
            impl_name=impl.get("name", "?"),
            impl_version=impl.get("version", "?"),
            impl_commit=impl.get("commit", "?"),
            operation=d.get("operation", "?"),
            runtime_requested=d.get("runtime_requested", "?"),
            runtime_effective=d.get("runtime_effective"),
            env=d.get("env", {}) or {},
            runs=runs,
            solutions_hex=d.get("solutions_hex"),
            peak_rss_kb=int(d.get("peak_rss_kb", 0)),
            error=d.get("error"),
            raw=d,
            winning_nonce_hex=d.get("winning_nonce_hex"),
        )
