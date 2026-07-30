#!/usr/bin/env bash
# End-to-end verification: build, probe each runner directly, run the smoke
# config, and assert the cross-implementation correctness gate passes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CRUN="build/runners/c/equix_runner"
RRUN="runners/rust/target/release/equix_runner"

echo "==> Ensuring runners are built"
[ -x "$CRUN" ] && [ -x "$RRUN" ] || ./scripts/setup.sh

probe() {
  local runner="$1" name="$2"
  local job='{"schema_version":1,"operation":"solve","runtime":"try-compile","challenge_hex":"deadbeef","repetitions":1,"warmup":0}'
  local out; out="$(echo "$job" | "$runner" | tail -1)"
  echo "$out" | grep -q '"ok":true' || { echo "FAIL: $name did not return ok:true"; echo "$out"; exit 1; }
  echo "$out" | grep -q '"solutions":4' || { echo "FAIL: $name did not find 4 solutions for deadbeef"; echo "$out"; exit 1; }
  echo "    OK: $name solve/deadbeef -> 4 solutions"
}

echo "==> Probing runners directly"
probe "$CRUN" "equix-c"
probe "$RRUN" "equix-rust"

echo "==> Running smoke config"
PYTHONPATH=harness python3 -m equix_bench run --config configs/smoke.toml --out results --root .

echo "==> Cross-check gate"
PYTHONPATH=harness python3 -m equix_bench run --config configs/smoke.toml --out results --root . --crosscheck-only

echo "==> Outputs"
ls -1 results/plots/*.png
test -f results/report.md && echo "    report.md OK"
test -f results/results.csv && echo "    results.csv OK"
echo "==> VERIFY PASSED"
