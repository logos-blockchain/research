#!/usr/bin/env bash
# Run the ENTIRE Equi-X benchmark pipeline end to end:
#   1. bootstrap dependencies + build both runners   (scripts/setup.sh)
#   2. harness unit tests
#   3. main benchmark: C vs Rust across all operations, incl. the DoS-protection
#      verdict, with the cross-implementation correctness gate; the --full
#      profile additionally measures sustained concurrency (saturation ladder)
#      and the mining rate vs difficulty
#   4. compiler-flag variants: build a gcc/clang/-O matrix and compare them
#
# Usage:
#   ./scripts/run_all.sh                 # quick profile (smoke config; a few minutes)
#   ./scripts/run_all.sh --full          # deep sweep (full config + effort sweep; longer)
#   ./scripts/run_all.sh --out DIR       # output base dir (default: results/)
#   ./scripts/run_all.sh --no-variants   # skip the compiler-flag matrix
#   ./scripts/run_all.sh --no-setup      # assume deps already installed/built
#   ./scripts/run_all.sh --no-tests      # skip the unit tests
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/harness${PYTHONPATH:+:$PYTHONPATH}"

PROFILE=quick
OUT=results
DO_SETUP=1
DO_VARIANTS=1
DO_TESTS=1

while [ $# -gt 0 ]; do
  case "$1" in
    --full) PROFILE=full ;;
    --quick) PROFILE=quick ;;
    --out) [ $# -ge 2 ] || { echo "error: --out requires a directory argument" >&2; exit 2; }
           OUT="$2"; shift ;;
    --out=*) OUT="${1#*=}" ;;
    --no-setup) DO_SETUP=0 ;;
    --no-variants) DO_VARIANTS=0 ;;
    --no-tests) DO_TESTS=0 ;;
    -h|--help) sed -n '2,/^set -uo/p' "$0" | sed '$d'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

MAIN_CONFIG="configs/smoke.toml"
[ "$PROFILE" = full ] && MAIN_CONFIG="configs/full.toml"
# Prefer the project venv scripts/setup.sh creates: it has the harness + pytest
# installed and sidesteps PEP-668 "externally-managed" pip failures on Linux.
PY="python3"
[ -x "$ROOT/.venv/bin/python" ] && PY="$ROOT/.venv/bin/python"
BENCH="$PY -m equix_bench"
fail() { echo "ERROR: $*" >&2; exit 1; }

# Ctrl+C: report the interruption plainly and exit 130, rather than letting the
# child's non-zero exit trip a misleading "ERROR: ... failed". The harness kills
# its own runner subprocesses on SIGINT; this trap just makes the pipeline's own
# exit clean. 128+SIGINT(2) = 130, the conventional interrupted-by-Ctrl+C code.
on_interrupt() { echo; echo "Interrupted (Ctrl+C) — stopping the pipeline." >&2; exit 130; }
trap on_interrupt INT

echo "======================================================================"
echo " Equi-X full pipeline   profile=$PROFILE   out=$OUT/"
echo "======================================================================"

if [ "$DO_SETUP" = 1 ]; then
  echo; echo "### [1/4] Bootstrap dependencies + build runners"
  ./scripts/setup.sh || fail "setup.sh failed"
fi

if [ "$DO_TESTS" = 1 ]; then
  echo; echo "### [2/4] Harness unit tests"
  # Ensure pytest is importable. Externally-managed interpreters (PEP 668, e.g.
  # Homebrew/Debian Python) reject a plain `pip install`, so fall back through
  # --user and finally --break-system-packages before giving up.
  # With the venv from setup.sh, pytest is already present. Otherwise fall back
  # through --user and --break-system-packages before giving up.
  if ! $PY -c 'import pytest' >/dev/null 2>&1; then
    $PY -m pip install -q pytest >/dev/null 2>&1 \
      || $PY -m pip install -q --user pytest >/dev/null 2>&1 \
      || $PY -m pip install -q --break-system-packages pytest >/dev/null 2>&1 \
      || true
  fi
  if $PY -c 'import pytest' >/dev/null 2>&1; then
    $PY -m pytest -q harness/tests || fail "unit tests failed"
  else
    echo "  WARNING: could not install pytest; skipping unit tests." >&2
    echo "  Fix: re-run ./scripts/setup.sh (creates .venv with pytest), or:" >&2
    echo "    python3 -m pip install --break-system-packages pytest" >&2
  fi
fi

echo; echo "### [3/4] Main benchmark: C vs Rust (all ops + DoS-protection; --full adds concurrency + mining)  [$MAIN_CONFIG]"
# cmd_run runs the interop cross-check internally and exits non-zero if it fails,
# so this step is also the correctness gate.
$BENCH run --config "$MAIN_CONFIG" --out "$OUT/main" || fail "main benchmark / cross-check failed"

if [ "$DO_VARIANTS" = 1 ]; then
  echo; echo "### [4/4] Compiler-flag variants (gcc/clang x -O levels)"
  ./scripts/build_variants.sh || echo "  (some variants failed to build; continuing with those that did)"
  $BENCH run --config configs/compiler_flags.toml --out "$OUT/compiler_flags" \
    || echo "  (compiler-flags run returned non-zero; see $OUT/compiler_flags/)"
fi

echo; echo "======================================================================"
echo " Done. Reports:"
echo "   $OUT/main/report.md            C vs Rust: time, throughput, RSS, compile, effort, DoS"
[ "$DO_VARIANTS" = 1 ] && echo "   $OUT/compiler_flags/report.md  compiler-flag comparison"
echo "   plots: $OUT/*/plots/*.png    data: $OUT/*/results.csv"
# The --full profile also measures sustained parallel solve/verify capacity.
[ -f "$OUT/main/concurrency.csv" ] && \
  echo "   $OUT/main/concurrency.csv      measured concurrency/saturation (solves/s, verify/s, knee)"
[ -f "$OUT/main/mining.csv" ] && \
  echo "   $OUT/main/mining.csv           measured mining rate vs difficulty (tokens/s, 1-core + machine)"
# Surface the DoS verdict inline.
if [ -f "$OUT/main/report.md" ]; then
  grep -h 'Verdict:' "$OUT/main/report.md" | sed 's/\*\*//g; s/^/   DoS → /'
fi
echo "======================================================================"
