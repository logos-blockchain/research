#!/usr/bin/env python3
"""Print the path of the bench binary from `cargo --message-format=json` on stdin.

Kept out of the Makefile because a shell one-liner cannot skip the non-JSON
lines cargo interleaves without becoming unreadable.
"""
import json
import sys

target = sys.argv[1] if len(sys.argv) > 1 else "verify_public_header"
found = []
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("reason") != "compiler-artifact" or not msg.get("executable"):
        continue
    if msg.get("target", {}).get("name") == target:
        found.append(msg["executable"])

if not found:
    sys.exit(f"no executable for bench target {target!r} in cargo's output")
print(found[-1])
