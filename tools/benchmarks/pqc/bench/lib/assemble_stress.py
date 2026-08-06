#!/usr/bin/env python3
"""assemble_stress.py — wrap the per-algorithm stress rows into one results
JSON with full provenance.

Inputs (all paths):
  --meta   meta.env      KEY=VALUE host/run facts collected by stress.sh
  --lock   versions.lock toolchain provenance from setup.sh
  --rows   rows.jsonl    one JSON object per algorithm from stress_roles
  --out    reports/pqc/results/stress-<host>-<ts>.json

The output deliberately carries `is_stress_grade`, never `is_baseline_grade`.
A stress run uses every core and does not pin, so it can never satisfy the
reference gate — and a file that answered to the same field name would sooner
or later be merged into the reference dataset by something that only checked
the flag. Different question, different field.

What a stress run IS good for is ratios between the two roles measured in the
same phase, on the same machine, at the same instant. Those survive being
compared across machines; the absolute rates do not.
"""
from __future__ import annotations
import argparse
import json
import sys

SCHEMA_VERSION = "stress-1.0.0"


def read_env(path):
    """meta.env is KEY=VALUE with optionally quoted values (same shape as the
    measurement run's meta.env, written by shell `echo`)."""
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                v = v[1:-1]
            out[k] = v
    return out


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--lock", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    meta = read_env(args.meta)
    try:
        lock = read_env(args.lock)
    except OSError:
        lock = {}

    rows = []
    with open(args.rows) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[assemble-stress] skipping unparseable row: {e}", file=sys.stderr)

    warnings = [w for w in (meta.get("WARNINGS", "") or "").split("||") if w]

    # A stress run is honest about what it is not. These are the reasons it can
    # never be a reference measurement, recorded in the file rather than left
    # to the reader to remember.
    not_reference = [
        "stress runs use every core and are not pinned (concurrency is the "
        "measurement, so pinning would defeat it)",
        "throughput under saturation is sensitive to thermal and scheduler "
        "behaviour that the reference protocol exists to exclude",
    ]
    if meta.get("SMOKE") == "1":
        not_reference.append("smoke mode: 250 ms phase legs, pipeline check only")
    if meta.get("GOVERNOR_AFTER") != "performance":
        not_reference.append(
            f"CPU governor is '{meta.get('GOVERNOR_AFTER')}', not 'performance'")

    result = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": meta.get("STRESS_TOOL_VERSION", "0.1.0"),
        "generated_utc": meta.get("TS_UTC", ""),
        "measurement": "role-asymmetry stress",
        "is_stress_grade": meta.get("SMOKE") != "1",
        "is_baseline_grade": False,
        "not_reference_because": not_reference,
        "roles_model": {
            "encoder": "the side that produces the wire object "
                       "(KEM: encaps; signature: sign)",
            "decoder": "the side that consumes it "
                       "(KEM: decaps; signature: verify)",
            "note": "X25519 is symmetric by construction — both peers run the "
                    "same keygen+derive — so its measured ratio near 1.0 also "
                    "serves as a check on the harness.",
        },
        "host": {
            "hostname": meta.get("HOSTNAME", ""),
            "os": meta.get("OS", ""),
            "os_pretty": meta.get("OS_PRETTY", ""),
            "arch": meta.get("ARCH", ""),
            "kernel": meta.get("KERNEL", ""),
            "is_rpi": meta.get("IS_RPI") == "1",
            "rpi_model": meta.get("RPI_MODEL", ""),
            "cpu_brand": meta.get("CPU_BRAND", ""),
            "ncpu": to_int(meta.get("NCPU")),
            "ram_bytes": to_int(meta.get("RAM_BYTES")),
        },
        "run": {
            "duration_ms_per_leg": to_int(meta.get("DURATION_MS")),
            "threads_requested": to_int(meta.get("THREADS_REQUESTED")),
            "pinned": False,
            "governor_before": meta.get("GOVERNOR_BEFORE", ""),
            "governor_after": meta.get("GOVERNOR_AFTER", ""),
            "smoke": meta.get("SMOKE") == "1",
        },
        # Key names follow setup/versions.lock exactly; the lock is the single
        # source of toolchain truth and a typo here silently empties the
        # provenance rather than failing.
        "toolchain": {
            "liboqs_ref": lock.get("LIBOQS_REF", ""),
            "liboqs_commit": lock.get("LIBOQS_COMMIT", ""),
            "liboqs_opt_defines": lock.get("LIBOQS_OPT_DEFINES", ""),
            "openssl_commit": lock.get("OPENSSL_COMMIT", ""),
            "openssl_prefix": lock.get("OPENSSL_PREFIX", ""),
            "cflags_target": lock.get("CFLAGS_TARGET", ""),
            "bench_cflags": lock.get("BENCH_CFLAGS", ""),
            "cc_version": lock.get("CC_VERSION", ""),
        },
        "warnings": warnings,
        "algorithms": rows,
    }

    with open(args.out, "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")
    print(args.out)


if __name__ == "__main__":
    main()
