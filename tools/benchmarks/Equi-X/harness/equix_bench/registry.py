"""Adapter registry: discover implementations from TOML manifests.

Each implementation ("adapter") ships a manifest declaring how to invoke its
runner and what it supports. New implementations plug in by adding a manifest --
no harness code changes. See adapters/README.md.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Adapter:
    name: str
    exec: list[str]  # argv; paths resolved against repo root
    protocol_version: int
    capabilities: list[str]
    runtimes: list[str]
    env: dict[str, str]

    def resolve(self, repo_root: Path) -> list[str]:
        """Resolve the executable path (first argv element) against repo root."""
        argv = list(self.exec)
        p = Path(argv[0])
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        argv[0] = str(p)
        return argv

    def available(self, repo_root: Path) -> bool:
        argv = self.resolve(repo_root)
        first = argv[0]
        # A bare interpreter name (e.g. "python3") is looked up on PATH.
        if "/" not in self.exec[0]:
            return True
        return os.path.exists(first) and os.access(first, os.X_OK)


def load_manifest(path: Path) -> Adapter:
    with open(path, "rb") as f:
        d = tomllib.load(f)
    exec_field = d["exec"]
    if isinstance(exec_field, str):
        exec_field = [exec_field]
    return Adapter(
        name=d["name"],
        exec=list(exec_field),
        protocol_version=int(d.get("protocol_version", 1)),
        capabilities=list(d.get("capabilities", [])),
        runtimes=list(d.get("runtimes", [])),
        env=dict(d.get("env", {})),
    )


def load_manifests(manifest_dirs) -> dict[str, Adapter]:
    """Load adapter manifests from one directory or several (later dirs win on
    name collision). This lets generated compiler-flag variants in a second dir
    coexist with the built-in adapters."""
    if isinstance(manifest_dirs, (str, Path)):
        manifest_dirs = [manifest_dirs]
    adapters: dict[str, Adapter] = {}
    for d in manifest_dirs:
        d = Path(d)
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.manifest.toml")):
            a = load_manifest(p)
            adapters[a.name] = a
    return adapters
