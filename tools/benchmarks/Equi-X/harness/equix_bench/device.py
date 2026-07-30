"""Device (CPU/GPU) identity.

Each runner self-reports its hardware in the result `env` (cpu, arch, device).
The harness derives a device record from that, so identity is correct even for a
remote runner or a future GPU adapter (which would report device="gpu"). A CLI
`--device-label` overrides only the human label, e.g. to disambiguate two machines
that report the same CPU model string.
"""
from __future__ import annotations

import platform
import re
from typing import Any, Optional


def slug(s: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower()).strip("-")
    return out or "unknown"


def device_from_env(env: dict[str, Any], override_label: Optional[str] = None) -> dict[str, str]:
    """Build a device record from a runner's reported env, falling back to the
    host when the runner did not report hardware (older/minimal adapters).

    The auto label combines the device model with the OS version so runs on the
    same CPU under different OS/kernel versions get distinct labels."""
    name = env.get("cpu") or _host_cpu()
    arch = env.get("arch") or platform.machine() or "unknown"
    dtype = env.get("device") or "cpu"
    os_name = env.get("os") or platform.system().lower() or "unknown"
    os_version = env.get("os_version") or platform.release() or "unknown"
    return {
        "type": dtype,
        "name": name,
        "arch": arch,
        "os": os_name,
        "os_version": os_version,
        "label": override_label or slug(f"{name}-{os_version}"),
    }


# Field priority works across arches: "model name" (x86), "Model" (Raspberry Pi
# board), "Hardware" (older ARM), "cpu model" (others).
_CPU_FIELDS = ("model name", "Model", "Hardware", "cpu model")


def parse_cpu_model(cpuinfo_text: str) -> str:
    found: dict[str, str] = {}
    for line in cpuinfo_text.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k in _CPU_FIELDS and k not in found and v:
            found[k] = v
    for f in _CPU_FIELDS:
        if f in found:
            return found[f]
    return "unknown"


def _host_cpu() -> str:
    try:
        model = parse_cpu_model(open("/proc/cpuinfo").read())
        if model != "unknown":
            return model
    except OSError:
        pass
    if platform.system() == "Darwin":  # macOS has no /proc
        try:
            import subprocess

            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=2,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except Exception:  # noqa: BLE001
            pass
    return platform.processor() or "unknown"
